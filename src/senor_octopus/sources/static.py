"""
Simple source node that generates static events.
"""

from datetime import datetime, timezone

from senor_octopus.types import Stream


async def static(name: str, value: str) -> Stream:
    """
    Generate static events.

    Parameters
    ----------
    name
        Name of the event
    value
        Value of the event

    Yields
    ------
    Event
        Static event
    """
    yield {
        "timestamp": datetime.now(timezone.utc),
        "name": name,
        "value": value,
    }
