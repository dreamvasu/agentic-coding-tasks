"""Degree/minute/second handling."""
from ..errors import GeometryError


def dms_to_decimal(degrees, minutes, seconds, hemisphere):
    """Convert a DMS triple plus hemisphere letter (N/S/E/W) to signed decimal degrees."""
    raise NotImplementedError


def normalise_longitude(lon_deg):
    """Wrap a longitude into the half-open range [-180, 180)."""
    raise NotImplementedError
