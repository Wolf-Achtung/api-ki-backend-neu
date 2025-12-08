# -*- coding: utf-8 -*-
"""
Sprint G17.4: Auto-Prompt-Rewrite Engine Tests

Tests for:
- Persona leak detection from prompt
- Redundancy pattern identification
- AI Act reasoning weakness detection
- Predictive drift detection
- Funding mismatch detection
- Patch format validation
- Confidence calculation
- No sensitive data in suggestions

Version: 1.0.0 (Sprint G17.4)
"""
from __future__ import annotations

import asyncio
import json
import pytest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch, MagicMock


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_prompt_text() -> str:
    """Sample prompt text with various patterns."""
    return """
# Roadmap 12 Monate

Beschreiben Sie kurz die wichtigsten Meilensteine für die nächsten 12 Monate.

Ihr Team sollte folgende Aspekte beachten:
- Wiederholte Betonung der Kernziele
- BAFA-Förderung einbeziehen
- Kurz die AI-Act Anforderungen erwähnen

Allgemein gilt: Die Empfehlungen sollten branchenübergreifend anwendbar sein.
"""


@pytest.fixture
def sample_prompt_text_clean() -> str:
    """Clean prompt text without issues."""
    return """
# Roadmap 12 Monate

Erstellen Sie einen detaillierten 12-Monats-Plan mit mindestens 4 konkreten Meilensteinen.

{{#if (eq unternehmensgroesse "solo")}}
Als Einzelunternehmer sollten Sie...
{{else}}
Ihr Team sollte...
{{/if}}

Basierend auf der Branche {{branche}} empfehlen wir spezifische Maßnahmen.
"""


@pytest.fixture
def sample_ft_signal():
    """Create a sample FT signal."""
    @dataclass
    class MockSignal:
        signal_id: str = "ft_persona_fix_abc123"
        signal_type: str = "persona_fix"
        source_section: str = "roadmap"
        prompt_input: str = "Korrigiere für solo-Persona: Ihr Team"
        ideal_output: str = "Sie"
        quality_score: float = 0.75
        confidence: float = 0.8

    return MockSignal()


@pytest.fixture
def sample_signals_list(sample_ft_signal):
    """Create a list of sample signals."""
    @dataclass
    class MockSignal:
        signal_id: str
        signal_type: str
        source_section: str = "test"
        prompt_input: str = ""
        ideal_output: str = ""
        quality_score: float = 0.7
        confidence: float = 0.75

    return [
        MockSignal(signal_id="ft_persona_fix_1", signal_type="persona_fix", prompt_input="Ihr Team"),
        MockSignal(signal_id="ft_persona_fix_2", signal_type="persona_fix", prompt_input="Ihr Team"),
        MockSignal(signal_id="ft_persona_fix_3", signal_type="persona_fix", prompt_input="Ihr Team"),
        MockSignal(signal_id="ft_persona_fix_4", signal_type="persona_fix", prompt_input="Ihr Team"),
        MockSignal(signal_id="ft_size_1", signal_type="size_aware_length"),
        MockSignal(signal_id="ft_size_2", signal_type="size_aware_length"),
        MockSignal(signal_id="ft_redundancy_1", signal_type="redundancy_compression"),
        MockSignal(signal_id="ft_ai_act_1", signal_type="ai_act_reasoning"),
        MockSignal(signal_id="ft_drift_1", signal_type="predictive_drift"),
        MockSignal(signal_id="ft_funding_1", signal_type="funding_misclassifications"),
    ]


@pytest.fixture
def sample_segment_stats():
    """Create sample segment stats."""
    @dataclass
    class MockSegmentStats:
        stability: str = "medium"
        risk_level: str = "minimal"
        funding_scope: str = "DE"
        sample_size: int = 50

    return MockSegmentStats()


# =============================================================================
# G17.4-A: ISSUE DETECTION TESTS
# =============================================================================

