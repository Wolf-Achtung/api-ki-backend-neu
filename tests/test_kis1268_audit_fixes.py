# -*- coding: utf-8 -*-
"""KIS-1268: Fixes aus dem Re-Audit vom 2026-07-06 (4 Sweeps über main).

(1) s5_vision ging im Formular-Flow verloren: strategy.html sendet das Feld,
    aber StrategyQuestionsCreate deklarierte es nicht → Pydantic verwarf die
    Eingabe still, {s5_vision} im Strategie-Prompt blieb immer leer.
(2) Frage-Chips-Kopplung: Die Ja/Nein-Chips (KIS-1264) brauchen eine
    Ja/Nein-geformte Sonnet-Frage — FIELD_DESCRIPTIONS ankert die Frageform.
(3) KPI-Kontext-Box (FIX-B35d-N39002) landete nur im nicht gerenderten
    RECOMMENDATIONS_HTML (Klasse KIS-1262/1264) → Doppel-Injektion in ENGINE.
(4) Benchmark sagte "exzellent (Note A)" / "hervorragende" ab 80 — synchron
    mit get_score_label jetzt ab 85 (Entscheidung Wolf 2026-07-05).
(5) Gamechanger contact-box ohne Umbruchschutz (Waisen-Klasse KIS-1264).
(6) funding_de(.en).json führte go_digital/digitalbonus_bayern noch als
    Laufzeitdaten — Schutz ruhte allein auf der Runtime-Blacklist.
(7) TESTUSERS war nicht synchron mit core/whitelist.py (5 Adressen fehlten).
(8) Auth-/Chat-Logs gaben Nutzer-E-Mails ungeschwärzt aus → core/pii.py.
(9) DE-Förder-Prompts hardcodeten 2025 als "aktuell" (EN war schon dynamisch).
"""
from __future__ import annotations

import json


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. s5_vision überlebt den Formular-Flow
# =========================================================================

class TestS5VisionPersisted:

    def test_schema_declares_field(self):
        from routes.strategy import StrategyQuestionsCreate
        assert "s5_vision" in StrategyQuestionsCreate.model_fields
        q = StrategyQuestionsCreate(
            s1_budget="2000_10000", s2_zeitrahmen="1_3_monate",
            s3_prioritaeten=["kosten"], s4_engpass="zeit",
            s6_foerderinteresse="ja", s7_entscheidung="sofort",
            s5_vision="Der Laden soll laufen, auch wenn ich nicht da bin.")
        assert q.s5_vision.startswith("Der Laden")

    def test_model_column_and_to_dict(self):
        from models import StrategyQuestion
        assert hasattr(StrategyQuestion, "s5_vision")
        src = _read("models.py")
        assert '"s5_vision": self.s5_vision,' in src

    def test_persistence_writes_field(self):
        src = _read("routes/strategy.py")
        assert "existing.s5_vision = questions.s5_vision" in src
        assert "s5_vision=questions.s5_vision," in src

    def test_migration_file_exists(self):
        src = _read("migrations/2026-07-06_add_s5_vision_postgres.sql")
        assert "ADD COLUMN IF NOT EXISTS s5_vision TEXT" in src


# =========================================================================
# 2. Frage-Chips-Kopplung für geschaeftsmodell_evolution
# =========================================================================

class TestQuestionChipCoupling:

    def test_field_description_anchors_yes_no_form(self):
        from services.chat_conversation import FIELD_DESCRIPTIONS
        d = FIELD_DESCRIPTIONS["geschaeftsmodell_evolution"]
        assert "Ja/Nein-Frage" in d
        assert "Chips" in d
        # Die drei Chip-Richtungen spiegeln sich in der Frage
        assert "Produkte" in d and "Vertriebswege" in d


# =========================================================================
# 3. KPI-Kontext-Box erreicht die gerenderte Sektion
# =========================================================================

