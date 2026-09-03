# -*- coding: utf-8 -*-
"""KIS-1267: Vier Defekte aus dem Lauf KIS-1262/1263 (03.09.2026).

Wolf hat fuenf erzeugte PDFs geschickt. Vier Fehler waren im Kundentext
sichtbar:

1. Strategiebericht S. 21 druckte eine Prompt-Anweisung woertlich ab,
   inklusive interner Ticket-Nummer.
2. Status-Report S. 20: "Investitionsbudget liegt bei 2.000-10.000 n. v."
   — der Empty-Value-Sanitizer fraß das Euro-Zeichen eines echten Betrags.
3. Status-Report S. 27: "Medienboard Berlin-Ihr Bundesland" — der
   Location-Validator ersetzte "Brandenburg" mitten im Eigennamen.
4. Status-Report S. 4: "'Datenreife: keine' widerspricht dem
   Digitalisierungsgrad von 8/10" — die Frage stellt der R1-Fragebogen
   gar nicht; der Report zitierte eine nie gegebene Antwort.
"""
from __future__ import annotations

from services.briefing_contradictions import detect_contradictions
from services.content_quality_enforcer import validate_location_in_section
from services.report_healer import sanitize_business_case_empty_values
from services.zero_leak_engine import CRITICAL_LEAK_REGEX


# =========================================================================
# 1. Prompt-Anweisung darf nicht im Lesertext landen
# =========================================================================

def _leak_scrub(text: str) -> str:
    """Wendet die CRITICAL-Regexe an wie die Engine (sub durch "")."""
    for pattern, _label in CRITICAL_LEAK_REGEX:
        text = pattern.sub("", text)
    return text


class TestPromptLeak:

    # Originaltext aus dem PDF (Strategiebericht KIS-1262, Seite 21).
    ORIGINAL = (
        "<p>Der vorliegende Strategiebericht setzt die Brutto-Jahresersparnis "
        "gegen die Gesamtinvestition über 12 Monate (24.000 €). "
        "Erklären Sie dem Leser verständlich, warum die ROI-Zahlen "
        "unterschiedlich sind — beide sind korrekt. KIS-1238: Führe die "
        "Differenz NICHT allein auf unterschiedliche Investitionssummen "
        "zurück (die können identisch sein); der entscheidende Unterschied "
        "ist der OPEX-Abzug in Report 1.</p>"
    )

    def test_ticket_anweisung_wird_entfernt(self):
        rest = _leak_scrub(self.ORIGINAL)
        assert "KIS-1238" not in rest
        assert "Führe die Differenz NICHT" not in rest

    def test_meta_anweisung_wird_entfernt(self):
        rest = _leak_scrub(self.ORIGINAL)
        assert "Erklären Sie dem Leser" not in rest

    def test_fachtext_bleibt_stehen(self):
        rest = _leak_scrub(self.ORIGINAL)
        assert "Brutto-Jahresersparnis" in rest
        assert "24.000 €" in rest

    def test_report_id_im_fuss_bleibt(self):
        """Der Fuß jeder Seite traegt "Report-ID: KIS-1262" — die Ticket-
        Regex darf dort nicht zuschlagen (kein Doppelpunkt nach der Zahl)."""
        fuss = "<footer>Report-ID: KIS-1262 • 03.09.2026</footer>"
        assert _leak_scrub(fuss) == fuss

    def test_legitimer_beratungssatz_bleibt(self):
        """"Erklaeren Sie Ihrem Team ..." ist echter Beratungstext
        (Strategiebericht S. 25) und darf nicht mitgeloescht werden."""
        satz = ("<p>Erklären Sie Ihrem Team zu Beginn, dass KI die "
                "Arbeitsbelastung reduziert.</p>")
        assert _leak_scrub(satz) == satz

    def test_prompt_quelle_trennt_lesertext_von_anweisung(self):
        """Die Quelle selbst ist entschaerft: die Anweisung an das Modell
        steht nicht mehr im Lesertext-Block."""
        from pathlib import Path
        roh = (Path(__file__).resolve().parent.parent
               / "prompts" / "strategy_prompts.py").read_text(encoding="utf-8")
        assert "--- LESERTEXT ANFANG ---" in roh
        # Die Anweisung mit Ticket-Nummer ist raus.
        assert "KIS-1238: Führe die Differenz NICHT" not in roh


# =========================================================================
# 2. Empty-Value-Sanitizer frisst keine echten Betraege mehr
# =========================================================================

class TestEuroSanitizer:

    def test_echter_betrag_am_satzende_bleibt(self):
        html = ("<p><strong>Budget-Einordnung:</strong> Ihr angegebenes "
                "Investitionsbudget liegt bei 2.000–10.000 €. Die hier "
                "kalkulierte Gesamtinvestition übersteigt diesen Rahmen.</p>")
        out, fixes = sanitize_business_case_empty_values(html)
        assert "2.000–10.000 €." in out
        assert "n.&thinsp;v." not in out
        assert fixes == 0

    def test_betrag_mit_zwei_leerzeichen_bleibt(self):
        html = "<p>Die Investition liegt bei 24.000  €.</p>"
        out, _ = sanitize_business_case_empty_values(html)
        assert "n.&thinsp;v." not in out

    def test_leerer_wert_wird_weiterhin_ersetzt(self):
        """Der eigentliche Zweck des Musters bleibt erhalten."""
        html = "<p>Laufende Kosten: €.</p>"
        out, fixes = sanitize_business_case_empty_values(html)
        assert "n.&thinsp;v." in out
        assert fixes >= 1

    def test_leerer_wert_nach_wort_wird_ersetzt(self):
        html = "<p>Die Startinvestition beträgt €.</p>"
        out, _ = sanitize_business_case_empty_values(html)
        assert "n.&thinsp;v." in out


