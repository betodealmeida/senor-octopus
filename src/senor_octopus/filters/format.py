import ast
import logging
from distutils.util import strtobool
from typing import Optional

from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def format(
    stream: Stream,
    format_name: Optional[str] = None,
    format_value: Optional[str] = None,
    eval_value: Optional[str] = "false",
) -> Stream:
    """
    Forma an event stream based on an f-string.
    """
    _logger.debug("Formatting events")
    async for event in stream:  # pragma: no cover
        event = event.copy()
        if format_name:
            event["name"] = format_name.format(**event)
        if format_value:
            event["value"] = format_value.format(**event)
        if eval_value and bool(strtobool(eval_value)):
            event["value"] = ast.literal_eval(event["value"])

        yield event
