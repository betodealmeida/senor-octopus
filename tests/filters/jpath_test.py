import random
from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from senor_octopus.filters.jpath import jsonpath
from senor_octopus.sources.rand import rand


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_jpath() -> None:
    random.seed(42)

    filter_ = "$.events[?(@.value<0.5)]"
    events = [event async for event in jsonpath(rand(2), filter_)]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.random",
            "value": 0.025010755222666936,
        },
    ]
