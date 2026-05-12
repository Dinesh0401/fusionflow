"""Integration tests for the `fusionflow diff` CLI subcommand."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args, cwd=None):
    cmd = [sys.executable, "-m", "fusionflow", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd or REPO_ROOT,
    )


def _write_spec(tmp_path, name, body):
    path = tmp_path / name
    path.write_text(body)
    return path


SPEC_A = """
dataset d v1
    source "x.csv"
end
pipeline p
    from d v1
    derive y = age + 1
    target y
end
"""

SPEC_B = """
dataset d v1
    source "x.csv"
end
pipeline p
    from d v1
    derive y = age + 2
    target y
end
"""


def test_cli_diff_identical_specs_returns_zero(tmp_path):
    a = _write_spec(tmp_path, "a.ff", SPEC_A)
    b = _write_spec(tmp_path, "b.ff", SPEC_A)
    result = run_cli("diff", str(a), str(b))
    assert result.returncode == 0
    assert "Identical" in result.stdout


def test_cli_diff_different_specs_returns_one(tmp_path):
    a = _write_spec(tmp_path, "a.ff", SPEC_A)
    b = _write_spec(tmp_path, "b.ff", SPEC_B)
    result = run_cli("diff", str(a), str(b))
    assert result.returncode == 1
    assert "pipelines:" in result.stdout
    assert "p" in result.stdout  # the changed pipeline


def test_cli_diff_json_output(tmp_path):
    a = _write_spec(tmp_path, "a.ff", SPEC_A)
    b = _write_spec(tmp_path, "b.ff", SPEC_B)
    result = run_cli("diff", str(a), str(b), "--json")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert "pipelines" in payload
    assert "p" in payload["pipelines"]["changed"]


def test_cli_diff_missing_file_returns_two(tmp_path):
    a = _write_spec(tmp_path, "a.ff", SPEC_A)
    result = run_cli("diff", str(a), "definitely_missing.ff")
    assert result.returncode == 2
    assert result.stderr  # some error message
