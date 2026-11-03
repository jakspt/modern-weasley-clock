from __future__ import annotations

import logging
import queue
from abc import ABC, abstractmethod

# prevents globally importing pynput on the Raspberry Pi which would crash it
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pynput.keyboard import Key, KeyCode

from weasley_clock.core.events import PrivacyToggleEvent

logger = logging.getLogger(__name__)


class PrivacyToggle(ABC):
    def __init__(self, event_queue: queue.Queue):
        self._event_queue = event_queue
        self._is_active = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    def _publish_event(self, is_active: bool):
        if self._is_active != is_active:
            logger.debug(f"Published privacy event: {is_active}")
            self._is_active = is_active
            self._event_queue.put(PrivacyToggleEvent(is_active))

    @abstractmethod
    def start(self): ...

    @abstractmethod
    def stop(self): ...


class MockPrivacyToggle(PrivacyToggle):
    def __init__(self, event_queue):
        super().__init__(event_queue)
        self._listener = None

    def stop(self):
        if self._listener:
            self._listener.stop()
            logger.debug("Mock privacy switch listener stopped")

    def start(self):
        from pynput import keyboard

        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()

    def _on_press(self, key: Key | KeyCode | None):
        char = getattr(key, "char", None)

        if char == "p":
            self._publish_event(True)
            logger.debug("Mock Input: Privacy Mode ON")

        elif char == "o":
            self._publish_event(False)
            logger.debug("Mock Input: Privacy Mode OFF")
