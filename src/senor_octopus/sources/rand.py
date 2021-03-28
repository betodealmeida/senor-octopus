import random
from datetime import datetime
from datetime import timezone
from typing import Union

from senor_octopus.types import Stream


async def rand(events: Union[str, int] = 10) -> Stream:
    for _ in range(int(events)):
        yield {
            "timestamp": datetime.now(timezone.utc),
            "name": "hub.random",
            "value": random.random(),
        }
