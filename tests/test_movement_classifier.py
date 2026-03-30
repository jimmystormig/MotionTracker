import pytest
from src.services.movement_classifier import classify


# ── Speed-only classification ─────────────────────────────
@pytest.mark.parametrize("speed, expected", [
    (0.0,   "stationary"),
    (0.5,   "stationary"),
    (1.0,   "walking"),
    (5.0,   "walking"),
    (6.9,   "walking"),
    (7.0,   "running"),
    (10.0,  "running"),
    (12.0,  "cycling"),
    (20.0,  "cycling"),
    (25.0,  "driving"),
    (100.0, "driving"),
])
def test_speed_only(speed, expected):
    assert classify(speed, None) == expected


def test_no_speed_no_activity():
    assert classify(None, None) == "unknown"


# ── HA activity takes priority ────────────────────────────
def test_ha_activity_walking_overrides_speed():
    # Speed says cycling but HA says walking
    assert classify(15.0, "walking") == "walking"


def test_ha_activity_automotive():
    assert classify(60.0, "automotive") == "driving"


def test_ha_activity_cycling():
    assert classify(18.0, "cycling") == "cycling"


def test_ha_activity_stationary():
    assert classify(0.0, "stationary") == "stationary"


def test_ha_activity_on_foot():
    assert classify(4.0, "on_foot") == "walking"


# ── Sanity checks override HA ─────────────────────────────
def test_ha_stationary_but_high_speed_uses_speed():
    # HA says stationary but person is clearly moving > 5 km/h
    result = classify(20.0, "stationary")
    assert result != "stationary"
    assert result == "cycling"


def test_ha_driving_but_very_low_speed_uses_speed():
    # HA says automotive but speed < 5 km/h (stopped at light)
    result = classify(0.5, "automotive")
    assert result == "stationary"


# ── Unknown / edge cases ──────────────────────────────────
def test_unknown_activity_string():
    assert classify(10.0, "unknown_activity") == "running"


def test_empty_activity():
    assert classify(5.0, "") == "walking"
