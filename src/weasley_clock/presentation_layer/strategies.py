import logging
from collections import defaultdict
from typing import Protocol

from weasley_clock.core.models import LocationType, UserState

NUMBER_OF_LEDS = 60

logger = logging.getLogger(__name__)
type Colour = tuple[int, int, int]
type User = str


class RenderStrategy(Protocol):
    def __call__(self, user_locations: dict[User, UserState]) -> list[Colour]: ...


def create_normal_strategy(
    colour_map: dict[User, Colour],
    segments: dict[LocationType, tuple[int, int]],
    dimming_factor: float = 0.15,
) -> RenderStrategy:

    def normal_strategy(
        user_locations: dict[User, UserState],
    ) -> list[Colour]:
        # The approach to first group users by locations, then render each of those locations separately
        # was first suggested by GitHub Copilot and subsequently expanded on by the author.
        framebuffer: list[Colour] = [(0, 0, 0)] * NUMBER_OF_LEDS
        users_by_locations: defaultdict[LocationType, list[User]] = (
            _get_users_by_locations(user_locations)
        )
        for location_type, users in users_by_locations.items():
            users_here = len(users)
            assert 1 <= users_here <= 4, (
                f"there should be between 1 and 4 users per location, but there are {users_here}"
            )

            start_index, stop_index = segments[location_type]
            assert stop_index - start_index == 12, (
                f"segment length should be 12, but was {stop_index - start_index}"
            )

            leds_per_user = (stop_index - start_index) // users_here

            # sorting guarantees deterministic ordering
            for i, user in enumerate(sorted(users)):
                user_colour = colour_map[user]
                if user_locations[user].is_stale:
                    user_colour = _dim(user_colour, dimming_factor)

                pixel_start = start_index + (i * leds_per_user)
                pixel_end = pixel_start + leds_per_user

                framebuffer[pixel_start:pixel_end] = [user_colour] * leds_per_user

        return framebuffer

    logger.debug(
        f"Created normal render strategy with a dimming factor of {dimming_factor}"
    )
    return normal_strategy


def _dim(base_colour: Colour, dimming_factor: float):
    return (
        int(base_colour[0] * dimming_factor),
        int(base_colour[1] * dimming_factor),
        int(base_colour[2] * dimming_factor),
    )


def _get_users_by_locations(user_locations: dict[User, UserState]):
    users_by_locations = defaultdict(list)
    for user_id, user_state in user_locations.items():
        location_type = user_state.semantic_location
        users_by_locations[location_type].append(user_id)
    return users_by_locations


def error_strategy(
    user_locations: dict[User, UserState],
) -> list[Colour]:
    error_red = (255, 0, 0)
    return [error_red] * NUMBER_OF_LEDS


def privacy_strategy(
    user_locations: dict[User, UserState],
) -> list[Colour]:
    off = (0, 0, 0)
    return [off] * NUMBER_OF_LEDS
