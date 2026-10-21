"""Magnetic declination from the reference geomagnetic field.

Declination is the angle from true north to magnetic north, positive when
magnetic north lies east of true north. It is obtained from the horizontal
components of the reference field at the waypoint's position, altitude and
observation date; ``ppigrf`` evaluates that field.
"""
import math

from ..errors import FieldError


def declination_deg(lat_deg, lon_deg, altitude_km, obs_date):
    """Magnetic declination in degrees at this position, altitude and date."""
    raise NotImplementedError
