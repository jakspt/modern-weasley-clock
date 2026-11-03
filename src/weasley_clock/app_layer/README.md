# The Application Layer / AppLogic and LocationResolver

The AppLogic acts as a state machine, keeping track of the sytem state.
This system state includes

- tracking network timeouts
- stale locations
- active privacy mode
- any active system errors
- updating each user's semantic locations (stored in the `household_state`)

It returns a `ClockSnapshot` via the system_snapshot property. This is used in the presentation layer of the application.

Most of the functions perform two actions:

- Update the system state (e.g., privacy mode is active)
- Return whether the system state changed during the update (e.g., whether privacy mode was inactive, but is now active) - this can be interpreted as "the user interface needs updating"

The most important functions are

- `perform_housekeeping`, which checks if the network has timed out and if yes, if the duration is large enough that it counts as a system error and it also checks the users' location staleness following a similar logic.
It uses the fields `_mqtt_timeout` and `_staleness_threshold`

- `on_location_update`. This calls the LocationResolver's `match_semantic_state` function which determines the semantic location of a user with the following logic:
  - Does the location fall within one of the geofences of `HOME` or `WORK_UNI`? If yes, return the matching location
  - Else check if the battery level is below a certain threshold -> `PERIL`
  - ... or if the velocity is above a certain threshold -> `IN_TRANSIT`
  - else the semantic_location is `LEISURE`
