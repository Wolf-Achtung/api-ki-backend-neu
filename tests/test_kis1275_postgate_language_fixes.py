# -*- coding: utf-8 -*-
"""KIS-1275 — Fixes aus dem adversarialen Audit des EN-Sprachgates (KIS-1273).

Alle Befunde betrafen Pässe NACH dem Sprachgate (gpt_analyze ~22912), die
EN-Reports wieder eindeuteten oder still tot waren. Abgedeckt (LLM gemockt,
ohne Netzwerk):

  1  services/solo_final_pass.apply_size_final_pass — lang-Gate: EN-Input
     byte-identisch (Governance-/Audit-Trail-Catchalls, Team-Map), DE
     byte-identisch zum bisherigen Verhalten (Default lang="de").
  2  services/judge_heal.run_judge_heal — EN-Prompt-Variante (kein
     "deutsch"/"Sie-Form" im Prompt), DE-Prompt unverändert.
  3  services/report_healer.heal_final_html — Signatur-Kontrakt (kein
     `hauptleistung`-Kwarg mehr, Aufruf auf result["html"]) + lang-Gate der
     Eindeutschungs-Subpässe (Governance→Spielregeln, 3.5→3,5, SOLO-Map).
  4  gpt_analyze._translate_de_blocks_to_en — Marker-Echo/Transposition/
     Prosa-Antworten: Original bleibt pro Block, Tag-Bilanz erhalten.
  5  gpt_analyze._text_looks_german — False-Negative-Repro ("Das Team plant
     den Start im August") + False-Positive-Repro (BAFA-Programmname,
     zitierte Studientitel).
  6  gpt_analyze._en_language_sweep_sections — Budget-Priorisierung
     (Executive Summary/Quick Wins vor Anhang) + Shadow-Twin-Dedup.
  7  Fail-open-Markierung <!--ksj-lang-failopen--> am Sektionsanfang.
"""

import os

os.environ.setdefault("JWT_SECRET", "t")
os.environ.setdefault("DATABASE_URL", "sqlite:///t.db")

import inspect
import re

import pytest


_DE_PARA = ("<p>Das Projekt trägt sich auch ohne externe Zuschüsse und bleibt "
            "wirtschaftlich stabil über die kommenden Monate.</p>")
_DE_PARA_EN = ("<p>The project sustains itself without external grants and remains "
               "economically stable over the coming months.</p>")

_FAILOPEN = "<!--ksj-lang-failopen-->"


def _briefing(lang):
    return {"lang": lang, "branche": "medien"}


# =============================================================================
# 1 — Size-Final-Pass: lang-Gate (P0)
# =============================================================================

class TestSizeFinalPassLangGate:
    EN_SOLO = ("<p>Good governance and clear KPIs are essential. "
               "Keep an audit trail for every AI decision you make.</p>")
    EN_TEAM = ("<p>Your team should adopt a lightweight Compliance Framework "
               "for all AI tools in daily use.</p>")

    def test_en_solo_input_unchanged(self):
        from services.solo_final_pass import apply_size_final_pass
        out, stats = apply_size_final_pass(self.EN_SOLO, segment="solo", lang="en")
        assert out == self.EN_SOLO                      # byte-identisch
        assert stats["total"] == 0
        assert "Spielregeln" not in out and "Kennzahlen" not in out
        assert "Protokollierung" not in out

    def test_en_team_input_unchanged(self):
        from services.solo_final_pass import apply_size_final_pass
        out, stats = apply_size_final_pass(self.EN_TEAM, segment="team", lang="en")
        assert out == self.EN_TEAM
        assert stats["total"] == 0
        assert "Regelwerk" not in out

    def test_en_gb_variant_also_gated(self):
        from services.solo_final_pass import apply_size_final_pass
        out, _ = apply_size_final_pass(self.EN_SOLO, segment="solo", lang="en-GB")
        assert out == self.EN_SOLO

    def test_de_default_byte_identical_to_explicit_de(self):
        """DE-Verhalten unverändert: Default (kein lang) == lang='de' und
        die Eindeutschungs-Maps greifen weiterhin."""
        from services.solo_final_pass import apply_size_final_pass
        de_html = "<p>Mit guter Governance und einem Audit-Trail startest du sicher.</p>"
        out_default, stats_default = apply_size_final_pass(de_html, segment="solo")
        out_de, stats_de = apply_size_final_pass(de_html, segment="solo", lang="de")
        assert out_default == out_de                    # byte-identisch
        assert stats_default == stats_de
        assert "Governance" not in out_de               # Map greift bei DE weiter
        assert "Audit-Trail" not in out_de

    def test_de_team_map_still_applies(self):
        from services.solo_final_pass import apply_size_final_pass
        de_html = "<p>Ein Compliance-Framework hilft dem Team im Alltag.</p>"
        out, stats = apply_size_final_pass(de_html, segment="team", lang="de")
        assert "Regelwerk" in out
        assert stats["total"] >= 1

    def test_sections_wrapper_en_noop(self):
        from services.solo_final_pass import apply_size_final_pass_to_sections
        sections = {"X_HTML": self.EN_SOLO}
        out, stats = apply_size_final_pass_to_sections(sections, segment="solo", lang="en")
        assert out["X_HTML"] == self.EN_SOLO
        assert stats["total"] == 0

    def test_callsites_pass_report_lang(self):
        """Source-Contract: beide Aufrufstellen in analyze_briefing reichen
        report_lang durch."""
        import gpt_analyze as g
        src = inspect.getsource(g.analyze_briefing)
        assert "apply_size_final_pass(final_html, segment=_segment, run_id=run_id, lang=report_lang)" in src
        assert "apply_size_final_pass_to_sections(" in src
        assert "sections, segment=_segment, run_id=run_id, lang=report_lang" in src


