"""Magnetic-to-true heading correction."""
from ..geo import normalise_bearing


def true_bearing(magnetic_bearing_deg, declination_deg_value):
    return normalise_bearing(float(magnetic_bearing_deg) + float(declination_deg_value))
