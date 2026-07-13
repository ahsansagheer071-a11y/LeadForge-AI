"""Integration tests for FidelityValidator + asset_manifest pipeline.

Tests the full data flow: WebsiteProfile → FidelityValidator,
ensuring asset_manifest is correctly propagated and fidelity checks work end-to-end.
"""

import pytest
from datetime import datetime, timezone
from typing import List, Optional

from app.services.website_intelligence.schemas import (
    WebsiteProfile, BusinessInfo, ContactInfo, BrandIdentity,
    DesignLanguageResult, HeroInfo, TypographyInfo, ColorPalette,
    ComponentStyles, ServiceCard,
)
from app.services.markdown_engine.asset_manifest import (
    AssetManifest, AssetManifestItem, AssetRole,
)
from app.services.markdown_engine.schemas import MarkdownPackage, MarkdownDocument, MarkdownMetadata
from app.services.website_generator.fidelity_validator import FidelityValidator, FidelityIssue, FidelityValidationResult
from app.services.website_generator.schemas import GenerationResult


@pytest.fixture
def sample_profile() -> WebsiteProfile:
    from app.services.website_intelligence.schemas import ImageAsset
    return WebsiteProfile(
        url="https://testcafe.com",
        business=BusinessInfo(
            name="Test Cafe",
            industry="Coffee",
            description="A premium coffee shop",
        ),
        contact=ContactInfo(
            emails=["hello@testcafe.com"],
            phones=["+1-555-0199"],
            address="456 Oak Ave, Portland, OR",
        ),
        brand=BrandIdentity(
            design_language=DesignLanguageResult(design_language="Modern", confidence_score=0.85),
            hero=HeroInfo(headline="Best Coffee in Town"),
            typography=TypographyInfo(primary_font="Inter"),
            colors=ColorPalette(primary="#1a1a2e"),
        ),
        services=[
            ServiceCard(name="Espresso", description="Rich espresso shot"),
            ServiceCard(name="Latte", description="Creamy latte"),
        ],
        images=[
            ImageAsset(url="https://testcafe.com/hero.jpg"),
            ImageAsset(url="https://testcafe.com/logo.png"),
        ],
    )


@pytest.fixture
def sample_manifest() -> AssetManifest:
    return AssetManifest(
        items=[
            AssetManifestItem(
                original_url="https://testcafe.com/hero.jpg",
                absolute_url="https://testcafe.com/hero.jpg",
                role=AssetRole.HERO,
                section="hero",
                local_filename="hero.jpg",
            ),
            AssetManifestItem(
                original_url="https://testcafe.com/logo.png",
                absolute_url="https://testcafe.com/logo.png",
                role=AssetRole.LOGO,
                section="header",
                local_filename="logo.png",
            ),
        ],
        source_url="https://testcafe.com",
        total_count=2,
    )


def make_fake_markdown_doc(content: str = "") -> MarkdownDocument:
    return MarkdownDocument(
        filename="test.md",
        title="Test",
        category="test",
        priority=0,
        content=content,
        version="1.0.0",
        generated_at=datetime.now(timezone.utc),
    )


