import logging
from datetime import datetime
from datetime import timezone

import httpx
from senor_octopus.lib import flatten
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def weatherapi(
    access_token: str,
    location: str,
    prefix: str = "hub.weatherapi",
) -> Stream:
    """
    Fetch weather forecast data from weatherapi.com.

    This source will periodically retrieve weather forecast
    data from weatherapi.com for a given location.

    Parameters
    ----------
    access_token
        Access token from https://www.weatherapi.com/my/.
    location
        Location name or ZIP code
    prefix
        Prefix for events from this source

    Yields
    ------
    Event
        Events with weather forecast data
    """
    _logger.info("Fetching weather data")
    url = (
        f"http://api.weatherapi.com/v1/forecast.json?key={access_token}"
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
