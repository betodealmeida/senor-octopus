import logging
from typing import Optional

from asyncio_mqtt import Client
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def mqtt(
    stream: Stream,
    topic: str,
    host: str = "localhost",
    port: int = 1883,
    username: Optional[str] = None,
    password: Optional[str] = None,
    qos: int = 1,
) -> None:
    async with Client(host, port, username=username, password=password) as client:
        async for event in stream:  # pragma: no cover
            await client.publish(topic, event["value"], qos=qos)
