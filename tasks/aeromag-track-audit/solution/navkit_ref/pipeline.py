"""End-to-end reduction."""
from . import config
from .field import declination_deg
from .io import read_legacy_log, read_tieins, read_waypoints
from .nav import track_closure_km, true_bearing
from .report import build_report, write_report


def load_all():
    wps = list(read_waypoints()) + list(read_legacy_log()) + list(read_tieins())
    wps.sort(key=lambda w: w.waypoint_id)
    return wps


def run():
    wps = load_all()
    decl = {w.waypoint_id: declination_deg(w.lat_deg, w.lon_deg, w.altitude_km, w.obs_date)
            for w in wps}
    tbs = {w.waypoint_id: true_bearing(w.magnetic_bearing_deg, decl[w.waypoint_id]) for w in wps}
    by_site = {}
    for w in wps:
        by_site.setdefault(w.site, []).append(w)
    closures = {site: track_closure_km(track, decl) for site, track in by_site.items()}
    payload = build_report(wps, decl, tbs, closures)
    write_report(payload)
    return payload