class TestKpiBoostReachesRender:

    def test_engine_double_injection_present(self):
        src = _read("gpt_analyze.py")
        assert src.count("[KIS-1268][KPI-BOOST-ENGINE]") == 1
        idx = src.find('sections["RECOMMENDATIONS_HTML"] = reco_html')
        block = src[idx:idx + 900]
        assert "RECOMMENDATIONS_ENGINE_HTML" in block

    def test_template_renders_engine_not_shadow(self):
        src = _read("templates/pdf_template_v7.html")
        assert "RECOMMENDATIONS_ENGINE_HTML" in src
        assert "RECOMMENDATIONS_HTML|safe" not in src


# =========================================================================
# 4. Benchmark-Wording synchron mit get_score_label (85)
# =========================================================================

class TestBenchmarkThreshold85:

    def _report(self, pct):
        from services.benchmark_engine import (BenchmarkPosition,
                                               BenchmarkRadar, BenchmarkReport)
        positions = [BenchmarkPosition(domain=d, company_value=1.0,
                                       industry_median=0.8,
                                       industry_top_quartile=1.2,
                                       score_percentile=pct, narrative="T")
                     for d in ("kpi", "tools", "risk")]
        return BenchmarkReport(positions=positions,
                               radar=BenchmarkRadar(categories=["A"], scores=[0.8]))

    def test_below_85_is_not_grade_a(self):
        # 80-84 hieß vorher "A/exzellent" — jetzt "B" (synchron mit gut-Band)
        assert self._report(82.0).competitiveness_grade == "B"
        assert self._report(84.0).competitiveness_grade == "B"

    def test_85_plus_is_grade_a(self):
        # 86 statt exakt 85: der gewichtete Durchschnitt identischer
        # Perzentile kann float-bedingt bei 84.999… landen.
        assert self._report(86.0).competitiveness_grade == "A"
        assert self._report(95.0).competitiveness_grade == "A"

    def test_position_phrases_at_85(self):
        from services.benchmark_engine import (_get_position_phrase_de,
                                               _get_position_phrase_en)
        assert _get_position_phrase_de(84) == "gute"
        assert _get_position_phrase_de(85) == "hervorragende"
        assert _get_position_phrase_en(84) == "good"
        assert _get_position_phrase_en(85) == "excellent"


# =========================================================================
# 5. Gamechanger contact-box umbruchgeschützt
# =========================================================================

class TestGamechangerContactBox:

    def test_class_has_break_inside_avoid(self):
        src = _read("templates/gamechanger_deep_dive_v1.html")
        idx = src.find(".contact-box {")
        assert "break-inside: avoid" in src[idx:idx + 300]

    def test_print_rule_lists_contact_box(self):
        src = _read("templates/gamechanger_deep_dive_v1.html")
        idx = src.find("@media print")
        assert ".contact-box" in src[idx:idx + 400]


# =========================================================================
# 6. Laufzeit-Förderdaten ohne tote/geblacklistete Programme
# =========================================================================

class TestRuntimeFundingHygiene:

    def test_no_dead_programmes_in_runtime_files(self):
        # KIS-1297: funding_de.json geloescht (kein Report las sie)
        for path in ("data/funding/funding_de_en.json",):
            d = json.load(open(path, encoding="utf-8"))
            ids = {p.get("id") for p in d["programmes"]}
            assert "go_digital" not in ids, path
            assert "digitalbonus_bayern" not in ids, path
            assert d["last_updated"] >= "2026-07"


# =========================================================================
# 7. Whitelist ↔ TESTUSERS synchron
# =========================================================================

class TestWhitelistTestusersSync:

    def test_testusers_covers_whitelist_minus_admin_and_ci(self):
        from core.whitelist import EMAIL_WHITELIST, ADMIN_EMAILS
        import setup_database
        ci = {e for e in EMAIL_WHITELIST
              if e.endswith("@example.com") or e.startswith("test-v7")}
        expected = EMAIL_WHITELIST - ADMIN_EMAILS - ci
        assert {u.lower() for u in setup_database.TESTUSERS} == expected


# =========================================================================
# 8. E-Mail-Maskierung in Auth-/Chat-Logs
# =========================================================================

