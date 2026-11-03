import pytest

from weasley_clock.config.config import LED_RING_LOCATIONS, _load_colours
from weasley_clock.core.models import LocationType, UserState
from weasley_clock.presentation_layer.strategies import (
    create_normal_strategy,
)

DIMMING_FACTOR = 0.15


@pytest.fixture
def colour_map(basic_config):
    return _load_colours(basic_config)


@pytest.fixture
def normal_strategy(colour_map):
    return create_normal_strategy(colour_map, LED_RING_LOCATIONS)


@pytest.fixture
def user_colours(colour_map):
    return [colour_map[f"p{i}"] for i in range(1, 5)]


OFF = (0, 0, 0)


def test_each_person_different_location(normal_strategy, user_colours):
    user_states: dict[str, UserState] = {
        "p1": UserState(semantic_location=LocationType.HOME, is_stale=False),
        "p2": UserState(semantic_location=LocationType.LEISURE, is_stale=False),
        "p3": UserState(semantic_location=LocationType.MORTAL_PERIL, is_stale=False),
        "p4": UserState(semantic_location=LocationType.WORK_UNI, is_stale=False),
    }
    framebuffer = normal_strategy(user_states)
    c1, c2, c3, c4 = user_colours
    expected_framebuffer = (
        [c1] * 12  # home
        + [c4] * 12  # work
        + [c2] * 12  # leisure
        + [OFF] * 12  # transit
        + [c3] * 12  # peril
    )
    assert framebuffer == expected_framebuffer


def test_two_people_same_location(normal_strategy, user_colours):
    user_states: dict[str, UserState] = {
        "p1": UserState(semantic_location=LocationType.HOME, is_stale=False),
        "p2": UserState(semantic_location=LocationType.HOME, is_stale=False),
        "p3": UserState(semantic_location=LocationType.MORTAL_PERIL, is_stale=False),
        "p4": UserState(semantic_location=LocationType.WORK_UNI, is_stale=False),
    }
    framebuffer = normal_strategy(user_states)
    c1, c2, c3, c4 = user_colours
    expected_framebuffer = (
        [c1] * 6  # home
        + [c2] * 6
        + [c4] * 12  # work
        + [OFF] * 12  # leisure
        + [OFF] * 12  # transit
        + [c3] * 12  # peril
    )
    assert framebuffer == expected_framebuffer


def test_three_people_same_location(normal_strategy, user_colours):
    user_states: dict[str, UserState] = {
        "p1": UserState(semantic_location=LocationType.HOME, is_stale=False),
        "p2": UserState(semantic_location=LocationType.HOME, is_stale=False),
        "p3": UserState(semantic_location=LocationType.HOME, is_stale=False),
        "p4": UserState(semantic_location=LocationType.WORK_UNI, is_stale=False),
    }
    framebuffer = normal_strategy(user_states)
    c1, c2, c3, c4 = user_colours
    expected_framebuffer = (
        [c1] * 4  # home
        + [c2] * 4
        + [c3] * 4
        + [c4] * 12  # work
        + [OFF] * 12  # leisure
        + [OFF] * 12  # transit
        + [OFF] * 12  # peril
    )
    assert framebuffer == expected_framebuffer


def test_four_people_same_location(normal_strategy, user_colours):
    user_states: dict[str, UserState] = {
        "p1": UserState(semantic_location=LocationType.HOME, is_stale=False),
        "p2": UserState(semantic_location=LocationType.HOME, is_stale=False),
        "p3": UserState(semantic_location=LocationType.HOME, is_stale=False),
        "p4": UserState(semantic_location=LocationType.HOME, is_stale=False),
    }
    framebuffer = normal_strategy(user_states)
    c1, c2, c3, c4 = user_colours
    expected_framebuffer = (
        [c1] * 3  # home
        + [c2] * 3
        + [c3] * 3
        + [c4] * 3
        + [OFF] * 12  # work
        + [OFF] * 12  # leisure
        + [OFF] * 12  # transit
        + [OFF] * 12  # peril
    )
    assert framebuffer == expected_framebuffer


def test_stale_user_state_dimmed_render(normal_strategy, colour_map):
    user_states = {
        "p1": UserState(semantic_location=LocationType.IN_TRANSIT, is_stale=True),
    }
    framebuffer = normal_strategy(user_states)

    dimmed_colour = tuple(int(c * DIMMING_FACTOR) for c in colour_map["p1"])

    expected_framebuffer = [OFF] * 36 + [dimmed_colour] * 12 + [OFF] * 12
    assert framebuffer == expected_framebuffer
