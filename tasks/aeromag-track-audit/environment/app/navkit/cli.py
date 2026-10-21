"""python -m navkit reduce"""
import sys

from .pipeline import run


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0] != "reduce":
        print("usage: python -m navkit reduce", file=sys.stderr)
        return 2
    payload = run()
    print("reduced %d waypoints" % payload["waypoint_count"])
    return 0
