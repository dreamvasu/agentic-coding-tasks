"""Track closure.

A survey track is flown as a loop: running every recorded leg from the first
waypoint along its true bearing should return to the start. The residual gap is
the track's closure error and is the desk's headline quality figure.
"""
from .. import config


def track_closure_km(waypoints, declinations):
    """Closure error in km for one ordered, looped track."""
    raise NotImplementedError
