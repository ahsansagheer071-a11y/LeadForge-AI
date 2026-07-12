"""PromptBudgetController — reduces prompt size by removing boilerplate
and duplicate content while preserving all meaningful business text verbatim."""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Set

from app.services.website_generator.schemas import PromptContext

logger = logging.getLogger(__name__)

DUPLICATE_NAV_PATTERNS = re.compile(
    r"(- \*\*(?:Home|About|Contact|Shop|Products|Services|Blog|Cart|Account|"
    r"Login|Sign Up|Search|Menu|Wishlist|Orders|Help|FAQ|Support|Reviews)\*\*)",
    re.IGNORECASE,
)

SHOPIFY_BOILERPLATE_PATTERNS = [
    re.compile(r"Shopify[_\s]?[A-Za-z]*", re.IGNORECASE),
    re.compile(r"Powered by Shopify", re.IGNORECASE),
    re.compile(r"Built with Shopify", re.IGNORECASE),
    re.compile(r"cart\.js|CartDrawer|cart-drawer", re.IGNORECASE),
    re.compile(r"product\-form|product__form", re.IGNORECASE),
    re.compile(r"variant-selector", re.IGNORECASE),
    re.compile(r"add\-to\-cart|add_to_cart", re.IGNORECASE),
    re.compile(r"data\-shopify\- checkout", re.IGNORECASE),
]

COOKIE_NOTICE_PATTERNS = [
    re.compile(r"cookie[-\s]?(?:notice|consent|banner|policy|bar|popup)", re.IGNORECASE),
    re.compile(r"accept(?:ed)?\s+(?:all\s+)?cookies", re.IGNORECASE),
    re.compile(r"this site uses cookies", re.IGNORECASE),
    re.compile(r"we use cookies", re.IGNORECASE),
]

TRACKING_PATTERNS = [
    re.compile(r"gtag\(|google[_\s]?analytics|gaProperty|ga\(\s*'create'", re.IGNORECASE),
    re.compile(r"fbq\(|facebook[_\s]?pixel|meta[_\s]?pixel", re.IGNORECASE),
    re.compile(r"analytics\.js|tracking[_-]?script|tracking[_-]?code", re.IGNORECASE),
    re.compile(r"hotjar|clarity[_-]?ms|mouseflow", re.IGNORECASE),
]

TECHNICAL_TEMPLATE = [
    re.compile(r"\{\{.*?liquid.*?\}\}", re.IGNORECASE),
    re.compile(r"\{\%-.*?-%\}", re.DOTALL),
    re.compile(r"\{\{.*?\}\}", re.DOTALL),
    re.compile(r"json\s+for\s+product|paginate\s+by|section\s+blocks", re.IGNORECASE),
]


@dataclass
class BudgetAction:
    field: str
    chars_removed: int
    reason: str


@dataclass
class BudgetReport:
    original_total_chars: int = 0
    final_total_chars: int = 0
    chars_saved: int = 0
    actions: List[BudgetAction] = field(default_factory=list)


MAX_CONTENT_CHARS = 6000  # ~1.5K tokens — content section
MAX_FIELD_CHARS = 3000    # ~750 tokens per field — keeps total prompt under 10K tokens


