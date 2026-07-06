from typing import Dict, List


class WebsiteIntelligenceConstants:
    """
    Reusable constants for the Website Intelligence service.
    Centralises limits, defaults, and supported value sets.
    """

    # ----------------------------------------------------------
    # Maximum sections / counts
    # ----------------------------------------------------------
    MAX_NAVIGATION_DEPTH: int = 3
    MAX_NAVIGATION_ITEMS: int = 20
    MAX_SERVICE_CARDS: int = 20
    MAX_TESTIMONIALS: int = 50
    MAX_FAQ_ITEMS: int = 100
    MAX_TEAM_MEMBERS: int = 50
    MAX_IMAGES: int = 200
    MAX_SOCIAL_LINKS: int = 20
    MAX_BLOG_LINKS: int = 50
    MAX_CTA_BUTTONS: int = 20
    MAX_FONTS: int = 10
    MAX_CONTACT_EMAILS: int = 10
    MAX_CONTACT_PHONES: int = 10
    MAX_KEYWORDS: int = 20
    MAX_RAW_HTML_KB: int = 2048
    MAX_EXTRACTION_TIMEOUT_SECONDS: int = 60

    # ----------------------------------------------------------
    # Default colors (hex)
    # ----------------------------------------------------------
    DEFAULT_PRIMARY_COLOR: str = "#2563EB"
    DEFAULT_SECONDARY_COLOR: str = "#64748B"
    DEFAULT_ACCENT_COLOR: str = "#F59E0B"
    DEFAULT_BACKGROUND_COLOR: str = "#FFFFFF"
    DEFAULT_TEXT_COLOR: str = "#0F172A"

    DEFAULT_COLORS: Dict[str, str] = {
        "primary": DEFAULT_PRIMARY_COLOR,
        "secondary": DEFAULT_SECONDARY_COLOR,
        "accent": DEFAULT_ACCENT_COLOR,
        "background": DEFAULT_BACKGROUND_COLOR,
        "text": DEFAULT_TEXT_COLOR,
    }

    # ----------------------------------------------------------
    # Supported industries
    # ----------------------------------------------------------
    SUPPORTED_INDUSTRIES: List[str] = [
        "restaurant",
        "retail",
        "healthcare",
        "legal",
        "real_estate",
        "construction",
        "technology",
        "education",
        "hospitality",
        "automotive",
        "fitness",
        "beauty",
        "financial_services",
        "manufacturing",
        "logistics",
        "agriculture",
        "energy",
        "media",
        "entertainment",
        "nonprofit",
        "other",
    ]

    # ----------------------------------------------------------
    # Supported languages (ISO 639-1)
    # ----------------------------------------------------------
    SUPPORTED_LANGUAGES: List[str] = [
        "en", "es", "fr", "de", "it", "pt", "nl", "ru",
        "ja", "ko", "zh", "ar", "hi", "tr", "pl", "sv",
        "da", "fi", "no", "cs", "ro", "hu", "el", "he",
        "th", "vi", "id", "ms",
    ]

    # ----------------------------------------------------------
    # Reserved route patterns
    # ----------------------------------------------------------
    RESERVED_ROUTES: List[str] = [
        "/admin",
        "/api",
        "/login",
        "/register",
        "/logout",
        "/dashboard",
        "/settings",
        "/profile",
        "/cart",
        "/checkout",
        "/account",
        "/search",
        "/404",
        "/500",
        "/robots.txt",
        "/sitemap.xml",
        "/favicon.ico",
    ]

    # ----------------------------------------------------------
    # Section keys used in WebsiteProfile
    # ----------------------------------------------------------
    PROFILE_SECTION_KEYS: List[str] = [
        "business",
        "brand",
        "seo",
        "colors",
        "typography",
        "navigation",
        "hero",
        "services",
        "contact",
        "images",
        "testimonials",
        "faqs",
        "team",
        "blog_links",
        "social_links",
        "call_to_actions",
        "statistics",
        "website_summary",
    ]


website_intelligence_constants = WebsiteIntelligenceConstants()