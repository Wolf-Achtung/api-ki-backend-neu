"""
[FIX-EXEC-DECISION-CLEAN] Tests for per-<li> mid-sentence detection
in the three decision sections (executive_decision, roadmap_90d_decision,
gamechanger_decision).

Reproduces KIS-1186 / R1 page 4: briefing 1069 emitted
'<li><strong>Tun:</strong> ... den Ablauf Input</li>' inside
executive_decision, while the "Risiko" bullet's terminal "." satisfied
the section-level last-char check used by FIX-B38a / FIX-B39 / the
PLATIN+++ validator. The broken bullet slipped through the entire
healing+validation pipeline.

Test contract:
- Healer (apply_segment_budget): truncated <li> is dropped and replaced
  with the neutral fallback, other bullets are preserved.
- Validator (ReportValidator._check_sentence_completeness): emits
  TRUNCATED_LI warning for the offending bullet even when the section
  ends cleanly.
"""
import re

import pytest


class TestHealerExecDecisionClean:
    def _heal(self, sections):
        from services.report_healer import apply_segment_budget
        result, _ = apply_segment_budget(sections, "solo")
        return result

    def test_truncated_bullet_dropped_and_replaced(self):
        """KIS-1186 reproduction: mid-sentence <li> in executive_decision."""
        sections = {
            "executive_decision": (
                '<div class="exec-decision-box">'
                '<p><strong>Ihre Entscheidung in 3 Punkten</strong></p>'
                '<ul>'
                '<li><strong>Tun:</strong> Einen verbindlichen Standard-Arbeitsablauf '
                'einführen, bei dem jede Beratungsleistung den Ablauf Input</li>'
                '<li><strong>Lassen:</strong> Tool-Zoo und Ad-hoc-Prompts ohne Standards.</li>'
                '<li><strong>Risiko:</strong> Nach 14 Tagen ohne Effekt stoppen.</li>'
                '</ul></div>'
            ),
        }
        out = self._heal(sections)
        assert "den Ablauf Input" not in out["executive_decision"]
        assert "Weitere Punkte siehe Business Case und Roadmap" in out["executive_decision"]
        assert "Lassen:" in out["executive_decision"]
        assert "Risiko:" in out["executive_decision"]

    def test_clean_section_unchanged(self):
        clean = (
            '<ul>'
            '<li>Tun: Standardisierung einführen mit klarem Owner.</li>'
            '<li>Lassen: Tool-Zoo vermeiden, keine parallelen Initiativen.</li>'
            '<li>Risiko: Nach 14 Tagen ohne Effekt stoppen.</li>'
            '</ul>'
        )
        out = self._heal({"executive_decision": clean})
        assert "Weitere Punkte siehe Business Case" not in out["executive_decision"]
        assert "Standardisierung einführen" in out["executive_decision"]

    def test_non_decision_section_ignored(self):
        """The cleaner must only target the three decision sections."""
        truncated_summary = (
            '<ul>'
            '<li>Punkt 1: Eine längere Aussage die mitten im Satz endet bei Input</li>'
            '<li>Punkt 2: Vollständiger Satz hier.</li>'
            '</ul>'
        )
        out = self._heal({"executive_summary": truncated_summary})
        # executive_summary is NOT a decision section - bullet must survive
        assert "bei Input" in out["executive_summary"]
        assert "Weitere Punkte siehe Business Case" not in out["executive_summary"]

    def test_short_bullet_below_threshold_preserved(self):
        """Bullets shorter than 25 chars (likely meta-labels) are skipped."""
        short = '<ul><li>Tun</li><li>Sonstiges hier.</li></ul>'
        out = self._heal({"executive_decision": short})
        # "Tun" (3 chars) is well below the 25-char floor - must be preserved
        assert "<li>Tun</li>" in out["executive_decision"]

    def test_all_three_decision_sections_covered(self):
        """The fix targets executive_decision, roadmap_90d_decision,
        gamechanger_decision (per prompt structure)."""
        truncated_li = (
            '<ul>'
            '<li>Eine Aussage die mitten im Wort endet bei Input</li>'
            '<li>Sauberes Ende hier mit Punkt.</li>'
            '</ul>'
        )
        for key in ("executive_decision", "roadmap_90d_decision", "gamechanger_decision"):
            out = self._heal({key: truncated_li})
            assert "bei Input" not in out[key], f"{key} not cleaned"
            assert "Weitere Punkte siehe Business Case" in out[key], f"{key} missing fallback"


