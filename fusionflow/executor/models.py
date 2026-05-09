"""Model registry for the executor.

Maps ``type_name`` strings (from ModelSpec) to scikit-learn estimator constructors.
Each entry coerces user-provided params to constructor kwargs and pins
``random_state`` to the run seed where applicable.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression


class UnknownModelTypeError(ValueError):
    """Raised when ``build_model`` is asked for a type not in the registry."""


def supported_model_types() -> Iterable[str]:
    """Return the tuple of model type strings the registry can build."""
    return (
        "linear_regression",
        "logistic_regression",
        "random_forest_classifier",
        "random_forest_regressor",
    )


def build_model(type_name: str, params: Dict[str, Any], seed: int) -> Any:
    """Construct a fresh estimator.

    Pins ``random_state`` to ``seed`` for stochastic models. For deterministic
    models (``LinearRegression``) ``seed`` is ignored.
    """
    if type_name == "linear_regression":
        # LinearRegression has no random_state; do NOT pass one.
        return LinearRegression(**_coerce_linear_params(params))
    if type_name == "logistic_regression":
        return LogisticRegression(random_state=seed, **_coerce_logistic_params(params))
    if type_name == "random_forest_classifier":
        return RandomForestClassifier(random_state=seed, **_coerce_rf_params(params))
    if type_name == "random_forest_regressor":
        return RandomForestRegressor(random_state=seed, **_coerce_rf_params(params))
    raise UnknownModelTypeError(
        f"Unknown model type: {type_name!r}. "
        f"Supported: {sorted(supported_model_types())}. "
        f"Add a constructor branch in fusionflow/executor/models.py::build_model."
    )


def _coerce_linear_params(params: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "fit_intercept" in params:
        out["fit_intercept"] = bool(params["fit_intercept"])
    return out


def _coerce_logistic_params(params: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "C" in params:
        out["C"] = float(params["C"])
    if "max_iter" in params:
        out["max_iter"] = int(params["max_iter"])
    if "fit_intercept" in params:
        out["fit_intercept"] = bool(params["fit_intercept"])
    return out


def _coerce_rf_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce friendly DSL names (``trees``) to sklearn names (``n_estimators``).

    Both ``trees`` and ``n_estimators`` are accepted; the latter wins if both
    are present (rare in practice).
    """
    out: Dict[str, Any] = {}
    if "trees" in params:
        out["n_estimators"] = int(params["trees"])
    if "n_estimators" in params:
        out["n_estimators"] = int(params["n_estimators"])
    if "max_depth" in params:
        out["max_depth"] = int(params["max_depth"])
    return out
