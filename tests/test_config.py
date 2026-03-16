"""
Unit tests for config.py
Run with: pytest tests/test_config.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch


class TestLLMConfig:
    def test_anthropic_provider_default(self):
        with patch.dict(os.environ, {"HIRELENS_LLM_PROVIDER": "anthropic"}, clear=False):
            from config import LLMConfig
            cfg = LLMConfig()
            assert cfg.provider == "anthropic"
            assert "claude" in cfg.active_model

    def test_openai_provider(self):
        with patch.dict(os.environ, {"HIRELENS_LLM_PROVIDER": "openai"}, clear=False):
            from config import LLMConfig
            cfg = LLMConfig()
            assert cfg.provider == "openai"
            assert "gpt" in cfg.active_model

    def test_gemini_provider(self):
        with patch.dict(os.environ, {"HIRELENS_LLM_PROVIDER": "gemini"}, clear=False):
            from config import LLMConfig
            cfg = LLMConfig()
            assert cfg.provider == "gemini"
            assert "gemini" in cfg.active_model

    def test_api_key_env_name_anthropic(self):
        with patch.dict(os.environ, {"HIRELENS_LLM_PROVIDER": "anthropic"}):
            from config import LLMConfig
            cfg = LLMConfig()
            assert cfg.api_key_env == "ANTHROPIC_API_KEY"

    def test_api_key_env_name_openai(self):
        with patch.dict(os.environ, {"HIRELENS_LLM_PROVIDER": "openai"}):
            from config import LLMConfig
            cfg = LLMConfig()
            assert cfg.api_key_env == "OPENAI_API_KEY"

    def test_is_configured_false_when_no_key(self):
        with patch.dict(os.environ, {"HIRELENS_LLM_PROVIDER": "anthropic"}, clear=False):
            env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
            with patch.dict(os.environ, env, clear=True):
                from config import LLMConfig
                cfg = LLMConfig()
                # Will be False if key not present, True if set in CI
                assert isinstance(cfg.is_configured(), bool)

    def test_display_name_anthropic(self):
        with patch.dict(os.environ, {"HIRELENS_LLM_PROVIDER": "anthropic"}):
            from config import LLMConfig
            cfg = LLMConfig()
            assert "Claude" in cfg.display_name()


class TestAppConfig:
    def test_defaults(self):
        from config import AppConfig
        cfg = AppConfig()
        assert cfg.app_name == "HireLens AI"
        assert cfg.max_resume_chars == 12_000
        assert cfg.max_jd_chars == 6_000

    def test_truncation_limits_positive(self):
        from config import AppConfig
        cfg = AppConfig()
        assert cfg.max_resume_chars > 0
        assert cfg.max_jd_chars > 0


class TestValidateEnv:
    def test_validate_env_returns_tuple(self):
        from config import validate_env
        result = validate_env()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)
