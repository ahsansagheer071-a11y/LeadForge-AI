"""DesignProvider — canonical interface for external visual design engines.

This replaces the legacy StaticHTMLGenerator pipeline.  A DesignProvider
receives all the context needed to produce a visual website redesign and
returns structured results.

The default implementation (DesignProviderNotConfigured) fails immediately
with a clear error until an external provider (e.g. Google Stitch) is wired
up.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from app.services.website_intelligence.schemas import WebsiteProfile
from app.services.markdown_engine.schemas import MarkdownPackage
from app.services.website_generator.schemas import GenerationResult

logger = logging.getLogger(__name__)


class DesignProvider(ABC):
    """Abstract interface for a visual design generation engine."""

    @abstractmethod
    async def generate(
        self,
        profile: WebsiteProfile,
        package: MarkdownPackage,
    ) -> GenerationResult:
        """Generate a visual website design from source website intelligence.

        Parameters
        ----------
        profile:
            Full WebsiteProfile extracted from the source website.
        package:
            MarkdownPackage built from the profile (content, rules, assets).

        Returns
        -------
        GenerationResult with success=True and a populated WebsiteProject,
        or success=False with structured errors.
        """
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """Short identifier for this provider (e.g. 'stitch', 'not_configured')."""
        ...


class DesignProviderNotConfigured(DesignProvider):
    """Stub that fails immediately — used until a real provider is wired up.

    This ensures the async job pipeline remains structurally functional:
    POST /jobs creates a job → background task runs → job finishes with
    status=failed, error_category=design_provider_not_configured, and a
    safe user-facing message.  No dummy HTML, no fake success.
    """

    NOT_CONFIGURED_MESSAGE = (
        "Website design provider is not configured. "
        "Premium website generation is being upgraded and will be available again soon."
    )

    async def generate(
        self,
        profile: WebsiteProfile,
        package: MarkdownPackage,
    ) -> GenerationResult:
        logger.warning("[DesignProvider] generate() called but no provider is configured")
        return GenerationResult(
            success=False,
            errors=[self.NOT_CONFIGURED_MESSAGE],
        )

    def provider_name(self) -> str:
        return "not_configured"
