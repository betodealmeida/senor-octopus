"""
Functions for building a DAG.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from asyncstdlib import itertools
from asyncstdlib.builtins import aiter as aiter_
from crontab import CronTab
from durations import Duration
from pkg_resources import iter_entry_points

from senor_octopus.exceptions import InvalidConfigurationException
from senor_octopus.lib import build_marshmallow_schema
from senor_octopus.types import (
    Event,
    FilterCallable,
    LoggerCallable,
    SinkCallable,
    SourceCallable,
    Stream,
)


async def log_events(stream: Stream, flow: str, log: LoggerCallable) -> Stream:
    """
    Log all events going through a stream.
    """
    async for event in stream:
        log("%s: %s", flow, event)
        yield event


class Node:  # pylint: disable=too-few-public-methods
    """
    A node.
    """

    def __init__(self, node_name: str):
        self.name = node_name

        self.next: Set[Union["Filter", "Sink"]] = set()
        self._logger = logging.getLogger(node_name)
        self._event_logger = logging.getLogger("senor_octopus.events")

    @staticmethod
    def build(
        node_name: str,
        section: Dict[str, Any],
    ) -> Union["Source", "Filter", "Sink"]:
        """
        Build a node from the configuration YAML.
        """
        # load plugin
        try:
            plugin_name = section.pop("plugin")
        except KeyError as ex:
            raise InvalidConfigurationException(
                "Invalid config, missing `plugin` key",
            ) from ex
        try:
            plugin = next(
                iter_entry_points("senor_octopus.plugins", plugin_name),
            ).load()
        except StopIteration as ex:
            raise InvalidConfigurationException(
                f"Invalid plugin name `{plugin_name}`",
            ) from ex

        if not hasattr(plugin, "configuration_schema"):
            plugin.configuration_schema = build_marshmallow_schema(plugin)

        kwargs = section.copy()
        flow = kwargs.pop("flow").strip()

        if flow.startswith("->"):
            plugin = cast(SourceCallable, plugin)
            return Source(node_name, plugin, **kwargs)

        if flow.endswith("->"):
            plugin = cast(SinkCallable, plugin)
            return Sink(node_name, plugin, **kwargs)

        plugin = cast(FilterCallable, plugin)
        return Filter(node_name, plugin, **kwargs)


class Source(Node):
    """
    A source node.

    A source node has no parents, and can optionally have a schedule for it to
    run periodically, cascading the events down the graph.
    """

    def __init__(
        self,
        node_name: str,
        plugin: SourceCallable,
        schedule: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(node_name)

        self.plugin = plugin
        self.schedule = CronTab(schedule) if schedule else None
        self.kwargs = plugin.configuration_schema.load(kwargs)

    async def run(self) -> None:
        """
        Run the source node.

        This will call the source node plugin to fetch events, and pass them
        down to children.
        """
        self._logger.info("Running")
        downstream = self.plugin(**self.kwargs)
        async with itertools.tee(downstream, n=len(self.next)) as streams:
            for node, stream_copy in zip(self.next, streams):
                logged_stream = log_events(
                    stream_copy,
                    f"{self.name} -> {node.name}",
                    self._event_logger.debug,
                )
                await node.run(logged_stream)


class Filter(Node):
    """
    A filter node.

    Filters will receive events from their parents, and can return them down
    to their children, modified or filtered.
    """

    def __init__(self, node_name: str, plugin: FilterCallable, **kwargs: Any):
        super().__init__(node_name)

        self.plugin = plugin
        self.kwargs = plugin.configuration_schema.load(kwargs)

    async def run(self, stream: Stream) -> None:
        """
        Run the filter node.

        This will receive a stream from the parent(s), process events,
        potentially modifying and/or filtering them.
        """
        self._logger.info("Running")
        downstream = self.plugin(stream, **self.kwargs)
        async with itertools.tee(downstream, n=len(self.next)) as streams:
            for node, stream_copy in zip(self.next, streams):
                logged_stream = log_events(
                    stream_copy,
                    f"{self.name} -> {node.name}",
                    self._event_logger.debug,
                )
                await node.run(logged_stream)


class Sink(Node):
    """
    A sink node.

    Sink nodes receive events and consume them, storing in databases, sending
    them over SMS, etc.
    """

    def __init__(
        self,
        node_name: str,
        plugin: SinkCallable,
        throttle: Optional[str] = None,
        batch: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(node_name)

        self.plugin = plugin
        self.throttle = Duration(throttle).to_seconds() if throttle else None
        self.batch = Duration(batch).to_seconds() if batch else None
        self.kwargs = plugin.configuration_schema.load(kwargs)

        self.last_run: Optional[float] = None
        self.queue: asyncio.Queue = asyncio.Queue()
        self.task = asyncio.create_task(self.worker())

    async def run(self, stream: Stream) -> None:
        """
        Run the sink node.

        This will receive a stream from the parent(s), process events.

        When running in batch mode the events will be stored in a queue
        instead, so that events are processed in batch periodically.

        The source node can also be throttled, so that it doesn't run too
        often, dropping events if necessary.
        """
        loop = asyncio.get_running_loop()

        if (
            self.last_run is not None
            and self.throttle
            and loop.time() - self.last_run < self.throttle
        ):
            self._logger.info(
                "Last run was %s, skipping this one due to throttle",
                self.last_run,
            )
            return

        self._logger.info("Running")
        stream = self.run_and_update_last_run(stream)

        # when in batch mode, send events to queue for worker to process
        if self.batch:
            self._logger.info("Sending events to queue")
            async for event in stream:  # pragma: no cover
                self.queue.put_nowait(event)
        else:
            self._logger.info("Processing events")
            await self.plugin(stream, **self.kwargs)  # type: ignore

    async def run_and_update_last_run(self, stream: Stream) -> Stream:
        """
        Run the sink node and store the time so events can be throttled.
        """
        loop = asyncio.get_running_loop()

        at_least_one = False
        async for event in stream:  # pragma: no cover
            at_least_one = True
            yield event

        if at_least_one:
            self.last_run = loop.time()

    async def worker(self) -> None:
        """
        An async worker that processes events in batch.
        """
        if self.batch is None:
            return

        loop = asyncio.get_running_loop()
        canceled = False
        while not canceled:
            # consume queue into a new stream
            stream: List[Event] = []
            batch_start: Optional[float] = None
            while True:
                now = loop.time()

                timeout: Optional[float]
                if batch_start is None:
                    # batch hasn't started, we can wait forever on a new event
                    timeout = None
                else:
                    # wait on new event while the batch lasts
                    timeout = batch_start + self.batch - now

                try:
                    event = await asyncio.wait_for(self.queue.get(), timeout)
                except asyncio.TimeoutError:
                    break
                except RuntimeError:
                    return
                except asyncio.CancelledError:
                    self._logger.info("Canceled, dumping currently batched events")
                    canceled = True
                    break

                # first event in a batch?
                if batch_start is None:
                    self._logger.info("Received event, starting a new batch")
                    batch_start = loop.time()

                stream.append(event)
                self.queue.task_done()

            self._logger.info("Processing batch")
            await self.plugin(aiter_(stream), **self.kwargs)  # type: ignore


def connected(config, source, target) -> bool:
    """
    Check if two nodes are connected in the DAG.
    """
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


def build_dag(config: Dict[str, Any]) -> Set[Source]:
    """
    Build the DAG from the configuration.
    """
    sections = set(config)
    for section in sections:
        if "flow" not in config[section]:
            raise InvalidConfigurationException("Invalid config, missing `flow` key")

    sources = {
        name for name in sections if config[name]["flow"].strip().startswith("->")
    }
    sinks = {name for name in sections if config[name]["flow"].strip().endswith("->")}
    filters = sections - sources - sinks

    dag: Set[Source] = set()
    seen: Dict[str, Node] = {}
    queue: List[Tuple[Optional[str], str]] = [(None, name) for name in sources]
    while queue:
        source, target = queue.pop()
        if target in seen:
            node = seen[target]
        else:
            node = Node.build(target, config[target])
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
