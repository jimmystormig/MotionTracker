import pytest


@pytest.fixture
def sample_locations():
    from datetime import datetime
    base = datetime(2026, 3, 29, 8, 0, 0)
    return [
        {"lat": 59.3293, "lon": 18.0686, "ts": base},
        # ~1 km north — ~6 km/h over 10 min = walking
        {"lat": 59.3383, "lon": 18.0686, "ts": base.replace(minute=10)},
        # ~3 km further north — ~18 km/h over 10 min = cycling
        {"lat": 59.3653, "lon": 18.0686, "ts": base.replace(minute=20)},
    ]
