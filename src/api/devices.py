from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.models.device import Device
from src.models.location import Location

router = APIRouter()


@router.get("/devices")
async def list_devices(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(
            Device.id,
            Device.entity_id,
            Device.friendly_name,
            func.count(Location.id).label("location_count"),
            func.max(Location.recorded_at).label("last_seen"),
        )
        .outerjoin(Location, Location.device_id == Device.id)
        .group_by(Device.id)
        .order_by(Device.id)
    )
    rows = result.all()
    return [
        {
            "id": r.id,
            "entity_id": r.entity_id,
            "friendly_name": r.friendly_name or r.entity_id,
            "location_count": r.location_count,
            "last_seen": r.last_seen.isoformat() + "Z" if r.last_seen else None,
        }
        for r in rows
    ]
