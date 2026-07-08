"""Smoke test: verify chain.py works on the deployed Python version."""
import asyncio
import sys
print("Python version:", sys.version)

# Check asyncio.TimeoutError
import asyncio
try:
    x = asyncio.TimeoutError
    print("asyncio.TimeoutError EXISTS")
except AttributeError:
    print("asyncio.TimeoutError REMOVED in 3.14")

from app.core.exceptions import ServiceUnavailableException
from app.services.ai.chain import run_chain, is_retryable

async def main():
    # verify classification works
    assert is_retryable(TimeoutError()), "TimeoutError should be retryable"
    assert is_retryable(ServiceUnavailableException("rate limit")), "rate limit should be retryable"
    assert not is_retryable(ServiceUnavailableException("Authentication failed")), "auth should NOT be retryable"
    assert not is_retryable("API key is not configured"), "API key missing should NOT be retryable"
    assert not is_retryable(ValueError("bad input")), "ValueError should NOT be retryable"
    print("Classification: OK")

    # verify chain stops on non-retryable
    called = []
    async def call_auth(name):
        called.append(name)
        raise ServiceUnavailableException("Authentication failed")

    result = await run_chain(["groq", "pollinations"], call_auth)
    assert result.success is False, "should fail on auth"
    assert len(called) == 1, "should only call groq, not pollinations"
    print("Non-retryable stops chain: OK")

    # verify chain falls back on retryable
    called2 = []
    async def call_retry(name):
        called2.append(name)
        if name == "groq":
            raise ServiceUnavailableException("rate limit exceeded")
        return "success_result"

    result = await run_chain(["groq", "pollinations"], call_retry)
    assert result.success is True, "should succeed on pollinations"
    assert result.provider_used == "pollinations"
    assert len(called2) == 2, "should call both"
    print("Retryable fallback: OK")

    # verify chain succeeds on first provider
    async def call_ok(name):
        return "ok"

    result = await run_chain(["groq", "pollinations"], call_ok)
    assert result.success is True
    assert result.provider_used == "groq"
    assert len(result.attempts) == 1
    print("First provider success: OK")

    print("\nAll smoke tests passed!")

asyncio.run(main())
