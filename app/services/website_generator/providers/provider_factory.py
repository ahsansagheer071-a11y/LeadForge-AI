import logging
from typing import Dict, Optional, Type, List

from app.core.config import settings
from app.services.website_generator.providers.base import AIProvider
from app.services.website_generator.providers.groq_provider import GroqProvider
from app.services.website_generator.providers.pollinations_provider import PollinationsProvider
from app.services.website_generator.providers.nvidia_provider import NvidiaProvider

logger = logging.getLogger(__name__)

_PROVIDER_REGISTRY: Dict[str, Type[AIProvider]] = {
    "groq": GroqProvider,
    "pollinations": PollinationsProvider,
    "nvidia": NvidiaProvider,
}

FALLBACK_CHAIN: List[str] = ["groq", "pollinations", "nvidia"]


def register_provider(name: str, provider_cls: Type[AIProvider]) -> None:
    _PROVIDER_REGISTRY[name] = provider_cls
    logger.info("Registered AI provider: %s", name)


class ProviderFactory:
    @staticmethod
    def get_provider(provider_name: Optional[str] = None) -> AIProvider:
        if provider_name is None:
            provider_name = "groq"
        key = provider_name.lower()

        cls = _PROVIDER_REGISTRY.get(key)
        if cls is None:
            available = ", ".join(_PROVIDER_REGISTRY.keys())
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available providers: {available}"
            )

        logger.info("Provider factory resolved: %s", key)
        return cls()

    @staticmethod
    def get_fallback_chain(start_with: Optional[str] = None) -> List[str]:
        if start_with:
            start_key = start_with.lower()
            if start_key in _PROVIDER_REGISTRY:
                chain = [start_key]
                chain.extend(p for p in FALLBACK_CHAIN if p != start_key)
                return chain
        return list(FALLBACK_CHAIN)
