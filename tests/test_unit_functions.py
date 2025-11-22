# -*- coding: utf-8 -*-
"""
Unit Tests fuer kritische Funktionen in main.py und gpt_analyze.py
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import patch

# Set test environment before imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["OPENAI_API_KEY"] = "test-api-key"


class TestMainHelpers:
    """Tests fuer Hilfsfunktionen in main.py"""

    def test_bool_env_true_values(self):
        """Test _bool_env erkennt verschiedene True-Werte"""
        from main import _bool_env

        with patch.dict(os.environ, {"TEST_VAR": "1"}):
            assert _bool_env("TEST_VAR") is True
        with patch.dict(os.environ, {"TEST_VAR": "true"}):
            assert _bool_env("TEST_VAR") is True
        with patch.dict(os.environ, {"TEST_VAR": "yes"}):
            assert _bool_env("TEST_VAR") is True
        with patch.dict(os.environ, {"TEST_VAR": "TRUE"}):
            assert _bool_env("TEST_VAR") is True
        with patch.dict(os.environ, {"TEST_VAR": "YES"}):
            assert _bool_env("TEST_VAR") is True

    def test_bool_env_false_values(self):
        """Test _bool_env erkennt False-Werte"""
        from main import _bool_env

        with patch.dict(os.environ, {"TEST_VAR": "0"}):
            assert _bool_env("TEST_VAR") is False
        with patch.dict(os.environ, {"TEST_VAR": "false"}):
            assert _bool_env("TEST_VAR") is False
        with patch.dict(os.environ, {"TEST_VAR": "no"}):
            assert _bool_env("TEST_VAR") is False
        with patch.dict(os.environ, {"TEST_VAR": ""}):
            assert _bool_env("TEST_VAR") is False

    def test_bool_env_default(self):
        """Test _bool_env nutzt Default-Wert"""
        from main import _bool_env

        # Variable nicht gesetzt -> Default
        result = _bool_env("NON_EXISTENT_VAR_12345", "1")
        assert result is True

        result = _bool_env("NON_EXISTENT_VAR_12345", "0")
        assert result is False

    def test_build_router_config_default(self):
        """Test _build_router_config liefert Standard-Router"""
        from main import _build_router_config

        with patch.dict(os.environ, {"ENABLE_ADMIN_ROUTES": "0", "ADMIN_ALLOW_RAW_SQL": "0"}):
            config = _build_router_config()
            # Mindestens 5 Standard-Router erwartet
            assert len(config) >= 5
            module_names = [c[0] for c in config]
            assert "routes.auth" in module_names
            assert "routes.briefings" in module_names
            assert "routes.analyze" in module_names
            assert "routes.report" in module_names
            assert "routes.smoke" in module_names

    def test_build_router_config_with_admin(self):
        """Test _build_router_config mit Admin-Routen aktiviert"""
        from main import _build_router_config

        with patch.dict(os.environ, {"ENABLE_ADMIN_ROUTES": "1", "ADMIN_ALLOW_RAW_SQL": "0"}):
            config = _build_router_config()
            module_names = [c[0] for c in config]
            assert "routes.admin" in module_names


class TestGptAnalyzeHelpers:
    """Tests fuer Hilfsfunktionen in gpt_analyze.py"""

    def test_ellipsize_short_string(self):
        """Test _ellipsize laesst kurze Strings unveraendert"""
        from gpt_analyze import _ellipsize

        result = _ellipsize("Kurzer Text", 50)
        assert result == "Kurzer Text"

    def test_ellipsize_long_string(self):
        """Test _ellipsize kuerzt lange Strings mit Ellipsis"""
        from gpt_analyze import _ellipsize

        long_text = "Dies ist ein sehr langer Text der gekuerzt werden muss"
        result = _ellipsize(long_text, 20)
        assert len(result) <= 20
        # Function uses Unicode ellipsis character
        assert result.endswith("...") or result.endswith("\u2026")

    def test_ellipsize_empty_string(self):
        """Test _ellipsize behandelt leere Strings"""
        from gpt_analyze import _ellipsize

        result = _ellipsize("", 10)
        assert result == ""

        result = _ellipsize(None, 10)
        assert result == ""

    def test_env_float_valid(self):
        """Test _env_float parsed Float-Werte korrekt"""
        from gpt_analyze import _env_float

        with patch.dict(os.environ, {"TEST_FLOAT": "3.14"}):
            result = _env_float("TEST_FLOAT", 0.0)
            assert result == 3.14

    def test_env_float_default(self):
        """Test _env_float nutzt Default bei fehlender Variable"""
        from gpt_analyze import _env_float

        result = _env_float("NON_EXISTENT_FLOAT", 2.5)
        assert result == 2.5

    def test_env_float_invalid(self):
        """Test _env_float nutzt Default bei ungueltigem Wert"""
        from gpt_analyze import _env_float

        with patch.dict(os.environ, {"TEST_FLOAT": "not_a_number"}):
            result = _env_float("TEST_FLOAT", 1.0)
            assert result == 1.0

    def test_env_int_valid(self):
        """Test _env_int parsed Integer-Werte korrekt"""
        from gpt_analyze import _env_int

        with patch.dict(os.environ, {"TEST_INT": "42"}):
            result = _env_int("TEST_INT", 0)
            assert result == 42

    def test_env_int_default(self):
        """Test _env_int nutzt Default bei fehlender Variable"""
        from gpt_analyze import _env_int

        result = _env_int("NON_EXISTENT_INT", 100)
        assert result == 100

    def test_is_nsfw_content_clean(self):
        """Test _is_nsfw_content erkennt sauberen Content"""
        from gpt_analyze import _is_nsfw_content

        result = _is_nsfw_content(
            "https://example.com",
            "Business Solutions",
            "Enterprise software for companies"
        )
        assert result is False

    def test_is_nsfw_content_blocked_domain(self):
        """Test _is_nsfw_content blockiert NSFW-Domains"""
        from gpt_analyze import _is_nsfw_content, ENABLE_NSFW_FILTER

        if not ENABLE_NSFW_FILTER:
            pytest.skip("NSFW filter disabled")

        result = _is_nsfw_content(
            "https://pornhub.com/video",
            "Some title",
            "Some description"
        )
        assert result is True

    def test_is_nsfw_content_blocked_keywords(self):
        """Test _is_nsfw_content blockiert NSFW-Keywords"""
        from gpt_analyze import _is_nsfw_content, ENABLE_NSFW_FILTER

        if not ENABLE_NSFW_FILTER:
            pytest.skip("NSFW filter disabled")

        result = _is_nsfw_content(
            "https://example.com",
            "XXX Content",
            "Adult material"
        )
        assert result is True

    def test_map_german_to_english_ai_strategy(self):
        """Test _map_german_to_english_keys mapped KI-Strategie korrekt"""
        from gpt_analyze import _map_german_to_english_keys

        # Test "ja" -> "yes"
        answers = {"roadmap_vorhanden": "ja"}
        result = _map_german_to_english_keys(answers)
        assert result["ai_strategy"] == "yes"

        # Test "teilweise" -> "in_progress"
        answers = {"roadmap_vorhanden": "teilweise"}
        result = _map_german_to_english_keys(answers)
        assert result["ai_strategy"] == "in_progress"

        # Test ohne Roadmap -> "no"
        answers = {}
        result = _map_german_to_english_keys(answers)
        assert result["ai_strategy"] == "no"

    def test_map_german_to_english_budget(self):
        """Test _map_german_to_english_keys mapped Budget korrekt"""
        from gpt_analyze import _map_german_to_english_keys

        budget_tests = [
            ("unter_2000", "under_10k"),
            ("2000_10000", "under_10k"),
            ("10000_50000", "10k-50k"),
            ("50000_100000", "50k-100k"),
            ("ueber_100000", "over_100k"),
        ]

        for german, english in budget_tests:
            answers = {"investitionsbudget": german}
            result = _map_german_to_english_keys(answers)
            assert result["budget"] == english, f"Failed for {german}"

    def test_map_german_to_english_gdpr(self):
        """Test _map_german_to_english_keys mapped DSGVO-Awareness korrekt"""
        from gpt_analyze import _map_german_to_english_keys

        # Mit Datenschutzbeauftragtem
        answers = {"datenschutzbeauftragter": "ja"}
        result = _map_german_to_english_keys(answers)
        assert result["gdpr_aware"] == "yes"

        # Ohne Datenschutz
        answers = {}
        result = _map_german_to_english_keys(answers)
        assert result["gdpr_aware"] == "no"


class TestScoreCalculation:
    """Tests fuer Score-Berechnung"""

    def test_calculate_realistic_score_empty(self):
        """Test Score-Berechnung mit leeren Antworten"""
        from gpt_analyze import _calculate_realistic_score

        result = _calculate_realistic_score({})
        assert "scores" in result
        assert "overall" in result["scores"]
        assert isinstance(result["scores"]["overall"], (int, float))

    def test_calculate_realistic_score_full(self):
        """Test Score-Berechnung mit vollstaendigen Antworten"""
        from gpt_analyze import _calculate_realistic_score

        answers = {
            "roadmap_vorhanden": "ja",
            "governance_richtlinien": "ja",
            "investitionsbudget": "50000_100000",
            "datenschutzbeauftragter": "ja",
            "technische_massnahmen": "alle",
            "folgenabschaetzung": "ja",
            "trainings_interessen": ["grundlagen", "prompting", "security"],
            "ki_kompetenz": "hoch",
            "zeitbudget": "ueber_10",
            "change_management": "hoch",
        }

        result = _calculate_realistic_score(answers)
        assert result["scores"]["overall"] > 0
        # Vollstaendige Antworten sollten hohen Score ergeben
        assert result["scores"]["governance"] > 10
        assert result["scores"]["security"] > 10


class TestJinjaRendering:
    """Tests fuer Jinja-Template-Rendering"""

    def test_ksj_render_string_simple(self):
        """Test einfaches Jinja-Rendering"""
        from gpt_analyze import ksj_render_string

        template = "Hallo {{ name }}!"
        result = ksj_render_string(template, {"name": "Welt"})
        assert result == "Hallo Welt!"

    def test_ksj_render_string_missing_var(self):
        """Test Rendering mit fehlender Variable"""
        from gpt_analyze import ksj_render_string

        template = "Wert: {{ missing_var }}"
        # Should not raise, just return empty or original
        result = ksj_render_string(template, {})
        assert isinstance(result, str)

    def test_ksj_render_string_no_template(self):
        """Test Rendering ohne Template-Syntax"""
        from gpt_analyze import ksj_render_string

        plain_text = "Einfacher Text ohne Variablen"
        result = ksj_render_string(plain_text, {"unused": "var"})
        assert result == plain_text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
