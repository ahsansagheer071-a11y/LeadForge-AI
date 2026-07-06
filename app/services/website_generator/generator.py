import logging
import time
from typing import Optional

from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.website_generator.context_builder import ContextBuilder
from app.services.website_generator.prompt_builder import PromptBuilder
from app.services.website_generator.providers.provider_factory import ProviderFactory
from app.services.website_generator.response_parser import ResponseParser
from app.services.website_generator.schemas import (
    GenerationContext,
    GenerationResult,
    PromptContext,
    WebsiteProject,
)
from app.services.website_intelligence.schemas import WebsiteProfile

logger = logging.getLogger(__name__)


class WebsiteGenerator:
    def __init__(
        self,
        context_builder: Optional[ContextBuilder] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        response_parser: Optional[ResponseParser] = None,
        provider_name: Optional[str] = None,
    ):
        self.context_builder = context_builder or ContextBuilder()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.response_parser = response_parser or ResponseParser()
        self.provider_name = provider_name

    async def generate(
        self,
        blueprint: WebsiteProfile,
        package: MarkdownPackage,
    ) -> GenerationResult:
        start = time.monotonic()
        logger.info("Website generation started")

        # Step 1 — Build GenerationContext
        logger.info("Building GenerationContext")
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
        logger.info("Building PromptContext")
        try:
            prompt: PromptContext = self.prompt_builder.build(context)
        except Exception as exc:
            logger.error("PromptBuilder failed: %s", exc)
            return GenerationResult(
                success=False,
                errors=[f"PromptBuilder failed: {type(exc).__name__}: {exc}"],
                generation_time=time.monotonic() - start,
            )
        logger.info("PromptContext built (%d chars)", len(str(prompt)))

        # Step 3 — Load provider
        logger.info("Loading provider")
        try:
            provider = ProviderFactory.get_provider(self.provider_name)
        except ValueError as exc:
            logger.error("ProviderFactory failed: %s", exc)
            return GenerationResult(
                success=False,
                errors=[f"Provider resolution failed: {exc}"],
                generation_time=time.monotonic() - start,
            )
        logger.info("Provider selected: %s", provider.provider_name())

        # Step 4 — Call provider
        logger.info("Sending prompt to provider")
        try:
            ai_response = await provider.generate(prompt)
        except Exception as exc:
            logger.error("Provider call failed: %s", exc)
            return GenerationResult(
                success=False,
                errors=[f"Provider call failed: {type(exc).__name__}: {exc}"],
                generation_time=time.monotonic() - start,
            )
        logger.info(
            "Provider responded: success=%s, latency=%.2fs",
            ai_response.success,
            ai_response.latency,
        )

        if not ai_response.success:
            logger.warning("Provider returned failure: %s", ai_response.errors)
            return GenerationResult(
                success=False,
                errors=ai_response.errors,
                warnings=ai_response.warnings,
                generation_time=time.monotonic() - start,
            )

        # Step 5 — Parse response
        logger.info("Parsing provider response")
        website_project: Optional[WebsiteProject] = None
        parse_errors: list = []
        parse_warnings: list = []
        try:
            website_project = self.response_parser.parse(ai_response)
        except NotImplementedError:
            msg = "ResponseParser.parse() is not implemented — raw AI response stored in warnings"
            logger.warning(msg)
            parse_warnings.append(msg)
            parse_warnings.append(
                f"Raw AI response ({len(ai_response.raw_response)} chars) available"
            )
        except Exception as exc:
            logger.error("ResponseParser failed: %s", exc)
            parse_errors.append(f"ResponseParser failed: {type(exc).__name__}: {exc}")

        elapsed = time.monotonic() - start
        logger.info(
            "Website generation finished: success=%s, duration=%.2fs",
            website_project is not None,
            elapsed,
        )

        return GenerationResult(
            success=website_project is not None,
            website_project=website_project,
            generation_time=elapsed,
            warnings=parse_warnings,
            errors=parse_errors,
        )
