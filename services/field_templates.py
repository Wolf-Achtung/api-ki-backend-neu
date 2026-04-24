# -*- coding: utf-8 -*-
"""
Deterministic field templates for QR-turns (no Sonnet call needed).

KIS-1128B V1-BE-1: Source of truth for question texts of QR fields.
QR button options are maintained in routes/chat.py (_QR_OPTIONS).

When a user clicks a QR button and the NEXT field has a template here,
the system can skip the Sonnet API call entirely and serve the question
text deterministically (~200ms instead of ~3300ms).
"""
from __future__ import annotations


# ──────────────────────────────────────────────────────────────────────
# Fields that ALWAYS need Sonnet (freetext answers expected)
# ──────────────────────────────────────────────────────────────────────

SONNET_REQUIRED_FIELDS: frozenset[str] = frozenset({
    "hauptleistung",
    "ki_projekte",
    "zeitersparnis_prioritaet",
    "geschaeftsmodell_evolution",
    "vision_3_jahre",
    "strategische_ziele",
    "ki_guardrails",
})


# ──────────────────────────────────────────────────────────────────────
# Template question texts for QR fields
#
# Each entry maps a field_name to the question Sonnet would normally ask.
# Texts are short, natural German, one sentence max.
# ──────────────────────────────────────────────────────────────────────

FIELD_QUESTIONS: dict[str, str] = {
    # ── Phase 1a (sequential QR) ──
    "branche": "In welcher Branche sind Sie tätig?",
    "unternehmensgroesse": "Wie groß ist Ihr Unternehmen?",
    "selbststaendig": "Welche Unternehmensform haben Sie?",
    "country": "In welchem Land ist Ihr Unternehmen ansässig?",
    "bundesland": "In welchem Bundesland bzw. welcher Region?",
    "investitionsbudget": "Wie hoch ist Ihr geplantes Investitionsbudget für KI?",

    # ── Phase 1b (QR fields asked in open conversation) ──
    "digitalisierungsgrad": "Wie digital arbeitet Ihr Unternehmen auf einer Skala von 1–10?",
    "ki_kompetenz": "Wie schätzen Sie die KI-Kompetenz in Ihrem Team ein?",
    "ki_ziele": "Was sind Ihre wichtigsten Ziele beim KI-Einsatz?",

    # ── Block A: Fördermittel & Budget ──
    "bisherige_foerdermittel": "Haben Sie bereits Fördermittel für Digitalisierung oder KI genutzt?",
    "interesse_foerderung": "Haben Sie Interesse an Förderprogrammen für KI-Investitionen?",
    "erfahrung_beratung": "Haben Sie bereits externe Beratung zu KI-Themen in Anspruch genommen?",
    "marktposition": "Wie schätzen Sie Ihre aktuelle Position im Markt ein?",
    "benchmark_wettbewerb": "Führen Sie regelmäßig Wettbewerber-Vergleiche durch?",
    "risikofreude": "Wie risikofreudig sind Sie bei Innovationen und neuen Geschäftsfeldern?",
    "jahresumsatz": "In welcher Größenordnung liegt Ihr Jahresumsatz?",

    # ── Block B: KI-Strategie & Roadmap (QR fields only) ──
    "roadmap_vorhanden": "Gibt es in Ihrem Unternehmen bereits eine KI-Roadmap oder -Strategie?",
    "change_management": "Wie hoch ist die Veränderungsbereitschaft in Ihrem Team?",
    "massnahmen_komplexitaet": "Wie schätzen Sie den Aufwand für die KI-Einführung ein?",
    "vision_prioritaet": "Was ist der wichtigste strategische Hebel für KI in Ihrem Unternehmen?",
    "innovationsprozess": "Wie entstehen Innovationen in Ihrem Unternehmen?",
    "zielgruppen": "Wer sind Ihre wichtigsten Zielgruppen?",
    "governance_richtlinien": "Gibt es bei Ihnen bereits KI-Governance-Richtlinien?",

    # ── Block C: Tools & Automatisierung ──
    "automatisierungsgrad": "Wie hoch ist der Automatisierungsgrad Ihrer Geschäftsprozesse?",
    "ki_einsatz": "In welchen Bereichen setzen Sie bereits KI ein?",
    "anwendungsfaelle": "Welche KI-Anwendungsfälle sind für Sie besonders interessant?",
    "pilot_bereich": "In welchem Bereich würden Sie am ehesten ein KI-Pilotprojekt starten?",
    "vorhandene_tools": "Welche Software-Systeme nutzen Sie aktuell?",
    "trainings_interessen": "Welche KI-Trainingsthemen interessieren Sie?",
    "zeitbudget": "Wie viel Zeit pro Woche können Sie für KI-Projekte aufbringen?",
    "prozesse_papierlos": "Wie hoch ist der Anteil papierloser Prozesse bei Ihnen?",
    "it_infrastruktur": "Wie ist Ihre IT-Infrastruktur aufgestellt?",
    "interne_ki_kompetenzen": "Gibt es in Ihrem Unternehmen internes KI-Know-how?",
    "datenquellen": "Welche Datenquellen stehen Ihnen für KI-Anwendungen zur Verfügung?",

    # ── Block D: Recht & Datenschutz ──
    "datenschutz": "Wie wichtig ist Ihnen Datenschutz beim KI-Einsatz?",
    "datenschutzbeauftragter": "Gibt es bei Ihnen einen Datenschutzbeauftragten?",
    "technische_massnahmen": "Wie steht es um technische Schutzmaßnahmen für Ihre Daten?",
    "folgenabschaetzung": "Wurde eine Datenschutz-Folgenabschätzung durchgeführt?",
    "meldewege": "Sind Meldewege bei Sicherheitsvorfällen klar definiert?",
    "loeschregeln": "Gibt es dokumentierte Lösch- und Anonymisierungsrichtlinien?",
    "ai_act_kenntnis": "Wie gut kennen Sie den EU AI Act?",
    "regulierte_branche": "Unterliegt Ihre Branche besonderen regulatorischen Anforderungen?",
    "ki_hemmnisse": "Was bremst Sie aktuell am meisten beim KI-Einsatz?",
}


