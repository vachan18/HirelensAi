"""
HireLens AI — Central Configuration
All settings in one place. Override via environment variables or .env file.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Literal
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────
# LLM PROVIDER CONFIGS
# ─────────────────────────────────────────────

LLMProvider = Literal["anthropic", "openai", "gemini"]


@dataclass
class LLMConfig:
    """LLM provider and model settings."""

    provider: LLMProvider = field(
        default_factory=lambda: os.getenv("HIRELENS_LLM_PROVIDER", "anthropic")  # type: ignore
    )

    # Model names per provider — can be overridden via env
    anthropic_model: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")
    )
    openai_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o")
    )
    gemini_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini/gemini-1.5-pro")
    )

    @property
    def active_model(self) -> str:
        """Return the fully qualified model string for the active provider."""
        mapping = {
            "anthropic": f"anthropic/{self.anthropic_model}",
            "openai": self.openai_model,
            "gemini": self.gemini_model,
        }
        return mapping[self.provider]

    @property
    def api_key_env(self) -> str:
        """Return the env var name for the active provider's API key."""
        return {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
        }[self.provider]

    @property
    def api_key(self) -> str | None:
        return os.getenv(self.api_key_env)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def display_name(self) -> str:
        return {
            "anthropic": f"Claude ({self.anthropic_model})",
            "openai": f"OpenAI ({self.openai_model})",
            "gemini": f"Gemini ({self.gemini_model})",
        }[self.provider]


# ─────────────────────────────────────────────
# APP SETTINGS
# ─────────────────────────────────────────────

@dataclass
class AppConfig:
    """General application settings."""

    app_name: str = "HireLens AI"
    app_version: str = "1.0.0"
    app_tagline: str = "Multi-Agent Job Rejection Analyzer"

    # Analysis defaults
    default_brutal_mode: bool = False
    max_resume_chars: int = 12_000   # Truncate very long resumes
    max_jd_chars: int = 6_000        # Truncate very long JDs

    # Crew settings
    crew_verbose: bool = field(
        default_factory=lambda: os.getenv("CREW_VERBOSE", "false").lower() == "true"
    )
    max_retries: int = 2

    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    log_to_file: bool = field(
        default_factory=lambda: os.getenv("LOG_TO_FILE", "false").lower() == "true"
    )
    log_file_path: str = "hirelens.log"


# ─────────────────────────────────────────────
# GLOBAL SINGLETONS
# ─────────────────────────────────────────────

llm_config = LLMConfig()
app_config = AppConfig()


def get_llm_config() -> LLMConfig:
    return llm_config


def get_app_config() -> AppConfig:
    return app_config


def validate_env() -> tuple[bool, list[str]]:
    """
    Validate that required environment variables are present.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    cfg = get_llm_config()

    if not cfg.is_configured():
        errors.append(
            f"Missing API key: set {cfg.api_key_env} in your .env file. "
            f"Current provider: {cfg.provider}"
        )

    return len(errors) == 0, errors
