"""Static HTML Website Generator - produces a single self-contained HTML file.

This generator wraps the existing pipeline but injects a directive to the AI
to output ONLY a complete HTML document with embedded CSS and JS, suitable
for immediate preview in an iframe.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.services.website_intelligence.schemas import WebsiteProfile
from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.website_generator.context_builder import ContextBuilder
from app.services.website_generator.prompt_builder import PromptBuilder
from app.services.website_generator.providers.provider_factory import ProviderFactory
from app.services.website_generator.schemas import (
    GenerationContext,
    GenerationResult,
    PromptContext,
    WebsiteProject,
    GeneratedFile,
)
from app.services.ai.chain import run_chain

logger = logging.getLogger(__name__)

HTML_DIRECTIVE = """
You MUST output ONLY a single, complete, valid HTML document starting with 
<!DOCTYPE html> and ending with </html>. All CSS must be inside a <style> 
tag in the head, and all JavaScript must be inside a <script> tag before 
the closing </body> tag. Do NOT include any explanations, markdown fences, 
or extra text outside the HTML. The HTML should be a functional, styled 
website representing the given business.
"""

# Maximum characters per individual markdown section sent to the AI.
# Groq llama-3.3-70b has a ~128k token context; each char ≈ 0.35 tokens.
# We cap each section at ~6 000 tokens (≈ 17 000 chars) and the total
# user message at ~80 000 tokens (≈ 228 000 chars) to leave room for the
# completion.  Values are conservative to avoid 413/context-overflow errors.
_MAX_SECTION_CHARS = 17_000
_MAX_TOTAL_CHARS = 228_000


def _trim_section(text: str, label: str) -> str:
    """Hard-truncate a single context section and log a warning if it was cut."""
    if not text or len(text) <= _MAX_SECTION_CHARS:
        return text
    logger.warning(
        "Prompt section '%s' truncated: %d → %d chars",
        label, len(text), _MAX_SECTION_CHARS,
    )
    return text[:_MAX_SECTION_CHARS] + "\n\n[… truncated for token budget …]"


def _enforce_prompt_budget(prompt: PromptContext) -> PromptContext:
    """Trim every section field to stay within per-section and total char budgets."""
    fields = [
        ("system_context",       prompt.system_context),
        ("developer_context",    prompt.developer_context),
        ("branding_context",     prompt.branding_context),
        ("content_context",      prompt.content_context),
        ("layout_context",       prompt.layout_context),
        ("components_context",   prompt.components_context),
        ("animation_context",    prompt.animation_context),
        ("seo_context",          prompt.seo_context),
        ("performance_context",  prompt.performance_context),
        ("accessibility_context",prompt.accessibility_context),
        ("assets_context",       prompt.assets_context),
        ("rules_context",        prompt.rules_context),
        ("output_context",       prompt.output_context),
    ]
    trimmed = {name: _trim_section(val or "", name) for name, val in fields}

    # Total budget enforcement — drop least-important sections first
    drop_order = [
        "assets_context", "performance_context", "accessibility_context",
        "animation_context", "seo_context",
    ]
    total = sum(len(v) for v in trimmed.values())
    for field_name in drop_order:
        if total <= _MAX_TOTAL_CHARS:
            break
        original_len = len(trimmed.get(field_name, ""))
        if original_len > 0:
            trimmed[field_name] = ""
            total -= original_len
            logger.warning("Prompt budget: dropped section '%s' (%d chars)", field_name, original_len)

    updated = trimmed
    updated["generation_constraints"] = prompt.generation_constraints
    return prompt.model_copy(update=updated)

class StaticHTMLGenerator:
    def __init__(
        self,
        context_builder: Optional[ContextBuilder] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        provider_name: Optional[str] = None,
    ):
        self.context_builder = context_builder or ContextBuilder()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.provider_name = provider_name

    async def generate(
        self,
        blueprint: WebsiteProfile,
        package: MarkdownPackage,
    ) -> GenerationResult:
        start = time.monotonic()
        biz_name = getattr(getattr(blueprint, 'business', None), 'name', None) or 'unknown'
        logger.info(
            "[GEN] generation started | business=%s",
            biz_name,
        )

        # Step 1 — Build GenerationContext
        t1 = time.monotonic()
        try:
            context: GenerationContext = self.context_builder.build(blueprint, package)
        except Exception as exc:
            logger.error("[GEN] ContextBuilder failed: %s", exc)
            return GenerationResult(
                success=False,
                errors=[f"ContextBuilder failed: {type(exc).__name__}: {exc}"],
                generation_time=time.monotonic() - start,
            )
        logger.info("[GEN] step=context_build done | id=%s | %.2fs", context.generation_id, time.monotonic() - t1)

        # Step 2 — Build PromptContext + enforce token budget
        t2 = time.monotonic()
        try:
            prompt: PromptContext = self.prompt_builder.build(context)
            updated_constraints = f"{prompt.generation_constraints}\n\n{HTML_DIRECTIVE}"
            updated_rules = f"{prompt.rules_context}\n\n{HTML_DIRECTIVE}"
            prompt = prompt.model_copy(
                update={
                    "generation_constraints": updated_constraints,
                    "rules_context": updated_rules,
                }
            )
            prompt = _enforce_prompt_budget(prompt)
        except Exception as exc:
            logger.error("[GEN] PromptBuilder failed: %s", exc)
            return GenerationResult(
                success=False,
                errors=[f"PromptBuilder failed: {type(exc).__name__}: {exc}"],
                generation_time=time.monotonic() - start,
            )
        total_chars = sum(len(getattr(prompt, f, "") or "") for f in prompt.model_fields)
        logger.info(
            "[GEN] step=prompt_build done | total_chars=%d | %.2fs",
            total_chars, time.monotonic() - t2,
        )

        # Step 3-4 — Run provider chain via shared orchestrator
        t3 = time.monotonic()
        providers_to_try = ProviderFactory.get_fallback_chain(self.provider_name)
        logger.info("[GEN] step=ai_call start | chain=%s", providers_to_try)

        async def _call(name: str):
            provider = ProviderFactory.get_provider(name)
            logger.info("[GEN] provider=%s | calling generate", name)
            t_p = time.monotonic()
            ai_resp = await provider.generate(prompt)
            if not ai_resp.success:
                msg = "; ".join(ai_resp.errors) if ai_resp.errors else "Provider returned failure"
                logger.warning("[GEN] provider=%s failed in %.2fs: %s", name, time.monotonic() - t_p, msg)
                from app.core.exceptions import ServiceUnavailableException
                raise ServiceUnavailableException(msg)
            logger.info("[GEN] provider=%s succeeded in %.2fs | tokens=%s",
                name, time.monotonic() - t_p,
                ai_resp.usage.total_tokens if ai_resp.usage else 'N/A')
            return ai_resp.raw_response, ai_resp.model

        chain_result = await run_chain(providers_to_try, _call)

        if not chain_result.success:
            logger.error("[GEN] all providers failed in %.2fs: %s", time.monotonic() - t3, chain_result.last_error)
            return GenerationResult(
                success=False,
                errors=[chain_result.last_error or "All AI providers failed"],
                generation_time=time.monotonic() - start,
                provider_attempts=len(chain_result.attempts),
            )

        logger.info(
            "[GEN] step=ai_call done | provider=%s | %.2fs",
            chain_result.provider_used, time.monotonic() - t3,
        )

        # Step 5 — Parse response: extract HTML and create single file
        t5 = time.monotonic()
        raw_response = chain_result.result
        html_content = self._extract_html_content(raw_response)
        logger.info(
            "[GEN] step=html_extract | raw_len=%d | html_len=%d | %.2fs",
            len(raw_response) if raw_response else 0,
            len(html_content) if html_content else 0,
            time.monotonic() - t5,
        )
        if not html_content:
            logger.error("[GEN] html extraction failed — no valid HTML in AI response")
            return GenerationResult(
                success=False,
                errors=["No valid HTML content found in AI response"],
                generation_time=time.monotonic() - start,
                warnings=[f"Raw AI response length: {len(raw_response)} chars"],
            )

        project_name = self._extract_project_name_from_raw(raw_response) or "generated_website"
        generation_id = uuid.uuid4().hex[:12]

        html_file = GeneratedFile(
            path="index.html",
            content=html_content,
            type="html",
            size=len(html_content),
        )

        website_project = WebsiteProject(
            project_name=project_name,
            framework="static-html",
            generation_id=generation_id,
            version="1.0.0",
            generated_at=datetime.now(timezone.utc),
            files=[html_file],
            assets=[],  # no separate assets since everything is inline
            metadata={},
            statistics={"file_count": 1},
        )

        total_elapsed = time.monotonic() - start
        logger.info(
            "[GEN] generation complete | business=%s | provider=%s | "
            "html_size=%d bytes | total=%.2fs",
            biz_name, chain_result.provider_used, len(html_content), total_elapsed,
        )
        return GenerationResult(
            success=True,
            website_project=website_project,
            generation_time=total_elapsed,
            provider_used=chain_result.provider_used,
            provider_attempts=len(chain_result.attempts),
        )

    def _extract_html_content(self, raw: str) -> str:
        """Extract HTML content from raw AI response, stripping markdown fences if present."""
        if not raw:
            return ""
        # Try to find content between ```html and ``` or <!DOCTYPE ... and </html>
        import re
        # Pattern for code fences with html tag
        fence_pattern = r"```(?:html)?\s*(<!DOCTYPE html[\s\S]*?</html>)\s*```"
        match = re.search(fence_pattern, raw, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # If no fences, assume the whole string is the HTML (should start with <!DOCTYPE)
        stripped = raw.strip()
        if stripped.lower().startswith("<!doctype html>") or stripped.lower().startswith("<html"):
            # Find the closing html tag
            end_pos = stripped.lower().rfind("</html>")
            if end_pos != -1:
                return stripped[: end_pos + len("</html>")].strip()
        # Fallback: return trimmed raw (may cause validation error upstream)
        return stripped

    def _extract_project_name_from_raw(self, raw: str) -> Optional[str]:
        if not raw:
            return None
        import re
        patterns = [
            r"<title>\s*(.*?)\s*</title>",
            r"<h1>\s*(.*?)\s*</h1>",
        ]
        for pat in patterns:
            match = re.search(pat, raw, re.IGNORECASE | re.DOTALL)
            if match:
                name = match.group(1).strip()
                if name:
                    return name
        return None
