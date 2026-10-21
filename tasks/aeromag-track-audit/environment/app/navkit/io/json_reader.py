"""Tie-in reference stations (JSON)."""
import json

from .. import config
from ..errors import ReaderError
from ..model import Waypoint


def read_tieins(path=None):
    """Read the tie-in station file into a list of Waypoint."""
    raise NotImplementedError
