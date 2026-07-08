import logging
import time
from typing import Dict, Optional

from app.services.website_generator.orchestrator.schemas import CircuitState

logger = logging.getLogger(__name__)

FAILURE_THRESHOLD = 3
HALF_OPEN_MAX_ATTEMPTS = 1
RESET_TIMEOUT = 60.0


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = FAILURE_THRESHOLD,
        reset_timeout: float = RESET_TIMEOUT,
        half_open_max_attempts: int = HALF_OPEN_MAX_ATTEMPTS,
    ):
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._half_open_max_attempts = half_open_max_attempts
        self._states: Dict[str, CircuitState] = {}

    def _ensure(self, provider: str) -> CircuitState:
        if provider not in self._states:
            self._states[provider] = CircuitState(provider=provider)
        return self._states[provider]

    def allow_request(self, provider: str) -> bool:
        state = self._ensure(provider)
        if state.state == "closed":
            return True
        if state.state == "open":
            if state.opened_at and (time.monotonic() - state.opened_at) >= self._reset_timeout:
                logger.info("Circuit breaker half-opening for provider: %s", provider)
                state.state = "half-open"
                state.half_open_attempts = 0
                return True
            logger.warning("Circuit breaker OPEN for provider: %s (opened %.1fs ago)", provider, time.monotonic() - (state.opened_at or 0))
            return False
        if state.state == "half-open":
            if state.half_open_attempts >= self._half_open_max_attempts:
                logger.warning("Circuit breaker half-open max attempts reached for: %s", provider)
                return False
            state.half_open_attempts += 1
            return True
        return True

    def record_success(self, provider: str) -> None:
        state = self._ensure(provider)
        if state.state != "closed":
            logger.info("Circuit breaker closing for provider: %s", provider)
        state.state = "closed"
        state.failure_count = 0
        state.half_open_attempts = 0
        state.opened_at = None
        state.last_failure_at = None

    def record_failure(self, provider: str) -> None:
        state = self._ensure(provider)
        state.failure_count += 1
        state.last_failure_at = time.monotonic()
        if state.state == "half-open":
            logger.warning("Circuit breaker re-opening for provider: %s (half-open failure)", provider)
            state.state = "open"
            state.opened_at = time.monotonic()
        elif state.failure_count >= self._failure_threshold:
            logger.warning(
                "Circuit breaker OPENING for provider: %s (%d consecutive failures)",
                provider, state.failure_count,
            )
            state.state = "open"
            state.opened_at = time.monotonic()

    def get_state(self, provider: str) -> CircuitState:
        return self._ensure(provider)

    def get_all_states(self) -> Dict[str, CircuitState]:
        return dict(self._states)
