from navkit.geo import dms_to_decimal, normalise_longitude, great_circle_km, normalise_bearing, bearing_difference


def test_dms_south_is_negative():
    assert abs(dms_to_decimal(26, 10, 38.496, "S") - (-26.177360)) < 1e-5


def test_dms_east_is_positive():
    assert abs(dms_to_decimal(20, 6, 26.388, "E") - 20.107330) < 1e-5


def test_longitude_wraps():
    assert abs(normalise_longitude(190.0) - (-170.0)) < 1e-9


def test_great_circle_known_leg():
    d = great_circle_km(-26.0, 21.0, -25.0, 21.0)
    assert 110.0 < d < 112.0


def test_bearing_normalises():
    assert abs(normalise_bearing(-30.0) - 330.0) < 1e-9
    assert abs(bearing_difference(10.0, 350.0) - 20.0) < 1e-9
