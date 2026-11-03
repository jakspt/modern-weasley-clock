# OwnTracks Setup

OwnTracks uses json-like files which can be imported into their app. The `example_config.otrc` can be used to speed up the setup process.

Before importing, change these values:

1. `"host"`, `"username"`, `"password"`: The URL, username and password of your MQTT broker (e.g., HiveMQ)
2. `"tid"`: The tracker ID for the user (must be one of `p1`, `p2`, `p3`, or `p4`). The main application logic uses this piece of information to identify the household member to whom a location update belongs to.
3. `"clientId"`: This is used for the network connection between the device and the MQTT broker. No two devices with the same ID can be connected at the same time. Therefore, ensure that `clientId` is unique for each device.
4. `"deviceId"`: This defines the topic OwnTracks will publish to. It has the structure `owntracks/<username>/<deviceId>`.

## Optional

1. `"ping"`: This is already set to `10` to ensure a "heartbeat" update is sent to the broker every 10 minutes.
2. `"locatorDisplacement"`: This is the interval used for "significant location change mode", meaning a location update is only sent when the device moves a certain amount of meters. This is currently set to `200` meters. "Ping" updates will be sent every 10 minutes in any case.
