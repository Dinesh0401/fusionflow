"""Visualize a FusionFlow specification as a graph.

Consumes the Temporal IR (never the AST) and renders two views:
- Experiment graph: datasets -> pipelines -> models -> experiments
- Timeline DAG: main + branch timelines with parent edges and merge arrows

Output formats:
- mermaid : Mermaid `graph` syntax (embeds in GitHub markdown)
- dot     : Graphviz DOT syntax (render with `dot -Tpng`)
- html    : a standalone HTML page embedding the Mermaid diagram via CDN

Used by the `fusionflow visualize` CLI subcommand.
"""

from __future__ import annotations

import html as _html
from typing import Any, Dict, List


SUPPORTED_FORMATS = ("mermaid", "dot", "html")


class VisualizeError(ValueError):
    """Raised when an unsupported format is requested."""


def _sanitize_id(raw: str) -> str:
    """Make a string safe for use as a graph node id (mermaid/dot identifiers
    must be alphanumeric/underscore)."""
    return "".join(c if c.isalnum() else "_" for c in raw)


def _experiment_edges(ir: Dict[str, Any]) -> List[tuple]:
    """Return (from_id, to_id, label) edges for the experiment graph.

    Wiring: dataset -> pipeline (via pipeline.input), pipeline -> experiment,
    model -> experiment. Covers main-timeline experiments and branch experiments.
    """
    edges: List[tuple] = []

    # pipeline -> its input dataset
    for pname, pdata in ir.get("pipelines", {}).items():
        input_ds = pdata.get("input", "")
        if input_ds:
            edges.append((f"ds_{_sanitize_id(input_ds)}", f"pipe_{_sanitize_id(pname)}", "feeds"))

    def _wire_experiment(exp_name: str, exp: Dict[str, Any]) -> None:
        eid = f"exp_{_sanitize_id(exp_name)}"
        pipeline = exp.get("pipeline")
        model = exp.get("model")
        if pipeline:
            edges.append((f"pipe_{_sanitize_id(pipeline)}", eid, "pipeline"))
        if model:
            edges.append((f"model_{_sanitize_id(model)}", eid, "model"))

    for exp_name, exp in ir.get("experiments", {}).items():
        _wire_experiment(exp_name, exp)
    for tl in ir.get("timelines", {}).values():
        for exp_name, exp in tl.get("experiments", {}).items():
            _wire_experiment(exp_name, exp)

    return edges


def _timeline_edges(ir: Dict[str, Any]) -> List[tuple]:
    """Return (from_id, to_id, label) edges for the timeline DAG.

    parent edges: child timeline -> parent timeline.
    merge edges: source timeline -> target timeline, labeled with justification.
    """
    edges: List[tuple] = []
    for tl_name, tl in ir.get("timelines", {}).items():
        parent = tl.get("parent")
        if parent:
            edges.append((f"tl_{_sanitize_id(tl_name)}", f"tl_{_sanitize_id(parent)}", "branches from"))
    for merge in ir.get("merges", []):
        src = merge.get("source", "")
        tgt = merge.get("target", "")
        just = merge.get("justification", "")
        label = f"merge: {just}" if just else "merge"
        edges.append((f"tl_{_sanitize_id(src)}", f"tl_{_sanitize_id(tgt)}", label))
    return edges


def _render_mermaid(ir: Dict[str, Any]) -> str:
    """Render the IR as a Mermaid `graph TD` document."""
    lines: List[str] = ["graph TD"]

    # --- Experiment graph nodes ---
    lines.append("    %% Datasets")
    for ds_key, ds in ir.get("datasets", {}).items():
        nid = f"ds_{_sanitize_id(ds_key)}"
        lines.append(f'    {nid}["dataset: {ds_key}"]')
    lines.append("    %% Pipelines")
    for pname in ir.get("pipelines", {}):
        nid = f"pipe_{_sanitize_id(pname)}"
        op_count = len(ir["pipelines"][pname].get("operations", []))
        lines.append(f'    {nid}("pipeline: {pname} ({op_count} ops)")')
    lines.append("    %% Models")
    for mname, mdata in ir.get("models", {}).items():
        nid = f"model_{_sanitize_id(mname)}"
        lines.append(f'    {nid}["model: {mname} ({mdata.get("type", "?")})"]')
    lines.append("    %% Experiments")

    def _exp_node(exp_name: str, exp: Dict[str, Any]) -> str:
        nid = f"exp_{_sanitize_id(exp_name)}"
        metrics = ", ".join(exp.get("metrics", []))
        return f'    {nid}{{{{"experiment: {exp_name} [{metrics}]"}}}}'

    for exp_name, exp in ir.get("experiments", {}).items():
        lines.append(_exp_node(exp_name, exp))
    for tl in ir.get("timelines", {}).values():
        for exp_name, exp in tl.get("experiments", {}).items():
            lines.append(_exp_node(exp_name, exp))

    for frm, to, label in _experiment_edges(ir):
        lines.append(f"    {frm} -->|{label}| {to}")

    # --- Timeline DAG ---
    timeline_names = ["main"] + sorted(ir.get("timelines", {}).keys())
    if len(timeline_names) > 1 or ir.get("merges"):
        lines.append("    %% Timelines")
        for tl_name in timeline_names:
            nid = f"tl_{_sanitize_id(tl_name)}"
            lines.append(f'    {nid}["timeline: {tl_name}"]')
        for frm, to, label in _timeline_edges(ir):
            lines.append(f"    {frm} -.->|{label}| {to}")

    return "\n".join(lines) + "\n"


