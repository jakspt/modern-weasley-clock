import time
from unittest.mock import patch

import pytest

from weasley_clock.app_layer.logic import AppLogic
from weasley_clock.core.events import (
    LocationUpdateEvent,
    MQTTConnectEvent,
    MQTTDisconnectEvent,
    PrivacyToggleEvent,
)
from weasley_clock.core.models import LocationType

# The structure of the following unit tests was initially suggested by GitHub Copilot on 04/16/2026
# and subsequently expanded on by the author.


@pytest.fixture
def mock_zones():
    return {"p1": [], "p2": [], "p3": [], "p4": []}


@pytest.fixture
def app_logic(mock_zones):
    with patch("time.monotonic", return_value=1000.0):
        return AppLogic(
            configured_zones=mock_zones, mqtt_timeout=5, staleness_threshold=10
        )


def test_on_privacy_toggle(app_logic):
    # Initially False
    assert app_logic.system_snapshot.is_privacy_active is False

    # Toggle On
    changed = app_logic.on_privacy_toggle(PrivacyToggleEvent(is_active=True))
    assert changed is True
    assert app_logic.system_snapshot.is_privacy_active is True

    # Toggle same state (should return False as no change occurred)
    changed = app_logic.on_privacy_toggle(PrivacyToggleEvent(is_active=True))
    assert changed is False


def test_on_location_update_updates_state(app_logic):
    event = LocationUpdateEvent(
        lat=52.5,
        lon=13.4,
        user_id="p1",
        timestamp=int(time.time()),
        velocity=0,
        battery=100,
    )

    # Mock the internal resolver to return HOME
    with patch.object(
        app_logic._location_resolver, "match_semantic_location"
    ) as mock_resolve:
        mock_resolve.return_value = LocationType.HOME

        changed = app_logic.on_location_update(event)

        assert changed is True
        assert (
            app_logic.system_snapshot.household_state["p1"].semantic_location
            == LocationType.HOME
        )
        assert app_logic.system_snapshot.household_state["p1"].is_stale is False


@patch("time.monotonic")
def test_network_timeout_logic(mock_time, app_logic):
    start_time = 1000.0
    mock_time.return_value = start_time

    app_logic.on_network_disconnect(MQTTDisconnectEvent(timestamp=start_time))

    assert app_logic.perform_housekeeping() is False
    assert app_logic.has_active_error is False

    mock_time.return_value = start_time + 6.0

    assert app_logic.perform_housekeeping() is True
    assert app_logic.has_active_error

    # Reconnect
    system_state_changed = app_logic.on_network_connect(MQTTConnectEvent())
    assert system_state_changed
    assert app_logic.has_active_error is False


@patch("time.time")
@patch("time.monotonic")
def test_location_staleness(mock_monotonic, mock_time, app_logic):
    start_mono = 1000.0
    start_wall = 1719928800.0
    mock_monotonic.return_value = start_mono
    mock_time.return_value = start_wall

    event = LocationUpdateEvent(
        lat=52.5,
        lon=13.4,
        user_id="p1",
        timestamp=int(start_wall),
        velocity=0,
        battery=100,
    )
    with patch.object(
        app_logic._location_resolver,
        "match_semantic_location",
        return_value=LocationType.HOME,
    ):
        app_logic.on_location_update(event)

    # Verify not stale at exactly 1000.0
    app_logic.perform_housekeeping()
    assert app_logic.system_snapshot.household_state["p1"].is_stale is False

    # Fast-forward 11 seconds (threshold is 10)
    mock_monotonic.return_value = start_mono + 11.0

    changed = app_logic.perform_housekeeping()
    assert changed is True
    assert app_logic.system_snapshot.household_state["p1"].is_stale is True


def test_initialization_validation():
    with pytest.raises(ValueError, match="cannot be negative"):
        AppLogic(configured_zones={}, mqtt_timeout=-1)
