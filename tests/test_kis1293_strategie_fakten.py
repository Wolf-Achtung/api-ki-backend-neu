# -*- coding: utf-8 -*-
"""KIS-1293 (Lauf KIS1272, 04.09.2026): Der Strategiebericht erfand Werkzeuge
und kannte das Datum nicht.

Befund im Kapitel „Tool-Landschaft" (S4): „Adobe Sensei", „Legiscope",
„TrustArc", „OpenDP" als Empfehlungen; Preismodelle und DSGVO-Einstufungen
im Fließtext; „Vendor-Audit-Status: nicht bestanden" an Claude und Runway
geheftet; als Quelle „Vendor-Audit-Status Report 1 (Kundenunterlagen)".
Befund im Risiko-Kapitel (S9): „Copilot, Adobe Sensei und Runway ML fallen
voraussichtlich unter hochriskante KI-Systeme" und „das Stichtagsdatum
02.08.2026 ist in wenigen Wochen erreicht" — vier Wochen nach dem Datum.

Ursache: S4 bekam keinen Faktenblock (KIS-1281 galt nur für R1), S9 bekam
die Anweisung „wenn das Reportdatum vor dem Stichtag liegt", aber kein
Reportdatum.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from services.ai_act_stichtag import (
    ART50_STICHTAG, art50_prompt_text, art50_satz, risikoklasse_regel, verstrichen,
)
from services.kuratierte_fakten import build_tool_fakten_strategie, build_tool_fakten

REPO = Path(__file__).resolve().parent.parent
VOR = date(2026, 6, 1)
NACH = date(2026, 9, 4)
MEDIEN = {"branche": "medien", "unternehmensgroesse": "team", "medien_sparte": "post_vfx"}


class TestStichtag:
    def test_stichtag_ist_der_zweite_august(self):
        assert ART50_STICHTAG == date(2026, 8, 2)
        assert not verstrichen(VOR)
        assert verstrichen(ART50_STICHTAG)
        assert verstrichen(NACH)

    @pytest.mark.parametrize("lang,seit,ab", [
        ("de", "gelten seit dem 2. August 2026", "gelten ab dem 2. August 2026"),
        ("en", "have applied since 2 August 2026", "apply from 2 August 2026"),
    ])
    def test_html_satz_kippt_am_stichtag(self, lang, seit, ab):
        assert art50_satz(lang, VOR) == ab
        assert art50_satz(lang, NACH) == seit

    @pytest.mark.parametrize("lang", ["de", "en"])
    def test_prompt_nach_stichtag_verbietet_zukunftsform(self, lang):
        text = art50_prompt_text(lang, NACH)
        assert "04.09.2026" in text and "02.08.2026" in text
        if lang == "de":
            assert "GELTEN SEIT" in text and "in wenigen" in text  # als Verbot genannt
            assert "VERBOTEN" in text
        else:
            assert "HAVE APPLIED SINCE" in text and "FORBIDDEN" in text

    @pytest.mark.parametrize("lang", ["de", "en"])
    def test_prompt_vor_stichtag_nennt_resttage(self, lang):
        text = art50_prompt_text(lang, VOR)
        assert "62" in text  # 01.06. → 02.08. = 62 Tage
        assert "VERBOTEN" not in text and "FORBIDDEN" not in text

    def test_risikoklasse_regel(self):
        assert "Anhang III" in risikoklasse_regel("de")
        assert "Annex III" in risikoklasse_regel("en")


class TestFaktenblockStrategie:
    def test_block_hat_kopf_regeln_und_urls(self):
        block = build_tool_fakten_strategie(MEDIEN, lang="de")
        assert "GEPRÜFTE WERKZEUG-DATEN" in block
        assert "nie für ein empfohlenes Werkzeug" in block
        assert "https://" in block, "S4 braucht Anbieteradressen für die Quellen"
        assert "Hosting:" in block
        assert block.rstrip().endswith("=== ENDE ===")

    def test_en_block(self):
        block = build_tool_fakten_strategie(MEDIEN, lang="en")
        assert "VERIFIED TOOL DATA" in block and "https://" in block

    def test_sparte_wirkt_im_block(self):
        vfx = build_tool_fakten_strategie(MEDIEN, lang="de")
        assert "Topaz Video AI" in vfx or "Frame.io" in vfx

    def test_nie_leer(self, monkeypatch):
        import services.tools_recommender as tr
        monkeypatch.setattr(tr, "recommend_tools", lambda *a, **k: [])
        de = build_tool_fakten_strategie(MEDIEN, lang="de")
        en = build_tool_fakten_strategie(MEDIEN, lang="en")
        assert "Kein Faktenblock" in de and "kein Audit-Status" in de
        assert "No fact block" in en

    def test_r1_block_unveraendert_ohne_url(self):
        """KIS-1281-Block für R1 bleibt wie er war — keine URL."""
        assert "https://" not in build_tool_fakten(MEDIEN)


class TestPrompts:
    @pytest.mark.parametrize("modul,var", [
        ("prompts.strategy_prompts", "STRATEGY_PROMPTS"),
        ("prompts.strategy_prompts_en", "STRATEGY_PROMPTS_EN"),
    ])
    def test_s4_und_s8_tragen_die_platzhalter(self, modul, var):
        import importlib
        prompts = getattr(importlib.import_module(modul), var)
        assert "{kuratierte_tools}" in prompts["S4"]
        assert "{ai_act_stichtag}" in prompts["S8"]
        assert "{ai_act_risikoklasse}" in prompts["S8"]
        assert "in wenigen Wochen" not in prompts["S8"]
        assert "in a few weeks" not in prompts["S8"]

    def test_s4_verlangt_keine_dsgvo_einstufung_mehr(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN
        assert "DSGVO-Konformität (ja/nein/teilweise)" not in STRATEGY_PROMPTS["S4"]
        assert "GDPR compliance (yes/no/partial)" not in STRATEGY_PROMPTS_EN["S4"]
        assert "keine Beträge" in STRATEGY_PROMPTS["S4"]

    def test_pipeline_fuellt_die_schluessel(self):
        src = (REPO / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        for key in ("kuratierte_tools", "ai_act_stichtag", "ai_act_risikoklasse"):
            assert f'base_context["{key}"]' in src, key


class TestFesteTexte:
    def test_kpa_impressum_sagt_seit(self):
        for f in ("gamechanger_deep_dive_v1.html", "gamechanger_deep_dive_en.html"):
            t = (REPO / "templates" / f).read_text(encoding="utf-8")
            assert "gelten ab dem 2. August 2026" not in t
            assert "apply from 2 August 2026" not in t

    def test_pflichtenmatrix_sagt_seit(self):
        from services.ai_act_module import _generate_duty_matrix_de, _generate_duty_matrix_en
        assert "gelten seit dem 2. August 2026" in _generate_duty_matrix_de("minimal", "medien", True)
        assert "have applied since 2 August 2026" in _generate_duty_matrix_en("minimal", "media", True)

    def test_feldhilfe_sagt_seit(self):
        src = (REPO / "services" / "field_templates.py").read_text(encoding="utf-8")
        assert "ab August 2026" not in src and "from August 2026" not in src


class TestNachlaufKIS1273:
    """Lauf KIS1273 (nach dem ersten Fix): S4 sauber, aber S3b nannte „Adobe
    Sensei" und „Azure Cognitive Services" als KI-Hebel, Copilot bekam die
    Hosting-Zeile von Frame.io, und die R1-Fördertabelle zeigte dem
    VFX-Studio weiter die Games-Förderung — eigener Pfad in extra_sections."""

    def test_r1_kerntabelle_filtert_nach_sparte(self):
        from services.extra_sections import build_core_funding_table_html
        basis = {"BRANCHE_LABEL": "Medien & Kreativwirtschaft", "BUNDESLAND_LABEL": "Berlin",
                 "UNTERNEHMENSGROESSE_LABEL": "Team (2-10)", "country": "DE"}
        ohne = build_core_funding_table_html(dict(basis))
        vfx = build_core_funding_table_html(dict(basis, MEDIEN_SPARTE_LABEL="Postproduktion / VFX / Animation"))
        assert "Games-Förderung" in ohne
        assert "Games-Förderung" not in vfx
        # KIS-1297: DFFF steht seit dem Antragsstopp (20.08.2026) auf paused;
        # das Filmerbe-Programm ist der beantragbare Film-Marker.
        assert "Filmerbe" in vfx and "ProFIT" in vfx
        assert "DFFF" not in vfx and "GMPF" not in vfx

    def test_r1_kerntabelle_versteht_en_label(self):
        from services.extra_sections import build_core_funding_table_html
        from services.medien_sparte import LABELS_EN
        basis = {"BRANCHE_LABEL": "Media", "BUNDESLAND_LABEL": "Berlin",
                 "UNTERNEHMENSGROESSE_LABEL": "Team (2-10)", "country": "DE",
                 "MEDIEN_SPARTE_LABEL": LABELS_EN["musik_audio"]}
        html = build_core_funding_table_html(basis, lang="en")
        assert "Filmerbe" not in html and "Games" not in html

    def test_tool_namen_fuer_s3b(self):
        from services.kuratierte_fakten import tool_namen_strategie
        namen = tool_namen_strategie(MEDIEN)
        assert "Runway" in namen and "," in namen
        assert "Adobe Sensei" not in namen

    def test_tool_namen_nie_leer(self, monkeypatch):
        import services.tools_recommender as tr
        from services.kuratierte_fakten import tool_namen_strategie
        monkeypatch.setattr(tr, "recommend_tools", lambda *a, **k: [])
        assert "Gattungsbegriff" in tool_namen_strategie(MEDIEN)

    def test_s3b_traegt_die_namensliste(self):
        from prompts.strategy_prompts import STRATEGY_PROMPTS
        from prompts.strategy_prompts_en import STRATEGY_PROMPTS_EN
        assert "{kuratierte_tools_namen}" in STRATEGY_PROMPTS["S3b"]
        assert "{kuratierte_tools_namen}" in STRATEGY_PROMPTS_EN["S3b"]
        assert "erfundenen Berichte" in STRATEGY_PROMPTS["S3b"]

    def test_header_regel_fuer_stack_software(self):
        de = build_tool_fakten_strategie(MEDIEN, lang="de")
        en = build_tool_fakten_strategie(MEDIEN, lang="en")
        assert "laut Anbieter prüfen" in de and "einer anderen Zeile" in de
        assert "check with the vendor" in en

    def test_pipeline_fuellt_namensliste(self):
        src = (REPO / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        assert 'base_context["kuratierte_tools_namen"]' in src

    def test_waechter_erkennt_erfundenes_werkzeug(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("cr", REPO / "scripts" / "compare_reports.py")
        cr = importlib.util.module_from_spec(spec); spec.loader.exec_module(cr)
        pruefe = dict((n, f) for n, _, f in cr.PRUEFUNGEN)["erfundenes_werkzeug"]
        assert pruefe("Einsatz von KI-Tools wie Adobe Sensei für Bildanalyse")
        assert pruefe("Runway und Frame.io im Review") is None


class TestSofortStartPreis:
    """R1 S.8 (Sofort-Start) zeigte feste Preise aus dem Code — ohne
    Prüfdatum. Regel aus KIS-1280 gilt auch hier."""

    def test_ohne_pruefdatum_kein_preis(self):
        from services.sofort_start_generator import _sofort_preis
        assert _sofort_preis({"name": "Claude Team", "preis": "25-30 €/Nutzer/Monat"}) == "siehe Anbieterseite"
        assert _sofort_preis({"name": "Make / n8n", "preis": "ab 9 €/Monat"}, is_en=True) == "see vendor site"
        assert _sofort_preis({"name": "Unbekanntes Werkzeug", "preis": "1 €"}) == "siehe Anbieterseite"

    def test_geprueftes_werkzeug_zeigt_seed_preis(self):
        import json
        from services.sofort_start_generator import _sofort_preis
        seed = json.loads((REPO / "data" / "tools_seed.json").read_text(encoding="utf-8"))
        geprueft = next(t for t in seed if t.get("verified_at"))
        assert _sofort_preis({"name": geprueft["name"], "preis": "x"}) == geprueft["price"]

    def test_seite_traegt_keinen_festen_preis_mehr(self):
        from services.sofort_start_generator import generate_sofort_start_html
        for lang, verweis in (("de", "siehe Anbieterseite"), ("en", "see vendor site")):
            html = generate_sofort_start_html(
                hauptleistung="Postproduktion", branche="medien", company_size="team",
                zeitersparnis_prioritaet="Sichtung", stundensatz=95, medien_sparte="post_vfx",
                lang=lang,
            )
            assert "€/Nutzer/Monat" not in html and "ab 9 €/Monat" not in html
            assert "/user/month" not in html and "from €9/month" not in html
            assert verweis in html, lang
