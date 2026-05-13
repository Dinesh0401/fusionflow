# Backends

FusionFlow's executor consumes the IR contract; backends plug in to actually run experiments. This page covers what's available in v0.4.0.

## Built-in backends

### `pandas` (default)

The reference backend. Loads CSV/Parquet via pandas, applies pipeline ops via `DataFrame.eval(...)` for expression/`WHERE` handling and pandas slicing for selection, splits via `sklearn.model_selection.train_test_split`, trains via the sklearn estimator registry.

**Pros:** zero infra, fits any laptop, fully deterministic with `--seed` + `--num-threads 1`.

**Cons:** single-machine, in-memory.

```bash
fusionflow run my_spec.ff --backend pandas --seed 42
```

### `noop`

Validates the plan without executing anything. Useful for IR validation in CI.

```bash
fusionflow run my_spec.ff --backend noop
# {"status": "skipped", ...}
```

**Coming in v0.5**: `spark` backend (same IR, distributed).

## Model registry (v0.4)

Backends use a shared model registry (`fusionflow.executor.models`). Supported types:

| `type` | Backing class | Param keys |
|---|---|---|
| `linear_regression` | `sklearn.linear_model.LinearRegression` | `fit_intercept` |
| `logistic_regression` | `sklearn.linear_model.LogisticRegression` | `fit_intercept`, `C`, `max_iter` |
| `random_forest_classifier` | `sklearn.ensemble.RandomForestClassifier` | `trees` (alias for `n_estimators`), `max_depth` |
| `random_forest_regressor` | `sklearn.ensemble.RandomForestRegressor` | `trees` (alias for `n_estimators`), `max_depth` |

Unknown param keys raise `UnknownModelTypeError` — your `.ff` file's intent is always surfaced.

## Metric registry (v0.4)

| Name | Definition |
|---|---|
| `rmse` | `sqrt(mean_squared_error(y_true, y_pred))` |
| `mae` | `mean_absolute_error(y_true, y_pred)` |
| `accuracy` | `accuracy_score(y_true, y_pred)` |
| `f1` | `f1_score(y_true, y_pred, average="weighted")` |
| `auc` | `roc_auc_score(...)` (binary or multi-class OvR) |

## Determinism contract

Two `fusionflow run` invocations with the same `--seed` and `--num-threads 1` produce **byte-identical** `RunResult.to_json()` output. Verified by `tests/test_determinism.py` (cross-process subprocess hash comparison).

## Writing a custom backend (preview)

Backends implement the `ExecutionBackend` Protocol from `fusionflow.executor.backends`:

```python
from fusionflow.executor.backends import ExecutionBackend, SupportReport
from fusionflow.executor.plan import ExecutionPlan
from fusionflow.executor.run_result import RunResult, RunStatus


class MyBackend:
    name = "mine"

    def supports(self, plan: ExecutionPlan) -> SupportReport:
        return SupportReport(supported=True)

    def execute(self, plan: ExecutionPlan) -> RunResult:
        return RunResult(
            experiment=plan.experiment_name,
            backend=self.name,
            status=RunStatus.SUCCESS,
            ir_version=plan.ir_version,
            metrics={"my_metric": 1.0},
        )
```

A formal plugin API (entry-point discovery for third-party backends) lands in v1.0.0.
