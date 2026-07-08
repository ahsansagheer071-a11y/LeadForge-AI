import json
import asyncio
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ServiceUnavailableException
from app.services.ai.base import AIBaseProvider


MODEL_QUERY_URL = "https://text.pollinations.ai/models"
CHAT_ENDPOINT = "/openai/chat/completions"
AUDIT_TIMEOUT = 120.0
OUTREACH_TIMEOUT = 60.0
POLLINATIONS_DEFAULT_AUDIT_MODEL = "openai"
POLLINATIONS_DEFAULT_GENERATION_MODEL = "openai"


class PollinationsProvider(AIBaseProvider):
    def __init__(self):
        # Pollinations legacy API is open — no auth required.
        self.api_key = None
        self._base_url = settings.POLLINATIONS_BASE_URL.rstrip("/")
        self._audit_model = None
        self._generation_model = None
        self._models_cached = False

    async def _ensure_models_cached(self) -> None:
        if self._models_cached:
            return
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(MODEL_QUERY_URL)
                if resp.status_code == 200:
                    models = resp.json()
                    if isinstance(models, list) and models:
                        fallbacks = [m for m in models if isinstance(m, str) and "instruct" in m.lower()]
                        if fallbacks:
                            self._audit_model = fallbacks[0]
                            self._generation_model = fallbacks[0]
                            logger.info("Pollinations: auto-selected model '%s' from available models", self._audit_model)
                        else:
                            self._audit_model = models[0] if isinstance(models[0], str) else "mistral"
                            self._generation_model = models[0] if isinstance(models[0], str) else "mistral"
                    self._models_cached = True
                    return
        except Exception as e:
            logger.warning("Pollinations model discovery failed: %s", e)

        if not self._audit_model:
            self._audit_model = settings.POLLINATIONS_AUDIT_MODEL or POLLINATIONS_DEFAULT_AUDIT_MODEL
        if not self._generation_model:
            self._generation_model = settings.POLLINATIONS_GENERATION_MODEL or POLLINATIONS_DEFAULT_GENERATION_MODEL
        self._models_cached = True

    @property
    def audit_model(self) -> str:
        return self._audit_model or settings.POLLINATIONS_AUDIT_MODEL or POLLINATIONS_DEFAULT_AUDIT_MODEL

    @property
    def generation_model(self) -> str:
        return self._generation_model or settings.POLLINATIONS_GENERATION_MODEL or POLLINATIONS_DEFAULT_GENERATION_MODEL

    async def audit_website(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        screenshot_urls: Dict[str, Any],
    ) -> Dict[str, Any]:
        await self._ensure_models_cached()
        model = self.audit_model

        prompt = self._build_audit_prompt(lead_info, website_analysis, screenshot_urls)
        result = await self._call_api(prompt, model, AUDIT_TIMEOUT)
        parsed = await self._parse_json_response(result)
        self._validate_result(parsed)
        return self._normalize_audit_result(parsed)

    async def generate_outreach(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        audit_data: Dict[str, Any],
        score_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        await self._ensure_models_cached()
        model = self.generation_model

        prompt = self._build_outreach_prompt(lead_info, website_analysis, audit_data, score_data)
        result = await self._call_api(prompt, model, OUTREACH_TIMEOUT)
        parsed = await self._parse_json_response(result)
        self._validate_outreach_result(parsed)
        return self._normalize_outreach_result(parsed)

    async def _call_api(self, prompt: str, model: str, timeout: float) -> str:
        endpoint = f"{self._base_url}{CHAT_ENDPOINT}"
        headers = {"Content-Type": "application/json"}
        # Pollinations legacy API is open — no auth needed.

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert digital marketing auditor. "
                        "You MUST return valid JSON only. "
                        "DO NOT wrap your response in markdown code blocks. "
                        "DO NOT add any explanatory text before or after the JSON. "
                        "The response must be a valid JSON object with all required fields."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
            "top_p": 0.95,
        }

        for retry in range(2):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(endpoint, json=payload, headers=headers)
            except httpx.TimeoutException:
                logger.warning("Pollinations API timed out (attempt %d/2)", retry + 1)
                if retry < 1:
                    await asyncio.sleep(2.0)
                    continue
                raise ServiceUnavailableException("Pollinations API call timed out")
            except httpx.ConnectError:
                logger.warning("Pollinations connection error (attempt %d/2)", retry + 1)
                if retry < 1:
                    await asyncio.sleep(1.0)
                    continue
                raise ServiceUnavailableException("Pollinations API connection failed")
            except Exception as e:
                logger.error("Pollinations API error: %s", e)
                raise ServiceUnavailableException(f"Pollinations API error: {e}")

            if resp.status_code == 429:
                logger.warning("Pollinations rate limited (attempt %d/2)", retry + 1)
                if retry < 1:
                    await asyncio.sleep(5.0)
                    continue
                raise ServiceUnavailableException("Pollinations rate limit exceeded")
            if resp.status_code in (401, 403):
                raise ServiceUnavailableException("Pollinations authentication failed")
            if resp.status_code != 200:
                body = resp.text[:300]
                logger.warning("Pollinations HTTP %d: %s", resp.status_code, body)
                raise ServiceUnavailableException(f"Pollinations returned HTTP {resp.status_code}")

            try:
                data = resp.json()
            except Exception:
                raise ServiceUnavailableException("Invalid JSON from Pollinations API")

            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                raise ServiceUnavailableException("Unexpected response structure from Pollinations")

            if not content or not content.strip():
                raise ServiceUnavailableException("Empty response from Pollinations API")

            return content

        raise ServiceUnavailableException("Pollinations API failed after retries")

    def _build_audit_prompt(self, lead_info: Dict[str, Any], website_analysis: Dict[str, Any], screenshot_urls: Dict[str, Any]) -> str:
        return f"""
Analyze the following business details and website data to generate a detailed audit.

### Lead Information:
- Business Name: {lead_info.get("name", "Not provided")}
- Industry: {lead_info.get("industry", "Not provided")}
- Location: {lead_info.get("city", "Not provided")}, {lead_info.get("country", "Not provided")}
- Google Maps Rating: {lead_info.get("rating", "Not provided")} ({lead_info.get("reviews_count", 0)} reviews)

### Scraped Website Analysis:
{json.dumps(website_analysis, indent=2, default=str)}

### Visual Screenshots:
- Desktop Screenshot: {screenshot_urls.get("desktop_url", "Not provided")}
- Mobile Screenshot: {screenshot_urls.get("mobile_url", "Not provided")}

Generate a structured JSON response with:
- Business Summary (string)
- Website Quality Score (int 1-100)
- Visual Design Score (int 1-100)
- SEO Score (int 1-100)
- Trust Score (int 1-100)
- Mobile Experience Score (int 1-100)
- Performance Score (int 1-100)
- Content Quality Score (int 1-100)
- CTA Score (int 1-100)
- Top Strengths (array of strings, 3-5 items)
- Top Weaknesses (array of strings, 3-5 items)
- Actionable Recommendations (array of strings, 3-5 items)
- Priority Improvements (array of strings, 3-5 items)
- Overall Summary (string)
"""

    def _build_outreach_prompt(self, lead_info: Dict[str, Any], website_analysis: Dict[str, Any], audit_data: Dict[str, Any], score_data: Dict[str, Any]) -> str:
        return f"""
Generate personalized outreach messages for this lead.

### Lead Information:
{json.dumps(lead_info, indent=2, default=str)}

### Website Audit Results:
{json.dumps(audit_data, indent=2, default=str)}

### Lead Score Data:
{json.dumps(score_data, indent=2, default=str)}

### Required Output Format:
{{
    "Email Subject": "string",
    "Personalized Cold Email": "string",
    "LinkedIn Message": "string",
    "Follow-up Email": "string",
    "Short Call-To-Action": "string"
}}

Return ONLY valid JSON matching this format.
"""

    async def _parse_json_response(self, content: str) -> Dict[str, Any]:
        if not content:
            raise ServiceUnavailableException("Empty content from Pollinations")

        cleaned = content.strip()
        fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(fence_pattern, cleaned)
        if matches:
            cleaned = matches[0].strip()

        if not cleaned.startswith("{") and not cleaned.startswith("["):
            json_pattern = r"(\{[\s\S]*\}|\[[\s\S]*\])"
            json_matches = re.findall(json_pattern, cleaned)
            if json_matches:
                cleaned = json_matches[0].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            cleaned = re.sub(r',\s*}', '}', re.sub(r',\s*]', ']', cleaned))
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                raise ServiceUnavailableException("Failed to parse JSON from Pollinations response")

    def _validate_result(self, result: Dict[str, Any]) -> None:
        required = [
            "Business Summary", "Website Quality Score", "Visual Design Score",
            "SEO Score", "Trust Score", "Mobile Experience Score",
            "Performance Score", "Content Quality Score", "CTA Score",
            "Top Strengths", "Top Weaknesses", "Actionable Recommendations",
            "Priority Improvements", "Overall Summary",
        ]
        missing = [k for k in required if k not in result]
        if missing:
            raise ServiceUnavailableException(f"Pollinations response missing keys: {missing}")

    def _validate_outreach_result(self, result: Dict[str, Any]) -> None:
        required = [
            "Email Subject", "Personalized Cold Email",
            "LinkedIn Message", "Follow-up Email", "Short Call-To-Action",
        ]
        missing = [k for k in required if k not in result]
        if missing:
            raise ServiceUnavailableException(f"Pollinations outreach missing keys: {missing}")

    def _normalize_audit_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        normalized = result.copy()
        score_keys = [
            "Website Quality Score", "Visual Design Score", "SEO Score",
            "Trust Score", "Mobile Experience Score", "Performance Score",
            "Content Quality Score", "CTA Score",
        ]
        for key in score_keys:
            if key in normalized:
                try:
                    normalized[key] = max(1, min(100, int(normalized[key])))
                except (ValueError, TypeError):
                    normalized[key] = 50

        list_keys = ["Top Strengths", "Top Weaknesses", "Actionable Recommendations", "Priority Improvements"]
        for key in list_keys:
            if key in normalized:
                if not isinstance(normalized[key], list):
                    normalized[key] = [str(normalized[key])]
                while len(normalized[key]) < 3:
                    normalized[key].append("Further analysis recommended")
            else:
                normalized[key] = ["Further analysis recommended"]

        text_keys = ["Business Summary", "Overall Summary"]
        for key in text_keys:
            if key in normalized:
                normalized[key] = str(normalized[key]).strip()
                if not normalized[key]:
                    normalized[key] = "Analysis pending additional data."
            else:
                normalized[key] = "Analysis pending additional data."

        return normalized

    def _normalize_outreach_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        normalized = result.copy()
        defaults = {
            "Email Subject": "Personalized consultation offer",
            "Personalized Cold Email": "We can help improve your online presence.",
            "LinkedIn Message": "I'd like to connect and discuss digital strategy.",
            "Follow-up Email": "Following up on my previous email.",
            "Short Call-To-Action": "Schedule a free consultation.",
        }
        for key, default_value in defaults.items():
            if key not in normalized or not normalized[key]:
                normalized[key] = default_value
            else:
                normalized[key] = str(normalized[key]).strip()
        return normalized

    async def health_check(self) -> Dict[str, Any]:
        try:
            await self._ensure_models_cached()
            return {
                "status": "healthy",
                "model": self.audit_model,
                "api_key_configured": False,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_key_configured": False,
            }
