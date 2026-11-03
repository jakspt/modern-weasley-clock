from weasley_clock.core.models import ConfiguredZone, LocationType


class LocationResolver:
    def __init__(
        self,
        configured_zones: dict[str, list[ConfiguredZone]],
        battery_threshold: int,
        velocity_threshold: int,
    ):
        self._user_zones = configured_zones
        self._battery_threshold = battery_threshold
        self._velocity_threshold = velocity_threshold

    def match_semantic_location(
        self, tid: str, lat: float, lon: float, velocity: int, battery_pct: int
    ) -> LocationType:

        # return the first matching user-defined zone
        if semantic_location := next(
            (zone.name for zone in self._user_zones[tid] if zone.contains(lat, lon)),
            None,
        ):
            return semantic_location

        # or one of the computed semantic locations

        if battery_pct <= self._battery_threshold:
            return LocationType.MORTAL_PERIL

        if velocity >= self._velocity_threshold:
            return LocationType.IN_TRANSIT

        return LocationType.LEISURE
