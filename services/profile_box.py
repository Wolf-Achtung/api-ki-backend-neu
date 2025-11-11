# -*- coding: utf-8 -*-
"""
services/profile_box.py
Builds a compact HTML profile box from questionnaire answers so that
all relevant fields and free-text inputs appear in the PDF.
"""
from __future__ import annotations
import html

LABELS = {
    "BRANCHE_LABEL": "Branche",
    "UNTERNEHMENSGROESSE_LABEL": "Größe",
    "BUNDESLAND_LABEL": "Bundesland",
    "hauptleistung": "Hauptleistung/Produkt",
    "zielgruppen": "Zielgruppen",
    "jahresumsatz": "Jahresumsatz",
    "it_infrastruktur": "IT-Infrastruktur",
    "interne_ki_kompetenzen": "Internes KI-/Digitalteam",
    "datenquellen": "Datenquellen",
    "digitalisierungsgrad": "Digitalisierungsgrad (1–10)",
    "prozesse_papierlos": "Papierlose Prozesse",
    "automatisierungsgrad": "Automatisierungsgrad",
    "ki_einsatz": "Bisheriger KI-Einsatz",
    "ki_kompetenz": "KI-Kompetenz",
    "ki_ziele": "KI-Ziele (3–6 Monate)",
    "ki_projekte": "Laufende/geplante KI-Projekte",
    "anwendungsfaelle": "Interessante Anwendungsfälle",
    "zeitersparnis_prioritaet": "Zeitersparnis-Priorität",
    "pilot_bereich": "Bester Pilotbereich",
    "geschaeftsmodell_evolution": "Geschäftsmodell-Idee",
    "vision_3_jahre": "Vision (3 Jahre)",
    "strategische_ziele": "Strategische Ziele",
    "massnahmen_komplexitaet": "Einführungsaufwand",
    "roadmap_vorhanden": "KI-Roadmap vorhanden",
    "governance_richtlinien": "KI-Governance vorhanden",
    "change_management": "Veränderungsbereitschaft",
    "zeitbudget": "Zeitbudget (pro Woche)",
    "vorhandene_tools": "Bereits genutzte Systeme",
    "regulierte_branche": "Regulierte Branche",
    "trainings_interessen": "Trainingsthemen",
    "vision_prioritaet": "Strategischer Hebel",
    "datenschutzbeauftragter": "Datenschutzbeauftragter vorhanden",
    "technische_massnahmen": "Technische Schutzmaßnahmen",
    "folgenabschaetzung": "DSFA",
    "meldewege": "Meldewege bei Vorfällen",
    "loeschregeln": "Lösch- & Anonymisierungsregeln",
    "ai_act_kenntnis": "Kenntnis EU AI Act",
    "ki_hemmnisse": "Hemmnisse",
    "bisherige_foerdermittel": "Bisherige Fördermittel",
    "interesse_foerderung": "Interesse an Förderung",
    "erfahrung_beratung": "Bisherige Beratung",
    "investitionsbudget": "Investitionsbudget (nächstes Jahr)",
    "marktposition": "Marktposition",
    "benchmark_wettbewerb": "Wettbewerbsvergleich",
    "innovationsprozess": "Entstehung von Innovationen",
    "risikofreude": "Risikofreude (1–5)",
}

ORDER = [
    "BRANCHE_LABEL","UNTERNEHMENSGROESSE_LABEL","BUNDESLAND_LABEL","hauptleistung","zielgruppen","jahresumsatz",
    "it_infrastruktur","interne_ki_kompetenzen","datenquellen","digitalisierungsgrad","prozesse_papierlos",
    "automatisierungsgrad","ki_einsatz","ki_kompetenz","ki_ziele","ki_projekte","anwendungsfaelle","zeitersparnis_prioritaet",
    "pilot_bereich","geschaeftsmodell_evolution","vision_3_jahre","strategische_ziele","massnahmen_komplexitaet",
    "roadmap_vorhanden","governance_richtlinien","change_management","zeitbudget","vorhandene_tools","regulierte_branche",
    "trainings_interessen","vision_prioritaet","datenschutzbeauftragter","technische_massnahmen","folgenabschaetzung",
    "meldewege","loeschregeln","ai_act_kenntnis","ki_hemmnisse","bisherige_foerdermittel","interesse_foerderung",
    "erfahrung_beratung","investitionsbudget","marktposition","benchmark_wettbewerb","innovationsprozess","risikofreude"
]

def _fmt(v):
    if isinstance(v, list):
        return ", ".join([str(x) for x in v if str(x).strip()])
    return str(v or "").strip()

def build_profile_box(answers: dict) -> str:
    """Return HTML table with most questionnaire answers in two columns."""
    rows = []
    # Derive label fallbacks for uppercase fields if lowercase exists
    answers = dict(answers or {})
    answers.setdefault("BRANCHE_LABEL", answers.get("branche",""))
    answers.setdefault("UNTERNEHMENSGROESSE_LABEL", answers.get("unternehmensgroesse",""))
    answers.setdefault("BUNDESLAND_LABEL", answers.get("bundesland",""))

    for key in ORDER:
        if key not in LABELS: 
            continue
        val = answers.get(key)
        if val in (None, "", [], {}): 
            continue
        rows.append(f"<tr><td><strong>{html.escape(LABELS[key])}</strong></td><td>{html.escape(_fmt(val))}</td></tr>")
    if not rows:
        return "<p class='small muted'>Keine Angaben vorhanden.</p>"
    return (
        "<table class='table'>"
        "<thead><tr><th>Feld</th><th>Angabe</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )