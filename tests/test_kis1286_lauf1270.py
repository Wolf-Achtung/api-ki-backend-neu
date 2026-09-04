# -*- coding: utf-8 -*-
"""KIS-1286: Wer zuerst ein colgroup setzt, gewinnt.

Lauf 1270 bestätigte die beiden Fixes aus KIS-1285: Der Score steht wieder
auf dem Deckblatt des Strategieberichts, und "Abonnement" bricht mit
Trennstrich. Die Tool-Vergleichstabelle liest sich sauber.

Die **Fördertabelle drei Kapitel weiter** aber nicht:

    Bis 80 % (Zuschu     Aktu      BAFA (Bunde
    ss), Rest Darlehe    ell       samt für
    n                    prüf en   Wirtsch

Beide Tabellen stehen im selben Dokument und laufen durch dieselbe
Pipeline. Der Unterschied ist nicht die Sprache und nicht die
Spaltenzahl, sondern **wer zuerst ein colgroup setzt**:

``html_enhancer._balance_column_widths`` (KIS-1257) greift nur bei
"echter Schieflage" — breiteste Spalte mindestens dreimal so breit wie
die schmalste. Die Fördertabelle mit ihrer 70-Zeichen-URL neben "Hoch"
erfüllt das, die ausgewogene Tool-Tabelle nicht. Der Balancer setzt dort
ein colgroup mit 8-–34-%-Klammer, und ``harden_wide_tables`` überspringt
Tabellen, die schon eines haben.

Für Englisch war das seit KIS-EN2-TABLES gelöst: eine Vorab-Härtung vor
dem Enhancer. Der DE-Pfad blieb "unverändert" — und damit ungelöst.

Zweiter Punkt: ``GitHub/GitLab`` brach zu ``GitHub/GitLa b`` (S. 18).
Für die Wortsuche sind das zwei Wörter zu je sechs Zeichen; keines
erreicht eine Trennschwelle. Ein Nullbreiten-Leerzeichen nach dem
Schrägstrich gibt den Umbruch frei, ohne einen Trennstrich zu drucken —
"GitHub/-GitLab" wäre falsch.
"""
from __future__ import annotations

import re

import pytest

from services.html_enhancer import enhance_strategy_html
from services.style_lint import harden_wide_tables, soften_table_long_words

ZWSP = "​"
SHY = "­"

# Die Fördertabelle aus dem Strategiebericht KIS-1270, S. 28.
FOERDER_7 = """<table><thead><tr>
<th>Programm</th><th>Träger</th><th>Förderhöhe</th><th>Förderquote</th>
<th>Antragsfrist</th><th>Passung für Ihr Unternehmen</th><th>Link/Kontakt</th>
</tr></thead><tbody>
<tr><td>ProFIT (Berlin)</td><td>IBB (Investitionsbank Berlin)</td>
<td>Variabel, projektabhängig</td><td>Bis 80 % (Zuschuss), Rest Darlehen</td>
<td>Aktuell prüfen</td><td>Hoch</td>
<td>https://www.ibb.de/de/foerderprogramme/pro-fit-projektfinanzierung.html</td></tr>
<tr><td>BAFA – Förderung von Unternehmensberatungen für KMU</td>
<td>BAFA (Bundesamt für Wirtschaft und Ausfuhrkontrolle)</td>
<td>Max. 1.750 €</td><td>50 %</td><td>Bis 31.12.2026</td><td>Hoch</td>
<td>https://www.bafa.de/DE/Wirtschaft/Beratung.html</td></tr>
</tbody></table>"""


def _breiten(html: str):
    return [float(x) for x in re.findall(r'<col style="width:([\d.]+)%"', html)]


