import logging
import time
from typing import List, Optional

import httpx

from app.core.config import settings
from app.services.website_generator.providers.base import AIProvider
from app.services.website_generator.providers.schemas import AIResponse, AIUsage
from app.services.website_generator.schemas import PromptContext

logger = logging.getLogger(__name__)

POLLINATIONS_CHAT_ENDPOINT = "/openai/chat/completions"
MODEL_QUERY_URL = "https://text.pollinations.ai/models"
GENERATION_TIMEOUT = 120.0
HEALTH_CHECK_TIMEOUT = 10.0


class PollinationsProvider(AIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        # Pollinations legacy API is open — no auth required.
        self._api_key = None
        self._base_url = (base_url or settings.POLLINATIONS_BASE_URL).rstrip("/")
        self._model = model or settings.POLLINATIONS_GENERATION_MODEL
        self._models_cached = False

    async def _ensure_model(self) -> str:
        if self._model:
            return self._model
        if self._models_cached:
            return self._model or "openai"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(MODEL_QUERY_URL)
                if resp.status_code == 200:
                    models = resp.json()
                    if isinstance(models, list) and models:
                        if isinstance(models[0], dict):
                            name = models[0].get("aliases", [models[0].get("name", "")])[0]
                            self._model = name
                        elif isinstance(models[0], str):
                            candidates = [m for m in models if "instruct" in m.lower()]
                            self._model = (candidates or models)[0]
        except Exception as e:
            logger.warning("Pollinations model discovery failed: %s", e)
        self._models_cached = True
        return self._model or "openai"

    def provider_name(self) -> str:
        return "pollinations"

    def supported_models(self) -> List[str]:
        return ["openai", "openai-fast", "gpt-oss"]

    async def health_check(self) -> bool:
        endpoint = f"{self._base_url}{POLLINATIONS_CHAT_ENDPOINT}"
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {
            "model": await self._ensure_model(),
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
        logger.info("Pollinations generation started")
        model = await self._ensure_model()

        if not self._api_key:
            logger.info("Pollinations: no API key — using open mode")

        messages = self._build_messages(prompt_context)
        endpoint = f"{self._base_url}{POLLINATIONS_CHAT_ENDPOINT}"
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 4096,
        }

        try:
            async with httpx.AsyncClient(timeout=GENERATION_TIMEOUT) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
        except httpx.TimeoutException:
            return AIResponse(
                success=False, provider="pollinations", model=model,
                errors=["Request timed out"], latency=time.monotonic() - start,
            )
        except httpx.ConnectError:
            return AIResponse(
                success=False, provider="pollinations", model=model,
                errors=["Connection error — provider unreachable"], latency=time.monotonic() - start,
            )
        except Exception as exc:
            return AIResponse(
                success=False, provider="pollinations", model=model,
                errors=[f"Unexpected error: {type(exc).__name__}"], latency=time.monotonic() - start,
            )

        if resp.status_code in (401, 403):
            return AIResponse(
                success=False, provider="pollinations", model=model,
                errors=["Authentication failed"], latency=time.monotonic() - start,
            )
        if resp.status_code == 429:
            return AIResponse(
                success=False, provider="pollinations", model=model,
                errors=["Rate limit exceeded"], latency=time.monotonic() - start,
            )
        if resp.status_code != 200:
            body = resp.text[:500]
            logger.warning("Pollinations HTTP %d: %s", resp.status_code, body)
            return AIResponse(
                success=False, provider="pollinations", model=model,
                errors=[f"Provider returned HTTP {resp.status_code}"], latency=time.monotonic() - start,
            )

        try:
            data = resp.json()
        except Exception:
            return AIResponse(
                success=False, provider="pollinations", model=model,
                errors=["Invalid JSON"], latency=time.monotonic() - start,
            )

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            logger.warning("Pollinations unexpected response: %s", str(data)[:500])
            return AIResponse(
                success=False, provider="pollinations", model=model,
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

        finish_reason = data.get("choices", [{}])[0].get("finish_reason", "unknown")
        latency = time.monotonic() - start
        logger.info("Pollinations generation finished | model=%s | latency=%.2fs | finish_reason=%s | content_len=%d",
            model, latency, finish_reason, len(content) if content else 0)

        return AIResponse(
            success=True, provider="pollinations", model=model,
            raw_response=content, usage=usage, latency=latency,
        )

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    @staticmethod
    def _build_messages(prompt_context: PromptContext) -> List[dict]:
        messages = [{"role": "system", "content": prompt_context.system_context}]
        body_parts = [
            ("Developer Guide", prompt_context.developer_context),
            ("Brand Identity", prompt_context.branding_context),
            ("Source Website Content", prompt_context.content_context),
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
