"""
Tests for the scheduler.
"""

import asyncio
from unittest import mock

import aiotools
import pytest
from pytest_mock import MockerFixture

from senor_octopus.scheduler import Scheduler


@pytest.mark.asyncio
async def test_scheduler(mocker: MockerFixture) -> None:
    """
    Basic tests.
    """
    mock_source1 = mock.MagicMock()
    mock_source1.schedule.next.return_value = 10
    mock_source1.run = mocker.AsyncMock()
    mock_source1.run.side_effect = [None, None]
    mock_source2 = mock.MagicMock()
    mock_source2.schedule = None
    mock_source2.run = mocker.AsyncMock()
    mock_dag = {mock_source1, mock_source2}
    vclock = aiotools.VirtualClock()

    with vclock.patch_loop():
        scheduler = Scheduler(mock_dag)  # type: ignore
        with pytest.raises(Exception) as excinfo:
            await scheduler.run()

    assert str(excinfo.value) == "coroutine raised StopIteration"
    assert len(mock_source1.run.mock_calls) == 3


@pytest.mark.asyncio
async def test_scheduler_short_long(mocker: MockerFixture) -> None:
    """
    Test the scheduler with a short and a long job.
    """
    mock_source1 = mock.MagicMock()
    mock_source1.schedule.next.return_value = 10
    mock_source1.run = mocker.AsyncMock()
    mock_source1.run.side_effect = [None, None]
    mock_source2 = mock.MagicMock()
    mock_source2.schedule.next.return_value = 120
    mock_source2.run = mocker.AsyncMock()
    mock_dag = {mock_source1, mock_source2}
    vclock = aiotools.VirtualClock()

    with vclock.patch_loop():
        scheduler = Scheduler(mock_dag)  # type: ignore
        with pytest.raises(Exception) as excinfo:
            await scheduler.run()

    assert str(excinfo.value) == "coroutine raised StopIteration"
    assert len(mock_source1.run.mock_calls) == 3


@pytest.mark.asyncio
async def test_scheduler_cancel(mocker: MockerFixture) -> None:
    """
    Test that the schduler can be canceled.
    """
    mock_source1 = mock.MagicMock()
    mock_source1.schedule.next.return_value = 10
    mock_source1.run = mocker.AsyncMock()
    mock_dag = {mock_source1}
    vclock = aiotools.VirtualClock()

    async def cancel_scheduler(scheduler) -> None:
        await asyncio.sleep(30)
        scheduler.cancel()

    with vclock.patch_loop():
        scheduler = Scheduler(mock_dag)  # type: ignore
        await asyncio.gather(scheduler.run(), cancel_scheduler(scheduler))

    assert len(scheduler.tasks) == 1
    assert scheduler.cancelled
    assert len(mock_source1.run.mock_calls) == 2


@pytest.mark.asyncio
async def test_scheduler_no_jobs() -> None:
    """
    Test that the scheduler exists when there are no jobs.
    """
    vclock = aiotools.VirtualClock()
    with vclock.patch_loop():
        scheduler = Scheduler({})  # type: ignore
        await scheduler.run()


@pytest.mark.asyncio
async def test_scheduler_exceptions(mocker) -> None:
    """
    Test that exceptions are properly logged.
    """
    mock_source1 = mock.MagicMock()
    mock_source1.schedule.next.return_value = 10
    mock_source1.run = mocker.AsyncMock()
    mock_source1.run.side_effect = Exception("A wild error appeared!")
    mock_dag = {mock_source1}
    _logger = mocker.patch("senor_octopus.scheduler._logger")
    vclock = aiotools.VirtualClock()

    async def cancel_scheduler(scheduler) -> None:
        await asyncio.sleep(25)
        scheduler.cancel()

    with vclock.patch_loop():
        scheduler = Scheduler(mock_dag)  # type: ignore
        await asyncio.gather(scheduler.run(), cancel_scheduler(scheduler))

    assert len(_logger.exception.mock_calls) == 2
