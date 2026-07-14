"""Tests for StitchDesignProvider — automated Stitch generation via TypeScript service.

All HTTP calls to the stitch-service are mocked; no real Stitch API key required.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.website_intelligence.schemas import (
    WebsiteProfile, BusinessInfo, ContactInfo, BrandIdentity, HeroInfo,
    ServiceCard, Testimonial, FAQ, TeamMember, CompanySection,
    DesignLanguageResult, Typography, ColorPalette, LogoInfo,
    NavigationItem, SocialLink, ImageAsset, TrustSignal,
)
from app.services.website_generator.schemas import GenerationResult
from app.services.website_generator.stitch.design_provider import StitchDesignProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def profile():
    return WebsiteProfile(
        business=BusinessInfo(
            name="Kiss the Hippo Coffee",
            category="Coffee Roaster",
            industry="Coffee & Tea",
            description="Premium specialty coffee roaster",
            website_url="https://kissthehippo.com",
            logo="https://cdn.shopify.com/s/files/1/0XXX/logo.png",
            email="info@kissthehippo.com",
            phone="+44 1234 567890",
            address="123 Coffee Lane, London",
            social_links=[
                SocialLink(platform="facebook", url="https://facebook.com/kissthehippo"),
            ],
        ),
        brand=BrandIdentity(
            tagline="Specialty Coffee, Roasted with Love",
            logo_info=LogoInfo(logo_url="https://cdn.shopify.com/s/files/1/0XXX/logo.png"),
            brand_colors=ColorPalette(
                primary="#2C5F2D", secondary="#97BC62", accent="#F4A460",
                background="#FFFFFF", text="#333333",
            ),
            brand_typography=Typography(heading_font="Playfair Display", body_font="Inter"),
            design_language=DesignLanguageResult(design_language="Organic Modern", confidence_score=0.82),
        ),
        hero_info=HeroInfo(
            hero_title="Kiss the Hippo Coffee",
            hero_subtitle="Premium Specialty Coffee, Roasted Fresh",
            hero_image="https://cdn.shopify.com/s/files/1/0XXX/hero.jpg",
            primary_cta={"text": "Shop Now", "url": "/shop"},
        ),
        services=[
            ServiceCard(name="Specialty Coffee", description="Single-origin beans"),
            ServiceCard(name="Coffee Subscriptions", description="Monthly delivery"),
        ],
        testimonials=[
            Testimonial(author_name="Sarah M.", content="Best coffee ever!", star_count=5),
        ],
        faqs=[
            FAQ(question="Where do you source?", answer="Directly from farms."),
        ],
        contact=ContactInfo(
            emails=["info@kissthehippo.com"],
            phones=["+44 1234 567890"],
            address="123 Coffee Lane, London",
        ),
        navigation=[
            NavigationItem(label="Home", url="/"),
            NavigationItem(label="Shop", url="/shop"),
        ],
        images=[
            ImageAsset(url="https://cdn.shopify.com/s/files/1/0XXX/hero.jpg", alt="Coffee"),
        ],
        social_links=[
            SocialLink(platform="facebook", url="https://facebook.com/kissthehippo"),
        ],
        trust_signals=[
            TrustSignal(type="award", value="Specialty Coffee Association"),
        ],
        team=[TeamMember(name="Alex Rivera", role="Head Roaster", bio="15 years experience")],
        company=CompanySection(
            description="Kiss the Hippo Coffee is a specialty roaster.",
            mission="Bring the world's best coffee to your cup.",
            core_values=["Quality", "Sustainability"],
        ),
    )


@pytest.fixture
def package():
    return MarkdownPackage()


@pytest.fixture
def good_stitch_response():
    """Simulates a successful stitch-service response."""
    html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Kiss the Hippo Coffee</title></head>
<body>
<h1>Kiss the Hippo Coffee</h1>
<p>Premium Specialty Coffee, Roasted Fresh</p>
<p>Contact: info@kissthehippo.com | +44 1234 567890</p>
<img src="https://cdn.shopify.com/s/files/1/0XXX/hero.jpg" alt="Coffee">
</body>
</html>"""
    return {
        "success": True,
        "html_content": html,
        "stitch_project_id": "stitch-proj-abc",
        "stitch_screen_id": "stitch-screen-123",
        "attempts": 1,
    }


