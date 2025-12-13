"""Lightweight in-memory scheduler for orchestrating DAG executions."""

import heapq
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from src.core.logger import get_logger


@dataclass(order=True)
class ScheduledJob:
    run_at: float
    job_id: int = field(compare=False)
    job_func: Callable = field(compare=False)


class Scheduler:
    def __init__(self, tick_seconds: float = 1.0):
        self.tick_seconds = tick_seconds
        self._queue: List[ScheduledJob] = []
        self._job_counter = 0
        self._stop_event = threading.Event()
        self.logger = get_logger(self.__class__.__name__)

    def add_job(self, job_func: Callable, delay_seconds: float = 0.0) -> int:
        """Schedule a job to run after the specified delay."""

        self._job_counter += 1
        run_at = time.time() + max(delay_seconds, 0.0)
        job = ScheduledJob(run_at=run_at, job_id=self._job_counter, job_func=job_func)
        heapq.heappush(self._queue, job)
        self.logger.debug("Job %s scheduled to run at %s", job.job_id, run_at)
        return job.job_id

    def start(self, blocking: bool = True, max_ticks: Optional[int] = None) -> None:
        """Start processing scheduled jobs.

        Set `blocking=False` to run the loop in a background thread. `max_ticks`
        is useful for tests to prevent infinite loops.
        """

        if blocking:
            self._run_loop(max_ticks=max_ticks)
        else:
            thread = threading.Thread(target=self._run_loop, kwargs={"max_ticks": max_ticks}, daemon=True)
            thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run_loop(self, max_ticks: Optional[int]) -> None:
        ticks = 0
        while not self._stop_event.is_set():
            now = time.time()
            while self._queue and self._queue[0].run_at <= now:
                job = heapq.heappop(self._queue)
                self.logger.info("Running scheduled job %s", job.job_id)
                try:
                    job.job_func()
                except Exception as exc:  # pylint: disable=broad-except
                    self.logger.error("Job %s failed: %s", job.job_id, exc)

            time.sleep(self.tick_seconds)
            ticks += 1
            if max_ticks is not None and ticks >= max_ticks:
                self.logger.debug("Max ticks reached; stopping scheduler loop")
                break