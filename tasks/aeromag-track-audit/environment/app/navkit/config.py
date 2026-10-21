"""Every constant the reduction depends on. Read these; do not restate them."""
DATA_DIR = "/app/data"
LEGACY_LOG = DATA_DIR + "/flightlog.dat"
WAYPOINTS_CSV = DATA_DIR + "/waypoints.csv"
TIEIN_JSON = DATA_DIR + "/tiein.json"
REPORT_PATH = "/app/report.json"

DECLINATION_DECIMALS = 4
BEARING_DECIMALS = 3
DISTANCE_DECIMALS = 3

EARTH_RADIUS_KM = 6371.0088

# The desk signs a track off when its closure error is within this.
CLOSURE_TOLERANCE_KM = 0.5
