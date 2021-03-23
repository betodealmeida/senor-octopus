from jsonpath import JSONPath
from senor_octopus.types import Stream


def jsonpath(stream: Stream, filter: str) -> Stream:
    """
    Filter event stream based on a JSON path.
    """
    yield from JSONPath(filter).parse({"events": list(stream)})
