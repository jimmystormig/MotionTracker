import asyncio
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.config import Settings
from src.database import get_engine
from src.models.device import Device
from src.models.location import Location
from src.services.movement_classifier import classify
from src.utils.geo import speed_kmh, haversine_km

logger = logging.getLogger(__name__)

# In-memory cache of last known position per device_id for speed calc
_last_positions: dict[int, tuple[float, float, datetime]] = {}


def _is_quiet_hours(settings: Settings) -> bool:
    if not settings.QUIET_HOURS_ENABLED:
        return False
    now_hour = datetime.now().hour
    start = settings.QUIET_HOURS_START
    end = settings.QUIET_HOURS_END
    if start > end:  # e.g. 23-6 wraps midnight
        return now_hour >= start or now_hour < end
    return start <= now_hour < end


async def _get_or_create_device(session, entity_id: str, friendly_name: str | None,
                                 activity_entity_id: str | None) -> Device:
    result = await session.execute(select(Device).where(Device.entity_id == entity_id))
    device = result.scalar_one_or_none()
    if device is None:
        device = Device(entity_id=entity_id, friendly_name=friendly_name,
                        activity_entity_id=activity_entity_id)
        session.add(device)
        await session.flush()
        logger.info("Registered new device: %s", entity_id)
    return device


async def _fetch_state(client: httpx.AsyncClient, ha_url: str, entity_id: str) -> dict | None:
    try:
        resp = await client.get(f"{ha_url}/api/states/{entity_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
        logger.warning("HA returned %d for %s", resp.status_code, entity_id)
    except Exception as e:
        logger.warning("Error fetching %s: %s", entity_id, e)
    return None


def _guess_activity_entity(tracker_entity_id: str) -> str:
    # device_tracker.person_iphone -> sensor.person_iphone_activity
    name = tracker_entity_id.removeprefix("device_tracker.").removeprefix("person.")
    return f"sensor.{name}_activity"


async def poll_once(settings: Settings, client: httpx.AsyncClient):
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    engine = get_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with session_factory() as session:
        for entity_id, activity_sensor_id in settings.tracked_entities:
            state_data = await _fetch_state(client, settings.HA_URL, entity_id)
            if not state_data:
                continue

            attrs = state_data.get("attributes", {})
            lat = attrs.get("latitude")
            lon = attrs.get("longitude")
            if lat is None or lon is None:
                continue

            accuracy = attrs.get("gps_accuracy") or attrs.get("accuracy")
            if accuracy and accuracy > 200:
                logger.debug("Skipping %s: accuracy %sm too low", entity_id, accuracy)
                continue

            altitude = attrs.get("altitude")
            battery = attrs.get("battery_level")
            friendly_name = attrs.get("friendly_name")

            ha_activity = None
            if activity_sensor_id:
                activity_data = await _fetch_state(client, settings.HA_URL, activity_sensor_id)
                ha_activity = activity_data["state"] if activity_data else None

            # Use our own sample time as recorded_at, not HA's last_updated.
            # HA's Companion App only pushes location on significant iOS events (zone
            # transitions, cell tower changes), so last_updated can stay unchanged for
            # hours. Sampling at our own clock every POLL_INTERVAL_SECONDS gives dense
            # coverage even when HA hasn't registered a state change.
            recorded_at = datetime.utcnow()

            device = await _get_or_create_device(session, entity_id, friendly_name, activity_sensor_id)

            # Calculate speed and check movement vs last stored point
            spd = None
            if device.id in _last_positions:
                prev_lat, prev_lon, prev_ts = _last_positions[device.id]
                dist_m = haversine_km(prev_lat, prev_lon, lat, lon) * 1000
                # Skip if moved less than 20 m — avoids 288 identical records/day when stationary
                if dist_m < 20:
                    logger.debug("Skipping %s — stationary (%.1f m moved)", entity_id, dist_m)
                    continue
                spd = speed_kmh(prev_lat, prev_lon, prev_ts, lat, lon, recorded_at)

            movement = classify(spd, ha_activity)
            _last_positions[device.id] = (lat, lon, recorded_at)

            stmt = pg_insert(Location).values(
                device_id=device.id,
                latitude=lat,
                longitude=lon,
                accuracy=accuracy,
                altitude=altitude,
                speed=spd,
                battery=int(battery) if battery is not None else None,
                activity_state=ha_activity,
                movement_type=movement,
                recorded_at=recorded_at,
            ).on_conflict_do_nothing(index_elements=["device_id", "recorded_at"])

            await session.execute(stmt)
            logger.debug("Stored location for %s: (%.5f, %.5f) type=%s", entity_id, lat, lon, movement)

        await session.commit()


async def poll_loop(settings: Settings):
    if not settings.tracked_entities:
        logger.warning("No device trackers configured — poller idle")
        return

    headers = {"Authorization": f"Bearer {settings.HA_TOKEN}"}
    async with httpx.AsyncClient(headers=headers) as client:
        while True:
            if _is_quiet_hours(settings):
                logger.debug("Quiet hours — skipping poll")
            else:
                try:
                    await poll_once(settings, client)
                    logger.info("Poll complete")
                except Exception as e:
                    logger.error("Poll error: %s", e, exc_info=True)

            await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
