"""
Tests for the DAP functions.
"""

import asyncio
import random
from typing import cast

import aiotools
import pytest
import yaml
from freezegun import freeze_time

from senor_octopus.graph import Sink, Source, build_dag, connected


def test_connected() -> None:
    """
    Test the ``connected`` function.
    """
    config = {
        "a": {"flow": "-> *"},
        "b": {"flow": "-> c"},
        "c": {"flow": "* -> d, e"},
        "d": {"flow": "* ->"},
        "e": {"flow": "c, b ->"},
    }
    assert not connected(config, "a", "b")
    assert connected(config, "a", "c")
    assert connected(config, "a", "d")
    assert not connected(config, "a", "e")
    assert not connected(config, "b", "a")
    assert connected(config, "b", "c")
    assert not connected(config, "b", "d")
    assert not connected(config, "b", "e")
    assert not connected(config, "c", "a")
    assert not connected(config, "c", "b")
    assert connected(config, "c", "d")
    assert connected(config, "c", "e")

    # connections have a direction
    assert not connected(config, "d", "a")
    assert not connected(config, "d", "b")
    assert not connected(config, "d", "c")
    assert not connected(config, "d", "e")
    assert not connected(config, "e", "a")
    assert not connected(config, "e", "b")
    assert not connected(config, "e", "c")
    assert not connected(config, "e", "d")


@pytest.mark.asyncio
async def test_build_dag(mock_config) -> None:
    """
    The the ``build_dag`` function.
    """
    dag = build_dag(mock_config)
    assert len(dag) == 1

    source = dag.pop()
    assert isinstance(source, Source)
    assert len(source.next) == 2


@pytest.mark.asyncio
async def test_build_dag_many_to_one() -> None:
    """
    Test ``build_dag`` with a many-to-one relationship.
    """
    config = yaml.load(
        """
one:
  plugin: source.random
  flow: -> three

two:
  plugin: source.random
  flow: -> three

three:
  plugin: sink.log
  flow: "* ->"
    """,
        Loader=yaml.SafeLoader,
    )
    dag = build_dag(config)
    assert len(dag) == 2

    one, two = dag
    assert one.next == two.next


def test_build_dag_missing_plugin() -> None:
    """
    Test ``build_dag`` with a missing plugin.
    """
    config = yaml.load(
        """
a:
  flow: -> *
    """,
        Loader=yaml.SafeLoader,
    )
    with pytest.raises(Exception) as excinfo:
        build_dag(config)
    assert str(excinfo.value) == "Invalid config, missing `plugin` key"


@pytest.mark.asyncio
async def test_build_dag_seen() -> None:
    """
    Test that ``build_dag`` doesn't get stuck in a loop.
    """
    config = yaml.load(
        """
a:
  flow: -> *
  plugin: source.random

b:
  flow: -> *
  plugin: source.random

c:
  flow: "* ->"
  plugin: sink.log
    """,
        Loader=yaml.SafeLoader,
    )
    build_dag(config)


def test_build_dag_missing_flow() -> None:
    """
    Test ``build_dag`` with a missing flow argument.
    """
    config = yaml.load(
        """
a:
  plugin: source.random
    """,
        Loader=yaml.SafeLoader,
    )
    with pytest.raises(Exception) as excinfo:
        build_dag(config)
    assert str(excinfo.value) == "Invalid config, missing `flow` key"


def test_build_dag_invalid_plugin() -> None:
    """
    Test ``build_dag`` with an invalid plugin.
    """
    config = yaml.load(
        """
a:
  plugin: source.invalid
  flow: -> *
    """,
        Loader=yaml.SafeLoader,
    )
    with pytest.raises(Exception) as excinfo:
        build_dag(config)
    assert str(excinfo.value) == "Invalid plugin name `source.invalid`"


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_run_source(mocker, mock_config) -> None:
    """
    Test running sources.
    """
    logging = mocker.patch("senor_octopus.sinks.log.logging")
    _logger = logging.getLogger()
    random.seed(42)

    dag = build_dag(mock_config)
    source = dag.pop()

    await source.run()
    assert len(_logger.log.mock_calls) == 14

    # test throttle, should get 10 entries from the non-throttled sink
    await source.run()
    assert len(_logger.log.mock_calls) == 24


