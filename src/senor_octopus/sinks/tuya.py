import logging
from functools import lru_cache

from senor_octopus.types import Stream
from tuyapy import TuyaApi
from typing_extensions import Literal

_logger = logging.getLogger(__name__)

api = TuyaApi()


@lru_cache(maxsize=None)
def authenticate(email: str, password: str, country: str, application: str) -> None:
    _logger.debug("Authenticating")
    api.init(email, password, country, application)


async def tuya(
    stream: Stream,
    device: str,
    email: str,
    password: str,
    country: str = "1",
    application: str = Literal["smart_life", "tuya"],
) -> None:
    """
    Send commands to a Tuya/Smart Life device.

    Currently this plugin supports sending on and off events, but
    it can be easily modified to support changing the color of a
    lightbulb.

    Parameters
    ----------
    stream
        The incoming stream of events
    device
        The name of the device to be controlled
    email
        The email of the account
    password
        The password of the account
    country
        Country telephone code
    application
        The application code, either "tuya" or "smart_life"
    """
    authenticate(email, password, country, application)
    devices = {d.name(): d for d in api.get_all_devices()}
    if device not in devices:
        valid = ", ".join(f'"{name}"' for name in devices)
        _logger.error('Device "%s" not found. Available devices: %s', device, valid)
        return

    async for event in stream:  # pragma: no cover
        _logger.debug(event)
        if event["name"].lower() == "turn":
            if event["value"].lower() == "on":
                devices[device].turn_on()
            elif event["value"].lower() == "off":
                devices[device].turn_off()
            else:
                _logger.warning("Unknown value: %s", event["value"])