# =============================================================================
# 2 — Judge-Heal: EN-Prompt-Variante (P1)
# =============================================================================

class TestJudgeHealLang:
    def _run(self, monkeypatch, lang):
        from services import anthropic_client
        from services.judge_heal import run_judge_heal
        captured = {}

        def fake_structured(prompt, **kw):
            captured["prompt"] = prompt
            captured["system_prompt"] = kw.get("system_prompt", "")
            return {"edits": []}

        monkeypatch.setattr(anthropic_client, "call_anthropic_structured", fake_structured)
        sections = {
            "EXECUTIVE_SUMMARY_HTML": "<p>" + "x" * 80 + "</p>",
        }
        judge_result = {"ampel": "gelb", "checks": [
            {"id": "dubletten", "verdict": "gelb", "begruendung": "doppelt"},
        ]}
        run_judge_heal(sections, {"hauptleistung": "Videoproduktion"},
                       judge_result, run_id="t", lang=lang)
        return captured

    def test_en_prompt_contains_no_german_instruction(self, monkeypatch):
        captured = self._run(monkeypatch, "en")
        prompt = captured["prompt"]
        assert "deutsch" not in prompt.lower().replace("kundenangaben", "")
        assert "Sie-Form" not in prompt
        assert "English" in prompt
        assert "surgical edits" in prompt
        assert "English" in captured["system_prompt"]

    def test_en_prompt_keeps_contract(self, monkeypatch):
        from services.judge_heal import MAX_EDITS, MIN_FIND_LEN
        captured = self._run(monkeypatch, "en")
        assert f"max. {MAX_EDITS}" in captured["prompt"]
        assert str(MIN_FIND_LEN) in captured["prompt"]

    def test_de_prompt_unchanged(self, monkeypatch):
        captured = self._run(monkeypatch, "de")
        prompt = captured["prompt"]
        assert "Ton beibehalten " in prompt
        assert "(Sie-Form, beratend, deutsch)" in prompt
        assert "chirurgische Edits" in prompt
        assert captured["system_prompt"].startswith("Du bist ein präziser Report-Chirurg")

    def test_de_is_default(self, monkeypatch):
        from services import anthropic_client
        from services.judge_heal import run_judge_heal
        captured = {}

        def fake_structured(prompt, **kw):
            captured["prompt"] = prompt
            return {"edits": []}

        monkeypatch.setattr(anthropic_client, "call_anthropic_structured", fake_structured)
        sections = {"EXECUTIVE_SUMMARY_HTML": "<p>" + "x" * 80 + "</p>"}
        judge_result = {"ampel": "gelb", "checks": [
            {"id": "budget", "verdict": "gelb", "begruendung": "b"}]}
        run_judge_heal(sections, {}, judge_result, run_id="t")  # ohne lang
        assert "(Sie-Form, beratend, deutsch)" in captured["prompt"]

    def test_callsite_passes_lang(self):
        import gpt_analyze as g
        src = inspect.getsource(g.analyze_briefing)
        assert re.search(r"run_judge_heal\(sections, answers, _judge_result, run_id=run_id,\s*lang=report_lang\)", src)


