"""
SOFORT-START-SEITE Generator
=============================
Generiert personalisierte "Sofort-Start" Inhalte für den KI-Readiness Report.

Enthält:
1. Der EINE erste Schritt (heute machbar)
2. 3 Copy-Paste Prompts für die Hauptleistung
3. Tool-Empfehlungen mit Links & Preisen
4. Wichtige Warnungen (Don'ts)
"""

import logging
from typing import Optional

log = logging.getLogger(__name__)

# =============================================================================
# BRANCHEN-SPEZIFISCHE PROMPTS
# =============================================================================

BRANCHE_PROMPTS = {
    "beratung": {
        "name": "Beratung & Consulting",
        "erster_schritt": "Lassen Sie ChatGPT Ihre nächste Kundenanfrage analysieren",
        "prompts": [
            {
                "titel": "Kundenanfrage analysieren",
                "prompt": """Analysiere diese Kundenanfrage und erstelle eine strukturierte Bedarfsanalyse:

[ANFRAGE HIER EINFÜGEN]

Bitte liefere:
1. Kernproblem in einem Satz
2. 3 mögliche Lösungsansätze
3. Geschätzter Aufwand (Stunden)
4. Empfohlene nächste Schritte""",
                "zeitersparnis": "30-45 Min pro Anfrage"
            },
            {
                "titel": "Angebot strukturieren",
                "prompt": """Erstelle eine Angebotsstruktur für folgendes Projekt:

Kunde: [NAME]
Branche: [BRANCHE]
Problem: [KURZBESCHREIBUNG]
Budget-Rahmen: [FALLS BEKANNT]

Liefere:
1. Executive Summary (3 Sätze)
2. Leistungsumfang (Bullet Points)
3. Zeitplan mit Meilensteinen
4. Investitionsübersicht""",
                "zeitersparnis": "1-2 Std pro Angebot"
            },
            {
                "titel": "Meeting-Protokoll erstellen",
                "prompt": """Erstelle aus diesen Meeting-Notizen ein professionelles Protokoll:

[NOTIZEN HIER EINFÜGEN]

Format:
- Datum, Teilnehmer, Dauer
- Besprochene Themen (nummeriert)
- Entscheidungen (fett markiert)
- Action Items mit Verantwortlichen und Deadline
- Nächster Termin""",
                "zeitersparnis": "20-30 Min pro Meeting"
            }
        ]
    },
    "it": {
        "name": "IT & Software",
        "erster_schritt": "Lassen Sie ChatGPT Ihren nächsten Code-Review unterstützen",
        "prompts": [
            {
                "titel": "Code Review",
                "prompt": """Überprüfe diesen Code auf:
1. Bugs und potenzielle Fehler
2. Performance-Probleme
3. Security-Risiken
4. Best Practices

[CODE HIER EINFÜGEN]

Liefere konkrete Verbesserungsvorschläge mit Codebeispielen.""",
                "zeitersparnis": "30-60 Min pro Review"
            },
            {
                "titel": "Technische Dokumentation",
                "prompt": """Erstelle eine technische Dokumentation für:

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
                "prompt": """Erstelle User Stories für dieses Feature:

Feature: [NAME]
Zielgruppe: [WER]
Problem: [WAS WIRD GELÖST]

Format pro Story:
- Als [Rolle] möchte ich [Funktion], damit [Nutzen]
- Akzeptanzkriterien (3-5 Punkte)
- Geschätzter Aufwand (S/M/L)""",
                "zeitersparnis": "30-45 Min pro Feature"
            }
        ]
    },
    "marketing": {
        "name": "Marketing & Kommunikation",
        "erster_schritt": "Lassen Sie ChatGPT 5 Social-Media-Posts für diese Woche erstellen",
        "prompts": [
            {
                "titel": "Social Media Posts",
                "prompt": """Erstelle 5 LinkedIn-Posts für diese Woche:

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
                "prompt": """Erstelle einen Newsletter:

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
                "prompt": """Analysiere diese Wettbewerber-Website:

URL: [LINK oder BESCHREIBUNG]
Mein Unternehmen: [KURZBESCHREIBUNG]

Analysiere:
1. Positionierung & USP
2. Zielgruppen-Ansprache
3. Content-Strategie
4. Stärken/Schwächen
5. Was können wir besser machen?""",
                "zeitersparnis": "2-3 Std pro Analyse"
            }
        ]
    },
    "handel": {
        "name": "Handel & E-Commerce",
        "erster_schritt": "Lassen Sie ChatGPT 10 Produktbeschreibungen optimieren",
        "prompts": [
            {
                "titel": "Produktbeschreibung optimieren",
                "prompt": """Optimiere diese Produktbeschreibung für SEO und Conversion:

Produkt: [NAME]
Kategorie: [KATEGORIE]
Aktuelle Beschreibung: [TEXT]
Zielgruppe: [WER KAUFT DAS?]

Liefere:
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
                "titel": "Angebotstext erstellen",
                "prompt": """Erstelle einen überzeugenden Angebotstext:

Aktion: [z.B. 20% Rabatt, Gratis Versand]
Produkte: [WELCHE]
Zeitraum: [VON-BIS]
Zielgruppe: [WER]

Liefere:
1. Headline (max. 8 Wörter)
2. Subheadline
3. 3 Bullet Points mit Benefits
4. CTA-Text
5. Kleingedrucktes""",
                "zeitersparnis": "20-30 Min pro Aktion"
            }
        ]
    },
    "default": {
        "name": "Allgemein",
        "erster_schritt": "Lassen Sie ChatGPT Ihre nächste E-Mail schreiben",
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
                "prompt": """Fasse diesen Text zusammen:

[TEXT HIER EINFÜGEN]

Liefere:
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

Liefere:
1. 10 kreative Ideen (auch unkonventionelle)
2. Pro/Contra für die Top 3
3. Empfehlung zum Starten""",
                "zeitersparnis": "30-45 Min pro Session"
            }
        ]
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
        "text": "Geben Sie NIEMALS Kundendaten, Passwörter oder vertrauliche Geschäftszahlen in KI-Tools ein."
    },
    {
        "icon": "🔍",
        "titel": "Immer prüfen",
        "text": "Vertrauen Sie KI-generierten Zahlen, Fakten und Zitaten nicht blind – immer gegenchecken."
    },
    {
        "icon": "🎯",
        "titel": "Klein starten",
        "text": "Beginnen Sie mit einfachen Aufgaben, nicht mit dem komplexesten Projekt."
    }
]

