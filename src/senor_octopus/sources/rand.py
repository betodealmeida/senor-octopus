import random
from datetime import datetime
from datetime import timezone

from senor_octopus.types import Stream


async def rand(events: int = 10) -> Stream:
    for _ in range(events):
        yield {
            "timestamp": datetime.now(timezone.utc),
            "name": "hub.random",
            "value": random.random(),
        }