# =============================================================================
# 3 — Post-Render-Healer: Signatur-Kontrakt + lang-Gate (P1)
# =============================================================================

class TestHealFinalHtmlReactivated:
    def test_signature_has_no_hauptleistung(self):
        from services.report_healer import heal_final_html
        params = inspect.signature(heal_final_html).parameters
        assert "hauptleistung" not in params
        assert "lang" in params
        assert params["lang"].default == "de"

    def test_callsite_matches_signature(self):
        """Der Aufruf in gpt_analyze verwendet nur existierende Kwargs und
        wendet den Healer auf result['html'] an (render() liefert ein Dict —
        der alte Guard `isinstance(result, str)` war immer False)."""
        import gpt_analyze as g
        src = inspect.getsource(g.analyze_briefing)
        assert 'result["html"] = heal_final_html(' in src
        call = src.split('result["html"] = heal_final_html(')[1].split(")")[0]
        assert "hauptleistung" not in call
        from services.report_healer import heal_final_html
        valid = set(inspect.signature(heal_final_html).parameters)
        for kwarg in re.findall(r"(\w+)=", call):
            assert kwarg in valid, f"Kwarg {kwarg} nicht in heal_final_html-Signatur"

    def test_call_with_callsite_kwargs_does_not_raise(self):
        from services.report_healer import heal_final_html
        out = heal_final_html(
            "<p>Test HTML with enough content to be healed properly.</p>",
            segment="team",
            canonical_payback_months=3.5,
            lang="de",
        )
        assert isinstance(out, str) and out

    def test_en_solo_no_germanization(self):
        """lang-Gate: die Eindeutschungs-Subpässe (SOLO-Map, Governance→
        Spielregeln, 3.5→3,5) laufen bei EN nicht."""
        from services.report_healer import heal_final_html
        html = ("<p>Good governance and a clean audit trail matter. "
                "The Executive Summary explains the rollout.</p>")
        out = heal_final_html(html, segment="solo", lang="en")
        assert "Spielregeln" not in out and "spielregeln" not in out
        assert "governance" in out
        assert "Executive Summary" in out          # keine "Kurzfassung"
        assert "Prüfung" not in out

    def test_de_solo_germanization_still_works(self):
        from services.report_healer import heal_final_html
        html = "<p>Starke Governance sichert die Einführung dauerhaft ab.</p>"
        out = heal_final_html(html, segment="solo", lang="de")
        assert "Governance" not in out
        assert "Spielregeln" in out

    def test_de_decimal_normalization_en_untouched(self):
        from services.report_healer import heal_final_html
        de = "<p>Amortisation nach 3.5 Monaten erreicht.</p>"
        out_de = heal_final_html(de, segment="team", lang="de")
        assert "3,5 Monaten" in out_de
        # EN: deutsches Dezimalformat wird NICHT erzwungen
        out_en = heal_final_html(de, segment="team", lang="en")
        assert "3.5 Monaten" in out_en

    def test_language_neutral_fixes_still_run_for_en(self):
        """Sprachneutrale Reparaturen (leere <p>, Prompt-Leak-Removal)
        laufen auch bei EN weiter."""
        from services.report_healer import heal_final_html
        html = "<p>Solid English content stays here.</p><p>  </p><p></p>"
        out = heal_final_html(html, segment="team", lang="en")
        assert "Solid English content" in out
        assert "<p></p>" not in out


# =============================================================================
# 4 — Marker-Echo / Transposition / Prosa (P1/P2)
# =============================================================================

