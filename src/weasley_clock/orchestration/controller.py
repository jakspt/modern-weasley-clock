import logging
import queue
from queue import Queue

from weasley_clock.app_layer.logic import AppLogic
from weasley_clock.core.events import (
    LocationUpdateEvent,
    MQTTConnectEvent,
    MQTTDisconnectEvent,
    PrivacyToggleEvent,
    SystemFatalErrorEvent,
)
from weasley_clock.presentation_layer.router import PresentationRouter

logger = logging.getLogger(__name__)


class AppController:
    def __init__(
        self,
        zones,
        presenter: PresentationRouter,
        event_queue: Queue,
        **app_settings,
    ):
        if not all([zones, presenter, event_queue]):
            raise ValueError("arguments must not be None")
        self._app_logic = AppLogic(zones, **app_settings)
        self._presenter = presenter
        self._event_queue = event_queue

    def run(self):
        while True:
            ui_update_necessary = False
            event = None
            try:
                event = self._event_queue.get(timeout=10)
                ui_update_necessary = self._dispatch_event(event)
            except queue.Empty:
                ui_update_necessary = self._perform_housekeeping()
            except Exception as e:
                logger.exception(f"Error processing event {type(event).__name__}: {e}")
                ui_update_necessary = self._handle_fatal_error(e)
            finally:
                if event is not None:
                    self._event_queue.task_done()
                if ui_update_necessary:
                    self._update_ui()

    def _dispatch_event(self, event) -> bool:
        """Routes the event to the appropriate handler and returns True if the UI needs to be updated."""
        ui_update_necessary = False
        match event:
            case LocationUpdateEvent():
                ui_update_necessary = self._app_logic.on_location_update(event)
            case MQTTConnectEvent():
                ui_update_necessary = self._app_logic.on_network_connect(event)
            case MQTTDisconnectEvent():
                self._app_logic.on_network_disconnect(event)
            case PrivacyToggleEvent():
                ui_update_necessary = self._app_logic.on_privacy_toggle(event)
            case SystemFatalErrorEvent():
                ui_update_necessary = self._app_logic.on_fatal_error(event)
            case _:
                raise ValueError(f"Unknown event: {event}")
        return ui_update_necessary

    def _perform_housekeeping(self) -> bool:
        # for stale data and connection timeouts
        try:
            return self._app_logic.perform_housekeeping()
        except Exception as e:
            logger.error(f"Housekeeping failed: {e}")
            return self._handle_fatal_error(e)

    def _handle_fatal_error(self, e: Exception) -> bool:
        try:
            return self._app_logic.on_fatal_error(SystemFatalErrorEvent(str(e)))
        except Exception as ex:
            logger.critical(f"Failed to even process fatal error: {ex}")
            return False

    def _update_ui(self):
        try:
            snapshot = self._app_logic.system_snapshot
            self._presenter.display(snapshot)
        except Exception as e:
            logger.critical(f"Failed to update LED ring!: {e}")
            # if the error cannot be displayed on the hardware, keeping the loop running is pointless
            raise RuntimeError("Fatal display failure") from e
