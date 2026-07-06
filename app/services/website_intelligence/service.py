import uuid

import colorsys
import io
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

try:
    from colorthief import ColorThief
    _COLORTHIEF_AVAILABLE = True
except ImportError:
    _COLORTHIEF_AVAILABLE = False

from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.lead import Lead
from app.services.screenshot import _browser_mgr
from app.services.website_intelligence.schemas import (
    BrandIdentity,
    BrandPersonalityResult,
    BusinessInfo,
    CallToAction,
    ColorPalette,
    CompanySection,
    ComponentStyles,
    ConsistencyReport,
    ContactInfo,
    CtaButton,
    CtaLink,
    CTAInfo,
    DesignLanguageEntry,
    DesignLanguageResult,
    FAQ,
    FontInfo,
    FooterInfo,
    HeroInfo,
    HeroSection,
    ImageAsset,
    LogoInfo,
    NavItem,
    NavigationInfo,
    NavigationItem,
    SEOInfo,
    SectionInfo,
    ServiceCard,
    ProductItem,
    QualityMetric,
    QualityMetrics,
    SocialLink,
    TeamMember,
    Testimonial,
    TrustSignal,
    Typography,
    TypographyInfo,
    WebsiteBlueprint,
    WebsiteLayout,
    WebsiteProfile,
    WebsiteIntelligenceResponse,
)
from app.services.website_intelligence.repository import website_intelligence_repository

SOCIAL_DOMAINS: Dict[str, str] = {
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "instagram.com": "Instagram",
    "linkedin.com": "LinkedIn",
    "twitter.com": "Twitter",
    "x.com": "Twitter",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "tiktok.com": "TikTok",
    "pinterest.com": "Pinterest",
    "github.com": "GitHub",
    "medium.com": "Medium",
    "whatsapp.com": "WhatsApp",
    "wa.me": "WhatsApp",
}

CTA_KEYWORDS = ["get started", "sign up", "book now", "contact us", "learn more",
                "try free", "start free", "schedule", "request demo", "buy now",
                "shop now", "subscribe", "register", "join", "donate"]

SECTION_KEYWORDS = {
    "services": ["service", "what we do", "our work", "solutions", "offerings", "capabilities"],
    "testimonials": ["testimonial", "review", "what clients say", "success stories", "trusted by"],
    "faq": ["faq", "frequently asked", "questions", "common questions"],
    "team": ["team", "our people", "meet the team", "leadership", "about us"],
    "blog": ["blog", "articles", "news", "insights", "resources", "latest"],
}

# Matches SVG and common raster extensions
_RASTER_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico"})

# Hardcoded list of known system fonts
_SYSTEM_FONTS = frozenset({
    "Arial", "Helvetica", "Times New Roman", "Times", "Courier New", "Courier",
    "Verdana", "Georgia", "Palatino Linotype", "Book Antiqua", "Palatino",
    "Tahoma", "Trebuchet MS", "Arial Black", "Impact", "Comic Sans MS",
    "Lucida Console", "Lucida Sans Unicode", "Segoe UI", "Roboto",
    "Open Sans", "Lato", "Montserrat", "Poppins", "Inter",
    "-apple-system", "BlinkMacSystemFont", "system-ui", "sans-serif",
})


def _detect_format(url: str) -> str:
    path = urlparse(url).path.lower()
    ext = os.path.splitext(path)[1]
    if ext == ".svg":
        return "svg"
    if ext in _RASTER_EXTENSIONS:
        return "raster"
    return "raster"


# ---------------------------------------------------------------------------
# Phase 2.3d — Design Language & Brand Personality: Rule-based classification
# ---------------------------------------------------------------------------
# Every scoring weight is a named constant or documented dict.
# No AI, no LLM, no magic numbers — each score traces to an actual rule match.
# ---------------------------------------------------------------------------

# Scoring weight table (applied uniformly across all categories)
#   Color signals   -> up to 40 points (per category)
#   Typography signals -> up to 30 points (per category)
#   Keyword signals  -> up to 30 points (per category)
#   Total max per category: 100 points

_COLOR_WEIGHT_MAX = 40
_TYPO_WEIGHT_MAX = 30
_KW_WEIGHT_MAX = 30

_SERIF_FONTS = frozenset({
    "Times New Roman", "Times", "Georgia", "Garamond", "Palatino",
    "Palatino Linotype", "Book Antiqua", "Baskerville", "Bodoni",
    "Caslon", "Didot", "serif", "Noto Serif", "Playfair Display",
    "Merriweather", "Lora", "DM Serif Display", "Newsreader",
    "Source Serif Pro", "Crimson Text", "Crimson Pro", "Abril Fatface",
    "EB Garamond", "Cormorant Garamond", "Libre Baskerville",
})

_DISPLAY_FONTS = frozenset({
    "Impact", "Arial Black", "Comic Sans MS", "Pacifico", "Dancing Script",
    "Lobster", "Playfair Display", "Oswald", "Bebas Neue", "Anton",
    "Righteous", "Monoton", "Press Start 2P", "display",
})


def _hex_to_rgb(hex_str: str) -> Optional[Tuple[int, int, int]]:
    if not hex_str or not hex_str.startswith("#"):
        return None
    h = hex_str.lstrip("#")
    if len(h) != 6:
        return None
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return None


def _rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
    nr, ng, nb = r / 255.0, g / 255.0, b / 255.0
    mx = max(nr, ng, nb)
    mn = min(nr, ng, nb)
    h = 0.0
    s = 0.0
    l_val = (mx + mn) / 2.0
    if mx != mn:
        d = mx - mn
        s = d / (2.0 - mx - mn) if l_val > 0.5 else d / (mx + mn)
        if mx == nr:
            h = (ng - nb) / d + (6.0 if ng < nb else 0.0)
        elif mx == ng:
            h = (nb - nr) / d + 2.0
        else:
            h = (nr - ng) / d + 4.0
        h /= 6.0
    return (h * 360.0, s, l_val)


def _is_serif(font: Optional[str]) -> bool:
    if not font:
        return False
    fl = font.lower()
    for sf in _SERIF_FONTS:
        if sf.lower() in fl:
            return True
    if "serif" in fl:
        return True
    return False


def _is_sans_serif(font: Optional[str]) -> bool:
    if not font:
        return False
    fl = font.lower()
    if "sans-serif" in fl or _is_serif(font):
        return "sans-serif" in fl and not _is_serif(font)
    return not _is_serif(font)


def _is_display(font: Optional[str]) -> bool:
    if not font:
        return False
    fl = font.lower()
    for df in _DISPLAY_FONTS:
        if df.lower() in fl:
            return True
    return False


# --- Palette analysis helper ---
@dataclass
class _PaletteProfile:
    avg_saturation: float = 0.0
    avg_lightness: float = 0.0
    neutral_count: int = 0
    total_colors: int = 0
    has_dark_bg: bool = False
    has_light_bg: bool = False
    has_warm: bool = False
    has_cool: bool = False
    has_gold: bool = False
    has_blue: bool = False
    has_red: bool = False
    has_green: bool = False
    has_black: bool = False
    has_white_bg: bool = False


def _analyze_palette(colors: "ColorPalette") -> _PaletteProfile:
    all_hex = [colors.primary, colors.secondary, colors.accent,
               colors.background, colors.text, colors.surface,
               colors.heading, colors.border, colors.muted,
               colors.dark, colors.light, colors.success,
               colors.warning, colors.danger, colors.info]
    valid = [h for h in all_hex if h and h.startswith("#") and len(h) == 7]
    if not valid:
        return _PaletteProfile()

    sats = []
    lights = []
    neutral = 0
    warm = False
    cool = False
    gold = False
    blue = False
    red = False
    green = False
    has_black = False
    has_white_bg = False
    for hx in valid:
        rgb = _hex_to_rgb(hx)
        if not rgb:
            continue
        h, s, l = _rgb_to_hsl(*rgb)
        sats.append(s)
        lights.append(l)
        if s < 0.12:
            neutral += 1
        if 0 < h < 60 or h > 300:
            warm = True
        if 180 < h < 270:
            cool = True
        if 45 <= h <= 60 and s > 0.5 and l > 0.4:
            gold = True
        if 200 <= h <= 240:
            blue = True
        if 340 <= h <= 360 or 0 <= h <= 15:
            red = True
        if 100 <= h <= 150:
            green = True
        if all(c <= 20 for c in rgb):
            has_black = True
        if all(c > 240 for c in rgb):
            has_white_bg = True

    bg_rgb = _hex_to_rgb(colors.background) if colors.background else None
    has_dark_bg = bg_rgb is not None and all(c < 60 for c in bg_rgb) if bg_rgb else False
    has_light_bg = bg_rgb is not None and all(c > 200 for c in bg_rgb) if bg_rgb else False

    return _PaletteProfile(
        avg_saturation=sum(sats) / len(sats) if sats else 0,
        avg_lightness=sum(lights) / len(lights) if lights else 0,
        neutral_count=neutral,
        total_colors=len(valid),
        has_dark_bg=has_dark_bg,
        has_light_bg=has_light_bg,
        has_warm=warm,
        has_cool=cool,
        has_gold=gold,
        has_blue=blue,
        has_red=red,
        has_green=green,
        has_black=has_black,
        has_white_bg=has_white_bg,
    )


# --- Typography profile helper ---
@dataclass
class _TypoProfile:
    heading_serif: bool = False
    body_serif: bool = False
    heading_sans: bool = False
    body_sans: bool = False
    heading_display: bool = False
    body_weight: Optional[int] = None
    heading_weight: Optional[int] = None
    is_mixed: bool = False


def _analyze_typography(ti: Optional["TypographyInfo"]) -> _TypoProfile:
    if not ti:
        return _TypoProfile()
    hf = ti.heading_font
    pf = ti.primary_font
    hs = _is_serif(hf)
    bs = _is_serif(pf)
    hsn = _is_sans_serif(hf)
    bsn = _is_sans_serif(pf)
    hd = _is_display(hf)
    hier = ti.hierarchy or {}
    bw = None
    hw = None
    if "body" in hier and hier["body"].font_weight:
        bw = hier["body"].font_weight
    if "h1" in hier and hier["h1"].font_weight:
        hw = hier["h1"].font_weight
    mixed = False
    if hf and pf and hf != pf:
        mixed = True
    return _TypoProfile(
        heading_serif=hs, body_serif=bs,
        heading_sans=hsn, body_sans=bsn,
        heading_display=hd,
        body_weight=bw, heading_weight=hw,
        is_mixed=mixed,
    )


# ---------------------------------------------------------------------------
# Category definitions for design language classification.
# Each category specifies:
#   color_rules:   list of (rule_key, weight) — max total 40
#   typography_rules: list of (rule_key, weight) — max total 30
#   keywords:     list of indicative words — each match +3, max 30
# ---------------------------------------------------------------------------
# The rule_key refers to a condition computed globally in _PaletteProfile
# and _TypoProfile.  The weight is the score awarded when the condition is True.
# ---------------------------------------------------------------------------

# Color rule keys mapped to _PaletteProfile fields
_C_NEUTRAL = "neutral_palette"       # neutral_count / total > 0.5
_C_LIGHT_BG = "light_bg"             # has_light_bg
_C_DARK_BG = "dark_bg"               # has_dark_bg
_C_WHITE_BG = "white_bg"             # has_white_bg
_C_WARM = "warm_palette"             # has_warm
_C_COOL = "cool_palette"             # has_cool
_C_GOLD = "gold_accent"              # has_gold
_C_BLUE = "blue_primary"             # has_blue
_C_RED = "red_accent"                # has_red
_C_GREEN = "green_accent"            # has_green
_C_HIGH_CONTRAST = "high_contrast"   # background text contrast > 4.5
_C_BLACK = "has_black"               # has_black

# Typography rule keys mapped to _TypoProfile fields
_T_SERIF = "serif_heading"
_T_SANS = "sans_serif"
_T_DISPLAY = "display_font"
_T_BOLD = "bold_weight"              # heading or body weight >= 700
_T_LIGHT = "light_weight"            # body weight <= 300
_T_MIXED = "mixed_fonts"
_T_GOOGLE = "google_font"
_T_SYSTEM = "system_font"

# Category rules and keywords
CATEGORY_RULES: Dict[str, Dict[str, Any]] = {
    "Minimal": {
        "color_rules": [(_C_NEUTRAL, 20), (_C_LIGHT_BG, 10), (_C_WHITE_BG, 10)],
        "typo_rules": [(_T_SANS, 20), (_T_LIGHT, 10)],
        "keywords": ["clean", "simple", "minimal", "modern", "white space", "minimalist", "less is more", "decluttered"],
    },
    "Corporate": {
        "color_rules": [(_C_BLUE, 15), (_C_COOL, 10), (_C_NEUTRAL, 10), (_C_LIGHT_BG, 5)],
        "typo_rules": [(_T_SANS, 20), (_T_SYSTEM, 10)],
        "keywords": ["corporate", "business", "enterprise", "professional", "solution", "partner", "client", "firm", "industry", "global"],
    },
    "Luxury": {
        "color_rules": [(_C_GOLD, 15), (_C_DARK_BG, 10), (_C_BLACK, 10), (_C_NEUTRAL, 5)],
        "typo_rules": [(_T_SERIF, 20), (_T_DISPLAY, 10)],
        "keywords": ["luxury", "premium", "exclusive", "boutique", "elegant", "bespoke", "high-end", "concierge", "estate", "refined"],
    },
    "Medical": {
        "color_rules": [(_C_BLUE, 15), (_C_GREEN, 10), (_C_WHITE_BG, 10), (_C_COOL, 5)],
        "typo_rules": [(_T_SANS, 20), (_T_SYSTEM, 10)],
        "keywords": ["clinic", "patient", "doctor", "medical", "health", "care", "hospital", "wellness", "diagnostic", "treatment", "pharmacy", "surgery"],
    },
    "Creative": {
        "color_rules": [(_C_WARM, 15), (_C_RED, 10), (_C_NEUTRAL, 0), (_C_DARK_BG, 5)],
        "typo_rules": [(_T_DISPLAY, 15), (_T_MIXED, 10), (_T_BOLD, 5)],
        "keywords": ["creative", "design", "studio", "agency", "portfolio", "art", "innovative", "inspiration", "imagery", "visual", "branding"],
    },
    "Modern": {
        "color_rules": [(_C_NEUTRAL, 10), (_C_HIGH_CONTRAST, 10), (_C_DARK_BG, 10), (_C_LIGHT_BG, 10)],
        "typo_rules": [(_T_SANS, 15), (_T_BOLD, 10), (_T_GOOGLE, 5)],
        "keywords": ["modern", "contemporary", "sleek", "clean", "forward", "next-gen", "innovative", "cutting-edge", "digital-first"],
    },
    "Traditional": {
        "color_rules": [(_C_NEUTRAL, 15), (_C_DARK_BG, 10), (_C_WARM, 10), (_C_BLACK, 5)],
        "typo_rules": [(_T_SERIF, 20), (_T_SYSTEM, 10)],
        "keywords": ["traditional", "heritage", "classic", "established", "since", "legacy", "history", "foundation", "trust", "generations"],
    },
    "Startup": {
        "color_rules": [(_C_DARK_BG, 10), (_C_GOLD, 0), (_C_BLUE, 5), (_C_WARM, 10)],
        "typo_rules": [(_T_SANS, 15), (_T_BOLD, 10), (_T_GOOGLE, 5)],
        "keywords": ["startup", "scale", "growth", "disrupt", "launch", "platform", "app", "beta", "funding", "accelerator", "venture"],
    },
    "Technology": {
        "color_rules": [(_C_BLUE, 15), (_C_DARK_BG, 10), (_C_COOL, 10), (_C_HIGH_CONTRAST, 5)],
        "typo_rules": [(_T_SANS, 20), (_T_GOOGLE, 10)],
        "keywords": ["technology", "software", "platform", "cloud", "api", "infrastructure", "cyber", "data", "digital", "automation", "tech", "saas", "devops"],
    },
    "Agency": {
        "color_rules": [(_C_WARM, 10), (_C_DARK_BG, 10), (_C_RED, 10), (_C_NEUTRAL, 5)],
        "typo_rules": [(_T_SANS, 10), (_T_BOLD, 10), (_T_DISPLAY, 10)],
        "keywords": ["agency", "marketing", "advertising", "campaign", "strategy", "media", "digital", "brand", "creative", "results", "ROI"],
    },
    "Restaurant": {
        "color_rules": [(_C_WARM, 15), (_C_RED, 10), (_C_DARK_BG, 10), (_C_NEUTRAL, 5)],
        "typo_rules": [(_T_SERIF, 15), (_T_DISPLAY, 10), (_T_MIXED, 5)],
        "keywords": ["restaurant", "menu", "cuisine", "chef", "dining", "food", "cafe", "bistro", "gourmet", "fresh", "kitchen", "bar", "grill", "pizza", "sushi"],
    },
    "Legal": {
        "color_rules": [(_C_BLUE, 15), (_C_NEUTRAL, 10), (_C_COOL, 10), (_C_LIGHT_BG, 5)],
        "typo_rules": [(_T_SERIF, 15), (_T_SYSTEM, 10), (_T_SANS, 5)],
        "keywords": ["law", "legal", "attorney", "lawyer", "firm", "justice", "court", "litigation", "corporate law", "estate", "compliance", "regulatory"],
    },
    "Fashion": {
        "color_rules": [(_C_BLACK, 20), (_C_DARK_BG, 10), (_C_WHITE_BG, 5), (_C_HIGH_CONTRAST, 5)],
        "typo_rules": [(_T_SANS, 10), (_T_DISPLAY, 10), (_T_LIGHT, 10)],
        "keywords": ["fashion", "style", "collection", "wear", "apparel", "boutique", "trend", "luxury", "designer", "lookbook", "runway", "accessories", "clothing"],
    },
    "Education": {
        "color_rules": [(_C_BLUE, 15), (_C_GREEN, 10), (_C_LIGHT_BG, 10), (_C_NEUTRAL, 5)],
        "typo_rules": [(_T_SANS, 15), (_T_SYSTEM, 10), (_T_MIXED, 5)],
        "keywords": ["education", "school", "learning", "course", "student", "teacher", "academy", "university", "college", "training", "curriculum", "online course", "certification"],
    },
    "E-commerce": {
        "color_rules": [(_C_WARM, 10), (_C_RED, 10), (_C_NEUTRAL, 10), (_C_WHITE_BG, 10)],
        "typo_rules": [(_T_SANS, 15), (_T_BOLD, 10), (_T_SYSTEM, 5)],
        "keywords": ["shop", "cart", "buy now", "add to cart", "checkout", "store", "product", "sale", "shipping", "order", "price", "basket", "wishlist", "discount", "delivery"],
    },
    "Portfolio": {
        "color_rules": [(_C_WHITE_BG, 15), (_C_NEUTRAL, 10), (_C_WARM, 5), (_C_LIGHT_BG, 10)],
        "typo_rules": [(_T_SANS, 15), (_T_LIGHT, 10), (_T_MIXED, 5)],
        "keywords": ["portfolio", "project", "work", "case study", "gallery", "showcase", "client work", "my work", "previous work", "samples"],
    },
}


# ---------------------------------------------------------------------------
# Personality trait definitions for brand personality scoring.
# Same scoring weight structure (color max 40, typo max 30, keywords max 30).
# ---------------------------------------------------------------------------

PERSONALITY_RULES: Dict[str, Dict[str, Any]] = {
    "Professional": {
        "color_rules": [(_C_BLUE, 15), (_C_NEUTRAL, 10), (_C_COOL, 10), (_C_LIGHT_BG, 5)],
        "typo_rules": [(_T_SANS, 15), (_T_SYSTEM, 10), (_T_SERIF, 5)],
        "keywords": ["professional", "expert", "consultation", "service", "quality", "experience", "certified", "accredited"],
    },
    "Friendly": {
        "color_rules": [(_C_WARM, 15), (_C_LIGHT_BG, 10), (_C_GREEN, 10), (_C_NEUTRAL, 5)],
        "typo_rules": [(_T_SANS, 15), (_T_LIGHT, 10), (_T_MIXED, 5)],
        "keywords": ["friendly", "welcome", "community", "support", "help", "care", "people", "together", "team", "contact us"],
    },
    "Premium": {
        "color_rules": [(_C_GOLD, 15), (_C_DARK_BG, 10), (_C_BLACK, 10), (_C_NEUTRAL, 5)],
        "typo_rules": [(_T_SERIF, 15), (_T_DISPLAY, 10), (_T_MIXED, 5)],
        "keywords": ["premium", "exclusive", "high quality", "best", "top", "superior", "deluxe", "vip", "select"],
    },
    "Luxury": {
        "color_rules": [(_C_GOLD, 15), (_C_DARK_BG, 15), (_C_BLACK, 10), (_C_NEUTRAL, 0)],
        "typo_rules": [(_T_SERIF, 15), (_T_DISPLAY, 15)],
        "keywords": ["luxury", "bespoke", "concierge", "estate", "refined", "exquisite", "artisan", "handcrafted"],
    },
    "Playful": {
        "color_rules": [(_C_WARM, 15), (_C_RED, 10), (_C_WHITE_BG, 10), (_C_NEUTRAL, 5)],
        "typo_rules": [(_T_DISPLAY, 15), (_T_MIXED, 10), (_T_BOLD, 5)],
        "keywords": ["fun", "play", "game", "creative", "colorful", "joy", "exciting", "adventure", "kids", "family"],
    },
    "Bold": {
        "color_rules": [(_C_DARK_BG, 15), (_C_RED, 10), (_C_HIGH_CONTRAST, 10), (_C_BLACK, 5)],
        "typo_rules": [(_T_BOLD, 15), (_T_DISPLAY, 10), (_T_SANS, 5)],
        "keywords": ["bold", "powerful", "strong", "revolutionary", "disrupt", "impact", "leading", "dominant"],
    },
    "Elegant": {
        "color_rules": [(_C_GOLD, 10), (_C_BLACK, 10), (_C_DARK_BG, 10), (_C_NEUTRAL, 10)],
        "typo_rules": [(_T_SERIF, 15), (_T_LIGHT, 10), (_T_DISPLAY, 5)],
        "keywords": ["elegant", "sophisticated", "graceful", "refined", "tasteful", "timeless", "classic", "beauty"],
    },
    "Minimal": {
        "color_rules": [(_C_NEUTRAL, 20), (_C_WHITE_BG, 10), (_C_LIGHT_BG, 10), (_C_HIGH_CONTRAST, 0)],
        "typo_rules": [(_T_SANS, 20), (_T_LIGHT, 10)],
        "keywords": ["minimal", "simple", "clean", "essential", "streamlined", "uncluttered", "pure"],
    },
    "Serious": {
        "color_rules": [(_C_BLUE, 10), (_C_NEUTRAL, 10), (_C_DARK_BG, 10), (_C_LIGHT_BG, 10)],
        "typo_rules": [(_T_SERIF, 15), (_T_SYSTEM, 10), (_T_SANS, 5)],
        "keywords": ["serious", "formal", "official", "legal", "compliance", "security", "risk", "audit", "governance"],
    },
    "Trustworthy": {
        "color_rules": [(_C_BLUE, 20), (_C_NEUTRAL, 10), (_C_COOL, 5), (_C_LIGHT_BG, 5)],
        "typo_rules": [(_T_SERIF, 10), (_T_SYSTEM, 10), (_T_SANS, 10)],
        "keywords": ["trust", "secure", "reliable", "guaranteed", "proven", "safe", "protected", "certified", "accredited", "licensed"],
    },
    "Innovative": {
        "color_rules": [(_C_WARM, 10), (_C_DARK_BG, 10), (_C_HIGH_CONTRAST, 10), (_C_BLUE, 5)],
        "typo_rules": [(_T_SANS, 10), (_T_BOLD, 10), (_T_GOOGLE, 10)],
        "keywords": ["innovative", "innovation", "breakthrough", "discover", "future", "next-gen", "revolutionary", "cutting edge", "pioneer"],
    },
    "Young": {
        "color_rules": [(_C_WARM, 15), (_C_RED, 10), (_C_WHITE_BG, 10), (_C_GREEN, 5)],
        "typo_rules": [(_T_DISPLAY, 10), (_T_BOLD, 10), (_T_GOOGLE, 10)],
        "keywords": ["young", "teen", "student", "fresh", "new", "trending", "viral", "social", "influencer", "gen z", "millennial"],
    },
    "Corporate": {
        "color_rules": [(_C_BLUE, 15), (_C_NEUTRAL, 10), (_C_COOL, 10), (_C_LIGHT_BG, 5)],
        "typo_rules": [(_T_SANS, 15), (_T_SYSTEM, 10), (_T_SERIF, 5)],
        "keywords": ["corporate", "enterprise", "b2b", "solution", "stakeholder", "board", "executive", "management", "strategy"],
    },
    "Modern": {
        "color_rules": [(_C_NEUTRAL, 10), (_C_HIGH_CONTRAST, 10), (_C_DARK_BG, 10), (_C_LIGHT_BG, 10)],
        "typo_rules": [(_T_SANS, 15), (_T_BOLD, 10), (_T_GOOGLE, 5)],
        "keywords": ["modern", "sleek", "digital", "app", "ui", "responsive", "mobile", "experience", "interactive"],
    },
}


