# -*- coding: utf-8 -*-
"""KIS-1235 P2b: Advisor-Kohärenz-Pass.

Beweisfall aus Lauf 1235: Vendor-Badges "AVV vorhanden/verfügbar" vs.
Persönliche Einschätzung "Anbindungen ohne AV-Vertrag (AVV)". Der Pass
prüft die erzählenden Sektionen nach allen Enforcern gegen die
deterministischen Fakten und wendet nur exakt matchende, längenbegrenzte
Korrekturen an.
"""
from __future__ import annotations

import services.coherence_pass as cp


BASE_SECTIONS = {
    "VENDOR_AUDIT_TOTAL": 3,
    "VENDOR_AUDIT_GREEN": 0,
    "VENDOR_AUDIT_YELLOW": 1,
    "VENDOR_AUDIT_RED": 2,
    "ROI_12M": "8.0",
    "PAYBACK_MONTHS": "11.1",
    "CANON_HOURS_MONTH": "15",
    "AI_ACT_RISK_LEVEL_DE": "begrenzt",
    "ADVISOR_NOTE_HTML": "<p>Der ROI liegt bei 42 % und alles ist risikofrei.</p>",
    "EXECUTIVE_SUMMARY_HTML": "<p>Solide Ausgangslage.</p>",
}


class TestFactsDigest:

    def test_digest_contains_facts_and_avv_semantics(self):
        digest = cp.build_facts_digest(dict(BASE_SECTIONS))
        assert "3 Tools geprüft" in digest
        assert "AVV verfügbar" in digest  # Semantik-Klarstellung
        assert "KEIN Widerspruch" in digest
        assert "ROI (12M): 8.0" in digest
        assert "begrenzt" in digest

    def test_empty_sections_empty_digest(self):
        assert cp.build_facts_digest({}) == ""


class TestCoherencePass:

    def _run(self, monkeypatch, corrections, sections=None):
        import services.anthropic_client as ac
        monkeypatch.setattr(
            ac, "call_anthropic_structured",
            lambda *a, **k: {"corrections": corrections},
        )
        s = dict(sections or BASE_SECTIONS)
        return cp.run_advisor_coherence_pass(s)

    def test_exact_match_correction_applied(self, monkeypatch):
        out = self._run(monkeypatch, [{
            "section": "advisor_note",
            "find": "Der ROI liegt bei 42 %",
            "replace": "Der ROI liegt bei 8 %",
            "reason": "ROI-Fakt ist 8,0 %",
        }])
        assert "8 %" in out["ADVISOR_NOTE_HTML"]
        assert "42 %" not in out["ADVISOR_NOTE_HTML"]

    def test_non_matching_find_skipped(self, monkeypatch):
        out = self._run(monkeypatch, [{
            "section": "advisor_note",
            "find": "Dieser Text existiert nicht",
            "replace": "egal",
            "reason": "x",
        }])
        assert out["ADVISOR_NOTE_HTML"] == BASE_SECTIONS["ADVISOR_NOTE_HTML"]

    def test_oversized_replacement_rejected(self, monkeypatch):
        out = self._run(monkeypatch, [{
            "section": "advisor_note",
            "find": "42 %",
            "replace": "x" * 500,
            "reason": "x",
        }])
        assert "42 %" in out["ADVISOR_NOTE_HTML"]

    def test_no_corrections_is_noop(self, monkeypatch):
        out = self._run(monkeypatch, [])
        assert out["ADVISOR_NOTE_HTML"] == BASE_SECTIONS["ADVISOR_NOTE_HTML"]

    def test_flag_off_skips_llm(self, monkeypatch):
        import services.anthropic_client as ac
        monkeypatch.setenv("ADVISOR_COHERENCE_PASS", "0")

        def _boom(*a, **k):
            raise AssertionError("LLM darf bei Flag=0 nicht aufgerufen werden")

        monkeypatch.setattr(ac, "call_anthropic_structured", _boom)
        out = cp.run_advisor_coherence_pass(dict(BASE_SECTIONS))
        assert out["ADVISOR_NOTE_HTML"] == BASE_SECTIONS["ADVISOR_NOTE_HTML"]

    def test_llm_failure_is_noop(self, monkeypatch):
        import services.anthropic_client as ac
        monkeypatch.setattr(ac, "call_anthropic_structured", lambda *a, **k: None)
        out = cp.run_advisor_coherence_pass(dict(BASE_SECTIONS))
        assert out["ADVISOR_NOTE_HTML"] == BASE_SECTIONS["ADVISOR_NOTE_HTML"]

    def test_max_five_corrections(self, monkeypatch):
        sections = dict(BASE_SECTIONS)
        sections["ADVISOR_NOTE_HTML"] = "<p>" + " ".join(f"W{i}." for i in range(10)) + "</p>"
        corrections = [{
            "section": "advisor_note", "find": f"W{i}.",
            "replace": f"K{i}.", "reason": "x",
        } for i in range(10)]
        out = self._run(monkeypatch, corrections, sections)
        applied = sum(1 for i in range(10) if f"K{i}." in out["ADVISOR_NOTE_HTML"])
        assert applied == 5
