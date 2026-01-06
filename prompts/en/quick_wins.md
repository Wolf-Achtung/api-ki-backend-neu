<!-- PLATIN+++ PROMPT v8.0 - JSON Quick Wins Output -->
<!-- SECTION: quick_wins -->
<!-- OUTPUT: JSON ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}}, {{ki_guardrails}}, {{vision_3_jahre}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, COMPANY_SIZE, {{STUNDENSATZ_EUR}}, {{score_security}}, {{score_governance}} -->
<!-- TOKEN-BUDGET: 2000 (solo:0.8x=1600, team:1.0x=2000, sme:1.2x=2400) -->

=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- [✓] Generate 3–5 Quick Wins as a JSON array tailored to the provided business context.
- [✓] Every Quick Win must explicitly support the core service "{{hauptleistung}}" and use ALL 5 Goldnuggets.
- [✓] Quick Win #1 must solve {{ZEITERSPARNIS_PRIORITAET}} verbatim; Quick Win #2 must reference {{ki_projekte}} if provided, otherwise focus on productivity improvements for {{hauptleistung}}.
- [✓] Additional Quick Wins depend on the scores: if {{score_security}} < 50, create a security policy Quick Win (icon 🔒); if {{score_governance}} < 50, create a governance Quick Win (icon ✅); otherwise propose automation, tool optimisation or template actions (icons 🔧 ⚡ 📋 🎨 💬 📊 🔄) that align with {{vision_3_jahre}}.
- [✓] Each Quick Win MUST contain the following fields:
  1. "title" – succinct headline (max 60 characters)
  2. "icon" – one emoji (choose from 🎯 🚀 💡 🔒 ✅ 🔧 ⚡ 📋 🎨 💬 📊 🔄)
  3. "time" – estimated monthly time investment (e.g. "6–10 h/month")
  4. "bottleneck" – your specific pain point (quote from {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}} or context)
  5. "description" – 2–3 sentences explaining the current problem with industry context
  6. "with_ai" – 2–3 sentences describing the AI solution, including concrete tools and respecting {{ki_guardrails}}
  7. "steps" – an array of 3–5 numbered actions with time or cost estimates and tool names
  8. "time_saving" – hours saved per month and euro value based on {{STUNDENSATZ_EUR}}
- [✓] Respect company size guidelines:
  - **Solo**: exactly 3 Quick Wins, use direct "you" language, budget ≤ €50/month.
  - **Team**: exactly 4 Quick Wins, address "you/your team", budget ≤ €200/month.
  - **SME**: 4–5 Quick Wins, address "your organisation/your teams", budgets should be scalable.
- [✓] Output MUST be valid JSON only. Do not include markdown fences, HTML tags or any explanatory text. Begin with "[" and end with "]".
- [✓] Use concrete tool names (e.g. ChatGPT Plus, Claude Pro, Microsoft Copilot). Avoid vague phrases and generic automation suggestions. Align each Quick Win with {{vision_3_jahre}} and the main service.
=============================================================================

## Input Context

Use the following information to personalise the Quick Wins:

**Industry:** {{BRANCHE_LABEL}}

**Company Size:** {{UNTERNEHMENSGROESSE_LABEL}} (COMPANY_SIZE = solo/team/sme)

**Hourly Rate:** {{STUNDENSATZ_EUR}}€/h

**Security Score:** {{score_security}}/100

**Governance Score:** {{score_governance}}/100

**Main Service:** "{{hauptleistung}}"

**Time‑Saving Priority:** "{{ZEITERSPARNIS_PRIORITAET}}"

**Planned AI Projects:** {% if ki_projekte %}"{{ki_projekte}}"{% else %}None{% endif %}

**Guardrails:** {% if ki_guardrails %}"{{ki_guardrails}}"{% else %}None{% endif %}

**Three‑Year Vision:** "{{vision_3_jahre}}"

## JSON Format Example (for illustration only)

```json
[
  {
    "title": "Short descriptive title",
    "icon": "🎯",
    "time": "6–10 h/month",
    "bottleneck": "Your biggest time drain quoted from ZEITERSPARNIS_PRIORITAET",
    "description": "Explain the current pain point in 2–3 sentences with industry context.",
    "with_ai": "Describe how a specific AI tool helps solve the problem, referencing guardrails if needed.",
    "steps": [
      "Concrete step 1 with time or cost",
      "Concrete step 2 with tool name",
      "Concrete step 3 with measurable outcome"
    ],
    "time_saving": "6–10 h/month = 600–1,000€ (at {{STUNDENSATZ_EUR}}€/h)"
  }
]
```

## Mandatory Rules

- Quick Win #1 must quote "{{ZEITERSPARNIS_PRIORITAET}}" verbatim in the "bottleneck" field.
- Quick Win #2 must reflect "{{ki_projekte}}" (if provided) in the "bottleneck" and description fields; otherwise propose a productivity improvement fitting "{{hauptleistung}}".
- Subsequent Quick Wins must be guided by the Security and Governance scores and the long‑term vision.
- Every Quick Win must have a copy‑paste prompt within the "with_ai" field. Include tool names (e.g. ChatGPT Plus, Claude Pro, Microsoft Copilot) and mention {{ki_guardrails}} if applicable.
- Setup steps must include 3–5 items, each with a time or cost estimate.
- ROI must clearly state hours saved and euro value, using {{STUNDENSATZ_EUR}} as the basis.
- Do not use generic automation phrases or enterprise jargon. All language should be professional and aligned with the company size.

## Now generate the Quick Wins!

Return only the JSON array as your output. Do not wrap it in Markdown fences or add any explanatory text before or after the array.