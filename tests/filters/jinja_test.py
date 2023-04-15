import random
from datetime import datetime
from datetime import timezone

import pytest
from freezegun import freeze_time
from senor_octopus.filters.jinja import jinja
from senor_octopus.sources.rand import rand


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_jinja() -> None:
    random.seed(42)

    template = (
        "{% if event['value'] < 0.5 %}{{ '{:.2f}'.format(event['value']) }}{% endif %}"
    )
    events = [event async for event in jinja(rand(2), template)]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.random",
            "value": "0.03",
        },
    ]
