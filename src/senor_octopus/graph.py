import asyncio
import logging
from typing import Any
from typing import cast
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

from asyncstdlib import itertools
from asyncstdlib.builtins import aiter
from crontab import CronTab
from durations import Duration
from pkg_resources import iter_entry_points
from senor_octopus.types import Event
from senor_octopus.types import FilterCallable
from senor_octopus.types import LoggerCallable
from senor_octopus.types import SinkCallable
from senor_octopus.types import SourceCallable
from senor_octopus.types import Stream


async def log_events(stream: Stream, flow: str, log: LoggerCallable) -> Stream:
    async for event in stream:
        log("%s: %s", flow, event)
        yield event


class Node:
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

        kwargs = section.copy()
        flow = kwargs.pop("flow").strip()
        if flow.startswith("->"):
            return Source(node_name, plugin, **kwargs)
        if flow.endswith("->"):
            return Sink(node_name, plugin, **kwargs)
        return Filter(node_name, plugin, **kwargs)


class Source(Node):
    def __init__(
        self,
        node_name: str,
        plugin: SourceCallable,
        schedule: Optional[str] = None,
        **extra_kwargs: Any,
    ):
        super().__init__(node_name)
        self.plugin = plugin
        self.schedule = CronTab(schedule) if schedule else None
        self.extra_kwargs = extra_kwargs

    async def run(self) -> None:
        self._logger.info("Running")
        stream = self.plugin(**self.extra_kwargs)
        async with itertools.tee(stream, n=len(self.next)) as streams:
            for node, stream in zip(self.next, streams):
                stream = log_events(
                    stream,
                    f"{self.name} -> {node.name}",
                    self._event_logger.debug,
                )
                await node.run(stream)


class Filter(Node):
    def __init__(self, node_name: str, plugin: FilterCallable, **extra_kwargs: Any):
        super().__init__(node_name)
        self.plugin = plugin
        self.extra_kwargs = extra_kwargs

    async def run(self, stream: Stream) -> None:
        self._logger.info("Running")
        stream = self.plugin(stream, **self.extra_kwargs)
        async with itertools.tee(stream, n=len(self.next)) as streams:
            for node, stream in zip(self.next, streams):
                stream = log_events(
                    stream,
                    f"{self.name} -> {node.name}",
                    self._event_logger.debug,
                )
                await node.run(stream)


class Sink(Node):
    def __init__(
        self,
        node_name: str,
        plugin: SinkCallable,
        throttle: Optional[str] = None,
        batch: Optional[str] = None,
        **extra_kwargs: Any,
    ):
        super().__init__(node_name)
        self.plugin = plugin
        self.throttle = Duration(throttle).to_seconds() if throttle else None
        self.batch = Duration(batch).to_seconds() if batch else None
        self.extra_kwargs = extra_kwargs

        self.last_run: Optional[float] = None
        self.queue: asyncio.Queue = asyncio.Queue()
        self.task = asyncio.create_task(self.worker())

    async def run(self, stream: Stream) -> None:
        loop = asyncio.get_running_loop()

        if (
            self.last_run is not None
            and self.throttle
            and loop.time() - self.last_run <= self.throttle
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
            await self.plugin(stream, **self.extra_kwargs)  # type: ignore

    async def run_and_update_last_run(self, stream: Stream) -> Stream:
        loop = asyncio.get_running_loop()

        at_least_one = False
        async for event in stream:  # pragma: no cover
            at_least_one = True
            yield event

        if at_least_one:
            self.last_run = loop.time()

    async def worker(self) -> None:
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
                    self._logger.info("Cancelled, dumping currently batched events")
                    canceled = True
                    break

                # first event in a batch?
                if batch_start is None:
                    self._logger.info("Received event, starting a new batch")
                    batch_start = loop.time()

                stream.append(event)
                self.queue.task_done()

            self._logger.info("Processing batch")
            await self.plugin(aiter(stream), **self.extra_kwargs)  # type: ignore


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


def build_dag(config: Dict[str, Any]) -> Set[Source]:
    sections = set(config)
    for section in sections:
        if "flow" not in config[section]:
            raise Exception("Invalid config, missing `flow` key")

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
