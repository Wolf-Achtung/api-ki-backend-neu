# Business Case Engine 2.0 – ROI-Simulation & Szenarien (G30)

Du generierst eine strukturierte JSON Business Case Analyse für ein KI-Projekt.
Diese Analyse beinhaltet 3 Szenarien, 12-Monats-KPI-Forecasts und konsolidierte ROI-Berechnungen.

## Kontext

**Unternehmen:** {{COMPANY_NAME}}
**Branche:** {{BRANCH_LABEL}} ({{BRANCH_SHORT_LABEL}})
**Größe:** {{SIZE_LABEL}}
**Reifegrad:** {{MATURITY_LEVEL}}
**Region:** {{BUNDESLAND}}

### Vorhandene Analysedaten

**Branch Deep Dive:**
{{BRANCH_DEEP_DIVE_SUMMARY}}

**Aktuelle KPI-Baseline:**
- ROI-Schätzung: {{ROI_12M}}%
- Payback-Schätzung: {{PAYBACK_MONTHS}} Monate
- Zeitersparnis: {{EINSPARUNG_STUNDEN_MONAT}} Std/Monat
- Monatliche Ersparnis: {{EINSPARUNG_MONAT_EUR}} €

**Tools Engine 4.0 Ergebnisse:**
{{TOOLS_SUMMARY}}

**Funding Engine v2 Ergebnisse:**
{{FUNDING_SUMMARY}}

**Strategy Plan (falls vorhanden):**
{{STRATEGY_SUMMARY}}

**Risk Engine v2 Ergebnisse:**
{{RISK_SUMMARY}}

## Anforderungen

Erstelle einen detaillierten Business Case basierend auf allen Eingabedaten.
Berücksichtige dabei die Unternehmensgröße ({{SIZE_LABEL}}):

- **Solo/Freelancer**:
  - Kleine, pragmatische Investments (500-5.000€)
  - Schneller Payback wichtiger als hoher ROI
  - Fokus auf Quick Wins und sofortige Zeitersparnis
  - Geringe laufende Kosten

- **Team (2-10 MA)**:
  - Moderate Investments (2.000-20.000€)
  - Balance zwischen ROI und Implementierungsaufwand
  - Skalierbare Lösungen bevorzugen
  - Teamadoption berücksichtigen

- **KMU (>10 MA)**:
  - Größere Investments möglich (10.000-100.000€)
  - Strukturierte ROI-Analyse erforderlich
  - Compliance-Kosten einbeziehen
  - Change Management berücksichtigen

## Output-Format

Du MUSST exakt dieses JSON-Schema ausgeben – keine weiteren Texte, nur JSON:

```json
{
  "baseline_monthly_cost": 5000.0,
  "baseline_effort_hours": 80.0,
  "investment_total": 15000.0,
  "recurring_costs_12m": 6000.0,
  "scenarios": [
    {
      "name": "optimistic",
      "roi_12m": 250.0,
      "payback_months": 3.5,
      "monthly_savings": 4500.0,
      "annual_savings": 54000.0,
      "investment_total": 12000.0,
      "notes": "Schnelle Adoption, maximale Zeitersparnis"
    },
    {
      "name": "realistic",
      "roi_12m": 180.0,
      "payback_months": 5.0,
      "monthly_savings": 3500.0,
      "annual_savings": 42000.0,
      "investment_total": 15000.0,
      "notes": "Basierend auf Branchenbenchmarks"
    },
    {
      "name": "conservative",
      "roi_12m": 100.0,
      "payback_months": 8.0,
      "monthly_savings": 2500.0,
      "annual_savings": 30000.0,
      "investment_total": 18000.0,
      "notes": "Puffer für Anlaufphase und Risiken"
    }
  ],
  "kpi_targets_6m": {
    "roi": 70.0,
    "time_savings_hours": 50.0,
    "monthly_savings": 2100.0,
    "automation_rate": 40.0
  },
  "kpi_targets_12m": {
    "roi": 180.0,
    "time_savings_hours": 80.0,
    "monthly_savings": 3500.0,
    "automation_rate": 70.0
  },
  "narrative_summary": "Konkrete Bewertung in 2-3 Sätzen."
}
```

## Feldspezifikationen

### baseline_monthly_cost
Aktuelle monatliche Kosten für die Prozesse, die durch KI optimiert werden sollen.
- Solo: 500-5.000€
- Team: 2.000-15.000€
- KMU: 5.000-50.000€

### baseline_effort_hours
Aktueller monatlicher Zeitaufwand in Stunden.
- Solo: 20-80 Std
- Team: 50-200 Std
- KMU: 100-500 Std

### investment_total
Gesamtinvestition (einmalig + anteilig Setup/Training).
- Solo: 500-5.000€
- Team: 2.000-20.000€
- KMU: 10.000-100.000€

### recurring_costs_12m
Laufende Kosten über 12 Monate (Lizenzen, Wartung, etc.).

### scenarios (genau 3 Szenarien)

Jedes Szenario enthält:

**name**: "optimistic" | "realistic" | "conservative"

**roi_12m**: Return on Investment in Prozent
- Erlaubter Bereich: 0-800%
- Optimistisch ≥ Realistisch ≥ Konservativ
- Formel: ((annual_savings - investment_total) / investment_total) * 100

