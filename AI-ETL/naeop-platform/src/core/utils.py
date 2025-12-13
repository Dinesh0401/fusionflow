"""Utility helpers used across the platform."""

import time
from functools import wraps
from typing import Any, Callable, Dict, Iterable, Tuple

from src.core.logger import get_logger

logger = get_logger(__name__)


def validate_dict_payload(data: Any, required_keys: Iterable[str] = ()) -> Dict[str, Any]:
    """Validate that a payload is a dictionary and contains required keys."""

    if not isinstance(data, dict):
        raise ValueError("Payload must be a dictionary.")
    missing = [key for key in required_keys if key not in data]
    if missing:
        raise ValueError(f"Missing required keys: {missing}")
    return data


def format_dict_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize dictionary keys by stripping whitespace and lowering case."""

    return {str(key).strip().lower(): value for key, value in data.items()}


def log_execution_time(start_time: float, end_time: float) -> str:
    """Return a human-readable execution time string."""

    execution_time = end_time - start_time
    return f"Execution time: {execution_time:.3f} seconds"


def handle_exceptions(func: Callable) -> Callable:
    """Decorator to log and re-raise exceptions in ETL tasks."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Task '%s' failed: %s", func.__name__, exc)
            raise

    return wrapper


def timed(func: Callable) -> Callable:
    """Decorator to measure execution time and attach it to the result tuple."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[Any, float]:
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        return result, duration

    return wrapper