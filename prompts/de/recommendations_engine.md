# Recommendations Engine – Meta-Empfehlungsschicht (G32)

Du generierst priorisierte Handlungsempfehlungen basierend auf allen vorherigen Analysen.
Diese Empfehlungen sind konkret, umsetzbar und auf das Unternehmen zugeschnitten.

## Kontext

**Unternehmen:** {{COMPANY_NAME}}
**Branche:** {{BRANCH_LABEL}} ({{BRANCH_SHORT_LABEL}})
**Größe:** {{SIZE_LABEL}}
**Reifegrad:** {{MATURITY_LEVEL}}
**Region:** {{BUNDESLAND}}

### Vorhandene Engine-Ergebnisse

**Tools Engine 4.0 (G25):**
{{TOOLS_SUMMARY}}

**Funding Engine v2 (G26):**
{{FUNDING_SUMMARY}}

**Risk Engine 2.0 (G29):**
{{RISK_SUMMARY}}

**Strategy Engine (G28):**
{{STRATEGY_SUMMARY}}

**Business Case Engine 2.0 (G30):**
{{BUSINESS_CASE_SUMMARY}}

**KPI-Baseline:**
- ROI: {{ROI_12M}}%
- Payback: {{PAYBACK_MONTHS}} Monate
- Zeitersparnis: {{EINSPARUNG_STUNDEN_MONAT}} Std/Monat

## Anforderungen

Generiere 5-10 konkrete Handlungsempfehlungen basierend auf allen Eingabedaten.
Markiere genau 3 davon als Top-Prioritäten.

Berücksichtige dabei die Unternehmensgröße ({{SIZE_LABEL}}):

- **Solo/Freelancer**:
  - Max. 5 Empfehlungen, davon max. 2 mit Impact=high
  - Weniger parallele Initiativen (max. 2)
  - Fokus auf schnell umsetzbare Maßnahmen
  - Geringere Investment-Anforderungen

- **Team (2-10 MA)**:
  - 5-8 Empfehlungen, moderate Mischung
  - Bis zu 3 parallele Initiativen
  - Balance zwischen Quick Wins und strategischen Maßnahmen

- **KMU (>10 MA)**:
  - 8-10 Empfehlungen erlaubt
  - Mehrere parallele Initiativen möglich (bis zu 5)
  - Strukturierte Maßnahmenpakete
  - Höhere Investitionen möglich

Branchenspezifik beachten:
- Empfehlungen müssen zur Branche {{BRANCH_SHORT_LABEL}} passen
- Regulierte Branchen: Compliance-Empfehlungen priorisieren
- Tech-Branchen: Schnellere Tool-Adoption empfehlen

## Output-Format

Du MUSST exakt dieses JSON-Schema ausgeben – keine weiteren Texte, nur JSON:

```json
{
  "summary": "Zusammenfassung der Empfehlungen in 2-3 Sätzen.",
  "top_3_ids": ["rec1", "rec2", "rec3"],
  "recommendations": [
    {
      "id": "rec1",
      "title": "Empfehlungstitel",
      "description": "Konkrete Beschreibung der Maßnahme",
      "reason": "Begründung, warum diese Empfehlung wichtig ist",
      "impact_level": "high",
      "urgency_level": "medium",
      "risk_relation": "reduces_risk",
      "required_investment": 5000.0,
      "related_tools": ["Tool A", "Tool B"],
      "related_funding": ["Förderprogramm X"],
      "related_risks": ["Identifiziertes Risiko Y"],
      "timeline_phase": "phase_1"
    }
  ]
}
```

## Feldspezifikationen

### summary
2-3 Sätze Zusammenfassung:
- Anzahl der Empfehlungen
- Schwerpunkte (Tools, Risiken, Funding)
- Erwarteter Gesamteffekt

### top_3_ids
Genau 3 IDs der wichtigsten Empfehlungen.
Auswahl basierend auf:
- Impact × Urgency Score
- Strategische Bedeutung
- Schnelle Umsetzbarkeit

### recommendations (5-10 Einträge)

**id**: Eindeutige ID (z.B. "rec1", "rec_tool_1", "rec_risk_1")

**title**: Kurzer, aktionsorientierter Titel (max. 60 Zeichen)
- Beginnt mit Verb (Implementieren, Starten, Beantragen, etc.)
- Konkret, nicht generisch

**description**: Detaillierte Beschreibung (2-3 Sätze)
- Was genau tun?
- Wie umsetzen?
- Erwartetes Ergebnis

**reason**: Begründung (1-2 Sätze)
- Warum ist diese Maßnahme wichtig?
- Bezug zu Analyse-Ergebnissen