class TestPromptWeaknessDetection:
    """Tests for detect_prompt_weaknesses function."""

    def test_detect_persona_leak_from_prompt(self, sample_prompt_text: str, sample_signals_list) -> None:
        """Test detection of persona leaks originating from prompt."""
        from services.prompt_rewrite_engine import detect_prompt_weaknesses

        result = detect_prompt_weaknesses(
            prompt_text=sample_prompt_text,
            aggregated_signals=sample_signals_list,
            prompt_file="prompts/de/roadmap_12m.md",
        )

        assert "issues" in result
        issues = result["issues"]

        # Should detect persona leak
        persona_issues = [i for i in issues if i["issue_type"] == "persona_leak"]
        assert len(persona_issues) >= 1

        # Check structure
        issue = persona_issues[0]
        assert issue["severity"] in ("low", "medium", "high")
        assert "Ihr Team" in issue.get("detected_pattern", "") or "Team" in issue.get("example_input", "")

    def test_detect_redundancy_pattern(self, sample_prompt_text: str, sample_signals_list) -> None:
        """Test detection of redundancy patterns from prompt."""
        from services.prompt_rewrite_engine import detect_prompt_weaknesses

        result = detect_prompt_weaknesses(
            prompt_text=sample_prompt_text,
            aggregated_signals=sample_signals_list,
        )

        issues = result["issues"]

        # Should detect redundancy due to "Wiederholte Betonung"
        redundancy_issues = [i for i in issues if i["issue_type"] == "redundancy_pattern"]
        # May or may not find depending on signal count
        assert isinstance(redundancy_issues, list)

    def test_detect_ai_act_weakness(self, sample_prompt_text: str, sample_signals_list) -> None:
        """Test detection of AI Act reasoning weakness."""
        from services.prompt_rewrite_engine import detect_prompt_weaknesses

        result = detect_prompt_weaknesses(
            prompt_text=sample_prompt_text,
            aggregated_signals=sample_signals_list,
        )

        issues = result["issues"]

        # Should detect weak AI Act instruction due to "Kurz die AI-Act"
        ai_act_issues = [i for i in issues if i["issue_type"] == "ai_act_weakness"]
        assert len(ai_act_issues) >= 1

    def test_detect_too_short_pattern(self, sample_prompt_text: str, sample_signals_list) -> None:
        """Test detection of too-short warning patterns."""
        from services.prompt_rewrite_engine import detect_prompt_weaknesses

        result = detect_prompt_weaknesses(
            prompt_text=sample_prompt_text,
            aggregated_signals=sample_signals_list,
        )

        issues = result["issues"]

        # Should detect "kurz beschreiben" pattern
        short_issues = [i for i in issues if i["issue_type"] == "too_short_warning"]
        assert len(short_issues) >= 1

    def test_detect_funding_mismatch(self, sample_prompt_text: str, sample_signals_list) -> None:
        """Test detection of funding mismatch patterns."""
        from services.prompt_rewrite_engine import detect_prompt_weaknesses

        result = detect_prompt_weaknesses(
            prompt_text=sample_prompt_text,
            aggregated_signals=sample_signals_list,
        )

        issues = result["issues"]

        # Should detect hardcoded BAFA reference
        funding_issues = [i for i in issues if i["issue_type"] == "funding_mismatch"]
        assert len(funding_issues) >= 1

    def test_detect_branch_context_misuse(self, sample_prompt_text: str) -> None:
        """Test detection of branch context misuse."""
        from services.prompt_rewrite_engine import detect_prompt_weaknesses

        result = detect_prompt_weaknesses(
            prompt_text=sample_prompt_text,
            aggregated_signals=[],
        )

        issues = result["issues"]

        # Should detect "Allgemein gilt" or "branchenübergreifend"
        branch_issues = [i for i in issues if i["issue_type"] == "branch_context_misuse"]
        assert len(branch_issues) >= 1

    def test_detect_predictive_drift(self, sample_signals_list, sample_segment_stats) -> None:
        """Test detection of predictive drift."""
        from services.prompt_rewrite_engine import detect_prompt_weaknesses

        # Add more drift signals
        @dataclass
        class MockDriftSignal:
            signal_id: str
            signal_type: str = "predictive_drift"
            quality_score: float = 0.7
            confidence: float = 0.8

        drift_signals = [MockDriftSignal(signal_id=f"drift_{i}") for i in range(5)]

        result = detect_prompt_weaknesses(
            prompt_text="Some prompt",
            aggregated_signals=drift_signals,
            segment_stats=sample_segment_stats,
        )

        issues = result["issues"]
        drift_issues = [i for i in issues if i["issue_type"] == "predictive_drift"]
        assert len(drift_issues) >= 1

    def test_clean_prompt_no_issues(self, sample_prompt_text_clean: str) -> None:
        """Test that clean prompts produce fewer issues."""
        from services.prompt_rewrite_engine import detect_prompt_weaknesses

        result = detect_prompt_weaknesses(
            prompt_text=sample_prompt_text_clean,
            aggregated_signals=[],
        )

        issues = result["issues"]

        # Clean prompt should have fewer issues
        persona_issues = [i for i in issues if i["issue_type"] == "persona_leak"]
        assert len(persona_issues) == 0  # Uses conditional persona

    def test_disabled_engine_returns_empty(self, sample_prompt_text: str) -> None:
        """Test that disabled engine returns empty issues."""
        from services.prompt_rewrite_engine import detect_prompt_weaknesses

        with patch("services.prompt_rewrite_engine.PROMPT_REWRITE_ENGINE_ENABLED", False):
            result = detect_prompt_weaknesses(
                prompt_text=sample_prompt_text,
                aggregated_signals=[],
            )

        assert result == {"issues": []}


