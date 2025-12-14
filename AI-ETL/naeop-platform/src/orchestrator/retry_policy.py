"""Retry policies with configurable backoff strategies."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass


class RetryPolicy(ABC):
    """Abstract retry policy determining delay between attempts."""

    @abstractmethod
    def delay(self, attempt: int) -> float:
        """Return delay in seconds before attempt number `attempt` (1-indexed)."""
        raise NotImplementedError


@dataclass
class FixedRetryPolicy(RetryPolicy):
    """Fixed delay between retries."""

    delay_seconds: float = 1.0

    def delay(self, attempt: int) -> float:
        return self.delay_seconds


@dataclass
class ExponentialBackoffPolicy(RetryPolicy):
    """Exponential backoff with optional jitter and cap."""

    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    jitter: float = 0.25  # ±25% randomness

    def delay(self, attempt: int) -> float:
        raw = self.base_delay_seconds * (2 ** (attempt - 1))
        capped = min(raw, self.max_delay_seconds)
        if self.jitter > 0:
            jitter_range = capped * self.jitter
            capped += random.uniform(-jitter_range, jitter_range)
        return max(0.0, capped)


def retry_policy_from_settings(
    strategy: str,
    base_delay: float,
    max_delay: float,
    jitter: float,
    fixed_delay: float,
) -> RetryPolicy:
    """Factory to build a retry policy from settings values."""
    if strategy == "exponential":
        return ExponentialBackoffPolicy(
            base_delay_seconds=base_delay,
            max_delay_seconds=max_delay,
            jitter=jitter,
        )
    return FixedRetryPolicy(delay_seconds=fixed_delay)
