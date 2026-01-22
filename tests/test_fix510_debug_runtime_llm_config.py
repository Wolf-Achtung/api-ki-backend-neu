"""
FIX-510 CHANGE 3: Debug Runtime LLM Config Tests

Tests for runtime_llm_config in debug artifact (debug_503d_quick_wins_keys.json).

Goal: Add runtime configuration visibility for audit trail.
Expected fields: openai_model, openai_base_url, perplexity_model,
                 perplexity_endpoint, release_strict_mode, debug_render
"""
import pytest
import os


class TestFix510_RuntimeLlmConfigFunction:
    """Tests for _get_runtime_llm_config function."""

    def test_get_runtime_llm_config_exists(self):
        """_get_runtime_llm_config function should exist."""
        from services.debug_503d import _get_runtime_llm_config
        assert callable(_get_runtime_llm_config)

    def test_get_runtime_llm_config_returns_dict(self):
        """_get_runtime_llm_config should return a dictionary."""
        from services.debug_503d import _get_runtime_llm_config

        result = _get_runtime_llm_config()
        assert isinstance(result, dict)

    def test_runtime_config_has_openai_model(self):
        """Runtime config should include openai_model."""
        from services.debug_503d import _get_runtime_llm_config

        result = _get_runtime_llm_config()
        assert "openai_model" in result, "Should have openai_model key"

    def test_runtime_config_has_openai_base_url(self):
        """Runtime config should include openai_base_url."""
        from services.debug_503d import _get_runtime_llm_config

        result = _get_runtime_llm_config()
        assert "openai_base_url" in result, "Should have openai_base_url key"

    def test_runtime_config_has_perplexity_model(self):
        """Runtime config should include perplexity_model."""
        from services.debug_503d import _get_runtime_llm_config

        result = _get_runtime_llm_config()
        assert "perplexity_model" in result, "Should have perplexity_model key"

    def test_runtime_config_has_perplexity_endpoint(self):
        """Runtime config should include perplexity_endpoint."""
        from services.debug_503d import _get_runtime_llm_config

        result = _get_runtime_llm_config()
        # Check for either perplexity_endpoint or perplexity_base_url
        has_endpoint = "perplexity_endpoint" in result or "perplexity_base_url" in result
        assert has_endpoint, "Should have perplexity endpoint info"

    def test_runtime_config_has_release_strict_mode(self):
        """Runtime config should include release_strict_mode."""
        from services.debug_503d import _get_runtime_llm_config

        result = _get_runtime_llm_config()
        assert "release_strict_mode" in result, "Should have release_strict_mode key"

    def test_runtime_config_has_debug_render(self):
        """Runtime config should include debug_render."""
        from services.debug_503d import _get_runtime_llm_config

        result = _get_runtime_llm_config()
        assert "debug_render" in result, "Should have debug_render key"


class TestFix510_RuntimeConfigEnvironmentOverride:
    """Tests that runtime config respects environment variables."""

    def test_openai_model_from_env(self, monkeypatch):
        """openai_model should come from OPENAI_MODEL env var."""
        from services.debug_503d import _get_runtime_llm_config

        monkeypatch.setenv("OPENAI_MODEL", "gpt-4-turbo-test")
        result = _get_runtime_llm_config()
        assert result["openai_model"] == "gpt-4-turbo-test"

    def test_release_strict_mode_from_env(self, monkeypatch):
        """release_strict_mode should come from RELEASE_STRICT_MODE env var."""
        from services.debug_503d import _get_runtime_llm_config

        monkeypatch.setenv("RELEASE_STRICT_MODE", "1")
        result = _get_runtime_llm_config()
        assert result["release_strict_mode"] == "1"

    def test_perplexity_model_from_env(self, monkeypatch):
        """perplexity_model should come from PERPLEXITY_MODEL env var."""
        from services.debug_503d import _get_runtime_llm_config

        monkeypatch.setenv("PERPLEXITY_MODEL", "sonar-large-online")
        result = _get_runtime_llm_config()
        assert result["perplexity_model"] == "sonar-large-online"


class TestFix510_RuntimeConfigDefaults:
    """Tests for default values when env vars not set."""

    def test_openai_model_default(self, monkeypatch):
        """openai_model should have a sensible default."""
        from services.debug_503d import _get_runtime_llm_config

        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        result = _get_runtime_llm_config()
        # Should have a default value, not be empty
        assert result["openai_model"], "Should have default openai_model"

    def test_release_strict_mode_default(self, monkeypatch):
        """release_strict_mode should default to '0'."""
        from services.debug_503d import _get_runtime_llm_config

        monkeypatch.delenv("RELEASE_STRICT_MODE", raising=False)
        result = _get_runtime_llm_config()
        assert result["release_strict_mode"] == "0", "Should default to '0'"


class TestFix510_DebugJsonIncludesRuntimeConfig:
    """Tests that debug JSON builder includes runtime config."""

    def test_build_quick_wins_keys_json_has_runtime_config(self):
        """_build_quick_wins_keys_json should include runtime_llm_config."""
        import json
        from services.debug_503d import _build_quick_wins_keys_json

        # Call with minimal valid sections data
        sections = {
            "QUICK_WINS_HTML": "<div class='quick-win'>Test</div>",
            "QUICK_WINS_HTML_LEFT": "",
            "QUICK_WINS_HTML_RIGHT": "",
            "quick_wins": ""
        }
        result_json = _build_quick_wins_keys_json(sections)
        result = json.loads(result_json)

        assert isinstance(result, dict)
        assert "runtime_llm_config" in result, \
            "_build_quick_wins_keys_json should include runtime_llm_config"

    def test_runtime_config_in_json_has_required_fields(self):
        """runtime_llm_config in debug JSON should have required fields."""
        import json
        from services.debug_503d import _build_quick_wins_keys_json

        sections = {
            "QUICK_WINS_HTML": "<div>Test</div>",
            "QUICK_WINS_HTML_LEFT": "",
            "QUICK_WINS_HTML_RIGHT": "",
            "quick_wins": ""
        }
        result_json = _build_quick_wins_keys_json(sections)
        result = json.loads(result_json)

        runtime_config = result.get("runtime_llm_config", {})
        required_fields = [
            "openai_model",
            "perplexity_model",
            "release_strict_mode",
            "debug_render"
        ]

        for field in required_fields:
            assert field in runtime_config, \
                f"runtime_llm_config should have {field}"
