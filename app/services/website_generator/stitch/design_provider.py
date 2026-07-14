"""StitchDesignProvider — automated Stitch generation via internal TypeScript service.

Calls the Stitch service over internal HTTP, retrieves real generated HTML,
and returns a valid GenerationResult. Falls back to StitchImportProvider
when the service is unavailable.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.website_intelligence.schemas import WebsiteProfile
from app.services.website_generator.design_provider import DesignProvider
from app.services.website_generator.schemas import (
    GenerationResult,
    GeneratedFile,
    WebsiteProject,
)
from app.services.website_generator.stitch.brief import BriefGenerator
from app.services.website_generator.stitch.import_provider import StitchImportProvider

logger = logging.getLogger(__name__)

STITCH_SERVICE_URL = os.getenv("STITCH_SERVICE_URL", "http://127.0.0.1:3100")
STITCH_SERVICE_SECRET = os.getenv("STITCH_SERVICE_SECRET", "leadforge-internal-shared-secret")
STITCH_GENERATE_TIMEOUT = int(os.getenv("STITCH_GENERATE_TIMEOUT", "360"))


class StitchDesignProvider(DesignProvider):
    """DesignProvider that calls the internal TypeScript Stitch service.

    Workflow:
    1. Build PremiumRedesignBrief from profile + package
    2. POST /generate to the Stitch service
    3. Receive real HTML content
    4. Return GenerationResult with WebsiteProject

    When the Stitch service is unreachable or returns an error,
    returns a structured failure — never dummy HTML.
    """

    async def generate(
        self,
        profile: WebsiteProfile,
        package: MarkdownPackage,
    ) -> GenerationResult:
        logger.info(
            "[StitchDesignProvider] Generating for %s",
            profile.business.name or profile.business.website_url,
        )

        brief_gen = BriefGenerator()
        brief = brief_gen.generate(profile, package)

        if not brief.full_instruction or len(brief.full_instruction) < 50:
            return GenerationResult(
                success=False,
                errors=["Brief generation produced empty instruction"],
            )

        try:
            result = await self._call_stitch_service(brief, profile)
            return result
        except Exception as exc:
            logger.error("[StitchDesignProvider] Service call failed: %s", exc)
            return GenerationResult(
                success=False,
                errors=[f"Stitch service error: {type(exc).__name__}: {exc}"],
            )

    async def _call_stitch_service(
        self,
        brief: Any,
        profile: WebsiteProfile,
    ) -> GenerationResult:
        payload = {
            "brief_instruction": brief.full_instruction,
            "business_name": brief.business_name,
        }

        url = f"{STITCH_SERVICE_URL}/generate"
        headers = {
            "Content-Type": "application/json",
            "X-Internal-Secret": STITCH_SERVICE_SECRET,
        }

        logger.info(
            "[StitchDesignProvider] Calling %s (brief length: %d)",
            url,
            len(brief.full_instruction),
        )

        async with httpx.AsyncClient(timeout=STITCH_GENERATE_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code != 200:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            error_msg = body.get("error", f"HTTP {resp.status_code}")
            logger.error("[StitchDesignProvider] Service returned %d: %s", resp.status_code, error_msg)
            return GenerationResult(
                success=False,
                errors=[f"Stitch service returned {resp.status_code}: {error_msg}"],
            )

        data = resp.json()

        if not data.get("success"):
            error_msg = data.get("error", "Unknown Stitch error")
            return GenerationResult(
                success=False,
                errors=[f"Stitch generation failed: {error_msg}"],
            )

        html_content = data.get("html_content", "")
        if not html_content or len(html_content.strip()) < 100:
            return GenerationResult(
                success=False,
                errors=["Stitch returned empty or too-short HTML content"],
            )

        stitch_project_id = data.get("stitch_project_id")
        stitch_screen_id = data.get("stitch_screen_id")
        provider_attempts = data.get("attempts", 1)

        generation_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc)

        files = [
            GeneratedFile(
                path="index.html",
                content=html_content,
                type="text/html",
                size=len(html_content.encode("utf-8")),
            )
        ]

        metadata = {
            "source": "stitch_automated",
            "stitch_project_id": stitch_project_id,
            "stitch_screen_id": stitch_screen_id,
            "generated_at": now.isoformat(),
            "html_size": len(html_content),
            "html_url": data.get("html_url"),
            "screenshot_url": data.get("screenshot_url"),
        }

        project = WebsiteProject(
            project_name=f"{profile.business.name or 'Website'} — Stitch Redesign",
            framework="static-html",
            generation_id=generation_id,
            version="1.0.0",
            generated_at=now,
            files=files,
            assets=[],
            metadata=metadata,
            statistics={
                "html_chars": len(html_content),
                "import_source": "stitch_automated",
                "stitch_project_id": stitch_project_id,
                "stitch_screen_id": stitch_screen_id,
            },
            preview_html=html_content,
        )

        logger.info(
            "[StitchDesignProvider] Success: %d bytes, project=%s, screen=%s",
            len(html_content),
            stitch_project_id,
            stitch_screen_id,
        )

        return GenerationResult(
            success=True,
            website_project=project,
            warnings=[],
            errors=[],
            provider_used="stitch_automated",
            provider_attempts=provider_attempts,
            generation_time=0.0,
        )

    def provider_name(self) -> str:
        return "stitch_automated"

    @staticmethod
    async def check_service_health() -> Dict[str, Any]:
        """Check if the Stitch service is reachable and healthy."""
        url = f"{STITCH_SERVICE_URL}/health"
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "error", "http_status": resp.status_code}
        except Exception as exc:
            return {"status": "unreachable", "error": str(exc)}
