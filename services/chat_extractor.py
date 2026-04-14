# -*- coding: utf-8 -*-
"""
Phase 1: Field extraction via Claude Haiku with tool_use.

The extractor receives the user message + recent conversation context
and returns structured fields using a tool call. It never writes to DB
directly — results go through the normalizer first.
"""
from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model Config
# ---------------------------------------------------------------------------
EXTRACTOR_MODEL = os.getenv(
    "CHAT_EXTRACTOR_MODEL", "claude-haiku-4-5-20251001"
)

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
EXTRACTOR_SYSTEM_PROMPT = """\
Du bist ein Daten-Extractor für einen KI-Readiness-Fragebogen.
Analysiere die Nutzerantwort und extrahiere strukturierte Felder
mit dem Tool update_intake_fields.

STRIKTE EXTRAKTIONSREGEL:
Du bist ein EXTRAKTOR, kein ANALYST.
- Extrahiere NUR Werte, die der User mit eigenen Worten EXPLIZIT gesagt hat.
- VERBOTEN: Logische Schlussfolgerungen, Kategorie-Mapping, Kontextableitung.
- Leere Felder sind BESSER als falsche Felder.

REGELN:
1. Setze NUR Felder, die der Nutzer EXPLIZIT genannt hat.
2. Erfinde NIEMALS Werte. Inferiere KEINE Werte aus dem Kontext.
3. Wenn unsicher, setze das Feld NICHT.
4. ERLAUBTE Normalisierung (Format-Transformation, KEINE Inhalts-Inferenz):
   - "in München" → bundesland: "München" (wird extern normalisiert)
   - "8 Mitarbeiter" → unternehmensgroesse: "8" (wird extern normalisiert)
   - "Handwerksbetrieb" → branche: "Handwerk" (wird extern normalisiert)
   - "komplett digital" → digitalisierungsgrad: 9 (NICHT 10 — 10 = kein \
   einziger analoger Prozess denkbar; "komplett/voll digital" → maximal 9)
   VERBOTENE Inferenz (Inhalte ableiten, die der User NICHT gesagt hat):
   - "Beratung von Unternehmen" → NICHT zielgruppen: ["b2b"] ableiten. \
     Das ist NUR relevant für "hauptleistung". Daraus NICHT ableiten: \
     zielgruppen, ki_einsatz, oder andere Felder.
   - User nennt "Content-Generierung, Datenanalyse" als Anwendungsfälle → \
     Trage das NUR bei "anwendungsfaelle" ein — NICHT bei "ki_einsatz".
   - User sagt "Markteintritt, Kundenakquise" als Ziele → Extrahiere die \
     WORTE des Users, NICHT Synonyme wie "Wettbewerbsfähigkeit" oder \
     "Automatisierung".
   Regel: Wenn der User ein Feld nicht DIREKT anspricht, setze es NICHT.
5. FELD-ISOLATION (Cross-Contamination verhindern):
   - ki_einsatz = wo KI HEUTE SCHON produktiv im Einsatz ist. \
     NUR setzen wenn der User sagt "wir nutzen KI für X" oder "KI läuft bei uns in Y".
   - anwendungsfaelle = was den User INTERESSIERT oder was er PLANT. \
     Wenn User Anwendungsfälle als Interesse nennt, NICHT in ki_einsatz kopieren.
   - ki_ziele = was der User als ZIEL oder WUNSCH formuliert. \
     NUR die Worte des Users verwenden, KEINE Buzzwords substituieren. \
     NICHT aus hauptleistung oder anwendungsfaelle ableiten.
   - zielgruppen = NUR setzen wenn der User explizit "meine Zielgruppe ist X" sagt. \
     NICHT aus Branche, Hauptleistung oder Kontext ableiten.
6. Bei Freitextfeldern: den Kern der Aussage in 1–3 Sätzen zusammenfassen.
7. Wenn der Nutzer eine Rückfrage stellt statt zu antworten,
   rufe das Tool NICHT auf.
8. Wenn der Nutzer auf ein Feld mit einer Ablehnung oder \
einem Skip-Signal antwortet (z.B. „nein", „keine Ahnung", „noch keine Idee", \
„weiß nicht", „weiß nicht genau", „weiter", „skip", „überspringen", \
„keine", „k.A.", „noch nicht", „nicht wirklich", „keine Angabe", \
„das kann ich nicht entscheiden", „schwer zu sagen", „müsste ich nachschauen", \
„egal", „ist mir nicht wichtig", „spielt keine Rolle", \
„kann ich nicht sagen", „keine Vorstellung", „passe", \
„überspring das", „kein Plan", „keine Idee"), dann extrahiere \
das aktuell gefragte Feld mit dem Wert „keine_angabe". \
Skip-Signale sind GÜLTIGE Antworten, NICHT „off-topic". \
Auch bei Pflichtfeldern: Wenn der Nutzer klar signalisiert, dass er \
nicht antworten kann oder will, setze „keine_angabe".

AKTUELL GEFRAGTES FELD: {current_field}
{current_field_hint}
Die Antwort des Nutzers bezieht sich höchstwahrscheinlich auf dieses Feld.
Wenn die Antwort plausibel zu diesem Feld passt, setze es.

Aktuell fehlende Felder: {missing_fields}
Bereits erfasst: {collected_fields}"""

