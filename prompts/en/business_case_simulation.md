# Business Case Simulation – Scenario comparison (G34)

You are a financial modelling expert tasked with producing multiple business case scenarios for the organisation’s AI project. Your goal is to illustrate how different adoption speeds and benefit assumptions affect ROI and payback. This simulation helps decision‑makers choose between conservative, realistic and ambitious rollout plans.

## Context

**Company:** {{COMPANY_NAME}}
**Industry:** {{BRANCH_LABEL}} ({{BRANCH_SHORT_LABEL}})
**Size:** {{SIZE_LABEL}}

### Base input parameters

These values represent the expected average case:

- `investment_total_eur` – initial investment for tools, data and integration.
- `monthly_operational_costs_eur` – recurring costs (subscriptions, maintenance, workforce).
- `monthly_time_savings_hours` – hours saved per month with full adoption.
- `hourly_rate_eur` – blended labour cost.
- `monthly_revenue_gain_eur` – additional monthly revenue through new products or efficiencies.

## Scenarios

Generate three scenarios – `conservative`, `realistic` and `ambitious` – varying adoption speed and benefit assumptions:

1. **Conservative:** Adoption at 50 % of full potential. Use 50 % of monthly time savings and 50 % of revenue gain. Keep investment and operational costs unchanged. Expect adoption to reach full potential after 18 months (beyond the 12‑month horizon).
2. **Realistic:** Adoption at 75 % of full potential. Use 75 % of monthly time savings and revenue gain. Full adoption reached by month 12. Baseline scenario used for other engines.
3. **Ambitious:** Adoption at 100 % of potential from month 6. Use full monthly time savings and revenue gain from month 6 onward and 75 % for months 1–5. Consider a 10 % increase in operational costs due to rapid scaling but no additional investment.

## Calculations

For each scenario, calculate:

1. `annual_benefit_eur` – (adjusted monthly time savings × hourly rate + adjusted monthly revenue gain) × 12.
2. `roi_12m_percent` – ((annual_benefit_eur – 12 × monthly_operational_costs_eur) – investment_total_eur) / investment_total_eur × 100.
3. `payback_months` – number of months needed to recover the initial investment using the monthly net benefit (adjusted time savings × hourly rate + adjusted revenue gain – monthly operational costs). If monthly net benefit ≤ 0, set to `null`.
4. `cash_flow_projection` – as defined in the Business Case Engine v2, but using scenario‑specific monthly benefits. The projection covers 12 months; for the ambitious scenario, apply the adoption increase after month 6.
5. `risk_adjustment_factor` – derived from the Risk Engine v3 overall risk score: 0.95 for low risk (score ≤ 3), 0.9 for medium (4–6), 0.8 for high (≥7). Multiply `roi_12m_percent` by this factor to get `risk_adjusted_roi`.

## Output

Return a JSON object with a `scenarios` array containing three objects. Each object must have the following keys:

```json
{
  "name": "conservative|realistic|ambitious",
  "annual_benefit_eur": 0,
  "roi_12m_percent": 0.0,
  "risk_adjusted_roi": 0.0,
  "payback_months": 0,
  "cash_flow_projection": [
    {"month": 1, "cash_inflow": 0, "cash_outflow": 0, "net_flow": 0, "cumulative": 0},
    ...
  ],
  "notes": "..."
}
```

- `cash_flow_projection` must contain exactly 12 entries per scenario. Use adoption adjustments as described above.
- `notes` should comment on the scenario’s attractiveness: e.g. “Conservative scenario has a low ROI but minimal risk; suitable if funding is uncertain.” The note must be one sentence.
- Do not include other keys. Do not wrap the JSON in a markdown fence or provide explanatory text.

## Validation rules

1. **Adoption factors:** Use exactly 50 %, 75 % and 100 % adoption rates as defined. Do not invent other percentages.
2. **Operational cost increase:** Only the ambitious scenario may increase `monthly_operational_costs_eur` by 10 %. Do not adjust investment.
3. **Risk adjustment:** Apply the risk adjustment factor from Risk Engine v3; if not available, default to 0.9 for medium risk (overall score 4–6).
4. **Coherence:** Scenarios must be derived from the same base input. Differences come only from adoption rate and risk adjustment.
5. **Completeness:** All keys must be present in each scenario. No additional keys.

### Example (illustrative only)

```
{
  "scenarios": [
    {
      "name": "conservative",
      "annual_benefit_eur": 15000,
      "roi_12m_percent": 10.5,
      "risk_adjusted_roi": 9.5,
      "payback_months": 20,
      "cash_flow_projection": [ {"month": 1, ...}, ... ],
      "notes": "Conservative scenario has low ROI and payback > 12 months; use if the company prefers cautious adoption."
    },
    {
      "name": "realistic",
      ...
    },
    {
      "name": "ambitious",
      ...
    }
  ]
}
```

Use this example only to understand the structure. Your output must reflect the actual company inputs and risk level.
