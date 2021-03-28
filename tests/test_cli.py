import asyncio
import logging
import sys
from unittest import mock

import pytest
from asynctest import CoroutineMock
from senor_octopus.cli import main
from senor_octopus.cli import parse_args
from senor_octopus.cli import run
from senor_octopus.cli import setup_logging


def test_parse_args() -> None:
    with pytest.raises(SystemExit) as excinfo:
        parse_args(["--version"])
    assert str(excinfo.value) == "0"

    parser = parse_args(["config.ini", "-vv"])
    assert parser.f == "config.ini"
    assert parser.loglevel == logging.DEBUG

    parser = parse_args(["config.ini", "-v"])
    assert parser.f == "config.ini"
    assert parser.loglevel == logging.INFO


def test_setup_logging(mocker, capfd) -> None:
    mock_logging = mock.MagicMock()
    mocker.patch("senor_octopus.cli.logging", mock_logging)

    setup_logging(logging.WARNING)

    mock_logging.basicConfig.assert_called_with(
        level=logging.WARNING,
        stream=sys.stdout,
        format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@pytest.mark.asyncio
async def test_main(mocker) -> None:
    mocker.patch("senor_octopus.cli.CaseConfigParser")
    mocker.patch("senor_octopus.cli.build_dag")

    mock_scheduler = mock.MagicMock()
    mock_scheduler.return_value.run = CoroutineMock()
    mocker.patch("senor_octopus.cli.Scheduler", mock_scheduler)

    await main(["config.ini"])

    mock_scheduler.return_value.run.assert_called()


@pytest.mark.asyncio
async def test_main_canceled(mocker) -> None:
    mocker.patch("senor_octopus.cli.CaseConfigParser")
    mocker.patch("senor_octopus.cli.build_dag")

    mock_scheduler = mock.MagicMock()
    mock_scheduler.return_value.run = CoroutineMock()
    mock_scheduler.return_value.run.side_effect = asyncio.CancelledError("Canceled")
    mocker.patch("senor_octopus.cli.Scheduler", mock_scheduler)

    await main(["config.ini"])

    mock_scheduler.return_value.cancel.assert_called()


def test_run(mocker) -> None:
    mock_main = CoroutineMock()
    mocker.patch("senor_octopus.cli.main", mock_main)
    mocker.patch("senor_octopus.cli.sys.argv", ["srocto", "config.ini", "-vv"])

    run()

    mock_main.assert_called_with(["config.ini", "-vv"])


def test_interrupt(mocker) -> None:
    mock_main = CoroutineMock()
    mock_main.side_effect = KeyboardInterrupt()
    mocker.patch("senor_octopus.cli.main", mock_main)
    mocker.patch("senor_octopus.cli.sys.argv", ["srocto", "config.ini", "-vv"])
    mock_logger = mocker.MagicMock()
    mocker.patch("senor_octopus.cli._logger", mock_logger)

    run()

    assert mock_logger.info.called_with("Stopping Sr. Octopus")
