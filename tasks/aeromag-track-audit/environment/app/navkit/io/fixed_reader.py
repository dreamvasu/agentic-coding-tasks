"""Legacy flight-log reader.

The desk's pre-2016 archive is a fixed-field export, one record per line, with
``;`` comment lines. Latitude and longitude are recorded as degrees/minutes/
seconds with a hemisphere letter. The exact column layout is documented in
/app/data/flightlog.dat's header comment.
"""
from .. import config
from ..errors import ReaderError
from ..model import Waypoint


def parse_record(line):
    """Parse one fixed-field record into a Waypoint."""
    raise NotImplementedError


def read_legacy_log(path=None):
    """Read the legacy flight log into a list of Waypoint."""
    raise NotImplementedError
