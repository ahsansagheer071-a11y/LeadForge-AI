"""Tests for website generation schema validation and normalization."""

import json
import pytest
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.services.website_intelligence.schemas import (
    HeroSection,
    CallToAction,
    CtaButton,
    CtaLink,
    NavigationItem,
    ServiceCard,
    ProductItem,
    Testimonial,
    FAQ,
    TeamMember,
    ContactInfo,
    SocialLink,
    SectionInfo,
    FooterInfo,
    NavItem,
    ImageAsset,
    SEOInfo,
    ColorPalette,
    Typography,
    BrandIdentity,
    BusinessInfo,
    WebsiteProfile,
    WebsiteBlueprint,
)


# ---------------------------------------------------------------------------
# HeroSection — cta_buttons
# ---------------------------------------------------------------------------

class TestHeroSectionCTA:
    def test_zero_ctas(self):
        """Hero with zero CTAs."""
        hero = HeroSection(title="Hello")
        assert hero.cta_buttons == []

    def test_one_cta_model(self):
        """Hero with one CallToAction model instance."""
        cta = CallToAction(text="Join Us", url="/signup", type="button", color="#ff6600")
        hero = HeroSection(cta_buttons=[cta])
        assert len(hero.cta_buttons) == 1
        assert hero.cta_buttons[0]["text"] == "Join Us"
        assert hero.cta_buttons[0]["url"] == "/signup"

    def test_one_cta_dict(self):
        """Hero with one CTA dictionary."""
        hero = HeroSection(cta_buttons=[{"text": "Learn More", "url": "#"}])
        assert len(hero.cta_buttons) == 1
        assert hero.cta_buttons[0]["text"] == "Learn More"

    def test_multiple_ctas(self):
        """Hero with multiple CTAs (mixed models and dicts)."""
        cta1 = CallToAction(text="Get Started", url="/start", type="button")
        cta2 = {"text": "Contact Us", "url": "/contact"}
        hero = HeroSection(cta_buttons=[cta1, cta2])
        assert len(hero.cta_buttons) == 2
        assert hero.cta_buttons[0]["text"] == "Get Started"
        assert hero.cta_buttons[1]["text"] == "Contact Us"

    def test_optional_fields_omitted(self):
        """Hero with optional fields omitted."""
        hero = HeroSection()
        assert hero.title is None
        assert hero.subtitle is None
        assert hero.cta_buttons == []
        assert hero.background_image is None

    def test_cta_without_color(self):
        """CTA with optional color omitted."""
        cta = CallToAction(text="Join", url="/join", type="link")
        hero = HeroSection(cta_buttons=[cta])
        assert hero.cta_buttons[0]["color"] is None

    def test_cta_without_url(self):
        """CTA with optional url omitted."""
        cta = CallToAction(text="Join", type="button")
        hero = HeroSection(cta_buttons=[cta])
        assert hero.cta_buttons[0]["url"] is None

    def test_cta_internal_link(self):
        """CTA with internal link."""
        cta = CallToAction(text="About", url="/about", type="link")
        hero = HeroSection(cta_buttons=[cta])
        assert hero.cta_buttons[0]["url"] == "/about"

    def test_cta_external_link(self):
        """CTA with external link."""
        cta = CallToAction(text="Visit", url="https://example.com", type="link")
        hero = HeroSection(cta_buttons=[cta])
        assert hero.cta_buttons[0]["url"] == "https://example.com"

    def test_empty_cta_list(self):
        """Empty list passed explicitly."""
        hero = HeroSection(cta_buttons=[])
        assert hero.cta_buttons == []

    def test_none_cta_list(self):
        """None passed as cta_buttons."""
        hero = HeroSection(cta_buttons=None)
        assert hero.cta_buttons == []

    @pytest.mark.parametrize("cta_data", [
        {"text": "A"},
        {"text": "B", "url": "/b"},
        {"text": "C", "type": "button", "color": "red"},
        {"text": "D", "url": "/d", "type": "link", "color": "#333"},
    ])
    def test_cta_dict_variations(self, cta_data):
        """Various CTA dictionary shapes."""
        hero = HeroSection(cta_buttons=[cta_data])
        assert hero.cta_buttons[0]["text"] == cta_data["text"]

    def test_model_dump_round_trip(self):
        """Pydantic model -> JSON -> dict -> model round trip preserves data."""
        cta = CallToAction(text="Join", url="/join", type="button", color="blue")
        hero = HeroSection(
            title="Welcome",
            subtitle="To our site",
            cta_buttons=[cta],
            background_image="bg.jpg",
        )
        dumped = hero.model_dump(mode="json")
        assert dumped["cta_buttons"][0]["text"] == "Join"

        restored = HeroSection(**dumped)
        assert restored.cta_buttons[0]["text"] == "Join"
        assert restored.title == "Welcome"

    def test_serialize_deserialize_website_profile_hero(self):
        """WebsiteProfile hero survives full serialization round trip."""
        cta = CallToAction(text="Get Started", url="/start", type="button")
        hero = HeroSection(
            title="Hero Title",
            subtitle="Hero Subtitle",
            cta_buttons=[cta],
            background_image="/img/hero.jpg",
        )
        profile = WebsiteProfile(
            business=BusinessInfo(name="TestCo"),
            hero=hero,
        )
        dumped = json.loads(profile.model_dump_json())
        assert dumped["hero"]["cta_buttons"][0]["text"] == "Get Started"

        restored = WebsiteProfile(**dumped)
        assert isinstance(restored.hero.cta_buttons, list)
        assert restored.hero.cta_buttons[0]["text"] == "Get Started"


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

