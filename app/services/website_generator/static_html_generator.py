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
OUTPUT: A single complete HTML file. Start with <!DOCTYPE html>, end with </html>.
Use embedded <style> in <head>. No markdown, no explanations, no extra text.

DESIGN: Modern, clean redesign. Dark or light theme matching the brand.
Keep CSS minimal — use utility classes and inline styles where possible.
Output ALL sections: hero, about, services, products, contact, footer.

CONTENT RULES:
- Use source content VERBATIM — never rewrite or paraphrase.
- Use ONLY images from the Approved Asset Manifest.
- No Lorem Ipsum, no "Service 1/2", no LeadForge branding, no fake content.
- Include all source sections; do not add new ones.
- Every <img> src must reference an approved asset.
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
            updated_constraints = f"{prompt.generation_constraints}\n\n{HTML_DIRECTIVE}"
            updated_rules = f"{prompt.rules_context}\n\n{HTML_DIRECTIVE}"
            prompt = prompt.model_copy(
                update={
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

        if len(html_content) < 1000:
            logger.warning("[GEN] very short HTML output (%d bytes) — AI may have truncated", len(html_content))

        # Step 5a — Recover from truncated HTML
        html_content = self._recover_truncated_html(html_content)

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

    @staticmethod
    def _recover_truncated_html(html: str) -> str:
        """If the AI response was truncated mid-HTML, try to salvage it by
        closing any open tags so the result is at least valid HTML."""
        if not html:
            return html
        lower = html.lower()
        # Already complete
        if "</html>" in lower:
            return html

        # Build closing sequence for open tags
        import re
        open_tags = re.findall(r"<(style|script|head|body|html)\b", html, re.IGNORECASE)
        # Remove tags that are already closed
        for tag in list(open_tags):
            if f"</{tag}>" in lower:
                open_tags.remove(tag)

        closings = []
        for tag in reversed(open_tags):
            closings.append(f"</{tag}>")

        if not closings:
            # No recognizable open tags — just append minimal closure
            closings = ["</style>", "</head>", "<body></body>", "</html>"]

        recovered = html + "\n" + "\n".join(closings)
        logger.info(
            "[GEN] html_recovery: added %d closing tags (%d -> %d bytes)",
            len(closings), len(html), len(recovered),
        )
        return recovered
