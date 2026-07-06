import json
import re
import unicodedata
from typing import Any, Dict, Optional
from urllib.parse import urlparse


class WebsiteIntelligenceHelpers:
    """
    Stateless utility helpers for website intelligence processing.
    No AI, no extraction logic — only pure utility functions.
    """

    @staticmethod
    def slugify(text: str, max_length: int = 80) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^\w\s-]", "", ascii_text).strip().lower()
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug[:max_length].rstrip("-")

    @staticmethod
    def is_valid_hex_color(value: str) -> bool:
        if not isinstance(value, str):
            return False
        return bool(re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", value.strip()))

    @staticmethod
    def is_valid_rgb_color(value: str) -> bool:
        if not isinstance(value, str):
            return False
        pattern = r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$"
        match = re.match(pattern, value.strip())
        if not match:
            return False
        return all(0 <= int(g) <= 255 for g in match.groups())

    @staticmethod
    def is_valid_color(value: str) -> bool:
        return WebsiteIntelligenceHelpers.is_valid_hex_color(value) or \
               WebsiteIntelligenceHelpers.is_valid_rgb_color(value) or \
               bool(re.match(r"^rgba\(", value.strip()))

    @staticmethod
    def is_valid_font_family(family: str) -> bool:
        if not isinstance(family, str) or not family.strip():
            return False
        return bool(re.match(r"^[\w\s\-']+$", family.strip()))

    @staticmethod
    def is_valid_url(url: str, require_scheme: bool = True) -> bool:
        if not isinstance(url, str) or not url.strip():
            return False
        if require_scheme and not url.startswith(("http://", "https://")):
            return False
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc)
        except Exception:
            return False

    @staticmethod
    def serialize_json(data: Any, indent: Optional[int] = None) -> str:
        return json.dumps(data, indent=indent, default=str)

    @staticmethod
    def deserialize_json(value: str) -> Dict[str, Any]:
        return json.loads(value)


website_intelligence_helpers = WebsiteIntelligenceHelpers()