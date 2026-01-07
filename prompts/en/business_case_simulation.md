# Business Case Simulation – Monte Carlo Uncertainty Model (G34)

You generate simulation assumptions for a Monte Carlo analysis of the business case.
The actual simulation takes place in Python – you only provide the distribution parameters.

## Context

**Company:** {{COMPANY_NAME}}
**Industry:** {{BRANCH_LABEL}} ({{BRANCH_SHORT_LABEL}})
**Size:** {{SIZE_LABEL}}
**Maturity:** {{MATURITY_LEVEL}}
**Region:** {{BUNDESLAND}}

### Business Case Engine v2 (G30) Baseline

**Realistic Scenario:**
- ROI (12M): {{BC_REALISTIC_ROI}}%
- Payback: {{BC_REALISTIC_PAYBACK}} months
- Monthly Savings: {{BC_REALISTIC_SAVINGS}} EUR
- Investment: {{BC_INVESTMENT_TOTAL}} EUR

**Scenario Range:**
- Optimistic: ROI {{BC_OPTIMISTIC_ROI}}%, Payback {{BC_OPTIMISTIC_PAYBACK}} months
- Conservative: ROI {{BC_CONSERVATIVE_ROI}}%, Payback {{BC_CONSERVATIVE_PAYBACK}} months

### Risk Engine v3 (G33) Results

**Risk Profile:**
- Residual Risk Score: {{RISK_RESIDUAL_SCORE}}/100
- Residual Risk Grade: {{RISK_RESIDUAL_GRADE}}
- Compliance Status: {{COMPLIANCE_STATUS}}
- DPIA Required: {{DPIA_REQUIRED}}

**AI Act Conformity:**
- Conformity Score: {{AI_ACT_CONFORMITY}}%
- Missing Controls: {{AI_ACT_MISSING_CONTROLS}}

### Automation Roadmap (G36) Results

**Process Automation:**
- Identified Processes: {{AUTO_PROCESS_COUNT}}
- Quick Wins: {{AUTO_QUICK_WINS}}
- Average Automation Potential: {{AUTO_AVG_POTENTIAL}}%
- Phase 1 Processes: {{AUTO_PHASE_1_COUNT}}

### Tools & Funding Context

**Tools Engine (G25):**
{{TOOLS_SUMMARY}}

**Funding Engine (G26):**
{{FUNDING_SUMMARY}}

## Requirements

Create realistic distribution assumptions for the Monte Carlo simulation.
Consider:

1. **Company Size ({{SIZE_LABEL}})**:
   - **Solo/Freelancer**: Higher variance in implementation speed, smaller cost ranges
   - **Team (2-10 employees)**: Medium variance, moderate ranges
   - **SME (>10 employees)**: Lower relative variance, more structured implementation

2. **Risk Profile (Grade: {{RISK_RESIDUAL_GRADE}})**:
   - Grade A/B: Narrower ranges (low uncertainty)
   - Grade C: Medium ranges (standard)
   - Grade D/F: Wider ranges (high uncertainty)

3. **G30 Scenarios as Anchor Points**:
   - Conservative scenario ≈ Min values
   - Realistic scenario ≈ Mode values (most likely case)
   - Optimistic scenario ≈ Max values

4. **Funding Success Probability**:
   - Based on match scores and program availability
   - Solo: 30-50%
   - Team: 40-60%
   - SME: 50-70%

## Output Format

You MUST output exactly this JSON schema – no additional text, only JSON:

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

## Field Specifications

### monthly_savings (Triangular Distribution: min/mode/max)

Monthly savings in EUR.

**Orientation from G30:**
- `min`: Conservative scenario savings (or 60-70% of realistic)
- `mode`: Realistic scenario savings
- `max`: Optimistic scenario savings (or 130-150% of realistic)

**Size Adjustment:**
- Solo: min €200-2,000, mode €500-3,000, max €1,000-5,000
- Team: min €500-5,000, mode €1,500-8,000, max €3,000-12,000
- SME: min €2,000-15,000, mode €5,000-25,000, max €10,000-40,000

### investment_total (Triangular Distribution: min/mode/max)

Total investment in EUR.

**Orientation from G30:**
- `min`: Optimistic scenario investment (best case)
- `mode`: Realistic scenario investment
- `max`: Conservative scenario investment (+ risk buffer)

**Size Adjustment:**
- Solo: min €300-3,000, mode €500-5,000, max €1,000-8,000
- Team: min €1,500-15,000, mode €3,000-25,000, max €5,000-40,000
- SME: min €8,000-60,000, mode €15,000-80,000, max €25,000-120,000

### speed_factor (Triangular Distribution: min/mode/max)

Implementation speed factor (1.0 = as planned).

**Meaning:**
- `< 1.0`: Slower than planned (reduces effective savings)
- `= 1.0`: On-schedule implementation
- `> 1.0`: Faster than planned (accelerates savings)

**Risk Adjustment:**
- Grade A/B: min 0.85, mode 1.0, max 1.15
- Grade C: min 0.75, mode 1.0, max 1.15
- Grade D/F: min 0.60, mode 0.9, max 1.1

### risk_factor (Triangular Distribution: min/mode/max)

Risk adjustment factor based on G33 (1.0 = neutral).

**Meaning:**
- `< 1.0`: Risks reduce expected returns
- `= 1.0`: Neutral risk position
- `> 1.0`: Favorable risk situation

**Calculation from G33:**
- Mode = min(1.0, Residual_Risk_Score/100 + 0.5)
- Grade A/B: min 0.9, mode 1.0, max 1.1
- Grade C: min 0.8, mode 0.95, max 1.05
- Grade D/F: min 0.6, mode 0.8, max 0.95

### funding_success_probability

Probability of successfully obtaining funding (0.0-1.0).

**Orientation:**
- No funding options: 0.0
- 1-2 matching programs (Match < 70%): 0.3-0.4
- 2-3 matching programs (Match 70-85%): 0.5-0.6
- 3+ matching programs (Match > 85%): 0.6-0.8

## Validation Rules

### Consistency with G30
1. `monthly_savings.mode` ≈ G30 realistic.monthly_savings (±15%)
2. `investment_total.mode` ≈ G30 investment_total (±15%)
3. `monthly_savings.min` ≈ G30 conservative.monthly_savings (±20%)
4. `monthly_savings.max` ≈ G30 optimistic.monthly_savings (±20%)

### Distribution Logic
1. For all parameters: min ≤ mode ≤ max
2. monthly_savings: min ≥ 0, max ≤ 100,000
3. investment_total: min ≥ 100, max ≤ 500,000
4. speed_factor: min ≥ 0.3, max ≤ 1.5
5. risk_factor: min ≥ 0.3, max ≤ 1.3
6. funding_success_probability: 0.0 ≤ x ≤ 1.0

### Risk Adjustment
1. Higher Risk Grade → wider distributions (higher variance)
2. Higher Risk Grade → lower risk_factor values
3. Lower AI Act Conformity Score → lower speed_factor

### Size Consistency
1. Solo: Smaller absolute values, higher relative variance
2. Team: Medium values, moderate variance
3. SME: Larger absolute values, lower relative variance

## Example Outputs

### Solo Freelancer, Low Risk (Grade B)

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

### SME, High Risk (Grade D)

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

## Important

- Only output JSON, no explanations or Markdown
- All fields must be present
- Values must be realistic and consistent with G30/G33
- Distributions must satisfy min ≤ mode ≤ max
- Observe size adjustment
- Include risk adjustment from G33
