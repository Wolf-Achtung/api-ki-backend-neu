# Business Case Simulation – Monte-Carlo Unsicherheitsmodell (G34)

Du generierst Simulationsannahmen fuer eine Monte-Carlo-Analyse des Business Case.
Die eigentliche Simulation findet in Python statt – du lieferst nur die Verteilungsparameter.

## Kontext

**Unternehmen:** {{COMPANY_NAME}}
**Branche:** {{BRANCH_LABEL}} ({{BRANCH_SHORT_LABEL}})
**Groesse:** {{SIZE_LABEL}}
**Reifegrad:** {{MATURITY_LEVEL}}
**Region:** {{BUNDESLAND}}

### Business Case Engine v2 (G30) Baseline

**Realistisches Szenario:**
- ROI (12M): {{BC_REALISTIC_ROI}}%
- Payback: {{BC_REALISTIC_PAYBACK}} Monate
- Monatliche Ersparnis: {{BC_REALISTIC_SAVINGS}} EUR
- Investment: {{BC_INVESTMENT_TOTAL}} EUR

**Szenario-Bandbreite:**
- Optimistisch: ROI {{BC_OPTIMISTIC_ROI}}%, Payback {{BC_OPTIMISTIC_PAYBACK}} Monate
- Konservativ: ROI {{BC_CONSERVATIVE_ROI}}%, Payback {{BC_CONSERVATIVE_PAYBACK}} Monate

### Risk Engine v3 (G33) Ergebnisse

**Risikoprofil:**
- Residual Risk Score: {{RISK_RESIDUAL_SCORE}}/100
- Residual Risk Grade: {{RISK_RESIDUAL_GRADE}}
- Compliance Status: {{COMPLIANCE_STATUS}}
- DPIA erforderlich: {{DPIA_REQUIRED}}

**AI Act Konformitaet:**
- Konformitaets-Score: {{AI_ACT_CONFORMITY}}%
- Fehlende Controls: {{AI_ACT_MISSING_CONTROLS}}

### Automation Roadmap (G36) Ergebnisse

**Prozessautomation:**
- Identifizierte Prozesse: {{AUTO_PROCESS_COUNT}}
- Quick Wins: {{AUTO_QUICK_WINS}}
- Durchschnittliches Automationspotenzial: {{AUTO_AVG_POTENTIAL}}%
- Phase 1 Prozesse: {{AUTO_PHASE_1_COUNT}}

### Tools & Funding Kontext

**Tools Engine (G25):**
{{TOOLS_SUMMARY}}

**Funding Engine (G26):**
{{FUNDING_SUMMARY}}

## Anforderungen

Erstelle realistische Verteilungsannahmen fuer die Monte-Carlo-Simulation.
Beruecksichtige dabei:

1. **Unternehmensgröße ({{SIZE_LABEL}})**:
   - **Solo/Freelancer**: Hoehere Varianz bei Umsetzungsgeschwindigkeit, kleinere Bandbreiten bei Kosten
   - **Team (2-10 MA)**: Mittlere Varianz, moderate Bandbreiten
   - **KMU (>10 MA)**: Niedrigere relative Varianz, strukturiertere Umsetzung

2. **Risikoprofil (Grade: {{RISK_RESIDUAL_GRADE}})**:
   - Grade A/B: Engere Bandbreiten (niedrige Unsicherheit)
   - Grade C: Mittlere Bandbreiten (Standard)
   - Grade D/F: Breitere Bandbreiten (hohe Unsicherheit)

3. **G30 Szenarien als Ankerpunkte**:
   - Konservatives Szenario ≈ Min-Werte
   - Realistisches Szenario ≈ Mode-Werte (wahrscheinlichster Fall)
   - Optimistisches Szenario ≈ Max-Werte

4. **Foerdererfolgswahrscheinlichkeit**:
   - Basierend auf Match-Scores und Programmverfuegbarkeit
   - Solo: 30-50%
   - Team: 40-60%
   - KMU: 50-70%

## Output-Format

Du MUSST exakt dieses JSON-Schema ausgeben – keine weiteren Texte, nur JSON:

```json
{
  "assumptions": {
    "monthly_savings": {
      "min": 3000,
      "mode": 5000,
      "max": 8000
    },
    "investment_total": {
      "min": 20000,
      "mode": 25000,
      "max": 35000
    },
    "speed_factor": {
      "min": 0.7,
      "mode": 1.0,
      "max": 1.2
    },
    "risk_factor": {
      "min": 0.8,
      "mode": 1.0,
      "max": 1.1
    },
    "funding_success_probability": 0.5
  }
}
```

## Feldspezifikationen

### monthly_savings (Dreiecksverteilung: min/mode/max)

Monatliche Ersparnis in EUR.

**Orientierung an G30:**
- `min`: Konservatives Szenario Ersparnis (oder 60-70% des realistischen)
- `mode`: Realistisches Szenario Ersparnis
- `max`: Optimistisches Szenario Ersparnis (oder 130-150% des realistischen)

**Groessenanpassung:**
- Solo: min 200-2.000€, mode 500-3.000€, max 1.000-5.000€
- Team: min 500-5.000€, mode 1.500-8.000€, max 3.000-12.000€
- KMU: min 2.000-15.000€, mode 5.000-25.000€, max 10.000-40.000€

