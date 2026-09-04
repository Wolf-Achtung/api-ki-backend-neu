# -*- coding: utf-8 -*-
"""KIS-1288: Die Sparte kommt an.

Branchen-Audit vom 04.09.2026 (docs/branchen-audit-2026-09-04.md): Der
Fragebogen erhebt ``medien_sparte`` mit sieben Werten. Bis dahin erreichte
sie einen Prompt von 139, die Fallstudie und das Deckblatt. Strategiebericht,
Potenzialanalyse und Resilienz-Check kannten sie nicht; der Resilienz-Check
fuehrte eine eigene Slug-Liste mit drei falschen Schluesseln.

Stufe 1 legt Leitungen, keinen Inhalt: ein Baustein fuer das Label, die
Sparte im Strategie- und KPA-Kontext, die Persona im Strategiebericht,
Content Creation in Persona und ``ki_rechte``.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from services import medien_sparte as ms

REPO = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# 1. Ein Baustein, eine Wahrheit                                              #
# --------------------------------------------------------------------------- #
class TestBaustein:

    def test_sieben_sparten_wie_im_registry(self):
        from field_registry import fields
        registry = [o["value"] for o in fields["medien_sparte"]["options"]]
        assert ms.SPARTEN == registry

    def test_labels_wie_im_registry(self):
        from field_registry import fields
        for o in fields["medien_sparte"]["options"]:
            assert ms.LABELS_DE[o["value"]] == o["label"]

    def test_en_labels_wie_im_normalizer(self):
        from services.answers_normalizer import MEDIEN_SPARTEN_LABELS_EN
        for s in ms.SPARTEN:
            assert ms.LABELS_EN[s] == MEDIEN_SPARTEN_LABELS_EN[s]

    @pytest.mark.parametrize("wert,erwartet", [
        ("musik_audio", "Musik / Audio / Tonstudio / Podcast"),
        ("Musik / Audio / Tonstudio / Podcast", "Musik / Audio / Tonstudio / Podcast"),
        ("MUSIK_AUDIO", "Musik / Audio / Tonstudio / Podcast"),
        ("  games ", "Games / Interactive"),
    ])
    def test_label_de(self, wert, erwartet):
        assert ms.label(wert) == erwartet

    def test_label_en(self):
        assert ms.label("verlag_publishing", lang="en") == "Publishing / editorial"
        assert ms.label("Verlag / Publishing / Redaktion", lang="en") == "Publishing / editorial"

    @pytest.mark.parametrize("wert", ["", None, "film_tv", "verlag", "agentur", "unfug"])
    def test_unbekannt_bleibt_leer(self, wert):
        """Nie ein Roh-Slug im Bericht."""
        assert ms.label(wert) == ""
        assert ms.slug(wert) == ""

    def test_aus_antworten(self):
        assert ms.aus_antworten({"medien_sparte": "post_vfx"}) == "Postproduktion / VFX / Animation"
        assert ms.aus_antworten({}) == ""
        assert ms.aus_antworten(None) == ""


# --------------------------------------------------------------------------- #
# 2. Strategiebericht: Persona und Sparte im System-Prompt                     #
# --------------------------------------------------------------------------- #
SYSTEM_DE = ("Du bist ein erfahrener KI-Strategieberater für den deutschen Mittelstand.\n"
             "Du erstellst professionelle, umsetzbare Strategieberichte.\n\nREGELN:\n1. ...")
SYSTEM_EN = ("You are an experienced AI strategy consultant for small and medium-sized "
             "businesses (SMEs).\nYou produce professional, actionable strategy reports.")


class TestStrategiePersona:

    def test_ohne_konfiguration_bleibt_alles(self, monkeypatch):
        monkeypatch.delenv("REPORT_PERSONA_PATH", raising=False)
        monkeypatch.delenv("REPORT_PERSONA_TEXT", raising=False)
        from services.medien_sparte_prompt import persona_und_sparte
        assert persona_und_sparte(SYSTEM_DE) == SYSTEM_DE

    def test_persona_ersetzt_die_mittelstands_zeile(self, monkeypatch):
        monkeypatch.setenv("REPORT_PERSONA_PATH", "prompts/de/_persona_medien.md")
        monkeypatch.delenv("REPORT_PERSONA_TEXT", raising=False)
        from services.medien_sparte_prompt import persona_und_sparte
        out = persona_und_sparte(SYSTEM_DE)
        assert "deutschen Mittelstand" not in out
        assert out.startswith("Du bist Senior-Strategieberater für KI-Einführung in der Medien-")
        # Der Rest des Prompts bleibt unangetastet.
        assert "REGELN:\n1. ..." in out
        assert "Du erstellst professionelle, umsetzbare Strategieberichte." in out

    def test_sparte_wird_genannt(self, monkeypatch):
        monkeypatch.delenv("REPORT_PERSONA_PATH", raising=False)
        monkeypatch.delenv("REPORT_PERSONA_TEXT", raising=False)
        from services.medien_sparte_prompt import persona_und_sparte
        out = persona_und_sparte(SYSTEM_DE, sparte="Musik / Audio / Tonstudio / Podcast")
        zeilen = out.split("\n")
        assert zeilen[0] == SYSTEM_DE.split("\n")[0]
        assert "Musik / Audio / Tonstudio / Podcast" in zeilen[1]
        assert "zuschneiden" in zeilen[1]

    def test_englisch_behaelt_persona_nennt_sparte(self, monkeypatch):
        monkeypatch.setenv("REPORT_PERSONA_PATH", "prompts/de/_persona_medien.md")
        from services.medien_sparte_prompt import persona_und_sparte
        out = persona_und_sparte(SYSTEM_EN, sparte="Games / interactive", lang="en")
        assert out.startswith("You are an experienced AI strategy consultant")
        assert "Games / interactive" in out.split("\n")[1]
        assert "Du bist" not in out

    def test_pipeline_ruft_den_baustein(self):
        quelle = (REPO / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        assert "persona_und_sparte" in quelle
        assert '"medien_sparte": _medien_sparte' in quelle

    def test_firmenname_kommt_nicht_aus_den_antworten(self):
        """CI-Invariante: Der Firmenname wird nirgends erhoben — und nirgends gelesen."""
        quelle = (REPO / "services" / "strategy_pipeline.py").read_text(encoding="utf-8")
        assert 'briefing_data.get(\n                "unternehmen_name"' not in quelle
        assert re.search(r'"firmenname":\s*"your company" if _is_en else "Ihr Unternehmen"', quelle)


# --------------------------------------------------------------------------- #
# 3. Potenzialanalyse: Sparte im Kontext und in allen vier Prompts             #
# --------------------------------------------------------------------------- #
class TestKpaSparte:

    @pytest.mark.parametrize("lang", ["de", "en"])
    @pytest.mark.parametrize("name", [
        "gc_strategic_analysis", "gc_implementation_plan",
        "gc_risk_assessment", "gc_next_steps",
    ])
    def test_prompt_nennt_die_sparte_bedingt(self, lang, name):
        text = (REPO / "prompts" / lang / f"{name}.md").read_text(encoding="utf-8")
        assert "{% if MEDIEN_SPARTE_LABEL %}" in text
        assert "{{MEDIEN_SPARTE_LABEL}}" in text
        assert "{% endif %}" in text

    def test_bedingung_rendert_leer_ohne_sparte(self):
        """Kein 'Sparte: ' mit leerem Wert im Prompt."""
        from services.prompt_loader import load_prompt
        vars_ohne = {"BRANCHE_LABEL": "Medien & Kreativwirtschaft", "HAUPTLEISTUNG": "x",
                     "MEDIEN_SPARTE_LABEL": "", "COMPANY_SIZE": "team",
                     "UNTERNEHMENSGROESSE_LABEL": "Kleines Team"}
        out = load_prompt("gc_risk_assessment", lang="de", vars_dict=vars_ohne)
        text = out if isinstance(out, str) else str(out)
        assert "Sparte:" not in text

    def test_bedingung_rendert_mit_sparte(self):
        from services.prompt_loader import load_prompt
        vars_mit = {"BRANCHE_LABEL": "Medien & Kreativwirtschaft", "HAUPTLEISTUNG": "x",
                    "MEDIEN_SPARTE_LABEL": "Verlag / Publishing / Redaktion",
                    "COMPANY_SIZE": "team", "UNTERNEHMENSGROESSE_LABEL": "Kleines Team"}
        out = load_prompt("gc_risk_assessment", lang="de", vars_dict=vars_mit)
        text = out if isinstance(out, str) else str(out)
        assert "Sparte:** Verlag / Publishing / Redaktion" in text

    def test_deep_dive_reicht_das_label_durch(self):
        quelle = (REPO / "services" / "gamechanger_deep_dive.py").read_text(encoding="utf-8")
        assert quelle.count("'MEDIEN_SPARTE_LABEL'") >= 2


# --------------------------------------------------------------------------- #
# 4. Resilienz-Check: kein Roh-Slug mehr                                       #
# --------------------------------------------------------------------------- #
class TestResilienzSparte:

    def test_eigene_slugliste_ist_weg(self):
        quelle = (REPO / "services" / "resilienz_pipeline.py").read_text(encoding="utf-8")
        assert "_SPARTE_LABELS = {" not in quelle
        assert '"film_tv":' not in quelle   # als Dict-Schluessel, nicht im Kommentar

    @pytest.mark.parametrize("slug,label", [
        ("produktion", "Film-/TV-Produktion"),
        ("verlag_publishing", "Verlag / Publishing / Redaktion"),
        ("agentur_design", "Agentur / Werbung / PR / Webdesign"),
    ])
    def test_die_drei_vorher_falschen(self, slug, label):
        """Genau die Schluessel, die vorher als Roh-Slug gedruckt wurden."""
        assert ms.label(slug) == label


# --------------------------------------------------------------------------- #
# 5. Alle sieben Sparten in Persona und ki_rechte                              #
# --------------------------------------------------------------------------- #
class TestAlleSiebenGenannt:

    def test_persona_nennt_alle_sieben(self):
        text = (REPO / "prompts" / "de" / "_persona_medien.md").read_text(encoding="utf-8")
        for stichwort in ("Film-/TV-Produktion", "Postproduktion", "Tonstudio",
                          "Agenturen", "Verlage", "Games", "Content Creation"):
            assert stichwort in text, stichwort

    @pytest.mark.parametrize("lang,stichwort", [
        ("de", "Content Creation:"), ("en", "content creation:"),
    ])
    def test_ki_rechte_nennt_content_creation(self, lang, stichwort):
        text = (REPO / "prompts" / lang / "ki_rechte_kennzeichnung.md").read_text(encoding="utf-8")
        assert stichwort in text

    def test_env_example_dokumentiert_die_vertikale(self):
        text = (REPO / ".env.example").read_text(encoding="utf-8")
        assert "REPORT_PERSONA_PATH" in text
        assert "VISIBLE_BRANCHES" in text
