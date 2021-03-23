import logging

from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def log(stream: Stream, level: str = "INFO") -> None:
    async for event in stream:
        _logger.log(getattr(logging, level.upper()), event)
