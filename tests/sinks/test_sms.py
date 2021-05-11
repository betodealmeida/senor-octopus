import random

import pytest
from senor_octopus.sinks.sms import sms
from senor_octopus.sources.rand import rand


@pytest.mark.asyncio
async def test_pushover(mocker) -> None:
    Client = mocker.patch("senor_octopus.sinks.sms.Client")
    client = Client.return_value

    random.seed(42)

    await sms(rand(1), "alice", "XXX", "+15558675309", **{"from": "+18002738255"})

    client.messages.create.assert_called_with(
        body="0.6394267984578837",
        from_="+18002738255",
        to="+15558675309",
    )
