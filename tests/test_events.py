# The following test cases are based on GitHub Copilot's suggestions, generated on 04/03/2026,
# which were reviewed, enhanced and corrected by the author.

import pytest
from weasley_clock.core.events import LocationUpdateEvent


def test_location_event_valid_data_creates_instance():
    event = LocationUpdateEvent(lat=47.2, lon=17.3, user_id="JA", timestamp=123456)

    assert event.lat == 47.2
    assert event.lon == 17.3
    assert event.user_id == "JA"
    assert event.timestamp == 123456


@pytest.mark.parametrize(
    "invalid_arguments",
    [
        dict(lat=999.0, lon=17.3, user_id="JA", timestamp=123456),
        dict(lat=50.0, lon=999, user_id="JA", timestamp=123456),
        dict(lat=50.0, lon=52.3, user_id=" ", timestamp=123456),
        dict(lat=50.0, lon=52.3, user_id="", timestamp=123456),
        dict(lat=50.0, lon=52.3, user_id="JA", timestamp=-1),
    ],
)
def test_location_event_invalid_arguments_raises_value_error(invalid_arguments):
    with pytest.raises(ValueError):
        LocationUpdateEvent(**invalid_arguments)