# Draft-mode extension — appended to EXTRACTOR_SYSTEM_PROMPT when draft_mode=True
_DRAFT_SIGNAL_EXTENSION = """

SIGNAL-ERKENNUNG (Draft-Modus aktiv):
Zusätzlich zum Tool-Call gib ein Signal über das Feld "_signal" zurück:

1. Wenn der User eine RÜCKFRAGE stellt (Fragezeichen, "was meinst du",
   "kannst du erklären", "warum", "wie genau", "was bedeutet"):
   → Rufe das Tool mit einem einzigen Feld auf: {{"_signal": "question"}}
   → Extrahiere KEINE inhaltlichen Felder.

2. Wenn der User einen BESTEHENDEN WERT BESTÄTIGT ("ja", "stimmt",
   "passt", "genau", "korrekt", "übernehmen", "ok"):
   → Rufe das Tool mit: {{"_signal": "confirm"}}
   → Extrahiere KEINE inhaltlichen Felder.

3. Wenn der User einen BESTEHENDEN WERT KORRIGIEREN will ("nein",
   "nicht ganz", "ich meinte", "eigentlich", "ändere das"):
   → Extrahiere den korrigierten Wert ganz normal als Feld.
   → Zusätzlich: {{"_signal": "correction"}}

4. Wenn der User eine INHALTLICHE ANTWORT gibt:
   → Extrahiere wie bisher.
   → Kein _signal-Feld nötig.

{pending_context}"""