# ──────────────────────────────────────────────────────────────────────
# KIS-1138: Inspiration chips for strategic-imaginative freetext fields
#
# For 4 Block-B fields where users tend to stall ("I don't know what to
# write"), we surface 3 short half-sentences as chips the frontend renders
# beneath the input. Scope is deliberately limited to strategic-imaginative
# fields; concrete-experiential fields (hauptleistung, ki_projekte,
# zeitersparnis_prioritaet) get no chips — users have lived experience there.
# ──────────────────────────────────────────────────────────────────────

FIELD_EXAMPLES: dict[str, list[str]] = {
    "geschaeftsmodell_evolution": [
        "Bestehende Leistungen als skalierbares KI-Produkt anbieten",
        "Neue Zielgruppen durch günstigere digitale Services",
        "KI als eigenständige Leistung vermarkten",
    ],
    "vision_3_jahre": [
        "KI ist fester Teil des Geschäftsmodells",
        "Neue KI-basierte Angebote etabliert",
        "Gesamte Organisation arbeitet KI-nativ",
    ],
    "strategische_ziele": [
        "Wiederkehrende Aufgaben automatisieren und Zeit gewinnen",
        "Reaktionszeiten im Kundenkontakt deutlich verkürzen",
        "Konsistente Qualität bei skalierendem Volumen sichern",
    ],
    "ki_guardrails": [
        "Keine Kundendaten in externe KI-Tools geben",
        "Finale Entscheidungen nur durch Menschen treffen",
        "KI-generierte Inhalte klar kennzeichnen",
    ],
}


# ──────────────────────────────────────────────────────────────────────
# Bug C H3: Short, user-visible field descriptions surfaced via
# QuickReply.description.
#
# DO NOT add DSGVO article numbers here — BLOCK_D_PROMPT's ARTIKEL-REGEL
# forbids them in user-facing strings. The long descriptions with article
# references live in services/chat_conversation.py:FIELD_DESCRIPTIONS and
# are Sonnet-prompt-internal only.
#
# Texts reviewed and signed off by Wolf 2026-04-22. All entries ≤ ~80
# chars so they fit under a chat bubble on mobile without clipping.
# ──────────────────────────────────────────────────────────────────────

FIELD_DESCRIPTIONS_SHORT: dict[str, str] = {
    "datenschutzbeauftragter": (
        "Ab 20 Mitarbeitenden mit systematischer Datenverarbeitung meist Pflicht."
    ),
    "technische_massnahmen": (
        "Gemeint sind z. B. Verschlüsselung, Zugriffskontrolle, Backups."
    ),
    "folgenabschaetzung": (
        "Nötig bei Verarbeitung sensibler oder umfangreicher personenbezogener Daten."
    ),
    "meldewege": (
        "Wer informiert wen wie schnell bei Datenpannen oder Sicherheitsvorfällen?"
    ),
    "loeschregeln": (
        "Regeln, wann und wie Daten gelöscht oder anonymisiert werden."
    ),
    "ai_act_kenntnis": (
        "EU-Gesetz zur KI-Regulierung, schrittweise wirksam, "
        "volle Anwendung ab August 2026."
    ),
    "ki_hemmnisse": (
        "Mehrfachauswahl möglich — welche Hürden bremsen den KI-Einsatz?"
    ),
}


# ──────────────────────────────────────────────────────────────────────
# KIS-1128B V1-BE-3: Deterministic confirmation sentences
#
# Short confirmations prepended to the template question.
# Varied to avoid "Notiert." 14x in a row.
# ──────────────────────────────────────────────────────────────────────

import random

_CONFIRMATIONS_SHORT: list[str] = [
    "Notiert.",
    "Erfasst.",
    "Verstanden.",
    "Alles klar.",
    "Gut.",
]

_CONFIRMATIONS_CONTEXTUAL: dict[str, list[str]] = {
    "risikofreude": ["Spannend.", "Verstanden."],
    "marktposition": ["Verstanden.", "Alles klar."],
    "bisherige_foerdermittel": ["Notiert.", "Erfasst."],
}


def get_confirmation(field_name: str, last_confirmation: str | None = None) -> str:
    """Return a short confirmation, avoiding repetition of the last one."""
    pool = _CONFIRMATIONS_CONTEXTUAL.get(field_name, _CONFIRMATIONS_SHORT)
    if last_confirmation:
        available = [c for c in pool if c != last_confirmation]
        if available:
            pool = available
    return random.choice(pool)


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def get_template_question(field_name: str) -> str | None:
    """Return question text if field can be answered deterministically.

    Returns None if the field requires Sonnet (freetext).
    """
    if field_name in SONNET_REQUIRED_FIELDS:
        return None
    return FIELD_QUESTIONS.get(field_name)


def is_template_field(field_name: str) -> bool:
    """Quick check: can this field be answered without Sonnet?"""
    return field_name not in SONNET_REQUIRED_FIELDS and field_name in FIELD_QUESTIONS
