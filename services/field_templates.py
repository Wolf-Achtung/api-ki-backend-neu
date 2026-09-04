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
    # KIS-1243: zeitersparnis_prioritaet und top_zeitfresser sind jetzt
    # Template-Felder. Beide tragen deterministische Chips — die Frage muss
    # daher ebenfalls deterministisch sein, sonst laufen Sonnet-Frage und
    # Chips auseinander (Tools-Block Anlauf 4: Zeitfresser-Chips unter der
    # Tools-Frage). Die Template-Texte grenzen die beiden Felder außerdem
    # sprachlich sauber ab (Bereich vs. konkrete Aufgaben).
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
    "vorhandene_tools": "Welche klassischen Business-Systeme (CRM, ERP, Projektmanagement, Buchhaltung) nutzen Sie aktuell? KI-Tools fragen wir separat ab.",
    # KIS-1255: branchenneutral — nicht jede Branche arbeitet in "Projekten"
    # (Lauf 1123: Restaurant-Kette). Die Klammer nennt Beispiele statt den
    # Begriff vorauszusetzen; der Chat-LLM passt die Formulierung zusätzlich
    # an die bekannte Branche an (BRANCHENGERECHTE SPRACHE).
    "projekte_pro_monat": "Wie viele Aufträge oder Vorgänge (z. B. Projekte, Bestellungen, Fälle) bearbeiten Sie üblicherweise pro Monat?",
    # KIS-1243: Bereichs-Frage vs. Aufgaben-Frage — bewusst unterschiedlich
    # formuliert, damit die beiden Zeitfresser-Felder nicht wie eine
    # Doppel-Frage wirken (Anlauf 4, Tools-Block).
    "zeitersparnis_prioritaet": "In welchem Bereich Ihrer Arbeit soll KI Sie zuerst entlasten — wo wäre gewonnene Zeit am wertvollsten?",
    "top_zeitfresser": "Und ganz konkret: Welche zwei, drei Einzelaufgaben kosten Sie im Arbeitsalltag die meiste Zeit?",
    "trainings_interessen": "Welche KI-Trainingsthemen interessieren Sie?",
    "zeitbudget": "Wie viel Zeit pro Woche können Sie für KI-Projekte aufbringen?",
    "prozesse_papierlos": "Wie hoch ist der Anteil papierloser Prozesse bei Ihnen?",
    "it_infrastruktur": "Wie ist Ihre IT-Infrastruktur aufgestellt?",
    "interne_ki_kompetenzen": "Gibt es bei Ihnen systematisch aufgebautes KI-Know-how? Bei Solo-Selbstständigen zählt Ihre eigene Kompetenz.",
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

    # ── KIS-1278: Freitext-Felder (Sonnet-pflichtig im Chat) ──
    # Diese Einträge dienen NUR dem Fast-Mode-Formular (GET
    # /session/{id}/fast-mode) — dort erschien bisher das nackte Label
    # ("3-Jahres-Vision") ohne jeden Hinweis, WAS einzutragen ist.
    # Der Template-Mode im Chat bleibt unverändert: get_template_question /
    # is_template_field gaten weiterhin über SONNET_REQUIRED_FIELDS.
    "ki_projekte": (
        "Gibt es bei Ihnen schon KI-Tests, Tools oder Projekte — auch "
        "informelle? Stichworte reichen."
    ),
    "geschaeftsmodell_evolution": (
        "Könnte KI Ihr Geschäftsmodell selbst verändern — etwa durch neue "
        "Produkte, Kundengruppen oder Vertriebswege?"
    ),
    "vision_3_jahre": (
        "Wo soll Ihr Unternehmen in 2–3 Jahren mit KI stehen? "
        "Stichworte reichen völlig."
    ),
    "strategische_ziele": (
        "Was soll KI bei Ihnen in den nächsten 6–12 Monaten konkret "
        "verbessern?"
    ),
    "ki_guardrails": (
        "Gibt es No-Gos oder sensible Bereiche beim KI-Einsatz — etwa "
        "Kundendaten oder finale Entscheidungen?"
    ),
}


# ──────────────────────────────────────────────────────────────────────
# KIS-1278: EN question texts (native English, same keys as
# FIELD_QUESTIONS).
#
# Used ONLY where the backend serves deterministic question text to
# lang=en sessions: the fast-mode form (previously fell back to the bare
# EN field label, e.g. "3-year vision") and the deterministic
# empty-response / question-guarantee fallbacks in routes/chat.py
# (previously the generic "Next up: <label> — how does that look for
# you?"). Regular EN chat turns keep going through Sonnet — the template
# short-cut stays DE-only.
# ──────────────────────────────────────────────────────────────────────

