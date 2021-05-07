import random

import pytest
from senor_octopus.sinks.mqtt import mqtt
from senor_octopus.sources.rand import rand


@pytest.mark.asyncio
async def test_mqtt(mocker) -> None:
    mock = mocker.patch("senor_octopus.sinks.mqtt.Client")
    mock__publish = (
        mock.return_value.__aenter__.return_value.publish
    ) = mocker.AsyncMock()
    mock.return_value.__aexit__ = mocker.AsyncMock()
    random.seed(42)

    await mqtt(rand(2), "topic")

    mock__publish.assert_has_calls(
        [
            mocker.call("topic", 0.6394267984578837, qos=1),
            mocker.call("topic", 0.025010755222666936, qos=1),
        ],
    )