# =========================================================================
# 3. Location-Validator zerschneidet keine Eigennamen
# =========================================================================

class TestLocationValidator:

    def test_berlin_brandenburg_bleibt_ganz(self):
        html = ("<p>Als Medienunternehmen mit Sitz in Berlin profitieren Sie "
                "von Institutionen wie dem Medienboard Berlin-Brandenburg.</p>")
        out, _ = validate_location_in_section(html, "Berlin")
        assert "Medienboard Berlin-Brandenburg" in out
        assert "Ihr Bundesland" not in out

    def test_sachsen_anhalt_bleibt_ganz(self):
        html = "<p>Die Förderlandschaft in Sachsen-Anhalt ist breit.</p>"
        out, _ = validate_location_in_section(html, "Sachsen-Anhalt")
        assert "Sachsen-Anhalt" in out
        assert "Ihr Bundesland" not in out

    def test_freistehendes_falsches_bundesland_wird_ersetzt(self):
        """Der Schutz gilt nur fuer Bindestrich-Komposita — ein einzeln
        stehendes fremdes Bundesland wird weiterhin neutralisiert."""
        html = "<p>Ein Programm des Landes Bayern unterstützt Sie dabei.</p>"
        out, count = validate_location_in_section(html, "Berlin")
        assert "Bayern" not in out
        assert "Ihr Bundesland" in out
        assert count >= 1

    def test_fremde_foerderzeile_wird_weiterhin_entfernt(self):
        """Die Erkennung fuer <li>/<tr> nutzt weiter das ungeschuetzte
        Muster — eine fremde Foerderzeile fliegt komplett raus."""
        html = ("<ul><li>Digitalbonus Bayern — Förderung für KMU</li>"
                "<li>ProFIT Berlin</li></ul>")
        out, count = validate_location_in_section(html, "Berlin")
        assert "Digitalbonus" not in out
        assert "ProFIT Berlin" in out
        assert count >= 1


# =========================================================================
# 4. Keine erfundenen Zitate aus unbeantworteten Feldern
# =========================================================================

class TestWiderspruchNurBeiEchterAntwort:

    def test_unbeantwortete_datenreife_loest_nichts_aus(self):
        """Der R1-Fragebogen kennt kein Feld 'datenreife'. Ohne Antwort
        darf der Report nicht behaupten, der Kunde habe 'keine' gesagt."""
        briefing = {"digitalisierungsgrad": "8"}
        findings = detect_contradictions(briefing)
        assert not any("Datenreife" in f for f in findings)

    def test_leere_datenreife_loest_nichts_aus(self):
        briefing = {"digitalisierungsgrad": "8", "datenreife": ""}
        assert not any("Datenreife" in f for f in detect_contradictions(briefing))

    def test_echte_antwort_keine_loest_weiterhin_aus(self):
        briefing = {"digitalisierungsgrad": "8", "datenreife": "keine"}
        findings = detect_contradictions(briefing)
        assert any("Datenreife" in f for f in findings)

    def test_positive_datenreife_loest_nichts_aus(self):
        briefing = {"digitalisierungsgrad": "8", "datenreife": "umfangreich"}
        assert not any("Datenreife" in f for f in detect_contradictions(briefing))

    def test_strategie_antwort_hat_vorrang_vor_leerem_briefing(self):
        """Lauf KIS-1262: FB1 leer, FB2 'umfangreich' — kein Widerspruch."""
        briefing = {"digitalisierungsgrad": "8", "datenreife": ""}
        findings = detect_contradictions(briefing, {"datenreife": "umfangreich"})
        assert not any("Datenreife" in f for f in findings)

    def test_unbeantwortete_tools_loesen_nichts_aus(self):
        briefing = {"ki_projekte": "API-Anbindung"}
        findings = detect_contradictions(briefing)
        assert not any("Vorhandene Tools" in f for f in findings)

    def test_echte_tool_spannung_bleibt_erkannt(self):
        """Der Fall aus Lauf KIS-1262: FB1 'keine', FB2 nennt fünf Tools."""
        briefing = {"vorhandene_tools": "keine"}
        strategie = {"s5_software": ["Microsoft 365", "ChatGPT / OpenAI"]}
        findings = detect_contradictions(briefing, strategie)
        assert any("Vorhandene Tools" in f for f in findings)

    def test_unbeantwortete_interne_kompetenzen_loesen_nichts_aus(self):
        briefing = {"ki_kompetenz": "hoch"}
        findings = detect_contradictions(briefing)
        assert not any("Interne KI-Kompetenzen" in f for f in findings)

    def test_echte_kompetenz_spannung_bleibt_erkannt(self):
        briefing = {"interne_ki_kompetenzen": "nein", "ki_kompetenz": "hoch"}
        findings = detect_contradictions(briefing)
        assert any("Interne KI-Kompetenzen" in f for f in findings)
