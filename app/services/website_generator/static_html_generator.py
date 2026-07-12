"""Static HTML Website Generator - produces a single self-contained HTML file.

This generator wraps the existing pipeline but injects a directive to the AI
to output ONLY a complete HTML document with embedded CSS and JS, suitable
for immediate preview in an iframe.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.services.website_intelligence.schemas import WebsiteProfile
from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.markdown_engine.asset_manifest import ManifestBuilder
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
from app.services.website_generator.prompt_budget import PromptBudgetController
from app.services.website_generator.fidelity_validator import FidelityValidator
from app.services.website_generator.asset_packager import AssetPackager
from app.services.ai.chain import run_chain

logger = logging.getLogger(__name__)

HTML_DIRECTIVE = """
You are an HTML code generator. Your ONLY job is to output raw HTML body content.
You must output ONLY HTML tags — no explanations, no markdown, no text summaries.

OUTPUT: Only the inner content of a <body> tag. Start with <header> or <section>.
Use inline styles for all elements. Use the provided source content VERBATIM.

SECTIONS TO INCLUDE (in order):
1. Hero/header with the business name and tagline
2. About section
3. Services or products (as grid cards)
4. Contact info (email, phone, address)
5. Footer

RULES:
- Output ONLY HTML tags, no text commentary
- Use inline styles like: style="color:#fff;padding:20px"
- Reference images with full URLs from the Approved Asset Manifest
- Never use Lorem Ipsum or placeholder text
- Never add LeadForge branding
"""

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
            # Override system context with clear HTML generation instruction
            system_msg = (
                "You are an expert HTML/CSS code generator. "
                "You output ONLY raw HTML body content — no explanations, no markdown, no text. "
                "Every response must start with <header or <section and contain valid HTML tags."
            )
            updated_constraints = f"{HTML_DIRECTIVE}"
            updated_rules = f"{prompt.rules_context}\n\n{HTML_DIRECTIVE}"
            prompt = prompt.model_copy(
                update={
                    "system_context": system_msg,
                    "generation_constraints": updated_constraints,
                    "rules_context": updated_rules,
                }
            )
            # Apply PromptBudgetController to remove boilerplate/duplicates
            budget_ctrl = PromptBudgetController()
            prompt, budget_report = budget_ctrl.apply(prompt)
            logger.info(
                "[GEN] prompt_budget: saved %d chars (removed %d items)",
                budget_report.chars_saved, len(budget_report.actions),
            )
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
            all_errors = [
                f"{a.provider}: {a.error}" if a.error else f"{a.provider}: success={a.success}"
                for a in chain_result.attempts
            ]
            return GenerationResult(
                success=False,
                errors=all_errors or [chain_result.last_error or "All AI providers failed"],
                generation_time=time.monotonic() - start,
                provider_attempts=len(chain_result.attempts),
            )

        logger.info(
            "[GEN] step=ai_call done | provider=%s | %.2fs",
            chain_result.provider_used, time.monotonic() - t3,
        )

        # Step 5 — Parse response: extract body content and wrap in template
        t5 = time.monotonic()
        raw_response = chain_result.result
        body_content = self._extract_body_content(raw_response)
        if not body_content:
            logger.error("[GEN] body extraction failed — no valid content in AI response")
            return GenerationResult(
                success=False,
                errors=["No valid body content found in AI response"],
                generation_time=time.monotonic() - start,
                warnings=[f"Raw AI response length: {len(raw_response)} chars"],
            )
        body_content = self._recover_body_content(body_content)
        logger.info(
            "[GEN] step=body_extract | raw_len=%d | body_len=%d | %.2fs",
            len(raw_response) if raw_response else 0,
            len(body_content),
            time.monotonic() - t5,
        )

        # Build complete HTML from template + AI body
        t5a = time.monotonic()
        html_template = self._build_html_template(blueprint)
        html_content = html_template.replace("<!--BODY_CONTENT-->", body_content)
        logger.info("[GEN] step=template_wrap | template=%d + body=%d = total=%d | %.2fs",
            len(html_template), len(body_content), len(html_content), time.monotonic() - t5a)

        # Step 5b — Fidelity validation
        t5b = time.monotonic()
        manifest = getattr(package, 'asset_manifest', None)
        validator = FidelityValidator(blueprint, manifest=manifest)
        fidelity_result = validator.validate(html_content)
        warnings: List[str] = []
        if not fidelity_result.valid:
            logger.warning(
                "[GEN] fidelity check failed: %d issues",
                len(fidelity_result.issues),
            )
            for issue in fidelity_result.issues:
                logger.warning("[GEN] fidelity issue [%s]: %s", issue.category, issue.detail)
                warnings.append(f"[{issue.category}] {issue.detail}")
        else:
            logger.info("[GEN] fidelity check passed | %.2fs", time.monotonic() - t5b)
        fidelity_issue_count = len(fidelity_result.issues)

        # Step 5c — Asset packaging: download images, rewrite HTML to local paths
        t5c = time.monotonic()
        original_html = html_content
        packager = AssetPackager()
        image_artifacts: List[str] = []
        try:
            rewritten_html, artifacts_list, asset_warnings = await packager.package_assets_async(
                html_content, manifest
            ) if manifest else (html_content, [], ["No manifest for asset packaging."])
            warnings.extend(asset_warnings)

            if rewritten_html != html_content:
                html_content = rewritten_html

            # Store image artifacts as JSON-encoded strings in project.assets
            import json as _json
            image_artifacts = [
                _json.dumps(a.model_dump(mode="json")) for a in artifacts_list
            ]

            logger.info(
                "[GEN] step=asset_packaging | images=%d | html_rewritten=%s | %.2fs",
                len(artifacts_list),
                rewritten_html != html_content,
                time.monotonic() - t5c,
            )
        except Exception as exc:
            logger.warning("[GEN] asset packaging failed (non-fatal): %s", exc)
            warnings.append(f"Asset packaging failed: {exc}")
        finally:
            try:
                packager.cleanup()
            except Exception:
                pass

        project_name = (getattr(getattr(blueprint, 'business', None), 'name', None) or "generated_website").replace(" ", "_")
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
            assets=image_artifacts,
            metadata={},
            statistics={
                "file_count": 1,
                "asset_count": len(image_artifacts),
                "fidelity_valid": fidelity_result.valid,
                "fidelity_issues": fidelity_issue_count,
            },
            preview_html=original_html,
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
            warnings=warnings,
            generation_time=total_elapsed,
            provider_used=chain_result.provider_used,
            provider_attempts=len(chain_result.attempts),
        )

    def _extract_html_content(self, raw: str) -> str:
        """Extract HTML content from raw AI response, stripping markdown fences if present."""
        if not raw:
            return ""
        import re
        fence_pattern = r"```(?:html)?\s*(<!DOCTYPE html[\s\S]*?</html>)\s*```"
        match = re.search(fence_pattern, raw, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        stripped = raw.strip()
        if stripped.lower().startswith("<!doctype html>") or stripped.lower().startswith("<html"):
            end_pos = stripped.lower().rfind("</html>")
            if end_pos != -1:
                return stripped[: end_pos + len("</html>")].strip()
        return stripped

    def _extract_body_content(self, raw: str) -> str:
        """Extract body content from AI response. Handles multiple formats:
        1. Full HTML document → extract body innerHTML
        2. Partial HTML with sections → return as-is
        3. Markdown fences → strip and extract
        """
        if not raw:
            return ""
        import re
        stripped = raw.strip()
        # Strip markdown fences if present
        fence_match = re.search(r"```(?:html)?\s*([\s\S]*?)```", stripped, re.IGNORECASE)
        if fence_match:
            stripped = fence_match.group(1).strip()

        # If AI returned a full HTML doc, extract body content
        body_match = re.search(r"<body[^>]*>([\s\S]*?)</body>", stripped, re.IGNORECASE)
        if body_match:
            return body_match.group(1).strip()

        # If it starts with DOCTYPE/html/head, extract everything after </style> or </head>
        if stripped.lower().startswith("<!doctype") or stripped.lower().startswith("<html"):
            after_head = re.sub(r"<!DOCTYPE[^>]*>\s*<html[^>]*>\s*<head[\s\S]*?</head>\s*", "", stripped, flags=re.IGNORECASE)
            after_head = re.sub(r"</?html[^>]*>\s*", "", after_head, flags=re.IGNORECASE)
            # Remove closing body/html tags
            after_head = re.sub(r"</body>\s*</html>\s*$", "", after_head, flags=re.IGNORECASE)
            after_head = re.sub(r"</html>\s*$", "", after_head, flags=re.IGNORECASE)
            if after_head.strip():
                return after_head.strip()

        # Assume it's already body content (sections, divs, etc.)
        return stripped

    @staticmethod
    def _recover_body_content(body: str) -> str:
        """Close any unclosed HTML tags in body content (from truncated AI output)."""
        if not body:
            return body
        import re
        if body.rstrip().endswith("</body>") or body.rstrip().endswith("</html>"):
            return body
        open_tags = re.findall(r"<(section|div|header|footer|nav|main|article|aside|figure|ul|ol|li|table|tr|td|th|thead|tbody|p|h[1-6])\b", body, re.IGNORECASE)
        closings = []
        for tag in reversed(open_tags):
            if not re.search(rf"</{tag}\s*>", body, re.IGNORECASE):
                closings.append(f"</{tag}>")
        if closings:
            recovered = body.rstrip() + "\n" + "\n".join(closings)
            logger.info("[GEN] body_recovery: added %d closing tags", len(closings))
            return recovered
        return body

    @staticmethod
    def _build_html_template(blueprint) -> str:
        """Build a minimal HTML template with CSS derived from brand identity."""
        # Extract brand colors
        brand = getattr(blueprint, 'brand', None)
        primary = "#1a1a2e"
        secondary = "#16213e"
        accent = "#e94560"
        text_color = "#ffffff"
        bg_color = "#0f0f23"
        heading_font = "'Inter', 'Segoe UI', sans-serif"
        body_font = "'Inter', 'Segoe UI', sans-serif"

        if brand:
            palette = getattr(brand, 'color_palette', None)
            if palette:
                primary = getattr(palette, 'primary', None) or primary
                secondary = getattr(palette, 'secondary', None) or secondary
                accent = getattr(palette, 'accent', None) or accent
            typography = getattr(brand, 'typography', None)
            if typography:
                heading_font = getattr(typography, 'heading_font', None) or heading_font
                body_font = getattr(typography, 'body_font', None) or body_font

        biz_name = getattr(getattr(blueprint, 'business', None), 'name', None) or 'Business'
        seo = getattr(blueprint, 'seo', None)
        description = ""
        if seo:
            description = getattr(seo, 'meta_description', None) or description

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{biz_name}</title>
<meta name="description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --primary:{primary};
  --secondary:{secondary};
  --accent:{accent};
  --text:{text_color};
  --bg:{bg_color};
  --heading-font:{heading_font};
  --body-font:{body_font};
}}
html{{scroll-behavior:smooth}}
body{{font-family:var(--body-font);color:var(--text);background:var(--bg);line-height:1.6}}
h1,h2,h3,h4,h5,h6{{font-family:var(--heading-font);font-weight:600;line-height:1.2}}
img{{max-width:100%;height:auto;display:block}}
a{{color:var(--accent);text-decoration:none}}
a:hover{{text-decoration:underline}}
.container{{max-width:1200px;margin:0 auto;padding:0 20px}}
section{{padding:80px 0}}
.hero{{min-height:80vh;display:flex;align-items:center;background:linear-gradient(135deg,var(--primary),var(--secondary))}}
.hero h1{{font-size:3rem;margin-bottom:1rem}}
.hero p{{font-size:1.25rem;max-width:600px;opacity:0.9}}
.btn{{display:inline-block;padding:12px 32px;background:var(--accent);color:#fff;border-radius:6px;font-weight:500;transition:opacity .2s}}
.btn:hover{{opacity:0.9;text-decoration:none}}
.grid{{display:grid;gap:2rem}}
.grid-2{{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}}
.grid-3{{grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}}
.card{{background:rgba(255,255,255,0.05);border-radius:12px;padding:2rem;border:1px solid rgba(255,255,255,0.1)}}
.card h3{{margin-bottom:0.75rem;color:var(--accent)}}
footer{{background:var(--primary);padding:40px 0;text-align:center;opacity:0.8}}
@media(max-width:768px){{
  .hero h1{{font-size:2rem}}
  section{{padding:40px 0}}
}}
</style>
</head>
<body>
<!--BODY_CONTENT-->
</body>
</html>"""
