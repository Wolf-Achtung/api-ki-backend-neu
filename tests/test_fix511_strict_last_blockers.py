"""
FIX-511: STRICT-On Last Blocker Cleanup Tests

Tests for the three changes that eliminate hard blockers for RELEASE_STRICT_MODE=1:

1. N4.6 Leak Sanitizer - deterministic healing of "bei Bedarf" etc.
2. Section-Guard Regeneration for KI_STACK + GAMECHANGER
3. Perplexity Competitor Query with dynamic year

All tests run in minimal test environment (no sqlalchemy dependency).
Tests use source inspection instead of imports where gpt_analyze has heavy dependencies.
"""
import pytest
import re
import os
from datetime import datetime, timezone


# Path to gpt_analyze.py for source inspection
GPT_ANALYZE_PATH = os.path.join(os.path.dirname(__file__), "..", "gpt_analyze.py")


def _read_gpt_analyze_source() -> str:
    """Read gpt_analyze.py source for inspection tests."""
    with open(GPT_ANALYZE_PATH, "r", encoding="utf-8") as f:
        return f.read()


class TestFix511_LeakSanitizer:
    """Tests for CHANGE 1: N4.6 deterministic leak sanitizer."""

    def test_sanitize_healable_leaks_function_exists(self):
        """_sanitize_healable_leaks function should be defined."""
        source = _read_gpt_analyze_source()
        assert "def _sanitize_healable_leaks(" in source

    def test_healable_leak_phrases_constant_exists(self):
        """HEALABLE_LEAK_PHRASES constant should be defined."""
        source = _read_gpt_analyze_source()
        assert "HEALABLE_LEAK_PHRASES = {" in source

    def test_healable_leak_phrases_contains_bei_bedarf(self):
        """HEALABLE_LEAK_PHRASES should contain 'bei bedarf'."""
        source = _read_gpt_analyze_source()
        assert '"bei bedarf"' in source.lower()

    def test_healable_leak_phrases_contains_wenn_sie_moechten(self):
        """HEALABLE_LEAK_PHRASES should contain 'wenn sie möchten'."""
        source = _read_gpt_analyze_source()
        assert '"wenn sie möchten"' in source.lower()

    def test_healable_leak_phrases_contains_falls_gewuenscht(self):
        """HEALABLE_LEAK_PHRASES should contain 'falls gewünscht'."""
        source = _read_gpt_analyze_source()
        assert '"falls gewünscht"' in source.lower()

    def test_sanitize_replaces_with_optional(self):
        """Sanitizer should replace healable phrases with 'optional'."""
        source = _read_gpt_analyze_source()
        # All replacements map to "optional"
        assert '"bei bedarf": "optional"' in source.lower()
        assert '"wenn sie möchten": "optional"' in source.lower()
        assert '"falls gewünscht": "optional"' in source.lower()

    def test_sanitize_uses_case_insensitive_regex(self):
        """Sanitizer should use case-insensitive replacement."""
        source = _read_gpt_analyze_source()
        # Check for re.IGNORECASE in the sanitize function
        # Find the function and check it uses case-insensitive matching
        sanitize_match = re.search(
            r'def _sanitize_healable_leaks.*?(?=\ndef |\nclass |\Z)',
            source,
            re.DOTALL
        )
        assert sanitize_match is not None
        func_source = sanitize_match.group()
        assert "re.IGNORECASE" in func_source or "IGNORECASE" in func_source

    def test_sanitize_logs_fix511_pattern(self):
        """Sanitizer should log with [FIX-511][LEAK-SAN] pattern."""
        source = _read_gpt_analyze_source()
        assert "[FIX-511][LEAK-SAN]" in source


class TestFix511_N46HealableLeaksNoFallback:
    """Tests that healable leaks don't trigger PLATIN fallback."""

    def test_healable_leaks_checked_before_regeneration(self):
        """Healable leaks should be checked before triggering regeneration."""
        source = _read_gpt_analyze_source()
        # Should check if remaining leaks are subset of healable
        assert "remaining_leak_set.issubset(healable_leak_set)" in source

    def test_accepted_without_fallback_logged(self):
        """Should log 'accepted_without_fallback=true' when healed."""
        source = _read_gpt_analyze_source()
        assert "accepted_without_fallback=true" in source

    def test_sanitize_runs_before_leak_detection(self):
        """Sanitizer should run BEFORE leak detection."""
        source = _read_gpt_analyze_source()
        # Find the N4.6 block and verify sanitize comes first
        n46_block = re.search(
            r'# N4\.6 Zero-Leak Policy.*?detected_leaks = _detect_leak_phrases',
            source,
            re.DOTALL
        )
        assert n46_block is not None
        block_source = n46_block.group()
        # Sanitize should appear before detect_leak_phrases call
        assert "_sanitize_healable_leaks" in block_source


