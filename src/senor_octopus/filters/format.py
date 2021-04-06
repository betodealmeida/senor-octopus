import ast
import logging
from typing import Optional

from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def format(
    stream: Stream,
    format_name: Optional[str] = None,
    format_value: Optional[str] = None,
    eval_value: bool = False,
) -> Stream:
    """
    Format an event stream based using Python string formatting.

    This filter will replace the name and/or value of an event
    by formatting a string based on the original event.

    Parameters
    ----------
    stream
        The incoming stream of events
    format_name
        A string formatted with the original event that replaces the name
    format_value
        A string formatted with the original event that replaces the value
    eval_value
        Wether the new value should be evaluated

    Yields
    ------
    Event
        Events formatted according to the configuration
    """
    _logger.debug("Formatting events")
    async for event in stream:  # pragma: no cover
        event = event.copy()
        if format_name:
            event["name"] = format_name.format(**event)
        if format_value:
            event["value"] = format_value.format(**event)
        if eval_value:
            event["value"] = ast.literal_eval(event["value"])

        yield event