# ---------------------------------------------------------------------------
# Tool Definition — ALL fields (Sektionen 0–7)
# ---------------------------------------------------------------------------
EXTRACTOR_TOOL: dict[str, Any] = {
    "name": "update_intake_fields",
    "description": (
        "Extrahiert strukturierte Felder aus der User-Nachricht. "
        "Nur Felder setzen, die der User tatsächlich genannt hat. "
        "Niemals Werte erfinden oder raten."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            # --- Sektion 0: Ihr Unternehmen ---
            "branche": {
                "type": "string",
                "description": "Branche des Unternehmens (z.B. bau, it, marketing, beratung, handel, gastronomie)",
            },
            "unternehmensgroesse": {
                "type": "string",
                "description": "Anzahl Mitarbeiter als Zahl oder Kategorie (z.B. '1', '8', '2-10', 'solo')",
            },
            "selbststaendig": {
                "type": "string",
                "description": "Unternehmensform bei Einzelperson: freiberufler, kapitalgesellschaft, einzelunternehmer, sonstiges",
            },
            "country": {
                "type": "string",
                "description": "Land als ISO-Code oder Name (z.B. DE, AT, CH, Deutschland, Österreich)",
            },
            "bundesland": {
                "type": "string",
                "description": "Bundesland, Kanton, Region oder Stadt (wird zu Bundesland-Code normalisiert)",
            },
            "hauptleistung": {
                "type": "string",
                "description": "Haupttätigkeit/Kernleistung des Unternehmens in 1–3 Sätzen",
            },
            "jahresumsatz": {
                "type": "string",
                "description": "Ungefährer Jahresumsatz (z.B. unter_100k, 100k_500k, 500k_2m, 2m_10m, ueber_10m)",
            },
            # --- Sektion 1: Organisation & Datenlage ---
            "zielgruppen": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Zielgruppen des Unternehmens (z.B. b2b, b2c, kmu, grossunternehmen, selbststaendige, oeffentliche_hand, privatpersonen, startups)",
            },
            "it_infrastruktur": {
                "type": "string",
                "description": "IT-Infrastruktur: cloud, on_premise, hybrid, unklar",
            },
            "interne_ki_kompetenzen": {
                "type": "string",
                "description": "Ob ein internes KI-/Digitalisierungsteam existiert: ja, nein, in_planung",
            },
            "datenquellen": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Verfügbare Datentypen (z.B. kundendaten, verkaufsdaten, produktionsdaten, personaldaten, marketingdaten, sonstige)",
            },
            # --- Sektion 2: Digitalisierung & KI-Status ---
            "digitalisierungsgrad": {
                "type": "integer",
                "description": "Digitalisierungsgrad 1–10 (1=sehr niedrig, 10=sehr hoch)",
            },
            "prozesse_papierlos": {
                "type": "string",
                "description": "Anteil papierloser Prozesse: 0-20, 21-50, 51-80, 81-100",
            },
            "automatisierungsgrad": {
                "type": "string",
                "description": "Automatisierungsgrad: sehr_niedrig, eher_niedrig, mittel, eher_hoch, sehr_hoch",
            },
            "ki_einsatz": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Bereiche mit KI-Einsatz (z.B. chatbots, marketing, vertrieb, datenanalyse, produktion, hr, andere, noch_keine)",
            },
            "ki_kompetenz": {
                "type": "string",
                "description": "KI-Kompetenz im Team: hoch, mittel, niedrig, keine",
            },
            # --- Sektion 3: Ziele & Use Cases ---
            "ki_ziele": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ziele mit KI — verwende die EXAKTEN WORTE des Users, "
                "NICHT vordefinierte Kategorien. Wenn der User 'von der Testphase "
                "auf den Markt kommen' sagt, extrahiere genau das.",
            },
            "ki_projekte": {
                "type": "string",
                "description": "Freitext: bestehende KI-Tests, Tools oder Projekte (auch informell)",
            },
            "anwendungsfaelle": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Interessante Anwendungsfälle (z.B. chatbots, content_generation, datenanalyse, dokumentation, prozess_automation, personalisierung)",
            },
            "zeitersparnis_prioritaet": {
                "type": "string",
                "description": "Freitext: Wo frisst heute am meisten Zeit oder Nerven?",
            },
            "pilot_bereich": {
                "type": "string",
                "description": "Bester Bereich für Pilotprojekt: kundenservice, marketing, vertrieb, verwaltung, produktion, andere",
            },
            "geschaeftsmodell_evolution": {
                "type": "string",
                "description": "Freitext: Ideen wie KI das Geschäftsmodell verändern oder ergänzen könnte",
            },
            "vision_3_jahre": {
                "type": "string",
                "description": "Freitext: Wie soll das Unternehmen in 2–3 Jahren mit KI arbeiten?",
            },
            # --- Sektion 4: Strategie & Governance ---
            "strategische_ziele": {
                "type": "string",
                "description": "Freitext: Was soll KI in 6–12 Monaten konkret verbessern?",
            },
            "ki_guardrails": {
                "type": "string",
                "description": "Freitext: No-Gos oder sensible Themen beim KI-Einsatz",
            },
            "massnahmen_komplexitaet": {
                "type": "string",
                "description": "Aufwand für KI-Einführung: niedrig, mittel, hoch, unklar",
            },
            "roadmap_vorhanden": {
                "type": "string",
                "description": "KI-Roadmap/Strategie vorhanden: ja, teilweise, nein",
            },
            "governance_richtlinien": {
                "type": "string",
                "description": "KI-Governance-Richtlinien vorhanden: ja, teilweise, nein",
            },
            "change_management": {
                "type": "string",
                "description": "Veränderungsbereitschaft im Team: sehr_hoch, hoch, mittel, niedrig, sehr_niedrig",
            },
            # --- Sektion 5: Ressourcen & Umsetzung ---
            "zeitbudget": {
                "type": "string",
                "description": "Zeit pro Woche für KI-Projekte: unter_2, 2_5, 5_10, ueber_10",
            },
            "vorhandene_tools": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Bereits genutzte Systeme (z.B. crm, erp, projektmanagement, marketing_automation, buchhaltung, keine)",
            },
            "trainings_interessen": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Interessante KI-Trainingsthemen (z.B. prompt_engineering, llm_basics, datenqualitaet_governance, automatisierung, ethik_recht)",
            },
            "vision_prioritaet": {
                "type": "string",
                "description": "Wichtigster strategischer Hebel: gpt_services, kundenservice, datenprodukte, prozessautomation, marktfuehrerschaft, keine_angabe",
            },
            "innovationsprozess": {
                "type": "string",
                "description": "Wie entstehen Innovationen: innovationsteam, mitarbeitende, kunden, berater, zufall, unbekannt",
            },
            # --- Sektion 6: Recht & Datenschutz ---
            "datenschutzbeauftragter": {
                "type": "string",
                "description": "Datenschutzbeauftragter vorhanden: ja, nein, teilweise",
            },
            "technische_massnahmen": {
                "type": "string",
                "description": "Technische Schutzmaßnahmen: alle, teilweise, keine",
            },
            "folgenabschaetzung": {
                "type": "string",
                "description": "Datenschutz-Folgenabschätzung: ja, nein, teilweise",
            },
            "meldewege": {
                "type": "string",
                "description": "Meldewege bei Sicherheitsvorfällen: ja, teilweise, nein",
            },
            "loeschregeln": {
                "type": "string",
                "description": "Löschrichtlinien: ja, teilweise, nein",
            },
            "ai_act_kenntnis": {
                "type": "string",
                "description": "Kenntnis EU AI Act: sehr_gut, gut, gehoert, unbekannt",
            },
            "regulierte_branche": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Regulierte Branche (z.B. gesundheit, finanzen, oeffentlich, recht, vertraulich_nda, keine)",
            },
            "ki_hemmnisse": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Hemmnisse beim KI-Einsatz (z.B. rechtsunsicherheit, datenschutz, knowhow, budget, teamakzeptanz, zeitmangel, keine)",
            },
            # --- Sektion 7: Förderung & Investition ---
            "bisherige_foerdermittel": {
                "type": "string",
                "description": "Bereits Fördermittel erhalten: ja, nein",
            },
            "interesse_foerderung": {
                "type": "string",
                "description": "Interesse an Fördermöglichkeiten: ja, nein, unklar",
            },
            "erfahrung_beratung": {
                "type": "string",
                "description": "Bisherige Beratung zu Digitalisierung/KI: ja, nein, unklar",
            },
            "investitionsbudget": {
                "type": "string",
                "description": "Budget für KI nächstes Jahr: unter_2000, 2000_10000, 10000_50000, ueber_50000, unklar",
            },
            "marktposition": {
                "type": "string",
                "description": "Marktposition: marktfuehrer, oberes_drittel, mittelfeld, nachzuegler, unsicher",
            },
            "benchmark_wettbewerb": {
                "type": "string",
                "description": "Vergleich mit Wettbewerbern: ja, nein, selten",
            },
            "risikofreude": {
                "type": "integer",
                "description": "Risikofreude bei Innovation 1–5 (1=niedrig, 5=hoch)",
            },
        },
        "required": [],  # CRITICAL: extractor only sets actually mentioned fields
    },
}

