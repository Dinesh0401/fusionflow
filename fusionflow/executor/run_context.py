"""RunContext: seed, thread count, and other determinism knobs.

A backend instantiated with the same RunContext must produce byte-identical
RunResult.to_json() output, even across different Python processes."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RunContext:
    """Pinned execution settings for deterministic runs.

    - ``seed``: random seed used by sklearn estimators and train_test_split.
    - ``num_threads``: pinned for numpy/sklearn parallelism. Default 1
      (single-thread). Higher values may produce non-deterministic output.

    Use ``apply_thread_pinning()`` to set the relevant env vars BEFORE
    importing numpy/sklearn for the first time. Most safely called once at
    process startup (e.g., from CLI before backend instantiation).
    """

    seed: int = 42
    num_threads: int = 1

    def apply_thread_pinning(self) -> None:
        """Set OMP_NUM_THREADS / MKL_NUM_THREADS / OPENBLAS_NUM_THREADS to
        ``num_threads`` if they are not already set in the environment.

        Uses ``setdefault`` so user-set env vars are respected. Idempotent.
        Note: numpy/MKL read these at first import -- call this BEFORE the
        first numpy import for full effect.
        """
        value = str(self.num_threads)
        os.environ.setdefault("OMP_NUM_THREADS", value)
        os.environ.setdefault("MKL_NUM_THREADS", value)
        os.environ.setdefault("OPENBLAS_NUM_THREADS", value)
        os.environ.setdefault("NUMEXPR_NUM_THREADS", value)
