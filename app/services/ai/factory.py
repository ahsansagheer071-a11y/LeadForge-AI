from app.services.ai.base import AIBaseProvider
from app.services.ai.gemini import GeminiProvider

class AIFactory:
    """
    Factory to retrieve configured AI Provider.
    """
    @staticmethod
    def get_provider(provider_name: str = "gemini") -> AIBaseProvider:
        if provider_name.lower() == "gemini":
            return GeminiProvider()
        
        # In the future we can add other providers: Groq, OpenAI etc.
        raise ValueError(f"Unsupported AI Provider: {provider_name}")

ai_factory = AIFactory()
