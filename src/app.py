import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.config import Settings
from src.database import init_engine

settings = Settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_poller_task: asyncio.Task | None = None
_backfill_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _poller_task, _backfill_task

    init_engine(settings.DATABASE_URL)

    from src.services.ha_poller import poll_loop
    from src.services.backfill import backfill_history

    _poller_task = asyncio.create_task(poll_loop(settings))
    logger.info("HA poller started (interval=%ds, quiet=%d-%d)",
                settings.POLL_INTERVAL_SECONDS, settings.QUIET_HOURS_START, settings.QUIET_HOURS_END)

    if settings.BACKFILL_ON_STARTUP and settings.tracked_entities:
        _backfill_task = asyncio.create_task(backfill_history(settings))
        logger.info("Backfill task started (days=%d)", settings.BACKFILL_DAYS)

    yield

    if _poller_task:
        _poller_task.cancel()
    if _backfill_task:
        _backfill_task.cancel()
    logger.info("MotionTracker shutdown complete")


app = FastAPI(title="MotionTracker", lifespan=lifespan)

from src.api.health import router as health_router
from src.api.devices import router as devices_router
from src.api.locations import router as locations_router
from src.api.stats import router as stats_router

app.include_router(health_router)
app.include_router(devices_router, prefix="/api")
app.include_router(locations_router, prefix="/api")
app.include_router(stats_router, prefix="/api")

app.mount("/", StaticFiles(directory="static", html=True), name="static")
