import asyncio
import logging
from asyncio.futures import Future
from datetime import datetime
from datetime import timezone
from typing import AsyncGenerator
from typing import Dict
from typing import List
from typing import Optional

from asyncio_mqtt import Client
from paho.mqtt.client import MQTTMessage
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)

MessageStream = AsyncGenerator[MQTTMessage, None]


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
        streams = []
        for topic in topics:
            streams.append(read_from_topic(client, topic))
        async for message in merge(*streams):
            yield {
                "timestamp": datetime.now(timezone.utc),
                "name": f"{prefix}.{message.topic}",
                "value": message.payload.decode(),
            }


async def merge(*iterables: MessageStream) -> MessageStream:
    iterables_next: Dict[
        MessageStream,
        Optional[Future[MessageStream]],
    ] = {iterable.__aiter__(): None for iterable in iterables}
    iterable_map: Dict[Future[MessageStream], MessageStream] = {}
    while iterables_next:
        # get the next message in each iterable
        for iterable, next_ in iterables_next.items():
            if next_ is None:
                future = asyncio.ensure_future(iterable.__anext__())
                iterable_map[future] = iterable
                iterables_next[iterable] = future

        done, pending = await asyncio.wait(
            {iterable for iterable in iterables_next.values() if iterable},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for future in done:
            # clear message in each completed iterable
            iterable = iterable_map[future]
            iterables_next[iterable] = None

            try:
                message = future.result()
            except StopAsyncIteration:
                del iterables_next[iterable]
                continue
            yield message


async def read_from_topic(client: Client, topic: str) -> MessageStream:
    async with client.filtered_messages(topic) as messages:
        _logger.debug("Subscribing to topic: %s", topic)
        await client.subscribe(topic)
        async for message in messages:  # pragma: no cover
            yield message
