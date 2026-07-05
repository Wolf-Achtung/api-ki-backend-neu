# -*- coding: utf-8 -*-
"""KIS-1264: User-Feedback + Befunde aus Lauf 1125 (KIS-1242, Handel/Team).

(1) Chips zur Geschäftsmodell-Frage (User-Screenshot): Die alten drei
Chips waren drei Beratersprech-Varianten von "Ja" ohne Nein-Pfad —
jetzt Klartext mit drei distinkten Richtungen inkl. ehrlichem Nein.

(2) Heal-Zahlenschutz: Der Budget-Edit wurde verworfen ("neue Zahl(en)
erfunden: ['10.000', '50.000']"), obwohl die Zahlen aus der Kundenangabe
investitionsbudget='10000_50000' stammten. Kundenangaben-Ziffern sind
jetzt erlaubt, Vergleich separator-normalisiert ('10.000' ≙ '10000').

(3) ROI-Einordnung (KIS-1251) landete nur in BUSINESS_CASE_HTML — das
Template rendert BUSINESS_CASE_ENGINE_HTML (KIS-1262). Lauf 1125 hatte
ROI 1 % und die Box fehlte im PDF. Doppel-Injektion wie beim Budget-Gate.

(4) Judge/Heal urteilen jetzt über die GERENDERTE Business-Case-Sektion
(ENGINE zuerst), und die deterministischen Einordnungs-Boxen werden
garantiert vollständig in den Digest gehoben (Limit-sicher).

(5) Re-Judge-Ratchet: dubletten flippte im Re-Judge 🟢→🟡 (Judge-Varianz)
und hielt die Gesamt-Ampel auf GELB. Checks, die vor dem Heal gruen
waren, können im Re-Judge nicht mehr schlechter werden; geflaggte
Checks bleiben ungeschönt.

(6) Thin pages S.3/S.5/S.31: TOC-Zeile kompakter, Score-Interpretation+
Kompetenz-Hinweis unteilbar, Kontakt-Kapitel unteilbar.
"""
from __future__ import annotations


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. Chips: Klartext, drei distinkte Richtungen, Nein-Pfad vorhanden
# =========================================================================

class TestGeschaeftsmodellChips:

    def test_three_distinct_directions(self):
        from services.field_templates import FIELD_EXAMPLES
        chips = FIELD_EXAMPLES["geschaeftsmodell_evolution"]
        assert len(chips) == 3
        # Ja (Produkt), Ja (Markt/Vertrieb), ehrliches Nein
        assert any(c.startswith("Ja,") and "Produkte" in c for c in chips)
        assert any(c.startswith("Ja,") and ("Vertriebswege" in c or "Kundengruppen" in c)
                   for c in chips)
        assert any(c.startswith("Eher nein") for c in chips)

    def test_no_consultant_speak_left(self):
        from services.field_templates import FIELD_EXAMPLES
        joined = " ".join(FIELD_EXAMPLES["geschaeftsmodell_evolution"])
        for phrase in ("skalierbares", "vermarkten", "eigenständige Leistung"):
            assert phrase not in joined

    def test_word_count_contract_kept(self):
        # Derselbe Kontrakt wie test_kis_1138 (4–8 Wörter) — hier explizit,
        # damit ein Regress sofort auf diesen Fix zeigt.
        from services.field_templates import FIELD_EXAMPLES
        for chip in FIELD_EXAMPLES["geschaeftsmodell_evolution"]:
            assert 4 <= len(chip.split()) <= 8, chip


# =========================================================================
# 2. Heal-Zahlenschutz: Kundenangaben-Ziffern + Separator-Normalisierung
# =========================================================================

