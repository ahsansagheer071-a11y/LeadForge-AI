"""Tests for the Asset Manifest Builder and Image Downloader."""

import json
import os
import tempfile
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.markdown_engine.asset_manifest import (
    AssetManifest,
    AssetManifestItem,
    AssetRole,
    DownloadStatus,
    ImageDownloader,
    ManifestBuilder,
)
from app.services.markdown_engine.source_content import (
    SourceWebsiteSnapshot,
    format_source_content,
)
from app.services.website_intelligence.schemas import (
    BrandIdentity,
    BusinessInfo,
    CallToAction,
    CompanySection,
    ContactInfo,
    FAQ,
    FooterInfo,
    HeroInfo,
    ImageAsset,
    LogoInfo,
    NavItem,
    NavigationInfo,
    ProductItem,
    SectionInfo,
    ServiceCard,
    SocialLink,
    TeamMember,
    Testimonial,
    WebsiteLayout,
    WebsiteProfile,
)


# ======================================================================
# Helpers
# ======================================================================

def make_profile(**overrides: Any) -> WebsiteProfile:
    return WebsiteProfile(**overrides)


def make_builder(profile: WebsiteProfile) -> ManifestBuilder:
    return ManifestBuilder(profile)


# ======================================================================
# URL Normalization
# ======================================================================

class TestURLNormalization:
    def test_absolute_url_unchanged(self):
        bp = make_profile(business=BusinessInfo(website_url="https://example.com"))
        builder = make_builder(bp)
        assert builder.normalize_url("https://example.com/image.jpg") == "https://example.com/image.jpg"

    def test_relative_url_resolved(self):
        bp = make_profile(business=BusinessInfo(website_url="https://example.com"))
        builder = make_builder(bp)
        assert builder.normalize_url("/images/logo.png") == "https://example.com/images/logo.png"

    def test_relative_without_slash(self):
        bp = make_profile(business=BusinessInfo(website_url="https://example.com"))
        builder = make_builder(bp)
        result = builder.normalize_url("images/logo.png")
        assert result == "https://example.com/images/logo.png"

    def test_data_url_returns_none(self):
        bp = make_profile(business=BusinessInfo(website_url="https://example.com"))
        builder = make_builder(bp)
        assert builder.normalize_url("data:image/png;base64,abc123") is None

    def test_none_returns_none(self):
        bp = make_profile(business=BusinessInfo(website_url="https://example.com"))
        builder = make_builder(bp)
        assert builder.normalize_url(None) is None

    def test_empty_string_returns_none(self):
        bp = make_profile(business=BusinessInfo(website_url="https://example.com"))
        builder = make_builder(bp)
        assert builder.normalize_url("") is None

    def test_no_website_url_preserves_relative(self):
        bp = make_profile()
        builder = make_builder(bp)
        assert builder.normalize_url("/images/logo.png") == "/images/logo.png"


# ======================================================================
# Logo Extraction and Preservation
# ======================================================================

class TestLogoPreservation:
    def test_business_logo_mapped_as_logo(self):
        bp = make_profile(business=BusinessInfo(logo="https://example.com/logo.png"))
        manifest = make_builder(bp).build()
        assert manifest.logo_count >= 1
        logo_items = [i for i in manifest.items if i.role == AssetRole.LOGO]
        assert len(logo_items) >= 1
        assert logo_items[0].absolute_url == "https://example.com/logo.png"

    def test_logo_info_mapped_as_logo(self):
        bp = make_profile(
            business=BusinessInfo(website_url="https://example.com"),
            brand=BrandIdentity(logo_info=LogoInfo(logo_url="https://example.com/brand.svg")),
        )
        manifest = make_builder(bp).build()
        logo_items = [i for i in manifest.items if i.role == AssetRole.LOGO]
        assert len(logo_items) >= 1
        assert logo_items[0].absolute_url == "https://example.com/brand.svg"

    def test_favicon_mapped_as_favicon(self):
        bp = make_profile(business=BusinessInfo(favicon="https://example.com/favicon.ico"))
        manifest = make_builder(bp).build()
        fav_items = [i for i in manifest.items if i.role == AssetRole.FAVICON]
        assert len(fav_items) >= 1

    def test_small_logo_not_filtered(self):
        bp = make_profile(
            business=BusinessInfo(logo="https://example.com/logo.png"),
            images=[ImageAsset(url="https://example.com/logo.png", width=16, height=16)],
        )
        manifest = make_builder(bp).build()
        logo_items = [i for i in manifest.items if i.role == AssetRole.LOGO]
        assert len(logo_items) >= 1


