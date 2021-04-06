import logging

import dateutil.parser
import httpx
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def awair(
    access_token: str,
    device_id: int,
    device_type: str = "awair-element",
    prefix: str = "hub.awair",
) -> Stream:
    """
    Fetch air quality data from Awair Element monitor.

    This source will periodically retrieve air quality data from
    an Awair Element monitor.

    Parameters
    ----------
    access_token
        Access token from the Awair API (https://developer.getawair.com/console/access-token)
    device_id
        Device ID
    device_type
        Device type
    prefix
        Prefix for events from this source

    Yields
    ------
    Event
        Events with data from sensors
    """
    _logger.info("Fetching air quality data")
    url = (
        "https://developer-apis.awair.is/v1/users/self/devices/"
        f"{device_type}/{device_id}/air-data/latest?fahrenheit=false"
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    payload = response.json()
    _logger.debug("Received %s", payload)

    for row in payload["data"]:
        timestamp = dateutil.parser.parse(row["timestamp"])
        yield {
            "timestamp": timestamp,
            "name": f"{prefix}.score",
            "value": row["score"],
        }

        for sensor in row["sensors"]:
            yield {
                "timestamp": timestamp,
                "name": f"{prefix}.{sensor['comp']}",
                "value": sensor["value"],
            }
