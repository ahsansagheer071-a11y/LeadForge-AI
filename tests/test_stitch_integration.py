"""Tests for the Stitch integration layer.

Covers: PremiumRedesignBrief generation, StitchImportProvider contract,
validation, fidelity, preview persistence, and ZIP packaging.
"""

import pytest
from datetime import datetime, timezone
from typing import List

from app.services.website_intelligence.schemas import (
    WebsiteProfile, BusinessInfo, ContactInfo, BrandIdentity, HeroInfo,
    ServiceCard, Testimonial, FAQ, TeamMember, CompanySection,
    DesignLanguageResult, Typography, ColorPalette, LogoInfo,
    NavigationItem, SocialLink, ImageAsset, TrustSignal,
)
from app.services.markdown_engine.schemas import MarkdownPackage, MarkdownDocument
from app.services.website_generator.schemas import GenerationResult
from app.services.website_generator.stitch.schemas import (
    PremiumRedesignBrief, StitchDesignTokens, StitchBriefSection,
)
from app.services.website_generator.stitch.brief import BriefGenerator
from app.services.website_generator.stitch.import_provider import StitchImportProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def kissthehippo_profile() -> WebsiteProfile:
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
                primary="#2C5F2D",
                secondary="#97BC62",
                accent="#F4A460",
                background="#FFFFFF",
                text="#333333",
            ),
            brand_typography=Typography(
                heading_font="Playfair Display",
                body_font="Inter",
            ),
            design_language=DesignLanguageResult(
                design_language="Organic Modern",
                confidence_score=0.82,
            ),
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
            ServiceCard(name="Wholesale", description="For cafés and restaurants"),
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
def brief_generator() -> BriefGenerator:
    return BriefGenerator()


@pytest.fixture
def sample_html_export() -> str:
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
                <p>Premium beans for cafés and restaurants</p>
            </div>
        </div>
    </section>

    <section class="testimonials">
        <h2>What Our Customers Say</h2>
        <blockquote>
            <p>"Best coffee I've ever had! The Ethiopian Yirgacheffe is incredible."</p>
            <cite>— Sarah M.</cite>
        </blockquote>
        <blockquote>
            <p>"Amazing quality and fast delivery. My go-to coffee subscription."</p>
            <cite>— James K.</cite>
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


# ---------------------------------------------------------------------------
# BriefGenerator Tests
# ---------------------------------------------------------------------------

