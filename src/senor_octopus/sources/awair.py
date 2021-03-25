import logging
import os

import dateutil.parser
import httpx
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def awair(prefix: str = "hub.awair") -> Stream:
    token = os.environ["AWAIR_ACCESS_TOKEN"]
    device_type = os.environ["AWAIR_DEVICE_TYPE"]
    device_id = os.environ["AWAIR_DEVICE_ID"]

    _logger.info("Fetching air quality data")
    url = (
        "https://developer-apis.awair.is/v1/users/self/devices/"
        f"{device_type}/{device_id}/air-data/latest?fahrenheit=false"
    )
    headers = {"Authorization": f"Bearer {token}"}
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