### investment_total (Dreiecksverteilung: min/mode/max)

Gesamtinvestition in EUR.

**Orientierung an G30:**
- `min`: Optimistisches Szenario Investment (guenstigster Fall)
- `mode`: Realistisches Szenario Investment
- `max`: Konservatives Szenario Investment (+ Risikopuffer)

**Groessenanpassung:**
- Solo: min 300-3.000€, mode 500-5.000€, max 1.000-8.000€
- Team: min 1.500-15.000€, mode 3.000-25.000€, max 5.000-40.000€
- KMU: min 8.000-60.000€, mode 15.000-80.000€, max 25.000-120.000€

### speed_factor (Dreiecksverteilung: min/mode/max)

Umsetzungsgeschwindigkeitsfaktor (1.0 = wie geplant).

**Bedeutung:**
- `< 1.0`: Langsamer als geplant (reduziert effektive Einsparungen)
- `= 1.0`: Planmaessige Umsetzung
- `> 1.0`: Schneller als geplant (beschleunigt Einsparungen)

**Risikoanpassung:**
- Grade A/B: min 0.85, mode 1.0, max 1.15
- Grade C: min 0.75, mode 1.0, max 1.15
- Grade D/F: min 0.60, mode 0.9, max 1.1

### risk_factor (Dreiecksverteilung: min/mode/max)

Risikoadjustierungsfaktor basierend auf G33 (1.0 = neutral).

**Bedeutung:**
- `< 1.0`: Risiken reduzieren erwartete Ertraege
- `= 1.0`: Neutrale Risikoposition
- `> 1.0`: Guenstige Risikosituation

**Berechnung aus G33:**
- Mode = min(1.0, Residual_Risk_Score/100 + 0.5)
- Grade A/B: min 0.9, mode 1.0, max 1.1
- Grade C: min 0.8, mode 0.95, max 1.05
- Grade D/F: min 0.6, mode 0.8, max 0.95

### funding_success_probability

Wahrscheinlichkeit, dass Foerderung erfolgreich beantragt wird (0.0-1.0).

**Orientierung:**
- Keine Foerderoptionen: 0.0
- 1-2 passende Programme (Match < 70%): 0.3-0.4
- 2-3 passende Programme (Match 70-85%): 0.5-0.6
- 3+ passende Programme (Match > 85%): 0.6-0.8

## Validierungsregeln

### Konsistenz mit G30
1. `monthly_savings.mode` ≈ G30 realistic.monthly_savings (±15%)
2. `investment_total.mode` ≈ G30 investment_total (±15%)
3. `monthly_savings.min` ≈ G30 conservative.monthly_savings (±20%)
4. `monthly_savings.max` ≈ G30 optimistic.monthly_savings (±20%)

### Verteilungslogik
1. Fuer alle Parameter: min ≤ mode ≤ max
2. monthly_savings: min ≥ 0, max ≤ 100.000
3. investment_total: min ≥ 100, max ≤ 500.000
4. speed_factor: min ≥ 0.3, max ≤ 1.5
5. risk_factor: min ≥ 0.3, max ≤ 1.3
6. funding_success_probability: 0.0 ≤ x ≤ 1.0

### Risikoanpassung
1. Hoeherer Risiko-Grade → breitere Verteilungen (hoehere Varianz)
2. Hoeherer Risiko-Grade → niedrigere risk_factor Werte
3. Niedrigerer AI Act Conformity Score → niedrigere speed_factor

### Groessenkonsistenz
1. Solo: Kleinere absolute Werte, hoehere relative Varianz
2. Team: Mittlere Werte, moderate Varianz
3. KMU: Groessere absolute Werte, niedrigere relative Varianz

## Beispiel-Outputs

### Solo-Freelancer, niedriges Risiko (Grade B)

```json
{
  "assumptions": {
    "monthly_savings": {
      "min": 400,
      "mode": 800,
      "max": 1200
    },
    "investment_total": {
      "min": 1500,
      "mode": 2000,
      "max": 2800
    },
    "speed_factor": {
      "min": 0.85,
      "mode": 1.0,
      "max": 1.15
    },
    "risk_factor": {
      "min": 0.9,
      "mode": 1.0,
      "max": 1.05
    },
    "funding_success_probability": 0.35
  }
}
```

### KMU, hohes Risiko (Grade D)

```json
{
  "assumptions": {
    "monthly_savings": {
      "min": 3000,
      "mode": 8000,
      "max": 15000
    },
    "investment_total": {
      "min": 25000,
      "mode": 45000,
      "max": 70000
    },
    "speed_factor": {
      "min": 0.55,
      "mode": 0.85,
      "max": 1.05
    },
    "risk_factor": {
      "min": 0.55,
      "mode": 0.75,
      "max": 0.9
    },
    "funding_success_probability": 0.55
  }
}
```

## Wichtig

- Nur JSON ausgeben, keine Erklaerungen oder Markdown
- Alle Felder muessen vorhanden sein
- Werte muessen realistisch und konsistent mit G30/G33 sein
- Verteilungen muessen min ≤ mode ≤ max erfuellen
- Groessenanpassung beachten
- Risikoanpassung aus G33 einbeziehen
