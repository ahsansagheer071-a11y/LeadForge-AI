import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.exceptions import NotFoundException, ServiceUnavailableException, ValidationException
from app.core.logging import logger
from app.models.lead import Lead
from app.models.user import User
from app.repositories.audit import audit_repository
from app.repositories.lead import lead_repository
from app.schemas.audit import AuditCreate, AuditUpdate, AuditResponse, WebsiteAnalysisResponse

from sqlalchemy.ext.asyncio import AsyncSession

# -------------------------------------------------------
# Constants
# -------------------------------------------------------
DEFAULT_TIMEOUT_SECONDS = 20.0
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB cap
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

# Regex patterns compiled once at module level
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,4}[\s\-.]?)?\(?\d{1,5}\)?[\s\-.]?\d{1,5}[\s\-.]?\d{1,9}",
)

# Social domain → field mapping
SOCIAL_DOMAINS: Dict[str, str] = {
    "facebook.com": "social_facebook",
    "fb.com": "social_facebook",
    "instagram.com": "social_instagram",
    "linkedin.com": "social_linkedin",
    "twitter.com": "social_twitter",
    "x.com": "social_twitter",
    "youtube.com": "social_youtube",
    "youtu.be": "social_youtube",
}


class WebsiteAnalyzerService:
    """
    Async service that downloads a lead's homepage, parses the HTML with
    BeautifulSoup, and extracts structured website intelligence for auditing.
    """

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------
    async def analyze(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        user: User,
    ) -> WebsiteAnalysisResponse:
        """
        Analyse the website of the given lead and persist results into the
        Audit table.  Returns a structured response with all extracted fields.
        """
        logger.info(
            "Website analysis started | lead_id=%s | user_id=%s",
            lead_id,
            user.id,
        )

        # 1. Load the lead
        lead = await lead_repository.get(db, id=lead_id)
        if not lead:
            raise NotFoundException(
                f"Lead with id '{lead_id}' was not found.",
                detail={"lead_id": str(lead_id)},
            )
        if lead.user_id != user.id:
            raise NotFoundException(
                f"Lead with id '{lead_id}' was not found.",
                detail={"lead_id": str(lead_id)},
            )

        # 2. Validate URL
        website_url = self._validate_url(lead.website)

        # 3. Download homepage
        html, status_code, response_time_ms, content_length = await self._fetch_page(website_url)

        # 4. Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # 5. Extract all data
        analysis = self._extract_all(
            soup=soup,
            url=website_url,
            status_code=status_code,
            response_time_ms=response_time_ms,
            content_length=content_length,
        )

        # 6. Persist into the Audit table (create or update)
        existing_audit = await audit_repository.get_by_lead_id(db, lead_id=lead_id)

        if existing_audit:
            await audit_repository.update(db, db_obj=existing_audit, obj_in=analysis)
            logger.info(
                "Audit record updated | lead_id=%s | audit_id=%s",
                lead_id,
                existing_audit.id,
            )
        else:
            audit_create = AuditCreate(lead_id=lead_id, **analysis)
            existing_audit = await audit_repository.create(db, obj_in=audit_create)
            logger.info(
                "Audit record created | lead_id=%s | audit_id=%s",
                lead_id,
                existing_audit.id,
            )

        # 7. Update lead status to ANALYZED
        if lead.status in ("NEW", "SCRAPED"):
            lead.status = "ANALYZED"
            db.add(lead)
            await db.flush()

        # 8. Build response
        response = WebsiteAnalysisResponse(
            lead_id=lead_id,
            website_url=website_url,
            page_title=analysis.get("website_title"),
            meta_description=analysis.get("meta_description"),
            website_language=analysis.get("website_language"),
            https_enabled=analysis.get("https_enabled", False),
            http_status_code=analysis.get("http_status_code"),
            h1_count=analysis.get("h1_count", 0),
            h2_count=analysis.get("h2_count", 0),
            total_paragraphs=analysis.get("total_paragraphs", 0),
            total_images=analysis.get("total_images", 0),
            total_forms=analysis.get("total_forms", 0),
            emails=analysis.get("emails", []),
            phone_numbers=analysis.get("phone_numbers", []),
            contact_page_exists=analysis.get("contact_page_exists", False),
            about_page_exists=analysis.get("about_page_exists", False),
            social_facebook=analysis.get("social_facebook"),
            social_instagram=analysis.get("social_instagram"),
            social_linkedin=analysis.get("social_linkedin"),
            social_twitter=analysis.get("social_twitter"),
            social_youtube=analysis.get("social_youtube"),
            missing_meta_description=analysis.get("missing_meta_description", False),
            missing_h1=analysis.get("missing_h1", False),
            missing_title=analysis.get("missing_title", False),
            html_size_kb=analysis.get("html_size_kb"),
            response_time_ms=analysis.get("response_time_ms"),
        )

        logger.info(
            "Website analysis completed | lead_id=%s | url=%s | status=%s",
            lead_id,
            website_url,
            status_code,
        )
        return response

    # ------------------------------------------------------------------
    # URL validation
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_url(website: Optional[str]) -> str:
        """Ensure the lead has a usable website URL."""
        if not website or not website.strip():
            raise ValidationException(
                "This lead does not have a website URL to analyze.",
            )

        url = website.strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValidationException(
                f"The URL '{website}' is not a valid web address.",
                detail={"url": website},
            )
        return url

    # ------------------------------------------------------------------
    # HTTP fetch
    # ------------------------------------------------------------------
    async def _fetch_page(
        self, url: str
    ) -> Tuple[str, int, float, int]:
        """
        Download the homepage and return (html, status_code, response_time_ms,
        content_length_bytes).
        """
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            start = time.perf_counter()
            async with httpx.AsyncClient(
                timeout=DEFAULT_TIMEOUT_SECONDS,
                follow_redirects=True,
                max_redirects=5,
            ) as client:
                response = await client.get(url, headers=headers)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

            content_bytes = len(response.content)
            if content_bytes > MAX_CONTENT_LENGTH:
                logger.warning(
                    "Page content exceeds 10 MB limit | url=%s | size=%s bytes",
                    url,
                    content_bytes,
                )

            html = response.text
            return html, response.status_code, elapsed_ms, content_bytes

        except httpx.TimeoutException as exc:
            logger.error("Website fetch timed out | url=%s", url)
            raise ServiceUnavailableException(
                f"The website at '{url}' did not respond within {DEFAULT_TIMEOUT_SECONDS}s.",
                detail={"url": url},
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Website fetch failed | url=%s | error=%s", url, str(exc))
            raise ServiceUnavailableException(
                f"Unable to reach the website at '{url}'.",
                detail={"url": url, "error": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Master extraction method
    # ------------------------------------------------------------------
    def _extract_all(
        self,
        *,
        soup: BeautifulSoup,
        url: str,
        status_code: int,
        response_time_ms: float,
        content_length: int,
    ) -> Dict[str, Any]:
        """Run every extractor and return a flat dict matching Audit columns."""

        title = self._extract_title(soup)
        meta_desc = self._extract_meta_description(soup)
        language = self._extract_language(soup)
        h1s = soup.find_all("h1")
        h2s = soup.find_all("h2")

        emails = self._extract_emails(soup)
        phones = self._extract_phones(soup)
        socials = self._extract_social_links(soup)
        contact_page, about_page = self._detect_navigation_pages(soup, url)

        return {
            # General
            "website_title": title,
            "meta_description": meta_desc,
            "website_language": language,
            "https_enabled": url.lower().startswith("https://"),
            "http_status_code": status_code,
            "ssl_status": url.lower().startswith("https://"),

            # Content counts
            "h1_count": len(h1s),
            "h2_count": len(h2s),
            "total_paragraphs": len(soup.find_all("p")),
            "total_images": len(soup.find_all("img")),
            "total_forms": len(soup.find_all("form")),

            # Business info
            "emails": emails,
            "phone_numbers": phones,
            "contact_form_present": len(soup.find_all("form")) > 0,

            # Navigation
            "contact_page_exists": contact_page,
            "about_page_exists": about_page,

            # Social presence
            **socials,

            # SEO flags
            "missing_title": not bool(title),
            "missing_meta_description": not bool(meta_desc),
            "missing_h1": len(h1s) == 0,

            # Performance
            "html_size_kb": round(content_length / 1024, 2),
            "response_time_ms": response_time_ms,
        }

    # ------------------------------------------------------------------
    # Individual extractors
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> Optional[str]:
        tag = soup.find("title")
        if tag and tag.string:
            return tag.string.strip()[:500]
        return None

    @staticmethod
    def _extract_meta_description(soup: BeautifulSoup) -> Optional[str]:
        tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()[:1000]
        return None

    @staticmethod
    def _extract_language(soup: BeautifulSoup) -> Optional[str]:
        html_tag = soup.find("html")
        if html_tag:
            lang = html_tag.get("lang") or html_tag.get("xml:lang")
            if lang:
                return str(lang).strip()[:20]
        meta_lang = soup.find("meta", attrs={"http-equiv": re.compile(r"^content-language$", re.I)})
        if meta_lang and meta_lang.get("content"):
            return str(meta_lang["content"]).strip()[:20]
        return None

    @staticmethod
    def _extract_emails(soup: BeautifulSoup) -> List[str]:
        text = soup.get_text(separator=" ", strip=True)
        # Also check mailto links
        mailto_emails = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0].strip()
                if email:
                    mailto_emails.add(email.lower())

        body_emails = set(EMAIL_REGEX.findall(text))
        all_emails = mailto_emails | {e.lower() for e in body_emails}

        # Filter out common false positives
        filtered = [
            e for e in sorted(all_emails)
            if not e.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js"))
            and "@" in e
        ]
        return filtered[:20]  # cap at 20

    @staticmethod
    def _extract_phones(soup: BeautifulSoup) -> List[str]:
        phones: set = set()
        # tel: links first (most reliable)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("tel:"):
                phone = href.replace("tel:", "").strip()
                if phone and len(phone) >= 7:
                    phones.add(phone)

        # Regex fallback on visible text
        text = soup.get_text(separator=" ", strip=True)
        for match in PHONE_REGEX.findall(text):
            cleaned = match.strip()
            # Only keep values that look like real phone numbers (7+ digits)
            digits_only = re.sub(r"\D", "", cleaned)
            if 7 <= len(digits_only) <= 15:
                phones.add(cleaned)

        return sorted(phones)[:10]  # cap at 10

    @staticmethod
    def _extract_social_links(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Return dict with keys social_facebook, social_instagram, etc."""
        result: Dict[str, Optional[str]] = {
            "social_facebook": None,
            "social_instagram": None,
            "social_linkedin": None,
            "social_twitter": None,
            "social_youtube": None,
        }
        seen_fields: set = set()

        for a_tag in soup.find_all("a", href=True):
            href = str(a_tag["href"]).strip()
            if not href.startswith(("http://", "https://")):
                continue
            try:
                domain = urlparse(href).netloc.lower().lstrip("www.")
            except Exception:
                continue

            for social_domain, field_name in SOCIAL_DOMAINS.items():
                if social_domain in domain and field_name not in seen_fields:
                    result[field_name] = href
                    seen_fields.add(field_name)

            if len(seen_fields) == 5:
                break  # all found

        return result

    @staticmethod
    def _detect_navigation_pages(
        soup: BeautifulSoup, base_url: str
    ) -> Tuple[bool, bool]:
        """Detect whether contact and about pages exist from anchor links."""
        contact_found = False
        about_found = False

        contact_patterns = re.compile(r"\bcontact\b", re.I)
        about_patterns = re.compile(r"\babout\b", re.I)

        for a_tag in soup.find_all("a", href=True):
            href = str(a_tag["href"]).lower()
            text = (a_tag.get_text() or "").lower()

            if not contact_found and (contact_patterns.search(href) or contact_patterns.search(text)):
                contact_found = True
            if not about_found and (about_patterns.search(href) or about_patterns.search(text)):
                about_found = True

            if contact_found and about_found:
                break

        return contact_found, about_found


# Module-level singleton
website_analyzer_service = WebsiteAnalyzerService()
