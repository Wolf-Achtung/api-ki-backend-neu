# -*- coding: utf-8 -*-
"""KIS-1282: Zwei Funde aus dem Lauf KIS-1266.

Der Lauf war der Beweislauf für KIS-1281. Zwei Dinge gingen daneben,
beide auf dieselbe Weise: Eine Anweisung wirkte, aber nicht dort, wo
sie gebraucht wurde.

**1. Die Leerformel stand im Prompt.** Der Annahmen-Absatz des
Strategieberichts wiederholte sich viermal wörtlich — schlimmer als im
Lauf davor, obwohl KIS-1281 eine Regel dagegen gesetzt hatte. Grund:
Der Satz war ein *Beispiel im Prompt*, viermal identisch über die
Sektionen verteilt:

    Beispiel: "Annahmen: Stabiles Marktumfeld in den nächsten 12
    Monaten; aktuelle Teamgröße bleibt bestehen; keine regulatorischen
    Verschärfungen über den EU AI Act hinaus."

Das Modell war nicht faul, sondern gehorsam. Meine Regel hatte nur eine
der vier Stellen erreicht. Ein Beispiel im Prompt schlägt jede Regel
daneben — es zeigt, was erwartet wird.

**2. Eine globale Wortersetzung traf festen Text.** In gpt_analyze.py
wandelt eine Regel ``\\bwir\\b`` in ``ich`` (Berater-Stimme im
Singular). Sie traf die Fußzeile des Werkzeug-Blocks aus KIS-1280 und
machte daraus „Preise ohne Prüfdatum weisen ich nicht aus". Die Regel
tauscht Wörter, nicht Verbformen. Statischer Text muss ihr ausweichen.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

# Der Satz, den vier Prompts als Beispiel vorgaben.
LEERFORMEL_DE = "Stabiles Marktumfeld in den nächsten 12 Monaten"
LEERFORMEL_EN = "Stable market environment over the next 12 months"


class TestKeinBeispielMitLeerformel:
    """Ein Prompt bekommt, was er vormacht."""

    def test_deutscher_prompt_gibt_die_leerformel_nicht_mehr_vor(self):
        text = (REPO / "prompts" / "strategy_prompts.py").read_text(encoding="utf-8")
        # Einmal darf sie stehen: als ausdrückliches Gegenbeispiel.
        stellen = [z for z in text.splitlines() if LEERFORMEL_DE in z]
        assert len(stellen) == 1, f"{len(stellen)} Vorkommen statt einem"
        assert "Falsch:" in stellen[0], "Leerformel steht nicht als Gegenbeispiel"

    def test_englischer_prompt_ebenso(self):
        text = (REPO / "prompts" / "strategy_prompts_en.py").read_text(encoding="utf-8")
        assert LEERFORMEL_EN not in text

    def test_regel_steht_in_allen_annahmen_abschnitten(self):
        """Vier Sektionen verlangen einen Annahmen-Absatz. Erreicht die
        Regel nur eine, bleibt es beim alten Verhalten — genau das war
        der Fehler."""
        text = (REPO / "prompts" / "strategy_prompts.py").read_text(encoding="utf-8")
        abschnitte = text.count("ANNAHMEN-ABSATZ (PFLICHT AM SECTION-ENDE)")
        regeln = text.count("Ein Satz, der in jedem anderen Abschnitt genauso stünde")
        assert abschnitte >= 4
        assert regeln == abschnitte - 1, (
            f"{regeln} Regeln für {abschnitte} Abschnitte — der Umsatz-Abschnitt "
            "hat seine eigene, ausführlichere Fassung"
        )

    def test_regel_nennt_was_hineingehoert(self):
        text = (REPO / "prompts" / "strategy_prompts.py").read_text(encoding="utf-8")
        assert "Mengen, Auslastung" in text
        assert "widerlegen" in text, "Ohne Prüfbarkeit bleibt es eine Floskel"


class TestFesterTextWeichtDerWortersetzung:
    """Die Ersetzung \\bwir\\b -> ich tauscht Wörter, keine Verbformen."""

    def _block(self) -> str:
        from services.tools_verified_box import build_verified_tools_html
        return build_verified_tools_html(
            {"branche": "medien", "unternehmensgroesse": "2–10"},
            tools=[{"name": "A", "price": "9 €", "trust_url": "https://a.de/p"}])

    @pytest.mark.parametrize("wort", ["wir", "Wir", "uns", "unser", "unsere"])
    def test_kein_erste_person_plural_im_festen_text(self, wort):
        muster = re.compile(rf"(?<![A-Za-zÄÖÜäöüß]){wort}(?![A-Za-zÄÖÜäöüß])")
        assert not muster.search(self._block()), (
            f"„{wort}" f"\" im festen Text — die globale Ersetzung macht daraus "
            "eine kaputte Verbform (Lauf KIS-1266: „weisen ich nicht aus\")"
        )

    def test_die_aussage_bleibt_erhalten(self):
        """Ausweichen heisst nicht weglassen: Die Regel muss weiter
        dastehen, sonst wirkt die leere Preisspalte wie ein Datenfehler."""
        block = self._block()
        assert "nur mit Prüfdatum" in block
        assert "Anbieter" in block

    def test_die_ersetzung_gibt_es_wirklich_noch(self):
        """Fällt die Regel weg, ist dieser Test wertlos — dann soll er
        das sagen, statt still durchzulaufen."""
        quelle = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        assert r"(r'\bwir\b', 'ich')" in quelle


class TestBefundeAusDemLauf:
    """Was der Lauf KIS-1266 bestätigt hat — als Erinnerung, was hier
    eigentlich geprüft wird."""

    def test_werkzeug_block_erscheint_im_werkzeug_abschnitt(self):
        """Im Lauf KIS-1266 stand er auf Seite 15, direkt vor dem
        Starter-Kit. Vorher erreichte die kuratierte Liste keinen Leser."""
        vorlage = (REPO / "templates" / "pdf_template_v7.html").read_text(encoding="utf-8")
        start = vorlage.find('id="tools-section"')
        assert 0 < vorlage.find("VERIFIED_TOOLS_HTML", start) < vorlage.find("</section>", start)

    def test_kuratierte_namen_stehen_im_prompt(self):
        """Der Lauf nannte 13 kuratierte Werkzeuge statt 8 — die
        Faktenblöcke wirken."""
        from services.kuratierte_fakten import build_tool_fakten
        block = build_tool_fakten({"branche": "medien", "unternehmensgroesse": "2–10"})
        assert block.count("\n- ") >= 5
