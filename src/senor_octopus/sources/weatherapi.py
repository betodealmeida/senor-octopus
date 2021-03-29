import logging
import os
from datetime import datetime
from datetime import timezone

import httpx
from senor_octopus.lib import flatten
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def weatherapi(location: str, prefix: str = "hub.weatherapi") -> Stream:
    token = os.environ["WEATHERAPI_TOKEN"]

    _logger.info("Fetching weather data")
    url = (
        f"http://api.weatherapi.com/v1/forecast.json?key={token}"
        f"&q={location}&days=2&aqi=no&alerts=no"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    payload = response.json()
    _logger.debug("Received %s", payload)

    for key, value in flatten(payload["current"]).items():
        yield {
            "timestamp": datetime.now(timezone.utc),
            "name": f"{prefix}.current.{key}",
            "value": value,
        }

    tomorrow = payload["forecast"]["forecastday"][1]
    for key, value in flatten(tomorrow["day"]).items():
        yield {
            "timestamp": datetime.now(timezone.utc),
            "name": f"{prefix}.forecast.forecastday.{key}",
            "value": value,
        }