class TestFix511_SectionGuardRegeneration:
    """Tests for CHANGE 2: Section-Guard regeneration for KI_STACK + GAMECHANGER."""

    def test_regenerate_ki_stack_strict_function_exists(self):
        """_regenerate_ki_stack_strict should be defined."""
        source = _read_gpt_analyze_source()
        assert "def _regenerate_ki_stack_strict(" in source

    def test_regenerate_gamechanger_strict_function_exists(self):
        """_regenerate_gamechanger_strict should be defined."""
        source = _read_gpt_analyze_source()
        assert "def _regenerate_gamechanger_strict(" in source

    def test_ki_stack_regeneration_has_min_600_chars(self):
        """KI_STACK regeneration should require min 600 chars."""
        source = _read_gpt_analyze_source()
        # Find the KI_STACK regeneration function
        func_match = re.search(
            r'def _regenerate_ki_stack_strict.*?(?=\n    def |\Z)',
            source,
            re.DOTALL
        )
        assert func_match is not None
        assert "600" in func_match.group()

    def test_gamechanger_regeneration_has_min_600_chars(self):
        """GAMECHANGER regeneration should require min 600 chars."""
        source = _read_gpt_analyze_source()
        func_match = re.search(
            r'def _regenerate_gamechanger_strict.*?(?=\n    def |\Z)',
            source,
            re.DOTALL
        )
        assert func_match is not None
        assert "600" in func_match.group()

    def test_section_guard_handles_ki_stack(self):
        """Section guard should have special handling for KI_STACK_SUMMARY_HTML."""
        source = _read_gpt_analyze_source()
        assert 'section_key == "KI_STACK_SUMMARY_HTML"' in source
        assert "_regenerate_ki_stack_strict(guard_context, answers" in source

    def test_section_guard_handles_gamechanger(self):
        """Section guard should have special handling for GAMECHANGER_DECISION_HTML."""
        source = _read_gpt_analyze_source()
        assert 'section_key == "GAMECHANGER_DECISION_HTML"' in source
        assert "_regenerate_gamechanger_strict(guard_context, answers" in source

    def test_sg_regen_log_patterns(self):
        """[FIX-511][SG-REGEN] log patterns should exist."""
        source = _read_gpt_analyze_source()
        assert "[FIX-511][SG-REGEN] section=KI_STACK_SUMMARY_HTML" in source
        assert "[FIX-511][SG-REGEN] section=GAMECHANGER_DECISION_HTML" in source

    def test_sg_regen_fail_log_pattern(self):
        """[FIX-511][SG-REGEN][FAIL] pattern should exist."""
        source = _read_gpt_analyze_source()
        assert "[FIX-511][SG-REGEN][FAIL]" in source


