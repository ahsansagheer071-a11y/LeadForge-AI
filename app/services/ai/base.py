from abc import ABC, abstractmethod
from typing import Dict, Any

class AIBaseProvider(ABC):
    """
    Interface for AI providers to perform website audits.
    """
    @abstractmethod
    async def audit_website(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        screenshot_urls: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submits lead context, raw website analysis details, and screenshot URLs to the AI model
        and returns a standardized audit dictionary.
        """
        pass

    @abstractmethod
    async def generate_outreach(
        self,
        lead_info: Dict[str, Any],
        website_analysis: Dict[str, Any],
        audit_data: Dict[str, Any],
        score_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submits lead context, raw website analysis, AI audit, and lead score to the AI model
        and returns a structured dictionary containing outreach templates (email, linkedin, etc).
        """
        pass
