from weasley_clock.config import config
from weasley_clock.presentation_layer.strategies import NUMBER_OF_LEDS

CALIBRATION_COLOUR = (255, 0, 255)


def calibrate_led_ring():
    """Lights up each segment's LEDs, one segment at a time.
    Useful for determining which LED ring segment corresponds to which semantic location."""
    led_driver = config.create_led_driver()

    with led_driver:
        print("Calibrating LED ring segments....")
        for location, bounds in config.LED_RING_LOCATIONS.items():
            frame_buffer = [(0, 0, 0)] * NUMBER_OF_LEDS
            for led_index in range(*bounds):
                frame_buffer[led_index] = CALIBRATION_COLOUR
            led_driver.render(frame_buffer)
            input(
                f"Now showing segment {location}, LEDs: {bounds}. Press enter to continue..."
            )
        print("Finished calibrating LED ring segments.")


if __name__ == "__main__":
    calibrate_led_ring()
