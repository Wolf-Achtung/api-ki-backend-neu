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
                "prompt": """Formuliere einen professionellen Kundenbrief:

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
                "prompt": """Strukturiere diese Risikoinformationen für einen Kunden:

Kunde: [PROFIL]
Produkt/Anlage: [BESCHREIBUNG]
Marktdaten: [RELEVANTE INFOS]

Erstelle:
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
                "prompt": """Formuliere konstruktives Feedback:

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
                "prompt": """Strukturiere diese Übergabe-Informationen:

Patient: [ANONYMISIERT - NUR ALTER/RELEVANTES]
Aktuelle Situation: [STICHPUNKTE]
Maßnahmen: [WAS WURDE GEMACHT]

Erstelle:
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
                "prompt": """Formuliere eine LV-Position:

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
                "prompt": """Formuliere ein Schreiben an den Bauherrn:

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
                "prompt": """Formuliere eine Kundeninfo zu Lieferverzögerung:

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
                "prompt": """Formuliere eine Antwort auf diese Reklamation:

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
                "prompt": """Formuliere diese Gerichtbeschreibung appetitlich um:

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
                "prompt": """Formuliere diese E-Mail professionell und klar:

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
) -> str:
    """
    Generiert die SOFORT_START_HTML Section.

    PLATIN+++ FIX 1.1/1.2/1.4: Uses canonical rates and size-based time savings.
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
    if canon_hours_month > 0:
        canon_yearly = int(canon_hours_month * 12)
        if savings["hours_per_year"] != canon_yearly:
            savings["hours_per_year"] = canon_yearly
            savings["savings_per_year"] = canon_yearly * savings["hourly_rate"]
            if savings.get("tool_costs", 0) > 0:
                savings["net_savings"] = savings["savings_per_year"] - savings["tool_costs"]
    
    # Personalisiere den ersten Schritt
    # FIX-EMPTY-PARENS: Strip hauptleistung and validate before using in parentheses.
    # If hauptleistung is whitespace-only or gets sanitized downstream, empty "()" remain.
    _hl_clean = (hauptleistung or "").strip()
    erster_schritt = branche_data["erster_schritt"]
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
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: #166534; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">💰</span>
            Ihre potenzielle Zeitersparnis
        </h3>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; text-align: center;">
            <div style="background: white; border-radius: 6px; padding: 12px;">
                <div style="font-size: 24px; font-weight: 700; color: #166534;">{savings['hours_per_week']}h</div>
                <div style="font-size: 11px; color: #64748b;">pro Woche</div>
            </div>
            <div style="background: white; border-radius: 6px; padding: 12px;">
                <div style="font-size: 24px; font-weight: 700; color: #166534;">{savings['hours_per_year']}h</div>
                <div style="font-size: 11px; color: #64748b;">pro Jahr</div>
            </div>
            <div style="background: white; border-radius: 6px; padding: 12px;">
                <div style="font-size: 24px; font-weight: 700; color: #166534;">{f"{savings['net_savings']:,}".replace(",", ".")}€</div>
                <div style="font-size: 11px; color: #64748b;">Netto-Ersparnis*</div>
            </div>
        </div>
        <p style="font-size: 10px; color: #64748b; margin: 8px 0 0 0; text-align: right;">
            *Bei {savings['hourly_rate']}€/h, abzgl. ~{savings['tool_costs']}€ Tool-Kosten/Jahr
        </p>
    </div>
    
    <!-- 4 PROMPTS – FIX-B17: heading + first box stay together, no forced page break -->
    <div style="margin-bottom: 24px;">
        <div style="page-break-inside: avoid; break-inside: avoid;">
        <h3 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 24px;">📋</span>
            4 Copy-Paste Prompts für {branche_data["name"]}
        </h3>
        <p style="font-size: 13px; color: #64748b; margin: 0 0 16px 0;">
            Kopieren Sie diese Prompts direkt in ChatGPT oder Claude:
        </p>
'''

    # Prompts hinzufügen
    prompts_list: List[Dict[str, Any]] = cast(List[Dict[str, Any]], branche_data["prompts"])
    for i, prompt_data in enumerate(prompts_list, 1):
        prompt_text = prompt_data["prompt"][:400] + "..." if len(prompt_data["prompt"]) > 400 else prompt_data["prompt"]
        # FIX-B17: Close the avoid-break wrapper after first prompt box
        close_wrapper = "</div>" if i == 1 else ""
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
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; font-family: monospace; font-size: 10px; line-height: 1.4; white-space: pre-wrap; color: #334155;">
{prompt_text}
            </div>
        </div>
        {close_wrapper}
'''
    
    # 4. Lern-Prompt – Verstehen & Erklären (branchenspezifisch)
    _lern_raw = branche_data.get("lern_prompt")
    lern_prompt: Dict[str, str] | None = cast(Dict[str, str], _lern_raw) if isinstance(_lern_raw, dict) else None
    if lern_prompt:
        lern_text = lern_prompt["prompt"][:400] + "..." if len(lern_prompt["prompt"]) > 400 else lern_prompt["prompt"]
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
            <div style="background: white; border: 1px solid #fde68a; border-radius: 6px; padding: 12px; font-family: monospace; font-size: 10px; line-height: 1.4; white-space: pre-wrap; color: #334155;">
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
    
    # Checkliste hinzufügen (Idee #9)
    html += '''
    <!-- CHECKLISTE -->
    <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: #1e40af; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">✅</span>
            Ihre Start-Checkliste (erste 60 Minuten)
        </h3>
        <div style="display: flex; flex-direction: column; gap: 6px;">
'''
    
    for item in CHECKLISTE_START:
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
    
    # Warnungen hinzufügen
    html += '''
    <!-- WARNUNGEN -->
    <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 16px;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: #92400e; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">⚠️</span>
            Wichtig: Das sollten Sie NICHT tun
        </h3>
        <div style="display: flex; flex-direction: column; gap: 8px;">
'''
    
    for warnung in WARNUNGEN:
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
    
    
    
    # Branchen-Fallstudie (Idee #5)
    html += generate_fallstudie_html(branche, size_key)

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
    """
    Generiert eine Entscheidungsvorlage für Vorgesetzte (Idee #10).

    PLATIN+++ FIX 1.1: Uses canonical rate from single source of truth.
    FIX-KIS-1085: Shows BRUTTO time savings (hours × rate × 12), dynamically.
    """
    # PLATIN+++ FIX 1.1: Use canonical rate
    if stundensatz <= 0:
        stundensatz = _get_canonical_rate(company_size)

    # FIX-KIS-1085: Use canonical monthly hours if available, otherwise derive
    # from weekly. Compute brutto directly as hours_month × rate × 12 to avoid
    # lossy weekly→yearly conversion (e.g. 6h/wk × 48 = 288 ≠ 25h/mo × 12 = 300).
    if canon_hours_month > 0:
        _hours_month = int(canon_hours_month)
    else:
        _hours_month = zeitersparnis_pro_woche * 4

    # Constraint #4: GF-Vorlage shows BRUTTO-Zeitersparnis (hours × rate × 12)
    _brutto_jahr = _hours_month * stundensatz * 12
    _brutto_jahr_fmt = f"{_brutto_jahr:,}".replace(",", ".")

    savings = calculate_yearly_savings(zeitersparnis_pro_woche, stundensatz, company_size)

    html = f'''
    <div style="background: white; border: 2px solid #1e40af; border-radius: 8px; padding: 20px; margin-top: 24px;">
        <h3 style="font-size: 18px; font-weight: 700; margin: 0 0 16px 0; color: #1e40af; text-align: center;">
            📄 Entscheidungsvorlage: KI-Tools einführen
        </h3>
        <p style="font-size: 12px; color: #64748b; text-align: center; margin: 0 0 16px 0;">
            Diese Vorlage können Sie Ihrer Geschäftsführung vorlegen
        </p>

        <div style="border-top: 1px solid #e2e8f0; padding-top: 16px;">
            <h4 style="font-size: 14px; font-weight: 600; margin: 0 0 8px 0;">Antrag: Einführung von KI-Assistenz-Tools</h4>

            <p style="font-size: 13px; margin: 0 0 12px 0;">
                <strong>Bereich:</strong> {hauptleistung or branche or "Allgemein"}<br>
                <strong>Beantragt von:</strong> [IHR NAME]<br>
                <strong>Datum:</strong> [DATUM]
            </p>

            <h4 style="font-size: 13px; font-weight: 600; margin: 16px 0 8px 0;">Erwarteter Nutzen:</h4>
            <ul style="font-size: 13px; margin: 0; padding-left: 20px;">
                <li>Zeitersparnis: {_hours_month} Stunden/Monat</li>
                <li>Jährliche Brutto-Zeitersparnis: ca. {_brutto_jahr_fmt}€ ({_hours_month}h × {stundensatz}€ × 12)</li>
                <li>Qualitätssteigerung bei Routineaufgaben</li>
            </ul>
            
            <h4 style="font-size: 13px; font-weight: 600; margin: 16px 0 8px 0;">Investition:</h4>
            <ul style="font-size: 13px; margin: 0; padding-left: 20px;">
                <li>Tool-Kosten: ca. {savings['tool_costs'] // 12}€/Monat (Organisation gesamt)</li>
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
    
    return html


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
            {"tag": 29, "aufgabe": "ROI der letzten 4 Wochen berechnen", "dauer": "20 Min", "kategorie": "Reflexion"},
            {"tag": 30, "aufgabe": "Nächste 30 Tage planen: Was wird Standard?", "dauer": "30 Min", "kategorie": "Planung"},
        ]
    }
}

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
}


def generate_30_tage_challenge_html(company_size: str = "solo") -> str:
    """
    Generiert die 30-Tage Challenge als HTML.
    """
    
    html = '''
    <div style="page-break-before: always;"></div>
    
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
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px;">
'''
    
    # Wochen-Übersicht
    wochen_farben = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]
    for i, (woche_key, woche_data) in enumerate(CHALLENGE_30_TAGE.items()):
        farbe = wochen_farben[i]
        html += f'''
        <div style="background: {farbe}15; border: 2px solid {farbe}; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 12px; font-weight: 600; color: {farbe}; text-transform: uppercase;">Woche {i+1}</div>
            <div style="font-size: 14px; font-weight: 700; color: #1e293b; margin: 4px 0;">{woche_data["titel"]}</div>
            <div style="font-size: 11px; color: #64748b;">{woche_data["ziel"]}</div>
        </div>
'''
    
    html += '''
    </div>
'''
    
    # Detaillierte Wochen
    for i, (woche_key, woche_data) in enumerate(CHALLENGE_30_TAGE.items()):
        farbe = wochen_farben[i]
        html += f'''
    <!-- WOCHE {i+1} -->
    <div style="margin-bottom: 20px;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: {farbe}; display: flex; align-items: center; gap: 8px;">
            <span style="background: {farbe}; color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 14px;">{i+1}</span>
            Woche {i+1}: {woche_data["titel"]}
        </h3>
        <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px;">
'''
        
        tage_list: List[Dict[str, Any]] = cast(List[Dict[str, Any]], woche_data["tage"])
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
            {"tag": 29, "aufgabe": "Gesamt-ROI berechnen", "dauer": "15 Min", "prio": True},
            {"tag": 30, "aufgabe": "Nächste Schritte planen", "dauer": "15 Min", "prio": True},
        ]
    }
}


def generate_30_tage_challenge_html_v2(
    company_size: str = "solo",
    zeitbudget: str = "2_5"
) -> str:
    """
    Generiert die 30-Tage Challenge angepasst ans Zeitbudget.
    
    Args:
        company_size: solo/team/kmu
        zeitbudget: unter_2/2_5/5_10/ueber_10
    """
    
    # Zeitbudget-Config holen
    zeit_config = ZEITBUDGET_CONFIG.get(zeitbudget, ZEITBUDGET_CONFIG["2_5"])
    
    # Challenge-Daten basierend auf Intensität wählen
    if zeit_config["intensitaet"] == "light":
        challenge_data = CHALLENGE_LIGHT
        show_prio = True
    else:
        challenge_data = CHALLENGE_30_TAGE
        show_prio = False
    
    html = f'''
    <div style="page-break-before: always;"></div>
    
    <!-- 30-TAGE CHALLENGE HEADER -->
    <div style="text-align: center; margin-bottom: 24px; padding-top: 20px;">
        <h2 style="font-size: 28px; font-weight: 700; margin: 0 0 8px 0; color: #1e40af;">
            🏆 Ihre 30-Tage KI-Challenge
        </h2>
        <p style="font-size: 16px; color: #64748b; margin: 0;">
            Von Null auf KI-Profi – angepasst an Ihr Zeitbudget
        </p>
    </div>
    
    <!-- ZEITBUDGET-INFO -->
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
    html += '''
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px;">
'''
    
    wochen_farben = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]
    for i, (woche_key, woche_data) in enumerate(challenge_data.items()):
        farbe = wochen_farben[i]
        html += f'''
        <div style="background: {farbe}15; border: 2px solid {farbe}; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="font-size: 12px; font-weight: 600; color: {farbe}; text-transform: uppercase;">Woche {i+1}</div>
            <div style="font-size: 14px; font-weight: 700; color: #1e293b; margin: 4px 0;">{woche_data["titel"]}</div>
        </div>
'''
    
    html += '''
    </div>
'''
    
    # Detaillierte Wochen
    for i, (woche_key, woche_data) in enumerate(challenge_data.items()):
        farbe = wochen_farben[i]
        html += f'''
    <div style="margin-bottom: 20px;">
        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 12px 0; color: {farbe};">
            Woche {i+1}: {woche_data["titel"]}
        </h3>
        <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px;">
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
    
    for w in range(1, 5):
        html += f'''
            <div style="text-align: center;">
                <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Woche {w}</div>
                <div style="border: 2px solid #22c55e; border-radius: 8px; padding: 12px; background: white;">
                    <div style="font-size: 10px; color: #64748b;">Gesparte Zeit:</div>
                    <div style="font-size: 16px; font-weight: 700; color: #166534;">_____ h</div>
                </div>
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
    
    html += '''
        </div>
        <div style="text-align: center; margin-top: 12px; padding-top: 12px; border-top: 1px solid #22c55e;">
            <span style="font-size: 14px; color: #166534; font-weight: 600;">
                🎯 Gesamt nach 30 Tagen: _______ Stunden = _______ € gespart
            </span>
        </div>
    </div>
'''
    
    return html


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


def generate_fallstudie_html(branche: str, size_key: str = "solo") -> str:
    """
    Generiert eine branchenspezifische, segment-aware Fallstudie.

    FIX-PERSONA: Uses _FALLSTUDIE_UNTERNEHMEN to pick a company description
    matching the user's size segment, avoiding persona leaks like
    "Solo-Berater" in a KMU report.
    """
    branche_key = get_branche_key(branche)
    fallstudie: Dict[str, Any] = cast(Dict[str, Any], FALLSTUDIEN.get(branche_key, FALLSTUDIEN["default"]))

    # FIX-PERSONA: Override "unternehmen" with segment-appropriate description
    size_overrides = _FALLSTUDIE_UNTERNEHMEN.get(branche_key, {})
    if size_key in size_overrides:
        fallstudie = {**fallstudie, "unternehmen": size_overrides[size_key]}
    
    html = f'''
    <!-- FALLSTUDIE -->
    <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px; margin-top: 24px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
            <span style="font-size: 24px;">📊</span>
            <h3 style="font-size: 18px; font-weight: 700; margin: 0; color: #1e293b;">
                Fallstudie: {fallstudie["titel"]}
            </h3>
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
'''
    
    return html
