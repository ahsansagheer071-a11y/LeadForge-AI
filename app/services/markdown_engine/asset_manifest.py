import asyncio
import hashlib
import logging
import mimetypes
import os
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
from uuid import uuid4

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.services.website_intelligence.schemas import (
    WebsiteProfile,
    ImageAsset,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_DOWNLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
DOWNLOAD_TIMEOUT_SECONDS = 30
VALID_IMAGE_MIMETYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "image/avif",
    "image/bmp",
    "image/tiff",
    "image/x-icon",
    "image/vnd.microsoft.icon",
}

TINY_DIMENSION_THRESHOLD = 16  # px — images smaller than this on both axes are filtered
TRACKING_PATTERNS = re.compile(
    r"(track(ing)?|pixel|analytics|beacon|spacer|clear\.gif|1x1|blank)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AssetRole(str, Enum):
    LOGO = "logo"
    HERO = "hero"
    SERVICE = "service"
    PRODUCT = "product"
    TEAM = "team"
    TESTIMONIAL = "testimonial"
    GALLERY = "gallery"
    BACKGROUND = "background"
    FAVICON = "favicon"
    OTHER = "other"


class DownloadStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    SKIPPED = "skipped"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class AssetManifestItem(BaseModel):
    original_url: str
    absolute_url: str
    local_filename: Optional[str] = None
    alt_text: Optional[str] = None
    role: AssetRole = AssetRole.OTHER
    source_section: Optional[str] = None
    related_item_name: Optional[str] = None
    source_page: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    download_status: DownloadStatus = DownloadStatus.PENDING
    failure_reason: Optional[str] = None
    sha256_hash: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


class AssetManifest(BaseModel):
    items: List[AssetManifestItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_url: Optional[str] = None
    total_count: int = 0
    logo_count: int = 0
    hero_count: int = 0
    service_count: int = 0
    product_count: int = 0
    testimonial_count: int = 0
    team_count: int = 0
    other_count: int = 0
    unassigned_count: int = 0
    downloaded_count: int = 0
    failed_count: int = 0
    duplicate_count_removed: int = 0

    model_config = ConfigDict(use_enum_values=True)


# ---------------------------------------------------------------------------
# Manifest Builder
# ---------------------------------------------------------------------------

class ManifestBuilder:
    """Extracts, deduplicates, and maps images from a WebsiteProfile."""

    def __init__(self, profile: WebsiteProfile) -> None:
        self.profile = profile
        self._base_url = self._resolve_base_url()

    def _resolve_base_url(self) -> str:
        biz = self.profile.business
        if biz and biz.website_url:
            return str(biz.website_url).rstrip("/") + "/"
        return ""

    def normalize_url(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        url = str(url).strip()
        if not url or url.startswith("data:"):
            return None
        if not self._base_url:
            return url
        if url.startswith("http://") or url.startswith("https://"):
            return url
        return urljoin(self._base_url, url)

    def _is_tracking_or_tiny(self, url: str, width: Optional[int], height: Optional[int]) -> bool:
        if width is not None and height is not None:
            if width < TINY_DIMENSION_THRESHOLD and height < TINY_DIMENSION_THRESHOLD:
                return True
        if TRACKING_PATTERNS.search(url):
            return True
        parsed = urlparse(url)
        path = parsed.path.lower()
        if TRACKING_PATTERNS.search(path):
            return True
        filename = os.path.basename(parsed.path).lower()
        if TRACKING_PATTERNS.search(filename):
            return True
        return False

    def build(self) -> AssetManifest:
        bp = self.profile
        biz = bp.business
        hero_info = bp.hero_info
        wl = bp.website_layout
        logo_info = bp.brand.logo_info if bp.brand else None
        footer = wl.footer_info if wl else None

        url_contexts: Dict[str, List[Dict[str, Any]]] = {}
        seen_extracted: Set[str] = set()

        def record(url: Optional[str], role: AssetRole, section: Optional[str] = None, item_name: Optional[str] = None):
            abs_url = self.normalize_url(url)
            if not abs_url:
                return
            if abs_url not in url_contexts:
                url_contexts[abs_url] = []
            url_contexts[abs_url].append({
                "role": role,
                "section": section,
                "item_name": item_name,
            })

        # -- Business logo & favicon --
        if biz:
            record(biz.logo, AssetRole.LOGO)
            record(biz.favicon, AssetRole.FAVICON)

        # -- LogoInfo --
        if logo_info and logo_info.logo_url:
            record(logo_info.logo_url, AssetRole.LOGO)

        # -- Hero --
        if hero_info:
            record(hero_info.hero_image, AssetRole.HERO, "hero")
            record(hero_info.background_image_url, AssetRole.BACKGROUND, "hero")

        # -- Services --
        if bp.services:
            for svc in bp.services:
                record(svc.image, AssetRole.SERVICE, "services", svc.name)

        # -- Products --
        if bp.products:
            for prod in bp.products:
                record(prod.image, AssetRole.PRODUCT, "products", prod.title)

        # -- Testimonials --
        if bp.testimonials:
            for t in bp.testimonials:
                author = t.author_name or t.author or ""
                record(t.avatar, AssetRole.TESTIMONIAL, "testimonials", author)
                record(t.avatar_url, AssetRole.TESTIMONIAL, "testimonials", author)

        # -- Team --
        if bp.team:
            for m in bp.team:
                name = m.full_name or m.name or ""
                record(m.image, AssetRole.TEAM, "team", name)
                record(m.photo_url, AssetRole.TEAM, "team", name)

        # -- Footer logo --
        if footer:
            record(footer.footer_logo, AssetRole.LOGO, "footer")

        # -- Section images from WebsiteLayout --
        if wl and wl.sections:
            for sec in wl.sections:
                if sec.images:
                    for img_url in sec.images:
                        section_role = {
                            "hero": AssetRole.HERO,
                            "services": AssetRole.SERVICE,
                            "products": AssetRole.PRODUCT,
                            "testimonials": AssetRole.TESTIMONIAL,
                            "team": AssetRole.TEAM,
                            "about": AssetRole.GALLERY,
                            "contact": AssetRole.GALLERY,
                            "footer": AssetRole.GALLERY,
                        }.get(sec.section_type or "", AssetRole.GALLERY)
                        record(img_url, section_role, sec.section_type)

        # -- ImageAsset list (the raw extracted images) --
        existing_assets: Dict[str, ImageAsset] = {}
        if bp.images:
            for img in bp.images:
                abs_url = self.normalize_url(img.url)
                if abs_url:
                    existing_assets[abs_url] = img
                    if abs_url not in url_contexts:
                        url_contexts[abs_url] = []

        # -- Build items --
        items: List[AssetManifestItem] = []
        seen_urls_for_dedup: Set[str] = set()
        duplicate_count = 0

        for abs_url, contexts in url_contexts.items():
            if abs_url in seen_urls_for_dedup:
                duplicate_count += 1
                continue

            # Check if tracking/tiny
            existing = existing_assets.get(abs_url)
            is_logo = any(ctx["role"] == AssetRole.LOGO for ctx in contexts)
            w = existing.width if existing else None
            h = existing.height if existing else None

            if not is_logo and self._is_tracking_or_tiny(abs_url, w, h):
                duplicate_count += 1
                continue

            seen_urls_for_dedup.add(abs_url)

            # Decide best role (priority: logo > hero > service > product > testimonial > team > background > gallery > other)
            if not contexts:
                role = AssetRole.OTHER
                section = None
                item_name = None
            else:
                role_priority = {
                    AssetRole.LOGO: 0,
                    AssetRole.FAVICON: 1,
                    AssetRole.HERO: 2,
                    AssetRole.SERVICE: 3,
                    AssetRole.PRODUCT: 4,
                    AssetRole.TESTIMONIAL: 5,
                    AssetRole.TEAM: 6,
                    AssetRole.BACKGROUND: 7,
                    AssetRole.GALLERY: 8,
                    AssetRole.OTHER: 9,
                }
                best_context = min(contexts, key=lambda c: role_priority.get(c["role"], 99))
                role = best_context["role"]
                section = best_context.get("section")
                item_name = best_context.get("item_name")

            # If section is None but we have a role-specific section
            if section is None:
                section_map = {
                    AssetRole.HERO: "hero",
                    AssetRole.SERVICE: "services",
                    AssetRole.PRODUCT: "products",
                    AssetRole.TESTIMONIAL: "testimonials",
                    AssetRole.TEAM: "team",
                    AssetRole.LOGO: None,
                    AssetRole.FAVICON: None,
                    AssetRole.BACKGROUND: None,
                    AssetRole.GALLERY: None,
                }
                section = section_map.get(role)

            # Only set related_item_name if we're confident
            if not item_name and role in (AssetRole.SERVICE, AssetRole.PRODUCT, AssetRole.TESTIMONIAL, AssetRole.TEAM) and len(contexts) == 1:
                pass  # no item name available from non-item contexts

            alt_text = existing.alt if existing else None

            items.append(AssetManifestItem(
                original_url=abs_url,
                absolute_url=abs_url,
                alt_text=alt_text,
                role=role,
                source_section=section,
                related_item_name=item_name,
                source_page=self._base_url.rstrip("/") if self._base_url else None,
                width=w,
                height=h,
            ))

        # -- Count stats --
        logo_count = sum(1 for i in items if i.role == AssetRole.LOGO)
        hero_count = sum(1 for i in items if i.role == AssetRole.HERO)
        service_count = sum(1 for i in items if i.role == AssetRole.SERVICE)
        product_count = sum(1 for i in items if i.role == AssetRole.PRODUCT)
        testimonial_count = sum(1 for i in items if i.role == AssetRole.TESTIMONIAL)
        team_count = sum(1 for i in items if i.role == AssetRole.TEAM)
        other_count = sum(1 for i in items if i.role in (AssetRole.GALLERY, AssetRole.BACKGROUND, AssetRole.FAVICON, AssetRole.OTHER))
        unassigned_count = sum(1 for i in items if not i.source_section)

        return AssetManifest(
            items=items,
            source_url=self._base_url.rstrip("/") if self._base_url else None,
            total_count=len(items),
            logo_count=logo_count,
            hero_count=hero_count,
            service_count=service_count,
            product_count=product_count,
            testimonial_count=testimonial_count,
            team_count=team_count,
            other_count=other_count,
            unassigned_count=unassigned_count,
            duplicate_count_removed=duplicate_count,
        )


# ---------------------------------------------------------------------------
# Image Downloader
# ---------------------------------------------------------------------------

class ImageDownloader:
    """Downloads images from an AssetManifest to a local workspace."""

    def __init__(self, workspace_dir: str, timeout: float = DOWNLOAD_TIMEOUT_SECONDS):
        self.workspace_dir = workspace_dir
        self.timeout = timeout
        self._used_filenames: Set[str] = set()

    def _sanitize_filename(self, url: str) -> str:
        parsed = urlparse(url)
        base = os.path.basename(parsed.path)
        if not base or "." not in base:
            ext = mimetypes.guess_extension(parsed.path) or ".jpg"
            base = f"image{ext}"
        name, ext = os.path.splitext(base)
        name = re.sub(r"[^\w\-]", "_", name)[:80]
        ext = ext.split("?")[0][:10]
        return f"{name}{ext}"

    def _unique_filename(self, url: str) -> str:
        base = self._sanitize_filename(url)
        if base not in self._used_filenames:
            self._used_filenames.add(base)
            return base
        name, ext = os.path.splitext(base)
        for i in range(1, 100):
            candidate = f"{name}_{i}{ext}"
            if candidate not in self._used_filenames:
                self._used_filenames.add(candidate)
                return candidate
        return f"{uuid4().hex}{ext}"

    async def download_all(self, manifest: AssetManifest, client: Optional[httpx.AsyncClient] = None) -> AssetManifest:
        os.makedirs(self.workspace_dir, exist_ok=True)
        should_close = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout), follow_redirects=True)

        try:
            for item in manifest.items:
                try:
                    url = item.absolute_url
                    if not url.startswith("http://") and not url.startswith("https://"):
                        item.download_status = DownloadStatus.SKIPPED
                        item.failure_reason = "Not an HTTP(S) URL"
                        continue

                    resp = await client.get(url, timeout=self.timeout)
                    resp.raise_for_status()

                    content_type = resp.headers.get("content-type", "").split(";")[0].strip()
                    if content_type not in VALID_IMAGE_MIMETYPES and not content_type.startswith("image/"):
                        item.download_status = DownloadStatus.SKIPPED
                        item.failure_reason = f"Invalid content type: {content_type}"
                        continue

                    body = resp.content
                    if len(body) > MAX_DOWNLOAD_SIZE_BYTES:
                        item.download_status = DownloadStatus.SKIPPED
                        item.failure_reason = f"File too large: {len(body)} bytes"
                        continue

                    if len(body) < 100:
                        item.download_status = DownloadStatus.SKIPPED
                        item.failure_reason = "File too small (likely placeholder)"
                        continue

                    filename = self._unique_filename(url)
                    filepath = os.path.join(self.workspace_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(body)

                    item.local_filename = filename
                    item.download_status = DownloadStatus.DOWNLOADED
                    item.sha256_hash = hashlib.sha256(body).hexdigest()

                except Exception as exc:
                    item.download_status = DownloadStatus.FAILED
                    item.failure_reason = f"{type(exc).__name__}: {exc}"
                    logger.debug("Failed to download %s: %s", item.absolute_url, exc)
        finally:
            if should_close:
                await client.aclose()

        manifest.downloaded_count = sum(1 for i in manifest.items if i.download_status == DownloadStatus.DOWNLOADED)
        manifest.failed_count = sum(1 for i in manifest.items if i.download_status == DownloadStatus.FAILED)
        return manifest

    def download_all_sync(self, manifest: AssetManifest) -> AssetManifest:
        import asyncio
        return asyncio.run(self.download_all(manifest))
