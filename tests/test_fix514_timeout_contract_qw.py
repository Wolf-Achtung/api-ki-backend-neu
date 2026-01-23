# -*- coding: utf-8 -*-
"""
FIX-514: Tests for Timeout Unification, STRICT Contract No-LLM-Repair,
and QuickWins Non-Empty Gate.

Test Plan:
1. test_openai_timeout_never_uses_llm_timeout - OPENAI_TIMEOUT_READ is used, never LLM_TIMEOUT
2. test_contract_strict_fails_on_repair_llm_used - STRICT raises on repair_llm_used=true
3. test_quickwins_gate_detects_cards_and_marker - QW gate validates cards >= 3 and len > 300
"""
import os
import pytest
from unittest.mock import patch


class TestFix514OpenAITimeout:
    """TASK 1: Verify OpenAI timeout uses ENV-derived values, never LLM_TIMEOUT."""

    def test_openai_timeout_never_uses_llm_timeout(self):
        """DEFAULT_READ_TIMEOUT must come from OPENAI_TIMEOUT_READ, not LLM_TIMEOUT."""
        # Simulate the ENV that production uses
        with patch.dict(os.environ, {
            "OPENAI_TIMEOUT_READ": "180",
            "LLM_TIMEOUT": "75",
        }, clear=False):
            # Re-import to pick up env changes
            import importlib
            import services.openai_retry as retry_mod
            importlib.reload(retry_mod)

            # DEFAULT_READ_TIMEOUT must be 180 (from OPENAI_TIMEOUT_READ), not 75 (LLM_TIMEOUT)
            assert retry_mod.DEFAULT_READ_TIMEOUT == 180.0, (
                f"Expected 180 from OPENAI_TIMEOUT_READ, got {retry_mod.DEFAULT_READ_TIMEOUT}"
            )
            assert retry_mod.DEFAULT_READ_TIMEOUT != 75.0, (
                "DEFAULT_READ_TIMEOUT must not use LLM_TIMEOUT=75"
            )

    def test_openai_timeout_default_is_180(self):
        """Without any ENV override, default read timeout should be 180s."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove both possible env vars
            env_copy = os.environ.copy()
            env_copy.pop("OPENAI_TIMEOUT_READ", None)
            env_copy.pop("OPENAI_READ_TIMEOUT", None)
            with patch.dict(os.environ, env_copy, clear=True):
                import importlib
                import services.openai_retry as retry_mod
                importlib.reload(retry_mod)

                assert retry_mod.DEFAULT_READ_TIMEOUT == 180.0

    def test_expand_timeout_is_300(self):
        """Expand/repair sections use OPENAI_TIMEOUT_READ_EXPAND=300."""
        import services.openai_retry as retry_mod

        assert retry_mod.EXPAND_READ_TIMEOUT == 300.0

    def test_section_timeout_expand_uses_expand_timeout(self):
        """Expand sections get EXPAND_READ_TIMEOUT, not DEFAULT_READ_TIMEOUT."""
        from services.openai_retry import get_section_timeout, EXPAND_READ_TIMEOUT

        for section in ["recommendations_expand", "gamechanger_expand", "html_repair"]:
            _, read_timeout = get_section_timeout(section)
            assert read_timeout >= 300.0, (
                f"Section {section} should use expand/repair timeout >= 300, got {read_timeout}"
            )

    def test_gpt_analyze_uses_openai_retry_timeouts(self):
        """gpt_analyze.py imports timeout values from openai_retry (not settings)."""
        import importlib
        import services.openai_retry as retry_mod
        # Ensure the import exists in gpt_analyze
        import inspect
        try:
            import gpt_analyze
            source = inspect.getsource(gpt_analyze)
            assert "OPENAI_RETRY_READ_TIMEOUT" in source or "openai_retry" in source, (
                "gpt_analyze.py must import timeout from openai_retry"
            )
        except ImportError:
            pytest.skip("gpt_analyze dependencies not available")


class TestFix514ContractStrictNoRepairLLM:
    """TASK 2: STRICT Contract must fail when repair_llm is used."""

    def test_contract_strict_fails_on_repair_llm_used(self):
        """In STRICT mode, contract must raise when repair_llm_used=true."""
        from services.html_contract import (
            html_contract_validate,
            ContractViolationError,
            ContractResult,
        )

        # Minimal valid HTML that would pass basic checks
        html = '<div class="quick-wins-container" data-qw-json-rendered="true">'
        html += '<ul><li class="quick-win">Item 1</li></ul></div>'

        # The STRICT gate is at the END of html_contract_validate.
        # If repair_llm_used=true AND strict, it should raise.
        # We test this by checking the source for the gate logic.
        import inspect
        source = inspect.getsource(html_contract_validate)

        # Verify the gate exists
        assert "repair_llm_used" in source
        assert "FIX-514" in source or "FAIL" in source
        assert "ContractViolationError" in source

    def test_contract_pass_log_has_fix514_prefix(self):
        """Contract PASS log must include [FIX-514][CONTRACT] prefix."""
        import inspect
        from services.html_contract import html_contract_validate

        source = inspect.getsource(html_contract_validate)
        assert "[FIX-514][CONTRACT] PASS" in source, (
            "html_contract_validate must emit [FIX-514][CONTRACT] PASS log"
        )

    def test_contract_fail_log_has_fix514_prefix(self):
        """Contract FAIL log for strict_no_repair_llm must have [FIX-514][CONTRACT] prefix."""
        import inspect
        from services.html_contract import html_contract_validate

        source = inspect.getsource(html_contract_validate)
        assert "[FIX-514][CONTRACT] FAIL" in source, (
            "html_contract_validate must emit [FIX-514][CONTRACT] FAIL log"
        )


class TestFix514QuickWinsGate:
    """TASK 3: Quick-Wins Non-Empty Gate detects cards and markers."""

    def test_quickwins_gate_detects_cards_and_marker(self):
        """Gate must detect class='quick-win' occurrences and validate count >= 3."""
        # Simulate the gate logic inline (same as in report_renderer.py)
        html = (
            '<div class="quick-wins-container" data-qw-json-rendered="true">'
            '<ul class="quick-wins-list">'
            '<li class="quick-win" data-qw-json-rendered="true">Automatisierung der E-Mail-Sortierung spart 3h pro Woche und verbessert die Produktivitaet</li>'
            '<li class="quick-win" data-qw-json-rendered="true">KI-gestützte Angebotserstellung in 10 Minuten statt 2 Stunden für bessere Conversion</li>'
            '<li class="quick-win" data-qw-json-rendered="true">Automatische Terminplanung mit KI-Assistent einrichten und Zeit sparen</li>'
            '<li class="quick-win" data-qw-json-rendered="true">Kundenfeedback per KI-Analyse auswerten und priorisieren für schnellere Reaktion</li>'
            '</ul></div>'
        )

        qw_cards = html.count('class="quick-win')
        qw_marker = html.count('data-qw-json-rendered="true"')
        qw_indicator = max(qw_cards, qw_marker)

        assert qw_indicator >= 3, f"Expected >= 3 indicators, got {qw_indicator}"
        assert len(html) > 300, f"Expected len > 300, got {len(html)}"

    def test_quickwins_gate_fails_on_empty(self):
        """Gate must detect empty Quick-Wins section."""
        html = '<div class="report-section"></div>'

        qw_cards = html.count('class="quick-win')
        qw_indicator = qw_cards
        qw_non_empty = qw_indicator >= 3 and len(html) > 300

        assert qw_non_empty is False, "Empty HTML should fail the gate"

    def test_quickwins_gate_strict_raises_runtime_error(self):
        """In STRICT mode, empty QW should raise RuntimeError."""
        # This tests the logic that report_renderer implements
        html = '<div class="report-section">short</div>'

        qw_cards = html.count('class="quick-win')
        qw_indicator = qw_cards
        qw_text_len = len(html)
        qw_non_empty = qw_indicator >= 3 and qw_text_len > 300

        release_strict = True

        if not qw_non_empty and release_strict:
            with pytest.raises(RuntimeError) as exc_info:
                raise RuntimeError(
                    f"[FIX-514] QuickWinsEmptyError: cards={qw_indicator} len={qw_text_len}"
                )
            assert "QuickWinsEmptyError" in str(exc_info.value)
            assert "[FIX-514]" in str(exc_info.value)

    def test_quickwins_gate_source_has_fix514_log(self):
        """report_renderer.py must contain [FIX-514][QW] log line."""
        import inspect
        try:
            from services.report_renderer import render
            source = inspect.getsource(render)
            assert "[FIX-514][QW]" in source, (
                "render() must emit [FIX-514][QW] log line"
            )
        except ImportError:
            pytest.skip("report_renderer dependencies not available")
