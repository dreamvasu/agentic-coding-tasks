from navkit.io import read_waypoints, read_legacy_log, read_tieins


def test_csv_reader_shapes():
    wps = read_waypoints()
    assert wps, "no waypoints parsed from the CSV export"
    w = wps[0]
    assert w.waypoint_id and w.site and isinstance(w.leg_km, int)


def test_legacy_log_parses_dms():
    wps = read_legacy_log()
    assert wps, "no waypoints parsed from the legacy flight log"
    assert all(-90 <= w.lat_deg <= 90 for w in wps)
    assert all(-180 <= w.lon_deg < 180 for w in wps)


def test_tieins_parse():
    assert read_tieins(), "no tie-in stations parsed"


def test_all_feeds_contribute():
    total = len(read_waypoints()) + len(read_legacy_log()) + len(read_tieins())
    assert total == 26
