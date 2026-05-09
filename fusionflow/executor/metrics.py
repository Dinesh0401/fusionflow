"""Metric registry for the executor.

Maps metric name strings (from EvalOp.metrics) to functions that take
``(model, X_test, y_true)`` and return a float.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
from sklearn.base import is_classifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)


class UnknownMetricError(ValueError):
    """Raised when ``compute_metric`` is asked for a metric not in the registry."""


def supported_metrics() -> Iterable[str]:
    """Return the tuple of metric names the registry can compute."""
    return ("rmse", "mae", "accuracy", "f1", "auc")


def compute_metric(name: str, model, X_test, y_true) -> float:
    """Compute the named metric and return a python float.

    Regression metrics call ``model.predict``; classification metrics may call
    ``model.predict_proba`` for AUC. ``f1`` uses weighted averaging so it works
    on both binary and multi-class labels without raising on imbalance.
    """
    if name == "rmse":
        y_pred = model.predict(X_test)
        return float(np.sqrt(mean_squared_error(y_true, y_pred)))
    if name == "mae":
        y_pred = model.predict(X_test)
        return float(mean_absolute_error(y_true, y_pred))
    if name == "accuracy":
        y_pred = model.predict(X_test)
        return float(accuracy_score(y_true, y_pred))
    if name == "f1":
        y_pred = model.predict(X_test)
        return float(f1_score(y_true, y_pred, average="weighted"))
    if name == "auc":
        if not is_classifier(model):
            raise UnknownMetricError("auc requires a classifier model.")
        proba = model.predict_proba(X_test)
        if proba.shape[1] == 2:
            return float(roc_auc_score(y_true, proba[:, 1]))
        return float(roc_auc_score(y_true, proba, multi_class="ovr", average="weighted"))
    raise UnknownMetricError(
        f"Unknown metric: {name!r}. "
        f"Supported: {sorted(supported_metrics())}. "
        f"Add a branch in fusionflow/executor/metrics.py::compute_metric."
    )
