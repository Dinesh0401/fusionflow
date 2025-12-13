"""Structured telemetry events and storage helpers."""

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class TelemetryEvent:
    """Captures a single task execution event."""

    pipeline_id: str
    run_id: str
    task_id: str
    step: str
    status: str  # completed / failed
    start_time: datetime
    end_time: datetime
    duration_ms: float
    rows_in: Optional[int] = None
    rows_out: Optional[int] = None
    error_type: Optional[str] = None
    resource_cpu: Optional[float] = None
    resource_mem: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        base = asdict(self)
        # Serialize datetimes to ISO for portability
        base["start_time"] = self.start_time.isoformat()
        base["end_time"] = self.end_time.isoformat()
        return base


class TelemetryStore:
    """Lightweight storage that appends telemetry events to CSV."""

    def __init__(self, base_path: str = "data/telemetry", filename: str = "pipeline_runs.csv"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.path = self.base_path / filename
        self._buffer: List[TelemetryEvent] = []

    def add_event(self, event: TelemetryEvent) -> None:
        self._buffer.append(event)

    def flush(self) -> None:
        if not self._buffer:
            return

        records = [event.to_dict() for event in self._buffer]
        df = pd.DataFrame(records)
        # Append with header only when file does not yet exist
        df.to_csv(self.path, mode="a", header=not self.path.exists(), index=False)
        self._buffer.clear()

    def load(self) -> pd.DataFrame:
        if not self.path.exists():
            return pd.DataFrame()
        return pd.read_csv(self.path, parse_dates=["start_time", "end_time"])
