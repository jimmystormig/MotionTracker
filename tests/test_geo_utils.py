from datetime import datetime, timedelta
from src.utils.geo import haversine_km, speed_kmh


def test_haversine_same_point():
    assert haversine_km(59.0, 18.0, 59.0, 18.0) == 0.0


def test_haversine_known_distance():
    # Stockholm city centre to ~1 degree north is roughly 111 km
    dist = haversine_km(59.0, 18.0, 60.0, 18.0)
    assert 110 < dist < 113


def test_haversine_symmetry():
    a = haversine_km(59.3, 18.0, 60.1, 17.5)
    b = haversine_km(60.1, 17.5, 59.3, 18.0)
    assert abs(a - b) < 1e-9


def test_speed_zero_time_delta():
    ts = datetime(2026, 1, 1, 12, 0, 0)
    assert speed_kmh(59.0, 18.0, ts, 59.1, 18.0, ts) == 0.0


def test_speed_walking_range():
    ts1 = datetime(2026, 1, 1, 12, 0, 0)
    ts2 = ts1 + timedelta(minutes=10)
    # ~1 km in 10 minutes = 6 km/h
    spd = speed_kmh(59.3293, 18.0686, ts1, 59.3383, 18.0686, ts2)
    assert 4.0 < spd < 8.0


def test_speed_driving_range():
    ts1 = datetime(2026, 1, 1, 12, 0, 0)
    ts2 = ts1 + timedelta(minutes=10)
    # ~5 km in 10 minutes = 30 km/h
    spd = speed_kmh(59.3293, 18.0686, ts1, 59.3743, 18.0686, ts2)
    assert spd > 25.0
