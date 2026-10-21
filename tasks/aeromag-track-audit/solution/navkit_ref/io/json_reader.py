"""Tie-in reference stations (JSON)."""
import json

from .. import config
from ..errors import ReaderError
from ..model import Waypoint


def read_tieins(path=None):
    path = path or config.TIEIN_JSON
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return [Waypoint(waypoint_id=s["waypoint_id"], site=s["site"],
                         lat_deg=float(s["lat_deg"]), lon_deg=float(s["lon_deg"]),
                         altitude_km=float(s["altitude_km"]), obs_date=s["obs_date"],
                         magnetic_bearing_deg=float(s["magnetic_bearing_deg"]),
                         leg_km=int(s["leg_km"])) for s in data["stations"]]
    except (OSError, KeyError, ValueError) as exc:
        raise ReaderError("cannot read tie-in stations: %s" % exc) from exc