# ======================================================================
# Section Mapping
# ======================================================================

class TestSectionMapping:
    def test_hero_image_maps_to_hero(self):
        bp = make_profile(
            hero_info=HeroInfo(hero_image="https://example.com/hero.jpg"),
        )
        manifest = make_builder(bp).build()
        hero_items = [i for i in manifest.items if i.role == AssetRole.HERO]
        assert len(hero_items) >= 1
        assert hero_items[0].source_section == "hero"

    def test_hero_background_maps_to_background(self):
        bp = make_profile(
            hero_info=HeroInfo(background_image_url="https://example.com/bg.jpg"),
        )
        manifest = make_builder(bp).build()
        bg_items = [i for i in manifest.items if i.role == AssetRole.BACKGROUND]
        assert len(bg_items) >= 1

    def test_service_image_maps_to_services(self):
        bp = make_profile(
            services=[ServiceCard(name="Web Dev", image="https://example.com/webdev.jpg")],
        )
        manifest = make_builder(bp).build()
        svc_items = [i for i in manifest.items if i.role == AssetRole.SERVICE]
        assert len(svc_items) >= 1
        assert svc_items[0].source_section == "services"
        assert svc_items[0].related_item_name == "Web Dev"

    def test_product_image_maps_to_products(self):
        bp = make_profile(
            products=[ProductItem(title="Widget", image="https://example.com/widget.png")],
        )
        manifest = make_builder(bp).build()
        prod_items = [i for i in manifest.items if i.role == AssetRole.PRODUCT]
        assert len(prod_items) >= 1
        assert prod_items[0].source_section == "products"
        assert prod_items[0].related_item_name == "Widget"

    def test_testimonial_avatar_maps_to_testimonials(self):
        bp = make_profile(
            testimonials=[Testimonial(content="Great!", avatar="https://example.com/avatar.jpg", author_name="Alice")],
        )
        manifest = make_builder(bp).build()
        test_items = [i for i in manifest.items if i.role == AssetRole.TESTIMONIAL]
        assert len(test_items) >= 1
        assert test_items[0].source_section == "testimonials"

    def test_team_photo_maps_to_team(self):
        bp = make_profile(
            team=[TeamMember(name="Bob", photo_url="https://example.com/bob.jpg")],
        )
        manifest = make_builder(bp).build()
        team_items = [i for i in manifest.items if i.role == AssetRole.TEAM]
        assert len(team_items) >= 1
        assert team_items[0].source_section == "team"

    def test_footer_logo_maps_to_logo_footer(self):
        bp = make_profile(
            website_layout=WebsiteLayout(
                footer_info=FooterInfo(footer_logo="https://example.com/footer-logo.png"),
            ),
        )
        manifest = make_builder(bp).build()
        logo_items = [i for i in manifest.items if i.role == AssetRole.LOGO]
        assert len(logo_items) >= 1
        assert logo_items[0].source_section == "footer"


# ======================================================================
# Uncertain Mapping
# ======================================================================

class TestUncertainMapping:
    def test_image_only_in_raw_list_is_unassigned(self):
        bp = make_profile(
            business=BusinessInfo(website_url="https://example.com"),
            images=[ImageAsset(url="https://example.com/mystery.jpg")],
        )
        manifest = make_builder(bp).build()
        unassigned = [i for i in manifest.items if i.source_section is None]
        assert len(unassigned) >= 1


# ======================================================================
# Deduplication
# ======================================================================

class TestDeduplication:
    def test_duplicate_urls_deduplicated(self):
        bp = make_profile(
            business=BusinessInfo(logo="https://example.com/logo.png"),
            hero_info=HeroInfo(hero_image="https://example.com/hero.jpg"),
            images=[
                ImageAsset(url="https://example.com/logo.png"),
                ImageAsset(url="https://example.com/hero.jpg"),
                ImageAsset(url="https://example.com/logo.png"),
            ],
        )
        manifest = make_builder(bp).build()
        urls = [i.absolute_url for i in manifest.items]
        assert len(urls) == len(set(urls))
        assert len(manifest.items) == 2


