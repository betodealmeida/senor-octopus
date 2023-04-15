from datetime import datetime
from datetime import timezone

import aiotools
import pytest
from freezegun import freeze_time
from senor_octopus.sources.sun import sun


@freeze_time("2021-01-01T12:00:00-07:00")
@pytest.mark.asyncio
async def test_sun() -> None:
    vclock = aiotools.VirtualClock()

    latitude = 38.3
    longitude = -123.0

    with vclock.patch_loop():
        events = sun(latitude, longitude)
        event = await events.__anext__()

    assert event == {
        "timestamp": datetime(2021, 1, 2, 1, 3, tzinfo=timezone.utc),
        "name": "hub.sun",
        "value": "sunset",
    }


@freeze_time("2021-01-01T12:00:00-07:00")
@pytest.mark.asyncio
async def test_sun_east() -> None:
    vclock = aiotools.VirtualClock()

    latitude = 51.21
    longitude = 21.01

    with vclock.patch_loop():
        events = sun(latitude, longitude)
        event = await events.__anext__()

    assert event == {
        "timestamp": datetime(2021, 1, 2, 6, 41, tzinfo=timezone.utc),
        "name": "hub.sun",
        "value": "sunrise",
    }


@freeze_time("2021-01-01T01:00:00-07:00")
@pytest.mark.asyncio
async def test_sun_early() -> None:
    vclock = aiotools.VirtualClock()

    latitude = 38.3
    longitude = -123.0

    with vclock.patch_loop():
        events = sun(latitude, longitude)
        event = await events.__anext__()

    assert event == {
        "timestamp": datetime(2021, 1, 1, 15, 29, tzinfo=timezone.utc),
        "name": "hub.sun",
        "value": "sunrise",
    }


@freeze_time("2021-01-01T23:00:00-07:00")
@pytest.mark.asyncio
async def test_sun_late() -> None:
    vclock = aiotools.VirtualClock()

    latitude = 38.3
    longitude = -123.0

    with vclock.patch_loop():
        events = sun(latitude, longitude)
        event = await events.__anext__()

    assert event == {
        "timestamp": datetime(2021, 1, 2, 15, 29, tzinfo=timezone.utc),
        "name": "hub.sun",
        "value": "sunrise",
    }
