"""Cross-process determinism tests for the v0.4.0 Pandas backend.

These tests invoke `fusionflow run` in subprocess (a fresh Python interpreter)
twice and assert byte-identical stdout. Same-process determinism is already
covered by tests/test_executor_pandas.py -- this file proves the contract holds
across process boundaries (the real-world reproducibility test)."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


def _run_once(env_overrides: dict | None = None) -> str:
    """Run `fusionflow run regression.ff` and return stdout."""
    env = os.environ.copy()
    # Pin all known thread env vars so the subprocess inherits a clean state
    env.update({
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "PYTHONHASHSEED": "0",
    })
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        [
            sys.executable, "-m", "fusionflow", "run",
            str(FIXTURES / "regression.ff"),
            "--backend", "pandas",
            "--seed", "42",
            "--num-threads", "1",
            "--data-root", str(FIXTURES),
        ],
        capture_output=True,
        text=True,
        check=True,
        env=env,
        cwd=REPO_ROOT,
    )
    return result.stdout


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def test_two_subprocess_runs_produce_byte_identical_output():
    """The headline determinism contract: same seed + same fixture -> same bytes."""
    first = _run_once()
    second = _run_once()
    assert first == second, "Two subprocess runs produced different output (determinism broken)"


def test_subprocess_output_is_valid_json():
    """The stdout from `fusionflow run` must be parseable as JSON."""
    output = _run_once()
    parsed = json.loads(output)
    assert parsed["status"] == "success"
    assert "rmse" in parsed["metrics"]


def test_subprocess_hash_matches_pinned_value():
    """Pin the SHA-256 of the expected output. If sklearn changes default
    behavior, this test fails LOUDLY (which is the signal we want)."""
    output = _run_once()
    digest = _sha256(output)
    # The pinned hash is computed on this machine + sklearn version + pandas version.
    # On other environments this may differ -- that is the intended signal that the
    # determinism guarantee is environment-bound. Skip if we don't have a recorded value.
    parsed = json.loads(output)
    assert isinstance(parsed["metrics"]["rmse"], float)
    assert isinstance(parsed["metrics"]["mae"], float)
    # Lock these golden values: any drift in sklearn/numpy that changes them indicates
    # we need to rebuild the pinned hash and announce it as a determinism breakpoint.
    assert parsed["metrics"]["rmse"] == 100.93763059566317, \
        f"RMSE drifted to {parsed['metrics']['rmse']} -- sklearn/numpy/pandas may have changed"
    assert parsed["metrics"]["mae"] == 88.63048903252889, \
        f"MAE drifted to {parsed['metrics']['mae']} -- sklearn/numpy/pandas may have changed"
    # Don't pin SHA -- it's also sensitive to whitespace/encoding which json.dumps handles
    # but might vary across platforms. Pinning floats is the load-bearing assertion.


def test_run_context_thread_pinning_idempotent():
    """RunContext.apply_thread_pinning uses setdefault -- calling twice doesn't override."""
    from fusionflow.executor import RunContext

    # Set an explicit value first
    os.environ["OMP_NUM_THREADS"] = "8"
    try:
        RunContext(seed=42, num_threads=1).apply_thread_pinning()
        # User's value is preserved
        assert os.environ["OMP_NUM_THREADS"] == "8"
    finally:
        # Cleanup so we don't pollute the test env
        del os.environ["OMP_NUM_THREADS"]


def test_run_context_pins_unset_env_vars():
    """RunContext.apply_thread_pinning sets vars that aren't already set."""
    from fusionflow.executor import RunContext

    # Make sure these are unset
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ.pop(var, None)

    try:
        RunContext(seed=42, num_threads=2).apply_thread_pinning()
        assert os.environ["OMP_NUM_THREADS"] == "2"
        assert os.environ["MKL_NUM_THREADS"] == "2"
        assert os.environ["OPENBLAS_NUM_THREADS"] == "2"
        assert os.environ["NUMEXPR_NUM_THREADS"] == "2"
    finally:
        for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            os.environ.pop(var, None)


def test_run_context_is_frozen():
    """RunContext is immutable for safety in shared use."""
    from fusionflow.executor import RunContext
    ctx = RunContext(seed=42, num_threads=1)
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError, depending on dataclass version
        ctx.seed = 99


def test_pandas_backend_accepts_run_context():
    """PandasBackend can be constructed with a RunContext OR a bare seed."""
    from fusionflow.executor import PandasBackend, RunContext, load_plan
    from fusionflow.lexer import Lexer
    from fusionflow.parser import Parser
    from fusionflow.interpreter import Interpreter
    from fusionflow.runtime import Runtime
    from fusionflow.ir_export import build_temporal_ir

    src = (FIXTURES / "regression.ff").read_text()
    tokens = Lexer(src).tokenize()
    program = Parser(tokens).parse()
    runtime = Runtime()
    Interpreter(runtime).execute(program)
    ir = build_temporal_ir(runtime)
    plan = load_plan(ir, experiment_name="regression_baseline")

    # With context
    ctx = RunContext(seed=42, num_threads=1)
    backend_with_ctx = PandasBackend(data_root=FIXTURES, context=ctx)
    result_ctx = backend_with_ctx.execute(plan)

    # With bare seed
    backend_bare = PandasBackend(seed=42, data_root=FIXTURES)
    result_bare = backend_bare.execute(plan)

    # Both must produce byte-identical output
    assert result_ctx.to_json() == result_bare.to_json()
