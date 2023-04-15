from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from senor_octopus.sources.static import static


@freeze_time("2021-01-01T12:00:00-07:00")
@pytest.mark.asyncio
async def test_sun() -> None:
    events = [event async for event in static("name", "value")]

    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 19, tzinfo=timezone.utc),
            "name": "name",
            "value": "value",
        },
    ]