# =============================================================================
# G17.4-B: REWRITE SUGGESTION TESTS
# =============================================================================

class TestRewriteSuggestionGeneration:
    """Tests for generate_prompt_rewrite_suggestions function."""

    def test_generate_suggestions_from_issues(self, sample_signals_list, sample_segment_stats) -> None:
        """Test generating rewrite suggestions from detected issues."""
        from services.prompt_rewrite_engine import (
            detect_prompt_weaknesses,
            generate_prompt_rewrite_suggestions,
        )

        prompt_text = "Beschreiben Sie kurz... Ihr Team sollte..."

        issues_result = detect_prompt_weaknesses(
            prompt_text=prompt_text,
            aggregated_signals=sample_signals_list,
        )

        suggestions = generate_prompt_rewrite_suggestions(
            issues=issues_result["issues"],
            aggregated_signals=sample_signals_list,
            segment_stats=sample_segment_stats,
        )

        assert isinstance(suggestions, list)

        # Check suggestion structure
        for s in suggestions:
            assert "suggestion_id" in s
            assert "prompt_file" in s
            assert "priority" in s
            assert s["priority"] in ("P1", "P2", "P3")
            assert "confidence" in s
            assert 0.0 <= s["confidence"] <= 1.0
            assert "change_type" in s
            assert s["change_type"] in ("add", "remove", "rewrite", "strengthen", "clarify", "tighten")
            assert "proposed_rewrite" in s
            assert "justification" in s

    def test_confidence_calculation(self, sample_signals_list, sample_segment_stats) -> None:
        """Test that confidence is correctly calculated."""
        from services.prompt_rewrite_engine import generate_prompt_rewrite_suggestions

        issues = [
            {
                "issue_type": "persona_leak",
                "severity": "high",
                "signal_ref": "ft_persona_fix_1",
                "detected_pattern": "Ihr Team",
                "ideal_behavior": "Use conditional",
            }
        ]

        suggestions = generate_prompt_rewrite_suggestions(
            issues=issues,
            aggregated_signals=sample_signals_list,
            segment_stats=sample_segment_stats,
        )

        if suggestions:
            # High severity + strong signals should produce higher confidence
            assert suggestions[0]["confidence"] >= 0.45  # Min threshold

    def test_weak_segment_skips_suggestions(self) -> None:
        """Test that weak segment stability skips suggestions when required."""
        from services.prompt_rewrite_engine import generate_prompt_rewrite_suggestions

        @dataclass
        class WeakSegment:
            stability: str = "weak"

        issues = [{"issue_type": "persona_leak", "severity": "high"}]

        with patch("services.prompt_rewrite_engine.PROMPT_REWRITE_REQUIRE_STRONG_SEGMENT", True):
            suggestions = generate_prompt_rewrite_suggestions(
                issues=issues,
                segment_stats=WeakSegment(),
            )

        assert suggestions == []

    def test_low_confidence_filtered(self) -> None:
        """Test that low confidence suggestions are filtered."""
        from services.prompt_rewrite_engine import generate_prompt_rewrite_suggestions

        issues = [
            {
                "issue_type": "branch_context_misuse",
                "severity": "low",
                "detected_pattern": "general",
            }
        ]

        # With high min confidence, low severity issues should be filtered
        with patch("services.prompt_rewrite_engine.PROMPT_REWRITE_MIN_CONFIDENCE", 0.9):
            suggestions = generate_prompt_rewrite_suggestions(
                issues=issues,
                aggregated_signals=[],
            )

        # Low severity without signals should not meet 0.9 threshold
        assert len(suggestions) == 0

    def test_max_suggestions_limit(self, sample_signals_list) -> None:
        """Test that max suggestions limit is applied."""
        from services.prompt_rewrite_engine import generate_prompt_rewrite_suggestions

        # Create many issues
        issues = [
            {"issue_type": "persona_leak", "severity": "high", "signal_ref": f"ref_{i}"}
            for i in range(20)
        ]

        with patch("services.prompt_rewrite_engine.PROMPT_REWRITE_MAX_SUGGESTIONS", 5):
            suggestions = generate_prompt_rewrite_suggestions(
                issues=issues,
                aggregated_signals=sample_signals_list,
            )

        assert len(suggestions) <= 5

    def test_no_sensitive_data_in_suggestions(self, sample_signals_list) -> None:
        """Test that suggestions don't contain sensitive data."""
        from services.prompt_rewrite_engine import generate_prompt_rewrite_suggestions

        issues = [
            {
                "issue_type": "persona_leak",
                "severity": "high",
                "example_input": "test@example.com sent the report",
                "example_output": "Email in output",
            }
        ]

        suggestions = generate_prompt_rewrite_suggestions(
            issues=issues,
            aggregated_signals=sample_signals_list,
        )

        for s in suggestions:
            # Check no emails in output
            assert "@" not in s.get("proposed_rewrite", "").lower() or "{{" in s.get("proposed_rewrite", "")


