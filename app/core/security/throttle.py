"""Brute-force throttling: tracks failed unlock attempts and enforces an
exponentially increasing delay before further attempts are allowed."""
from __future__ import annotations

import time
from dataclasses import dataclass

MAX_DELAY_SECONDS = 300  # cap the delay at 5 minutes
BASE_DELAY_SECONDS = 1


@dataclass
class ThrottleState:
    """Persisted brute-force throttling state."""

    failed_attempts: int = 0
    locked_until_timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "failed_attempts": self.failed_attempts,
            "locked_until_timestamp": self.locked_until_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ThrottleState":
        return cls(
            failed_attempts=data.get("failed_attempts", 0),
            locked_until_timestamp=data.get("locked_until_timestamp", 0.0),
        )


def seconds_until_unlocked(state: ThrottleState) -> float:
    """Return how many seconds remain before another attempt is allowed.

    Returns 0.0 if attempts are currently allowed.
    """
    remaining = state.locked_until_timestamp - time.time()
    return max(0.0, remaining)


def record_failed_attempt(state: ThrottleState) -> ThrottleState:
    """Return updated throttle state after a failed unlock attempt.

    The delay doubles with each consecutive failure, up to a maximum.
    """
    failed_attempts = state.failed_attempts + 1
    delay = min(BASE_DELAY_SECONDS * (2 ** (failed_attempts - 1)), MAX_DELAY_SECONDS)
    locked_until = time.time() + delay
    return ThrottleState(
        failed_attempts=failed_attempts, locked_until_timestamp=locked_until
    )


def record_successful_attempt() -> ThrottleState:
    """Return reset throttle state after a successful unlock."""
    return ThrottleState(failed_attempts=0, locked_until_timestamp=0.0)