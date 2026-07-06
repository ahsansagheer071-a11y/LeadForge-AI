from app.services.ai.base import AIBaseProvider
from app.services.ai.groq import GroqProvider


class AIFactory:
    """
    Factory to retrieve configured AI Provider.
    """

    @staticmethod
    def get_provider(provider_name: str = "groq") -> AIBaseProvider:
        if provider_name.lower() == "groq":
            return GroqProvider()

        raise ValueError(f"Unsupported AI Provider: {provider_name}")


ai_factory = AIFactory()