class TestHealerExecDecisionClean10261:
    """Sprint 1026.1 — coverage for LLM-output-quality scenarios that PR #1026
    missed (KIS-1187 reproduction)."""

    def _heal(self, sections):
        from services.report_healer import apply_segment_budget
        result, _ = apply_segment_budget(sections, "solo")
        return result

    def test_kis1187_p_bullets_scenario_c(self):
        """KIS-1187 root cause: LLM emitted <p> bullets instead of <li>. The
        strict regex from PR #1026 saw zero <li> and the broken bullet slipped
        through. Pass 3 (<p>-fallback) must now catch it."""
        sections = {
            "executive_decision": (
                '<div class="exec-decision-box">'
                '<p><strong>Ihre Entscheidung in 3 Punkten</strong></p>'
                '<p><strong>Tun:</strong> Einen verbindlichen Standard einführen, '
                'bei dem jedes Objekt dem Schema Input</p>'
                '<p><strong>Lassen:</strong> Tool-Zoo ohne Standards.</p>'
                '<p><strong>Risiko:</strong> Nach 14 Tagen ohne Effekt stoppen.</p>'
                '</div>'
            ),
        }
        out = self._heal(sections)
        assert "dem Schema Input" not in out["executive_decision"]
        assert "Weitere Punkte siehe Business Case und Roadmap" in out["executive_decision"]
        # Sibling p-bullets preserved
        assert "Lassen:" in out["executive_decision"]
        assert "Risiko:" in out["executive_decision"]
        # Non-bullet <p> (header) preserved
        assert "Ihre Entscheidung in 3 Punkten" in out["executive_decision"]

    def test_tag_salad_scenario_e(self):
        """LLM emitted <li>...<li> (no </li>) or closed <li> with </p>. PR #1026
        regex greedy-matched across bullets and accepted the last sibling's "."
        as terminal. Pass 2 (tag-salat) splits on <li>-boundaries."""
        sections = {
            "executive_decision": (
                '<ul>'
                '<li><strong>Tun:</strong> Einen verbindlichen Standard einführen, '
                'bei dem jedes Objekt dem Schema Input</p>'
                '<li><strong>Lassen:</strong> Tool-Zoo ohne Standards.</li>'
                '<li><strong>Risiko:</strong> Nach 14 Tagen stoppen.</li>'
                '</ul>'
            ),
        }
        out = self._heal(sections)
        assert "dem Schema Input" not in out["executive_decision"]
        assert "Weitere Punkte siehe Business Case und Roadmap" in out["executive_decision"]
        # Siblings preserved with proper <li>...</li>
        assert "Tool-Zoo ohne Standards." in out["executive_decision"]
        assert "Nach 14 Tagen stoppen." in out["executive_decision"]

    def test_non_decision_p_bullets_not_repaired(self):
        """Non-decision sections with similar <p><strong>Tun:</strong> patterns
        must NOT be touched — Pass 3 is gated on section key."""
        html = (
            '<p><strong>Tun:</strong> Eine längere Aussage die mitten endet bei Input</p>'
        )
        out = self._heal({"executive_summary": html})
        # executive_summary is NOT a decision section
        assert "bei Input" in out["executive_summary"]
        assert "Weitere Punkte siehe Business Case" not in out["executive_summary"]

    def test_p_bullets_all_clean_no_repair(self):
        """When all <p>-bullets end cleanly, nothing changes."""
        clean = (
            '<p><strong>Tun:</strong> Standardisierung einführen.</p>'
            '<p><strong>Lassen:</strong> Tool-Zoo vermeiden.</p>'
            '<p><strong>Risiko:</strong> Nach 14 Tagen stoppen.</p>'
        )
        out = self._heal({"executive_decision": clean})
        assert "Weitere Punkte siehe Business Case" not in out["executive_decision"]
        assert "Standardisierung einführen" in out["executive_decision"]

    def test_p_bullets_only_non_bullet_p_unchanged(self):
        """<p> blocks without the Tun:/Lassen:/Risiko prefix must not trigger
        Pass 3 (prevents false-positives in headers, intro text, etc.)."""
        html = (
            '<p>Diese Sektion enthält einen längeren Einleitungstext der mitten endet bei Input</p>'
        )
        # Decision-section key but non-bullet <p> with no prefix — must NOT touch
        out = self._heal({"executive_decision": html})
        assert "bei Input" in out["executive_decision"]
        assert "Weitere Punkte siehe Business Case" not in out["executive_decision"]

    def test_tag_salad_all_clean_no_repair(self):
        """Tag-salat with all bullets ending cleanly: split heuristic must not
        flag anything and must produce well-formed <li>...</li> output."""
        sections = {
            "executive_decision": (
                '<ul>'
                '<li><strong>Tun:</strong> Standardisierung einführen mit klarem Owner.'
                '<li><strong>Lassen:</strong> Tool-Zoo vermeiden, keine Parallelinitiativen.'
                '<li><strong>Risiko:</strong> Nach 14 Tagen ohne Effekt stoppen.'
                '</ul>'
            ),
        }
        out = self._heal(sections)
        assert "Weitere Punkte siehe Business Case" not in out["executive_decision"]
        # All three sibling texts present
        assert "Standardisierung einführen" in out["executive_decision"]
        assert "Tool-Zoo vermeiden" in out["executive_decision"]
        assert "Nach 14 Tagen ohne Effekt stoppen" in out["executive_decision"]


