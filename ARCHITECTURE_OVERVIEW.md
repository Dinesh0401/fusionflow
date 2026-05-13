# FusionFlow Architecture Overview

A 5-minute orientation for new contributors.

## Top-level dataflow

```
.ff source
   │
   ▼
[ Lexer ]   →  Tokens
   │
   ▼
[ Parser ]  →  AST (typed dataclasses)
   │
   ▼
[ Interpreter ]  →  Runtime registry
   │
   ▼
[ ir_export.build_temporal_ir ]  →  IR (JSON dict)
   │
   ▼
─────── IR is the contract ───────
   │
   ▼
[ ir_loader.load_plan ]  →  ExecutionPlan (frozen dataclasses)
   │
   ▼
[ Backend.execute(plan) ]  →  RunResult
```

## Source layout

```
fusionflow/
├── lexer.py           # Tokenize .ff source
├── tokens.py          # TokenType enum
├── parser.py          # Recursive descent parser
├── ast_nodes.py       # AST dataclasses
├── interpreter.py     # AST → Runtime registry (compile-time)
├── runtime.py         # Registry of datasets/pipelines/models/timelines/experiments
├── ir_export.py       # Runtime → deterministic JSON IR
├── diff.py            # IR-aware semantic diff (v0.5)
├── merge_algorithm.py # Real merge conflict detection (v0.5)
├── __main__.py        # CLI (run/validate/compile/diff/bare-run)
├── __init__.py        # Package marker + __version__
├── executor/
│   ├── plan.py        # ExecutionPlan + Op subclasses (frozen)
│   ├── ir_loader.py   # IR dict → ExecutionPlan
│   ├── run_result.py  # RunResult + RunStatus
│   ├── run_context.py # Seed + thread pinning
│   ├── models.py      # Model registry (4 sklearn estimators)
│   ├── metrics.py     # Metric registry (5 sklearn metrics)
│   └── backends/
│       ├── __init__.py     # ExecutionBackend Protocol + SupportReport
│       ├── noop_backend.py # Validates plan, returns SKIPPED
│       └── pandas_backend.py # Real execution (csv/parquet → train → eval)
└── integrations/      # Opt-in (gated by [mlflow] / [jupyter] extras)
    ├── mlflow_logger.py
    └── jupyter_magic.py
```

## Where to make changes

| Want to... | Touch... |
|---|---|
| Add a new keyword | `tokens.py` + `lexer.py` + `parser.py` + `ast_nodes.py` + `ir_export.py` + `ir_loader.py` + backend dispatch |
| Add a new model type | `executor/models.py` only |
| Add a new metric | `executor/metrics.py` only |
| Add a new backend | New file under `executor/backends/`; implement `ExecutionBackend` Protocol |
| Add a CLI subcommand | `__main__.py` only |
| Add an integration | New module under `integrations/` + `[name]` extra in `pyproject.toml` |

## What NOT to do

- Don't import `parser` / `ast_nodes` / `interpreter` from anything under `executor/`.
- Don't `mlflow.start_run()` at module top level — keep imports lazy.
- Don't break IR v0.4 — additions must be backwards-compatible until the next major version.
- Don't add CI jobs without a determinism story.

## Open architectural questions

- **Backend plugins**: third-party backends via entry-points is a v1.0 feature. Until then, backends live in-tree.
- **IR v0.5 schema**: do we add a `meta` top-level dict, or keep `ir_version` flat? Pinned by the v0.5 release decision.
- **Expression IR**: today `where`/`derive` expressions are STRINGS. v1.0 may upgrade to typed expression trees for backend pushdown.
