import logging

from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def log(stream: Stream, level: str = "INFO") -> None:
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
    async for event in stream:
        _logger.log(getattr(logging, level.upper()), event)