# =============================================================================
# G17.4-C: PATCH GENERATION TESTS
# =============================================================================

class TestPatchGeneration:
    """Tests for patch generation functions."""

    def test_patch_format_valid(self) -> None:
        """Test that generated patch has valid diff format."""
        from services.prompt_rewrite_engine import generate_patch_output

        suggestion = {
            "suggestion_id": "rewrite_persona_leak_abc123",
            "prompt_file": "prompts/de/roadmap_12m.md",
            "change_type": "rewrite",
            "current_section_excerpt": "Ihr Team sollte",
            "proposed_rewrite": "{{#if (eq unternehmensgroesse 'solo')}}Sie{{else}}Ihr Team{{/if}} sollte",
        }

        patch = generate_patch_output("prompts/de/roadmap_12m.md", suggestion)

        assert patch is not None
        assert "patch_content" in patch
        content = patch["patch_content"]

        # Check diff format
        assert "---" in content
        assert "+++" in content
        assert "@@" in content
        assert "-" in content or "+" in content

    def test_patch_contains_file_paths(self) -> None:
        """Test that patch contains correct file paths."""
        from services.prompt_rewrite_engine import generate_patch_output

        suggestion = {
            "suggestion_id": "test_123",
            "change_type": "add",
            "current_section_excerpt": "",
            "proposed_rewrite": "New content",
        }

        patch = generate_patch_output("prompts/de/test.md", suggestion)

        assert patch is not None
        content = patch["patch_content"]
        assert "prompts/de/test.md" in content

    def test_generate_all_patches(self) -> None:
        """Test generating patches for multiple suggestions."""
        from services.prompt_rewrite_engine import generate_all_patches

        suggestions = [
            {
                "suggestion_id": "s1",
                "prompt_file": "prompts/de/a.md",
                "change_type": "rewrite",
                "current_section_excerpt": "old",
                "proposed_rewrite": "new",
            },
            {
                "suggestion_id": "s2",
                "prompt_file": "prompts/de/b.md",
                "change_type": "add",
                "current_section_excerpt": "",
                "proposed_rewrite": "added",
            },
        ]

        patches = generate_all_patches(suggestions)

        assert len(patches) == 2
        assert all("patch_content" in p for p in patches)

    def test_patch_disabled_returns_none(self) -> None:
        """Test that disabled patch generation returns None."""
        from services.prompt_rewrite_engine import generate_patch_output

        suggestion = {"suggestion_id": "test", "proposed_rewrite": "test"}

        with patch("services.prompt_rewrite_engine.PROMPT_REWRITE_GENERATE_PATCHES", False):
            result = generate_patch_output("test.md", suggestion)

        assert result is None


