# CLI Reference

The `fusionflow` CLI has four subcommands plus a v0.3-compatible bare-run mode.

## `fusionflow run <file>`

Execute one experiment from a `.ff` file via the chosen backend.

| Flag | Default | Description |
|---|---|---|
| `--experiment <name>` | first found | Which experiment to execute |
| `--backend pandas\|noop` | `pandas` | Backend to use |
| `--seed <int>` | `42` | Random seed for `train_test_split` and stochastic models |
| `--num-threads <int>` | `1` | Threads for numpy/sklearn parallelism (`1` for determinism) |
| `--out <path>` | stdout | Write `RunResult.to_json()` to this file |
| `--data-root <path>` | `<.ff file's directory>` | Base for resolving `DatasetSpec.source` paths |
| `--mlflow` | off | Log run to MLflow (requires `pip install fusionflow[mlflow]`) |

Exit codes:
- `0`: success or skipped (NoopBackend always returns SKIPPED)
- `1`: failure (parse error, file not found, plan-level error, model error)
- `2`: ambiguous or unknown experiment

Examples:

```bash
# Smallest invocation
fusionflow run my_spec.ff

# With explicit backend, seed, output file, data root
fusionflow run my_spec.ff --backend pandas --seed 42 --out runs/today.json --data-root data/

# Multiple experiments in one file? Pick one
fusionflow run my_spec.ff --experiment alt_baseline

# Skip execution to validate the IR plan only
fusionflow run my_spec.ff --backend noop
```

## `fusionflow validate <file>`

Parse and interpret a `.ff` file. Exits 0 if valid, 1 with a structured error message otherwise. No execution. No IR output.

```bash
fusionflow validate my_spec.ff
# OK: my_spec.ff is a valid FusionFlow specification.
```

## `fusionflow compile <file>`

Build the deterministic Temporal IR JSON.

| Flag | Default | Description |
|---|---|---|
| `--out <path>` | stdout | Write JSON to this file |
| `--compact` | off | Emit compact JSON without indentation |

```bash
fusionflow compile my_spec.ff --out my_spec.tir.json
fusionflow compile my_spec.ff --compact
```

The IR is byte-deterministic: the same `.ff` file always produces the same JSON. Use this for reproducibility audits or to feed downstream tools.

## `fusionflow <file>` (v0.3 bare-run mode)

The legacy bare-run mode is preserved for backwards compatibility:

| Flag | Description |
|---|---|
| `--print-ast` | Dump the parsed AST |
| `--print-state` | List declared datasets, pipelines, models, timelines, experiments |
| `--debug` | Print token stream + full traceback on errors |
| `--version` | Print version and exit |

```bash
fusionflow my_spec.ff --print-state
fusionflow --version
```

In v0.5 this bare-run mode will likely be deprecated in favor of explicit subcommands.
