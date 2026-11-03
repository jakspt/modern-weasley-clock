from contextlib import AbstractContextManager
from dataclasses import dataclass
from queue import Queue
from typing import Any

from weasley_clock.config import config
from weasley_clock.config.config import LED_RING_LOCATIONS
from weasley_clock.core.models import ConfiguredZone
from weasley_clock.data_layer import MQTTClient
from weasley_clock.presentation_layer.strategies import (
    RenderStrategy,
    create_normal_strategy,
)


@dataclass(frozen=True)
class AppEnvironment:
    zones: dict[str, list[ConfiguredZone]]
    app_settings: dict[str, Any]
    location_provider: AbstractContextManager[Any]
    render_strategy: RenderStrategy


def bootstrap_normal_environment(event_queue: Queue) -> AppEnvironment:
    zones, colours, app_settings = config.load_json()
    normal_render_strategy = create_normal_strategy(
        colours, LED_RING_LOCATIONS, config.get_dimming_factor()
    )
    mqtt_config = config.load_mqtt_credentials()
    mqtt_client = MQTTClient(mqtt_config, event_queue)

    return AppEnvironment(zones, app_settings, mqtt_client, normal_render_strategy)


def bootstrap_demo_environment(event_queue: Queue) -> AppEnvironment:
    from weasley_clock.demo import (
        DEMO_COLOURS,
        DEMO_SETTINGS,
        DEMO_ZONES,
        DemoLocationSimulator,
    )

    normal_render_strategy = create_normal_strategy(
        DEMO_COLOURS, LED_RING_LOCATIONS, config.get_dimming_factor()
    )
    location_provider = DemoLocationSimulator(event_queue)
    return AppEnvironment(
        DEMO_ZONES, DEMO_SETTINGS, location_provider, normal_render_strategy
    )
