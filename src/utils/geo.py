from math import radians, sin, cos, sqrt, atan2
from datetime import datetime


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def speed_kmh(lat1: float, lon1: float, ts1: datetime,
              lat2: float, lon2: float, ts2: datetime) -> float:
    dist_km = haversine_km(lat1, lon1, lat2, lon2)
    dt_hours = (ts2 - ts1).total_seconds() / 3600.0
    if dt_hours <= 0:
        return 0.0
    return dist_km / dt_hours