FIELD_QUESTIONS_EN: dict[str, str] = {
    # ── Phase 1a ──
    "branche": "What industry are you in?",
    "unternehmensgroesse": "How large is your company?",
    "selbststaendig": "What is your business structure?",
    "country": "In which country is your company based?",
    "bundesland": "In which federal state or region?",
    "investitionsbudget": "What investment budget are you planning for AI?",

    # ── Phase 1b ──
    "digitalisierungsgrad": "How digital is your company on a scale of 1–10?",
    "ki_kompetenz": "How would you rate the AI competence in your team?",
    "ki_ziele": "What are your most important goals for using AI?",

    # ── Block A ──
    "bisherige_foerdermittel": "Have you already used funding programmes for digitalisation or AI?",
    "interesse_foerderung": "Are you interested in funding programmes for AI investments?",
    "erfahrung_beratung": "Have you already used external consulting on AI topics?",
    "marktposition": "How would you rate your current market position?",
    "benchmark_wettbewerb": "Do you regularly compare yourself with competitors?",
    "risikofreude": "How much risk are you willing to take with innovations and new business areas?",
    "jahresumsatz": "Roughly what is your annual revenue?",

    # ── Block B ──
    "roadmap_vorhanden": "Does your company already have an AI roadmap or strategy?",
    "change_management": "How high is the willingness to change in your team?",
    "massnahmen_komplexitaet": "How would you rate the effort of introducing AI?",
    "vision_prioritaet": "What is the most important strategic lever for AI in your company?",
    "innovationsprozess": "How do innovations come about in your company?",
    "zielgruppen": "Who are your most important target groups?",
    "governance_richtlinien": "Do you already have AI governance guidelines?",

    # ── Block C ──
    "automatisierungsgrad": "How automated are your business processes?",
    "ki_einsatz": "In which areas are you already using AI?",
    "anwendungsfaelle": "Which AI use cases are particularly interesting for you?",
    "pilot_bereich": "In which area would you most likely start an AI pilot project?",
    "vorhandene_tools": (
        "Which classic business systems (CRM, ERP, project management, "
        "accounting) do you currently use? We'll ask about AI tools separately."
    ),
    "projekte_pro_monat": (
        "How many orders or transactions (e.g. projects, orders, cases) "
        "do you typically handle per month?"
    ),
    "zeitersparnis_prioritaet": (
        "In which area of your work should AI relieve you first — "
        "where would saved time be most valuable?"
    ),
    "top_zeitfresser": (
        "And specifically: which two or three individual tasks cost you "
        "the most time in your day-to-day work?"
    ),
    "trainings_interessen": "Which AI training topics interest you?",
    "zeitbudget": "How much time per week can you dedicate to AI projects?",
    "prozesse_papierlos": "What share of your processes is paperless?",
    "it_infrastruktur": "How is your IT infrastructure set up?",
    "interne_ki_kompetenzen": (
        "Do you have systematically built AI know-how? "
        "For solo entrepreneurs, your own competence counts."
    ),
    "datenquellen": "Which data sources are available to you for AI applications?",

    # ── Block D ──
    "datenschutz": "How important is data protection to you when using AI?",
    "datenschutzbeauftragter": "Do you have a data protection officer?",
    "technische_massnahmen": "How are you doing on technical safeguards for your data?",
    "folgenabschaetzung": "Has a data protection impact assessment been carried out?",
    "meldewege": "Are reporting channels for security incidents clearly defined?",
    "loeschregeln": "Are there documented deletion and anonymisation policies?",
    "ai_act_kenntnis": "How familiar are you with the EU AI Act?",
    "regulierte_branche": "Is your industry subject to specific regulatory requirements?",
    "ki_hemmnisse": "What is currently slowing you down most in adopting AI?",

    # ── KIS-1278: freetext fields (Sonnet-required in chat) ──
    "ki_projekte": (
        "Are there any AI experiments, tools or projects at your company — "
        "even informal ones? Keywords are fine."
    ),
    "geschaeftsmodell_evolution": (
        "Could AI change your business model itself — for example through "
        "new products, customer groups or sales channels?"
    ),
    "vision_3_jahre": (
        "Where do you want your company to be with AI in 2–3 years? "
        "Keywords are perfectly fine."
    ),
    "strategische_ziele": (
        "What should AI concretely improve for you over the next "
        "6–12 months?"
    ),
    "ki_guardrails": (
        "Are there any no-gos or sensitive areas for AI use — such as "
        "customer data or final decisions?"
    ),
}


