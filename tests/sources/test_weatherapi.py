import json
import os
from datetime import datetime
from datetime import timezone

import pytest
from freezegun import freeze_time
from senor_octopus.sources.weatherapi import weatherapi

dirname, filename = os.path.split(os.path.abspath(__file__))
with open(os.path.join(dirname, "weatherapi_response.json")) as fp:
    mock_payload = json.load(fp)


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_weatherapi(httpx_mock) -> None:
    httpx_mock.add_response(json=mock_payload)

    events = [event async for event in weatherapi("XXX", "iceland")]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.last_updated_epoch",
            "value": 1616644811,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.last_updated",
            "value": "2021-03-25 04:00",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.temp_c",
            "value": -2.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.temp_f",
            "value": 28.4,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.is_day",
            "value": 0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.condition.text",
            "value": "Partly cloudy",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.condition.icon",
            "value": "//cdn.weatherapi.com/weather/64x64/night/116.png",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.condition.code",
            "value": 1003,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.wind_mph",
            "value": 2.5,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.wind_kph",
            "value": 4.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.wind_degree",
            "value": 100,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.wind_dir",
            "value": "E",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.pressure_mb",
            "value": 988.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.pressure_in",
            "value": 29.6,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.precip_mm",
            "value": 0.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.precip_in",
            "value": 0.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.humidity",
            "value": 93,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.cloud",
            "value": 75,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.feelslike_c",
            "value": -6.5,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.feelslike_f",
            "value": 20.4,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.vis_km",
            "value": 10.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.vis_miles",
            "value": 6.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.uv",
            "value": 1.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.gust_mph",
            "value": 11.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.current.gust_kph",
            "value": 17.6,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.maxtemp_c",
            "value": 3.7,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.maxtemp_f",
            "value": 38.7,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.mintemp_c",
            "value": 0.2,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.mintemp_f",
            "value": 32.4,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.avgtemp_c",
            "value": 1.7,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.avgtemp_f",
            "value": 35.1,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.maxwind_mph",
            "value": 10.7,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.maxwind_kph",
            "value": 17.3,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.totalprecip_mm",
            "value": 1.7,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.totalprecip_in",
            "value": 0.07,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.avgvis_km",
            "value": 9.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.avgvis_miles",
            "value": 5.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.avghumidity",
            "value": 77.0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.daily_will_it_rain",
            "value": 1,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.daily_chance_of_rain",
            "value": "74",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.daily_will_it_snow",
            "value": 0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.daily_chance_of_snow",
            "value": "0",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.condition.text",
            "value": "Patchy rain possible",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.condition.icon",
            "value": "//cdn.weatherapi.com/weather/64x64/day/176.png",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.condition.code",
            "value": 1063,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.weatherapi.forecast.forecastday.uv",
            "value": 1.0,
        },
    ]
