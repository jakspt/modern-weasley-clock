# `main.py`, `demo.py` and `calibrate.py`

The three files present roughly correspond to the three modes of the application.

- `calibrate.py` is the entrypoint for the `uv run calibrate_clock` script, which activates "calibration mode, lighting up  each of the five 12-LED-segments sequentially.

- `main.py` is the entrypoint for both "normal" (`uv run weasley_clock`) and demo mode (`uv run weasley_clock --demo`). If the script is started with `--demo`, the `bootstrap_demo_environment` function from `bootstrap.py` is used instead of `bootstrap_normal_environment`.
The program itself runs in two stages: First, during setup, the core dependencies are loaded, including the `normal_render_strategy` of the `PresentationRouter`. Since at this point, validation errors could happen, the LEDDriver is already loaded and ready to present any errors, triggered via the `display_fatal_error` convenience function of the `PresentationRouter`.
After a successful `try`-block, the system enters the `else` block where it initializes the location provider (an MQTT client if in normal mode and a `DemoLocationSimulator` if in demo mode) and the `AppController`. Finally, the main application loop is started via `controller.run()`. All resource-owning classes are Python Context Managers who are guaranteed to release their resources (e.g., active threads or access to hardware) even if an exception (such as a ``KeyboardInterrupt`) is thrown.

`main.py` also uses `signal.signal` to intercept OS-level termination signals and translates them into a `KeyboardInterrupt` which bubbles up and triggers a graceful system shutdown.
