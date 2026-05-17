# FusionFlow Roadmap

A living document. Updated when priorities shift.

## v0.4.0 (shipped)

- TSL `.ff` source → AST → deterministic JSON IR
- Pandas execution backend (4 model types, 5 metrics)
- CLI: `run`, `validate`, `compile`, bare-run (v0.3 compat)
- New keywords: `where`, `split`, `features`, `checkpoint`
- IR v0.4 schema with explicit `ir_version`
- MLflow + Jupyter integrations (opt-in extras)
- VS Code extension v0.2.0 with 13 snippets
- Cross-process determinism contract

## v0.5.0-dev0 (current)

**Theme:** Distributed and Diagnosable.

Shipped in dev0:
- [x] Merge algorithm wired (real conflict detection + 3 strategies)
- [x] `fusionflow diff` IR-aware semantic diff
- [x] Codex P1 fixes (IR expression parenthesization correctness)
- [x] Contributor + adoption infrastructure (this PR)

Targeted for v0.5.0 final:
- [ ] `join` keyword (multi-dataset support)
- [ ] Spark backend on the same IR
- [x] `fusionflow visualize` — timeline DAG / experiment graph (mermaid / dot / html) (see [`docs/visualize-design.md`](docs/visualize-design.md))
- [ ] Basic LSP (diagnostics + go-to-def) for VS Code v0.3.0
- [ ] mkdocs docs site at GitHub Pages

**Explicitly deferred** (not v0.5): `.exe` builds, W&B integration, advanced LSP (hover/completion), online-learning hooks.

## v1.0.0 (future)

- IR frozen forever (semver promise)
- Plugin API for third-party backends, models, metrics
- Reproducibility certificate command
- Polars backend as third proof of pluggability
- Full LSP with hover docs + refactoring
- arXiv paper publication (see [`docs/paper-outline.md`](docs/paper-outline.md))

## How this roadmap is maintained

- New features are scoped to a target version BEFORE work begins.
- Items only move "forward" (e.g., v0.5 → v0.6) — never backward.
- Each shipped version freezes its scope; no quiet scope creep mid-cycle.
