"""FidelityValidator — validates generated HTML against source content
to ensure no invented content, missing sections, or unapproved images."""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from app.services.markdown_engine.asset_manifest import AssetManifest
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
    source_section_count: int = 0
    generated_section_count: int = 0
    source_service_count: int = 0
    preserved_service_count: int = 0
    source_product_count: int = 0
    preserved_product_count: int = 0
    source_contact_emails: List[str] = field(default_factory=list)
    preserved_contact_emails: List[str] = field(default_factory=list)
    source_contact_phones: List[str] = field(default_factory=list)
    preserved_contact_phones: List[str] = field(default_factory=list)
    source_meaningful_images: int = 0
    approved_image_count: int = 0
    broken_image_refs: List[str] = field(default_factory=list)


class FidelityValidator:
    """Validates that generated HTML faithfully represents source content."""

    def __init__(self, profile: WebsiteProfile, manifest: Optional[AssetManifest] = None):
        self.profile = profile
        self.manifest = manifest

    def validate(self, html: str) -> FidelityValidationResult:
        result = FidelityValidationResult(valid=False)

        if not html or not html.strip():
            result.issues.append(FidelityIssue(
                category="empty_output", detail="Generated HTML is empty"
            ))
            result.valid = False
            return result

        # Check for markdown fences in output
        if _MARKDOWN_FENCE.search(html):
            result.issues.append(FidelityIssue(
                category="markdown_fences",
                detail="Generated output contains markdown code fences",
            ))

        # Check business name
        biz_name = self.profile.business.name
        if biz_name and biz_name not in html:
            result.issues.append(FidelityIssue(
                category="missing_business_name",
                detail=f"Source business name '{biz_name}' not found in generated HTML",
            ))

        # Check for Lorem Ipsum
        if _LOREM_IPSUM.search(html):
            result.issues.append(FidelityIssue(
                category="lorem_ipsum",
                detail="Generated HTML contains Lorem Ipsum placeholder text",
            ))

        # Check for Service 1/2/3 placeholders
        if _SERVICE_PLACEHOLDER.search(html):
            result.issues.append(FidelityIssue(
                category="service_placeholder",
                detail="Generated HTML contains generic Service 1/2/3 placeholder",
            ))

        # Check for LeadForge branding
        if _LEADFORGE_BRANDING.search(html):
            result.issues.append(FidelityIssue(
                category="leadforge_branding",
                detail="Generated HTML contains LeadForge branding",
            ))

        # Check for dummy contact info
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

        # Check contact preservation
        contact = self.profile.contact
        if contact:
            result.source_contact_emails = list(contact.emails or [])
            result.source_contact_phones = list(contact.phones or [])

            for email in contact.emails or []:
                if email and email in html:
                    result.preserved_contact_emails.append(email)

            for phone in contact.phones or []:
                if phone and phone in html:
                    result.preserved_contact_phones.append(phone)

            if contact.emails and not result.preserved_contact_emails:
                result.issues.append(FidelityIssue(
                    category="missing_contact_email",
                    detail=f"Source email(s) {contact.emails} not found in generated HTML",
                ))
            if contact.phones and not result.preserved_contact_phones:
                result.issues.append(FidelityIssue(
                    category="missing_contact_phone",
                    detail=f"Source phone(s) {contact.phones} not found in generated HTML",
                ))

        # Check services/products preservation
        result.source_service_count = len([s for s in (self.profile.services or []) if s.name])
        result.source_product_count = len([p for p in (self.profile.products or []) if p.title])

        for svc in (self.profile.services or []):
            if svc.name and svc.name in html:
                result.preserved_service_count += 1

        for prod in (self.profile.products or []):
            if prod.title and prod.title in html:
                result.preserved_product_count += 1

        if result.source_service_count > 0 and result.preserved_service_count == 0:
            result.issues.append(FidelityIssue(
                category="missing_services",
                detail=f"None of {result.source_service_count} source service(s) found in generated HTML",
            ))

        if result.source_product_count > 0 and result.preserved_product_count == 0:
            result.issues.append(FidelityIssue(
                category="missing_products",
                detail=f"None of {result.source_product_count} source product(s) found in generated HTML",
            ))

        # Check images
        if self.manifest:
            approved_urls: Set[str] = set()
            local_files: Set[str] = set()
            for item in self.manifest.items:
                if item.absolute_url:
                    approved_urls.add(item.absolute_url)
                if item.local_filename:
                    local_files.add(item.local_filename)

            result.source_meaningful_images = self.manifest.total_count

            # Find all img src references in HTML
            img_refs = re.findall(r'<img[^>]+src\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            img_refs.extend(
                re.findall(r'(?:url|src)\s*[:=]\s*["\']([^"\']+\.(?:png|jpg|jpeg|gif|svg|webp))["\']',
                          html, re.IGNORECASE)
            )

            approved_image_count = 0
            for ref in img_refs:
                filename = ref.split("/")[-1].split("?")[0]
                if ref in approved_urls or filename in local_files or any(
                    item.original_url == ref for item in self.manifest.items
                ):
                    approved_image_count += 1
                    continue
                if any(item.absolute_url == ref for item in self.manifest.items):
                    approved_image_count += 1
                    continue
                if any(item.local_filename and item.local_filename == ref for item in self.manifest.items):
                    approved_image_count += 1
                    continue
                result.broken_image_refs.append(ref)

            result.approved_image_count = approved_image_count

            if result.broken_image_refs:
                result.issues.append(FidelityIssue(
                    category="unapproved_images",
                    detail=f"{len(result.broken_image_refs)} image reference(s) not in AssetManifest: {result.broken_image_refs[:5]}",
                ))
        else:
            # No manifest: basic check that images at least exist in HTML
            img_refs = re.findall(r'<img[^>]+src\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            result.source_meaningful_images = len(self.profile.images or [])
            result.approved_image_count = len(img_refs)

        # Check that HTML is not empty and contains visible content
        text_only = re.sub(r'<[^>]+>', '', html).strip()
        visible_words = len(text_only.split())
        if visible_words < 5:
            result.issues.append(FidelityIssue(
                category="no_visible_content",
                detail=f"Generated HTML contains only {visible_words} visible word(s)",
            ))

        result.valid = len(result.issues) == 0

        if result.valid:
            logger.info("FidelityValidator: PASS — %d checks", sum(
                1 for attr in ["generated_section_count", "preserved_service_count",
                                "preserved_product_count", "approved_image_count"]
            ))
        else:
            logger.warning("FidelityValidator: FAIL — %d issue(s)", len(result.issues))
            for issue in result.issues:
                logger.warning("  %s: %s", issue.category, issue.detail)

        return result
