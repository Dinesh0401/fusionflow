import pandas as pd

from src.ml.feature_store import build_feature_matrix
from src.ml.failure_model import FailurePredictor


def _sample_telemetry() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "pipeline_id": "Sample Pipeline",
                "run_id": "run-1",
                "task_id": "extract",
                "step": "extract",
                "status": "completed",
                "start_time": "2025-01-01T00:00:00",
                "end_time": "2025-01-01T00:00:01",
                "duration_ms": 1000.0,
                "rows_in": 0,
                "rows_out": 3,
            },
            {
                "pipeline_id": "Sample Pipeline",
                "run_id": "run-1",
                "task_id": "transform",
                "step": "transform",
                "status": "failed",
                "start_time": "2025-01-01T00:00:01",
                "end_time": "2025-01-01T00:00:03",
                "duration_ms": 2000.0,
                "rows_in": 3,
                "rows_out": 0,
            },
        ]
    )


def test_build_feature_matrix_aggregates_stats():
    df = _sample_telemetry()
    features, labels = build_feature_matrix(df)

    assert len(features) == 1
    row = features.iloc[0]
    assert row["total_tasks"] == 2
    assert row["failed_tasks"] == 1
    assert row["max_duration_ms"] == 2000.0
    assert labels.iloc[0] == 1


def test_failure_predictor_without_model_returns_none(tmp_path):
    telemetry_path = tmp_path / "telemetry.csv"
    df = _sample_telemetry()
    df.to_csv(telemetry_path, index=False)

    predictor = FailurePredictor(
        telemetry_path=telemetry_path,
        model_path=tmp_path / "missing.joblib",
        risk_threshold=0.5,
    )

    assert predictor.predict_pipeline_risk("Sample Pipeline") is None
