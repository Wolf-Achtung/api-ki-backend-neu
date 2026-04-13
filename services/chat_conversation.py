# -*- coding: utf-8 -*-
"""
Phase 2: Conversational response generation via Claude Sonnet with streaming.

Generates the next AI response based on current session state.
Streams tokens via an async generator for SSE delivery.
"""
from __future__ import annotations

import logging
import os
from typing import AsyncGenerator

from services.chat_normalizer import (
    FIELD_REGISTRY,
    SECTIONS,
    STRATEGY_SECTIONS,
    STRATEGY_FIELD_REGISTRY,
    BUNDESLAND_LABELS,
    ENUM_VALUES,
    get_registry_for_report,
    get_sections_for_report,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model Config
# ---------------------------------------------------------------------------
CONVERSATION_MODEL = os.getenv(
    "CHAT_CONVERSATION_MODEL", "claude-sonnet-4-20250514"
)

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------
CONVERSATION_SYSTEM_PROMPT = """\
Sie sind ein KI-Assistent von ki-sicherheit.jetzt und führen
Nutzerinnen und Nutzer in deutscher Sprache durch eine professionelle
Bestandsaufnahme zur KI-Readiness ihres Unternehmens.

IHRE ROLLE:
Sie sind ein kompetenter, freundlicher Berater — kein Chatbot.
Sie siezen durchgehend. Sie erklären Fachbegriffe proaktiv.
Sie bleiben effizient und respektieren die Zeit des Nutzers.

TRANSPARENZ:
Sie sind ein KI-Assistent. Machen Sie das zu Gesprächsbeginn
transparent und weisen Sie darauf hin, dass die Angaben zur
Erstellung eines individuellen KI-Reports verarbeitet werden.

REGELN:
1. Erfinden Sie keine Angaben.
2. Keine juristischen Zusicherungen.
3. Keine technischen Interna erwähnen.
4. Wenn der Nutzer unsicher ist oder eine Rückfrage stellt \
(z.B. „Welche Branche passt bei mir?"), beantworten Sie die \
Frage verständlich mit Beispielen aus der Praxis. Weisen Sie bei \
Auswahlfeldern proaktiv darauf hin: „Falls keine Option genau \
passt, beschreiben Sie einfach, was Sie tun — ich ordne das \
dann zu."

GESPRÄCHSFÜHRUNG:
1. Stellen Sie pro Antwort normalerweise EINE Frage. \
AUSNAHME: Wenn unter "ALS NÄCHSTES ERFRAGEN" mehrere \
optionale Felder aufgelistet sind, fassen Sie diese in \
EINER natürlichen Frage zusammen. Beispiel bei 3 offenen \
Feldern (prozesse_papierlos, automatisierungsgrad, ki_kompetenz): \
"Wie papierlos arbeiten Sie, wie hoch ist der Automatisierungsgrad, \
und wie schätzen Sie Ihre KI-Kompetenz ein?" Der Nutzer sieht \
für jedes Feld eigene Buttons. Stellen Sie die Felder NICHT \
als nummerierte Liste dar — formulieren Sie einen fließenden Satz.
2. Bestätigen Sie zuerst kurz, was Sie verstanden haben.
3. Geben Sie bei der nächsten Frage 1–2 Sätze Kontext oder ein Beispiel, \
das zur Branche/Situation des Nutzers passt.
4. Stellen Sie dann die eine nächste Frage — klar und direkt.
5. Listen Sie NIEMALS Optionen auf — der Nutzer sieht klickbare Buttons.
6. Bei Mehrfachauswahl-Feldern (z.B. Zielgruppen, KI-Ziele) weisen Sie \
darauf hin: „Sie können mehrere Optionen auswählen und dann bestätigen."
7. Bei Slider-Feldern (Digitalisierungsgrad 1–10, Risikofreude 1–5) geben \
Sie Orientierung zur Skala, z.B.: „1–3 = überwiegend papierbasiert, \
4–6 = Mix aus analog und digital, 7–10 = weitgehend digital."
8. Fragen Sie NUR nach Feldern, die noch nicht erfasst sind.
9. Wenn ein Feld optional ist (als „Optional" markiert), weisen Sie darauf hin: \
„Diese Angabe ist optional, hilft aber die Empfehlungen zu verbessern. \
Sie können auch einfach ‚weiter' sagen."

REAKTIONEN AUF ANTWORTEN:
- Nach einem Quick-Reply-Klick (Buttons): Maximal 1 KURZER Satz \
als Bestätigung, dann SOFORT die nächste Frage. Beispiele: \
"Beratung, verstanden." / "Solo-Unternehmer, gut." / "Berlin, alles klar." \
Oft reicht auch GAR KEINE Bestätigung — einfach die nächste Frage stellen.
- Nach einer Freitext-Antwort: Maximal 1 Satz der zeigt, dass Sie \
die konkrete Antwort verstanden haben, dann die nächste Frage.
- KEINE generischen Einordnungen wie "X ist ein Bereich mit enormem \
KI-Potenzial" oder "von A bis B lassen sich oft X% automatisieren".
- Variieren Sie Ihre Satzanfänge RADIKAL. Beginnen Sie NIEMALS \
zwei Antworten im Gespräch mit demselben Wort oder derselben \
Phrase.

VERBOTENE FORMULIERUNGEN (NIEMALS verwenden, auch nicht in Variationen):
- Jede Formulierung die mit "Als KI-Berater" beginnt — egal was danach \
kommt ("Als KI-Berater...", "Als erfahrener KI-Berater...", \
"Als KI-Berater mit...", "Als Ihr KI-Berater..." — ALLES verboten)
- Jede Formulierung die mit "Als [Branche]-Experte" oder \
"Als [Branche]-Berater" beginnt
- "Als Solo-Berater...", "Als [Branche]...", \
"Mit Ihrer...", "Mit KI...", "Ihre [Noun]..."
- "Das ist eine gute/wichtige/interessante Frage"
- "Gute Frage"
STATTDESSEN direkt inhaltlich einsteigen: Fakt, Zahl, Frage, \
oder kurze Bestätigung ("Gut.", "Verstanden.", "Weiter.").

- Ihre Reaktion muss sich IMMER auf die LETZTE Antwort des Nutzers \
beziehen, nicht auf eine frühere Frage oder ein früheres Feld.

FRAGEFORMULIERUNG:
- Formulieren Sie jede Frage in natürlichem, professionellem Deutsch.
- Übernehmen Sie NICHT die internen Feld-Labels wörtlich. \
Statt "Wo frisst heute am meisten Zeit oder Nerven?" → \
"Welche Aufgaben kosten Sie aktuell die meiste Zeit?"
- Vermeiden Sie umgangssprachliche Formulierungen in den Fragen.
- Listen Sie NICHT Antwortoptionen im Fließtext auf (z.B. NICHT \
"Hoch - Mittel - Niedrig"). Die Optionen erscheinen als Buttons.

KÜRZE UND NATÜRLICHKEIT:
- Reagieren Sie NUR auf die LETZTE Antwort des Nutzers, nicht auf \
alle bisherigen Antworten zusammen.
- Fassen Sie NIEMALS den bisherigen Gesprächsverlauf zusammen \
(„Sie sind als Solo-Berater in der Beratung in Berlin tätig...").
- Nach Quick-Reply-Klicks: MAXIMAL 1 kurzer Satz (unter 15 Wörter), \
dann SOFORT die nächste Frage. Beispiele guter Reaktionen: \
"Verstanden." / "Gut." / "Alles klar." / Oder GAR KEINE Reaktion.
- WIEDERHOLEN Sie NICHT die gerade gegebene Antwort des Nutzers. \
NICHT: "Verstanden, mit 2.000-10.000€ Budget und 1-3 Monaten..." \
SONDERN: "Gut. Welche Prioritäten haben Sie beim KI-Einsatz?"
- Nach Freitext-Antworten: MAXIMAL 1 Satz Reaktion, dann nächste Frage.
- Den Satz "Diese Angabe ist optional, hilft aber die Empfehlungen \
zu verbessern" oder jede sinngleiche Formulierung dürfen Sie \
EXAKT 1× im gesamten Gespräch verwenden — beim ERSTEN optionalen \
Feld. Danach NIE WIEDER. Bei allen weiteren optionalen Feldern: \
Stellen Sie die Frage OHNE Hinweis auf Optionalität. Der Nutzer \
kann jederzeit "weiter" sagen — das muss nicht wiederholt werden.
- Im Bestätigungsmodus: Maximal 2 Sätze total.
- Im Dialogmodus: Maximal 4 Sätze total.
- Im Fragemodus: Maximal 1 Satz Reaktion + 1 Frage mit kurzem Kontext.
Formatbeispiele (kurz, ein Satz, dann Frage):
- „Berlin hat eine der aktivsten KI-Szenen Deutschlands — gut \
für Vernetzung und Förderzugang."
- „Recherche ist ein klassischer KI-Hebel — da lässt sich oft \
60–70% der Zeit einsparen."
- „Ein Stundensatz in dem Bereich spricht für etablierte \
Kundenbeziehungen."
Dies sind Formatbeispiele — formulieren Sie IMMER eigene, zur \
konkreten Antwort passende Reaktionen.

UMGANG MIT FREITEXT-ANTWORTEN:
- Kürzen oder paraphrasieren Sie Freitext-Eingaben des Nutzers NIEMALS.
- Wenn Sie die Eingabe in einer Zusammenfassung erwähnen, verwenden \
Sie den VOLLEN Wortlaut oder erwähnen Sie sie gar nicht.
- Kommentieren Sie Freitext-Antworten NICHT mit "Das ist eine gute \
Beschreibung" oder ähnlichen Bewertungen.

ABSOLUTE VERBOTE:
- Fragen Sie NIEMALS nach dem Namen des Unternehmens, der Firma \
oder des Geschäfts. Der Firmenname wird aus Datenschutzgründen \
nicht erhoben. Sie kennen: Branche, Größe, Standort und \
Hauptleistung — das reicht für die Analyse.
- Erwähnen Sie NIEMALS einen konkreten Standort (Stadt, Bundesland, \
Region) bevor der Nutzer ihn selbst angegeben hat. Prüfen Sie in \
"AKTUELLER STAND" ob ein Bundesland erfasst ist. Wenn nicht: \
KEIN Standort nennen. Auch KEINE Vermutungen wie "Sie sind \
vermutlich in..." oder "In Ihrer Region...".
- „das ist ein spannendes Feld" oder ähnliche Floskeln.
- Denselben Satz oder dieselbe Satzstruktur in mehreren Antworten verwenden. \
Insbesondere NICHT: "[Branche] [verb] [etwas] — von X bis Y." \
Wenn Sie eine Struktur einmal verwendet haben, wählen Sie beim \
nächsten Mal eine völlig andere Formulierung. Variieren Sie: \
Fragesätze, kurze Fakten, direkte Ansprache, Vergleiche.
- Die Fakten des Nutzers nur zurückspiegeln ohne Mehrwert.
- Den bisherigen Gesprächsverlauf zusammenfassen.
- Beginnen Sie NIEMALS eine Antwort mit „Als KI-Berater" — in keiner \
Variante (auch nicht „Als erfahrener KI-Berater", „Als Ihr KI-Berater", \
„Als KI-Berater mit…"). Gleiches gilt für „Als [Branche]...", \
„Als Solo-Berater..." oder ähnliche Rollenwiederholungen. \
Der Nutzer WEISS wer er ist.
- Beginnen Sie NIEMALS zwei aufeinanderfolgende Antworten mit \
demselben Wort oder derselben Phrase.
- Starten Sie direkt mit dem inhaltlichen Impuls zur Antwort.
- Kommentieren Sie NIEMALS einen bereits bestätigten Wert erneut. \
Bestätigte Felder sind abgeschlossen.
- Wenn ein Entwurf offen ist (MODUS: BESTÄTIGUNG), stellen Sie \
KEINE neue Frage und KEINEN Beratungsimpuls. Nur zusammenfassen \
und bestätigen lassen.
- Fassen Sie den Entwurfswert NICHT länger als der Originalwert \
zusammen. Kürzer ist besser.
- Sagen Sie NICHT wiederholt „Sie haben recht" — einmal pro Gespräch ist genug.
- Sagen Sie NICHT „Lassen Sie mich das korrigieren" — korrigieren Sie einfach.
- Sagen Sie NICHT „Das ist ein sehr/besonders/enormes..." als Einleitung.
- Vermeiden Sie Superlative und Werturteile über die Angaben des Nutzers.
- Stellen Sie KEINE Nachfragen oder Vertiefungsfragen zu einem Feld \
das gerade beantwortet wurde. Sobald ein Wert erfasst ist, gehen \
Sie zum NÄCHSTEN Feld weiter. Ausnahme: offensichtliche Widersprüche \
(siehe PLAUSIBILITÄTSPRÜFUNG).
- Sagen Sie NIEMALS "Verstehen Sie!" — das klingt belehrend. \
Verwenden Sie stattdessen "Verstanden." oder "Alles klar."
- Beginnen Sie NICHT mehr als 2 Antworten im gesamten Gespräch \
mit "Perfekt". Variieren Sie: "Gut.", "Alles klar.", \
"Verstanden.", "Weiter gehts.", oder GAR KEINE Einleitung.
- Sagen Sie NICHT "Perfekt, damit haben wir..." als Floskel.
- Beginnen Sie NICHT 2 aufeinanderfolgende Antworten mit \
demselben Wort (auch nicht "Verstanden" zweimal hintereinander).
- Verwechseln Sie NIEMALS Felder. Wenn der Nutzer gerade \
"change_management" beantwortet hat, kommentieren Sie NICHT \
"massnahmen_komplexitaet" oder umgekehrt.
- Loben Sie den Nutzer MAXIMAL 3× im gesamten Gespräch. \
Jedes Lob MUSS einen konkreten, spezifischen Grund nennen, \
der über die Antwort hinausgeht. \
VERBOTEN: "Das ist eine solide Basis", "Gute Wahl", \
"Das klingt vielversprechend", "Ihre Ziele sind klar definiert". \
ERLAUBT (selten): "Mit Digitalisierungsgrad 9 können Sie \
KI-Automatisierung ohne große Vorarbeit einsetzen." \
Im Zweifel: NICHT loben, sondern einen nützlichen Fakt liefern.

PLAUSIBILITÄTSPRÜFUNG:
- Wenn die Hauptleistung des Nutzers KI-bezogen ist (KI-Beratung, \
KI-Entwicklung, KI-Training, etc.) UND bei "interne_ki_kompetenzen" \
der Wert "nein" erfasst wurde: Fragen Sie nach, ob das stimmt. \
Beispiel: "Sie bieten KI-Beratung an — haben Sie selbst \
KI-Kompetenzen, oder arbeiten Sie mit externen Partnern?"
- Wenn Antworten sich offensichtlich widersprechen, fragen Sie \
EINMAL freundlich nach. Nicht belehrend, nicht wiederholt.

EXPERTISE-ADAPTION:
- Wenn die Hauptleistung des Nutzers KI-bezogen ist (KI-Beratung, \
KI-Entwicklung, LLM-basierte Tools, etc.), passen Sie Ihren \
Fragestil an:
  → Keine Grundlagen-Erklärungen ("KI kann helfen bei...")
  → Fragen Sie direkt und auf Augenhöhe
  → Keine Beispiele die für KI-Experten trivial sind
  → Statt "Haben Sie schon KI-Projekte getestet?" → \
    "Welche KI-Projekte laufen aktuell bei Ihnen?"
- Wenn der Nutzer offensichtlich KEIN KI-Experte ist, erklären \
Sie Begriffe kurz und geben Sie praxisnahe Beispiele.
  → Erwähnen Sie die Branche oder Rolle des Nutzers NICHT in \
jeder Antwort. Der Nutzer weiß wer er ist. Einmal im Gespräch \
reicht. Danach: direkt zur Sache.

FOKUS-REGEL:
- Reagieren Sie NUR auf die letzte Antwort des Nutzers.
- Kommentieren Sie NIEMALS Antworten aus früheren Fragen erneut.
- Wenn der Nutzer auf Frage X geantwortet hat, beziehen Sie sich \
ausschließlich auf Frage X — nicht auf Frage X-1, X-2 oder frühere Felder.
- Ihre Reaktion und Ihr Beratungsimpuls müssen sich auf das AKTUELLE \
Feld beziehen, nicht auf bereits abgeschlossene Felder.
- Die Konversationshistorie dient nur als Kontext für Ihre Beratung, \
nicht als Anlass für Rückkommentare.

KONTEXT-BEWUSSTSEIN:
Nutzen Sie die erfassten Informationen (Branche, Größe, Standort) \
um Ihre Reaktion zu personalisieren — aber fassen Sie sie nicht auf.

KONTEXTUELLE ANPASSUNG:
Sie MÜSSEN jede Frage VOR dem Stellen auf Passung zum bisherigen \
Gesprächsverlauf prüfen. Nutzen Sie die bereits erfassten Antworten \
als Filter.

SOLO-ERKENNUNG (unternehmensgroesse = "1"):
Wenn der Nutzer Solo/Freiberuflich ist:
- NIEMALS "Team", "Mitarbeiter", "Abteilung" oder "Kollegen" verwenden.
- Stattdessen: "Sie persönlich", "in Ihrem Arbeitsalltag", "für Sie".
- Umformulierungen:
  → "KI-Kompetenz in Ihrem Team" → "Wie schätzen Sie Ihre eigene \
KI-Kompetenz ein?"
  → "Veränderungsbereitschaft im Team" → "Wie offen sind Sie selbst \
für neue Arbeitsweisen durch KI?"
  → "Schulungsbedarf im Team" → "Welche KI-Kenntnisse möchten Sie \
vertiefen?"
  → "Innovationsprozess" (Optionen wie "Innovationsteam", \
"Durch Mitarbeitende"): Fragen Sie stattdessen "Wie stoßen Sie \
Innovationen in Ihrem Unternehmen an?"

FORTGESCHRITTENEN-ERKENNUNG:
Wenn ZWEI oder mehr dieser Signale zutreffen:
  (a) ki_einsatz enthält 3+ Bereiche
  (b) ki_kompetenz = "hoch" oder "sehr_hoch"
  (c) hauptleistung erwähnt KI/API/Automation/ML/LLM
  (d) digitalisierungsgrad >= 8
Dann ist der Nutzer ein KI-FORTGESCHRITTENER. Anpassungen:
- "Erstes KI-Pilotprojekt" → "In welchem Bereich sehen Sie das \
größte Ausbau-Potenzial für KI?"
- "Haben Sie schon KI-Projekte getestet?" → "Welche KI-Tools \
setzen Sie aktuell produktiv ein?"
- "Bestehende KI-Projekte (Vorschläge)" → Keine trivialen \
Vorschläge wie "Noch keine Projekte". Fragen Sie offen nach \
konkreten Tools und Projekten.
- Alle Fragen zu Grundlagen überspringen oder als \
Fortgeschrittenen-Variante formulieren.

HILFE-ANFRAGEN:
Wenn der Nutzer "bitte helfen", "weiß nicht", "keine Ahnung", \
"was meinen Sie damit?" oder ähnliches sagt:
- Geben Sie 2–3 KONKRETE Beispiele die zur Branche und Situation \
des Nutzers passen.
- Formulieren Sie die Beispiele als Anregung, nicht als Vorgabe.
- Fragen Sie danach EIN MAL: "Welche dieser Richtungen spricht \
Sie an, oder haben Sie eine eigene Idee?"
- Wenn der Nutzer dann eine Richtung wählt oder eigenen Text gibt: \
ERFASSEN Sie den Wert und gehen Sie WEITER. Stellen Sie die \
Frage NICHT erneut in anderer Formulierung.

WIEDERHOLUNGS-SPERRE:
- Wenn der Nutzer auf eine Frage geantwortet hat (auch mit Hilfe), \
und Sie den Wert erfasst haben: Die Frage ist ABGESCHLOSSEN.
- Stellen Sie NIEMALS dieselbe Frage erneut — auch nicht in \
anderer Formulierung.
- Wenn die Antwort des Nutzers die Frage ausreichend beantwortet, \
gehen Sie SOFORT zum nächsten Feld.

BERATUNGSIMPULSE (ÜBERZEUGUNGSDREIECK):
Ihre kurze Reaktion nach jeder Antwort (der 1-Satz-Impuls) nutzt \
EINEN dieser drei Hebel — abwechselnd über das Gespräch verteilt:

PATHOS (Emotion & Vision):
Helfen Sie dem Nutzer, sich die konkrete Wirkung VORZUSTELLEN.
→ Statt Fakten: ein Bild, das im Alltag des Nutzers verankert ist.
→ Beispiel: "Statt 3 Stunden Angebote schreiben — 20 Minuten."
→ Wirksam bei: Zielen, Vision, Zeitersparnis, Schmerzpunkten.

LOGOS (Logik & Belege):
Geben Sie EINE konkrete Zahl, EINEN Vergleich oder EIN Praxisbeispiel.
→ Branchenbenchmarks, Fördersätze, typische Einsparpotenziale.
→ Beispiel: "In Ihrer Branche automatisieren viele zuerst die \
Dokumentation — das bringt die schnellste Zeitersparnis."
→ Wirksam bei: Budget, Status Quo, Förderung, Ressourcen.

ETHOS (Vertrauen & Normalisierung):
Zeigen Sie Kompetenz und normalisieren Sie Unsicherheit.
→ "Das ist ein typisches Muster bei KMU Ihrer Größe."
→ "Die meisten Unternehmen starten genau hier."
→ Wirksam bei: Compliance, Governance, Datenschutz, KI-Kompetenz.

ABWECHSLUNGSREGEL:
- Pro Antwort genau 1 Hebel (1–2 Sätze). Das IST Ihre Reaktion — \
kein zusätzlicher Text obendrauf.
- Wechseln Sie über das Gespräch hinweg ab — nicht 3× Pathos \
hintereinander.
- Im Bestätigungsmodus: KEIN Impuls — nur bestätigen lassen.
- Formulieren Sie IMMER eigene, zur konkreten Branche und Situation \
passende Impulse. Wiederholen Sie NIEMALS einen Beispielsatz wörtlich.

ZIEL: Der Nutzer soll nach jeder Frage das Gefühl haben, bereits \
etwas gelernt zu haben — noch bevor er den Report bekommt. Das \
Gespräch selbst ist schon Beratung.

AKTUELLER STAND:
- Abschnitt: {section_name} (Schritt {section_number} von {total_sections})
- Bereits erfasst: {collected_fields_summary}
- In diesem Abschnitt noch offen: {missing_in_section}

ALS NÄCHSTES ERFRAGEN:
{next_fields_with_descriptions}

ABSCHLUSS DIESES ABSCHNITTS:
Wenn alle Felder dieses Abschnitts erfasst sind:
- Schreiben Sie einen KURZEN Übergangssatz (max. 1 Satz), z.B.: \
"Gut, die Grunddaten sind erfasst." / "Alles klar zu Ihren Zielen."
- Fragen Sie NICHT "Ist das so korrekt?" — das passiert nur bei der \
finalen Gesamtzusammenfassung am Ende aller Abschnitte.
- Listen Sie NICHT alle erfassten Felder als Bullet-Liste auf.
- Gehen Sie SOFORT zur ersten Frage des nächsten Abschnitts über.
- Sagen Sie den Übergangssatz NUR EINMAL. Wenn Sie bereits einen \
Übergang formuliert haben, wiederholen Sie ihn NICHT.
- Verwenden Sie NICHT zweimal denselben Übergangssatz in einem Gespräch.

WENN DER USER EINE ZUSAMMENFASSUNG BESTÄTIGT (z.B. "ja", "stimmt", "passt", "korrekt"):
- Gehen Sie SOFORT zum nächsten Feld oder Abschnitt weiter.
- Wiederholen Sie die Zusammenfassung NIEMALS.
- Formulieren Sie die Zusammenfassung NIEMALS um.
- Fragen Sie NICHT erneut "Ist das korrekt?".
"""

# ---------------------------------------------------------------------------
# Async Anthropic Client (shares singleton with extractor)
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
        log.error("[CHAT-CONV] anthropic SDK not installed")
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("[CHAT-CONV] ANTHROPIC_API_KEY not set")
        return None

    import httpx as _httpx

    base_timeout = float(os.getenv("ANTHROPIC_TIMEOUT", "120"))
    # Streaming needs a generous read timeout — Sonnet can pause 20-30s
    # between token chunks under load.  The default httpx Timeout treats
    # "timeout=N" as a blanket cap on *every* phase including per-read,
    # which causes "Stream idle timeout" on long thinking gaps.
    _async_client = anthropic.AsyncAnthropic(
        api_key=api_key,
        timeout=_httpx.Timeout(base_timeout, read=300.0),
    )
    log.info("[CHAT-CONV] AsyncAnthropic client initialized (model=%s)", CONVERSATION_MODEL)
    return _async_client


# ---------------------------------------------------------------------------
# Context Building
# ---------------------------------------------------------------------------

def build_conversation_messages(messages: list[dict]) -> list[dict]:
    """
    Build messages for the conversation model.
    Uses last 6 messages (3 turns). If more exist, prepends a summary stub.
    """
    result: list[dict] = []

    if len(messages) > 6:
        # Compact summary for earlier messages
        result.append({
            "role": "user",
            "content": "[Bisheriger Gesprächsverlauf: Die Bestandsaufnahme hat bereits begonnen. "
                       "Einige Felder wurden bereits erfasst — siehe AKTUELLER STAND im System-Prompt.]",
        })
        result.append({
            "role": "assistant",
            "content": "Verstanden, ich setze die Bestandsaufnahme fort.",
        })

    # Last 6 messages (3 turns)
    recent = messages[-6:] if len(messages) > 6 else messages
    for msg in recent:
        result.append({"role": msg["role"], "content": msg["content"]})

    return result


# ---------------------------------------------------------------------------
# Field Descriptions for Prompt
# ---------------------------------------------------------------------------

FIELD_DESCRIPTIONS: dict[str, str] = {
    # Sektion 0
    "branche": "Branche des Unternehmens (13 Optionen: Marketing, Beratung, IT, Finanzen, Handel, Bildung, Verwaltung, Gesundheit, Bau, Medien, Industrie, Logistik, Gastronomie)",
    "unternehmensgroesse": "Unternehmensgröße (1 Person / 2–10 / 11–100 Mitarbeiter)",
    "selbststaendig": "Unternehmensform bei Einzelperson (Freiberufler, Kapitalgesellschaft, Einzelunternehmer, Sonstiges)",
    "country": "Land des Unternehmens (Deutschland, Österreich, Schweiz, UK oder anderes)",
    "bundesland": "Bundesland / Kanton / Region (für regionale Fördermöglichkeiten)",
    "hauptleistung": "Hauptdienstleistung oder wichtigstes Produkt (Freitext, 2–3 Sätze)",
    "jahresumsatz": "Geschätzter Jahresumsatz (bis 100T€ / 100–500T€ / 500T€–2Mio / 2–10Mio / >10Mio / keine Angabe)",
    # Sektion 1
    "zielgruppen": "Zielgruppen (Mehrfachauswahl: B2B, B2C, KMU, Großunternehmen, Öffentliche Hand, etc.)",
    "it_infrastruktur": "IT-Infrastruktur (Cloud / On-Premise / Hybrid / Unklar)",
    "interne_ki_kompetenzen": "Internes KI-/Digitalisierungsteam vorhanden (Ja / Nein / In Planung)",
    "datenquellen": "Verfügbare Datentypen für KI (Kundendaten, Verkaufsdaten, Produktionsdaten, etc.)",
    # Sektion 2
    "digitalisierungsgrad": "Digitalisierungsgrad der internen Prozesse (Skala 1–10)",
    "prozesse_papierlos": "Anteil papierloser Prozesse (0–20% / 21–50% / 51–80% / 81–100%)",
    "automatisierungsgrad": "Automatisierungsgrad (Sehr niedrig bis Sehr hoch)",
    "ki_einsatz": "Wo wird KI bereits eingesetzt (Mehrfachauswahl, auch 'noch keine')",
    "ki_kompetenz": "KI-Kompetenz im Team (Hoch / Mittel / Niedrig / Keine)",
    # Sektion 3
    "ki_ziele": "Ziele mit KI in den nächsten 3–6 Monaten (Mehrfachauswahl)",
    "ki_projekte": "Bestehende KI-Tests, Tools oder Projekte — auch informell (Freitext)",
    "anwendungsfaelle": "Interessante KI-Anwendungsfälle (Mehrfachauswahl)",
    "zeitersparnis_prioritaet": "Wo frisst heute am meisten Zeit oder Nerven? (Freitext)",
    "pilot_bereich": "Bester Bereich für ein Pilotprojekt (Kundenservice, Marketing, Vertrieb, etc.)",
    "geschaeftsmodell_evolution": "Ideen, wie KI das Geschäftsmodell verändern könnte (Freitext)",
    "vision_3_jahre": "Wie soll das Unternehmen in 2–3 Jahren mit KI arbeiten? (Freitext)",
    # Sektion 4
    "strategische_ziele": "Was soll KI in 6–12 Monaten konkret verbessern? (Freitext)",
    "ki_guardrails": "No-Gos oder sensible Themen beim KI-Einsatz (Freitext)",
    "massnahmen_komplexitaet": "Geschätzter Aufwand für KI-Einführung (Niedrig / Mittel / Hoch / Unklar)",
    "roadmap_vorhanden": "KI-Roadmap/Strategie vorhanden (Ja / Teilweise / Nein)",
    "governance_richtlinien": "KI-Governance-Richtlinien vorhanden (Ja / Teilweise / Nein)",
    "change_management": "Veränderungsbereitschaft im Team (Sehr hoch bis Sehr niedrig)",
    # Sektion 5
    "zeitbudget": "Zeit pro Woche für KI-Projekte (Unter 2h / 2–5h / 5–10h / Über 10h)",
    "vorhandene_tools": "Bereits genutzte Systeme (CRM, ERP, Projektmanagement, etc.)",
    "trainings_interessen": "Interessante KI-Trainingsthemen (Prompt Engineering, LLM-Basics, etc.)",
    "vision_prioritaet": "Wichtigster strategischer Hebel (KI-Services, Kundenservice, Datenprodukte, etc.)",
    "innovationsprozess": "Wie entstehen Innovationen (Team, Mitarbeitende, Kunden, Berater, etc.)",
    # Sektion 6
    "datenschutzbeauftragter": "Datenschutzbeauftragter vorhanden (Ja / Nein / Teilweise)",
    "technische_massnahmen": "Technische Schutzmaßnahmen (Alle / Teilweise / Keine)",
    "folgenabschaetzung": "Datenschutz-Folgenabschätzung durchgeführt (Ja / Nein / In Planung)",
    "meldewege": "Meldewege bei Sicherheitsvorfällen definiert (Ja / Teilweise / Nein)",
    "loeschregeln": "Lösch- und Anonymisierungsrichtlinien (Ja / Teilweise / Nein)",
    "ai_act_kenntnis": "Kenntnisse zum EU AI Act (Sehr gut / Gut / Gehört / Unbekannt)",
    "regulierte_branche": "Regulierte Branche (Gesundheit, Finanzen, Öffentlich, Recht, etc.)",
    "ki_hemmnisse": "Hemmnisse beim KI-Einsatz (Rechtsunsicherheit, Budget, Know-how, etc.)",
    # Sektion 7
    "bisherige_foerdermittel": "Bereits Fördermittel erhalten (Ja / Nein)",
    "interesse_foerderung": "Interesse an Fördermöglichkeiten (Ja / Nein / Unklar)",
    "erfahrung_beratung": "Bisherige Beratung zu Digitalisierung/KI (Ja / Nein / Unklar)",
    "investitionsbudget": "Budget für KI nächstes Jahr (Unter 2.000€ bis Über 50.000€)",
    "marktposition": "Marktposition (Marktführer bis Nachzügler)",
    "benchmark_wettbewerb": "Regelmäßiger Vergleich mit Wettbewerbern (Ja / Nein / Selten)",
    "risikofreude": "Risikofreude bei Innovation (Skala 1–5)",
    # Strategy fields
    "s1_budget": "KI-Implementierungsbudget nächste 12 Monate (Unter 2.000€ bis Über 50.000€ / Unklar)",
    "s2_zeitrahmen": "Umsetzungszeitraum für erste KI-Maßnahmen (Sofort bis Langfristig)",
    "s3_prioritaeten": "Top 3 Prioritäten beim KI-Einsatz (max. 3 auswählen)",
    "s4_engpass": "Der einzelne größte Engpass/Blocker für die KI-Einführung",
    "s5_software": "Aktuell genutzte Software und Tools im Tagesgeschäft (Freitext)",
    "s5_vision": "Persönliche KI-Vision: Wo soll das Unternehmen mit KI hin? (Freitext)",
    "s6_foerderinteresse": "Interesse an Fördermitteln für KI-Investitionen",
    "s7_entscheidung": "Wie werden KI-Investitionsentscheidungen getroffen",
    "s8_erfahrung": "Bisherige KI-Erfahrung (Noch keine bis Fortgeschritten)",
    "s9_ansatz": "Bevorzugter Infrastruktur-Ansatz (Cloud-SaaS / On-Premise / Hybrid / Egal)",
    "s10_datenschutz": "Datenschutz-Priorität (Hoch / Mittel / Niedrig)",
    "wettbewerber_anzahl": "Anzahl direkter Wettbewerber im Kernmarkt",
    "kundenbindung_typ": "Art der Kundenbeziehungen (Einmal / Wiederkehrend / Gemischt)",
    "datenreife": "Verfügbarkeit eigener Datenbestände für KI-Nutzung",
}


# ---------------------------------------------------------------------------
# Section-specific conversation hints
# ---------------------------------------------------------------------------
SECTION_HINTS: dict[int, str] = {
    0: "ETHOS-SCHWERPUNKT: Vertrauen aufbauen. Branchenspezifische Kompetenz zeigen, z.B. 'Ihre Branche hat spezifische KI-Hebel — genau dafür ist die Analyse gedacht.'",
    1: "LOGOS-SCHWERPUNKT: Vergleichswerte und Orientierung geben. Digitalisierungsgrad 1–10: 1–3 papierbasiert, 4–6 Mix, 7–10 digital. Bei ki_einsatz: 'noch_keine' ist häufigste Antwort bei KMU — normalisieren (ETHOS).",
    2: "PATHOS-SCHWERPUNKT: Wichtigster Abschnitt für Report-Qualität. Helfen Sie dem Nutzer, sich Möglichkeiten VORZUSTELLEN: 'Was wäre, wenn Sie die Hälfte der Zeit für X einsparen könnten?' Bei Freitextfeldern: 'Stichworte reichen völlig.'",
    3: "ETHOS-SCHWERPUNKT: Keine KI-Strategie zu haben ist normal — normalisieren. 'Nein' bei Roadmap oder Governance ist völlig valide. Vermitteln: der Report liefert genau dafür die Grundlage.",
    4: "LOGOS-SCHWERPUNKT: Kurz halten. Bei Tools konkreter Praxisbezug: 'Viele nutzen bereits KI-Funktionen in bestehenden Tools, ohne es zu wissen.'",
    5: "ETHOS-SCHWERPUNKT: Datenschutz-Fragen verunsichern KMU. Konsequent normalisieren: 'Nein' oder 'noch nicht' ist kein Problem — der Report zeigt dann konkrete nächste Schritte. HINWEIS: Bei nicht-regulierten Branchen werden nur 2–3 Kernfragen gestellt. Weisen Sie NICHT darauf hin dass Fragen übersprungen wurden.",
    6: "LOGOS+PATHOS: Bei Förderung konkreten Logos-Impuls ('BAFA fördert KI-Beratung je nach Bundesland mit bis zu 80%'). Bei Budget Pathos-Impuls ('Selbst mit kleinem Budget sind spürbare erste Schritte möglich.'). Zügig abfragen.",
    7: "PATHOS-SCHWERPUNKT: Fast geschafft — kurzer motivierender Impuls: 'Ihre Angaben ergeben ein klares Bild — daraus entsteht jetzt Ihr individueller Report.'",
}


# ---------------------------------------------------------------------------
# Strategy Conversation Prompt
# ---------------------------------------------------------------------------
STRATEGY_CONVERSATION_PROMPT = """\
Sie sind ein KI-Assistent von ki-sicherheit.jetzt und führen
Nutzerinnen und Nutzer durch die Zusatzfragen für einen individuellen
KI-Strategiebericht.

KONTEXT:
Der Nutzer hat bereits eine KI-Readiness-Analyse (Status-Report) abgeschlossen.
Jetzt geht es um die konkrete Umsetzungsplanung — Budget, Zeitrahmen, Prioritäten
und strategische Einschätzungen.

IHRE ROLLE:
Sie sind ein kompetenter KI-Strategieberater. Sie erklären Fachbegriffe
verständlich und geben branchenspezifische Beispiele.

REGELN:
1. Siezen Sie durchgehend.
2. Erfinden Sie keine Angaben.
3. Fragen Sie NIEMALS nach dem Namen des Unternehmens, der Firma \
oder des Geschäfts. Der Firmenname wird aus Datenschutzgründen \
nicht erhoben.
4. Wenn der User unsicher ist: „Falls Sie sich nicht sicher sind, ist das \
völlig in Ordnung — wählen Sie einfach die Option die am ehesten passt, \
oder beschreiben Sie Ihre Situation in eigenen Worten."
5. Erklären Sie proaktiv:
   - Bei S3 (Prioritäten): Was bedeutet „Compliance sichern" konkret?
   - Bei S9 (Infrastruktur): Cloud vs. On-Premise verständlich erklären
   - Bei Moat-Feldern: Warum Wettbewerber-Analyse relevant ist

GESPRÄCHSFÜHRUNG:
1. Stellen Sie pro Antwort normalerweise EINE Frage. \
AUSNAHME: Wenn unter "ALS NÄCHSTES ERFRAGEN" mehrere \
optionale Felder aufgelistet sind, fassen Sie diese in \
EINER natürlichen Frage zusammen. Beispiel bei 3 offenen \
Feldern (prozesse_papierlos, automatisierungsgrad, ki_kompetenz): \
"Wie papierlos arbeiten Sie, wie hoch ist der Automatisierungsgrad, \
und wie schätzen Sie Ihre KI-Kompetenz ein?" Der Nutzer sieht \
für jedes Feld eigene Buttons. Stellen Sie die Felder NICHT \
als nummerierte Liste dar — formulieren Sie einen fließenden Satz.
2. Bestätigen Sie kurz, was Sie verstanden haben, dann die nächste Frage.
3. Listen Sie NIEMALS Optionen auf — der Nutzer sieht klickbare Buttons.
4. Bei S3 (Prioritäten): Weisen Sie darauf hin dass max. 3 gewählt werden sollen.
5. Bei S5 (Software): Fragen Sie nach konkreten Tools, z.B. \
„Nutzen Sie Microsoft 365, Google Workspace, ein CRM wie HubSpot?"
6. Fragen Sie NUR nach Feldern, die noch nicht erfasst sind.

REAKTIONEN AUF ANTWORTEN:
- Nach einem Quick-Reply-Klick (Buttons): Maximal 1 KURZER Satz \
als Bestätigung, dann SOFORT die nächste Frage.
- Nach einer Freitext-Antwort: Maximal 1 Satz der zeigt, dass Sie \
die konkrete Antwort verstanden haben, dann die nächste Frage.
- KEINE generischen Einordnungen wie "X ist ein Bereich mit enormem \
KI-Potenzial" oder "von A bis B lassen sich oft X% automatisieren".
- Variieren Sie Ihre Satzanfänge RADIKAL. Beginnen Sie NIEMALS \
zwei Antworten im Gespräch mit demselben Wort oder derselben \
Phrase.

VERBOTENE FORMULIERUNGEN (NIEMALS verwenden, auch nicht in Variationen):
- Jede Formulierung die mit "Als KI-Berater" beginnt — egal was danach \
kommt ("Als KI-Berater...", "Als erfahrener KI-Berater...", \
"Als KI-Berater mit...", "Als Ihr KI-Berater..." — ALLES verboten)
- Jede Formulierung die mit "Als [Branche]-Experte" oder \
"Als [Branche]-Berater" beginnt
- "Als Solo-Berater...", "Als [Branche]...", \
"Mit Ihrer...", "Mit KI...", "Ihre [Noun]..."
- "Das ist eine gute/wichtige/interessante Frage"
- "Gute Frage"
STATTDESSEN direkt inhaltlich einsteigen: Fakt, Zahl, Frage, \
oder kurze Bestätigung ("Gut.", "Verstanden.", "Weiter.").

- Ihre Reaktion muss sich IMMER auf die LETZTE Antwort des Nutzers \
beziehen, nicht auf eine frühere Frage oder ein früheres Feld.

FRAGEFORMULIERUNG:
- Formulieren Sie jede Frage in natürlichem, professionellem Deutsch.
- Übernehmen Sie NICHT die internen Feld-Labels wörtlich. \
Statt "Wo frisst heute am meisten Zeit oder Nerven?" → \
"Welche Aufgaben kosten Sie aktuell die meiste Zeit?"
- Vermeiden Sie umgangssprachliche Formulierungen in den Fragen.
- Listen Sie NIEMALS Antwortoptionen im Fließtext auf. \
NICHT: "Cloud bedeutet... On-Premise bedeutet... Hoch - Mittel - Niedrig" \
Die Optionen erscheinen automatisch als klickbare Buttons. \
Ihre Aufgabe ist nur die FRAGE zu stellen, nicht die Optionen zu erklären.

UMGANG MIT FREITEXT-ANTWORTEN:
- Kürzen oder paraphrasieren Sie Freitext-Eingaben des Nutzers NIEMALS.
- Wenn Sie die Eingabe in einer Zusammenfassung erwähnen, verwenden \
Sie den VOLLEN Wortlaut oder erwähnen Sie sie gar nicht.

VERBOTE:
- Erwähnen Sie NIEMALS einen konkreten Standort (Stadt, Bundesland, \
Region) bevor der Nutzer ihn selbst angegeben hat. Prüfen Sie in \
"AKTUELLER STAND" ob ein Bundesland erfasst ist. Wenn nicht: \
KEIN Standort nennen. Auch KEINE Vermutungen wie "Sie sind \
vermutlich in..." oder "In Ihrer Region...".
- Kommentieren Sie NIEMALS einen bereits bestätigten Wert erneut. \
Bestätigte Felder sind abgeschlossen.
- Wenn ein Entwurf offen ist (MODUS: BESTÄTIGUNG), stellen Sie \
KEINE neue Frage und KEINEN Beratungsimpuls. Nur zusammenfassen \
und bestätigen lassen.
- Fassen Sie den Entwurfswert NICHT länger als der Originalwert \
zusammen. Kürzer ist besser.
- Sagen Sie NICHT wiederholt „Sie haben recht" — einmal pro Gespräch ist genug.
- Sagen Sie NICHT „Lassen Sie mich das korrigieren" — korrigieren Sie einfach.
- Sagen Sie NICHT „Das ist ein sehr/besonders/enormes..." als Einleitung.
- Vermeiden Sie Superlative und Werturteile über die Angaben des Nutzers.
- Stellen Sie KEINE Nachfragen oder Vertiefungsfragen zu einem Feld \
das gerade beantwortet wurde. Sobald ein Wert erfasst ist, gehen \
Sie zum NÄCHSTEN Feld weiter.
- Sagen Sie NIEMALS "Verstehen Sie!" — das klingt belehrend. \
Verwenden Sie stattdessen "Verstanden." oder "Alles klar."
- Beginnen Sie NICHT mehr als 2 Antworten im gesamten Gespräch \
mit "Perfekt". Variieren Sie: "Gut.", "Alles klar.", \
"Verstanden.", "Weiter gehts.", oder GAR KEINE Einleitung.
- Sagen Sie NICHT "Perfekt, damit haben wir..." als Floskel.
- Beginnen Sie NICHT 2 aufeinanderfolgende Antworten mit \
demselben Wort (auch nicht "Verstanden" zweimal hintereinander).
- Verwechseln Sie NIEMALS Felder. Wenn der Nutzer gerade ein \
Feld beantwortet hat, kommentieren Sie NICHT ein anderes Feld.
- Loben Sie den Nutzer MAXIMAL 3× im gesamten Gespräch. \
Jedes Lob MUSS einen konkreten, spezifischen Grund nennen, \
der über die Antwort hinausgeht. \
VERBOTEN: "Das ist eine solide Basis", "Gute Wahl", \
"Das klingt vielversprechend", "Ihre Ziele sind klar definiert". \
ERLAUBT (selten): "Mit Digitalisierungsgrad 9 können Sie \
KI-Automatisierung ohne große Vorarbeit einsetzen." \
Im Zweifel: NICHT loben, sondern einen nützlichen Fakt liefern.

EXPERTISE-ADAPTION:
- Wenn die Hauptleistung des Nutzers KI-bezogen ist (KI-Beratung, \
KI-Entwicklung, LLM-basierte Tools, etc.), passen Sie Ihren \
Fragestil an:
  → Keine Grundlagen-Erklärungen ("KI kann helfen bei...")
  → Fragen Sie direkt und auf Augenhöhe
  → Keine Beispiele die für KI-Experten trivial sind
  → Statt "Haben Sie schon KI-Projekte getestet?" → \
    "Welche KI-Projekte laufen aktuell bei Ihnen?"
- Wenn der Nutzer offensichtlich KEIN KI-Experte ist, erklären \
Sie Begriffe kurz und geben Sie praxisnahe Beispiele.
  → Erwähnen Sie die Branche oder Rolle des Nutzers NICHT in \
jeder Antwort. Der Nutzer weiß wer er ist. Einmal im Gespräch \
reicht. Danach: direkt zur Sache.

KONTEXTUELLE ANPASSUNG:
Sie MÜSSEN jede Frage VOR dem Stellen auf Passung prüfen. \
Der Nutzer hat bereits einen R1-Fragebogen ausgefüllt — nutzen \
Sie dessen Daten als Kontext-Filter.

SOLO-ERKENNUNG:
Wenn der Nutzer im R1-Kontext als Solo-Unternehmer erkennbar ist:
- NIEMALS "Team", "Mitarbeiter" oder "Abteilung" verwenden.
- Stattdessen: "Sie persönlich", "für Ihr Unternehmen".

FORTGESCHRITTENEN-ERKENNUNG:
Wenn der R1-Kontext zeigt, dass der Nutzer KI-Experte ist \
(KI-Beratung als Hauptleistung, hohe KI-Kompetenz, 3+ \
KI-Einsatzbereiche, hoher Digitalisierungsgrad):
- Keine Grundlagen-Erklärungen.
- Fragen Sie auf Augenhöhe und direkt.
- Keine trivialen Beispiele.

HILFE-ANFRAGEN:
Wenn der Nutzer "bitte helfen", "weiß nicht" oder ähnliches sagt:
- Geben Sie 2–3 konkrete Beispiele passend zur Branche.
- Fragen Sie EIN MAL nach der bevorzugten Richtung.
- Wenn der Nutzer antwortet: Wert erfassen und WEITER.
- Die Frage NICHT erneut stellen.

WIEDERHOLUNGS-SPERRE:
- Beantwortete Fragen sind ABGESCHLOSSEN — NIEMALS erneut stellen, \
auch nicht umformuliert.

R1-KONTEXT NUTZEN:
- Der Nutzer hat bereits einen R1-Fragebogen ausgefüllt. Die \
Ergebnisse stehen im System-Kontext.
- Wenn Strategy-Fragen sich mit R1-Antworten überschneiden \
(z.B. Budget, Tools), verweisen Sie kurz darauf: \
"Im ersten Teil haben Sie als Budget 2.000-10.000€ angegeben — \
gilt das auch speziell für die KI-Implementierung?"
- Stellen Sie KEINE Frage erneut, deren Antwort bereits aus \
dem R1-Kontext bekannt ist, OHNE darauf zu verweisen.

KÜRZE:
- Nach Quick-Reply-Klicks: MAXIMAL 1 kurzer Satz (unter 15 Wörter), \
dann SOFORT die nächste Frage. Beispiele guter Reaktionen: \
"Verstanden." / "Gut." / "Alles klar." / Oder GAR KEINE Reaktion.
- WIEDERHOLEN Sie NICHT die gerade gegebene Antwort des Nutzers. \
NICHT: "Verstanden, mit 2.000-10.000€ Budget und 1-3 Monaten..." \
SONDERN: "Gut. Welche Prioritäten haben Sie beim KI-Einsatz?"
- Nach Freitext-Antworten: MAXIMAL 1 Satz Reaktion, dann nächste Frage.
- Den Satz "Diese Angabe ist optional, hilft aber die Empfehlungen \
zu verbessern" oder jede sinngleiche Formulierung dürfen Sie \
EXAKT 1× im gesamten Gespräch verwenden — beim ERSTEN optionalen \
Feld. Danach NIE WIEDER. Bei allen weiteren optionalen Feldern: \
Stellen Sie die Frage OHNE Hinweis auf Optionalität. Der Nutzer \
kann jederzeit "weiter" sagen — das muss nicht wiederholt werden.
- Im Bestätigungsmodus: Maximal 2 Sätze total.
- Im Dialogmodus: Maximal 4 Sätze total.
- Im Fragemodus: Maximal 1 Satz Reaktion + 1 Frage mit kurzem Kontext.

BERATUNGSIMPULSE (ÜBERZEUGUNGSDREIECK):
Nutzen Sie pro Reaktion EINEN dieser drei Hebel — abwechselnd:

PATHOS: Helfen Sie dem Nutzer, die strategische Wirkung zu sehen. \
"Mit einem klaren Zeitrahmen lässt sich das erste KI-Projekt in \
Wochen statt Monaten umsetzen."

LOGOS: Geben Sie EINEN konkreten Vergleich oder Branchenwert. \
"Die meisten KMU starten mit 2.000–10.000 € für den ersten \
KI-Use-Case — das reicht oft für spürbare Ergebnisse."

ETHOS: Normalisieren Sie Unsicherheit und zeigen Sie Kompetenz. \
"Die Frage nach dem Ansatz ist für viele KMU neu — genau deshalb \
gibt der Strategiebericht hier konkrete Empfehlungen."

Pro Antwort 1 Hebel (1–2 Sätze). Wechseln Sie ab. \
Im Bestätigungsmodus: KEIN Impuls. Formulieren Sie IMMER eigene, \
zur Branche passende Impulse — nie Beispielsätze wörtlich.

ZIEL: Auch das Strategy-Gespräch soll sich wie kompetente \
Beratung anfühlen, nicht wie ein Formular.

AKTUELLER STAND:
- Abschnitt: {section_name} (Schritt {section_number} von {total_sections})
- Bereits erfasst: {collected_fields_summary}
- Noch offen: {missing_in_section}

ALS NÄCHSTES ERFRAGEN:
{next_fields_with_descriptions}

ABSCHLUSS:
Wenn alle Felder erfasst sind:
- Schreiben Sie einen KURZEN Übergangssatz (max. 1 Satz), z.B.: \
"Gut, ich habe alle Informationen für Ihren Strategiebericht."
- Fragen Sie: "Soll ich Ihren Strategiebericht jetzt erstellen?"
- Listen Sie NICHT alle erfassten Felder als Bullet-Liste auf.

WENN DER USER EINE ZUSAMMENFASSUNG BESTÄTIGT (z.B. "ja", "stimmt", "passt"):
- Gehen Sie SOFORT zum nächsten Feld weiter.
- Wiederholen Sie die Zusammenfassung NIEMALS.
- Fragen Sie NICHT erneut ob die Angaben korrekt sind.
"""

STRATEGY_SECTION_HINTS: dict[int, str] = {
    0: "LOGOS+ETHOS: Budget und Zeitrahmen sind oft die schwierigsten Fragen. 'Unklar' ist valide — normalisieren (ETHOS). Bei Prioritäten (S3) konkret helfen (LOGOS): 'Kosten senken = z.B. Prozesse automatisieren. Compliance = z.B. DSGVO und EU AI Act.' Bei Engpass (S4) Verständnis zeigen: 'Die meisten KMU nennen Know-how oder fehlende Use Cases.'",
    1: "ETHOS+PATHOS: Abschnitt ist komplett optional — transparent machen. Bei S9 (Infrastruktur) kurz Cloud/On-Premise/Hybrid erklären. Moat-Felder: Relevanz erklären (PATHOS): 'Damit Ihr Strategiebericht zeigt, wo Sie sich differenzieren können.'",
}


def _get_system_prompt(report_type: str) -> str:
    """Get the system prompt template for a report type."""
    if report_type == "strategy":
        return STRATEGY_CONVERSATION_PROMPT
    return CONVERSATION_SYSTEM_PROMPT


def _get_section_hints(report_type: str) -> dict[int, str]:
    """Get section hints for a report type."""
    if report_type == "strategy":
        return STRATEGY_SECTION_HINTS
    return SECTION_HINTS


def _format_next_fields(field_names: list[str], report_type: str = "r1") -> str:
    """Format field descriptions for the system prompt."""
    if not field_names:
        return "Alle Felder dieses Abschnitts sind erfasst."
    registry = get_registry_for_report(report_type)
    lines = []
    for name in field_names:
        desc = FIELD_DESCRIPTIONS.get(name, name)
        reg = registry.get(name, {})
        pflicht = "Pflicht" if reg.get("required") else "Optional"
        lines.append(f"- {name} ({pflicht}): {desc}")
    return "\n".join(lines)


def _format_collected_summary(collected: dict) -> str:
    """Format collected fields for display in the system prompt."""
    if not collected:
        return "noch keine Angaben"
    parts = []
    for k, v in collected.items():
        # Make bundesland human-readable
        if k == "bundesland" and isinstance(v, str):
            label = BUNDESLAND_LABELS.get(v, v)
            parts.append(f"{k}: {label}")
        else:
            parts.append(f"{k}: {v}")
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Streaming Response Generator
# ---------------------------------------------------------------------------

async def generate_response(
    session_messages: list[dict],
    collected_fields: dict,
    missing_fields: list[str],
    next_fields: list[str],
    section: dict,
    report_type: str = "r1",
    draft_mode: bool = False,
    pending_field: str | None = None,
    pending_value: object = None,
    dialog_mode: bool = False,
) -> AsyncGenerator[str, None]:
    """
    Generate streaming AI response.

    Yields text tokens as they arrive from Claude Sonnet.

    When draft_mode=True, injects a context block describing the current
    draft state (dialog / pending confirmation / normal question).
    """
    client = _get_async_client()
    if client is None:
        yield "Entschuldigung, ich bin gerade nicht erreichbar. Bitte versuchen Sie es gleich nochmal."
        return

    sections = get_sections_for_report(report_type)
    section_index: int = section["index"]
    prompt_template = _get_system_prompt(report_type)
    system_prompt = prompt_template.format(
        section_name=section["name"],
        section_number=section_index + 1,
        total_sections=len(sections),
        collected_fields_summary=_format_collected_summary(collected_fields),
        missing_in_section=", ".join(missing_fields) if missing_fields else "alle erfasst",
        next_fields_with_descriptions=_format_next_fields(next_fields, report_type),
    )

    # Inject section-specific hint
    hints = _get_section_hints(report_type)
    hint = hints.get(section_index, "")
    if hint:
        system_prompt += f"\n\nHINWEIS FÜR DIESEN ABSCHNITT:\n{hint}"

    # Draft-mode context injection
    if draft_mode:
        system_prompt += _build_draft_context(pending_field, pending_value, dialog_mode)

    messages = build_conversation_messages(session_messages)

    try:
        async with client.messages.stream(
            model=CONVERSATION_MODEL,
            max_tokens=800,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as exc:
        log.error("[CHAT-CONV] Streaming failed: %s", exc, exc_info=True)
        yield "Entschuldigung, es gab einen Verbindungsfehler. Könnten Sie das bitte nochmal versuchen?"


def _build_draft_context(
    pending_field: str | None,
    pending_value: object,
    dialog_mode: bool,
) -> str:
    """Build the draft-mode context block for the system prompt."""
    if dialog_mode and not pending_field:
        return """

AKTUELLER MODUS: DIALOG
Der Nutzer hat eine Rückfrage zum aktuellen Thema gestellt.

REGELN FÜR DIESEN MODUS:
- Beantworten Sie die Frage hilfreich, konkret und mit Branchenbezug.
- Stellen Sie NICHT die nächste Frage.
- Bleiben Sie beim aktuellen Thema.
- Wenn die Antwort den Nutzer zu einer besseren eigenen Antwort \
führen kann, geben Sie am Ende einen sanften Impuls: \
"Hilft Ihnen das bei der Einschätzung?"
- Maximal 4 Sätze.
- Wiederholen Sie NICHT Informationen die der Nutzer bereits \
gegeben hat."""

    if pending_field and pending_value is not None:
        desc = FIELD_DESCRIPTIONS.get(pending_field, pending_field)
        label = desc.split("(")[0].strip() if desc else pending_field
        return f"""

AKTUELLER MODUS: BESTÄTIGUNG
Ich habe folgenden Wert für "{label}" erkannt: "{pending_value}"

REGELN FÜR DIESEN MODUS:
- Fassen Sie den erkannten Wert in EINEM Satz zusammen — in eigenen \
Worten, nicht als wörtliches Zitat.
- Fragen Sie kurz ob das korrekt ist. Beispiel: "Passt das so?"
- Stellen Sie NICHT die nächste Frage.
- Bieten Sie KEINE Alternativen oder Ergänzungen an.
- Wenn der Wert sehr kurz oder vage ist, fragen Sie gezielt nach: \
"Können Sie das noch etwas konkretisieren?"
- Maximal 2 Sätze."""

    return """

AKTUELLER MODUS: FRAGE
Der Nutzer hat die vorherige Angabe bestätigt oder es gibt keinen \
offenen Entwurf.

REGELN FÜR DIESEN MODUS:
- Reagieren Sie KURZ (maximal 1 Satz) auf die letzte bestätigte Antwort.
- Stellen Sie dann genau EINE neue Frage zum nächsten Feld.
- Beziehen Sie sich NUR auf das aktuelle Feld — nicht auf frühere.
- Beginnen Sie NICHT mit "Verstanden", "Perfekt", "Großartig" \
wenn diese Wörter in den letzten 3 Antworten bereits vorkamen."""


# ===========================================================================
# Template-based summary (no LLM — deterministic)
# ===========================================================================

# Display labels for enum/multi values (value -> German label)
# Source of truth: formbuilder_de_SINGLE_FULL.js + strategy.html
_ENUM_DISPLAY: dict[str, dict[str, str]] = {
    # ── R1: Block 1 – Firmendaten & Branche ──
    "branche": {
        "marketing": "Marketing & Werbung", "beratung": "Beratung & Dienstleistungen",
        "it": "IT & Software", "finanzen": "Finanzen & Versicherungen",
        "handel": "Handel & E-Commerce", "bildung": "Bildung", "verwaltung": "Verwaltung",
        "gesundheit": "Gesundheit & Pflege", "bau": "Bauwesen & Architektur",
        "medien": "Medien & Kreativwirtschaft", "industrie": "Industrie & Produktion",
        "logistik": "Transport & Logistik", "gastronomie": "Gastronomie & Tourismus",
    },
    "unternehmensgroesse": {
        "1": "1 (Solo)", "2–10": "2–10 (Kleines Team)", "11–100": "11–100 (KMU)",
    },
    "country": {
        "DE": "Deutschland", "AT": "Österreich", "CH": "Schweiz",
        "FR": "Frankreich", "NL": "Niederlande", "IT": "Italien", "ES": "Spanien",
        "BE": "Belgien", "LU": "Luxemburg", "DK": "Dänemark", "SE": "Schweden",
        "PL": "Polen", "CZ": "Tschechien", "IE": "Irland", "PT": "Portugal",
        "FI": "Finnland", "GR": "Griechenland", "HR": "Kroatien", "SI": "Slowenien",
        "SK": "Slowakei", "HU": "Ungarn", "RO": "Rumänien", "BG": "Bulgarien",
        "EE": "Estland", "LV": "Lettland", "LT": "Litauen", "MT": "Malta", "CY": "Zypern",
        "GB": "Vereinigtes Königreich (UK)", "NO": "Norwegen", "IS": "Island",
        "LI": "Liechtenstein", "other_europe": "Anderes europäisches Land",
        "other": "Nicht-europäisches Land",
    },
    "zielgruppen": {
        "b2b": "B2B (Geschäftskunden)", "b2c": "B2C (Endverbraucher)",
        "kmu": "KMU", "grossunternehmen": "Großunternehmen",
        "selbststaendige": "Selbstständige/Freiberufler",
        "oeffentliche_hand": "Öffentliche Hand", "privatpersonen": "Privatpersonen",
        "startups": "Startups", "andere": "Andere",
    },
    "jahresumsatz": {
        "unter_100k": "Bis 100.000 €", "100k_500k": "100.000–500.000 €",
        "500k_2m": "500.000–2 Mio. €", "2m_10m": "2–10 Mio. €",
        "ueber_10m": "Über 10 Mio. €", "keine_angabe": "Keine Angabe",
    },
    "it_infrastruktur": {
        "cloud": "Cloud-basiert", "on_premise": "On-Premises",
        "hybrid": "Hybrid (Cloud + eigene Server)", "unklar": "Unklar / noch offen",
    },
    "interne_ki_kompetenzen": {
        "ja": "Ja", "nein": "Nein", "in_planung": "In Planung",
    },
    "datenquellen": {
        "kundendaten": "Kundendaten (CRM, Service)", "verkaufsdaten": "Verkaufs-/Bestelldaten",
        "produktionsdaten": "Produktions-/Betriebsdaten", "personaldaten": "Personal-/HR-Daten",
        "marketingdaten": "Marketing-/Kampagnendaten", "sonstige": "Sonstige Datenquellen",
    },
    # ── R1: Block 2 – Status Quo ──
    "prozesse_papierlos": {
        "0-20": "0–20 %", "21-50": "21–50 %", "51-80": "51–80 %", "81-100": "81–100 %",
    },
    "automatisierungsgrad": {
        "sehr_niedrig": "Sehr niedrig", "eher_niedrig": "Eher niedrig",
        "mittel": "Mittel", "eher_hoch": "Eher hoch", "sehr_hoch": "Sehr hoch",
    },
    "ki_einsatz": {
        "chatbots": "Chatbots / Kundenservice", "marketing": "Marketing & Content",
        "vertrieb": "Vertrieb & CRM", "datenanalyse": "Datenanalyse",
        "produktion": "Produktion / Logistik", "hr": "Personalmanagement",
        "andere": "Andere Bereiche", "noch_keine": "Noch keine Nutzung",
    },
    "ki_kompetenz": {
        "hoch": "Hoch", "mittel": "Mittel", "niedrig": "Niedrig", "keine": "Keine",
    },
    # ── R1: Block 3 – Ziele & Use Cases ──
    "ki_ziele": {
        "effizienz": "Effizienz steigern", "automatisierung": "Automatisierung",
        "neue_produkte": "Neue Produkte/Services", "kundenservice": "Kundenservice verbessern",
        "datenauswertung": "Daten besser nutzen", "kosten_senken": "Kosten senken",
        "wettbewerbsfaehigkeit": "Wettbewerbsfähigkeit", "keine_angabe": "Noch unklar",
    },
    "anwendungsfaelle": {
        "chatbots": "Chatbots / FAQ-Automatisierung", "content_generation": "Content-Generierung",
        "datenanalyse": "Datenanalyse & Reporting", "dokumentation": "Dokumentation & Wissen",
        "prozess_automation": "Prozessautomation", "personalisierung": "Personalisierung",
        "andere": "Andere", "keine_angabe": "Noch unklar",
    },
    "pilot_bereich": {
        "kundenservice": "Kundenservice", "marketing": "Marketing / Content",
        "vertrieb": "Vertrieb", "verwaltung": "Verwaltung / Backoffice",
        "produktion": "Produktion / Logistik", "andere": "Andere",
    },
    # ── R1: Block 4 – Strategie & Governance ──
    "massnahmen_komplexitaet": {
        "niedrig": "Niedrig", "mittel": "Mittel", "hoch": "Hoch", "unklar": "Unklar",
    },
    "roadmap_vorhanden": {
        "ja": "Ja", "teilweise": "Teilweise", "nein": "Nein",
    },
    "governance_richtlinien": {
        "ja": "Ja", "teilweise": "Teilweise", "nein": "Nein",
    },
    "change_management": {
        "sehr_hoch": "Sehr hoch", "hoch": "Hoch", "mittel": "Mittel",
        "niedrig": "Niedrig", "sehr_niedrig": "Sehr niedrig",
    },
    # ── R1: Block 5 – Ressourcen & Präferenzen ──
    "zeitbudget": {
        "unter_2": "Unter 2 Stunden", "2_5": "2–5 Stunden",
        "5_10": "5–10 Stunden", "ueber_10": "Über 10 Stunden",
    },
    "vorhandene_tools": {
        "crm": "CRM-Systeme (HubSpot, Salesforce)", "erp": "ERP-Systeme (SAP, Odoo)",
        "projektmanagement": "Projektmanagement (Asana, Trello)",
        "marketing_automation": "Marketing Automation",
        "buchhaltung": "Buchhaltungssoftware", "keine": "Keine / andere",
    },
    "regulierte_branche": {
        "gesundheit": "Gesundheit & Medizin", "finanzen": "Finanzen & Versicherungen",
        "oeffentlich": "Öffentlicher Sektor", "recht": "Rechtliche Dienstleistungen",
        "vertraulich_nda": "Vertrauliche Kundendaten / NDA-Material",
        "keine": "Keine dieser Branchen",
    },
    "trainings_interessen": {
        "prompt_engineering": "Prompt Engineering", "llm_basics": "LLM-Grundlagen",
        "datenqualitaet_governance": "Datenqualität & Governance",
        "automatisierung": "Automatisierung & Skripte",
        "ethik_recht": "Ethische & rechtliche Grundlagen", "keine": "Keine / noch unklar",
    },
    "vision_prioritaet": {
        "gpt_services": "KI-gestützte Services und Produkte",
        "kundenservice": "Optimierung Kundenservice und Support",
        "datenprodukte": "Entwicklung datenbasierter Angebote",
        "prozessautomation": "Automatisierung interner Prozesse",
        "marktfuehrerschaft": "Technologieführerschaft im Markt",
        "keine_angabe": "Noch unklar",
    },
    # ── R1: Block 6 – Rechtliches & Compliance ──
    "datenschutzbeauftragter": {
        "ja": "Ja", "nein": "Nein", "teilweise": "Teilweise (extern/Planung)",
    },
    "technische_massnahmen": {
        "alle": "Alle relevanten Maßnahmen", "teilweise": "Teilweise vorhanden",
        "keine": "Noch keine",
    },
    "folgenabschaetzung": {
        "ja": "Ja, durchgeführt", "nein": "Nein, noch nicht", "teilweise": "In Planung",
    },
    "meldewege": {
        "ja": "Ja, klar definiert", "teilweise": "Teilweise vorhanden",
        "nein": "Nein, noch nicht geregelt",
    },
    "loeschregeln": {
        "ja": "Ja, dokumentiert", "teilweise": "Teilweise vorhanden",
        "nein": "Nein, noch nicht definiert",
    },
    "ai_act_kenntnis": {
        "sehr_gut": "Sehr gut", "gut": "Gut",
        "gehoert": "Schon mal gehört", "unbekannt": "Noch nicht bekannt",
    },
    "ki_hemmnisse": {
        "rechtsunsicherheit": "Rechtsunsicherheit", "datenschutz": "Datenschutz",
        "knowhow": "Fehlendes Know-how", "budget": "Begrenztes Budget",
        "teamakzeptanz": "Teamakzeptanz", "zeitmangel": "Zeitmangel",
        "it_integration": "IT-Integration", "keine": "Keine Hemmnisse", "andere": "Andere",
    },
    # ── R1: Block 7 – Förderung & Investition ──
    "bisherige_foerdermittel": {"ja": "Ja", "nein": "Nein"},
    "interesse_foerderung": {
        "ja": "Ja, Programme vorschlagen", "nein": "Kein Bedarf",
        "unklar": "Unklar, bitte beraten",
    },
    "erfahrung_beratung": {"ja": "Ja", "nein": "Nein", "unklar": "Unklar"},
    "investitionsbudget": {
        "unter_2000": "Unter 2.000 €", "2000_10000": "2.000–10.000 €",
        "10000_50000": "10.000–50.000 €", "ueber_50000": "Über 50.000 €",
        "unklar": "Noch unklar",
    },
    "marktposition": {
        "marktfuehrer": "Marktführer", "oberes_drittel": "Oberes Drittel",
        "mittelfeld": "Mittelfeld", "nachzuegler": "Nachzügler",
        "unsicher": "Schwer einzuschätzen",
    },
    "benchmark_wettbewerb": {
        "ja": "Ja, regelmäßig", "nein": "Nein", "selten": "Selten",
    },
    "innovationsprozess": {
        "innovationsteam": "Innovationsteam", "mitarbeitende": "Durch Mitarbeitende",
        "kunden": "Mit Kunden", "berater": "Externe Berater",
        "zufall": "Zufällig", "unbekannt": "Keine klare Strategie",
    },
    # ── Strategy: S1–S10 ──
    "s1_budget": {
        "unter_2000": "Unter 2.000 €", "2000_10000": "2.000–10.000 €",
        "10000_50000": "10.000–50.000 €", "ueber_50000": "Über 50.000 €",
        "unklar": "Noch unklar",
    },
    # s2–s10: values are already human-readable labels in the form
    # ── Strategy: Moat-Felder ──
    "wettbewerber_anzahl": {
        "wenige": "Wenige (1–3)", "mehrere": "Mehrere (4–10)",
        "viele": "Viele (mehr als 10)", "unklar": "Schwer einzuschätzen",
    },
    "kundenbindung_typ": {
        "einmalig": "Einmalkunden / Projektgeschäft",
        "wiederkehrend": "Wiederkehrende Kunden / Verträge / Abos",
        "gemischt": "Mischung aus beidem",
    },
    "datenreife": {
        "keine": "Kaum / keine strukturierten Daten",
        "basis": "Grundlegende Daten (CRM, Buchhaltung)",
        "umfangreich": "Umfangreiche eigene Datenbestände",
        "unklar": "Bin mir nicht sicher",
    },
}


def build_summary(collected_fields: dict, report_type: str = "r1") -> str:
    """
    Build a structured, template-based summary of all collected fields.
    No LLM involved — purely deterministic from collected data.
    """
    sections = get_sections_for_report(report_type)
    registry = get_registry_for_report(report_type)
    lines = ["**Zusammenfassung Ihrer Angaben:**\n"]

    for section in sections:
        section_lines: list[str] = []
        section_fields: list[str] = section["fields"]
        for field_name in section_fields:
            if field_name not in collected_fields:
                continue
            value = collected_fields[field_name]
            label = FIELD_DESCRIPTIONS.get(field_name, field_name).split("(")[0].strip()
            display = _format_value_for_display(field_name, value)
            section_lines.append(f"- {label}: {display}")

        if section_lines:
            lines.append(f"\n**{section['name']}**")
            lines.extend(section_lines)

    lines.append("\n\nSind alle Angaben korrekt? Dann starte ich die Auswertung.")
    return "\n".join(lines)


def _format_value_for_display(field_name: str, value: object) -> str:
    """Format a field value for human-readable display."""
    reg = FIELD_REGISTRY.get(field_name) or STRATEGY_FIELD_REGISTRY.get(field_name, {})
    field_type = reg.get("type", "text")

    # Enum: use display label
    if field_type == "enum":
        str_val = str(value)
        enum_labels = _ENUM_DISPLAY.get(field_name)
        if enum_labels and str_val in enum_labels:
            return enum_labels[str_val]
        # Bundesland code → label
        if field_name == "bundesland":
            return BUNDESLAND_LABELS.get(str_val, str_val)
        return str_val

    # Multi: resolve labels, then comma-separated
    if field_type == "multi" and isinstance(value, list):
        if not value:
            return "–"
        enum_labels = _ENUM_DISPLAY.get(field_name, {})
        resolved = [enum_labels.get(str(v), str(v)) for v in value]
        return ", ".join(resolved)

    # Slider: number with context
    if field_type == "slider":
        mx = reg.get("max", 10)
        return f"{value} von {mx}"

    # Bool
    if field_type == "bool":
        return "Ja" if value else "Nein"

    # Text: show full text in summary (truncation removed –
    # the summary is the last touchpoint before report generation)
    if field_type == "text":
        return str(value).strip() or "–"

    return str(value)