class TestBriefGenerator:
    def test_generates_brief_from_profile(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        assert isinstance(brief, PremiumRedesignBrief)
        assert brief.business_name == "Kiss the Hippo Coffee"
        assert brief.business_url == "https://kissthehippo.com"

    def test_brief_has_design_tokens(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        tokens = brief.design_tokens
        assert tokens.primary_color == "#2C5F2D"
        assert tokens.secondary_color == "#97BC62"
        assert tokens.heading_font == "Playfair Display"
        assert tokens.body_font == "Inter"
        assert tokens.logo_url is not None

    def test_brief_has_hero_section(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        hero = brief.hero_section
        assert hero.section_type == "hero"
        assert "Kiss the Hippo Coffee" in hero.content_instructions
        assert len(hero.source_images) > 0

    def test_brief_has_services(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        svc_sections = [s for s in brief.sections if s.section_type == "services"]
        assert len(svc_sections) == 1
        assert "Specialty Coffee" in svc_sections[0].content_instructions
        assert "Coffee Subscriptions" in svc_sections[0].content_instructions

    def test_brief_has_testimonials(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        test_sections = [s for s in brief.sections if s.section_type == "testimonials"]
        assert len(test_sections) == 1
        assert "testimonials" in test_sections[0].content_instructions.lower()

    def test_brief_has_faqs(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        faq_sections = [s for s in brief.sections if s.section_type == "faq"]
        assert len(faq_sections) == 1
        assert "FAQ" in faq_sections[0].content_instructions or "faq" in faq_sections[0].content_instructions.lower()

    def test_brief_has_navigation(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        assert len(brief.navigation_items) == 4
        labels = [n["label"] for n in brief.navigation_items]
        assert "Home" in labels
        assert "Shop" in labels

    def test_brief_has_contact_info(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        assert brief.contact_info.get("email") == "info@kissthehippo.com"
        assert brief.contact_info.get("phone") == "+44 1234 567890"

    def test_brief_has_social_links(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        platforms = [s["platform"] for s in brief.social_links]
        assert "facebook" in platforms
        assert "instagram" in platforms

    def test_brief_has_original_images(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        assert len(brief.original_images) >= 2
        urls = [img["url"] for img in brief.original_images]
        assert any("hero" in u for u in urls)

    def test_brief_has_content_rules(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        assert len(brief.content_rules) >= 5
        assert any("Lorem Ipsum" in r for r in brief.content_rules)
        assert any("LeadForge" in r for r in brief.content_rules)
        assert any("PRESERVE" in r for r in brief.content_rules)

    def test_brief_has_design_rules(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        assert len(brief.design_rules) >= 8
        assert any("responsive" in r.lower() for r in brief.design_rules)
        assert any("typography" in r.lower() or "font" in r.lower() for r in brief.design_rules)

    def test_brief_incorporates_weaknesses(self, kissthehippo_profile, brief_generator):
        weaknesses = ["Poor mobile responsiveness", "Missing call-to-action above the fold"]
        brief = brief_generator.generate(kissthehippo_profile, weaknesses=weaknesses)
        assert "Poor mobile responsiveness" in brief.full_instruction
        assert "Missing call-to-action" in brief.full_instruction
        assert "AUDIT IMPROVEMENTS" in brief.full_instruction

    def test_brief_incorporates_recommendations(self, kissthehippo_profile, brief_generator):
        recommendations = ["Add customer reviews section", "Improve page load speed"]
        brief = brief_generator.generate(kissthehippo_profile, recommendations=recommendations)
        assert "Add customer reviews" in brief.full_instruction

    def test_full_instruction_is_compiled(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        assert len(brief.full_instruction) > 500
        assert "Kiss the Hippo Coffee" in brief.full_instruction
        assert "ROLE" in brief.full_instruction
        assert "SOURCE WEBSITE" in brief.full_instruction
        assert "BUSINESS RULES" in brief.full_instruction
        assert "DESIGN DIRECTION" in brief.full_instruction

    def test_brief_hash_is_deterministic(self, kissthehippo_profile, brief_generator):
        brief1 = brief_generator.generate(kissthehippo_profile)
        brief2 = brief_generator.generate(kissthehippo_profile)
        assert brief_generator.brief_hash(brief1) == brief_generator.brief_hash(brief2)

    def test_brief_hash_changes_with_different_data(self, brief_generator):
        profile1 = WebsiteProfile(business=BusinessInfo(name="Cafe A", website_url="https://a.com"))
        profile2 = WebsiteProfile(business=BusinessInfo(name="Cafe B", website_url="https://b.com"))
        brief1 = brief_generator.generate(profile1)
        brief2 = brief_generator.generate(profile2)
        assert brief_generator.brief_hash(brief1) != brief_generator.brief_hash(brief2)

    def test_brief_handles_minimal_profile(self, brief_generator):
        profile = WebsiteProfile(business=BusinessInfo(name="Minimal Biz"))
        brief = brief_generator.generate(profile)
        assert brief.business_name == "Minimal Biz"
        assert len(brief.full_instruction) > 100
        assert len(brief.navigation_items) >= 4

    def test_brief_logo_url(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        assert "logo.png" in brief.logo_url

    def test_brief_has_company_section(self, kissthehippo_profile, brief_generator):
        brief = brief_generator.generate(kissthehippo_profile)
        about_sections = [s for s in brief.sections if s.section_type == "about"]
        assert len(about_sections) == 1
        assert "specialty coffee roaster" in about_sections[0].content_instructions.lower()


# ---------------------------------------------------------------------------
# StitchImportProvider Tests
# ---------------------------------------------------------------------------

class TestStitchImportProvider:
    @pytest.mark.asyncio
    async def test_import_valid_html(self, kissthehippo_profile, sample_html_export):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(
            kissthehippo_profile, package,
            html_content=sample_html_export,
            stitch_project_id="test-project-123",
        )
        assert result.success is True
        assert result.provider_used == "stitch_import"
        assert result.website_project is not None
        assert len(result.website_project.files) == 1
        assert result.website_project.files[0].path == "index.html"
        assert "Kiss the Hippo Coffee" in result.website_project.files[0].content
        assert result.website_project.preview_html is not None
        assert "Kiss the Hippo Coffee" in result.website_project.preview_html
        assert result.website_project.metadata.get("stitch_project_id") == "test-project-123"

    @pytest.mark.asyncio
    async def test_import_no_html_returns_not_configured(self, kissthehippo_profile):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(kissthehippo_profile, package)
        assert result.success is False
        assert result.website_project is None
        assert "not provided" in result.errors[0].lower() or "stitch" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_import_empty_html_returns_not_configured(self, kissthehippo_profile):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(kissthehippo_profile, package, html_content="")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_import_too_short_html_returns_error(self, kissthehippo_profile):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(kissthehippo_profile, package, html_content="<html>tiny</html>")
        assert result.success is False

    def test_provider_name(self):
        provider = StitchImportProvider()
        assert provider.provider_name() == "stitch_import"

    @pytest.mark.asyncio
    async def test_import_preserves_generation_id(self, kissthehippo_profile, sample_html_export):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(
            kissthehippo_profile, package,
            html_content=sample_html_export,
        )
        assert result.website_project.generation_id
        assert len(result.website_project.generation_id) == 32

    @pytest.mark.asyncio
    async def test_import_project_name(self, kissthehippo_profile, sample_html_export):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(
            kissthehippo_profile, package,
            html_content=sample_html_export,
        )
        assert "Kiss the Hippo" in result.website_project.project_name
        assert "Stitch" in result.website_project.project_name

    @pytest.mark.asyncio
    async def test_import_framework_is_static_html(self, kissthehippo_profile, sample_html_export):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(
            kissthehippo_profile, package,
            html_content=sample_html_export,
        )
        assert result.website_project.framework == "static-html"


# ---------------------------------------------------------------------------
# StitchImportProvider.validate_export Tests
# ---------------------------------------------------------------------------

class TestStitchExportValidation:
    def test_valid_export_passes(self, sample_html_export):
        issues = StitchImportProvider.validate_export(sample_html_export)
        critical = [i for i in issues if "empty" in i.lower() or "too short" in i.lower()]
        assert len(critical) == 0

    def test_empty_export_fails(self):
        issues = StitchImportProvider.validate_export("")
        assert len(issues) > 0
        assert any("empty" in i.lower() for i in issues)

    def test_lorem_ipsum_detected(self):
        html = "<html><body><p>Lorem ipsum dolor sit amet</p></body></html>"
        issues = StitchImportProvider.validate_export(html)
        assert any("lorem ipsum" in i.lower() for i in issues)

    def test_leadforge_branding_detected(self):
        html = "<html><body><p>Generated by LeadForge AI</p></body></html>"
        issues = StitchImportProvider.validate_export(html)
        assert any("leadforge" in i.lower() for i in issues)

    def test_dummy_email_detected(self):
        html = "<html><body><p>Contact us at info@example.com</p></body></html>"
        issues = StitchImportProvider.validate_export(html)
        assert any("dummy email" in i.lower() for i in issues)

    def test_no_headings_detected(self):
        html = "<html><body><p>Just a paragraph, no headings at all.</p></body></html>"
        issues = StitchImportProvider.validate_export(html)
        assert any("heading" in i.lower() for i in issues)

    def test_no_images_detected(self):
        html = "<html><body><h1>Title</h1><p>Text only content here.</p></body></html>"
        issues = StitchImportProvider.validate_export(html)
        assert any("no images" in i.lower() for i in issues)

    def test_markdown_fences_detected(self):
        html = "<html><body><h1>Title</h1><img src='x.jpg'><p>```code```</p></body></html>"
        issues = StitchImportProvider.validate_export(html)
        assert any("markdown" in i.lower() or "code fence" in i.lower() for i in issues)

    def test_dummy_phone_detected(self):
        html = "<html><body><h1>Title</h1><img src='x.jpg'><p>Call 555-0100</p></body></html>"
        issues = StitchImportProvider.validate_export(html)
        assert any("dummy phone" in i.lower() for i in issues)


# ---------------------------------------------------------------------------
# Fidelity Validation with Imported Export
# ---------------------------------------------------------------------------

class TestFidelityWithImport:
    def test_fidelity_passes_with_good_import(self, kissthehippo_profile, sample_html_export):
        from app.services.website_generator.fidelity_validator import FidelityValidator
        validator = FidelityValidator(kissthehippo_profile)
        result = validator.validate(sample_html_export)
        assert result.valid, f"Issues: {[(i.category, i.detail) for i in result.issues]}"

    def test_fidelity_detects_bad_import(self, kissthehippo_profile):
        from app.services.website_generator.fidelity_validator import FidelityValidator
        bad_html = """<!DOCTYPE html>
<html><body>
<h1>Generic Business</h1>
<p>Lorem ipsum dolor sit amet.</p>
<p>Contact: info@example.com</p>
<p>Powered by LeadForge AI</p>
</body></html>"""
        validator = FidelityValidator(kissthehippo_profile)
        result = validator.validate(bad_html)
        assert not result.valid
        categories = {i.category for i in result.issues}
        assert "lorem_ipsum" in categories
        assert "dummy_email" in categories
        assert "leadforge_branding" in categories
        assert "missing_business_name" in categories


# ---------------------------------------------------------------------------
# GenerationResult Contract Tests
# ---------------------------------------------------------------------------

class TestGenerationResultContract:
    @pytest.mark.asyncio
    async def test_result_has_required_fields(self, kissthehippo_profile, sample_html_export):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(
            kissthehippo_profile, package,
            html_content=sample_html_export,
        )
        assert hasattr(result, "success")
        assert hasattr(result, "website_project")
        assert hasattr(result, "provider_used")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "provider_attempts")
        assert result.success is True
        assert result.website_project is not None

    @pytest.mark.asyncio
    async def test_website_project_has_preview_html(self, kissthehippo_profile, sample_html_export):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(
            kissthehippo_profile, package,
            html_content=sample_html_export,
        )
        assert result.website_project.preview_html is not None
        assert len(result.website_project.preview_html) > 100

    @pytest.mark.asyncio
    async def test_website_project_has_files(self, kissthehippo_profile, sample_html_export):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(
            kissthehippo_profile, package,
            html_content=sample_html_export,
        )
        assert len(result.website_project.files) == 1
        assert result.website_project.files[0].type == "text/html"

    @pytest.mark.asyncio
    async def test_metadata_includes_stitch_info(self, kissthehippo_profile, sample_html_export):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(
            kissthehippo_profile, package,
            html_content=sample_html_export,
            stitch_project_id="proj-abc",
            stitch_screen_id="screen-123",
        )
        meta = result.website_project.metadata
        assert meta.get("source") == "stitch_import"
        assert meta.get("stitch_project_id") == "proj-abc"
        assert meta.get("stitch_screen_id") == "screen-123"


# ---------------------------------------------------------------------------
# ZIP Packaging Tests
# ---------------------------------------------------------------------------

class TestZipPackaging:
    def test_package_manager_works_with_stitch_result(self, kissthehippo_profile, sample_html_export):
        from app.services.website_generator.deployment.package_manager import PackageManager
        from app.services.website_generator.build.schemas import BuildResult
        from app.services.website_generator.preview.schemas import PreviewResult
        from app.services.website_generator.schemas import WebsiteProject, GeneratedFile

        project = WebsiteProject(
            project_name="Test Stitch Redesign",
            framework="static-html",
            generation_id="test123",
            version="1.0.0",
            generated_at=datetime.now(timezone.utc),
            files=[
                GeneratedFile(
                    path="index.html",
                    content=sample_html_export,
                    type="text/html",
                    size=len(sample_html_export.encode()),
                )
            ],
            preview_html=sample_html_export,
        )
        build_result = BuildResult(
            success=True, build_success=True, npm_install_success=True,
            logs=["Imported."],
        )
        preview_result = PreviewResult(
            success=True, preview_url="/preview/test", status="ready",
        )
        pkg = PackageManager().create_package(project, build_result, preview_result)
        assert pkg.package_id
        assert len(pkg.artifacts) >= 1
        html_artifacts = [a for a in pkg.artifacts if a.get("path") == "index.html"]
        assert len(html_artifacts) == 1
        assert html_artifacts[0].get("content") == sample_html_export


# ---------------------------------------------------------------------------
# Preview Persistence Tests
# ---------------------------------------------------------------------------

class TestPreviewPersistence:
    @pytest.mark.asyncio
    async def test_preview_html_matches_import(self, kissthehippo_profile, sample_html_export):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(
            kissthehippo_profile, package,
            html_content=sample_html_export,
        )
        preview = result.website_project.preview_html
        file_content = result.website_project.files[0].content
        assert preview == file_content

    @pytest.mark.asyncio
    async def test_preview_survives_roundtrip(self, kissthehippo_profile, sample_html_export):
        provider = StitchImportProvider()
        package = MarkdownPackage()
        result = await provider.generate(
            kissthehippo_profile, package,
            html_content=sample_html_export,
        )
        html = result.website_project.preview_html
        assert "<!DOCTYPE html>" in html
        assert "Kiss the Hippo Coffee" in html
        assert "info@kissthehippo.com" in html
        assert "+44 1234 567890" in html


# ---------------------------------------------------------------------------
# DesignProvider ABC Compliance
# ---------------------------------------------------------------------------

class TestDesignProviderCompliance:
    def test_stitch_import_is_subclass(self):
        from app.services.website_generator.design_provider import DesignProvider
        assert issubclass(StitchImportProvider, DesignProvider)

    @pytest.mark.asyncio
    async def test_stitch_import_implements_generate(self):
        provider = StitchImportProvider()
        assert hasattr(provider, "generate")
        assert callable(provider.generate)

    def test_stitch_import_has_provider_name(self):
        provider = StitchImportProvider()
        name = provider.provider_name()
        assert isinstance(name, str)
        assert len(name) > 0
