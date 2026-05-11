# FusionFlow Examples

This folder contains runnable v0.4 examples. All examples assume `fusionflow` is installed (`pip install fusionflow[pandas]`).

## Files

| File | Description | Try it |
|---|---|---|
| `iris.ff` + `iris.csv` | Random forest classification on the Iris dataset (3 classes, 4 features). | `fusionflow run examples/iris.ff --backend pandas --seed 42 --data-root examples` |
| `regression.ff` + `customers.csv` | Linear regression predicting customer spend from age and income. | `fusionflow run examples/regression.ff --backend pandas --seed 42 --data-root examples` |
| `timeline.ff` | Two experiments — a baseline plus a branch with an extended split + checkpoint. | `fusionflow run examples/timeline.ff --experiment baseline --backend pandas --data-root examples` |
| `quickstart.ipynb` | Jupyter notebook using the `%%fusionflow` cell magic (requires `pip install fusionflow[jupyter]`). | Open in Jupyter and run all cells from the repo root. |

## What you should see

Each `.ff` example prints a JSON `RunResult` to stdout. The `--seed 42` invocation is fully deterministic; rerunning produces byte-identical output.

```bash
$ fusionflow run examples/iris.ff --backend pandas --seed 42 --data-root examples
{
  "experiment": "iris_baseline",
  "backend": "pandas",
  "status": "success",
  "ir_version": "0.4",
  "metrics": { "accuracy": ..., "f1": ... },
  "detail": "Executed 4 ops; checkpoints=[]"
}
```

## Validate without running

```bash
fusionflow validate examples/iris.ff
# OK: examples/iris.ff is a valid FusionFlow specification.
```

## Compile to IR

```bash
fusionflow compile examples/iris.ff --out iris.tir.json
```
