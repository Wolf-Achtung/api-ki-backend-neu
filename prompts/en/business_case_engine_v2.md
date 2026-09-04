# Business Case Engine 2.0 – ROI Simulation & Scenarios (G30)

You generate a structured JSON business case analysis for an AI project.
This analysis includes 3 scenarios, 12-month KPI forecasts and consolidated ROI calculations.

## Context

**Company:** {{COMPANY_NAME}}
**Industry:** {{BRANCH_LABEL}} ({{BRANCH_SHORT_LABEL}})
**Size:** {{SIZE_LABEL}}
**Maturity:** {{MATURITY_LEVEL}}
**Region:** {{BUNDESLAND}}

### Available Analysis Data

**Branch Deep Dive:**
{{BRANCH_DEEP_DIVE_SUMMARY}}

**Current KPI Baseline:**
- ROI Estimate: {{ROI_12M}}%
- Payback Estimate: {{PAYBACK_MONTHS}} months
- Time Savings: {{EINSPARUNG_STUNDEN_MONAT}} hrs/month
- Monthly Savings: {{EINSPARUNG_MONAT_EUR}} €

**Tools Engine 4.0 Results:**
{{TOOLS_SUMMARY}}

**Funding Engine v2 Results:**
{{FUNDING_SUMMARY}}

**Strategy Plan (if available):**
{{STRATEGY_SUMMARY}}

**Risk Engine v2 Results:**
{{RISK_SUMMARY}}

## Requirements

Create a detailed business case based on all input data.
Consider company size ({{SIZE_LABEL}}):

- **Solo/Freelancer**:
  - Small, pragmatic investments (€500-5,000)
  - Quick payback more important than high ROI
  - Focus on quick wins and immediate time savings
  - Low ongoing costs

- **Team (2-10 employees)**:
  - Moderate investments (€2,000-20,000)
  - Balance between ROI and implementation effort
  - Prefer scalable solutions
  - Consider team adoption

- **SME (>10 employees)**:
  - Larger investments possible (€10,000-100,000)
  - Structured ROI analysis required
  - Include compliance costs
  - Consider change management

## Output Format

You MUST output exactly this JSON schema – no additional text, only JSON:

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
      "notes": "Fast adoption, maximum time savings"
    },
    {
      "name": "realistic",
      "roi_12m": 180.0,
      "payback_months": 5.0,
      "monthly_savings": 3500.0,
      "annual_savings": 42000.0,
      "investment_total": 15000.0,
      "notes": "Based on industry benchmarks"
    },
    {
      "name": "conservative",
      "roi_12m": 100.0,
      "payback_months": 8.0,
      "monthly_savings": 2500.0,
      "annual_savings": 30000.0,
      "investment_total": 18000.0,
      "notes": "Buffer for ramp-up phase and risks"
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
  "narrative_summary": "Concrete assessment in 2-3 sentences."
}
```

## Field Specifications

### baseline_monthly_cost
Current monthly costs for processes to be optimized through AI.
- Solo: €500-5,000
- Team: €2,000-15,000
- SME: €5,000-50,000

### baseline_effort_hours
Current monthly time effort in hours.
- Solo: 20-80 hrs
- Team: 50-200 hrs
- SME: 100-500 hrs

### investment_total
Total investment (one-time + proportional setup/training).
- Solo: €500-5,000
- Team: €2,000-20,000
- SME: €10,000-100,000

### recurring_costs_12m
Ongoing costs over 12 months (licenses, maintenance, etc.).

### scenarios (exactly 3 scenarios)

Each scenario contains:

**name**: "optimistic" | "realistic" | "conservative"

**roi_12m**: Return on Investment in percent
- Allowed range: 0-800%
- Optimistic ≥ Realistic ≥ Conservative
- Formula: ((annual_savings - investment_total) / investment_total) * 100

**payback_months**: Payback period in months
- Minimum 1 month (not below 0.5)
- Maximum 36 months
- Optimistic ≤ Realistic ≤ Conservative
- Formula: investment_total / monthly_savings

**monthly_savings**: Monthly savings in EUR
- Optimistic ≥ Realistic ≥ Conservative
- annual_savings = monthly_savings * 12

**annual_savings**: Annual savings in EUR

**investment_total**: Scenario-specific investment
- Optimistic ≤ Realistic ≤ Conservative

**notes**: Brief explanation of the scenario (max. 100 characters)

### kpi_targets_6m
6-month targets (approx. 60% of 12-month potential):
- `roi`: ROI after 6 months (%)
- `time_savings_hours`: Saved hours per month
- `monthly_savings`: Monthly savings in EUR
- `automation_rate`: Automation rate in % (typical: 30-50%)

### kpi_targets_12m
12-month targets (full potential):
- `roi`: ROI after 12 months (%)
- `time_savings_hours`: Saved hours per month
- `monthly_savings`: Monthly savings in EUR
- `automation_rate`: Automation rate in % (typical: 60-80%)

### narrative_summary
2-3 sentences overall assessment. Concrete and action-oriented.
- Mention specific ROI and payback
- Consider funding effects if applicable
- No platitudes

## Validation Rules

### Scenario Consistency (CRITICAL)
Scenarios MUST be logically consistent:
1. optimistic.roi_12m ≥ realistic.roi_12m ≥ conservative.roi_12m
2. optimistic.payback_months ≤ realistic.payback_months ≤ conservative.payback_months
3. optimistic.monthly_savings ≥ realistic.monthly_savings ≥ conservative.monthly_savings
4. optimistic.investment_total ≤ realistic.investment_total ≤ conservative.investment_total

### Mathematical Consistency
- annual_savings = monthly_savings * 12 (±5% tolerance)
- ROI = ((annual_savings - investment_total) / investment_total) * 100 (±10% tolerance)
- payback_months = investment_total / monthly_savings (±1 month tolerance)

### Size-Related Limits

**Solo:**
- investment_total: €500-5,000
- monthly_savings: €200-2,000
- roi_12m: 50-500%
- payback_months: 1-18

**Team:**
- investment_total: €2,000-20,000
- monthly_savings: €500-5,000
- roi_12m: 50-400%
- payback_months: 2-24

**SME:**
- investment_total: €10,000-100,000
- monthly_savings: €2,000-20,000
- roi_12m: 30-300%
- payback_months: 3-36

## Forbidden Phrases

- "It is important to note..."
- "In summary, it can be said..."
- "In general..."
- "Basically..."
- Generic phrases without concrete numbers

## Example Output (Post-production, Small Team, Realistic)

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
      "notes": "Fast integration, high team acceptance"
    },
    {
      "name": "realistic",
      "roi_12m": 160.0,
      "payback_months": 6.0,
      "monthly_savings": 7000.0,
      "annual_savings": 84000.0,
      "investment_total": 35000.0,
      "notes": "Incl. 3 months onboarding and optimization"
    },
    {
      "name": "conservative",
      "roi_12m": 90.0,
      "payback_months": 9.0,
      "monthly_savings": 5000.0,
      "annual_savings": 60000.0,
      "investment_total": 40000.0,
      "notes": "Buffer for compliance and change management"
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
  "narrative_summary": "With an investment of €35,000, the realistic scenario yields an ROI of 160% with a payback of 6 months. Even in the conservative scenario, the business case remains positive at 90% ROI. The monthly savings of €7,000 result primarily from automation of 160 hours of routine work."
}
```

## Important

- Only output JSON, no explanations or Markdown
- All fields must be present
- Exactly 3 scenarios with correct names
- Scenario order must be logically consistent
- ROI, payback, savings must be mathematically coherent
- Values must fit company size
