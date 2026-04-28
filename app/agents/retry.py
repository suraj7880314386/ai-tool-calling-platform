"""Retry logic with exponential backoff for agent execution."""

import time
import logging
from typing import Callable, Any, Optional
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)

from app.config import settings

logger = logging.getLogger(__name__)


# ─── Retryable Exceptions ─────────────────────────────────

class RetryableError(Exception):
    """Exception that should trigger a retry."""
    pass


class RateLimitError(RetryableError):
    """LLM rate limit hit."""
    pass


class TimeoutError(RetryableError):
    """Operation timed out."""
    pass


class ToolExecutionError(Exception):
    """Non-retryable tool error."""
    pass


# ─── Retry Decorator ──────────────────────────────────────

def with_retry(
    max_retries: Optional[int] = None,
    backoff_base: Optional[int] = None,
):
    """
    Decorator that adds retry logic with exponential backoff.

    Args:
        max_retries: Override max retries (default from settings)
        backoff_base: Override backoff base (default from settings)
    """
    _max = max_retries or settings.max_retries
    _base = backoff_base or settings.retry_backoff_base

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries_used = 0
            last_error = None

            for attempt in range(_max + 1):
                try:
                    result = func(*args, **kwargs)
                    if retries_used > 0:
                        logger.info(
                            f"[Retry] {func.__name__} succeeded after {retries_used} retries"
                        )
                    result["retries_used"] = retries_used
                    return result

                except (RateLimitError, TimeoutError) as e:
                    retries_used += 1
                    last_error = e

                    if attempt < _max:
                        wait_time = _base ** attempt
                        logger.warning(
                            f"[Retry] {func.__name__} failed (attempt {attempt + 1}/{_max + 1}): "
                            f"{str(e)}. Waiting {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"[Retry] {func.__name__} exhausted all {_max} retries"
                        )

                except Exception as e:
                    # Non-retryable error
                    logger.error(f"[Retry] {func.__name__} non-retryable error: {e}")
                    raise

            # All retries exhausted
            raise last_error or Exception("All retries exhausted")

        return wrapper
    return decorator


# ─── Utility Functions ─────────────────────────────────────

def classify_error(error: Exception) -> str:
    """Classify an error to determine if it's retryable."""
    error_str = str(error).lower()

    if "rate limit" in error_str or "429" in error_str:
        return "rate_limit"
    elif "timeout" in error_str or "timed out" in error_str:
        return "timeout"
    elif "connection" in error_str:
        return "connection"
    elif "authentication" in error_str or "401" in error_str:
        return "auth"
    else:
        return "unknown"


def should_retry(error: Exception) -> bool:
    """Determine if an error should trigger a retry."""
    error_type = classify_error(error)
    return error_type in {"rate_limit", "timeout", "connection"}
