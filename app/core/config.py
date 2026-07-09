import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # System Configurations
    ENV: str = Field(default="production")
    DEBUG: bool = Field(default=False)
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")
    LOG_LEVEL: str = Field(default="INFO")

    # CORS Origins
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8000")

    # Security & JWT Tokens
    JWT_SECRET: str
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)

    # Database
    DATABASE_URL: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        if not v:
            raise ValueError("DATABASE_URL is not set.")

        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)

        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        return v

    # Local Screenshot directory
    SCREENSHOTS_DIR: str = Field(default="app/static/screenshots")

    # API Keys & Integrations
    SERPAPI_KEY: Optional[str] = Field(default=None)
    CLOUDINARY_CLOUD_NAME: Optional[str] = Field(default=None)
    CLOUDINARY_API_KEY: Optional[str] = Field(default=None)
    CLOUDINARY_API_SECRET: Optional[str] = Field(default=None)

    # AI Provider — Groq (primary)
    GROQ_API_KEY: Optional[str] = Field(default=None)
    GROQ_DEFAULT_MODEL: str = Field(default="llama-3.3-70b-versatile")
    GROQ_BASE_URL: str = Field(default="https://api.groq.com")

    # AI Provider — Pollinations AI (secondary fallback)
    POLLINATIONS_API_KEY: Optional[str] = Field(default=None)
    POLLINATIONS_AUDIT_MODEL: Optional[str] = Field(default=None)
    POLLINATIONS_GENERATION_MODEL: Optional[str] = Field(default=None)
    POLLINATIONS_BASE_URL: str = Field(default="https://text.pollinations.ai")

    # AI Provider — NVIDIA NIM (tertiary fallback)
    NVIDIA_API_KEY: Optional[str] = Field(default=None)
    NVIDIA_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1")
    NVIDIA_AUDIT_MODEL: str = Field(default="meta/llama-3.1-8b-instruct")
    NVIDIA_GENERATION_MODEL: str = Field(default="meta/llama-3.1-8b-instruct")

    # Frontend URL for preview/share links in outreach (set to Vercel deployment URL in Railway env)
    FRONTEND_URL: str = Field(default="https://lead-forge-oyjnslyea-ahsansagheer071-8737s-projects.vercel.app")


# Create settings instance
settings = Settings()

# Ensure screenshots directory exists
os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)