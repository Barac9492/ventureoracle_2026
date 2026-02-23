"""Configuration management using Pydantic Settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, YamlConfigSettingsSource
from typing import Tuple, Type


class Settings(BaseSettings):
    """Application settings loaded from environment variables, .env file, and settings.yaml."""

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        yaml_file="config/settings.yaml",
        yaml_file_encoding="utf-8"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()

