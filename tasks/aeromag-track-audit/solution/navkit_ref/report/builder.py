"""Assemble the reduction report."""
from .. import config


def build_report(waypoints, declinations, true_bearings, closures):
    md, bd, cd = (config.DECLINATION_DECIMALS, config.BEARING_DECIMALS, config.DISTANCE_DECIMALS)
    return {
        "waypoint_count": len(waypoints),
        "total_leg_km": int(sum(int(w.leg_km) for w in waypoints)),
        "sites": sorted({w.site for w in waypoints}),
        "declination_by_id": {k: round(float(v), md) for k, v in declinations.items()},
        "true_bearing_by_id": {k: round(float(v), bd) for k, v in true_bearings.items()},
        "closure_km_by_site": {k: round(float(v), cd) for k, v in closures.items()},
    }
