"""
Tests for the combine filter.
"""

from datetime import datetime, timezone
from math import isnan

import pytest
from freezegun import freeze_time

from senor_octopus.filters.combine import (
    AggregationType,
    AverageAggregation,
    CountAggregation,
    FirstAggregation,
    LastAggregation,
    MaxAggregation,
    MinAggregation,
    SumAggregation,
    combine,
)
from senor_octopus.types import Stream


async def stream() -> Stream:
    """
    Generates events.
    """
    timestamp = datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    values = [
        {"key": "a", "battery": 100},
        {"key": "a", "location": "home"},
        {"key": "a", "battery": 93, "location": "work"},
        {"key": "b", "battery": 14},
    ]
    for value in values:
        yield {"timestamp": timestamp, "name": "name", "value": value}


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_serialize() -> None:
    """
    Tests for the filter.
    """
    events = [
        event
        async for event in combine(
            stream(),
            "key",
            {"battery": AggregationType.AVERAGE, "location": AggregationType.LAST},
        )
    ]
    assert events == [
        {
            "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            "name": "hub.combine.key",
            "value": {"key": "a", "battery": 96.5, "location": "work"},
        },
    ]


def test_average_aggregation() -> None:
    """
    Test ``AverageAggregation``.
    """
    aggregation = AverageAggregation()
    assert aggregation(1) == 1
    assert aggregation(0) == 0.5
    assert isnan(aggregation("invalid"))


def test_count_aggregation() -> None:
    """
    Test ``CountAggregation``.
    """
    aggregation = CountAggregation()
    assert aggregation(1) == 1
    assert aggregation(0) == 2
    assert aggregation("invalid") == 3


def test_first_aggregation() -> None:
    """
    Test ``FirstAggregation``.
    """
    aggregation = FirstAggregation()
    assert aggregation(1) == 1
    assert aggregation(0) == 1
    assert aggregation("invalid") == 1


def test_last_aggregation() -> None:
    """
    Test ``LastAggregation``.
    """
    aggregation = LastAggregation()
    assert aggregation(1) == 1
    assert aggregation(0) == 0
    assert aggregation("invalid") == "invalid"


def test_max_aggregation() -> None:
    """
    Test ``MaxAggregation``.
    """
    aggregation = MaxAggregation()
    assert aggregation(1) == 1
    assert aggregation(0) == 1
    with pytest.raises(TypeError) as excinfo:
        aggregation("invalid")
    assert (
        str(excinfo.value) == "'>' not supported between instances of 'str' and 'int'"
    )


def test_min_aggregation() -> None:
    """
    Test ``MinAggregation``.
    """
    aggregation = MinAggregation()
    assert aggregation(1) == 1
    assert aggregation(0) == 0
    with pytest.raises(TypeError) as excinfo:
        aggregation("invalid")
    assert (
        str(excinfo.value) == "'<' not supported between instances of 'str' and 'int'"
    )


def test_sum_aggregation() -> None:
    """
    Test ``SumAggregation``.
    """
    aggregation = SumAggregation()
    assert aggregation(1) == 1
    assert aggregation(0) == 1
    assert aggregation(2) == 3
    with pytest.raises(TypeError) as excinfo:
        aggregation("invalid")
    assert str(excinfo.value) == "unsupported operand type(s) for +=: 'int' and 'str'"
