"""
Tests for the CLI.
"""

import asyncio
import logging
import sys
from unittest import mock

import pytest

from senor_octopus.cli import main, parse_args, run, setup_logging


def test_parse_args() -> None:
    """
    Test ``parse_args``.
    """
    with pytest.raises(SystemExit) as excinfo:
        parse_args(["--version"])
    assert str(excinfo.value) == "0"

    parser = parse_args(["config.yaml", "-vv"])
    assert parser.f == "config.yaml"
    assert parser.loglevel == logging.DEBUG

    parser = parse_args(["config.yaml", "-v"])
    assert parser.f == "config.yaml"
    assert parser.loglevel == logging.INFO


def test_setup_logging(mocker) -> None:
    """
    Test ``setup_logging``.
    """
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
    """
    Test ``main``.
    """
    mocker.patch("senor_octopus.cli.yaml")
    mocker.patch("senor_octopus.cli.build_dag")
    mocker.patch("senor_octopus.cli.open")

    mock_scheduler = mock.MagicMock()
    mock_scheduler.return_value.run = mocker.AsyncMock()
    mocker.patch("senor_octopus.cli.Scheduler", mock_scheduler)

    await main(["config.yaml"])

    mock_scheduler.return_value.run.assert_called()


@pytest.mark.asyncio
async def test_main_dryrun(mocker) -> None:
    """
    Test a dry run.
    """
    mocker.patch("senor_octopus.cli.yaml")
    mocker.patch("senor_octopus.cli.build_dag")
    mocker.patch("senor_octopus.cli.open")

    mock_scheduler = mock.MagicMock()
    mock_scheduler.return_value.run = mocker.AsyncMock()
    mocker.patch("senor_octopus.cli.Scheduler", mock_scheduler)

    await main(["config.yaml", "--dry-run"])

    mock_scheduler.return_value.run.assert_not_called()


@pytest.mark.asyncio
async def test_main_canceled(mocker) -> None:
    """
    Test canceling the `main` function.
    """
    mocker.patch("senor_octopus.cli.yaml")
    mocker.patch("senor_octopus.cli.build_dag")
    mocker.patch("senor_octopus.cli.open")

    mock_scheduler = mock.MagicMock()
    mock_scheduler.return_value.run = mocker.AsyncMock()
    mock_scheduler.return_value.run.side_effect = asyncio.CancelledError("Canceled")
    mocker.patch("senor_octopus.cli.Scheduler", mock_scheduler)

    await main(["config.yaml"])

    mock_scheduler.return_value.cancel.assert_called()


def test_run(mocker) -> None:
    """
    Test `run`.
    """
    mock_main = mocker.AsyncMock()
    mocker.patch("senor_octopus.cli.main", mock_main)
    mocker.patch("senor_octopus.cli.sys.argv", ["srocto", "config.yaml", "-vv"])

    run()

    mock_main.assert_called_with(["config.yaml", "-vv"])


def test_interrupt(mocker) -> None:
    """
    Test interrupting `run`.
    """
    mock_main = mocker.AsyncMock()
    mock_main.side_effect = KeyboardInterrupt()
    mocker.patch("senor_octopus.cli.main", mock_main)
    mocker.patch("senor_octopus.cli.sys.argv", ["srocto", "config.yaml", "-vv"])
    mock_logger = mocker.patch("senor_octopus.cli._logger")

    run()

    mock_logger.info.assert_called_with("Stopping Sr. Octopus")