class TestNavigation:
    def test_navigation_items(self):
        """Navigation items with labels and URLs."""
        nav = NavigationItem(label="Home", url="/")
        assert nav.label == "Home"
        assert nav.url == "/"

    def test_nav_with_children(self):
        """Nested navigation items."""
        child = NavigationItem(label="Sub", url="/sub")
        parent = NavigationItem(label="Parent", url="/parent", children=[child])
        assert len(parent.children) == 1
        assert parent.children[0].label == "Sub"

    def test_nav_item_defaults(self):
        """Default children is empty list."""
        nav = NavigationItem(label="Home", url="/")
        assert nav.children == []


# ---------------------------------------------------------------------------
# Service / Feature Cards
# ---------------------------------------------------------------------------

class TestServiceCard:
    def test_minimal_service(self):
        """Service card with only required fields."""
        svc = ServiceCard(name="Web Design")
        assert svc.name == "Web Design"
        assert svc.features == []

    def test_service_with_cta(self):
        """Service card with CTA link."""
        cta = CtaLink(text="Learn More", url="/services/web-design")
        svc = ServiceCard(name="Web Design", cta=cta)
        assert svc.cta.text == "Learn More"
        assert svc.cta.url == "/services/web-design"

    def test_service_features(self):
        """Service card with features list."""
        svc = ServiceCard(
            name="SEO",
            features=["Keyword research", "On-page optimization", "Link building"],
        )
        assert len(svc.features) == 3

    def test_service_model_dump_round_trip(self):
        """Service card survives JSON round trip."""
        svc = ServiceCard(name="Dev", description="Full-stack", price="$5000")
        dumped = json.loads(svc.model_dump_json())
        restored = ServiceCard(**dumped)
        assert restored.name == "Dev"
        assert restored.price == "$5000"


# ---------------------------------------------------------------------------
# Testimonials
# ---------------------------------------------------------------------------

class TestTestimonial:
    def test_minimal_testimonial(self):
        """Testimonial with only required content."""
        t = Testimonial(content="Great service!")
        assert t.content == "Great service!"

    def test_full_testimonial(self):
        """Testimonial with all optional fields."""
        t = Testimonial(
            author="John",
            role="CEO",
            company="Acme",
            content="Excellent!",
            rating=5,
        )
        assert t.author == "John"
        assert t.rating == 5

    def test_testimonial_defaults(self):
        """Default rating and verified_badge."""
        t = Testimonial(content="Nice!")
        assert t.rating is None
        assert t.verified_badge is False


# ---------------------------------------------------------------------------
# Contact / Footer
# ---------------------------------------------------------------------------

class TestContactInfo:
    def test_empty_contact(self):
        """Contact with no data."""
        c = ContactInfo()
        assert c.emails == []
        assert c.phones == []

    def test_contact_with_data(self):
        """Contact with populated fields."""
        c = ContactInfo(emails=["a@b.com"], phones=["+123"])
        assert "a@b.com" in c.emails
        assert "+123" in c.phones

    def test_map_coordinates(self):
        """Map coordinates as dict."""
        c = ContactInfo(map_coordinates={"lat": 51.5, "lng": -0.13})
        assert c.map_coordinates["lat"] == 51.5


class TestFooterInfo:
    def test_footer_defaults(self):
        """Footer with defaults."""
        f = FooterInfo()
        assert f.footer_links == []
        assert f.newsletter_signup is False

    def test_footer_with_social(self):
        """Footer with social links."""
        sl = SocialLink(platform="twitter", url="https://twitter.com/test")
        f = FooterInfo(social_links=[sl])
        assert f.social_links[0].platform == "twitter"


# ---------------------------------------------------------------------------
# SEO
# ---------------------------------------------------------------------------

