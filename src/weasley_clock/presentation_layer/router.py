import logging
from typing import Optional

from weasley_clock.core.models import ClockSnapshot, UserState
from weasley_clock.presentation_layer.led_driver import LEDDriver
from weasley_clock.presentation_layer.strategies import RenderStrategy

logger = logging.getLogger(__name__)


class PresentationRouter:
    def __init__(
        self,
        led_driver: LEDDriver,
        error_strategy: RenderStrategy,
        privacy_strategy: RenderStrategy,
        normal_strategy: Optional[RenderStrategy] = None,
    ):
        self._led_driver = led_driver
        self._error_strategy = error_strategy
        self._privacy_strategy = privacy_strategy
        if normal_strategy:
            self._normal_strategy = normal_strategy

    def display(self, system_snapshot: ClockSnapshot) -> None:

        if not self._normal_strategy:
            logger.critical("Normal render strategy not initialized!")
            self.display_fatal_error()
            return
        elif system_snapshot.has_active_error:
            strategy_to_use = self._error_strategy
        elif system_snapshot.is_privacy_active:
            strategy_to_use = self._privacy_strategy
        else:
            strategy_to_use = self._normal_strategy

        framebuffer = strategy_to_use(system_snapshot.household_state)
        self._led_driver.render(framebuffer)

    def set_normal_strategy(self, normal_strategy: RenderStrategy):
        logger.info("Normal render strategy set.")
        self._normal_strategy = normal_strategy

    def display_fatal_error(self):
        """Convenience method to display errors that happen before the system is initialized."""
        unknown_state = {"": UserState()}
        framebuffer = self._error_strategy(unknown_state)
        self._led_driver.render(framebuffer)
