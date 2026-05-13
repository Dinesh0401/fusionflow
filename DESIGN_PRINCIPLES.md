# FusionFlow Design Principles

The few decisions that explain most of the codebase.

## 1. The IR is the contract

Frontends produce IR. Backends consume IR. They never talk to each other directly. This single rule is why:
- The parser can add new keywords without breaking backends.
- Backends can be swapped (Pandas today, Spark soon) with no source-level changes.
- The IR can be persisted, diffed, and version-gated.

If you find yourself importing `fusionflow.parser` from a backend, stop. Lower it to IR first.

## 2. Time is first-class

Datasets carry versions. Pipelines reference dataset versions. Timelines branch off other timelines. Merges require justification. **Time isn't metadata — it's part of the language.**

## 3. Determinism > speed

Given the same seed + same fixture, two runs must produce byte-identical `RunResult.to_json()` output. This is enforced by `tests/test_determinism.py` (subprocess hash test). If a backend can't be deterministic, that's a backend bug, not an acceptable tradeoff.

## 4. Additive evolution

New keywords are additive. v0.3 `.ff` files still parse under v0.4. The IR `ir_version` field gates incompatible changes. Removing or renaming syntax requires a major version bump and migration notes in `RELEASE_NOTES.md`.

## 5. Errors are structured

`RunResult.status = FAILED` for plan-level errors (missing files, bad columns, unknown models). Backends do NOT raise on these — they return a structured result. Raises are reserved for genuine bugs.

## 6. Opt-in extras for the long tail

`pip install fusionflow` ships the core. Integrations (`[mlflow]`, `[jupyter]`) are extras. Heavy deps don't get into the base install path.

## 7. Tests pin behavior, not implementation

When a P1 IR bug is fixed, the regression test asserts the **string output** of `_expression_to_string`, not the internal precedence table. This way refactors don't trigger churn.
