"""Failure prediction model built from telemetry features."""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Optional

import pandas as pd

try:  # pragma: no cover - optional dependency
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    SimpleImputer = None  # type: ignore
    LogisticRegression = None  # type: ignore
    Pipeline = None  # type: ignore
    StandardScaler = None  # type: ignore
    SKLEARN_AVAILABLE = False

from src.ml.feature_store import TELEMETRY_DEFAULT_PATH, build_feature_matrix, latest_feature_vector, load_telemetry

LOGGER = logging.getLogger(__name__)
DEFAULT_MODEL_PATH = Path("models/failure_model.joblib")


class FailureModelTrainer:
    """Trains and persists a lightweight failure classifier."""

    def __init__(self, telemetry_path: Path | str = TELEMETRY_DEFAULT_PATH, model_path: Path | str = DEFAULT_MODEL_PATH):
        self.telemetry_path = Path(telemetry_path)
        self.model_path = Path(model_path)

    def load_dataset(self) -> tuple[pd.DataFrame, pd.Series]:
        df = load_telemetry(self.telemetry_path)
        features, labels = build_feature_matrix(df)
        return features, labels

    def train(self) -> "Pipeline":
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required to train the failure model. Install 'scikit-learn'.")

        features, labels = self.load_dataset()
        if features.empty or labels.empty or labels.nunique() < 2:
            raise ValueError("Not enough labeled telemetry data to train failure model.")

        X = features.drop(columns=["pipeline_id", "run_id"], errors="ignore")
        y = labels

        model = Pipeline(
            steps=[
                ("imputer", SimpleImputer()),
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(max_iter=200)),
            ]
        )
        model.fit(X, y)

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with self.model_path.open("wb") as handle:
            pickle.dump({"model": model, "feature_columns": list(X.columns)}, handle)
        LOGGER.info("Saved failure model to %s", self.model_path)
        return model


class FailurePredictor:
    """Loads trained model and produces risk scores for pipelines."""

    def __init__(
        self,
        telemetry_path: Path | str = TELEMETRY_DEFAULT_PATH,
        model_path: Path | str = DEFAULT_MODEL_PATH,
        risk_threshold: float = 0.6,
    ):
        self.telemetry_path = Path(telemetry_path)
        self.model_path = Path(model_path)
        self.risk_threshold = risk_threshold
        self._model: Optional[Any] = None
        self._feature_columns: Optional[list[str]] = None
        self._load_model()

    def _load_model(self) -> None:
        if not SKLEARN_AVAILABLE:
            LOGGER.warning("scikit-learn not installed; failure model cannot be loaded.")
            return
        if not self.model_path.exists():
            LOGGER.warning("Failure model not found at %s", self.model_path)
            return
        with self.model_path.open("rb") as handle:
            bundle = pickle.load(handle)
        self._model = bundle["model"]
        self._feature_columns = bundle["feature_columns"]

    def predict_pipeline_risk(self, pipeline_id: str) -> Optional[float]:
        if not self._model:
            LOGGER.info("Failure model unavailable; skipping risk prediction.")
            return None

        feature_vector = latest_feature_vector(
            pipeline_id,
            telemetry_path=self.telemetry_path,
            expected_columns=self._feature_columns,
        )
        if feature_vector is None:
            return None

        risk = float(self._model.predict_proba(feature_vector)[0, 1])
        return risk
