"""Integration tests for the `fusionflow visualize` CLI subcommand."""

import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args, cwd=None):
    cmd = [sys.executable, "-m", "fusionflow", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=cwd or REPO_ROOT)


SPEC = """
dataset d v1
    source "x.csv"
end
pipeline p
    from d v1
    derive y = age + 1
    target y
end
model m
    type linear_regression
end
experiment e
    uses pipeline p
    uses model m
    metrics [rmse]
end
"""


def _write(tmp_path, body):
    path = tmp_path / "spec.ff"
    path.write_text(body)
    return path


def test_cli_visualize_default_mermaid(tmp_path):
    spec = _write(tmp_path, SPEC)
    result = run_cli("visualize", str(spec))
    assert result.returncode == 0
    assert result.stdout.startswith("graph TD")


def test_cli_visualize_dot_format(tmp_path):
    spec = _write(tmp_path, SPEC)
    result = run_cli("visualize", str(spec), "--format", "dot")
    assert result.returncode == 0
    assert "digraph fusionflow" in result.stdout


def test_cli_visualize_html_to_file(tmp_path):
    spec = _write(tmp_path, SPEC)
    out = tmp_path / "viz.html"
    result = run_cli("visualize", str(spec), "--format", "html", "--out", str(out))
    assert result.returncode == 0
    assert out.exists()
    content = out.read_text()
    assert "<!DOCTYPE html>" in content


def test_cli_visualize_missing_file():
    result = run_cli("visualize", "definitely_missing.ff")
    assert result.returncode == 2
    assert result.stderr


def test_cli_visualize_bad_format(tmp_path):
    spec = _write(tmp_path, SPEC)
    result = run_cli("visualize", str(spec), "--format", "crayon")
    # argparse rejects invalid choice with exit code 2
    assert result.returncode == 2