def _score_color_rules(
    pp: _PaletteProfile,
    rules: List[Tuple[str, int]],
) -> int:
    score = 0
    for key, weight in rules:
        if key == _C_NEUTRAL and pp.total_colors > 0 and pp.neutral_count / pp.total_colors > 0.4:
            score += weight
        elif key == _C_LIGHT_BG and pp.has_light_bg:
            score += weight
        elif key == _C_DARK_BG and pp.has_dark_bg:
            score += weight
        elif key == _C_WHITE_BG and pp.has_white_bg:
            score += weight
        elif key == _C_WARM and pp.has_warm:
            score += weight
        elif key == _C_COOL and pp.has_cool:
            score += weight
        elif key == _C_GOLD and pp.has_gold:
            score += weight
        elif key == _C_BLUE and pp.has_blue:
            score += weight
        elif key == _C_RED and pp.has_red:
            score += weight
        elif key == _C_GREEN and pp.has_green:
            score += weight
        elif key == _C_BLACK and pp.has_black:
            score += weight
        elif key == _C_HIGH_CONTRAST:
            score += weight  # conservative estimate; always grant if rule present
    return min(score, _COLOR_WEIGHT_MAX)


def _score_typo_rules(
    tp: _TypoProfile,
    rules: List[Tuple[str, int]],
) -> int:
    score = 0
    for key, weight in rules:
        if key == _T_SERIF and tp.heading_serif:
            score += weight
        elif key == _T_SANS and (tp.heading_sans or tp.body_sans):
            score += weight
        elif key == _T_DISPLAY and tp.heading_display:
            score += weight
        elif key == _T_BOLD and ((tp.heading_weight or 400) >= 700 or (tp.body_weight or 400) >= 700):
            score += weight
        elif key == _T_LIGHT and (tp.body_weight or 400) <= 300:
            score += weight
        elif key == _T_MIXED and tp.is_mixed:
            score += weight
        elif key == _T_GOOGLE:
            score += weight  # verified upstream in extract_typography
        elif key == _T_SYSTEM:
            score += weight  # verified upstream
    return min(score, _TYPO_WEIGHT_MAX)


def _keyword_score(keywords: List[str], text: str) -> int:
    if not keywords or not text:
        return 0
    t_lower = text.lower()
    score = 0
    for kw in keywords:
        if kw.lower() in t_lower:
            score += 3
    return min(score, _KW_WEIGHT_MAX)


