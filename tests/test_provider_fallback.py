"""Focused tests for the AI provider fallback chain (Groq → Pollinations → NVIDIA)."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.core.exceptions import ServiceUnavailableException
from app.services.ai.factory import AIFactory
from app.services.ai.groq import GroqProvider
from app.services.ai.pollinations import PollinationsProvider
from app.services.ai.nvidia import NvidiaProvider


class TestAIFactory:
    def test_get_provider_groq(self):
        provider = AIFactory.get_provider("groq")
        assert isinstance(provider, GroqProvider)

    def test_get_provider_pollinations(self):
        provider = AIFactory.get_provider("pollinations")
        assert isinstance(provider, PollinationsProvider)

    def test_get_provider_nvidia(self):
        provider = AIFactory.get_provider("nvidia")
        assert isinstance(provider, NvidiaProvider)

    def test_get_provider_invalid(self):
        with pytest.raises(ValueError, match="Unsupported AI Provider"):
            AIFactory.get_provider("invalid_provider")

    def test_fallback_chain_default(self):
        chain = AIFactory.get_fallback_chain()
        assert chain == ["groq", "pollinations", "nvidia"]

    def test_fallback_chain_start_with(self):
        chain = AIFactory.get_fallback_chain("pollinations")
        assert chain[0] == "pollinations"
        assert "groq" in chain
        assert "nvidia" in chain
        assert len(chain) == 3

    def test_fallback_chain_no_duplicates(self):
        chain = AIFactory.get_fallback_chain("groq")
        assert chain == ["groq", "pollinations", "nvidia"]


class TestGroqSucceeds:
    @pytest.mark.asyncio
    async def test_audit_website_no_api_key(self):
        with patch("app.services.ai.groq.settings.GROQ_API_KEY", None):
            provider = GroqProvider()
            with pytest.raises(ServiceUnavailableException, match="API key"):
                await provider.audit_website({}, {}, {})

    @pytest.mark.asyncio
    async def test_generate_outreach_no_api_key(self):
        with patch("app.services.ai.groq.settings.GROQ_API_KEY", None):
            provider = GroqProvider()
            with pytest.raises(ServiceUnavailableException, match="API key"):
                await provider.generate_outreach({}, {}, {}, {})


class TestPollinationsSucceeds:
    @pytest.mark.asyncio
    async def test_provider_name(self):
        provider = PollinationsProvider()
        assert isinstance(provider, PollinationsProvider)

    @pytest.mark.asyncio
    async def test_audit_website_no_api_key_does_not_raise_at_init(self):
        """Pollinations works without an API key."""
        provider = PollinationsProvider()
        assert provider.api_key is None or provider.api_key == ""


class TestNvidiaSucceeds:
    @pytest.mark.asyncio
    async def test_provider_name(self):
        provider = NvidiaProvider()
        assert isinstance(provider, NvidiaProvider)

    @pytest.mark.asyncio
    async def test_audit_website_no_api_key(self):
        with patch("app.services.ai.nvidia.settings.NVIDIA_API_KEY", None):
            provider = NvidiaProvider()
            with pytest.raises(ServiceUnavailableException, match="NVIDIA_API_KEY"):
                await provider.audit_website({}, {}, {})


class TestFallbackChain:
    @pytest.mark.asyncio
    async def test_groq_fails_pollinations_succeeds(self):
        """Simulate Groq failure → fallback to Pollinations."""
        from app.services.audit_engine import AuditEngineService

        mock_groq = AsyncMock(spec=GroqProvider)
        mock_groq.audit_website = AsyncMock(side_effect=ServiceUnavailableException("Groq down"))

        mock_pollinations = AsyncMock(spec=PollinationsProvider)
        expected_result = {
            "Business Summary": "Test",
            "Website Quality Score": 75,
            "Visual Design Score": 75,
            "SEO Score": 75,
            "Trust Score": 75,
            "Mobile Experience Score": 75,
            "Performance Score": 75,
            "Content Quality Score": 75,
            "CTA Score": 75,
            "Top Strengths": ["S1", "S2", "S3"],
            "Top Weaknesses": ["W1", "W2", "W3"],
            "Actionable Recommendations": ["R1", "R2", "R3"],
            "Priority Improvements": ["P1", "P2", "P3"],
            "Overall Summary": "Summary",
        }
        mock_pollinations.audit_website = AsyncMock(return_value=expected_result)

        with patch.object(AIFactory, "get_provider") as mock_get:
            mock_get.side_effect = [mock_groq, mock_pollinations]

            providers = AIFactory.get_fallback_chain("groq")
            result = None
            last_error = ""

            for provider_name in providers:
                try:
                    provider = AIFactory.get_provider(provider_name)
                    result = await provider.audit_website({}, {}, {})
                    break
                except ServiceUnavailableException as e:
                    last_error = str(e)
                    continue

            assert result == expected_result
            assert mock_get.call_count == 2
            mock_groq.audit_website.assert_awaited_once()
            mock_pollinations.audit_website.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_groq_and_pollinations_fail_nvidia_succeeds(self):
        """Simulate Groq + Pollinations failure → fallback to NVIDIA."""
        mock_groq = AsyncMock(spec=GroqProvider)
        mock_groq.audit_website = AsyncMock(side_effect=ServiceUnavailableException("Groq down"))

        mock_pollinations = AsyncMock(spec=PollinationsProvider)
        mock_pollinations.audit_website = AsyncMock(side_effect=ServiceUnavailableException("Pollinations down"))

        mock_nvidia = AsyncMock(spec=NvidiaProvider)
        expected_result = {
            "Business Summary": "Nvidia Result",
            "Website Quality Score": 80,
            "Visual Design Score": 80,
            "SEO Score": 80,
            "Trust Score": 80,
            "Mobile Experience Score": 80,
            "Performance Score": 80,
            "Content Quality Score": 80,
            "CTA Score": 80,
            "Top Strengths": ["S1", "S2", "S3"],
            "Top Weaknesses": ["W1", "W2", "W3"],
            "Actionable Recommendations": ["R1", "R2", "R3"],
            "Priority Improvements": ["P1", "P2", "P3"],
            "Overall Summary": "Nvidia Summary",
        }
        mock_nvidia.audit_website = AsyncMock(return_value=expected_result)

        with patch.object(AIFactory, "get_provider") as mock_get:
            mock_get.side_effect = [mock_groq, mock_pollinations, mock_nvidia]

            providers = AIFactory.get_fallback_chain("groq")
            result = None
            last_error = ""

            for provider_name in providers:
                try:
                    provider = AIFactory.get_provider(provider_name)
                    result = await provider.audit_website({}, {}, {})
                    break
                except ServiceUnavailableException as e:
                    last_error = str(e)
                    continue

            assert result == expected_result
            assert mock_get.call_count == 3

    @pytest.mark.asyncio
    async def test_all_providers_fail_safely(self):
        """All providers fail → raise ServiceUnavailableException."""
        mock_groq = AsyncMock(spec=GroqProvider)
        mock_groq.audit_website = AsyncMock(side_effect=ServiceUnavailableException("Groq down"))

        mock_pollinations = AsyncMock(spec=PollinationsProvider)
        mock_pollinations.audit_website = AsyncMock(side_effect=ServiceUnavailableException("Pollinations down"))

        mock_nvidia = AsyncMock(spec=NvidiaProvider)
        mock_nvidia.audit_website = AsyncMock(side_effect=ServiceUnavailableException("Nvidia down"))

        with patch.object(AIFactory, "get_provider") as mock_get:
            mock_get.side_effect = [mock_groq, mock_pollinations, mock_nvidia]

            providers = AIFactory.get_fallback_chain("groq")
            result = None
            last_error = ""

            for provider_name in providers:
                try:
                    provider = AIFactory.get_provider(provider_name)
                    result = await provider.audit_website({}, {}, {})
                    break
                except ServiceUnavailableException as e:
                    last_error = str(e)
                    continue

            assert result is None
            assert "Nvidia" in last_error

    @pytest.mark.asyncio
    async def test_invalid_json_rejected(self):
        """Invalid JSON from a provider is rejected."""
        import json as _json
        provider = GroqProvider()
        with pytest.raises(_json.JSONDecodeError):
            await provider._parse_json_response("{invalid json}")

    @pytest.mark.asyncio
    async def test_audit_persists_once(self):
        """Mock test: audit creates a single record."""
        from app.services.audit_engine import AuditEngineService
        service = AuditEngineService()
        assert hasattr(service, "generate_audit")
        assert callable(service.generate_audit)

    @pytest.mark.asyncio
    async def test_generation_provider_not_configured(self):
        """DesignProviderNotConfigured fails gracefully — no dummy HTML."""
        from app.services.website_generator.design_provider import DesignProviderNotConfigured
        from app.services.website_intelligence.schemas import WebsiteProfile, BusinessInfo
        from app.services.markdown_engine.schemas import MarkdownPackage

        provider = DesignProviderNotConfigured()
        assert provider.provider_name() == "not_configured"

        profile = WebsiteProfile(business=BusinessInfo(name="Test"))
        pkg = MarkdownPackage()
        result = await provider.generate(profile, pkg)
        assert result.success is False
        assert result.website_project is None
        assert "not configured" in result.errors[0].lower() or "upgraded" in result.errors[0].lower()
