import logging
from datetime import datetime
from datetime import timezone
from typing import List
from typing import Optional

from asyncio_mqtt import Client
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


async def mqtt(
    topics: List[str],
    host: str = "localhost",
    port: int = 1883,
    username: Optional[str] = None,
    password: Optional[str] = None,
    prefix: str = "hub.mqtt",
) -> Stream:
    """
    Subscribe to messages on one or more MQTT topics.

    This source will subscribe to one or more MQTT topics (or topic
    wildcards), sending an event every time a message is received.

    Parameters
    ----------
    topics
        List of topics (or topic wildcards) to subscribe to
    host
        Host where the MQTT server is running
    port
        Port which the MQTT is listening to
    username
        Optional username to use when connecting to the MQTT server
    password
        Optional password to use when connecting to the MQTT server
    prefix
        Prefix for events from this source

    Yields
    ------
    Event
        Events with data from MQTT messages
    """
    _logger.info("Subscribing to MQTT topics")

    async with Client(host, port, username=username, password=password) as client:
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
