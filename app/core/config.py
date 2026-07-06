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

    # AI Provider
    GROQ_API_KEY: Optional[str] = Field(default=None)

    # Website Generation - Groq
    GROQ_DEFAULT_MODEL: str = Field(default="llama-3.3-70b-versatile")
    GROQ_BASE_URL: str = Field(default="https://api.groq.com/openai/v1")


# Create settings instance
settings = Settings()

# Ensure screenshots directory exists
os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)