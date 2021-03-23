import random
from datetime import datetime

from senor_octopus.types import Stream


async def rand(events: int = 10) -> Stream:
    for _ in range(events):
        yield {
            "timestamp": datetime.now(),
            "name": "hub.random",
            "value": random.random(),
        }
