# The `AppController`

This class is the central orchestrator of the package, alongside `bootstrap.py` which configures the application's environment, depending on whether it is started in demo mode or not.

It depends on the `PresentationRouter`, the `zones` dict as loaded by `config.py` and optionally an `app_settings` dict which I used to pass optional parameters to the `AppLogic`.

A central piece is the `run()` function whose execution in `main.py` marks the start of the application after all the configuration steps are done.

`run()` does three things:

- It fetches an event from the event queue
- Lets the event be handled by the `AppLogic`
- And depending on whether the UI needs to be changed, it fetches the `sytem_snapshot` and has the `PresentationRouter` display it.

I catch the very general `Exception` on purpose since the IoT device has no way to communicate to its users except the LED Ring. This means that the application should not crash immediately, but display an error pattern to alert the users.
