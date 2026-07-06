import json
import asyncio
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from groq import Groq
from groq.types.chat import ChatCompletion
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ServiceUnavailableException
from app.services.ai.base import AIBaseProvider


class GroqProvider(AIBaseProvider):
    """
    Groq implementation for the AI Audit Engine with robust error handling,
    JSON parsing, retry logic, and response validation.

    This provider handles Groq's specific quirks including:
    - Markdown code block wrapping in responses
    - Incomplete or malformed JSON
    - Missing required fields
    - API timeouts and rate limiting
    - Graceful fallback mechanisms
    """

    def __init__(self):
        """Initialize Groq client with proper error handling."""
        self.api_key = settings.GROQ_API_KEY
        self.model = "llama-3.3-70b-versatile"
        self.max_retries = 1
        self.retry_delay = 2
        self.timeout = 30

        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set in configuration.")
            self.client = None
        else:
            try:
                self.client = Groq(
                    api_key=self.api_key,
                    base_url="https://api.groq.com",
                    timeout=self.timeout,
                    max_retries=1,
                )
                logger.info("Groq provider initialized successfully with model: %s", self.model)
            except Exception as e:
                logger.error("Failed to initialize Groq client: %s", e)
                self.client = None

        self.audit_required_keys = [
            "Business Summary",
            "Website Quality Score",
            "Visual Design Score",
            "SEO Score",
            "Trust Score",
            "Mobile Experience Score",
            "Performance Score",
            "Content Quality Score",
            "CTA Score",
            "Top Strengths",
            "Top Weaknesses",
            "Actionable Recommendations",
            "Priority Improvements",
            "Overall Summary",
        ]

        self.outreach_required_keys = [
            "Email Subject",
            "Personalized Cold Email",
            "LinkedIn Message",
            "Follow-up Email",
            "Short Call-To-Action",
        ]

    async def audit_website(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        screenshot_urls: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not settings.GROQ_API_KEY:
            raise ServiceUnavailableException(
                "Groq API key is not configured. Please set GROQ_API_KEY in environment variables."
            )

        if not self.client:
            raise ServiceUnavailableException(
                "Groq client is not initialized. Check API key and network connectivity."
            )

        base_prompt = self._build_audit_prompt(lead_info, website_analysis, screenshot_urls)
        strict_prompt = self._build_audit_prompt_with_strict_format(
            lead_info, website_analysis, screenshot_urls
        )

        attempts = [
            {"prompt": base_prompt, "description": "Standard prompt"},
            {"prompt": strict_prompt, "description": "Strict format prompt"},
        ]

        last_error = None

        for attempt_idx, attempt_config in enumerate(attempts):
            for retry_count in range(self.max_retries + 1):
                try:
                    logger.info(
                        "Groq audit attempt %d/%d (strategy: %s)",
                        retry_count + 1,
                        self.max_retries + 1,
                        attempt_config["description"],
                    )

                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.client.chat.completions.create,
                            model=self.model,
                            messages=[
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
                                {
                                    "role": "user",
                                    "content": attempt_config["prompt"],
                                },
                            ],
                            temperature=0.3,
                            max_tokens=2048,
                            top_p=0.95,
                            response_format={"type": "json_object"},
                        ),
                        timeout=self.timeout + 5,  # 5s buffer on top of SDK timeout
                    )

                    content = response.choices[0].message.content

                    if not content or not content.strip():
                        raise ValueError("Empty response received from Groq API")

                    logger.debug(
                        "Raw Groq response (first 500 chars): %s",
                        content[:500] + "..." if len(content) > 500 else content,
                    )

                    parsed_result = await self._parse_json_response(content)
                    self._validate_result(parsed_result)
                    normalized_result = self._normalize_audit_result(parsed_result)

                    logger.info(
                        "Groq audit completed successfully on attempt %d",
                        retry_count + 1,
                    )

                    return normalized_result

                except asyncio.TimeoutError:
                    last_error = Exception("Groq API call timed out")
                    logger.warning(
                        "Groq API timed out on attempt %d (strategy: %s)",
                        retry_count + 1,
                        attempt_config["description"],
                    )

                except json.JSONDecodeError as e:
                    last_error = e
                    logger.warning(
                        "JSON parsing failed on attempt %d (strategy: %s): %s",
                        retry_count + 1,
                        attempt_config["description"],
                        str(e),
                    )
                    if retry_count == self.max_retries and attempt_idx < len(attempts) - 1:
                        logger.info("Moving to next prompt strategy")
                        break

                except ValueError as e:
                    last_error = e
                    logger.warning(
                        "Validation failed on attempt %d (strategy: %s): %s",
                        retry_count + 1,
                        attempt_config["description"],
                        str(e),
                    )

                except Exception as e:
                    last_error = e
                    logger.error(
                        "Groq API error on attempt %d (strategy: %s): %s",
                        retry_count + 1,
                        attempt_config["description"],
                        str(e),
                    )

                    if "rate_limit" in str(e).lower() or "429" in str(e):
                        await asyncio.sleep(self.retry_delay * 2)
                    else:
                        await asyncio.sleep(self.retry_delay)

                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (retry_count + 1))

        logger.error(
            "All Groq audit attempts failed. Last error: %s",
            str(last_error),
        )

        fallback_audit = self._generate_fallback_audit(lead_info)

        if last_error:
            raise ServiceUnavailableException(
                f"Failed to generate AI Audit using Groq after 4 attempts. "
                f"Last error: {str(last_error)}"
            )
        else:
            raise ServiceUnavailableException(
                "Failed to generate AI Audit using Groq: Unknown error"
            )

    async def generate_outreach(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        audit_data: Dict[str, Any],
        score_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not settings.GROQ_API_KEY:
            raise ServiceUnavailableException(
                "Groq API key is not configured. Please set GROQ_API_KEY in environment variables."
            )

        if not self.client:
            raise ServiceUnavailableException(
                "Groq client is not initialized. Check API key and network connectivity."
            )

        base_prompt = self._build_outreach_prompt(
            lead_info, website_analysis, audit_data, score_data
        )

        for retry_count in range(self.max_retries + 1):
            try:
                logger.info(
                    "Groq outreach attempt %d/%d",
                    retry_count + 1,
                    self.max_retries + 1,
                )

                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert B2B copywriter and digital marketing strategist. "
                                    "You MUST return valid JSON only. "
                                    "DO NOT wrap your response in markdown code blocks. "
                                    "DO NOT add any explanatory text before or after the JSON. "
                                    "The response must be a valid JSON object with all required fields."
                                ),
                            },
                            {
                                "role": "user",
                                "content": base_prompt,
                            },
                        ],
                        temperature=0.7,
                        max_tokens=2048,
                        top_p=0.95,
                        response_format={"type": "json_object"},
                    ),
                    timeout=self.timeout + 5,
                )

                content = response.choices[0].message.content

                if not content or not content.strip():
                    raise ValueError("Empty response received from Groq API")

                logger.debug(
                    "Raw Groq outreach response (first 500 chars): %s",
                    content[:500] + "..." if len(content) > 500 else content,
                )

                parsed_result = await self._parse_json_response(content)
                self._validate_outreach_result(parsed_result)
                normalized_result = self._normalize_outreach_result(parsed_result)

                logger.info("Groq outreach completed successfully")
                return normalized_result

            except asyncio.TimeoutError:
                last_error = Exception("Groq API call timed out")
                logger.error("Groq outreach timed out on attempt %d", retry_count + 1)
            except Exception as e:
                last_error = e
                logger.error(
                    "Groq outreach attempt %d failed. Error: %s",
                    retry_count + 1,
                    str(e),
                )

            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
            else:
                raise ServiceUnavailableException(
                    f"Failed to generate AI Outreach using Groq after {self.max_retries + 1} attempts. "
                    f"Last error: {last_error}"
                )

    def _build_audit_prompt(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        screenshot_urls: Dict[str, Any],
    ) -> str:
        return f"""
You are an expert digital marketing auditor and website conversion specialist.
Analyze the following details of a lead business, their homepage technical scraped metrics, and visual screenshots to generate a detailed audit.

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
- Full Page Screenshot: {screenshot_urls.get("full_page_url", "Not provided")}

Generate a structured JSON response matching the required audit format.
Scores should be integers from 1-100.
All lists should contain at least 3-5 items.
"""

    def _build_audit_prompt_with_strict_format(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        screenshot_urls: Dict[str, Any],
    ) -> str:
        return f"""
You are an expert digital marketing auditor. Generate a comprehensive website audit in EXACTLY this JSON format:

{{
    "Business Summary": "string - 2-3 sentence summary of the business and its website",
    "Website Quality Score": integer 1-100,
    "Visual Design Score": integer 1-100,
    "SEO Score": integer 1-100,
    "Trust Score": integer 1-100,
    "Mobile Experience Score": integer 1-100,
    "Performance Score": integer 1-100,
    "Content Quality Score": integer 1-100,
    "CTA Score": integer 1-100,
    "Top Strengths": ["string", "string", "string"],
    "Top Weaknesses": ["string", "string", "string"],
    "Actionable Recommendations": ["string", "string", "string"],
    "Priority Improvements": ["string", "string", "string"],
    "Overall Summary": "string - comprehensive summary of the audit"
}}

Now analyze this data:
- Lead: {lead_info.get("name", "Not provided")} ({lead_info.get("industry", "Not provided")})
- Location: {lead_info.get("city", "Not provided")}, {lead_info.get("country", "Not provided")}
- Rating: {lead_info.get("rating", "Not provided")}
- Website Analysis: {json.dumps(website_analysis, indent=2, default=str)}
- Screenshots: {json.dumps(screenshot_urls, indent=2, default=str)}

Return ONLY valid JSON matching the format above. Do not add any other text.
"""

    def _build_outreach_prompt(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        audit_data: Dict[str, Any],
        score_data: Dict[str, Any],
    ) -> str:
        return f"""
You are an expert B2B copywriter and digital marketing strategist.

Generate personalized outreach messages for this lead based on their data.

### Lead Information:
{json.dumps(lead_info, indent=2, default=str)}

### Website Audit Results:
{json.dumps(audit_data, indent=2, default=str)}

### Lead Score Data:
{json.dumps(score_data, indent=2, default=str)}

### Required Output Format:
{{
    "Email Subject": "string - compelling subject line for cold email",
    "Personalized Cold Email": "string - full email body with personalization",
    "LinkedIn Message": "string - concise LinkedIn connection message",
    "Follow-up Email": "string - follow-up email for non-responders",
    "Short Call-To-Action": "string - clear, specific CTA"
}}

Return ONLY valid JSON matching this format. Make messages professional, personalized, and value-focused.
"""

    async def _parse_json_response(self, content: str) -> Dict[str, Any]:
        if not content:
            raise json.JSONDecodeError("Empty content", content, 0)

        cleaned_content = content.strip()

        json_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(json_block_pattern, cleaned_content)

        if matches:
            cleaned_content = matches[0].strip()
            logger.debug("Extracted JSON from markdown code block")

        if not cleaned_content.startswith("{") and not cleaned_content.startswith("["):
            json_pattern = r"(\{[\s\S]*\}|\[[\s\S]*\])"
            json_matches = re.findall(json_pattern, cleaned_content)
            if json_matches:
                cleaned_content = json_matches[0].strip()
                logger.debug("Extracted JSON from surrounding text")

        parse_attempts = [
            lambda: json.loads(cleaned_content),
            lambda: json.loads(re.sub(r',\s*}', '}', re.sub(r',\s*]', ']', cleaned_content))),
            lambda: json.loads(re.sub(r'(\w+):', r'"\1":', cleaned_content)),
            lambda: json.loads(re.sub(r"'([^']*)'", r'"\1"', cleaned_content)),
            lambda: self._repair_malformed_json(cleaned_content),
        ]

        for idx, parse_func in enumerate(parse_attempts):
            try:
                result = parse_func()
                if isinstance(result, dict):
                    logger.debug("Successfully parsed JSON using strategy %d", idx + 1)
                    return result
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue

        raise json.JSONDecodeError(
            f"Unable to parse JSON after multiple strategies. Content: {content[:200]}...",
            content,
            0,
        )

    def _repair_malformed_json(self, content: str) -> Dict[str, Any]:
        try:
            content = content.strip()
            if not content.startswith("{"):
                content = "{" + content
            if not content.endswith("}"):
                content = content + "}"

            content = re.sub(r"(\w+):", r'"\1":', content)
            content = re.sub(r':\s*([^",\{\}\[\]]+?)(?=,|\})', r': "\1"', content)
            content = re.sub(r',\s*}', '}', content)
            content = re.sub(r',\s*]', ']', content)

            return json.loads(content)
        except json.JSONDecodeError:
            raise

    def _normalize_audit_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        normalized = result.copy()

        score_keys = [
            "Website Quality Score",
            "Visual Design Score",
            "SEO Score",
            "Trust Score",
            "Mobile Experience Score",
            "Performance Score",
            "Content Quality Score",
            "CTA Score",
        ]

        for key in score_keys:
            if key in normalized:
                try:
                    score = int(normalized[key])
                    normalized[key] = max(1, min(100, score))
                except (ValueError, TypeError):
                    normalized[key] = 50

        list_keys = [
            "Top Strengths",
            "Top Weaknesses",
            "Actionable Recommendations",
            "Priority Improvements",
        ]

        for key in list_keys:
            if key in normalized:
                if not isinstance(normalized[key], list):
                    normalized[key] = [str(normalized[key])]
                while len(normalized[key]) < 3:
                    if key == "Top Strengths":
                        normalized[key].append("Website is operational")
                    elif key == "Top Weaknesses":
                        normalized[key].append("Could be improved further")
                    elif key == "Actionable Recommendations":
                        normalized[key].append("Consider professional consultation")
                    else:
                        normalized[key].append("Regular monitoring recommended")
            else:
                normalized[key] = [
                    "Further analysis recommended",
                    "Detailed review needed",
                    "Professional consultation advised",
                ]

        text_keys = ["Business Summary", "Overall Summary"]
        for key in text_keys:
            if key in normalized:
                normalized[key] = str(normalized[key]).strip()
                if not normalized[key]:
                    normalized[key] = "Business appears to be a legitimate operation requiring further analysis."
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

    def _validate_result(self, result: Dict[str, Any]) -> None:
        missing_keys = [k for k in self.audit_required_keys if k not in result]

        if missing_keys:
            logger.debug("Response keys present: %s", list(result.keys()))
            raise ValueError(f"AI response is missing keys: {missing_keys}")

    def _validate_outreach_result(self, result: Dict[str, Any]) -> None:
        missing_keys = [k for k in self.outreach_required_keys if k not in result]

        if missing_keys:
            logger.debug("Response keys present: %s", list(result.keys()))
            raise ValueError(f"AI response is missing keys: {missing_keys}")

    def _generate_fallback_audit(self, lead_info: Dict[str, Any]) -> Dict[str, Any]:
        business_name = lead_info.get("name", "Business")
        industry = lead_info.get("industry", "Unknown")

        return {
            "Business Summary": f"{business_name} operates in the {industry} industry. Complete analysis was not possible due to API limitations.",
            "Website Quality Score": 50,
            "Visual Design Score": 50,
            "SEO Score": 50,
            "Trust Score": 50,
            "Mobile Experience Score": 50,
            "Performance Score": 50,
            "Content Quality Score": 50,
            "CTA Score": 50,
            "Top Strengths": [
                "Business is established in its market",
                "Has online presence",
                "Relevant industry experience",
            ],
            "Top Weaknesses": [
                "Limited website optimization",
                "Need for digital marketing strategy",
                "Potential improvements in user experience",
            ],
            "Actionable Recommendations": [
                "Perform a thorough SEO audit",
                "Review website design and responsiveness",
                "Implement modern web technologies",
            ],
            "Priority Improvements": [
                "Mobile optimization",
                "Page speed improvement",
                "Content marketing strategy",
            ],
            "Overall Summary": f"{business_name} shows potential but would benefit from significant website improvements. "
            f"As a {industry} business, a strong digital presence is crucial for growth.",
        }

    async def health_check(self) -> Dict[str, Any]:
        try:
            if not self.client:
                return {
                    "status": "unhealthy",
                    "error": "Groq client not initialized",
                    "model": self.model,
                    "api_key_configured": bool(self.api_key),
                }

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5,
                    temperature=0,
                ),
                timeout=10,
            )

            if response and response.choices:
                return {
                    "status": "healthy",
                    "model": self.model,
                    "api_key_configured": True,
                    "response_received": True,
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Invalid response from Groq",
                    "model": self.model,
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model,
                "api_key_configured": bool(self.api_key),
            }
