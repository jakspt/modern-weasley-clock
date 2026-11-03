from pprint import pprint

import pytest

from weasley_clock.app_layer.geofencing import LocationResolver
from weasley_clock.config import config
from weasley_clock.core.models import LocationType

BATTERY_THRESHOLD = 10
VELOCITY_THRESHOLD = 15

BATTERY_JUST_ABOVE_THRESHOLD = BATTERY_THRESHOLD + 1
VELOCITY_JUST_BELOW_THRESHOLD = VELOCITY_THRESHOLD - 1


@pytest.fixture
def configured_zones(basic_config):
    return config._load_zones(basic_config)


@pytest.fixture
def location_resolver(configured_zones) -> LocationResolver:
    return LocationResolver(configured_zones, BATTERY_THRESHOLD, VELOCITY_THRESHOLD)


@pytest.fixture
def velocity_just_below_threshold():
    return VELOCITY_THRESHOLD - 1


@pytest.fixture
def battery_just_above_threshold():
    return BATTERY_THRESHOLD + 1


@pytest.mark.parametrize(
    # velocity and battery percentage are set at their threshold values which would
    # result in a match for "TRANSIT" / "MORTAL PERIL" if the user wasn't at home
    "coords_within_home_zone",
    [
        dict(
            lat=48.208200,
            lon=16.373800,
            tid="p1",
            velocity=VELOCITY_THRESHOLD,
            battery_pct=BATTERY_THRESHOLD,
        ),
        dict(
            lat=48.207840,
            lon=16.373800,
            tid="p1",
            velocity=VELOCITY_THRESHOLD,
            battery_pct=BATTERY_THRESHOLD,
        ),
        dict(
            lat=48.208200,
            lon=16.373260,
            tid="p1",
            velocity=VELOCITY_THRESHOLD,
            battery_pct=BATTERY_THRESHOLD,
        ),
    ],
)
def test_coordinates_in_home_zone_matches_home(
    location_resolver, coords_within_home_zone
):
    location = location_resolver.match_semantic_location(**coords_within_home_zone)
    assert location == LocationType.HOME


@pytest.mark.parametrize(
    "coords_within_work_zone",
    [
        dict(
            lat=48.209460,
            lon=16.3738,
            tid="p1",
            velocity=VELOCITY_THRESHOLD,
            battery_pct=BATTERY_THRESHOLD,
        ),
        dict(
            lat=48.209100,
            lon=16.374340,
            tid="p1",
            velocity=VELOCITY_THRESHOLD,
            battery_pct=BATTERY_THRESHOLD,
        ),
    ],
)
def test_coordinates_in_work_zone_matches_work(
    location_resolver, coords_within_work_zone
):
    location = location_resolver.match_semantic_location(**coords_within_work_zone)
    assert location == LocationType.WORK_UNI


OUTSIDE_COORDS = [
    {"lat": 48.208200, "lon": 16.374610},
    {"lat": 48.209100, "lon": 16.372990},
    {"lat": 48.208650, "lon": 16.374000},
]

# This way of nesting parameterizations was suggested by GitHub Copilot on 05/06/2026,
# checked for correctness and further adapted by the author


@pytest.mark.parametrize("base_coord", OUTSIDE_COORDS)
@pytest.mark.parametrize(
    "velocity, battery_pct, expected_location",
    [
        (
            VELOCITY_JUST_BELOW_THRESHOLD,
            BATTERY_JUST_ABOVE_THRESHOLD,
            LocationType.LEISURE,
        ),
        (
            VELOCITY_JUST_BELOW_THRESHOLD,
            BATTERY_THRESHOLD,
            LocationType.MORTAL_PERIL,
        ),
        # MORTAL_PERIL should override IN_TRANSIT
        (VELOCITY_THRESHOLD, BATTERY_THRESHOLD, LocationType.MORTAL_PERIL),
        (VELOCITY_THRESHOLD, BATTERY_JUST_ABOVE_THRESHOLD, LocationType.IN_TRANSIT),
        (
            VELOCITY_JUST_BELOW_THRESHOLD,
            BATTERY_JUST_ABOVE_THRESHOLD,
            LocationType.LEISURE,
        ),
    ],
)
def test_coordinates_outside_fences_match_computed_locations(
    location_resolver, base_coord, velocity, battery_pct, expected_location
):
    kwargs = {
        **base_coord,
        "tid": "p1",
        "velocity": velocity,
        "battery_pct": battery_pct,
    }

    location = location_resolver.match_semantic_location(**kwargs)
    assert location == expected_location
