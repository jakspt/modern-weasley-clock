from weasley_clock.config import config
from weasley_clock.core.models import ConfiguredZone, GeoFence, LocationType


def test_load_zones_successful_with_valid_config(basic_config):
    all_zones = config._load_zones(basic_config)

    assert (
        ConfiguredZone(LocationType("HOME"), [GeoFence(48.208200, 16.3738, 50)])
        in all_zones["p1"]
    )
    # "WORK_UNI": [{"lat": 48.2082, "lon": 16.3738, "radius_m": 50}]
    assert len(all_zones["p3"][0]) == 3
    assert len(all_zones["p3"][1]) == 1
    assert len(all_zones["p4"][0]) == 1
    assert len(all_zones["p4"][1]) == 1

    # pprint(all_zones)


def test_load_colours_creates_expected_tuple(basic_config):
    colour_dict = config._load_colours(basic_config)
    assert colour_dict["p1"] == (255, 100, 0)
    assert colour_dict["p2"] == (0, 255, 0)
    assert colour_dict["p3"] == (50, 100, 0)
    assert colour_dict["p4"] == (0, 100, 0)
