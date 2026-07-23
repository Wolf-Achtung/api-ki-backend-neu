"""
SOFORT-START-SEITE Generator v2.0
==================================
Generiert personalisierte "Sofort-Start" Inhalte für den KI-Readiness Report.

Enthält:
1. Der EINE erste Schritt (heute machbar)
2. 3 Copy-Paste Prompts für die Hauptleistung
3. Tool-Empfehlungen mit Links & Preisen
4. Wichtige Warnungen (Don'ts)
5. Konkrete Zeitersparnis-Berechnung
6. Checkliste für den Start
7. Entscheidungsvorlage für Vorgesetzte

Unterstützte Branchen (13):
- Marketing & Werbung
- Beratung & Dienstleistungen
- IT & Software
- Finanzen & Versicherungen
- Handel & E-Commerce
- Bildung
- Verwaltung
- Gesundheit & Pflege
- Bauwesen & Architektur
- Medien & Kreativwirtschaft
- Industrie & Produktion
- Transport & Logistik
- Gastronomie & Tourismus
"""

import logging
import re
from typing import Any, Dict, List, Optional, cast

log = logging.getLogger(__name__)

# PLATIN+++ FIX 1.1/1.2/1.4: Import canonical rates from single source of truth
try:
    from services.business_case_engine_v2 import (
        HOURLY_RATES_BY_SIZE,
        OPEX_DEFAULTS_BY_SIZE,
        MAX_TIME_SAVINGS_BY_SIZE,
    )
except ImportError:
    HOURLY_RATES_BY_SIZE = {"solo": 80, "team": 95, "kmu": 110, "enterprise": 130}
    OPEX_DEFAULTS_BY_SIZE = {"solo": 50, "team": 150, "kmu": 400, "enterprise": 1500}
    MAX_TIME_SAVINGS_BY_SIZE = {"solo": 20, "team": 60, "kmu": 150, "enterprise": 400}


def _get_canonical_rate(company_size: str) -> int:
    """Get canonical hourly rate for company size. PLATIN+++ single source of truth."""
    size_key = "solo"
    if company_size:
        size_lower = company_size.lower()
        if any(x in size_lower for x in ["team", "klein", "2-10", "2–10"]):
            size_key = "team"
        elif any(x in size_lower for x in ["kmu", "mittel", "11-100", "11–100", "100"]):
            size_key = "kmu"
    return int(HOURLY_RATES_BY_SIZE.get(size_key, 80))


def _get_canonical_opex_yearly(company_size: str) -> int:
    """Get canonical yearly OPEX for company size. PLATIN+++ single source of truth."""
    size_key = "solo"
    if company_size:
        size_lower = company_size.lower()
        if any(x in size_lower for x in ["team", "klein", "2-10", "2–10"]):
            size_key = "team"
        elif any(x in size_lower for x in ["kmu", "mittel", "11-100", "11–100", "100"]):
            size_key = "kmu"
    return int(OPEX_DEFAULTS_BY_SIZE.get(size_key, 50)) * 12

# =============================================================================
# BRANCHEN-SPEZIFISCHE PROMPTS (13 Branchen)
# =============================================================================

