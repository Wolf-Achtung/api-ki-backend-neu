# -*- coding: utf-8 -*-
"""KIS-1284: Befunde aus Lauf 1268 (Briefing 1151).

Fünf Punkte, alle leise — kein Report ist je daran abgestürzt:

1. Die 7-spaltigen Tabellen im deutschen Strategiebericht brachen
   buchstabenweise um. Auf S. 20-23 stand "Na htl os in Mi cr os oft
   36 5,", auf S. 30 "Bis 31.1 2.20 26" und "Ja, EU - ko nf or m".
   Ursache: Die Spaltenbreite kam allein aus der Kopfzeile, und der
   Fallback ``max(6 %)`` ergibt bei 180 mm Satzspiegel vier Zeichen.
   Die inhaltsbasierte Härtung gab es seit KIS-1272/1273/1275 — aber
   ausdrücklich nur für Englisch ("DE byte-identisch").

2. Der Schluss-Validator meldete in jedem Berliner Report ein
   "falsches Bundesland 'Brandenburg'" — für das Medienboard
   Berlin-Brandenburg, das genau so heißt.

3. Der Redundanz-Prüfer verglich ``QUICK_WINS_HTML`` mit der internen
   Sicherungskopie ``_QUICK_WINS_PRISTINE``. Zwei von fünf möglichen
   Warnungen gingen an eine garantierte Dublette.

4. Die zwei ROI-Sichten auf der Business-Case-Seite zeigten beide
   "1 %" (1,25 % und 1,06 %), während der Satz darunter erklärte, sie
   unterschieden sich.

5. Die Prozent-Schreibweise war innerhalb EINES Dokuments gemischt:
   23 x "80%" gegen 11 x "80 %" im Status-Report. lint_style meldet das
   seit jeher, repariert hat es niemand.
"""
from __future__ import annotations

import re

import pytest

from services.style_lint import (
    harden_wide_tables,
    normalize_percent_spacing,
    _unbreakable_len,
)

NBSP = " "

# Die Fördertabelle aus dem Strategiebericht KIS-1268, S. 30.
FOERDER_7 = """<table><thead><tr>
<th>Programm</th><th>Träger</th><th>Förderhöhe</th><th>Förderquote</th>
<th>Antragsfrist</th><th>Passung für Ihr Unternehmen</th><th>Link/Kontakt</th>
</tr></thead><tbody>
<tr><td>ProFIT (Berlin)</td><td>IBB (Investitionsbank Berlin)</td>
<td>Variabel, projektabhängig</td><td>Bis 80% Zuschuss, Rest Darlehen</td>
<td>Aktuell prüfen</td><td>Hoch</td>
<td>https://www.ibb.de/de/foerderprogramme/pro-fit-projektfinanzierung.html</td></tr>
<tr><td>BAFA – Förderung von Unternehmensberatungen für KMU</td>
<td>BAFA (Bundesamt für Wirtschaft und Ausfuhrkontrolle)</td>
<td>Max. 1.750 €</td><td>50%</td><td>Bis 31.12.2026</td><td>Hoch</td>
<td>https://www.bafa.de/DE/Wirtschaft/Beratung.html</td></tr>
</tbody></table>"""

# Die Tool-Vergleichstabelle, S. 20-23.
TOOLS_7 = """<table><thead><tr>
<th>Handlungsfeld</th><th>Tool / Anbieter</th><th>Kernfunktion</th>
<th>Preismodell</th><th>DSGVO</th><th>Integration mit bestehendem Stack</th>
<th>Empfehlung</th>
</tr></thead><tbody>
<tr><td>Automatisierung Postproduktion</td><td>Microsoft 365 Copilot / Microsoft</td>
<td>KI-Automatisierung in Office, Schnitt, Untertitelung</td>
<td>In Microsoft 365 Lizenz enthalten</td><td>Ja, EU-konform</td>
<td>Nahtlos in Microsoft 365, kompatibel mit ChatGPT, Claude, Perplexity</td>
<td>★★★</td></tr>
<tr><td>Compliance &amp; KI-Richtlinie</td><td>OneTrust / OneTrust LLC</td>
<td>Datenschutz- und KI-Compliance-Management</td><td>Ab ca. 79 €/Monat</td>
<td>Ja, EU-konform</td><td>Schnittstellen zu Microsoft 365</td><td>★★★</td></tr>
</tbody></table>"""


