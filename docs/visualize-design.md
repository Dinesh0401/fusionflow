# `fusionflow visualize` — Design Doc

**Status:** designed, not implemented. Target: v0.5.x.

## Goal

`fusionflow visualize <spec.ff>` produces a static HTML page (or PNG via Graphviz) showing:
1. The **timeline DAG** — main + branches, with merge arrows annotated by justification.
2. The **experiment graph** — datasets → pipelines → models → experiments, with operation lists.
3. (Optional v0.5.x) **metric comparison** when multiple experiments are present.

## CLI shape

```bash
fusionflow visualize spec.ff --out report.html
fusionflow visualize spec.ff --format dot       # graphviz dot
fusionflow visualize spec.ff --format mermaid   # mermaid for GitHub README embedding
```

## Implementation sketch

- `fusionflow/visualize.py` — pure IR-consumer (same as `diff.py`).
- Render via:
  - **HTML**: Jinja2-ish string templates (no external dep beyond what's already in `pyproject.toml`).
  - **DOT**: emit Graphviz dot syntax directly (no Graphviz binary required to GENERATE — only to render).
  - **Mermaid**: emit Mermaid syntax, paste into a markdown file.
- CLI subcommand wires into `fusionflow/__main__.py` next to `diff`.

## Why this matters

- Demos: `fusionflow visualize` on a 30-line timeline `.ff` shows what a 300-line Python script can't.
- Research: papers love clean diagrams of experiment graphs.
- Adoption: README GIFs / blog posts use the output directly.

## Not in scope for v0.5.x

- Interactive web UI.
- Live updating during execution.
- Integration with Jupyter (could come via `IPython.display.HTML`, but defer).
