# -*- coding: utf-8 -*-
"""KIS-1251/1252: Platin+++-Feinschliff + Platin++++-Kohärenz-Judge.

Befunde aus Lauf 1122 (Gesundheit & Pflege / Team / MV): (1) Platin-QA-Scan
lief VOR Badge-Eindeutschung → english_badge-Timing-Artefakte; (2) AI-Act-/
Guardrail-/Automation-Enums sickerten als snake_case durch; (3) FIX-B39
ließ offene Abkürzungs-Klammern („… (z.B.") stehen; (4) [FIX-B17-ROI-CAP]
kappte die Upside-Perzentile P80/P90 auf den P50-Wert (17 %/29 % → 1 %);
(5) Team-Business-Case wies 1,2 % ROI kommentarlos aus. Dazu Platin++++:
LLM-Kohärenz-Judge mit 5 festen Fragen über dem Auslieferungszustand.
"""
from __future__ import annotations


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. FIX-B17-ROI-CAP: P80/P90 nicht mehr auf P50 kappen
# =========================================================================

class TestRoiPercentileCap:

    def test_outlier_caps_replace_inverted_cap(self):
        src = _read("gpt_analyze.py")
        assert "_b17_outlier_caps" in src
        idx = src.find("_b17_outlier_caps")
        block = src[idx:idx + 400]
        assert '"ROI_P80": 200.0' in block
        assert '"ROI_P90": 300.0' in block

    def test_old_inverted_cap_removed(self):
        # Die invertierte Form kappte P80/P90 auf den P50-Cap-Wert.
        src = _read("gpt_analyze.py")
        assert "sections[_pkey] = _b731_roi_cap" not in src


# =========================================================================
# 2. ROI-Ehrlichkeits-Einordnung bei ROI < 10 %
# =========================================================================

class TestRoiEinordnung:

    def test_injection_present_with_canonical_sources(self):
        src = _read("gpt_analyze.py")
        assert "[KIS-1251][ROI-EINORDNUNG]" in src
        idx = src.find("KIS-1251: ROI-Ehrlichkeits-Einordnung")
        assert idx != -1
        # KIS-1270: Fenster 3500→6000 — die EN-Fassung der Box (lang=en)
        # steht jetzt vor der DE-Fassung im selben Block.
        block = src[idx:idx + 6000]
        assert "_re_roi < 10" in block
        assert "CANON_CAPEX_EUR" in block
        assert "CANON_HOURS_MONTH" in block
        assert "ROI-Einordnung" in block
        # 3-Jahres-Sicht aus Kanonik, kein erfundener Wert
        assert "_re_jahr * 3 - _re_capex" in block
        # Nur bei positivem 3-Jahres-Netto und ohne Doppel-Injektion
        assert "_re_net3 > 0" in block
        assert "'ROI-Einordnung' not in _re_sec" in block


# =========================================================================
# 3. snake_case-Enum-Eindeutschung (Lauf 1122: AI-Act/Guardrails/Automation)
# =========================================================================

