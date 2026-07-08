"""Shared provider chain orchestrator — generic fallback across any provider architecture."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from app.core.exceptions import ServiceUnavailableException

logger = logging.getLogger(__name__)


@dataclass
class ProviderAttempt:
    provider: str
    model: str
    success: bool
    latency: float
    error: str = ""


@dataclass
class ChainResult:
    success: bool
    result: Any = None
    provider_used: str = ""
    model_used: str = ""
    attempts: List[ProviderAttempt] = field(default_factory=list)
    last_error: str = ""


_NON_RETRYABLE = [
    "authentication failed", "auth failed", "auth error",
    "401", "403",
    "api key is not configured", "api key is not set",
    "client is not initialized",
]

_RETRYABLE = [
    "timeout", "timed out", "connection error", "connection refused",
    "rate limit", "429", "500", "502", "503", "504",
    "service unavailable", "empty response",
    "invalid json", "failed to parse", "unexpected response structure",
    "model not found", "model overloaded", "model is unavailable",
    "missing keys", "validation failed",
]


def is_retryable(error: Any) -> bool:
    error_str = str(error).lower()
    for m in _NON_RETRYABLE:
        if m in error_str:
            return False
    for m in _RETRYABLE:
        if m in error_str:
            return True
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True
    if isinstance(error, ServiceUnavailableException):
        return True
    return False


async def run_chain(
    providers: List[str],
    call_provider: Callable[[str], Any],
) -> ChainResult:
    start = time.monotonic()
    attempts: List[ProviderAttempt] = []
    last_error = ""

    for provider_name in providers:
        attempt_start = time.monotonic()
        try:
            result = await call_provider(provider_name)
            elapsed = time.monotonic() - attempt_start
            model = ""
            if isinstance(result, tuple) and len(result) == 2:
                result, model = result
            attempts.append(ProviderAttempt(
                provider=provider_name, model=model, success=True, latency=elapsed,
            ))
            logger.info("Chain succeeded on %s (%.2fs)", provider_name, elapsed)
            return ChainResult(
                success=True, result=result, provider_used=provider_name,
                model_used=model, attempts=attempts,
            )
        except Exception as e:
            elapsed = time.monotonic() - attempt_start
            error_msg = str(e).strip() or type(e).__name__
            last_error = f"{provider_name}: {error_msg}"
            if not is_retryable(e):
                logger.warning("Non-retryable from %s: %s", provider_name, error_msg)
                attempts.append(ProviderAttempt(
                    provider=provider_name, model="", success=False,
                    latency=elapsed, error=error_msg,
                ))
                return ChainResult(
                    success=False, attempts=attempts, last_error=last_error,
                )
            logger.warning("Retryable from %s, next: %s", provider_name, error_msg)
            attempts.append(ProviderAttempt(
                provider=provider_name, model="", success=False,
                latency=elapsed, error=error_msg,
            ))

    return ChainResult(
        success=False, attempts=attempts,
        last_error=last_error or "All providers exhausted",
    )
