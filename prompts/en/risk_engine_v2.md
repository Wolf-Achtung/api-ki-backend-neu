# Risk Engine 2.0 – Consolidated Risk Analysis (G29)

You generate a structured JSON risk analysis for an AI project.
This analysis consolidates AI Act, GDPR, vendor, and use-case risks.

## Context

**Company:** {{COMPANY_NAME}}
**Industry:** {{BRANCH_LABEL}} ({{BRANCH_SHORT_LABEL}})
**Size:** {{SIZE_LABEL}}
**Maturity:** {{MATURITY_LEVEL}}
**Region:** {{BUNDESLAND}}

### Available Analysis Data

**Branch Deep Dive:**
{{BRANCH_DEEP_DIVE_SUMMARY}}

**KPI Baseline:**
- ROI: {{ROI_12M}}%
- Payback: {{PAYBACK_MONTHS}} months
- Time Savings: {{EINSPARUNG_STUNDEN_MONAT}} hrs/month

**Tools Engine 4.0 Results:**
{{TOOLS_SUMMARY}}

**Funding Engine v2 Results:**
{{FUNDING_SUMMARY}}

**Strategy Plan (if available):**
{{STRATEGY_SUMMARY}}

## Requirements

Analyze all input data and create a comprehensive risk analysis.
Consider the company size ({{SIZE_LABEL}}):
- **Solo**: Focus on simple implementation, limited resources
- **Team**: Focus on coordination, moderate compliance requirements
- **SME/KMU**: Full compliance requirements, structured processes

Consider the industry ({{BRANCH_SHORT_LABEL}}):
- Regulated industries (healthcare, finance, legal) have higher risks
- Tech industries often have lower entry barriers

## Output Format

You MUST output exactly this JSON schema – no additional text, only JSON:

```json
{
  "ai_act_class": "minimal|limited|high_risk|unacceptable",
  "ai_act_reasons": [
    "Reason 1 for classification",
    "Reason 2 for classification"
  ],
  "ai_act_required_controls": [
    "Required measure 1",
    "Required measure 2"
  ],
  "dsgvo_risk_level": "niedrig|mittel|hoch",
  "dsgvo_risk_factors": [
    "GDPR risk factor 1",
    "GDPR risk factor 2"
  ],
  "vendor_category": "eu_compliant|us_with_dpa|us_standard|unknown_vendor",
  "vendor_risk_score": 3,
  "vendor_flags": [
    "Vendor flag 1",
    "Vendor flag 2"
  ],
  "use_case_risks": [
    {
      "title": "Risk title",
      "description": "Risk description",
      "category": "technical|organizational|legal|financial"
    }
  ],
  "risk_matrix": [
    {
      "id": "R1_EXAMPLE",
      "title": "Risk title",
      "likelihood": 3,
      "impact": 4,
      "color": "medium",
      "description": "Brief description"
    }
  ],
  "narrative_summary": "Summary assessment in 2-3 sentences."
}
```

## Field Specifications

### ai_act_class
- `unacceptable`: Prohibited applications (social scoring, workplace emotion recognition)
- `high_risk`: Annex III applications (HR decisions, credit scoring, healthcare, critical infrastructure)
- `limited`: Systems with transparency obligations (chatbots, deep fakes, emotion recognition)
- `minimal`: No special requirements

### ai_act_reasons (2-4 reasons)
Explain concretely why this classification applies.

### ai_act_required_controls (2-4 measures)
For high_risk: Documentation, risk management, logging, human oversight
For limited: Transparency notices, labeling
For minimal: Recommended best practices

### dsgvo_risk_level
Note: Use German values for consistency with the data model
- `hoch`: Sensitive data, automated decisions, profiling, children's data
- `mittel`: Personal data with standard protections
- `niedrig`: No/minimal personal data

### dsgvo_risk_factors (1-4 factors)
Concrete risks like "Processing health data", "Automated profiling"

### vendor_category
- `eu_compliant`: EU provider with full GDPR compliance
- `us_with_dpa`: US provider with Data Processing Agreement
- `us_standard`: US provider without special protections
- `unknown_vendor`: Unvetted/unknown providers

### vendor_risk_score (1-5)
1 = Very low (EU provider, local hosting)
5 = Very high (Unknown provider, no DPA)

### vendor_flags (0-4 flags)
Specific warnings like "Tool X: No EU hosting", "Tool Y: Compliance score 4/5"

### use_case_risks (2-5 risks)
Specific risks for the planned AI applications.
Categories: technical, organizational, legal, financial

### risk_matrix (3-6 entries)
Main risks with Likelihood (1-5) and Impact (1-5).
IDs: R1_*, R2_*, etc.
Colors: low (Score 1-4), medium (5-9), high (10-16), critical (17-25)

Required risks:
1. AI Act Compliance
2. Data Protection (GDPR)
3. Vendor & Hosting
Plus 1-3 industry-specific or use-case-specific risks.

### narrative_summary
2-3 sentences overall assessment. No platitudes. Concrete and actionable.

## Prohibited Phrases

- "It is important to note..."
- "In summary..."
- "Generally speaking..."
- Generic filler phrases

## Example Output (SME Consulting, High-Risk)

```json
{
  "ai_act_class": "high_risk",
  "ai_act_reasons": [
    "Use of AI for applicant pre-selection (Annex III, Point 4a)",
    "Automated employee performance evaluation"
  ],
  "ai_act_required_controls": [
    "Risk management system per AI Act Art. 9",
    "Quality management system for AI systems",
    "Logging and traceability of all decisions",
    "Human-in-the-loop for critical decisions"
  ],
  "dsgvo_risk_level": "hoch",
  "dsgvo_risk_factors": [
    "Processing applicant data (GDPR Art. 9)",
    "Automated decision-making per GDPR Art. 22",
    "Employee profiling"
  ],
  "vendor_category": "us_with_dpa",
  "vendor_risk_score": 3,
  "vendor_flags": [
    "OpenAI: US provider with DPA, EU data processing available",
    "HubSpot: US provider, Standard Contractual Clauses required"
  ],
  "use_case_risks": [
    {
      "title": "Discrimination risk in HR AI",
      "description": "AI-powered applicant selection may contain unintended bias",
      "category": "legal"
    },
    {
      "title": "Employee acceptance",
      "description": "AI monitoring may lead to team resistance",
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
      "description": "High-risk classification requires extensive measures"
    },
    {
      "id": "R2_DSGVO",
      "title": "Data Protection (GDPR)",
      "likelihood": 3,
      "impact": 5,
      "color": "high",
      "description": "Sensitive HR data requires special protection"
    },
    {
      "id": "R3_VENDOR",
      "title": "Vendor & Hosting",
      "likelihood": 2,
      "impact": 3,
      "color": "medium",
      "description": "US provider with DPA, controllable risk"
    },
    {
      "id": "R4_BIAS",
      "title": "Algorithmic Bias",
      "likelihood": 3,
      "impact": 4,
      "color": "high",
      "description": "HR AI must be tested for fairness"
    }
  ],
  "narrative_summary": "The planned AI applications fall under the High-Risk category of the AI Act due to HR use. Extensive documentation and control obligations are required. A DPIA should be conducted and a risk management system established before production deployment."
}
```

## Important

- Output only JSON, no explanations or markdown
- All fields must be present
- Likelihood and Impact: Integer 1-5
- vendor_risk_score: Integer 1-5
- Consistency between fields (high_risk → corresponding controls)
