# -*- coding: utf-8 -*-
"""KIS-1261: Golden-Referenzprofil-Gate.

Drei repräsentative Gold-Profile (solo/kmu/team, alle deutsch) laufen bei
jedem CI-Lauf durch die DETERMINISTISCHE Platin-Kette — Quality-Enforcer →
Report-Healer → Platin-QA-Scan — mit gemocktem LLM-Output. Der Roh-Output
ist ein Regressions-Korpus: Er enthält gezielt die historischen
Befund-Klassen der manuellen PDF-Reviews (englische Badges über
Tag-Grenzen, ROI-Zahlen im Förder-Text, dreifach wiederholte Sätze,
Marken-Schreibfehler, klebende Währungszeichen, snake_case in URLs).

Das Gate stellt sicher, dass die Kette JEDE dieser Klassen weiterhin
heilt — und dass der Platin-QA-Scan am Ende 0 Befunde meldet. Dazu:
der Sicherheits-Constraint des Produkts als Invariante (kein
Firmennamens-Feld in irgendeinem Gold-Profil) plus ein Tripwire-Test,
der beweist, dass der name_leak-Detektor scharf ist.

Kein Netz, kein LLM, keine DB — läuft in Sekunden bei jedem PR.
"""
from __future__ import annotations

import glob
import json
import re

import pytest

PROFILE_IDS = [
    "solo_beratung_ki_assessments",
    "kmu_handel_ecommerce_advisory",
    "team_it_software_saas_advisory",
]

# Ein Satz >= 90 Zeichen, der 3x nahezu wortgleich im Roh-Output steht —
# die Befund-Klasse aus Lauf 1123 (Judge: dubletten GELB).
_DUP_SENTENCE = (
    "Die Automatisierung der wiederkehrenden Routineprozesse entlastet Ihr "
    "Team spürbar und schafft dauerhaft Kapazität für das eigentliche "
    "Kerngeschäft Ihres Unternehmens."
)

_BAFA_URL = (
    "https://www.bafa.de/DE/Wirtschaft/Beratung_Finanzierung/"
    "Unternehmensberatung/unternehmensberatung_node.html"
)


def _load_profile(profile_id: str) -> dict:
    with open(f"data/test_profiles_gold/{profile_id}.json", encoding="utf-8") as f:
        return json.load(f)


def _ctx(text: str) -> str:
    """Individueller Sektionskontext, damit Dedupe-Pässe nur die
    gezielt gesetzten Dubletten treffen."""
    return f"<p>{text} Dieser Abschnitt beschreibt die Ausgangslage differenziert und konkret.</p>"


def build_raw_sections(answers: dict) -> dict:
    """Gemockter LLM-Roh-Output mit dem historischen Befund-Korpus."""
    hl = str(answers.get("hauptleistung") or "Ihr Kerngeschäft")[:120]
    return {
        "EXECUTIVE_SUMMARY_HTML": (
            _ctx(f"Für {hl} zeigt die Analyse eine belastbare Ausgangslage.")
            + f"<p>{_DUP_SENTENCE}</p>"
            + "<p>Die Marke KI-sicherheit.Jetzt begleitet die Umsetzung beratend.</p>"
        ),
        "BUSINESS_CASE_HTML": (
            _ctx("Der Business Case rechnet bewusst konservativ und transparent.")
            + "<p>Die laufenden Kosten von 600€ pro Monat sind im Modell enthalten "
            "und werden gegen die Zeitersparnis gerechnet.</p>"
        ),
        "QUICK_WINS_HTML": (
            _ctx("Die Quick Wins setzen direkt an Ihren größten Zeitfressern an.")
            + '<div>Erster Schritt | Komplexität: <span style="color:#22c55e;">low</span> '
            "| Werkzeug: bestehende Bordmittel (DSGVO-Vorbehalt — siehe Vendor-Audit)</div>"
        ),
        "RECOMMENDATIONS_HTML": (
            _ctx("Die Empfehlungen sind nach Wirkung und Machbarkeit priorisiert.")
            + f"<p>{_DUP_SENTENCE}</p>"
            + "<p>Für Kundendaten gilt eine klare Freigaberegel "
            "(DSGVO-Vorbehalt — siehe Vendor-Audit).</p>"
        ),
        "FOERDERPOTENZIAL_HTML": (
            _ctx("Passende Programme senken den effektiven Eigenanteil deutlich.")
            + "<p>Der ausgewiesene ROI von 22 % nach 12 Monaten basiert auf dem "
            "vollen Eigenanteil und steigt mit jeder bewilligten Förderung.</p>"
            + f"<p>Quellen: BAFA – Förderung von Unternehmensberatungen: {_BAFA_URL}</p>"
        ),
        "ADVISOR_NOTE_HTML": (
            _ctx("Meine Einschätzung stützt sich auf Ihre konkreten Angaben.")
            + f"<p>{_DUP_SENTENCE}</p>"
        ),
        "TOOLS_EMPFEHLUNGEN_HTML": _ctx(
            "Die Tool-Auswahl folgt Ihrem vorhandenen Software-Stack und den "
            "Datenschutz-Anforderungen; jede Empfehlung nennt den konkreten Einsatzzweck."
        ),
    }


def _run_platin_chain(sections: dict, answers: dict) -> dict:
    """Produktions-Reihenfolge: Enforcer → Healer (gleiches Sequencing wie
    in gpt_analyze vor dem Platin-QA-Scan)."""
    from services.content_quality_enforcer import apply_all_quality_enforcers
    from services.report_healer import heal_report_html

    healed = apply_all_quality_enforcers(
        dict(sections),
        hauptleistung=str(answers.get("hauptleistung") or ""),
        bundesland=str(answers.get("bundesland") or ""),
        company_size=str(answers.get("unternehmensgroesse") or "kmu"),
    )
    result = heal_report_html(
        healed,
        segment=str(answers.get("unternehmensgroesse") or "kmu"),
        hauptleistung=str(answers.get("hauptleistung") or ""),
    )
    return result.sections


