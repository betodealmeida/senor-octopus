import logging
import time
from collections import defaultdict
from typing import Dict
from typing import Set

from senor_octopus.graph import Source

_logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, dag: Set[Source]):
        self.dag = dag

    def run(self) -> None:
        _logger.info("Starting scheduler...")

        while True:
            delays: Dict[int, Set[Source]] = defaultdict(set)
            for node in self.dag:
                if node.schedule:
                    delays[node.schedule.next(default_utc=True)].add(node)
            min_delay = min(delays)
            _logger.info(f"Sleeping for {min_delay} seconds...")
            time.sleep(min_delay)

            for node in delays[min_delay]:
                node.run()