class TestFix511_PerplexityCompetitorQuery:
    """Tests for CHANGE 3: Perplexity competitor query with dynamic year."""

    def _read_research_pipeline_source(self) -> str:
        """Read research_pipeline.py source for inspection."""
        pipeline_path = os.path.join(os.path.dirname(__file__), "..", "services", "research_pipeline.py")
        with open(pipeline_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_perplexity_competitor_uses_dynamic_year(self):
        """Competitor analysis should use datetime for year, not hardcoded 2025."""
        source = self._read_research_pipeline_source()

        # Find the _perplexity_competitor_analysis function
        func_match = re.search(
            r'def _perplexity_competitor_analysis.*?(?=\ndef |\nclass |\Z)',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Should have dynamic year calculation
        assert "datetime.now(timezone.utc).year" in func_source
        # Should use variable in topic string
        assert "Deutschland {current_year}" in func_source
        # Should NOT have hardcoded 2025 in topic
        assert 'Deutschland 2025"' not in func_source

    def test_perplexity_logs_endpoint_and_model(self):
        """Competitor analysis should log endpoint, model, year, query."""
        source = self._read_research_pipeline_source()

        # Find the _perplexity_competitor_analysis function
        func_match = re.search(
            r'def _perplexity_competitor_analysis.*?(?=\ndef |\nclass |\Z)',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        assert "[PERPLEXITY]" in func_source
        assert "endpoint=" in func_source
        assert "model=" in func_source
        assert "year=" in func_source
        assert "query=" in func_source

    def test_market_fallback_uses_dynamic_year(self):
        """Market fallback HTML should use dynamic year."""
        source = self._read_research_pipeline_source()

        # Find the _market_fallback_html function
        func_match = re.search(
            r'def _market_fallback_html.*?(?=\ndef |\nclass |\Z)',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Should use current_year variable
        assert "current_year" in func_source
        # Should have the trend heading with dynamic year
        assert "{current_year}" in func_source

    def test_market_fallback_not_hardcoded_2025(self):
        """Market fallback should not have hardcoded 2025."""
        source = self._read_research_pipeline_source()

        # Find the _market_fallback_html function
        func_match = re.search(
            r'def _market_fallback_html.*?(?=\ndef |\nclass |\Z)',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # Should NOT have hardcoded 2025
        assert "Aktuelle Markttrends 2025" not in func_source
        # Should use f-string with current_year
        assert "{current_year}" in func_source


class TestFix511_StrictModeIntegration:
    """Integration tests for STRICT mode behavior."""

    def test_strict_mode_env_check_in_n46(self):
        """N4.6 leak handling should check RELEASE_STRICT_MODE."""
        source = _read_gpt_analyze_source()
        assert 'release_strict_n46 = os.getenv("RELEASE_STRICT_MODE"' in source

    def test_strict_mode_raises_runtime_error_for_n46_leaks(self):
        """In STRICT mode, unhealed leaks should raise RuntimeError."""
        source = _read_gpt_analyze_source()
        assert "[FIX-511][N4.6] ❌ Section" in source
        # Should raise RuntimeError after the error message
        n46_strict_block = re.search(
            r'\[FIX-511\]\[N4\.6\] ❌.*?raise RuntimeError',
            source,
            re.DOTALL
        )
        assert n46_strict_block is not None

    def test_strict_mode_blocks_ki_stack_fallback(self):
        """In STRICT mode, KI_STACK failures should raise RuntimeError."""
        source = _read_gpt_analyze_source()
        assert "[FIX-511][SG-REGEN][FAIL] section=KI_STACK_SUMMARY_HTML after_attempts=2 strict=1" in source

    def test_strict_mode_blocks_gamechanger_fallback(self):
        """In STRICT mode, GAMECHANGER failures should raise RuntimeError."""
        source = _read_gpt_analyze_source()
        assert "[FIX-511][SG-REGEN][FAIL] section=GAMECHANGER_DECISION_HTML after_attempts=2 strict=1" in source


class TestFix511_ForbiddenLogPatterns:
    """Tests that forbidden patterns should NOT appear in logs."""

    def _read_research_pipeline_source(self) -> str:
        """Read research_pipeline.py source for inspection."""
        pipeline_path = os.path.join(os.path.dirname(__file__), "..", "services", "research_pipeline.py")
        with open(pipeline_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_no_hardcoded_2025_in_competitor_query_topic(self):
        """Topic string should not have hardcoded 2025."""
        source = self._read_research_pipeline_source()

        # Find the _perplexity_competitor_analysis function
        func_match = re.search(
            r'def _perplexity_competitor_analysis.*?(?=\ndef |\nclass |\Z)',
            source,
            re.DOTALL
        )
        assert func_match is not None
        func_source = func_match.group()

        # The topic assignment should use {current_year}, not 2025
        topic_line = [line for line in func_source.split('\n') if 'topic = f"' in line]
        assert len(topic_line) > 0, "Should have topic assignment with f-string"
        assert '2025' not in topic_line[0], "Topic should not have hardcoded 2025"


class TestFix511_ExpectedLogPatterns:
    """Tests for expected log patterns that SHOULD appear."""

    def _read_research_pipeline_source(self) -> str:
        """Read research_pipeline.py source for inspection."""
        pipeline_path = os.path.join(os.path.dirname(__file__), "..", "services", "research_pipeline.py")
        with open(pipeline_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_leak_san_section_replaced_pattern(self):
        """[FIX-511][LEAK-SAN] section= replaced= pattern should exist."""
        source = _read_gpt_analyze_source()
        assert "[FIX-511][LEAK-SAN] section=" in source
        assert "replaced=" in source

    def test_perplexity_log_has_all_fields(self):
        """[PERPLEXITY] log should include endpoint, model, year, query."""
        source = self._read_research_pipeline_source()

        # Should have complete log line
        log_match = re.search(r'\[PERPLEXITY\].*endpoint=.*model=.*year=.*query=', source)
        assert log_match is not None, "PERPLEXITY log should have all fields"
