"""
Measure internet speed.
"""

import logging
from datetime import datetime, timezone

import speedtest

from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def speed(prefix: str = "hub.speedtest") -> Stream:
    """
    Measure internet speed.

    This source will measure internet speed (download, upload,
    latency and more) by using the speedtest.net website.

    Parameters
    ----------
    prefix
        Prefix for events from this source

    Yields
    ------
    Event
        Events with internet speed data
    """
    _logger.info("Testing internet speed")
    client = speedtest.Speedtest()
    client.get_best_server()
    client.download()
    client.upload()
    _logger.debug("Received %s", client.results.dict())

    for key, value in client.results.dict().items():
        yield {
            "timestamp": datetime.now(timezone.utc),
            "name": f"{prefix}.{key}",
            "value": value,
        }
