# Contributing to FusionFlow

Thank you for considering contributing to FusionFlow. This document explains how to get set up and what to expect.

## Quick start for contributors

```bash
git clone https://github.com/Dinesh0401/fusionflow.git
cd fusionflow
pip install -e ".[dev,mlflow,jupyter]"
python -m pytest tests/ -q
```

You should see all tests pass.

## Code style

- Follow existing patterns in the file you're modifying.
- Run `python -m ruff check fusionflow tests` before submitting a PR.
- New language features go through `lexer → parser → AST → ir_export → executor` — preserve that flow.
- The IR is the contract between frontend and backends. Backends never import from `fusionflow.parser` or `fusionflow.ast_nodes`.

## What we welcome

- **Bug fixes** with regression tests
- **New backend implementations** (Spark, Polars, Ray) against the existing `ExecutionBackend` Protocol
- **Documentation improvements** — getting-started, examples, IR spec clarifications
- **Test coverage** for under-tested paths

## What's on hold

The language grammar is **frozen for the v0.5 cycle** (see [`SYNTAX_FROZEN.md`](SYNTAX_FROZEN.md)). New keywords or breaking syntax changes will not be accepted until the next major version. This is to give early adopters a stable target.

## PR process

1. Open a draft PR early — even one-line fixes benefit from review.
2. CI runs on every PR (matrix: ubuntu/windows/macos × py3.10/3.11/3.12).
3. Tests must pass + ruff must run clean.
4. One commit per logical change. Squash before merge.

## Questions?

Open an issue at https://github.com/Dinesh0401/fusionflow/issues.
