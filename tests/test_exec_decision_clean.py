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