class TestFidelityPipelineIntegration:
    """Integration tests: MarkdownPackage → FidelityValidator pipeline."""

    def test_markdown_package_carries_asset_manifest(self, sample_manifest):
        """Verify MarkdownPackage.asset_manifest is properly set."""
        pkg = MarkdownPackage()
        pkg.asset_manifest = sample_manifest
        assert pkg.asset_manifest is not None
        assert pkg.asset_manifest.total_count == 2
        assert len(pkg.asset_manifest.items) == 2

    def test_fidelity_validator_receives_manifest_from_package(self, sample_profile, sample_manifest):
        """Verify FidelityValidator can be constructed from package.asset_manifest."""
        validator = FidelityValidator(sample_profile, manifest=sample_manifest)
        assert validator.manifest is not None
        assert validator.manifest.total_count == 2

    def test_fidelity_passes_with_good_html(self, sample_profile, sample_manifest):
        """End-to-end: good HTML + manifest → valid fidelity result."""
        html = """<!DOCTYPE html>
<html><head><title>Test Cafe</title></head>
<body>
<h1>Test Cafe</h1>
<nav><a href="/">Home</a><a href="/about">About</a></nav>
<section><h2>Espresso</h2><p>Rich espresso shot</p></section>
<section><h2>Latte</h2><p>Creamy latte</p></section>
<img src="https://testcafe.com/hero.jpg" alt="Hero">
<img src="https://testcafe.com/logo.png" alt="Logo">
<p>Email: hello@testcafe.com</p>
<p>Phone: +1-555-0199</p>
<footer>456 Oak Ave, Portland, OR</footer>
</body></html>"""
        validator = FidelityValidator(sample_profile, manifest=sample_manifest)
        result = validator.validate(html)
        assert result.valid, f"Issues: {[(i.category, i.detail) for i in result.issues]}"
        assert result.preserved_service_count == 2
        assert "hello@testcafe.com" in result.preserved_contact_emails
        assert "+1-555-0199" in result.preserved_contact_phones
        assert result.approved_image_count >= 2
        assert len(result.broken_image_refs) == 0

    def test_fidelity_detects_unapproved_images(self, sample_profile, sample_manifest):
        """Unapproved images are flagged as broken_image_refs."""
        html = """<!DOCTYPE html>
<html><body>
<h1>Test Cafe</h1>
<img src="https://evil.com/stock.jpg" alt="Stock">
<img src="https://testcafe.com/hero.jpg" alt="Hero">
<p>Email: hello@testcafe.com</p>
<p>Phone: +1-555-0199</p>
</body></html>"""
        validator = FidelityValidator(sample_profile, manifest=sample_manifest)
        result = validator.validate(html)
        assert not result.valid
        assert "https://evil.com/stock.jpg" in result.broken_image_refs
        assert any(i.category == "unapproved_images" for i in result.issues)

    def test_fidelity_detects_invented_content(self, sample_profile):
        """Lorem Ipsum, dummy email, and LeadForge branding all fail."""
        html = """<!DOCTYPE html>
<html><body>
<h1>Test Cafe</h1>
<p>Lorem ipsum dolor sit amet. Contact us at admin@example.com.</p>
<p>Powered by LeadForge AI.</p>
</body></html>"""
        validator = FidelityValidator(sample_profile)
        result = validator.validate(html)
        assert not result.valid
        categories = {i.category for i in result.issues}
        assert "lorem_ipsum" in categories
        assert "dummy_email" in categories
        assert "leadforge_branding" in categories
        assert "missing_contact_email" in categories

    def test_fidelity_detects_missing_content(self, sample_profile):
        """Missing business name, services, and contacts all flagged."""
        html = """<!DOCTYPE html>
<html><body><p>Welcome to our cafe.</p></body></html>"""
        validator = FidelityValidator(sample_profile)
        result = validator.validate(html)
        assert not result.valid
        categories = {i.category for i in result.issues}
        assert "missing_business_name" in categories
        assert "missing_services" in categories
        assert "missing_contact_email" in categories

    def test_fidelity_no_manifest_skips_image_check(self, sample_profile):
        """Without manifest, image check is skipped (no false positives)."""
        sample_profile.services = []
        html = """<!DOCTYPE html>
<html><body>
<h1>Test Cafe</h1>
<img src="https://anywhere.com/photo.jpg" alt="Photo">
<p>Email: hello@testcafe.com</p>
<p>Phone: +1-555-0199</p>
</body></html>"""
        validator = FidelityValidator(sample_profile, manifest=None)
        result = validator.validate(html)
        assert result.valid, f"Issues: {[(i.category, i.detail) for i in result.issues]}"
        assert len(result.broken_image_refs) == 0

    def test_fidelity_handles_empty_manifest(self, sample_profile):
        """Empty manifest = no approved images; all image refs are flagged."""
        empty_manifest = AssetManifest(items=[], source_url="https://testcafe.com", total_count=0)
        html = """<!DOCTYPE html>
<html><body>
<h1>Test Cafe</h1>
<img src="https://testcafe.com/hero.jpg" alt="Hero">
<p>Email: hello@testcafe.com</p>
<p>Phone: +1-555-0199</p>
</body></html>"""
        validator = FidelityValidator(sample_profile, manifest=empty_manifest)
        result = validator.validate(html)
        assert not result.valid
        assert "https://testcafe.com/hero.jpg" in result.broken_image_refs

    def test_fidelity_detects_missing_contact_fields_partial(self, sample_profile):
        """Partial contact (email present, phone missing) flagged correctly."""
        html = """<!DOCTYPE html>
<html><body>
<h1>Test Cafe</h1>
<p>Email: hello@testcafe.com</p>
</body></html>"""
        validator = FidelityValidator(sample_profile)
        result = validator.validate(html)
        assert not result.valid
        assert any(i.category == "missing_contact_phone" for i in result.issues)
        assert "hello@testcafe.com" in result.preserved_contact_emails
        assert len(result.preserved_contact_phones) == 0

    def test_fidelity_stats_are_recorded(self, sample_profile, sample_manifest):
        """Validate statistics fields are populated correctly."""
        html = """<!DOCTYPE html>
<html><body>
<h1>Test Cafe</h1>
<img src="https://testcafe.com/hero.jpg" alt="Hero">
<img src="https://testcafe.com/logo.png" alt="Logo">
<p>Email: hello@testcafe.com</p>
<p>Phone: +1-555-0199</p>
</body></html>"""
        validator = FidelityValidator(sample_profile, manifest=sample_manifest)
        result = validator.validate(html)
        assert result.source_contact_emails == ["hello@testcafe.com"]
        assert result.source_contact_phones == ["+1-555-0199"]
        assert result.preserved_contact_emails == ["hello@testcafe.com"]
        assert result.preserved_contact_phones == ["+1-555-0199"]
        assert result.source_service_count == 2
        assert result.source_meaningful_images == 2
        assert result.approved_image_count >= 2


