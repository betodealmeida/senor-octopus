from datetime import datetime
from typing import Any
from typing import AsyncGenerator

from typing_extensions import Protocol
from typing_extensions import TypedDict


class Event(TypedDict):
    timestamp: datetime
    name: str
    value: Any


Stream = AsyncGenerator[Event, None]


class SourceCallable(Protocol):
    def __call__(self, **kwargs: Any) -> Stream:
        ...


class FilterCallable(Protocol):
    def __call__(self, stream: Stream, **kwargs: Any) -> Stream:
        ...


class SinkCallable(Protocol):
    def __call__(self, stream: Stream, **kwargs: Any) -> None:
        ...
