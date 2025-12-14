"""Phase-2B advanced failure prediction utilities with neural ensemble support."""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

try:  # pragma: no cover - optional dependency guard
    from sklearn.impute import SimpleImputer
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    SimpleImputer = None  # type: ignore
    MLPClassifier = None  # type: ignore
    Pipeline = None  # type: ignore
    StandardScaler = None  # type: ignore
    SKLEARN_AVAILABLE = False

from src.ml.failure_model import FailurePredictor
from src.ml.feature_store import TELEMETRY_DEFAULT_PATH, build_feature_matrix, latest_feature_vector, load_telemetry

LOGGER = logging.getLogger(__name__)
DEFAULT_ADVANCED_MODEL_PATH = Path("models/failure_model_advanced.joblib")


class AdvancedFailureModelTrainer:
    """Train a deeper neural network-based failure predictor."""

    def __init__(
        self,
        telemetry_path: Path | str = TELEMETRY_DEFAULT_PATH,
        model_path: Path | str = DEFAULT_ADVANCED_MODEL_PATH,
        hidden_layer_sizes: tuple[int, ...] = (64, 32),
        max_iter: int = 400,
        learning_rate_init: float = 0.001,
        random_state: int = 42,
    ) -> None:
        self.telemetry_path = Path(telemetry_path)
        self.model_path = Path(model_path)
        self.hidden_layer_sizes = hidden_layer_sizes
        self.max_iter = max_iter
        self.learning_rate_init = learning_rate_init
        self.random_state = random_state

    def load_dataset(self) -> tuple[pd.DataFrame, pd.Series]:
        df = load_telemetry(self.telemetry_path)
        features, labels = build_feature_matrix(df)
        return features, labels

    def train(self) -> "Pipeline":
        if not SKLEARN_AVAILABLE or MLPClassifier is None:
            raise ImportError("scikit-learn with MLPClassifier is required for the advanced failure model.")

        features, labels = self.load_dataset()
        if features.empty or labels.empty or labels.nunique() < 2:
            raise ValueError("Not enough labeled telemetry to train advanced failure model.")

        X = features.drop(columns=["pipeline_id", "run_id"], errors="ignore")
        y = labels

        model = Pipeline(
            steps=[
                ("imputer", SimpleImputer()),
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    MLPClassifier(
                        hidden_layer_sizes=self.hidden_layer_sizes,
                        activation="relu",
                        solver="adam",
                        max_iter=self.max_iter,
                        learning_rate_init=self.learning_rate_init,
                        random_state=self.random_state,
                    ),
                ),
            ]
        )
        model.fit(X, y)

        class_balance = labels.value_counts(normalize=True).to_dict()

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with self.model_path.open("wb") as handle:
            pickle.dump(
                {
                    "model": model,
                    "feature_columns": list(X.columns),
                    "metadata": {
                        "class_balance": class_balance,
                        "hidden_layer_sizes": self.hidden_layer_sizes,
                        "max_iter": self.max_iter,
                    },
                },
                handle,
            )
        LOGGER.info("Saved advanced failure model to %s", self.model_path)
        return model


class AdvancedFailurePredictor:
    """Hybrid predictor that combines deep model outputs with the baseline predictor when available."""

    def __init__(
        self,
        telemetry_path: Path | str = TELEMETRY_DEFAULT_PATH,
        model_path: Path | str = DEFAULT_ADVANCED_MODEL_PATH,
        risk_threshold: float = 0.6,
        baseline_predictor: Optional[FailurePredictor] = None,
        ensemble_weight: float = 0.6,
    ) -> None:
        if not 0.0 <= ensemble_weight <= 1.0:
            raise ValueError("ensemble_weight must be between 0 and 1.")

        self.telemetry_path = Path(telemetry_path)
        self.model_path = Path(model_path)
        self.risk_threshold = risk_threshold
        self.baseline_predictor = baseline_predictor
        self.ensemble_weight = ensemble_weight

        self._model: Optional[Any] = None
        self._feature_columns: Optional[list[str]] = None
        self.metadata: Dict[str, Any] | None = None
        self._load_model()

    def _load_model(self) -> None:
        if not SKLEARN_AVAILABLE:
            LOGGER.warning("scikit-learn not installed; advanced failure model cannot be loaded.")
            return
        if not self.model_path.exists():
            LOGGER.info("Advanced failure model not found at %s", self.model_path)
            return
        with self.model_path.open("rb") as handle:
            bundle = pickle.load(handle)
        self._model = bundle.get("model")
        self._feature_columns = bundle.get("feature_columns")
        self.metadata = bundle.get("metadata")

    def predict_pipeline_risk(self, pipeline_id: str) -> Optional[float]:
        advanced_risk = self._predict_advanced_risk(pipeline_id)
        baseline_risk: Optional[float] = None
        if self.baseline_predictor:
            baseline_risk = self.baseline_predictor.predict_pipeline_risk(pipeline_id)

        if advanced_risk is None:
            return baseline_risk
        if baseline_risk is None:
            return advanced_risk

        combined = float(self.ensemble_weight * advanced_risk + (1.0 - self.ensemble_weight) * baseline_risk)
        return combined

    def _predict_advanced_risk(self, pipeline_id: str) -> Optional[float]:
        if not self._model:
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