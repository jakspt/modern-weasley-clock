import json
import logging
import socket
from dataclasses import dataclass
from queue import Queue

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client

from weasley_clock.core.events import (
    LocationUpdateEvent,
    MQTTConnectEvent,
    MQTTDisconnectEvent,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MQTTConfig:
    host: str
    username: str
    password: str
    port: int = 8883

    def __post_init__(self):
        if not self.host:
            raise ValueError("host must be provided")
        if not self.username:
            raise ValueError("username must be provided")
        if not self.password:
            raise ValueError("password must be provided")


class MQTTClient:
    def __init__(self, config: MQTTConfig, event_queue: Queue):
        if not all([config, event_queue]):
            raise ValueError("config and event_queue must be provided")
        self._config = config
        self._event_queue = event_queue
        self._client = mqtt.Client(
            client_id="weasley_clock",
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self._client.username_pw_set(config.username, config.password)
        self._client.tls_set()
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def start(self):
        mqtt_logger = logging.getLogger("paho.mqtt")
        self._client.enable_logger(mqtt_logger)

        try:
            self._client.connect(self._config.host, self._config.port)
            self._client.loop_start()
        except (ConnectionRefusedError, socket.gaierror, TimeoutError) as e:
            logger.exception(f"Fatal error reaching MQTT Broker: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected MQTT initialization error: {e}")
            raise

    def stop(self):
        self._client.disconnect()
        self._client.loop_stop()
        logger.info("MQTT Client stopped successfully.")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        # don't suppress exceptions
        return False

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if not reason_code.is_failure:
            logger.info(f"Connected to broker successfully. (Code: {reason_code})")
            client.subscribe(f"owntracks/{self._config.username}/+")
            self._event_queue.put(MQTTConnectEvent())
        else:
            logger.error(f"Connection refused by broker: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.warning(f"Unexpected disconnection! Reason: {reason_code}")
            self._event_queue.put(MQTTDisconnectEvent())
        else:
            logger.info("Disconnected cleanly from broker.")

    def _on_message(self, client: Client, userdata, message: mqtt.MQTTMessage):
        try:
            data = json.loads(message.payload.decode())
            message_type = data.get("_type")
            if message_type == "location":
                event = LocationUpdateEvent(
                    data.get("lat"),
                    data.get("lon"),
                    data.get("tid"),
                    data.get("created_at"),
                    data.get("batt", 100),
                    data.get("vel", 0),
                )
                trigger = data.get("t")
                if trigger == "p":
                    logger.debug(f"Ping received from tracker ID: {data.get('tid')}")
                else:
                    logger.debug(
                        f"Location update received from tracker ID: {data.get('tid')}"
                    )
                if "batt" not in data:
                    logger.debug(
                        f"Battery level missing for {event.user_id}, proceeding with default value."
                    )
                if "vel" not in data:
                    logger.debug(
                        f"Velocity missing for {event.user_id}, proceeding with default value."
                    )
                self._event_queue.put(event)
            else:
                logger.warning(f"Unsupported message type: {message_type}")
        except json.decoder.JSONDecodeError as e:
            logger.exception(f"Error decoding JSON payload: {e}")
        except Exception as e:
            logger.exception(f"Error while processing MQTT message: {e}")