# =========================================================================
# 1. Das Gate: 3 Profile × Befund-Korpus → Platin-QA muss 0 Befunde melden
# =========================================================================

class TestGoldenReferenceGate:

    @pytest.mark.parametrize("profile_id", PROFILE_IDS)
    def test_platin_qa_zero_findings(self, profile_id):
        from services.platin_qa import scan_sections
        answers = _load_profile(profile_id)["answers"]
        healed = _run_platin_chain(build_raw_sections(answers), answers)
        findings = scan_sections(healed, answers)
        assert findings == [], f"{profile_id}: {findings}"

    @pytest.mark.parametrize("profile_id", PROFILE_IDS)
    def test_defect_corpus_healed(self, profile_id):
        answers = _load_profile(profile_id)["answers"]
        healed = _run_platin_chain(build_raw_sections(answers), answers)

        # (a) englisches Badge über Tag-Grenze eingedeutscht (KIS-1254)
        qw = healed.get("QUICK_WINS_HTML", "")
        assert ">low<" not in qw
        assert "niedrig" in qw

        # (b) ROI-Zahl aus dem Förder-Text entfernt, grammatisch ersetzt (KIS-1251/1254)
        fp = healed.get("FOERDERPOTENZIAL_HTML", "")
        assert "22 %" not in fp
        assert "siehe Business Case" in fp

        # (c) Satz-Dublette gekappt: max. 2 Vorkommen (KIS-1254)
        marker = "entlastet Ihr Team spürbar"
        total = sum(
            str(v).count(marker) for k, v in healed.items()
            if isinstance(v, str) and not k.startswith("_")
        )
        assert total <= 2, f"Dublette {total}x statt <=2"

        # (d) Quellen-URL bleibt erhalten (kein Über-Scrubbing, KIS-1257)
        assert "unternehmensberatung_node" in fp

        # (e) DSGVO-Vorbehalt bleibt unter dem Cap von 2
        dsgvo = sum(
            str(v).count("DSGVO-Vorbehalt") for k, v in healed.items()
            if isinstance(v, str) and not k.startswith("_")
        )
        assert dsgvo <= 2

        # (f) Marken-Schreibweise kanonisiert (STYLE-LINT)
        es = healed.get("EXECUTIVE_SUMMARY_HTML", "")
        assert "KI-sicherheit.Jetzt" not in es
        assert "KI-Sicherheit.jetzt" in es


# =========================================================================
# 2. Sicherheits-Constraint: Firmenname wird NIRGENDS erhoben
# =========================================================================

_NAME_KEY_RE = re.compile(
    r"(unternehmens?[_-]?name|firmen[_-]?name|company[_-]?name|firma\b)",
    re.IGNORECASE,
)


class TestNoCompanyNameInvariant:

    def test_no_gold_profile_carries_a_company_name_field(self):
        for path in sorted(glob.glob("data/test_profiles_gold/*.json")):
            data = json.load(open(path, encoding="utf-8"))
            keys = list(data) + list(data.get("answers") or {})
            offenders = [k for k in keys if _NAME_KEY_RE.search(k)]
            assert not offenders, f"{path}: Firmennamens-Feld {offenders}"

    def test_name_leak_tripwire_is_armed(self):
        # Beweist, dass das Gate einen Namens-Leak WÜRDE erkennen — der
        # Detektor selbst darf nie stillschweigend stumpf werden.
        from services.platin_qa import scan_sections
        answers = dict(_load_profile(PROFILE_IDS[0])["answers"])
        answers["unternehmen_name"] = "Raststätten Müller GmbH"
        sections = {
            "EXECUTIVE_SUMMARY_HTML": (
                "<p>Dieser ausreichend lange Bericht für die Raststätten Müller GmbH "
                "beschreibt die KI-Ausgangslage im Detail und mit Kontext.</p>"
            )
        }
        findings = scan_sections(sections, answers)
        assert any(f["type"] == "name_leak" for f in findings)


# =========================================================================
# 3. Kanonik-Invariante: Business-Case-Mathematik bleibt konsistent
# =========================================================================

class TestCanonicalBusinessCaseMath:

    def test_kmu_reference_values(self):
        # Die Referenz-Kanonik aller Testläufe seit Lauf 1123:
        # 50h × 110 € − 600 € OPEX → 4.900 €/Monat Netto,
        # 48.000 € CAPEX → 9,8 Monate Payback, ~22,5 % Jahr-1-ROI.
        from services.business_case_engine_v2 import BusinessCaseCanonical
        bc = BusinessCaseCanonical(
            hours_saved_per_month=50, hourly_rate_eur=110,
            capex_eur=48000, opex_month_eur=600, company_size="kmu",
        )
        assert bc.monthly_net == 4900
        assert round(bc.payback_months, 1) == 9.8
        assert 22 <= bc.roi_12m_net_raw <= 23

    def test_payback_and_roi_are_formula_consistent(self):
        from services.business_case_engine_v2 import BusinessCaseCanonical
        for capex, hours in ((12000, 20), (48000, 50), (90000, 80)):
            bc = BusinessCaseCanonical(
                hours_saved_per_month=hours, hourly_rate_eur=110,
                capex_eur=capex, opex_month_eur=600,
            )
            assert bc.payback_months == pytest.approx(
                capex / (hours * 110 - 600), rel=0.01)
            assert bc.roi_12m_net_raw == pytest.approx(
                ((hours * 110 - 600) * 12 - capex) / capex * 100, rel=0.01)