def _breiten(html: str) -> list:
    return [float(w) for w in re.findall(r'<col style="width:([\d.]+)%"', html)]


# --------------------------------------------------------------------------- #
# 1. Deutsche Tabellen werden gehärtet                                        #
# --------------------------------------------------------------------------- #
class TestBreiteTabellenAufDeutsch:

    @pytest.mark.parametrize("tabelle", [FOERDER_7, TOOLS_7])
    def test_spalten_summieren_auf_hundert(self, tabelle):
        out, _ = harden_wide_tables(tabelle, lang="de")
        breiten = _breiten(out)
        assert len(breiten) == 7
        assert sum(breiten) == pytest.approx(100.0, abs=0.2)

    @pytest.mark.parametrize("tabelle", [FOERDER_7, TOOLS_7])
    def test_keine_vier_zeichen_spalte_mehr(self, tabelle):
        """Die alte Formel liess 6 % zu — rund vier Zeichen."""
        out, _ = harden_wide_tables(tabelle, lang="de")
        assert min(_breiten(out)) >= 10.0, _breiten(out)

    def test_frist_traegt_das_datum(self):
        """"Bis 31.1 2.20 26" (S. 30) — das Datum braucht ~15 % am Stück."""
        out, _ = harden_wide_tables(FOERDER_7, lang="de")
        assert _breiten(out)[4] >= 15.0

    def test_datum_bricht_nicht(self):
        out, _ = harden_wide_tables(FOERDER_7, lang="de")
        assert '<span style="white-space:nowrap">31.12.2026</span>' in out

    def test_dsgvo_spalte_traegt_konform(self):
        """"Ja, EU - ko nf or m" (S. 23). "konform" sind sieben Zeichen."""
        out, _ = harden_wide_tables(TOOLS_7, lang="de")
        assert _breiten(out)[4] >= 11.0

    def test_kompaktstil_und_marker(self):
        out, _ = harden_wide_tables(TOOLS_7, lang="de")
        assert "table-layout:fixed" in out
        assert 'data-ksj-hardened="1"' in out

    def test_deutsch_trennt_nur_an_gesetzten_stellen(self):
        """KIS-1244: hyphens:auto trennte deutsche Wörter falsch."""
        out, _ = harden_wide_tables(TOOLS_7, lang="de")
        assert "hyphens:manual" in out
        assert "hyphens:auto" not in out

    def test_englisch_bleibt_wie_es_war(self):
        en = TOOLS_7.replace("DSGVO", "GDPR")
        out, _ = harden_wide_tables(en, lang="en")
        assert "hyphens:auto" in out
        assert "hyphens:manual" not in out

    def test_vier_spalten_bleiben_beim_alten(self):
        vier = ("<table><tr><th>Phase</th><th>Fokus</th><th>Budget</th>"
                "<th>Pfad</th></tr><tr><td>A</td><td>B</td><td>C</td>"
                "<td>D</td></tr></table>")
        out, _ = harden_wide_tables(vier, lang="de")
        assert "table-layout:fixed" not in out
        assert "data-ksj-hardened" not in out


