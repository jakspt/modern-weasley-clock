import queue
from unittest.mock import Mock

import pytest


@pytest.fixture
def event_queue():
    return queue.Queue()


@pytest.fixture
def mock_msg_factory():

    def _create_msg(payload_bytes: bytes):
        msg = Mock()
        msg.payload = payload_bytes
        return msg

    return _create_msg


@pytest.fixture
def basic_config():

    return {
        "users": {
            "Person1": {
                "tid": "p1",
                "color_rgb": [255, 100, 0],
                "geofences": {
                    "HOME": [{"lat": 48.208200, "lon": 16.3738, "radius_m": 50}],
                    "WORK_UNI": [{"lat": 48.209100, "lon": 16.3738, "radius_m": 50}],
                },
            },
            "Person2": {
                "tid": "p2",
                "color_rgb": [0, 255, 0],
                "geofences": {
                    "HOME": [{"lat": 48.2082, "lon": 16.3738, "radius_m": 50}],
                    "WORK_UNI": [{"lat": 48.5082, "lon": 16.3738, "radius_m": 50}],
                },
            },
            "Person3": {
                "tid": "p3",
                "color_rgb": [50, 100, 0],
                "geofences": {
                    "HOME": [
                        {"lat": 48.5082, "lon": 16.3738, "radius_m": 50},
                        {"lat": 48.5082, "lon": 16.3738, "radius_m": 50},
                        {"lat": 48.5082, "lon": 16.3738, "radius_m": 50},
                    ],
                    "WORK_UNI": [{"lat": 48.2082, "lon": 16.3738, "radius_m": 50}],
                },
            },
            "Person4": {
                "tid": "p4",
                "color_rgb": [0, 100, 0],
                "geofences": {
                    "HOME": [{"lat": 48.5082, "lon": 16.3738, "radius_m": 50}],
                    "WORK_UNI": [{"lat": 48.2082, "lon": 16.3738, "radius_m": 50}],
                },
            },
        }
    }