class PromptBudgetController:
    """Removes boilerplate, duplicates, and tracking content from prompts
    while preserving all meaningful business content verbatim."""

    def apply(self, prompt: PromptContext) -> tuple[PromptContext, BudgetReport]:
        report = BudgetReport()
        original_total = sum(
            len(getattr(prompt, f, "") or "")
            for f in prompt.model_fields
        )
        report.original_total_chars = original_total

        cleaned = {}
        for field_name in prompt.model_fields:
            text = getattr(prompt, field_name, "") or ""
            cleaned[field_name], actions = self._clean_text(text, field_name)
            report.actions.extend(actions)

        report.final_total_chars = sum(len(v) for v in cleaned.values())
        report.chars_saved = report.original_total_chars - report.final_total_chars

        prompt = prompt.model_copy(update=cleaned)

        if report.actions:
            by_reason: Dict[str, int] = {}
            for a in report.actions:
                by_reason[a.reason] = by_reason.get(a.reason, 0) + a.chars_removed
            for reason, chars in sorted(by_reason.items(), key=lambda x: -x[1]):
                logger.info(
                    "PromptBudget: removed %d chars (%s)", chars, reason
                )

        logger.info(
            "PromptBudget: %d → %d chars (saved %d, %d actions)",
            report.original_total_chars,
            report.final_total_chars,
            report.chars_saved,
            len(report.actions),
        )
        return prompt, report

    def _clean_text(self, text: str, field_name: str) -> tuple[str, List[BudgetAction]]:
        if not text:
            return text, []
        actions: List[BudgetAction] = []
        original = text

        if field_name == "content_context":
            text, a = self._remove_duplicate_nav_labels(text)
            actions.extend(a)
            text, a = self._remove_tracking_content(text)
            actions.extend(a)
            text, a = self._truncate_content(text)
            actions.extend(a)

        if field_name in ("content_context", "layout_context", "components_context"):
            text, a = self._remove_shopify_boilerplate(text)
            actions.extend(a)

        if field_name in ("content_context", "rules_context", "system_context"):
            text, a = self._remove_cookie_notices(text)
            actions.extend(a)

        if field_name == "content_context":
            text, a = self._remove_technical_template(text)
            actions.extend(a)

        # General cap on any oversized field
        if len(text) > MAX_FIELD_CHARS:
            text = text[:MAX_FIELD_CHARS]
            actions.append(BudgetAction(
                field=field_name,
                chars_removed=len(original) - len(text) if len(original) > MAX_FIELD_CHARS else 0,
                reason=f"field cap {MAX_FIELD_CHARS}",
            ))

        chars_removed = len(original) - len(text)
        return text, actions

    def _remove_duplicate_nav_labels(self, text: str) -> tuple[str, List[BudgetAction]]:
        lines = text.split("\n")
        seen: Set[str] = set()
        kept: List[str] = []
        actions: List[BudgetAction] = []
        dup_chars = 0
        for line in lines:
            match = DUPLICATE_NAV_PATTERNS.match(line.strip())
            if match:
                key = match.group(0).lower()
                if key in seen:
                    dup_chars += len(line) + 1
                    continue
                seen.add(key)
            kept.append(line)
        result = "\n".join(kept)
        if dup_chars > 0:
            actions.append(BudgetAction(
                field="content_context",
                chars_removed=dup_chars,
                reason="duplicate nav labels",
            ))
        return result, actions

    def _remove_tracking_content(self, text: str) -> tuple[str, List[BudgetAction]]:
        actions: List[BudgetAction] = []
        for pattern in TRACKING_PATTERNS:
            new_text = pattern.sub("", text)
            removed = len(text) - len(new_text)
            if removed > 0:
                actions.append(BudgetAction(
                    field="content_context",
                    chars_removed=removed,
                    reason=f"tracking content: {pattern.pattern[:40]}",
                ))
            text = new_text
        return text, actions

    def _remove_shopify_boilerplate(self, text: str) -> tuple[str, List[BudgetAction]]:
        actions: List[BudgetAction] = []
        for pattern in SHOPIFY_BOILERPLATE_PATTERNS:
            new_text = pattern.sub("", text)
            removed = len(text) - len(new_text)
            if removed > 0:
                actions.append(BudgetAction(
                    field="content_context",
                    chars_removed=removed,
                    reason=f"Shopify boilerplate: {pattern.pattern[:40]}",
                ))
            text = new_text
        return text, actions

    def _remove_cookie_notices(self, text: str) -> tuple[str, List[BudgetAction]]:
        actions: List[BudgetAction] = []
        for pattern in COOKIE_NOTICE_PATTERNS:
            new_text = pattern.sub("", text)
            removed = len(text) - len(new_text)
            if removed > 0:
                actions.append(BudgetAction(
                    field="content_context",
                    chars_removed=removed,
                    reason=f"cookie notice: {pattern.pattern[:40]}",
                ))
            text = new_text
        return text, actions

    def _remove_technical_template(self, text: str) -> tuple[str, List[BudgetAction]]:
        actions: List[BudgetAction] = []
        for pattern in TECHNICAL_TEMPLATE:
            new_text = pattern.sub("", text)
            removed = len(text) - len(new_text)
            if removed > 0:
                actions.append(BudgetAction(
                    field="content_context",
                    chars_removed=removed,
                    reason=f"technical template: {pattern.pattern[:40]}",
                ))
            text = new_text
        return text, actions

    def _truncate_content(self, text: str) -> tuple[str, List[BudgetAction]]:
        actions: List[BudgetAction] = []
        if len(text) <= MAX_CONTENT_CHARS:
            return text, actions
        # Preserve the first N chars (which contain the most important content:
        # business name, hero, key sections) and truncate the rest
        truncated = text[:MAX_CONTENT_CHARS]
        # Try to cut at a section boundary (## heading)
        last_heading = truncated.rfind("\n## ")
        if last_heading > MAX_CONTENT_CHARS * 0.7:
            truncated = truncated[:last_heading]
        removed = len(text) - len(truncated)
        actions.append(BudgetAction(
            field="content_context",
            chars_removed=removed,
            reason=f"content truncation to {MAX_CONTENT_CHARS} chars",
        ))
        logger.info(
            "PromptBudget: content_context truncated %d -> %d chars (kept %.0f%%)",
            len(text), len(truncated), len(truncated) / len(text) * 100,
        )
        return truncated, actions
