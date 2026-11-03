import enum
import logging
import random
import threading
import time
from dataclasses import astuple
from enum import Enum
from queue import Queue
from typing import Literal

from weasley_clock.core.events import (
    LocationUpdateEvent,
    MQTTConnectEvent,
    MQTTDisconnectEvent,
)
from weasley_clock.core.models import ConfiguredZone, GeoFence, LocationType

logger = logging.getLogger(__name__)

HOME_LAT = 51.5194
HOME_LON = -0.1270
HOME_RADIUS = 100


def _create_configured_zone(
    location: Literal[LocationType.HOME] | Literal[LocationType.WORK_UNI],
    lat: float,
    lon: float,
    radius_m: int,
):
    return ConfiguredZone(location, [GeoFence(lat, lon, radius_m)])


DEMO_ZONES = {
    "Molly": [
        _create_configured_zone(LocationType.HOME, HOME_LAT, HOME_LON, HOME_RADIUS),
        _create_configured_zone(LocationType.WORK_UNI, 51.5246, -0.1340, 200),
    ],
    "Arthur": [
        _create_configured_zone(LocationType.HOME, HOME_LAT, HOME_LON, HOME_RADIUS),
        _create_configured_zone(LocationType.WORK_UNI, 51.5115, -0.1160, 150),
    ],
    "Ron": [
        _create_configured_zone(LocationType.HOME, HOME_LAT, HOME_LON, HOME_RADIUS),
        _create_configured_zone(LocationType.WORK_UNI, 51.4988, -0.1749, 250),
    ],
    "Ginny": [
        _create_configured_zone(LocationType.HOME, HOME_LAT, HOME_LON, HOME_RADIUS),
        _create_configured_zone(LocationType.WORK_UNI, 51.5333, -0.1261, 150),
    ],
}
DEMO_COLOURS: dict[str, tuple[int, int, int]] = {
    "Molly": (0, 255, 255),
    "Arthur": (255, 0, 255),
    "Ron": (0, 255, 0),
    "Ginny": (255, 100, 0),
}
# units are seconds here
DEMO_SETTINGS = {"staleness_threshold": 20, "mqtt_timeout": 2}


def _choose_coordinates() -> tuple[float, float]:
    chosen_member = random.choice(list(DEMO_ZONES.keys()))
    chosen_zone = random.choice(DEMO_ZONES[chosen_member])
    first_fence = chosen_zone.fences[0]
    lat, lon, _ = astuple(first_fence)
    return lat, lon


class ConnectionState(Enum):
    CONNECTED = enum.auto()
    DISCONNECTED = enum.auto()


class DemoLocationSimulator:
    def __init__(self, event_queue: Queue):
        self.event_queue = event_queue
        self.stop_event = threading.Event()
        self._thread = None
        self.connection_state = ConnectionState.CONNECTED

    def __enter__(self):
        self._thread = threading.Thread(target=self._run_simulation, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)
        logger.debug("Stopping simulation...")
        # don't suppress exceptions
        return False

    def _run_simulation(self):
        family_members = list(DEMO_ZONES.keys())

        skip_update_probability = 0.2
        disconnect_probability = 0.05
        reconnect_probability = 0.5

        while not self.stop_event.is_set():
            assert (
                self.connection_state == ConnectionState.CONNECTED
                or self.connection_state == ConnectionState.DISCONNECTED
            )

            if self.connection_state == ConnectionState.CONNECTED:
                if not random.random() < skip_update_probability:
                    self._post_location_update(family_members)
                if random.random() < disconnect_probability:
                    self._disconnect()
            elif self.connection_state == ConnectionState.DISCONNECTED:
                if random.random() < reconnect_probability:
                    self._reconnect()

            time.sleep(random.uniform(5, 25))

    def _reconnect(self):
        self.event_queue.put(MQTTConnectEvent())
        self.connection_state = ConnectionState.CONNECTED

    def _disconnect(self):
        self.event_queue.put(MQTTDisconnectEvent())
        self.connection_state = ConnectionState.DISCONNECTED

    def _post_location_update(self, family_members: list[str]):
        chosen_member = random.choice(family_members)
        lat, lon = _choose_coordinates()
        battery_percentage = random.randint(1, 100)
        velocity = random.choice([0, 50])
        event = LocationUpdateEvent(
            lat,
            lon,
            chosen_member,
            time.time_ns(),
            battery_percentage,
            velocity,
        )
        self.event_queue.put(event)
        logger.debug(f"Published Event {event}")
