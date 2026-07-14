"""StitchImportProvider — DesignProvider that imports Stitch HTML exports.

This provider implements the manual-import proof of concept:
1. User generates a PremiumRedesignBrief from LeadForge
2. User pastes the brief into Google Stitch
3. Stitch generates the design
4. User exports/downloads the HTML
5. User provides the HTML to LeadForge via import endpoint
6. This provider validates, stores, and packages the result

When no export is supplied, returns design_provider_not_configured.
"""

import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.website_intelligence.schemas import WebsiteProfile
from app.services.website_generator.design_provider import DesignProvider
from app.services.website_generator.schemas import (
    GenerationResult,
    GeneratedFile,
    WebsiteProject,
)

logger = logging.getLogger(__name__)


class StitchImportProvider(DesignProvider):
    """DesignProvider that imports a Stitch HTML export.

    Unlike DesignProviderNotConfigured, this provider can accept a real
    HTML export from Google Stitch and produce a valid GenerationResult.
    """

    NOT_CONFIGURED_MESSAGE = (
        "Stitch export not provided. Generate a redesign brief, "
        "create the design in Google Stitch, then import the HTML export."
    )

    async def generate(
        self,
        profile: WebsiteProfile,
        package: MarkdownPackage,
        *,
        html_content: Optional[str] = None,
        stitch_project_id: Optional[str] = None,
        stitch_screen_id: Optional[str] = None,
    ) -> GenerationResult:
        if not html_content or len(html_content.strip()) < 100:
            logger.warning("[StitchImportProvider] No valid HTML content provided")
            return GenerationResult(
                success=False,
                errors=[self.NOT_CONFIGURED_MESSAGE],
            )

        logger.info(
            "[StitchImportProvider] Importing Stitch export: %d bytes",
            len(html_content),
        )

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
            "source": "stitch_import",
            "stitch_project_id": stitch_project_id,
            "stitch_screen_id": stitch_screen_id,
            "imported_at": now.isoformat(),
            "html_size": len(html_content),
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
                "import_source": "stitch",
            },
            preview_html=html_content,
        )

        return GenerationResult(
            success=True,
            website_project=project,
            warnings=[],
            errors=[],
            provider_used="stitch_import",
            provider_attempts=1,
        )

    def provider_name(self) -> str:
        return "stitch_import"

    @staticmethod
    def validate_export(html_content: str) -> list[str]:
        """Validate a Stitch HTML export. Returns list of issues (empty = valid)."""
        issues = []

        if not html_content or not html_content.strip():
            issues.append("HTML content is empty")
            return issues

        if len(html_content.strip()) < 100:
            issues.append(f"HTML content too short ({len(html_content)} chars)")

        if "<!DOCTYPE" not in html_content and "<html" not in html_content:
            issues.append("Content does not appear to be valid HTML (no DOCTYPE or <html> tag)")

        if re.search(r"lorem\s+ipsum", html_content, re.IGNORECASE):
            issues.append("Contains Lorem Ipsum placeholder text")

        if re.search(r"leadforge|lead\s*forge", html_content, re.IGNORECASE):
            issues.append("Contains LeadForge branding")

        if re.search(r"@example\.com|@domain\.com", html_content, re.IGNORECASE):
            issues.append("Contains dummy email addresses")

        if re.search(r"555-0100|123-456-7890", html_content):
            issues.append("Contains dummy phone numbers")

        if not re.search(r"<h[1-6]", html_content, re.IGNORECASE):
            issues.append("No heading tags found (H1-H6)")

        if not re.search(r"<img", html_content, re.IGNORECASE):
            issues.append("No images found in HTML")

        if re.search(r"```", html_content):
            issues.append("Contains markdown code fences")

        return issues
