import logging
from datetime import datetime
from datetime import timezone
from typing import List
from typing import Optional
from typing import Union

from asyncio_mqtt import Client
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def mqtt(
    topics: Union[str, List[str]],
    host: str = "localhost",
    port: str = "1883",
    username: Optional[str] = None,
    password: Optional[str] = None,
    prefix: str = "hub.mqtt",
) -> Stream:
    _logger.info("Subscribing to MQTT topics")

    if isinstance(topics, str):
        topics = [topic.strip() for topic in topics.split(",")]

    async with Client(host, int(port), username=username, password=password) as client:
        for topic in topics:
            async with client.filtered_messages(topic) as messages:
                _logger.debug("Subscribing to topic: %s", topic)
                await client.subscribe(topic)
                async for message in messages:  # pragma: no cover
                    yield {
                        "timestamp": datetime.now(timezone.utc),
                        "name": f"{prefix}.{message.topic}",
                        "value": message.payload.decode(),
                    }
