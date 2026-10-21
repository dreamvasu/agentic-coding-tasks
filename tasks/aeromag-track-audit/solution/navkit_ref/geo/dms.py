"""Degree/minute/second handling."""
from ..errors import GeometryError


def dms_to_decimal(degrees, minutes, seconds, hemisphere):
    h = (hemisphere or "").strip().upper()
    if h not in ("N", "S", "E", "W"):
        raise GeometryError("bad hemisphere %r" % hemisphere)
    val = abs(float(degrees)) + float(minutes) / 60.0 + float(seconds) / 3600.0
    return -val if h in ("S", "W") else val


def normalise_longitude(lon_deg):
    lon = (float(lon_deg) + 180.0) % 360.0 - 180.0
    return lon
