import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://motiontracker:motiontracker@localhost:5432/motiontracker"

    HA_URL: str = "http://homeassistant.local:8123"
    HA_TOKEN: str = ""
    # New format: entity:activity_sensor pairs, e.g. "device_tracker.person1_iphone:sensor.person1_activity,device_tracker.person2_iphone:sensor.person2_activity"
    HA_TRACKED_ENTITIES: str = ""
    HA_DEVICE_TRACKERS: str = ""  # DEPRECATED: use HA_TRACKED_ENTITIES instead

    POLL_INTERVAL_SECONDS: int = 300
    QUIET_HOURS_START: int = 23
    QUIET_HOURS_END: int = 6
    QUIET_HOURS_ENABLED: bool = True

    BACKFILL_ON_STARTUP: bool = True
    BACKFILL_DAYS: int = 7
    BACKFILL_INTERVAL_HOURS: float = 1      # How often the catch-up backfill runs
    BACKFILL_CATCHUP_HOURS: float = 2       # How far back each catch-up looks

    MIN_MOVEMENT_METERS: float = 0          # 0 = no filter; set to 20 for old behaviour

    STADIA_API_KEY: str = ""

    LOG_LEVEL: str = "INFO"
    TZ: str = "Europe/Stockholm"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def tracked_entities(self) -> list[tuple[str, str | None]]:
        """Return list of (entity_id, activity_sensor_id | None) tuples."""
        if self.HA_TRACKED_ENTITIES:
            result = []
            for entry in self.HA_TRACKED_ENTITIES.split(","):
                entry = entry.strip()
                if not entry:
                    continue
                if ":" in entry:
                    entity, activity = entry.split(":", 1)
                    result.append((entity.strip(), activity.strip() or None))
                else:
                    result.append((entry, None))
            return result
        if self.HA_DEVICE_TRACKERS:
            logger.warning("HA_DEVICE_TRACKERS is deprecated, use HA_TRACKED_ENTITIES instead")
            return [(e.strip(), None) for e in self.HA_DEVICE_TRACKERS.split(",") if e.strip()]
        return []

    @property
    def device_tracker_list(self) -> list[str]:
        """Deprecated: use tracked_entities instead."""
        return [e for e, _ in self.tracked_entities]
