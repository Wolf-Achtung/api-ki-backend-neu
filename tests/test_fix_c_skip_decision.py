"""Sprint 1026.2 — FIX-C skip for executive_decision.

KIS-1188 reproduction: FIX-C (`reduce_redundancy`) was stripping the
broken bullet blocks from `executive_decision` before the downstream
[FIX-EXEC-DECISION-CLEAN] detection in `apply_segment_budget` had a
chance to run. With the blocks gone, detection saw nothing to repair
and the truncated bullet survived to the customer-facing PDF.

Fix: extend FIX-C with a dedicated skip-set
`_DECISION_DETECTION_OWNED_KEYS` so the decision-detection downstream
sees the LLM's raw output (including any duplicate / over-generated
blocks that signal a mid-sentence cut).

Acceptance: `reduce_redundancy` returns `executive_decision` /
`EXECUTIVE_DECISION_HTML` byte-for-byte identical to input, regardless
of duplicate-block content. All other sections retain their existing
FIX-C behaviour.
"""
from __future__ import annotations

import re

import pytest

from services.report_healer import reduce_redundancy


def _build_duplicate_block_section(label: str) -> str:
    """Construct an `executive_decision`-style HTML payload with three
    duplicate paragraph blocks above the FIX-C `min_chars=160` threshold.
    Mirrors the KIS-1188 LLM output pattern (over-generation with
    repeated wrapper).
    """
    duplicate_p = (
        '<p>Einleitende Ausführungen zur Entscheidungsvorlage mit '
        'ausreichend Inhalt, um die Mindestlänge für FIX-C-Block-Dedup '
        'sicher zu überschreiten — dieser Absatz wird absichtlich '
        f'mehrfach wiederholt um die Block-Removal zu triggern ({label}).</p>'
    )
    return (
        '<div class="exec-decision-box">'
        + duplicate_p
        + duplicate_p
        + duplicate_p
        + '<ul>'
        + '<li><strong>Tun:</strong> Einen verbindlichen Standard '
          'einführen, bei dem jede Beratung den festen Ablauf Input</li>'
        + '</ul></div>'
    )


class TestFixCSkipDecision:
    def test_executive_decision_unchanged_when_blocks_duplicate(self):
        """KIS-1188 regression: FIX-C must skip executive_decision even
        when its content contains duplicate blocks above min_chars."""
        original = _build_duplicate_block_section("dup")
        sections = {"executive_decision": original}

        result, stats = reduce_redundancy(sections)

        assert result["executive_decision"] == original, (
            "executive_decision must be passed through byte-for-byte"
        )
        assert stats.blocks_removed == 0
        assert "executive_decision" not in stats.sections_affected
        # KIS-1188 specific: the broken-bullet text must survive FIX-C so
        # downstream detection can flag and repair it.
        assert "den festen Ablauf Input" in result["executive_decision"]

    def test_uppercase_html_key_also_skipped(self):
        """Both `executive_decision` and `EXECUTIVE_DECISION_HTML` must
        be covered — the section flows through the healer under both
        keys depending on the call site."""
        original = _build_duplicate_block_section("upper")
        sections = {"EXECUTIVE_DECISION_HTML": original}

        result, stats = reduce_redundancy(sections)

        assert result["EXECUTIVE_DECISION_HTML"] == original
        assert stats.blocks_removed == 0

    def test_other_decision_sections_still_deduped(self):
        """Per sprint scope: roadmap_90d_decision and
        gamechanger_decision MUST retain their existing FIX-C
        behaviour. They did not show production cutoffs."""
        original = _build_duplicate_block_section("roadmap")
        sections = {"roadmap_90d_decision": original}

        result, stats = reduce_redundancy(sections)

        # FIX-C must still operate on this section — duplicates removed.
        assert stats.blocks_removed >= 1, (
            "roadmap_90d_decision must still be deduplicated by FIX-C"
        )

    def test_unrelated_section_retains_dedup_behaviour(self):
        """An ordinary section with duplicate blocks must still be
        deduped — the skip is targeted, not blanket."""
        original = _build_duplicate_block_section("data")
        sections = {"data_readiness": original}

        result, stats = reduce_redundancy(sections)

        assert stats.blocks_removed >= 1, (
            "Non-decision section must keep its FIX-C behaviour"
        )
        # Result is shorter than input because duplicates were removed
        assert len(result["data_readiness"]) < len(original)

    def test_skip_log_emitted_at_info_level(self, caplog):
        """The skip is observable in production logs as
        `[FIX-C-SKIP] section=... reason=decision_detection_owns_this`
        at INFO level (not DEBUG) per sprint briefing."""
        import logging

        original = _build_duplicate_block_section("log")
        sections = {"executive_decision": original}

        with caplog.at_level(logging.INFO, logger="services.report_healer"):
            reduce_redundancy(sections)

        skip_lines = [
            r for r in caplog.records
            if "[FIX-C-SKIP]" in r.getMessage()
        ]
        assert skip_lines, f"Expected [FIX-C-SKIP] log line, got: {[r.getMessage() for r in caplog.records]}"
        assert skip_lines[0].levelno == logging.INFO
        msg = skip_lines[0].getMessage()
        assert "section=executive_decision" in msg
        assert "reason=decision_detection_owns_this" in msg
