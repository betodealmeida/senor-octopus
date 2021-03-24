from datetime import datetime

import speedtest
from senor_octopus.types import Stream


async def speed(prefix: str = "hub.speedtest") -> Stream:
    s = speedtest.Speedtest()
    s.get_best_server()
    s.download()
    s.upload()
    for key, value in s.results.dict().items():
        yield {
            "timestamp": datetime.utcnow(),
            "name": f"{prefix}.{key}",
            "value": value,
        }
