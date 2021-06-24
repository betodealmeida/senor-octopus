import random

import pytest
from senor_octopus.sinks.slack import slack
from senor_octopus.sources.rand import rand


@pytest.mark.asyncio
async def test_slack(mocker) -> None:
    WebClient = mocker.patch("senor_octopus.sinks.slack.WebClient")
    client = WebClient.return_value

    random.seed(42)

    await slack(rand(1), "XXX", "C0123456789")

    client.chat_postMessage.assert_called_with(
        channel="C0123456789",
        text="0.6394267984578837",
    )
