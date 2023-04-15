import random
from datetime import datetime
from datetime import timezone

import pytest
from freezegun import freeze_time

from senor_octopus.sources.rand import rand


@freeze_time("2021-01-01T12:00:00-07:00")
@pytest.mark.asyncio
async def test_sun() -> None:
    random.seed(42)

    events = [event async for event in rand(1)]

    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 19, tzinfo=timezone.utc),
            "name": "hub.random",
            "value": 0.6394267984578837,
        },
    ]
