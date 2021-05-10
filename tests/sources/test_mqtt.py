import asyncio
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone

import aiotools
import pytest
from asyncstdlib.builtins import aiter
from freezegun import freeze_time
from senor_octopus.sources.mqtt import mqtt


@dataclass
class FakeMessage:
    topic: str
    payload: bytes


messages = [FakeMessage("topic/1", str(i).encode("utf-8")) for i in range(3)]


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_mqtt(mocker) -> None:
    mock = mocker.patch("senor_octopus.sources.mqtt.Client")
    mock.return_value.__aenter__.return_value = mocker.MagicMock()
    mock.return_value.__aenter__.return_value.subscribe = mocker.AsyncMock()
    mock.return_value.__aenter__.return_value.filtered_messages.return_value.__aenter__ = (
        mocker.AsyncMock()
    )
    mock.return_value.__aenter__.return_value.filtered_messages.return_value.__aenter__.return_value = aiter(
        messages,
    )
    topics = ["topic/#"]
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