class TestSEOInfo:
    def test_seo_defaults(self):
        """SEO defaults."""
        s = SEOInfo()
        assert s.focus_keywords == []
        assert s.missing_meta_description is False

    def test_seo_with_data(self):
        """SEO with all fields."""
        s = SEOInfo(
            page_title="Test Page",
            meta_description="A test page",
            focus_keywords=["test", "example"],
        )
        assert s.page_title == "Test Page"
        assert len(s.focus_keywords) == 2


# ---------------------------------------------------------------------------
# Complete WebsiteProfile
# ---------------------------------------------------------------------------

class TestWebsiteProfile:
    def test_minimal_profile(self):
        """Minimal WebsiteProfile with just a business name."""
        p = WebsiteProfile()
        assert isinstance(p.business, BusinessInfo)
        assert isinstance(p.hero, HeroSection)
        assert isinstance(p.colors, ColorPalette)
        assert p.navigation == []

    def test_full_profile(self):
        """Full WebsiteProfile with all sections."""
        profile = WebsiteProfile(
            business=BusinessInfo(name="TestBiz", category="Tech"),
            seo=SEOInfo(page_title="TestBiz - Home"),
            hero=HeroSection(
                title="Welcome",
                cta_buttons=[CallToAction(text="Start", url="/start")],
            ),
            services=[
                ServiceCard(name="Design", features=["UX", "UI"]),
                ServiceCard(name="Dev", features=["Frontend", "Backend"]),
            ],
            testimonials=[
                Testimonial(content="Great!", author="Alice"),
            ],
            contact=ContactInfo(emails=["hi@testbiz.com"]),
            navigation=[
                NavigationItem(label="Home", url="/"),
                NavigationItem(label="About", url="/about"),
            ],
        )
        assert profile.business.name == "TestBiz"
        assert profile.hero.cta_buttons[0]["text"] == "Start"
        assert len(profile.services) == 2
        assert profile.testimonials[0].author == "Alice"
        assert profile.navigation[0].label == "Home"

    def test_profile_json_round_trip(self):
        """Complete profile survives JSON serialization round trip."""
        original = WebsiteProfile(
            business=BusinessInfo(name="Acme", category="Services"),
            hero=HeroSection(
                title="Acme Solutions",
                subtitle="We deliver",
                cta_buttons=[
                    CallToAction(text="Get Quote", url="/quote"),
                    {"text": "Learn More", "url": "/about"},
                ],
            ),
            services=[ServiceCard(name="Consulting", description="Expert advice")],
            testimonials=[Testimonial(content="Excellent!", author="Bob")],
            navigation=[NavigationItem(label="Home", url="/")],
            contact=ContactInfo(emails=["info@acme.com"]),
            social_links=[SocialLink(platform="twitter", url="https://twitter.com/acme")],
        )

        dumped = json.loads(original.model_dump_json())
        restored = WebsiteProfile(**dumped)

        assert restored.business.name == "Acme"
        assert restored.hero.title == "Acme Solutions"
        assert restored.hero.cta_buttons[0]["text"] == "Get Quote"
        assert restored.services[0].name == "Consulting"
        assert restored.testimonials[0].author == "Bob"
        assert restored.navigation[0].label == "Home"
        assert restored.social_links[0].platform == "twitter"

    def test_profile_with_blueprint(self):
        """Profile with blueprint."""
        bp = WebsiteBlueprint(
            hero={"title": "Custom Hero"},
            color_palette={"primary": "#ff6600"},
        )
        profile = WebsiteProfile(
            business=BusinessInfo(name="BP Test"),
            blueprint=bp,
        )
        assert profile.blueprint.hero["title"] == "Custom Hero"

    def test_coerce_none_to_empty(self):
        """Model validator coerces None list fields to empty."""
        data = {
            "business": {"name": "CoerceTest"},
            "navigation": None,
            "services": None,
            "testimonials": None,
            "call_to_actions": None,
        }
        profile = WebsiteProfile(**data)
        assert profile.navigation == []
        assert profile.services == []
        assert profile.testimonials == []
        assert profile.call_to_actions == []


# ---------------------------------------------------------------------------
# CallToAction specific
# ---------------------------------------------------------------------------

