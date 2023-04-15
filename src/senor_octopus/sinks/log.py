"""
A simple sink that logs events to a logger.
"""

import logging

from senor_octopus.types import Stream


async def log(
    stream: Stream,
    level: str = "INFO",
    name: str = __name__,
) -> None:
    """
    Send events to a logger.

    This sink can be used to send events to a logger, using
    a configurable level (DEBUG, INFO, WARNING, ERROR, etc.).

    Parameters
    ----------
    stream
        The incoming stream of events
    level
        The logging level to be used
    """
    _logger = logging.getLogger(name)
    async for event in stream:
        _logger.log(getattr(logging, level.upper()), event)
