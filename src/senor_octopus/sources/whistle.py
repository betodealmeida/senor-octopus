import logging
from datetime import datetime
from datetime import timezone

import geohash
from aiohttp import ClientSession
from pywhistle import Client
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def whistle(username: str, password: str, prefix: str = "hub.whistle") -> Stream:
    """
    Fetch device information and location for a Whistle pet tracker.

    This source will periodically fetch device information (battery level,
    last check-in, tracking status, battery status) and location for a
    given Whistle pet tracker.

    The location is emitted both as a pair of latitude, longitude, as well
    as a geohash.

    Parameters
    ----------
    username
        Username for https://app.whistle.com/
    password
        Password for https://app.whistle.com/
    prefix
        Prefix for events from this source

    Yields
    ------
    Event
        Events with device information and location
    """
    _logger.info("Fetching location from Whistle")
    async with ClientSession() as websession:
        client = Client(username, password, websession)
        await client.async_init()
        payload = await client.get_pets()
        _logger.debug("Received %s", payload)

        for pet in payload["pets"]:
            name = pet["name"]

            # device info
            keys = {
                "battery_level",
                "last_check_in",
                "tracking_status",
                "battery_status",
            }
            for key in keys:
                yield {
                    "timestamp": datetime.now(timezone.utc),
                    "name": f"{prefix}.{name}.{key}",
                    "value": pet["device"][key],
                }

            # last location
            location = pet["last_location"]
            yield {
                "timestamp": datetime.now(timezone.utc),
                "name": f"{prefix}.{name}.location",
                "value": (location["latitude"], location["longitude"]),
            }
            yield {
                "timestamp": datetime.now(timezone.utc),
                "name": f"{prefix}.{name}.geohash",
                "value": geohash.encode(location["latitude"], location["longitude"]),
            }
