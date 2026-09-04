# -*- coding: utf-8 -*-
"""KIS-1293: Der Art.-50-Stichtag ist ein Datum, kein Prompt-Satz.

Lauf KIS1272 (04.09.2026) schrieb im Strategiebericht: „Da das Stichtagsdatum
in wenigen Wochen erreicht ist" — der 02.08.2026 lag da vier Wochen zurück.
Der Prompt sagte dem Modell „wenn das Reportdatum vor dem Stichtag liegt“,
gab ihm aber kein Reportdatum. Das Modell rechnete mit seinem Trainingsstand.

Hier steht die Rechnung einmal, deterministisch, für Prompt und HTML.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

ART50_STICHTAG = date(2026, 8, 2)


def verstrichen(heute: Optional[date] = None) -> bool:
    return (heute or date.today()) >= ART50_STICHTAG


def art50_satz(lang: str = "de", heute: Optional[date] = None) -> str:
    """Halbsatz für feste HTML-Hinweise: „gelten seit dem 2. August 2026“."""
    en = str(lang or "de").lower().startswith("en")
    if verstrichen(heute):
        return "have applied since 2 August 2026" if en else "gelten seit dem 2. August 2026"
    return "apply from 2 August 2026" if en else "gelten ab dem 2. August 2026"


def art50_prompt_text(lang: str = "de", heute: Optional[date] = None) -> str:
    """Anweisung für die Risiko-Sektion (S9) — mit ausgerechneter Zeitlage."""
    heute = heute or date.today()
    en = str(lang or "de").lower().startswith("en")
    tage = (ART50_STICHTAG - heute).days
    if verstrichen(heute):
        if en:
            return (
                f"DEADLINE (MANDATORY): Today is {heute.strftime('%d.%m.%Y')}. The Art. 50 EU AI Act "
                "transparency obligations (labelling of AI chatbots and AI-generated content) "
                "HAVE APPLIED SINCE 02.08.2026. Write 'in force since 02.08.2026'. FORBIDDEN: "
                "'in a few weeks', 'upcoming deadline', 'from 02.08.2026' or any other wording "
                "that presents the date as future. Frame the pressure to act as: the obligation "
                "already applies, every unlabelled output is a risk today. Do not invent any "
                "further deadlines."
            )
        return (
            f"FRISTEN (PFLICHT): Heute ist der {heute.strftime('%d.%m.%Y')}. Die Transparenzpflichten "
            "aus Art. 50 EU AI Act (Kennzeichnung von KI-Chatbots und KI-generierten Inhalten) "
            "GELTEN SEIT DEM 02.08.2026. Schreibe 'gilt seit dem 02.08.2026'. VERBOTEN: 'in wenigen "
            "Wochen', 'bevorstehender Stichtag', 'ab dem 02.08.2026' oder jede andere Formulierung, "
            "die das Datum als Zukunft darstellt. Handlungsdruck heißt: Die Pflicht gilt bereits, "
            "jede ungekennzeichnete Ausgabe ist heute ein Risiko. Keine weiteren Fristen erfinden."
        )
    if en:
        return (
            f"DEADLINE (MANDATORY): Today is {heute.strftime('%d.%m.%Y')}. The Art. 50 EU AI Act "
            f"transparency obligations apply from 02.08.2026 — in {tage} days. Make the remaining "
            "time visible as pressure to act. Do not invent any further deadlines."
        )
    return (
        f"FRISTEN (PFLICHT): Heute ist der {heute.strftime('%d.%m.%Y')}. Die Transparenzpflichten "
        f"aus Art. 50 EU AI Act gelten ab dem 02.08.2026 — in {tage} Tagen. Mache die verbleibende "
        "Zeit als Handlungsdruck sichtbar. Keine weiteren Fristen erfinden."
    )


RISIKOKLASSE_REGEL_DE = (
    "RISIKOKLASSE (PFLICHT): Werkzeuge für Text, Bild, Video und Ton (Office-Assistenten, "
    "Bild- und Videogeneratoren, Schnitt- und Transkriptions-KI) sind nach heutigem Stand KEINE "
    "Hochrisiko-Systeme nach Anhang III. Ordne sie unter 'begrenztes Risiko — Transparenzpflichten "
    "nach Art. 50' ein. 'Hochrisiko' nur, wenn ein Anwendungsfall aus Anhang III vorliegt "
    "(z. B. Personalauswahl, Kreditvergabe, biometrische Identifizierung) — dann nenne den "
    "Anwendungsfall, nicht das Werkzeug. VERBOTEN: 'fallen voraussichtlich unter Hochrisiko' "
    "für Standard-Werkzeuge."
)

RISIKOKLASSE_REGEL_EN = (
    "RISK CLASS (MANDATORY): Tools for text, image, video and audio (office assistants, image and "
    "video generators, editing and transcription AI) are, as of today, NOT high-risk systems under "
    "Annex III. Classify them as 'limited risk — transparency obligations under Art. 50'. "
    "'High-risk' only where an Annex III use case exists (e.g. recruitment, credit scoring, "
    "biometric identification) — then name the use case, not the tool. FORBIDDEN: 'will likely "
    "fall under high-risk' for standard tools."
)


def risikoklasse_regel(lang: str = "de") -> str:
    return RISIKOKLASSE_REGEL_EN if str(lang or "de").lower().startswith("en") else RISIKOKLASSE_REGEL_DE