class TestKopfwortBreite:
    """Ein Kopfwort bekommt &shy; und braucht deshalb nicht seine volle
    Länge — das war der Grund, warum die Minima auf 138 % summierten."""

    @pytest.mark.parametrize("wort,erwartet_hoechstens", [
        ("HANDLUNGSFELD", 7),
        ("Kernfunktion", 7),
        ("Antragsfrist", 9),
    ])
    def test_deutsche_kopfwoerter_zaehlen_ihr_segment(self, wort, erwartet_hoechstens):
        assert _unbreakable_len(wort, False) <= erwartet_hoechstens
        assert _unbreakable_len(wort, False) < len(wort)

    def test_kurze_woerter_bleiben_ganz(self):
        assert _unbreakable_len("DSGVO", False) == 5
        assert _unbreakable_len("Träger", False) == 6

    def test_englisch_zaehlt_weiter_das_ganze_wort(self):
        """Im EN-Pfad steht hyphens:none auf th (KIS-1273)."""
        assert _unbreakable_len("RECOMMENDATION", True) == len("RECOMMENDATION")


# --------------------------------------------------------------------------- #
# 2. Bundesland: Eigennamen mit Bindestrich                                   #
# --------------------------------------------------------------------------- #
class TestBundeslandEigenname:

    def test_validator_meldet_medienboard_nicht(self):
        from services.report_validator import ReportValidator
        sections = {
            "FOERDERPOTENZIAL_HTML":
                "<p>Anlaufstelle ist das Medienboard Berlin-Brandenburg.</p>",
        }
        v = ReportValidator(sections, {"bundesland": "Berlin"})
        v.validate_all()
        treffer = [e for e in v.errors
                   if getattr(e, "category", "") == "LOCATION_INCONSISTENCY"]
        assert not treffer, [e.message for e in treffer]

    def test_validator_meldet_echtes_fremdes_bundesland(self):
        """Das Netz darf nicht durchhängen."""
        from services.report_validator import ReportValidator
        sections = {
            "FOERDERPOTENZIAL_HTML":
                "<p>Der Digitalbonus Bayern passt zu Ihrem Vorhaben.</p>",
        }
        v = ReportValidator(sections, {"bundesland": "Berlin"})
        v.validate_all()
        treffer = [e for e in v.errors
                   if getattr(e, "category", "") == "LOCATION_INCONSISTENCY"]
        assert treffer, "fremdes Bundesland wurde nicht gemeldet"

    def test_enforcer_loescht_die_zeile_nicht(self):
        """Die Zeilen-Löschung nutzte bis hierher das ungeschützte Muster —
        ein Berliner Kunde haette das Programm samt Zeile verloren."""
        from services.content_quality_enforcer import validate_location_in_section
        html = ('<table><tr><td>Medienboard Berlin-Brandenburg</td>'
                '<td>Förderung für Medienprojekte</td></tr></table>')
        neu, anzahl = validate_location_in_section(html, "Berlin")
        assert anzahl == 0
        assert "Medienboard Berlin-Brandenburg" in neu

    def test_enforcer_loescht_fremde_foerderzeile_weiter(self):
        from services.content_quality_enforcer import validate_location_in_section
        html = ('<table><tr><td>Digitalbonus Bayern</td>'
                '<td>Förderung für KMU</td></tr></table>')
        neu, anzahl = validate_location_in_section(html, "Berlin")
        assert anzahl >= 1
        assert "Digitalbonus Bayern" not in neu


# --------------------------------------------------------------------------- #
# 3. Interne Sicherungskopien zählen nicht als Dublette                       #
# --------------------------------------------------------------------------- #
class TestPristineNichtAlsDublette:

    def test_unterstrich_keys_bleiben_draussen(self):
        from services.report_validator import ReportValidator
        satz = ("Richten Sie zunächst eine lokal betriebene "
                "Transkriptionslösung für Rohmaterial ein, um NDA-Material "
                "nicht in die Cloud zu geben und die Freigabe beim Team zu "
                "belassen, so wie es der Ablauf vorsieht.")
        sections = {
            "QUICK_WINS_HTML": f"<p>{satz}</p>",
            "_QUICK_WINS_PRISTINE": f"<p>{satz}</p>",
        }
        v = ReportValidator(sections, {})
        assert "_QUICK_WINS_PRISTINE" not in v.canonical_sections
        assert "_QUICK_WINS_PRISTINE" in v.excluded_shadow_keys


