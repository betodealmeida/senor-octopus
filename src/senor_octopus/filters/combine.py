"""
A filter that combines events in a stream.
"""

# pylint: disable=too-few-public-methods

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from marshmallow import Schema, fields

from senor_octopus.lib import configuration_schema
from senor_octopus.types import Stream

_logger = logging.getLogger(__name__)


class AggregationType(Enum):
    """
    Different types of aggregation.
    """

    AVERAGE = "average"
    SUM = "sum"
    LAST = "last"
    FIRST = "first"
    MIN = "min"
    MAX = "max"
    COUNT = "count"


class Aggregation:
    """
    An aggregation.
    """

    def __call__(self, value: Any) -> Any:
        raise NotImplementedError


class AverageAggregation(Aggregation):
    """
    Computes the average value.
    """

    def __init__(self):
        self.sum = 0
        self.count = 0

    def __call__(self, value: Any) -> float:
        try:
            value = float(value)
        except ValueError:
            _logger.warning("Could not convert %s to float", value)
            return float("nan")

        self.sum += value
        self.count += 1
        return self.sum / self.count


class SumAggregation(Aggregation):
    """
    Computes the sum of the values.
    """

    def __init__(self):
        self.sum = 0

    def __call__(self, value: Any) -> float:
        self.sum += value
        return self.sum


class LastAggregation(Aggregation):
    """
    Returns the last value seen.
    """

    def __call__(self, value: Any) -> Any:
        return value


class FirstAggregation(Aggregation):
    """
    Returns the first value seen.
    """

    def __init__(self):
        self.first = None

    def __call__(self, value: Any) -> Any:
        if self.first is None:
            self.first = value
        return self.first


class MinAggregation(Aggregation):
    """
    Returns the minimum value seen.
    """

    def __init__(self):
        self.min = None

    def __call__(self, value: Any) -> Any:
        if self.min is None:
            self.min = value
        else:
            self.min = min(self.min, value)
        return self.min


class MaxAggregation(Aggregation):
    """
    Returns the maximum value seen.
    """

    def __init__(self):
        self.max = None

    def __call__(self, value: Any) -> Any:
        if self.max is None:
            self.max = value
        else:
            self.max = max(self.max, value)
        return self.max


class CountAggregation(Aggregation):
    """
    Returns the number of values seen.
    """

    def __init__(self):
        self.count = 0

    def __call__(self, value: Any) -> int:
        self.count += 1
        return self.count


aggregation_map = {
    AggregationType.AVERAGE: AverageAggregation,
    AggregationType.SUM: SumAggregation,
    AggregationType.LAST: LastAggregation,
    AggregationType.FIRST: FirstAggregation,
    AggregationType.MIN: MinAggregation,
    AggregationType.MAX: MaxAggregation,
    AggregationType.COUNT: CountAggregation,
}


class CombineConfig(Schema):  # pylint: disable=too-few-public-methods
    """
    A filter that combines events in a stream.

    The events can be joined based on a key, so that all events with the same key are
    combined into a single event. For example:

        key: name
        aggregate:
          battery: average
          location: last

        Before:

            {"key": "a", "battery": 100},
            {"key": "a", "location": "home"},
            {"key": "a", "battery": 93, "location": "work"},
            {"key": "b", "battery": 14},

        After:

            {"key": "a", "battery": 96.5, "location": "work"},

    Note that key "b" is not emitted until an event with a different key is received.

    Possible aggregations are: average, sum, last, first, min, max, count.
    """

    key = fields.String(
        required=True,
        default=None,
        title="Key to aggregate events by",
        description=(
            "A key in the event value to aggregate events by. This assumes that the "
            "event value is a dictionary"
        ),
    )
    aggregate = fields.Dict(
        keys=fields.String(),
        values=fields.Enum(AggregationType),
        required=True,
        default=None,
        title="Columns and their aggregation",
        description=(
            "A dictionary mapping names of columns in the event value to an "
            "aggregation that should be used."
        ),
    )


@configuration_schema(CombineConfig())
async def combine(
    stream: Stream,
    key: str,
    aggregate: Dict[str, AggregationType],
    prefix: str = "hub.combine",
) -> Stream:
    """
    Combine events.
    """
    aggregators = {
        column: aggregation_map[aggregation]()
        for column, aggregation in aggregate.items()
    }
    current_key: Optional[str] = None
    value = {}
    async for event in stream:  # pragma: no cover
        # first event
        if current_key is None:
            current_key = event["value"][key]
            value = {
                column: aggregators[column](event["value"][column])
                for column in event["value"]
                if column in aggregators
            }
            continue

        # new event, same key
        if event["value"][key] == current_key:
            for column in event["value"]:
                if column in aggregators:
                    value[column] = aggregators[column](event["value"][column])
            continue

        # new key
        value[key] = current_key
        yield {
            "timestamp": datetime.now(timezone.utc),
            "name": f"{prefix}.{key}",
            "value": value,
        }
        current_key = event["value"][key]
        value = {
            column: aggregators[column](event["value"][column])
            for column in event["value"]
            if column in aggregators
        }