# ---------------------------------------------------------------------------
# Tool Definition — Strategy (Report 3, 14 fields)
# ---------------------------------------------------------------------------
EXTRACTOR_TOOL_STRATEGY: dict[str, Any] = {
    "name": "update_intake_fields",
    "description": (
        "Extrahiert Strategy-Felder aus der Nutzerantwort. "
        "Nur Felder setzen, die der User tatsächlich genannt hat."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "s1_budget": {
                "type": "string",
                "description": "KI-Budget nächste 12 Monate: unter_2000, 2000_10000, 10000_50000, ueber_50000, unklar",
            },
            "s2_zeitrahmen": {
                "type": "string",
                "description": "Umsetzungszeitraum: Sofort (1-3 Monate), Kurzfristig (3-6 Monate), Mittelfristig (6-12 Monate), Langfristig (12-18 Monate)",
            },
            "s3_prioritaeten": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Top 3 Prioritäten beim KI-Einsatz (max 3): Kosten senken, Umsatz steigern, Qualität verbessern, Geschwindigkeit erhöhen, Compliance sichern, Neue Geschäftsfelder, Fachkräftemangel kompensieren, Kundenerlebnis verbessern",
            },
            "s4_engpass": {
                "type": "string",
                "description": "Größter einzelner Engpass: Zu wenig Know-how, Kein Budget, Fehlende Daten, Widerstand im Team, Regulatorische Unsicherheit, Kein klarer Use Case, Andere",
            },
            "s5_software": {
                "type": "string",
                "description": "Kommagetrennte Liste aktuell genutzter Software und Tools im Tagesgeschäft",
            },
            "s5_vision": {
                "type": "string",
                "description": "Persönliche KI-Vision für das Unternehmen (Freitext)",
            },
            "s6_foerderinteresse": {
                "type": "string",
                "description": "Interesse an Fördermitteln: Ja, dringend / Ja, wenn passend / Nein, eigenes Budget / Weiß nicht",
            },
            "s7_entscheidung": {
                "type": "string",
                "description": "Entscheidungsstruktur: Entscheide allein / Brauche Vorlage für Geschäftsleitung / Muss Gesellschafter überzeugen / Muss Aufsichtsrat/Beirat informieren",
            },
            "s8_erfahrung": {
                "type": "string",
                "description": "Bisherige KI-Erfahrung: Noch keine, Experimentiert, Erste Tools im Einsatz, Fortgeschritten",
            },
            "s9_ansatz": {
                "type": "string",
                "description": "Bevorzugter Infrastruktur-Ansatz: Cloud-SaaS, On-Premise, Hybrid, Egal",
            },
            "s10_datenschutz": {
                "type": "string",
                "description": "Datenschutz-Priorität: Hoch, Mittel, Niedrig",
            },
            "wettbewerber_anzahl": {
                "type": "string",
                "description": "Anzahl direkter Wettbewerber: wenige, mehrere, viele, unklar",
            },
            "kundenbindung_typ": {
                "type": "string",
                "description": "Art der Kundenbeziehungen: einmalig, wiederkehrend, gemischt",
            },
            "datenreife": {
                "type": "string",
                "description": "Verfügbarkeit eigener Datenbestände: keine, basis, umfangreich, unklar",
            },
        },
        "required": [],
    },
}


