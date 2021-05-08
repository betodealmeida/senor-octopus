import asyncio
import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from senor_octopus.types import Stream
from suntime import Sun

_logger = logging.getLogger(__name__)


async def sun(
    latitude: float,
    longitude: float,
    prefix: str = "hub.sun",
) -> Stream:
    """
    Send events on sunrise and sunset.

    This source will send a "sunrise" message on sunrise, and a
    "sunset" message on sunset.

    Parameters
    ----------
    latitude
        Latitude of the location, as a float (eg, -45.2)
    longitude
        Longitude of the location, as a float (eg, -200.1)

    Yields
    ------
    Event
        Sunrise and sunset events
    """
    _logger.info("Waiting for sunrise/sunset")
    info = Sun(latitude, longitude)

    while True:
        now = datetime.now(timezone.utc).astimezone()
        _logger.debug("Now is: %s", now)

        reference = now.date()

        next_sunrise = info.get_local_sunrise_time(reference)
        _logger.debug("Next sunrise: %s", next_sunrise)
        next_sunset = info.get_local_sunset_time(reference)
        if next_sunset < next_sunrise:
            next_sunset = info.get_local_sunset_time(reference + timedelta(days=1))
        _logger.debug("Next sunset: %s", next_sunset)

        if now < next_sunrise:
            _logger.debug("Waiting for today's sunrise")
            await asyncio.sleep((next_sunrise - now).total_seconds())
            yield {
                "timestamp": next_sunrise.astimezone(timezone.utc),
                "name": prefix,
                "value": "sunrise",
            }
        elif now < next_sunset:
            _logger.debug("Waiting for today's sunset")
            await asyncio.sleep((next_sunset - now).total_seconds())
            yield {
                "timestamp": next_sunset.astimezone(timezone.utc),
                "name": prefix,
                "value": "sunset",
            }
        else:
            _logger.debug("Waiting for tomorrow's sunrise")
            tomorrow = reference + timedelta(days=1)
            next_sunrise = info.get_local_sunrise_time(tomorrow)
            await asyncio.sleep((next_sunrise - now).total_seconds())
            yield {
                "timestamp": next_sunrise.astimezone(timezone.utc),
                "name": prefix,
                "value": "sunrise",
            }
