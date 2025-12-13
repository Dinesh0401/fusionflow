"""Logging utilities for the NeuroAdaptive ETL Orchestration Platform."""

import logging
import sys
from typing import Optional


def _build_handler() -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    return handler


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Return a configured logger with a stable console handler.

    The function is idempotent: it will not attach duplicate handlers when called
    multiple times for the same logger name.
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(_build_handler())
    logger.propagate = False
    return logger


def configure_root_logger(level: str = "INFO") -> None:
    """Configure the root logger once for the entire application."""

    root = logging.getLogger()
    root.setLevel(level)
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(_build_handler())