class TestHealNumberGuard:

    _SENTENCE = ("Die kalkulierte Gesamtinvestition bewegt sich im Rahmen "
                 "Ihres Budgets und bleibt jederzeit steuerbar im Projektverlauf.")

    def _sections(self):
        return {"BUSINESS_CASE_HTML": "<p>Kontext davor.</p><p>" + self._SENTENCE
                + "</p><p>Kontext danach mit ausreichend Länge im Text.</p>"}

    def test_budget_band_from_answers_accepted(self):
        # Der exakte Lauf-1125-Fall: replace zitiert '10.000–50.000 €' aus
        # answers['investitionsbudget'] = '10000_50000'.
        from services.judge_heal import validate_edit, _canon_numbers, _answer_numbers
        sections = self._sections()
        canon = _canon_numbers(sections) | _answer_numbers(
            {"investitionsbudget": "10000_50000"})
        key, reason = validate_edit(
            {"section": "BUSINESS_CASE_HTML", "find": self._SENTENCE,
             "replace": self._SENTENCE.replace(
                 "im Rahmen Ihres Budgets",
                 "im Rahmen Ihres Budgets von 10.000–50.000 €")},
            sections, canon)
        assert key == "BUSINESS_CASE_HTML", reason

    def test_truly_invented_numbers_still_rejected(self):
        from services.judge_heal import validate_edit, _answer_numbers
        sections = self._sections()
        canon = _answer_numbers({"investitionsbudget": "10000_50000"})
        key, reason = validate_edit(
            {"section": "BUSINESS_CASE_HTML", "find": self._SENTENCE,
             "replace": self._SENTENCE + " Der ROI liegt bei 87.500 €."},
            sections, canon)
        assert key is None
        assert "erfunden" in reason

    def test_run_judge_heal_passes_answers_to_apply(self):
        src = _read("services/judge_heal.py")
        assert "apply_edits(edits, sections, run_id=run_id, answers=answers)" in src


# =========================================================================
# 3. ROI-Einordnung landet in der GERENDERTEN Sektion
# =========================================================================

class TestRoiBoxInEngineSection:

    def test_roi_box_engine_injection_exists(self):
        src = _read("gpt_analyze.py")
        assert src.count("[KIS-1264][ROI-BOX-ENGINE]") == 1
        # hinter dem bestehenden BUSINESS_CASE_HTML-Zweig
        assert (src.find("[KIS-1251][ROI-EINORDNUNG] ROI")
                < src.find("[KIS-1264][ROI-BOX-ENGINE]"))

    def test_roi_box_class_is_fixc_protected(self):
        # KIS-1262 schützt hinweis-box/roi-einordnung bereits in beiden
        # Dedup-Pässen — die neue Engine-Injektion hängt davon ab.
        src = _read("services/report_healer.py")
        assert "roi-einordnung" in src


# =========================================================================
# 4. Judge & Heal sehen die gerenderte Sektion + die Boxen vollständig
# =========================================================================

class TestJudgeSeesRenderedBusinessCase:

    def test_digest_prefers_engine_html(self):
        from services.coherence_judge import build_judge_digest
        digest = build_judge_digest(
            {"BUSINESS_CASE_ENGINE_HTML": "<p>" + "Gerenderte Engine-Fassung "
             "des Business Case mit allen Kennzahlen im Auslieferungszustand. "
             "</p>" * 3,
             "BUSINESS_CASE_HTML": "<p>" + "Digest-Schattenfassung ohne "
             "Render-Relevanz für den Leser des fertigen PDF-Dokuments. "
             "</p>" * 3},
            {})
        assert "Gerenderte Engine-Fassung" in digest
        assert "Digest-Schattenfassung" not in digest

    def test_einordnungs_boxen_survive_digest_limit(self):
        # Box hängt HINTER 6000 Zeichen Fließtext (jenseits des
        # 2400er-Limits) — sie muss trotzdem im Digest stehen.
        from services.coherence_judge import build_judge_digest
        filler = "<p>" + ("Ausführlicher Business-Case-Fließtext. " * 20) + "</p>"
        box = ('<div class="hinweis-box budget-gate" style="padding:12px;">'
               "<strong>Budget-Einordnung:</strong> Die Investition liegt "
               "innerhalb Ihres angegebenen Rahmens.</div>")
        digest = build_judge_digest(
            {"BUSINESS_CASE_ENGINE_HTML": filler * 4 + box}, {})
        assert "EINORDNUNGS-BOXEN" in digest
        assert "innerhalb Ihres angegebenen Rahmens" in digest

    def test_heal_candidates_include_engine(self):
        from services.judge_heal import _HEAL_SECTION_KEYS
        assert any("BUSINESS_CASE_ENGINE_HTML" in group
                   for group in _HEAL_SECTION_KEYS)

    def test_budget_question_mentions_mittelfeld(self):
        from services.coherence_judge import _CHECK_QUESTIONS
        q = _CHECK_QUESTIONS["budget"]
        assert "80" in q  # Grenznähe-Schwelle explizit
        assert "KEINE explizite Einordnung" in q
        # KIS-1260-Kontrakt bleibt erhalten
        assert "INNERHALB des" in q and "oberen Rand" in q and "ÜBERSCHREITUNG" in q


