SPEED_THRESHOLDS: list[tuple[str, float, float]] = [
    ("stationary", 0.0,  1.0),
    ("walking",    1.0,  7.0),
    ("running",    7.0, 12.0),
    ("cycling",   12.0, 25.0),
    ("driving",   25.0, float("inf")),
]

HA_ACTIVITY_MAP: dict[str, str] = {
    "stationary": "stationary",
    "walking":    "walking",
    "running":    "running",
    "cycling":    "cycling",
    "automotive": "driving",
    "on_foot":    "walking",
}


def classify(speed_kmh: float | None, ha_activity: str | None) -> str:
    """Classify movement type. HA activity takes priority when plausible against speed."""
    ha_type = HA_ACTIVITY_MAP.get((ha_activity or "").lower())

    if ha_type and speed_kmh is not None:
        # Sanity-check: if HA says stationary but speed > 5 km/h, trust speed
        if ha_type == "stationary" and speed_kmh > 5.0:
            ha_type = None
        # If HA says driving but speed < 5 km/h, trust speed
        elif ha_type == "driving" and speed_kmh < 5.0:
            ha_type = None

    if ha_type:
        return ha_type

    if speed_kmh is None:
        return "unknown"

    for mtype, low, high in SPEED_THRESHOLDS:
        if low <= speed_kmh < high:
            return mtype

    return "unknown"
