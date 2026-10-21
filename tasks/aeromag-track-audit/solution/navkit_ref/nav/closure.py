"""Track closure."""
from .. import config
from ..geo import great_circle_km
from .correct import true_bearing
from .legs import leg_endpoint


def track_closure_km(waypoints, declinations):
    if not waypoints:
        return 0.0
    lat, lon = waypoints[0].lat_deg, waypoints[0].lon_deg
    cur_lat, cur_lon = lat, lon
    for w in waypoints:
        tb = true_bearing(w.magnetic_bearing_deg, declinations[w.waypoint_id])
        cur_lat, cur_lon = leg_endpoint(cur_lat, cur_lon, tb, w.leg_km)
    return great_circle_km(lat, lon, cur_lat, cur_lon)