class TestReihenfolgeDerBreitenvergabe:

    def test_balancer_greift_bei_der_foerdertabelle(self):
        """Die Voraussetzung des Befunds — sonst prüft der Rest nichts."""
        aus = enhance_strategy_html(FOERDER_7)
        assert "<colgroup" in aus.lower()
        assert min(_breiten(aus)) <= 9.0, _breiten(aus)

    def test_haertung_ueberspringt_fremdes_colgroup(self):
        """Der Mechanismus, der den DE-Pfad aushebelte."""
        aus = enhance_strategy_html(FOERDER_7)
        gehaertet, n = harden_wide_tables(aus, lang="de")
        assert n == 0
        assert "data-ksj-hardened" not in gehaertet

    def test_vorab_haertung_setzt_sich_durch(self):
        """Die Reihenfolge, die Englisch seit KIS-EN2-TABLES nutzt."""
        vorab, _ = harden_wide_tables(FOERDER_7, lang="de")
        aus = enhance_strategy_html(vorab)
        endgueltig, _ = harden_wide_tables(aus, lang="de")
        assert 'data-ksj-hardened="1"' in endgueltig
        breiten = _breiten(endgueltig)
        assert len(breiten) == 7
        assert min(breiten) >= 12.0, breiten

    def test_datum_bleibt_am_stueck(self):
        vorab, _ = harden_wide_tables(FOERDER_7, lang="de")
        aus = enhance_strategy_html(vorab)
        assert '<span style="white-space:nowrap">31.12.2026</span>' in aus

    def test_kurzer_header_greift(self):
        """"ANTRAGSFRIST" → "Frist" (KIS-1247) lief ins Leere."""
        vorab, _ = harden_wide_tables(FOERDER_7, lang="de")
        assert "Antragsfrist" not in vorab
        assert "Frist" in vorab

    def test_renderer_haertet_in_beiden_sprachen_vorab(self):
        from pathlib import Path
        quelle = (Path(__file__).resolve().parent.parent
                  / "services" / "strategy_renderer.py").read_text(encoding="utf-8")
        stelle = quelle.find("_pre_hwt")
        assert stelle > 0
        block = quelle[stelle - 400:stelle + 200]
        assert 'lang="en" if _ctx_en else "de"' in block, block


class TestSchraegstrichFuegungen:

    TABELLE = """<table><thead><tr>
<th>Handlungsfeld</th><th>Tool</th><th>Kernfunktion</th><th>Preismodell</th>
<th>DSGVO</th><th>Integration</th><th>Empfehlung</th>
</tr></thead><tbody>
<tr><td>Schulung</td><td>Microsoft 365 Copilot</td><td>KI-Assistenz</td>
<td>Abonnement</td><td>Teilweise</td>
<td>Nahtlos in Microsoft 365, kompatibel mit GitHub/GitLab</td><td>★★★</td></tr>
<tr><td>Recherche</td><td>Claude</td><td>Sprachmodell</td><td>pro Nutzung</td>
<td>Ja</td><td>https://www.anthropic.com/claude</td><td>★★</td></tr>
</tbody></table>"""

    def _weich(self):
        gehaertet, _ = harden_wide_tables(self.TABELLE, lang="de")
        return soften_table_long_words(gehaertet, lang="de")[0]

    def test_umbruchstelle_nach_dem_schraegstrich(self):
        assert "GitHub/" + ZWSP + "GitLab" in self._weich()

    def test_kein_trennstrich_am_schraegstrich(self):
        """"GitHub/-GitLab" wäre falsch — das ist keine Worttrennung."""
        weich = self._weich()
        assert "GitHub/" + SHY not in weich

    def test_urls_bleiben_unangetastet(self):
        assert "https://www.anthropic.com/claude" in self._weich()

    def test_nur_in_gehaerteten_tabellen(self):
        weich, _ = soften_table_long_words(self.TABELLE, lang="de")
        assert ZWSP not in weich

    def test_idempotent(self):
        einmal = self._weich()
        zweimal, _ = soften_table_long_words(einmal, lang="de")
        assert zweimal == einmal

    @pytest.mark.parametrize("text,erwartet", [
        ("Input/Output", True),
        ("GitHub/GitLab", True),
        # Kürzel und Einheiten bleiben ganz — sie passen ohnehin in jede
        # Spalte, und ein Umbruch mitten in "h/mo." liest sich falsch.
        ("Film/TV", False),
        ("22.5 h/mo.", False),
        ("€/Monat", False),
        ("31.12./2026", False),
    ])
    def test_nur_zwischen_zwei_woertern(self, text, erwartet):
        tabelle = self.TABELLE.replace("GitHub/GitLab", text)
        gehaertet, _ = harden_wide_tables(tabelle, lang="de")
        weich, _ = soften_table_long_words(gehaertet, lang="de")
        assert (ZWSP in weich) is erwartet, weich
