import json
import asyncio
from typing import Dict, Any
import google.generativeai as genai

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ServiceUnavailableException
from app.services.ai.base import AIBaseProvider


class GeminiProvider(AIBaseProvider):
    """
    Gemini implementation for the AI Audit Engine.
    """

    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        else:
            logger.warning("GEMINI_API_KEY is not set in configuration.")

    async def audit_website(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        screenshot_urls: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Audit website using Google Gemini.
        """
        if not settings.GEMINI_API_KEY:
            raise ServiceUnavailableException("Gemini API key is not configured.")

        # Construct prompt
        prompt = self._build_prompt(lead_info, website_analysis, screenshot_urls)
        
        # Implement retry logic
        max_retries = 2
        attempt = 0
        
        while attempt <= max_retries:
            try:
                # Use gemini-1.5-flash as default, or fallback to gemini-1.5-pro
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                # google-generativeai call is synchronous, wrap in asyncio.to_thread
                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                if not response.text:
                    raise ValueError("Empty response received from Gemini.")

                parsed_result = json.loads(response.text)
                self._validate_result(parsed_result)
                return parsed_result

            except Exception as e:
                attempt += 1
                logger.error("Gemini audit attempt %d failed. Error: %s", attempt, e)
                if attempt > max_retries:
                    raise ServiceUnavailableException(f"Failed to generate AI Audit using Gemini: {e}")
                await asyncio.sleep(2)
        
        return {}

    def _build_prompt(self, lead_info: Dict[str, Any], website_analysis: Dict[str, Any], screenshot_urls: Dict[str, Any]) -> str:
        return f"""
You are an expert digital marketing auditor and website conversion specialist.
Analyze the following details of a lead business, their homepage technical scraped metrics, and visual screenshots to generate a detailed audit.

### Lead Information:
- Business Name: {lead_info.get("name")}
- Industry: {lead_info.get("industry")}
- Location: {lead_info.get("city")}, {lead_info.get("country")}
- Google Maps Rating: {lead_info.get("rating")} ({lead_info.get("reviews_count")} reviews)

### Scraped Website Analysis:
- Title: {website_analysis.get("website_title")}
- Meta Description: {website_analysis.get("meta_description")}
- SSL Enabled: {website_analysis.get("https_enabled")}
- HTTP Status Code: {website_analysis.get("http_status_code")}
- Total H1 tags: {website_analysis.get("h1_count")}
- Total H2 tags: {website_analysis.get("h2_count")}
- Total Paragraphs: {website_analysis.get("total_paragraphs")}
- Total Images: {website_analysis.get("total_images")}
- Total Forms: {website_analysis.get("total_forms")}
- Found Emails: {website_analysis.get("emails")}
- Found Phones: {website_analysis.get("phone_numbers")}
- Contact Page Exists: {website_analysis.get("contact_page_exists")}
- About Page Exists: {website_analysis.get("about_page_exists")}
- Navigation Size & Complexity: {len(website_analysis.get("navigation_structure") or [])} links
- Social Links: Facebook: {website_analysis.get("social_facebook")}, Instagram: {website_analysis.get("social_instagram")}, LinkedIn: {website_analysis.get("social_linkedin")}, Twitter/X: {website_analysis.get("social_twitter")}, YouTube: {website_analysis.get("social_youtube")}
- SEO Flags: Missing Title: {website_analysis.get("missing_title")}, Missing Meta Description: {website_analysis.get("missing_meta_description")}, Missing H1: {website_analysis.get("missing_h1")}
- HTML Page Size: {website_analysis.get("html_size_kb")} KB
- Page Load Time: {website_analysis.get("response_time_ms")} ms

### Visual Screenshots (Cloudinary URLs):
- Desktop Screenshot: {screenshot_urls.get("desktop_url")}
- Mobile Screenshot: {screenshot_urls.get("mobile_url")}
- Full Page Screenshot: {screenshot_urls.get("full_page_url")}

---
Generate a structured JSON response matching the following keys exactly:
- "Business Summary": A concise breakdown of what the business does and their online presence.
- "Website Quality Score": Integer between 0 and 100 representing overall quality.
- "Visual Design Score": Integer between 0 and 100 evaluating visual aesthetics.
- "SEO Score": Integer between 0 and 100 based on title tags, meta description, and headers.
- "Trust Score": Integer between 0 and 100 based on SSL, reviews, trust indicators, clear contact info.
- "Mobile Experience Score": Integer between 0 and 100 based on mobile structure/scrapes.
- "Performance Score": Integer between 0 and 100 based on HTML size and load times.
- "Content Quality Score": Integer between 0 and 100 based on paragraphs, structure, readability.
- "CTA Score": Integer between 0 and 100 evaluating calls to action and forms.
- "Top Strengths": Array of strings representing what the website does well.
- "Top Weaknesses": Array of objects. Each object must have keys:
  - "title": Short title of weakness.
  - "evidence": Technical or design evidence observed.
  - "impact": The business impact of the weakness.
  - "recommendation": Actionable remediation advice.
- "Actionable Recommendations": Array of strings containing concrete design/marketing advice.
- "Priority Improvements": Array of strings listing highest-priority fixes.
- "Overall Summary": Summary sentence highlighting the primary conversion/SEO opportunity.

Ensure your response is valid JSON only. Do not wrap in backticks or markdown tags.
"""

    def _validate_result(self, result: Dict[str, Any]) -> None:
        required_keys = [
            "Business Summary", "Website Quality Score", "Visual Design Score", "SEO Score",
            "Trust Score", "Mobile Experience Score", "Performance Score", "Content Quality Score",
            "CTA Score", "Top Strengths", "Top Weaknesses", "Actionable Recommendations",
            "Priority Improvements", "Overall Summary"
        ]
        missing = [k for k in required_keys if k not in result]
        if missing:
            raise ValueError(f"AI response is missing keys: {missing}")

    async def generate_outreach(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        audit_data: Dict[str, Any],
        score_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized outreach using Google Gemini.
        """
        if not settings.GEMINI_API_KEY:
            raise ServiceUnavailableException("Gemini API key is not configured.")

        # Construct prompt
        prompt = self._build_outreach_prompt(lead_info, website_analysis, audit_data, score_data)
        
        # Implement retry logic
        max_retries = 2
        attempt = 0
        
        while attempt <= max_retries:
            try:
                # Use gemini-1.5-flash as default
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                if not response.text:
                    raise ValueError("Empty response received from Gemini.")

                parsed_result = json.loads(response.text)
                self._validate_outreach_result(parsed_result)
                return parsed_result

            except Exception as e:
                attempt += 1
                logger.error("Gemini outreach attempt %d failed. Error: %s", attempt, e)
                if attempt > max_retries:
                    raise ServiceUnavailableException(f"Failed to generate AI Outreach using Gemini: {e}")
                await asyncio.sleep(2)
        
        return {}

    def _build_outreach_prompt(self, lead_info: Dict[str, Any], website_analysis: Dict[str, Any], audit_data: Dict[str, Any], score_data: Dict[str, Any]) -> str:
        return f"""
You are an expert B2B copywriter and digital marketing strategist.
Generate highly personalized outreach messages for a lead using their business details, website analysis, AI audit findings, and lead score.

### Lead Information:
- Business Name: {lead_info.get("name")}
- Industry: {lead_info.get("industry")}
- Location: {lead_info.get("city")}, {lead_info.get("country")}

### AI Audit & Weaknesses:
- Overall Score: {score_data.get("overall_score")} (Category: {score_data.get("category")})
- Top Weaknesses: {json.dumps(audit_data.get("weaknesses", []))}
- Actionable Recommendations: {json.dumps(audit_data.get("actionable_recommendations", []))}

---
Generate a structured JSON response matching exactly the following keys:
- "Email Subject": A catchy, personalized subject line.
- "Personalized Cold Email": A concise, highly personalized cold email body that references a specific weakness from the audit and offers a solution. Use professional but conversational tone.
- "LinkedIn Message": A shorter, engaging message suitable for LinkedIn connection request or direct message.
- "Follow-up Email": A short, polite follow-up email.
- "Short Call-To-Action": A 1-2 sentence compelling call to action (e.g. for SMS, WhatsApp, or ending a message).

Ensure your response is valid JSON only. Do not wrap in backticks or markdown tags.
"""

    def _validate_outreach_result(self, result: Dict[str, Any]) -> None:
        required_keys = [
            "Email Subject", "Personalized Cold Email", "LinkedIn Message", "Follow-up Email", "Short Call-To-Action"
        ]
        missing = [k for k in required_keys if k not in result]
        if missing:
            raise ValueError(f"AI response is missing keys: {missing}")
