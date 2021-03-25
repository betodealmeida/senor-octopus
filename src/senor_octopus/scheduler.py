import asyncio
import logging
from typing import Dict
from typing import Set

from senor_octopus.graph import Source

_logger = logging.getLogger(__name__)


SLEEP_TIME = 5


class Scheduler:
    def __init__(self, dag: Set[Source]):
        self.dag = dag

    async def run(self) -> None:
        nodes = {node for node in self.dag if node.schedule}
        if not nodes:
            _logger.info("Nothing to schedule")
            return

        _logger.info("Starting scheduler")
        loop = asyncio.get_event_loop()

        schedules: Dict[str, float] = {}
        while True:
            for node in nodes:
                now = loop.time()
                delay = node.schedule.next(default_utc=False)
                when = now + delay

                if node.name not in schedules:
                    _logger.info(f"Scheduling {node.name} to run in {delay} seconds")
                    schedules[node.name] = when
                elif schedules[node.name] <= now:
                    _logger.info(f"Running {node.name}")
                    await node.run()
                    del schedules[node.name]

            _logger.debug(f"Sleeping for {SLEEP_TIME} seconds")
            await asyncio.sleep(SLEEP_TIME)
