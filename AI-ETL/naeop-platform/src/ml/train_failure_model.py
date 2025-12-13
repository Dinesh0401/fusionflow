"""CLI entrypoint to train the failure prediction model."""

from __future__ import annotations

import argparse

from src.ml.failure_model import FailureModelTrainer


def main() -> None:
    parser = argparse.ArgumentParser(description="Train failure prediction model from telemetry data")
    parser.add_argument("--telemetry", default="data/telemetry/pipeline_runs.csv", help="Path to telemetry CSV")
    parser.add_argument("--model", default="models/failure_model.joblib", help="Where to store the trained model")
    args = parser.parse_args()

    trainer = FailureModelTrainer(telemetry_path=args.telemetry, model_path=args.model)
    trainer.train()


if __name__ == "__main__":  # pragma: no cover
    main()