class TestMarkerEchoValidation:
    def _tag_balance(self, html):
        import gpt_analyze as g
        return g._lang_sweep_tag_balance(html)

    def test_marker_echo_keeps_original_and_tag_balance(self, monkeypatch):
        """Audit-Repro: LLM erwähnt den Marker im Text erneut → früher wurde
        der Block mit dem Fragment nach dem zweiten Marker überschrieben
        (Tag-Bilanz -1, offenes </p>). Jetzt: Original bleibt."""
        import gpt_analyze as g

        def fake_llm(section_key, prompt, **kw):
            return ("<<<BLOCK 0>>>\n<p>The marker "
                    "<<<BLOCK 0>>> appears again in prose.</p>")

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert _DE_PARA in out["X_HTML"]
        body = out["X_HTML"].replace(_FAILOPEN, "")
        assert self._tag_balance(body) == self._tag_balance(_DE_PARA)

    def test_prose_answer_without_markers_keeps_original(self, monkeypatch):
        import gpt_analyze as g
        monkeypatch.setattr(
            g, "_call_llm_for_section",
            lambda **k: "Sure! Here is the translation you asked for: <p>text</p>")
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert out["X_HTML"] == _FAILOPEN + _DE_PARA

    def test_tag_balance_violation_keeps_block(self, monkeypatch):
        """Ersatz mit fehlendem schließenden Tag wird verworfen."""
        import gpt_analyze as g
        monkeypatch.setattr(
            g, "_call_llm_for_section",
            lambda **k: ("<<<BLOCK 0>>>\n<p>The project sustains itself without "
                         "external grants and remains stable going forward."))
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert _DE_PARA in out["X_HTML"]
        assert "sustains itself" not in out["X_HTML"]

    def test_partial_failure_replaces_only_valid_blocks(self, monkeypatch):
        """Fail-open PRO BLOCK: valider Block wird ersetzt, invalider bleibt
        original; Sektion trägt die Fail-open-Markierung."""
        import gpt_analyze as g
        de_2 = ("<p>Die Planung wird mit dem Team abgestimmt und für die "
                "kommenden Wochen dokumentiert und geprüft.</p>")

        def fake_llm(section_key, prompt, **kw):
            return (f"<<<BLOCK 0>>>\n{_DE_PARA_EN}\n"
                    "<<<BLOCK 1>>>\n<p>broken block")   # Tag-Bilanz verletzt

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        sections = {"X_HTML": _DE_PARA + de_2}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert "external grants" in out["X_HTML"]        # Block 0 ersetzt
        assert de_2 in out["X_HTML"]                     # Block 1 original
        assert out["X_HTML"].startswith(_FAILOPEN)

    def test_length_implausible_replacement_rejected(self, monkeypatch):
        """[P2] Längen-Plausibilität: Ersatz unter 30 % der Originallänge
        (typisch bei vertauschten/verstümmelten Markern) wird verworfen."""
        import gpt_analyze as g
        monkeypatch.setattr(
            g, "_call_llm_for_section",
            lambda **k: "<<<BLOCK 0>>>\n<p>ok</p>")
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert _DE_PARA in out["X_HTML"]
        assert "<p>ok</p>" not in out["X_HTML"]

    def test_oversized_replacement_rejected(self, monkeypatch):
        import gpt_analyze as g
        blown_up = "<p>" + ("The project remains stable. " * 60) + "</p>"
        monkeypatch.setattr(
            g, "_call_llm_for_section",
            lambda **k: f"<<<BLOCK 0>>>\n{blown_up}")
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert _DE_PARA in out["X_HTML"]

    def test_valid_translation_still_applied(self, monkeypatch):
        import gpt_analyze as g
        monkeypatch.setattr(
            g, "_call_llm_for_section",
            lambda **k: f"<<<BLOCK 0>>>\n{_DE_PARA_EN}")
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert out["X_HTML"] == _DE_PARA_EN              # kein Marker, sauber ersetzt
        assert _FAILOPEN not in out["X_HTML"]


# =============================================================================
# 5 — Heuristik: False Negatives / False Positives (P2)
# =============================================================================