class TestValidatorExecDecisionClean:
    def _validate(self, sections):
        from services.report_validator import PlatinValidator
        v = PlatinValidator(sections=sections)
        v._check_sentence_completeness()
        return v.warnings

    def test_truncated_li_emits_warning_despite_clean_section_end(self):
        """KIS-1186: section ends with '.' (Risiko bullet) but middle <li>
        is mid-sentence. Section-level check passes; per-<li> check must
        catch it."""
        html = (
            '<ul>'
            '<li>Tun: Einen verbindlichen Standard einführen, bei dem '
            'jede Beratung den Ablauf Input</li>'
            '<li>Lassen: Tool-Zoo ohne Standards vermeiden.</li>'
            '<li>Risiko: Nach 14 Tagen stoppen.</li>'
            '</ul>'
        )
        warnings = self._validate({"executive_decision": html})
        assert any(
            "TRUNCATED_LI" in w and "executive_decision" in w
            for w in warnings
        ), f"Expected TRUNCATED_LI warning, got: {warnings}"

    def test_clean_section_no_truncated_li_warning(self):
        html = (
            '<ul>'
            '<li>Tun: Standardisierung mit klarem Owner einführen.</li>'
            '<li>Lassen: Tool-Zoo vermeiden, keine Parallelinitiativen.</li>'
            '<li>Risiko: Nach 14 Tagen ohne Effekt stoppen.</li>'
            '</ul>'
        )
        warnings = self._validate({"executive_decision": html})
        assert not any("TRUNCATED_LI" in w for w in warnings), f"Unexpected warning: {warnings}"

    def test_non_decision_section_not_checked_per_li(self):
        html = (
            '<ul>'
            '<li>Lange Aussage die mitten endet bei Input</li>'
            '</ul>'
        )
        warnings = self._validate({"executive_summary": html})
        assert not any("TRUNCATED_LI" in w for w in warnings), f"False positive: {warnings}"


class TestValidatorExecDecisionClean10261:
    """Sprint 1026.1 validator parity for scenarios C and E."""

    def _validate(self, sections):
        from services.report_validator import PlatinValidator
        v = PlatinValidator(sections=sections)
        v._check_sentence_completeness()
        return v.warnings

    def test_p_bullet_truncation_emits_warning(self):
        """Scenario C: <p>-only decision section with truncated Tun bullet."""
        html = (
            '<p><strong>Ihre Entscheidung in 3 Punkten</strong></p>'
            '<p><strong>Tun:</strong> Einen Standard einführen, bei dem jedes Objekt dem Schema Input</p>'
            '<p><strong>Lassen:</strong> Tool-Zoo ohne Standards.</p>'
            '<p><strong>Risiko:</strong> Nach 14 Tagen stoppen.</p>'
        )
        warnings = self._validate({"executive_decision": html})
        assert any(
            "TRUNCATED_LI" in w and "executive_decision" in w and "dem Schema Input" in w
            for w in warnings
        ), f"Expected TRUNCATED_LI warning for <p>-bullet, got: {warnings}"

    def test_tag_salad_truncation_emits_warning(self):
        """Scenario E: <li>...<li> tag-salat with truncated Tun bullet."""
        html = (
            '<ul>'
            '<li><strong>Tun:</strong> Einen Standard einführen, bei dem jedes Objekt dem Schema Input</p>'
            '<li><strong>Lassen:</strong> Tool-Zoo ohne Standards.</li>'
            '<li><strong>Risiko:</strong> Nach 14 Tagen stoppen.</li>'
            '</ul>'
        )
        warnings = self._validate({"executive_decision": html})
        assert any(
            "TRUNCATED_LI" in w and "executive_decision" in w and "dem Schema Input" in w
            for w in warnings
        ), f"Expected TRUNCATED_LI warning for tag-salat, got: {warnings}"

    def test_p_bullet_clean_section_no_warning(self):
        html = (
            '<p><strong>Tun:</strong> Standardisierung einführen.</p>'
            '<p><strong>Lassen:</strong> Tool-Zoo vermeiden.</p>'
            '<p><strong>Risiko:</strong> Nach 14 Tagen stoppen.</p>'
        )
        warnings = self._validate({"executive_decision": html})
        assert not any("TRUNCATED_LI" in w for w in warnings), f"False positive: {warnings}"

    def test_non_bullet_p_in_decision_section_not_flagged(self):
        """Non-bullet <p> (no Tun:/Lassen:/Risiko prefix) must not flag,
        prevents false positives on intro text inside decision sections."""
        html = (
            '<p>Diese Sektion enthält Einleitungstext der mitten endet bei Input</p>'
        )
        warnings = self._validate({"executive_decision": html})
        assert not any("TRUNCATED_LI" in w for w in warnings), f"False positive: {warnings}"


