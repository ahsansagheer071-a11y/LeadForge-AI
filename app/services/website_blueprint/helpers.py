from typing import Any, Dict, List, Optional

from .constants import (
    COMPONENT_REQUIREMENTS,
    LAYOUT_RECOMMENDATIONS,
    SECTION_PRIORITIES,
    STANDARD_SECTIONS,
)
from .schemas import (
    BlueprintSection,
    WebsiteBlueprint,
)


def determine_section_priority(section_type: str) -> int:
    return SECTION_PRIORITIES.get(section_type, 10)


def get_default_layout(section_type: str) -> str:
    rec = LAYOUT_RECOMMENDATIONS.get(section_type, {})
    return rec.get("layout", "default")


def get_default_columns(section_type: str) -> int:
    rec = LAYOUT_RECOMMENDATIONS.get(section_type, {})
    return int(rec.get("columns", "1"))


def get_required_components(section_type: str) -> List[str]:
    return COMPONENT_REQUIREMENTS.get(section_type, [])


def find_missing_sections(existing_sections: List[str]) -> List[str]:
    existing_lower = {s.lower().replace(" ", "_") for s in existing_sections}
    return [s for s in STANDARD_SECTIONS if s not in existing_lower]


def build_section_priority_list(
    existing_sections: List[str],
    missing_sections: List[str],
) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    all_standard = STANDARD_SECTIONS[:]
    for section_type in all_standard:
        is_present = section_type in {s.lower().replace(" ", "_") for s in existing_sections}
        result.append({
            "section_type": section_type,
            "present": is_present,
            "priority": SECTION_PRIORITIES.get(section_type, 10),
        })
    result.sort(key=lambda x: x["priority"])
    return result


def estimate_complexity(blueprint: WebsiteBlueprint) -> str:
    section_count = len([s for s in [
        blueprint.hero, blueprint.about, blueprint.services,
        blueprint.products, blueprint.portfolio, blueprint.pricing,
        blueprint.testimonials, blueprint.faq, blueprint.team, blueprint.contact,
    ] if s is not None])
    if section_count <= 4:
        return "low"
    if section_count <= 7:
        return "medium"
    return "high"


def normalize_section_name(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def denormalize_section_name(name: str) -> str:
    return name.replace("_", " ").title()
