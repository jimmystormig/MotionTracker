from fastapi import APIRouter
from src.app import _poller_task

router = APIRouter()


@router.get("/health")
async def health():
    polling = _poller_task is not None and not _poller_task.done()
    return {"status": "healthy", "polling": polling}
