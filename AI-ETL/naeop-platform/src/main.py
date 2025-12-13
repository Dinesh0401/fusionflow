"""Entry point for the NeuroAdaptive ETL Orchestration Platform."""

import logging
import os

from src.config.settings import get_settings
from src.core.logger import configure_root_logger, get_logger
from src.pipelines.examples.sample_pipeline import SamplePipeline


def main():
    settings = get_settings()
    configure_root_logger(settings.log_level)
    logger = get_logger(__name__, level=settings.log_level)

    logger.info("Starting NeuroAdaptive ETL Orchestration Platform")

    pipeline = SamplePipeline()
    success = pipeline.execute()
    logger.info("Sample pipeline finished with status: %s", pipeline.status)

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()