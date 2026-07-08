import json
import asyncio
import re
from typing import Dict, Any, Optional

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ServiceUnavailableException
from app.services.ai.base import AIBaseProvider


NVIDIA_CHAT_ENDPOINT = "/chat/completions"
NVIDIA_TIMEOUT = 120.0


class NvidiaProvider(AIBaseProvider):
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self._base_url = settings.NVIDIA_BASE_URL.rstrip("/")

    async def audit_website(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        screenshot_urls: Dict[str, Any],
    ) -> Dict[str, Any]:
        model = settings.NVIDIA_AUDIT_MODEL
        prompt = self._build_audit_prompt(lead_info, website_analysis, screenshot_urls)
        result = await self._call_api(prompt, model, NVIDIA_TIMEOUT)
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
        model = settings.NVIDIA_GENERATION_MODEL
        prompt = self._build_outreach_prompt(lead_info, website_analysis, audit_data, score_data)
        result = await self._call_api(prompt, model, NVIDIA_TIMEOUT)
        parsed = await self._parse_json_response(result)
        self._validate_outreach_result(parsed)
        return self._normalize_outreach_result(parsed)

    async def _call_api(self, prompt: str, model: str, timeout: float) -> str:
        if not self.api_key:
            raise ServiceUnavailableException("NVIDIA_API_KEY is not configured")

        endpoint = f"{self._base_url}{NVIDIA_CHAT_ENDPOINT}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert digital marketing auditor. "
                        "You MUST return valid JSON only. "
                        "DO NOT wrap your response in markdown code blocks. "
                        "The response must be a valid JSON object."
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
                logger.warning("NVIDIA API timed out (attempt %d/2)", retry + 1)
                if retry < 1:
                    await asyncio.sleep(2.0)
                    continue
                raise ServiceUnavailableException("NVIDIA API call timed out")
            except httpx.ConnectError:
                logger.warning("NVIDIA connection error (attempt %d/2)", retry + 1)
                if retry < 1:
                    await asyncio.sleep(1.0)
                    continue
                raise ServiceUnavailableException("NVIDIA API connection failed")
            except Exception as e:
                logger.error("NVIDIA API error: %s", e)
                raise ServiceUnavailableException(f"NVIDIA API error: {e}")

            if resp.status_code == 429:
                logger.warning("NVIDIA rate limited (attempt %d/2)", retry + 1)
                if retry < 1:
                    await asyncio.sleep(5.0)
                    continue
                raise ServiceUnavailableException("NVIDIA rate limit exceeded")
            if resp.status_code in (401, 403):
                raise ServiceUnavailableException("NVIDIA authentication failed")
            if resp.status_code != 200:
                body = resp.text[:300]
                logger.warning("NVIDIA HTTP %d: %s", resp.status_code, body)
                raise ServiceUnavailableException(f"NVIDIA returned HTTP {resp.status_code}")

            try:
                data = resp.json()
            except Exception:
                raise ServiceUnavailableException("Invalid JSON from NVIDIA API")

            try:
                content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                raise ServiceUnavailableException("Unexpected response structure from NVIDIA")

            if not content or not content.strip():
                raise ServiceUnavailableException("Empty response from NVIDIA API")

            return content

        raise ServiceUnavailableException("NVIDIA API failed after retries")

    def _build_audit_prompt(self, lead_info: Dict[str, Any], website_analysis: Dict[str, Any], screenshot_urls: Dict[str, Any]) -> str:
        return f"""
Analyze the following business details and website data to generate a detailed audit.

### Lead Information:
- Business Name: {lead_info.get("name", "Not provided")}
- Industry: {lead_info.get("industry", "Not provided")}
- Location: {lead_info.get("city", "Not provided")}, {lead_info.get("country", "Not provided")}
- Rating: {lead_info.get("rating", "Not provided")}

### Website Analysis:
{json.dumps(website_analysis, indent=2, default=str)}

### Screenshots:
{json.dumps(screenshot_urls, indent=2, default=str)}

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

### Audit Results:
{json.dumps(audit_data, indent=2, default=str)}

### Score Data:
{json.dumps(score_data, indent=2, default=str)}

### Required Output Format:
{{
    "Email Subject": "string",
    "Personalized Cold Email": "string",
    "LinkedIn Message": "string",
    "Follow-up Email": "string",
    "Short Call-To-Action": "string"
}}

Return ONLY valid JSON.
"""

    async def _parse_json_response(self, content: str) -> Dict[str, Any]:
        if not content:
            raise ServiceUnavailableException("Empty content from NVIDIA")

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
                raise ServiceUnavailableException("Failed to parse JSON from NVIDIA response")

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
            raise ServiceUnavailableException(f"NVIDIA response missing keys: {missing}")

    def _validate_outreach_result(self, result: Dict[str, Any]) -> None:
        required = [
            "Email Subject", "Personalized Cold Email",
            "LinkedIn Message", "Follow-up Email", "Short Call-To-Action",
        ]
        missing = [k for k in required if k not in result]
        if missing:
            raise ServiceUnavailableException(f"NVIDIA outreach missing keys: {missing}")

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
            return {
                "status": "healthy",
                "model": settings.NVIDIA_AUDIT_MODEL,
                "api_key_configured": bool(self.api_key),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_key_configured": bool(self.api_key),
            }