def _get_tool_for_report(report_type: str) -> dict[str, Any]:
    """Select the right extractor tool schema for a report type."""
    if report_type == "strategy":
        return EXTRACTOR_TOOL_STRATEGY
    return EXTRACTOR_TOOL


# ---------------------------------------------------------------------------
# Async Anthropic Client (singleton)
# ---------------------------------------------------------------------------
_async_client = None


def _get_async_client():
    """Lazy-initialize async Anthropic client."""
    global _async_client
    if _async_client is not None:
        return _async_client

    try:
        import anthropic
    except ImportError:
        log.error("[CHAT-EXTRACT] anthropic SDK not installed")
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("[CHAT-EXTRACT] ANTHROPIC_API_KEY not set")
        return None

    import httpx as _httpx

    base_timeout = float(os.getenv("ANTHROPIC_TIMEOUT", "60"))
    _async_client = anthropic.AsyncAnthropic(
        api_key=api_key,
        timeout=_httpx.Timeout(base_timeout, read=120.0),
    )
    log.info("[CHAT-EXTRACT] AsyncAnthropic client initialized (model=%s)", EXTRACTOR_MODEL)
    return _async_client


# ---------------------------------------------------------------------------
# Main Extraction Function
# ---------------------------------------------------------------------------

async def extract_fields(
    user_message: str,
    conversation_context: list[dict],
    missing_fields: list[str],
    collected_fields: dict,
    report_type: str = "r1",
    current_field: str = "",
    current_field_description: str = "",
    draft_mode: bool = False,
    pending_field: str | None = None,
    pending_value: Any = None,
) -> dict:
    """
    Call Claude Haiku with tool_use to extract structured fields.

    Args:
        user_message: The current user message
        conversation_context: Last 6 messages (3 turns) for context
        missing_fields: Fields still needed
        collected_fields: Already collected field values
        current_field: The field the AI just asked about
        current_field_description: Human description of that field
        draft_mode: When True, extractor returns signal + fields dict
        pending_field: Currently pending draft field (draft_mode only)
        pending_value: Currently pending draft value (draft_mode only)

    Returns:
        When draft_mode=False: Dict of extracted fields (backward compat).
        When draft_mode=True: {"signal": str|None, "fields": dict}
    """
    client = _get_async_client()
    if client is None:
        log.error("[CHAT-EXTRACT] No async client available")
        return {"signal": None, "fields": {}} if draft_mode else {}

    # Build messages: recent context + current message
    messages: list[dict] = []
    for turn in conversation_context[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    # Build current field hint
    if current_field and current_field_description:
        field_hint = f"{current_field} — {current_field_description}"
    elif current_field:
        field_hint = current_field
    else:
        field_hint = "keines (allgemeine Nachricht)"

    # Format system prompt with current state
    system = EXTRACTOR_SYSTEM_PROMPT.format(
        current_field=current_field or "keines",
        current_field_hint=f"Beschreibung: {current_field_description}" if current_field_description else "",
        missing_fields=", ".join(missing_fields) if missing_fields else "keine",
        collected_fields=_format_collected(collected_fields),
    )

    # Draft-mode: append signal detection instructions
    if draft_mode:
        pending_ctx = ""
        if pending_field and pending_value is not None:
            pending_ctx = (
                f'OFFENER ENTWURF: Feld "{pending_field}" hat den Entwurfswert: "{pending_value}"\n'
                f"Der User bestätigt, korrigiert oder fragt nach — handle entsprechend."
            )
        system += _DRAFT_SIGNAL_EXTENSION.format(pending_context=pending_ctx)

    # Build tool — add _signal property in draft mode
    tool = _get_tool_for_report(report_type)
    if draft_mode:
        tool = _add_signal_property(tool)

    try:
        response = await client.messages.create(
            model=EXTRACTOR_MODEL,
            max_tokens=500,
            system=system,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "auto"},  # auto: no tool call if user asks question
        )

        # Extract tool result
        for block in response.content:
            if block.type == "tool_use" and block.name == "update_intake_fields":
                extracted: dict = dict(block.input)
                signal = extracted.pop("_signal", None)
                extracted = _validate_extracted(extracted)
                log.info(
                    "[CHAT-EXTRACT] Extracted %d fields: %s (signal=%s)",
                    len(extracted),
                    list(extracted.keys()),
                    signal,
                )
                if draft_mode:
                    return {"signal": signal, "fields": extracted}
                return extracted

        # No tool call — user probably asked a question
        log.info("[CHAT-EXTRACT] No fields extracted (user question or off-topic)")
        if draft_mode:
            # No tool call in draft mode = likely a question
            return {"signal": "question", "fields": {}}
        return {}

    except Exception as exc:
        log.error("[CHAT-EXTRACT] Extraction failed: %s", exc, exc_info=True)
        return {"signal": None, "fields": {}} if draft_mode else {}


