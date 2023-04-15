from datetime import datetime
from typing import Any, AsyncGenerator

from typing_extensions import Protocol, TypedDict


class Event(TypedDict):
    timestamp: datetime
    name: str
    value: Any


Stream = AsyncGenerator[Event, None]


class SourceCallable(Protocol):
    def __call__(self, **kwargs: Any) -> Stream:
        ...  # pragma: no cover


class FilterCallable(Protocol):
    def __call__(self, stream: Stream, **kwargs: Any) -> Stream:
        ...  # pragma: no cover


class SinkCallable(Protocol):
    def __call__(self, stream: Stream, **kwargs: Any) -> None:
        ...  # pragma: no cover


class LoggerCallable(Protocol):
    def __call__(self, msg: str, *args: Any) -> None:
        ...  # pragma: no cover