# ======================================================================
# Tracking / Tiny Image Filtering
# ======================================================================

class TestTrackingTinyFilter:
    def test_tracking_pixel_filtered(self):
        bp = make_profile(
            business=BusinessInfo(website_url="https://example.com"),
            images=[ImageAsset(url="https://example.com/track/pixel.gif")],
        )
        manifest = make_builder(bp).build()
        assert len(manifest.items) == 0

    def test_tiny_image_filtered(self):
        bp = make_profile(
            business=BusinessInfo(website_url="https://example.com"),
            images=[ImageAsset(url="https://example.com/spacer.gif", width=1, height=1)],
        )
        manifest = make_builder(bp).build()
        assert len(manifest.items) == 0

    def test_large_image_not_filtered(self):
        bp = make_profile(
            business=BusinessInfo(website_url="https://example.com"),
            images=[ImageAsset(url="https://example.com/photo.jpg", width=800, height=600)],
        )
        manifest = make_builder(bp).build()
        assert len(manifest.items) == 1

    def test_tracking_url_with_analytics_filtered(self):
        bp = make_profile(
            business=BusinessInfo(website_url="https://example.com"),
            images=[ImageAsset(url="https://example.com/analytics/beacon.gif")],
        )
        manifest = make_builder(bp).build()
        assert len(manifest.items) == 0


# ======================================================================
# Full Profile Build
# ======================================================================

class TestFullBuild:
    def test_empty_profile_returns_empty_manifest(self):
        bp = make_profile()
        manifest = make_builder(bp).build()
        assert manifest.total_count == 0
        assert manifest.items == []

    def test_all_roles_represented(self):
        bp = make_profile(
            business=BusinessInfo(logo="https://example.com/logo.png"),
            hero_info=HeroInfo(hero_image="https://example.com/hero.jpg"),
            services=[ServiceCard(name="Dev", image="https://example.com/dev.jpg")],
            products=[ProductItem(title="Widget", image="https://example.com/widget.png")],
            testimonials=[Testimonial(content="Nice!", avatar="https://example.com/avatar.jpg")],
            team=[TeamMember(name="Alice", photo_url="https://example.com/alice.jpg")],
            website_layout=WebsiteLayout(
                footer_info=FooterInfo(footer_logo="https://example.com/footer.png"),
            ),
        )
        manifest = make_builder(bp).build()
        assert manifest.logo_count >= 1
        assert manifest.hero_count >= 1
        assert manifest.service_count >= 1
        assert manifest.product_count >= 1
        assert manifest.testimonial_count >= 1
        assert manifest.team_count >= 1

    def test_json_serialization(self):
        bp = make_profile(
            business=BusinessInfo(logo="https://example.com/logo.png"),
        )
        manifest = make_builder(bp).build()
        data = json.loads(manifest.model_dump_json())
        assert "items" in data
        assert data["total_count"] == 1
        assert data["items"][0]["role"] == "logo"

    def test_manifest_in_format_source_content(self):
        bp = make_profile(
            business=BusinessInfo(name="TestCo", logo="https://example.com/logo.png"),
            hero_info=HeroInfo(hero_image="https://example.com/hero.jpg"),
        )
        manifest = make_builder(bp).build()
        snapshot = SourceWebsiteSnapshot.from_profile(bp)
        md = format_source_content(snapshot, manifest=manifest)
        assert "## Hero Images" in md
        assert "## Approved Asset Manifest" in md
        assert "https://example.com/hero.jpg" in md
        assert "https://example.com/logo.png" in md
        # No LeadForge footer branding
        assert "Generated by LeadForge" not in md


# ======================================================================
# Image Downloader
# ======================================================================