def _add_signal_property(tool: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the tool definition with _signal added to properties."""
    import copy
    tool = copy.deepcopy(tool)
    tool["input_schema"]["properties"]["_signal"] = {
        "type": "string",
        "enum": ["question", "confirm", "correction"],
        "description": (
            "Signal-Typ: 'question' wenn User eine Rückfrage stellt, "
            "'confirm' wenn User einen Entwurf bestätigt, "
            "'correction' wenn User einen Wert korrigiert. "
            "Nur setzen wenn zutreffend."
        ),
    }
    return tool


def _format_collected(collected: dict) -> str:
    """Format collected fields for the system prompt."""
    if not collected:
        return "keine"
    parts = []
    for k, v in collected.items():
        parts.append(f"{k}={v!r}")
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Post-Extraction Validation (Hallucination Guard)
# ---------------------------------------------------------------------------

# KIS-1124 Testrun 4 R2: Fields that must NEVER be auto-extracted.
# These fields are only set via explicit QR selection or direct question.
# Prompt rules alone cannot prevent Haiku from inferring these.
# KIS-1124-HOTFIX: Extended — Haiku was hallucinating values for all of these
# from unrelated answers (e.g. "Nein" → marktposition: "Nachzügler").
NEVER_AUTO_EXTRACT: set[str] = {
    "zielgruppen",
    "marktposition",
    "benchmark_wettbewerb",
    "risikofreude",
    "innovationsprozess",
    "interne_ki_kompetenzen",
}

# Array fields where Haiku tends to over-generate via category-mapping
_ARRAY_FIELDS_MAX = {
    "ki_einsatz": 4,
    "ki_ziele": 4,
    "zielgruppen": 4,
    "anwendungsfaelle": 5,
    "datenquellen": 5,
    "ki_hemmnisse": 4,
    "trainings_interessen": 4,
    "vorhandene_tools": 6,
    "regulierte_branche": 3,
}


def _validate_extracted(extracted: dict) -> dict:
    """Post-extraction validation to catch hallucination patterns.

    - Removes NEVER_AUTO_EXTRACT fields (e.g. zielgruppen).
    - Caps array fields at a reasonable max (truncates excess).
    - Clamps digitalisierungsgrad: "komplett digital" → max 9.
    - Logs warnings for suspicious extractions.
    """
    # Remove fields that must not be auto-extracted
    for field in NEVER_AUTO_EXTRACT:
        if field in extracted:
            log.info(
                "[CHAT-EXTRACT-VALIDATE] Removing auto-extracted '%s' "
                "(NEVER_AUTO_EXTRACT): %s",
                field, extracted[field],
            )
            del extracted[field]

    for field, max_len in _ARRAY_FIELDS_MAX.items():
        if field in extracted and isinstance(extracted[field], list):
            original_len = len(extracted[field])
            if original_len > max_len:
                log.warning(
                    "[CHAT-EXTRACT-VALIDATE] Suspicious: %s has %d values "
                    "(max %d) — truncating. Values: %s",
                    field, original_len, max_len, extracted[field],
                )
                extracted[field] = extracted[field][:max_len]

    # Digitalisierungsgrad: verbal→numeric mapping + cap at 9
    if "digitalisierungsgrad" in extracted:
        val = extracted["digitalisierungsgrad"]
        # KIS-1124 Testrun 3 Bugs 16+17: Map verbal answers to numeric
        if isinstance(val, str):
            _verbal_map = {
                "sehr niedrig": 2, "kaum digital": 2, "kaum": 2,
                "niedrig": 3, "wenig": 3,
                "mittel": 5, "durchschnittlich": 5, "halb-halb": 5,
                "hoch": 7, "gut": 7, "fortgeschritten": 7,
                "sehr hoch": 8, "weit fortgeschritten": 8,
                "komplett digital": 9, "voll digital": 9, "komplett": 9,
            }
            mapped = _verbal_map.get(val.lower().strip())
            if mapped:
                log.info(
                    "[CHAT-EXTRACT-VALIDATE] digitalisierungsgrad '%s' → %d",
                    val, mapped,
                )
                extracted["digitalisierungsgrad"] = mapped
                val = mapped
            else:
                # Try to parse as integer
                try:
                    val = int(val)
                    extracted["digitalisierungsgrad"] = val
                except (ValueError, TypeError):
                    log.warning(
                        "[CHAT-EXTRACT-VALIDATE] digitalisierungsgrad '%s' "
                        "could not be mapped — removing",
                        val,
                    )
                    del extracted["digitalisierungsgrad"]
                    val = None
        if isinstance(val, int) and val >= 10:
            log.info(
                "[CHAT-EXTRACT-VALIDATE] digitalisierungsgrad %d → capped to 9",
                val,
            )
            extracted["digitalisierungsgrad"] = 9

    return extracted


# ---------------------------------------------------------------------------
# KIS-1124 Sprint 2: Multi-Field Extraction for Phase 1 Free Conversation
# ---------------------------------------------------------------------------

MULTI_FIELD_SYSTEM_PROMPT = """\
Du bist ein Daten-Extractor für einen KI-Readiness-Fragebogen.
Analysiere die Nutzerantwort und extrahiere Werte für die unten
aufgelisteten Felder. Antworte NUR mit einem JSON-Objekt
über das Tool extract_multi_fields.

STRIKTE EXTRAKTIONSREGEL:
Du bist ein EXTRAKTOR, kein ANALYST.
- Extrahiere NUR Werte, die der User mit eigenen Worten EXPLIZIT gesagt hat.
- VERBOTEN: Logische Schlussfolgerungen, Kategorie-Mapping, Kontextableitung.
- Leere Felder sind BESSER als falsche Felder.
- Wenn ein Feld mehr als 3 Werte hätte: Prüfe kritisch, ob der User wirklich \
  ALLE diese Werte explizit genannt hat. Im Zweifel weniger extrahieren.

REGELN:
1. Setze NUR Felder, die der Nutzer EXPLIZIT genannt hat.
2. Erfinde NIEMALS Werte. Inferiere KEINE Werte aus dem Kontext.
3. Bei Unsicherheit: Feld NICHT setzen (weglassen).
4. Bei enum-Feldern: Exakt einen der vorgegebenen Werte verwenden.
5. Bei multi-Feldern: Array der erkannten Werte.
6. Bei text-Feldern: Relevanten Textabschnitt in 1–3 Sätzen zusammenfassen.
7. Bei slider-Feldern: Numerischen Wert ableiten (1–10).
8. ERLAUBTE Normalisierung (Format-Transformation, KEINE Inhalts-Inferenz):
   - "in München" → bundesland: "by" (Bayern) — Ort → Region
   - "8 Mitarbeiter" → unternehmensgroesse: "team" — Zahl → Kategorie
   - "komplett digital" → digitalisierungsgrad: 9 (NICHT 10 — 10 = kein \
   einziger analoger Prozess denkbar; "komplett/voll digital" → maximal 9)
   - "viel Papier" → digitalisierungsgrad: 2 oder 3 — Beschreibung → Skala
   - "ich arbeite mit LLM-APIs" → ki_kompetenz: "hoch" — Aussage → Einstufung
   VERBOTENE Inferenz (Inhalte ableiten, die der User NICHT gesagt hat):
   - "Beratung von Unternehmen" → NICHT zielgruppen: ["b2b"] ableiten. \
     Das ist NUR relevant für "hauptleistung". Daraus NICHT ableiten: \
     zielgruppen, ki_einsatz, oder andere Felder.
   - "KI-Beratung" → NICHT ki_ziele oder ki_einsatz daraus ableiten
   - "Automatisierung" als Hauptleistung → NICHT ki_ziele: ["automatisierung"] setzen
   - User nennt Anwendungsfälle → NICHT in ki_einsatz kopieren
   - User nennt Ziele → NUR seine Worte verwenden, KEINE Buzzword-Synonyme
   Regel: Wenn der User ein Feld nicht DIREKT anspricht, setze es NICHT.
9. FELD-ISOLATION (Cross-Contamination verhindern):
   - ki_einsatz = wo KI HEUTE SCHON produktiv im Einsatz ist. \
     NUR setzen wenn der User sagt "wir nutzen KI für X" / "KI läuft bei uns in Y".
   - anwendungsfaelle = was den User INTERESSIERT oder was er PLANT. \
     Wenn User Anwendungsfälle als Interesse nennt, NICHT in ki_einsatz kopieren.
   - ki_ziele = was der User als ZIEL oder WUNSCH formuliert. \
     NUR die Worte des Users verwenden, KEINE Buzzwords substituieren. \
     NICHT aus hauptleistung oder anwendungsfaelle ableiten.
   - zielgruppen = NUR setzen wenn der User explizit "meine Zielgruppe ist X" sagt. \
     NICHT aus Branche, Hauptleistung oder Kontext ableiten.
10. Wenn der Nutzer signalisiert, nicht antworten zu wollen \
(z.B. "weiß nicht", "weiß nicht genau", "keine Ahnung", "überspring", \
"egal", "später", "kann ich nicht", "kann ich nicht sagen", \
"schwer zu sagen", "nächste Frage", "keine Vorstellung", "passe", \
"überspring das", "kein Plan", "keine Idee"), setze \
__skip_signal auf true.

FELDER ZUM EXTRAHIEREN:
{fields_descriptions}

Bereits erfasst (NICHT nochmal setzen): {collected_fields}"""


def _build_multi_field_tool(target_fields: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a dynamic tool schema for multi-field extraction.

    Args:
        target_fields: List of dicts with keys: name, type, description,
                       and optionally options (for enum/multi).
    """
    properties: dict[str, Any] = {}

    for field in target_fields:
        fname = field["name"]
        ftype = field.get("type", "text")
        fdesc = field.get("description", fname)
        foptions = field.get("options")

        if ftype == "enum" and foptions:
            properties[fname] = {
                "type": "string",
                "enum": foptions,
                "description": fdesc,
            }
        elif ftype == "multi" and foptions:
            properties[fname] = {
                "type": "array",
                "items": {"type": "string", "enum": foptions},
                "description": fdesc,
            }
        elif ftype == "slider":
            properties[fname] = {
                "type": "integer",
                "description": fdesc,
            }
        else:
            # text or fallback
            properties[fname] = {
                "type": "string",
                "description": fdesc,
            }

    # Add skip signal
    properties["__skip_signal"] = {
        "type": "boolean",
        "description": (
            "true wenn der User signalisiert, nicht antworten zu wollen "
            "(weiß nicht, überspring, egal, etc.)"
        ),
    }

    return {
        "name": "extract_multi_fields",
        "description": (
            "Extrahiert mehrere strukturierte Felder gleichzeitig aus der "
            "User-Nachricht. Nur Felder setzen, die erkennbar sind."
        ),
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": [],
        },
    }


