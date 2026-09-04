# -*- coding: utf-8 -*-
"""
FIX-506 TASK 1: Test wettbewerb_benchmark template with score variables.

Ensures the template renders without fallback when score variables are
provided, missing, or set to 0.
"""

import pytest
from unittest.mock import patch
import os


class TestWettbewerbBenchmarkTemplate:
    """Tests for wettbewerb_benchmark template score variable handling."""

    def test_render_with_all_scores(self, tmp_path):
        """Template renders correctly with all score variables provided."""
        from services.prompt_loader import load_prompt, _set_include_stack

        # Reset include stack
        _set_include_stack([])

        vars_dict = {
            "score_gesamt": 75,
            "score_befaehigung": 70,
            "score_governance": 65,
            "score_sicherheit": 68,
            "score_nutzen": 72,
            "BRANCHE_LABEL": "IT & Software",
            "report_date": "Januar 2026",
            "COMPANY_SIZE": "team",
            "UNTERNEHMENSGROESSE_LABEL": "Kleines Team",
        }

        result = load_prompt("wettbewerb_benchmark", lang="de", vars_dict=vars_dict)

        # Should contain rendered scores
        assert "75" in result  # score_gesamt
        assert "70" in result  # score_befaehigung
        assert "IT & Software" in result
        assert "über dem Richtwert" in result  # 75 > 65

    def test_render_with_missing_scores_uses_defaults(self, tmp_path):
        """Template renders without error when scores are missing (uses defaults)."""
        from services.prompt_loader import load_prompt, _set_include_stack

        _set_include_stack([])

        vars_dict = {
            # No score variables provided
            "BRANCHE_LABEL": "Marketing",
            "report_date": "Februar 2026",
            "COMPANY_SIZE": "solo",
            "UNTERNEHMENSGROESSE_LABEL": "Einzelperson",
        }

        # Should NOT raise exception
        result = load_prompt("wettbewerb_benchmark", lang="de", vars_dict=vars_dict)

        # Should render with default(0) values
        assert "unter dem Richtwert" in result  # 0 < 65
        assert "Marketing" in result

    def test_render_with_zero_scores(self, tmp_path):
        """Template handles zero scores correctly."""
        from services.prompt_loader import load_prompt, _set_include_stack

        _set_include_stack([])

        vars_dict = {
            "score_gesamt": 0,
            "score_befaehigung": 0,
            "score_governance": 0,
            "score_sicherheit": 0,
            "score_nutzen": 0,
            "BRANCHE_LABEL": "Handel",
            "report_date": "März 2026",
            "COMPANY_SIZE": "kmu",
            "UNTERNEHMENSGROESSE_LABEL": "KMU",
        }

        result = load_prompt("wettbewerb_benchmark", lang="de", vars_dict=vars_dict)

        # 0 should be displayed and classified correctly
        assert "unter dem Richtwert" in result
        assert "Handel" in result

    def test_render_with_empty_string_scores(self, tmp_path):
        """Template handles empty string scores using defaults."""
        from services.prompt_loader import load_prompt, _set_include_stack

        _set_include_stack([])

        vars_dict = {
            "score_gesamt": "",
            "score_befaehigung": "",
            "score_governance": "",
            "score_sicherheit": "",
            "score_nutzen": "",
            "BRANCHE_LABEL": "Gesundheit",
            "report_date": "April 2026",
            "COMPANY_SIZE": "team",
            "UNTERNEHMENSGROESSE_LABEL": "Team",
        }

        # Empty strings should use default(0) - may raise on comparison
        # The important thing is no Jinja2 UndefinedError
        result = load_prompt("wettbewerb_benchmark", lang="de", vars_dict=vars_dict)
        assert "Gesundheit" in result

    def test_english_template_with_scores(self):
        """English competition_benchmark template renders correctly."""
        from services.prompt_loader import load_prompt, _set_include_stack

        _set_include_stack([])

        vars_dict = {
            "score_gesamt": 85,
            "score_befaehigung": 80,
            "score_governance": 75,
            "score_sicherheit": 78,
            "score_nutzen": 82,
            "BRANCHE_LABEL": "Finance",
            "report_date": "January 2026",
            "COMPANY_SIZE": "kmu",
            "UNTERNEHMENSGROESSE_LABEL": "SME",
        }

        result = load_prompt("competition_benchmark", lang="en", vars_dict=vars_dict)

        # English template should have EN text
        assert "well above the guide value" in result or "above the guide value" in result
        assert "Finance" in result

    def test_strict_mode_no_fallback_with_valid_scores(self):
        """With STRICT_MODE, valid scores should not trigger fallback."""
        from services.prompt_loader import load_prompt, _set_include_stack

        _set_include_stack([])

        vars_dict = {
            "score_gesamt": 70,
            "score_befaehigung": 72,
            "score_governance": 60,
            "score_sicherheit": 65,
            "score_nutzen": 75,
            "BRANCHE_LABEL": "Produktion",
            "report_date": "Mai 2026",
            "COMPANY_SIZE": "kmu",
            "UNTERNEHMENSGROESSE_LABEL": "KMU",
        }

        with patch.dict(os.environ, {"RELEASE_STRICT_MODE": "1"}):
            # Should not raise RuntimeError
            result = load_prompt(
                "wettbewerb_benchmark", lang="de", vars_dict=vars_dict
            )
            assert "70" in result
            assert "über dem Richtwert" in result


