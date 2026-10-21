"""Bearing arithmetic."""


def normalise_bearing(bearing_deg):
    return float(bearing_deg) % 360.0


def bearing_difference(a_deg, b_deg):
    d = (float(a_deg) - float(b_deg) + 180.0) % 360.0 - 180.0
    return d + 360.0 if d <= -180.0 else d
