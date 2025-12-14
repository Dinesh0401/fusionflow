"""Feature engineering helpers built on pipeline telemetry."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

TELEMETRY_DEFAULT_PATH = Path("data/telemetry/pipeline_runs.csv")


def load_telemetry(path: Path | str = TELEMETRY_DEFAULT_PATH) -> pd.DataFrame:
    """Load telemetry CSV into a DataFrame.

    Returns an empty DataFrame if the file does not exist.
    """

    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=["start_time", "end_time"], low_memory=False)


def _ensure_datetime(df: pd.DataFrame, columns: Tuple[str, ...]) -> pd.DataFrame:
    for column in columns:
        if column in df and not is_datetime64_any_dtype(df[column]):
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def _safe_duration_stats(group: pd.DataFrame) -> Tuple[float, float, float]:
    durations = group["duration_ms"].fillna(0.0).astype(float)
    if durations.empty:
        return 0.0, 0.0, 0.0
    return (
        float(durations.mean()),
        float(durations.max()),
        float(durations.min()),
    )


def _safe_percentile(values: pd.Series, percentile: float) -> float:
    arr = values.dropna().astype(float)
    if arr.empty:
        return 0.0
    return float(np.percentile(arr, percentile))


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def build_feature_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Aggregate telemetry rows into per-run feature matrix and labels with richer statistics."""

    if df.empty:
        return pd.DataFrame(), pd.Series(dtype=int)

    df = df.copy()
    df = _ensure_datetime(df, ("start_time", "end_time"))

    grouped = df.groupby(["pipeline_id", "run_id"], as_index=False)

    feature_rows = []

    for _, group in grouped:
        total_tasks = len(group)
        failed_tasks = int((group["status"] != "completed").sum())
        avg_duration_ms, max_duration_ms, min_duration_ms = _safe_duration_stats(group)
        duration_std = float(group["duration_ms"].fillna(0).astype(float).std(ddof=0) or 0.0)
        duration_range_ms = float(max_duration_ms - min_duration_ms)
        duration_p95_ms = _safe_percentile(group["duration_ms"], 95.0)

        total_rows_in = float(group["rows_in"].fillna(0).sum())
        total_rows_out = float(group["rows_out"].fillna(0).sum())

        completed_tasks = total_tasks - failed_tasks
        success_ratio = _safe_ratio(completed_tasks, total_tasks)
        failure_ratio = _safe_ratio(failed_tasks, total_tasks)
        rows_out_per_task = _safe_ratio(total_rows_out, total_tasks)
        rows_in_per_task = _safe_ratio(total_rows_in, total_tasks)
        rows_out_to_in_ratio = _safe_ratio(total_rows_out, total_rows_in)

        last_event = group["end_time"].max()
        last_event_epoch = float(last_event.timestamp()) if pd.notna(last_event) else 0.0

        feature_rows.append(
            {
                "pipeline_id": group.iloc[0]["pipeline_id"],
                "run_id": group.iloc[0]["run_id"],
                "total_tasks": total_tasks,
                "failed_tasks": failed_tasks,
                "completed_tasks": completed_tasks,
                "avg_duration_ms": avg_duration_ms,
                "max_duration_ms": max_duration_ms,
                "min_duration_ms": min_duration_ms,
                "duration_range_ms": duration_range_ms,
                "duration_std_ms": duration_std,
                "duration_p95_ms": duration_p95_ms,
                "total_rows_in": total_rows_in,
                "total_rows_out": total_rows_out,
                "rows_delta": total_rows_out - total_rows_in,
                "rows_out_per_task": rows_out_per_task,
                "rows_in_per_task": rows_in_per_task,
                "rows_out_to_in_ratio": rows_out_to_in_ratio,
                "success_ratio": success_ratio,
                "failure_ratio": failure_ratio,
                "last_event_epoch": last_event_epoch,
                "failed_label": 1 if failed_tasks > 0 else 0,
            }
        )

    feature_df = pd.DataFrame(feature_rows)
    feature_df = feature_df.sort_values(by=["pipeline_id", "last_event_epoch", "run_id"]).reset_index(drop=True)
    label_series = feature_df.pop("failed_label").rename("failed")
    return feature_df, label_series


def latest_feature_vector(
    pipeline_id: str,
    telemetry_path: Path | str = TELEMETRY_DEFAULT_PATH,
    expected_columns: Optional[list[str]] = None,
) -> Optional[pd.DataFrame]:
    """Return the most recent feature vector for a pipeline with optional column alignment."""

    df = load_telemetry(telemetry_path)
    if df.empty:
        return None

    df = df[df["pipeline_id"] == pipeline_id]
    if df.empty:
        return None

    features, _ = build_feature_matrix(df)
    if features.empty:
        return None

    latest = features.iloc[-1]
    vector = latest.drop(labels=["pipeline_id", "run_id"], errors="ignore").to_frame().T

    if expected_columns:
        for column in expected_columns:
            if column not in vector:
                vector[column] = 0.0
        extra_columns = [column for column in vector.columns if column not in expected_columns]
        if extra_columns:
            vector = vector.drop(columns=extra_columns)
        vector = vector[expected_columns]

    return vector