BRANCHE_PROMPTS = {
    # -------------------------------------------------------------------------
    # 1. MARKETING & WERBUNG
    # -------------------------------------------------------------------------
    "marketing": {
        "name": "Marketing & Werbung",
        "erster_schritt": "Lassen Sie ChatGPT 5 Social-Media-Posts für diese Woche erstellen",
        "zeitersparnis_pro_woche": 8,  # Stunden
        "typische_aufgaben": ["Content-Erstellung", "Kampagnen-Planung", "Analyse"],
        "prompts": [
            {
                "titel": "Social Media Posts erstellen",
                "prompt": """Erstellen Sie 5 LinkedIn-Posts für diese Woche:

Thema/Produkt: [BESCHREIBUNG]
Zielgruppe: [WER]
Tonalität: [professionell/locker/inspirierend]

Pro Post:
- Hook (erster Satz, der Aufmerksamkeit erregt)
- Haupttext (max. 150 Wörter)
- Call-to-Action
- 3-5 relevante Hashtags""",
                "zeitersparnis": "1-2 Std pro Woche"
            },
            {
                "titel": "Newsletter schreiben",
                "prompt": """Erstellen Sie einen Newsletter:

Thema: [HAUPTTHEMA]
Zielgruppe: [WER]
Ziel: [Was soll der Leser tun?]

Struktur:
1. Betreffzeile (A/B-Varianten)
2. Preview-Text
3. Einleitung (persönlich)
4. Hauptinhalt
5. CTA-Button-Text
6. P.S.-Zeile""",
                "zeitersparnis": "1-2 Std pro Newsletter"
            },
            {
                "titel": "Wettbewerbsanalyse",
                "prompt": """Analysieren Sie diese Wettbewerber-Positionierung:

Wettbewerber: [NAME/BESCHREIBUNG]
Mein Unternehmen: [KURZBESCHREIBUNG]

Analysieren Sie:
1. Positionierung & USP
2. Zielgruppen-Ansprache
3. Content-Strategie
4. Stärken/Schwächen
5. Was können wir besser machen?""",
                "zeitersparnis": "2-3 Std pro Analyse"
            }
        ],
        "lern_prompt": {
            "titel": "Werbewirkung verstehen & erklären",
            "thema": "wie KI-gestützte Zielgruppenanalyse die Werbewirkung verbessert",
            "zielgruppe": "Kunden",
            "prompt": """Erkläre mir, wie KI-gestützte Zielgruppenanalyse die Werbewirkung verbessert, so dass ich es einem Kunden ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },
    
    # -------------------------------------------------------------------------
    # 1b. HANDWERK & GEWERBE (FIX-S25-B1: Separate from bauwesen)
    # -------------------------------------------------------------------------
    "handwerk": {
        "name": "Handwerk & Gewerbe",
        "erster_schritt": "Lassen Sie ChatGPT ein Angebot für eine Standardleistung formulieren",
        "zeitersparnis_pro_woche": 5,
        "typische_aufgaben": ["Angebote", "Wartungsprotokolle", "Kundenkommunikation"],
        "prompts": [
            {
                "titel": "Angebotsbeschreibung für Standardleistungen erstellen",
                "prompt": """Erstellen Sie ein professionelles Angebot:

Leistung: [z.B. Heizungswartung, Bad-Sanierung, Elektroinstallation]
Kunde: [Privat/Gewerbe]
Umfang: [BESCHREIBUNG]

Struktur:
1. Leistungsbeschreibung (verständlich für Laien)
2. Einzelpositionen mit Erläuterung
3. Material- und Arbeitskosten (getrennt)
4. Zeitrahmen
5. Gewährleistungshinweise
6. Gültigkeitsdauer""",
                "zeitersparnis": "30-45 Min pro Angebot"
            },
            {
                "titel": "Wartungsbericht/Protokoll formulieren",
                "prompt": """Erstellen Sie einen Wartungsbericht:

Anlage/Gerät: [BESCHREIBUNG]
Kunde: [NAME/ADRESSE]
Durchgeführte Arbeiten: [STICHPUNKTE]

Struktur:
- Anlagendaten und Zustand
- Durchgeführte Wartungsarbeiten
- Festgestellte Mängel
- Empfohlene Maßnahmen
- Nächster Wartungstermin
- Unterschriftsfeld""",
                "zeitersparnis": "15-20 Min pro Bericht"
            },
            {
                "titel": "Kundenerinnerung für Wartungstermin schreiben",
                "prompt": """Schreiben Sie eine freundliche Wartungserinnerung:

Kunde: [NAME]
Anlage/Gerät: [z.B. Heizung, Klimaanlage]
Letzte Wartung: [DATUM]
Empfohlener Termin: [ZEITRAUM]

Die Erinnerung soll:
- Freundlich und nicht aufdringlich sein
- Den Nutzen der Wartung erklären
- Konkrete Terminvorschläge machen
- Kontaktmöglichkeit nennen""",
                "zeitersparnis": "5-10 Min pro Erinnerung"
            }
        ],
        "lern_prompt": {
            "titel": "Qualitätsmanagement verstehen & erklären",
            "thema": "wie digitales Qualitätsmanagement und Checklisten-Apps die Arbeit im Handwerk verbessern",
            "zielgruppe": "Mitarbeitenden",
            "prompt": """Erkläre mir, wie digitales Qualitätsmanagement und Checklisten-Apps die Arbeit im Handwerk verbessern, so dass ich es einem Mitarbeitenden ohne technischen Hintergrund in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },

    # -------------------------------------------------------------------------
    # 2. BERATUNG & DIENSTLEISTUNGEN
    # -------------------------------------------------------------------------
    "beratung": {
        "name": "Beratung & Dienstleistungen",
        "erster_schritt": "Lassen Sie ChatGPT Ihre nächste Kundenanfrage analysieren",
        "zeitersparnis_pro_woche": 6,
        "typische_aufgaben": ["Kundenanalyse", "Angebotserstellung", "Dokumentation"],
        "prompts": [
            {
                "titel": "Kundenanfrage analysieren",
                "prompt": """Analysieren Sie diese Kundenanfrage und erstellen Sie eine strukturierte Bedarfsanalyse:

[ANFRAGE HIER EINFÜGEN]

Bitte liefern Sie:
1. Kernproblem in einem Satz
2. 3 mögliche Lösungsansätze
3. Geschätzter Aufwand (Stunden)
4. Empfohlene nächste Schritte""",
                "zeitersparnis": "30-45 Min pro Anfrage"
            },
            {
                "titel": "Angebot strukturieren",
                "prompt": """Erstellen Sie eine Angebotsstruktur für folgendes Projekt:

Kunde: [NAME/BRANCHE]
Problem: [KURZBESCHREIBUNG]
Budget-Rahmen: [FALLS BEKANNT]

Liefern Sie:
1. Executive Summary (3 Sätze)
2. Leistungsumfang (Bullet Points)
3. Zeitplan mit Meilensteinen
4. Investitionsübersicht""",
                "zeitersparnis": "1-2 Std pro Angebot"
            },
            {
                "titel": "Meeting-Protokoll erstellen",
                "prompt": """Erstellen Sie aus diesen Meeting-Notizen ein professionelles Protokoll:

[NOTIZEN HIER EINFÜGEN]

Format:
- Datum, Teilnehmer, Dauer
- Besprochene Themen (nummeriert)
- Entscheidungen (fett markiert)
- Action Items mit Verantwortlichen und Deadline
- Nächster Termin""",
                "zeitersparnis": "20-30 Min pro Meeting"
            }
        ],
        "lern_prompt": {
            "titel": "E-Rechnung verstehen & erklären",
            "thema": "die wichtigsten Änderungen bei der E-Rechnung ab 2025",
            "zielgruppe": "Mandanten",
            "prompt": """Erkläre mir die wichtigsten Änderungen bei der E-Rechnung ab 2025, so dass ich es einem Mandanten ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },
    
    # -------------------------------------------------------------------------
    # 3. IT & SOFTWARE
    # -------------------------------------------------------------------------
    "it": {
        "name": "IT & Software",
        "erster_schritt": "Lassen Sie ChatGPT Ihren nächsten Code-Review unterstützen",
        "zeitersparnis_pro_woche": 10,
        "typische_aufgaben": ["Code-Review", "Dokumentation", "Debugging"],
        "prompts": [
            {
                "titel": "Code Review",
                "prompt": """Überprüfe diesen Code auf:
1. Bugs und potenzielle Fehler
2. Performance-Probleme
3. Security-Risiken
4. Best Practices

[CODE HIER EINFÜGEN]

Liefern Sie konkrete Verbesserungsvorschläge mit Codebeispielen.""",
                "zeitersparnis": "30-60 Min pro Review"
            },
            {
                "titel": "Technische Dokumentation",
                "prompt": """Erstellen Sie eine technische Dokumentation für:

Komponente/Feature: [NAME]
Zweck: [KURZBESCHREIBUNG]
Technologie-Stack: [LISTE]

Struktur:
1. Übersicht
2. Architektur
3. API-Referenz
4. Beispiele
5. Troubleshooting""",
                "zeitersparnis": "2-3 Std pro Doku"
            },
            {
                "titel": "User Story schreiben",
                "prompt": """Erstellen Sie User Stories für dieses Feature:

Feature: [NAME]
Zielgruppe: [WER]
Problem: [WAS WIRD GELÖST]

Format pro Story:
- Als [Rolle] möchte ich [Funktion], damit [Nutzen]
- Akzeptanzkriterien (3-5 Punkte)
- Geschätzter Aufwand (S/M/L)""",
                "zeitersparnis": "30-45 Min pro Feature"
            }
        ],
        "lern_prompt": {
            "titel": "KI-Architekturmuster verstehen & erklären",
            "thema": "wie Retrieval Augmented Generation (RAG) funktioniert und wann es sich für Unternehmen lohnt",
            "zielgruppe": "Kunden",
            "prompt": """Erkläre mir, wie Retrieval Augmented Generation (RAG) funktioniert und wann es sich für Unternehmen lohnt, so dass ich es einem Kunden ohne technischen Hintergrund in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },
    
    # -------------------------------------------------------------------------
    # 4. FINANZEN & VERSICHERUNGEN
    # -------------------------------------------------------------------------
    "finanzen": {
        "name": "Finanzen & Versicherungen",
        "erster_schritt": "Lassen Sie ChatGPT einen Kundenbrief zu Vertragsänderungen formulieren",
        "zeitersparnis_pro_woche": 5,
        "typische_aufgaben": ["Kundenkorrespondenz", "Analyse", "Reporting"],
        "prompts": [
            {
                "titel": "Kundenbrief formulieren",
                "prompt": """Formulieren Sie einen professionellen Kundenbrief:

Anlass: [z.B. Vertragsänderung, Beitragsanpassung]
Kernbotschaft: [WAS soll kommuniziert werden]
Tonalität: [seriös/empathisch/sachlich]

Der Brief soll:
- Verständlich sein (keine Fachsprache)
- Die wichtigsten Infos zuerst nennen
- Handlungsoptionen klar darstellen
- Kontaktmöglichkeiten aufzeigen""",
                "zeitersparnis": "20-30 Min pro Brief"
            },
            {
                "titel": "Risikoanalyse strukturieren",
                "prompt": """Strukturieren Sie diese Risikoinformationen für einen Kunden:

Kunde: [PROFIL]
Produkt/Anlage: [BESCHREIBUNG]
Marktdaten: [RELEVANTE INFOS]

Erstellen Sie:
1. Risikozusammenfassung (3 Sätze)
2. Chancen vs. Risiken (Tabelle)
3. Empfehlung mit Begründung
4. Disclaimer (kurz)""",
                "zeitersparnis": "30-45 Min pro Analyse"
            },
            {
                "titel": "Reporting-Text erstellen",
                "prompt": """Erstellen Sie einen Reporting-Text aus diesen Zahlen:

Kennzahlen: [LISTE]
Zeitraum: [VON-BIS]
Vergleich zu: [Vorjahr/Plan/Benchmark]

Der Text soll:
- Die wichtigsten Entwicklungen zusammenfassen
- Abweichungen erklären
- Ausblick geben
- Max. 200 Wörter""",
                "zeitersparnis": "30-45 Min pro Report"
            }
        ],
        "lern_prompt": {
            "titel": "ESG-Reporting verstehen & erklären",
            "thema": "wie KI das ESG-Reporting und die Nachhaltigkeitsberichterstattung für Finanzdienstleister verändert",
            "zielgruppe": "Kunden",
            "prompt": """Erkläre mir, wie KI das ESG-Reporting und die Nachhaltigkeitsberichterstattung für Finanzdienstleister verändert, so dass ich es einem Kunden ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },
    
    # -------------------------------------------------------------------------
    # 5. HANDEL & E-COMMERCE
    # -------------------------------------------------------------------------
    "handel": {
        "name": "Handel & E-Commerce",
        "erster_schritt": "Lassen Sie ChatGPT 10 Produktbeschreibungen optimieren",
        "zeitersparnis_pro_woche": 8,
        "typische_aufgaben": ["Produkttexte", "Kundenservice", "Aktionen"],
        "prompts": [
            {
                "titel": "Produktbeschreibung optimieren",
                "prompt": """Optimiere diese Produktbeschreibung für SEO und Conversion:

Produkt: [NAME]
Kategorie: [KATEGORIE]
Aktuelle Beschreibung: [TEXT]
Zielgruppe: [WER KAUFT DAS?]

Liefern Sie:
1. SEO-optimierter Titel
2. Kurzbeschreibung (50 Wörter)
3. Langbeschreibung mit Bullet Points
4. 5 relevante Keywords""",
                "zeitersparnis": "15-20 Min pro Produkt"
            },
            {
                "titel": "Kundenanfrage beantworten",
                "prompt": """Beantworte diese Kundenanfrage freundlich und hilfreich:

Anfrage: [TEXT]
Produkt/Bestellung: [DETAILS]
Unternehmens-Tonalität: [freundlich/professionell]

Die Antwort soll:
- Das Problem anerkennen
- Eine Lösung anbieten
- Nächste Schritte klar benennen
- Positiv enden""",
                "zeitersparnis": "10-15 Min pro Anfrage"
            },
            {
                "titel": "Aktionstext erstellen",
                "prompt": """Erstellen Sie einen überzeugenden Aktionstext:

Aktion: [z.B. 20% Rabatt, Gratis Versand]
Produkte: [WELCHE]
Zeitraum: [VON-BIS]
Zielgruppe: [WER]

Liefern Sie:
1. Headline (max. 8 Wörter)
2. Subheadline
3. 3 Bullet Points mit Benefits
4. CTA-Text
5. Kleingedrucktes""",
                "zeitersparnis": "20-30 Min pro Aktion"
            }
        ],
        "lern_prompt": {
            "titel": "Predictive Analytics verstehen & erklären",
            "thema": "wie Predictive Analytics die Lagerhaltung und Bestandsplanung optimiert",
            "zielgruppe": "Mitarbeitenden",
            "prompt": """Erkläre mir, wie Predictive Analytics die Lagerhaltung und Bestandsplanung optimiert, so dass ich es einem Mitarbeitenden ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },
    
    # -------------------------------------------------------------------------
    # 6. BILDUNG
    # -------------------------------------------------------------------------
    "bildung": {
        "name": "Bildung",
        "erster_schritt": "Lassen Sie ChatGPT einen Unterrichtsentwurf erstellen",
        "zeitersparnis_pro_woche": 6,
        "typische_aufgaben": ["Unterrichtsplanung", "Material-Erstellung", "Feedback"],
        "prompts": [
            {
                "titel": "Unterrichtsentwurf erstellen",
                "prompt": """Erstellen Sie einen Unterrichtsentwurf:

Thema: [THEMA]
Zielgruppe: [Alter/Niveau]
Dauer: [MINUTEN]
Lernziel: [WAS sollen die Teilnehmer können?]

Struktur:
1. Einstieg (Aktivierung)
2. Erarbeitung (Methoden)
3. Sicherung (Übungen)
4. Transfer (Anwendung)
5. Benötigte Materialien""",
                "zeitersparnis": "45-60 Min pro Entwurf"
            },
            {
                "titel": "Übungsaufgaben generieren",
                "prompt": """Erstellen Sie Übungsaufgaben:

Fach/Thema: [BESCHREIBUNG]
Schwierigkeitsgrad: [leicht/mittel/schwer]
Anzahl: [WIE VIELE]
Format: [Multiple Choice/Freitext/Lückentext]

Bitte mit:
- Klarer Aufgabenstellung
- Lösungshinweisen
- Bewertungskriterien""",
                "zeitersparnis": "30-45 Min pro Set"
            },
            {
                "titel": "Feedback formulieren",
                "prompt": """Formulieren Sie konstruktives Feedback:

Leistung: [BESCHREIBUNG der Arbeit]
Stärken: [WAS war gut?]
Verbesserungspotenzial: [WAS kann besser werden?]

Das Feedback soll:
- Wertschätzend beginnen
- Konkret und nachvollziehbar sein
- Verbesserungsvorschläge enthalten
- Motivierend enden""",
                "zeitersparnis": "15-20 Min pro Feedback"
            }
        ],
        "lern_prompt": {
            "titel": "KI-gestütztes Lernen verstehen & erklären",
            "thema": "wie adaptives Lernen mit KI den Unterricht individualisiert und welche Grenzen es gibt",
            "zielgruppe": "Kolleginnen und Kollegen",
            "prompt": """Erkläre mir, wie adaptives Lernen mit KI den Unterricht individualisiert und welche Grenzen es gibt, so dass ich es Kolleginnen und Kollegen ohne technischen Hintergrund in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },
    
    # -------------------------------------------------------------------------
    # 7. VERWALTUNG
    # -------------------------------------------------------------------------
    "verwaltung": {
        "name": "Verwaltung",
        "erster_schritt": "Lassen Sie ChatGPT einen Bescheid-Entwurf strukturieren",
        "zeitersparnis_pro_woche": 5,
        "typische_aufgaben": ["Bescheide", "Protokolle", "Bürgeranfragen"],
        "prompts": [
            {
                "titel": "Bescheid-Entwurf erstellen",
                "prompt": """Erstellen Sie einen Bescheid-Entwurf:

Art: [z.B. Genehmigung, Ablehnung, Änderung]
Sachverhalt: [KURZBESCHREIBUNG]
Rechtsgrundlage: [FALLS BEKANNT]

Struktur:
1. Tenor (Entscheidung)
2. Sachverhalt
3. Begründung
4. Rechtsbehelfsbelehrung
5. Fristen""",
                "zeitersparnis": "30-45 Min pro Bescheid"
            },
            {
                "titel": "Bürgeranfrage beantworten",
                "prompt": """Beantworte diese Bürgeranfrage verständlich:

Anfrage: [TEXT]
Zuständigkeit: [ABTEILUNG/THEMA]

Die Antwort soll:
- Verständlich sein (keine Amtssprache)
- Die Frage direkt beantworten
- Nächste Schritte erklären
- Ansprechpartner nennen""",
                "zeitersparnis": "15-20 Min pro Anfrage"
            },
            {
                "titel": "Sitzungsprotokoll erstellen",
                "prompt": """Erstellen Sie ein Sitzungsprotokoll:

Gremium: [NAME]
Datum: [DATUM]
Notizen: [STICHPUNKTE]

Format:
- Anwesende/Entschuldigte
- Tagesordnung
- Zu jedem TOP: Diskussion, Beschluss
- Aufgaben mit Verantwortlichen
- Nächster Termin""",
                "zeitersparnis": "30-45 Min pro Protokoll"
            }
        ],
        "lern_prompt": {
            "titel": "OZG und Digitalisierungspflichten verstehen & erklären",
            "thema": "welche Digitalisierungspflichten das Onlinezugangsgesetz (OZG 2.0) für Kommunen bringt",
            "zielgruppe": "Bürgerinnen und Bürgern",
            "prompt": """Erkläre mir, welche Digitalisierungspflichten das Onlinezugangsgesetz (OZG 2.0) für Kommunen bringt, so dass ich es Bürgerinnen und Bürgern ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },

    # -------------------------------------------------------------------------
    # 8. GESUNDHEIT & PFLEGE
    # -------------------------------------------------------------------------
    "gesundheit": {
        "name": "Gesundheit & Pflege",
        "erster_schritt": "Lassen Sie ChatGPT eine Patienteninformation formulieren",
        "zeitersparnis_pro_woche": 4,
        "typische_aufgaben": ["Patienteninfos", "Dokumentation", "Schulungen"],
        "prompts": [
            {
                "titel": "Patienteninformation erstellen",
                "prompt": """Erstellen Sie eine verständliche Patienteninformation:

Thema: [z.B. Behandlung, Medikament, Nachsorge]
Zielgruppe: [Patient/Angehörige]
Wichtige Punkte: [LISTE]

Die Info soll:
- Einfache Sprache verwenden
- Keine medizinischen Fachbegriffe (oder erklärt)
- Handlungsanweisungen klar formulieren
- Warnzeichen benennen
- Kontaktinfos enthalten""",
                "zeitersparnis": "20-30 Min pro Info"
            },
            {
                "titel": "Übergabe strukturieren",
                "prompt": """Strukturieren Sie diese Übergabe-Informationen:

Patient: [ANONYMISIERT - NUR ALTER/RELEVANTES]
Aktuelle Situation: [STICHPUNKTE]
Maßnahmen: [WAS WURDE GEMACHT]

Erstellen Sie:
- SBAR-Format (Situation, Background, Assessment, Recommendation)
- Prioritäten klar markiert
- Offene Aufgaben""",
                "zeitersparnis": "10-15 Min pro Übergabe"
            },
            {
                "titel": "Schulungskonzept erstellen",
                "prompt": """Erstellen Sie ein Schulungskonzept:

Thema: [z.B. Hygiene, Notfall, Gerät]
Zielgruppe: [WER]
Dauer: [MINUTEN]

Struktur:
1. Lernziele
2. Theorieteil (Kernpunkte)
3. Praktische Übung
4. Lernerfolgskontrolle
5. Handout-Inhalte""",
                "zeitersparnis": "45-60 Min pro Konzept"
            }
        ],
        "lern_prompt": {
            "titel": "KI in der Pflege verstehen & erklären",
            "thema": "wie KI-gestützte Dokumentation und Spracherkennung den Pflegealltag entlastet",
            "zielgruppe": "Patientinnen und Patienten",
            "prompt": """Erkläre mir, wie KI-gestützte Dokumentation und Spracherkennung den Pflegealltag entlastet, so dass ich es Patientinnen und Patienten ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },
    
    # -------------------------------------------------------------------------
    # 9. BAUWESEN & ARCHITEKTUR
    # -------------------------------------------------------------------------
    "bauwesen": {
        "name": "Bauwesen & Architektur",
        "erster_schritt": "Lassen Sie ChatGPT ein Baustellenprotokoll strukturieren",
        "zeitersparnis_pro_woche": 5,
        "typische_aufgaben": ["Protokolle", "Ausschreibungen", "Kundenkorrespondenz"],
        "prompts": [
            {
                "titel": "Baustellenprotokoll erstellen",
                "prompt": """Erstellen Sie ein Baustellenprotokoll:

Projekt: [NAME]
Datum: [DATUM]
Notizen: [STICHPUNKTE]

Struktur:
- Wetter, Anwesende
- Baufortschritt (mit %)
- Festgestellte Mängel
- Vereinbarungen
- Nächste Schritte
- Fotodokumentation (Beschreibung)""",
                "zeitersparnis": "20-30 Min pro Protokoll"
            },
            {
                "titel": "Leistungsverzeichnis-Position",
                "prompt": """Formulieren Sie eine LV-Position:

Gewerk: [z.B. Mauerwerk, Elektro]
Leistung: [BESCHREIBUNG]
Menge: [EINHEIT]

Die Position soll:
- VOB-konform formuliert sein
- Alle relevanten Details enthalten
- Eindeutig kalkulierbar sein""",
                "zeitersparnis": "15-20 Min pro Position"
            },
            {
                "titel": "Bauherren-Schreiben",
                "prompt": """Formulieren Sie ein Schreiben an den Bauherrn:

Anlass: [z.B. Nachtrag, Terminverzug, Änderung]
Kernbotschaft: [WAS soll kommuniziert werden]
Tonalität: [sachlich/erklärend]

Das Schreiben soll:
- Sachverhalt klar darstellen
- Auswirkungen benennen
- Lösungsvorschlag machen
- Nächste Schritte definieren""",
                "zeitersparnis": "20-30 Min pro Schreiben"
            }
        ],
        "lern_prompt": {
            "titel": "BIM verstehen & erklären",
            "thema": "wie Building Information Modeling (BIM) mit KI-Unterstützung die Bauplanung verändert",
            "zielgruppe": "Bauherren",
            "prompt": """Erkläre mir, wie Building Information Modeling (BIM) mit KI-Unterstützung die Bauplanung verändert, so dass ich es einem Bauherren ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },
    
    # -------------------------------------------------------------------------
    # 10. MEDIEN & KREATIVWIRTSCHAFT
    # -------------------------------------------------------------------------
    "medien": {
        "name": "Medien & Kreativwirtschaft",
        "erster_schritt": "Lassen Sie ChatGPT 10 Headline-Varianten generieren",
        "zeitersparnis_pro_woche": 8,
        "typische_aufgaben": ["Content-Ideen", "Texte", "Briefings"],
        "prompts": [
            {
                "titel": "Headline-Varianten generieren",
                "prompt": """Generiere 10 Headline-Varianten:

Thema: [BESCHREIBUNG]
Medium: [Web/Print/Social]
Zielgruppe: [WER]
Tonalität: [seriös/provokant/emotional]

Varianten:
- 3x sachlich-informativ
- 3x emotional/storytelling
- 2x mit Zahlen/Fakten
- 2x mit Frage/Aufforderung""",
                "zeitersparnis": "20-30 Min pro Thema"
            },
            {
                "titel": "Creative Brief erstellen",
                "prompt": """Erstellen Sie ein Creative Brief:

Projekt: [NAME]
Kunde: [BRANCHE/TYP]
Ziel: [WAS soll erreicht werden]

Struktur:
1. Hintergrund & Ausgangslage
2. Zielgruppe (Detail)
3. Kernbotschaft
4. Tone of Voice
5. Must-haves & No-Gos
6. Deliverables & Formate
7. Timeline & Budget""",
                "zeitersparnis": "30-45 Min pro Brief"
            },
            {
                "titel": "Skript-Outline erstellen",
                "prompt": """Erstellen Sie eine Skript-Outline:

Format: [Video/Podcast/Präsentation]
Länge: [MINUTEN]
Thema: [BESCHREIBUNG]
Ziel: [WAS soll der Zuschauer mitnehmen]

Struktur:
- Hook (erste 10 Sekunden)
- Intro
- Hauptteil (3-5 Punkte)
- Call-to-Action
- Outro""",
                "zeitersparnis": "30-45 Min pro Outline"
            }
        ],
        "lern_prompt": {
            "titel": "KI-generierte Inhalte verstehen & erklären",
            "thema": "welche Kennzeichnungspflichten der EU AI Act für KI-generierte Inhalte in Medien bringt",
            "zielgruppe": "Kunden",
            "prompt": """Erkläre mir, welche Kennzeichnungspflichten der EU AI Act für KI-generierte Inhalte in Medien bringt, so dass ich es einem Kunden ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },
    
    # -------------------------------------------------------------------------
    # 11. INDUSTRIE & PRODUKTION
    # -------------------------------------------------------------------------
    "industrie": {
        "name": "Industrie & Produktion",
        "erster_schritt": "Lassen Sie ChatGPT eine Arbeitsanweisung strukturieren",
        "zeitersparnis_pro_woche": 4,
        "typische_aufgaben": ["Arbeitsanweisungen", "Fehleranalysen", "Berichte"],
        "prompts": [
            {
                "titel": "Arbeitsanweisung erstellen",
                "prompt": """Erstellen Sie eine Arbeitsanweisung:

Tätigkeit: [BESCHREIBUNG]
Zielgruppe: [WER führt aus]
Sicherheitshinweise: [RELEVANTE]

Struktur:
1. Zweck & Geltungsbereich
2. Benötigte Materialien/Werkzeuge
3. Schritt-für-Schritt-Anleitung
4. Qualitätskriterien
5. Sicherheitshinweise
6. Dokumentation""",
                "zeitersparnis": "30-45 Min pro Anweisung"
            },
            {
                "titel": "Fehleranalyse (5-Why)",
                "prompt": """Führe eine 5-Why-Analyse durch:

Fehler/Problem: [BESCHREIBUNG]
Wann aufgetreten: [ZEITPUNKT]
Auswirkung: [WAS ist passiert]

Analysieren Sie:
1. Warum ist das passiert? → Antwort
2. Warum? (auf Antwort 1) → Antwort
3. Warum? (auf Antwort 2) → Antwort
4. Warum? (auf Antwort 3) → Antwort
5. Warum? (auf Antwort 4) → Grundursache

→ Maßnahmenvorschlag""",
                "zeitersparnis": "20-30 Min pro Analyse"
            },
            {
                "titel": "Schichtbericht erstellen",
                "prompt": """Erstellen Sie einen Schichtbericht:

Datum/Schicht: [INFO]
Notizen: [STICHPUNKTE]

Format:
- Produktionszahlen (Soll/Ist)
- Besondere Vorkommnisse
- Störungen/Stillstände
- Qualitätsabweichungen
- Übergabe an Folgeschicht
- Offene Punkte""",
                "zeitersparnis": "15-20 Min pro Bericht"
            }
        ],
        "lern_prompt": {
            "titel": "Predictive Maintenance verstehen & erklären",
            "thema": "wie KI-gestützte vorausschauende Wartung (Predictive Maintenance) ungeplante Stillstände reduziert",
            "zielgruppe": "Mitarbeitenden",
            "prompt": """Erkläre mir, wie KI-gestützte vorausschauende Wartung (Predictive Maintenance) ungeplante Stillstände reduziert, so dass ich es einem Mitarbeitenden ohne technischen Hintergrund in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },
    
    # -------------------------------------------------------------------------
    # 12. TRANSPORT & LOGISTIK
    # -------------------------------------------------------------------------
    "transport": {
        "name": "Transport & Logistik",
        "erster_schritt": "Lassen Sie ChatGPT Lieferverzögerungs-Mails formulieren",
        "zeitersparnis_pro_woche": 5,
        "typische_aufgaben": ["Kundeninfo", "Routenplanung", "Dokumentation"],
        "prompts": [
            {
                "titel": "Lieferverzögerung kommunizieren",
                "prompt": """Formulieren Sie eine Kundeninfo zu Lieferverzögerung:

Kunde: [TYP]
Ursprünglicher Termin: [DATUM]
Neuer Termin: [DATUM]
Grund: [KURZ]

Die Nachricht soll:
- Sich entschuldigen
- Den neuen Termin klar nennen
- Grund knapp erklären
- Kompensation anbieten (falls passend)
- Kontaktmöglichkeit geben""",
                "zeitersparnis": "10-15 Min pro Mail"
            },
            {
                "titel": "Frachtbrief-Daten prüfen",
                "prompt": """Prüfen Sie diese Frachtbrief-Daten auf Vollständigkeit:

[DATEN HIER EINFÜGEN]

Checkliste:
- Absender vollständig?
- Empfänger vollständig?
- Warenbeschreibung korrekt?
- Gewicht/Maße plausibel?
- Gefahrgut-Kennzeichnung (falls nötig)?
- Unterschriften vorhanden?""",
                "zeitersparnis": "5-10 Min pro Dokument"
            },
            {
                "titel": "Reklamationsantwort formulieren",
                "prompt": """Formulieren Sie eine Antwort auf diese Reklamation:

Beschwerde: [TEXT]
Sendungsdaten: [FALLS RELEVANT]
Unser Verschulden: [ja/nein/teilweise]

Die Antwort soll:
- Verständnis zeigen
- Sachverhalt klären
- Lösung/Kompensation anbieten
- Verbesserungsmaßnahme nennen""",
                "zeitersparnis": "15-20 Min pro Antwort"
            }
        ],
        "lern_prompt": {
            "titel": "KI-Routenoptimierung verstehen & erklären",
            "thema": "wie KI-gestützte Routenoptimierung Lieferzeiten und Kraftstoffkosten senkt",
            "zielgruppe": "Kunden",
            "prompt": """Erkläre mir, wie KI-gestützte Routenoptimierung Lieferzeiten und Kraftstoffkosten senkt, so dass ich es einem Kunden ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },

    # -------------------------------------------------------------------------
    # 13. GASTRONOMIE & TOURISMUS
    # -------------------------------------------------------------------------
    "gastronomie": {
        "name": "Gastronomie & Tourismus",
        "erster_schritt": "Lassen Sie ChatGPT Ihre Speisekarten-Texte aufwerten",
        "zeitersparnis_pro_woche": 4,
        "typische_aufgaben": ["Speisekarten", "Gästekommunikation", "Marketing"],
        "prompts": [
            {
                "titel": "Speisekarten-Text aufwerten",
                "prompt": """Formulieren Sie diese Gerichtbeschreibung appetitlich um:

Gericht: [NAME]
Zutaten: [LISTE]
Besonderheit: [z.B. regional, vegan, hausgemacht]

Die Beschreibung soll:
- Max. 25 Wörter
- Appetit machen
- Besonderheiten hervorheben
- Allergene-Hinweis (wo nötig)""",
                "zeitersparnis": "5-10 Min pro Gericht"
            },
            {
                "titel": "Gästebewertung beantworten",
                "prompt": """Beantworte diese Online-Bewertung:

Bewertung: [TEXT]
Sterne: [1-5]
Plattform: [Google/TripAdvisor/etc.]

Die Antwort soll:
- Persönlich sein (nicht Standard)
- Positives aufgreifen
- Bei Kritik: Verständnis + Verbesserung
- Zur Wiederkehr einladen""",
                "zeitersparnis": "10-15 Min pro Antwort"
            },
            {
                "titel": "Event-Angebot erstellen",
                "prompt": """Erstellen Sie ein Angebot für diese Veranstaltung:

Art: [z.B. Hochzeit, Firmenfeier, Geburtstag]
Personenzahl: [ANZAHL]
Budget-Rahmen: [FALLS BEKANNT]
Besondere Wünsche: [LISTE]

Das Angebot soll enthalten:
- Menüvorschlag (3 Gänge)
- Getränkepauschale-Optionen
- Raum/Dekoration
- Ablauf-Vorschlag
- Preis-Übersicht""",
                "zeitersparnis": "30-45 Min pro Angebot"
            }
        ],
        "lern_prompt": {
            "titel": "Dynamische Preisgestaltung verstehen & erklären",
            "thema": "wie dynamische Preisgestaltung in der Gastronomie funktioniert und wo die Grenzen liegen",
            "zielgruppe": "Team",
            "prompt": """Erkläre mir, wie dynamische Preisgestaltung in der Gastronomie funktioniert und wo die Grenzen liegen, so dass ich es meinem Team ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },

    # -------------------------------------------------------------------------
    # 14. RECHT & KANZLEI (FIX-S25-B1: New branch)
    # -------------------------------------------------------------------------
    "recht": {
        "name": "Recht & Kanzlei",
        "erster_schritt": "Lassen Sie ChatGPT einen Textbaustein für ein Standardschreiben formulieren",
        "zeitersparnis_pro_woche": 6,
        "typische_aufgaben": ["Textbausteine", "Recherche-Zusammenfassungen", "Mandantenkommunikation"],
        "prompts": [
            {
                "titel": "Textbaustein formulieren",
                "prompt": """Formulieren Sie einen juristischen Textbaustein:

Schreibentyp: [z.B. Abmahnung, Vertragsentwurf, Widerspruch]
Sachverhalt: [KURZBESCHREIBUNG]
Tonalität: [sachlich/bestimmt/kooperativ]

Der Textbaustein soll:
- Juristisch präzise formuliert sein
- Den Sachverhalt klar darstellen
- Rechtsgrundlagen referenzieren
- Handlungsaufforderung/Frist enthalten
- Als Vorlage wiederverwendbar sein""",
                "zeitersparnis": "30-45 Min pro Baustein"
            },
            {
                "titel": "Recherche-Zusammenfassung erstellen",
                "prompt": """Fassen Sie diese juristische Recherche zusammen:

Thema: [RECHTSFRAGE]
Gefundene Quellen: [STICHPUNKTE/URTEILE]
Relevanter Sachverhalt: [KONTEXT]

Liefern Sie:
1. Kernaussage in 2-3 Sätzen
2. Relevante Rechtsprechung (Aktenzeichen)
3. Pro/Contra-Argumente
4. Handlungsempfehlung
5. Offene Fragen""",
                "zeitersparnis": "1-2 Std pro Recherche"
            },
            {
                "titel": "Mandanten-Update schreiben",
                "prompt": """Schreiben Sie ein Mandanten-Update:

Mandant: [NAME/ROLLE]
Verfahren/Sache: [KURZBESCHREIBUNG]
Aktueller Stand: [STICHPUNKTE]
Nächste Schritte: [GEPLANT]

Das Update soll:
- Für juristische Laien verständlich sein
- Den aktuellen Stand klar darstellen
- Nächste Schritte und Fristen nennen
- Professionell aber nahbar formuliert sein""",
                "zeitersparnis": "15-20 Min pro Update"
            }
        ],
        "lern_prompt": {
            "titel": "Fristenmanagement verstehen & erklären",
            "thema": "wie KI-gestütztes Fristenmanagement Haftungsrisiken in der Kanzlei reduziert",
            "zielgruppe": "Mandanten",
            "prompt": """Erkläre mir, wie KI-gestütztes Fristenmanagement Haftungsrisiken in der Kanzlei reduziert, so dass ich es einem Mandanten ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    },

    # -------------------------------------------------------------------------
    # DEFAULT (Fallback für alle anderen)
    # -------------------------------------------------------------------------
    "default": {
        "name": "Allgemein",
        "erster_schritt": "Lassen Sie ChatGPT Ihre nächste E-Mail schreiben",
        "zeitersparnis_pro_woche": 4,
        "typische_aufgaben": ["E-Mails", "Zusammenfassungen", "Brainstorming"],
        "prompts": [
            {
                "titel": "E-Mail professionell formulieren",
                "prompt": """Formulieren Sie diese E-Mail professionell und klar:

Empfänger: [Rolle/Beziehung]
Anlass: [WARUM schreibe ich?]
Kernbotschaft: [WAS will ich?]
Gewünschte Reaktion: [WAS soll der Empfänger tun?]

Tonalität: [formell/freundlich-professionell]""",
                "zeitersparnis": "10-15 Min pro E-Mail"
            },
            {
                "titel": "Zusammenfassung erstellen",
                "prompt": """Fassen Sie diesen Text zusammen:

[TEXT HIER EINFÜGEN]

Liefern Sie:
1. Executive Summary (3 Sätze)
2. Kernpunkte (5 Bullet Points)
3. Handlungsempfehlung (falls relevant)""",
                "zeitersparnis": "15-30 Min pro Dokument"
            },
            {
                "titel": "Brainstorming-Partner",
                "prompt": """Hilf mir beim Brainstorming:

Thema/Problem: [BESCHREIBUNG]
Kontext: [HINTERGRUND]
Bisherige Ideen: [FALLS VORHANDEN]

Liefern Sie:
1. 10 kreative Ideen (auch unkonventionelle)
2. Pro/Contra für die Top 3
3. Empfehlung zum Starten""",
                "zeitersparnis": "30-45 Min pro Session"
            }
        ],
        "lern_prompt": {
            "titel": "KI-Chancen & Risiken verstehen & erklären",
            "thema": "die wichtigsten Chancen und Risiken von KI für kleine und mittlere Unternehmen",
            "zielgruppe": "Geschäftspartnern",
            "prompt": """Erkläre mir die wichtigsten Chancen und Risiken von KI für kleine und mittlere Unternehmen, so dass ich es einem Geschäftspartner ohne Fachwissen in 3 Sätzen erklären kann.

Strukturiere deine Antwort als:
1. Kernaussage (1 Satz)
2. Warum das wichtig ist (1 Satz)
3. Was sich dadurch ändert (1 Satz)

Zusätzlich: Gib mir 3 häufige Missverständnisse zu diesem Thema.""",
            "zeitersparnis": "15-20 Min"
        }
    }
}

# =============================================================================
# TOOL-EMPFEHLUNGEN
# =============================================================================

TOOL_EMPFEHLUNGEN = {
    "solo": [
        {
            "name": "ChatGPT Plus",
            "preis": "20 €/Monat",
            "url": "https://chat.openai.com",
            "nutzen": "Texte, Analysen, Brainstorming",
            "empfehlung": "Basis-Tool für den Einstieg"
        },
        {
            "name": "Perplexity Pro",
            "preis": "20 €/Monat",
            "url": "https://perplexity.ai",
            "nutzen": "Recherche mit Quellenangaben",
            "empfehlung": "Ideal für faktenbasierte Arbeit"
        }
    ],
    "team": [
        {
            "name": "ChatGPT Team",
            "preis": "25 €/Nutzer/Monat",
            "url": "https://chat.openai.com/team",
            "nutzen": "Gemeinsame Nutzung, Admin-Kontrolle",
            "empfehlung": "Für Teams bis 10 Personen"
        },
        {
            "name": "Notion AI",
            "preis": "10 €/Nutzer/Monat",
            "url": "https://notion.so",
            "nutzen": "Dokumentation & Wissensmanagement",
            "empfehlung": "Gut integriert in Workflows"
        }
    ],
    "kmu": [
        {
            "name": "Microsoft Copilot",
            "preis": "30 €/Nutzer/Monat",
            "url": "https://microsoft.com/copilot",
            "nutzen": "Office-Integration, Enterprise-ready",
            "empfehlung": "Wenn bereits Microsoft 365 im Einsatz"
        },
        {
            "name": "Claude Pro",
            "preis": "20 €/Monat",
            "url": "https://claude.ai",
            "nutzen": "Lange Dokumente, komplexe Analysen",
            "empfehlung": "Für anspruchsvolle Textarbeit"
        }
    ]
}

# =============================================================================
# KIS-1132: EXPERTISE-AWARE TOOL-EMPFEHLUNGEN
# =============================================================================
# beginner → uses TOOL_EMPFEHLUNGEN above (unchanged)
# intermediate/expert → use these upgraded recommendations

TOOL_EMPFEHLUNGEN_INTERMEDIATE = {
    "solo": [
        {
            "name": "Claude Pro / ChatGPT Plus",
            "preis": "20 €/Monat",
            "url": "https://claude.ai",
            "nutzen": "Lange Dokumente, komplexe Analysen, Brainstorming",
            "empfehlung": "Primäres Arbeitstool für strukturierte Aufgaben"
        },
        {
            "name": "Make (ehem. Integromat)",
            "preis": "ab 9 €/Monat",
            "url": "https://make.com",
            "nutzen": "Workflow-Automatisierung ohne Code",
            "empfehlung": "Verknüpft KI-Tools mit bestehenden Systemen"
        }
    ],
    "team": [
        {
            "name": "Claude Team / ChatGPT Team",
            "preis": "25-30 €/Nutzer/Monat",
            "url": "https://claude.ai",
            "nutzen": "Gemeinsame Nutzung, Prompt-Bibliotheken",
            "empfehlung": "Team-weite KI-Produktivität"
        },
        {
            "name": "Make / n8n",
            "preis": "ab 9 €/Monat",
            "url": "https://make.com",
            "nutzen": "Workflow-Automatisierung, API-Integrationen",
            "empfehlung": "Automatisiert wiederkehrende Team-Prozesse"
        }
    ],
    "kmu": [
        {
            "name": "Microsoft Copilot + Azure OpenAI",
            "preis": "30 €/Nutzer/Monat + API-Kosten",
            "url": "https://microsoft.com/copilot",
            "nutzen": "Office-Integration + eigene KI-Workflows",
            "empfehlung": "Enterprise-ready mit Datenschutz-Kontrolle"
        },
        {
            "name": "n8n / Make Enterprise",
            "preis": "ab 50 €/Monat",
            "url": "https://n8n.io",
            "nutzen": "Komplexe Automatisierungen, Self-hosted möglich",
            "empfehlung": "Skalierbare Workflow-Engine für KMU"
        }
    ]
}

TOOL_EMPFEHLUNGEN_EXPERT = {
    "solo": [
        {
            "name": "Anthropic / OpenAI API",
            "preis": "nutzungsbasiert (ab ~20 €/Monat)",
            "url": "https://console.anthropic.com",
            "nutzen": "Direkte API-Integration, volle Kontrolle",
            "empfehlung": "Für eigene Pipelines und Custom-Workflows"
        },
        {
            "name": "Langfuse (Monitoring)",
            "preis": "Open Source / ab 0 €",
            "url": "https://langfuse.com",
            "nutzen": "LLM-Observability, Prompt-Tracking, Kosten-Monitoring",
            "empfehlung": "Unverzichtbar für produktive LLM-Pipelines"
        }
    ],
    "team": [
        {
            "name": "Anthropic / OpenAI API + Gateway",
            "preis": "nutzungsbasiert",
            "url": "https://console.anthropic.com",
            "nutzen": "API-Zugang, zentrale Steuerung, Rate Limiting",
            "empfehlung": "Team-weite API-Nutzung mit Governance"
        },
        {
            "name": "Langfuse / Helicone",
            "preis": "Open Source / ab 0 €",
            "url": "https://langfuse.com",
            "nutzen": "Monitoring, Evaluierung, Cost-Tracking",
            "empfehlung": "Transparenz über LLM-Nutzung im Team"
        }
    ],
    "kmu": [
        {
            "name": "LLM-Gateway (LiteLLM / Portkey)",
            "preis": "Open Source / ab 99 €/Monat",
            "url": "https://litellm.ai",
            "nutzen": "Multi-Provider-Routing, Fallback, Cost Control",
            "empfehlung": "Zentrales API-Management für alle LLM-Aufrufe"
        },
        {
            "name": "Langfuse + Evaluierung",
            "preis": "Cloud oder Self-hosted",
            "url": "https://langfuse.com",
            "nutzen": "Monitoring, A/B-Testing, Prompt-Versionierung",
            "empfehlung": "Produktionsreife LLM-Operations"
        }
    ]
}

# =============================================================================
# WARNUNGEN / DON'Ts
# =============================================================================

WARNUNGEN = [
    {
        "icon": "🔒",
        "titel": "Keine sensiblen Daten",
        "text": "Geben Sie NIEMALS Kundendaten, Passwörter oder vertrauliche Zahlen in KI-Tools ein."
    },
    {
        "icon": "🔍",
        "titel": "Immer prüfen",
        "text": "Vertrauen Sie KI-generierten Zahlen und Fakten nicht blind – immer gegenchecken."
    },
    {
        "icon": "🎯",
        "titel": "Klein starten",
        "text": "Beginnen Sie mit einfachen Aufgaben, nicht mit dem komplexesten Projekt."
    }
]

# KIS-1132: Expertise-aware Warnungen
WARNUNGEN_INTERMEDIATE = [
    {
        "icon": "🔒",
        "titel": "Datenschutz bei Automatisierung",
        "text": "Bei Workflow-Automatisierung: Prüfen Sie, welche Daten über welche APIs fließen. DSGVO gilt auch für KI-Pipelines."
    },
    {
        "icon": "🔍",
        "titel": "Output-Qualität sichern",
        "text": "Automatisierte KI-Outputs brauchen Stichproben-Kontrolle. Definieren Sie Quality Gates für kritische Prozesse."
    },
    {
        "icon": "📋",
        "titel": "Prozesse dokumentieren",
        "text": "Dokumentieren Sie KI-gestützte Workflows, damit auch Kollegen sie nutzen und pflegen können."
    }
]

WARNUNGEN_EXPERT = [
    {
        "icon": "🔒",
        "titel": "API-Keys & Secrets Management",
        "text": "Keine API-Keys in Code oder Logs. Nutzen Sie Secret-Manager (Vault, AWS Secrets Manager) und rotieren Sie regelmäßig."
    },
    {
        "icon": "📊",
        "titel": "Kosten-Monitoring ist Pflicht",
        "text": "LLM-API-Kosten können exponentiell steigen. Setzen Sie Budgetlimits, Alerts und Cost-per-Request-Tracking von Tag 1."
    },
    {
        "icon": "⚖️",
        "titel": "AI Act Compliance beachten",
        "text": "Dokumentieren Sie Ihr KI-System gemäß EU AI Act: Zweckbestimmung, Risikoeinstufung, menschliche Aufsicht, Transparenzpflichten."
    }
]

# =============================================================================
# CHECKLISTE FÜR DEN START (Idee #9)
# =============================================================================

CHECKLISTE_START = [
    {"text": "ChatGPT oder Claude Account erstellen", "dauer": "5 Min"},
    {"text": "Ersten Prompt aus diesem Report testen", "dauer": "10 Min"},
    {"text": "Eine echte Arbeitsaufgabe mit KI lösen", "dauer": "30 Min"},
    {"text": "Ergebnis prüfen und anpassen", "dauer": "15 Min"},
    {"text": "Zeitersparnis notieren", "dauer": "5 Min"},
]

# KIS-1132: Expertise-aware Checklisten
CHECKLISTE_START_INTERMEDIATE = [
    {"text": "Wiederkehrenden Prozess identifizieren, der >1h/Woche kostet", "dauer": "15 Min"},
    {"text": "Strukturierten Prompt für diesen Prozess entwickeln", "dauer": "30 Min"},
    {"text": "Prompt mit 3 echten Beispielen testen und verfeinern", "dauer": "30 Min"},
    {"text": "Workflow-Automatisierung skizzieren (z.B. Make/n8n)", "dauer": "20 Min"},
    {"text": "Zeitersparnis pro Woche schätzen und dokumentieren", "dauer": "10 Min"},
]

CHECKLISTE_START_EXPERT = [
    {"text": "Bestehenden KI-Stack auf größten Engpass analysieren", "dauer": "30 Min"},
    {"text": "Messbares Optimierungsziel definieren (Latenz/Kosten/Qualität)", "dauer": "15 Min"},
    {"text": "Monitoring-Setup prüfen oder einrichten (Langfuse/Helicone)", "dauer": "30 Min"},
    {"text": "Prompt-Versionierung und Evaluierungsprozess dokumentieren", "dauer": "20 Min"},
    {"text": "Cost-per-Output-Baseline für Top-3-Use-Cases erfassen", "dauer": "20 Min"},
]

# =============================================================================
# KIS-1132: EXPERT/INTERMEDIATE COPY-PASTE PROMPTS
# =============================================================================
# These replace the branch-specific beginner prompts for higher expertise levels.

EXPERT_PROMPT_PATTERNS = [
    {
        "titel": "System-Prompt für konsistente Outputs",
        "prompt": """Sie sind ein erfahrener Experte für {fachgebiet}. Ihre Aufgabe ist es, [AUFGABE] auszuführen.

## Kontext
- Zielgruppe: [ZIELGRUPPE]
- Qualitätsstandard: [STANDARD]
- Bestehende Constraints: [EINSCHRÄNKUNGEN]

## Output-Anforderungen
- Format: [JSON/Markdown/Structured Text]
- Maximale Länge: [TOKENS/WÖRTER]
- Sprache: Deutsch, formell

## Evaluierungskriterien
1. Fachliche Korrektheit (Priorität 1)
2. Strukturierte Ausgabe (Priorität 2)
3. Handlungsrelevanz (Priorität 3)

Antworte NUR im definierten Format. Keine Einleitungen, keine Meta-Kommentare.""",
        "zeitersparnis": "Basis für alle Prompts"
    },
    {
        # KIS-1235: Lauf 1235 zeigte den Titel als "2. für komplexe Analysen" —
        # ein nachgelagerter Filter entfernte "Chain-of-Thought". Deutscher
        # Titel ist filterfest und für die Zielgruppe ohnehin verständlicher.
        "titel": "Schritt-für-Schritt-Denkanweisung für komplexe Analysen",
        "prompt": """Analysieren Sie folgendes Problem Schritt für Schritt:

Problem: [BESCHREIBUNG]
Kontext: {hauptleistung}

Schritt 1: Identifizieren Sie die 3 wichtigsten Einflussfaktoren.
Schritt 2: Bewerten Sie jeden Faktor auf einer Skala 1-5 (Impact × Wahrscheinlichkeit).
Schritt 3: Leiten Sie konkrete Handlungsempfehlungen ab.
Schritt 4: Priorisieren Sie nach Aufwand/Wirkung-Verhältnis.

Format: Strukturierte Tabelle mit Faktor | Bewertung | Empfehlung | Priorität""",
        "zeitersparnis": "Bessere Analyse-Qualität"
    },
    {
        "titel": "Few-Shot Pattern für konsistente Bewertungen",
        "prompt": """Sie bewerten [OBJEKT] nach folgenden Kriterien. Hier sind 2 Beispiele:

### Beispiel 1 (Bewertung: GUT)
Input: [BEISPIEL-INPUT-1]
Bewertung: [STRUKTURIERTE-BEWERTUNG-1]
Begründung: [BEGRÜNDUNG-1]

### Beispiel 2 (Bewertung: VERBESSERUNGSBEDARF)
Input: [BEISPIEL-INPUT-2]
Bewertung: [STRUKTURIERTE-BEWERTUNG-2]
Begründung: [BEGRÜNDUNG-2]

### Jetzt bewerten:
Input: [NEUER INPUT]

Bewerten Sie exakt im gleichen Format wie die Beispiele.""",
        "zeitersparnis": "Konsistente Ergebnisse"
    },
]

INTERMEDIATE_PROMPTS = [
    {
        "titel": "Prozess-Optimierung mit KI",
        "prompt": """Analysieren Sie folgenden Arbeitsprozess und identifizieren Sie KI-Automatisierungspotenzial:

Prozess: [BESCHREIBUNG DES PROZESSES]
Bereich: {hauptleistung}
Häufigkeit: [täglich/wöchentlich/monatlich]
Aktueller Zeitaufwand: [STUNDEN]

Liefern Sie:
1. Welche Teilschritte sind automatisierbar?
2. Welches KI-Tool eignet sich jeweils? (konkrete Namen)
3. Erwartete Zeitersparnis pro Durchlauf
4. Empfohlene Implementierungsreihenfolge
5. Mögliche Stolperfallen und wie man sie vermeidet""",
        "zeitersparnis": "1-2 Std Setup, dann fortlaufend"
    },
    {
        "titel": "Branchen-spezifische Vorlage erstellen",
        "prompt": """Erstellen Sie eine wiederverwendbare Vorlage für:

Aufgabe: [z.B. Kundenreport, Angebot, Analyse]
Branche: {hauptleistung}
Zielgruppe: [WER LIEST DAS?]

Die Vorlage soll enthalten:
1. Feste Strukturelemente (immer gleich)
2. Variable Platzhalter (pro Auftrag anpassen)
3. Qualitätskriterien zur Prüfung
4. Beispiel-Prompt, um die Vorlage mit KI zu befüllen

Ziel: 60-70% Zeitersparnis bei gleichbleibender Qualität.""",
        "zeitersparnis": "30-45 Min pro Vorlage"
    },
    {
        "titel": "KI-gestützte Recherche & Zusammenfassung",
        "prompt": """Recherchieren und fassen Sie zusammen:

Thema: [THEMA]
Kontext: {hauptleistung}
Tiefe: [Überblick / Detailanalyse / Entscheidungsgrundlage]

Anforderungen:
1. Aktuelle Entwicklungen (letzte 12 Monate)
2. Relevanz für mein Geschäftsfeld bewerten
3. 3 konkrete Handlungsempfehlungen ableiten
4. Quellen und weiterführende Ressourcen nennen

Format: Executive Summary (max. 500 Wörter) + Detail-Anhang""",
        "zeitersparnis": "1-2 Std pro Recherche"
    },
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_branche_key(branche: str) -> str:
    """Mappt Branche auf den passenden Key."""
    if not branche:
        return "default"
    
    branche_lower = branche.lower()
    
    # Mapping basierend auf den 15 Branchen
    # FIX-S25-FINAL-BRANCHE: Use word-boundary matching for short keywords
    # to prevent false positives (e.g., "pr" matching "Produktion",
    # "it" matching "gesundheit"). Keywords ≤3 chars use \b word boundary.
    import re

    mappings = {
        "marketing": ["marketing", "werbung", r"\bpr\b", "kommunikation"],
        "beratung": ["berat", "consult", "coach", "dienstleist"],
        "it": [r"\bit\b", r"\bit-", "software", "tech", "digital", r"\bweb\b", "entwickl"],
        "finanzen": ["finanz", "versicher", "bank", "invest"],
        "handel": ["handel", "shop", "commerce", "retail", "verkauf", "e-commerce"],
        "bildung": ["bildung", "schul", "training", "akadem", "lehr"],
        "verwaltung": ["verwalt", "behörd", "öffentlich", r"\bamt\b"],
        "gesundheit": ["gesundheit", "pflege", "medizin", "arzt", "klinik", "praxis"],
        "handwerk": ["handwerk", r"\bshk\b", "heizung", "sanitär", "elektro", "maler", "tischler", "schreiner", "dachdecker", "klempner", "schlosser", r"\bkfz\b", "werkstatt", "meister", "gewerk"],
        "bauwesen": [r"\bbau", "architekt", "immobil"],
        "medien": ["medien", "kreativ", "agentur", "design", "film", "foto"],
        "industrie": ["industrie", "produktion", "fertigung", "maschin", "herstellung"],
        "transport": ["transport", "logistik", "spedition", "versand", "lieferung"],
        "gastronomie": ["gastro", "hotel", "restaurant", "touris", "reise", "catering"],
        "recht": ["recht", "anwalt", "kanzlei", "jurist", "notar", "rechtsanwalt"],
    }

    for key, keywords in mappings.items():
        for kw in keywords:
            if kw.startswith(r"\b") or kw.endswith(r"\b"):
                # Regex word-boundary match for short/ambiguous keywords
                if re.search(kw, branche_lower):
                    return key
            else:
                # Simple substring match for longer, unambiguous keywords
                if kw in branche_lower:
                    return key
    
    return "default"


def calculate_yearly_savings(hours_per_week: int, hourly_rate: int = 80, company_size: str = "solo", canon_opex_monthly: float = 0) -> dict:
    """Berechnet Jahresersparnis (Idee #3 + #6).

    PLATIN+++ FIX 1.1/1.4: Uses canonical hourly rate and OPEX from single source of truth.
    FIX-GRAMMAR-T1: canon_opex_monthly overrides size-based OPEX when provided.
    """
    # PLATIN+++ FIX 1.1: Use canonical rate if default was passed
    if hourly_rate == 80:
        hourly_rate = _get_canonical_rate(company_size)

    hours_per_month = hours_per_week * 4
    hours_per_year = hours_per_week * 48  # 48 Arbeitswochen

    savings_per_month = hours_per_month * hourly_rate
    savings_per_year = hours_per_year * hourly_rate

    # PLATIN+++ FIX 1.4: Use canonical OPEX instead of hardcoded 240€
    # FIX-GRAMMAR-T1: Prefer explicit canonical OPEX over size-based default
    if canon_opex_monthly > 0:
        tool_costs_per_year = int(canon_opex_monthly * 12)
    else:
        tool_costs_per_year = _get_canonical_opex_yearly(company_size)
    net_savings = savings_per_year - tool_costs_per_year

    return {
        "hours_per_week": hours_per_week,
        "hours_per_month": hours_per_month,
        "hours_per_year": hours_per_year,
        "savings_per_month": savings_per_month,
        "savings_per_year": savings_per_year,
        "tool_costs": tool_costs_per_year,
        "net_savings": net_savings,
        "hourly_rate": hourly_rate
    }


# =============================================================================
# HTML GENERATORS
# =============================================================================

def generate_sofort_start_html(
    hauptleistung: str,
    branche: str,
    company_size: str = "solo",
    zeitersparnis_prioritaet: str = "",
    stundensatz: int = 0,
    canon_hours_month: float = 0,  # FIX-B732: CANON hours for consistency
    canon_opex_monthly: float = 0,  # FIX-GRAMMAR-T1: CANON OPEX for consistency
    expertise_level: str = "beginner",  # KIS-1132: competence-aware content
    ki_projekte: str = "",  # KIS-1132: existing AI projects for context
    medien_sparte: str = "",  # KIS-1247: sparten-aware Fallstudien-Auswahl
) -> str:
    """
    Generiert die SOFORT_START_HTML Section.

    PLATIN+++ FIX 1.1/1.2/1.4: Uses canonical rates and size-based time savings.
    KIS-1132: Expertise-aware content calibration.
    """

    branche_key = get_branche_key(branche)
    branche_data = BRANCHE_PROMPTS.get(branche_key, BRANCHE_PROMPTS["default"])

    # Company size normalisieren
    size_key = "solo"
    if company_size:
        size_lower = company_size.lower()
        if any(x in size_lower for x in ["team", "klein", "2-10", "2–10"]):
            size_key = "team"
        elif any(x in size_lower for x in ["kmu", "mittel", "11-100", "11–100", "100"]):
            size_key = "kmu"

    # KIS-1132: Select tools based on expertise level
    if expertise_level == "expert":
        tools = TOOL_EMPFEHLUNGEN_EXPERT.get(size_key, TOOL_EMPFEHLUNGEN_EXPERT["solo"])
    elif expertise_level == "intermediate":
        tools = TOOL_EMPFEHLUNGEN_INTERMEDIATE.get(size_key, TOOL_EMPFEHLUNGEN_INTERMEDIATE["solo"])
    else:
        tools = TOOL_EMPFEHLUNGEN.get(size_key, TOOL_EMPFEHLUNGEN["solo"])

    # PLATIN+++ FIX 1.1: Use canonical rate from single source of truth
    if stundensatz <= 0:
        stundensatz = _get_canonical_rate(company_size)

    # PLATIN+++ FIX 1.2: Calculate time savings based on BOTH branche AND company size
    branche_hours_per_week: int = cast(int, branche_data.get("zeitersparnis_pro_woche", 4))
    # Scale by company size: team gets ~1.5x, kmu gets ~2x the branche base
    size_multipliers = {"solo": 1.0, "team": 1.5, "kmu": 2.0}
    size_mult = size_multipliers.get(size_key, 1.0)
    hours_per_week = max(2, min(40, int(branche_hours_per_week * size_mult)))

    # Ensure monthly hours don't exceed canonical MAX_TIME_SAVINGS_BY_SIZE
    max_monthly = MAX_TIME_SAVINGS_BY_SIZE.get(size_key, 20)
    hours_per_month_raw = hours_per_week * 4
    if hours_per_month_raw > max_monthly:
        hours_per_week = max(1, max_monthly // 4)


    # FIX-B732-HOURS-SYNC: Override with CANON hours if provided
    # FIX-S25-HOURS: Use round() instead of int() to avoid precision loss
    # (15h/month ÷ 4 = 3.75 → int()=3 WRONG, round()=4 CORRECT)
    if canon_hours_month > 0:
        _b732_hours_week = max(1, round(canon_hours_month / 4.33))
        if _b732_hours_week != hours_per_week:
            hours_per_week = _b732_hours_week

    savings = calculate_yearly_savings(hours_per_week, stundensatz, company_size, canon_opex_monthly=canon_opex_monthly)

    # FIX-S25-HOURS: Override yearly hours with canonical value (month × 12)
    # to avoid weekly→yearly rounding drift (3h/wk × 48 = 144 ≠ 15h/mo × 12 = 180)
    # FIX-KIS-1192-ITEM-G: Auch hours_per_month auf Canonical syncen, sodass
    # Sofort-Start Hero-Box (R1 S.5) auf monatlicher Basis konsistent ist
    # (Display "15h pro Monat" / "180h pro Jahr" / "12.960€ Netto").
    if canon_hours_month > 0:
        canon_monthly = int(canon_hours_month)
        canon_yearly = int(canon_hours_month * 12)
        if savings["hours_per_month"] != canon_monthly:
            savings["hours_per_month"] = canon_monthly
            savings["savings_per_month"] = canon_monthly * savings["hourly_rate"]
        if savings["hours_per_year"] != canon_yearly:
            savings["hours_per_year"] = canon_yearly
            savings["savings_per_year"] = canon_yearly * savings["hourly_rate"]
            if savings.get("tool_costs", 0) > 0:
                savings["net_savings"] = savings["savings_per_year"] - savings["tool_costs"]
    
    # Personalisiere den ersten Schritt
    # FIX-EMPTY-PARENS: Strip hauptleistung and validate before using in parentheses.
    # If hauptleistung is whitespace-only or gets sanitized downstream, empty "()" remain.
    _hl_clean = (hauptleistung or "").strip()
    _ki_proj_clean = (ki_projekte or "").strip()

    # KIS-1132: Expertise-aware first step
    if expertise_level == "expert":
        if _ki_proj_clean:
            erster_schritt = (
                f"Analysieren Sie Ihren bestehenden KI-Stack ({_ki_proj_clean[:80]}) auf den "
                f"größten Engpass: Ist es Latenz, Kosten, Output-Qualität oder Governance? "
                f"Definieren Sie ein messbares Optimierungsziel für die nächsten 30 Tage."
            )
        else:
            erster_schritt = (
                f"Analysieren Sie Ihren bestehenden KI-Einsatz im Bereich "
                f"{_hl_clean or branche_data['name']} auf den größten Engpass: "
                f"Latenz, Kosten, Output-Qualität oder Governance? "
                f"Definieren Sie ein messbares Optimierungsziel für die nächsten 30 Tage."
            )
    elif expertise_level == "intermediate":
        erster_schritt = (
            f"Identifizieren Sie den zeitintensivsten wiederkehrenden Prozess in "
            f"{_hl_clean or 'Ihrem Arbeitsalltag'} und erstellen Sie einen strukturierten "
            f"Prompt, der diesen Prozess in 3 Schritte zerlegt. Testen Sie das Ergebnis "
            f"mit einem realen Beispiel."
        )
    else:
        # Beginner: original logic
        erster_schritt = str(branche_data["erster_schritt"])
        if _hl_clean:
            erster_schritt = (
                f"Testen Sie ChatGPT mit einer typischen Aufgabe aus Ihrem Bereich "
                f"({_hl_clean}). Nutzen Sie dafür die Copy-Paste Prompts auf der nächsten Seite."
            )
    
    # HTML generieren
    html = f'''
    <!-- ERSTER SCHRITT -->
    <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 12px; padding: 24px; margin-bottom: 24px; color: white;">
        <div style="display: flex; align-items: flex-start; gap: 16px;">
            <span style="font-size: 32px;">⚡</span>
            <div>
                <h3 style="font-size: 18px; font-weight: 700; margin: 0 0 8px 0; color: white;">
                    Der EINE erste Schritt – heute noch machbar
                </h3>
                <p style="font-size: 15px; margin: 0; opacity: 0.95; line-height: 1.5;">
                    {erster_schritt}
                </p>
            </div>
        </div>
    </div>
    
    <!-- ZEITERSPARNIS-RECHNUNG (Idee #3 + #6) -->
    <!-- FIX-KIS-1192-ITEM-G: Hero-Box auf monatliche Basis umgestellt.
         Vorher zeigte Wochen-Wert round(canon_hours_month/4.33) (z.B. 3h),
         aber Jahres-Wert canon_hours_month*12 (180h) — Mathematik stimmte
         nicht (3h*52=156h ≠ 180h). Monatlich bindet Sofort-Start visuell
         an Business Case S.9 (15h/Mo = Canonical). -->
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: #166534; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">💰</span>
            Ihre potenzielle Zeitersparnis
        </h3>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; text-align: center;">
            <div style="background: white; border-radius: 6px; padding: 12px;">
                <div style="font-size: 24px; font-weight: 700; color: #166534;">{savings['hours_per_month']}h</div>
                <div style="font-size: 11px; color: #64748b;">pro Monat</div>
            </div>
            <div style="background: white; border-radius: 6px; padding: 12px;">
                <div style="font-size: 24px; font-weight: 700; color: #166534;">{savings['hours_per_year']}h</div>
                <div style="font-size: 11px; color: #64748b;">pro Jahr</div>
            </div>
            <div style="background: white; border-radius: 6px; padding: 12px;">
                <div style="font-size: 24px; font-weight: 700; color: #166534;">{f"{savings['net_savings']:,}".replace(",", ".")}&nbsp;€</div>
                <div style="font-size: 11px; color: #64748b;">Netto-Ersparnis*</div>
            </div>
        </div>
        <p style="font-size: 10px; color: #64748b; margin: 8px 0 0 0; text-align: right;">
            *Bei {savings['hourly_rate']}&nbsp;€/h, abzgl. ~{f"{savings['tool_costs']:,}".replace(",", ".")}&nbsp;€ Tool-Kosten/Jahr
        </p>
    </div>
    
    <!-- PROMPTS SECTION – KIS-1132: expertise-aware -->
    <!-- KIS-1128 audit M3: outer page-break-inside:avoid wrapper removed —
         it kept H3 + intro + first prompt-box together, which on S.5/S.6
         pushed the whole block forward and left ~40% whitespace on S.5.
         Each prompt-box still has its own page-break-inside:avoid below. -->
    <div style="margin-bottom: 24px;">
'''

    # KIS-1132: Select prompts based on expertise level
    _hl_context_prefix = ""
    if _hl_clean:
        _hl_context_prefix = f"Kontext: Mein Unternehmen ist spezialisiert auf {_hl_clean}.\n\n"

    if expertise_level == "expert":
        # Expert: Prompt-Engineering-Patterns statt generische Prompts
        html += f'''
        <h3 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 24px;">🧠</span>
            Prompt-Engineering-Patterns für Ihr Technikpaket
        </h3>
        <p style="font-size: 13px; color: #64748b; margin: 0 0 16px 0;">
            Wiederverwendbare Patterns für konsistente, hochwertige LLM-Outputs:
        </p>
'''
        _expert_prompts = EXPERT_PROMPT_PATTERNS
        # KIS-1232: Kurzes Fachgebiet für den Experten-Slot — vorher wurde die
        # KOMPLETTE Hauptleistung (mehrere Sätze) in "…{X}-Experte" injiziert
        # und erzeugte kaputte Sätze wie "erfahrener Finanzberatung für
        # KMU.Das Unternehmen bietet …an.-Experte" (Status-Report S. 7).
        _fachgebiet = re.split(r'(?<=[a-zäöüß])[.!?]', _hl_clean, maxsplit=1)[0].strip() if _hl_clean else ""
        if not _fachgebiet or len(_fachgebiet) > 80:
            _fachgebiet = (_fachgebiet[:77].rsplit(" ", 1)[0] + "…") if len(_fachgebiet) > 80 else str(branche_data["name"])
        for i, prompt_data in enumerate(_expert_prompts, 1):
            _prompt_text = (
                prompt_data["prompt"]
                .replace("{fachgebiet}", _fachgebiet)
                .replace("{hauptleistung}", _hl_clean or str(branche_data["name"]))
            )
            html += f'''
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; page-break-inside: avoid;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <h4 style="font-size: 14px; font-weight: 600; margin: 0; color: #1e293b;">
                    {i}. {prompt_data["titel"]}
                </h4>
                <span style="font-size: 11px; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px; white-space: nowrap;">
                    {prompt_data["zeitersparnis"]}
                </span>
            </div>
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; font-family: monospace; font-size: 9pt; line-height: 1.5; white-space: pre-wrap; color: #334155;">
{_prompt_text}
            </div>
        </div>
'''

    elif expertise_level == "intermediate":
        # Intermediate: structured workflow prompts
        html += f'''
        <h3 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 24px;">📋</span>
            3 Workflow-Prompts für {branche_data["name"]}
        </h3>
        <p style="font-size: 13px; color: #64748b; margin: 0 0 16px 0;">
            Strukturierte Prompts für Workflow-Optimierung – kopieren und anpassen:
        </p>
'''
        _inter_prompts = INTERMEDIATE_PROMPTS
        for i, prompt_data in enumerate(_inter_prompts, 1):
            _prompt_text = prompt_data["prompt"].replace("{hauptleistung}", _hl_clean or str(branche_data["name"]))
            html += f'''
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; page-break-inside: avoid;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <h4 style="font-size: 14px; font-weight: 600; margin: 0; color: #1e293b;">
                    {i}. {prompt_data["titel"]}
                </h4>
                <span style="font-size: 11px; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px; white-space: nowrap;">
                    ⏱️ {prompt_data["zeitersparnis"]}
                </span>
            </div>
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; font-family: monospace; font-size: 9pt; line-height: 1.5; white-space: pre-wrap; color: #334155;">
{_prompt_text}
            </div>
        </div>
'''

    else:
        # Beginner: original branch-specific prompts (unchanged)
        html += f'''
        <h3 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 24px;">📋</span>
            4 Copy-Paste Prompts für {branche_data["name"]}
        </h3>
        <p style="font-size: 13px; color: #64748b; margin: 0 0 16px 0;">
            Kopieren Sie diese Prompts direkt in ChatGPT oder Claude:
        </p>
'''
        prompts_list: List[Dict[str, Any]] = cast(List[Dict[str, Any]], branche_data["prompts"])
        for i, prompt_data in enumerate(prompts_list, 1):
            _raw_prompt = _hl_context_prefix + prompt_data["prompt"] if _hl_context_prefix else prompt_data["prompt"]
            prompt_text = _raw_prompt
            html += f'''
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px; page-break-inside: avoid;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <h4 style="font-size: 14px; font-weight: 600; margin: 0; color: #1e293b;">
                    {i}. {prompt_data["titel"]}
                </h4>
                <span style="font-size: 11px; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px; white-space: nowrap;">
                    ⏱️ {prompt_data["zeitersparnis"]}
                </span>
            </div>
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; font-family: monospace; font-size: 9pt; line-height: 1.5; white-space: pre-wrap; color: #334155;">
{prompt_text}
            </div>
        </div>
'''
        # Lern-Prompt (beginner only)
        _lern_raw = branche_data.get("lern_prompt")
        lern_prompt: Dict[str, str] | None = cast(Dict[str, str], _lern_raw) if isinstance(_lern_raw, dict) else None
        if lern_prompt:
            _raw_lern = _hl_context_prefix + lern_prompt["prompt"] if _hl_context_prefix else lern_prompt["prompt"]
            lern_text = _raw_lern
            html += f'''
        <div style="background: #fffbeb; border: 1px solid #f59e0b; border-radius: 8px; padding: 16px; margin-bottom: 12px; page-break-inside: avoid;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <h4 style="font-size: 14px; font-weight: 600; margin: 0; color: #92400e;">
                    4. {lern_prompt["titel"]}
                    <span style="font-size: 10px; font-weight: 500; background: #fef3c7; color: #92400e; padding: 1px 6px; border-radius: 3px; margin-left: 6px; vertical-align: middle;">Lern-Prompt</span>
                </h4>
                <span style="font-size: 11px; background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 4px; white-space: nowrap;">
                    ⏱️ {lern_prompt["zeitersparnis"]}
                </span>
            </div>
            <div style="background: white; border: 1px solid #fde68a; border-radius: 6px; padding: 12px; font-family: monospace; font-size: 9pt; line-height: 1.5; white-space: pre-wrap; color: #334155;">
{lern_text}
            </div>
        </div>
'''

    html += '''
    </div>
'''

    # Tools hinzufügen
    html += '''
    <!-- TOOL-EMPFEHLUNGEN -->
    <div style="margin-bottom: 24px;">
        <h3 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 24px;">🛠️</span>
            Empfohlene Tools
        </h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
'''
    
    for tool in tools[:2]:
        html += f'''
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
                <h4 style="font-size: 15px; font-weight: 600; margin: 0 0 4px 0; color: #1e293b;">
                    {tool["name"]}
                </h4>
                <p style="font-size: 12px; color: #64748b; margin: 0 0 8px 0;">
                    {tool["nutzen"]}
                </p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px; font-weight: 600; color: #1e40af;">
                        {tool["preis"]}
                    </span>
                    <span style="font-size: 10px; color: #64748b;">
                        {tool["url"].replace("https://", "")}
                    </span>
                </div>
            </div>
'''
    
    html += '''
        </div>
    </div>
'''
    
    # KIS-1132: Expertise-aware Checkliste
    if expertise_level == "expert":
        _checkliste = CHECKLISTE_START_EXPERT
        _checkliste_title = "Ihr Optimierungs-Fahrplan (erste 2 Stunden)"
    elif expertise_level == "intermediate":
        _checkliste = CHECKLISTE_START_INTERMEDIATE
        _checkliste_title = "Ihr Workflow-Optimierungs-Plan (erste 90 Minuten)"
    else:
        _checkliste = CHECKLISTE_START
        _checkliste_title = "Ihre Start-Checkliste (erste 60 Minuten)"

    html += f'''
    <!-- CHECKLISTE -->
    <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: #1e40af; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">✅</span>
            {_checkliste_title}
        </h3>
        <div style="display: flex; flex-direction: column; gap: 6px;">
'''

    for item in _checkliste:
        html += f'''
            <div style="display: flex; align-items: center; gap: 8px; font-size: 13px;">
                <span style="width: 18px; height: 18px; border: 2px solid #3b82f6; border-radius: 4px; display: inline-block;"></span>
                <span style="flex: 1;">{item["text"]}</span>
                <span style="font-size: 11px; color: #64748b; background: white; padding: 2px 6px; border-radius: 4px;">{item["dauer"]}</span>
            </div>
'''

    html += '''
        </div>
    </div>
'''

    # KIS-1132: Expertise-aware Warnungen
    if expertise_level == "expert":
        _warnungen = WARNUNGEN_EXPERT
    elif expertise_level == "intermediate":
        _warnungen = WARNUNGEN_INTERMEDIATE
    else:
        _warnungen = WARNUNGEN

    html += '''
    <!-- WARNUNGEN -->
    <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 16px;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: #92400e; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">⚠️</span>
            Wichtig: Das sollten Sie NICHT tun
        </h3>
        <div style="display: flex; flex-direction: column; gap: 8px;">
'''

    for warnung in _warnungen:
        html += f'''
            <div style="display: flex; align-items: flex-start; gap: 8px;">
                <span style="font-size: 16px;">{warnung["icon"]}</span>
                <div>
                    <strong style="font-size: 13px; color: #92400e;">{warnung["titel"]}:</strong>
                    <span style="font-size: 13px; color: #78350f;"> {warnung["text"]}</span>
                </div>
            </div>
'''

    html += '''
        </div>
    </div>
'''
    
    
    
    # Branchen-Fallstudie (Idee #5) — KIS-1247: sparten-aware für Medien
    html += generate_fallstudie_html(branche, size_key, medien_sparte=medien_sparte)

    # Entscheidungsvorlage für Vorgesetzte (Idee #10) - nur für Team/KMU
    if size_key in ["team", "kmu"]:
        # FIX-KIS-1085: Pass canon_hours_month so the GF-Vorlage uses
        # the exact canonical monthly hours (not lossy weekly→monthly conversion)
        html += generate_entscheidungsvorlage_html(
            hauptleistung=hauptleistung,
            branche=str(branche_data["name"]),
            company_size=size_key,
            zeitersparnis_pro_woche=int(hours_per_week),
            stundensatz=stundensatz,
            canon_hours_month=canon_hours_month,
        )

    log.info(f"[SOFORT-START] Generated for branche={branche_key}, size={size_key}, hauptleistung={hauptleistung[:30] if hauptleistung else 'N/A'}...")
    
    return html


def generate_entscheidungsvorlage_html(
    hauptleistung: str,
    branche: str,
    company_size: str,
    zeitersparnis_pro_woche: int = 4,
    stundensatz: int = 0,
    canon_hours_month: float = 0,
) -> str:
    """No-op: GF-Vorlage is now injected via bypass in gpt_analyze.py (KIS-1094).

    Kept as empty stub so existing call sites don't break.
    """
    return ""


def build_gf_vorlage_html(
    hours: int,
    rate: int,
    opex_month: int,
    hauptleistung: str,
    capex: int = 0,
) -> str:
    """Deterministic template for GF-Entscheidungsvorlage.

    KIS-1093-A: Built from canonical values AFTER the full rendering pipeline.
    No LLM, no regex, no broken HTML possible.
    KIS-1238: capex erg\u00e4nzt \u2014 die Vorlage nannte nur Tool-Kosten
    (600 \u20ac/Monat), w\u00e4hrend der Business Case mit der vollen
    Startinvestition rechnet. Eine GF h\u00e4tte auf dieser Basis etwas
    anderes genehmigt als der Report kalkuliert (Lauf 1119, S. 6).
    """
    brutto = hours * rate * 12
    brutto_fmt = f"{brutto:,}".replace(",", ".")
    capex_li = ""
    if capex > 0:
        capex_fmt = f"{int(capex):,}".replace(",", ".")
        capex_li = (
            f"<li>Startinvestition (einmalig, \u00fcber 12 Monate verteilt): "
            f"ca. {capex_fmt}\u00a0\u20ac \u2014 Details im Business Case</li>\n                "
        )

    return f'''
    <div style="background: white; border: 2px solid #1e40af; border-radius: 8px; padding: 20px; margin-top: 24px;">
        <h3 style="font-size: 18px; font-weight: 700; margin: 0 0 16px 0; color: #1e40af; text-align: center;">
            \U0001f4c4 Entscheidungsvorlage: KI-Tools einführen
        </h3>
        <p style="font-size: 12px; color: #64748b; text-align: center; margin: 0 0 16px 0;">
            Diese Vorlage können Sie Ihrer Geschäftsführung vorlegen
        </p>

        <div style="border-top: 1px solid #e2e8f0; padding-top: 16px;">
            <h4 style="font-size: 14px; font-weight: 600; margin: 0 0 8px 0;">Antrag: Einführung von KI-Assistenz-Tools</h4>

            <p style="font-size: 13px; margin: 0 0 12px 0;">
                <strong>Bereich:</strong> {hauptleistung or "Allgemein"}<br>
                <strong>Beantragt von:</strong> [IHR NAME]<br>
                <strong>Datum:</strong> [DATUM]
            </p>

            <h4 style="font-size: 13px; font-weight: 600; margin: 16px 0 8px 0;">Erwarteter Nutzen:</h4>
            <ul style="font-size: 13px; margin: 0; padding-left: 20px;">
                <li>Zeitersparnis: {hours} Stunden/Monat</li>
                <li>Jährliche Brutto-Zeitersparnis: ca. {brutto_fmt}\u00a0\u20ac ({hours}h \u00d7 {rate}\u00a0\u20ac \u00d7 12)</li>
                <li>Qualitätssteigerung bei Routineaufgaben</li>
            </ul>

            <h4 style="font-size: 13px; font-weight: 600; margin: 16px 0 8px 0;">Investition:</h4>
            <ul style="font-size: 13px; margin: 0; padding-left: 20px;">
                {capex_li}<li>Laufende Tool-Kosten: ca. {opex_month}\u00a0\u20ac/Monat (Organisation gesamt)</li>
                <li>Einarbeitung: ca. 2-4 Stunden</li>
            </ul>

            <h4 style="font-size: 13px; font-weight: 600; margin: 16px 0 8px 0;">Risikominimierung:</h4>
            <ul style="font-size: 13px; margin: 0; padding-left: 20px;">
                <li>Keine sensiblen Daten in KI-Tools</li>
                <li>Alle Ergebnisse werden geprüft</li>
                <li>Testphase von 30 Tagen möglich</li>
            </ul>

            <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-between;">
                <div>
                    <p style="font-size: 11px; color: #64748b; margin: 0;">Unterschrift Antragsteller</p>
                    <div style="border-bottom: 1px solid #1e293b; width: 150px; margin-top: 24px;"></div>
                </div>
                <div>
                    <p style="font-size: 11px; color: #64748b; margin: 0;">Genehmigung</p>
                    <div style="border-bottom: 1px solid #1e293b; width: 150px; margin-top: 24px;"></div>
                </div>
            </div>
        </div>
    </div>
'''


# =============================================================================
# 30-TAGE CHALLENGE (Idee #8)
# =============================================================================

CHALLENGE_30_TAGE = {
    "woche_1": {
        "titel": "Erste Schritte",
        "ziel": "KI-Tools kennenlernen und erste Erfolge feiern",
        "tage": [
            {"tag": 1, "aufgabe": "ChatGPT oder Claude Account erstellen", "dauer": "10 Min", "kategorie": "Setup"},
            {"tag": 2, "aufgabe": "Ersten Prompt aus diesem Report testen", "dauer": "15 Min", "kategorie": "Praxis"},
            {"tag": 3, "aufgabe": "Eine echte E-Mail mit KI formulieren", "dauer": "20 Min", "kategorie": "Praxis"},
            {"tag": 4, "aufgabe": "Ergebnis mit manueller Version vergleichen", "dauer": "10 Min", "kategorie": "Reflexion"},
            {"tag": 5, "aufgabe": "Einen Text zusammenfassen lassen", "dauer": "15 Min", "kategorie": "Praxis"},
            {"tag": 6, "aufgabe": "Brainstorming zu einem aktuellen Thema", "dauer": "20 Min", "kategorie": "Praxis"},
            {"tag": 7, "aufgabe": "Woche 1 Review: Was hat Zeit gespart?", "dauer": "15 Min", "kategorie": "Reflexion"},
        ]
    },
    "woche_2": {
        "titel": "Routinen aufbauen",
        "ziel": "KI in tägliche Arbeitsabläufe integrieren",
        "tage": [
            {"tag": 8, "aufgabe": "Morgen-Routine: Tagesplanung mit KI besprechen", "dauer": "10 Min", "kategorie": "Routine"},
            {"tag": 9, "aufgabe": "Meeting-Vorbereitung mit KI-Unterstützung", "dauer": "20 Min", "kategorie": "Praxis"},
            {"tag": 10, "aufgabe": "Komplexe Kundenanfrage analysieren lassen", "dauer": "25 Min", "kategorie": "Praxis"},
            {"tag": 11, "aufgabe": "Eigene Prompt-Vorlage erstellen und speichern", "dauer": "20 Min", "kategorie": "Optimierung"},
            {"tag": 12, "aufgabe": "Dokument/Bericht strukturieren lassen", "dauer": "30 Min", "kategorie": "Praxis"},
            {"tag": 13, "aufgabe": "Feedback zu eigenem Text einholen", "dauer": "15 Min", "kategorie": "Praxis"},
            {"tag": 14, "aufgabe": "Woche 2 Review: Zeitersparnis dokumentieren", "dauer": "15 Min", "kategorie": "Reflexion"},
        ]
    },
    "woche_3": {
        "titel": "Effizienz steigern",
        "ziel": "Fortgeschrittene Techniken anwenden",
        "tage": [
            {"tag": 15, "aufgabe": "Mehrstufigen Prompt testen (Schritt für Schritt)", "dauer": "25 Min", "kategorie": "Fortgeschritten"},
            {"tag": 16, "aufgabe": "KI als Sparringspartner für Entscheidung nutzen", "dauer": "30 Min", "kategorie": "Praxis"},
            {"tag": 17, "aufgabe": "Prozess-Dokumentation erstellen lassen", "dauer": "30 Min", "kategorie": "Praxis"},
            {"tag": 18, "aufgabe": "Zweites KI-Tool testen (z.B. Perplexity)", "dauer": "20 Min", "kategorie": "Exploration"},
            {"tag": 19, "aufgabe": "Recherche-Aufgabe mit Quellenangaben", "dauer": "30 Min", "kategorie": "Praxis"},
            {"tag": 20, "aufgabe": "Präsentation/Pitch vorbereiten mit KI", "dauer": "40 Min", "kategorie": "Praxis"},
            {"tag": 21, "aufgabe": "Woche 3 Review: Beste Use Cases identifizieren", "dauer": "20 Min", "kategorie": "Reflexion"},
        ]
    },
    "woche_4": {
        "titel": "Workflow etablieren",
        "ziel": "Nachhaltige Integration in den Arbeitsalltag",
        "tage": [
            {"tag": 22, "aufgabe": "Persönliche Prompt-Bibliothek anlegen", "dauer": "30 Min", "kategorie": "Optimierung"},
            {"tag": 23, "aufgabe": "Kollegen einen Use Case zeigen", "dauer": "20 Min", "kategorie": "Sharing"},
            {"tag": 24, "aufgabe": "Komplexes Projekt mit KI-Unterstützung starten", "dauer": "45 Min", "kategorie": "Praxis"},
            {"tag": 25, "aufgabe": "Qualitätskontrolle: KI-Output kritisch prüfen", "dauer": "20 Min", "kategorie": "Qualität"},
            {"tag": 26, "aufgabe": "Workflow-Checkliste für wiederkehrende Aufgabe", "dauer": "25 Min", "kategorie": "Optimierung"},
            {"tag": 27, "aufgabe": "Alternative Formulierungen für gleiche Aufgabe testen", "dauer": "20 Min", "kategorie": "Fortgeschritten"},
            {"tag": 28, "aufgabe": "Team-Anwendungsfall identifizieren", "dauer": "25 Min", "kategorie": "Scaling"},
        ]
    },
    # KIS-1126 / C7 FIX: Days 29-30 moved to own section to prevent orphaned
    # grid cells (9 items in a 7-col grid → 2 isolated items after page break)
    "abschluss": {
        "titel": "Abschluss & Ausblick",
        "ziel": "Ergebnisse sichern und nächste Phase planen",
        "tage": [
            {"tag": 29, "aufgabe": "ROI der letzten 4 Wochen berechnen", "dauer": "20 Min", "kategorie": "Reflexion"},
            {"tag": 30, "aufgabe": "Nächste 30 Tage planen: Was wird Standard?", "dauer": "30 Min", "kategorie": "Planung"},
        ]
    }
}

# =============================================================================
# KIS-1142 Punkt 6 Variante C: Challenge-Wochen-Opt-in per company size
# =============================================================================
# Maps company_size → set of week-keys that should NOT be rendered. Empty
# sets act as no-ops. Populate when Wolf decides which week arcs feel
# out-of-scale for the target profile (e.g. governance-heavy weeks for
# solo freelancers). The filter runs AFTER challenge-variant selection
# (beginner/intermediate/expert), so solo-on-expert can still be trimmed.
#
# FIX-KIS-1192-ITEM-H: Solo woche_3/4-Skip wurde aufgehoben und durch
# Override (siehe _CHALLENGE_SOLO_WEEK_OVERRIDES) ersetzt. Vorher entstand
# auf R1 S.12 eine sichtbare Lücke (Tag 1-14 + Tag 29-30, nichts dazwischen)
# weil Abschluss-Block unverändert auf Tag 29/30 hängt.
_CHALLENGE_WEEKS_SKIP_BY_SIZE: Dict[str, set] = {
    "solo": set(),  # Solo-Override siehe _CHALLENGE_SOLO_WEEK_OVERRIDES
    "team": set(),
    "kmu":  set(),
}


# FIX-KIS-1192-ITEM-H: Solo-spezifische Woche 3+4 Inhalte für Intermediate/
# Expert-Solo-Berater. Ersetzt die ursprünglichen Enterprise-LLM-Ops-Wochen
# durch Vorlagen-Pflege, Mandanten-Automatisierung und Self-Marketing —
# realistischer Zuschnitt für einen Einzel-Berater. Wird in
# _filter_challenge_weeks_by_size() als Override angewandt.
_CHALLENGE_SOLO_WEEK_OVERRIDES: Dict[str, Dict[str, Any]] = {
    "woche_3": {
        "titel": "Vorlagen & Wiederverwendung",
        "ziel": "Eigene Prompt-Bibliothek und Mandanten-Templates aufbauen",
        "tage": [
            {"tag": 15, "aufgabe": "Top-10-Wiederkehrende Aufgaben aus Woche 1+2 dokumentieren", "dauer": "30 Min", "kategorie": "Reflexion"},
            {"tag": 16, "aufgabe": "Aus jeder Aufgabe einen wiederverwendbaren Prompt machen", "dauer": "45 Min", "kategorie": "Optimierung"},
            {"tag": 17, "aufgabe": "Prompt-Bibliothek in Notion/Obsidian/Markdown anlegen", "dauer": "30 Min", "kategorie": "Setup"},
            {"tag": 18, "aufgabe": "Mandanten-spezifische Templates (Angebot, Protokoll, Follow-up)", "dauer": "45 Min", "kategorie": "Praxis"},
            {"tag": 19, "aufgabe": "Versionierung der Templates etablieren (Git oder Cloud-Versionen)", "dauer": "30 Min", "kategorie": "Setup"},
            {"tag": 20, "aufgabe": "Test: Wie viel Zeit spart die Bibliothek pro Auftrag?", "dauer": "30 Min", "kategorie": "Reflexion"},
            {"tag": 21, "aufgabe": "Woche 3 Review: Top-3 Bibliotheks-Bausteine markieren", "dauer": "20 Min", "kategorie": "Reflexion"},
        ],
    },
    "woche_4": {
        "titel": "Mandanten-Onboarding & Self-Marketing",
        "ziel": "Kunden-Workflows automatisieren und Sichtbarkeit aufbauen",
        "tage": [
            {"tag": 22, "aufgabe": "Standard-Onboarding-Brief für neue Mandanten erstellen", "dauer": "45 Min", "kategorie": "Praxis"},
            {"tag": 23, "aufgabe": "KI-gestützte FAQ-Antworten für Stammkunden anlegen", "dauer": "30 Min", "kategorie": "Praxis"},
            {"tag": 24, "aufgabe": "LinkedIn/Newsletter-Posting-Bausteine vorbereiten", "dauer": "45 Min", "kategorie": "Sharing"},
            {"tag": 25, "aufgabe": "Case-Study aus eigenem Projekt mit KI-Hilfe ausformulieren", "dauer": "45 Min", "kategorie": "Praxis"},
            {"tag": 26, "aufgabe": "Backup-Strategie: Was tun, wenn KI-Dienst ausfällt?", "dauer": "30 Min", "kategorie": "Strategie"},
            {"tag": 27, "aufgabe": "Eigene KI-Honorar-Position formulieren (Beratungs-Angebot)", "dauer": "30 Min", "kategorie": "Strategie"},
            # KIS-1235: Quartals-/Saisonbezug dynamisch — "Q2-Ziel … bis Sommer"
            # stand im Juli-Report (Lauf 1235). Platzhalter wird beim Rendern
            # über _resolve_quarter_goal() ersetzt.
            {"tag": 28, "aufgabe": "__QUARTAL_ZIEL__", "dauer": "30 Min", "kategorie": "Planung"},
        ],
    },
}


def _filter_challenge_weeks_by_size(
    challenge_data: Dict[str, Any], company_size: str,
) -> Dict[str, Any]:
    """Drop week-keys flagged as out-of-scale; apply solo-specific overrides.

    Filter runs AFTER variant selection (beginner/intermediate/expert).
    For solo+intermediate/expert, woche_3/4 get overridden with
    solo-realistic content (Vorlagen-Bibliothek + Mandanten-Onboarding)
    instead of Enterprise-LLM-Ops (KIS-1192 Item H).
    """
    size_norm = (company_size or "").strip().lower()
    skip_keys = _CHALLENGE_WEEKS_SKIP_BY_SIZE.get(size_norm, set())

    # Apply skip first
    if skip_keys:
        challenge_data = {k: v for k, v in challenge_data.items() if k not in skip_keys}

    # Solo override for Intermediate/Expert (where week 3/4 are Enterprise-LLM-Ops)
    # Only triggers if the challenge variant actually has woche_3/woche_4 keys
    # (CHALLENGE_30_TAGE_EXPERT and _INTERMEDIATE do, CHALLENGE_30_TAGE/_LIGHT do not).
    if size_norm == "solo":
        has_expert_week_3 = "woche_3" in challenge_data and any(
            kw in (challenge_data["woche_3"].get("titel") or "").lower()
            for kw in ("optimierung", "ops", "skalierung")
        )
        has_expert_week_4 = "woche_4" in challenge_data and any(
            kw in (challenge_data["woche_4"].get("titel") or "").lower()
            for kw in ("optimierung", "ops", "skalierung")
        )
        if has_expert_week_3 or has_expert_week_4:
            result: Dict[str, Any] = {}
            for k, v in challenge_data.items():
                if k in _CHALLENGE_SOLO_WEEK_OVERRIDES and (
                    (k == "woche_3" and has_expert_week_3)
                    or (k == "woche_4" and has_expert_week_4)
                ):
                    result[k] = _CHALLENGE_SOLO_WEEK_OVERRIDES[k]
                else:
                    result[k] = v
            return result

    return challenge_data


# =============================================================================
# KIS-1142 Punkt 3: Drop-first-week helper for Intermediate/Expert
# =============================================================================
#
# The challenge dicts (CHALLENGE_30_TAGE, _INTERMEDIATE, _EXPERT, _LIGHT) all
# keep their tage numbered sequentially (1..30) so the beginner rendering
# reads as a true 30-day journey.  When we drop the first week for
# intermediate / expert users, the remaining weeks would otherwise start
# with "Tag 8" — confusing, since the template already bills it as
# "Challenge-Start".  ``_drop_first_week_and_renumber`` returns a shallow
# copy with the first ``woche_*`` entry removed and every remaining
# ``tag_data["tag"]`` renumbered from 1 upwards.  Source dict stays
# untouched (same defensive pattern as _filter_options_by_profile in
# routes/chat.py).


def _drop_first_week_and_renumber(challenge_data: Dict[str, Any]) -> Dict[str, Any]:
    """Drop the first ``woche_*`` entry and renumber the remaining days."""
    if not challenge_data:
        return challenge_data
    items = list(challenge_data.items())
    # Skip every leading entry whose key does not start with ``woche_`` — the
    # "abschluss" tail is a separator, not a week. If the dict is
    # abschluss-only (pathological), return as-is.
    first_week_idx = next(
        (i for i, (k, _) in enumerate(items) if k.startswith("woche_")),
        None,
    )
    if first_week_idx is None:
        return challenge_data
    trimmed = items[:first_week_idx] + items[first_week_idx + 1:]
    if not trimmed:
        return challenge_data
    result: Dict[str, Any] = {}
    day_counter = 1
    for key, week in trimmed:
        week_copy = dict(week)
        tage = week_copy.get("tage") or []
        new_tage: List[Dict[str, Any]] = []
        for tag in tage:
            tag_copy = dict(tag)
            tag_copy["tag"] = day_counter
            new_tage.append(tag_copy)
            day_counter += 1
        week_copy["tage"] = new_tage
        result[key] = week_copy
    return result


KATEGORIE_ICONS = {
    "Setup": "⚙️",
    "Praxis": "💪",
    "Reflexion": "🔍",
    "Routine": "🔄",
    "Optimierung": "⚡",
    "Fortgeschritten": "🚀",
    "Exploration": "🔬",
    "Sharing": "👥",
    "Qualität": "✅",
    "Scaling": "📈",
    "Planung": "📋",
    "Monitoring": "📊",
    "Governance": "⚖️",
    "Strategie": "🎯",
    "Analyse": "🔬",
}

# =============================================================================
# KIS-1132: EXPERT 30-TAGE CHALLENGE
# =============================================================================

CHALLENGE_30_TAGE_EXPERT = {
    "woche_1": {
        "titel": "Stack-Audit",
        "ziel": "Ist-Zustand erfassen: Kosten, Latenz, Qualität messen",
        "tage": [
            {"tag": 1, "aufgabe": "Alle LLM-API-Aufrufe inventarisieren", "dauer": "30 Min", "kategorie": "Analyse"},
            {"tag": 2, "aufgabe": "Cost-per-Request für Top-3-Use-Cases messen", "dauer": "45 Min", "kategorie": "Monitoring"},
            {"tag": 3, "aufgabe": "Durchschnittliche Latenz pro Endpoint erfassen", "dauer": "30 Min", "kategorie": "Monitoring"},
            {"tag": 4, "aufgabe": "Output-Qualität mit 10 Testfällen bewerten", "dauer": "45 Min", "kategorie": "Qualität"},
            {"tag": 5, "aufgabe": "Monitoring-Dashboard aufsetzen (Langfuse/Helicone)", "dauer": "60 Min", "kategorie": "Setup"},
            {"tag": 6, "aufgabe": "Baseline-Report erstellen: Kosten/Qualität/Latenz", "dauer": "30 Min", "kategorie": "Analyse"},
            {"tag": 7, "aufgabe": "Woche 1 Review: Top-3-Optimierungspotenziale priorisieren", "dauer": "20 Min", "kategorie": "Reflexion"},
        ]
    },
    "woche_2": {
        "titel": "Governance & Compliance",
        "ziel": "KI-Richtlinie erstellen, Prüfschritte definieren, Dokumentation",
        "tage": [
            {"tag": 8, "aufgabe": "KI-Nutzungsrichtlinie Entwurf (Scope, Rollen, Verantwortung)", "dauer": "45 Min", "kategorie": "Governance"},
            {"tag": 9, "aufgabe": "Datenklassifikation: Was darf in welches LLM?", "dauer": "30 Min", "kategorie": "Governance"},
            {"tag": 10, "aufgabe": "AI Act Risikoeinstufung für eigene Use Cases", "dauer": "45 Min", "kategorie": "Governance"},
            {"tag": 11, "aufgabe": "Quality Gates definieren: Wann ist LLM-Output produktionsreif?", "dauer": "30 Min", "kategorie": "Qualität"},
            {"tag": 12, "aufgabe": "Prompt-Versionierung einrichten (Git/Langfuse)", "dauer": "45 Min", "kategorie": "Optimierung"},
            {"tag": 13, "aufgabe": "Incident-Response-Plan für LLM-Fehler erstellen", "dauer": "30 Min", "kategorie": "Governance"},
            {"tag": 14, "aufgabe": "Woche 2 Review: Governance-Dokumente finalisieren", "dauer": "20 Min", "kategorie": "Reflexion"},
        ]
    },
    "woche_3": {
        "titel": "Optimierung",
        "ziel": "Prompt-Engineering, Caching, Cost-per-Output optimieren",
        "tage": [
            {"tag": 15, "aufgabe": "Top-Prompt mit A/B-Varianten testen", "dauer": "45 Min", "kategorie": "Optimierung"},
            {"tag": 16, "aufgabe": "Semantic Caching für häufige Anfragen evaluieren", "dauer": "30 Min", "kategorie": "Optimierung"},
            {"tag": 17, "aufgabe": "Model-Routing: Günstigeres Modell für einfache Tasks", "dauer": "45 Min", "kategorie": "Optimierung"},
            {"tag": 18, "aufgabe": "Prompt-Kompression testen (Kosten vs. Qualität)", "dauer": "30 Min", "kategorie": "Optimierung"},
            {"tag": 19, "aufgabe": "Evaluierungs-Suite mit 20+ Testfällen aufbauen", "dauer": "60 Min", "kategorie": "Qualität"},
            {"tag": 20, "aufgabe": "Cost-per-Output nach Optimierung messen (Delta)", "dauer": "30 Min", "kategorie": "Monitoring"},
            {"tag": 21, "aufgabe": "Woche 3 Review: ROI der Optimierungen berechnen", "dauer": "20 Min", "kategorie": "Reflexion"},
        ]
    },
    "woche_4": {
        "titel": "Skalierung",
        "ziel": "Monitoring, Error-Handling, Fallback-Strategien, Team-Rollout",
        "tage": [
            {"tag": 22, "aufgabe": "Fallback-Strategie definieren (Provider B, Cached Response)", "dauer": "30 Min", "kategorie": "Strategie"},
            {"tag": 23, "aufgabe": "Rate-Limiting und Budget-Alerts konfigurieren", "dauer": "30 Min", "kategorie": "Monitoring"},
            {"tag": 24, "aufgabe": "Error-Handling und Retry-Logik überprüfen", "dauer": "45 Min", "kategorie": "Optimierung"},
            {"tag": 25, "aufgabe": "Team-Dokumentation: Onboarding-Guide für LLM-Nutzung", "dauer": "45 Min", "kategorie": "Sharing"},
            {"tag": 26, "aufgabe": "Compliance-Check: Alle Dokumentationspflichten erfüllt?", "dauer": "30 Min", "kategorie": "Governance"},
            {"tag": 27, "aufgabe": "Nächste 3 Use Cases für LLM-Integration identifizieren", "dauer": "30 Min", "kategorie": "Strategie"},
            {"tag": 28, "aufgabe": "Team-Präsentation: Ergebnisse und Learnings teilen", "dauer": "45 Min", "kategorie": "Sharing"},
        ]
    },
    "abschluss": {
        "titel": "Abschluss & Skalierungs-Roadmap",
        "ziel": "Ergebnisse sichern und Q2-Roadmap planen",
        "tage": [
            {"tag": 29, "aufgabe": "Kosten-Qualität-Delta vs. Baseline dokumentieren", "dauer": "30 Min", "kategorie": "Reflexion"},
            {"tag": 30, "aufgabe": "90-Tage-Roadmap für LLM-Skalierung erstellen", "dauer": "45 Min", "kategorie": "Planung"},
        ]
    }
}

CHALLENGE_30_TAGE_INTERMEDIATE = {
    "woche_1": {
        "titel": "Workflow-Analyse",
        "ziel": "Zeitfresser identifizieren und erste KI-Workflows aufsetzen",
        "tage": [
            {"tag": 1, "aufgabe": "Top-5-Zeitfresser in Ihrem Arbeitstag auflisten", "dauer": "15 Min", "kategorie": "Analyse"},
            {"tag": 2, "aufgabe": "Für #1 Zeitfresser: Strukturierten Prompt entwickeln", "dauer": "25 Min", "kategorie": "Praxis"},
            {"tag": 3, "aufgabe": "Prompt mit 3 realen Beispielen testen und verfeinern", "dauer": "25 Min", "kategorie": "Praxis"},
            {"tag": 4, "aufgabe": "Für #2 Zeitfresser: Prompt entwickeln und testen", "dauer": "30 Min", "kategorie": "Praxis"},
            {"tag": 5, "aufgabe": "Mehrstufigen Prompt testen (Schritt-für-Schritt-Anleitung)", "dauer": "25 Min", "kategorie": "Fortgeschritten"},
            {"tag": 6, "aufgabe": "Prompt-Vorlage für Ihren häufigsten Use Case speichern", "dauer": "15 Min", "kategorie": "Optimierung"},
            {"tag": 7, "aufgabe": "Woche 1 Review: Welcher Prompt spart am meisten Zeit?", "dauer": "15 Min", "kategorie": "Reflexion"},
        ]
    },
    "woche_2": {
        "titel": "Automatisierung",
        "ziel": "Wiederkehrende Aufgaben mit KI-Workflows automatisieren",
        "tage": [
            {"tag": 8, "aufgabe": "Make/n8n Account erstellen und ersten Workflow anlegen", "dauer": "30 Min", "kategorie": "Setup"},
            {"tag": 9, "aufgabe": "E-Mail-zu-Zusammenfassung-Workflow aufsetzen", "dauer": "30 Min", "kategorie": "Praxis"},
            {"tag": 10, "aufgabe": "Dokument-Analyse-Workflow mit KI-Unterstützung", "dauer": "30 Min", "kategorie": "Praxis"},
            {"tag": 11, "aufgabe": "Qualitätskriterien für automatische Outputs definieren", "dauer": "20 Min", "kategorie": "Qualität"},
            {"tag": 12, "aufgabe": "Zweites KI-Tool evaluieren (Claude/Perplexity/Spezialtool)", "dauer": "25 Min", "kategorie": "Exploration"},
            {"tag": 13, "aufgabe": "Prompt-Bibliothek mit Top-5-Prompts anlegen", "dauer": "20 Min", "kategorie": "Optimierung"},
            {"tag": 14, "aufgabe": "Woche 2 Review: Zeitersparnis pro Workflow dokumentieren", "dauer": "15 Min", "kategorie": "Reflexion"},
        ]
    },
    "woche_3": {
        "titel": "Vertiefung & Qualität",
        "ziel": "Fortgeschrittene Techniken, Qualitätssicherung",
        "tage": [
            {"tag": 15, "aufgabe": "System-Prompts für konsistente Ergebnisse einrichten", "dauer": "30 Min", "kategorie": "Fortgeschritten"},
            {"tag": 16, "aufgabe": "KI als Sparringspartner für Entscheidungsfindung nutzen", "dauer": "30 Min", "kategorie": "Praxis"},
            {"tag": 17, "aufgabe": "Branchen-spezifisches Template mit KI erstellen", "dauer": "30 Min", "kategorie": "Praxis"},
            {"tag": 18, "aufgabe": "Qualitäts-Checkliste: Wann ist KI-Output verwendbar?", "dauer": "20 Min", "kategorie": "Qualität"},
            {"tag": 19, "aufgabe": "Workflow-Integration: KI-Tool an bestehendes System anbinden", "dauer": "45 Min", "kategorie": "Fortgeschritten"},
            {"tag": 20, "aufgabe": "Kolleg:innen einweisen: Bester Use Case demonstrieren", "dauer": "30 Min", "kategorie": "Sharing"},
            {"tag": 21, "aufgabe": "Woche 3 Review: Top-3-Use-Cases nach ROI ranken", "dauer": "20 Min", "kategorie": "Reflexion"},
        ]
    },
    "woche_4": {
        "titel": "Skalierung & Standardisierung",
        "ziel": "Workflows standardisieren, Team einbeziehen, nächste Schritte",
        "tage": [
            {"tag": 22, "aufgabe": "Standard-Prompts dokumentieren und mit Team teilen", "dauer": "25 Min", "kategorie": "Sharing"},
            {"tag": 23, "aufgabe": "Einfache KI-Nutzungsregeln aufschreiben (Do's & Don'ts)", "dauer": "20 Min", "kategorie": "Governance"},
            {"tag": 24, "aufgabe": "Komplexeres Projekt mit KI-Workflow durchführen", "dauer": "45 Min", "kategorie": "Praxis"},
            {"tag": 25, "aufgabe": "Feedback-Loop: Output-Qualität systematisch verbessern", "dauer": "25 Min", "kategorie": "Optimierung"},
            {"tag": 26, "aufgabe": "Tool-Stack evaluieren: Was behalten, was ersetzen?", "dauer": "20 Min", "kategorie": "Analyse"},
            {"tag": 27, "aufgabe": "Automatisierungs-Roadmap für nächste 3 Monate", "dauer": "30 Min", "kategorie": "Planung"},
            {"tag": 28, "aufgabe": "Budgetplanung: Tools + Zeitinvest für nächstes Quartal", "dauer": "20 Min", "kategorie": "Planung"},
        ]
    },
    "abschluss": {
        "titel": "Abschluss & Nächste Phase",
        "ziel": "Ergebnisse sichern und Ausbau planen",
        "tage": [
            {"tag": 29, "aufgabe": "ROI berechnen: Zeitersparnis × Stundensatz", "dauer": "20 Min", "kategorie": "Reflexion"},
            {"tag": 30, "aufgabe": "Nächste 30 Tage planen: Welche Workflows werden Standard?", "dauer": "30 Min", "kategorie": "Planung"},
        ]
    }
}


def generate_30_tage_challenge_html(company_size: str = "solo") -> str:
    """
    Generiert die 30-Tage Challenge als HTML.
    """
    
    html = '''
    <!-- M1-FIX: page-break-before entfernt — #challenge-section hat break-before:page in CSS -->

    <!-- 30-TAGE CHALLENGE HEADER -->
    <div style="text-align: center; margin-bottom: 24px; padding-top: 20px;">
        <h2 style="font-size: 28px; font-weight: 700; margin: 0 0 8px 0; color: #1e40af;">
            🏆 Ihre 30-Tage KI-Challenge
        </h2>
        <p style="font-size: 16px; color: #64748b; margin: 0;">
            Von Null auf KI-Profi in 4 Wochen – mit täglichen Micro-Tasks
        </p>
    </div>
    
    <!-- ÜBERSICHT -->
    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 24px;">
'''

    # Wochen-Übersicht
    # KIS-1126 / C7 FIX: 5 sections (4 weeks + Abschluss) with matching colors
    wochen_farben = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"]
    wochen_labels = ["Woche 1", "Woche 2", "Woche 3", "Woche 4", "Abschluss"]
    for i, (woche_key, woche_data) in enumerate(CHALLENGE_30_TAGE.items()):
        farbe = wochen_farben[i]
        label = wochen_labels[i]
        html += f'''
        <div style="background: {farbe}15; border: 2px solid {farbe}; border-radius: 8px; padding: 10px; text-align: center;">
            <div style="font-size: 11px; font-weight: 600; color: {farbe}; text-transform: uppercase;">{label}</div>
            <div style="font-size: 13px; font-weight: 700; color: #1e293b; margin: 4px 0;">{woche_data["titel"]}</div>
            <div style="font-size: 10px; color: #64748b;">{woche_data["ziel"]}</div>
        </div>
'''

    html += '''
    </div>
'''

    # Detaillierte Wochen
    for i, (woche_key, woche_data) in enumerate(CHALLENGE_30_TAGE.items()):
        farbe = wochen_farben[i]
        label = wochen_labels[i]
        tage_list: List[Dict[str, Any]] = cast(List[Dict[str, Any]], woche_data["tage"])
        # KIS-1126 / C7: Adapt grid columns to number of days in section
        grid_cols = min(len(tage_list), 7)
        html += f'''
    <!-- {label.upper()} -->
    <div style="margin-bottom: 20px;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: {farbe}; display: flex; align-items: center; gap: 8px;">
            <span style="background: {farbe}; color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 14px;">{i+1}</span>
            {label}: {woche_data["titel"]}
        </h3>
        <div style="display: grid; grid-template-columns: repeat({grid_cols}, 1fr); gap: 6px;">
'''

        for tag_data in tage_list:
            icon = KATEGORIE_ICONS.get(str(tag_data.get("kategorie", "")), "📌")
            html += f'''
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; font-size: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="font-weight: 700; color: {farbe};">Tag {tag_data.get("tag", "")}</span>
                    <span>{icon}</span>
                </div>
                <div style="color: #334155; line-height: 1.3; min-height: 36px;">{tag_data.get("aufgabe", "")}</div>
                <div style="color: #94a3b8; font-size: 9px; margin-top: 4px;">⏱️ {tag_data.get("dauer", "")}</div>
            </div>
'''

        html += '''
        </div>
    </div>
'''
    
    # Tracking-Bereich
    # L3: Added break-inside:avoid to prevent orphan micro-pages
    html += '''
    <!-- ERFOLGS-TRACKING -->
    <!-- L3: break-inside:avoid prevents orphan micro-page on page 6 -->
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 8px; padding: 16px; margin-top: 20px; break-inside: avoid; page-break-inside: avoid;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: #166534;">
            📊 Ihr Erfolgs-Tracking
        </h3>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
            <div style="text-align: center;">
                <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Woche 1</div>
                <div style="border: 2px solid #22c55e; border-radius: 8px; padding: 12px; background: white;">
                    <div style="font-size: 10px; color: #64748b;">Gesparte Zeit:</div>
                    <div style="font-size: 16px; font-weight: 700; color: #166534;">_____ h</div>
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Woche 2</div>
                <div style="border: 2px solid #22c55e; border-radius: 8px; padding: 12px; background: white;">
                    <div style="font-size: 10px; color: #64748b;">Gesparte Zeit:</div>
                    <div style="font-size: 16px; font-weight: 700; color: #166534;">_____ h</div>
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Woche 3</div>
                <div style="border: 2px solid #22c55e; border-radius: 8px; padding: 12px; background: white;">
                    <div style="font-size: 10px; color: #64748b;">Gesparte Zeit:</div>
                    <div style="font-size: 16px; font-weight: 700; color: #166534;">_____ h</div>
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Woche 4</div>
                <div style="border: 2px solid #22c55e; border-radius: 8px; padding: 12px; background: white;">
                    <div style="font-size: 10px; color: #64748b;">Gesparte Zeit:</div>
                    <div style="font-size: 16px; font-weight: 700; color: #166534;">_____ h</div>
                </div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 12px; padding-top: 12px; border-top: 1px solid #22c55e;">
            <span style="font-size: 14px; color: #166534; font-weight: 600;">
                🎯 Gesamt nach 30 Tagen: _______ Stunden = _______ € gespart
            </span>
        </div>
    </div>
    
    <!-- TIPPS -->
    <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 12px; margin-top: 16px;">
        <h4 style="font-size: 13px; font-weight: 600; margin: 0 0 8px 0; color: #1e40af;">💡 Tipps für Ihren Erfolg</h4>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 11px; color: #334155;">
            <div>✓ Feste Zeit im Kalender blocken</div>
            <div>✓ Erfolge sofort notieren</div>
            <div>✓ Bei Problemen: einfacher Prompt</div>
            <div>✓ Nicht perfekt sein müssen</div>
            <div>✓ Wochenreview ernst nehmen</div>
            <div>✓ Mit Kollegen austauschen</div>
        </div>
    </div>
'''

    # KIS-1235: dynamischer Quartalsbezug (falls Platzhalter im Datensatz)
    html = html.replace("__QUARTAL_ZIEL__", _resolve_quarter_goal())

    return html


# =============================================================================
# ZEITBUDGET-ANGEPASSTE 30-TAGE CHALLENGE
# =============================================================================

ZEITBUDGET_CONFIG = {
    "unter_2": {
        "label": "Unter 2 Stunden/Woche",
        "minuten_pro_tag": 15,
        "intensitaet": "light",
        "empfehlung": "Fokussieren Sie sich auf die wichtigsten Tage (markiert mit ⭐)"
    },
    "2_5": {
        "label": "2–5 Stunden/Woche",
        "minuten_pro_tag": 30,
        "intensitaet": "moderate",
        "empfehlung": "Perfektes Tempo für nachhaltiges Lernen"
    },
    "5_10": {
        "label": "5–10 Stunden/Woche",
        "minuten_pro_tag": 60,
        "intensitaet": "intensive",
        "empfehlung": "Sie können alle Aufgaben plus Bonus-Challenges machen"
    },
    "ueber_10": {
        "label": "Über 10 Stunden/Woche",
        "minuten_pro_tag": 90,
        "intensitaet": "full",
        "empfehlung": "Maximales Lerntempo – ideal für schnelle Transformation"
    }
}

# Angepasste Challenges je nach Zeitbudget
CHALLENGE_LIGHT = {
    "woche_1": {
        "titel": "Erste Schritte",
        "tage": [
            {"tag": 1, "aufgabe": "Account erstellen", "dauer": "10 Min", "prio": True},
            {"tag": 2, "aufgabe": "Ersten Prompt testen", "dauer": "15 Min", "prio": True},
            {"tag": 3, "aufgabe": "E-Mail formulieren lassen", "dauer": "15 Min", "prio": False},
            {"tag": 4, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 5, "aufgabe": "Text zusammenfassen", "dauer": "10 Min", "prio": True},
            {"tag": 6, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 7, "aufgabe": "Wochenreview", "dauer": "10 Min", "prio": True},
        ]
    },
    "woche_2": {
        "titel": "Anwenden",
        "tage": [
            {"tag": 8, "aufgabe": "Echte Aufgabe mit KI lösen", "dauer": "15 Min", "prio": True},
            {"tag": 9, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 10, "aufgabe": "Prompt speichern", "dauer": "10 Min", "prio": True},
            {"tag": 11, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 12, "aufgabe": "Zweiten Use Case testen", "dauer": "15 Min", "prio": True},
            {"tag": 13, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 14, "aufgabe": "Wochenreview + Zeitersparnis", "dauer": "10 Min", "prio": True},
        ]
    },
    "woche_3": {
        "titel": "Vertiefen",
        "tage": [
            {"tag": 15, "aufgabe": "Mehrstufiger Prompt", "dauer": "15 Min", "prio": True},
            {"tag": 16, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 17, "aufgabe": "Routine etablieren", "dauer": "15 Min", "prio": True},
            {"tag": 18, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 19, "aufgabe": "Dritten Use Case", "dauer": "15 Min", "prio": True},
            {"tag": 20, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 21, "aufgabe": "Wochenreview", "dauer": "10 Min", "prio": True},
        ]
    },
    "woche_4": {
        "titel": "Festigen",
        "tage": [
            {"tag": 22, "aufgabe": "Prompt-Bibliothek anlegen", "dauer": "15 Min", "prio": True},
            {"tag": 23, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 24, "aufgabe": "Kollegen zeigen", "dauer": "15 Min", "prio": False},
            {"tag": 25, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 26, "aufgabe": "Standard-Workflow definieren", "dauer": "15 Min", "prio": True},
            {"tag": 27, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
            {"tag": 28, "aufgabe": "Pause / Nachholen", "dauer": "-", "prio": False},
        ]
    },
    # KIS-1126 / C7 FIX: Days 29-30 as own section (matches CHALLENGE_30_TAGE structure)
    "abschluss": {
        "titel": "Abschluss & Ausblick",
        "tage": [
            {"tag": 29, "aufgabe": "Gesamt-ROI berechnen", "dauer": "15 Min", "prio": True},
            {"tag": 30, "aufgabe": "Nächste Schritte planen", "dauer": "15 Min", "prio": True},
        ]
    }
}


def generate_30_tage_challenge_html_v2(
    company_size: str = "solo",
    zeitbudget: str = "2_5",
    expertise_level: str = "beginner",  # KIS-1132
    hauptleistung: str = "",  # KIS-1132
    hours_per_week: float = 0.0,  # KIS-1134-FX-2: Prognose-Werte
    stundensatz: float = 0.0,  # KIS-1134-FX-2: Für €-Berechnung
) -> str:
    """
    Generiert die 30-Tage Challenge angepasst ans Zeitbudget und Kompetenz-Level.

    Args:
        company_size: solo/team/kmu
        zeitbudget: unter_2/2_5/5_10/ueber_10
        expertise_level: beginner/intermediate/expert (KIS-1132)
        hauptleistung: Core business description (KIS-1132)
        hours_per_week: Geschätzte Zeitersparnis pro Woche (KIS-1134-FX-2)
        stundensatz: Stundensatz in EUR (KIS-1134-FX-2)
    """

    # Zeitbudget-Config holen
    zeit_config = ZEITBUDGET_CONFIG.get(zeitbudget, ZEITBUDGET_CONFIG["2_5"])

    # KIS-1132: Challenge-Daten basierend auf Expertise UND Intensität wählen
    show_prio = False
    if expertise_level == "expert":
        challenge_data = CHALLENGE_30_TAGE_EXPERT
    elif expertise_level == "intermediate":
        challenge_data = CHALLENGE_30_TAGE_INTERMEDIATE
    elif zeit_config["intensitaet"] == "light":
        challenge_data = CHALLENGE_LIGHT
        show_prio = True
    else:
        challenge_data = CHALLENGE_30_TAGE

    # KIS-1142 Punkt 6 Variante C: trim weeks flagged as out-of-scale for
    # the user's company size. No-op until _CHALLENGE_WEEKS_SKIP_BY_SIZE
    # is populated; wired now so the opt-in hook ships with the branch.
    challenge_data = _filter_challenge_weeks_by_size(challenge_data, company_size)

    # KIS-1142 Punkt 3: Woche 1 für Intermediate/Expert weglassen
    # (Variante B aus Briefing 9). Der bisherige Widerspruch — das Template
    # empfahl "Woche 1 überspringbar", das Rendering zeigte sie trotzdem —
    # wird gelöst, indem die Woche hier wirklich aus challenge_data fällt
    # und die Tages-Nummerierung der restlichen Wochen auf 1 zurückgesetzt
    # wird. Das Template-Banner ("beginnt ab Woche 1") zeigt damit
    # denselben Inhalt, den der Report rendert. Läuft NACH dem P6-Filter,
    # so dass beide zusammen wirken können.
    #
    # KIS-1142 P6-C-solo-exempt: Solo bleibt von P3 unberührt. Sonst würde
    # Solo+Intermediate/Expert nach P6-C's {w3, w4}-Drop auf eine einzige
    # Governance-Woche degenerieren. P3's "Advanced braucht keine Basics"-
    # Rationale rechtfertigt sich erst bei Team/KMU-Profil-Tiefe —
    # Solo-Berater werden stattdessen über den P6-C-Filter zugeschnitten.
    _company_size_norm = (company_size or "").strip().lower()
    if expertise_level in ("intermediate", "expert") and _company_size_norm != "solo":
        challenge_data = _drop_first_week_and_renumber(challenge_data)

    # KIS-1132: Expertise-aware subtitle
    # KIS-1142 P3: Wochen-Anzahl ist 3 für Team/KMU Int/Expert (Woche 1 gedroppt).
    # Hotfix 1027.2.1 F3: Solo behält nach Item H alle 4 Wochen — Subtitle muss
    # company_size-aware sein, sonst widerspricht S.3 Management Summary dem
    # gerenderten Inhalt auf S.13-14.
    _wochen_label = "4 Wochen" if _company_size_norm == "solo" else "3 Wochen"
    if expertise_level == "expert":
        _subtitle = f"Stack-Optimierung und Governance in {_wochen_label}"
    elif expertise_level == "intermediate":
        _subtitle = f"Vom Anwender zum Workflow-Profi in {_wochen_label}"
    else:
        _subtitle = "Von Null auf KI-Profi – angepasst an Ihr Zeitbudget"

    # KIS-1246: Titel an die real gerenderte Tageszahl anpassen — nach dem
    # Woche-1-Drop endete die "30-Tage"-Challenge sichtbar bei Tag 23
    # (Audit KIS-1244/1246: "Challenge-Tage 24-30 fehlen").
    _total_days = sum(
        len(w.get("tage") or []) for w in challenge_data.values() if isinstance(w, dict)
    )
    _challenge_title = (
        "Ihre 30-Tage KI-Challenge" if _total_days >= 30
        else f"Ihre {_total_days}-Tage KI-Challenge"
    )
    if _total_days < 30 and expertise_level in ("intermediate", "expert"):
        _subtitle = f"{_subtitle} · Grundlagen-Woche übersprungen"

    html = f'''
    <!-- M1-FIX: page-break-before entfernt — #challenge-section hat break-before:page in CSS -->

    <!-- 30-TAGE CHALLENGE HEADER -->
    <div style="text-align: center; margin-bottom: 24px; padding-top: 20px;">
        <h2 style="font-size: 28px; font-weight: 700; margin: 0 0 8px 0; color: #1e40af;">
            🏆 {_challenge_title}
        </h2>
        <p style="font-size: 16px; color: #64748b; margin: 0;">
            {_subtitle}
        </p>
    </div>
    
    <!-- ZEITBUDGET-INFO -->
    <!--NO-SANITIZE-ZEITBUDGET--><!-- KIS-1235: verfügbare Zeit, KEINE Ersparnis —
         F4 (final_sanitizer) darf "Stunden/Woche" hier nicht umschreiben -->
    <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 12px; padding: 16px; margin-bottom: 24px; color: white;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 12px; opacity: 0.8; text-transform: uppercase;">Ihr Zeitbudget</div>
                <div style="font-size: 20px; font-weight: 700;">{zeit_config["label"]}</div>
                <div style="font-size: 13px; opacity: 0.9; margin-top: 4px;">≈ {zeit_config["minuten_pro_tag"]} Minuten pro Tag</div>
            </div>
            <div style="text-align: right; max-width: 250px;">
                <div style="font-size: 13px; opacity: 0.95;">💡 {zeit_config["empfehlung"]}</div>
            </div>
        </div>
    </div>
    <!--/NO-SANITIZE-ZEITBUDGET-->
'''
    
    # Wenn Light-Version: Hinweis auf Prio-Tasks
    if show_prio:
        html += '''
    <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 12px; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 13px; color: #92400e;">
            <strong>⭐ Tipp bei wenig Zeit:</strong> Konzentrieren Sie sich auf die markierten Prioritäts-Aufgaben. 
            Die anderen Tage sind als Puffer eingeplant.
        </p>
    </div>
'''
    
    # Wochen-Übersicht
    # KIS-1126 / C7 FIX: Dynamic grid columns based on number of sections
    _num_sections = len(challenge_data)
    html += f'''
    <div style="display: grid; grid-template-columns: repeat({_num_sections}, 1fr); gap: 10px; margin-bottom: 24px;">
'''

    wochen_farben = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"]
    wochen_labels_v2 = ["Woche 1", "Woche 2", "Woche 3", "Woche 4", "Abschluss"]
    for i, (woche_key, woche_data) in enumerate(challenge_data.items()):
        farbe = wochen_farben[i % len(wochen_farben)]
        label = wochen_labels_v2[i] if i < len(wochen_labels_v2) else f"Woche {i+1}"
        html += f'''
        <div style="background: {farbe}15; border: 2px solid {farbe}; border-radius: 8px; padding: 10px; text-align: center;">
            <div style="font-size: 11px; font-weight: 600; color: {farbe}; text-transform: uppercase;">{label}</div>
            <div style="font-size: 13px; font-weight: 700; color: #1e293b; margin: 4px 0;">{woche_data["titel"]}</div>
        </div>
'''

    html += '''
    </div>
'''

    # Detaillierte Wochen
    for i, (woche_key, woche_data) in enumerate(challenge_data.items()):
        farbe = wochen_farben[i % len(wochen_farben)]
        label = wochen_labels_v2[i] if i < len(wochen_labels_v2) else f"Woche {i+1}"
        tage_in_section = len(woche_data.get("tage", []))
        grid_cols = min(tage_in_section, 7)
        html += f'''
    <div style="margin-bottom: 20px;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: {farbe};">
            {label}: {woche_data["titel"]}
        </h3>
        <div style="display: grid; grid-template-columns: repeat({grid_cols}, 1fr); gap: 6px;">
'''
        
        tage_list2: List[Dict[str, Any]] = cast(List[Dict[str, Any]], woche_data["tage"])
        for tag_data in tage_list2:
            is_prio = tag_data.get("prio", False)
            is_pause = "Pause" in str(tag_data.get("aufgabe", ""))

            if is_pause:
                bg_color = "#f1f5f9"
                border_color = "#e2e8f0"
                text_color = "#94a3b8"
            elif is_prio and show_prio:
                bg_color = "#fef3c7"
                border_color = "#f59e0b"
                text_color = "#92400e"
            else:
                bg_color = "#f8fafc"
                border_color = "#e2e8f0"
                text_color = "#334155"

            prio_star = "⭐ " if is_prio and show_prio else ""

            html += f'''
            <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 8px; font-size: 10px;">
                <div style="font-weight: 700; color: {farbe}; margin-bottom: 4px;">Tag {tag_data.get("tag", "")}</div>
                <div style="color: {text_color}; line-height: 1.3; min-height: 32px;">{prio_star}{tag_data.get("aufgabe", "")}</div>
                <div style="color: #94a3b8; font-size: 9px; margin-top: 4px;">⏱️ {tag_data.get("dauer", "")}</div>
            </div>
'''
        
        html += '''
        </div>
    </div>
'''
    
    # KIS-1134-FX-2: Prognose-Werte für Erfolgs-Tracking
    _has_values = hours_per_week > 0 and stundensatz > 0
    _week_factors = [0.5, 0.75, 1.0, 1.0]
    _weekly_hours = [round(hours_per_week * f, 1) for f in _week_factors]
    _total_hours = round(sum(_weekly_hours), 1)
    _total_savings = round(_total_hours * stundensatz)

    # Erfolgs-Tracking
    # L3: Added break-inside:avoid to prevent orphan micro-pages
    html += '''
    <!-- L3: break-inside:avoid prevents orphan micro-page -->
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 8px; padding: 16px; margin-top: 20px; break-inside: avoid; page-break-inside: avoid;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: #166534;">
            📊 Ihr Erfolgs-Tracking
        </h3>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
'''

    # KIS-1232: Wochenwerte deutsch formatieren (5,8 h statt 5.8 h)
    def _de_hours(v: float) -> str:
        return f"{v:g}".replace(".", ",")

    for w in range(1, 5):
        _display = f"~{_de_hours(_weekly_hours[w - 1])} h" if _has_values else "_____ h"
        html += f'''
            <div style="text-align: center;">
                <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Woche {w}</div>
                <div style="border: 2px solid #22c55e; border-radius: 8px; padding: 12px; background: white;">
                    <div style="font-size: 10px; color: #64748b;">Gesparte Zeit:</div>
                    <div style="font-size: 16px; font-weight: 700; color: #166534;">{_display}</div>
                </div>
            </div>
'''

    # KIS-1232: Grid HIER schließen — die Tipps-Box stand vorher als fünftes
    # Grid-Item im 4-Spalten-Raster und wurde auf 1/4-Breite gequetscht
    # (Status-Report S. 16, schmale umgebrochene Box).
    html += '''
        </div>
'''

    # v14.18: Tipps für Erfolg
    html += '''
        <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-radius: 12px; padding: 16px; margin-top: 16px; margin-bottom: 16px;">
            <h4 style="font-size: 13px; font-weight: 600; margin: 0 0 12px 0; color: #1e40af;">💡 Tipps für Ihren Erfolg</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px; color: #334155;">
                <div>✓ Feste Zeit im Kalender blocken</div>
                <div>✓ Kleine Schritte, große Wirkung</div>
                <div>✓ Erfolge dokumentieren</div>
                <div>✓ Bei Rückstand: nächsten Tag neu starten</div>
                <div>✓ Kollegen einbeziehen (wenn vorhanden)</div>
                <div>✓ Nach 30 Tagen: Routine beibehalten!</div>
            </div>
        </div>
    '''

    if _has_values:
        _savings_str = f"{_total_savings:,}".replace(",", ".")
        html += f'''
        <div style="text-align: center; margin-top: 12px; padding-top: 12px; border-top: 1px solid #22c55e;">
            <span style="font-size: 14px; color: #166534; font-weight: 600;">
                🎯 Prognose nach 30 Tagen: ~{_de_hours(_total_hours)} Stunden = ~{_savings_str} € gespart
            </span>
            <div style="font-size: 11px; color: #475569; margin-top: 6px; line-height: 1.5;">
                Diese Tracking-Prognose ist konservativ (Ramp-up: 50&nbsp;%/75&nbsp;%/100&nbsp;%/100&nbsp;% der Wochenleistung).
                Die volle Ziel-Zeitersparnis aus dem Business Case wird typischerweise ab Monat&nbsp;2 erreicht.
            </div>
        </div>
    </div>
'''
    else:
        html += '''
        <div style="text-align: center; margin-top: 12px; padding-top: 12px; border-top: 1px solid #22c55e;">
            <span style="font-size: 14px; color: #166534; font-weight: 600;">
                🎯 Gesamt nach 30 Tagen: _______ Stunden = _______ € gespart
            </span>
        </div>
    </div>
'''

    # KIS-1235: Quartals-/Saisonbezug dynamisch auflösen (statt hartem
    # "Q2-Ziel … bis Sommer", das im Juli-Report veraltet war).
    html = html.replace("__QUARTAL_ZIEL__", _resolve_quarter_goal())

    return html


def _resolve_quarter_goal(today: "Optional[Any]" = None) -> str:
    """Tag-28-Aufgabe mit aktuellem Quartals-/Saisonbezug.

    Ziel-Quartal ist das aktuelle, solange mindestens ~1 Monat davon übrig
    ist (Tag 28 der Challenge liegt ~4 Wochen nach Report-Erstellung),
    sonst das Folgequartal.
    """
    from datetime import date as _date
    d = today or _date.today()
    quarter = (d.month - 1) // 3 + 1
    year_q = quarter
    # Letzter Monat des Quartals bereits angebrochen → Folgequartal anpeilen
    if d.month % 3 == 0:
        year_q = quarter + 1
    if year_q > 4:
        year_q = 1
    season = {1: "zum Frühjahr", 2: "zum Sommer", 3: "zum Herbst", 4: "zum Jahresende"}[year_q]
    return f"Q{year_q}-Ziel definieren: Was soll bis {season} KI-gestützt laufen?"


# =============================================================================
# BRANCHEN-FALLSTUDIEN (Idee #5)
# =============================================================================

# FIX-PERSONA: Segment-aware company descriptions for Fallstudien.
# Maps size_key → company description per Branche.
_FALLSTUDIE_UNTERNEHMEN: Dict[str, Dict[str, str]] = {
    "beratung": {
        "solo": "Solo-Berater, Strategieberatung",
        "team": "Beratungsteam mit 5 Mitarbeitenden",
        "kmu": "Beratungsunternehmen mit 25 Mitarbeitenden",
    },
    "it": {
        "solo": "Freelance Entwickler, Web-Anwendungen",
        "team": "IT-Team mit 8 Entwicklern",
        "kmu": "IT-Dienstleister mit 40 Mitarbeitenden",
    },
    "finanzen": {
        "solo": "Unabhängiger Finanzberater",
        "team": "Finanzberatungsteam mit 6 Beratern",
        "kmu": "Finanzberatungsunternehmen mit 30 Mitarbeitenden",
    },
    "bildung": {
        "solo": "Freiberuflicher Trainer, IT-Schulungen",
        "team": "Schulungsteam mit 5 Trainern",
        "kmu": "Weiterbildungsinstitut mit 20 Mitarbeitenden",
    },
    "gesundheit": {
        "solo": "Selbstständiger Therapeut",
        "team": "Praxis mit 3 Therapeuten",
        "kmu": "Gesundheitszentrum mit 15 Mitarbeitenden",
    },
    # FIX-S25-B2: Handwerk & Recht segment overrides
    "handwerk": {
        "solo": "Selbstständiger Handwerksmeister, SHK",
        "team": "SHK-Betrieb mit 5 Mitarbeitern",
        "kmu": "Handwerksbetrieb mit 25 Mitarbeitern",
    },
    "recht": {
        "solo": "Einzelanwalt, Zivilrecht",
        "team": "Kanzlei mit 4 Anwälten",
        "kmu": "Wirtschaftskanzlei mit 20 Mitarbeitenden",
    },
}

# KIS-1247: Sparten-spezifischer Medien-Fallstudien-Pool. Alle Cases sind
# fiktive, aber produktionstypische Branchen-Beispiele (Disclaimer wird im
# HTML gerendert) — Auswahl über medien_sparte-Stichworte.
FALLSTUDIEN_MEDIEN: List[Dict[str, Any]] = [
    {
        "keywords": ("produktion", "film", "tv", "doku", "post", "vfx"),
        "titel": "Doku-Produktion erschließt ihr Rohmaterial-Archiv",
        "unternehmen": "Produktionsfirma, 8 Mitarbeitende (Doku & Corporate)",
        "unternehmen_solo": "Freie:r Filmemacher:in mit festem Editor:innen-Netzwerk",
        "ausgangslage": "Sichtung und Logging fressen die Schnittzeit, Archivmaterial ist praktisch unauffindbar, Untertitel entstehen manuell pro Fassung",
        "loesung": "Automatische Transkription + Szenenmarker beim Import (EU-Tool), textbasierter Rohschnitt in Premiere, Metadaten-Pflichtfelder im Archiv",
        "ergebnis": {
            "zeitersparnis": "60 Stunden/Monat (Team)",
            "kosteneinsparung": "~5.700 €/Monat",
            "qualitaet": "Schnittvorbereitung von 3 Tagen auf 1; Archiv-Clips in Minuten auffindbar und lizenzierbar"
        },
        "zitat": "Die Geschichten entstehen wieder im Schnitt – nicht beim Durchsuchen von Festplatten.",
        "dauer_bis_roi": "4 Wochen"
    },
    {
        "keywords": ("agentur", "werbung", "corporate", "marketing", "content", "verlag", "musik", "audio", "pr", "webdesign", "design", "social", "tonstudio"),
        "titel": "Werbefilm-Studio verdoppelt seine Pitch-Schlagzahl",
        "unternehmen": "Werbefilm-Studio, 5 Kreative (Markenkunden & Sender)",
        "unternehmen_solo": "Solo-Creative-Producer:in für Markenfilme",
        "ausgangslage": "Treatments, Moodboards und Pitch-Decks binden die Kreativen, Stoffe bleiben liegen, Änderungsrunden dauern",
        "loesung": "KI-Treatment-Entwürfe als Startpunkt, gekennzeichnete Moodboard-Visuals (Firefly), fester Freigabeschritt vor jedem Versand",
        "ergebnis": {
            "zeitersparnis": "30 Stunden/Monat (Team)",
            "kosteneinsparung": "~2.900 €/Monat",
            "qualitaet": "Doppelt so viele Pitches bei gleicher Teamgröße, höhere Trefferquote durch mehr Varianten"
        },
        "zitat": "Doppelt so viele Pitches – und die Ideen bleiben im Haus.",
        "dauer_bis_roi": "3 Wochen"
    },
    {
        "keywords": ("games", "game", "animation", "interactive", "xr"),
        "titel": "Games-Studio verkürzt die Lokalisierung um Wochen",
        "unternehmen": "Independent-Studio, 12 Mitarbeitende",
        "unternehmen_solo": "Solo-Entwickler:in mit Publisher-Anbindung",
        "ausgangslage": "Untertitel, Übersetzungen und Asset-Verschlagwortung verzögern jeden Release; Store-Vorgaben zur KI-Deklaration sind unklar",
        "loesung": "KI-Untertitel und Übersetzungs-Entwürfe mit menschlicher Endkontrolle, automatisches Asset-Tagging, dokumentierte KI-Deklaration je Build",
        "ergebnis": {
            "zeitersparnis": "50 Stunden/Monat (Team)",
            "kosteneinsparung": "~4.000 €/Monat",
            "qualitaet": "Lokalisierung in 6 statt 10 Wochen, Release in 5 Sprachen gleichzeitig, saubere Store-Deklaration"
        },
        "zitat": "Der Release erscheint jetzt in fünf Sprachen gleichzeitig.",
        "dauer_bis_roi": "6 Wochen"
    },
]


def _pick_medien_fallstudie(sparte: str, size_key: str) -> Dict[str, Any]:
    """Wählt den passenden Medien-Case nach Sparte (Fallback: Produktion)."""
    s = (sparte or "").lower()
    chosen: Dict[str, Any] = FALLSTUDIEN_MEDIEN[0]
    if s:
        for case in FALLSTUDIEN_MEDIEN:
            if any(k in s for k in case["keywords"]):
                chosen = case
                break
    result = {k: v for k, v in chosen.items() if k not in ("keywords", "unternehmen_solo")}
    if size_key == "solo" and chosen.get("unternehmen_solo"):
        result["unternehmen"] = chosen["unternehmen_solo"]
    return result


FALLSTUDIEN: Dict[str, Dict[str, Any]] = {
    "beratung": {
        "titel": "Unternehmensberater spart 12 Stunden pro Woche",
        "unternehmen": "Solo-Berater, Strategieberatung",
        "ausgangslage": "Aufwändige Angebotserstellung (4h pro Angebot), zeitintensive Meeting-Protokolle, repetitive E-Mail-Korrespondenz",
        "loesung": "ChatGPT Plus für Angebote, Protokolle und E-Mails",
        "ergebnis": {
            "zeitersparnis": "12 Stunden/Woche",
            "kosteneinsparung": "~4.800 €/Monat",
            "qualitaet": "Konsistentere Angebote, schnellere Reaktionszeit"
        },
        "zitat": "Ich kann jetzt doppelt so viele Anfragen bearbeiten – ohne Qualitätsverlust.",
        "dauer_bis_roi": "2 Wochen"
    },
    "it": {
        "titel": "IT-Freelancer automatisiert Code-Reviews",
        "unternehmen": "Freelance Entwickler, Web-Anwendungen",
        "ausgangslage": "Zeitaufwändige Code-Reviews, repetitive Dokumentation, Support-Anfragen",
        "loesung": "ChatGPT für Code-Review, Dokumentation und technischen Support",
        "ergebnis": {
            "zeitersparnis": "15 Stunden/Woche",
            "kosteneinsparung": "~6.000 €/Monat",
            "qualitaet": "Weniger Bugs, bessere Dokumentation"
        },
        "zitat": "Die KI findet Bugs, die ich übersehen hätte. Meine Code-Qualität ist messbar gestiegen.",
        "dauer_bis_roi": "1 Woche"
    },
    "marketing": {
        "titel": "Marketing-Agentur verdreifacht Content-Output",
        "unternehmen": "Kleine Agentur, 5 Mitarbeiter",
        "ausgangslage": "Hoher Zeitdruck bei Social Media, Newsletter dauern zu lange, Ideenfindung stockt",
        "loesung": "ChatGPT Team + Midjourney für Content-Erstellung",
        "ergebnis": {
            "zeitersparnis": "25 Stunden/Woche (Team)",
            "kosteneinsparung": "~5.000 €/Monat",
            "qualitaet": "3x mehr Content bei gleicher Teamgröße"
        },
        "zitat": "Wir haben keinen Mitarbeiter eingestellt, sondern KI. Beste Entscheidung.",
        "dauer_bis_roi": "3 Wochen"
    },
    "handel": {
        "titel": "Online-Shop optimiert 500 Produkttexte",
        "unternehmen": "E-Commerce, Haushaltsartikel",
        "ausgangslage": "Generische Produktbeschreibungen, schlechte SEO-Rankings, hohe Retourenquote",
        "loesung": "ChatGPT für SEO-optimierte Produkttexte + Kundenservice",
        "ergebnis": {
            "zeitersparnis": "20 Stunden/Woche",
            "kosteneinsparung": "~3.200 €/Monat",
            "qualitaet": "+40% organischer Traffic, -15% Retouren"
        },
        "zitat": "Unsere Produktseiten ranken jetzt auf Seite 1. Der ROI war nach einem Monat erreicht.",
        "dauer_bis_roi": "4 Wochen"
    },
    "finanzen": {
        "titel": "Finanzberater automatisiert Kundenreports",
        "unternehmen": "Unabhängiger Finanzberater",
        "ausgangslage": "Zeitintensive Kundenberichte, repetitive Analysen, viele Standardanfragen",
        "loesung": "ChatGPT für Report-Erstellung und Kundenkorrespondenz",
        "ergebnis": {
            "zeitersparnis": "8 Stunden/Woche",
            "kosteneinsparung": "~3.500 €/Monat",
            "qualitaet": "Professionellere Reports, schnellere Reaktion"
        },
        "zitat": "Meine Kunden bekommen jetzt Reports am gleichen Tag statt nach einer Woche.",
        "dauer_bis_roi": "2 Wochen"
    },
    "bildung": {
        "titel": "Trainer erstellt Kursmaterial in halber Zeit",
        "unternehmen": "Freiberuflicher Trainer, IT-Schulungen",
        "ausgangslage": "Aufwändige Materialerstellung, individuelle Übungsaufgaben, Feedback schreiben",
        "loesung": "ChatGPT für Kursmaterial, Übungen und Teilnehmer-Feedback",
        "ergebnis": {
            "zeitersparnis": "10 Stunden/Woche",
            "kosteneinsparung": "~2.400 €/Monat",
            "qualitaet": "Aktuelleres Material, individuellere Übungen"
        },
        "zitat": "Ich kann jetzt mehr Kurse anbieten, weil die Vorbereitung so viel schneller geht.",
        "dauer_bis_roi": "2 Wochen"
    },
    "gesundheit": {
        "titel": "Physiotherapie-Praxis optimiert Dokumentation",
        "unternehmen": "Praxis mit 3 Therapeuten",
        "ausgangslage": "Zeitaufwändige Befundberichte, repetitive Übungsanleitungen, Terminkoordination",
        "loesung": "ChatGPT für Befunde und Patientenanleitungen",
        "ergebnis": {
            "zeitersparnis": "6 Stunden/Woche",
            "kosteneinsparung": "~1.800 €/Monat",
            "qualitaet": "Ausführlichere Befunde, bessere Patientenkommunikation"
        },
        "zitat": "Die Dokumentation frisst nicht mehr unsere Behandlungszeit.",
        "dauer_bis_roi": "3 Wochen"
    },
    "bauwesen": {
        "titel": "Architekturbüro beschleunigt Leistungsverzeichnisse",
        "unternehmen": "Kleines Architekturbüro, 4 Mitarbeiter",
        "ausgangslage": "Zeitintensive LV-Erstellung, Baustellenprotokolle, Kundenkorrespondenz",
        "loesung": "ChatGPT für LV-Positionen, Protokolle und Schriftverkehr",
        "ergebnis": {
            "zeitersparnis": "12 Stunden/Woche",
            "kosteneinsparung": "~2.800 €/Monat",
            "qualitaet": "Weniger Fehler in LVs, schnellere Projektabwicklung"
        },
        "zitat": "Früher hat ein LV zwei Tage gedauert. Jetzt schaffen wir es in einem halben.",
        "dauer_bis_roi": "3 Wochen"
    },
    "verwaltung": {
        "titel": "Kommunalverwaltung modernisiert Bürgerservice",
        "unternehmen": "Stadtverwaltung, 50.000 Einwohner",
        "ausgangslage": "Viele Standardanfragen, lange Bearbeitungszeiten, Bescheid-Formulierungen",
        "loesung": "ChatGPT für Bürgeranfragen und Bescheid-Entwürfe (ohne sensible Daten)",
        "ergebnis": {
            "zeitersparnis": "15 Stunden/Woche (Sachbearbeiter)",
            "kosteneinsparung": "~2.400 €/Monat",
            "qualitaet": "Verständlichere Bescheide, schnellere Antworten"
        },
        "zitat": "Die Bürger verstehen unsere Schreiben jetzt besser – weniger Rückfragen.",
        "dauer_bis_roi": "4 Wochen"
    },
    "medien": {
        "titel": "Kreativagentur wächst ohne neue Mitarbeiter",
        "unternehmen": "Design-Agentur, 6 Kreative",
        "ausgangslage": "Briefings dauern zu lange, Ideenfindung stockt, Textarbeit bindet Designer",
        "loesung": "ChatGPT für Briefings, Texte und Konzeptentwicklung",
        "ergebnis": {
            "zeitersparnis": "20 Stunden/Woche (Team)",
            "kosteneinsparung": "~4.000 €/Monat",
            "qualitaet": "Mehr Zeit für Kreativarbeit, bessere Briefings"
        },
        "zitat": "Unsere Designer designen wieder – statt Texte zu schreiben.",
        "dauer_bis_roi": "2 Wochen"
    },
    "industrie": {
        "titel": "Mittelständler optimiert Arbeitsanweisungen",
        "unternehmen": "Produktionsbetrieb, 80 Mitarbeiter",
        "ausgangslage": "Veraltete Arbeitsanweisungen, aufwändige Fehleranalysen, Schichtübergaben",
        "loesung": "ChatGPT für Dokumentation und Prozessanalysen",
        "ergebnis": {
            "zeitersparnis": "10 Stunden/Woche",
            "kosteneinsparung": "~2.000 €/Monat",
            "qualitaet": "Aktuelle Dokumentation, bessere Fehleranalyse"
        },
        "zitat": "Unsere Arbeitsanweisungen sind endlich auf dem neuesten Stand.",
        "dauer_bis_roi": "4 Wochen"
    },
    "transport": {
        "titel": "Spedition verbessert Kundenkommunikation",
        "unternehmen": "Regionale Spedition, 25 Fahrzeuge",
        "ausgangslage": "Viele Kundenanfragen zu Lieferstatus, Reklamationsbearbeitung, Dokumentation",
        "loesung": "ChatGPT für Kundenkorrespondenz und Reklamationsantworten",
        "ergebnis": {
            "zeitersparnis": "8 Stunden/Woche",
            "kosteneinsparung": "~1.600 €/Monat",
            "qualitaet": "Schnellere Antworten, professionellere Kommunikation"
        },
        "zitat": "Kunden bekommen jetzt in Minuten Antwort statt am nächsten Tag.",
        "dauer_bis_roi": "2 Wochen"
    },
    "gastronomie": {
        "titel": "Restaurant steigert Online-Bewertungen",
        "unternehmen": "Gehobenes Restaurant, 40 Plätze",
        "ausgangslage": "Bewertungen unbeantwortet, Speisekarten veraltet, Eventanfragen zeitaufwändig",
        "loesung": "ChatGPT für Bewertungsantworten, Speisekartentexte, Eventangebote",
        "ergebnis": {
            "zeitersparnis": "5 Stunden/Woche",
            "kosteneinsparung": "~800 €/Monat",
            "qualitaet": "+0.4 Sterne bei Google, mehr Eventbuchungen"
        },
        "zitat": "Jede Bewertung bekommt jetzt eine persönliche Antwort. Das macht den Unterschied.",
        "dauer_bis_roi": "3 Wochen"
    },
    # FIX-S25-B2: Handwerk-specific Fallstudie
    "handwerk": {
        "titel": "SHK-Betrieb halbiert Dispositionszeit",
        "unternehmen": "SHK-Betrieb mit 5 Mitarbeitern",
        "ausgangslage": "Tägliche Disposition bindet Meister 1-2h, Angebote dauern zu lange, Wartungstermine werden vergessen",
        "loesung": "Craftboxx Tourenplanung + ChatGPT Angebotsbausteine",
        "ergebnis": {
            "zeitersparnis": "25 Stunden/Monat (Team)",
            "kosteneinsparung": "~2.375 €/Monat",
            "qualitaet": "Kein vergessener Wartungstermin mehr"
        },
        "zitat": "Die KI schreibt jetzt unsere Angebote vor – der Meister prüft nur noch. Beste Entscheidung.",
        "dauer_bis_roi": "3 Wochen"
    },
    # FIX-S25-B2: Recht-specific Fallstudie
    "recht": {
        "titel": "Einzelanwalt verdoppelt Mandantenkapazität",
        "unternehmen": "Einzelanwalt, Zivilrecht",
        "ausgangslage": "Zeitintensive Schriftsatzformulierung, aufwändige Recherche-Zusammenfassungen, viele Mandanten-Updates per Hand",
        "loesung": "ChatGPT Plus für Textbausteine, Recherche und Mandantenkommunikation",
        "ergebnis": {
            "zeitersparnis": "10 Stunden/Woche",
            "kosteneinsparung": "~4.000 €/Monat",
            "qualitaet": "Schnellere Reaktionszeit, konsistentere Schriftsätze"
        },
        "zitat": "Meine Mandanten bekommen jetzt am gleichen Tag Antwort statt nach einer Woche.",
        "dauer_bis_roi": "2 Wochen"
    },
    "default": {
        "titel": "Selbstständiger spart 8 Stunden pro Woche",
        "unternehmen": "Freiberufler, Dienstleistungen",
        "ausgangslage": "Zeitfresser: E-Mails, Angebote, Dokumentation, Recherche",
        "loesung": "ChatGPT Plus für tägliche Textaufgaben",
        "ergebnis": {
            "zeitersparnis": "8 Stunden/Woche",
            "kosteneinsparung": "~2.500 €/Monat",
            "qualitaet": "Mehr Zeit für Kerngeschäft, bessere Work-Life-Balance"
        },
        "zitat": "Ich arbeite nicht weniger – aber ich schaffe mehr in der gleichen Zeit.",
        "dauer_bis_roi": "2 Wochen"
    }
}


def generate_fallstudie_html(branche: str, size_key: str = "solo", medien_sparte: str = "") -> str:
    """
    Generiert eine branchenspezifische, segment-aware Fallstudie.

    FIX-PERSONA: Uses _FALLSTUDIE_UNTERNEHMEN to pick a company description
    matching the user's size segment, avoiding persona leaks like
    "Solo-Berater" in a KMU report.
    KIS-1247: Medien-Branche wählt sparten-spezifisch aus dem
    FALLSTUDIEN_MEDIEN-Pool (Produktion/Werbung/Games).
    """
    branche_key = get_branche_key(branche)
    if branche_key == "medien":
        fallstudie: Dict[str, Any] = _pick_medien_fallstudie(medien_sparte, size_key)
    else:
        fallstudie = cast(Dict[str, Any], FALLSTUDIEN.get(branche_key, FALLSTUDIEN["default"]))
        # FIX-PERSONA: Override "unternehmen" with segment-appropriate description
        size_overrides = _FALLSTUDIE_UNTERNEHMEN.get(branche_key, {})
        if size_key in size_overrides:
            fallstudie = {**fallstudie, "unternehmen": size_overrides[size_key]}
    
    # KIS-1190 Sprint-1027.1 Item A: Fallstudie wird als externes Branchen-
    # Beispiel gekennzeichnet und gegen final_sanitizer F4 (Stunden/Woche →
    # Stunden/Monat) per NO-SANITIZE-FALLSTUDIE-Marker geschützt. Werte sind
    # fiktive Beispieldaten und müssen NICHT der User-canonical ROI matchen.
    html = f'''<!--NO-SANITIZE-FALLSTUDIE-->
    <!-- FALLSTUDIE -->
    <div class="card-nobreak" data-no-sanitize="true" style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px; margin-top: 24px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-size: 24px;">📊</span>
            <h3 style="font-size: 18px; font-weight: 700; margin: 0; color: #1e293b;">
                Fallstudie: {fallstudie["titel"]}
            </h3>
        </div>
        <div style="font-size: 11px; color: #64748b; font-style: italic; margin-bottom: 16px; padding: 4px 8px; background: #fff; border-left: 3px solid #94a3b8; border-radius: 0 4px 4px 0;">
            Branchen-Beispiel · fiktive Beispieldaten zur Veranschaulichung · weicht von Ihrem persönlichen ROI bewusst ab
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
            <div>
                <div style="font-size: 11px; color: #64748b; text-transform: uppercase; margin-bottom: 4px;">Unternehmen</div>
                <div style="font-size: 13px; color: #334155;">{fallstudie["unternehmen"]}</div>
            </div>
            <div>
                <div style="font-size: 11px; color: #64748b; text-transform: uppercase; margin-bottom: 4px;">ROI erreicht nach</div>
                <div style="font-size: 13px; color: #334155; font-weight: 600;">{fallstudie["dauer_bis_roi"]}</div>
            </div>
        </div>
        
        <div style="margin-bottom: 16px;">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; margin-bottom: 4px;">Ausgangslage</div>
            <div style="font-size: 13px; color: #334155;">{fallstudie["ausgangslage"]}</div>
        </div>
        
        <div style="margin-bottom: 16px;">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; margin-bottom: 4px;">Lösung</div>
            <div style="font-size: 13px; color: #334155;">{fallstudie["loesung"]}</div>
        </div>
        
        <!-- Ergebnisse -->
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px;">
            <div style="background: white; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="font-size: 20px; font-weight: 700; color: #166534;">{fallstudie["ergebnis"]["zeitersparnis"]}</div>
                <div style="font-size: 11px; color: #64748b;">Zeitersparnis</div>
            </div>
            <div style="background: white; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="font-size: 20px; font-weight: 700; color: #166534;">{fallstudie["ergebnis"]["kosteneinsparung"]}</div>
                <div style="font-size: 11px; color: #64748b;">Ersparnis/Monat</div>
            </div>
            <div style="background: white; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="font-size: 14px; font-weight: 600; color: #1e40af;">{fallstudie["ergebnis"]["qualitaet"]}</div>
                <div style="font-size: 11px; color: #64748b;">Qualität</div>
            </div>
        </div>
        
        <!-- Zitat -->
        <div style="background: white; border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 0 8px 8px 0;">
            <div style="font-size: 14px; color: #334155; font-style: italic;">
                "{fallstudie["zitat"]}"
            </div>
        </div>
    </div>
<!--/NO-SANITIZE-FALLSTUDIE-->
'''

    return html
