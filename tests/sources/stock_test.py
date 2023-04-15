from datetime import datetime
from datetime import timezone

import pytest
from freezegun import freeze_time
from senor_octopus.sources.stock import stock


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_stock(mocker) -> None:
    mock = mocker.patch("senor_octopus.sources.stock.stockquotes")
    type(mock.Stock.return_value).current_price = mocker.PropertyMock(
        side_effect=[283.02, 64.51, 283.02, 64.51],
    )
    type(mock.Stock.return_value).increase_percent = mocker.PropertyMock(
        side_effect=[1.54, 1.48, 1.54, 1.48],
    )
    symbols = ["FB", "LYFT"]
    events = [event async for event in stock(symbols)]
    events = sorted(events, key=lambda e: e["name"])
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.stock.FB.current_price",
            "value": 283.02,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.stock.FB.increase_percent",
            "value": 1.54,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.stock.LYFT.current_price",
            "value": 64.51,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.stock.LYFT.increase_percent",
            "value": 1.48,
        },
    ]