# --------------------------------------------------------------------------- #
# 4. Zwei ROI-Sichten, zwei Zahlen                                            #
# --------------------------------------------------------------------------- #
class TestRoiAnzeige:
    """Lauf 1268: CAPEX-Sicht 1,25 %, Gesamt-Sicht 1,06 % — beide gedruckt
    als "1 %", darunter der Satz, sie unterschieden sich."""

    def test_kleine_werte_bekommen_eine_nachkommastelle(self):
        from services.roi_anzeige import als_prozent
        # 1,25 rundet nach IEEE 754 auf 1,2 — entscheidend ist nur, dass
        # die beiden Sichten nicht mehr dieselbe Zahl zeigen.
        assert als_prozent(1.25) == "1,2 %"
        assert als_prozent(1.06) == "1,1 %"
        assert als_prozent(1.25) != als_prozent(1.06)

    def test_grosse_werte_bleiben_ganzzahlig(self):
        from services.roi_anzeige import als_prozent
        assert als_prozent(47.3) == "47 %"
        assert als_prozent(200.0) == "200 %"

    def test_grenze_bei_zehn(self):
        from services.roi_anzeige import als_prozent
        assert als_prozent(9.9) == "9,9 %"
        assert als_prozent(10.0) == "10 %"

    def test_negative_werte(self):
        from services.roi_anzeige import als_prozent
        assert als_prozent(-3.5) == "-3,5 %"

    def test_unbrauchbare_eingabe_gibt_none(self):
        from services.roi_anzeige import als_prozent
        assert als_prozent(None) is None
        assert als_prozent("n. v.") is None


# --------------------------------------------------------------------------- #
# 5. Eine Prozent-Schreibweise                                                #
# --------------------------------------------------------------------------- #
class TestProzentAbstand:

    def test_ziffer_und_prozent_bekommen_geschuetzten_abstand(self):
        out, n = normalize_percent_spacing("<p>Bis 80% Zuschuss.</p>")
        assert out == f"<p>Bis 80{NBSP}% Zuschuss.</p>"
        assert n == 1

    def test_vorhandener_abstand_wird_geschuetzt(self):
        out, n = normalize_percent_spacing("<p>50 % Quote</p>")
        assert out == f"<p>50{NBSP}% Quote</p>"

    def test_idempotent(self):
        einmal, _ = normalize_percent_spacing("<p>Bis 80% Zuschuss.</p>")
        zweimal, n = normalize_percent_spacing(einmal)
        assert zweimal == einmal and n == 0

    def test_style_attribute_bleiben_heil(self):
        html = '<td style="width:80%"><div style="flex:0 0 33%">33%</div></td>'
        out, _ = normalize_percent_spacing(html)
        assert 'style="width:80%"' in out
        assert 'style="flex:0 0 33%"' in out
        assert f"33{NBSP}%" in out

    def test_prozentige_bleibt_zusammen(self):
        out, n = normalize_percent_spacing("<p>eine 100%ige Tochter</p>")
        assert "100%ige" in out and n == 0

    def test_leerer_text(self):
        assert normalize_percent_spacing("") == ("", 0)
        assert normalize_percent_spacing("<p>ohne Zeichen</p>")[1] == 0


# --------------------------------------------------------------------------- #
# 6. Das Prüfwerkzeug erkennt den Rückfall                                    #
# --------------------------------------------------------------------------- #
class TestVergleichsWerkzeug:

    def test_zerhackte_tabelle_wird_erkannt(self):
        import importlib.util
        from pathlib import Path
        pfad = Path(__file__).resolve().parent.parent / "scripts" / "compare_reports.py"
        spec = importlib.util.spec_from_file_location("cr", pfad)
        cr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cr)
        kaputt = "Na\nhtl\nos\nin\nMi\ncr\nos\noft\n36\n5,\n"
        assert cr._zerhackte_tabelle(kaputt)
        heil = "Nahtlos in Microsoft 365, kompatibel mit ChatGPT\nca.\n50\n"
        assert cr._zerhackte_tabelle(heil) is None