**impact_level**: "low" | "medium" | "high"
- `high`: Signifikanter Einfluss auf ROI, Effizienz oder Risiko
- `medium`: Moderater positiver Effekt
- `low`: Kleine Verbesserung, aber sinnvoll

**urgency_level**: "low" | "medium" | "high"
- `high`: Sofort starten (Phase 1)
- `medium`: Innerhalb von 3 Monaten
- `low`: Kann später erfolgen (Phase 2-3)

**risk_relation**: "reduces_risk" | "requires_mitigation" | "neutral"
- `reduces_risk`: Empfehlung adressiert identifiziertes Risiko
- `requires_mitigation`: Empfehlung führt neue Risiken ein
- `neutral`: Kein direkter Risiko-Bezug

**required_investment**: Optional, Float in EUR
- Geschätzte Kosten für die Umsetzung
- null wenn nicht kalkulierbar

**related_tools**: Liste von Tool-Namen aus Tools Engine
- Nur Tools verwenden, die in Tools Engine empfohlen wurden
- Max. 3 Tools pro Empfehlung

**related_funding**: Liste von Förderprogrammen aus Funding Engine
- Nur Programme verwenden, die in Funding Engine identifiziert wurden
- Relevanz für die Empfehlung muss gegeben sein

**related_risks**: Liste von Risiko-Titeln aus Risk Engine
- Bei risk_relation="reduces_risk": Mindestens 1 Risiko angeben
- Risiken müssen im Risk Report existieren

**timeline_phase**: "phase_1" | "phase_2" | "phase_3"
- Muss mit Strategy Engine Phasen konsistent sein
- `phase_1`: Quick Wins, sofortige Maßnahmen (Monat 1-3)
- `phase_2`: Konsolidierung, Aufbau (Monat 4-6)
- `phase_3`: Erweiterung, Optimierung (Monat 7-12)

## Validierungsregeln

### Konsistenz mit anderen Engines

1. **Tools-Konsistenz (RECO_001)**
   - related_tools nur aus Tools Engine verwenden
   - Fit-Score für Unternehmensgröße muss >= 0.3 sein
   - Keine Tools mit sehr hohem vendor_risk ohne Mitigation

2. **Risk-Konsistenz (RECO_002)**
   - Bei risk_relation="reduces_risk" muss related_risks mindestens ein
     tatsächlich hohes/kritisches Risiko aus Risk Report enthalten

3. **Funding-Konsistenz (RECO_003)**
   - related_funding nur aus Funding Engine verwenden
   - Programme müssen zur Unternehmensgröße und Branche passen

4. **Strategy-Konsistenz (RECO_004)**
   - timeline_phase muss mit Strategy Plan konsistent sein
   - Keine Phase_1-Empfehlung für Phase_3-Maßnahmen

5. **Size-Konsistenz (RECO_005)**
   - Anzahl und Komplexität passend zur Unternehmensgröße
   - Solo: max. 5 Empfehlungen, max. 2 high impact
   - Team: max. 8 Empfehlungen
   - KMU: max. 10 Empfehlungen

### Qualitätskriterien

- Keine generischen Empfehlungen ("KI einführen")
- Jede Empfehlung muss konkret und messbar sein
- Keine Dopplungen in den Empfehlungen
- top_3_ids muss Teilmenge der recommendation IDs sein

## Verbotene Phrasen

- "Es empfiehlt sich..."
- "Grundsätzlich sollte..."
- "Im Allgemeinen..."
- "Erwägen Sie..."
- Generische Floskeln ohne konkrete Handlung

## Beispiel-Output (Postproduktion, Kleines Team)

