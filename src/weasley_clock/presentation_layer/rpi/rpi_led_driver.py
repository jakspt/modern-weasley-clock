import logging

import board
import neopixel

from weasley_clock.presentation_layer.led_driver import LEDDriver

logger = logging.getLogger(__name__)


class NeoPixelDriver(LEDDriver):
    def __init__(
        self,
        num_pixels: int = 60,
        pixel_pin=board.D18,  # pyrefly: ignore
        brightness: float = 0.5,
    ):

        self.num_pixels = num_pixels
        self.pixel_pin = pixel_pin
        self.brightness = brightness

        self._pixels = None

    def render(self, framebuffer: list[tuple[int, int, int]]) -> None:
        if self._pixels:
            self._pixels[:] = framebuffer
            self._pixels.show()
        else:
            logger.error("NeoPixel LED driver was not initialized!")

    def __enter__(self) -> LEDDriver:
        logger.debug("Starting NeoPixel LED driver...")
        self._pixels = neopixel.NeoPixel(
            self.pixel_pin,
            self.num_pixels,
            brightness=self.brightness,
            auto_write=False,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        if self._pixels:
            logger.debug("Stopping NeoPixel LED driver...")
            self._pixels.fill((0, 0, 0))
            self._pixels.show()
            self._pixels.deinit()
        return False
