from datetime import datetime, date
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models.device import Device
from src.models.location import Location

router = APIRouter()


@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    total_q = await session.execute(select(func.count(Location.id)))
    total = total_q.scalar_one()

    dev_q = await session.execute(select(func.count(Device.id)))
    total_devices = dev_q.scalar_one()

    range_q = await session.execute(
        select(func.min(Location.recorded_at), func.max(Location.recorded_at))
    )
    earliest, latest = range_q.one()

    today_start = datetime.combine(date.today(), datetime.min.time())
    today_q = await session.execute(
        select(func.count(Location.id)).where(Location.recorded_at >= today_start)
    )
    today_points = today_q.scalar_one()

    size_q = await session.execute(
        text("SELECT pg_total_relation_size('locations') / 1024.0 / 1024.0")
    )
    storage_mb = round(float(size_q.scalar_one() or 0), 2)

    return {
        "total_locations": total,
        "total_devices": total_devices,
        "date_range": {
            "earliest": earliest.date().isoformat() if earliest else None,
            "latest": latest.date().isoformat() if latest else None,
        },
        "today_points": today_points,
        "storage_mb": storage_mb,
    }
