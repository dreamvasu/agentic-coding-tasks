"""The shapes every reader must produce."""
from dataclasses import dataclass


@dataclass
class Waypoint:
    """One archived survey waypoint."""
    waypoint_id: str
    site: str
    lat_deg: float
    lon_deg: float
    altitude_km: float
    obs_date: str          # ISO YYYY-MM-DD
    magnetic_bearing_deg: float
    leg_km: int
