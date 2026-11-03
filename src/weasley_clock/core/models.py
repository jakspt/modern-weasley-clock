# define data model here:
import datetime
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List

from geopy.distance import geodesic


@dataclass(frozen=True)
class GeoFence:
    latitude: float
    longitude: float
    radius_m: int

    def __post_init__(self):
        if not self.latitude or not self.longitude or not self.radius_m:
            raise ValueError("latitude, longitude, radius_m must be set")
        if self.radius_m < 0:
            raise ValueError("radius cannot be negative")
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"latitude {self.latitude} is out of bounds")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"longitude {self.longitude} is out of bounds")

    def contains(self, target_lat: float, target_lon: float) -> bool:
        distance = geodesic(
            (self.latitude, self.longitude), (target_lat, target_lon)
        ).meters
        return distance <= self.radius_m


@dataclass(frozen=True)
class ConfiguredZone:
    name: LocationType
    fences: List[GeoFence]

    def __post_init__(self):
        if not self.name or not str(self.name).strip():
            raise ValueError("name cannot be empty")
        if not self.fences:
            raise ValueError("at least one fence must be set")

    def __len__(self) -> int:
        return len(self.fences)

    def contains(self, target_lat: float, target_lon: float) -> bool:
        return any(fence.contains(target_lat, target_lon) for fence in self.fences)


class LocationType(str, Enum):
    HOME = "HOME"
    WORK_UNI = "WORK_UNI"
    IN_TRANSIT = "IN_TRANSIT"
    LEISURE = "LEISURE"
    MORTAL_PERIL = "MORTAL_PERIL"  # aka "low battery"


CONFIGURABLE_LOCATIONS = {LocationType.HOME, LocationType.WORK_UNI}
TRACKER_IDS = ["p1", "p2", "p3", "p4"]


@dataclass
class UserState:
    semantic_location: LocationType = LocationType.LEISURE
    last_updated: float = field(default_factory=time.monotonic, compare=False)
    is_stale: bool = True

    def update_staleness(self, threshold: int) -> bool:
        current_time = time.monotonic()
        time_difference = current_time - self.last_updated
        assert time_difference >= 0

        staleness_status = time_difference > threshold

        if staleness_status != self.is_stale:
            self.is_stale = staleness_status
            return True

        return False


@dataclass(frozen=True)
class ClockSnapshot:
    household_state: dict[str, UserState]
    has_active_error: bool
    is_privacy_active: bool

    def __post_init__(self):
        if not self.household_state:
            raise ValueError("household_state cannot be None")