def _format_fields_for_prompt(target_fields: list[dict[str, Any]]) -> str:
    """Format target fields as a readable list for the system prompt."""
    lines = []
    for f in target_fields:
        fname = f["name"]
        ftype = f.get("type", "text")
        fdesc = f.get("description", fname)
        opts = f.get("options")
        if opts:
            opts_str = ", ".join(opts[:15])
            lines.append(f"- {fname} ({ftype}): {fdesc} | Optionen: [{opts_str}]")
        else:
            lines.append(f"- {fname} ({ftype}): {fdesc}")
    return "\n".join(lines)


async def extract_fields_multi(
    user_message: str,
    conversation_context: list[dict],
    target_fields: list[dict[str, Any]],
    collected_fields: dict,
) -> dict:
    """
    Multi-field extraction for Phase 1 free conversation mode.

    Instead of extracting one field at a time, this extracts ALL recognizable
    values from a single user message across multiple target fields.

    Args:
        user_message: The current user message
        conversation_context: Last 6 messages for context
        target_fields: List of field descriptors, each with:
            name, type, description, and optionally options
        collected_fields: Already collected field values

    Returns:
        Dict with extracted fields. Keys are field names, values are
        extracted values. Special key "__skip_signal" is True if the
        user signaled unwillingness to answer.
    """
    client = _get_async_client()
    if client is None:
        log.error("[CHAT-EXTRACT-MULTI] No async client available")
        return {}

    # Build messages
    messages: list[dict] = []
    for turn in conversation_context[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    # Build system prompt
    fields_desc = _format_fields_for_prompt(target_fields)
    system = MULTI_FIELD_SYSTEM_PROMPT.format(
        fields_descriptions=fields_desc,
        collected_fields=_format_collected(collected_fields),
    )

    # Build dynamic tool
    tool = _build_multi_field_tool(target_fields)

    try:
        response = await client.messages.create(
            model=EXTRACTOR_MODEL,
            max_tokens=800,
            system=system,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "auto"},
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "extract_multi_fields":
                extracted: dict = dict(block.input)
                skip = extracted.pop("__skip_signal", False)
                # Remove None values
                extracted = {k: v for k, v in extracted.items() if v is not None}
                extracted = _validate_extracted(extracted)
                log.info(
                    "[CHAT-EXTRACT-MULTI] Extracted %d fields: %s (skip=%s)",
                    len(extracted),
                    list(extracted.keys()),
                    skip,
                )
                if skip:
                    extracted["__skip_signal"] = True
                return extracted

        log.info("[CHAT-EXTRACT-MULTI] No fields extracted (question or off-topic)")
        return {}

    except Exception as exc:
        log.error("[CHAT-EXTRACT-MULTI] Multi-extraction failed: %s", exc, exc_info=True)
        return {}
