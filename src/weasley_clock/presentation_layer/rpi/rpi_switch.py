import logging
import queue
import time
from typing import Optional

from gpiozero import Button as ToggleSwitch

from weasley_clock.presentation_layer.switch import PrivacyToggle

logger = logging.getLogger(__name__)


class GPIOPrivacyToggle(PrivacyToggle):
    def __init__(self, event_queue: queue.Queue, pin: int = 4, pull_up: bool = True):
        super().__init__(event_queue)
        self._pin = pin
        self._pull_up = pull_up
        self._switch: Optional[ToggleSwitch] = None

    def start(self):
        self._switch = ToggleSwitch(self._pin, pull_up=self._pull_up, bounce_time=0.2)
        assert self._switch is not None
        logger.info("Starting GPIO privacy switch listener...")
        time.sleep(0.1)  # give the software time to setup the internal pull-up resistor
        self._publish_event(self._switch.is_active)

        self._switch.when_pressed = lambda: self._publish_event(True)
        self._switch.when_released = lambda: self._publish_event(False)

    def stop(self):
        if self._switch:
            self._switch.close()
            self._switch = None
            logger.info("Stopped GPIO privacy switch listener...")