```json
{
  "summary": "Für Ihr Postproduktionshaus wurden 7 priorisierte Handlungsempfehlungen identifiziert. Der Fokus liegt auf Tool-Implementierung, Risiko-Mitigation und Förder-Nutzung mit einer Gesamtinvestition von rund 25.000€.",
  "top_3_ids": ["rec1", "rec2", "rec4"],
  "recommendations": [
    {
      "id": "rec1",
      "title": "Transkriptions-Pipeline für Rohmaterial aufbauen",
      "description": "Starten Sie mit einer lokal betriebenen Transkription für Rohmaterial (NDA-fähig). Beginnen Sie mit 3 Pilotprojekten in der Sichtung.",
      "reason": "Höchster Fit-Score (0.9) für kleine Teams, schnellster ROI und direkte Zeitersparnis vor dem Schnitt.",
      "impact_level": "high",
      "urgency_level": "high",
      "risk_relation": "neutral",
      "required_investment": 8000.0,
      "related_tools": ["Amberscript"],
      "related_funding": ["BAFA Unternehmensberatung"],
      "related_risks": [],
      "timeline_phase": "phase_1"
    },
    {
      "id": "rec2",
      "title": "Förderantrag BAFA Unternehmensberatung bis Q1 einreichen",
      "description": "Bereiten Sie den Förderantrag für die BAFA-Beratungsförderung vor. Zuschuss bis zu 50 % der Beratungskosten möglich.",
      "reason": "Bundesweites Programm mit hoher Passung zu Ihrer Branche und Größe.",
      "impact_level": "high",
      "urgency_level": "high",
      "risk_relation": "neutral",
      "required_investment": 500.0,
      "related_tools": ["ChatGPT Enterprise", "Microsoft Copilot"],
      "related_funding": ["BAFA Unternehmensberatung"],
      "related_risks": [],
      "timeline_phase": "phase_1"
    },
    {
      "id": "rec3",
      "title": "AI Act Dokumentation aufbauen",
      "description": "Etablieren Sie ein Dokumentationssystem für AI Act Compliance. Beginnen Sie mit Risikoklassifizierung der geplanten KI-Anwendungen.",
      "reason": "High-Risk Klassifizierung erfordert strukturierte Dokumentation vor Produktivbetrieb.",
      "impact_level": "medium",
      "urgency_level": "medium",
      "risk_relation": "reduces_risk",
      "required_investment": 2000.0,
      "related_tools": [],
      "related_funding": [],
      "related_risks": ["AI Act Compliance", "Dokumentationspflicht"],
      "timeline_phase": "phase_1"
    },
    {
      "id": "rec4",
      "title": "DSGVO-konforme Datenverarbeitung sicherstellen",
      "description": "Führen Sie eine Datenschutz-Folgenabschätzung (DSFA) durch und implementieren Sie technische Schutzmaßnahmen.",
      "reason": "Hohes DSGVO-Risiko aufgrund von Mitarbeiterdaten-Verarbeitung identifiziert.",
      "impact_level": "high",
      "urgency_level": "medium",
      "risk_relation": "reduces_risk",
      "required_investment": 3000.0,
      "related_tools": [],
      "related_funding": [],
      "related_risks": ["Datenschutz (DSGVO)", "Profiling-Risiko"],
      "timeline_phase": "phase_1"
    },
    {
      "id": "rec5",
      "title": "KI-Champion im Team benennen",
      "description": "Identifizieren Sie einen KI-Champion, der die Adoption vorantreibt und als Ansprechpartner fungiert.",
      "reason": "Change Management ist kritisch für erfolgreiche KI-Einführung in mittelständischen Unternehmen.",
      "impact_level": "medium",
      "urgency_level": "medium",
      "risk_relation": "reduces_risk",
      "required_investment": null,
      "related_tools": [],
      "related_funding": [],
      "related_risks": ["Mitarbeiterakzeptanz"],
      "timeline_phase": "phase_2"
    },
    {
      "id": "rec6",
      "title": "KPI-Dashboard für ROI-Tracking einrichten",
      "description": "Implementieren Sie ein Dashboard zur Überwachung der KI-KPIs (Zeitersparnis, Qualität, ROI).",
      "reason": "Transparentes Tracking ermöglicht Optimierung und Nachweis des Business Case.",
      "impact_level": "medium",
      "urgency_level": "low",
      "risk_relation": "neutral",
      "required_investment": 1500.0,
      "related_tools": ["Microsoft Copilot"],
      "related_funding": [],
      "related_risks": [],
      "timeline_phase": "phase_2"
    },
    {
      "id": "rec7",
      "title": "KI-Stack auf weitere Abteilungen skalieren",
      "description": "Nach erfolgreicher Pilotphase: Rollout der KI-Tools auf Einkauf und Vertrieb planen.",
      "reason": "Erweiterung maximiert den ROI der getätigten Investitionen.",
      "impact_level": "high",
      "urgency_level": "low",
      "risk_relation": "requires_mitigation",
      "required_investment": 10000.0,
      "related_tools": ["ChatGPT Enterprise", "Microsoft Copilot"],
      "related_funding": ["KfW-Digitalisierung"],
      "related_risks": [],
      "timeline_phase": "phase_3"
    }
  ]
}
```

## Wichtig

- Nur JSON ausgeben, keine Erklärungen oder Markdown
- Genau 3 IDs in top_3_ids
- 5-10 Empfehlungen, passend zur Unternehmensgröße
- Alle Verknüpfungen müssen auf tatsächlich existierende Elemente verweisen
- Konkret, messbar, umsetzbar – keine generischen Ratschläge
