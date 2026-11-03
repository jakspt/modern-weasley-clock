from unittest.mock import patch

import pytest

from weasley_clock.config import validate
from weasley_clock.config.validate import (
    ConfigSchemaError,
    DuplicateColourError,
    DuplicateTrackerIdError,
    GeoFenceOverlapError,
)


def test_validate_colours_succeeds_with_unique_colours(basic_config):
    validate.colour_uniqueness(basic_config)
    assert True


def test_validate_colours_fails_for_duplicate_colours(basic_config):
    basic_config["users"]["Person1"]["color_rgb"] = [255, 255, 255]
    basic_config["users"]["Person2"]["color_rgb"] = [255, 255, 255]
    with pytest.raises(DuplicateColourError):
        validate.colour_uniqueness(basic_config)


def test_validate_config_structure_succeeds_for_valid_config(basic_config):
    validate.config_structure(basic_config)
    assert True


def test_validate_config_structure_fails_for_invalid_tid(basic_config):
    basic_config["users"]["Person1"]["tid"] = "p11"
    with pytest.raises(ConfigSchemaError):
        validate.config_structure(basic_config)


def test_validate_config_structure_succeeds_for_duplicate_tids(basic_config):
    # The JSON Schema cannot check for duplicate TIDs:
    basic_config["users"]["Person2"]["tid"] = "p1"
    assert True


def test_validate_config_structure_fails_for_invalid_number_of_users(basic_config):
    basic_config["users"].pop("Person1")
    with pytest.raises(ConfigSchemaError):
        validate.config_structure(basic_config)


def test_validate_tids_succeeds_for_valid_tids(basic_config):
    validate.tid_uniqueness(basic_config)
    assert True


def test_validate_tids_fails_for_duplicate_tids(basic_config):
    basic_config["users"]["Person1"]["tid"] = "p2"
    with pytest.raises(DuplicateTrackerIdError):
        validate.tid_uniqueness(basic_config)


def validate_all_user_geofences(basic_config):
    zones_list = [username["geofences"] for username in basic_config["users"].values()]
    for user_zones in zones_list:
        validate._validate_user_zones(user_zones)


def test_validate_geofence_overlap_succeeds_with_valid_config(basic_config):
    validate_all_user_geofences(basic_config)
    assert True


def test_validate_geofence_overlap_fails_for_overlapping_fences(basic_config):
    basic_config["users"]["Person1"]["geofences"]["WORK_UNI"] = [
        {"lat": 48.209098, "lon": 16.3738, "radius_m": 50},
    ]
    basic_config["users"]["Person1"]["geofences"]["HOME"] = [
        {"lat": 48.208200, "lon": 16.3738, "radius_m": 50},
    ]
    with pytest.raises(GeoFenceOverlapError):
        validate_all_user_geofences(basic_config)


def test_validate_geofence_overlap_succeeds_for_overlapping_fences_between_users(
    basic_config,
):
    basic_config["users"]["Person2"]["geofences"]["WORK_UNI"] = [
        {"lat": 48.208200, "lon": 16.3738, "radius_m": 50}
    ]
    basic_config["users"]["Person2"]["geofences"]["HOME"] = [
        {"lat": 48.209100, "lon": 16.3738, "radius_m": 50}
    ]
    validate_all_user_geofences(basic_config)
    assert True


# Edge case: The geofences intersect at exactly one point.
# The system also marks those as overlapping to prevent the user being assigned to an undefined
# semantic location if they are at exactly this intersection point between zones


@patch("weasley_clock.config.validate.distance")
def test_validate_geofence_overlap_fails_for_touching_fences(
    mock_geodesic, basic_config
):
    # mock to prevent any rounding errors
    mock_geodesic.return_value.meters = 250.0

    # geofences whose radii sum up to exactly 250 meters
    basic_config["users"]["Person1"]["geofences"]["WORK_UNI"] = [
        {"lat": 0.0, "lon": 0.0, "radius_m": 100},
    ]
    basic_config["users"]["Person1"]["geofences"]["HOME"] = [
        {
            "lat": 99.0,
            "lon": 99.0,
            "radius_m": 150,
        },  # Coordinates don't matter due to the mock
    ]
    with pytest.raises(GeoFenceOverlapError):
        validate_all_user_geofences(basic_config)
