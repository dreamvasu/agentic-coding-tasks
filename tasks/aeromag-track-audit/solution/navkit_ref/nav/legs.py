"""Leg geometry along a survey track."""
import math

from .. import config
from ..geo import normalise_longitude


def leg_endpoint(lat_deg, lon_deg, true_bearing_deg, distance_km):
    ang = float(distance_km) / config.EARTH_RADIUS_KM
    br = math.radians(float(true_bearing_deg))
    p1 = math.radians(float(lat_deg))
    l1 = math.radians(float(lon_deg))
    p2 = math.asin(math.sin(p1) * math.cos(ang) + math.cos(p1) * math.sin(ang) * math.cos(br))
    l2 = l1 + math.atan2(math.sin(br) * math.sin(ang) * math.cos(p1),
                         math.cos(ang) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), normalise_longitude(math.degrees(l2))

