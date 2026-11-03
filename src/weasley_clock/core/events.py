import logging
import time
from abc import ABC
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class SystemEvent(ABC):
    """Base Class for Events in the System"""


@dataclass(frozen=True)
class LocationUpdateEvent(SystemEvent):
    lat: float
    lon: float
    user_id: str
    timestamp: int  # taken from the received payload, reflects the time the GPS tracker _created_ the message
    battery: int = 100
    velocity: int = 0

    def __post_init__(self):
        if not self.user_id or not str(self.user_id).strip():
            raise ValueError("user_id cannot be empty or just whitespace")
        if not (-90.0 <= self.lat <= 90.0):
            raise ValueError(f"latitude {self.lat} is out of bounds")
        if not (-180.0 <= self.lon <= 180.0):
            raise ValueError(f"longitude {self.lon} is out of bounds")
        if self.timestamp <= 0:
            raise ValueError("timestamp must be a positive integer")
        if self.battery < 0:
            raise ValueError("battery cannot be negative")
        if self.velocity < 0:
            raise ValueError("velocity cannot be negative")


@dataclass(frozen=True)
class MQTTDisconnectEvent(SystemEvent):
    timestamp: float = field(default_factory=time.monotonic)


@dataclass(frozen=True)
class MQTTConnectEvent(SystemEvent):
    pass


@dataclass(frozen=True)
class PrivacyToggleEvent(SystemEvent):
    is_active: bool


@dataclass(frozen=True)
class SystemFatalErrorEvent(SystemEvent):
    reason: str = field(default_factory=str)
