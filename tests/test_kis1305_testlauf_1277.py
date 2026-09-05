# -*- coding: utf-8 -*-
"""KIS-1305 — Befunde aus Testlauf KIS1277 (05.09.2026, nach KIS-1304).

R1: „DaVinci Resolve (Neural System)" (S. 15/16), 12-Monats-Ausblick endet
mit „Jahresabschluss." (S. 31), Persönliche Einschätzung erklärt das
FB1-Budget für maßgeblich (S. 33). Strategie: S1 „Top-Handlungsfeld:
strategische Handlungsfelder" (S. 3), Benchmark-Tabelle mit 75 %/96 % ohne
Quelle und „Ihr Unternehmen 0 %" (S. 8), nackte Werkzeugliste allein auf
S. 21, „EU-gehostete Tools wie … DaVinci Resolve" (S. 36), „EU AI Act
(Verordnung 2021/0691)" (S. 37).
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _lade_compare_reports():
    spec = importlib.util.spec_from_file_location("compare_reports", ROOT / "scripts" / "compare_reports.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# 1. Produktnamen überleben den Anglizismus-Fixer
# ---------------------------------------------------------------------------

class TestProduktnameEngine:
    def test_grammatik_fixer_schont_neural_engine(self):
        from services.content_quality_enforcer import apply_grammar_fixes
        out, _ = apply_grammar_fixes(
            "Starter-Kit: DaVinci Resolve (Neural Engine) und Unreal Engine; "
            "die Risk Engine v3 bleibt Fließtext."
        )
        assert "DaVinci Resolve (Neural Engine)" in out
        assert "Unreal Engine" in out
        assert "Risk System v3" in out

    def test_siezen_fixer_schont_neural_engine(self):
        from services.content_quality_enforcer import apply_extended_siezen
        out, _ = apply_extended_siezen("DaVinci Resolve (Neural Engine) und eine Engine.")
        assert "Neural Engine" in out
        assert "eine System" in out or "eine Engine" not in out

    def test_solo_blacklist_schont_neural_engine(self):
        from services.report_healer import final_solo_terminology_cleanup
        sections = {"TOOLS_HTML": "DaVinci Resolve (Neural Engine) statt einer Engine für alles."}
        final_solo_terminology_cleanup(sections, "solo")
        assert "Neural Engine" in sections["TOOLS_HTML"]
        assert "einer Baustein" in sections["TOOLS_HTML"]


# ---------------------------------------------------------------------------
# 2. Verwaiste Einwort-Absätze am Sektionsende
# ---------------------------------------------------------------------------

class TestEinwortAbsatz:
    def test_jahresabschluss_faellt(self):
        from services.report_healer import _strip_trailing_orphan_headings
        html = "<section><p>Der Prüfschritt bleibt beim Menschen.</p><p>Jahresabschluss.</p></section>"
        out = _strip_trailing_orphan_headings(html)
        assert "Jahresabschluss" not in out
        assert out.endswith("</section>")

    def test_strong_einwort_faellt(self):
        from services.report_healer import _strip_trailing_orphan_headings
        html = "<p>Ein Satz.</p><p><strong>Jahresabschluss:</strong></p>"
        assert "Jahresabschluss" not in _strip_trailing_orphan_headings(html)

    def test_meilenstein_satz_bleibt(self):
        from services.report_healer import _strip_trailing_orphan_headings
        html = "<p>Ein Satz.</p><p><strong>Meilenstein Jahresende:</strong> Board-Entscheidung für Jahr 2.</p>"
        assert _strip_trailing_orphan_headings(html) == html

    def test_b39_pass_entfernt_einwort(self):
        from services.report_healer import apply_segment_budget
        html = "<section><p>" + "Ein vollständiger Satz mit Inhalt. " * 6 + "</p><p>Jahresabschluss.</p></section>"
        out, _ = apply_segment_budget({"ROADMAP_12M_HTML": html}, "team")
        assert "Jahresabschluss" not in out["ROADMAP_12M_HTML"]


# ---------------------------------------------------------------------------
# 3. Budget: FB2 ist maßgeblich — auch für die Persönliche Einschätzung
# ---------------------------------------------------------------------------

class TestBudgetKontext:
    def test_shared_context_traegt_fb2_als_investitionsbudget(self):
        src = (ROOT / "gpt_analyze.py").read_text(encoding="utf-8")
        assert '_ctx_answers["investitionsbudget"] = _bud_eff' in src
        assert '_ctx_answers["investitionsbudget_readiness_fragebogen_ueberholt"] = _bud_fb1' in src
        assert "ist überholt" in src

    @pytest.mark.parametrize("pfad", ["prompts/de/advisor_note.md", "prompts/en/advisor_note.md"])
    def test_advisor_prompt_kennt_budgetregel(self, pfad):
        text = (ROOT / pfad).read_text(encoding="utf-8")
        assert "{{INVESTITIONSBUDGET}}" in text
        assert "BUDGET" in text


# ---------------------------------------------------------------------------
# 4. S1: Top-Handlungsfeld ist nie das Kapitel-Etikett
# ---------------------------------------------------------------------------

class TestTopHandlungsfeld:
    def test_etikett_wird_uebersprungen(self):
        from services.strategy_pipeline import _extract_top_handlungsfeld
        s3 = ("<h3>Strategische Handlungsfelder</h3><p>Einleitung.</p>"
              "<h3>Handlungsfeld 1: Governance-Rahmen für KI-Nutzung</h3><p>…</p>")
        assert _extract_top_handlungsfeld(s3) == "Governance-Rahmen für KI-Nutzung"

    def test_fallback_aus_dimensionen(self):
        from services.strategy_pipeline import _extract_top_handlungsfeld
        s3 = "<h3>Handlungsfelder im Überblick</h3><p>Nur Prosa.</p>"
        assert _extract_top_handlungsfeld(s3, "Governance & Spielregeln (64/100)") == "Governance & Spielregeln (64/100)"

    def test_kein_fester_platzhalter_bei_leerem_s3(self):
        from services.strategy_pipeline import _extract_top_handlungsfeld
        assert _extract_top_handlungsfeld("", "Sicherheit & Datenschutz (72/100)") == "Sicherheit & Datenschutz (72/100)"

    def test_aufrufer_gibt_fallback_mit(self):
        src = (ROOT / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        assert re.search(r"_extract_top_handlungsfeld\(\s*sections\[\"S3\"\],\s*fallback=", src)


# ---------------------------------------------------------------------------
# 5. Enhancer: Quellenblöcke werden auch mit Template-CSS umgewandelt
# ---------------------------------------------------------------------------

class TestQuellenblock:
    CSS = "<style>.sources-footer { font-size: 8pt; }</style>"

    def test_div_sources_wird_trotz_css_zur_zeile(self):
        from services.html_enhancer import _transform_sources
        html = (self.CSS + '<section><p>Text.</p><div class="sources"><ul>'
                '<li><a href="https://www.amberscript.com">Amberscript</a></li>'
                '<li>Topaz Video AI</li><li>DaVinci Resolve</li></ul></div></section>')
        out = _transform_sources(html)
        assert "<ul>" not in out
        assert 'class="sources-footer"' in out
        assert "Amberscript</a> · Topaz Video AI · DaVinci Resolve." in out

    def test_quellen_absatz_wird_eingepackt_und_nicht_doppelt(self):
        from services.html_enhancer import _transform_sources
        html = self.CSS + "<p>Quellen: KI-Readiness-Analyse Report 1, EU AI Act.</p>"
        out = _transform_sources(html)
        assert out.count('class="sources-footer"') == 1
        assert _transform_sources(out).count('class="sources-footer"') == 1

    def test_div_mit_einem_absatz_nicht_verschachtelt(self):
        from services.html_enhancer import _transform_sources
        out = _transform_sources('<div class="sources"><p>Quellen: nur Text.</p></div>')
        assert "<p><p>" not in out and out.count("<p") == 1

    def test_strategie_enhancer_ende_zu_ende(self):
        from services.html_enhancer import enhance_strategy_html
        html = (self.CSS + '<section><h2>Tool-Landschaft</h2><p>Text.</p>'
                '<div class="sources"><ul><li>Microsoft 365 Copilot</li><li>Amberscript</li>'
                '<li>Frame.io (Adobe)</li></ul></div></section>')
        out = enhance_strategy_html(html)
        assert "<li>" not in out
        assert "Microsoft 365 Copilot · Amberscript · Frame.io (Adobe)." in out

    def test_faktenblock_verlangt_eine_zeile(self):
        from services.kuratierte_fakten import _KOPF_TOOLS_STRATEGIE_DE, _KOPF_TOOLS_STRATEGIE_EN
        assert 'class="sources"' in _KOPF_TOOLS_STRATEGIE_DE and "keine Liste" in _KOPF_TOOLS_STRATEGIE_DE
        assert 'class="sources"' in _KOPF_TOOLS_STRATEGIE_EN and "no bullet list" in _KOPF_TOOLS_STRATEGIE_EN


# ---------------------------------------------------------------------------
# 6. AI-Act-Verordnungsnummer
# ---------------------------------------------------------------------------

class TestVerordnungsnummer:
    def test_erfundene_nummer_wird_ersetzt(self):
        from services.strategy_sanitizer import ai_act_verordnungsnummer_korrigieren
        out, n = ai_act_verordnungsnummer_korrigieren(
            "<p>Quellen: EU AI Act (Verordnung 2021/0691) · DSGVO und BDSG.</p>")
        assert n == 1
        assert "2021/0691" not in out
        assert "(Verordnung (EU) 2024/1689)" in out

    def test_eu_praefix_bleibt_einfach(self):
        from services.strategy_sanitizer import ai_act_verordnungsnummer_korrigieren
        out, n = ai_act_verordnungsnummer_korrigieren("KI-Verordnung (EU) 2021/0206 gilt seit 2024.")
        assert n == 1 and "(EU) 2024/1689" in out and "(EU) (EU)" not in out

    def test_richtige_nummer_unveraendert(self):
        from services.strategy_sanitizer import ai_act_verordnungsnummer_korrigieren
        text = "EU AI Act (Verordnung (EU) 2024/1689), Art. 50."
        assert ai_act_verordnungsnummer_korrigieren(text) == (text, 0)

    def test_pass_laeuft_in_sanitize(self):
        from services.strategy_sanitizer import sanitize_strategy_sections
        html = "<p>" + "Ein sauberer Satz ohne Auffälligkeit. " * 5 + "Quellen: EU AI Act (Verordnung 2021/0691).</p>"
        out = sanitize_strategy_sections({"S8": html})
        assert "2024/1689" in out["S8"] and "2021/0691" not in out["S8"]


# ---------------------------------------------------------------------------
# 7. Prompts: Hosting „lokal" und belegte Benchmarks
# ---------------------------------------------------------------------------

class TestPrompts:
    def test_s8_und_s4_kennen_lokal(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS as DE
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN as EN
        assert "lokal installiert" in DE["S8"] and "lokal installiert" in DE["S4"]
        assert "installed locally" in EN["S8"] and "installed locally" in EN["S4"]

    def test_faktenblock_kennt_lokal(self):
        from services.kuratierte_fakten import _KOPF_TOOLS_STRATEGIE_DE, _KOPF_TOOLS_STRATEGIE_EN
        assert "lokal installiert" in _KOPF_TOOLS_STRATEGIE_DE
        assert "installed locally" in _KOPF_TOOLS_STRATEGIE_EN

    def test_s2_verlangt_quelle_je_zahl_und_kennt_den_stack(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS as DE
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN as EN
        assert "{s5_software}" in DE["S2"] and "Richtwert" in DE["S2"] and "0 %" in DE["S2"]
        assert "{s5_software}" in EN["S2"] and "guide value" in EN["S2"]

    def test_s2_platzhalter_sind_im_kontext(self):
        src = (ROOT / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        assert '"s5_software": strategy_questions.get("s5_software"' in src
        assert '"s8_erfahrung"' in src


# ---------------------------------------------------------------------------
# 8. Wächter in compare_reports
# ---------------------------------------------------------------------------

class TestWaechter:
    @pytest.fixture(scope="class")
    def cr(self):
        return _lade_compare_reports()

    def test_verordnungsnummer(self, cr):
        assert cr._ai_act_verordnungsnummer("Quellen: EU AI Act (Verordnung 2021/0691) · DSGVO")
        assert cr._ai_act_verordnungsnummer("Quellen: EU AI Act (Verordnung (EU) 2024/1689) · DSGVO") is None
        assert cr._ai_act_verordnungsnummer("AI Act, Art. 50, gilt seit 02.08.2026") is None

    def test_lokal_als_eu(self, cr):
        assert cr._lokal_als_eu_gehostet(
            "Nutzen Sie EU-gehostete Tools wie Amberscript für Transkription und DaVinci Resolve für Postproduktion.")
        assert cr._lokal_als_eu_gehostet("DaVinci Resolve läuft lokal; EU-gehostet ist Amberscript.") is None
        assert cr._lokal_als_eu_gehostet(
            "Priorisieren Sie EU-gehostete Lösungen wie Amberscript und lokale Desktop-Tools wie Topaz.") is None

    def test_einwort_absatz(self, cr):
        text = ("Jeder Versuch, diesen Prüfschritt zu überspringen, untergräbt das Vertrauen.\n"
                "Jahresabschluss.\n"
                "Auf einen Blick: Der strategische Bruchpunkt.\n")
        assert cr._einwort_absatz_am_kapitelende(text) == "Jahresabschluss."
        ok = ("Jeder Versuch, diesen Prüfschritt zu überspringen, untergräbt das Vertrauen.\n"
              "Jahresabschluss.\n"
              "Management-Review mit ROI-Nachweis und Budget-Planung für Jahr 2.\n")
        assert cr._einwort_absatz_am_kapitelende(ok) is None

    def test_pruefungen_registriert(self, cr):
        namen = {p[0] for p in cr.PRUEFUNGEN}
        assert {"ai_act_verordnungsnummer", "lokal_als_eu_gehostet", "einwort_absatz_am_kapitelende"} <= namen
