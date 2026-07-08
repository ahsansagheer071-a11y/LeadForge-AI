"""Focused tests for the shared provider chain orchestrator."""

import pytest
from app.services.ai.chain import (
    run_chain, is_retryable, ChainResult, ProviderAttempt,
)
from app.core.exceptions import ServiceUnavailableException


# ── is_retryable ──────────────────────────────────────────────────────────

class TestIsRetryable:
    def test_retryable_timeout(self):
        assert is_retryable(TimeoutError()) is True
        assert is_retryable("request timed out") is True

    def test_retryable_connection(self):
        assert is_retryable(ConnectionError()) is True
        assert is_retryable("connection error") is True
        assert is_retryable("connection refused") is True

    def test_retryable_rate_limit(self):
        assert is_retryable("rate limit exceeded") is True
        assert is_retryable(ServiceUnavailableException("429 Too Many Requests")) is True

    def test_retryable_5xx(self):
        assert is_retryable("500 Internal Server Error") is True
        assert is_retryable("503 Service Unavailable") is True

    def test_retryable_unavailable_model(self):
        assert is_retryable("model not found") is True
        assert is_retryable("model is unavailable") is True

    def test_retryable_invalid_json(self):
        assert is_retryable("invalid JSON from API") is True
        assert is_retryable("failed to parse JSON") is True
        assert is_retryable("unexpected response structure") is True

    def test_retryable_missing_keys(self):
        assert is_retryable("response missing keys: Business Summary") is True

    def test_retryable_service_unavailable(self):
        assert is_retryable(ServiceUnavailableException("something broke")) is True

    def test_non_retryable_auth(self):
        assert is_retryable(ServiceUnavailableException("Authentication failed")) is False
        assert is_retryable("NVIDIA authentication failed") is False
        assert is_retryable("HTTP 401") is False

    def test_non_retryable_api_key(self):
        assert is_retryable("GROQ_API_KEY is not configured") is False
        assert is_retryable("API key is not set") is False

    def test_non_retryable_generic_exception(self):
        assert is_retryable(ValueError("invalid input")) is False
        assert is_retryable(RuntimeError("unexpected crash")) is False
        assert is_retryable("some random error") is False


# ── run_chain ─────────────────────────────────────────────────────────────

class TestRunChain:
    async def test_first_provider_succeeds(self):
        async def call(name):
            return f"result_from_{name}", f"model_{name}"

        result = await run_chain(["groq", "pollinations", "nvidia"], call)
        assert result.success is True
        assert result.provider_used == "groq"
        assert result.result == "result_from_groq"
        assert len(result.attempts) == 1
        assert result.attempts[0].success is True

    async def test_fallback_on_retryable(self):
        call_count = []

        async def call(name):
            call_count.append(name)
            if name == "groq":
                raise ServiceUnavailableException("rate limit exceeded")
            return f"result_from_{name}", f"model_{name}"

        result = await run_chain(["groq", "pollinations"], call)
        assert result.success is True
        assert result.provider_used == "pollinations"
        assert result.result == "result_from_pollinations"
        assert len(result.attempts) == 2
        assert result.attempts[0].success is False
        assert result.attempts[1].success is True

    async def test_non_retryable_stops_chain(self):
        call_count = []

        async def call(name):
            call_count.append(name)
            if name == "groq":
                raise ServiceUnavailableException("Authentication failed")
            return "ok"

        result = await run_chain(["groq", "pollinations", "nvidia"], call)
        assert result.success is False
        assert result.provider_used == ""
        assert len(result.attempts) == 1
        assert "Authentication failed" in result.last_error
        assert len(call_count) == 1  # pollinations/nvidia never called

    async def test_all_providers_exhausted(self):
        async def call(name):
            raise ServiceUnavailableException("rate limit")

        result = await run_chain(["groq", "pollinations", "nvidia"], call)
        assert result.success is False
        assert len(result.attempts) == 3
        for a in result.attempts:
            assert a.success is False

    async def test_first_provider_non_retryable_stops(self):
        async def call(name):
            if name == "groq":
                raise ValueError("bad input")
            return "ok"

        result = await run_chain(["groq", "pollinations"], call)
        assert result.success is False
        assert len(result.attempts) == 1

    async def test_empty_provider_list(self):
        async def call(name):
            return "ok"

        result = await run_chain([], call)
        assert result.success is False
        assert result.last_error == "All providers exhausted"

    async def test_retryable_then_non_retryable(self):
        async def call(name):
            if name == "groq":
                raise ServiceUnavailableException("rate limit")
            if name == "pollinations":
                raise ServiceUnavailableException("Authentication failed")
            return "ok"

        result = await run_chain(["groq", "pollinations", "nvidia"], call)
        assert result.success is False
        assert len(result.attempts) == 2  # stopped at pollinations
