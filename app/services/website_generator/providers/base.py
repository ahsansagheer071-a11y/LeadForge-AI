from abc import ABC, abstractmethod
from typing import List

from app.services.website_generator.providers.schemas import AIResponse
from app.services.website_generator.schemas import PromptContext


class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt_context: PromptContext) -> AIResponse:
        """Send a PromptContext to the AI provider and return a structured AIResponse."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is reachable and the API key is valid."""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    def supported_models(self) -> List[str]:
        ...
