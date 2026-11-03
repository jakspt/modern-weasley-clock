import logging
import time
from dataclasses import dataclass
from typing import Optional

from weasley_clock.app_layer.geofencing import LocationResolver
from weasley_clock.core.events import (
    LocationUpdateEvent,
    MQTTConnectEvent,
    MQTTDisconnectEvent,
    PrivacyToggleEvent,
    SystemFatalErrorEvent,
)
from weasley_clock.core.models import (
    ClockSnapshot,
    ConfiguredZone,
    UserState,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MessageTiming:
    last_updated: float
    is_stale: bool


class AppLogic:
    def __init__(
        self,
        configured_zones: dict[str, list[ConfiguredZone]],
        mqtt_timeout: int = 600,
        staleness_threshold: int = 1200,
        battery_threshold: int = 15,
        velocity_threshold: int = 15,
    ):
        if any(
            [
                battery_threshold < 0,
                velocity_threshold < 0,
                staleness_threshold < 0,
                mqtt_timeout < 0,
            ]
        ):
            raise ValueError("timeouts and thresholds cannot be negative")
        self._location_resolver = LocationResolver(
            configured_zones, battery_threshold, velocity_threshold
        )
        # -inf guarantees stale states even directly after the system booted
        self._household_state: dict[str, UserState] = {
            tid: UserState(last_updated=float("-inf"))
            for tid in configured_zones.keys()
        }
        self._mqtt_timeout = mqtt_timeout
        self._staleness_threshold = staleness_threshold
        self._has_terminal_error = False
        self._is_network_timed_out = False
        self._privacy_active = False
        self._mqtt_disconnect_timestamp: Optional[float] = None

    @property
    def system_snapshot(self) -> ClockSnapshot:
        return ClockSnapshot(
            household_state=self._household_state.copy(),
            has_active_error=self.has_active_error,
            is_privacy_active=self._privacy_active,
        )

    @property
    def has_active_error(self) -> bool:
        return self._has_terminal_error or self._is_network_timed_out

    def perform_housekeeping(self) -> bool:
        """Check for mqtt connection timeouts and update user location staleness. Return whether the system state changed (meaning a UI re-render is necessary)"""
        logger.debug("Performing housekeeping...")
        system_health_changed = self._process_network_timeout()
        staleness_changed = self._update_location_staleness()
        change_occurred = system_health_changed or staleness_changed

        if change_occurred:
            logger.debug(
                f"System state changed, system state is now: {self.system_snapshot}"
            )

        return change_occurred

    def _process_network_timeout(self) -> bool:
        """Evaluate if the network connection has timed out, update internal state and return whether the state was changed"""
        current_time = time.monotonic()
        network_was_timed_out = self._is_network_timed_out

        if self._mqtt_disconnect_timestamp:
            disconnect_duration = current_time - self._mqtt_disconnect_timestamp
            assert disconnect_duration >= 0, (
                "disconnect duration should not be negative"
            )

            if disconnect_duration > self._mqtt_timeout:
                self._is_network_timed_out = True
        else:
            self._is_network_timed_out = False

        return network_was_timed_out != self._is_network_timed_out

    def _update_location_staleness(self) -> bool:
        """Update each user state's staleness and return whether any of them have changed."""
        return any(
            [
                user_state.update_staleness(self._staleness_threshold)
                for user_state in self._household_state.values()
            ]
        )

    def on_network_connect(self, event: MQTTConnectEvent):
        """Process a network connect event and return whether it changed the system state, making a UI re-render necessary"""
        logger.debug("Connected to network.")
        self._mqtt_disconnect_timestamp = None
        return self._process_network_timeout()

    def on_network_disconnect(self, event: MQTTDisconnectEvent):
        logger.warning(f"Network disconnected: {event}")
        self._mqtt_disconnect_timestamp = event.timestamp

    def on_location_update(self, location_update: LocationUpdateEvent) -> bool:
        """Update the semantic locations of the users and return whether any of them have changed."""

        tid = location_update.user_id
        semantic_location = self._location_resolver.match_semantic_location(
            tid,
            location_update.lat,
            location_update.lon,
            location_update.velocity,
            location_update.battery,
        )

        timing = self._parse_message_timing(location_update.timestamp)

        current_state = self._household_state[tid]
        new_state = UserState(
            semantic_location,
            is_stale=timing.is_stale,
            last_updated=timing.last_updated,
        )

        state_changed = current_state != new_state
        self._household_state[tid] = new_state

        logger.debug(f"Updated semantic location for {tid}: {semantic_location}")

        return state_changed

    def _parse_message_timing(self, message_timestamp: int) -> MessageTiming:
        """
        Parse the LocationUpdateEvent's timestamp to check when the last update happened and whether the update is already stale.
        This is necessary since the system uses time.monotonic() internally
        """
        current_wall = time.time()
        current_mono = time.monotonic()
        # prevent negative age
        message_age = max(0.0, current_wall - message_timestamp)

        return MessageTiming(
            last_updated=current_mono - message_age,
            is_stale=message_age > self._staleness_threshold,
        )

    def on_privacy_toggle(self, event: PrivacyToggleEvent):
        """Update the privacy state of the system and return whether it changed"""

        if self._privacy_active != event.is_active:
            self._privacy_active = event.is_active
            logger.debug(f"Privacy status changed, is now {self._privacy_active}")
            return True

        return False

    def on_fatal_error(self, event: SystemFatalErrorEvent):
        """Process a fatal error. Returns whether the internal state changed / whether this is the first fatal error the system encountered"""
        logger.critical(f"Fatal error: {event.reason}")

        if not self._has_terminal_error:
            self._has_terminal_error = True
            return True

        return False
