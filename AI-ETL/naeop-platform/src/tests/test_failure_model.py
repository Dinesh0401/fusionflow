import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.ml.advanced_failure_model import AdvancedFailurePredictor, SKLEARN_AVAILABLE
from src.ml.feature_store import build_feature_matrix, latest_feature_vector
from src.ml.failure_model import FailurePredictor


class _PickleableDummyModel:
    def __init__(self, expected_columns: list[str], probabilities: list[float]):
        self.expected_columns = expected_columns
        self.probabilities = probabilities

    def predict_proba(self, X):  # noqa: D401
        assert list(X.columns) == self.expected_columns
        return np.array([self.probabilities])


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
    assert row["min_duration_ms"] == 1000.0
    assert row["duration_range_ms"] == 1000.0
    assert row["duration_p95_ms"] == pytest.approx(1950.0)
    assert row["rows_out_per_task"] == pytest.approx(1.5)
    assert row["success_ratio"] == pytest.approx(0.5)
    assert row["failure_ratio"] == pytest.approx(0.5)
    assert row["last_event_epoch"] > 0
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


def test_latest_feature_vector_aligns_columns(tmp_path):
    telemetry_path = tmp_path / "telemetry.csv"
    df = _sample_telemetry()
    df.to_csv(telemetry_path, index=False)

    features, _ = build_feature_matrix(df)
    expected_columns = [col for col in features.columns if col not in {"pipeline_id", "run_id"}]

    vector = latest_feature_vector(
        "Sample Pipeline",
        telemetry_path=telemetry_path,
        expected_columns=expected_columns,
    )

    assert vector is not None
    assert list(vector.columns) == expected_columns


def test_advanced_predictor_falls_back_to_baseline(tmp_path):
    telemetry_path = tmp_path / "telemetry.csv"
    df = _sample_telemetry()
    df.to_csv(telemetry_path, index=False)

    class BaselineStub:
        risk_threshold = 0.6

        def predict_pipeline_risk(self, pipeline_id: str):  # noqa: D401
            return 0.42

    predictor = AdvancedFailurePredictor(
        telemetry_path=telemetry_path,
        model_path=tmp_path / "missing.joblib",
        baseline_predictor=BaselineStub(),
        ensemble_weight=0.5,
    )

    risk = predictor.predict_pipeline_risk("Sample Pipeline")
    assert risk == pytest.approx(0.42)


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not installed")
def test_advanced_predictor_ensembles_with_baseline(tmp_path):
    telemetry_path = tmp_path / "telemetry.csv"
    df = _sample_telemetry()
    df.to_csv(telemetry_path, index=False)

    features, _ = build_feature_matrix(df)
    feature_columns = [col for col in features.columns if col not in {"pipeline_id", "run_id"}]

    bundle = {
        "model": _PickleableDummyModel(feature_columns, [0.2, 0.8]),
        "feature_columns": feature_columns,
        "metadata": {"test": True},
    }

    model_path = tmp_path / "advanced.joblib"
    with model_path.open("wb") as handle:
        pickle.dump(bundle, handle)

    class BaselineStub:
        risk_threshold = 0.6

        def predict_pipeline_risk(self, pipeline_id: str):  # noqa: D401
            return 0.5

    predictor = AdvancedFailurePredictor(
        telemetry_path=telemetry_path,
        model_path=model_path,
        baseline_predictor=BaselineStub(),
        ensemble_weight=0.25,
        risk_threshold=0.7,
    )

    risk = predictor.predict_pipeline_risk("Sample Pipeline")
    expected = 0.25 * 0.8 + 0.75 * 0.5
    assert risk == pytest.approx(expected)
