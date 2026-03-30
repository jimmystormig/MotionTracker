import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.config import Settings
from src.database import get_engine
from src.models.device import Device
from src.models.location import Location
from src.services.ha_poller import _get_or_create_device
from src.services.movement_classifier import classify
from src.utils.geo import speed_kmh

logger = logging.getLogger(__name__)

# HA keeps full GPS history only in its short-term states table (~24-48h).
# Older data is compressed to zone-transition records only.
# Querying in 1-day chunks ensures we always hit the dense recent-states table.
CHUNK_DAYS = 1


async def _fetch_chunk(client: httpx.AsyncClient, ha_url: str, entity_id: str,
                       start: datetime, end: datetime) -> list[dict]:
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    url = (f"{ha_url}/api/history/period/{start_str}"
           f"?filter_entity_id={entity_id}"
           f"&end_time={end_str}"
           f"&significant_changes_only=false")
    try:
        resp = await client.get(url, timeout=60)
        if resp.status_code != 200:
            logger.warning("History API %d for %s (%s → %s)", resp.status_code, entity_id, start_str, end_str)
            return []
        history = resp.json()
        return history[0] if history and history[0] else []
    except Exception as e:
        logger.error("Fetch error for %s chunk %s: %s", entity_id, start_str, e)
        return []


async def backfill_history(settings: Settings):
    """Fetch the last N days from HA history API in 1-day chunks and insert location data."""
    if not settings.tracked_entities:
        return

    import asyncio
    await asyncio.sleep(5)

    engine = get_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    overall_start = now - timedelta(days=settings.BACKFILL_DAYS)

    headers = {"Authorization": f"Bearer {settings.HA_TOKEN}"}
    async with httpx.AsyncClient(headers=headers) as client:
        for entity_id, activity_sensor_id in settings.tracked_entities:
            logger.info("Backfilling %s: %d days in %d-day chunks",
                        entity_id, settings.BACKFILL_DAYS, CHUNK_DAYS)

            # Ensure device row exists before chunk loop
            async with session_factory() as session:
                await _get_or_create_device(session, entity_id, None, activity_sensor_id)
                await session.commit()

            total_inserted = 0
            chunk_start = overall_start

            while chunk_start < now:
                chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS), now)
                states = await _fetch_chunk(client, settings.HA_URL, entity_id, chunk_start, chunk_end)

                with_gps = [s for s in states if s.get("attributes", {}).get("latitude") is not None]
                logger.info("  %s → %s : %d records, %d with GPS",
                            chunk_start.strftime("%m-%d"), chunk_end.strftime("%m-%d"),
                            len(states), len(with_gps))
                if states and not with_gps:
                    sample_attrs = list(states[0].get("attributes", {}).keys())
                    logger.info("    [diag] first record state=%r attrs=%s",
                                states[0].get("state"), sample_attrs)

                async with session_factory() as session:
                    result = await session.execute(select(Device).where(Device.entity_id == entity_id))
                    device = result.scalar_one()

                    prev_lat = prev_lon = prev_ts = None
                    for state in with_gps:
                        attrs = state.get("attributes", {})
                        lat = attrs["latitude"]
                        lon = attrs["longitude"]

                        accuracy = attrs.get("gps_accuracy") or attrs.get("accuracy")
                        if accuracy and accuracy > 200:
                            continue

                        ts_str = state.get("last_updated") or state.get("last_changed")
                        try:
                            recorded_at = datetime.fromisoformat(
                                ts_str.replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                        except Exception:
                            continue

                        spd = None
                        if prev_lat is not None:
                            spd = speed_kmh(prev_lat, prev_lon, prev_ts, lat, lon, recorded_at)

                        movement = classify(spd, attrs.get("activity"))
                        prev_lat, prev_lon, prev_ts = lat, lon, recorded_at

                        stmt = pg_insert(Location).values(
                            device_id=device.id,
                            latitude=lat,
                            longitude=lon,
                            accuracy=accuracy,
                            altitude=attrs.get("altitude"),
                            speed=spd,
                            battery=int(attrs["battery_level"]) if attrs.get("battery_level") is not None else None,
                            activity_state=attrs.get("activity"),
                            movement_type=movement,
                            recorded_at=recorded_at,
                        ).on_conflict_do_nothing(index_elements=["device_id", "recorded_at"])

                        await session.execute(stmt)
                        total_inserted += 1

                    await session.commit()

                chunk_start = chunk_end

            logger.info("Backfill complete for %s: %d locations total", entity_id, total_inserted)
