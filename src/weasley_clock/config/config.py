import json
import logging
import os
from collections import defaultdict
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from queue import Queue
from typing import TypedDict

from dotenv import load_dotenv

from weasley_clock.config import validate
from weasley_clock.config.validate import (
    ConfigSyntaxError,
    ConfigurationError,
)
from weasley_clock.core.models import (
    ConfiguredZone,
    GeoFence,
    LocationType,
)
from weasley_clock.data_layer.mqtt_client import MQTTConfig
from weasley_clock.presentation_layer.led_driver import LEDDriver, MockDriver
from weasley_clock.presentation_layer.switch import MockPrivacyToggle, PrivacyToggle

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

ENV_PATH = BASE_DIR / ".env"
CONFIG_PATH = BASE_DIR / "config.json"

logger = logging.getLogger(__name__)

# the tuples represent the range of pixels that belong to a location
# with the lower bound inclusive and the upper bound exclusive
LED_RING_LOCATIONS: dict[LocationType, tuple[int, int]] = {
    LocationType.HOME: (0, 12),
    LocationType.WORK_UNI: (12, 24),
    LocationType.LEISURE: (24, 36),
    LocationType.IN_TRANSIT: (36, 48),
    LocationType.MORTAL_PERIL: (48, 60),
}


def _assert_no_led_overlaps():
    all_assigned_leds = [
        led_index
        for lower, upper in LED_RING_LOCATIONS.values()
        for led_index in range(lower, upper)
    ]
    assert len(all_assigned_leds) == len(set(all_assigned_leds)), (
        "LED_RING_LOCATIONS overlap!"
    )


# sanity check:
_assert_no_led_overlaps()


class Fence(TypedDict):
    lat: float
    lon: float
    radius_m: int


class UserConfig(TypedDict):
    tid: str
    color_rgb: list[int]
    geofences: dict[str, list[Fence]]


class PartialConfig(TypedDict):
    users: dict[str, UserConfig]


def load_environment(path: Path = ENV_PATH):
    load_dotenv(dotenv_path=path)


def create_led_driver() -> LEDDriver:
    try:
        import board

        from weasley_clock.presentation_layer.rpi.rpi_led_driver import NeoPixelDriver

        brightness = float(os.getenv("LED_BRIGHTNESS", "0.2"))
        pin_name = os.getenv("LED_PIN", "D18")
        pixel_pin = getattr(board, pin_name, board.D18)  # pyrefly: ignore

        led_driver = NeoPixelDriver(pixel_pin=pixel_pin, brightness=brightness)

        logger.debug(
            f"Created NeoPixel driver with pixel_pin={pixel_pin} and a brightness of {brightness}."
        )

    except (ImportError, NotImplementedError) as e:
        logger.warning(
            "Could not import NeoPixel driver, proceeding with Mock Driver..."
        )
        logger.debug(f"Loading failed because of {repr(e)}")
        led_driver = MockDriver()

    return led_driver


def get_dimming_factor() -> float:
    try:
        return float(os.getenv("DIMMING_FACTOR", "0.15"))
    except ValueError:
        logger.warning("Invalid DIMMING_FACTOR in .env. Falling back to 0.15")
        return 0.15


def create_privacy_toggle(event_queue: Queue) -> PrivacyToggle:
    try:
        import gpiozero

        from weasley_clock.presentation_layer.rpi.rpi_switch import GPIOPrivacyToggle

        # Force gpiozero to check for the existence of a pin factory now
        gpiozero.Device.ensure_pin_factory()

        switch_pin = int(os.getenv("SWITCH_PIN", "4"))

        privacy_toggle = GPIOPrivacyToggle(event_queue, pin=switch_pin)
    except Exception:
        logger.warning(
            "Could not load GPIO Privacy Toggle, proceeding with Mock Toggle..."
        )
        privacy_toggle = MockPrivacyToggle(event_queue)

    return privacy_toggle


def load_json(json_path: Path = CONFIG_PATH):
    try:
        with open(json_path, "r") as config_file:
            config_dict = json.load(config_file)

            validate.config_structure(config_dict)
            validate.tid_uniqueness(config_dict)
            validate.colour_uniqueness(config_dict)
            validate.geofences(config_dict)

            zones = _load_zones(config_dict)
            colours = _load_colours(config_dict)
            app_settings = _load_app_settings(config_dict)

            return zones, colours, app_settings
    except FileNotFoundError:
        raise ConfigurationError(f"config file not found at path {json_path}") from None
    except json.JSONDecodeError as j:
        raise ConfigSyntaxError(f"invalid json syntax: {j}") from None


def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_to_file = os.getenv("LOG_TO_FILE", "False").lower() in ("true", "1", "yes")

    handlers: list[StreamHandler] = [logging.StreamHandler()]

    # Rotating File Handler keeps the Raspberry Pi's SD card from getting full
    if log_to_file:
        file_handler = RotatingFileHandler(
            filename="../weasley_clock.log", maxBytes=5 * 1024 * 1024, backupCount=2
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=handlers,
        force=True,  # override third-party setups
    )
    logging.getLogger("paho.mqtt").setLevel(logging.WARNING)


def load_mqtt_credentials() -> MQTTConfig:
    try:
        host = os.environ["MQTT_HOST"]
        username = os.environ["MQTT_USERNAME"]
        password = os.environ["MQTT_PASSWORD"]
    except KeyError as k:
        raise KeyError(f"Missing required MQTT credential: {k}") from None
    return MQTTConfig(host, username, password)


def _load_zones(config_dict: PartialConfig) -> dict[str, list[ConfiguredZone]]:
    all_zones = defaultdict(list)

    for user in config_dict["users"].values():
        tid = user["tid"]
        for zone_name, zone_content in user["geofences"].items():
            zone_enum = LocationType(zone_name)
            conf_zone = ConfiguredZone(
                zone_enum,
                [
                    GeoFence(fence["lat"], fence["lon"], fence["radius_m"])
                    for fence in zone_content
                ],
            )
            all_zones[tid].append(conf_zone)

    return all_zones


def _load_colours(config_dict: PartialConfig) -> dict[str, tuple[int, int, int]]:
    result: dict[str, tuple[int, int, int]] = {}

    for user in config_dict["users"].values():
        tid = str(user["tid"])
        r, g, b = user["color_rgb"][:3]
        # explicit casting to make the type checker happy
        result[tid] = (int(r), int(g), int(b))

    return result


def _load_app_settings(config_dict: dict) -> dict:
    # app_settings are optional
    app_settings = config_dict.get("app_settings", {})
    if app_settings:
        logger.debug(f"Loaded additional configuration: {app_settings}")

    return app_settings