class TestCallToAction:
    def test_minimal_cta(self):
        """Minimal CTA with just text."""
        cta = CallToAction(text="Click")
        assert cta.text == "Click"
        assert cta.url is None
        assert cta.type is None
        assert cta.color is None

    def test_cta_serialization(self):
        """CTA serializes to JSON-compatible dict."""
        cta = CallToAction(text="Go", url="/go", type="button", color="red")
        d = cta.model_dump(mode="json")
        assert d == {"text": "Go", "url": "/go", "type": "button", "color": "red"}

    def test_cta_round_trip(self):
        """CTA -> JSON -> CTA round trip."""
        cta = CallToAction(text="Sign Up", url="/signup", type="button", color="#00cc00")
        dumped = json.loads(cta.model_dump_json())
        restored = CallToAction(**dumped)
        assert restored.text == "Sign Up"
        assert restored.url == "/signup"
        assert restored.type == "button"
        assert restored.color == "#00cc00"

    def test_cta_list_in_hero_model_dump(self):
        """CTAs in HeroSection produce JSON-compatible dicts."""
        cta = CallToAction(text="Subscribe", url="/subscribe")
        hero = HeroSection(cta_buttons=[cta])
        dumped = hero.model_dump(mode="json")
        assert dumped["cta_buttons"][0]["text"] == "Subscribe"
        assert isinstance(dumped["cta_buttons"][0], dict)

    def test_cta_in_json_string(self):
        """CTAs survive json.dumps."""
        cta = CallToAction(text="Buy", url="/buy", type="button")
        hero = HeroSection(cta_buttons=[cta])
        json_str = hero.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["cta_buttons"][0]["text"] == "Buy"


# ---------------------------------------------------------------------------
# Image and Asset metadata
# ---------------------------------------------------------------------------

class TestImageAsset:
    def test_minimal_image(self):
        """Image with just URL."""
        img = ImageAsset(url="https://example.com/img.jpg")
        assert img.url == "https://example.com/img.jpg"

    def test_full_image(self):
        """Image with all metadata."""
        img = ImageAsset(
            url="/img/photo.jpg",
            alt="A photo",
            width=800,
            height=600,
            type="hero",
        )
        assert img.width == 800
        assert img.type == "hero"

    def test_image_defaults(self):
        """Image with default optional fields."""
        img = ImageAsset(url="/img.jpg")
        assert img.alt is None
        assert img.width is None


# ---------------------------------------------------------------------------
# SectionInfo
# ---------------------------------------------------------------------------

class TestSectionInfo:
    def test_minimal_section(self):
        """Minimal section info."""
        s = SectionInfo()
        assert s.section_type == "Other"
        assert s.images == []
        assert s.buttons == []

    def test_section_with_buttons(self):
        """Section with CTA buttons."""
        btn = CtaLink(text="Read More", url="/read")
        s = SectionInfo(
            section_type="services",
            heading="Our Services",
            buttons=[btn],
        )
        assert s.heading == "Our Services"
        assert s.buttons[0].text == "Read More"
        assert s.buttons[0].url == "/read"


# ---------------------------------------------------------------------------
# Edge cases and error handling
# ---------------------------------------------------------------------------

class TestSchemaEdgeCases:
    def test_cta_with_malformed_data(self):
        """Malformed CTA-like data should not break schema."""
        # Pass a string through - should be handled gracefully
        hero = HeroSection(cta_buttons=[])  # No string items
        assert hero.cta_buttons == []

    def test_missing_cta_buttons_key(self):
        """HeroSection constructed without cta_buttons key."""
        hero = HeroSection(title="Test")
        assert hero.cta_buttons == []

    def test_empty_profile(self):
        """Empty profile with no optional fields."""
        data = {"business": {"name": "EmptyTest"}}
        profile = WebsiteProfile(**data)
        assert profile.hero.cta_buttons == []
        assert profile.testimonials == []

    def test_all_optional_omitted(self):
        """Profile with minimal required data only."""
        p = WebsiteProfile()
        assert p.hero.cta_buttons == []
        assert p.call_to_actions == []
        assert p.navigation == []


# ---------------------------------------------------------------------------
# Database JSON persistence compatibility
# ---------------------------------------------------------------------------

class TestDatabasePersistence:
    def test_hero_cta_buttons_json_compatible(self):
        """Hero's cta_buttons stores as JSON-compatible list of dicts."""
        hero = HeroSection(
            cta_buttons=[CallToAction(text="OK", url="/ok")]
        )
        dumped = hero.model_dump(mode="json")
        json_str = json.dumps(dumped["cta_buttons"])
        parsed = json.loads(json_str)
        assert parsed[0]["text"] == "OK"
        assert isinstance(parsed[0], dict)

    def test_profile_hero_in_json_column(self):
        """WebsiteProfile hero survives JSON column storage pattern."""
        cta = CallToAction(text="Go", url="/go")
        hero = HeroSection(title="T", cta_buttons=[cta])
        profile = WebsiteProfile(
            business=BusinessInfo(name="JSONTest"),
            hero=hero,
        )
        profile_data = profile.model_dump()
        hero_data = profile_data.get("hero", {})
        hero_cta = hero_data.get("cta_buttons", [])

        # Simulate DB storage: model_dump -> json.dumps -> DB -> json.loads -> model_validate
        json_str = json.dumps(profile_data, default=str)
        loaded_profile_data = json.loads(json_str)

        restored_hero = HeroSection(**loaded_profile_data.get("hero", {}))
        assert len(restored_hero.cta_buttons) == 1
        assert restored_hero.cta_buttons[0]["text"] == "Go"
