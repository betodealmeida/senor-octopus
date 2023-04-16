"""
Tests for the serializer filter.
"""

from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from senor_octopus.filters.serialize import serialize
from senor_octopus.sources.static import static


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_serialize() -> None:
    """
    Tests for the filter.
    """
    events = [
        event async for event in serialize(static("name", {"foo": "bar"}), "json")
    ]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "name",
            "value": '{"foo": "bar"}',
        },
    ]

    events = [
        event async for event in serialize(static("name", {"foo": "bar"}), "yaml")
    ]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "name",
            "value": "foo: bar\n",
        },
    ]
