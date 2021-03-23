import random
from typing import Dict
from unittest import mock

import pytest
from freezegun import freeze_time
from senor_octopus.cli import CaseConfigParser
from senor_octopus.graph import build_dag
from senor_octopus.graph import connected
from senor_octopus.graph import Source


def test_connected() -> None:
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
    assert not connected(config, "d", "a")
    assert not connected(config, "d", "b")
    assert not connected(config, "d", "c")
    assert not connected(config, "d", "e")
    assert not connected(config, "e", "a")
    assert not connected(config, "e", "b")
    assert not connected(config, "e", "c")
    assert not connected(config, "e", "d")


def test_build_dag(mock_config) -> None:
    dag = build_dag(mock_config)
    assert len(dag) == 1

    source = dag.pop()
    assert isinstance(source, Source)
    assert len(source.next) == 2


def test_build_dag_missing_plugin() -> None:
    config = CaseConfigParser()
    config.read_string(
        """
        [a]
        flow = -> *
    """,
    )
    with pytest.raises(Exception) as excinfo:
        build_dag(config)
    assert str(excinfo.value) == "Invalid config, missing `plugin` key"


def test_build_dag_seen() -> None:
    config = CaseConfigParser()
    config.read_string(
        """
        [a]
        flow = -> *
        plugin = source.random

        [b]
        flow = -> *
        plugin = source.random

        [c]
        flow = * ->
        plugin = sink.log
    """,
    )
    build_dag(config)


def test_build_dag_missing_flow() -> None:
    config = CaseConfigParser()
    config.read_string(
        """
        [a]
        plugin = source.random
    """,
    )
    with pytest.raises(Exception) as excinfo:
        build_dag(config)
    assert str(excinfo.value) == "Invalid config, missing `flow` key"


def test_build_dag_invalid_plugin() -> None:
    config = CaseConfigParser()
    config.read_string(
        """
        [a]
        plugin = source.invalid
        flow = -> *
    """,
    )
    with pytest.raises(Exception) as excinfo:
        build_dag(config)
    assert str(excinfo.value) == "Invalid plugin name `source.invalid`"


def test_build_dag_environ(mocker) -> None:
    mock_env: Dict[str, str] = {}
    mocker.patch("senor_octopus.graph.os.environ", mock_env)

    config = CaseConfigParser()
    config.read_string(
        """
        [a]
        flow = -> *
        plugin = source.random
        A_ENV_VAR = 1
    """,
    )
    build_dag(config)
    assert mock_env == {"A_ENV_VAR": "1"}


@freeze_time("2021-01-01")
@pytest.mark.asyncio
async def test_run_source(mocker, mock_config) -> None:
    mock_logger = mock.MagicMock()
    mocker.patch("senor_octopus.sinks.log._logger", mock_logger)
    random.seed(42)

    dag = build_dag(mock_config)
    source = dag.pop()

    await source.run()
    assert len(mock_logger.log.mock_calls) == 14

    # test throttle, should get 10 entries from the non-throttled sink
    await source.run()
    assert len(mock_logger.log.mock_calls) == 24
