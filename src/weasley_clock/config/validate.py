import itertools

from geopy.distance import distance
from jsonschema import ValidationError as JsonSchemaError
from jsonschema import validate

from weasley_clock.core.models import CONFIGURABLE_LOCATIONS, TRACKER_IDS


class ConfigurationError(Exception):
    """Raised when the configuration file is invalid"""


class ConfigSyntaxError(ConfigurationError):
    """Raised when the JSON file contains invalid syntax."""


class ConfigNotFoundError(ConfigurationError):
    """Raised when the configuration file is not found."""


class ConfigSchemaError(ConfigurationError):
    """Raised when the is valid but violates the schema (e.g., missing keys, values out of range, etc.)."""


class DuplicateTrackerIdError(ConfigurationError):
    """Raised when two users have the same tracker id (tid)."""


class DuplicateColourError(ConfigurationError):
    """Raised when two users have the same color (color_rgb)."""


class GeoFenceOverlapError(ConfigurationError):
    """Raised when user-defined geofences overlap."""


NUMBER_OF_USERS = len(TRACKER_IDS)
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["users"],
    "properties": {
        "users": {
            "type": "object",
            "minProperties": NUMBER_OF_USERS,
            "maxProperties": NUMBER_OF_USERS,
            "patternProperties": {
                "^.*$": {
                    "type": "object",
                    "required": ["tid", "color_rgb", "geofences"],
                    "properties": {
                        "tid": {"type": "string", "enum": TRACKER_IDS},
                        "color_rgb": {
                            "type": "array",
                            "minItems": 3,
                            "maxItems": 3,
                            "items": {"type": "integer", "minimum": 0, "maximum": 255},
                        },
                        "geofences": {
                            "type": "object",
                            "required": [
                                location.value for location in CONFIGURABLE_LOCATIONS
                            ],
                            "patternProperties": {
                                "^.*$": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                        "type": "object",
                                        "required": ["lat", "lon", "radius_m"],
                                        "properties": {
                                            "lat": {
                                                "type": "number",
                                                "minimum": -90.0,
                                                "maximum": 90.0,
                                            },
                                            "lon": {
                                                "type": "number",
                                                "minimum": -180.0,
                                                "maximum": 180.0,
                                            },
                                            "radius_m": {
                                                "type": "number",
                                                "exclusiveMinimum": 0,  # radius must be strictly greater than 0
                                            },
                                        },
                                    },
                                }
                            },
                        },
                    },
                }
            },
        },
        "app_settings": {
            "type": "object",
            "properties": {
                "mqtt_timeout": {"type": "integer", "minimum": 0},
                "staleness_threshold": {"type": "integer", "minimum": 0},
                "battery_threshold": {"type": "integer", "minimum": 0, "maximum": 100},
                "velocity_threshold": {"type": "integer", "minimum": 0},
            },
        },
    },
}


def config_structure(config_dict):
    # validate everything the schema can validate
    try:
        validate(instance=config_dict, schema=CONFIG_SCHEMA)
    except JsonSchemaError as e:
        # This user-friendly way of formatting the error message was provided by GitHub Copilot on 04/09/2026
        # and subsequently tested and extended by the author
        if e.path:
            path_string = " -> ".join([str(p) for p in e.path])
        else:
            path_string = "Root Configuration"

        friendly_error = f"Invalid configuration at [{path_string}]: {e.message}"

        raise ConfigSchemaError(friendly_error) from None


def tid_uniqueness(config_dict):
    all_tids = [user["tid"] for user in config_dict["users"].values()]
    unique_tids = set(all_tids)

    unique_tid_count = len(unique_tids)
    actual_tid_count = len(all_tids)

    if unique_tid_count != actual_tid_count:
        raise DuplicateTrackerIdError(f"duplicate tracker ids detected: {all_tids}")


def geofences(config_dict):
    """Validates all geofence configurations for errors and overlaps."""
    configured_zones_list = [
        username["geofences"] for username in config_dict["users"].values()
    ]
    for configured_zones in configured_zones_list:
        _validate_user_zones(configured_zones)


def _validate_user_zones(
    configured_zones: dict[str, list[dict[str, float | int]]],
):
    """
    Check a user's defined zones for overlaps between them.
    Note that overlaps *within* a zone (e.g., HOME: [{"lat": a, "lon": b, radius_m: 50}, {"lat": a, "lon": b, "radius_m": 100}] are perfectly
    valid, but overlaps *between* zones (e.g., HOME: [{"lat": a, "lon": b, radius_m: 50}], WORK: [{"lat": a, "lon": b, "radius_m": 100}]) are not.
    """

    zone_names = list(configured_zones.keys())
    # check zones pairwise
    for zone_a_name, zone_b_name in itertools.combinations(zone_names, 2):
        zone_a = configured_zones[zone_a_name]
        zone_b = configured_zones[zone_b_name]

        for fence_a in zone_a:
            for fence_b in zone_b:
                if _are_geofences_overlapping(fence_a, fence_b):
                    raise GeoFenceOverlapError(
                        f"the geofences {fence_a} (for {zone_a_name}) and {fence_b} (for {zone_b_name}) overlap"
                    )


def _are_geofences_overlapping(first_fence: dict, second_fence: dict) -> bool:
    """Determines whether two geofences overlap.
    This is the case if the distance between their centers is smaller than or equal to the sum of their radii.
    In the (rare) case of two geofences intersecting at exactly one point, the fences are also considered to overlap.
    """
    coords_a = (first_fence["lat"], first_fence["lon"])
    coords_b = (second_fence["lat"], second_fence["lon"])

    center_distance = distance(coords_a, coords_b).meters
    sum_of_radii = first_fence["radius_m"] + second_fence["radius_m"]

    return center_distance <= sum_of_radii


def colour_uniqueness(config_dict: dict):
    all_colours = [tuple(user["color_rgb"]) for user in config_dict["users"].values()]

    if len(all_colours) != len(set(all_colours)):
        raise DuplicateColourError(f"duplicate colours detected: {all_colours}")
