"""Integration contract test: full Stitch pipeline.

StitchDesignProvider (mocked HTTP) → generated HTML → FidelityValidator
→ WebsiteProject persistence → Preview → ZIP packaging.

This verifies that all components compose correctly end-to-end.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from app.services.markdown_engine.builder import MarkdownBuilder
from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.website_intelligence.schemas import (
    WebsiteProfile, BusinessInfo, ContactInfo, BrandIdentity, HeroInfo,
    ServiceCard, Testimonial, FAQ, TeamMember, CompanySection,
    DesignLanguageResult, Typography, ColorPalette, LogoInfo,
    NavigationItem, SocialLink, ImageAsset, TrustSignal,
)
from app.services.website_generator.stitch.brief import BriefGenerator
from app.services.website_generator.stitch.design_provider import StitchDesignProvider
from app.services.website_generator.fidelity_validator import FidelityValidator
from app.services.website_generator.deployment.package_manager import PackageManager
from app.services.website_generator.build.schemas import BuildResult
from app.services.website_generator.preview.schemas import PreviewResult
from app.services.website_generator.schemas import (
    GenerationResult, WebsiteProject, GeneratedFile,
)


# ---------------------------------------------------------------------------
# Fixture: realistic WebsiteProfile
# ---------------------------------------------------------------------------

@pytest.fixture
def profile():
    return WebsiteProfile(
        business=BusinessInfo(
            name="Kiss the Hippo Coffee",
            category="Coffee Roaster",
            industry="Coffee & Tea",
            description="Premium specialty coffee roaster based in the UK",
            website_url="https://kissthehippo.com",
            logo="https://cdn.shopify.com/s/files/1/0XXX/logo.png",
            email="info@kissthehippo.com",
            phone="+44 1234 567890",
            address="123 Coffee Lane, London",
            social_links=[
                SocialLink(platform="facebook", url="https://facebook.com/kissthehippo"),
                SocialLink(platform="instagram", url="https://instagram.com/kissthehippo"),
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
            ServiceCard(name="Specialty Coffee", description="Single-origin beans from the world's best farms"),
            ServiceCard(name="Coffee Subscriptions", description="Fresh coffee delivered to your door monthly"),
            ServiceCard(name="Wholesale", description="Premium beans for cafes and restaurants"),
        ],
        products=[],
        testimonials=[
            Testimonial(author_name="Sarah M.", content="Best coffee I've ever had! The Ethiopian Yirgacheffe is incredible.", star_count=5),
            Testimonial(author_name="James K.", content="Amazing quality and fast delivery. My go-to coffee subscription.", star_count=5),
        ],
        faqs=[
            FAQ(question="Where do you source your beans?", answer="We source directly from farms in Ethiopia, Colombia, and Guatemala."),
            FAQ(question="How fresh is the coffee?", answer="All our coffee is roasted within the last 7 days."),
        ],
        contact=ContactInfo(
            emails=["info@kissthehippo.com"],
            phones=["+44 1234 567890"],
            address="123 Coffee Lane, London",
        ),
        navigation=[
            NavigationItem(label="Home", url="/"),
            NavigationItem(label="Shop", url="/shop"),
            NavigationItem(label="About", url="/about"),
            NavigationItem(label="Contact", url="/contact"),
        ],
        images=[
            ImageAsset(url="https://cdn.shopify.com/s/files/1/0XXX/hero.jpg", alt="Coffee beans"),
            ImageAsset(url="https://cdn.shopify.com/s/files/1/0XXX/logo.png", alt="Logo"),
        ],
        social_links=[
            SocialLink(platform="facebook", url="https://facebook.com/kissthehippo"),
            SocialLink(platform="instagram", url="https://instagram.com/kissthehippo"),
        ],
        trust_signals=[
            TrustSignal(type="award", value="Specialty Coffee Association Member"),
            TrustSignal(type="certification", value="Rainforest Alliance Certified"),
        ],
        team=[
            TeamMember(name="Alex Rivera", role="Head Roaster", bio="15 years specialty coffee experience"),
        ],
        company=CompanySection(
            description="Kiss the Hippo Coffee is a specialty coffee roaster.",
            mission="To bring the world's best coffee to your cup.",
            core_values=["Quality", "Sustainability", "Community"],
        ),
    )


@pytest.fixture
def realistic_stitch_html():
    """Simulates a high-quality Stitch-generated HTML page."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kiss the Hippo Coffee — Premium Redesign</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; color: #333; }
        .hero { background: linear-gradient(135deg, #2C5F2D, #97BC62); padding: 80px 20px; text-align: center; }
        .hero h1 { font-family: 'Playfair Display', serif; font-size: 3rem; color: #fff; }
        .hero p { color: rgba(255,255,255,0.9); font-size: 1.25rem; margin-top: 16px; }
        .btn { display: inline-block; margin-top: 24px; padding: 14px 32px; background: #F4A460; color: #fff; text-decoration: none; border-radius: 8px; font-weight: 600; }
        .services { padding: 60px 20px; max-width: 1200px; margin: 0 auto; }
        .services h2 { text-align: center; font-size: 2rem; margin-bottom: 40px; }
        .service-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 32px; }
        .service-card { background: #f9f9f9; padding: 32px; border-radius: 12px; }
        .service-card h3 { font-size: 1.25rem; margin-bottom: 12px; }
        .testimonials { background: #f5f5f5; padding: 60px 20px; }
        .faq { padding: 60px 20px; max-width: 800px; margin: 0 auto; }
        footer { background: #2C5F2D; color: #fff; padding: 40px 20px; text-align: center; }
    </style>
</head>
<body>
    <header class="hero">
        <img src="https://cdn.shopify.com/s/files/1/0XXX/logo.png" alt="Kiss the Hippo Coffee" width="120">
        <h1>Kiss the Hippo Coffee</h1>
        <p>Premium Specialty Coffee, Roasted Fresh</p>
        <a href="/shop" class="btn">Shop Now</a>
    </header>

    <nav>
        <a href="/">Home</a>
        <a href="/shop">Shop</a>
        <a href="/about">About</a>
        <a href="/contact">Contact</a>
    </nav>

    <section class="services">
        <h2>Our Services</h2>
        <div class="service-grid">
            <div class="service-card">
                <h3>Specialty Coffee</h3>
                <p>Single-origin beans from the world's best farms</p>
            </div>
            <div class="service-card">
                <h3>Coffee Subscriptions</h3>
                <p>Fresh coffee delivered to your door monthly</p>
            </div>
            <div class="service-card">
                <h3>Wholesale</h3>
                <p>Premium beans for cafes and restaurants</p>
            </div>
        </div>
    </section>

    <section class="testimonials">
        <h2>What Our Customers Say</h2>
        <blockquote>
            <p>"Best coffee I've ever had! The Ethiopian Yirgacheffe is incredible."</p>
            <cite>-- Sarah M.</cite>
        </blockquote>
        <blockquote>
            <p>"Amazing quality and fast delivery. My go-to coffee subscription."</p>
            <cite>-- James K.</cite>
        </blockquote>
    </section>

    <section class="faq">
        <h2>Frequently Asked Questions</h2>
        <details>
            <summary>Where do you source your beans?</summary>
            <p>We source directly from farms in Ethiopia, Colombia, and Guatemala.</p>
        </details>
        <details>
            <summary>How fresh is the coffee?</summary>
            <p>All our coffee is roasted within the last 7 days.</p>
        </details>
    </section>

    <footer>
        <p>Contact: info@kissthehippo.com | +44 1234 567890</p>
        <p>123 Coffee Lane, London</p>
        <p>&copy; 2026 Kiss the Hippo Coffee</p>
    </footer>
</body>
</html>"""


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.headers = {"content-type": "application/json"}
    return resp


# ---------------------------------------------------------------------------
# Integration contract test
# ---------------------------------------------------------------------------

class TestStitchPipelineContract:
    """End-to-end contract: profile → brief → Stitch → fidelity → persist → preview → ZIP."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, profile, realistic_stitch_html):
        # ── Step 1: Build MarkdownPackage ──────────────────────────
        builder = MarkdownBuilder(blueprint=profile)
        package = builder.build_package()
        assert isinstance(package, MarkdownPackage)

        # ── Step 2: Build PremiumRedesignBrief ─────────────────────
        brief_gen = BriefGenerator()
        brief = brief_gen.generate(profile, package)
        assert brief.business_name == "Kiss the Hippo Coffee"
        assert len(brief.full_instruction) > 500
        assert "Kiss the Hippo Coffee" in brief.full_instruction

        # ── Step 3: StitchDesignProvider (mocked HTTP) ─────────────
        stitch_response = {
            "success": True,
            "html_content": realistic_stitch_html,
            "stitch_project_id": "stitch-proj-contract",
            "stitch_screen_id": "stitch-screen-contract",
            "attempts": 1,
        }
        mock_resp = _mock_response(200, stitch_response)
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
        project = result.website_project
        assert project.framework == "static-html"
        assert len(project.files) == 1
        assert project.files[0].path == "index.html"
        assert "Kiss the Hippo Coffee" in project.preview_html

        # ── Step 4: FidelityValidator ─────────────────────────────
        fidelity_validator = FidelityValidator(profile)
        fidelity_result = fidelity_validator.validate(project.preview_html)
        assert fidelity_result.valid, (
            f"Fidelity failed: {[(i.category, i.detail) for i in fidelity_result.issues]}"
        )

        # ── Step 5: Preview record (simulates DB persistence) ─────
        preview_record = {
            "lead_id": "00000000-0000-0000-0000-000000000001",
            "generation_id": project.generation_id,
            "project_name": project.project_name,
            "framework": project.framework,
            "status": "generated",
            "html": project.preview_html,
            "preview_path": f"/preview/contract-test-id",
            "build_metadata": {
                "generation_time": result.generation_time,
                "provider_used": result.provider_used,
                "fidelity_valid": fidelity_result.valid,
                "fidelity_issues": len(fidelity_result.issues),
                "completeness": fidelity_result.completeness_score,
                "stitch_project_id": project.metadata.get("stitch_project_id"),
                "stitch_screen_id": project.metadata.get("stitch_screen_id"),
            },
        }
        assert preview_record["html"] is not None
        assert len(preview_record["html"]) > 100
        assert preview_record["build_metadata"]["fidelity_valid"] is True
        assert preview_record["build_metadata"]["stitch_project_id"] == "stitch-proj-contract"

        # ── Step 6: PackageManager → ZIP ──────────────────────────
        build_result = BuildResult(
            success=True, build_success=True, npm_install_success=True,
            logs=["Stitch generation complete.", "Fidelity: PASS"],
        )
        preview_result = PreviewResult(
            success=True, preview_url=preview_record["preview_path"],
            status="ready", health_check=True,
        )
        pkg = PackageManager().create_package(project, build_result, preview_result)
        assert pkg.package_id is not None
        assert len(pkg.artifacts) >= 1

        html_artifacts = [a for a in pkg.artifacts if a.get("path") == "index.html"]
        assert len(html_artifacts) == 1
        assert html_artifacts[0].get("content") == realistic_stitch_html

    @pytest.mark.asyncio
    async def test_pipeline_with_bad_fidelity_fails(self, profile):
        """When Stitch returns HTML that fails fidelity, pipeline catches it."""
        bad_html = """<!DOCTYPE html>
<html><body>
<h1>Generic Business</h1>
<p>Lorem ipsum dolor sit amet.</p>
<p>Contact: info@example.com</p>
<p>Powered by LeadForge AI</p>
</body></html>"""

        stitch_response = {
            "success": True,
            "html_content": bad_html,
            "stitch_project_id": "stitch-proj-bad",
            "stitch_screen_id": "stitch-screen-bad",
            "attempts": 1,
        }
        mock_resp = _mock_response(200, stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, MarkdownPackage())

        assert result.success is True  # Stitch itself succeeded

        # Fidelity should fail
        fidelity_validator = FidelityValidator(profile)
        fidelity_result = fidelity_validator.validate(result.website_project.preview_html)
        assert not fidelity_result.valid

        # Pipeline would abort here in production (critical issues)
        critical = [i for i in fidelity_result.issues if i.category not in ("duplicate_images",)]
        assert len(critical) > 0

    @pytest.mark.asyncio
    async def test_brief_and_fidelity_share_content(self, profile):
        """Brief instructions match what fidelity validates (content roundtrip)."""
        builder = MarkdownBuilder(blueprint=profile)
        package = builder.build_package()
        brief_gen = BriefGenerator()
        brief = brief_gen.generate(profile, package)

        # Brief should contain business identity
        assert "Kiss the Hippo Coffee" in brief.full_instruction
        assert "BUSINESS RULES" in brief.full_instruction

        # Simulate Stitch generates HTML that preserves business identity
        html = """<!DOCTYPE html>
<html lang="en">
<head><title>Kiss the Hippo Coffee</title></head>
<body>
<h1>Kiss the Hippo Coffee</h1>
<p>Premium specialty coffee roaster.</p>
</body></html>"""

        fidelity_validator = FidelityValidator(profile)
        result = fidelity_validator.validate(html)
        assert result.valid, f"Issues: {[(i.category, i.detail) for i in result.issues]}"
        assert result.completeness_score > 0

    @pytest.mark.asyncio
    async def test_stitch_provider_failure_aborts_pipeline(self, profile):
        """When Stitch service is unreachable, pipeline aborts cleanly."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, MarkdownPackage())

        assert result.success is False
        assert result.website_project is None
        assert any("error" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_zip_contains_html(self, profile, realistic_stitch_html):
        """ZIP package contains the generated index.html."""
        stitch_response = {
            "success": True,
            "html_content": realistic_stitch_html,
            "stitch_project_id": "proj-zip",
            "stitch_screen_id": "scr-zip",
            "attempts": 1,
        }
        mock_resp = _mock_response(200, stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, MarkdownPackage())

        build_result = BuildResult(success=True, build_success=True, npm_install_success=True, logs=["ok"])
        preview_result = PreviewResult(success=True, preview_url="/preview/test", status="ready")
        pkg = PackageManager().create_package(result.website_project, build_result, preview_result)

        html_artifacts = [a for a in pkg.artifacts if a.get("path") == "index.html"]
        assert len(html_artifacts) == 1
        content = html_artifacts[0].get("content", "")
        assert "Kiss the Hippo Coffee" in content
        assert len(content) > 1000

    @pytest.mark.asyncio
    async def test_metadata_preserved_through_pipeline(self, profile, realistic_stitch_html):
        """Stitch project/screen IDs survive through the full pipeline."""
        stitch_response = {
            "success": True,
            "html_content": realistic_stitch_html,
            "stitch_project_id": "proj-meta-123",
            "stitch_screen_id": "scr-meta-456",
            "attempts": 2,
        }
        mock_resp = _mock_response(200, stitch_response)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.website_generator.stitch.design_provider.httpx.AsyncClient", return_value=mock_client):
            provider = StitchDesignProvider()
            result = await provider.generate(profile, MarkdownPackage())

        project = result.website_project
        assert project.metadata["stitch_project_id"] == "proj-meta-123"
        assert project.metadata["stitch_screen_id"] == "scr-meta-456"
        assert project.metadata["source"] == "stitch_automated"
        assert result.provider_attempts == 2

        # Metadata flows into build_metadata
        build_metadata = {
            "stitch_project_id": project.metadata.get("stitch_project_id"),
            "stitch_screen_id": project.metadata.get("stitch_screen_id"),
            "fidelity_valid": True,
        }
        assert build_metadata["stitch_project_id"] == "proj-meta-123"
        assert build_metadata["stitch_screen_id"] == "scr-meta-456"
