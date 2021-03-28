import logging
import os
from datetime import datetime
from datetime import timezone

import geohash
from aiohttp import ClientSession
from pywhistle import Client
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def whistle(prefix: str = "hub.whistle") -> Stream:
    username = os.environ["WHISTLE_USERNAME"]
    password = os.environ["WHISTLE_PASSWORD"]

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
