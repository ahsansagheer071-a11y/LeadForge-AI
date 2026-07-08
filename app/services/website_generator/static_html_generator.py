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
from app.services.website_generator.context_builder import ContextBuilder
from app.services.website_generator.prompt_builder import PromptBuilder
from app.services.website_generator.orchestrator.router import AIProviderRouter
from app.services.website_generator.schemas import (
    GenerationContext,
    GenerationResult,
    PromptContext,
    WebsiteProject,
    GeneratedFile,
)

logger = logging.getLogger(__name__)

HTML_DIRECTIVE = """
You MUST output ONLY a single, complete, valid HTML document starting with 
<!DOCTYPE html> and ending with </html>. All CSS must be inside a <style> 
tag in the head, and all JavaScript must be inside a <script> tag before 
the closing </body> tag. Do NOT include any explanations, markdown fences, 
or extra text outside the HTML. The HTML should be a functional, styled 
website representing the given business.
"""

class StaticHTMLGenerator:
    def __init__(
        self,
        context_builder: Optional[ContextBuilder] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        provider_name: Optional[str] = None,
        router: Optional[AIProviderRouter] = None,
    ):
        self.context_builder = context_builder or ContextBuilder()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.provider_name = provider_name
        self.router = router or AIProviderRouter()

    async def generate(
        self,
        blueprint: WebsiteProfile,
        package: MarkdownPackage,
    ) -> GenerationResult:
        start = time.monotonic()
        logger.info("Static HTML generation started")

        # Step 1 — Build GenerationContext
        try:
            context: GenerationContext = self.context_builder.build(blueprint, package)
        except Exception as exc:
            logger.error("ContextBuilder failed: %s", exc)
            return GenerationResult(
                success=False,
                errors=[f"ContextBuilder failed: {type(exc).__name__}: {exc}"],
                generation_time=time.monotonic() - start,
            )
        logger.info("GenerationContext built (id=%s)", context.generation_id)

        # Step 2 — Build PromptContext
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
        except Exception as exc:
            logger.error("PromptBuilder failed: %s", exc)
            return GenerationResult(
                success=False,
                errors=[f"PromptBuilder failed: {type(exc).__name__}: {exc}"],
                generation_time=time.monotonic() - start,
            )
        logger.info("PromptContext built with HTML directive (%d chars)", len(str(prompt)))

        # Step 3-4 — Route via orchestrator with circuit breaker + fallback
        router_result = await self.router.route(
            prompt=prompt,
            preferred_provider=self.provider_name,
            max_attempts_per_provider=2,
        )

        if not router_result.success:
            logger.error("Orchestrator failed: %s", "; ".join(router_result.errors))
            return GenerationResult(
                success=False,
                errors=router_result.errors or ["All AI providers failed"],
                generation_time=time.monotonic() - start,
                warnings=router_result.warnings,
                provider_attempts=len(router_result.attempts),
            )

        logger.info("Generation succeeded with provider: %s (latency=%.2fs)", router_result.provider_used, router_result.total_latency)

        # Step 5 — Parse response: extract HTML and create single file
        logger.info("Parsing provider response for HTML content")
        html_content = self._extract_html_content(router_result.raw_response)
        if not html_content:
            logger.error("Failed to extract HTML content from AI response")
            return GenerationResult(
                success=False,
                errors=["No valid HTML content found in AI response"],
                generation_time=time.monotonic() - start,
                warnings=[f"Raw AI response length: {len(router_result.raw_response)} chars"],
            )

        project_name = self._extract_project_name_from_raw(router_result.raw_response) or "generated_website"
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

        logger.info("Static HTML generation successful")
        return GenerationResult(
            success=True,
            website_project=website_project,
            generation_time=time.monotonic() - start,
            provider_used=router_result.provider_used,
            provider_attempts=len(router_result.attempts),
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
