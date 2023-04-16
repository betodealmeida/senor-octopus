"""
A filter that parses the event value into different formats.
"""

import json
import logging

import yaml

from senor_octopus.exceptions import InvalidConfigurationException
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


# pylint: disable=redefined-builtin
async def parse(stream: Stream, format: str) -> Stream:
    """
    Parse an event value.

    Parameters
    ----------
    format
        The format of the payload ("JSON" or "YAML")

    Yields
    ------
    Event
        Events parsed by the filter
    """
    _logger.debug("Applying template to events")
    async for event in stream:  # pragma: no cover
        if format.lower() == "json":
            value = json.loads(event["value"])
        elif format.lower() == "yaml":
            value = yaml.safe_load(event["value"])
        else:
            raise InvalidConfigurationException(f'Invalid format "{format}"')

        yield {
            "timestamp": event["timestamp"],
            "name": event["name"],
            "value": value,
        }
