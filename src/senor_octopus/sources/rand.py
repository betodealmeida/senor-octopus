import random
from datetime import datetime
from typing import Union

from senor_octopus.types import Stream


async def rand(events: Union[str, int] = 10) -> Stream:
    for _ in range(int(events)):
        yield {
            "timestamp": datetime.now(),
            "name": "hub.random",
            "value": random.random(),
        }
