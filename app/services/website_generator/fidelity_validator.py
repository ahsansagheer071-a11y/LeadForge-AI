"""FidelityValidator — validates generated HTML against source content.

Phase 3: Simplified to focus on business identity and content authenticity.
Stitch is treated as an expert UI/UX designer, not an HTML generator.
We validate that the redesign preserves the correct business and doesn't
invent fake content — not that it matches exact section counts.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.website_intelligence.schemas import WebsiteProfile

logger = logging.getLogger(__name__)

_LOREM_IPSUM = re.compile(r"lorem\s+ipsum", re.IGNORECASE)
_SERVICE_PLACEHOLDER = re.compile(
    r"service\s+[123]|service\s+one|service\s+two|service\s+three",
    re.IGNORECASE,
)
_LEADFORGE_BRANDING = re.compile(
    r"leadforge|lead\s*forge|generated\s+by\s+leadforge",
    re.IGNORECASE,
)
_MARKDOWN_FENCE = re.compile(r"```")
_DUMMY_EMAIL = re.compile(r"@example\.com|@domain\.com|@yourcompany\.com", re.IGNORECASE)
_DUMMY_PHONE = re.compile(
    r"\(?000\)?\s*[-.]?\s*000[-.]?\s*0000|123-456-7890|555-0100",
    re.IGNORECASE,
)
_DUMMY_ADDRESS = re.compile(
    r"123\s+(main|elm|oak|maple|fake|example)\s+(st|street|ave|avenue)",
    re.IGNORECASE,
)


@dataclass
class FidelityIssue:
    category: str
    detail: str


@dataclass
class FidelityValidationResult:
    valid: bool
    issues: List[FidelityIssue] = field(default_factory=list)
    completeness_score: float = 0.0

    # Legacy fields kept for metadata compatibility — not actively populated
    source_section_count: int = 0
    generated_section_count: int = 0
    source_service_count: int = 0
    preserved_service_count: int = 0
    source_product_count: int = 0
    preserved_product_count: int = 0
    source_testimonial_count: int = 0
    preserved_testimonial_count: int = 0
    source_faq_count: int = 0
    preserved_faq_count: int = 0
    source_contact_emails: List[str] = field(default_factory=list)
    preserved_contact_emails: List[str] = field(default_factory=list)
    source_contact_phones: List[str] = field(default_factory=list)
    preserved_contact_phones: List[str] = field(default_factory=list)
    source_meaningful_images: int = 0
    approved_image_count: int = 0
    broken_image_refs: List[str] = field(default_factory=list)
    source_nav_items: int = 0
    preserved_nav_items: int = 0
    missing_item_names: List[str] = field(default_factory=list)


class FidelityValidator:
    """Validates that a redesigned HTML preserves business identity and contains no fakes.

    Phase 3 philosophy: Stitch is an expert designer. We don't demand
    exact section counts or product matches. We validate:
    - Correct business name
    - No Lorem Ipsum
    - No fake content (dummy emails, phones, addresses)
    - No LeadForge branding
    - Valid HTML with visible content
    - H1 contains business name
    """

    def __init__(self, profile: WebsiteProfile, manifest: Optional[object] = None):
        self.profile = profile

    def validate(self, html: str) -> FidelityValidationResult:
        result = FidelityValidationResult(valid=False)

        if not html or not html.strip():
            result.issues.append(FidelityIssue(
                category="empty_output", detail="Generated HTML is empty"
            ))
            result.valid = False
            return result

        # ── Content authenticity checks ───────────────────────────────────
        if _MARKDOWN_FENCE.search(html):
            result.issues.append(FidelityIssue(
                category="markdown_fences",
                detail="Generated output contains markdown code fences",
            ))

        biz_name = self.profile.business.name
        if biz_name and biz_name not in html:
            result.issues.append(FidelityIssue(
                category="missing_business_name",
                detail=f"Source business name '{biz_name}' not found in generated HTML",
            ))

        if _LOREM_IPSUM.search(html):
            result.issues.append(FidelityIssue(
                category="lorem_ipsum",
                detail="Generated HTML contains Lorem Ipsum placeholder text",
            ))

        if _SERVICE_PLACEHOLDER.search(html):
            result.issues.append(FidelityIssue(
                category="service_placeholder",
                detail="Generated HTML contains generic Service 1/2/3 placeholder",
            ))

        if _LEADFORGE_BRANDING.search(html):
            result.issues.append(FidelityIssue(
                category="leadforge_branding",
                detail="Generated HTML contains LeadForge branding",
            ))

        if _DUMMY_EMAIL.search(html):
            result.issues.append(FidelityIssue(
                category="dummy_email",
                detail="Generated HTML contains example.com or dummy email address",
            ))

        if _DUMMY_PHONE.search(html):
            result.issues.append(FidelityIssue(
                category="dummy_phone",
                detail="Generated HTML contains dummy phone number",
            ))

        if _DUMMY_ADDRESS.search(html):
            result.issues.append(FidelityIssue(
                category="dummy_address",
                detail="Generated HTML contains dummy street address",
            ))

        # ── HTML quality checks ───────────────────────────────────────────
        text_only = re.sub(r'<[^>]+>', '', html).strip()
        visible_words = len(text_only.split())
        if visible_words < 5:
            result.issues.append(FidelityIssue(
                category="no_visible_content",
                detail=f"Generated HTML contains only {visible_words} visible word(s)",
            ))

        # ── H1 must contain business name ─────────────────────────────────
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
        if biz_name:
            if h1_match:
                h1_text = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
                if biz_name.lower() not in h1_text.lower():
                    result.issues.append(FidelityIssue(
                        category="wrong_h1",
                        detail=f"H1 '{h1_text}' does not contain business name '{biz_name}'",
                    ))
            else:
                result.issues.append(FidelityIssue(
                    category="missing_h1",
                    detail="Generated HTML has no <h1> tag",
                ))

        # ── Completeness score ────────────────────────────────────────────
        # Simple: 1.0 if no issues, penalized per issue
        result.completeness_score = max(0.0, 1.0 - len(result.issues) * 0.15)

        result.valid = len(result.issues) == 0

        logger.info(
            "FidelityValidator: %s | issues=%d completeness=%.0f%%",
            "PASS" if result.valid else "FAIL",
            len(result.issues),
            result.completeness_score * 100,
        )
        if not result.valid:
            for issue in result.issues:
                logger.warning("  %s: %s", issue.category, issue.detail)

        return result
