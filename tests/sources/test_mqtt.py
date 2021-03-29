from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import List
from typing import Union

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
    topics: Union[str, List[str]]

    mock.return_value.__aenter__.return_value.filtered_messages.return_value.__aenter__.return_value = aiter(
        messages,
    )
    topics = "topic/#"
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
