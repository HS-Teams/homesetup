"""Opt-in performance timing helpers for the HomeSetup Streamlit UI."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from typing import TypeVar

PERFORMANCE_LOG_ENV_KEY = "HHS_UI_PERFORMANCE_LOG"
TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
R = TypeVar("R")


def performance_logging_enabled() -> bool:
    """Return whether opt-in UI performance logging is enabled."""
    return os.environ.get(PERFORMANCE_LOG_ENV_KEY, "").strip().lower() in TRUE_VALUES


@contextmanager
def measure_ui_phase(phase: str, **context: object) -> Iterator[None]:
    """Log the elapsed time for one UI phase when diagnostics are enabled."""
    if not performance_logging_enabled():
        yield
        return
    started_at = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - started_at) * 1000
        details = " ".join(
            f"{key}={value!s}" for key, value in sorted(context.items()) if value != ""
        )
        logger = logging.getLogger("hhs_ui.performance")
        logger.setLevel(logging.INFO)
        logger.info(
            "ui_performance phase=%s duration_ms=%.2f%s",
            phase,
            duration_ms,
            f" {details}" if details else "",
        )


def timed_ui_phase(
    phase: str,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Decorate a callable with the opt-in UI phase timer."""

    def decorator(function: Callable[..., R]) -> Callable[..., R]:
        @wraps(function)
        def measured(*args: object, **kwargs: object) -> R:
            with measure_ui_phase(phase):
                return function(*args, **kwargs)

        return measured

    return decorator
