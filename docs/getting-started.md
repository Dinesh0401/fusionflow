# Getting Started

This page takes you from zero to a successful `fusionflow run` in 5 minutes.

## Install

```bash
pip install fusionflow
```

For the full v0.4.0 experience, install the extras you need:

```bash
pip install "fusionflow[mlflow,jupyter]"   # MLflow autologging + Jupyter magic
```

## Verify the installation

```bash
fusionflow --version
# FusionFlow v0.4.0.dev0
```

## Your first .ff file

Create `iris.ff` next to a CSV named `iris.csv`:

```fusionflow
dataset iris v1
    source "iris.csv"
    schema {
        sepal_length: float,
        sepal_width: float,
        petal_length: float,
        petal_width: float,
        species: int
    }
end

pipeline iris_pipe
    from iris v1
    features [sepal_length, sepal_width, petal_length, petal_width]
    split 0.8
    target species
end

model rf
    type random_forest_classifier
    params { trees: 100, max_depth: 5 }
end

experiment iris_baseline
    uses pipeline iris_pipe
    uses model rf
    metrics [accuracy, f1]
end
```

## Run it

```bash
fusionflow run iris.ff --backend pandas --seed 42
```

You should see a JSON `RunResult` printed to stdout:

```json
{
  "experiment": "iris_baseline",
  "backend": "pandas",
  "status": "success",
  "ir_version": "0.4",
  "metrics": {
    "accuracy": 0.97,
    "f1": 0.97
  },
  "detail": "Executed 4 ops; checkpoints=[]"
}
```

The exact metrics depend on your data and split, but the **same seed always produces the same numbers**.

## Save the result

```bash
fusionflow run iris.ff --out runs/iris.json --seed 42
```

## What just happened?

1. **Lex + parse**: your `.ff` file became an AST (typed declarations).
2. **Compile**: the AST became a deterministic JSON IR (the contract).
3. **Plan**: the IR was loaded into an `ExecutionPlan` (one experiment).
4. **Execute**: the Pandas backend ran the pipeline + trained the model + computed the metrics.
5. **Result**: a `RunResult` was printed (and optionally saved).

You can inspect the IR alone, without execution:

```bash
fusionflow compile iris.ff --out iris.tir.json
```

You can also validate without running:

```bash
fusionflow validate iris.ff
# OK: iris.ff is a valid FusionFlow specification.
```

## Next steps

- See [`docs/cli.md`](cli.md) for every CLI flag.
- See [`docs/backends.md`](backends.md) for backend selection and the path to Spark in v0.5.
- See [`docs/ir-spec-v0.4.md`](ir-spec-v0.4.md) for the full IR contract.
