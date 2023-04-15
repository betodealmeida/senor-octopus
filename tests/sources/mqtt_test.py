import asyncio
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone

import aiotools
import pytest
from asyncio_mqtt import MqttError
from freezegun import freeze_time
from senor_octopus.sources.mqtt import mqtt


@dataclass
class FakeMessage:
    topic: str
    payload: bytes


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_mqtt(mocker) -> None:
    vclock = aiotools.VirtualClock()

    async def gen(events, exception):
        for i in range(events):
            yield FakeMessage("topic/1", str(i).encode("utf-8"))

        raise exception

    client1 = mocker.AsyncMock()
    client1.__aenter__.return_value = mocker.MagicMock()
    client1.__aenter__.return_value.subscribe = mocker.AsyncMock()
    filtered_messages = client1.__aenter__.return_value.filtered_messages
    filtered_messages.return_value.__aenter__ = mocker.AsyncMock()
    filtered_messages.return_value.__aenter__.return_value = gen(
        3,
        MqttError("Disconnect"),
    )

    client2 = mocker.AsyncMock()
    client2.__aenter__.return_value = mocker.MagicMock()
    client2.__aenter__.return_value.subscribe = mocker.AsyncMock()
    filtered_messages = client2.__aenter__.return_value.filtered_messages
    filtered_messages.return_value.__aenter__ = mocker.AsyncMock()
    filtered_messages.return_value.__aenter__.return_value = gen(
        0,
        MqttError("Disconnect"),
    )

    client3 = mocker.AsyncMock()
    client3.__aenter__.return_value = mocker.MagicMock()
    client3.__aenter__.return_value.subscribe = mocker.AsyncMock()
    filtered_messages = client3.__aenter__.return_value.filtered_messages
    filtered_messages.return_value.__aenter__ = mocker.AsyncMock()
    filtered_messages.return_value.__aenter__.return_value = gen(
        3,
        asyncio.CancelledError("Canceled"),
    )

    Client = mocker.patch("senor_octopus.sources.mqtt.Client")
    Client.side_effect = [client1, client2, client3]

    topics = ["topic/#"]
    with vclock.patch_loop():
        events = [event async for event in mqtt(topics)]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.topic/1",
            "value": "0",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.topic/1",
            "value": "1",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.topic/1",
            "value": "2",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.topic/1",
            "value": "0",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.topic/1",
            "value": "1",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.topic/1",
            "value": "2",
        },
    ]


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_mqtt_multiple_topics(mocker) -> None:
    vclock = aiotools.VirtualClock()

    mock = mocker.patch("senor_octopus.sources.mqtt.Client")
    mock.return_value.__aenter__.return_value = mocker.MagicMock()
    mock.return_value.__aenter__.return_value.subscribe = mocker.AsyncMock()

    async def gen(topic):
        sleep = 2 if topic == "topic/1" else 5
        count = 3 if topic == "topic/1" else 2

        for i in range(count):
            await asyncio.sleep(sleep)
            yield FakeMessage(topic, str(i).encode("utf-8"))

        if topic == "other/1":
            raise asyncio.CancelledError("Canceled")

    def get_stream(topic):
        stream = mocker.MagicMock()
        stream.__aenter__ = mocker.AsyncMock()
        stream.__aenter__.return_value = gen(topic)
        return stream

    mock.return_value.__aenter__.return_value.filtered_messages.side_effect = get_stream
    topics = ["topic/1", "other/1"]
    with vclock.patch_loop():
        events = [event async for event in mqtt(topics, message_is_json=True)]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.topic/1",
            "value": 0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.topic/1",
            "value": 1,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.other/1",
            "value": 0,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.topic/1",
            "value": 2,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.mqtt.other/1",
            "value": 1,
        },
    ]
