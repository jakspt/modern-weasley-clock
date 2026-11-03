# Configuration loading and validation

The modules in this package are responsible for loading and validating the configuration files - `config.json` and `.env`, see also the `/src/README` for a further explanation on how those files are used and what they should contain.

## `config.py`

This "public" functions of this module include:

- `load_environment`: Loads the `.env` file using the `dotenv` library. This should to happen before calling any other methods from this module.
- `setup_logging`: Configures logging including the defined `LOG_LEVEL` from the `.env` file. If `LOG_TO_FILE` is `True`, a rotating file handler is setup. The rotating file handler keeps the Pi's SD card from getting full by restricting the log file to 5MB (while also keeping two backup files).
- `load_mqtt_credentials`: This function loads the credentials for the MQTT broker from the `.env` file, raising a `KeyError` if loading fails.
- `get_dimming_factor`: Loads the dimming factor used to indicate stale locations, defaults to 0.15. Used by `bootstrap.py` for setting up the `normal_render_strategy`.
- `create_led_driver` and `create_privacy_toggle()`: Those functions decide whether to use the hardware versions of the PrivacyToggle/LEDDriver or their mock versions. They achieve this by catching (import) errors that happen when trying to use `gpiozero`/`rpi_ws281x` on a Non-Raspberry Pi computer. They also access key-value pairs from the `.env` file and fall back to default values if they are not defined.
- `load_json`: Opens the `config.json` as a dictionary, and has `validate.py` validate the content. After that, it loads the `ConfiguredZone`s, colour mappings and optional `app_settings`. This is also called in `bootstrap.py`

Besides those functions, the `LED_RING_LOCATIONS` constant is defined which is used in the `RenderStrategy`.

## `validate.py`

This module defines the rules for a valid `config.json` file and what exceptions are thrown in the case of rule violations.

At its core are validation functions which are meant to be called sequentially. I decided against a more complex validation patter, for example using decorators, to keep the code more readable, staying in line with KISS.

- The `CONFIG_SCHEMA`: This is a json schema (to be used on python dictionaries, which are nearly identical to json syntax-wise) used for validating the structure of the json file which is loaded as `config_dict` in `config.py`.
- `config_structure`: uses `CONFIG_SCHEMA` as described above.
- `tid_uniqueness`: Validates whether the tracker IDs are unique (e.g., `p1` through `p4`) using set operations.
- `geofences`: Validates geofences (or rather: the list of configured zones, representing the semantic locations `HOME`/`WORK_UNI` for each users which can contain multiple geofences each) for overlaps. A geofence overlaps with another when the sum of their radii is greater than or equal to the distance of their center points. This is the most complex part of the module, refer to the in-code comments for more detail.

If a validation error occurs, a custom exception describing the issue is thrown. At the configuration file loading stage (meaning inside the `bootstrap_environment` function), those errors will result in the LED ring displaying an error pattern, and the concrete config error will be logged.