# ──────────────────────────────────────────────────────────────────────
# KIS-1138: Inspiration chips for strategic-imaginative freetext fields
#
# For 4 Block-B fields where users tend to stall ("I don't know what to
# write"), we surface 3 short half-sentences as chips the frontend renders
# beneath the input. Scope is deliberately limited to strategic-imaginative
# fields; concrete-experiential fields (hauptleistung, ki_projekte) get no
# chips here — users have lived experience there. zeitersparnis_prioritaet
# bekommt branchenspezifische Chips über FREETEXT_SUGGESTIONS (routes/chat).
# ──────────────────────────────────────────────────────────────────────

FIELD_EXAMPLES: dict[str, list[str]] = {
    # KIS-1264: User-Feedback (Screenshot Lauf 1125) — die alten drei Chips
    # waren drei Beratersprech-Varianten von "Ja" (Chip 1 ≈ Chip 3) ohne
    # Nein-Pfad, obwohl die Frage als Ja/Nein-Frage gestellt wird ("Könnte
    # KI Ihr Geschäftsmodell selbst verändern?"). Neu: Klartext, drei
    # DISTINKTE Richtungen inkl. ehrlichem Nein — auch "KI nur intern" ist
    # eine vollwertige, report-relevante Antwort.
    "geschaeftsmodell_evolution": [
        "Ja, neue digitale Produkte oder Services denkbar",
        "Ja, neue Kundengruppen oder Vertriebswege erschließen",
        "Eher nein, KI soll vor allem intern entlasten",
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
    # KIS-1235-P3: Zeitfresser als Quick-Win-Anker
    # KIS-1255: "nach Projektabschluss" → "im Nachgang" (branchenneutral)
    "top_zeitfresser": [
        "Angebote und Proposals schreiben",
        "E-Mail-Korrespondenz und laufende Terminabstimmung",
        "Dokumentation und Berichte im Nachgang",
    ],
}


# EN chip variants for lang=en sessions (same keys/order as FIELD_EXAMPLES;
# fallback: German list — never crash).
FIELD_EXAMPLES_EN: dict[str, list[str]] = {
    "geschaeftsmodell_evolution": [
        "Yes, new digital products or services conceivable",
        "Yes, reach new customer groups or sales channels",
        "Rather no, AI should mainly help internally",
    ],
    "vision_3_jahre": [
        "AI is an integral part of the business model",
        "New AI-based offerings established",
        "The whole organisation works AI-natively",
    ],
    "strategische_ziele": [
        "Automate recurring tasks and win back time",
        "Significantly shorten customer response times",
        "Ensure consistent quality at growing volume",
    ],
    "ki_guardrails": [
        "No customer data in external AI tools",
        "Final decisions made by humans only",
        "Clearly label AI-generated content",
    ],
    "top_zeitfresser": [
        "Writing offers and proposals",
        "Email correspondence and ongoing scheduling",
        "Documentation and follow-up reports",
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
        "seit August 2026 weitgehend anwendbar."
    ),
    "ki_hemmnisse": (
        "Mehrfachauswahl möglich — welche Hürden bremsen den KI-Einsatz?"
    ),
}


# EN variants for lang=en sessions (fallback: German text — never crash).
FIELD_DESCRIPTIONS_SHORT_EN: dict[str, str] = {
    "datenschutzbeauftragter": (
        "Usually mandatory from 20 employees with systematic data processing."
    ),
    "technische_massnahmen": (
        "E.g. encryption, access control, backups."
    ),
    "folgenabschaetzung": (
        "Required when processing sensitive or extensive personal data."
    ),
    "meldewege": (
        "Who informs whom, and how quickly, after data breaches or incidents?"
    ),
    "loeschregeln": (
        "Rules for when and how data is deleted or anonymised."
    ),
    "ai_act_kenntnis": (
        "EU law regulating AI, phased in, largely applicable since August 2026."
    ),
    "ki_hemmnisse": (
        "Multiple selection possible — which hurdles slow down your AI adoption?"
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


def get_template_question_en(field_name: str) -> str | None:
    """KIS-1278: EN counterpart of get_template_question.

    Same SONNET_REQUIRED_FIELDS gate — freetext fields return None so
    Sonnet formulates them, exactly like the German path. Used by the
    deterministic EN fallbacks in routes/chat.py (empty-response guard,
    question guarantee).
    """
    if field_name in SONNET_REQUIRED_FIELDS:
        return None
    return FIELD_QUESTIONS_EN.get(field_name)


def is_template_field(field_name: str) -> bool:
    """Quick check: can this field be answered without Sonnet?"""
    return field_name not in SONNET_REQUIRED_FIELDS and field_name in FIELD_QUESTIONS
