import random
from datetime import datetime
from datetime import timezone

from senor_octopus.types import Stream


async def rand(events: int = 10, prefix: str = "hub.random") -> Stream:
    """
    Generate random numbers between 0 and 1.

    This source will generate random numbers between 0 and 1
    when schedule. It's useful for testing.

    Parameters
    ----------
    events
        Number of events to generate every time it runs
    prefix
        Prefix for events from this source

    Yields
    ------
    Event
         Events with random numbers
    """
    for _ in range(events):
        yield {
            "timestamp": datetime.now(timezone.utc),
            "name": prefix,
            "value": random.random(),
        }
