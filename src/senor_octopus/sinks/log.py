import logging

from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


def log(stream: Stream) -> None:
    for event in stream:
        _logger.info(event)
