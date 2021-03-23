import configparser
import os
import re
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import cast
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from asyncstdlib import itertools
from crontab import CronTab
from durations import Duration
from pkg_resources import iter_entry_points
from senor_octopus.types import Event
from senor_octopus.types import FilterCallable
from senor_octopus.types import SinkCallable
from senor_octopus.types import SourceCallable
from senor_octopus.types import Stream


class Node:
    def __init__(self, name: str):
        self.name = name
        self.next: Set[Union["Filter", "Sink"]] = set()

    @staticmethod
    def build(name: str, section: Dict[str, Any]) -> Union["Source", "Filter", "Sink"]:
        # load plugin
        try:
            plugin_name = section.pop("plugin")
        except KeyError:
            raise Exception("Invalid config, missing `plugin` key")
        try:
            plugin = next(
                iter_entry_points("senor_octopus.plugins", plugin_name),
            ).load()
        except StopIteration:
            raise Exception(f"Invalid plugin name `{plugin_name}`")

        # all uppercase keys are environment variables
        for key in list(section):
            if re.match("[A-Z_]", key):
                os.environ[key] = section.pop(key)

        flow = section.pop("flow")
        if flow.startswith("->"):
            return Source(name, plugin, **section)
        if flow.endswith("->"):
            return Sink(name, plugin, **section)
        return Filter(name, plugin, **section)

    def __repr__(self) -> str:
        return (
            "\n".join(f"{self.name} -> {node!r}" for node in self.next)
            if self.next
            else self.name
        )


class Source(Node):
    def __init__(
        self,
        name: str,
        plugin: SourceCallable,
        schedule: Optional[str] = None,
        **extra_kwargs: Any,
    ):
        super().__init__(name)
        self.plugin = plugin
        self.schedule = CronTab(schedule) if schedule else None
        self.extra_kwargs = extra_kwargs

    async def run(self) -> None:
        stream = self.plugin(**self.extra_kwargs)
        async with itertools.tee(stream, n=len(self.next)) as streams:
            for node, stream in zip(self.next, streams):
                await node.run(stream)


class Filter(Node):
    def __init__(self, name: str, plugin: FilterCallable, **extra_kwargs: Any):
        super().__init__(name)
        self.plugin = plugin
        self.extra_kwargs = extra_kwargs

    async def run(self, stream: Stream) -> None:
        stream = self.plugin(stream, **self.extra_kwargs)
        async with itertools.tee(stream, n=len(self.next)) as streams:
            for node, stream in zip(self.next, streams):
                await node.run(stream)


class Sink(Node):
    def __init__(
        self,
        name: str,
        plugin: SinkCallable,
        throttle: Optional[str] = None,
        batch: Optional[str] = None,
        **extra_kwargs: Any,
    ):
        super().__init__(name)
        self.plugin = plugin
        self.throttle = (
            timedelta(seconds=Duration(throttle).to_seconds()) if throttle else None
        )
        self.batch = timedelta(seconds=Duration(batch).to_seconds()) if batch else None
        self.extra_kwargs = extra_kwargs

        self.last_run: Optional[datetime] = None
        self.buffer: List[Event] = []

    async def run(self, stream: Stream) -> None:
        if (
            self.last_run is not None
            and self.throttle
            and datetime.now() - self.last_run < self.throttle
        ):
            return

        await self.plugin(stream, **self.extra_kwargs)  # type: ignore
        self.last_run = datetime.now()


def connected(config, source, target) -> bool:
    targets = config[source]["flow"].split("->")[1].strip()
    if targets != "*" and target not in {
        target.strip() for target in targets.split(",")
    }:
        return False

    sources = config[target]["flow"].split("->")[0].strip()
    if sources != "*" and source not in {
        source.strip() for source in sources.split(",")
    }:
        return False

    return True


def build_dag(config: configparser.RawConfigParser) -> Set[Source]:
    sections = set(config.sections())
    for section in sections:
        if "flow" not in config[section]:
            raise Exception("Invalid config, missing `flow` key")

    sources = {name for name in sections if config[name]["flow"].startswith("->")}
    sinks = {name for name in sections if config[name]["flow"].endswith("->")}
    filters = sections - sources - sinks

    dag: Set[Source] = set()
    seen: Dict[str, Node] = {}
    queue: List[Tuple[Optional[str], str]] = [(None, name) for name in sources]
    while queue:
        source, target = queue.pop()
        if target in seen:
            continue

        node = Node.build(target, dict(config[target]))
        seen[target] = node

        if source:
            node = cast(Union[Filter, Sink], node)
            seen[source].next.add(node)
        else:
            node = cast(Source, node)
            dag.add(node)

        source = target
        for target in filters | sinks:
            if connected(config, source, target):
                queue.append((source, target))

    return dag