class TestExecDecisionDiagMarker:
    """Sprint 1026.5a — always-on [FIX-EXEC-DECISION-DIAG] marker emits for
    every decision-section pass through apply_segment_budget regardless of
    detection outcome. Pure observability, no behavior change."""

    def _heal_with_logs(self, sections, caplog):
        from services.report_healer import apply_segment_budget
        import logging
        caplog.set_level(logging.INFO, logger="services.report_healer")
        result, _ = apply_segment_budget(sections, "solo")
        return result, caplog.records

    def test_diag_marker_emitted_on_truncated_section(self, caplog):
        """KIS-1186-style truncated <li> must trigger both the existing
        [FIX-EXEC-DECISION-CLEAN] warning AND the new diagnostic marker
        with the expected fields."""
        sections = {
            "executive_decision": (
                '<div class="exec-decision-box">'
                '<p><strong>Ihre Entscheidung in 3 Punkten</strong></p>'
                '<ul>'
                '<li><strong>Tun:</strong> Einen verbindlichen Standard-Arbeitsablauf '
                'einführen, bei dem jede Beratungsleistung den Ablauf Input</li>'
                '<li><strong>Lassen:</strong> Tool-Zoo und Ad-hoc-Prompts ohne Standards.</li>'
                '<li><strong>Risiko:</strong> Nach 14 Tagen ohne Effekt stoppen.</li>'
                '</ul></div>'
            ),
        }
        _, records = self._heal_with_logs(sections, caplog)
        diag = [r for r in records if "[FIX-EXEC-DECISION-DIAG]" in r.getMessage()]
        assert diag, "DIAG marker must emit even when detection repairs the section"
        msg = diag[0].getMessage()
        assert "section=executive_decision" in msg
        assert "open_li=3" in msg
        assert "close_li=3" in msg
        assert "p_total=" in msg
        assert "p_strong_prefix=" in msg
        assert "last_chars=" in msg
        assert "tags=" in msg
        # Hotfix-1027.2.1-F1: content_hash für Persistence-vs-Render-Korrelation
        assert "content_hash=" in msg

    def test_diag_marker_emitted_on_clean_section(self, caplog):
        """When the LLM honors the contract and no bullet is truncated, the
        [FIX-EXEC-DECISION-CLEAN] line is DEBUG-only and effectively silent at
        production log levels. The DIAG marker must still appear so production
        runs always show the section's tag inventory."""
        clean = (
            '<div class="exec-decision-box">'
            '<p><strong>Ihre Entscheidung in 3 Punkten</strong></p>'
            '<ul>'
            '<li><strong>Tun:</strong> Standardisierung einführen mit klarem Owner.</li>'
            '<li><strong>Lassen:</strong> Tool-Zoo vermeiden, keine parallelen Initiativen.</li>'
            '<li><strong>Risiko:</strong> Nach 14 Tagen ohne Effekt stoppen.</li>'
            '</ul></div>'
        )
        _, records = self._heal_with_logs({"executive_decision": clean}, caplog)
        diag = [r for r in records if "[FIX-EXEC-DECISION-DIAG]" in r.getMessage()]
        assert diag, "DIAG marker must emit on clean sections too"
        msg = diag[0].getMessage()
        assert "section=executive_decision" in msg
        assert "open_li=3" in msg
        assert "close_li=3" in msg
        # Tail must end on the Risiko bullet's terminal punctuation
        assert "last_chars=" in msg
        # Hotfix-1027.2.1-F1: content_hash gehört in jede DIAG-Zeile
        assert "content_hash=" in msg
        # Trailing position-Invariant: nach dem Hash steht nichts mehr
        assert re.search(r"content_hash=[0-9a-f]{12}\s*$", msg), msg