def _render_dot(ir: Dict[str, Any]) -> str:
    """Render the IR as a Graphviz DOT document."""
    lines: List[str] = ["digraph fusionflow {", "    rankdir=TD;", '    node [shape=box];']

    for ds_key in ir.get("datasets", {}):
        nid = f"ds_{_sanitize_id(ds_key)}"
        lines.append(f'    {nid} [label="dataset: {ds_key}", shape=cylinder];')
    for pname in ir.get("pipelines", {}):
        nid = f"pipe_{_sanitize_id(pname)}"
        lines.append(f'    {nid} [label="pipeline: {pname}", shape=box];')
    for mname, mdata in ir.get("models", {}).items():
        nid = f"model_{_sanitize_id(mname)}"
        lines.append(f'    {nid} [label="model: {mname}", shape=box];')

    def _exp_dot(exp_name: str) -> str:
        nid = f"exp_{_sanitize_id(exp_name)}"
        return f'    {nid} [label="experiment: {exp_name}", shape=diamond];'

    for exp_name in ir.get("experiments", {}):
        lines.append(_exp_dot(exp_name))
    for tl in ir.get("timelines", {}).values():
        for exp_name in tl.get("experiments", {}):
            lines.append(_exp_dot(exp_name))

    for frm, to, label in _experiment_edges(ir):
        lines.append(f'    {frm} -> {to} [label="{label}"];')

    timeline_names = ["main"] + sorted(ir.get("timelines", {}).keys())
    if len(timeline_names) > 1 or ir.get("merges"):
        for tl_name in timeline_names:
            nid = f"tl_{_sanitize_id(tl_name)}"
            lines.append(f'    {nid} [label="timeline: {tl_name}", shape=ellipse];')
        for frm, to, label in _timeline_edges(ir):
            lines.append(f'    {frm} -> {to} [label="{label}", style=dashed];')

    lines.append("}")
    return "\n".join(lines) + "\n"


def _render_html(ir: Dict[str, Any]) -> str:
    """Render a standalone HTML page embedding the Mermaid diagram."""
    mermaid_body = _render_mermaid(ir)
    ir_version = _html.escape(str(ir.get("ir_version", "0.3")))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>FusionFlow Visualization</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
  h1 {{ font-size: 1.4rem; }}
  .meta {{ color: #666; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>FusionFlow Visualization</h1>
<p class="meta">IR version: {ir_version}</p>
<pre class="mermaid">
{_html.escape(mermaid_body)}
</pre>
<script>mermaid.initialize({{ startOnLoad: true }});</script>
</body>
</html>
"""


def visualize_ir(ir: Dict[str, Any], fmt: str = "mermaid") -> str:
    """Render an IR dict to the requested format.

    Args:
        ir: a Temporal IR dict from ir_export.build_temporal_ir.
        fmt: one of "mermaid", "dot", "html".

    Returns:
        The rendered diagram as a string.

    Raises:
        VisualizeError: if fmt is not supported.
    """
    if fmt == "mermaid":
        return _render_mermaid(ir)
    if fmt == "dot":
        return _render_dot(ir)
    if fmt == "html":
        return _render_html(ir)
    raise VisualizeError(
        f"Unsupported visualize format: {fmt!r}. Supported: {list(SUPPORTED_FORMATS)}."
    )
