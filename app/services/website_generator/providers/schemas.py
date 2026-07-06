from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AIUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class AIResponse(BaseModel):
    success: bool = False
    provider: str = ""
    model: str = ""
    raw_response: str = ""
    usage: Optional[AIUsage] = None
    latency: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
