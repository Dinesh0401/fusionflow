"""Tests for the Jupyter magic integration.

The pure execute_cell function is tested directly. The IPython extension
loading is tested with a mock IPython shell."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"


def test_execute_cell_runs_inline_spec():
    """The pure execute_cell entry point parses, runs, and returns a Series with metrics."""
    from fusionflow.integrations.jupyter_magic import execute_cell

    source = """
    dataset customers v1
        source "tiny.csv"
    end
    pipeline p
        from customers v1
        features [age, income]
        split 0.7
        target spend
    end
    model lin
        type linear_regression
    end
    experiment baseline
        uses pipeline p
        uses model lin
        metrics [rmse, mae]
    end
    """
    result = execute_cell(source, seed=42, data_root=FIXTURES)
    # Returns a pandas Series of metrics
    assert "rmse" in result.index
    assert "mae" in result.index
    # Determinism: matches the pinned values from earlier tasks
    assert result["rmse"] == 100.93763059566317
    assert result["mae"] == 88.63048903252889
    # The full RunResult is attached for advanced users
    assert result._fusionflow_run_result.status.value == "success"


def test_execute_cell_picks_first_experiment_by_default():
    """When experiment_name is None, the magic picks the first experiment from main timeline."""
    from fusionflow.integrations.jupyter_magic import execute_cell

    source = """
    dataset d v1
        source "tiny.csv"
    end
    pipeline p
        from d v1
        features [age]
        split 0.7
        target spend
    end
    model lin
        type linear_regression
    end
    experiment first_exp
        uses pipeline p
        uses model lin
        metrics [rmse]
    end
    experiment second_exp
        uses pipeline p
        uses model lin
        metrics [mae]
    end
    """
    result = execute_cell(source, seed=42, data_root=FIXTURES)
    # first_exp uses metric rmse; second_exp uses mae. Default = first.
    assert "rmse" in result.index
    assert "mae" not in result.index


def test_execute_cell_explicit_experiment_name():
    """experiment_name=... overrides the default."""
    from fusionflow.integrations.jupyter_magic import execute_cell

    source = """
    dataset d v1
        source "tiny.csv"
    end
    pipeline p
        from d v1
        features [age]
        split 0.7
        target spend
    end
    model lin
        type linear_regression
    end
    experiment first_exp
        uses pipeline p
        uses model lin
        metrics [rmse]
    end
    experiment second_exp
        uses pipeline p
        uses model lin
        metrics [mae]
    end
    """
    result = execute_cell(source, seed=42, data_root=FIXTURES, experiment_name="second_exp")
    assert "mae" in result.index
    assert "rmse" not in result.index


def test_execute_cell_raises_on_no_experiments():
    """A spec with no experiments raises a clear error."""
    from fusionflow.integrations.jupyter_magic import execute_cell

    source = """
    dataset d v1
        source "tiny.csv"
    end
    """
    with pytest.raises(ValueError, match="No experiments"):
        execute_cell(source, data_root=FIXTURES)


def test_load_ipython_extension_registers_magic():
    """`%load_ext` calls load_ipython_extension, which registers the cell magic."""
    from fusionflow.integrations.jupyter_magic import load_ipython_extension

    fake_ipython = MagicMock()
    load_ipython_extension(fake_ipython)
    # register_magics should have been called with our Magics class
    fake_ipython.register_magics.assert_called_once()
    # The argument is a class instance; check it has a 'fusionflow' attribute (the cell magic)
    args, kwargs = fake_ipython.register_magics.call_args
    magics_cls = args[0]
    assert hasattr(magics_cls, "fusionflow"), "FusionFlowMagics should expose `fusionflow` cell magic"


def test_quickstart_notebook_is_valid_json():
    """The shipped quickstart notebook must be valid nbformat JSON."""
    import json
    nb_path = REPO_ROOT / "examples" / "quickstart.ipynb"
    assert nb_path.exists(), f"Notebook not found at {nb_path}"
    with open(nb_path) as fh:
        nb = json.load(fh)
    assert nb["nbformat"] == 4
    assert "cells" in nb
    assert any(cell["cell_type"] == "code" and "%load_ext" in "".join(cell.get("source", [])) for cell in nb["cells"]), \
        "Notebook should contain a %load_ext cell"
    assert any("%%fusionflow" in "".join(cell.get("source", [])) for cell in nb["cells"]), \
        "Notebook should contain at least one %%fusionflow cell"
