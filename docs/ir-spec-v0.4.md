# Temporal IR v0.4 Specification

The Temporal IR is the contract between the FusionFlow language frontend and execution backends. It is a deterministic JSON document.

## Top-level shape

```json
{
  "ir_version": "0.4",
  "datasets": { "<name>:<version>": { ... } },
  "pipelines": { "<name>": { ... } },
  "models": { "<name>": { ... } },
  "experiments": { "<name>": { ... } },
  "timelines": { "<name>": { ... } },
  "merges": [ ... ]
}
```

The `ir_version` field is **required** in v0.4. v0.3 IR omits it (loaders treat missing as `"0.3"`).

## Dataset object

```json
{
  "name": "users",
  "version": "v1",
  "source": "data/users.csv",
  "schema": { "age": "int", "income": "float" },
  "description": "(optional)"
}
```

Keys in the top-level `datasets` map are `<name>:<version>` for unique addressing.

## Pipeline object

```json
{
  "name": "scoring",
  "input": "users:v1",
  "operations": [ <op>, ... ]
}
```

## Operation atoms

Each `op` is a flat dict with a `type` discriminator.

### `derive`
```json
{ "type": "derive", "target": "bonus", "expression": "income * 0.1" }
```
Adds/overwrites a column. The `expression` is a string evaluated by the backend.

### `select`
```json
{ "type": "select", "fields": ["age", "income"] }
```
Projects the DataFrame to a subset of columns.

### `where`  *(v0.4)*
```json
{ "type": "where", "condition": "age >= 18" }
```
Row filter. The `condition` evaluates to a boolean Series.

### `split`  *(v0.4)*
```json
{ "type": "split", "train_ratio": 0.8 }
```
Train/test split. `train_ratio` is in the open interval `(0, 1)`.

### `features`  *(v0.4)*
```json
{ "type": "features", "fields": ["age", "income"] }
```
Declares the feature columns for training. Pure metadata — does not modify the DataFrame.

### `target`
```json
{ "type": "target", "field": "spend" }
```
Declares the target column for training. Pure metadata.

### `checkpoint`  *(v0.4)*
```json
{ "type": "checkpoint", "name": "pre_train" }
```
Named save point. v0.4 backends treat this as a no-op marker (logged in `RunResult.detail`); future backends may persist intermediate state.

## Model object

```json
{ "type": "linear_regression", "params": { "fit_intercept": true } }
```

Supported `type` values in v0.4: `linear_regression`, `logistic_regression`, `random_forest_classifier`, `random_forest_regressor`.

Param keys vary by model type. See [`docs/backends.md`](backends.md) for the full registry.

## Experiment object

```json
{
  "pipeline": "scoring",
  "model": "rf",
  "metrics": ["rmse", "mae"],
  "description": "(optional)",
  "extension": [ <op>, ... ]
}
```

The `extension` (optional, only on timeline experiments) is a list of additional ops applied AFTER the pipeline ops and BEFORE training.

## Timeline object

```json
{
  "parent": "main",
  "experiments": { "<name>": { ... } },
  "description": "(optional)"
}
```

## Merge object

```json
{
  "source": "v2",
  "target": "main",
  "justification": "Improved f1 without accuracy loss",
  "strategy": { "name": "prefer_metrics", "arguments": ["f1"] }
}
```

## Determinism

The IR is **byte-deterministic**: the same source `.ff` file always produces the same JSON bytes (insertion-order is preserved; no sets are serialized). Two `fusionflow compile` invocations on the same input produce identical output.

## Backwards compatibility

- v0.3 IR (no `ir_version` field) still loads in v0.4. The loader treats missing as `"0.3"`.
- v0.3 IR containing v0.4-only ops (`where`, `split`, `features`, `checkpoint`) is REJECTED with `IRLoadError` (defensive against hand-edited files).
- v0.4 IR cannot be loaded by v0.3 toolchains.

## Reserved keywords (v0.4)

The new keywords `where`, `split`, `features`, `checkpoint` are now reserved by the lexer. If you have v0.3 `.ff` files using these names as identifiers (e.g., a schema field named `features`), you will get a parse error in v0.4. **Migration**: rename the colliding identifier (e.g., `features` -> `feature_set` or `cols`).
