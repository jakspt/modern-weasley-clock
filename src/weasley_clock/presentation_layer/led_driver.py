import logging
from typing import Protocol

from rich.console import Console
from rich.text import Text

logger = logging.getLogger(__name__)


class LEDDriver(Protocol):
    def render(self, framebuffer: list[tuple[int, int, int]]) -> None: ...
    def __enter__(self) -> LEDDriver: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None: ...


class MockDriver(LEDDriver):
    def __init__(self):
        self._console = Console(force_terminal=True, color_system="truecolor")

    def render(self, framebuffer: list[tuple[int, int, int]]) -> None:

        led_strip = Text()

        # The following "boosting" logic was suggested by GitHub Copilot on 04/18/2026 and subsequently
        # reviewed and extended by the author
        for r, g, b in framebuffer:
            # "boost" the shown color if the corresponding value is too low to show up on the terminal
            disp_r = max(r, 50) if r > 0 else 0
            disp_g = max(g, 50) if g > 0 else 0
            disp_b = max(b, 50) if b > 0 else 0

            led_strip.append("⬤ ", style=f"rgb({disp_r},{disp_g},{disp_b})")

        self._console.print(led_strip)
        # self._console.print(framebuffer)

    def __enter__(self) -> LEDDriver:
        logger.debug("Starting Mock LED driver...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        logger.debug("Stopping Mock LED driver...")
        return False