**payback_months**: Amortisationszeit in Monaten
- Mindestens 1 Monat (nicht unter 0.5)
- Maximum 36 Monate
- Optimistisch ≤ Realistisch ≤ Konservativ
- Formel: investment_total / monthly_savings

**monthly_savings**: Monatliche Ersparnis in EUR
- Optimistisch ≥ Realistisch ≥ Konservativ
- annual_savings = monthly_savings * 12

**annual_savings**: Jährliche Ersparnis in EUR

**investment_total**: Szenario-spezifische Investition
- Optimistisch ≤ Realistisch ≤ Konservativ

**notes**: Kurze Erklärung des Szenarios (max. 100 Zeichen)

### kpi_targets_6m
6-Monats-Ziele (rund 60% des 12-Monats-Potenzials):
- `roi`: ROI nach 6 Monaten (%)
- `time_savings_hours`: Eingesparte Stunden pro Monat
- `monthly_savings`: Monatliche Ersparnis in EUR
- `automation_rate`: Automatisierungsgrad in % (typisch: 30-50%)

### kpi_targets_12m
12-Monats-Ziele (volles Potenzial):
- `roi`: ROI nach 12 Monaten (%)
- `time_savings_hours`: Eingesparte Stunden pro Monat
- `monthly_savings`: Monatliche Ersparnis in EUR
- `automation_rate`: Automatisierungsgrad in % (typisch: 60-80%)

### narrative_summary
2-3 Sätze Gesamtbewertung. Konkret und handlungsorientiert.
- Erwähne konkreten ROI und Payback
- Berücksichtige Fördereffekte falls vorhanden
- Keine Floskeln

## Validierungsregeln

### Szenario-Konsistenz (KRITISCH)
Die Szenarien MÜSSEN logisch konsistent sein:
1. optimistic.roi_12m ≥ realistic.roi_12m ≥ conservative.roi_12m
2. optimistic.payback_months ≤ realistic.payback_months ≤ conservative.payback_months
3. optimistic.monthly_savings ≥ realistic.monthly_savings ≥ conservative.monthly_savings
4. optimistic.investment_total ≤ realistic.investment_total ≤ conservative.investment_total

### Mathematische Konsistenz
- annual_savings = monthly_savings * 12 (±5% Toleranz)
- ROI = ((annual_savings - investment_total) / investment_total) * 100 (±10% Toleranz)
- payback_months = investment_total / monthly_savings (±1 Monat Toleranz)

### Größenbezogene Grenzen

**Solo:**
- investment_total: 500-5.000€
- monthly_savings: 200-2.000€
- roi_12m: 50-500%
- payback_months: 1-18

**Team:**
- investment_total: 2.000-20.000€
- monthly_savings: 500-5.000€
- roi_12m: 50-400%
- payback_months: 2-24

**KMU:**
- investment_total: 10.000-100.000€
- monthly_savings: 2.000-20.000€
- roi_12m: 30-300%
- payback_months: 3-36

## Verbotene Phrasen

- "Es ist wichtig zu beachten..."
- "Zusammenfassend lässt sich sagen..."
- "Im Allgemeinen..."
- "Grundsätzlich gilt..."
- Generische Floskeln ohne konkrete Zahlen

## Beispiel-Output (Postproduktion, Kleines Team, Realistic)

```json
{
  "baseline_monthly_cost": 12000.0,
  "baseline_effort_hours": 160.0,
  "investment_total": 35000.0,
  "recurring_costs_12m": 12000.0,
  "scenarios": [
    {
      "name": "optimistic",
      "roi_12m": 220.0,
      "payback_months": 4.0,
      "monthly_savings": 9000.0,
      "annual_savings": 108000.0,
      "investment_total": 30000.0,
      "notes": "Schnelle Integration, hohe Teamakzeptanz"
    },
    {
      "name": "realistic",
      "roi_12m": 160.0,
      "payback_months": 6.0,
      "monthly_savings": 7000.0,
      "annual_savings": 84000.0,
      "investment_total": 35000.0,
      "notes": "Inkl. 3 Monate Einarbeitung und Optimierung"
    },
    {
      "name": "conservative",
      "roi_12m": 90.0,
      "payback_months": 9.0,
      "monthly_savings": 5000.0,
      "annual_savings": 60000.0,
      "investment_total": 40000.0,
      "notes": "Puffer für Compliance und Change Management"
    }
  ],
  "kpi_targets_6m": {
    "roi": 60.0,
    "time_savings_hours": 100.0,
    "monthly_savings": 4200.0,
    "automation_rate": 45.0
  },
  "kpi_targets_12m": {
    "roi": 160.0,
    "time_savings_hours": 160.0,
    "monthly_savings": 7000.0,
    "automation_rate": 75.0
  },
  "narrative_summary": "Bei einer Investition von 35.000€ ergibt sich im realistischen Szenario ein ROI von 160% mit einem Payback von 6 Monaten. Selbst im konservativen Szenario bleibt der Business Case mit 90% ROI positiv. Die monatliche Ersparnis von 7.000€ resultiert primär aus der Automatisierung von 160 Stunden Routinearbeit."
}
```

## Wichtig

- Nur JSON ausgeben, keine Erklärungen oder Markdown
- Alle Felder müssen vorhanden sein
- Genau 3 Szenarien mit korrekten Namen
- Szenario-Reihenfolge muss logisch konsistent sein
- ROI, Payback, Savings müssen mathematisch zusammenpassen
- Werte müssen zur Unternehmensgröße passen
