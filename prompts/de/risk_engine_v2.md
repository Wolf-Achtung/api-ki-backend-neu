# Risk Engine 2.0 – Konsolidierte Risikoanalyse (G29)

Du generierst eine strukturierte JSON-Risikoanalyse für ein KI-Projekt.
Diese Analyse fasst AI Act, DSGVO, Vendor- und Use-Case-Risiken zusammen.

## Kontext

**Unternehmen:** {{COMPANY_NAME}}
**Branche:** {{BRANCH_LABEL}} ({{BRANCH_SHORT_LABEL}})
**Größe:** {{SIZE_LABEL}}
**Reifegrad:** {{MATURITY_LEVEL}}
**Region:** {{BUNDESLAND}}

### Vorhandene Analysedaten

**Branch Deep Dive:**
{{BRANCH_DEEP_DIVE_SUMMARY}}

**KPI-Baseline:**
- ROI: {{ROI_12M}}%
- Payback: {{PAYBACK_MONTHS}} Monate
- Zeitersparnis: {{EINSPARUNG_STUNDEN_MONAT}} Std/Monat

**Tools Engine 4.0 Ergebnisse:**
{{TOOLS_SUMMARY}}

**Funding Engine v2 Ergebnisse:**
{{FUNDING_SUMMARY}}

**Strategy Plan (falls vorhanden):**
{{STRATEGY_SUMMARY}}

## Anforderungen

Analysiere alle Eingabedaten und erstelle eine umfassende Risikoanalyse.
Berücksichtige dabei die Unternehmensgröße ({{SIZE_LABEL}}):
- **Solo**: Fokus auf einfache Umsetzbarkeit, geringe Ressourcen
- **Team**: Fokus auf Koordination, mittlere Compliance-Anforderungen
- **KMU**: Vollständige Compliance-Anforderungen, strukturierte Prozesse

Berücksichtige die Branche ({{BRANCH_SHORT_LABEL}}):
- Regulierte Branchen (Medizin, Finanzen, Recht) haben höhere Risiken
- Tech-Branchen haben oft niedrigere Einstiegshürden

## Output-Format

Du MUSST exakt dieses JSON-Schema ausgeben – keine weiteren Texte, nur JSON:

```json
{
  "ai_act_class": "minimal|limited|high_risk|unacceptable",
  "ai_act_reasons": [
    "Grund 1 für die Klassifizierung",
    "Grund 2 für die Klassifizierung"
  ],
  "ai_act_required_controls": [
    "Erforderliche Maßnahme 1",
    "Erforderliche Maßnahme 2"
  ],
  "dsgvo_risk_level": "niedrig|mittel|hoch",
  "dsgvo_risk_factors": [
    "DSGVO-Risikofaktor 1",
    "DSGVO-Risikofaktor 2"
  ],
  "vendor_category": "eu_compliant|us_with_dpa|us_standard|unknown_vendor",
  "vendor_risk_score": 3,
  "vendor_flags": [
    "Vendor-Hinweis 1",
    "Vendor-Hinweis 2"
  ],
  "use_case_risks": [
    {
      "title": "Risikotitel",
      "description": "Beschreibung des Risikos",
      "category": "technical|organizational|legal|financial"
    }
  ],
  "risk_matrix": [
    {
      "id": "R1_EXAMPLE",
      "title": "Risikotitel",
      "likelihood": 3,
      "impact": 4,
      "color": "medium",
      "description": "Kurzbeschreibung"
    }
  ],
  "narrative_summary": "Zusammenfassende Bewertung in 2-3 Sätzen."
}
```

## Feldspezifikationen

### ai_act_class
- `unacceptable`: Verbotene Anwendungen (Social Scoring, Emotionserkennung am Arbeitsplatz)
- `high_risk`: Anhang III Anwendungen (HR-Entscheidungen, Kreditvergabe, Medizin, kritische Infrastruktur)
- `limited`: Transparenzpflichtige Systeme (Chatbots, Deep Fakes, Emotionserkennung)
- `minimal`: Keine besonderen Anforderungen

### ai_act_reasons (2-4 Gründe)
Erkläre konkret, warum diese Klassifizierung zutrifft.

### ai_act_required_controls (2-4 Maßnahmen)
Bei high_risk: Dokumentation, Risikomanagement, Logging, Human Oversight
Bei limited: Transparenzhinweise, Kennzeichnung
Bei minimal: Empfohlene Best Practices

### dsgvo_risk_level
- `hoch`: Sensible Daten, automatisierte Entscheidungen, Profiling, Kinder-Daten
- `mittel`: Personenbezogene Daten mit Standard-Schutzmaßnahmen
- `niedrig`: Keine/minimale personenbezogene Daten

### dsgvo_risk_factors (1-4 Faktoren)
Konkrete Risiken wie "Verarbeitung von Gesundheitsdaten", "Automatisierte Profilbildung"