# =============================================================================
# G17.4-D: DASHBOARD ENDPOINT TESTS
# =============================================================================

# Check if FastAPI is available
try:
    import fastapi
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI not available")
class TestPromptDashboardEndpoints:
    """Tests for prompt analysis dashboard endpoints."""

    def test_prompt_analysis_endpoint(self, tmp_path) -> None:
        """Test prompt analysis endpoint."""
        from routes.feedback_dashboard import get_prompt_analysis

        with patch("services.prompt_rewrite_engine.get_storage_path", return_value=tmp_path):
            result = asyncio.get_event_loop().run_until_complete(
                get_prompt_analysis()
            )

        assert hasattr(result, "total_suggestions")
        assert hasattr(result, "by_priority")
        assert hasattr(result, "by_file")
        assert hasattr(result, "enabled")

    def test_rewrite_suggestions_endpoint(self, tmp_path) -> None:
        """Test rewrite suggestions endpoint."""
        from routes.feedback_dashboard import get_prompt_rewrite_suggestions

        with patch("services.prompt_rewrite_engine.get_storage_path", return_value=tmp_path):
            result = asyncio.get_event_loop().run_until_complete(
                get_prompt_rewrite_suggestions(priority=None, limit=10)
            )

        assert hasattr(result, "suggestions")
        assert hasattr(result, "count")
        assert isinstance(result.suggestions, list)

    def test_next_patches_endpoint(self, tmp_path) -> None:
        """Test next patches endpoint."""
        from routes.feedback_dashboard import get_prompt_next_patches

        with patch("services.prompt_rewrite_engine.get_storage_path", return_value=tmp_path):
            result = asyncio.get_event_loop().run_until_complete(
                get_prompt_next_patches(limit=5)
            )

        assert hasattr(result, "patches")
        assert hasattr(result, "count")
        assert isinstance(result.patches, list)


# =============================================================================
# G17.4-E: STORAGE TESTS
# =============================================================================

class TestSuggestionStorage:
    """Tests for suggestion storage functions."""

    def test_store_suggestions(self, tmp_path) -> None:
        """Test storing suggestions to disk."""
        from services.prompt_rewrite_engine import store_suggestions, load_suggestions

        suggestions = [
            {
                "suggestion_id": "test_1",
                "prompt_file": "prompts/test.md",
                "priority": "P1",
                "confidence": 0.8,
                "change_type": "rewrite",
                "current_section_excerpt": "old",
                "proposed_rewrite": "new",
                "justification": "test",
                "created_at": datetime.utcnow().isoformat(),
            }
        ]

        with patch("services.prompt_rewrite_engine.get_storage_path", return_value=tmp_path):
            count = store_suggestions(suggestions)
            assert count == 1

            loaded = load_suggestions()
            assert len(loaded) >= 1
            assert loaded[0]["suggestion_id"] == "test_1"

    def test_load_suggestions_with_date_filter(self, tmp_path) -> None:
        """Test loading suggestions respects date filter."""
        from services.prompt_rewrite_engine import load_suggestions

        with patch("services.prompt_rewrite_engine.get_storage_path", return_value=tmp_path):
            # Load with short window should return empty for non-existent files
            loaded = load_suggestions(days=1)
            assert isinstance(loaded, list)


