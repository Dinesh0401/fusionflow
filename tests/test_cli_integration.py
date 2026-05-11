"""Integration tests for the FusionFlow CLI (subprocess-driven)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


def run_cli(*args, cwd=None):
    """Invoke `python -m fusionflow ...` and return CompletedProcess."""
    cmd = [sys.executable, "-m", "fusionflow", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd or REPO_ROOT,
    )


# --- validate ---

def test_cli_validate_accepts_valid_spec():
    result = run_cli("validate", str(FIXTURES / "regression.ff"))
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "OK" in result.stdout


def test_cli_validate_rejects_missing_file():
    result = run_cli("validate", "definitely_does_not_exist.ff")
    assert result.returncode == 1
    assert "not found" in result.stderr.lower() or "no such file" in result.stderr.lower()


def test_cli_validate_rejects_syntax_error(tmp_path):
    bad = tmp_path / "bad.ff"
    bad.write_text("dataset @@@ not valid syntax\n")
    result = run_cli("validate", str(bad))
    assert result.returncode == 1
    assert result.stderr  # some error message


# --- run ---

def test_cli_run_executes_regression_with_pandas(tmp_path):
    out = tmp_path / "result.json"
    result = run_cli(
        "run",
        str(FIXTURES / "regression.ff"),
        "--backend", "pandas",
        "--seed", "42",
        "--out", str(out),
        "--data-root", str(FIXTURES),
    )
    assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
    payload = json.loads(out.read_text())
    assert payload["status"] == "success"
    assert payload["backend"] == "pandas"
    assert payload["ir_version"] == "0.4"
    assert "rmse" in payload["metrics"]
    assert "mae" in payload["metrics"]


def test_cli_run_prints_json_when_no_out(tmp_path):
    result = run_cli(
        "run",
        str(FIXTURES / "regression.ff"),
        "--backend", "pandas",
        "--seed", "42",
        "--data-root", str(FIXTURES),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    # stdout should be JSON
    payload = json.loads(result.stdout)
    assert payload["experiment"] == "regression_baseline"


def test_cli_run_with_noop_backend_returns_skipped(tmp_path):
    result = run_cli(
        "run",
        str(FIXTURES / "regression.ff"),
        "--backend", "noop",
        "--data-root", str(FIXTURES),
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "skipped"
    assert payload["backend"] == "noop"


def test_cli_run_explicit_experiment_selection(tmp_path):
    result = run_cli(
        "run",
        str(FIXTURES / "regression.ff"),
        "--experiment", "regression_baseline",
        "--backend", "pandas",
        "--seed", "42",
        "--data-root", str(FIXTURES),
    )
    assert result.returncode == 0


def test_cli_run_unknown_experiment(tmp_path):
    result = run_cli(
        "run",
        str(FIXTURES / "regression.ff"),
        "--experiment", "no_such_experiment",
        "--backend", "noop",
    )
    # Either 1 (not found) or 2 (ambiguous) is acceptable; not 0
    assert result.returncode != 0


def test_cli_run_default_data_root_is_ff_directory(tmp_path):
    """When --data-root is omitted, paths in the .ff resolve relative to the .ff file's directory."""
    # Copy the fixture into a fresh temp dir so the .ff and tiny.csv are siblings
    spec = (FIXTURES / "regression.ff").read_text()
    csv_data = (FIXTURES / "tiny.csv").read_text()
    (tmp_path / "tiny.csv").write_text(csv_data)
    (tmp_path / "regression.ff").write_text(spec)
    result = run_cli(
        "run",
        str(tmp_path / "regression.ff"),
        "--backend", "pandas",
        "--seed", "42",
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_cli_run_mlflow_flag_warns_but_succeeds(tmp_path):
    """--mlflow is accepted in v0.4 but defers actual integration to Task 9."""
    result = run_cli(
        "run",
        str(FIXTURES / "regression.ff"),
        "--backend", "noop",
        "--mlflow",
        "--data-root", str(FIXTURES),
    )
    assert result.returncode == 0
    assert "mlflow" in result.stderr.lower() or "mlflow" in result.stdout.lower()


# --- backwards-compat (existing v0.3 surface still works) ---

def test_cli_version_flag_still_works():
    result = run_cli("--version")
    assert result.returncode == 0
    assert "FusionFlow" in result.stdout
    assert "0.4.0.dev0" in result.stdout


def test_cli_print_state_still_works():
    result = run_cli(str(FIXTURES / "regression.ff"), "--print-state")
    assert result.returncode == 0
    assert "Datasets" in result.stdout
    assert "Pipelines" in result.stdout


def test_cli_compile_still_works(tmp_path):
    out = tmp_path / "ir.json"
    result = run_cli("compile", str(FIXTURES / "regression.ff"), "--out", str(out))
    assert result.returncode == 0
    ir = json.loads(out.read_text())
    assert ir["ir_version"] == "0.4"
