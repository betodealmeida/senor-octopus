from datetime import datetime
from typing import Any
from typing import Iterator

from typing_extensions import Protocol
from typing_extensions import TypedDict


class Event(TypedDict):
    timestamp: datetime
    name: str
    value: float


Stream = Iterator[Event]


class SourceCallable(Protocol):
    def __call__(self, **kwargs: Any) -> Stream:
        ...


class FilterCallable(Protocol):
    def __call__(self, stream: Stream, **kwargs: Any) -> Stream:
        ...


class SinkCallable(Protocol):
    def __call__(self, stream: Stream, **kwargs: Any) -> None:
        ...
