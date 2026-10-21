"""Magnetic-to-true heading correction."""


def true_bearing(magnetic_bearing_deg, declination_deg_value):
    """True bearing for a recorded magnetic bearing at a point of known declination.

    Result is normalised into [0, 360).
    """
    raise NotImplementedError
