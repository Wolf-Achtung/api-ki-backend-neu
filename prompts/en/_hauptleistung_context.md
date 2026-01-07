<!--
=============================================================================
MAIN SERVICE CONTEXT BLOCK v1.0 (central configuration)
=============================================================================
This file is referenced by all prompts that should focus on the
customer's main service. Addresses Problem #7:
Generic recommendations instead of tailored analysis.

USAGE in other prompts:
{% include '_hauptleistung_context.md' %}
=============================================================================
-->

## CORE INFORMATION: What This Business Does

{% if hauptleistung %}
The client describes their business as:
**"{{hauptleistung}}"**

This is the MOST IMPORTANT information for this analysis.
{% else %}
**Note:** No explicit main service specified.
Use {{OFFERING_LABEL}} as fallback: "{{OFFERING_LABEL}}"
{% endif %}

### STRICT RULES FOR THIS ANALYSIS:

1. **EVERY recommendation** must directly relate to "{{hauptleistung}}"
2. **NO generic phrases** like "optimize processes" or "increase efficiency"
3. **CONCRETE EXAMPLES** must literally reference the main service
4. **QUICK WINS** must explain how they help with "{{hauptleistung}}"

### EXAMPLE TRANSFORMATION:

{% if hauptleistung %}
**FORBIDDEN (too generic):**
"Introduce email automation to save time."

**CORRECT (main-service-focused):**
"Create email templates for {{hauptleistung}} inquiries – saves 30 min/inquiry."
{% endif %}

### CONTEXT VARIABLES (available):

- **hauptleistung:** "{{hauptleistung}}"
- **ZEITERSPARNIS_PRIORITAET:** "{{ZEITERSPARNIS_PRIORITAET}}"
- **KI_GUARDRAILS:** "{{KI_GUARDRAILS}}"
- **BRANCHE:** "{{BRANCHE_LABEL}}"
- **COMPANY_SIZE:** "{{COMPANY_SIZE}}"

