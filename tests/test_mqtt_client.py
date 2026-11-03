# The following test cases are based on GitHub Copilot's suggestions, generated on 04/03/2026,
# which were reviewed, enhanced and corrected by the author.

import json
from typing import cast
from unittest.mock import Mock

import pytest
from paho.mqtt.client import Client

from weasley_clock.core.events import LocationUpdateEvent
from weasley_clock.data_layer.mqtt_client import MQTTClient, MQTTConfig


@pytest.fixture
def dummy_client():
    return cast(Client, Mock(spec=Client))


@pytest.fixture
def mqtt_client(event_queue):
    config = MQTTConfig(
        host="localhost", username="test_user", password="test_password"
    )
    return MQTTClient(config=config, event_queue=event_queue)


def test_on_message_valid_location_is_enqueued(
    event_queue, mock_msg_factory, dummy_client, mqtt_client
):
    valid_data = {
        "_type": "location",
        "lat": 47.2,
        "lon": 17.3,
        "tid": "JA",
        "created_at": 1679659200,
    }
    msg = mock_msg_factory(json.dumps(valid_data).encode())

    # Call the instance method on the mqtt_client, pass None for userdata
    mqtt_client._on_message(dummy_client, None, msg)

    assert event_queue.qsize() == 1
    queued_event = event_queue.get()
    assert isinstance(queued_event, LocationUpdateEvent)
    assert queued_event.user_id == "JA"


def test_on_message_unsupported_type_is_discarded(
    event_queue, mock_msg_factory, dummy_client, mqtt_client
):
    waypoint_data = {"_type": "waypoint", "desc": "Home"}
    msg = mock_msg_factory(json.dumps(waypoint_data).encode())

    mqtt_client._on_message(dummy_client, None, msg)

    assert event_queue.empty()  # Queue should be empty, message was dropped


def test_on_message_invalid_payload_handles_exception_safely(
    event_queue, mock_msg_factory, dummy_client, mqtt_client
):
    # Missing 'lat' and 'lon', which will cause LocationUpdateEvent to raise a ValueError
    invalid_data = {"_type": "location", "tid": "JA"}
    msg = mock_msg_factory(json.dumps(invalid_data).encode())

    # the test passes by not crashing since _on_message catches the exception
    mqtt_client._on_message(dummy_client, None, msg)

    assert event_queue.empty()  # Nothing was queued due to the error


def test_on_message_malformed_json_handles_decode_error(
    event_queue, mock_msg_factory, dummy_client, mqtt_client
):
    msg = mock_msg_factory(b"{this is not valid json}")

    mqtt_client._on_message(dummy_client, None, msg)

    assert event_queue.empty()