class TestGermanHeuristic:
    def test_fn_repro_article_sentence_detected(self):
        """Audit-Repro (FN): 'Das Team plant den Start im August' hatte mit
        der alten Stopwortliste 0 Treffer."""
        import gpt_analyze as g
        assert g._text_looks_german("Das Team plant den Start im August")

    def test_fn_more_articles(self):
        import gpt_analyze as g
        assert g._text_looks_german(
            "Dieser Ansatz passt zum Zeitplan, dass beim Start zur Not alles bereit ist")

    def test_english_still_negative(self):
        import gpt_analyze as g
        assert not g._text_looks_german(
            "This approach fits the timeline and the team can start right away.")
        assert not g._text_looks_german(
            "The plan covers implementation, training and monitoring in detail.")

    def test_fp_repro_bafa_name_neutralized(self):
        """Audit-Repro (FP): EN-Block mit 'BAFA – Förderung von
        Unternehmensberatungen für KMU' wurde als deutsch klassifiziert."""
        import gpt_analyze as g
        assert not g._text_looks_german(
            "The BAFA – Förderung von Unternehmensberatungen für KMU grant "
            "covers consulting projects for small companies.")

    def test_fp_quoted_study_title_neutralized(self):
        import gpt_analyze as g
        assert not g._text_looks_german(
            "The study „Künstliche Intelligenz für den Mittelstand und die "
            "Verwaltung“ shows strong adoption across all sectors.")

    def test_german_text_with_program_name_still_detected(self):
        """Ein echter deutscher Satz bleibt trotz Namens-Neutralisierung
        deutsch (Stopwörter/Umlaute außerhalb des Namens)."""
        import gpt_analyze as g
        assert g._text_looks_german(
            "Für Ihr Vorhaben ist die Games-Förderung des Bundes eine geeignete "
            "Wahl und ein guter Einstieg in die Förderlandschaft.")

    def test_sweep_makes_no_call_for_en_block_with_program_name(self, monkeypatch):
        import gpt_analyze as g
        calls = []

        def _boom(**k):
            calls.append(1)
            raise AssertionError("EN-Block mit Programmnamen darf keinen Call auslösen")

        monkeypatch.setattr(g, "_call_llm_for_section", _boom)
        sections = {"FOERDER_HTML": (
            "<p>Apply for the BAFA – Förderung von Unternehmensberatungen für KMU "
            "programme to co-finance your consulting project.</p>")}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert not calls
        assert "BAFA – Förderung von Unternehmensberatungen für KMU" in out["FOERDER_HTML"]


# =============================================================================
# 6 — Budget-Priorisierung + Shadow-Twin-Dedup (P2)
# =============================================================================

class TestBudgetPriorityAndTwins:
    def _distinct_de(self, i):
        return (f"<p>Variante {i}: Das Projekt trägt sich auch ohne externe "
                f"Zuschüsse und bleibt über die kommenden Monate stabil.</p>")

    def test_executive_summary_translated_before_annex(self, monkeypatch):
        """Audit-Repro: 12 Anhang-Sektionen (Dict-Reihenfolge) verbrauchten
        das 10er-Budget, die Executive Summary blieb deutsch."""
        import gpt_analyze as g
        calls = []

        def fake_llm(section_key, prompt, **kw):
            calls.append(section_key)
            return None

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        # KIS-1279: Default-Budget ist jetzt 40 (ENV) — Test pinnt 10, er
        # prüft die Priorisierung unter Budget-Erschöpfung.
        monkeypatch.setenv("LANG_SWEEP_MAX_LLM_CALLS", "10")
        sections = {f"ANNEX_{i:02d}_HTML": self._distinct_de(i) for i in range(12)}
        sections["EXECUTIVE_SUMMARY_HTML"] = self._distinct_de(90)
        sections["QUICK_WINS_HTML"] = self._distinct_de(91)
        g._en_language_sweep_sections(sections, _briefing("en"))
        assert len(calls) == 10                          # gepinntes Budget
        assert calls[0] == "EXECUTIVE_SUMMARY_HTML"
        assert calls[1] == "QUICK_WINS_HTML"

    def test_html_keys_before_plain_keys(self, monkeypatch):
        import gpt_analyze as g
        calls = []

        def fake_llm(section_key, prompt, **kw):
            calls.append(section_key)
            return None

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        sections = {
            "notes": self._distinct_de(1),
            "RISK_HTML": self._distinct_de(2),
        }
        g._en_language_sweep_sections(sections, _briefing("en"))
        assert calls == ["RISK_HTML", "notes"]

    def test_twin_translated_once_and_copied(self, monkeypatch):
        """Audit-Repro: 4 Calls für 2 logische Sektionen (UPPER-_HTML +
        lowercase-Schattenkey mit identischem Inhalt)."""
        import gpt_analyze as g
        calls = []

        def fake_llm(section_key, prompt, **kw):
            calls.append(section_key)
            return f"<<<BLOCK 0>>>\n{_DE_PARA_EN}"

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        de_2 = ("<p>Die Planung wird mit dem Team abgestimmt und für die "
                "kommenden Wochen sauber dokumentiert und geprüft.</p>")
        de_2_en = ("<p>The planning is aligned with the team and cleanly "
                   "documented and reviewed for the coming weeks.</p>")

        def fake_llm2(section_key, prompt, **kw):
            calls.append(section_key)
            if "Zuschüsse" in prompt:
                return f"<<<BLOCK 0>>>\n{_DE_PARA_EN}"
            return f"<<<BLOCK 0>>>\n{de_2_en}"

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm2)
        sections = {
            "EXECUTIVE_SUMMARY_HTML": _DE_PARA,
            "executive_summary": _DE_PARA,
            "QUICK_WINS_HTML": de_2,
            "quick_wins": de_2,
        }
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert len(calls) == 2                           # 2 statt 4 Calls
        assert out["EXECUTIVE_SUMMARY_HTML"] == _DE_PARA_EN
        assert out["executive_summary"] == _DE_PARA_EN   # Twin kopiert
        assert out["QUICK_WINS_HTML"] == de_2_en
        assert out["quick_wins"] == de_2_en

    def test_failed_twin_inherits_failopen(self, monkeypatch):
        import gpt_analyze as g
        calls = []

        def fake_llm(section_key, prompt, **kw):
            calls.append(section_key)
            return None

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        sections = {
            "EXECUTIVE_SUMMARY_HTML": _DE_PARA,
            "executive_summary": _DE_PARA,
        }
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert len(calls) == 1
        assert out["EXECUTIVE_SUMMARY_HTML"] == _FAILOPEN + _DE_PARA
        assert out["executive_summary"] == _FAILOPEN + _DE_PARA