class TestImageDownloader:
    def test_sanitize_filename_removes_query_strings(self):
        downloader = ImageDownloader(workspace_dir="/tmp")
        name = downloader._sanitize_filename("https://example.com/image.jpg?w=800")
        assert name == "image.jpg"

    def test_sanitize_filename_handles_no_extension(self):
        downloader = ImageDownloader(workspace_dir="/tmp")
        name = downloader._sanitize_filename("https://example.com/photo")
        assert "jpg" in name or "jpeg" in name or "png" in name

    def test_unique_filename_collision(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(workspace_dir=tmpdir)
            name1 = downloader._unique_filename("https://example.com/image.jpg")
            name2 = downloader._unique_filename("https://example.com/image.jpg")
            assert name1 != name2

    @pytest.mark.asyncio
    async def test_successful_download(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(workspace_dir=tmpdir)
            manifest = AssetManifest(items=[
                AssetManifestItem(
                    original_url="https://example.com/photo.jpg",
                    absolute_url="https://example.com/photo.jpg",
                ),
            ])
            mock_client = AsyncMock(spec=httpx.AsyncClient)
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.content = b"A" * 200
            mock_client.get.return_value = mock_response

            result = await downloader.download_all(manifest, client=mock_client)
            assert result.items[0].download_status == DownloadStatus.DOWNLOADED
            assert result.items[0].local_filename is not None
            filepath = os.path.join(tmpdir, result.items[0].local_filename)
            assert os.path.exists(filepath)

    @pytest.mark.asyncio
    async def test_failed_download(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(workspace_dir=tmpdir)
            manifest = AssetManifest(items=[
                AssetManifestItem(
                    original_url="https://example.com/missing.jpg",
                    absolute_url="https://example.com/missing.jpg",
                ),
            ])
            mock_client = AsyncMock(spec=httpx.AsyncClient)
            mock_client.get.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=MagicMock(), response=MagicMock(status_code=404)
            )

            result = await downloader.download_all(manifest, client=mock_client)
            assert result.items[0].download_status == DownloadStatus.FAILED
            assert result.failed_count == 1

    @pytest.mark.asyncio
    async def test_invalid_content_type_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(workspace_dir=tmpdir)
            manifest = AssetManifest(items=[
                AssetManifestItem(
                    original_url="https://example.com/file.pdf",
                    absolute_url="https://example.com/file.pdf",
                ),
            ])
            mock_client = AsyncMock(spec=httpx.AsyncClient)
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/pdf"}
            mock_response.content = b"A" * 200
            mock_client.get.return_value = mock_response

            result = await downloader.download_all(manifest, client=mock_client)
            assert result.items[0].download_status == DownloadStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_too_large_file_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ImageDownloader(workspace_dir=tmpdir)
            manifest = AssetManifest(items=[
                AssetManifestItem(
                    original_url="https://example.com/huge.jpg",
                    absolute_url="https://example.com/huge.jpg",
                ),
            ])
            mock_client = AsyncMock(spec=httpx.AsyncClient)
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "image/jpeg"}
            from app.services.markdown_engine.asset_manifest import MAX_DOWNLOAD_SIZE_BYTES
            mock_response.content = b"x" * (MAX_DOWNLOAD_SIZE_BYTES + 1)
            mock_client.get.return_value = mock_response

            result = await downloader.download_all(manifest, client=mock_client)
            assert result.items[0].download_status == DownloadStatus.SKIPPED


# ======================================================================
# Markdown Contains Section Assets
# ======================================================================

class TestMarkdownSectionAssets:
    def test_markdown_contains_section_images(self):
        bp = make_profile(
            business=BusinessInfo(website_url="https://example.com"),
            services=[ServiceCard(name="Web Dev", image="https://example.com/webdev.jpg")],
            team=[TeamMember(name="Alice", photo_url="https://example.com/alice.jpg")],
        )
        manifest = make_builder(bp).build()
        snapshot = SourceWebsiteSnapshot.from_profile(bp)
        md = format_source_content(snapshot, manifest=manifest)
        assert "## Services Images" in md
        assert "## Team Images" in md
        assert "https://example.com/webdev.jpg" in md
        assert "https://example.com/alice.jpg" in md

    def test_markdown_approved_asset_manifest_section(self):
        bp = make_profile(
            business=BusinessInfo(logo="https://example.com/logo.png"),
        )
        manifest = make_builder(bp).build()
        snapshot = SourceWebsiteSnapshot.from_profile(bp)
        md = format_source_content(snapshot, manifest=manifest)
        assert "## Approved Asset Manifest" in md
        assert "Role" in md
        assert "https://example.com/logo.png" in md
