"""
A source that subscribes to one or more MQTT topics.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

from asyncio_mqtt import Client, MqttError
from paho.mqtt.client import MQTTMessage

from senor_octopus.lib import merge_streams
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)

MessageStream = AsyncGenerator[MQTTMessage, None]


async def mqtt(  # pylint: disable=too-many-arguments
    topics: List[str],
    host: str = "localhost",
    port: int = 1883,
    username: Optional[str] = None,
    password: Optional[str] = None,
    client_id: Optional[str] = None,
    message_is_json: bool = False,
    reconnect_interval: int = 3,
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
    client_id:
        Optional client ID to use when connecting to the MQTT server
    message_is_json
        The MQTT message is encoded as JSON and should be parsed
    reconnect_interval
        Number of seconds to wait before reconnecting to the MQTT server
    prefix
        Prefix for events from this source

    Yields
    ------
    Event
        Events with data from MQTT messages
    """
    _logger.info("Connecting to MQTT server")

    while True:
        try:
            async with Client(  # pragma: no cover
                host,
                port,
                username=username,
                password=password,
                client_id=client_id or prefix,
                clean_session=False,
            ) as client:
                streams = [
                    read_from_topic(client, topic, prefix, message_is_json)
                    for topic in topics
                ]
                async for event in merge_streams(*streams):  # pragma: no cover
                    yield event
        except MqttError as error:
            _logger.warning(
                'Error "%s". Reconnecting in %s seconds.',
                error,
                reconnect_interval,
            )
            await asyncio.sleep(reconnect_interval)
        except asyncio.CancelledError:
            break


async def read_from_topic(
    client: Client,
    topic: str,
    prefix: str,
    message_is_json: bool,
) -> Stream:
    """
    Read from a given topic.
    """
    async with client.filtered_messages(topic) as messages:
        _logger.debug("Subscribing to topic: %s", topic)
        await client.subscribe(topic, qos=1)
        async for message in messages:  # pragma: no cover
            value = message.payload.decode()
            if message_is_json:
                try:
                    value = json.loads(value)
                except json.decoder.JSONDecodeError:
                    _logger.warning('Invalid JSON found: "%s"', value)

            yield {
                "timestamp": datetime.now(timezone.utc),
                "name": f"{prefix}.{message.topic}",
                "value": value,
            }
