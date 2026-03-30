from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models.device import Device
from src.models.location import Location

router = APIRouter()

GAP_THRESHOLD_MINUTES = 360  # 6 hours — connects long drives; overnight stays (8h+) still split


def _split_into_segments(points: list[dict]) -> list[list[dict]]:
    """Split a device's points into segments on time gaps > GAP_THRESHOLD_MINUTES."""
    if not points:
        return []
    segments: list[list[dict]] = []
    current: list[dict] = [points[0]]
    for pt in points[1:]:
        prev = current[-1]
        gap = (datetime.fromisoformat(pt["recorded_at"].rstrip("Z"))
               - datetime.fromisoformat(prev["recorded_at"].rstrip("Z")))
        if gap > timedelta(minutes=GAP_THRESHOLD_MINUTES):
            segments.append(current)
            current = [pt]
        else:
            current.append(pt)
    segments.append(current)
    return segments


@router.get("/locations")
async def get_locations(
    start: str = Query(..., description="ISO date or datetime"),
    end: str = Query(..., description="ISO date or datetime"),
    device_ids: str | None = Query(None, description="Comma-separated device IDs"),
    min_accuracy: float = Query(200.0, description="Max accuracy threshold in meters"),
    session: AsyncSession = Depends(get_session),
):
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", ""))
        end_dt = datetime.fromisoformat(end.replace("Z", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    if end_dt < start_dt:
        raise HTTPException(status_code=400, detail="end must be after start")

    # Resolve device filter
    wanted_ids: list[int] | None = None
    if device_ids:
        try:
            wanted_ids = [int(x) for x in device_ids.split(",") if x.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="device_ids must be integers")

    # Fetch devices
    dev_q = select(Device)
    if wanted_ids:
        dev_q = dev_q.where(Device.id.in_(wanted_ids))
    dev_result = await session.execute(dev_q)
    devices = {d.id: d for d in dev_result.scalars()}

    response: dict = {"devices": {}, "total_points": 0,
                      "date_range": {"start": start_dt.isoformat() + "Z",
                                     "end": end_dt.isoformat() + "Z"}}

    for dev_id, device in devices.items():
        loc_q = (
            select(Location)
            .where(
                Location.device_id == dev_id,
                Location.recorded_at >= start_dt,
                Location.recorded_at <= end_dt,
            )
            .order_by(Location.recorded_at)
        )
        if min_accuracy:
            loc_q = loc_q.where(
                (Location.accuracy == None) | (Location.accuracy <= min_accuracy)  # noqa: E711
            )

        loc_result = await session.execute(loc_q)
        locations = loc_result.scalars().all()

        points = [
            {
                "lat": loc.latitude,
                "lon": loc.longitude,
                "speed": round(loc.speed, 1) if loc.speed is not None else None,
                "movement_type": loc.movement_type,
                "recorded_at": loc.recorded_at.isoformat() + "Z",
                "accuracy": loc.accuracy,
                "battery": loc.battery,
            }
            for loc in locations
        ]

        segments = _split_into_segments(points)
        response["total_points"] += len(points)
        response["devices"][str(dev_id)] = {
            "entity_id": device.entity_id,
            "friendly_name": device.friendly_name or device.entity_id,
            "segments": [{"points": seg} for seg in segments if seg],
        }

    return response