class TestDesignProviderContract:
    """Tests for the DesignProvider interface and DesignProviderNotConfigured stub."""

    @pytest.mark.asyncio
    async def test_not_configured_provider_fails_gracefully(self, sample_profile, sample_manifest):
        """DesignProviderNotConfigured returns a structured failure — no dummy HTML."""
        from app.services.website_generator.design_provider import DesignProviderNotConfigured
        provider = DesignProviderNotConfigured()
        pkg = MarkdownPackage()
        pkg.asset_manifest = sample_manifest

        result = await provider.generate(sample_profile, pkg)

        assert result.success is False
        assert len(result.errors) > 0
        assert "not configured" in result.errors[0].lower() or "upgraded" in result.errors[0].lower()
        assert result.website_project is None

    @pytest.mark.asyncio
    async def test_not_configured_provider_name(self):
        """DesignProviderNotConfigured has the expected provider_name."""
        from app.services.website_generator.design_provider import DesignProviderNotConfigured
        provider = DesignProviderNotConfigured()
        assert provider.provider_name() == "not_configured"

    @pytest.mark.asyncio
    async def test_not_configured_no_generated_website_created(self, sample_profile):
        """No dummy GeneratedWebsite or WebsiteProject is created by the stub."""
        from app.services.website_generator.design_provider import DesignProviderNotConfigured
        provider = DesignProviderNotConfigured()
        pkg = MarkdownPackage()

        result = await provider.generate(sample_profile, pkg)

        assert result.website_project is None
        assert result.success is False
        # Verify no files were generated
        assert len(result.warnings) == 0

    def test_design_provider_is_abstract(self):
        """DesignProvider cannot be instantiated directly."""
        from app.services.website_generator.design_provider import DesignProvider
        with pytest.raises(TypeError):
            DesignProvider()


class TestPromptBudgetIntegration:
    """Integration tests for PromptBudgetController in the pipeline."""

    def test_prompt_budget_removes_duplicates(self):
        """Duplicate nav labels removed from prompt."""
        from app.services.website_generator.prompt_budget import PromptBudgetController
        from app.services.website_generator.schemas import PromptContext

        prompt = PromptContext(
            content_context="- **Home**\n- **About**\n- **Home**\n- **Contact**\n- **Home**",
            generation_constraints="test",
        )
        ctrl = PromptBudgetController()
        result, report = ctrl.apply(prompt)
        assert result.content_context.count("- **Home**") == 1
        assert report.chars_saved > 0

    def test_prompt_budget_preserves_business_content(self):
        """Business-critical content is preserved after budget control."""
        from app.services.website_generator.prompt_budget import PromptBudgetController
        from app.services.website_generator.schemas import PromptContext

        prompt = PromptContext(
            content_context=(
                "- **Home**\n- **About**\n- **Shop**\n- **Home**\n"
                "Welcome to Kiss the Hippo Coffee. We sell premium coffee beans.\n"
                "Contact us at info@kissthehippo.com.\n"
            ),
            generation_constraints="test",
        )
        ctrl = PromptBudgetController()
        result, report = ctrl.apply(prompt)
        assert "- **Home**" in result.content_context
        assert "Kiss the Hippo Coffee" in result.content_context
        assert "premium coffee beans" in result.content_context
        assert "info@kissthehippo.com" in result.content_context
        assert result.content_context.count("- **Home**") == 1

    def test_prompt_budget_shopify_boilerplate_removed(self):
        """Shopify boilerplate is stripped but business content remains."""
        from app.services.website_generator.prompt_budget import PromptBudgetController
        from app.services.website_generator.schemas import PromptContext

        prompt = PromptContext(
            content_context=(
                "Real business content here.\n"
                "Powered by Shopify\n"
                "Built with Shopify theme\n"
                "More real content.\n"
            ),
            generation_constraints="test",
        )
        ctrl = PromptBudgetController()
        result, report = ctrl.apply(prompt)
        assert "Real business content" in result.content_context
        assert "More real content" in result.content_context
        assert "Powered by Shopify" not in result.content_context
        assert report.chars_saved > 0

    def test_prompt_budget_only_affects_target_fields(self):
        """Rules/system contexts are not affected by content-specific cleanups."""
        from app.services.website_generator.prompt_budget import PromptBudgetController
        from app.services.website_generator.schemas import PromptContext

        prompt = PromptContext(
            content_context="- **Home**\n- **Home**\ncoffee",
            rules_context="- **Home**\n- **Home**\nbe good",
            system_context="- **Home**\nsetup",
            generation_constraints="test",
        )
        ctrl = PromptBudgetController()
        result, _ = ctrl.apply(prompt)
        # content_context should have dedup
        assert result.content_context.count("- **Home**") == 1
        # rules_context and system_context should NOT have dedup applied
        # (dedup only runs on content_context)
        assert result.rules_context == "- **Home**\n- **Home**\nbe good"