@pytest.mark.asyncio
async def test_batch(mocker) -> None:
    """
    Test batch mode.
    """
    logging = mocker.patch("senor_octopus.sinks.log.logging")
    _logger = logging.getLogger()
    vclock = aiotools.VirtualClock()

    config = yaml.load(
        """
random:
  plugin: source.random
  flow: -> log
  schedule: "* * * * *"

log:
  plugin: sink.log
  flow: random ->
  batch: 2 minutes
    """,
        Loader=yaml.SafeLoader,
    )

    with vclock.patch_loop():
        dag = build_dag(config)
        source = dag.pop()

        await source.run()
        assert len(_logger.log.mock_calls) == 0

        await asyncio.sleep(180)
        assert len(_logger.log.mock_calls) == 10


@pytest.mark.asyncio
async def test_batch_empty_source(mocker) -> None:
    """
    Test batch mode when no plugins are configured in batch mode.
    """
    logging = mocker.patch("senor_octopus.sinks.log.logging")
    _logger = logging.getLogger()
    vclock = aiotools.VirtualClock()

    config = yaml.load(
        """
random:
  plugin: source.random
  flow: -> log
  schedule: "* * * * *"
  events: 0

log:
  plugin: sink.log
  flow: random ->
  batch: 2 minutes
    """,
        Loader=yaml.SafeLoader,
    )

    with vclock.patch_loop():
        dag = build_dag(config)
        source = dag.pop()

        await source.run()
        assert len(_logger.log.mock_calls) == 0

        await asyncio.sleep(180)
        assert len(_logger.log.mock_calls) == 0


@pytest.mark.asyncio
async def test_throttle(mocker) -> None:
    """
    Test throttle mode.
    """
    logging = mocker.patch("senor_octopus.sinks.log.logging")
    _logger = logging.getLogger()
    vclock = aiotools.VirtualClock()

    config = yaml.load(
        """
random:
  plugin: source.random
  flow: -> log
  schedule: "* * * * *"
  events: 1

log:
  plugin: sink.log
  flow: random ->
  throttle: 2 minutes
    """,
        Loader=yaml.SafeLoader,
    )

    with vclock.patch_loop():
        dag = build_dag(config)
        source = dag.pop()
        sink = list(source.next)[0]

        sink = cast(Sink, sink)
        assert sink.last_run is None

        await source.run()
        assert len(_logger.log.mock_calls) == 1
        assert sink.last_run == 0.0

        await asyncio.sleep(60)
        await source.run()
        assert len(_logger.log.mock_calls) == 1
        assert sink.last_run == 0.0

        await asyncio.sleep(60)
        await source.run()
        assert len(_logger.log.mock_calls) == 2
        assert sink.last_run == 120.0

        await asyncio.sleep(90)
        await source.run()
        assert len(_logger.log.mock_calls) == 2
        assert sink.last_run == 120.0

        await asyncio.sleep(60)
        await source.run()
        assert len(_logger.log.mock_calls) == 3
        assert sink.last_run == 270.0


@pytest.mark.asyncio
async def test_throttle_without_events(mocker) -> None:
    """
    Test throttle mode when no events happen.
    """
    logging = mocker.patch("senor_octopus.sinks.log.logging")
    _logger = logging.getLogger()
    vclock = aiotools.VirtualClock()

    config = yaml.load(
        """
random:
  plugin: source.random
  flow: -> log
  schedule: "* * * * *"
  events: 0

log:
  plugin: sink.log
  flow: random ->
  throttle: 2 minutes
    """,
        Loader=yaml.SafeLoader,
    )

    with vclock.patch_loop():
        dag = build_dag(config)
        source = dag.pop()
        sink = list(source.next)[0]

        sink = cast(Sink, sink)
        assert sink.last_run is None

        await source.run()
        assert len(_logger.log.mock_calls) == 0
        assert sink.last_run is None


@pytest.mark.asyncio
async def test_batch_cancel(mocker) -> None:
    """
    Test that batch events are processed when the scheduler is canceled.
    """
    logging = mocker.patch("senor_octopus.sinks.log.logging")
    _logger = logging.getLogger()
    vclock = aiotools.VirtualClock()

    config = yaml.load(
        """
random:
  plugin: source.random
  flow: -> log
  schedule: "* * * * *"
  events: 0

log:
  plugin: sink.log
  flow: random ->
  batch: 2 minutes
    """,
        Loader=yaml.SafeLoader,
    )

    with vclock.patch_loop():
        dag = build_dag(config)
        source = dag.pop()
        sink = list(source.next)[0]

        sink = cast(Sink, sink)
        sink.queue = mocker.MagicMock()
        sink.queue.get = mocker.AsyncMock(  # type: ignore
            side_effect=[0, 1, 2, asyncio.CancelledError("Cancelled")],
        )

        await source.run()
        assert len(_logger.log.mock_calls) == 0

        await asyncio.sleep(1800)
        assert len(_logger.log.mock_calls) == 3
