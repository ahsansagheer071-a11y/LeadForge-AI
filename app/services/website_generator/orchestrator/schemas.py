import logging
import time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ProviderAttempt(BaseModel):
    provider: str
    model: str
    success: bool
    latency: float
    status_code: Optional[int] = None
    errors: List[str] = Field(default_factory=list)
    attempted_at: float = 0.0


class RouterResult(BaseModel):
    success: bool
    provider_used: str
    model_used: str
    raw_response: str
    attempts: List[ProviderAttempt] = Field(default_factory=list)
    total_latency: float = 0.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class CircuitState(BaseModel):
    provider: str
    state: str = "closed"
    failure_count: int = 0
    last_failure_at: Optional[float] = None
    half_open_attempts: int = 0
    opened_at: Optional[float] = None

    model_config = {"frozen": False}


class ProviderHealth(BaseModel):
    provider: str
    healthy: bool
    latency: float
    last_checked: float
    consecutive_failures: int = 0
