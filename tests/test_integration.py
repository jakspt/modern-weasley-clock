import queue
import time
from unittest.mock import MagicMock

import pytest

from weasley_clock.core.events import LocationUpdateEvent
from weasley_clock.core.models import (
    ConfiguredZone,
    GeoFence,
    LocationType,
)
from weasley_clock.orchestration.controller import AppController
from weasley_clock.presentation_layer.router import PresentationRouter

# The following test cases are based on GitHub Copilot's suggestions, generated on 05/09/2026,
# which were reviewed, enhanced and corrected by the author.


@pytest.fixture
def mock_presenter():

    return MagicMock(spec=PresentationRouter)


@pytest.fixture
def test_zones() -> dict[str, list[ConfiguredZone]]:
    return {
        "p1": [
            ConfiguredZone(
                LocationType.HOME,
                [GeoFence(latitude=48.208200, longitude=16.3738, radius_m=50)],
            ),
            ConfiguredZone(
                name=LocationType.WORK_UNI,
                fences=[GeoFence(latitude=48.209100, longitude=16.3738, radius_m=50)],
            ),
        ]
    }


@pytest.mark.parametrize(
    "lat, lon, expected_location",
    [
        (48.208200, 16.373800, LocationType.HOME),
        (48.207840, 16.373800, LocationType.HOME),
        (48.209100, 16.373800, LocationType.WORK_UNI),
        (48.209460, 16.373800, LocationType.WORK_UNI),
        (
            48.208650,
            16.374000,
            LocationType.LEISURE,
        ),
        (
            48.208200,
            16.374610,
            LocationType.LEISURE,
        ),
    ],
)
def test_location_updates_display(
    test_zones, mock_presenter, lat, lon, expected_location
):
    event_queue = MagicMock(spec=queue.Queue)
    controller = AppController(test_zones, mock_presenter, event_queue)

    test_event = LocationUpdateEvent(
        lat=lat, lon=lon, user_id="p1", timestamp=time.time_ns()
    )

    # 1st loop: Process the event. 2nd loop: Kill the test.
    event_queue.get.side_effect = [test_event, KeyboardInterrupt("Stop Loop")]

    try:
        controller.run()
    except KeyboardInterrupt as e:
        assert str(e) == "Stop Loop"

    # Verify the queue was managed correctly
    event_queue.task_done.assert_called_once()
    # Verify the presenter was triggered
    mock_presenter.display.assert_called_once()
    # Inspect the snapshot to ensure the location logic resolved correctly
    sent_snapshot = mock_presenter.display.call_args[0][0]
    assert sent_snapshot.household_state["p1"].semantic_location == expected_location


@pytest.mark.parametrize(
    "lat, lon, expected_location",
    [
        (48.208200, 16.373800, LocationType.HOME),
        (48.207840, 16.373800, LocationType.HOME),
        (48.209100, 16.373800, LocationType.WORK_UNI),
        (48.209460, 16.373800, LocationType.WORK_UNI),
        (
            48.208650,
            16.374000,
            LocationType.LEISURE,
        ),
        (
            48.208200,
            16.374610,
            LocationType.LEISURE,
        ),
    ],
)
def test_alternate_id_location_updates_display(
    test_zones, mock_presenter, lat, lon, expected_location
):
    event_queue = MagicMock(spec=queue.Queue)
    test_zones = {
        "px": [
            ConfiguredZone(
                LocationType.HOME,
                [GeoFence(latitude=48.208200, longitude=16.3738, radius_m=50)],
            ),
            ConfiguredZone(
                name=LocationType.WORK_UNI,
                fences=[GeoFence(latitude=48.209100, longitude=16.3738, radius_m=50)],
            ),
        ]
    }
    controller = AppController(test_zones, mock_presenter, event_queue)

    test_event = LocationUpdateEvent(
        lat=lat, lon=lon, user_id="px", timestamp=time.time_ns()
    )

    # 1st loop: Process the event. 2nd loop: Kill the test.
    event_queue.get.side_effect = [test_event, KeyboardInterrupt("Stop Loop")]

    try:
        controller.run()
    except KeyboardInterrupt as e:
        assert str(e) == "Stop Loop"

    event_queue.task_done.assert_called_once()
    mock_presenter.display.assert_called_once()

    sent_snapshot = mock_presenter.display.call_args[0][0]
    assert sent_snapshot.household_state["px"].semantic_location == expected_location
