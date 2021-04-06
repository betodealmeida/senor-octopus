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
    """
    Send events as messages to an MQTT topic.

    This sink can be used to send events to an MQTT topic.
    The value of the event is sent as the message; its name
    is ignored.

    Parameters
    ----------
    stream
        The incoming stream of events
    topic
        The MQTT topic where messages are sent to
    host
        Host where the MQTT server is running
    port
        Port which the MQTT is listening to
    username
        Optional username to use when connecting to the MQTT server
    password
        Optional password to use when connecting to the MQTT server
    qos
        Quality of Service (QoS) level
    """
    async with Client(host, port, username=username, password=password) as client:
        async for event in stream:  # pragma: no cover
            await client.publish(topic, event["value"], qos=qos)
