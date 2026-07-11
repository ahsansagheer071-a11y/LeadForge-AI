import logging
import time
from typing import List, Optional

import httpx

from app.core.config import settings
from app.services.website_generator.providers.base import AIProvider
from app.services.website_generator.providers.schemas import AIResponse, AIUsage
from app.services.website_generator.schemas import PromptContext

logger = logging.getLogger(__name__)

NVIDIA_CHAT_ENDPOINT = "/chat/completions"
GENERATION_TIMEOUT = 120.0
HEALTH_CHECK_TIMEOUT = 10.0
SUPPORTED_MODELS = [
    "meta/llama-3.1-8b-instruct",
    "meta/llama-3.1-70b-instruct",
    "meta/llama-3.1-405b-instruct",
    "mistralai/mistral-7b-instruct-v0.3",
    "mistralai/mixtral-8x22b-instruct-v0.1",
]


class NvidiaProvider(AIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        key = api_key or settings.NVIDIA_API_KEY
        self._api_key = key.strip("\"' \t\n\r") if key else None
        self._model = model or settings.NVIDIA_GENERATION_MODEL
        self._base_url = (base_url or settings.NVIDIA_BASE_URL).rstrip("/")

    def provider_name(self) -> str:
        return "nvidia"

    def supported_models(self) -> List[str]:
        return list(SUPPORTED_MODELS)

    async def health_check(self) -> bool:
        if not self._api_key:
            return False
        endpoint = f"{self._base_url}{NVIDIA_CHAT_ENDPOINT}"
        headers = self._headers()
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                return resp.status_code == 200
        except Exception:
            return False

    async def generate(self, prompt_context: PromptContext) -> AIResponse:
        start = time.monotonic()
        logger.info("NVIDIA generation started | model=%s", self._model)

        if not self._api_key:
            return AIResponse(
                success=False, provider="nvidia", model=self._model,
                errors=["NVIDIA_API_KEY is not configured"], latency=time.monotonic() - start,
            )

        messages = self._build_messages(prompt_context)
        endpoint = f"{self._base_url}{NVIDIA_CHAT_ENDPOINT}"
        headers = self._headers()
        payload = {
            "model": self._model,
            "messages": messages,
            "max_tokens": 16384,
        }

        try:
            async with httpx.AsyncClient(timeout=GENERATION_TIMEOUT) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
        except httpx.TimeoutException:
            return AIResponse(
                success=False, provider="nvidia", model=self._model,
                errors=["Request timed out"], latency=time.monotonic() - start,
            )
        except httpx.ConnectError:
            return AIResponse(
                success=False, provider="nvidia", model=self._model,
                errors=["Connection error — provider unreachable"], latency=time.monotonic() - start,
            )
        except Exception as exc:
            return AIResponse(
                success=False, provider="nvidia", model=self._model,
                errors=[f"Unexpected error: {type(exc).__name__}"], latency=time.monotonic() - start,
            )

        if resp.status_code in (401, 403):
            return AIResponse(
                success=False, provider="nvidia", model=self._model,
                errors=["Authentication failed — check API key"], latency=time.monotonic() - start,
            )
        if resp.status_code == 429:
            return AIResponse(
                success=False, provider="nvidia", model=self._model,
                errors=["Rate limit exceeded"], latency=time.monotonic() - start,
            )
        if resp.status_code != 200:
            body = resp.text[:500]
            logger.warning("NVIDIA HTTP %d: %s", resp.status_code, body)
            return AIResponse(
                success=False, provider="nvidia", model=self._model,
                errors=[f"Provider returned HTTP {resp.status_code}"], latency=time.monotonic() - start,
            )

        try:
            data = resp.json()
        except Exception:
            return AIResponse(
                success=False, provider="nvidia", model=self._model,
                errors=["Invalid JSON"], latency=time.monotonic() - start,
            )

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return AIResponse(
                success=False, provider="nvidia", model=self._model,
                errors=["Unexpected response structure"], latency=time.monotonic() - start,
            )

        usage_data = data.get("usage")
        usage: Optional[AIUsage] = None
        if usage_data:
            usage = AIUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

        latency = time.monotonic() - start
        logger.info("NVIDIA generation finished | model=%s | latency=%.2fs", self._model, latency)

        return AIResponse(
            success=True, provider="nvidia", model=self._model,
            raw_response=content, usage=usage, latency=latency,
        )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _build_messages(prompt_context: PromptContext) -> List[dict]:
        messages = [{"role": "system", "content": prompt_context.system_context}]
        body_parts = [
            ("Developer Guide", prompt_context.developer_context),
            ("Brand Identity", prompt_context.branding_context),
            ("Layout Structure", prompt_context.layout_context),
            ("Component Library", prompt_context.components_context),
            ("Animation System", prompt_context.animation_context),
            ("SEO Configuration", prompt_context.seo_context),
            ("Performance Targets", prompt_context.performance_context),
            ("Accessibility Requirements", prompt_context.accessibility_context),
            ("Asset Management", prompt_context.assets_context),
        ]
        combined_parts = []
        for title, content in body_parts:
            if content:
                combined_parts.append(f"## {title}\n\n{content}")
        combined_parts.append(f"## Generation Constraints\n\n{prompt_context.generation_constraints}")
        user_content = "\n\n---\n\n".join(combined_parts)
        messages.append({"role": "user", "content": user_content})
        return messages
