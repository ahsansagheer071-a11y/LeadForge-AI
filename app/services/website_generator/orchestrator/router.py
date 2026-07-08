import asyncio
import logging
import time
from typing import Dict, List, Optional

from app.services.website_generator.orchestrator.circuit_breaker import CircuitBreaker
from app.services.website_generator.orchestrator.schemas import ProviderAttempt, ProviderHealth, RouterResult
from app.services.website_generator.providers.provider_factory import ProviderFactory
from app.services.website_generator.schemas import PromptContext

logger = logging.getLogger(__name__)

HEALTH_CHECK_INTERVAL = 30.0
HEALTH_CHECK_CONCURRENCY = 3
BACKOFF_BASE = 1.0
BACKOFF_MAX = 16.0


class AIProviderRouter:
    def __init__(self, circuit_breaker: Optional[CircuitBreaker] = None):
        self._circuit_breaker = circuit_breaker or CircuitBreaker()
        self._health_cache: Dict[str, ProviderHealth] = {}
        self._health_lock = asyncio.Lock()

    async def route(
        self,
        prompt: PromptContext,
        preferred_provider: Optional[str] = None,
        fallback_chain: Optional[List[str]] = None,
        max_attempts_per_provider: int = 2,
    ) -> RouterResult:
        start = time.monotonic()
        chain = fallback_chain or ProviderFactory.get_fallback_chain(preferred_provider)
        all_errors: List[str] = []
        attempts: List[ProviderAttempt] = []
        last_error: str = ""

        for provider_name in chain:
            if not self._circuit_breaker.allow_request(provider_name):
                msg = f"Circuit breaker open for provider: {provider_name}"
                logger.warning(msg)
                all_errors.append(msg)
                attempts.append(ProviderAttempt(
                    provider=provider_name, model="", success=False,
                    latency=0.0, errors=[msg], attempted_at=time.monotonic(),
                ))
                continue

            for attempt_num in range(max_attempts_per_provider):
                if attempt_num > 0:
                    backoff = min(BACKOFF_BASE * (2 ** (attempt_num - 1)), BACKOFF_MAX)
                    logger.info("Backoff %.1fs before retry %d for provider: %s", backoff, attempt_num + 1, provider_name)
                    await asyncio.sleep(backoff)

                attempt_start = time.monotonic()
                try:
                    provider = ProviderFactory.get_provider(provider_name)
                    ai_resp = await provider.generate(prompt)
                    elapsed = time.monotonic() - attempt_start

                    attempt = ProviderAttempt(
                        provider=provider_name,
                        model=ai_resp.model or provider_name,
                        success=ai_resp.success,
                        latency=elapsed,
                        errors=list(ai_resp.errors),
                        attempted_at=attempt_start,
                    )
                    attempts.append(attempt)

                    if ai_resp.success:
                        self._circuit_breaker.record_success(provider_name)
                        return RouterResult(
                            success=True,
                            provider_used=provider_name,
                            model_used=ai_resp.model or provider_name,
                            raw_response=ai_resp.raw_response,
                            attempts=attempts,
                            total_latency=time.monotonic() - start,
                            warnings=list(ai_resp.warnings),
                        )

                    self._circuit_breaker.record_failure(provider_name)
                    last_error = "; ".join(ai_resp.errors) if ai_resp.errors else f"Provider {provider_name} returned failure"
                    all_errors.append(f"{provider_name} attempt {attempt_num + 1}: {last_error}")

                except Exception as exc:
                    elapsed = time.monotonic() - attempt_start
                    self._circuit_breaker.record_failure(provider_name)
                    err_msg = f"{type(exc).__name__}: {exc}"
                    attempts.append(ProviderAttempt(
                        provider=provider_name, model=provider_name, success=False,
                        latency=elapsed, errors=[err_msg], attempted_at=attempt_start,
                    ))
                    last_error = err_msg
                    all_errors.append(f"{provider_name} attempt {attempt_num + 1}: {err_msg}")

        return RouterResult(
            success=False,
            provider_used="",
            model_used="",
            raw_response="",
            attempts=attempts,
            total_latency=time.monotonic() - start,
            errors=all_errors,
        )

    async def check_provider_health(self, provider_name: str) -> ProviderHealth:
        async with self._health_lock:
            cached = self._health_cache.get(provider_name)
            now = time.monotonic()
            if cached and (now - cached.last_checked) < HEALTH_CHECK_INTERVAL:
                return cached

            check_start = time.monotonic()
            try:
                provider = ProviderFactory.get_provider(provider_name)
                healthy = await provider.health_check()
            except Exception:
                healthy = False

            elapsed = time.monotonic() - check_start
            health = ProviderHealth(
                provider=provider_name,
                healthy=healthy,
                latency=elapsed,
                last_checked=now,
                consecutive_failures=0 if healthy else (cached.consecutive_failures + 1 if cached else 1),
            )
            self._health_cache[provider_name] = health
            return health

    async def get_provider_health_status(self) -> Dict[str, ProviderHealth]:
        chain = ProviderFactory.get_fallback_chain()
        sem = asyncio.Semaphore(HEALTH_CHECK_CONCURRENCY)

        async def _check(name: str) -> ProviderHealth:
            async with sem:
                return await self.check_provider_health(name)

        results = await asyncio.gather(*[_check(n) for n in chain], return_exceptions=True)
        status = {}
        for name, result in zip(chain, results):
            if isinstance(result, Exception):
                status[name] = ProviderHealth(
                    provider=name, healthy=False, latency=0.0,
                    last_checked=time.monotonic(), consecutive_failures=0,
                )
            else:
                status[name] = result
        return status

    def get_circuit_states(self) -> dict:
        return {
            name: state.model_dump()
            for name, state in self._circuit_breaker.get_all_states().items()
        }
