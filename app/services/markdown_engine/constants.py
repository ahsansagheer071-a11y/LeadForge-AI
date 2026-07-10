from enum import Enum
from typing import Dict, List


class MarkdownCategory(str, Enum):
    SYSTEM = "SYSTEM"
    DEVELOPER = "DEVELOPER"
    BRANDING = "BRANDING"
    LAYOUT = "LAYOUT"
    COMPONENTS = "COMPONENTS"
    ANIMATIONS = "ANIMATIONS"
    SEO = "SEO"
    PERFORMANCE = "PERFORMANCE"
    ACCESSIBILITY = "ACCESSIBILITY"
    ASSETS = "ASSETS"
    CONTENT = "CONTENT"
    RULES = "RULES"
    OUTPUT = "OUTPUT"


MARKDOWN_PACKAGE_VERSION: str = "1.0.0"

GENERATOR_VERSION: str = "leadforge-markdown-engine-1.0.0"

CATEGORY_PRIORITIES: Dict[MarkdownCategory, int] = {
    MarkdownCategory.SYSTEM: 1,
    MarkdownCategory.RULES: 2,
    MarkdownCategory.DEVELOPER: 3,
    MarkdownCategory.BRANDING: 4,
    MarkdownCategory.CONTENT: 5,
    MarkdownCategory.LAYOUT: 6,
    MarkdownCategory.COMPONENTS: 7,
    MarkdownCategory.ANIMATIONS: 8,
    MarkdownCategory.SEO: 9,
    MarkdownCategory.PERFORMANCE: 10,
    MarkdownCategory.ACCESSIBILITY: 11,
    MarkdownCategory.ASSETS: 12,
    MarkdownCategory.OUTPUT: 13,
}

CATEGORY_DISPLAY_NAMES: Dict[MarkdownCategory, str] = {
    MarkdownCategory.SYSTEM: "System Rules",
    MarkdownCategory.DEVELOPER: "Developer Guide",
    MarkdownCategory.BRANDING: "Brand Identity",
    MarkdownCategory.CONTENT: "Source Content",
    MarkdownCategory.LAYOUT: "Layout Structure",
    MarkdownCategory.COMPONENTS: "Component Library",
    MarkdownCategory.ANIMATIONS: "Animation System",
    MarkdownCategory.SEO: "SEO Configuration",
    MarkdownCategory.PERFORMANCE: "Performance Targets",
    MarkdownCategory.ACCESSIBILITY: "Accessibility Requirements",
    MarkdownCategory.ASSETS: "Asset Management",
    MarkdownCategory.RULES: "Coding Standards",
    MarkdownCategory.OUTPUT: "Output Requirements",
}

CATEGORY_FILENAMES: Dict[MarkdownCategory, str] = {
    MarkdownCategory.SYSTEM: "00-system.md",
    MarkdownCategory.DEVELOPER: "01-developer.md",
    MarkdownCategory.BRANDING: "02-branding.md",
    MarkdownCategory.CONTENT: "03-content.md",
    MarkdownCategory.LAYOUT: "04-layout.md",
    MarkdownCategory.COMPONENTS: "05-components.md",
    MarkdownCategory.ANIMATIONS: "06-animations.md",
    MarkdownCategory.SEO: "07-seo.md",
    MarkdownCategory.PERFORMANCE: "08-performance.md",
    MarkdownCategory.ACCESSIBILITY: "09-accessibility.md",
    MarkdownCategory.ASSETS: "10-assets.md",
    MarkdownCategory.RULES: "11-rules.md",
    MarkdownCategory.OUTPUT: "12-output.md",
}
