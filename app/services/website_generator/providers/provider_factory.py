import logging
from typing import Dict, Optional, Type

from app.core.config import settings
from app.services.website_generator.providers.base import AIProvider
from app.services.website_generator.providers.groq_provider import GroqProvider

logger = logging.getLogger(__name__)

_PROVIDER_REGISTRY: Dict[str, Type[AIProvider]] = {
    "groq": GroqProvider,
}


def register_provider(name: str, provider_cls: Type[AIProvider]) -> None:
    """Register a new AI provider for use via the factory.

    Usage:
        from app.services.website_generator.providers.my_provider import MyProvider
        register_provider("my_provider", MyProvider)

    Once registered, ProviderFactory.get_provider("my_provider") returns
    an instance of MyProvider. No changes to ProviderFactory or
    WebsiteGenerator are needed.
    """
    _PROVIDER_REGISTRY[name] = provider_cls
    logger.info("Registered AI provider: %s", name)


class ProviderFactory:
    @staticmethod
    def get_provider(provider_name: Optional[str] = None) -> AIProvider:
        if provider_name is None:
            provider_name = "groq"
        provider_name = provider_name.lower()

        cls = _PROVIDER_REGISTRY.get(provider_name)
        if cls is None:
            available = ", ".join(_PROVIDER_REGISTRY.keys())
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available providers: {available}"
            )

        logger.info("Provider factory resolved: %s", provider_name)
        instance = cls()
        return instance
