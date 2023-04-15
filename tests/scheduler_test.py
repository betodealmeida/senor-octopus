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
async def test_scheduler_cancel(mocker: MockerFixture) -> None:
    """
    Test that the schduler can be canceled.
    """
    source1 = mock.MagicMock()
    source1.schedule.next.return_value = 10
    source1.run = mocker.AsyncMock()
    source2 = mock.MagicMock()
    source2.schedule = None
    source2.run = mocker.AsyncMock()
    source3 = mock.MagicMock()
    source3.schedule.next.return_value = 100
    source3.run = mocker.AsyncMock()
    dag = {source1, source2, source3}
    vclock = aiotools.VirtualClock()

    async def cancel_scheduler(scheduler) -> None:
        await asyncio.sleep(30)
        scheduler.cancel()

    with vclock.patch_loop():
        scheduler = Scheduler(dag)  # type: ignore
        await asyncio.gather(scheduler.run(), cancel_scheduler(scheduler))

    assert len(scheduler.tasks) == 1
    assert scheduler.canceled
    assert len(source1.run.mock_calls) == 2


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
    source1 = mock.MagicMock()
    source1.schedule.next.return_value = 10
    source1.run = mocker.AsyncMock()
    source1.run.side_effect = Exception("A wild error appeared!")
    dag = {source1}
    _logger = mocker.patch("senor_octopus.scheduler._logger")
    vclock = aiotools.VirtualClock()

    async def cancel_scheduler(scheduler) -> None:
        await asyncio.sleep(25)
        scheduler.cancel()

    with vclock.patch_loop():
        scheduler = Scheduler(dag)  # type: ignore
        await asyncio.gather(scheduler.run(), cancel_scheduler(scheduler))

    assert len(_logger.exception.mock_calls) == 2
