# The Data Layer / MQTTClient

This module is responsible for communication with the MQTT broker.

An `MQTTClient` client needs

- an `MQTTConfig` object and
- the event queue (to put `LocationUpdateEvents` into)

to be instantiated.

It uses `paho-mqtt` which dictates the structure of this class.
The callbacks (`on_X`) are a result of using this library.

The `MQTTClient` is a Context Manager, meaning it automatically executes its `__enter__` and `__exit__` methods upon entering/exiting a `with` statement (as used in `main.py`).
The `__exit__` method is always executed, even in the case of an exception being thrown.
This ensures the system cleanly disconnects from the broker even in the event of an error.

The main logic of this class lies in the `on_message` callback, which is executed upon receiving a new MQTT message (which happens as soon as the `paho-mqtt` starts a new thread with `self._client.loop_start()`).
The function checks the received json payload for its type (`location`) and extracts the necessary parameters to create an `LocationUpdateEvent`, then puts it into the queue.
To maintain availability, exceptions do not immediately lead to a crash, but are instead logged.
