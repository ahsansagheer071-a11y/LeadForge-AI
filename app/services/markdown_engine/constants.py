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
    RULES = "RULES"
    OUTPUT = "OUTPUT"


MARKDOWN_PACKAGE_VERSION: str = "1.0.0"

GENERATOR_VERSION: str = "leadforge-markdown-engine-1.0.0"

CATEGORY_PRIORITIES: Dict[MarkdownCategory, int] = {
    MarkdownCategory.SYSTEM: 1,
    MarkdownCategory.RULES: 2,
    MarkdownCategory.DEVELOPER: 3,
    MarkdownCategory.BRANDING: 4,
    MarkdownCategory.LAYOUT: 5,
    MarkdownCategory.COMPONENTS: 6,
    MarkdownCategory.ANIMATIONS: 7,
    MarkdownCategory.SEO: 8,
    MarkdownCategory.PERFORMANCE: 9,
    MarkdownCategory.ACCESSIBILITY: 10,
    MarkdownCategory.ASSETS: 11,
    MarkdownCategory.OUTPUT: 12,
}

CATEGORY_DISPLAY_NAMES: Dict[MarkdownCategory, str] = {
    MarkdownCategory.SYSTEM: "System Rules",
    MarkdownCategory.DEVELOPER: "Developer Guide",
    MarkdownCategory.BRANDING: "Brand Identity",
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
    MarkdownCategory.LAYOUT: "03-layout.md",
    MarkdownCategory.COMPONENTS: "04-components.md",
    MarkdownCategory.ANIMATIONS: "05-animations.md",
    MarkdownCategory.SEO: "06-seo.md",
    MarkdownCategory.PERFORMANCE: "07-performance.md",
    MarkdownCategory.ACCESSIBILITY: "08-accessibility.md",
    MarkdownCategory.ASSETS: "09-assets.md",
    MarkdownCategory.RULES: "10-rules.md",
    MarkdownCategory.OUTPUT: "11-output.md",
}
