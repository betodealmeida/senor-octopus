import json
import logging
from datetime import datetime
from datetime import timezone
from typing import AsyncGenerator
from typing import List
from typing import Optional

from asyncio_mqtt import Client
from paho.mqtt.client import MQTTMessage
from senor_octopus.lib import merge_streams
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)

MessageStream = AsyncGenerator[MQTTMessage, None]


async def mqtt(
    topics: List[str],
    host: str = "localhost",
    port: int = 1883,
    username: Optional[str] = None,
    password: Optional[str] = None,
    message_is_json: bool = False,
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
    message_is_json
        The MQTT message is encoded as JSON and should be parsed
    prefix
        Prefix for events from this source

    Yields
    ------
    Event
        Events with data from MQTT messages
    """
    _logger.info("Subscribing to MQTT topics")

    async with Client(host, port, username=username, password=password) as client:
        streams = [
            read_from_topic(client, topic, prefix, message_is_json) for topic in topics
        ]
        async for event in merge_streams(*streams):
            yield event


async def read_from_topic(
    client: Client,
    topic: str,
    prefix: str,
    message_is_json: bool,
) -> Stream:
    async with client.filtered_messages(topic) as messages:
        _logger.debug("Subscribing to topic: %s", topic)
        await client.subscribe(topic)
        async for message in messages:  # pragma: no cover
            value = message.payload.decode()
            if message_is_json:
                try:
                    value = json.loads(value)
                except Exception:
                    pass

            yield {
                "timestamp": datetime.now(timezone.utc),
                "name": f"{prefix}.{message.topic}",
                "value": value,
            }
