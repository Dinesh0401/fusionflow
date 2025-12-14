"""CLI entrypoint to train baseline and advanced failure prediction models."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.ml.failure_model import FailureModelTrainer


def main() -> None:
    parser = argparse.ArgumentParser(description="Train failure prediction models from telemetry data")
    parser.add_argument("--telemetry", default="data/telemetry/pipeline_runs.csv", help="Path to telemetry CSV")
    parser.add_argument(
        "--model",
        default="models/failure_model.joblib",
        help="Where to store the trained baseline model",
    )
    parser.add_argument(
        "--advanced-model",
        dest="advanced_model",
        default="models/failure_model_advanced.joblib",
        help="Where to store the advanced failure model",
    )
    parser.add_argument(
        "--variant",
        choices=["baseline", "advanced", "both"],
        default="baseline",
        help="Which model variant to train",
    )
    args = parser.parse_args()

    telemetry_path = Path(args.telemetry)

    if args.variant in {"baseline", "both"}:
        trainer = FailureModelTrainer(telemetry_path=telemetry_path, model_path=Path(args.model))
        trainer.train()

    if args.variant in {"advanced", "both"}:
        from src.ml.advanced_failure_model import AdvancedFailureModelTrainer

        advanced_trainer = AdvancedFailureModelTrainer(
            telemetry_path=telemetry_path,
            model_path=Path(args.advanced_model),
        )
        advanced_trainer.train()


if __name__ == "__main__":  # pragma: no cover
    main()
