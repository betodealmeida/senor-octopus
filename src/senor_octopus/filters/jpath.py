import logging

from jsonpath import JSONPath
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def jsonpath(stream: Stream, filter: str) -> Stream:
    """
    Filter event stream based on a JSON path.

    This filter can be used to filter events based on their
    name and value, allowing events to be dynamically routed.

    Parameters
    ----------
    stream
        The incoming stream of events
    filter
        A JSON Path expression used to filter events

    Yields
    ------
    Event
        Events filtered by the JSON Path expression
    """
    _logger.debug("Filtering events")
    parser = JSONPath(filter)
    async for event in stream:  # pragma: no cover
        if parser.parse({"events": [event]}):
            yield event
