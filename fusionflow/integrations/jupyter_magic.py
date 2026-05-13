"""Jupyter `%%fusionflow` cell magic.

Usage in a Jupyter notebook:

    %load_ext fusionflow.integrations.jupyter_magic

    %%fusionflow
    dataset users v1
        source "users.csv"
    end
    pipeline p
        from users v1
        features [age]
        split 0.8
        target spend
    end
    model lin
        type linear_regression
    end
    experiment baseline
        uses pipeline p
        uses model lin
        metrics [rmse]
    end

The magic parses the cell, executes the FIRST experiment via PandasBackend,
and returns a pandas Series of the metrics for inline display.

Install with: pip install fusionflow[jupyter]
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Optional


class JupyterNotInstalledError(RuntimeError):
    """Raised when IPython is needed but not installed."""


def _import_ipython():
    """Lazy IPython import with a helpful install hint."""
    try:
        from IPython.core.magic import Magics, cell_magic, magics_class  # type: ignore
        return Magics, cell_magic, magics_class
    except ImportError as exc:
        raise JupyterNotInstalledError(
            "IPython is not installed. Install with: pip install fusionflow[jupyter]"
        ) from exc


def _import_pandas():
    try:
        import pandas as pd  # type: ignore
        return pd
    except ImportError as exc:
        raise JupyterNotInstalledError(
            "pandas is not installed. Install with: pip install fusionflow[jupyter]"
        ) from exc


def execute_cell(
    source: str,
    seed: int = 42,
    data_root: Optional[Path] = None,
    experiment_name: Optional[str] = None,
) -> Any:
    """Pure (non-IPython) entry point: parse, execute, return result.

    Returns a pandas Series of the metrics, with the full RunResult attached
    as the `_fusionflow_run_result` attribute for advanced use.
    """
    pd = _import_pandas()

    from fusionflow.executor import PandasBackend, load_plan
    from fusionflow.interpreter import Interpreter
    from fusionflow.ir_export import build_temporal_ir
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.runtime import Runtime

    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    ir = build_temporal_ir(runtime)

    if experiment_name is None:
        # Pick first experiment from main timeline, then sub-timelines
        main = runtime.timelines.get("main")
        if main and main.experiments:
            experiment_name = next(iter(main.experiments))
        else:
            for tl_name in sorted(runtime.timelines):
                if tl_name == "main":
                    continue
                tl = runtime.timelines[tl_name]
                if tl.experiments:
                    experiment_name = next(iter(tl.experiments))
                    break
        if experiment_name is None:
            raise ValueError("No experiments found in the cell.")

    plan = load_plan(ir, experiment_name=experiment_name)
    backend = PandasBackend(seed=seed, data_root=data_root or Path.cwd())
    result = backend.execute(plan)

    series = pd.Series(result.metrics, name=f"{result.experiment} ({result.status.value})")
    # pandas warns on attribute creation; suppress since this is intentional metadata.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        series._fusionflow_run_result = result  # type: ignore[attr-defined]
    return series


def load_ipython_extension(ipython):
    """Called by `%load_ext fusionflow.integrations.jupyter_magic`."""
    Magics, cell_magic, magics_class = _import_ipython()

    @magics_class
    class FusionFlowMagics(Magics):

        @cell_magic
        def fusionflow(self, line: str, cell: str):
            """Parse and execute a FusionFlow cell. Returns metrics as a Series."""
            return execute_cell(cell)

    ipython.register_magics(FusionFlowMagics)


def unload_ipython_extension(ipython):
    """Optional: called by `%unload_ext`. No-op for now."""
    pass
