"""Modern waypoint export (CSV)."""
import csv

from .. import config
from ..errors import ReaderError
from ..model import Waypoint


def read_waypoints(path=None):
    path = path or config.WAYPOINTS_CSV
    out = []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                out.append(Waypoint(
                    waypoint_id=r["waypoint_id"].strip(),
                    site=r["site"].strip(),
                    lat_deg=float(r["lat_deg"]),
                    lon_deg=float(r["lon_deg"]),
                    altitude_km=float(r["altitude_km"]),
                    obs_date=r["obs_date"].strip(),
                    magnetic_bearing_deg=float(r["magnetic_bearing_deg"]),
                    leg_km=int(r["leg_km"])))
    except (OSError, KeyError, ValueError) as exc:
        raise ReaderError("cannot read waypoint export: %s" % exc) from exc
    return out