# =============================================================================
# HTML GENERATOR
# =============================================================================

def get_branche_key(branche: str) -> str:
    """Mappt Branche auf den passenden Key."""
    branche_lower = branche.lower() if branche else ""
    
    if any(x in branche_lower for x in ["berat", "consult", "coach"]):
        return "beratung"
    elif any(x in branche_lower for x in ["it", "software", "tech", "digital", "web"]):
        return "it"
    elif any(x in branche_lower for x in ["marketing", "kommunikation", "pr", "werbung", "media"]):
        return "marketing"
    elif any(x in branche_lower for x in ["handel", "shop", "commerce", "retail", "verkauf"]):
        return "handel"
    else:
        return "default"


def generate_sofort_start_html(
    hauptleistung: str,
    branche: str,
    company_size: str = "solo",
    zeitersparnis_prioritaet: str = ""
) -> str:
    """
    Generiert die SOFORT_START_HTML Section.
    
    Args:
        hauptleistung: Das Kerngeschäft des Users
        branche: Die Branche
        company_size: solo/team/kmu
        zeitersparnis_prioritaet: Was der User als Zeitfresser angegeben hat
        
    Returns:
        HTML-String für die Sofort-Start-Seite
    """
    
    branche_key = get_branche_key(branche)
    branche_data = BRANCHE_PROMPTS.get(branche_key, BRANCHE_PROMPTS["default"])
    
    # Company size normalisieren
    size_key = "solo"
    if company_size and "team" in company_size.lower():
        size_key = "team"
    elif company_size and ("kmu" in company_size.lower() or "mittel" in company_size.lower() or "100" in str(company_size)):
        size_key = "kmu"
    
    tools = TOOL_EMPFEHLUNGEN.get(size_key, TOOL_EMPFEHLUNGEN["solo"])
    
    # Personalisiere den ersten Schritt wenn möglich
    erster_schritt = branche_data["erster_schritt"]
    if hauptleistung:
        erster_schritt = f"Testen Sie ChatGPT mit einer typischen Aufgabe aus {hauptleistung}"
    
    # HTML generieren
    html = f'''
    <!-- ERSTER SCHRITT -->
    <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 12px; padding: 24px; margin-bottom: 24px; color: white;">
        <div style="display: flex; align-items: flex-start; gap: 16px;">
            <span style="font-size: 32px;">⚡</span>
            <div>
                <h3 style="font-size: 18px; font-weight: 700; margin: 0 0 8px 0; color: white;">
                    Der EINE erste Schritt
                </h3>
                <p style="font-size: 15px; margin: 0; opacity: 0.95; line-height: 1.5;">
                    {erster_schritt}
                </p>
            </div>
        </div>
    </div>
    
    <!-- 3 PROMPTS -->
    <div style="margin-bottom: 24px;">
        <h3 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 24px;">📋</span>
            3 Copy-Paste Prompts für Sie
        </h3>
        <p style="font-size: 13px; color: #64748b; margin: 0 0 16px 0;">
            Kopieren Sie diese Prompts direkt in ChatGPT oder Claude:
        </p>
'''
    
    # Prompts hinzufügen
    for i, prompt_data in enumerate(branche_data["prompts"], 1):
        html += f'''
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <h4 style="font-size: 14px; font-weight: 600; margin: 0; color: #1e293b;">
                    {i}. {prompt_data["titel"]}
                </h4>
                <span style="font-size: 11px; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px;">
                    ⏱️ {prompt_data["zeitersparnis"]}
                </span>
            </div>
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; font-family: monospace; font-size: 11px; line-height: 1.5; white-space: pre-wrap; color: #334155;">
{prompt_data["prompt"][:500]}{"..." if len(prompt_data["prompt"]) > 500 else ""}
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
    
    for tool in tools[:2]:  # Max 2 Tools
        html += f'''
            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
                <h4 style="font-size: 15px; font-weight: 600; margin: 0 0 4px 0; color: #1e293b;">
                    {tool["name"]}
                </h4>
                <p style="font-size: 13px; color: #64748b; margin: 0 0 8px 0;">
                    {tool["nutzen"]}
                </p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px; font-weight: 600; color: #1e40af;">
                        {tool["preis"]}
                    </span>
                    <span style="font-size: 11px; color: #64748b;">
                        {tool["url"].replace("https://", "")}
                    </span>
                </div>
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
    
    log.info(f"[SOFORT-START] Generated for branche={branche_key}, size={size_key}, hauptleistung={hauptleistung[:30] if hauptleistung else 'N/A'}...")
    
    return html
