"""Leg geometry along a survey track."""
import math

from .. import config


def leg_endpoint(lat_deg, lon_deg, true_bearing_deg, distance_km):
    """Destination point reached by running ``distance_km`` along ``true_bearing_deg``."""
    raise NotImplementedError

