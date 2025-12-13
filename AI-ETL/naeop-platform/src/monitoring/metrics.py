"""Simple in-memory metrics collector."""

import logging
import time
from datetime import datetime
from typing import Dict, Optional


class Metrics:
    def __init__(self):
        self.metrics_data: Dict[str, Dict[str, Optional[float]]] = {}

    def start_timer(self, task_name: str) -> None:
        self.metrics_data[task_name] = {
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
            "status": "running",
        }

    def stop_timer(self, task_name: str, status: str = "completed") -> None:
        if task_name not in self.metrics_data:
            logging.warning("Task '%s' was not started.", task_name)
            return

        self.metrics_data[task_name]["end_time"] = time.time()
        self.metrics_data[task_name]["duration"] = (
            self.metrics_data[task_name]["end_time"]
            - self.metrics_data[task_name]["start_time"]
        )
        self.metrics_data[task_name]["status"] = status
        logging.info(
            "Task '%s' finished with status '%s' in %.3f seconds.",
            task_name,
            status,
            self.metrics_data[task_name]["duration"],
        )

    def get_metrics(self) -> Dict[str, Dict[str, Optional[float]]]:
        return self.metrics_data

    def log_metrics(self) -> None:
        for task, data in self.metrics_data.items():
            start_time = data.get("start_time")
            logging.info(
                "Task: %s, Duration: %s, Status: %s, Start Time: %s",
                task,
                data.get("duration"),
                data.get("status"),
                datetime.fromtimestamp(start_time) if start_time else None,
            )