from jsonpath import JSONPath
from senor_octopus.types import Stream


async def jsonpath(stream: Stream, filter: str) -> Stream:
    """
    Filter event stream based on a JSON path.
    """
    events = [event async for event in stream]
    for event in JSONPath(filter).parse({"events": events}):
        yield event
