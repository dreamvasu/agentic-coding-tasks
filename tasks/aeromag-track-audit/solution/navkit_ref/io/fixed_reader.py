"""Legacy flight-log reader (fixed-field, DMS)."""
from .. import config
from ..errors import ReaderError
from ..geo import dms_to_decimal
from ..model import Waypoint


def parse_record(line):
    try:
        lat = dms_to_decimal(int(line[16:19]), int(line[19:21]), float(line[21:27]), line[27])
        lon = dms_to_decimal(int(line[28:32]), int(line[32:34]), float(line[34:40]), line[40])
        return Waypoint(
            waypoint_id=line[0:6].strip(),
            site=line[6:16].strip(),
            lat_deg=lat,
            lon_deg=lon,
            altitude_km=float(line[41:47]),
            obs_date=line[47:57].strip(),
            magnetic_bearing_deg=float(line[62:68]),
            leg_km=int(line[57:62]))
    except (ValueError, IndexError) as exc:
        raise ReaderError("bad legacy record %r: %s" % (line[:20], exc)) from exc


def read_legacy_log(path=None):
    path = path or config.LEGACY_LOG
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip() or line.lstrip().startswith(";"):
                    continue
                out.append(parse_record(line.rstrip("\n")))
    except OSError as exc:
        raise ReaderError("cannot read legacy log: %s" % exc) from exc
    return out
