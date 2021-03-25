import os
from datetime import datetime

import httpx
from senor_octopus.lib import flatten
from senor_octopus.types import Stream


async def weatherapi(location: str, prefix: str = "hub.weatherapi") -> Stream:
    token = os.environ["WEATHERAPI_TOKEN"]

    url = (
        f"http://api.weatherapi.com/v1/forecast.json?key={token}"
        f"&q={location}&days=2&aqi=no&alerts=no"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    payload = response.json()

    for key, value in flatten(payload["current"]).items():
        yield {
            "timestamp": datetime.utcnow(),
            "name": f"{prefix}.current.{key}",
            "value": value,
        }

    tomorrow = payload["forecast"]["forecastday"][1]
    for key, value in flatten(tomorrow["day"]).items():
        yield {
            "timestamp": datetime.utcnow(),
            "name": f"{prefix}.forecast.forecastday.{key}",
            "value": value,
        }