def _mock_response(status_code=200, json_data=None):
    """Build a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.headers = {"content-type": "application/json"}
    return resp


# ---------------------------------------------------------------------------
# DesignProvider ABC Compliance
# ---------------------------------------------------------------------------

class TestStitchDesignProviderCompliance:
    def test_is_subclass_of_design_provider(self):
        from app.services.website_generator.design_provider import DesignProvider
        assert issubclass(StitchDesignProvider, DesignProvider)

    def test_provider_name(self):
        provider = StitchDesignProvider()
        assert provider.provider_name() == "stitch_automated"

    def test_has_generate_method(self):
        provider = StitchDesignProvider()
        assert hasattr(provider, "generate")
        assert callable(provider.generate)


# ---------------------------------------------------------------------------
# Successful Generation
# ---------------------------------------------------------------------------

class TestStitchDesignProviderSuccess:
    @pytest.mark.asyncio
    async def test_successful_generation(self, profile, package, good_stitch_response):
        mock_resp = _mock_response(200, good_stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.success is True
        assert result.website_project is not None
        assert result.provider_used == "stitch_automated"
        assert result.website_project.framework == "static-html"

    @pytest.mark.asyncio
    async def test_result_has_html(self, profile, package, good_stitch_response):
        mock_resp = _mock_response(200, good_stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.website_project.preview_html is not None
        assert len(result.website_project.preview_html) > 100
        assert "Kiss the Hippo Coffee" in result.website_project.preview_html

    @pytest.mark.asyncio
    async def test_result_files_array(self, profile, package, good_stitch_response):
        mock_resp = _mock_response(200, good_stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert len(result.website_project.files) == 1
        assert result.website_project.files[0].path == "index.html"
        assert result.website_project.files[0].type == "text/html"

    @pytest.mark.asyncio
    async def test_metadata_has_stitch_ids(self, profile, package, good_stitch_response):
        mock_resp = _mock_response(200, good_stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        meta = result.website_project.metadata
        assert meta.get("stitch_project_id") == "stitch-proj-abc"
        assert meta.get("stitch_screen_id") == "stitch-screen-123"
        assert meta.get("source") == "stitch_automated"

    @pytest.mark.asyncio
    async def test_project_name_includes_business(self, profile, package, good_stitch_response):
        mock_resp = _mock_response(200, good_stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert "Kiss the Hippo" in result.website_project.project_name

    @pytest.mark.asyncio
    async def test_provider_attempts_from_response(self, profile, package, good_stitch_response):
        good_stitch_response["attempts"] = 3
        mock_resp = _mock_response(200, good_stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.provider_attempts == 3


# ---------------------------------------------------------------------------
# HTTP Error Handling
# ---------------------------------------------------------------------------

class TestStitchDesignProviderErrors:
    @pytest.mark.asyncio
    async def test_http_500_returns_failure(self, profile, package):
        mock_resp = _mock_response(500, {"error": "Internal Server Error"})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.success is False
        assert any("500" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_http_429_rate_limit_returns_failure(self, profile, package):
        mock_resp = _mock_response(429, {"error": "Rate limit exceeded"})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.success is False
        assert any("429" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_stitch_success_false_returns_failure(self, profile, package):
        mock_resp = _mock_response(200, {"success": False, "error": "Stitch project failed"})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.success is False
        assert any("failed" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_empty_html_returns_failure(self, profile, package):
        mock_resp = _mock_response(200, {"success": True, "html_content": ""})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.success is False
        assert any("empty" in e.lower() or "short" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_too_short_html_returns_failure(self, profile, package):
        mock_resp = _mock_response(200, {"success": True, "html_content": "<html>tiny</html>"})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_connection_error_returns_failure(self, profile, package):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.success is False
        assert any("error" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_timeout_returns_failure(self, profile, package):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_non_json_error_response(self, profile, package):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 502
        resp.json.return_value = {}
        resp.headers = {"content-type": "text/html"}

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert result.success is False
        assert any("502" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Brief Generation Edge Cases
# ---------------------------------------------------------------------------

class TestStitchDesignProviderBrief:
    @pytest.mark.asyncio
    async def test_minimal_profile_still_generates_brief(self, package):
        minimal = WebsiteProfile(business=BusinessInfo(name="Minimal Biz"))
        mock_resp = _mock_response(200, {
            "success": True,
            "html_content": "<html><body><h1>Minimal Biz</h1><p>A professional website with enough content to pass validation checks successfully.</p></body></html>",
            "stitch_project_id": "proj-min",
            "stitch_screen_id": "scr-min",
        })
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(minimal, package)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_sends_auth_header(self, profile, package, good_stitch_response):
        mock_resp = _mock_response(200, good_stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            await provider.generate(profile, package)

        call_kwargs = mock_client.post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert "X-Internal-Secret" in headers
        assert len(headers["X-Internal-Secret"]) > 0


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class TestStitchDesignProviderHealth:
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        mock_resp = _mock_response(200, {"status": "healthy", "stitch_sdk": True})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            health = await StitchDesignProvider.check_service_health()

        assert health.get("status") == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_unreachable(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            health = await StitchDesignProvider.check_service_health()

        assert health.get("status") == "unreachable"

    @pytest.mark.asyncio
    async def test_health_check_http_error(self):
        mock_resp = _mock_response(503, {"status": "degraded"})
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            health = await StitchDesignProvider.check_service_health()

        assert health.get("http_status") == 503


# ---------------------------------------------------------------------------
# GenerationResult Contract
# ---------------------------------------------------------------------------

class TestStitchDesignProviderContract:
    @pytest.mark.asyncio
    async def test_result_has_all_required_fields(self, profile, package, good_stitch_response):
        mock_resp = _mock_response(200, good_stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        assert hasattr(result, "success")
        assert hasattr(result, "website_project")
        assert hasattr(result, "provider_used")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "provider_attempts")
        assert hasattr(result, "generation_time")
        assert result.success is True
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)

    @pytest.mark.asyncio
    async def test_no_dummy_html_in_success(self, profile, package, good_stitch_response):
        mock_resp = _mock_response(200, good_stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, package)

        html = result.website_project.preview_html
        assert "Lorem Ipsum" not in html
        assert "Generated by LeadForge" not in html
        assert "example.com" not in html
