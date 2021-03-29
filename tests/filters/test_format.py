import random
from datetime import datetime
from datetime import timezone

import pytest
from freezegun import freeze_time
from senor_octopus.filters.format import format
from senor_octopus.sources.rand import rand


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_format() -> None:
    random.seed(42)

    events = [event async for event in format(rand(2))]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.random",
            "value": 0.6394267984578837,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.random",
            "value": 0.025010755222666936,
        },
    ]

    events = [
        event
        async for event in format(
            rand(2),
            format_name="random number",
            format_value="{value:.2f}",
            eval_value="false",
        )
    ]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "random number",
            "value": "0.28",
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "random number",
            "value": "0.22",
        },
    ]

    events = [
        event
        async for event in format(
            rand(2),
            format_value="{value:.2f}",
            eval_value="true",
        )
    ]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.random",
            "value": 0.74,
        },
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.random",
            "value": 0.68,
        },
    ]