# =========================================================================
# 5. Re-Judge-Ratchet: keine neuen Befunde im Re-Judge
# =========================================================================

class TestRejudgeRatchet:

    def _pre(self):
        return {"ampel": "gelb", "checks": [
            {"id": "budget", "verdict": "gelb", "begruendung": "fehlende Einordnung"},
            {"id": "dubletten", "verdict": "gruen", "begruendung": "ok"},
            {"id": "zahlen", "verdict": "gruen", "begruendung": "ok"},
        ]}

    def test_green_check_cannot_worsen(self):
        from services.judge_heal import apply_rejudge_ratchet
        post = {"ampel": "gelb", "checks": [
            {"id": "budget", "verdict": "gruen", "begruendung": "geheilt"},
            {"id": "dubletten", "verdict": "gelb", "begruendung": "Varianz-Flip"},
            {"id": "zahlen", "verdict": "gruen", "begruendung": "ok"},
        ]}
        sections: dict = {}
        changed = apply_rejudge_ratchet(self._pre(), post, sections)
        assert changed is True
        by_id = {c["id"]: c for c in post["checks"]}
        assert by_id["dubletten"]["verdict"] == "gruen"
        assert post["ampel"] == "gruen"  # Lauf 1125 wäre damit GRÜN gewesen
        assert sections["_COHERENCE_JUDGE_AMPEL"] == "gruen"

    def test_flagged_check_stays_honest(self):
        # budget war gelb geflaggt — bleibt der Heal wirkungslos (oder wird
        # es schlimmer), darf der Ratchet das NICHT schönen.
        from services.judge_heal import apply_rejudge_ratchet
        post = {"ampel": "rot", "checks": [
            {"id": "budget", "verdict": "rot", "begruendung": "weiter verletzt"},
            {"id": "dubletten", "verdict": "gruen", "begruendung": "ok"},
            {"id": "zahlen", "verdict": "gruen", "begruendung": "ok"},
        ]}
        sections: dict = {}
        changed = apply_rejudge_ratchet(self._pre(), post, sections)
        assert changed is False
        assert post["checks"][0]["verdict"] == "rot"
        assert "_COHERENCE_JUDGE_AMPEL" not in sections

    def test_ratchet_wired_into_heal(self):
        src = _read("services/judge_heal.py")
        assert "apply_rejudge_ratchet(judge_result, re_result, sections" in src


# =========================================================================
# 6. Thin pages S.3 / S.5 / S.31
# =========================================================================

class TestThinPageFixes:

    def test_toc_entry_more_compact(self):
        src = _read("templates/pdf_template_v7.html")
        idx = src.find(".toc-entry {")
        block = src[idx:idx + 400]
        assert "padding: 3px 0;" in block

    def test_skip_hint_kept_with_score_interpretation(self):
        src = _read("templates/pdf_template_v7.html")
        idx_wrap = src.find("KIS-1264: Score-Interpretation + Kompetenz-Hinweis unteilbar")
        idx_hint = src.find("Für Ihr Kompetenzniveau (erfahren)")
        idx_close = src.find("/KIS-1264 unteilbar")
        assert -1 < idx_wrap < idx_hint < idx_close

    def test_next_steps_section_unbreakable(self):
        src = _read("templates/pdf_template_v7.html")
        idx = src.find('id="next-steps"')
        assert idx != -1
        tag = src[src.rfind("<section", 0, idx):src.find(">", idx) + 1]
        assert "break-inside: avoid" in tag
