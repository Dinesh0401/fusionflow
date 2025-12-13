"""Feature engineering helpers built on pipeline telemetry."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd

TELEMETRY_DEFAULT_PATH = Path("data/telemetry/pipeline_runs.csv")


def load_telemetry(path: Path | str = TELEMETRY_DEFAULT_PATH) -> pd.DataFrame:
    """Load telemetry CSV into a DataFrame.

    Returns an empty DataFrame if the file does not exist.
    """

    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=["start_time", "end_time"], low_memory=False)


def _safe_duration_stats(group: pd.DataFrame) -> Tuple[float, float]:
    durations = group["duration_ms"].fillna(0.0)
    return float(durations.mean()), float(durations.max())


def build_feature_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Aggregate telemetry rows into per-run feature matrix and labels."""

    if df.empty:
        return pd.DataFrame(), pd.Series(dtype=int)

    grouped = df.groupby(["pipeline_id", "run_id"], as_index=False)

    feature_rows = []
    labels = []

    for _, group in grouped:
        total_tasks = len(group)
        failed_tasks = int((group["status"] != "completed").sum())
        avg_duration_ms, max_duration_ms = _safe_duration_stats(group)
        total_rows_in = float(group["rows_in"].fillna(0).sum())
        total_rows_out = float(group["rows_out"].fillna(0).sum())
        duration_std = float(group["duration_ms"].fillna(0).std(ddof=0) or 0.0)

        feature_rows.append(
            {
                "pipeline_id": group.iloc[0]["pipeline_id"],
                "run_id": group.iloc[0]["run_id"],
                "total_tasks": total_tasks,
                "failed_tasks": failed_tasks,
                "avg_duration_ms": avg_duration_ms,
                "max_duration_ms": max_duration_ms,
                "duration_std_ms": duration_std,
                "total_rows_in": total_rows_in,
                "total_rows_out": total_rows_out,
                "rows_delta": total_rows_out - total_rows_in,
            }
        )
        labels.append(1 if failed_tasks > 0 else 0)

    feature_df = pd.DataFrame(feature_rows)
    label_series = pd.Series(labels, name="failed")
    return feature_df, label_series