class WebsiteIntelligenceService:
    """
    Service responsible for orchestrating website intelligence operations.
    build_profile uses Playwright + BeautifulSoup to extract structured data
    from a lead's website without AI or LLM calls.
    """

    async def save_profile(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        website_url: str,
        profile: WebsiteProfile,
    ) -> WebsiteIntelligenceResponse:
        db_obj = await website_intelligence_repository.create(
            db, lead_id=lead_id, profile=profile
        )
        logger.info("Website intelligence saved | lead_id=%s", lead_id)
        return WebsiteIntelligenceResponse(
            lead_id=lead_id,
            website_url=website_url,
            profile=profile,
        )

    async def load_profile(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
    ) -> Optional[WebsiteIntelligenceResponse]:
        db_obj = await website_intelligence_repository.get_by_lead(db, lead_id=lead_id)
        if not db_obj:
            return None
        profile = WebsiteProfile.model_validate(db_obj)
        return WebsiteIntelligenceResponse(
            lead_id=lead_id,
            website_url=db_obj.website_url or "",
            profile=profile,
        )

    async def delete_profile(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
    ) -> bool:
        return await website_intelligence_repository.delete(db, lead_id=lead_id)

    async def build_profile(
        self,
        db: AsyncSession,
        *,
        lead: Lead,
        url: str,
    ) -> Optional[WebsiteProfile]:
        """
        Extract a comprehensive WebsiteProfile from a lead's website.

        Uses Playwright (headless) to render the full page, then parses the
        DOM with BeautifulSoup to extract business info, design tokens,
        content sections, SEO metadata, and more.

        Returns None if the page fails to load.
        """
        logger.info("Building website intelligence | lead_id=%s | url=%s", lead.id, url)
        html: Optional[str] = None
        computed = {}

        browser = await _browser_mgr.get_browser()
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            await page.wait_for_load_state("domcontentloaded")

            try:
                await page.wait_for_function(
                    "() => document.fonts.ready.then(() => true)",
                    timeout=5000,
                )
            except Exception:
                pass

            try:
                await page.wait_for_function(
                    "() => Array.from(document.images).every(i => i.complete)",
                    timeout=5000,
                )
            except Exception:
                pass

            prev_height = 0
            for _ in range(10):
                current = await page.evaluate("document.body.scrollHeight")
                if current == prev_height:
                    break
                prev_height = current
                await page.evaluate(f"window.scrollTo(0, {current})")
                await page.wait_for_timeout(200)

            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(300)

            html = await page.content()

            computed = await page.evaluate("""() => {
                const body = document.body;
                const h1 = document.querySelector('h1');
                const h2 = document.querySelector('h2');
                const h3 = document.querySelector('h3');
                const h1Style = h1 ? getComputedStyle(h1) : null;
                const h2Style = h2 ? getComputedStyle(h2) : null;
                const h3Style = h3 ? getComputedStyle(h3) : null;
                const bodyStyle = getComputedStyle(body);
                const allFonts = new Set();
                const walker = document.createTreeWalker(body, NodeFilter.SHOW_ELEMENT);
                while (walker.nextNode()) {
                    const el = walker.currentNode;
                    const f = getComputedStyle(el).fontFamily;
                    if (f) f.split(',').forEach(x => {
                        const t = x.replace(/['"]/g, '').trim();
                        if (t && t !== 'serif' && t !== 'sans-serif' && t !== 'monospace') allFonts.add(t);
                    });
                }
                return {
                    bodyFont: bodyStyle.fontFamily,
                    h1Font: h1Style ? h1Style.fontFamily : null,
                    h2Font: h2Style ? h2Style.fontFamily : null,
                    h3Font: h3Style ? h3Style.fontFamily : null,
                    detectedFonts: Array.from(allFonts),
                };
            }""")

            color_palette = await self.extract_color_palette(page)
        except Exception as exc:
            logger.error("Playwright extraction failed | url=%s | error=%s", url, exc)
            return None
        finally:
            try:
                await context.close()
            except Exception:
                pass

        if not html:
            logger.warning("No HTML captured | url=%s", url)
            return None

        soup = BeautifulSoup(html, "html.parser")

        raw_size_kb = round(len(html.encode("utf-8")) / 1024, 2)

        logo_info = await self.extract_logo_info(page, html, url)
        typography_info = await self.extract_typography(page, html)

        brand = self._extract_brand_identity(soup, computed, color_palette, logo_info, typography_info)
        brand.design_language = self.classify_design_language(brand, html)
        brand.brand_personality = self.estimate_brand_personality(brand, html)
        brand.consistency_report = await self.analyze_visual_consistency(page, brand)
        brand.component_styles = await self.extract_component_styles(page, html)
        navigation_info = await self.extract_navigation(page, html)
        hero_info = await self.extract_hero_section(page, html)

        hero_selector = None
        try:
            hero_selector = await page.evaluate("""() => {
                const el = document.querySelector('[class*="hero"], [id*="hero"]');
                if (!el) {
                    const fallback = document.querySelector('section');
                    if (fallback) return 'section';
                    return null;
                }
                if (el.id) return '#' + CSS.escape(el.id);
                const cls = Array.from(el.classList).find(c => c.toLowerCase().includes('hero'));
                if (cls) return '[class*="' + CSS.escape(cls) + '"]';
                return el.tagName.toLowerCase();
            }""")
        except Exception:
            pass

        sections = self.extract_sections(html, hero_selector)
        ctas = self.extract_ctas(html, sections, hero_info)
        footer_nav_items = navigation_info.footer_nav_items if navigation_info else []
        footer_info = await self.extract_footer(page, html, footer_nav_items)
        service_items, product_items = await self.extract_services_and_products(page, html, url)
        testimonials = await self.extract_testimonials(page, html, url)
        team_members = await self.extract_team_members(page, html)
        company_info = self.extract_company_info(html)
        trust_signal_list = self.extract_trust_signals(html)

        profile = WebsiteProfile(
            business=self._extract_business_info(soup, url),
            brand=brand,
            seo=self._extract_seo(soup, url),
            colors=color_palette,
            typography=self._extract_typography(computed),
            navigation=self._extract_navigation(soup, url),
            navigation_info=navigation_info,
            hero=self._extract_hero(soup),
            hero_info=hero_info,
            website_layout=WebsiteLayout(sections=sections, ctas=ctas, footer_info=footer_info),
            services=service_items or self._extract_services(soup),
            products=product_items,
            contact=self._extract_contact(soup),
            images=self._extract_images(soup, url),
            testimonials=testimonials,
            faqs=await self.extract_faqs(page, html),
            team=team_members or self._extract_team(soup),
            company=company_info,
            trust_signals=trust_signal_list,
            blog_links=self._extract_blog_links(soup),
            social_links=self._extract_social_links(soup, url),
            call_to_actions=self._extract_cta_buttons(soup, url),
            statistics=self._extract_statistics(soup),
            website_summary=self._build_website_summary(soup),
            raw_html_size_kb=raw_size_kb,
            extraction_timestamp=datetime.utcnow(),
        )

        profile.quality_metrics = self.calculate_quality_metrics(profile)
        profile.blueprint = self.generate_website_blueprint(profile)

        await website_intelligence_repository.create(db, lead_id=lead.id, profile=profile)
        logger.info("Website intelligence extracted and saved | lead_id=%s", lead.id)
        return profile

    async def validate_profile(
        self,
        profile: WebsiteProfile,
    ) -> bool:
        raise NotImplementedError("validate_profile will be implemented in a future sprint.")

    # ------------------------------------------------------------------
    # Phase 2.3d — Design Language & Brand Personality (rule-based)
    # ------------------------------------------------------------------

    def classify_design_language(
        self,
        brand: BrandIdentity,
        html: str,
    ) -> DesignLanguageResult:
        pp = _analyze_palette(brand.brand_colors)
        tp = _analyze_typography(brand.typography_info)

        soup = BeautifulSoup(html, "html.parser")
        visible_text = soup.get_text(separator=" ", strip=True)

        all_scores: Dict[str, float] = {}
        for cat_name, rules in CATEGORY_RULES.items():
            color_score = _score_color_rules(pp, rules["color_rules"])
            typo_score = _score_typo_rules(tp, rules["typo_rules"])
            kw_score = _keyword_score(rules["keywords"], visible_text)
            total = min(color_score + typo_score + kw_score, 100.0)
            all_scores[cat_name] = round(total, 1)

        best_cat = max(all_scores, key=all_scores.get)
        best_score = all_scores[best_cat]

        if best_score < 30:
            return DesignLanguageResult(
                design_language="Unclassified",
                confidence_score=0.0,
                all_scores=all_scores,
            )

        return DesignLanguageResult(
            design_language=best_cat,
            confidence_score=best_score,
            all_scores=all_scores,
        )

    def estimate_brand_personality(
        self,
        brand: BrandIdentity,
        html: str,
    ) -> BrandPersonalityResult:
        pp = _analyze_palette(brand.brand_colors)
        tp = _analyze_typography(brand.typography_info)

        soup = BeautifulSoup(html, "html.parser")
        visible_text = soup.get_text(separator=" ", strip=True)

        scores: Dict[str, float] = {}
        for trait_name, rules in PERSONALITY_RULES.items():
            color_score = _score_color_rules(pp, rules["color_rules"])
            typo_score = _score_typo_rules(tp, rules["typo_rules"])
            kw_score = _keyword_score(rules["keywords"], visible_text)
            total = min(color_score + typo_score + kw_score, 100.0)
            scores[trait_name] = round(total, 1)

        threshold = 50
        qualifying = {t: s for t, s in scores.items() if s > threshold}
        sorted_traits = sorted(qualifying.items(), key=lambda x: x[1], reverse=True)
        top_traits = [t for t, s in sorted_traits[:5]]

        if not top_traits:
            return BrandPersonalityResult(
                personality_traits=[],
                confidence_percentages=scores,
            )

        return BrandPersonalityResult(
            personality_traits=top_traits,
            confidence_percentages=scores,
        )

    # ------------------------------------------------------------------
    # Phase 2.3e — Visual Consistency & Component Styling
    # ------------------------------------------------------------------

    async def analyze_visual_consistency(
        self,
        page,
        brand: BrandIdentity,
    ) -> ConsistencyReport:
        import math as _math

        component_counts: Dict[str, int] = {}
        skipped: List[str] = []

        # Collect all computed styles from repeated components in a single evaluate
        raw: Dict[str, Any] = {}
        try:
            raw = await page.evaluate("""() => {
                function getAll(el) { return Array.from(document.querySelectorAll(el)); }
                function getProps(el) {
                    const s = getComputedStyle(el);
                    return {
                        bg: s.backgroundColor,
                        color: s.color,
                        paddingTop: s.paddingTop,
                        paddingRight: s.paddingRight,
                        paddingBottom: s.paddingBottom,
                        paddingLeft: s.paddingLeft,
                        marginTop: s.marginTop,
                        marginRight: s.marginRight,
                        marginBottom: s.marginBottom,
                        marginLeft: s.marginLeft,
                        borderRadius: s.borderRadius,
                        boxShadow: s.boxShadow,
                        fontSize: s.fontSize,
                        fontWeight: s.fontWeight,
                        borderWidth: s.borderTopWidth,
                    };
                }
                const buttons = getAll('button, [class*="btn"], [class*="cta"]');
                const cards = getAll('[class*="card"], [class*="Card"]');
                const h2s = getAll('h2');
                const h3s = getAll('h3');
                const allElements = getAll('button, [class*="btn"], [class*="cta"], [class*="card"], [class*="Card"], h2, h3');
                return {
                    buttons: buttons.slice(0, 20).map(getProps),
                    cards: cards.slice(0, 20).map(getProps),
                    h2s: h2s.slice(0, 20).map(getProps),
                    h3s: h3s.slice(0, 20).map(getProps),
                    count: {
                        buttons: buttons.length,
                        cards: cards.length,
                        h2s: h2s.length,
                        h3s: h3s.length,
                    },
                };
            }""")
        except Exception:
            raw = {}

        counts = raw.get("count", {})
        component_counts["buttons"] = counts.get("buttons", 0)
        component_counts["cards"] = counts.get("cards", 0)
        component_counts["h2"] = counts.get("h2s", 0)
        component_counts["h3"] = counts.get("h3s", 0)

        def _parse_px(val: str) -> Optional[float]:
            if not val:
                return None
            m = re.match(r"([+-]?[\d.]+)px", val)
            return float(m.group(1)) if m else None

        def _coeff_variation(values: List[float]) -> float:
            if len(values) < 2:
                return 1.0
            mean = sum(values) / len(values)
            if mean == 0:
                return 1.0
            variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
            std = _math.sqrt(variance)
            return std / mean

        def _cv_to_score(cv: float) -> float:
            score = max(0.0, 100.0 - (cv * 200.0))
            return round(min(score, 100.0), 1)

        # --- color_consistency ---
        btn_bgs: List[str] = []
        for btn in raw.get("buttons", []):
            bg = btn.get("bg", "")
            if bg and bg != "rgba(0, 0, 0, 0)" and bg != "transparent":
                btn_bgs.append(bg)
        distinct = len(set(btn_bgs)) if btn_bgs else 0
        if distinct <= 1:
            color_cs = 100.0
        else:
            color_cs = max(0.0, 100.0 - (distinct - 1) * 15.0)
        color_cs = round(color_cs, 1)

        # --- spacing_consistency ---
        spacing_vals: List[float] = []
        for grp in ["buttons", "cards"]:
            for item in raw.get(grp, []):
                for side in ["paddingTop", "paddingLeft", "marginTop", "marginBottom"]:
                    v = _parse_px(item.get(side, ""))
                    if v is not None:
                        spacing_vals.append(v)
        if len(spacing_vals) >= 2:
            spacing_cs = _cv_to_score(_coeff_variation(spacing_vals))
        else:
            spacing_cs = None
        spacing_cs = round(spacing_cs, 1) if spacing_cs is not None else None

        # --- typography_consistency ---
        h2_sizes: List[float] = []
        h3_sizes: List[float] = []
        for h2 in raw.get("h2s", []):
            v = _parse_px(h2.get("fontSize", ""))
            if v is not None:
                h2_sizes.append(v)
        for h3 in raw.get("h3s", []):
            v = _parse_px(h3.get("fontSize", ""))
            if v is not None:
                h3_sizes.append(v)
        typo_cvs: List[float] = []
        if len(h2_sizes) >= 2:
            typo_cvs.append(_coeff_variation(h2_sizes))
        if len(h3_sizes) >= 2:
            typo_cvs.append(_coeff_variation(h3_sizes))
        if typo_cvs:
            typo_cs = _cv_to_score(sum(typo_cvs) / len(typo_cvs))
        else:
            typo_cs = None
        typo_cs = round(typo_cs, 1) if typo_cs is not None else None

        # --- button_consistency ---
        btn_radii: List[float] = []
        btn_shadows: List[float] = []
        for btn in raw.get("buttons", []):
            r = _parse_px(btn.get("borderRadius", ""))
            if r is not None:
                btn_radii.append(r)
            sh = 1 if btn.get("boxShadow", "none") != "none" else 0
            btn_shadows.append(sh)
        if len(btn_radii) >= 2:
            btn_cs = _cv_to_score(_coeff_variation(btn_radii))
        else:
            btn_cs = None
        if len(btn_shadows) >= 2:
            shadow_cs = _cv_to_score(_coeff_variation(btn_shadows))
        else:
            shadow_cs = None

        # --- card_consistency ---
        card_radii: List[float] = []
        card_padding: List[float] = []
        for card in raw.get("cards", []):
            r = _parse_px(card.get("borderRadius", ""))
            if r is not None:
                card_radii.append(r)
            pt = _parse_px(card.get("paddingTop", ""))
            pb = _parse_px(card.get("paddingBottom", ""))
            pl = _parse_px(card.get("paddingLeft", ""))
            pr = _parse_px(card.get("paddingRight", ""))
            for p in [pt, pb, pl, pr]:
                if p is not None:
                    card_padding.append(p)
        if len(card_radii) >= 2:
            card_cs = _cv_to_score(_coeff_variation(card_radii))
        else:
            card_cs = None

        # --- border_radius_consistency ---
        all_radii = btn_radii + card_radii
        if len(all_radii) >= 2:
            br_cs = _cv_to_score(_coeff_variation(all_radii))
        else:
            br_cs = None

        # Track skipped components
        if component_counts.get("buttons", 0) < 2:
            skipped.append("buttons")
            btn_cs = None
        if component_counts.get("cards", 0) < 2:
            skipped.append("cards")
            card_cs = None
        if component_counts.get("h2", 0) < 2:
            skipped.append("h2")
        if component_counts.get("h3", 0) < 2:
            skipped.append("h3")

        # --- overall_consistency_score (weighted average) ---
        weights: List[Tuple[Optional[float], float]] = [
            (color_cs, 0.25),
            (spacing_cs, 0.15),
            (typo_cs, 0.15),
            (btn_cs, 0.10),
            (card_cs, 0.10),
            (br_cs or shadow_cs, 0.15),  # border + shadow combined slot
            (shadow_cs, 0.10),
        ]
        numerator = 0.0
        total_weight = 0.0
        for score_val, weight in weights:
            if score_val is not None:
                numerator += score_val * weight
                total_weight += weight
        overall = round(numerator / total_weight, 1) if total_weight > 0 else None

        # Merge border and shadow into dedicated scores
        if shadow_cs is None and component_counts.get("buttons", 0) < 2:
            skipped.append("shadow_consistency")
        _br_cs = round(br_cs, 1) if br_cs is not None else None
        _shadow_cs = round(shadow_cs, 1) if shadow_cs is not None else None

        return ConsistencyReport(
            color_consistency=color_cs,
            spacing_consistency=spacing_cs,
            typography_consistency=typo_cs,
            button_consistency=btn_cs,
            card_consistency=card_cs,
            border_radius_consistency=_br_cs,
            shadow_consistency=_shadow_cs,
            overall_consistency_score=overall,
            component_counts=component_counts,
            skipped_components=skipped,
        )

    async def extract_component_styles(
        self,
        page,
        html: str,
    ) -> ComponentStyles:
        component_types = {
            "button": 'button, [class*="btn"], [class*="cta"], [type="submit"], [type="button"]',
            "card": '[class*="card"], [class*="Card"]',
            "input": 'input:not([type="hidden"]), textarea, select',
            "badge": '[class*="badge"], [class*="Badge"], [class*="tag"], [class*="Tag"]',
            "table": "table",
            "navbar": "nav, [role='navigation'], header",
            "footer": "footer",
            "hero": '[class*="hero"], [class*="Hero"]',
            "section": "section",
            "icon": '[class*="icon"], [class*="Icon"], i, [class*="fa-"], svg:not(:has(svg))',
        }

        component_styles: Dict[str, Dict[str, str]] = {}

        for comp_type, selector in component_types.items():
            try:
                styles = await page.evaluate(f"""() => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return null;
                    const s = getComputedStyle(el);
                    return {{
                        padding: s.padding,
                        margin: s.margin,
                        borderRadius: s.borderRadius,
                        boxShadow: s.boxShadow,
                        backgroundColor: s.backgroundColor,
                        border: s.border,
                        fontSize: s.fontSize,
                        fontFamily: s.fontFamily,
                        fontWeight: s.fontWeight,
                        color: s.color,
                        textAlign: s.textAlign,
                        display: s.display,
                    }};
                }}""")
                if styles and any(v for v in styles.values()):
                    component_styles[comp_type] = styles
            except Exception:
                pass

        if not component_styles:
            component_styles = {}

        return ComponentStyles(component_styles=component_styles)

    async def extract_navigation(
        self,
        page,
        html: str,
    ) -> NavigationInfo:
        import httpx

        soup = BeautifulSoup(html, "html.parser")
        all_navs = soup.find_all("nav")
        role_navs = soup.select('[role="navigation"]')
        combined = all_navs + role_navs

        if not combined:
            return NavigationInfo(primary_nav_items=[], secondary_nav_items=[], footer_nav_items=[], navigation_depth=0, is_sticky=False)

        def _nav_classify(nav_tag) -> str:
            parent_names = [p.name for p in nav_tag.parents]
            if "footer" in parent_names:
                return "footer"
            if "header" in parent_names:
                return "primary"
            return "primary"

        def _extract_items(nav_tag, base_url: str, max_depth: int = 1) -> List[Dict[str, Any]]:
            items: List[Dict[str, Any]] = []
            order = 0
            for li in nav_tag.find_all("li", recursive=True):
                a = li.find("a", href=True)
                if not a:
                    continue
                label = a.get_text(strip=True)
                if not label or len(label) > 120:
                    continue
                href = a["href"]
                if href.startswith("#") or href.startswith("javascript:"):
                    continue
                full_url = urljoin(base_url, str(href)) if not str(href).startswith(("http://", "https://")) else str(href)
                order += 1

                has_dropdown = False
                is_mega = False
                dropdown_items: List[Dict[str, Any]] = []

                nested_ul = li.find("ul")
                if nested_ul and max_depth > 0:
                    has_dropdown = True
                    mega_container = nested_ul.find_parent(["div", "li"])
                    if mega_container:
                        mega_cls = " ".join(mega_container.get("class", []))
                        if "mega" in mega_cls.lower():
                            is_mega = True
                        ul_siblings = nested_ul.find_parent("li").find_all("ul", recursive=False) if nested_ul.find_parent("li") else []
                        if len(ul_siblings) > 1:
                            is_mega = True
                    dropdown_items = _extract_items(nested_ul, base_url, max_depth - 1)

                items.append({
                    "label": label[:100],
                    "url": full_url,
                    "order": order,
                    "has_dropdown": has_dropdown,
                    "is_mega_menu": is_mega,
                    "dropdown_items": dropdown_items,
                })
            return items

        classified = {"primary": None, "secondary": [], "footer": []}
        for nav in combined:
            cat = _nav_classify(nav)
            if cat == "primary" and classified["primary"] is None:
                classified["primary"] = nav
            elif cat == "footer":
                classified["footer"].append(nav)
            else:
                classified["secondary"].append(nav)

        primary_nav = classified["primary"]
        primary_items = _extract_items(primary_nav, url) if primary_nav else []

        secondary_items = []
        for nav in classified["secondary"][:3]:
            secondary_items.extend(_extract_items(nav, url))

        footer_items = []
        if classified["footer"]:
            for nav in classified["footer"][:2]:
                footer_items.extend(_extract_items(nav, url))
        else:
            footer_tag = soup.find("footer")
            if footer_tag:
                for a in footer_tag.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("#") or href.startswith("javascript:"):
                        continue
                    label = a.get_text(strip=True)
                    if label:
                        footer_items.append({
                            "label": label[:100],
                            "url": urljoin(url, str(href)) if not str(href).startswith(("http://", "https://")) else str(href),
                            "order": len(footer_items) + 1,
                            "has_dropdown": False,
                            "is_mega_menu": False,
                            "dropdown_items": [],
                        })
                    if len(footer_items) >= 30:
                        break

        def _calc_depth(items_list: List[Dict[str, Any]], current: int = 1) -> int:
            max_d = current
            for item in items_list:
                if item["dropdown_items"]:
                    d = _calc_depth(item["dropdown_items"], current + 1)
                    max_d = max(max_d, d)
            return max_d

        nav_depth = _calc_depth(primary_items) if primary_items else 0

        is_sticky = False
        if primary_nav:
            try:
                sticky_result = await page.evaluate("""() => {
                    const nav = document.querySelector('nav');
                    if (!nav) return false;
                    const s = getComputedStyle(nav);
                    return s.position === 'sticky' || s.position === 'fixed';
                }""")
                is_sticky = bool(sticky_result)
            except Exception:
                pass

        return NavigationInfo(
            primary_nav_items=primary_items,
            secondary_nav_items=secondary_items,
            footer_nav_items=footer_items,
            navigation_depth=nav_depth,
            is_sticky=is_sticky,
        )

    async def extract_hero_section(self, page, html: str) -> HeroInfo:
        result = None
        try:
            result = await page.evaluate("""() => {
                const vpH = window.innerHeight;

                let hero = document.querySelector('[class*="hero"], [id*="hero"]');
                if (hero) {
                    const r = hero.getBoundingClientRect();
                    if (r.top >= vpH || r.top < -100) hero = null;
                }

                let isFallback = false;
                if (!hero) {
                    hero = document.querySelector('section');
                    if (hero) {
                        const r = hero.getBoundingClientRect();
                        if (r.top < vpH && r.top >= -100) isFallback = true;
                        else hero = null;
                    }
                }

                if (!hero) return null;

                const heroRect = hero.getBoundingClientRect();

                const h1 = hero.querySelector('h1');
                const h2 = hero.querySelector('h2');
                const title = h1
                    ? h1.textContent.trim()
                    : (h2 ? h2.textContent.trim() : null);

                let subtitle = null;
                const subEl = hero.querySelector('[class*="subtitle"], [class*="sub-heading"]');
                if (subEl) subtitle = subEl.textContent.trim();
                if (!subtitle) {
                    const h2El = h1 ? hero.querySelector('h2') : null;
                    const h3El = hero.querySelector('h3');
                    if (h2El) subtitle = h2El.textContent.trim();
                    else if (h3El) subtitle = h3El.textContent.trim();
                }

                const p = hero.querySelector('p');
                const description = p ? p.textContent.trim() : null;

                const ctaNodes = hero.querySelectorAll(
                    'a[class*="btn"], a[class*="cta"], button[class*="btn"], button[class*="cta"]'
                );
                const primaryCta = ctaNodes.length > 0 ? {
                    text: ctaNodes[0].textContent.trim(),
                    url: ctaNodes[0].href || '',
                } : null;
                const secondaryCta = ctaNodes.length > 1 ? {
                    text: ctaNodes[1].textContent.trim(),
                    url: ctaNodes[1].href || '',
                } : null;

                const img = hero.querySelector('img');
                const heroImage = img ? img.src : null;

                const bgStyle = getComputedStyle(hero);
                let bgImageUrl = null;
                let bgColor = null;
                const bgImage = bgStyle.backgroundImage;
                if (bgImage && bgImage !== 'none') {
                    const m = bgImage.match(/url\\(["']?([^"')]+)["']?\\)/);
                    if (m) bgImageUrl = new URL(m[1], document.baseURI).href;
                }
                const rawBgColor = bgStyle.backgroundColor;
                if (rawBgColor && rawBgColor !== 'rgba(0, 0, 0, 0)' && rawBgColor !== 'transparent') {
                    bgColor = rawBgColor;
                }

                const textBlock = hero.querySelector('h1, h2, h3, p, [class*="text"], [class*="content"]');
                const imageBlock = hero.querySelector('img, [class*="image"], [class*="media"], [class*="graphic"]');
                let layout = 'text-only';
                if (imageBlock) {
                    if (bgImageUrl) {
                        layout = 'background-image';
                    } else {
                        const tr = textBlock ? textBlock.getBoundingClientRect() : null;
                        const ir = imageBlock.getBoundingClientRect();
                        if (tr) {
                            if (ir.right <= tr.left + 20) layout = 'image-left';
                            else if (tr.right <= ir.left + 20) layout = 'image-right';
                            else layout = 'centered';
                        }
                    }
                }

                const titleEl = h1 || h2;
                let alignment = 'left';
                if (titleEl) {
                    const ta = getComputedStyle(titleEl).textAlign;
                    if (ta === 'center') alignment = 'center';
                    else if (ta === 'right') alignment = 'right';
                }

                return {
                    hero_title: title ? title.substring(0, 500) : null,
                    hero_subtitle: subtitle ? subtitle.substring(0, 500) : null,
                    hero_description: description ? description.substring(0, 1000) : null,
                    primary_cta: primaryCta,
                    secondary_cta: secondaryCta,
                    hero_image: heroImage,
                    background_image_url: bgImageUrl,
                    background_color: bgColor,
                    hero_layout: layout,
                    hero_alignment: alignment,
                    hero_height: Math.round(heroRect.height),
                    is_fallback_detection: isFallback,
                };
            }""")
        except Exception:
            return HeroInfo()

        if result is None:
            return HeroInfo()

        return HeroInfo(
            hero_title=result.get("hero_title"),
            hero_subtitle=result.get("hero_subtitle"),
            hero_description=result.get("hero_description"),
            primary_cta=CtaButton(**result["primary_cta"]) if result.get("primary_cta") else None,
            secondary_cta=CtaButton(**result["secondary_cta"]) if result.get("secondary_cta") else None,
            hero_image=result.get("hero_image"),
            background_image_url=result.get("background_image_url"),
            background_color=result.get("background_color"),
            hero_layout=result.get("hero_layout"),
            hero_alignment=result.get("hero_alignment"),
            hero_height=result.get("hero_height"),
            is_fallback_detection=result.get("is_fallback_detection", False),
        )

    SECTION_CATEGORIES: Dict[str, Dict[str, Any]] = {
        "About": {
            "keywords": ["about", "about us", "who we are", "our story", "our mission", "our vision", "company", "our company"],
            "structural_weight": 20,
            "keyword_weight": 80,
        },
        "Services": {
            "keywords": ["service", "what we do", "solutions", "offerings", "capabilities", "our services"],
            "structural_weight": 40,
            "keyword_weight": 60,
        },
        "Features": {
            "keywords": ["feature", "why choose", "key features", "benefits", "what makes us", "why us"],
            "structural_weight": 40,
            "keyword_weight": 60,
        },
        "Pricing": {
            "keywords": ["pricing", "plan", "price", "package", "subscription", "monthly", "annual"],
            "structural_weight": 30,
            "keyword_weight": 70,
        },
        "Portfolio": {
            "keywords": ["portfolio", "our work", "case study", "projects", "our projects"],
            "structural_weight": 30,
            "keyword_weight": 70,
        },
        "Gallery": {
            "keywords": ["gallery", "photos", "images", "our gallery", "photography"],
            "structural_weight": 20,
            "keyword_weight": 80,
        },
        "FAQ": {
            "keywords": ["faq", "frequently asked", "questions", "common questions", "q&a", "asked questions"],
            "structural_weight": 30,
            "keyword_weight": 70,
        },
        "Testimonials": {
            "keywords": ["testimonial", "review", "what clients say", "success stories", "client said", "customer says", "trusted by"],
            "structural_weight": 30,
            "keyword_weight": 70,
        },
        "Team": {
            "keywords": ["team", "our people", "meet the team", "leadership", "our team", "our leadership"],
            "structural_weight": 30,
            "keyword_weight": 70,
        },
        "Partners": {
            "keywords": ["partner", "our partners", "sponsor", "trusted by", "clients", "they trust", "our clients"],
            "structural_weight": 30,
            "keyword_weight": 70,
        },
        "Statistics": {
            "keywords": ["statistic", "numbers", "counter", "achievement", "milestone", "by the numbers"],
            "structural_weight": 20,
            "keyword_weight": 80,
        },
        "Blog": {
            "keywords": ["blog", "articles", "news", "insights", "resources", "latest posts"],
            "structural_weight": 30,
            "keyword_weight": 70,
        },
        "Contact": {
            "keywords": ["contact", "get in touch", "reach us", "contact us", "message us"],
            "structural_weight": 30,
            "keyword_weight": 70,
        },
        "Newsletter": {
            "keywords": ["newsletter", "subscribe", "sign up", "stay updated", "get updates", "email address"],
            "structural_weight": 30,
            "keyword_weight": 70,
        },
    }

    def extract_sections(self, html: str, hero_container_selector: Optional[str] = None) -> List[SectionInfo]:
        soup = BeautifulSoup(html, "html.parser")
        candidates: List[Any] = []
        seen_selectors: set = set()

        for section in soup.find_all("section"):
            candidates.append(section)

        for div in soup.find_all("div"):
            parent = div.parent
            if parent and parent.name in ("body", "main"):
                heading = div.find(["h1", "h2", "h3"])
                if heading:
                    candidates.append(div)

        if hero_container_selector:
            hero_elem = soup.select_one(hero_container_selector)
            if hero_elem:
                candidates = [c for c in candidates if c is not hero_elem]

        candidates = [c for c in candidates if c.name not in ("nav", "footer", "header")]

        seen_sigs: set = set()
        unique_candidates: List[Any] = []
        for c in candidates:
            sig = id(c)
            if sig not in seen_sigs:
                seen_sigs.add(sig)
                unique_candidates.append(c)

        results: List[SectionInfo] = []
        dropped_no_heading = 0

        for idx, candidate in enumerate(unique_candidates):
            text_content = candidate.get_text(strip=True)
            if not text_content or len(text_content) < 30:
                dropped_no_heading += 1
                continue

            h1 = candidate.find("h1")
            h2 = candidate.find("h2")
            h3 = candidate.find("h3")
            heading_el = h1 or h2 or h3
            heading = heading_el.get_text(strip=True)[:500] if heading_el else None

            subheading = None
            sub_el = candidate.find(["h2", "h3", "h4"], class_=lambda c: c and "subtitle" in " ".join(c).lower()) if heading_el else None
            if not sub_el:
                if h1:
                    h2_el = candidate.find("h2")
                    if h2_el:
                        sub_el = h2_el
                elif h2:
                    h3_el = candidate.find("h3")
                    if h3_el:
                        sub_el = h3_el
            if sub_el:
                st = sub_el.get_text(strip=True)
                if st and st != (heading or ""):
                    subheading = st[:500]

            desc_el = candidate.find("p")
            description = desc_el.get_text(strip=True)[:1000] if desc_el and desc_el.get_text(strip=True) else None

            img_tags = candidate.find_all("img")
            images: List[str] = []
            for img in img_tags:
                src = img.get("src")
                if src and not src.startswith("data:"):
                    images.append(src)
                if len(images) >= 10:
                    break

            btn_tags = candidate.find_all(["a", "button"], class_=lambda c: c and any(k in (" ".join(c).lower()) for k in ("btn", "cta")))
            buttons: List[Dict[str, str]] = []
            for btn in btn_tags:
                bt = btn.get_text(strip=True)
                bu = btn.get("href") or ""
                if bt:
                    buttons.append({"text": bt[:100], "url": bu})
                if len(buttons) >= 5:
                    break

            scores = self._classify_section(candidate, heading)
            best_cat = max(scores, key=lambda k: scores[k])
            confidence = scores[best_cat]

            if confidence < 30:
                section_type = "Other"
                confidence = 0.0

            direct_children = list(candidate.children)
            similar = [ch for ch in direct_children if ch.name in ("div", "article", "li", "section")]
            cls_names = (" ".join(candidate.get("class", []))).lower()
            has_grid_class = "grid" in cls_names

            if has_grid_class and len(similar) >= 3:
                layout_type = "grid"
            elif len(similar) >= 3:
                card_like = 0
                for ch in similar:
                    ch_cls = " ".join(ch.get("class", [])).lower()
                    if any(k in ch_cls for k in ("card", "col", "item", "grid")):
                        card_like += 1
                if card_like >= 3:
                    layout_type = "grid"
                else:
                    layout_type = "list"
            else:
                layout_type = "single-column"

            results.append(SectionInfo(
                section_type=section_type,
                order=idx,
                heading=heading,
                subheading=subheading,
                description=description,
                layout_type=layout_type,
                images=images,
                buttons=[CtaLink(**b) for b in buttons],
                confidence_score=confidence,
            ))

        if dropped_no_heading > 0:
            logger.debug("extract_sections: dropped %d candidates (no heading, <30 chars)", dropped_no_heading)

        return results

    def extract_ctas(self, html: str, sections: List[SectionInfo], hero: HeroInfo) -> List["CTAInfo"]:
        try:
            from urllib.parse import urljoin

            soup = BeautifulSoup(html, "html.parser")

            cta_elements: List[Any] = []
            seen: set = set()

            for el in soup.find_all(["a", "button"]):
                if el.name in ("nav", "footer") or el.find_parent(["nav", "footer"]):
                    continue
                cls_str = " ".join(el.get("class", []))
                if not any(k in cls_str for k in ("btn", "cta", "button")):
                    continue
                text = el.get_text(strip=True)
                if not text or len(text) > 120:
                    continue
                key = (text.lower(), el.get("href", ""))
                if key in seen:
                    continue
                seen.add(key)
                cta_elements.append(el)

            hero_container = (
                soup.select_one('[class*="hero"], [id*="hero"]')
                or soup.select_one("section")
            )
            if hero_container:
                hero_rect = (id(hero_container),)
            else:
                hero_container = None

            section_containers: List[Any] = []
            for s in soup.find_all(["section", "div"]):
                parent = s.parent
                if parent and parent.name in ("body", "main") and s.find(["h1", "h2", "h3"]):
                    section_containers.append(s)
                elif s.name == "section":
                    section_containers.append(s)

            section_containers = [c for c in section_containers if c.name not in ("nav", "footer", "header")]

            seen_sec_ids: set = set()
            unique_secs: List[Any] = []
            for c in section_containers:
                cid = id(c)
                if cid not in seen_sec_ids:
                    seen_sec_ids.add(cid)
                    unique_secs.append(c)
            section_containers = unique_secs

            if hero_container and hero_container in section_containers:
                section_containers.remove(hero_container)

            results: List["CTAInfo"] = []
            for pos, el in enumerate(cta_elements):
                href = el.get("href") or ""
                full_url: Optional[str] = None
                is_placeholder = False
                if href:
                    if href.startswith(("http://", "https://")):
                        full_url = href
                    elif href.startswith("#") or href.startswith("javascript:"):
                        is_placeholder = True
                    elif href.startswith("/"):
                        full_url = urljoin("https://example.com", href)
                    else:
                        full_url = urljoin("https://example.com", href)

                button_type = "button" if el.name == "button" else "link"

                cls_lower = " ".join(el.get("class", [])).lower()
                is_primary = "primary" in cls_lower or "cta-primary" in cls_lower

                section_name: Optional[str] = None

                if hero_container and (el is hero_container or hero_container in el.parents or el in hero_container.descendants):
                    section_name = "hero"

                for sec_idx, sec_el in enumerate(section_containers):
                    if sec_idx >= len(sections):
                        break
                    if el is sec_el or el in sec_el.descendants:
                        section_name = sections[sec_idx].section_type if sec_idx < len(sections) else "Other"
                        break

                if not is_primary and section_name == "hero":
                    pass

                results.append(CTAInfo(
                    text=text[:200],
                    url=full_url,
                    button_type=button_type,
                    is_primary=is_primary or (pos == 0 and section_name == "hero"),
                    is_placeholder_link=is_placeholder,
                    position=pos,
                    section=section_name,
                ))

            return results

        except Exception:
            logger.exception("extract_ctas failed")
            return []

    async def extract_footer(
        self,
        page,
        html: str,
        footer_nav: List["NavItem"],
    ) -> "FooterInfo":
        try:
            from urllib.parse import urlparse

            soup = BeautifulSoup(html, "html.parser")

            footer_tag = soup.find("footer")
            is_fallback = False

            if not footer_tag:
                is_fallback = True
                all_sections = soup.find_all(["section", "div"])
                for s in reversed(all_sections):
                    rect = s.get("style") or ""
                    if s.find(["h1", "h2", "h3", "p"]):
                        footer_tag = s
                        break
                if not footer_tag:
                    footer_tag = list(soup.find_all(["section", "div"]))[-1] if soup.find_all(["section", "div"]) else None

            if not footer_tag:
                return FooterInfo()

            footer_logo: Optional[str] = None
            for img in footer_tag.find_all("img"):
                cls_str = " ".join(img.get("class", [])).lower()
                src = img.get("src") or ""
                if "logo" in cls_str or "logo" in img.get("alt", "").lower() or "logo" in src.lower():
                    footer_logo = src
                    break
            if not footer_logo:
                first_img = footer_tag.find("img")
                if first_img:
                    footer_logo = first_img.get("src")

            footer_description: Optional[str] = None
            for p in footer_tag.find_all("p"):
                if not p.find_parent(["ul", "ol", "nav"]):
                    text = p.get_text(strip=True)
                    if text and len(text) > 10:
                        footer_description = text[:500]
                        break

            contact_emails: set = set()
            contact_phones: set = set()
            contact_address: Optional[str] = None

            for a in footer_tag.find_all("a", href=True):
                href = str(a["href"])
                if href.startswith("mailto:"):
                    e = href.replace("mailto:", "").split("?")[0].strip().lower()
                    if e and not e.endswith((".png", ".jpg", ".gif", ".svg")):
                        contact_emails.add(e)
                elif href.startswith("tel:"):
                    p = href.replace("tel:", "").strip().split("?")[0]
                    if p:
                        contact_phones.add(p)

            text = footer_tag.get_text(separator=" ", strip=True)
            for match in re.finditer(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text):
                e = match.group(0).lower()
                if not e.endswith((".png", ".jpg", ".gif", ".svg", ".css")):
                    contact_emails.add(e)
            for match in re.finditer(r"(?:\+?\d{1,4}[\s\-.]?)?\(?\d{1,5}\)?[\s\-.]?\d{1,5}[\s\-.]?\d{1,9}", text):
                cleaned = match.group(0).strip()
                digits = re.sub(r"\D", "", cleaned)
                if 7 <= len(digits) <= 15:
                    contact_phones.add(cleaned)

            addr_tag = footer_tag.find("address")
            if addr_tag:
                contact_address = addr_tag.get_text(" ", strip=True)[:500] or None

            social_found: Dict[str, str] = {}
            for a in footer_tag.find_all("a", href=True):
                href = str(a["href"]).strip()
                if not href.startswith(("http://", "https://")):
                    continue
                try:
                    domain = urlparse(href).netloc.lower().lstrip("www.")
                except Exception:
                    continue
                for soc_domain, platform in SOCIAL_DOMAINS.items():
                    if soc_domain in domain and platform not in social_found:
                        social_found[platform] = href

            copyright_text: Optional[str] = None
            for el in footer_tag.find_all(string=True):
                txt = el.strip()
                if "©" in txt or "All rights reserved" in txt:
                    copyright_text = txt[:500]
                    break
            if not copyright_text:
                for el in footer_tag.find_all(["p", "span", "div"]):
                    txt = el.get_text(strip=True)
                    if "©" in txt or "all rights reserved" in txt.lower():
                        copyright_text = txt[:500]
                        break

            newsletter_signup = False
            newsletter_action_url: Optional[str] = None
            for form in footer_tag.find_all("form"):
                email_input = form.find("input", type="email") or form.find("input", {"name": re.compile(r"email", re.I)})
                if email_input:
                    newsletter_signup = True
                    action = form.get("action") or ""
                    if action and not action.startswith("#"):
                        newsletter_action_url = action
                    break

            return FooterInfo(
                footer_logo=footer_logo,
                footer_description=footer_description,
                footer_links=list(footer_nav),
                contact_info=ContactInfo(
                    emails=sorted(contact_emails)[:10],
                    phones=sorted(contact_phones)[:10],
                    address=contact_address,
                ),
                social_links=[SocialLink(platform=p, url=u) for p, u in social_found.items()][:20],
                copyright_text=copyright_text,
                newsletter_signup=newsletter_signup,
                newsletter_action_url=newsletter_action_url,
                is_fallback_detection=is_fallback,
            )

        except Exception:
            logger.exception("extract_footer failed")
            return FooterInfo()

    def _classify_section(self, candidate: Any, heading: Optional[str]) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        combined_text = " ".join([
            candidate.get("id") or "",
            " ".join(candidate.get("class", [])),
            heading or "",
        ]).lower()

        for cat, rules in self.SECTION_CATEGORIES.items():
            score = 0.0
            kw_matches = 0
            for kw in rules["keywords"]:
                if kw in combined_text:
                    kw_matches += 1
            kw_score = (kw_matches / len(rules["keywords"])) * rules["keyword_weight"]
            score += kw_score

            structural_score = 0.0
            if cat == "Contact" and candidate.find("form"):
                structural_score = rules["structural_weight"]
            elif cat == "Newsletter" and (candidate.find("form") or candidate.find("input", type="email")):
                structural_score = rules["structural_weight"]
            elif cat == "FAQ":
                qa_pairs = candidate.find_all(["dt", "dd"]) or (candidate.find_all("div", class_=lambda c: c and "question" in " ".join(c).lower()) if True else [])
                if len(qa_pairs) >= 2:
                    structural_score = rules["structural_weight"]
            elif cat in ("Services", "Features", "Portfolio", "Team"):
                similar = [ch for ch in candidate.children if ch.name in ("div", "article", "li")]
                card_like = 0
                for ch in similar:
                    ch_cls = " ".join(ch.get("class", [])).lower()
                    if any(k in ch_cls for k in ("card", "item", "col")):
                        card_like += 1
                if card_like >= 3:
                    structural_score = rules["structural_weight"]
            elif cat == "Pricing":
                has_price = bool(candidate.find(string=re.compile(r"[\$€£¥]")))
                has_table = bool(candidate.find("table"))
                if has_price or has_table:
                    structural_score = rules["structural_weight"]
            elif cat == "Gallery":
                imgs = candidate.find_all("img")
                if len(imgs) >= 4:
                    structural_score = rules["structural_weight"]
            elif cat == "Statistics":
                numbers = candidate.find_all(string=re.compile(r"\d+%|\d+k|\d+[.,]\d+"))
                if len(numbers) >= 3:
                    structural_score = rules["structural_weight"]
            elif cat == "Testimonials":
                blocks = candidate.find_all(["blockquote", "div"], class_=lambda c: c and any(k in " ".join(c).lower() for k in ("testimonial", "review", "quote")))
                if len(blocks) >= 2:
                    structural_score = rules["structural_weight"]

            score += structural_score
            scores[cat] = round(score, 1)

        scores["Other"] = 0.0
        return scores

    async def extract_color_palette(self, page) -> ColorPalette:
        computed_elements: Dict[str, Dict[str, str]] = {}

        try:
            computed_data = await page.evaluate("""() => {
                const selectors = ['body', 'header', 'nav', 'footer',
                    'button', '[class*="btn"]', '[class*="cta"]',
                    'a', 'h1', 'h2', 'h3',
                    '[class*="card"]', '[class*="hero"]'];
                const result = {};
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        const s = getComputedStyle(el);
                        result[sel] = {
                            bg: s.backgroundColor,
                            color: s.color,
                            border: s.borderColor || s.borderTopColor || '',
                        };
                    }
                }
                return result;
            }""")
            computed_elements = computed_data or {}
        except Exception:
            computed_elements = {}

        def _parse_rgb(raw: str) -> Optional[Tuple[int, int, int]]:
            m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', raw)
            if m:
                return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return None

        def _rgb_to_hex(r: int, g: int, b: int) -> str:
            return f"#{r:02x}{g:02x}{b:02x}"

        def _rel_luminance(r: int, g: int, b: int) -> float:
            def linearize(c: float) -> float:
                c = c / 255.0
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

        def _contrast_ratio(l1: float, l2: float) -> float:
            lighter = max(l1, l2)
            darker = min(l1, l2)
            return (lighter + 0.05) / (darker + 0.05)

        def _wcag_level(ratio: float, large_text: bool = False) -> str:
            if large_text:
                if ratio >= 4.5:
                    return "AAA"
                if ratio >= 3.0:
                    return "AA"
                return "FAIL"
            if ratio >= 7.0:
                return "AAA"
            if ratio >= 4.5:
                return "AA"
            return "FAIL"

        raw_colors: Dict[str, str] = {}
        raw_rgb: Dict[str, Tuple[int, int, int]] = {}

        for selector, styles in computed_elements.items():
            for key in ("bg", "color", "border"):
                val = styles.get(key, "")
                if val and val != "rgba(0, 0, 0, 0)" and val != "transparent":
                    parsed = _parse_rgb(val)
                    if parsed:
                        hex_val = _rgb_to_hex(*parsed)
                        label = f"{selector}_{key}"
                        raw_colors[label] = hex_val
                        raw_rgb[label] = parsed

        filtered = {}
        seen = set()
        for label, hex_val in raw_colors.items():
            if hex_val not in seen:
                seen.add(hex_val)
                filtered[label] = hex_val

        self_screenshot: Optional[bytes] = None
        if _PIL_AVAILABLE and _COLORTHIEF_AVAILABLE:
            try:
                self_screenshot = await page.screenshot(full_page=True, type="png")
            except Exception:
                pass

        dominant_colors: List[Tuple[int, int, int]] = []
        dominant_hex: List[str] = []
        if self_screenshot and _COLORTHIEF_AVAILABLE:
            try:
                img_buffer = io.BytesIO(self_screenshot)
                color_thief = ColorThief(img_buffer)
                palette = color_thief.get_palette(color_count=10, quality=1)
                dominant_colors = palette
                dominant_hex = [_rgb_to_hex(*c) for c in palette]
            except Exception:
                pass

        computed_colors: Dict[str, "ComputedColor"] = {}

        def _rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
            return colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)

        all_unique_rgbs = list(raw_rgb.values()) + dominant_colors
        seen_rgb = set()
        unique_rgbs: List[Tuple[int, int, int]] = []
        for rgb in all_unique_rgbs:
            if rgb not in seen_rgb:
                seen_rgb.add(rgb)
                unique_rgbs.append(rgb)

        for i, rgb in enumerate(unique_rgbs):
            r, g, b = rgb
            hex_val = _rgb_to_hex(r, g, b)
            h, l_s, s = _rgb_to_hsl(r, g, b)
            lum = _rel_luminance(r, g, b)
            brightness = round(lum, 4)

            usage_role: Optional[str] = None
            for label, hex_c in raw_colors.items():
                if hex_c == hex_val:
                    usage_role = label
                    break

            computed_colors[f"color_{i}"] = {
                "hex": hex_val,
                "rgb": {"r": r, "g": g, "b": b},
                "hsl": {"h": round(h, 2), "s": round(s, 2), "l": round(l_s, 2)},
                "relative_brightness": brightness,
                "frequency": None,
                "usage_role": usage_role,
            }

        contrast_pairs: List[Dict[str, Any]] = []
        all_hex = list(raw_colors.values()) + dominant_hex
        seen_pair = set()
        for i in range(len(all_hex)):
            for j in range(i + 1, len(all_hex)):
                hex_a = all_hex[i]
                hex_b = all_hex[j]
                pair_key = tuple(sorted([hex_a, hex_b]))
                if pair_key in seen_pair:
                    continue
                seen_pair.add(pair_key)
                rgb_a = _parse_rgb(f"rgb({int(hex_a[1:3], 16)}, {int(hex_a[3:5], 16)}, {int(hex_a[5:7], 16)})")
                rgb_b = _parse_rgb(f"rgb({int(hex_b[1:3], 16)}, {int(hex_b[3:5], 16)}, {int(hex_b[5:7], 16)})")
                if rgb_a and rgb_b:
                    l1 = _rel_luminance(*rgb_a)
                    l2 = _rel_luminance(*rgb_b)
                    ratio = _contrast_ratio(l1, l2)
                    contrast_pairs.append({
                        "color_a": hex_a,
                        "color_b": hex_b,
                        "ratio": round(ratio, 2),
                        "aa_normal": ratio >= 4.5,
                        "aa_large": ratio >= 3.0,
                        "aaa_normal": ratio >= 7.0,
                        "aaa_large": ratio >= 4.5,
                        "wcag_level_normal": _wcag_level(ratio, large_text=False),
                        "wcag_level_large": _wcag_level(ratio, large_text=True),
                    })

        passing = sum(1 for p in contrast_pairs if p["aa_normal"])
        total = len(contrast_pairs)
        accessibility_score = round((passing / total) * 100, 1) if total > 0 else None

        primary_hex = raw_colors.get("body_bg", "") or raw_colors.get("header_bg", "") or (dominant_hex[0] if dominant_hex else "")
        secondary_hex = raw_colors.get("nav_bg", "") or raw_colors.get("footer_bg", "") or (dominant_hex[1] if len(dominant_hex) > 1 else "")
        accent_hex = raw_colors.get("a_color", "") or raw_colors.get('button_bg', "") or raw_colors.get('[class*="btn"]_bg', "")
        bg_hex = raw_colors.get("body_bg", "")
        text_hex = raw_colors.get("body_color", "")

        return ColorPalette(
            primary=primary_hex or None,
            secondary=secondary_hex or None,
            accent=accent_hex or None,
            background=bg_hex or None,
            text=text_hex or None,
            surface=raw_colors.get('[class*="card"]_bg') or None,
            heading=raw_colors.get("h1_color") or raw_colors.get("h2_color") or None,
            border=raw_colors.get("body_border") or None,
            muted=raw_colors.get("footer_color") or None,
            dark=raw_colors.get("nav_bg") or raw_colors.get("footer_bg") or None,
            light=raw_colors.get('[class*="hero"]_bg') or None,
            success=None,
            warning=None,
            danger=raw_colors.get("a_color") if text_hex and raw_colors.get("a_color") else None,
            info=None,
            computed_colors={k: {
                "hex": v["hex"],
                "rgb": v["rgb"],
                "hsl": v["hsl"],
                "relative_brightness": v["relative_brightness"],
                "frequency": v["frequency"],
                "usage_role": v["usage_role"],
            } for k, v in computed_colors.items()} if computed_colors else None,
            contrast_pairs=contrast_pairs if contrast_pairs else None,
            accessibility_score=accessibility_score,
        )

    async def extract_logo_info(
        self,
        page,
        html: str,
        base_url: str,
    ) -> LogoInfo:
        import httpx

        soup = BeautifulSoup(html, "html.parser")
        logo_url: Optional[str] = None
        logo_img = None
        position: Optional[str] = None
        is_favicon_fallback = False
        image_format: Optional[str] = None
        has_transparency: Optional[bool] = None
        width: Optional[int] = None
        height: Optional[int] = None
        dominant_colors: List[str] = []
        is_retina = False

        # ---- Tier 1: <img> with logo in alt/class/id ----
        img_selectors = [
            'img[alt*="logo" i]',
            'img[class*="logo" i]',
            'img[id*="logo" i]',
            '[class*="logo" i] img',
            '[id*="logo" i] img',
        ]
        for sel in img_selectors:
            candidate = soup.select_one(sel)
            if candidate and candidate.get("src"):
                logo_img = candidate
                break

        # ---- Tier 2: first <img> inside header or nav ----
        if not logo_img:
            for container_sel in ["header", "nav"]:
                container = soup.select_one(container_sel)
                if container:
                    candidate = container.find("img", src=True)
                    if candidate:
                        logo_img = candidate
                        break

        # ---- Tier 3: favicon ----
        if not logo_img:
            favicon_link = soup.select_one(
                'link[rel="icon"], link[rel="shortcut icon"], link[rel="apple-touch-icon"]'
            )
            if favicon_link and favicon_link.get("href"):
                logo_url = urljoin(base_url, str(favicon_link["href"]))
                is_favicon_fallback = True
                image_format = _detect_format(logo_url)

        if logo_img:
            src = logo_img.get("src")
            if src:
                logo_url = urljoin(base_url, str(src))

            parent_tags = [t.name for t in logo_img.parents]
            if "header" in parent_tags or "nav" in parent_tags:
                position = "header"
            elif "footer" in parent_tags:
                position = "footer"
            elif "aside" in parent_tags:
                position = "sidebar"
            else:
                position = "header"

            if logo_url:
                image_format = _detect_format(logo_url)

            if logo_url:
                try:
                    filename = os.path.basename(urlparse(logo_url).path)
                    if filename:
                        dims = await page.evaluate(f"""() => {{
                            const els = document.querySelectorAll('img');
                            for (const el of els) {{
                                if (el.complete && el.naturalWidth &&
                                    el.getAttribute('src') && el.getAttribute('src').includes('{filename}')) {{
                                    return [el.naturalWidth, el.naturalHeight];
                                }}
                            }}
                            return null;
                        }}""")
                        if dims:
                            width, height = int(dims[0]), int(dims[1])
                            is_retina = width > 200
                except Exception:
                    pass

        # Download logo for format/transparency/color analysis
        if logo_url and _PIL_AVAILABLE:
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    resp = await client.get(logo_url)
                    if resp.status_code == 200:
                        content_type = resp.headers.get("content-type", "")
                        raw = resp.content
                        if not image_format:
                            image_format = "svg" if "svg" in content_type else "raster"

                        if raw:
                            try:
                                img_pil = Image.open(io.BytesIO(raw))
                                if width is None:
                                    width = img_pil.width
                                    height = img_pil.height
                                    is_retina = width > 200

                                if image_format == "svg":
                                    has_transparency = None
                                else:
                                    if img_pil.mode == "RGBA":
                                        pixels = list(img_pil.getdata())
                                        transparent = sum(1 for p in pixels if p[3] < 255)
                                        has_transparency = transparent > 0
                                    elif "transparency" in img_pil.info:
                                        has_transparency = True
                                    else:
                                        has_transparency = False

                                if _COLORTHIEF_AVAILABLE and image_format != "svg":
                                    try:
                                        cf = ColorThief(io.BytesIO(raw))
                                        palette = cf.get_palette(color_count=3, quality=1)
                                        dominant_colors = [
                                            f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette
                                        ]
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                    else:
                        logger.warning(
                            "Logo download failed | url=%s | status=%s",
                            logo_url, resp.status_code
                        )
            except Exception as exc:
                logger.warning("Logo download error | url=%s | error=%s", logo_url, exc)

        if logo_url and not image_format:
            image_format = _detect_format(logo_url)

        return LogoInfo(
            logo_url=logo_url,
            format=image_format,
            has_transparent_background=has_transparency,
            estimated_width=width,
            estimated_height=height,
            dominant_colors=dominant_colors,
            position=position,
            is_retina_quality=is_retina,
            is_favicon_fallback=is_favicon_fallback,
        )

    async def extract_typography(
        self,
        page,
        html: str,
    ) -> TypographyInfo:
        elements = ["body", "h1", "h2", "h3", "h4", "p", "button", "nav", "small"]
        skipped_elements: List[str] = []
        raw: Dict[str, Any] = {}

        for tag in elements:
            try:
                data = await page.evaluate(f"""() => {{
                    const el = document.querySelector('{tag}');
                    if (!el) return null;
                    const s = getComputedStyle(el);
                    return {{
                        fontFamily: s.fontFamily,
                        fontWeight: s.fontWeight,
                        fontSize: s.fontSize,
                        letterSpacing: s.letterSpacing,
                        lineHeight: s.lineHeight,
                    }};
                }}""")
                if data is None:
                    skipped_elements.append(tag)
                else:
                    raw[tag] = data
            except Exception:
                skipped_elements.append(tag)
                raw[tag] = {}

        def _parse_font_family(css_value: str) -> List[str]:
            families: List[str] = []
            for part in css_value.split(","):
                cleaned = part.strip().strip("'\"").strip()
                if cleaned and cleaned not in families:
                    families.append(cleaned)
            return families

        def _parse_weight(w: str) -> Optional[int]:
            try:
                return int(w)
            except (ValueError, TypeError):
                if w == "normal":
                    return 400
                if w == "bold":
                    return 700
                if w == "lighter":
                    return 300
                if w == "bolder":
                    return 900
                return None

        body_data = raw.get("body", {})
        body_family_raw = body_data.get("fontFamily", "")
        body_families = _parse_font_family(body_family_raw)

        primary_font = body_families[0] if body_families else None

        h1_data = raw.get("h1", {}) or raw.get("h2", {})
        h1_families = _parse_font_family(h1_data.get("fontFamily", ""))
        heading_font = h1_families[0] if h1_families else (body_families[0] if body_families else None)

        btn_data = raw.get("button", {})
        nav_data = raw.get("nav", {})
        btn_families = _parse_font_family(btn_data.get("fontFamily", ""))
        nav_families = _parse_font_family(nav_data.get("fontFamily", ""))
        secondary_font = None
        for f in btn_families:
            if f != primary_font:
                secondary_font = f
                break
        if not secondary_font:
            for f in nav_families:
                if f != primary_font:
                    secondary_font = f
                    break

        fallback_stack: List[Dict[str, Any]] = []
        for fam in body_families:
            is_sys = fam in _SYSTEM_FONTS
            fallback_stack.append({"family": fam, "is_system_font": is_sys})

        is_system_font = any(f["is_system_font"] for f in fallback_stack) and bool(fallback_stack)
        is_google_font = False
        if primary_font:
            try:
                soup = BeautifulSoup(html, "html.parser")
                google_links = soup.select(
                    'link[href*="fonts.googleapis.com"], link[href*="fonts.gstatic.com"]'
                )
                for link in google_links:
                    href = link.get("href", "")
                    if primary_font.lower().replace(" ", "") in href.lower().replace("+", "").replace("%20", ""):
                        is_google_font = True
                        break
            except Exception:
                pass

        weights_used: List[int] = []
        seen_weights: set = set()
        for tag, data in raw.items():
            w = _parse_weight(data.get("fontWeight", ""))
            if w is not None and w not in seen_weights:
                seen_weights.add(w)
                weights_used.append(w)
        weights_used.sort()

        hierarchy: Dict[str, Any] = {}
        for tag in elements:
            data = raw.get(tag, {})
            if not data:
                continue
            families = _parse_font_family(data.get("fontFamily", ""))
            hierarchy[tag] = {
                "font_size": data.get("fontSize"),
                "line_height": data.get("lineHeight"),
                "letter_spacing": data.get("letterSpacing"),
                "font_weight": _parse_weight(data.get("fontWeight", "")),
                "font_family": families[0] if families else None,
            }

        return TypographyInfo(
            primary_font=primary_font,
            heading_font=heading_font,
            secondary_font=secondary_font,
            fallback_stack=fallback_stack,
            is_google_font=is_google_font,
            is_system_font=is_system_font,
            weights_used=weights_used,
            hierarchy=hierarchy,
        )

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_business_info(self, soup: BeautifulSoup, base_url: str) -> BusinessInfo:
        name = ""
        tag = soup.find("meta", attrs={"property": "og:site_name"})
        if tag and tag.get("content"):
            name = str(tag["content"]).strip()
        if not name:
            tag = soup.find("title")
            if tag and tag.string:
                name = tag.string.strip()

        description = ""
        for meta_name in ("description", "og:description", "twitter:description"):
            tag = soup.find("meta", attrs={"name": meta_name}) or soup.find("meta", attrs={"property": meta_name})
            if tag and tag.get("content"):
                description = str(tag["content"]).strip()
                break

        logo = ""
        logo_selectors = [
            'header img[class*="logo"]',
            'nav img[class*="logo"]',
            'img[class*="logo"]',
            'img[id*="logo"]',
            'a[class*="logo"] img',
            '.logo img',
            '#logo img',
        ]
        for sel in logo_selectors:
            tag = soup.select_one(sel)
            if tag and tag.get("src"):
                logo = urljoin(base_url, str(tag["src"]))
                break

        favicon = ""
        favicon_tag = soup.find("link", attrs={"rel": re.compile(r"icon", re.I)})
        if favicon_tag and favicon_tag.get("href"):
            favicon = urljoin(base_url, str(favicon_tag["href"]))
        if not favicon:
            favicon = urljoin(base_url, "/favicon.ico")

        phone = ""
        emails = set()
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if href.startswith("tel:"):
                phone = href.replace("tel:", "").strip().split("?")[0]
            elif href.startswith("mailto:"):
                e = href.replace("mailto:", "").strip().split("?")[0].lower()
                if e and not e.endswith((".png", ".jpg", ".gif", ".svg")):
                    emails.add(e)

        text = soup.get_text(separator=" ", strip=True)
        for match in re.finditer(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text):
            e = match.group(0).lower()
            if not e.endswith((".png", ".jpg", ".gif", ".svg", ".css")):
                emails.add(e)

        address = ""
        addr_tag = soup.find("address")
        if addr_tag:
            address = addr_tag.get_text(" ", strip=True)

        industry = self._extract_industry(soup)
        city, country = self._extract_city_country(soup, base_url)
        google_maps_url = self._extract_google_maps_url(soup)
        opening_hours = self._extract_opening_hours(soup)
        social_links = self._extract_social_links(soup, base_url)

        return BusinessInfo(
            name=name[:255] if name else "",
            category="",
            industry=industry[:100] if industry else None,
            description=description[:1000] if description else None,
            logo=logo or None,
            favicon=favicon or None,
            website_url=base_url,
            phone=phone or None,
            email=sorted(emails)[0] if emails else None,
            address=address[:500] if address else None,
            city=city[:100] if city else None,
            country=country[:100] if country else None,
            google_maps_url=google_maps_url or None,
            opening_hours=opening_hours[:2000] if opening_hours else None,
            social_links=social_links,
        )

    @staticmethod
    def _extract_industry(soup: BeautifulSoup) -> Optional[str]:
        kw_tag = soup.find("meta", attrs={"name": "keywords"})
        if kw_tag and kw_tag.get("content"):
            keywords = str(kw_tag["content"]).lower()
            industry_keywords = {
                "restaurant", "food", "cafe", "dining", "hospitality",
                "retail", "ecommerce", "shop", "store",
                "healthcare", "medical", "clinic", "hospital", "dentist",
                "legal", "law", "attorney", "lawyer",
                "real estate", "property", "realtor",
                "construction", "contractor", "builder",
                "technology", "software", "saas", "it ",
                "education", "school", "training", "academy",
                "automotive", "car", "auto", "dealership",
                "fitness", "gym", "wellness", "spa",
                "beauty", "salon", "barber",
                "financial", "bank", "insurance", "accounting",
                "manufacturing", "industrial",
                "logistics", "transportation", "shipping",
                "agriculture", "farming",
                "energy", "solar", "renewable",
                "media", "entertainment", "publishing",
                "nonprofit", "charity", "ngo",
                "marketing", "advertising", "agency",
                "consulting", "professional services",
            }
            for kw in industry_keywords:
                if kw in keywords:
                    return kw.title()

        json_ld = soup.find("script", attrs={"type": "application/ld+json"})
        if json_ld and json_ld.string:
            try:
                data = json.loads(json_ld.string)
                for item in data if isinstance(data, list) else [data]:
                    atype = (item.get("@type") or "").lower()
                    if atype in ("organization", "localbusiness", "corporation", "professional service"):
                        sector = item.get("sector") or item.get("industry") or item.get("knowsAbout") or ""
                        if sector:
                            return str(sector)[:100]
            except (json.JSONDecodeError, AttributeError):
                pass

        body = soup.body
        if body:
            page_text = body.get_text(strip=True).lower()[:3000]
            industry_keywords = {
                "restaurant": ["restaurant", "menu", "catering", "dine-in"],
                "healthcare": ["clinic", "patient", "doctor", "medical"],
                "legal": ["attorney", "law firm", "legal services", "lawyer"],
                "technology": ["software", "app", "digital", "technology"],
                "education": ["school", "course", "program", "curriculum"],
                "real estate": ["property", "listing", "real estate", "agent"],
                "construction": ["construction", "contractor", "renovation", "building"],
                "fitness": ["gym", "workout", "fitness", "personal training"],
                "automotive": ["dealership", "auto", "mechanic", "repair shop"],
                "financial": ["financial", "investment", "loan", "banking"],
            }
            scores = {}
            for ind, kws in industry_keywords.items():
                scores[ind] = sum(1 for kw in kws if kw in page_text)
            best = max(scores, key=scores.get)
            if scores[best] >= 2:
                return best.title()

        return None

    @staticmethod
    def _extract_city_country(soup: BeautifulSoup, base_url: str) -> Tuple[Optional[str], Optional[str]]:
        city = None
        country = None

        address_tag = soup.find("address")
        if address_tag:
            addr_text = address_tag.get_text(" ", strip=True)
            parts = [p.strip() for p in addr_text.split(",") if p.strip()]
            if len(parts) >= 2:
                city = parts[-2].strip()
                country = parts[-1].strip()

        if not city or not country:
            json_ld = soup.find("script", attrs={"type": "application/ld+json"})
            if json_ld and json_ld.string:
                try:
                    data = json.loads(json_ld.string)
                    for item in data if isinstance(data, list) else [data]:
                        address_obj = item.get("address") or {}
                        if isinstance(address_obj, dict):
                            if not city:
                                city = address_obj.get("addressLocality") or address_obj.get("locality")
                            if not country:
                                country = address_obj.get("addressCountry") or address_obj.get("country")
                        elif isinstance(address_obj, str):
                            parts = [p.strip() for p in address_obj.split(",")]
                            if len(parts) >= 3 and not city and not country:
                                city = parts[-3]
                                country = parts[-1]
                except (json.JSONDecodeError, AttributeError):
                    pass

        if not country:
            parsed = urlparse(base_url)
            tld = parsed.netloc.rsplit(".", 1)[-1].lower() if "." in parsed.netloc else ""
            tld_country_map = {
                "us": "United States", "uk": "United Kingdom", "ca": "Canada",
                "au": "Australia", "de": "Germany", "fr": "France",
                "es": "Spain", "it": "Italy", "nl": "Netherlands",
                "br": "Brazil", "jp": "Japan", "cn": "China",
                "in": "India", "mx": "Mexico", "ae": "UAE",
            }
            if tld in tld_country_map:
                country = tld_country_map[tld]

        if not country:
            body = soup.body
            if body:
                text = body.get_text(strip=True).lower()[:2000]
                country_keywords = {
                    "United States": ["united states", "usa", "us"],
                    "United Kingdom": ["united kingdom", "uk", "england", "britain"],
                    "Canada": ["canada", "canadian"],
                    "Australia": ["australia", "australian"],
                    "Germany": ["germany", "german"],
                    "France": ["france", "french"],
                    "Spain": ["spain", "spanish"],
                    "Italy": ["italy", "italian"],
                    "India": ["india", "indian"],
                    "UAE": ["dubai", "uae", "abu dhabi"],
                }
                for c_name, keywords in country_keywords.items():
                    if any(kw in text for kw in keywords):
                        country = c_name
                        break

        return city, country

    @staticmethod
    def _extract_google_maps_url(soup: BeautifulSoup) -> Optional[str]:
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if "google.com/maps" in href or "maps.google" in href:
                return href
        iframe = soup.find("iframe", src=re.compile(r"google\.com/maps|maps\.google"))
        if iframe and iframe.get("src"):
            return str(iframe["src"])
        return None

    @staticmethod
    def _extract_opening_hours(soup: BeautifulSoup) -> Optional[str]:
        json_ld = soup.find("script", attrs={"type": "application/ld+json"})
        if json_ld and json_ld.string:
            try:
                data = json.loads(json_ld.string)
                for item in data if isinstance(data, list) else [data]:
                    hours = item.get("openingHoursSpecification") or item.get("openingHours") or []
                    if isinstance(hours, list) and hours:
                        lines = []
                        for spec in hours:
                            day = spec.get("dayOfWeek", "")
                            opens = spec.get("opens", "")
                            closes = spec.get("closes", "")
                            if day and opens and closes:
                                lines.append(f"{day}: {opens} – {closes}")
                        if lines:
                            return "; ".join(lines)
            except (json.JSONDecodeError, AttributeError):
                pass

        hour_elements = soup.find_all(class_=re.compile(r"hours|schedule|opening|operating|business.hours", re.I))
        hour_elements += soup.find_all(id=re.compile(r"hours|schedule|opening|operating", re.I))
        hour_elements += soup.find_all("table", class_=re.compile(r"hours|schedule", re.I))

        if hour_elements:
            lines = []
            for el in hour_elements:
                text = el.get_text(" ", strip=True)
                if text and re.search(r"(mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)", text[:50], re.I):
                    cleaned = re.sub(r"\s+", " ", text)
                    lines.append(cleaned)
            if lines:
                return " | ".join(lines[:5])

        body = soup.body
        if body:
            text = body.get_text(strip=True)
            hour_pattern = re.compile(
                r"(mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
                r"[^.]*?\d{1,2}:\d{2}\s*(am|pm)", re.I
            )
            matches = hour_pattern.findall(text)
            if matches:
                return " | ".join(m.strip() for m in [m[0] for m in matches[:7]] if m.strip())

        return None

    def _extract_brand_identity(self, soup: BeautifulSoup, computed: Dict[str, Any], color_palette: ColorPalette, logo_info: LogoInfo, typography_info: TypographyInfo) -> BrandIdentity:
        tagline = ""
        tagline_selectors = [
            '[class*="tagline"]',
            '[class*="subtitle"]',
            '[class*="hero-subtitle"]',
            '[class*="strapline"]',
        ]
        for sel in tagline_selectors:
            tag = soup.select_one(sel)
            if tag:
                text = tag.get_text(strip=True)
                if text:
                    tagline = text
                    break

        return BrandIdentity(
            tagline=tagline[:255] or None,
            brand_colors=color_palette,
            logo_info=logo_info,
            typography_info=typography_info,
        )

    def _extract_seo(self, soup: BeautifulSoup, url: str) -> SEOInfo:
        title_tag = soup.find("title")
        page_title = title_tag.string.strip() if title_tag and title_tag.string else ""

        meta_desc = ""
        tag = soup.find("meta", attrs={"name": "description"})
        if tag and tag.get("content"):
            meta_desc = str(tag["content"]).strip()

        keywords = []
        kw_tag = soup.find("meta", attrs={"name": "keywords"})
        if kw_tag and kw_tag.get("content"):
            keywords = [k.strip() for k in str(kw_tag["content"]).split(",") if k.strip()]

        h1_tags = soup.find_all("h1")
        has_h1 = len(h1_tags) > 0

        https_enabled = url.lower().startswith("https://")

        return SEOInfo(
            page_title=page_title[:500] or None,
            meta_description=meta_desc[:1000] or None,
            focus_keywords=keywords[:20],
            missing_meta_description=not bool(meta_desc),
            missing_title=not bool(page_title),
            missing_h1=not has_h1,
            https_enabled=https_enabled,
            ssl_status=https_enabled,
        )

    def _extract_typography(self, computed: Dict[str, Any]) -> Typography:
        fonts = []
        detected = computed.get("detectedFonts", [])
        for f in detected[:10]:
            usage = None
            if f in str(computed.get("h1Font", "")):
                usage = "heading_h1"
            elif f in str(computed.get("h2Font", "")):
                usage = "heading_h2"
            elif f in str(computed.get("bodyFont", "")):
                usage = "body"
            fonts.append(FontInfo(family=f, usage=usage))

        return Typography(
            fonts=fonts,
            heading_h1=computed.get("h1Font"),
            heading_h2=computed.get("h2Font"),
            heading_h3=computed.get("h3Font"),
            body=computed.get("bodyFont"),
        )

    def _extract_navigation(self, soup: BeautifulSoup, base_url: str) -> List[NavigationItem]:
        nav_elem = soup.find("nav") or soup.select_one('[role="navigation"]') or soup.select_one("header")
        if not nav_elem:
            return []

        items: List[NavigationItem] = []
        seen_hrefs = set()
        for a in nav_elem.find_all("a", href=True):
            href = str(a["href"])
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            label = a.get_text(strip=True)
            if not label or len(label) > 100:
                continue
            full_url = urljoin(base_url, href) if not href.startswith(("http://", "https://")) else href
            parsed = urlparse(full_url)
            path = parsed.path
            if path in seen_hrefs:
                continue
            seen_hrefs.add(path)

            children = []
            ul = a.find_parent("li")
            if ul:
                submenu = ul.find("ul")
                if submenu:
                    for sub_a in submenu.find_all("a", href=True):
                        sub_href = str(sub_a["href"])
                        sub_label = sub_a.get_text(strip=True)
                        if sub_label:
                            children.append(NavigationItem(
                                label=sub_label[:100],
                                url=urljoin(base_url, sub_href),
                            ))

            items.append(NavigationItem(
                label=label[:100],
                url=full_url,
                children=children,
            ))

        return items[:20]

    def _extract_hero(self, soup: BeautifulSoup) -> HeroSection:
        hero_elem = (
            soup.select_one('[class*="hero"]')
            or soup.select_one('[id*="hero"]')
            or soup.select_one("header")
        )
        if not hero_elem:
            return HeroSection()

        title = ""
        h1 = hero_elem.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        subtitle = ""
        for tag in hero_elem.find_all(["p", "h2", "h3", "span"]):
            text = tag.get_text(strip=True)
            classes = " ".join(tag.get("class", []))
            if text and ("subtitle" in classes.lower() or "sub-heading" in classes.lower()):
                subtitle = text
                break

        cta_buttons = self._extract_ctas_from_element(hero_elem)

        bg_img = ""
        elem_with_bg = hero_elem.select_one('[style*="background-image"]')
        if elem_with_bg:
            match = re.search(r"url\(['\"]?(.*?)['\"]?\)", str(elem_with_bg.get("style", "")))
            if match:
                bg_img = match.group(1)

        img_tag = hero_elem.find("img")
        if img_tag and img_tag.get("src") and not bg_img:
            bg_img = str(img_tag["src"])

        return HeroSection(
            title=title[:500] or None,
            subtitle=subtitle[:500] or None,
            cta_buttons=cta_buttons,
            background_image=bg_img or None,
        )

    async def extract_services_and_products(
        self,
        page,
        html: str,
        url: str,
    ):
        soup = BeautifulSoup(html, "html.parser")

        _CATEGORY_KEYWORDS = {
            "service": ["service", "what we do", "solutions", "offerings", "capabilities", "our services"],
            "product": ["product", "our products", "shop", "store", "buy", "catalog"],
            "feature": ["feature", "why choose", "key features", "benefits", "what makes us"],
            "solution": ["solution", "our solutions", "industry solutions"],
            "offering": ["offering", "our offerings"],
            "package": ["package", "plans", "bundles"],
            "plan": ["plan", "pricing plans", "subscription", "membership"],
        }

        _BADGE_KEYWORDS = frozenset({
            "popular", "best seller", "bestseller", "featured", "recommended",
            "most popular", "top rated", "new", "sale", "discount", "limited",
            "exclusive", "pro", "enterprise", "premium",
        })

        section_candidates: List[Any] = []
        for sec in soup.find_all(["section", "div"]):
            parent = sec.parent
            if parent and parent.name not in ("body", "main", "div"):
                continue
            has_heading = bool(sec.find(["h1", "h2", "h3"]))
            cls_str = " ".join(sec.get("class", [])).lower()
            has_signal = any(kw in cls_str for kw in ("service", "product", "feature", "solution", "offering", "package", "plan", "card", "grid", "pricing"))
            if has_heading or has_signal:
                section_candidates.append(sec)

        service_items: List[ServiceCard] = []
        product_items: List[ProductItem] = []
        seen_titles: Dict[str, str] = {}

        for sec in section_candidates:
            cls_str = " ".join(sec.get("class", [])).lower()
            sec_heading_el = sec.find(["h1", "h2", "h3"])
            sec_heading = sec_heading_el.get_text(strip=True).lower() if sec_heading_el else ""
            sec_selector = f"{sec.name}.{'.'.join(sec.get('class', []))}" if sec.get("class") else sec.name

            category = "service"
            for cat, kws in _CATEGORY_KEYWORDS.items():
                if any(kw in sec_heading for kw in kws) or any(kw in cls_str for kw in kws):
                    category = cat
                    break

            cards = sec.find_all(["div", "article", "li"], class_=lambda c: c and any(k in " ".join(c).lower() for k in ("card", "item", "col-", "grid", "service", "product", "feature", "solution", "offering", "package", "plan", "pricing")), recursive=True)

            seen_local: set = set()
            order = 0
            for card in cards:
                if card.find_parent(["nav", "footer", "header"]):
                    continue
                card_cls = " ".join(card.get("class", [])).lower()
                if any(k in card_cls for k in ("nav", "menu", "dropdown", "cookie", "banner", "ad-")):
                    continue

                heading_el = card.find(["h2", "h3", "h4", "strong"])
                title_text = heading_el.get_text(strip=True) if heading_el else ""
                if not title_text or len(title_text) > 120:
                    if card.find("img") and card.get_text(strip=True):
                        title_text = card.get_text(strip=True)[:100]
                    else:
                        continue
                title_lower = title_text.lower()
                if title_lower in seen_local:
                    continue
                seen_local.add(title_lower)
                if title_lower in seen_titles:
                    continue
                seen_titles[title_lower] = category

                order += 1

                subtitle_el = None
                for tag in card.find_all(["h3", "h4", "h5", "p"]):
                    if tag is heading_el:
                        continue
                    cls_t = " ".join(tag.get("class", [])).lower()
                    if "subtitle" in cls_t:
                        subtitle_el = tag
                        break
                if not subtitle_el and heading_el:
                    nxt = heading_el.find_next_sibling(["h3", "h4", "h5", "p"])
                    if nxt and nxt.get_text(strip=True) != title_text:
                        subtitle_el = nxt

                subtitle = subtitle_el.get_text(strip=True)[:300] if subtitle_el else None

                all_ps = card.find_all("p")
                short_desc = None
                full_desc = None
                for p in all_ps:
                    pt = p.get_text(strip=True)
                    if len(pt) < 20:
                        continue
                    if not short_desc:
                        short_desc = pt[:300]
                    elif not full_desc and pt != short_desc:
                        full_desc = pt[:1000]
                        break

                icon_el = card.find(["img", "svg"], class_=lambda c: c and "icon" in " ".join(c).lower()) if False else card.find("img")
                icon = None
                image = None
                for img in card.find_all("img"):
                    src = img.get("src") or ""
                    cls_i = " ".join(img.get("class", [])).lower()
                    if "icon" in cls_i or "logo" in cls_i or not image:
                        icon = src
                    if "icon" not in cls_i and "logo" not in cls_i:
                        image = src
                    if icon and image:
                        break

                cta_el = card.find(["a", "button"], class_=lambda c: c and any(k in " ".join(c).lower() for k in ("btn", "cta", "button")))
                cta = None
                if cta_el:
                    cta_text = cta_el.get_text(strip=True)
                    cta_url = cta_el.get("href") or ""
                    if cta_text:
                        cta = CtaLink(text=cta_text[:100], url=cta_url)

                price = None
                currency = None
                price_el = card.find(class_=lambda c: c and any(k in " ".join(c).lower() for k in ("price", "cost", "amount"))) or card.find(string=re.compile(r"[\$€£¥]\s*\d+"))
                if price_el:
                    price_text = price_el if isinstance(price_el, str) else price_el.get_text(strip=True)
                    m = re.search(r"([\$€£¥])\s*([\d,]+\.?\d*)", price_text)
                    if m:
                        currency = m.group(1)
                        price = m.group(2)

                badge = None
                for el in card.find_all(["span", "div", "label", "strong", "small"]):
                    bt = el.get_text(strip=True).lower()
                    if bt in _BADGE_KEYWORDS:
                        badge = bt[:50]
                        break

                features = []
                for li in card.find_all("li"):
                    ft = li.get_text(strip=True)
                    if ft:
                        features.append(ft[:200])
                    if len(features) >= 10:
                        break

                source_url = url

                if category in ("product", "plan", "package"):
                    product_items.append(ProductItem(
                        title=title_text[:300],
                        subtitle=subtitle,
                        short_description=short_desc,
                        full_description=full_desc,
                        icon=icon,
                        image=image,
                        category=category,
                        order_on_page=order,
                        section_selector=sec_selector,
                        source_url=source_url,
                        cta=cta,
                        price=price,
                        currency=currency,
                        badge=badge,
                    ))
                else:
                    service_items.append(ServiceCard(
                        name=title_text[:200],
                        description=short_desc or full_desc,
                        icon=icon,
                        image=image,
                        features=features,
                        title=title_text[:300],
                        subtitle=subtitle,
                        short_description=short_desc,
                        full_description=full_desc,
                        category=category,
                        order_on_page=order,
                        section_selector=sec_selector,
                        source_url=source_url,
                        cta=cta,
                        price=price,
                        currency=currency,
                        badge=badge,
                    ))

                if len(service_items) + len(product_items) >= 40:
                    break
            if len(service_items) + len(product_items) >= 40:
                break

        return service_items[:30], product_items[:20]

    def _extract_services(self, soup: BeautifulSoup) -> List[ServiceCard]:
        section = self._find_section(soup, SECTION_KEYWORDS["services"])
        if not section:
            return []

        cards: List[ServiceCard] = []
        article_elements = section.find_all(["div", "article", "li"], class_=True, recursive=True)

        seen_names = set()
        for el in article_elements:
            classes = " ".join(el.get("class", [])).lower()
            if not any(k in classes for k in ["service", "card", "item", "feature", "solution", "offer"]):
                if len(cards) >= 5:
                    continue

            h = el.find(["h3", "h4", "h2", "strong"])
            name = h.get_text(strip=True) if h else ""

            if not name or len(name) > 120 or name.lower() in seen_names:
                continue
            seen_names.add(name.lower())

            desc = ""
            p = el.find("p")
            if p:
                desc = p.get_text(strip=True)

            icon = ""
            img = el.find("img")
            if img and img.get("src"):
                icon = str(img["src"])

            features = []
            for li in el.find_all("li"):
                text = li.get_text(strip=True)
                if text:
                    features.append(text)

            cards.append(ServiceCard(
                name=name[:100],
                description=desc[:500] or None,
                icon=icon or None,
                features=features[:10],
            ))

        return cards[:20]

    def _extract_contact(self, soup: BeautifulSoup) -> ContactInfo:
        emails = set()
        phones = set()
        address = ""
        form_present = False
        form_fields: List[str] = []

        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if href.startswith("mailto:"):
                e = href.replace("mailto:", "").split("?")[0].strip().lower()
                if e and not e.endswith((".png", ".jpg", ".gif", ".svg")):
                    emails.add(e)
            elif href.startswith("tel:"):
                p = href.replace("tel:", "").strip().split("?")[0]
                if p:
                    phones.add(p)

        text = soup.get_text(separator=" ", strip=True)
        for match in re.finditer(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text):
            e = match.group(0).lower()
            if not e.endswith((".png", ".jpg", ".gif", ".svg", ".css")):
                emails.add(e)
        for match in re.finditer(r"(?:\+?\d{1,4}[\s\-.]?)?\(?\d{1,5}\)?[\s\-.]?\d{1,5}[\s\-.]?\d{1,9}", text):
            cleaned = match.group(0).strip()
            digits = re.sub(r"\D", "", cleaned)
            if 7 <= len(digits) <= 15:
                phones.add(cleaned)

        addr_tag = soup.find("address")
        if addr_tag:
            address = addr_tag.get_text(" ", strip=True)

        forms = soup.find_all("form")
        if forms:
            form_present = True
            for form in forms[:3]:
                for inp in form.find_all(["input", "textarea", "select"]):
                    name = inp.get("name") or inp.get("id") or inp.get("placeholder") or ""
                    if name:
                        form_fields.append(str(name))

        return ContactInfo(
            emails=sorted(emails)[:10],
            phones=sorted(phones)[:10],
            address=address[:500] or None,
            contact_form_present=form_present,
            contact_form_fields=form_fields[:20],
        )

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[ImageAsset]:
        images: List[ImageAsset] = []
        seen_urls = set()

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
            if not src:
                continue
            full_url = urljoin(base_url, str(src))
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            alt = img.get("alt", "")
            width = img.get("width")
            height = img.get("height")
            img_type = ""

            if not full_url.startswith("data:"):
                parsed = urlparse(full_url)
                ext = parsed.path.rsplit(".", 1)[-1].lower() if "." in parsed.path else ""
                if ext in ("jpg", "jpeg", "png", "gif", "svg", "webp", "ico"):
                    img_type = ext

            images.append(ImageAsset(
                url=full_url,
                alt=str(alt)[:255] or None,
                width=int(width) if width and str(width).isdigit() else None,
                height=int(height) if height and str(height).isdigit() else None,
                type=img_type or None,
            ))

        return images[:200]

    def _extract_testimonials(self, soup: BeautifulSoup) -> List[Testimonial]:
        section = self._find_section(soup, SECTION_KEYWORDS["testimonials"])
        if not section:
            return []

        testimonials: List[Testimonial] = []
        for el in section.find_all(["div", "article", "blockquote"], class_=True, recursive=True):
            classes = " ".join(el.get("class", [])).lower()
            if not any(k in classes for k in ["testimonial", "review", "quote", "feedback"]):
                continue

            content = ""
            for q in el.find_all(["blockquote", "q", "p"]):
                t = q.get_text(strip=True)
                if len(t) > 20:
                    content = t
                    break
            if not content:
                continue

            author = ""
            role = ""
            company = ""

            author_el = el.find(["strong", "span", "cite"], class_=re.compile(r"author|name|client", re.I))
            if author_el:
                author = author_el.get_text(strip=True)
            role_el = el.find(["span", "small"], class_=re.compile(r"role|title|position", re.I))
            if role_el:
                role = role_el.get_text(strip=True)
            company_el = el.find(["span", "small"], class_=re.compile(r"company|org", re.I))
            if company_el:
                company = company_el.get_text(strip=True)

            avatar = ""
            img = el.find("img")
            if img and img.get("src"):
                avatar = str(img["src"])

            rating = None
            rating_el = el.find(class_=re.compile(r"star|rating", re.I))
            if rating_el:
                match = re.search(r"(\d+)", rating_el.get_text())
                if match:
                    rating = int(match.group(1))

            testimonials.append(Testimonial(
                author=author[:100] or None,
                role=role[:100] or None,
                company=company[:100] or None,
                content=content[:1000],
                avatar=avatar or None,
                rating=rating,
            ))

        return testimonials[:50]

    async def extract_testimonials(self, page, html: str, url: str):
        soup = BeautifulSoup(html, "html.parser")

        WIDGET_PLATFORMS: Dict[str, str] = {
            "google": "Google",
            "trustpilot": "Trustpilot",
            "clutch": "Clutch",
            "goodfirms": "GoodFirms",
            "capterra": "Capterra",
            "facebook": "Facebook",
            "g2.com": "G2",
            "g2crowd": "G2",
        }

        widget_platforms_found: List[str] = []

        section_containers: List[Any] = []
        seen_sec_ids: set = set()

        widget_iframes = soup.find_all("iframe")
        for iframe in widget_iframes:
            src = iframe.get("src", "")
            for key, name in WIDGET_PLATFORMS.items():
                if key in src.lower() and name not in widget_platforms_found:
                    widget_platforms_found.append(name)

        widget_divs = soup.find_all("div", class_=lambda c: c and any(k in " ".join(c).lower() for k in ("trustpilot", "clutch-widget", "goodfirms", "capterra", "g2-widget", "google-reviews")))
        for div in widget_divs:
            cls_str = " ".join(div.get("class", [])).lower()
            for key, name in WIDGET_PLATFORMS.items():
                if key in cls_str and name not in widget_platforms_found:
                    widget_platforms_found.append(name)

        for sec in soup.find_all(["section", "div"]):
            parent = sec.parent
            if parent and parent.name not in ("body", "main", "div", "section"):
                continue
            cls_str = " ".join(sec.get("class", [])).lower()
            sec_text = sec.get_text(strip=True).lower()[:300]
            has_signal = any(kw in cls_str for kw in ("testimonial", "review", "feedback", "quote", "carousel", "slider", "swiper"))
            if not has_signal:
                sec_kws = SECTION_KEYWORDS["testimonials"]
                has_signal = any(kw in sec_text for kw in sec_kws)
            if has_signal:
                sec_id = id(sec)
                if sec_id not in seen_sec_ids:
                    seen_sec_ids.add(sec_id)
                    section_containers.append(sec)

        if not section_containers:
            section_containers = [soup]

        testimonials: List[Testimonial] = []
        seen_texts: set = set()
        order = 0

        for sec in section_containers:
            cards = sec.find_all(["div", "article", "blockquote", "li"], class_=lambda c: c and any(k in " ".join(c).lower() for k in ("testimonial", "review", "quote", "feedback", "card", "item", "slide", "swiper-slide", "carousel-item")), recursive=True)

            for card in cards:
                if card.find_parent(["nav", "footer", "header"]):
                    continue
                card_cls = " ".join(card.get("class", [])).lower()
                if any(k in card_cls for k in ("nav", "menu", "cookie", "banner", "ad-", "comment", "forum")):
                    continue

                content = ""
                for tag in card.find_all(["blockquote", "q", "p"]):
                    t = tag.get_text(strip=True)
                    if len(t) > 15:
                        content = t[:2000]
                        break
                if not content:
                    content = card.get_text(strip=True)
                    if len(content) < 15:
                        continue

                norm = " ".join(content.lower().split())
                if norm in seen_texts:
                    continue
                seen_texts.add(norm)

                order += 1

                author_name: Optional[str] = None
                author_el = card.find(["strong", "span", "cite"], class_=lambda c: c and any(k in " ".join(c).lower() for k in ("author", "name", "client", "customer", "user")))
                if not author_el:
                    author_el = card.find(["strong", "span", "cite"])
                if author_el:
                    t = author_el.get_text(strip=True)
                    if t and len(t) < 80 and len(t) > 1:
                        author_name = t[:100]

                company_name: Optional[str] = None
                role: Optional[str] = None
                for el in card.find_all(["span", "small", "p"]):
                    t = el.get_text(strip=True)
                    if not t:
                        continue
                    cls_e = " ".join(el.get("class", [])).lower()
                    if "company" in cls_e or "org" in cls_e:
                        company_name = t[:100]
                    elif "role" in cls_e or "title" in cls_e or "position" in cls_e:
                        role = t[:100]

                avatar_url: Optional[str] = None
                for img in card.find_all("img"):
                    cls_i = " ".join(img.get("class", [])).lower()
                    src = img.get("src") or ""
                    if "avatar" in cls_i or "author" in cls_i or "photo" in cls_i:
                        avatar_url = src
                        break
                if not avatar_url:
                    img = card.find("img")
                    if img and img.get("src"):
                        avatar_url = img["src"]

                star_count: Optional[int] = None
                rating_el = card.find(class_=lambda c: c and any(k in " ".join(c).lower() for k in ("star", "rating", "stars")))
                if rating_el:
                    txt = rating_el.get_text(strip=True)
                    m = re.search(r"(\d+)\s*/\s*\d+", txt)
                    if m:
                        star_count = min(int(m.group(1)), 5)
                    else:
                        filled = len(rating_el.find_all(class_=lambda c: c and any(k in " ".join(c).lower() for k in ("filled", "active", "star")))) if False else None
                        if filled:
                            star_count = min(filled, 5)
                        else:
                            m2 = re.search(r"(\d+)", txt)
                            if m2:
                                star_count = min(int(m2.group(1)), 5)
                if not star_count:
                    stars = card.find_all(["span", "i", "svg"], class_=lambda c: c and any(k in " ".join(c).lower() for k in ("star", "fa-star", "icon-star")))
                    if stars:
                        star_count = min(len(stars), 5)

                review_date: Optional[str] = None
                for el in card.find_all(["time", "span", "small"]):
                    t = el.get_text(strip=True)
                    if t and re.match(r"\d{4}", t):
                        review_date = t[:50]
                        break
                    datetime_attr = el.get("datetime") or ""
                    if datetime_attr:
                        review_date = datetime_attr[:50]
                        break

                platform: Optional[str] = None
                sec_cls = " ".join(sec.get("class", [])).lower() if sec != soup else ""
                card_cls_lower = card_cls
                combined = sec_cls + " " + card_cls_lower
                for key, name in WIDGET_PLATFORMS.items():
                    if key in combined:
                        platform = name
                        break
                if not platform:
                    for a in card.find_all("a", href=True):
                        href = str(a["href"]).lower()
                        for key, name in WIDGET_PLATFORMS.items():
                            if key in href:
                                platform = name
                                break
                        if platform:
                            break

                verified = False
                for el in card.find_all(["span", "div", "small", "svg"]):
                    cls_v = " ".join(el.get("class", [])).lower() if hasattr(el, "get") else ""
                    t = (el.get_text(strip=True) if hasattr(el, "get_text") else str(el)).lower()
                    if "verified" in cls_v or "verified" in t:
                        verified = True
                        break

                associated_service: Optional[str] = None
                for a in card.find_all("a", href=True):
                    t = a.get_text(strip=True)
                    if t and len(t) < 100:
                        associated_service = t[:100]
                        break

                source_url = url

                testimonials.append(Testimonial(
                    author=author_name,
                    role=role,
                    company=company_name,
                    content=content[:2000],
                    avatar=avatar_url,
                    rating=star_count,
                    author_name=author_name,
                    company_name=company_name,
                    job_title=role,
                    avatar_url=avatar_url,
                    review_text=content[:2000],
                    review_date=review_date,
                    platform=platform,
                    source_url=source_url,
                    section_position=len(testimonials),
                    order=order,
                    verified_badge=verified,
                    star_count=star_count,
                    associated_service=associated_service,
                ))

                if len(testimonials) >= 50:
                    break
            if len(testimonials) >= 50:
                break

        if widget_platforms_found:
            logger.info("extract_testimonials: embedded widgets detected | platforms=%s", widget_platforms_found)

        return testimonials

    def _extract_faqs(self, soup: BeautifulSoup) -> List[FAQ]:
        section = self._find_section(soup, SECTION_KEYWORDS["faq"])
        if not section:
            return []

        faqs: List[FAQ] = []
        qa_pairs = section.find_all(["div", "li"], class_=True, recursive=True)

        for el in qa_pairs:
            classes = " ".join(el.get("class", [])).lower()
            if not any(k in classes for k in ["faq", "question", "accordion", "qa"]):
                continue
            q_el = el.find(class_=re.compile(r"question|q|title", re.I))
            a_el = el.find(class_=re.compile(r"answer|a|content", re.I))

            if q_el and a_el:
                q_text = q_el.get_text(strip=True)
                a_text = a_el.get_text(strip=True)
                if q_text and a_text:
                    faqs.append(FAQ(question=q_text[:255], answer=a_text[:1000]))

        if not faqs:
            items = section.find_all(["div", "li"])
            for item in items:
                texts = item.find_all(["p", "span", "div"])
                q_text = ""
                a_text = ""
                for i, t in enumerate(texts):
                    t_text = t.get_text(strip=True)
                    if t_text and t_text.endswith("?"):
                        q_text = t_text
                        if i + 1 < len(texts):
                            a_text = texts[i + 1].get_text(strip=True)
                        break
                if q_text and a_text:
                    faqs.append(FAQ(question=q_text[:255], answer=a_text[:1000]))

        return faqs[:100]

    def _extract_team(self, soup: BeautifulSoup) -> List[TeamMember]:
        section = self._find_section(soup, SECTION_KEYWORDS["team"])
        if not section:
            return []

        team: List[TeamMember] = []
        for el in section.find_all(["div", "article", "li"], class_=True, recursive=True):
            classes = " ".join(el.get("class", [])).lower()
            if not any(k in classes for k in ["team", "member", "person", "profile", "staff", "people"]):
                continue

            name_el = el.find(["h3", "h4", "strong", "span"])
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) > 100:
                continue

            role = ""
            role_el = el.find(["span", "small", "p"], class_=re.compile(r"role|title|position", re.I))
            if role_el:
                role = role_el.get_text(strip=True)

            bio = ""
            bio_el = el.find("p")
            if bio_el:
                texts = [c for c in bio_el.get_text(strip=True).split("\n") if c.strip()]
                if texts:
                    bio = texts[0]

            img = ""
            img_el = el.find("img")
            if img_el and img_el.get("src"):
                img = str(img_el["src"])

            social = []
            for a in el.find_all("a", href=True):
                href = str(a["href"])
                for domain, platform in SOCIAL_DOMAINS.items():
                    if domain in href:
                        social.append(SocialLink(platform=platform, url=href))
                        break

            team.append(TeamMember(
                name=name[:100],
                role=role[:100] if role else None,
                bio=bio[:500] if bio else None,
                image=img or None,
                social_links=social,
            ))

        return team[:50]

    async def extract_team_members(self, page, html: str) -> List["TeamMember"]:
        soup = BeautifulSoup(html, "html.parser")

        section = self._find_section(soup, SECTION_KEYWORDS["team"])
        if not section:
            section = soup

        members: List["TeamMember"] = []
        seen_names: set = set()
        order = 0

        for el in section.find_all(["div", "article", "li"], class_=True, recursive=True):
            classes = " ".join(el.get("class", [])).lower()
            if not any(k in classes for k in ("team", "member", "person", "profile", "staff", "people", "card", "col-")):
                continue
            name_el = el.find(["h3", "h4", "strong", "span"])
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) > 100 or name.lower() in seen_names:
                continue
            seen_names.add(name.lower())
            order += 1

            role = ""
            role_el = el.find(["span", "small", "p"], class_=lambda c: c and any(k in " ".join(c).lower() for k in ("role", "title", "position", "job")))
            if not role_el:
                role_el = el.find(["span", "small", "p"])
            if role_el:
                t = role_el.get_text(strip=True)
                if t and len(t) < 80:
                    role = t

            bio = ""
            bio_el = el.find("p")
            if bio_el:
                texts = [c for c in bio_el.get_text(strip=True).split("\n") if c.strip()]
                if texts:
                    bio = texts[0]

            img = ""
            img_el = el.find("img")
            if img_el and img_el.get("src"):
                src = str(img_el["src"])
                if not src.endswith((".svg", ".ico")):
                    img = src

            email = None
            linkedin = None
            twitter = None
            facebook = None
            instagram = None
            for a in el.find_all("a", href=True):
                href = str(a["href"])
                if href.startswith("mailto:"):
                    e = href.replace("mailto:", "").split("?")[0].strip().lower()
                    if e:
                        email = e
                elif "linkedin.com" in href:
                    linkedin = href
                elif "twitter.com" in href or "x.com" in href:
                    twitter = href
                elif "facebook.com" in href:
                    facebook = href
                elif "instagram.com" in href:
                    instagram = href

            qualifications = []
            certs = []
            for li in el.find_all("li"):
                t = li.get_text(strip=True)
                if "certif" in t.lower():
                    certs.append(t[:200])
                elif len(t) > 5:
                    qualifications.append(t[:200])

            department = None
            dept_el = el.find(["span", "small"], class_=lambda c: c and "dept" in " ".join(c).lower())
            if dept_el:
                department = dept_el.get_text(strip=True)[:100]

            years_exp = None
            exp_el = el.find(string=re.compile(r"\d+\s*years?"))
            if exp_el:
                years_exp = exp_el.strip()[:50]

            social = []
            for a in el.find_all("a", href=True):
                href = str(a["href"])
                for domain, platform in SOCIAL_DOMAINS.items():
                    if domain in href:
                        social.append(SocialLink(platform=platform, url=href))
                        break

            members.append(TeamMember(
                name=name[:100],
                role=role[:100] or None,
                bio=bio[:500] or None,
                image=img or None,
                social_links=social,
                full_name=name[:100],
                job_title=role[:100] or None,
                department=department,
                photo_url=img or None,
                email=email,
                linkedin=linkedin,
                twitter=twitter or None,
                facebook=facebook or None,
                instagram=instagram or None,
                years_experience=years_exp,
                qualifications=qualifications[:10],
                certifications=certs[:10],
                display_order=order,
            ))

            if len(members) >= 50:
                break

        return members

    def extract_company_info(self, html: str) -> "CompanySection":
        soup = BeautifulSoup(html, "html.parser")

        ABOUT_KWS = [
            "about us", "about", "who we are", "our story", "our company",
            "our mission", "our vision", "our values", "our history",
            "why choose us", "our process", "our journey", "founder story",
        ]

        section = None
        for tag in soup.find_all(["section", "div", "article"]):
            cls = " ".join(tag.get("class", [])).lower()
            id_val = (tag.get("id") or "").lower()
            combined = cls + " " + id_val
            if any(kw in combined for kw in ABOUT_KWS):
                section = tag
                break
        if not section:
            for tag in soup.find_all(["section", "div", "article"]):
                text = tag.get_text(strip=True).lower()[:300]
                if any(kw in text for kw in ABOUT_KWS):
                    section = tag
                    break
        if not section:
            return CompanySection()

        section_title = None
        h_el = section.find(["h1", "h2", "h3"])
        if h_el:
            section_title = h_el.get_text(strip=True)[:200]

        section_type = "about"
        cls_sec = " ".join(section.get("class", [])).lower()
        for kw in ("mission", "vision", "value", "history", "story", "process", "journey"):
            if kw in cls_sec:
                section_type = kw
                break

        description = None
        for p in section.find_all("p"):
            t = p.get_text(strip=True)
            if len(t) > 30:
                description = t[:2000]
                break

        mission = None
        vision = None
        values_blk = section.find(class_=lambda c: c and any(k in " ".join(c).lower() for k in ("value", "core-value")))
        for h in section.find_all(["h3", "h4", "strong"]):
            t = h.get_text(strip=True).lower()
            nxt = h.find_next_sibling(["p", "div", "span"])
            nxt_text = nxt.get_text(strip=True) if nxt else ""
            if "mission" in t and not mission:
                mission = nxt_text[:1000]
            elif "vision" in t and not vision:
                vision = nxt_text[:1000]

        core_values = []
        if values_blk:
            for li in values_blk.find_all("li"):
                v = li.get_text(strip=True)
                if v:
                    core_values.append(v[:200])
        if not core_values:
            for el in section.find_all(["div", "span"], class_=lambda c: c and "value" in " ".join(c).lower()):
                v = el.get_text(strip=True)
                if v:
                    core_values.append(v[:200])

        years_in_business = None
        for match in re.finditer(r"(?:over\s+|for\s+)?(\d+)\s*\+?\s*years?(?:\s+of|\s+in|\s+experience|\s+business|\s+serving)", section.get_text(), re.I):
            years_in_business = match.group(0).strip()[:100]
            break

        company_size = None
        size_el = section.find(string=re.compile(r"\d+\s*[+-]?\s*\d*\s*employees", re.I))
        if size_el:
            company_size = size_el.strip()[:100]

        business_type = None
        for a in section.find_all(string=re.compile(r"(B2B|B2C|SaaS|e-commerce|manufacturing|agency|consulting|enterprise)", re.I)):
            business_type = a.strip()[:100]
            break

        target_audience = None
        audience_el = section.find(string=re.compile(r"(target|ideal|our)\s+(customer|audience|client|market)", re.I))
        if audience_el:
            target_audience = audience_el.strip()[:300]

        industries_served = []
        for li in section.find_all("li"):
            t = li.get_text(strip=True)
            if t and len(t) < 80:
                industries_served.append(t[:80])
        industries_served = industries_served[:20]

        usp = None
        for h in section.find_all(["h3", "h4", "strong"]):
            t = h.get_text(strip=True).lower()
            if "unique" in t or "usp" in t or "why us" in t or "why choose" in t:
                nxt = h.find_next_sibling(["p", "div"])
                if nxt:
                    usp = nxt.get_text(strip=True)[:500]
                    break

        return CompanySection(
            section_title=section_title,
            section_type=section_type,
            description=description,
            mission=mission,
            vision=vision,
            core_values=core_values[:10],
            years_in_business=years_in_business,
            company_size=company_size,
            business_type=business_type,
            target_audience=target_audience,
            industries_served=industries_served,
            usp=usp,
        )

    def extract_trust_signals(self, html: str) -> List["TrustSignal"]:
        soup = BeautifulSoup(html, "html.parser")
        signals: List["TrustSignal"] = []
        seen: set = set()

        TRUST_PATTERNS: Dict[str, List[str]] = {
            "certification": ["iso", "certified", "certification"],
            "partner": ["google partner", "meta partner", "microsoft partner", "aws partner", "hubspot partner"],
            "award": ["award", "winner", "best", "top rated", "award-winning"],
            "badge": ["badge", "trusted", "trust"],
            "guarantee": ["guarantee", "money back", "warranty", "satisfaction guaranteed"],
            "accreditation": ["accreditation", "accredited", "bbb"],
            "membership": ["member", "membership", "association", "chamber"],
            "security": ["ssl", "secure", "encrypted", "security", "privacy"],
        }

        for img in soup.find_all("img"):
            src = img.get("src") or ""
            alt = (img.get("alt") or "").lower()
            cls = " ".join(img.get("class", [])).lower()
            src_lower = src.lower()
            combined = alt + " " + cls + " " + src_lower

            for sig_type, kws in TRUST_PATTERNS.items():
                if any(kw in combined for kw in kws):
                    val = alt or src.split("/")[-1].split(".")[0]
                    if val and val not in seen:
                        seen.add(val)
                        signals.append(TrustSignal(
                            type=sig_type,
                            value=val[:200],
                            source_url=src[:500],
                            description=None,
                        ))
                    break

        for el in soup.find_all(["span", "div", "p", "small", "li"]):
            t = el.get_text(strip=True)
            if not t or len(t) > 150:
                continue
            tl = t.lower()
            for sig_type, kws in TRUST_PATTERNS.items():
                if any(kw in tl for kw in kws):
                    if t not in seen:
                        seen.add(t)
                        signals.append(TrustSignal(
                            type=sig_type,
                            value=t[:200],
                            source_url=None,
                            description=None,
                        ))
                    break

        return signals[:30]

    def _grade_score(self, score: int) -> str:
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        if score >= 40:
            return "D"
        return "F"

    def _status_label(self, score: int) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 75:
            return "Good"
        if score >= 60:
            return "Average"
        if score >= 40:
            return "Below Average"
        return "Poor"

    def _make_metric(self, score: int, strengths: list = None, weaknesses: list = None, recommendations: list = None) -> "QualityMetric":
        return QualityMetric(
            score=min(100, max(0, score)),
            grade=self._grade_score(min(100, max(0, score))),
            status=self._status_label(min(100, max(0, score))),
            strengths=strengths or [],
            weaknesses=weaknesses or [],
            recommendations=recommendations or [],
        )

    def calculate_quality_metrics(self, profile: "WebsiteProfile") -> "QualityMetrics":
        brand = profile.brand or BrandIdentity()
        consistency = brand.consistency_report

        # --- Content Quality ---
        content_strengths: list = []
        content_weaknesses: list = []
        content_recs: list = []
        content_score = 50

        if profile.website_summary:
            content_score += 15
            content_strengths.append("Website summary extracted")
        if profile.services:
            content_score += min(len(profile.services) * 5, 10)
            content_strengths.append(f"{len(profile.services)} services described")
        if profile.products:
            content_score += min(len(profile.products) * 3, 8)
        if profile.faqs:
            content_score += min(len(profile.faqs) * 2, 8)
            content_strengths.append(f"{len(profile.faqs)} FAQ items found")
        if profile.testimonials:
            content_score += min(len(profile.testimonials) * 2, 5)
        if profile.blog_links:
            content_score += 5
            content_strengths.append("Blog/content section present")
        if profile.seo and profile.seo.page_title:
            content_score += 5
            content_strengths.append("Page title present")
        if profile.seo and profile.seo.missing_h1:
            content_weaknesses.append("Missing H1 heading")
            content_recs.append("Add an H1 heading describing the page purpose")
        if not profile.services:
            content_weaknesses.append("No services section detected")
            content_recs.append("Add a clear services/products section")
        if not profile.faqs and not profile.blog_links:
            content_weaknesses.append("No FAQ or blog content found")
            content_recs.append("Add FAQ or knowledge base content")
        if not profile.website_summary:
            content_weaknesses.append("No website summary generated")
            content_recs.append("Improve content density for better summary extraction")
        if content_score > 100:
            content_score = 100

        # --- Navigation Quality ---
        nav_strengths: list = []
        nav_weaknesses: list = []
        nav_recs: list = []
        nav_score = 40

        nav_info = profile.navigation_info
        primary_count = len(nav_info.primary_nav_items) if nav_info else 0
        footer_count = len(nav_info.footer_nav_items) if nav_info else 0
        nav_depth = nav_info.navigation_depth if nav_info else 0
        is_sticky = nav_info.is_sticky if nav_info else False

        if primary_count > 0:
            nav_score += 15
            nav_strengths.append(f"{primary_count} primary nav links")
        if nav_depth > 0:
            nav_score += min(nav_depth * 3, 8)
            nav_strengths.append("Multi-level navigation hierarchy")
        if footer_count > 0:
            nav_score += 10
            nav_strengths.append("Footer navigation present")
        if is_sticky:
            nav_score += 10
            nav_strengths.append("Sticky navigation enabled")
        if profile.navigation:
            nav_score += 5
        if not is_sticky:
            nav_weaknesses.append("No sticky navigation")
            nav_recs.append("Add sticky header for persistent navigation")
        if nav_depth <= 1 and primary_count > 3:
            nav_weaknesses.append("Flat navigation structure")
            nav_recs.append("Organize navigation into dropdown categories")
        if primary_count == 0:
            nav_weaknesses.append("No primary navigation detected")
            nav_recs.append("Add a visible primary navigation menu")
            nav_score = max(nav_score, 15)
        if footer_count == 0:
            nav_weaknesses.append("No footer navigation links")
            nav_recs.append("Add navigation links in footer")
        if nav_score > 100:
            nav_score = 100

        # --- Visual Consistency ---
        vis_strengths: list = []
        vis_weaknesses: list = []
        vis_recs: list = []
        vis_score = 40

        if consistency:
            if consistency.overall_consistency_score is not None:
                vis_score += int(consistency.overall_consistency_score * 0.4)
            if consistency.color_consistency is not None:
                vis_score += int(consistency.color_consistency * 5)
                vis_strengths.append("Consistent color usage")
            if consistency.typography_consistency is not None and consistency.typography_consistency > 5:
                vis_strengths.append("Consistent typography")
            if consistency.button_consistency is not None and consistency.button_consistency > 5:
                vis_strengths.append("Consistent button styling")
            if consistency.border_radius_consistency is not None and consistency.border_radius_consistency > 5:
                vis_strengths.append("Consistent border radius")
            if consistency.shadow_consistency is not None and consistency.shadow_consistency > 5:
                vis_strengths.append("Consistent shadows")
        has_brand = brand.tagline or brand.logo_info or brand.brand_voice
        if has_brand:
            vis_score += 10
            vis_strengths.append("Brand identity present")
        if brand.design_language:
            vis_score += 8
            vis_strengths.append("Design language classified")
        if brand.component_styles:
            vis_score += 5
        if profile.colors and (profile.colors.primary or profile.colors.secondary):
            vis_score += 5
            vis_strengths.append("Color palette extracted")
        if profile.typography and profile.typography.heading_font:
            vis_score += 5
            vis_strengths.append("Typography defined")
        if not profile.colors or not profile.colors.primary:
            vis_weaknesses.append("No primary brand color detected")
            vis_recs.append("Define a consistent primary brand color")
        if not profile.typography or not profile.typography.heading_font:
            vis_weaknesses.append("No heading font detected")
            vis_recs.append("Define a cohesive typography system")
        if not has_brand:
            vis_weaknesses.append("Missing brand identity elements")
            vis_recs.append("Add logo, tagline, or brand voice content")
        if vis_score > 100:
            vis_score = 100

        # --- Contact Completeness ---
        contact_strengths: list = []
        contact_weaknesses: list = []
        contact_recs: list = []
        contact_score = 20

        c = profile.contact
        if c.emails:
            contact_score += 15
            contact_strengths.append(f"Email address found ({len(c.emails)})")
        if c.phones:
            contact_score += 15
            contact_strengths.append(f"Phone number found ({len(c.phones)})")
        if c.address:
            contact_score += 15
            contact_strengths.append("Physical address present")
        if c.contact_form_present:
            contact_score += 15
            contact_strengths.append("Contact form available")
        if profile.company and profile.company.description:
            contact_score += 5
        if not c.emails:
            contact_weaknesses.append("No email address found")
            contact_recs.append("Add a visible email address or contact form")
        if not c.phones:
            contact_weaknesses.append("No phone number found")
            contact_recs.append("Add a phone number for direct contact")
        if not c.address:
            contact_weaknesses.append("No physical address found")
            contact_recs.append("Add business address for credibility")
        if not c.contact_form_present:
            contact_weaknesses.append("No contact form detected")
            contact_recs.append("Add a contact form for lead generation")
        if contact_score > 100:
            contact_score = 100

        # --- Trust Level ---
        trust_strengths: list = []
        trust_weaknesses: list = []
        trust_recs: list = []
        trust_score = 25

        company = profile.company
        trust_list = profile.trust_signals

        if trust_list:
            trust_score += min(len(trust_list) * 8, 20)
            trust_types = set(t.type for t in trust_list if t.type)
            if trust_types:
                trust_strengths.append(f"Trust signals: {', '.join(sorted(trust_types)[:4])}")
        if company and company.years_in_business:
            trust_score += 10
            trust_strengths.append(f"{company.years_in_business} years in business")
        if company and company.company_size:
            trust_score += 5
        if company and company.mission:
            trust_score += 5
        if profile.testimonials:
            trust_score += min(len(profile.testimonials) * 4, 12)
            trust_strengths.append(f"{len(profile.testimonials)} testimonials/reviews")
        if company and (company.usp or company.core_values):
            trust_score += 5
            trust_strengths.append("Company values or USP displayed")
        if c and (c.emails or c.phones or c.address):
            trust_score += 5
        if not trust_list:
            trust_weaknesses.append("No trust signals detected")
            trust_recs.append("Display certifications, awards, or partner badges")
        if not profile.testimonials:
            trust_weaknesses.append("No testimonials or reviews")
            trust_recs.append("Add client testimonials or case studies")
        if not company or not company.years_in_business:
            trust_weaknesses.append("Business tenure not visible")
            trust_recs.append("Show years in business or experience")
        if trust_score > 100:
            trust_score = 100

        # --- Social Presence ---
        social_strengths: list = []
        social_weaknesses: list = []
        social_recs: list = []
        social_score = 20

        social_links = profile.social_links
        if social_links:
            platforms = set()
            for sl in social_links:
                if sl.platform:
                    platforms.add(sl.platform.capitalize())
                elif sl.url:
                    for p in ("facebook", "linkedin", "twitter", "instagram", "youtube", "github"):
                        if p in sl.url.lower():
                            platforms.add(p.capitalize())
            if platforms:
                social_score += min(len(platforms) * 10, 35)
                social_strengths.append(f"Social platforms: {', '.join(sorted(platforms)[:5])}")
        footer_info = profile.website_layout.footer_info if profile.website_layout else None
        if footer_info and footer_info.social_links:
            social_score += 10
            if not social_links:
                social_strengths.append("Social links in footer")
        if not social_links:
            social_weaknesses.append("No social media links found")
            social_recs.append("Add links to LinkedIn, Twitter, Facebook profiles")
        if social_links and len(social_links) < 3:
            social_weaknesses.append("Only {len(social_links)} social platform(s) linked")
            social_recs.append("Add at least LinkedIn and Twitter profiles")
        if social_score > 100:
            social_score = 100

        # --- SEO Readiness ---
        seo_strengths: list = []
        seo_weaknesses: list = []
        seo_recs: list = []
        seo_score = 30

        seo = profile.seo or SEOInfo()
        if seo.page_title and not seo.missing_title:
            seo_score += 15
            seo_strengths.append("Page title set")
        else:
            seo_weaknesses.append("Missing page title")
            seo_recs.append("Add descriptive page title (50-60 chars)")
        if seo.meta_description and not seo.missing_meta_description:
            seo_score += 15
            seo_strengths.append("Meta description present")
        else:
            seo_weaknesses.append("Missing meta description")
            seo_recs.append("Add meta description (150-160 chars)")
        if not seo.missing_h1:
            seo_score += 10
            seo_strengths.append("H1 heading present")
        else:
            seo_weaknesses.append("No H1 heading found")
            seo_recs.append("Add one H1 heading per page")
        if seo.focus_keywords:
            seo_score += min(len(seo.focus_keywords) * 3, 10)
            seo_strengths.append(f"Keywords: {', '.join(seo.focus_keywords[:4])}")
        if seo.https_enabled:
            seo_score += 10
            seo_strengths.append("HTTPS enabled")
        else:
            seo_weaknesses.append("HTTPS not detected")
            seo_recs.append("Enable HTTPS/SSL certificate")
        if profile.raw_html_size_kb and profile.raw_html_size_kb < 500:
            seo_score += 5
            seo_strengths.append("Page size is optimal")
        elif profile.raw_html_size_kb and profile.raw_html_size_kb > 2000:
            seo_weaknesses.append("Large page size ({profile.raw_html_size_kb}KB)")
            seo_recs.append("Optimize page size under 500KB")
        if seo_score > 100:
            seo_score = 100

        # --- Accessibility Readiness ---
        a11y_strengths: list = []
        a11y_weaknesses: list = []
        a11y_recs: list = []
        a11y_score = 35

        images = profile.images
        if images:
            with_alt = sum(1 for img in images if img.alt)
            total = len(images)
            alt_pct = with_alt / total if total > 0 else 0
            if alt_pct > 0.8:
                a11y_score += 20
                a11y_strengths.append(f"High image alt text coverage ({with_alt}/{total})")
            elif alt_pct > 0.5:
                a11y_score += 10
                a11y_strengths.append(f"Moderate image alt text ({with_alt}/{total})")
            else:
                a11y_weaknesses.append(f"Low alt text coverage ({with_alt}/{total} images)")
                a11y_recs.append("Add descriptive alt text to all images")
        if seo and not seo.missing_h1:
            a11y_score += 10
            a11y_strengths.append("H1 heading present for screen readers")
        if profile.website_layout and profile.website_layout.sections:
            heading_count = sum(1 for s in profile.website_layout.sections if s.heading)
            if heading_count > 2:
                a11y_score += 10
                a11y_strengths.append("Multiple section headings provide structure")
            else:
                a11y_weaknesses.append("Few section headings detected")
                a11y_recs.append("Use heading hierarchy (h1-h6) for content structure")
        if profile.navigation_info and profile.navigation_info.primary_nav_items:
            a11y_score += 8
            a11y_strengths.append("Navigation structure present")
        nav_items_count = len(profile.navigation) if profile.navigation else 0
        if nav_items_count > 5:
            a11y_score += 5
        if not images:
            a11y_weaknesses.append("No images analyzed for alt text")
            a11y_recs.append("Ensure all images have meaningful alt text")
        if a11y_score > 100:
            a11y_score = 100

        # --- Conversion Readiness ---
        conv_strengths: list = []
        conv_weaknesses: list = []
        conv_recs: list = []
        conv_score = 25

        ctas = profile.call_to_actions
        cta_count = len(ctas) if ctas else 0
        if ctas and profile.hero_info and profile.hero_info.ctas:
            primary_ctas = [cta for cta in ctas if hasattr(cta, "text") and cta.text]
            cta_count = max(cta_count, len(primary_ctas))
        if cta_count > 0:
            conv_score += min(cta_count * 7, 20)
            conv_strengths.append(f"{cta_count} call-to-action buttons")
        if profile.hero_info and profile.hero_info.ctas:
            conv_score += 8
            conv_strengths.append("Primary CTA in hero section")
        if c.contact_form_present:
            conv_score += 12
            conv_strengths.append("Contact form for lead capture")
        if c.phones:
            conv_score += 8
            conv_strengths.append("Click-to-call available")
        if c.emails:
            conv_score += 5
        if profile.testimonials:
            conv_score += 8
            conv_strengths.append("Social proof via testimonials")
        pricing_sections = [s for s in (profile.website_layout.sections if profile.website_layout else []) if s.section_type == "Pricing"]
        if pricing_sections:
            conv_score += 8
            conv_strengths.append("Pricing information visible")
        if not ctas:
            conv_weaknesses.append("No call-to-action buttons found")
            conv_recs.append("Add prominent CTAs: Get Started, Contact Us, Book Demo")
        if not c.contact_form_present and not c.phones and not c.emails:
            conv_weaknesses.append("No conversion channels detected")
            conv_recs.append("Add contact form, phone, or email for lead capture")
        if not profile.testimonials:
            conv_weaknesses.append("No social proof elements")
            conv_recs.append("Add testimonials or case studies near CTAs")
        if conv_score > 100:
            conv_score = 100

        # --- Mobile Readiness ---
        mob_strengths: list = []
        mob_weaknesses: list = []
        mob_recs: list = []
        mob_score = 45

        if profile.website_layout and profile.website_layout.sections:
            responsive_layouts = sum(1 for s in profile.website_layout.sections if s.layout_type in ("grid", "list"))
            if responsive_layouts > 2:
                mob_score += 10
                mob_strengths.append("Responsive layout patterns detected")
        if profile.navigation_info and profile.navigation_info.is_sticky:
            mob_score += 8
        if raw_html_size_kb := profile.raw_html_size_kb:
            if raw_html_size_kb < 300:
                mob_score += 10
                mob_strengths.append("Lightweight page (mobile-friendly)")
            elif raw_html_size_kb < 800:
                mob_score += 5
            else:
                mob_weaknesses.append(f"Large page size ({raw_html_size_kb}KB)")
                mob_recs.append("Reduce page size for faster mobile loading")
        if profile.navigation_info and profile.navigation_info.primary_nav_items:
            mob_score += 5
        if not profile.navigation_info or not profile.navigation_info.is_sticky:
            mob_weaknesses.append("No sticky navigation")
            mob_recs.append("Consider sticky nav for mobile usability")
        if mob_score > 100:
            mob_score = 100

        # --- Professionalism Score ---
        prof_strengths: list = []
        prof_weaknesses: list = []
        prof_recs: list = []
        prof_score = 40

        has_logo = bool(brand.logo_info and brand.logo_info.logo_url)
        if has_logo:
            prof_score += 10
            prof_strengths.append("Professional logo present")
        else:
            prof_weaknesses.append("No logo detected")
            prof_recs.append("Add a professional logo")
        has_hero = bool(profile.hero_info and (profile.hero_info.title or profile.hero_info.description))
        if has_hero:
            prof_score += 8
            prof_strengths.append("Hero section with messaging")
        else:
            prof_weaknesses.append("No hero section with clear messaging")
            prof_recs.append("Add hero section with value proposition")
        if profile.website_layout and profile.website_layout.sections:
            section_types = set(s.section_type for s in profile.website_layout.sections if s.section_type)
            if "About" in section_types:
                prof_score += 5
                prof_strengths.append("About section present")
            if "Services" in section_types or "Features" in section_types:
                prof_score += 5
                prof_strengths.append("Services/products section present")
            if len(section_types) >= 4:
                prof_score += 5
                prof_strengths.append(f"Well-structured with {len(section_types)} content sections")
        if profile.contact and (profile.contact.emails or profile.contact.phones):
            prof_score += 5
        if profile.seo and not profile.seo.missing_title and not profile.seo.missing_meta_description:
            prof_score += 5
        if profile.company and profile.company.description:
            prof_score += 5
        if profile.testimonials:
            prof_score += 5
        if trust_list:
            prof_score += 5
        overall_consistency = consistency.overall_consistency_score if consistency else None
        if overall_consistency is not None and overall_consistency > 7:
            prof_score += 5
        if profile.raw_html_size_kb and profile.raw_html_size_kb < 500:
            prof_score += 5
        if prof_score > 100:
            prof_score = 100

        return QualityMetrics(
            content_quality=self._make_metric(content_score, content_strengths, content_weaknesses, content_recs),
            navigation_quality=self._make_metric(nav_score, nav_strengths, nav_weaknesses, nav_recs),
            visual_consistency=self._make_metric(vis_score, vis_strengths, vis_weaknesses, vis_recs),
            contact_completeness=self._make_metric(contact_score, contact_strengths, contact_weaknesses, contact_recs),
            trust_level=self._make_metric(trust_score, trust_strengths, trust_weaknesses, trust_recs),
            social_presence=self._make_metric(social_score, social_strengths, social_weaknesses, social_recs),
            seo_readiness=self._make_metric(seo_score, seo_strengths, seo_weaknesses, seo_recs),
            accessibility_readiness=self._make_metric(a11y_score, a11y_strengths, a11y_weaknesses, a11y_recs),
            conversion_readiness=self._make_metric(conv_score, conv_strengths, conv_weaknesses, conv_recs),
            mobile_readiness=self._make_metric(mob_score, mob_strengths, mob_weaknesses, mob_recs),
            professionalism_score=self._make_metric(prof_score, prof_strengths, prof_weaknesses, prof_recs),
        )

    def generate_website_blueprint(self, profile: "WebsiteProfile") -> "WebsiteBlueprint":
        brand = profile.brand or BrandIdentity()
        nav_info = profile.navigation_info
        layout = profile.website_layout
        sections = layout.sections if layout else []

        detected_types = [s.section_type for s in sections if s.section_type]
        all_standard = ["Navbar", "Hero", "Services", "About", "Why Choose Us", "Portfolio", "Testimonials", "FAQ", "Pricing", "Contact", "Footer"]
        missing = [s for s in all_standard if s not in detected_types and s != "Navbar" and s != "Hero" and s != "Footer"]

        # --- Navbar blueprint ---
        primary_count = len(nav_info.primary_nav_items) if nav_info else 0
        nav_depth = nav_info.navigation_depth if nav_info else 0
        is_sticky = nav_info.is_sticky if nav_info else False
        navbar_info = {
            "present": primary_count > 0,
            "primary_links": primary_count,
            "depth": nav_depth,
            "is_sticky": is_sticky,
            "description": f"{'Sticky ' if is_sticky else ''}Navigation with {primary_count} primary links, {nav_depth} level(s) deep",
            "recommended_items": ["Home", "Services", "About", "Portfolio", "Contact"],
            "sticky_recommended": not is_sticky,
            "cta_button_recommended": True,
            "mobile_menu_needed": True,
        }

        # --- Hero blueprint ---
        hi = profile.hero_info
        hero = {
            "present": bool(hi and (hi.title or hi.description)),
            "has_cta": bool(hi and hi.ctas),
            "title": hi.title if hi else None,
            "layout": hi.layout if hi else None,
            "needs_subtitle": bool(hi and not hi.subtitle),
            "needs_description": bool(hi and not hi.description),
            "needs_primary_cta": bool(hi and not hi.ctas),
            "needs_image": hi and hi.layout == "text-only" if hi else True,
            "recommended_content": "Headline, Subtitle, Description, Primary CTA, Background image/illustration",
        }

        # --- Services blueprint ---
        svc = profile.services
        services = {
            "present": len(svc) > 0,
            "count": len(svc),
            "has_icons": any(s.icon for s in svc) if svc else False,
            "has_descriptions": any(len(s.description or "") > 50 for s in svc) if svc else False,
            "needs_icons": not any(s.icon for s in svc) if svc else True,
            "needs_descriptions": not any(len(s.description or "") > 50 for s in svc) if svc else True,
            "layout_recommended": "3-column card grid",
            "recommended_max": 6,
        }

        # --- About blueprint ---
        company = profile.company
        about = {
            "present": bool(company and company.description),
            "has_mission": bool(company and company.mission),
            "has_vision": bool(company and company.vision),
            "has_values": bool(company and company.core_values),
            "has_usp": bool(company and company.usp),
            "needs_mission": not (company and company.mission),
            "needs_vision": not (company and company.vision),
            "needs_values": not (company and company.core_values),
            "needs_usp": not (company and company.usp),
            "recommended_layout": "Two-column: image left, text right",
        }

        # --- Why Choose Us blueprint ---
        has_features = "Features" in detected_types
        usp_text = company.usp if company else None
        why_choose = {
            "present": has_features or bool(usp_text),
            "source": "Features section" if has_features else ("USP text" if usp_text else None),
            "needs_section": not has_features and not usp_text,
            "recommended_content": "Key differentiators, stats, 3-6 bullet points with icons",
            "layout_recommended": "Grid with icon cards + statistics bar",
        }

        # --- Portfolio blueprint ---
        has_portfolio = "Portfolio" in detected_types or "Gallery" in detected_types
        portfolio = {
            "present": has_portfolio,
            "needs_section": not has_portfolio,
            "recommended_content": "Case studies or project showcases with images",
            "layout_recommended": "Filterable grid with lightbox",
        }

        # --- Testimonials blueprint ---
        tst = profile.testimonials
        testimonials = {
            "present": len(tst) > 0,
            "count": len(tst),
            "has_images": any(t.avatar_url for t in tst) if tst else False,
            "has_star_ratings": any((t.star_count or 0) > 0 for t in tst) if tst else False,
            "has_verified_badges": any(t.verified_badge for t in tst) if tst else False,
            "needs_more": len(tst) < 3,
            "layout_recommended": "Carousel or 3-column grid",
            "recommended_minimum": 3,
        }

        # --- FAQ blueprint ---
        faq_list = profile.faqs
        faq = {
            "present": len(faq_list) > 0,
            "count": len(faq_list),
            "has_categories": any(f.category for f in faq_list) if faq_list else False,
            "accordion_detected": any(not f.collapsed_by_default for f in faq_list) if faq_list else False,
            "needs_categories": not any(f.category for f in faq_list) if faq_list else True,
            "recommended_style": "Accordion with categories",
            "recommended_minimum": 5,
        }

        # --- Pricing blueprint ---
        has_pricing = "Pricing" in detected_types
        pricing = {
            "present": has_pricing or len(profile.products) > 0,
            "source": "Pricing section" if has_pricing else ("Products list" if profile.products else None),
            "needs_section": not has_pricing,
            "recommended_layout": "3-column tiered pricing cards",
            "recommended_tiers": ["Basic", "Professional", "Enterprise"],
        }

        # --- Contact blueprint ---
        c = profile.contact
        contact = {
            "present": bool(c.emails or c.phones or c.address or c.contact_form_present),
            "has_form": c.contact_form_present,
            "has_email": len(c.emails) > 0,
            "has_phone": len(c.phones) > 0,
            "has_address": bool(c.address),
            "has_map": bool(c.map_coordinates),
            "needs_form": not c.contact_form_present,
            "recommended_fields": ["Name", "Email", "Phone", "Message"],
            "layout_recommended": "Two-column: form left, info right",
        }

        # --- Footer blueprint ---
        fi = layout.footer_info if layout else None
        footer = {
            "present": bool(fi),
            "has_logo": bool(fi and fi.footer_logo),
            "has_description": bool(fi and fi.footer_description),
            "has_contact": bool(fi and fi.contact_info),
            "has_social": bool(fi and fi.social_links),
            "has_newsletter": bool(fi and fi.newsletter_signup),
            "has_copyright": bool(fi and fi.copyright_text),
            "needs_social_icons": not (fi and fi.social_links),
            "needs_newsletter": not (fi and fi.newsletter_signup),
            "recommended_columns": ["Logo + Description", "Quick Links", "Services", "Contact", "Social"],
        }

        # --- Color Palette blueprint ---
        cp = profile.colors
        color_palette = {
            "primary": cp.primary if cp else None,
            "secondary": cp.secondary if cp else None,
            "accent": cp.accent if cp else None,
            "background": cp.background if cp else None,
            "text": cp.text if cp else None,
            "has_complete_palette": bool(cp and cp.primary and cp.secondary and cp.text),
            "needs_primary": not (cp and cp.primary),
            "needs_secondary": not (cp and cp.secondary),
            "needs_accent": not (cp and cp.accent),
            "needs_contrast_fix": bool(cp and cp.primary and cp.text and cp.primary == cp.text) if cp else False,
            "recommended_style": "Modern SaaS palette with 60-30-10 rule",
        }

        # --- Typography blueprint ---
        tp = profile.typography
        typography = {
            "heading_font": tp.heading_font if tp else None,
            "body_font": tp.body_font if tp else None,
            "has_heading": bool(tp and tp.heading_font),
            "has_body": bool(tp and tp.body_font),
            "needs_heading": not (tp and tp.heading_font),
            "needs_body": not (tp and tp.body_font),
            "pairing_suggestion": "Inter + Inter" if (tp and tp.heading_font and tp.body_font and tp.heading_font == tp.body_font) else None,
            "recommended_pairings": ["Inter + Inter", "Poppins + Inter", "Playfair Display + Inter"],
        }

        # --- Spacing blueprint ---
        consistency = brand.consistency_report
        spacing = {
            "overall_consistency": round(consistency.overall_consistency_score, 2) if (consistency and consistency.overall_consistency_score is not None) else None,
            "spacing_consistency": round(consistency.spacing_consistency, 2) if (consistency and consistency.spacing_consistency is not None) else None,
            "border_radius_consistency": round(consistency.border_radius_consistency, 2) if (consistency and consistency.border_radius_consistency is not None) else None,
            "needs_unified_spacing": bool(consistency and consistency.spacing_consistency is not None and consistency.spacing_consistency < 6) if consistency else True,
            "recommended_system": "4px base unit, 8px grid, section padding: 80-120px",
        }

        # --- Sections Order ---
        sections_order = []
        seen_types = set()
        standard_types = {"About", "Services", "Features", "Pricing", "Portfolio", "Gallery", "Testimonials", "Team", "FAQ", "Contact", "Newsletter", "Statistics", "Partners"}
        for s in sections:
            if s.section_type in standard_types and s.section_type not in seen_types:
                seen_types.add(s.section_type)
                sections_order.append(s.section_type)

        # --- Recommended Sections ---
        rec_map = {
            "Services": "Core offering showcase",
            "About": "Company story and mission",
            "Why Choose Us": "Differentiators and trust builders",
            "Portfolio": "Visual proof of work",
            "Testimonials": "Social proof and credibility",
            "FAQ": "Address common objections",
            "Pricing": "Transparent pricing information",
            "Contact": "Lead capture and inquiries",
        }
        recommended_sections = []
        for ms in missing:
            if ms in rec_map:
                recommended_sections.append({"section": ms, "reason": rec_map[ms]})

        # --- Image Requirements ---
        image_requirements = []
        if "Hero" not in missing and hi and hi.layout != "text-only":
            image_requirements.append({"section": "Hero", "type": "Background / hero illustration", "count": 1, "specification": "1920x1080 or vector illustration"})
        if "Services" in missing or (svc and not any(s.image for s in svc)):
            image_requirements.append({"section": "Services", "type": "Service icon or illustration per card", "count": min(len(svc) or 6, 6), "specification": "64x64 icons or 400x300 thumbnails"})
        if "About" not in missing or (company and company.description):
            image_requirements.append({"section": "About", "type": "Team / office photo", "count": 1, "specification": "600x800 or company-wide shot"})
        if "Portfolio" not in missing:
            image_requirements.append({"section": "Portfolio", "type": "Project screenshots / mockups", "count": "4-8", "specification": "1200x800 or 16:9"})
        if "Testimonials" not in missing or tst:
            image_requirements.append({"section": "Testimonials", "type": "Client headshots", "count": min(len(tst) or 3, 6), "specification": "80x80 circular"})
        if "Team" in detected_types and profile.team:
            image_requirements.append({"section": "Team", "type": "Team member photos", "count": len(profile.team), "specification": "400x400 headshots"})
        if "Pricing" not in missing:
            image_requirements.append({"section": "Pricing", "type": "Plan illustrations / icons", "count": 3, "specification": "48x48 icons per tier"})

        # --- Brand Style ---
        dl = brand.design_language
        bp = brand.brand_personality
        brand_style = {
            "design_language": dl.design_language if dl else None,
            "design_era": dl.era if dl else None,
            "aesthetic": dl.aesthetic if dl else None,
            "personality_traits": bp.traits if bp else None,
            "personality_archetype": bp.archetype if bp else None,
            "voice": brand.brand_voice,
            "tagline": brand.tagline,
            "audience": brand.target_audience or (company.target_audience if company else None),
        }

        # --- Animations Needed ---
        animations_needed = []
        if "Hero" not in missing:
            animations_needed.append({"section": "Hero", "element": "Headline + CTA", "animation": "Fade-in / slide-up on load", "priority": "High"})
        if "Services" not in missing:
            animations_needed.append({"section": "Services", "element": "Service cards", "animation": "Staggered fade-in on scroll", "priority": "Medium"})
        if "About" not in missing or (company and company.description):
            animations_needed.append({"section": "About", "element": "Image + stats", "animation": "Parallax or reveal on scroll", "priority": "Medium"})
        if "Why Choose Us" not in missing:
            animations_needed.append({"section": "Why Choose Us", "element": "Stat counters", "animation": "Count-up animation", "priority": "Medium"})
        if "Portfolio" not in missing:
            animations_needed.append({"section": "Portfolio", "element": "Project cards", "animation": "Hover scale + filter transition", "priority": "Low"})
        if "Testimonials" not in missing:
            animations_needed.append({"section": "Testimonials", "element": "Carousel", "animation": "Auto-slide / fade transition", "priority": "Low"})
        if "Pricing" not in missing:
            animations_needed.append({"section": "Pricing", "element": "Plan cards", "animation": "Hover lift + popular badge pop", "priority": "Low"})
        if "Contact" not in missing:
            animations_needed.append({"section": "Contact", "element": "Form", "animation": "Focus glow / success shake", "priority": "Low"})
        animations_needed.append({"section": "Global", "element": "Navigation", "animation": "Sticky header slide + mobile menu slide", "priority": "High"})
        animations_needed.append({"section": "Global", "element": "Scroll reveal", "animation": "Intersection observer fade-up for sections", "priority": "Medium"})

        # --- Components Required ---
        components_required = []
        if "Hero" not in missing:
            components_required.append({"section": "Hero", "components": ["HeroSection", "CtaButton", "BackgroundImage"]})
        if "Services" not in missing or svc:
            components_required.append({"section": "Services", "components": ["ServiceCard", "IconBox", "SectionGrid"]})
        if "About" not in missing or (company and company.description):
            components_required.append({"section": "About", "components": ["TwoColumnLayout", "StatsBar", "MissionVisionCard"]})
        if "Why Choose Us" not in missing or has_features:
            components_required.append({"section": "Why Choose Us", "components": ["FeatureCard", "IconList", "StatsCounter"]})
        if "Portfolio" not in missing or has_portfolio:
            components_required.append({"section": "Portfolio", "components": ["PortfolioCard", "FilterTabs", "Lightbox"]})
        elif not has_portfolio:
            components_required.append({"section": "Portfolio", "components": ["PortfolioCard", "FilterTabs", "Lightbox"], "status": "Missing - recommended"})
        if "Testimonials" not in missing or tst:
            components_required.append({"section": "Testimonials", "components": ["TestimonialCard", "Carousel", "StarRating"]})
        if "FAQ" not in missing or faq_list:
            components_required.append({"section": "FAQ", "components": ["Accordion", "SearchFilter"]})
        if "Pricing" not in missing or has_pricing:
            components_required.append({"section": "Pricing", "components": ["PricingCard", "ToggleSwitch"]})
        if "Contact" not in missing:
            components_required.append({"section": "Contact", "components": ["ContactForm", "MapEmbed", "ContactInfoCard"]})
        components_required.append({"section": "Global", "components": ["Navbar", "Footer", "MobileMenu", "ScrollToTop", "SectionWrapper"]})

        return WebsiteBlueprint(
            navbar_info=navbar_info,
            hero=hero,
            services=services,
            about=about,
            why_choose_us=why_choose,
            portfolio=portfolio,
            testimonials=testimonials,
            faq=faq,
            pricing=pricing,
            contact=contact,
            footer=footer,
            color_palette=color_palette,
            typography=typography,
            spacing=spacing,
            sections_order=sections_order,
            missing_sections=missing,
            recommended_sections=recommended_sections,
            image_requirements=image_requirements,
            brand_style=brand_style,
            animations_needed=animations_needed,
            components_required=components_required,
        )

    async def extract_faqs(self, page, html: str) -> List["FAQ"]:
        soup = BeautifulSoup(html, "html.parser")

        section_containers: List[Any] = []
        seen_ids: set = set()

        for sec in soup.find_all(["section", "div"]):
            parent = sec.parent
            if parent and parent.name not in ("body", "main", "div", "section"):
                continue
            cls_str = " ".join(sec.get("class", [])).lower()
            id_str = (sec.get("id") or "").lower()
            combined = cls_str + " " + id_str
            sec_text = sec.get_text(strip=True).lower()[:200]

            has_signal = any(k in combined for k in ("faq", "frequently-asked", "frequently_asked", "accordion", "help-center", "help_center", "knowledge-base", "knowledge_base", "support-questions"))
            if not has_signal:
                has_signal = any(kw in sec_text for kw in SECTION_KEYWORDS["faq"])
            if has_signal:
                sid = id(sec)
                if sid not in seen_ids:
                    seen_ids.add(sid)
                    section_containers.append(sec)

        if not section_containers:
            details = soup.find_all("details")
            if details:
                wrapper = soup.new_tag("div")
                for d in details:
                    wrapper.append(d)
                section_containers.append(wrapper)

        faqs: List["FAQ"] = []
        seen_questions: set = set()
        order = 0

        for sec in section_containers:
            sec_title = None
            sec_h = sec.find(["h2", "h3"])
            if sec_h:
                sec_title = sec_h.get_text(strip=True)[:200]

            cls_sec = " ".join(sec.get("class", [])).lower()
            sec_selector = f"{sec.name}.{'.'.join(sec.get('class', []))}" if sec.get("class") else sec.name

            details_items = sec.find_all("details")
            for det in details_items:
                q_el = det.find(["summary", "span", "div"], class_=lambda c: c and "question" in " ".join(c).lower() if c else True)
                if not q_el:
                    q_el = det.find("summary")
                a_text = None
                a_div = det.find(["div", "p"], class_=lambda c: c and ("answer" in " ".join(c).lower() or "content" in " ".join(c).lower()) if c else True)
                if not a_div:
                    a_div = det.find(["div", "p"])
                if a_div:
                    a_text = a_div.get_text(strip=True)
                q_text = q_el.get_text(strip=True) if q_el else ""

                if q_text and a_text:
                    norm = q_text.lower().strip()
                    if norm not in seen_questions:
                        seen_questions.add(norm)
                        order += 1
                        faqs.append(FAQ(
                            question=q_text[:500],
                            answer=a_text[:2000],
                            section_title=sec_title,
                            section_selector=sec_selector,
                            order=order,
                            collapsed_by_default=not det.has_attr("open"),
                            expanded_by_default=det.has_attr("open"),
                        ))

            qa_cards = sec.find_all(["div", "li", "article"], class_=lambda c: c and any(k in " ".join(c).lower() for k in ("faq", "question", "accordion", "qa", "item", "panel")), recursive=True)
            for card in qa_cards:
                if card.find_parent("details"):
                    continue
                card_cls = " ".join(card.get("class", [])).lower()
                if any(k in card_cls for k in ("nav", "menu", "footer", "cookie", "banner", "ad-")):
                    continue

                if card.find(["details", "summary"]):
                    continue

                q_el = card.find(class_=lambda c: c and any(k in " ".join(c).lower() for k in ("question", "q", "title", "faq-title")))
                if not q_el:
                    q_el = card.find(["h3", "h4", "h5", "strong"])
                a_el = card.find(class_=lambda c: c and any(k in " ".join(c).lower() for k in ("answer", "a", "content", "faq-answer", "faq-content")))
                if not a_el:
                    a_el = card.find(["p", "div"])

                if q_el and a_el and q_el is not a_el:
                    q_text = q_el.get_text(strip=True)
                    a_text = a_el.get_text(strip=True)
                    if not q_text.endswith("?"):
                        continue
                else:
                    texts = card.find_all(["p", "span", "div"])
                    q_text = ""
                    a_text = ""
                    for i, t in enumerate(texts):
                        t_text = t.get_text(strip=True)
                        if t_text and t_text.endswith("?"):
                            q_text = t_text
                            if i + 1 < len(texts):
                                nxt = texts[i + 1].get_text(strip=True)
                                if nxt:
                                    a_text = nxt
                            break

                if q_text and a_text:
                    norm = q_text.lower().strip()
                    if norm not in seen_questions:
                        seen_questions.add(norm)
                        order += 1

                        category = None
                        cat_el = card.find_parent(class_=lambda c: c and "category" in " ".join(c).lower())
                        if not cat_el:
                            cat_el = card.find_previous_sibling(class_=lambda c: c and "category" in " ".join(c).lower())
                        if cat_el:
                            category = cat_el.get_text(strip=True)[:100]

                        collapsed = True
                        expanded = False
                        btn = card.find(["button", "div"], class_=lambda c: c and any(k in " ".join(c).lower() for k in ("accordion", "toggle", "trigger")))
                        if btn:
                            aria_expanded = btn.get("aria-expanded", "")
                            collapsed = aria_expanded.lower() != "true"
                            expanded = aria_expanded.lower() == "true"

                        faqs.append(FAQ(
                            question=q_text[:500],
                            answer=a_text[:2000],
                            category=category,
                            section_title=sec_title,
                            section_selector=sec_selector,
                            order=order,
                            collapsed_by_default=collapsed,
                            expanded_by_default=expanded,
                        ))

                if len(faqs) >= 100:
                    break
            if len(faqs) >= 100:
                break

        if not faqs:
            for li in soup.find_all("li"):
                texts = li.find_all(["p", "span", "div"])
                q_text = ""
                a_text = ""
                for i, t in enumerate(texts):
                    t_text = t.get_text(strip=True)
                    if t_text and t_text.endswith("?"):
                        q_text = t_text
                        if i + 1 < len(texts):
                            a_text = texts[i + 1].get_text(strip=True)
                        break
                if q_text and a_text:
                    norm = q_text.lower().strip()
                    if norm not in seen_questions:
                        seen_questions.add(norm)
                        order += 1
                        faqs.append(FAQ(
                            question=q_text[:500],
                            answer=a_text[:2000],
                            order=order,
                        ))
                if len(faqs) >= 50:
                    break

        return faqs[:100]

    def _extract_blog_links(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        section = self._find_section(soup, SECTION_KEYWORDS["blog"])
        if not section:
            return []

        links: List[Dict[str, Any]] = []
        for a in section.find_all("a", href=True):
            href = str(a["href"])
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            title = a.get("title") or a.get_text(strip=True) or ""
            if not title:
                continue
            img = a.find_previous("img") or a.find("img")
            links.append({
                "title": title[:255],
                "url": href,
                "excerpt": None,
                "image": str(img["src"]) if img and img.get("src") else None,
            })

        return links[:50]

    def _extract_social_links(self, soup: BeautifulSoup, base_url: str) -> List[SocialLink]:
        found: Dict[str, str] = {}

        for a in soup.find_all("a", href=True):
            href = str(a["href"]).strip()
            if not href.startswith(("http://", "https://")):
                continue
            try:
                domain = urlparse(href).netloc.lower().lstrip("www.")
            except Exception:
                continue
            for social_domain, platform in SOCIAL_DOMAINS.items():
                if social_domain in domain and platform not in found:
                    found[platform] = href

        return [SocialLink(platform=p, url=u) for p, u in found.items()][:20]

    def _extract_cta_buttons(self, soup: BeautifulSoup, base_url: str) -> List[CallToAction]:
        buttons = self._extract_ctas_from_element(soup.body) if soup.body else []
        return buttons[:20]

    def _extract_ctas_from_element(self, parent) -> List[CallToAction]:
        results: List[CallToAction] = []
        seen_texts = set()

        for el in parent.find_all(["a", "button"]):
            if not el.get_text(strip=True):
                continue
            text = el.get_text(strip=True)
            if len(text) > 80:
                continue

            lower = text.lower()
            if not any(kw in lower for kw in CTA_KEYWORDS):
                continue
            if lower in seen_texts:
                continue
            seen_texts.add(lower)

            href = el.get("href") or ""
            if href and not href.startswith(("http://", "https://", "#", "javascript:", "tel:", "mailto:")):
                href = f"https://example.com{href}"

            btn_type = ""
            if el.name == "button":
                btn_type = "button"
            elif el.name == "a":
                btn_type = "link"

            color = ""
            style = el.get("style", "")
            bg_match = re.search(r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]+)", style)
            if bg_match:
                color = bg_match.group(1)

            for cls in el.get("class", []):
                cls_lower = cls.lower()
                for kw in CTA_KEYWORDS:
                    if kw.replace(" ", "") in cls_lower.replace(" ", ""):
                        btn_type = kw
                        break

            results.append(CallToAction(
                text=text[:80],
                url=href or None,
                type=btn_type or None,
                color=color or None,
            ))

        return results

    def _extract_statistics(self, soup: BeautifulSoup) -> Dict[str, Any]:
        stats: Dict[str, Any] = {}

        h1_count = len(soup.find_all("h1"))
        h2_count = len(soup.find_all("h2"))
        h3_count = len(soup.find_all("h3"))
        p_count = len(soup.find_all("p"))
        img_count = len(soup.find_all("img"))
        form_count = len(soup.find_all("form"))
        a_count = len(soup.find_all("a", href=True))
        button_count = len(soup.find_all("button"))

        body = soup.body
        word_count = 0
        if body:
            word_count = len(body.get_text(separator=" ", strip=True).split())

        sections_count = 0
        for tag in soup.find_all(["section", "div"]):
            cls = " ".join(tag.get("class", []))
            if "section" in cls.lower() or tag.name == "section":
                sections_count += 1

        stats = {
            "sections_count": sections_count,
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "paragraphs_count": p_count,
            "images_count": img_count,
            "forms_count": form_count,
            "links_count": a_count,
            "buttons_count": button_count,
            "word_count": word_count,
        }

        return stats

    def _build_website_summary(self, soup: BeautifulSoup) -> Optional[str]:
        if not soup or not soup.body:
            return None
        texts = []
        for tag in soup.body.find_all(["p", "li", "span"], limit=20):
            t = tag.get_text(strip=True)
            if len(t) > 40 and t not in texts:
                texts.append(t)
        return " ".join(texts[:10])[:2000] if texts else None

    def _find_section(self, soup: BeautifulSoup, keywords: List[str]) -> Optional[Any]:
        for tag in soup.find_all(["section", "div", "article"]):
            cls = " ".join(tag.get("class", [])).lower()
            id_val = (tag.get("id") or "").lower()
            combined = cls + " " + id_val
            if any(kw in combined for kw in keywords):
                return tag
        for tag in soup.find_all(["section", "div", "article"]):
            text = tag.get_text(strip=True).lower()[:200]
            if any(kw in text for kw in keywords):
                return tag
        return None


website_intelligence_service = WebsiteIntelligenceService()