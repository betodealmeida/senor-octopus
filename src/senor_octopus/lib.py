"""
Helper functions for Señor Octopus.
"""

from __future__ import annotations

import asyncio
from asyncio.futures import Future
from io import StringIO
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union

import asciidag.graph
import asciidag.node
from asyncstdlib.builtins import anext as anext_
from marshmallow import Schema

from senor_octopus.graph import Node, Source
from senor_octopus.types import Event, Stream


def flatten(
    obj: Dict[str, Any],
    prefix: str = "",
    sep: str = ".",
) -> Dict[str, Union[str, int, float]]:
    """
    Flatten a nested dictionary.

    This will flatten a dictionary with nested dictionaries, combining the keys
    with a period.
    """
    items: List[Tuple[str, Union[str, int, float]]] = []
    for key, value in obj.items():
        new_key = sep.join((prefix, key)) if prefix else key
        if isinstance(value, dict):
            items.extend(flatten(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def render_dag(dag: Set[Source], **kwargs: Any) -> str:
    """
    Render a DAG as an ASCII graph.
    """
    out = StringIO()
    graph = asciidag.graph.Graph(out, **kwargs)
    asciidag_nodes: Dict[str, asciidag.node.Node] = {}
    tips = sorted(
        [build_asciidag(node, asciidag_nodes) for node in dag],
        key=lambda n: n.item,
    )

    graph.show_nodes(tips)
    out.seek(0)
    return out.getvalue()


def build_asciidag(
    node: Node,
    asciidag_nodes: Dict[str, asciidag.node.Node],
) -> asciidag.node.Node:
    """
    Build an asciidag node from a Node.
    """
    if node.name in asciidag_nodes:
        asciidag_node = asciidag_nodes[node.name]
    else:
        asciidag_node = asciidag.node.Node(node.name)
        asciidag_nodes[node.name] = asciidag_node

    asciidag_node.parents = sorted(
        [build_asciidag(child, asciidag_nodes) for child in node.next],
        key=lambda n: n.item,
    )

    return asciidag_node


async def merge_streams(*streams: Stream) -> Stream:
    """
    Merge multiple streams into a single stream.
    """
    streams_next: Dict[
        Stream,
        Optional[Future[Event]],
    ] = {stream: None for stream in streams}
    stream_map: Dict[Future[Event], Stream] = {}
    while streams_next:
        for stream, next_ in streams_next.items():
            if next_ is None:
                future = asyncio.ensure_future(anext_(stream))
                stream_map[future] = stream
                streams_next[stream] = future

        done, pending = await asyncio.wait(  # pylint: disable=unused-variable
            {stream for stream in streams_next.values() if stream},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for future in done:
            # clear message in each completed stream
            stream = stream_map[future]
            streams_next[stream] = None

            try:
                event = future.result()
            except StopAsyncIteration:
                del streams_next[stream]
                continue
            yield event


Plugin = TypeVar("Plugin", bound=Callable[..., Optional[Stream]])


def configuration_schema(schema: Schema) -> Callable[[Plugin], Plugin]:
    """
    Attach a schema to a plugin.
    """

    def decorator(plugin: Plugin) -> Plugin:
        plugin.configuration_schema = schema  # type: ignore
        return plugin

    return decorator
