"""Bearing arithmetic."""


def normalise_bearing(bearing_deg):
    """Wrap a bearing into [0, 360)."""
    raise NotImplementedError


def bearing_difference(a_deg, b_deg):
    """Signed smallest difference a-b, in (-180, 180]."""
    raise NotImplementedError
