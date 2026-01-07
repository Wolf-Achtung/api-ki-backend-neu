# Tools Engine V4 – Multi-Dimensional Tool Assessment

You are an AI expert in tool evaluation. Analyze the named tool and provide a structured assessment across all dimensions.

## Context

**Tool Name:** {{TOOL_NAME}}
**Category:** {{TOOL_CATEGORY}}
**Industry:** {{BRANCH_SHORT_LABEL}}
**Company Size:** {{SIZE_LABEL}}

## Assessment Dimensions

Evaluate the tool on a scale of 1-5:

### 1. Cost Level (cost_level)
- 1 = Free / very affordable (< €10/month)
- 2 = Affordable (€10-30/month)
- 3 = Moderate (€30-100/month)
- 4 = Expensive (€100-500/month)
- 5 = Enterprise / very expensive (> €500/month)

### 2. Complexity Level (complexity_level)
- 1 = Plug-and-play, immediately usable
- 2 = Simple setup (< 1 hour)
- 3 = Moderate integration (1-8 hours)
- 4 = Complex integration (days)
- 5 = Enterprise integration (weeks/months)

### 3. Maturity Level (maturity_level)
- 1 = New/Beta/Experimental
- 2 = Early adoption
- 3 = Growing, establishing itself
- 4 = Established, many users
- 5 = Market leader, standard

### 4. Compliance Score (compliance_score)
- 1 = EU-friendly, GDPR-compliant, DPA available
- 2 = EU option available, good data protection practices
- 3 = US provider with DPA/AVV
- 4 = Data protection practices unclear
- 5 = Compliance risk, no clear policies

### 5. Vendor Risk (vendor_risk)
- 1 = EU provider, low dependency
- 2 = Established provider with EU presence
- 3 = US provider with clear policies
- 4 = Dependency on single provider
- 5 = Unclear policies, high dependency

### 6. EU Hosting (eu_hosting)
- true = EU servers available
- false = US/Non-EU only
- null = Unknown

### 7. Fit Scores (0.0 - 1.0)

Evaluate suitability for different company sizes:

**fit_solo** (Solo Entrepreneur):
- Consider: Cost, simplicity, time investment, self-service

**fit_team** (Team 2-10 people):
- Consider: Collaboration, cost per user, learning curve

**fit_sme** (SME 10-250 people):
- Consider: Scalability, governance, support, integration

## Output Format

Respond exclusively with a JSON object:

```json
{
  "tool_name": "{{TOOL_NAME}}",
  "category": "{{TOOL_CATEGORY}}",
  "cost_level": <1-5>,
  "complexity_level": <1-5>,
  "maturity_level": <1-5>,
  "compliance_score": <1-5>,
  "vendor_risk": <1-5>,
  "eu_hosting": <true|false|null>,
  "fit_solo": <0.0-1.0>,
  "fit_team": <0.0-1.0>,
  "fit_sme": <0.0-1.0>,
  "reasoning": "<Brief justification of the assessment>"
}
```

## Important Notes

- Be conservative with compliance ratings (when in doubt, score higher)
- Consider the specified industry in the fit assessment
- EU tools receive a bonus for compliance and vendor risk
- Open-source tools may score higher on complexity (self-hosting)
