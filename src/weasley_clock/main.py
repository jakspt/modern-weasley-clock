import argparse
import logging
import queue
import signal
import time

from weasley_clock.config import config
from weasley_clock.orchestration.bootstrap import (
    bootstrap_demo_environment,
    bootstrap_normal_environment,
)
from weasley_clock.orchestration.controller import AppController
from weasley_clock.presentation_layer.router import PresentationRouter
from weasley_clock.presentation_layer.strategies import (
    error_strategy,
    privacy_strategy,
)

logger = logging.getLogger(__name__)


def main():
    if is_demo():
        bootstrap_environment = bootstrap_demo_environment
    else:
        bootstrap_environment = bootstrap_normal_environment
    try:
        configure_exit_signal_handling()
        config.load_environment()
        config.setup_logging()
        led_driver = config.create_led_driver()
        presenter = PresentationRouter(led_driver, error_strategy, privacy_strategy)
        with led_driver:
            try:
                event_queue = queue.Queue()
                env = bootstrap_environment(event_queue)
                presenter.set_normal_strategy(env.render_strategy)
                privacy_toggle = config.create_privacy_toggle(event_queue)
            except Exception as e:
                logger.exception(f"Fatal startup error: {e}")
                presenter.display_fatal_error()
                while True:
                    time.sleep(60)
            else:
                location_provider = env.location_provider
                controller = AppController(
                    env.zones, presenter, event_queue, **env.app_settings
                )
                with location_provider, privacy_toggle:
                    logger.info("Starting Weasley Clock...")
                    controller.run()
    except Exception as e:
        logger.exception(f"Application crashed: {e}")
    except KeyboardInterrupt:
        logger.info("Shutting down...")


def is_demo() -> bool:
    parser = argparse.ArgumentParser(description="Run the Weasley Clock.")
    parser.add_argument(
        "--demo", action="store_true", help="Run in demo mode with mock data"
    )
    return parser.parse_args().demo


def handle_exit_signal(signum, frame):
    """Translates system termination signals into a KeyboardInterrupt"""
    raise KeyboardInterrupt()


def configure_exit_signal_handling():
    signal.signal(signal.SIGTERM, handle_exit_signal)
    if hasattr(signal, "SIGHUP"):  # Windows has no SIGHUP signal, for example
        signal.signal(signal.SIGHUP, handle_exit_signal)


if __name__ == "__main__":
    main()

# The initial idea to use a message queuing structure to solve thread synchronization issues was
# proposed by GitHub Copilot and subsequently expanded on and implemented by the author.