class TestScoreConditionalLogic:
    """Tests for score comparison logic in templates."""

    def test_high_score_classification(self):
        """Scores above Top 10% threshold are classified correctly."""
        from services.prompt_loader import load_prompt, _set_include_stack

        _set_include_stack([])

        vars_dict = {
            "score_gesamt": 90,  # > 82 (Top 10%)
            "score_befaehigung": 90,  # > 85
            "score_governance": 85,  # > 78
            "score_sicherheit": 85,  # > 80
            "score_nutzen": 92,  # > 88
            "BRANCHE_LABEL": "Tech",
            "report_date": "2026",
            "COMPANY_SIZE": "team",
            "UNTERNEHMENSGROESSE_LABEL": "Team",
        }

        result = load_prompt("wettbewerb_benchmark", lang="de", vars_dict=vars_dict)
        assert "deutlich über dem Richtwert" in result

    def test_medium_score_classification(self):
        """Scores between average and Top 10% are classified correctly."""
        from services.prompt_loader import load_prompt, _set_include_stack

        _set_include_stack([])

        vars_dict = {
            "score_gesamt": 75,  # > 65, < 82
            "score_befaehigung": 75,
            "score_governance": 65,
            "score_sicherheit": 70,
            "score_nutzen": 78,
            "BRANCHE_LABEL": "Beratung",
            "report_date": "2026",
            "COMPANY_SIZE": "solo",
            "UNTERNEHMENSGROESSE_LABEL": "Solo",
        }

        result = load_prompt("wettbewerb_benchmark", lang="de", vars_dict=vars_dict)
        assert "über dem Richtwert" in result

    def test_low_score_classification(self):
        """Scores below average are classified correctly."""
        from services.prompt_loader import load_prompt, _set_include_stack

        _set_include_stack([])

        vars_dict = {
            "score_gesamt": 50,  # < 65
            "score_befaehigung": 55,
            "score_governance": 45,
            "score_sicherheit": 50,
            "score_nutzen": 60,
            "BRANCHE_LABEL": "Retail",
            "report_date": "2026",
            "COMPANY_SIZE": "kmu",
            "UNTERNEHMENSGROESSE_LABEL": "KMU",
        }

        result = load_prompt("wettbewerb_benchmark", lang="de", vars_dict=vars_dict)
        assert "unter dem Richtwert" in result
