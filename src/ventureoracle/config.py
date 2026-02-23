"""Configuration management using Pydantic Settings."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # API Keys
    anthropic_api_key: str = ""
    brave_api_key: str = ""

    # Database
    database_url: str = "sqlite:///data/ventureoracle.db"

    # Claude model settings
    claude_model: str = "claude-sonnet-4-20250514"
    claude_model_heavy: str = "claude-opus-4-20250514"
    claude_max_tokens: int = 4096

    # Discovery settings
    discovery_max_results: int = 20
    discovery_relevance_threshold: float = 0.5

    # Project paths
    project_root: Path = Path(".")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
