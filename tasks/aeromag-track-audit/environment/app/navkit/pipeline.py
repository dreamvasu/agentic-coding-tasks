"""End-to-end reduction: read all three feeds, evaluate the field, reduce, report."""
from . import config
from .io import read_waypoints, read_legacy_log, read_tieins
from .field import declination_deg
from .nav import true_bearing, track_closure_km
from .report import build_report, write_report


def load_all():
    """Read every survey feed and return one ordered list of Waypoint."""
    raise NotImplementedError


def run():
    """Run the whole reduction and write the report."""
    raise NotImplementedError