class TestSnakeEnumLocalization:

    def test_leaked_values_from_run_1122(self):
        from services.content_quality_enforcer import apply_badge_localization
        s = {"AI_ACT_RISK_REASONING":
             "<p>Einsatzfelder: content_generation, sensitive_area und "
             "regulatory_compliance sind relevant. Empfohlen: starter_stacks.</p>"}
        out = apply_badge_localization(s)["AI_ACT_RISK_REASONING"]
        assert "Content-Generierung" in out
        assert "Sensibler Bereich" in out
        assert "Regulatorische Anforderungen" in out
        assert "Starter-Stacks" in out
        assert "content_generation" not in out
        assert "sensitive_area" not in out

    def test_html_attributes_untouched(self):
        from services.content_quality_enforcer import _localize_snake_tokens
        html = '<div id="starter_stacks" class="content_generation">starter_stacks</div>'
        out = _localize_snake_tokens(html)
        assert 'id="starter_stacks"' in out
        assert 'class="content_generation"' in out
        assert ">Starter-Stacks<" in out

    def test_internal_keys_skipped(self):
        from services.content_quality_enforcer import apply_badge_localization
        s = {"_meta_key": "content_generation bleibt hier roh"}
        assert apply_badge_localization(s)["_meta_key"] == s["_meta_key"]

    def test_word_boundaries_respected(self):
        from services.content_quality_enforcer import _localize_snake_tokens
        assert _localize_snake_tokens("recontent_generation") == "recontent_generation"
        assert _localize_snake_tokens("data_quality_score") == "data_quality_score"

    def test_blocker_and_process_families_covered(self):
        from services.content_quality_enforcer import _SNAKE_ENUM_LABELS
        # Geschwister-Werte derselben Enum-Familien (automation_roadmap_engine)
        for token in ("skill_gap", "vendor_dependency", "workflow_automation",
                      "internal_communication", "explicit_keyword"):
            assert token in _SNAKE_ENUM_LABELS
        for label in _SNAKE_ENUM_LABELS.values():
            assert "_" not in label, f"Label '{label}' enthält Unterstrich"


# =========================================================================
# 4. Offene Abkürzungs-Klammer am Sektionsende („… (z.B.")
# =========================================================================

class TestParenTailHealer:

    def _heal(self, html: str) -> str:
        from services.report_healer import apply_segment_budget
        out, _ = apply_segment_budget({"TEST_SECTION_HTML": html}, "team")
        return out["TEST_SECTION_HTML"]

    def test_dangling_zb_removed_and_sentence_closed(self):
        html = ("<p>Wir empfehlen den Einstieg mit etablierten und bewährten "
                "KI-Lösungen für Ihr Team (z.B.</p>")
        out = self._heal(html)
        assert "(z.B." not in out
        assert out.rstrip().endswith("</p>")
        assert "Team.</p>" in out

    def test_dangling_max_removed(self):
        html = ("<p>Das Format folgt einer klaren Vorgabe für die Länge der "
                "Executive Summary im Statusbericht (max.</p>")
        out = self._heal(html)
        assert "(max." not in out
        assert "Statusbericht.</p>" in out

    def test_complete_parenthesis_untouched(self):
        html = ("<p>Wir empfehlen den Einstieg mit etablierten KI-Lösungen "
                "für kleine Teams (z.B. Canva, DeepL) im ersten Quartal.</p>")
        assert self._heal(html) == html

    def test_source_hook_present(self):
        src = _read("services/report_healer.py")
        assert "[KIS-1251][PAREN-TAIL]" in src


# =========================================================================
# 5. Platin++++: Kohärenz-Judge
# =========================================================================

def _judge_sections() -> dict:
    filler = "Substanzieller Inhalt mit konkreten Aussagen zum KI-Einsatz. " * 8
    return {
        "ROI_12M_DISPLAY_DE": "12 %",
        "CANON_CAPEX_EUR": 24000,
        "CANON_OPEX_MONTH_EUR": 350,
        "CANON_HOURS_MONTH": 25,
        "CANON_RATE_EUR": 95,
        "PAYBACK_MONTHS_FMT_DE": "11,1",
        "VENDOR_AUDIT_TOTAL": 4,
        "VENDOR_AUDIT_GREEN": 2,
        "VENDOR_AUDIT_YELLOW": 1,
        "VENDOR_AUDIT_RED": 1,
        "EXECUTIVE_SUMMARY_HTML": f"<p>{filler}</p>",
        "BUSINESS_CASE_HTML": f"<p>{filler}</p>",
        "QUICK_WINS_HTML": f"<p>{filler}</p>",
    }


def _five_checks(**overrides) -> list:
    from services.coherence_judge import CHECK_IDS
    checks = [{"id": cid, "verdict": "gruen", "begruendung": "passt"}
              for cid in CHECK_IDS]
    for cid, verdict in overrides.items():
        for c in checks:
            if c["id"] == cid:
                c["verdict"] = verdict
    return checks


