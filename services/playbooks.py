# -*- coding: utf-8 -*-
"""
Branchen‑Playbooks (Gold‑Standard+)
===================================
Erzeugt branchen‑spezifische Playbooks als valides HTML.
- Saubere Normalisierung von Branchenbezeichnungen
- 3–4 sofort einsetzbare Standard‑Workflows pro Branche
- Je Workflow: Ziel, Ablauf (Schritte), empfohlene Tools (EU/DSGVO‑freundlich), KPIs,
  Risiken & Mitigation (kurz)
- Keine externen Abhängigkeiten; reine HTML‑Erzeugung

Nutzung:
    from services.playbooks import build_playbooks_html, normalize_industry

    html = build_playbooks_html(branche="IT & Software", unternehmensgroesse="11–100")

Hinweis:
Die Tool‑Nennungen sind bewusst generisch (z. B. „EU‑RAG‑Stack“), damit die konkrete
Tooltabelle/Research separat aktuell eingespielt werden kann.
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Any
import html
import re


# ----------------------------- Normalisierung -----------------------------

_BRANCHE_MAP = {
    "beratung & dienstleistungen": "beratung",
    "beratung": "beratung",
    "it & software": "it",
    "it": "it",
    "handel & e-commerce": "handel",
    "handel & ecom": "handel",
    "e-commerce": "handel",
    "gesundheit & pflege": "gesundheit",
    "gesundheit": "gesundheit",
    "industrie & produktion": "industrie",
    "industrie": "industrie",
    "produktion": "industrie",
    "transport & logistik": "logistik",
    "logistik": "logistik",
    "marketing & werbung": "marketing",
    "marketing": "marketing",
    "werbung": "marketing",
    "finanzen & versicherungen": "finanzen",
    "finanzen": "finanzen",
    "versicherung": "finanzen",
    "bildung": "bildung",
    "verwaltung": "verwaltung",
    "bauwesen & architektur": "bau",
    "bau": "bau",
    "architektur": "bau",
    "medien & kreativwirtschaft": "medien",
    "medien": "medien",
    "kreativwirtschaft": "medien",
    "gastronomie & tourismus": "gastronomie",
    "gastronomie": "gastronomie",
    "tourismus": "gastronomie",
    "hotel": "gastronomie",
    "hotellerie": "gastronomie",
    "restaurant": "gastronomie",
}


def normalize_industry(value: str | None) -> str:
    if not value:
        return "beratung"
    v = re.sub(r"\s+", " ", value.strip().lower())
    return _BRANCHE_MAP.get(v, v.split(" ")[0])  # fallback: erstes Wort


# --------------------------- Datenbasis Playbooks --------------------------

# Für jede Branche: Liste von Playbooks (dict)
# Key-Namen sind stabil, damit PDF/Frontend darauf rendern kann.
Playbooks: Dict[str, List[Dict[str, Any]]] = {
    # Bereits vorhanden im ersten Paket: "beratung" – belassen + leicht gestrafft
    "beratung": [
        {
            "title": "Fragebogen ➝ Auswertung ➝ Handlungsempfehlungen (RAG‑gestützt)",
            "goal": "Schnelle, konsistente Erstberatung mit belastbaren Empfehlungen.",
            "steps": [
                "Intake‑Fragebogen finalisieren (rechtlich & fachlich geprüft).",
                "RAG‑Stack mit Domänenwissen (Policies, Templates, Cases) bereitstellen.",
                "Automatisierte Auswertung + Review‑Queue (4‑Augen‑Prinzip) etablieren.",
            ],
            "tools": [
                "EU‑RAG‑Stack (Open Source + EU‑Hosting)",
                "Workflow‑Automation (z. B. n8n, Make EU)",
                "Audit‑Trail & Versionierung (Git/Docs)"
            ],
            "kpis": [
                "⏱️ TTR (Time to Recommendation)",
                "✅ First‑Pass‑Approval‑Rate",
                "💶 Ersparnis/Monat (h, €)"
            ],
            "risks": [
                ("Halluzinationen", "Reviewer‑Gate + Zitierpflicht bei Empfehlungen"),
                ("Compliance‑Verstöße", "DPA/TOMs, Datenminimierung, Löschkonzept"),
                ("Tool‑Abhängigkeit", "Offene Schnittstellen, dokumentierte Exporte"),
            ],
        },
        {
            "title": "Kundenservice‑Assist (FAQ/Routing)",
            "goal": "Anfragen automatisch klassifizieren & beantworten.",
            "steps": [
                "Top‑10 FAQs + Vorlagen sammeln, Tonalität definieren.",
                "Intent‑Erkennung + Antwortmodule implementieren.",
                "Live‑Übergabe an Mensch bei Unsicherheit > Schwelle.",
            ],
            "tools": ["FAQ‑Bot (On‑Prem/ EU‑SaaS)", "Helpdesk‑Integration", "Analytics/KPI‑Board"],
            "kpis": ["🎯 Self‑Service‑Rate", "⏱️ Antwortzeit", "😊 CSAT/NPS"],
            "risks": [("Falschauskünfte", "Konfidenz‑Schwelle + Eskalation"), ("Bias", "Evaluation & Red‑Teaming")],
        },
        {
            "title": "Dokumenten‑KI (Verträge/Angebote)",
            "goal": "Wissensextraktion & Vorlagen‑Befüllung.",
            "steps": [
                "Dokumentenkorpus klassifizieren (sensibel/nicht sensibel).",
                "Extraktions‑Pipelines + Validierungsregeln erstellen.",
                "Vorlagen automatisiert ausfüllen, juristischer Check.",
            ],
            "tools": ["Doc‑AI (OCR+NLP)", "Vorlagen‑Engine", "Review‑Workflows"],
            "kpis": ["⏱️ Bearbeitungszeit", "🧪 Fehlerquote", "📈 Durchsatz/Monat"],
            "risks": [("Datenschutz", "PII‑Erkennung, Pseudonymisierung"), ("Vendorsperre", "Exportformate prüfen")],
        },
    ],

    # IT & Software
    "it": [
        {
            "title": "Dev‑Copilot & PR‑Reviewer",
            "goal": "Produktivität im Entwicklungsprozess steigern, Code‑Qualität sichern.",
            "steps": [
                "Coding‑Guidelines & Secure‑Defaults definieren.",
                "Copilot mit Unternehmenskontext (RAG) & Policies verbinden.",
                "Automatisierte PR‑Checks (Tests, SAST/DAST, Lizenz‑Scan).",
            ],
            "tools": ["IDE‑Copilot (EU‑Option)", "CI/CD‑Pipeline", "SAST/DAST‑Suite"],
            "kpis": ["⏱️ Cycle Time", "🐞 Defekte pro PR", "🧪 Test‑Coverage"],
            "risks": [("Lizenz‑Leaks", "Secret‑Scanner, Pre‑Commit Hooks"), ("Code‑Bias", "Review‑Standards/Pairing")],
        },
        {
            "title": "Incident‑Triage & Wissensbot (SRE)",
            "goal": "Störungen schneller erkennen, triagieren und lösen.",
            "steps": [
                "Log‑/Alert‑RAG mit Runbooks und Vorfällen verbinden.",
                "Root‑Cause‑Vorschläge + Standard‑Fixes generieren.",
                "Post‑Mortem‑Berichte automatisch erstellen.",
            ],
            "tools": ["Observability‑Stack", "RAG mit Runbooks", "ChatOps‑Bot"],
            "kpis": ["⏱️ MTTA/MTTR", "🔁 Wiederhol‑Incidents", "📚 Runbook‑Coverage"],
            "risks": [("Fehlalarme", "Konfidenz‑Schwellen, human‑in‑the‑loop"), ("Datenschutz", "PII‑Maskierung")],
        },
        {
            "title": "Produkt‑Discovery mit KI",
            "goal": "Kundenfeedback & Markt signaldicht auswerten.",
            "steps": [
                "Feedback‑Quellen anbinden (Tickets, App‑Reviews, Sales‑Notes).",
                "Themen‑Clustering & Impact‑Schätzung automatisieren.",
                "Roadmap‑Vorschläge priorisieren und validieren.",
            ],
            "tools": ["Vector DB", "Topic Modeling", "Product Analytics"],
            "kpis": ["🎯 Adoption", "📈 Feature‑Impact", "⏱️ Time‑to‑Insight"],
            "risks": [("Fehlinterpretation", "Stichproben‑Checks, AB‑Tests")],
        },
    ],

    # Handel & E‑Commerce
    "handel": [
        {
            "title": "Produktdaten‑Veredelung (PIM/RAG)",
            "goal": "Schnellere Listung, bessere SEO/Conversion.",
            "steps": [
                "Datenquellen harmonisieren (PIM/ERP).",
                "KI‑Texte & Attribute generieren, Redaktionsregeln anwenden.",
                "Bilder/Alt‑Texte & Übersetzungen automatisieren (EU‑Sprachen).",
            ],
            "tools": ["PIM‑Connector", "Gen‑AI Text/Bild", "QA‑Validator"],
            "kpis": ["🛒 Conversion‑Rate", "⏱️ Time‑to‑List", "🔎 SEO‑Visibility"],
            "risks": [("Fehlinfo", "Attribut‑Validierung & Haftungsklauseln"), ("Urheberrecht", "Bild‑Lizenzen prüfen")],
        },
        {
            "title": "Support‑Automation (Pre/Post‑Sale)",
            "goal": "Ticketvolumen senken, Zufriedenheit steigern.",
            "steps": [
                "FAQ‑Bot & Bestellstatus‑Abfragen integrieren.",
                "Retouren‑Logik & Kulanz‑Regeln abbilden.",
                "Feedback‑Schleife in PIM/CRM schließen.",
            ],
            "tools": ["Helpdesk‑Bot", "Order‑API", "NPS‑Survey"],
            "kpis": ["📉 Ticket‑Reduktion", "😊 CSAT/NPS", "⏱️ Antwortzeit"],
            "risks": [("Missbrauch", "Rate‑Limits & Fraud‑Checks"), ("Datenleck", "Token‑Scopes minimieren")],
        },
        {
            "title": "Preis‑/Promo‑Assistent",
            "goal": "Dynamische Preispunkte & Aktionen datengetrieben setzen.",
            "steps": [
                "Preis‑Historie & Wettbewerb scrapen (rechtskonform).",
                "Elastizitäts‑Modelle + Regeln definieren.",
                "Promos simulieren & ausrollen (AB‑Test).",
            ],
            "tools": ["Pricing‑Engine", "AB‑Testing", "Data Lake"],
            "kpis": ["📈 Deckungsbeitrag", "⏱️ Umsetzungszeit", "🧪 Promo‑Lifts"],
            "risks": [("Kartellrecht", "Compliance‑Leitplanken"), ("Fehlsteuerung", "Rollback‑Plan")],
        },
    ],

    # Gesundheit & Pflege
    "gesundheit": [
        {
            "title": "Dokumentations‑Assist (Anamnese/Bericht)",
            "goal": "Zeitersparnis in Pflege/Arztpraxis bei gleichzeitiger Qualitätssicherung.",
            "steps": [
                "Sprach‑/Text‑Intake mit medizinischen Formularen verbinden.",
                "Terminologie‑Normalisierung & Kodierung (ICD/OPS) halbautomatisieren.",
                "Review durch medizinisches Personal (Vier‑Augen‑Prinzip).",
            ],
            "tools": ["EU‑Speech‑to‑Text", "Terminologie‑Services", "Audit‑Trail"],
            "kpis": ["⏱️ Dokumentationszeit", "🧪 Korrekturquote", "😊 Patientenzufriedenheit"],
            "risks": [("Datenschutz", "DSFA, Pseudonymisierung, Zugriffskontrollen"), ("Haftung", "Freigabeprozess")],
        },
        {
            "title": "Termin-/Ressourcen‑Disposition",
            "goal": "Auslastung von Personal/Räumen/Equipment optimieren.",
            "steps": [
                "Echtzeit‑Kapazitäten und SLA‑Ziele definieren.",
                "Optimierungs‑Agent mit Regeln (Notfälle/Prio) einsetzen.",
                "Monitoring & Eskalation einführen.",
            ],
            "tools": ["Planungs‑Engine", "EHR/KIS‑Schnittstellen", "Dashboard"],
            "kpis": ["📅 Auslastung", "⏱️ Wartezeit", "📉 Ausfälle"],
            "risks": [("Fehlplanung", "Regeln + Override durch Personal"), ("Bias", "Fairness‑Checks")],
        },
        {
            "title": "Patienten‑Informationsbot (Aufklärung)",
            "goal": "Qualität & Konsistenz in der Aufklärung erhöhen.",
            "steps": [
                "Geprüfte Inhalte (Leitlinien) im RAG hinterlegen.",
                "Q&A‑Flows pro Behandlung definieren.",
                "Verständlichkeits‑Checks + Sprachen aktivieren.",
            ],
            "tools": ["RAG‑Stack (medizin‑geprüft)", "Messenger/Web", "Feedback‑Loop"],
            "kpis": ["😊 Verständnis‑Score", "📩 Rückfragen‑Rate", "⏱️ Beratungszeit"],
            "risks": [("Fehlinformation", "Zitierpflicht + menschliche Freigabe"), ("PII‑Risiko", "Datenminimierung")],
        },
    ],

    # Industrie & Produktion
    "industrie": [
        {
            "title": "Qualitätsprüfung (Visuelle Inspektion)",
            "goal": "Ausschuss reduzieren, Ursachen schneller erkennen.",
            "steps": [
                "Datenaufnahme (Kamera/Sensoren) standardisieren.",
                "Modelltraining & Drift‑Überwachung etablieren.",
                "Fehlerklassen in MES/ERP rückmelden.",
            ],
            "tools": ["Vision‑AI (On‑Edge)", "MES‑Connector", "Model Monitoring"],
            "kpis": ["📉 Ausschussquote", "⏱️ Prüfzeit", "💶 Nacharbeit"],
            "risks": [("Drift", "Kontinuierliche Evaluation"), ("Datensilos", "OT/IT‑Integration")],
        },
        {
            "title": "Wartungs‑Assist (Predictive)",
            "goal": "Stillstände vermeiden, Ersatzteile planen.",
            "steps": [
                "Sensorik/Logs erfassen & labeln.",
                "Anomalie‑/Prognose‑Modelle mit Wartungsplänen verbinden.",
                "Aufträge & Teile automatisch vorschlagen.",
            ],
            "tools": ["Time‑Series‑DB", "AutoML/Forecasting", "CMMS‑Integration"],
            "kpis": ["⏱️ Stillstandszeit", "🔧 Reaktionszeit", "💶 Teilebestand"],
            "risks": [("Fehlalarme", "Schwellen & menschliche Bestätigung"), ("Sicherheit", "Netzsegmentierung")],
        },
        {
            "title": "Arbeitsanweisungen & Schulung (AR/Assist)",
            "goal": "Einlernzeiten verkürzen, Qualität erhöhen.",
            "steps": [
                "Schritt‑für‑Schritt‑Anweisungen standardisieren.",
                "AR‑/Assist‑System verbinden (offline‑fähig).",
                "KVP‑Feedback einbauen.",
            ],
            "tools": ["AR‑Assist", "Wissens‑RAG", "Learning‑Hub"],
            "kpis": ["⏱️ Einlernzeit", "🧪 Fehlerquote", "📈 Produktivität"],
            "risks": [("Akzeptanz", "Usability + Schulung"), ("Datenschutz", "Kamera‑Zonen regeln")],
        },
    ],

    # Transport & Logistik
    "logistik": [
        {
            "title": "Routen‑/Flotten‑Optimierung",
            "goal": "Kilometer, Zeit & Emissionen reduzieren.",
            "steps": [
                "Echtzeit‑Daten (Verkehr, Wetter, Aufträge) integrieren.",
                "Optimierungs‑Modelle + Restriktionen (Fenster/ADR) anwenden.",
                "Disposition & Fahrer‑App anbinden.",
            ],
            "tools": ["Routing‑Engine", "Telematik", "Dispatch‑Portal"],
            "kpis": ["⛽ Verbrauch/Tour", "⏱️ Pünktlichkeit", "🌍 CO₂/Tonne"],
            "risks": [("Regelverstöße", "Compliance‑Regeln hard‑codieren"), ("Datenqualität", "Sensor‑Checks")],
        },
        {
            "title": "Lager‑Kommisionierung (Pick‑Assist)",
            "goal": "Wege & Fehler reduzieren.",
            "steps": [
                "Hit‑Maps erstellen, Pick‑Routen optimieren.",
                "Pick‑By‑Voice/Light/AR einführen.",
                "Inventur & Nachschub automatisieren.",
            ],
            "tools": ["WMS‑Integration", "AR/Voice", "Analytics"],
            "kpis": ["⏱️ Picks/Stunde", "🧪 Fehlerquote", "📦 Bestandstreue"],
            "risks": [("Ergonomie", "Usability‑Tests"), ("Systemausfall", "Fallback‑Prozesse")],
        },
        {
            "title": "Kundenkommunikation (Proaktiv)",
            "goal": "Transparenz & Zufriedenheit erhöhen.",
            "steps": [
                "Status‑Events triggern Benachrichtigungen.",
                "Self‑Service‑Portal/Chat mit RAG‑FAQ bereitstellen.",
                "Feedback in Dispo/CRM zurückspielen.",
            ],
            "tools": ["Event‑Bus", "Messaging", "RAG‑FAQ"],
            "kpis": ["😊 CSAT", "📞 Anrufvolumen", "⏱️ Reaktionszeit"],
            "risks": [("Fehlmeldungen", "Quellenvalidierung"), ("DSGVO", "Datenminimierung")],
        },
    ],

    # Marketing & Werbung
    "marketing": [
        {
            "title": "Content‑Factory (Multichannel)",
            "goal": "Skalierbare Content‑Produktion mit Markenkonsistenz.",
            "steps": [
                "Brand‑Guidelines + Style‑Prompts definieren.",
                "Themen‑Plan & Wiederverwertung (Atomisierung) autom.",
                "QA‑Gate (Faktencheck/Zitate) vor Veröffentlichung.",
            ],
            "tools": ["Gen‑AI Suite (EU)", "DAM/CMS", "Review‑Workflow"],
            "kpis": ["📈 Reichweite", "🧪 CTR/Conversion", "⏱️ Produktionszeit"],
            "risks": [("Markenrisiko", "Freigabestufen"), ("Urheberrecht", "Lizenzen/KI‑Assets kennzeichnen")],
        },
        {
            "title": "Lead‑Scoring & Nurturing",
            "goal": "Wachstum ohne Budget‑Verschwendung.",
            "steps": [
                "Datenqualität sichern (Duplikate/Opt‑ins).",
                "Score‑Modelle + Trigger‑Journeys, AB‑Tests.",
                "Sales‑Handoff & Attribution messen.",
            ],
            "tools": ["CRM/MA‑Suite", "Journey‑Builder", "CDP"],
            "kpis": ["📈 MQL➝SQL‑Rate", "💶 CPL/CPA", "⏱️ Time‑to‑First‑Contact"],
            "risks": [("DSGVO", "Einwilligung, DPA"), ("Überfrachtung", "Frequency‑Capping")],
        },
    ],

    # Finanzen & Versicherungen
    "finanzen": [
        {
            "title": "KYC/AML‑Assist",
            "goal": "Schnellere, sichere Prüfungen & Dokumentation.",
            "steps": [
                "Dokumente/Quellen anbinden, PII‑Erkennung.",
                "Risiko‑Scoring + Regeln, 4‑Augen‑Prinzip.",
                "Audit‑Trail & Reporting automatisieren.",
            ],
            "tools": ["OCR/KYC‑Suite", "Rules‑Engine", "Case‑Management"],
            "kpis": ["⏱️ Durchlaufzeit", "🧪 False Positives", "✅ Prüf‑Quote"],
            "risks": [("Regulatorik", "DPIA/ISMS, Explainability"), ("Datenhaltung", "EU‑Hosting")],
        },
        {
            "title": "Schaden‑Triage (Versicherungen)",
            "goal": "Bearbeitungszeit & Kosten senken.",
            "steps": [
                "Intake‑Bots & Formulare, Betrugsindikatoren.",
                "Dokumenten‑KI + Regeln, Priorisierung.",
                "Auszahlung/Weiterleitung, Qualitätssicherung.",
            ],
            "tools": ["Doc‑AI", "Fraud‑Signals", "BPM"],
            "kpis": ["⏱️ Bearbeitungszeit", "💶 Regulierungsquote", "🧪 Fehlerquote"],
            "risks": [("Bias", "regelmäßige Audits"), ("Beschwerden", "Transparenztexte")],
        },
    ],

    # Bildung
    "bildung": [
        {
            "title": "Lernmaterial‑Generator",
            "goal": "Individualisierte Übungen & Prüfungen erstellen.",
            "steps": [
                "Lehrplan & Kompetenzen in Wissens‑RAG ablegen.",
                "Items generieren (Bloom‑Stufen), Peer‑Review.",
                "Analytics zu Lernfortschritt bereitstellen.",
            ],
            "tools": ["RAG‑Bildung", "LMS‑Connector", "Analytics"],
            "kpis": ["📈 Lernfortschritt", "😊 Zufriedenheit", "⏱️ Vorbereitungszeit"],
            "risks": [("Bias", "Diversitäts‑Review"), ("PII", "Kinder‑/Jugend‑Schutz")],
        },
        {
            "title": "Assistive Services (Barrierefreiheit)",
            "goal": "Teilhabe verbessern (Live‑Transkript, Vereinfachte Sprache).",
            "steps": ["Speech‑to‑Text", "Simplified‑Language‑Adapter", "Nutzerfeedback sammeln"],
            "tools": ["Speech‑API (EU)", "Simplified‑Pipeline", "Frontend‑Widgets"],
            "kpis": ["👂 Verständlichkeit", "📈 Nutzung", "😊 Zufriedenheit"],
            "risks": [("Fehltranskripte", "Korrektur‑Interface"), ("Datenübertragung", "On‑Prem Optionen")],
        },
    ],

    # Verwaltung
    "verwaltung": [
        {
            "title": "Antrags‑Assist (Bürgerleistungen)",
            "goal": "Durchlaufzeiten und Rückfragen senken.",
            "steps": [
                "Formulare digitalisieren, Pflichtfelder validieren.",
                "RAG aus Rechtsgrundlagen/FAQ, Fallrouting.",
                "Transparente Status‑Updates an Bürger.",
            ],
            "tools": ["DMS/E‑Akte", "RAG‑Rechtsgrundlagen", "Prozess‑Automation"],
            "kpis": ["⏱️ Durchlaufzeit", "📉 Rückfragen", "😊 Zufriedenheit"],
            "risks": [("Rechtsfehler", "Juristic Review"), ("Alt‑Systeme", "Schnittstellen planen")],
        },
        {
            "title": "Schriftgut‑Automation",
            "goal": "Standardtexte & Bescheide fehlerarm erzeugen.",
            "steps": ["Textbausteine katalogisieren", "Vorlagen mit Regeln", "Stichproben‑Prüfung"],
            "tools": ["Text‑Engine", "DMS‑Connector", "Audit‑Trail"],
            "kpis": ["⏱️ Bearbeitungszeit", "🧪 Fehlerquote", "📦 Durchsatz"],
            "risks": [("Transparenz", "Begründungspflicht"), ("Sicherheit", "Zugriffsrollen")],
        },
    ],

    # Bauwesen & Architektur
    "bau": [
        {
            "title": "LV/Angebots‑Assist",
            "goal": "Ausschreibungen schneller beantworten, Risiken erkennen.",
            "steps": [
                "LV‑Parsing & Normen‑Mapping (DIN).",
                "Mengen/Leistungen kalkulieren, Alternativen vorschlagen.",
                "Freigabe & Angebotserstellung automatisieren.",
            ],
            "tools": ["Doc‑AI", "Kalkulations‑Engine", "DMS"],
            "kpis": ["⏱️ Angebotserstellung", "🧪 Nachträge", "💶 Marge"],
            "risks": [("Fehlmengen", "Plausibilitäts‑Checks"), ("Haftung", "Freigabestufen")],
        },
        {
            "title": "Bauüberwachung (Foto/Plan‑Abgleich)",
            "goal": "Abweichungen früh finden, Nacharbeit senken.",
            "steps": ["Fotodokumentation standardisieren", "Plan‑Abgleich KI", "Mängel‑Tickets"],
            "tools": ["Vision‑AI", "Ticketing", "Planserver"],
            "kpis": ["📉 Mängelquote", "⏱️ Reaktionszeit", "💶 Nachträge"],
            "risks": [("Haftung", "Beweisführung/Audit"), ("Datenschutz", "Personen/Nummern unkenntlich")],
        },
    ],

    # Gastronomie & Tourismus
    "gastronomie": [
        {
            "title": "Reservierungs‑ & Gäste‑Assist",
            "goal": "Buchungen automatisieren, No‑Shows reduzieren, Gästebindung erhöhen.",
            "steps": [
                "Online‑Buchungssystem mit Echtzeit‑Verfügbarkeit anbinden.",
                "KI‑Chatbot für Reservierungen, FAQ & Sonderwünsche.",
                "Automatische Erinnerungen & Feedback‑Abfrage nach Besuch.",
            ],
            "tools": ["Booking‑Engine (EU‑SaaS)", "Chatbot/Messenger", "CRM/Gästedatenbank"],
            "kpis": ["📅 Buchungsrate", "📉 No‑Show‑Rate", "😊 Gästezufriedenheit"],
            "risks": [("Datenschutz", "DSGVO‑konforme Gästedaten, Löschkonzept"), ("Fehlbuchungen", "Validierung & Override")],
        },
        {
            "title": "Speisekarten‑ & Angebotsoptimierung",
            "goal": "Margen verbessern, saisonale Anpassungen beschleunigen.",
            "steps": [
                "Verkaufsdaten & Wareneinsatz analysieren.",
                "KI‑gestützte Menü‑Empfehlungen & Preisoptimierung.",
                "Automatische Übersetzung & Allergen‑Kennzeichnung.",
            ],
            "tools": ["POS‑Analytics", "Kalkulations‑Tool", "Übersetzungs‑API"],
            "kpis": ["💶 Deckungsbeitrag/Gericht", "📈 Durchschnittlicher Bon", "⏱️ Menü‑Update‑Zeit"],
            "risks": [("Fehlkalkulation", "Warenwirtschafts‑Abgleich"), ("Allergene", "Pflicht‑Review durch Küche")],
        },
        {
            "title": "Bewertungsmanagement & Reputation",
            "goal": "Online‑Reputation aktiv steuern, Gästefeedback nutzen.",
            "steps": [
                "Bewertungsportale zentral monitoren (Google, TripAdvisor, etc.).",
                "KI‑Antwortvorschläge für Bewertungen generieren.",
                "Sentiment‑Analyse für Verbesserungsmaßnahmen.",
            ],
            "tools": ["Review‑Monitoring", "KI‑Textassistent", "Dashboard"],
            "kpis": ["⭐ Durchschnittsbewertung", "⏱️ Antwortzeit", "📈 Bewertungsanzahl"],
            "risks": [("Authentizität", "Menschliche Freigabe"), ("Negative PR", "Eskalationsregeln")],
        },
    ],

    # Medien & Kreativwirtschaft
    "medien": [
        {
            "title": "Post‑Production‑Assist (Video/Audio)",
            "goal": "Schnitt, Untertitel, Versionierung beschleunigen.",
            "steps": [
                "Asset‑Ingest & Rechteverwaltung.",
                "Auto‑Schnitt/Transkript/Untertitel mehrsprachig.",
                "QC‑Gate & Master‑Export automatisieren.",
            ],
            "tools": ["Media‑Suite", "Speech/Subtitle", "DAM"],
            "kpis": ["⏱️ Produktionszeit", "🧪 QC‑Fehler", "📦 Ausspielungen"],
            "risks": [("Rechte", "Lizenzen/Model Releases"), ("Fehlübersetzungen", "Korrektur‑Workflow")],
        },
        {
            "title": "News‑Briefing‑Bot (Redaktion)",
            "goal": "Recherche bündeln, Falschmeldungen minimieren.",
            "steps": ["Whitelist‑Recherche", "Quellenbewertung", "Zitierpflicht & Link‑Ausgabe"],
            "tools": ["Research‑Policy", "RAG‑Archiv", "Fact‑Checker"],
            "kpis": ["⏱️ Time‑to‑Briefing", "🧪 Korrekturquote", "🔁 Quellen‑Diversität"],
            "risks": [("Desinformation", "Mehrquellen‑Pflicht"), ("Urheberrecht", "Snippet‑Länge begrenzen")],
        },
    ],
}


def _html_escape_list(items: List[str]) -> str:
    return "".join(f"<li>{html.escape(x)}</li>" for x in items)


def _html_risks(risks: List[Tuple[str, str]]) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(r)}</td><td>{html.escape(m)}</td></tr>"
        for r, m in risks
    )
    return (
        "<table class='table table-modern'><thead><tr><th>Risiko</th><th>Mitigation</th>"
        "</tr></thead><tbody>" + rows + "</tbody></table>"
    )


def build_playbooks_html(branche: str | None, unternehmensgroesse: str | None = None) -> str:
    """
    Liefert das HTML für die gewählte Branche.
    Der Parameter unternehmensgroesse kann für zukünftige Feinabstimmungen genutzt werden.
    """
    bkey = normalize_industry(branche)
    playbooks = Playbooks.get(bkey) or Playbooks["beratung"]

    blocks = []
    for pb in playbooks:
        blocks.append(
            "<div class='card'>"
            f"<h3>{html.escape(pb['title'])}</h3>"
            f"<p><strong>Ziel:</strong> {html.escape(pb['goal'])}</p>"
            f"<h4>Ablauf</h4><ol>{_html_escape_list(pb['steps'])}</ol>"
            f"<p><strong>Empfohlene Tools:</strong> {html.escape(', '.join(pb['tools']))}</p>"
            f"<p><strong>KPI‑Vorschläge:</strong> {html.escape(', '.join(pb['kpis']))}</p>"
            f"<h4>Risiken & Mitigation</h4>{_html_risks(pb['risks'])}"
            "</div>"
        )

    intro = (
        f"<p>Playbooks für <strong>{html.escape(branche or 'Ihre Branche')}</strong>. "
        "Die Workflows sind praxiserprobt, DSGVO‑sensibel und auf schnelle Wirkung ausgelegt.</p>"
    )
    return intro + "".join(blocks)
