"""Modern waypoint export (CSV)."""
import csv

from .. import config
from ..errors import ReaderError
from ..model import Waypoint


def read_waypoints(path=None):
    """Read the CSV waypoint export into a list of Waypoint.

    Columns: waypoint_id, site, lat_deg, lon_deg, altitude_km, obs_date,
    magnetic_bearing_deg, leg_km.
    """
    raise NotImplementedError
