import logging
from datetime import datetime
from datetime import timezone

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
    s = speedtest.Speedtest()
    s.get_best_server()
    s.download()
    s.upload()
    _logger.debug("Received %s", s.results.dict())

    for key, value in s.results.dict().items():
        yield {
            "timestamp": datetime.now(timezone.utc),
            "name": f"{prefix}.{key}",
            "value": value,
        }