class TestLogMasking:

    def test_mask_email_helper(self):
        from core.pii import mask_email
        assert mask_email("wolf.hohl@web.de") == "wo***@web.de"
        assert mask_email(None) == "(none)"
        assert mask_email("kaputt") == "***"

    def test_auth_logs_masked(self):
        src = _read("routes/auth.py")
        assert "from core.pii import mask_email" in src
        # keine Log-Zeile mehr mit rohem payload.email
        for line in src.splitlines():
            if "log." in line and "payload.email" in line:
                assert "mask_email" in line, line

    def test_chat_briefing_log_masked(self):
        src = _read("routes/chat.py")
        assert "_kis1268_mask(user_email)" in src


# =========================================================================
# 9. DE-Förder-Prompts ohne 2025-Hardcodes
# =========================================================================

class TestPromptYearHardcodes:

    def test_funding_engine_de_is_relative(self):
        src = _read("prompts/de/funding_engine_v2.md")
        assert "2025 = Aktuell verfügbar" not in src
        assert "Aktuelles Jahr = Aktuell verfügbar" in src
        assert "{{report_date}}" in src
        assert '"deadline": "Q2 2025"' not in src

    def test_exec_snapshot_de_is_relative(self):
        src = _read("prompts/de/exec_snapshot.md")
        assert "(2025/2026/2027)" not in src
        assert "Förder-Timeline 2025–2027" not in src
        assert "{{report_date}}" in src


# =========================================================================
# KIS-1264: Whitelist zusaetzlich aus EXTRA_WHITELIST
# =========================================================================

class TestExtraWhitelistAusEnv:
    """Freischalten ohne Deploy — ein Backend-Deploy bricht laufende
    Report-Generierungen ab, das soll eine Freischaltung nicht kosten."""

    def test_env_adresse_wird_freigeschaltet(self, monkeypatch):
        from core.whitelist import is_whitelisted
        assert not is_whitelisted("neu@example.org")
        monkeypatch.setenv("EXTRA_WHITELIST", "neu@example.org")
        assert is_whitelisted("neu@example.org")

    def test_mehrere_adressen_und_schreibweise(self, monkeypatch):
        from core.whitelist import is_whitelisted
        monkeypatch.setenv("EXTRA_WHITELIST", " Eins@Example.ORG , zwei@example.org ")
        assert is_whitelisted("eins@example.org")
        assert is_whitelisted("ZWEI@example.org")

    def test_eintrag_ohne_at_wird_verworfen(self, monkeypatch):
        from core.whitelist import all_whitelisted
        monkeypatch.setenv("EXTRA_WHITELIST", "kaputt.de,gut@example.org")
        wirksam = all_whitelisted()
        assert "gut@example.org" in wirksam
        assert "kaputt.de" not in wirksam

    def test_leere_env_aendert_nichts(self, monkeypatch):
        from core.whitelist import EMAIL_WHITELIST, all_whitelisted
        monkeypatch.setenv("EXTRA_WHITELIST", "")
        assert all_whitelisted() == EMAIL_WHITELIST

    def test_env_macht_niemanden_zum_admin(self, monkeypatch):
        # Admin bleibt eine Sicherheitsgrenze, keine Betriebseinstellung.
        from core.whitelist import is_admin, is_whitelisted
        monkeypatch.setenv("EXTRA_WHITELIST", "moechtegern@example.org")
        assert is_whitelisted("moechtegern@example.org")
        assert not is_admin("moechtegern@example.org")

    def test_require_whitelisted_akzeptiert_env_adresse(self, monkeypatch):
        from core.whitelist import require_whitelisted
        monkeypatch.setenv("EXTRA_WHITELIST", "neu@example.org")
        assert require_whitelisted("Neu@Example.org") == "neu@example.org"

    def test_neu_freigeschaltete_adressen_sind_drin(self):
        from core.whitelist import is_whitelisted
        for adresse in ("jan.bonath@white-spot-films.com", "jbfilm@outlook.de",
                        "mail@ennoreese.de", "michelmorales@me.com"):
            assert is_whitelisted(adresse), adresse
