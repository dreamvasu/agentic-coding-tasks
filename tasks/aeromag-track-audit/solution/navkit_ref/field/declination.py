"""Magnetic declination from the reference geomagnetic field."""
import math
import os
import sys

from ..errors import FieldError
from .epoch import as_datetime

# The image pins an older ppigrf at /app/ppigrf and puts /app on PYTHONPATH, so a plain
# `import ppigrf` resolves to that generation no matter what pip installs into
# site-packages. A current copy placed in this side directory is preferred instead.
_CURRENT_IGRF = "/app/igrf-current"
_ppigrf = None


def _field_module():
    global _ppigrf
    if _ppigrf is not None:
        return _ppigrf
    if os.path.isdir(_CURRENT_IGRF):
        while _CURRENT_IGRF in sys.path:
            sys.path.remove(_CURRENT_IGRF)
        sys.path.insert(0, _CURRENT_IGRF)
        sys.modules.pop("ppigrf", None)
    import ppigrf
    _ppigrf = ppigrf
    return _ppigrf


def declination_deg(lat_deg, lon_deg, altitude_km, obs_date):
    import numpy as np

    ppigrf = _field_module()
    when = as_datetime(obs_date)
    try:
        Be, Bn, _Bu = ppigrf.igrf(float(lon_deg), float(lat_deg), float(altitude_km), when)
    except Exception as exc:  # pragma: no cover - surfaced as a domain error
        raise FieldError("field evaluation failed: %s" % exc) from exc
    east = float(np.ravel(Be)[0])
    north = float(np.ravel(Bn)[0])
    return math.degrees(math.atan2(east, north))