class TestCoherenceJudge:

    def test_digest_contains_facts_quotes_and_sections(self):
        from services.coherence_judge import build_judge_digest
        digest = build_judge_digest(
            _judge_sections(),
            {"investitionsbudget": "10000_20000",
             "top_zeitfresser": "Angebote und Proposals schreiben"},
        )
        assert "KANONISCHE WERTE" in digest
        assert "24000" in digest
        assert "VENDOR-AMPEL" in digest
        assert "Angebote und Proposals schreiben" in digest
        assert "EXECUTIVE SUMMARY" in digest

    def test_overall_ampel_logic(self):
        from services.coherence_judge import _overall
        assert _overall(_five_checks()) == "gruen"
        assert _overall(_five_checks(budget="gelb")) == "gelb"
        assert _overall(_five_checks(budget="gelb", zahlen="rot")) == "rot"

    def test_run_stores_result_in_sections(self, monkeypatch):
        import services.anthropic_client as ac
        from services.coherence_judge import run_coherence_judge
        monkeypatch.setattr(
            ac, "call_anthropic_structured",
            lambda *a, **k: {"checks": _five_checks(spiegelung="gelb")},
        )
        s = _judge_sections()
        result = run_coherence_judge(s, {"top_zeitfresser": "Dokumentation"}, run_id="test")
        assert result is not None
        assert result["ampel"] == "gelb"
        assert s["_COHERENCE_JUDGE"]["ampel"] == "gelb"
        assert s["_COHERENCE_JUDGE_AMPEL"] == "gelb"
        assert len(result["checks"]) == 5

    def test_disabled_via_flag(self, monkeypatch):
        from services.coherence_judge import run_coherence_judge
        monkeypatch.setenv("PLATIN_COHERENCE_JUDGE", "0")
        assert run_coherence_judge(_judge_sections(), {}, run_id="test") is None

    def test_thin_digest_skips(self, monkeypatch):
        import services.anthropic_client as ac
        from services.coherence_judge import run_coherence_judge
        monkeypatch.setattr(
            ac, "call_anthropic_structured",
            lambda *a, **k: (_ for _ in ()).throw(AssertionError("darf nicht aufgerufen werden")),
        )
        assert run_coherence_judge({"X": "<p>kurz</p>"}, {}, run_id="test") is None

    def test_garbage_response_fails_open(self, monkeypatch):
        import services.anthropic_client as ac
        from services.coherence_judge import run_coherence_judge
        monkeypatch.setattr(ac, "call_anthropic_structured", lambda *a, **k: None)
        s = _judge_sections()
        assert run_coherence_judge(s, {}, run_id="test") is None
        assert "_COHERENCE_JUDGE" not in s

    def test_llm_exception_fails_open(self, monkeypatch):
        import services.anthropic_client as ac
        from services.coherence_judge import run_coherence_judge
        def _boom(*a, **k):
            raise RuntimeError("API down")
        monkeypatch.setattr(ac, "call_anthropic_structured", _boom)
        assert run_coherence_judge(_judge_sections(), {}, run_id="test") is None

    def test_hooked_after_platin_qa_before_render(self):
        src = _read("gpt_analyze.py")
        idx_qa = src.find("run_platin_qa(sections, answers, run_id=run_id)")
        idx_judge = src.find("run_coherence_judge(sections, answers, run_id=run_id)")
        idx_render = src.find("result = render(")
        assert idx_qa != -1 and idx_judge != -1 and idx_render != -1
        assert idx_qa < idx_judge < idx_render

    def test_schema_has_five_fixed_questions(self):
        from services.coherence_judge import CHECK_IDS, JUDGE_SCHEMA, _CHECK_QUESTIONS
        assert CHECK_IDS == ["vendor_ampel", "budget", "zahlen", "spiegelung", "dubletten"]
        assert set(_CHECK_QUESTIONS) == set(CHECK_IDS)
        items = JUDGE_SCHEMA["properties"]["checks"]
        assert items["minItems"] == 5 and items["maxItems"] == 5
