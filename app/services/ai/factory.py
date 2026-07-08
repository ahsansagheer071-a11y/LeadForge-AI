from typing import Dict, Type, Optional

from app.core.logging import logger
from app.services.ai.base import AIBaseProvider
from app.services.ai.groq import GroqProvider
from app.services.ai.pollinations import PollinationsProvider
from app.services.ai.nvidia import NvidiaProvider


_PROVIDER_REGISTRY: Dict[str, Type[AIBaseProvider]] = {
    "groq": GroqProvider,
    "pollinations": PollinationsProvider,
    "nvidia": NvidiaProvider,
}

FALLBACK_CHAIN = ["groq", "pollinations", "nvidia"]


class AIFactory:
    @staticmethod
    def get_provider(provider_name: str) -> AIBaseProvider:
        key = provider_name.lower()
        cls = _PROVIDER_REGISTRY.get(key)
        if cls is None:
            available = ", ".join(_PROVIDER_REGISTRY.keys())
            raise ValueError(f"Unsupported AI Provider: {provider_name}. Available: {available}")
        return cls()

    @staticmethod
    def get_fallback_chain(start_with: Optional[str] = None) -> list:
        if start_with:
            start_key = start_with.lower()
            if start_key in _PROVIDER_REGISTRY:
                chain = [start_key]
                chain.extend(p for p in FALLBACK_CHAIN if p != start_key)
                return chain
        return list(FALLBACK_CHAIN)


ai_factory = AIFactory()
