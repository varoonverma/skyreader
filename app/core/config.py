"""
Configuration settings for the SkyReader TTY Message Parser.
"""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    # API settings
    app_name: str = "SkyReader - Qantas TTY Message Parser"
    app_version: str = "0.1.0"
    app_description: str = "API for parsing Qantas TTY messages using LLMs"

    # OpenAI settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    openai_temperature: float = Field(0.0, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(1000, env="OPENAI_MAX_TOKENS")

    # Parsing settings
    confidence_threshold: float = Field(0.8, env="CONFIDENCE_THRESHOLD")
    fallback_to_antlr: bool = Field(False, env="FALLBACK_TO_ANTLR")

    # Performance settings
    batch_size: int = Field(10, env="BATCH_SIZE")
    request_timeout: int = Field(30, env="REQUEST_TIMEOUT")

    # Security settings
    enable_cors: bool = Field(True, env="ENABLE_CORS")
    cors_origins: list = Field(["*"], env="CORS_ORIGINS")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()