# =============================================================================
# 7 — Fail-open-Markierung (P2)
# =============================================================================

class TestFailOpenMarker:
    def test_marker_constant_value(self):
        import gpt_analyze as g
        assert g._LANG_SWEEP_FAILOPEN_MARKER == "<!--ksj-lang-failopen-->"

    def test_failed_section_gets_marker_once(self, monkeypatch):
        import gpt_analyze as g
        monkeypatch.setattr(g, "_call_llm_for_section", lambda **k: None)
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert out["X_HTML"].startswith(_FAILOPEN)
        assert out["X_HTML"].count(_FAILOPEN) == 1
        # Idempotent: zweiter Sweep-Lauf fügt keinen zweiten Marker an
        out2 = g._en_language_sweep_sections(dict(out), _briefing("en"))
        assert out2["X_HTML"].count(_FAILOPEN) == 1

    def test_successful_section_has_no_marker(self, monkeypatch):
        import gpt_analyze as g
        monkeypatch.setattr(
            g, "_call_llm_for_section",
            lambda **k: f"<<<BLOCK 0>>>\n{_DE_PARA_EN}")
        sections = {"X_HTML": _DE_PARA}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert _FAILOPEN not in out["X_HTML"]

    def test_failed_section_not_token_resanitized(self, monkeypatch):
        """fail-open-Sektionen werden von der Locale-Token-Nachsanitisierung
        ausgenommen (kein Denglisch im bewusst behaltenen deutschen Block)."""
        import gpt_analyze as g
        monkeypatch.setattr(g, "_call_llm_for_section", lambda **k: None)
        de_with_token = ("<p>Nutzen Sie das Vier-Augen-Prinzip für alle "
                         "kritischen Freigaben und dokumentieren Sie die Schritte.</p>")
        sections = {"X_HTML": de_with_token}
        out = g._en_language_sweep_sections(sections, _briefing("en"))
        assert "Vier-Augen-Prinzip" in out["X_HTML"]     # NICHT tokenisiert
        assert out["X_HTML"].startswith(_FAILOPEN)

    def test_de_run_never_gets_marker(self, monkeypatch):
        import gpt_analyze as g

        def _boom(**k):
            raise AssertionError("DE-Lauf: kein Call")

        monkeypatch.setattr(g, "_call_llm_for_section", _boom)
        sections = {"X_HTML": _DE_PARA, "LANG": "de"}
        before = dict(sections)
        out = g._en_language_sweep_sections(sections, _briefing("de"))
        assert out == before                             # byte-identisch, kein Marker


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
