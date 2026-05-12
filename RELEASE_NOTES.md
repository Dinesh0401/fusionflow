# Release Notes

## v0.4.0 — "FusionFlow Runs" (2026-05-11)

**The TSL stops being a spec and starts being a tool.** v0.4.0 ships real execution: `pip install fusionflow && fusionflow run my_spec.ff` actually trains a model on Pandas and prints metrics — byte-deterministic across runs given the same seed.

### Install

```bash
pip install fusionflow                   # core
pip install "fusionflow[mlflow]"         # + MLflow autologger
pip install "fusionflow[jupyter]"        # + Jupyter %%fusionflow magic
pip install "fusionflow[all]"            # everything
```

### Highlights

- **Pandas execution backend** — full op support (`derive`, `select`, `target`, `where`, `split`, `features`, `checkpoint`). 4 model types (linear/logistic regression, RF classifier/regressor) and 5 metrics (rmse, mae, accuracy, f1, auc).
- **New CLI subcommands**:
  - `fusionflow run <file>` — execute one experiment via the chosen backend
  - `fusionflow validate <file>` — parse + interpret without running
  - `fusionflow compile <file>` — emit Temporal IR JSON (unchanged from v0.3)
- **Determinism contract** — same seed + same fixture → byte-identical `RunResult.to_json()` across processes (verified by `tests/test_determinism.py`).
- **MLflow autologger** (opt-in) — `--mlflow` flag logs params, metrics, and the IR artifact.
- **Jupyter `%%fusionflow` magic** (opt-in) — run pipelines inline in notebooks; metrics returned as a pandas Series.
- **VS Code extension v0.2.0** — 13 snippets for every v0.4 construct, listed in the "Snippets" Marketplace category.
- **CI/CD** — GitHub Actions for tests (matrix: ubuntu/windows/macos × py3.10/3.11/3.12), automated PyPI publishing on `v*` tags, automated VS Code Marketplace publishing on `vscode-v*` tags.
- **138 tests passing** across lexer, parser, IR roundtrip, executor, Pandas backend, CLI integration, determinism, MLflow, Jupyter, VS Code extension, examples, backwards-compat.

### New language features

Four additive keywords (parser unchanged for v0.3 specs without them):

| Keyword | Meaning |
|---|---|
| `where <expr>` | Row filter — keeps rows where the expression evaluates to true |
| `split <number>` | Train/test split — number is the train ratio in `(0, 1)` |
| `features [<id>, ...]` | Declares feature columns for training |
| `checkpoint <name>` | Named save point (no-op in v0.4; persisted state in v0.5+) |

### IR v0.4

The Temporal IR now carries an `ir_version` field. v0.3 IR (no field) is treated as `"0.3"` by the loader. v0.4 IR with new ops cannot be loaded by v0.3 tools. See [`docs/ir-spec-v0.4.md`](docs/ir-spec-v0.4.md).

### Breaking changes

- **Reserved keywords**: `where`, `split`, `features`, and `checkpoint` are now reserved. If your v0.3 `.ff` files used these as identifier names (e.g., a schema field called `features`), you must rename before upgrading.
- **Python 3.8 / 3.9 dropped**: minimum is now Python 3.10.
- **`fusionflow/upeg.py` removed**: was unused; replacement plugin API lands in v1.0.0.

### CLI flags (new)

| Flag | Default | Description |
|---|---|---|
| `--backend pandas\|noop` | `pandas` | Execution backend |
| `--seed <int>` | `42` | RNG seed for splits + stochastic models |
| `--num-threads <int>` | `1` | Threads for numpy/sklearn (`1` for determinism) |
| `--out <path>` | stdout | Write `RunResult.to_json()` to file |
| `--data-root <path>` | `<.ff dir>` | Base for resolving dataset source paths |
| `--mlflow` | off | Log run to MLflow (requires `[mlflow]` extra) |
| `--experiment <name>` | first | Which experiment to execute (when multiple exist) |

### Architecture

`fusionflow run` walks the standard path: **`.ff` → Lexer → Parser → AST → ir_export → IR (JSON) → ir_loader → ExecutionPlan → Backend.execute(plan) → RunResult**. The executor consumes IR ONLY (never AST) — the firewall that lets parser additions stay backwards-compatible. Backends register via the `ExecutionBackend` Protocol in `fusionflow.executor.backends`.

### Coming in v0.5

- Spark backend on the same IR
- LSP (diagnostics, go-to-def) for the VS Code extension
- `join` keyword
- Merge algorithm wired (conflict detection + strategy resolution)
- W&B integration
- `fusionflow diff` for IR-aware semantic diffs

### Coming in v1.0

- IR frozen forever (semver promise)
- Full LSP (hover, completion, refactoring)
- Plugin API for third-party backends, models, metrics
- Reproducibility certificates
- arXiv paper

### Manual setup required before publishing

Both publishing workflows require one-time configuration:

**PyPI** (`.github/workflows/publish-pypi.yml`):
1. Create a trusted publisher at https://pypi.org/manage/account/publishing/ pointing at this repo and the `publish-pypi.yml` workflow.
2. In GitHub repo Settings → Environments, create an environment named `pypi`.
3. Push the `v0.4.0` tag: `git push origin v0.4.0`.

**VS Code Marketplace** (`.github/workflows/publish-vscode.yml`):
1. Generate a Personal Access Token at https://learn.microsoft.com/en-us/azure/devops/marketplace/extensions with `Marketplace > Publish` scope.
2. Add it as a repo secret named `VSCE_PAT`.
3. In GitHub repo Settings → Environments, create an environment named `vscode-marketplace`.
4. Push the `vscode-v0.2.0` tag: `git push origin vscode-v0.2.0`.

---

## Older releases

- **v0.3.0** — TSL Freeze (language semantics frozen, Temporal IR stable, execution intentionally deferred).
- **v0.1.0** — First public release (lexer/parser/interpreter for the TSL syntax).