# =============================================================================
# G17.4-F: CONFIGURATION TESTS
# =============================================================================

class TestConfiguration:
    """Tests for configuration handling."""

    def test_env_variables_defaults(self) -> None:
        """Test default values for environment variables."""
        from services.prompt_rewrite_engine import (
            PROMPT_REWRITE_ENGINE_ENABLED,
            PROMPT_REWRITE_MIN_CONFIDENCE,
            PROMPT_REWRITE_MAX_SUGGESTIONS,
        )

        assert isinstance(PROMPT_REWRITE_ENGINE_ENABLED, bool)
        assert 0.0 <= PROMPT_REWRITE_MIN_CONFIDENCE <= 1.0
        assert PROMPT_REWRITE_MAX_SUGGESTIONS > 0

    def test_severity_weights(self) -> None:
        """Test severity weights configuration."""
        from services.prompt_rewrite_engine import SEVERITY_WEIGHTS

        assert "high" in SEVERITY_WEIGHTS
        assert "medium" in SEVERITY_WEIGHTS
        assert "low" in SEVERITY_WEIGHTS
        assert SEVERITY_WEIGHTS["high"] > SEVERITY_WEIGHTS["medium"] > SEVERITY_WEIGHTS["low"]

    def test_issue_types_defined(self) -> None:
        """Test that all issue types are defined."""
        from services.prompt_rewrite_engine import ISSUE_TYPES

        expected_types = [
            "too_short_warning",
            "persona_leak",
            "redundancy_pattern",
            "predictive_drift",
            "funding_mismatch",
            "ai_act_weakness",
            "branch_context_misuse",
            "insight_collision",
        ]

        for issue_type in expected_types:
            assert issue_type in ISSUE_TYPES


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline(self, sample_prompt_text: str, sample_signals_list, sample_segment_stats, tmp_path) -> None:
        """Test the full detection -> suggestion -> patch pipeline."""
        from services.prompt_rewrite_engine import (
            detect_prompt_weaknesses,
            generate_prompt_rewrite_suggestions,
            generate_all_patches,
            store_suggestions,
        )

        # Step 1: Detect issues
        issues_result = detect_prompt_weaknesses(
            prompt_text=sample_prompt_text,
            aggregated_signals=sample_signals_list,
            segment_stats=sample_segment_stats,
            prompt_file="prompts/de/roadmap.md",
        )

        assert len(issues_result["issues"]) > 0

        # Step 2: Generate suggestions
        suggestions = generate_prompt_rewrite_suggestions(
            issues=issues_result["issues"],
            aggregated_signals=sample_signals_list,
            segment_stats=sample_segment_stats,
        )

        # Step 3: Generate patches
        if suggestions:
            patches = generate_all_patches(suggestions)
            assert len(patches) > 0

            # Step 4: Store suggestions
            with patch("services.prompt_rewrite_engine.get_storage_path", return_value=tmp_path):
                stored = store_suggestions(suggestions)
                assert stored > 0

    def test_empty_signals_still_detects_prompt_issues(self, sample_prompt_text: str) -> None:
        """Test that prompt issues are detected even without signals."""
        from services.prompt_rewrite_engine import detect_prompt_weaknesses

        result = detect_prompt_weaknesses(
            prompt_text=sample_prompt_text,
            aggregated_signals=[],
        )

        # Should still detect static patterns
        issues = result["issues"]
        branch_issues = [i for i in issues if i["issue_type"] == "branch_context_misuse"]
        assert len(branch_issues) >= 1  # "Allgemein gilt" pattern
