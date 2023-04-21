"""
Señor Octopus types.
"""

# pylint: disable=too-few-public-methods

from datetime import datetime
from typing import Any, AsyncGenerator

from marshmallow import Schema
from typing_extensions import Protocol, TypedDict


class Event(TypedDict):
    """
    An event.

    This is the basic data structure that is passed between the various
    nodes.
    """

    timestamp: datetime
    name: str
    value: Any


Stream = AsyncGenerator[Event, None]


class SourceCallable(Protocol):
    """
    A function that acts as a source.
    """

    configuration_schema: Schema

    def __call__(self, **kwargs: Any) -> Stream:
        ...  # pragma: no cover


class FilterCallable(Protocol):
    """
    A function that acts as a filter.
    """

    configuration_schema: Schema

    def __call__(self, stream: Stream, **kwargs: Any) -> Stream:
        ...  # pragma: no cover


class SinkCallable(Protocol):
    """
    A function that acts as a sink.
    """

    configuration_schema: Schema

    def __call__(self, stream: Stream, **kwargs: Any) -> None:
        ...  # pragma: no cover


class LoggerCallable(Protocol):
    """
    A function that acts as a logger.
    """

    def __call__(self, msg: str, flow: str, event: Event) -> None:
        ...  # pragma: no cover