### vendor_category
- `eu_compliant`: EU-Anbieter mit voller DSGVO-Konformität
- `us_with_dpa`: US-Anbieter mit Data Processing Agreement
- `us_standard`: US-Anbieter ohne besondere Schutzmaßnahmen
- `unknown_vendor`: Ungeprüfte/unbekannte Anbieter

### vendor_risk_score (1-5)
1 = Sehr niedrig (EU-Anbieter, lokales Hosting)
5 = Sehr hoch (Unbekannter Anbieter, kein DPA)

### vendor_flags (0-4 Hinweise)
Konkrete Warnungen wie "Tool X: Kein EU-Hosting", "Tool Y: Compliance-Score 4/5"

### use_case_risks (2-5 Risiken)
Spezifische Risiken für die geplanten KI-Anwendungen.
Categories: technical, organizational, legal, financial

### risk_matrix (3-6 Einträge)
Hauptrisiken mit Likelihood (1-5) und Impact (1-5).
IDs: R1_*, R2_*, etc.
Colors: low (Score 1-4), medium (5-9), high (10-16), critical (17-25)

Pflicht-Risiken:
1. AI Act Compliance
2. Datenschutz (DSGVO)
3. Vendor & Hosting
Plus 1-3 branchenspezifische oder use-case-spezifische Risiken.

### narrative_summary
2-3 Sätze Gesamtbewertung. Keine Floskeln. Konkret und handlungsorientiert.

## Verbotene Phrasen

- "Es ist wichtig zu beachten..."
- "Zusammenfassend lässt sich sagen..."
- "Im Allgemeinen..."
- Generische Floskeln

## Beispiel-Output (KMU Beratung, High-Risk)

```json
{
  "ai_act_class": "high_risk",
  "ai_act_reasons": [
    "Einsatz von KI für Bewerbervorauswahl (Anhang III, Punkt 4a)",
    "Automatisierte Leistungsbewertung von Mitarbeitern"
  ],
  "ai_act_required_controls": [
    "Risikomanagementsystem nach Art. 9 AI Act",
    "Qualitätsmanagementsystem für KI-Systeme",
    "Logging und Nachvollziehbarkeit aller Entscheidungen",
    "Human-in-the-Loop für kritische Entscheidungen"
  ],
  "dsgvo_risk_level": "hoch",
  "dsgvo_risk_factors": [
    "Verarbeitung von Bewerberdaten (Art. 9 DSGVO)",
    "Automatisierte Entscheidungsfindung nach Art. 22 DSGVO",
    "Profiling von Mitarbeitern"
  ],
  "vendor_category": "us_with_dpa",
  "vendor_risk_score": 3,
  "vendor_flags": [
    "OpenAI: US-Anbieter mit DPA, EU-Datenverarbeitung möglich",
    "HubSpot: US-Anbieter, Standard Contractual Clauses erforderlich"
  ],
  "use_case_risks": [
    {
      "title": "Diskriminierungsrisiko bei HR-KI",
      "description": "KI-gestützte Bewerberauswahl kann unbeabsichtigte Bias enthalten",
      "category": "legal"
    },
    {
      "title": "Mitarbeiterakzeptanz",
      "description": "KI-Monitoring kann zu Widerstand im Team führen",
      "category": "organizational"
    }
  ],
  "risk_matrix": [
    {
      "id": "R1_AI_ACT",
      "title": "AI Act Compliance",
      "likelihood": 4,
      "impact": 4,
      "color": "high",
      "description": "High-Risk Klassifizierung erfordert umfangreiche Maßnahmen"
    },
    {
      "id": "R2_DSGVO",
      "title": "Datenschutz (DSGVO)",
      "likelihood": 3,
      "impact": 5,
      "color": "high",
      "description": "Sensible HR-Daten erfordern besondere Schutzmaßnahmen"
    },
    {
      "id": "R3_VENDOR",
      "title": "Vendor & Hosting",
      "likelihood": 2,
      "impact": 3,
      "color": "medium",
      "description": "US-Anbieter mit DPA, kontrollierbares Risiko"
    },
    {
      "id": "R4_BIAS",
      "title": "Algorithmic Bias",
      "likelihood": 3,
      "impact": 4,
      "color": "high",
      "description": "HR-KI muss auf Fairness geprüft werden"
    }
  ],
  "narrative_summary": "Die geplanten KI-Anwendungen fallen unter die High-Risk Kategorie des AI Act aufgrund des HR-Einsatzes. Umfangreiche Dokumentations- und Kontrollpflichten sind erforderlich. Vor Produktivbetrieb sollte eine DSFA durchgeführt und ein Risikomanagementsystem etabliert werden."
}
```

## Wichtig

- Nur JSON ausgeben, keine Erklärungen oder Markdown
- Alle Felder müssen vorhanden sein
- Likelihood und Impact: Integer 1-5
- vendor_risk_score: Integer 1-5
- Konsistenz zwischen Feldern (high_risk → entsprechende Controls)
