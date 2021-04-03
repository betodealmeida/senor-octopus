from datetime import datetime
from datetime import timezone

import pytest
from freezegun import freeze_time
from senor_octopus.sources.crypto import crypto

mock_payloads = [{"BTC": {"USD": 55816.61}}, {"AUDIO": {"USD": 4.051}}]


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_crypto(mocker) -> None:
    mock = mocker.patch("senor_octopus.sources.crypto.cryptocompare")

    mock.get_price.side_effect = mock_payloads
    coins = ["BTC", "AUDIO"]
    events = [event async for event in crypto(coins)]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.crypto.BTC.USD",
            "value": 55816.61,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.crypto.AUDIO.USD",
            "value": 4.051,
        },
    ]
