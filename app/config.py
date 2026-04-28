"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.2
    max_agent_iterations: int = 10

    # Database
    database_url: str = "sqlite:///./agent.db"

    # Rate Limiting
    rate_limit: str = "30/minute"

    # Retry
    max_retries: int = 3
    retry_backoff_base: int = 2

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]

    # Tools
    search_api_key: str = ""
    weather_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
