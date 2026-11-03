# The Presentation Layer

This module/layer is concerned with interfacing with the "User Interface" which in the case of the Weasley Clock is a hardware switch and a LED ring.

## The PresentationRouter

The `PresentationRouter` manages the process of rendering the system state to the LED ring.

It makes use of the strategy pattern in its `display(system_snapshot)` method to select a `RenderStrategy` which converts the system state to a framebuffer - a list of RGB tuples, one for each LED on the ring.
Under normal circumstances, `normal_strategy` is responsible for rendering the semantic locations to a framebuffer. It does so by iterating over each 12-LED-segment, determining how many users are in it, splitting it appropriately and assigning each user the proportionate amount of slots.
If a user's location is stale, the corresponding RGB values are multiplied by a factor between 0 and 1 (`0.15` per default).
This results in the LEDs dimming, making the "stale" effect appear to the user.

## LEDDriver and PrivacyToggle

The `PresentationRouter` uses the injected `LEDDriver` to push the framebuffer to the LED ring.
Depending on the environment the system is running in, either the real LEDDriver is injected or a mock one is used (for example, if the app is run on any system _except_ the Raspberry Pi).
The mock driver simply outputs the framebuffer to the console for debugging while the `NeoPixelDriver` uses the rpi_ws281x library to control the LED ring.

The PrivacyToggle monitors the GPIO pin the physical toggle is connected to and pushes  a `PrivacyToggleEvent` to the event queue if there is a change.
It acts very similarly to the `MQTTClient` as it also spawns a new thread for listening to external events.
Just like the LEDDriver, the PrivacyToggle is either instantiated as the GPIO version (on the Raspberry Pi) or as a mock version.
For the mock version, the keyboard acts as the switch: "P" activates Privacy Mode while "O" deactivates it.

Both the LEDDriver and PrivacyToggle are Context Managers, which means they support a graceful shutdown even in the case of the system crashing.
This is especially important for the NeoPixelDriver since the LEDs would retain their last known state long after the python application has crashed.
