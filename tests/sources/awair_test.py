from datetime import datetime
from datetime import timezone

import pytest
from senor_octopus.sources.awair import awair

mock_payload = {
    "data": [
        {
            "timestamp": "2021-03-23T22:26:51.000Z",
            "score": 95.0,
            "sensors": [
                {"comp": "temp", "value": 25.0},
                {"comp": "voc", "value": 158.0},
                {"comp": "pm25", "value": 3.0},
                {"comp": "co2", "value": 640.0},
                {"comp": "humid", "value": 42.45000076293945},
            ],
            "indices": [
                {"comp": "pm25", "value": 0.0},
                {"comp": "voc", "value": 0.0},
                {"comp": "humid", "value": 0.0},
                {"comp": "co2", "value": 1.0},
                {"comp": "temp", "value": 0.0},
            ],
        },
    ],
}


@pytest.mark.asyncio
async def test_awair(httpx_mock) -> None:
    httpx_mock.add_response(json=mock_payload)

    events = [event async for event in awair("XXX", 12345)]
    assert events == [
        {
            "timestamp": datetime(2021, 3, 23, 22, 26, 51, tzinfo=timezone.utc),
            "name": "hub.awair.score",
            "value": 95.0,
        },
        {
            "timestamp": datetime(2021, 3, 23, 22, 26, 51, tzinfo=timezone.utc),
            "name": "hub.awair.temp",
            "value": 25.0,
        },
        {
            "timestamp": datetime(2021, 3, 23, 22, 26, 51, tzinfo=timezone.utc),
            "name": "hub.awair.voc",
            "value": 158.0,
        },
        {
            "timestamp": datetime(2021, 3, 23, 22, 26, 51, tzinfo=timezone.utc),
            "name": "hub.awair.pm25",
            "value": 3.0,
        },
        {
            "timestamp": datetime(2021, 3, 23, 22, 26, 51, tzinfo=timezone.utc),
            "name": "hub.awair.co2",
            "value": 640.0,
        },
        {
            "timestamp": datetime(2021, 3, 23, 22, 26, 51, tzinfo=timezone.utc),
            "name": "hub.awair.humid",
            "value": 42.45000076293945,
        },
    ]
