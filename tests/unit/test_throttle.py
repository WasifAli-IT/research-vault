"""Tests for brute-force throttling logic."""
from core.security.throttle import (
    ThrottleState,
    record_failed_attempt,
    record_successful_attempt,
    seconds_until_unlocked,
)


def test_fresh_state_allows_attempts_immediately():
    state = ThrottleState()
    assert seconds_until_unlocked(state) == 0.0


def test_failed_attempt_introduces_delay():
    state = ThrottleState()
    state = record_failed_attempt(state)

    assert state.failed_attempts == 1
    assert seconds_until_unlocked(state) > 0.0


def test_delay_increases_with_repeated_failures():
    state = ThrottleState()
    state = record_failed_attempt(state)
    first_delay = seconds_until_unlocked(state)

    state = record_failed_attempt(state)
    second_delay = seconds_until_unlocked(state)

    assert second_delay > first_delay


def test_successful_attempt_resets_state():
    state = ThrottleState()
    state = record_failed_attempt(state)
    state = record_failed_attempt(state)

    state = record_successful_attempt()

    assert state.failed_attempts == 0
    assert seconds_until_unlocked(state) == 0.0