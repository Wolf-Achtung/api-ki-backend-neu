<!--
=============================================================================
PERSONA GUARDRAILS v1.0 (central configuration)
=============================================================================
This file defines language guardrails based on company size.
Referenced by all prompts that need to be size-aware.

USAGE in other prompts:
{% raw %}{% include '_persona_guardrails.md' %}{% endraw %}

FIX-SOLO-VEREINFACHUNG: Solo reports use simplified language
without enterprise terminology.
=============================================================================
-->

## STRICT PERSONA RULES (Company Size: {{COMPANY_SIZE}})

{% if COMPANY_SIZE == "solo" %}
<!--
=============================================================================
SOLO MODE: Simplified language for solo entrepreneurs
=============================================================================
-->

### SOLO - FORBIDDEN TERMS (Blacklist)
NEVER use these terms:
- "Stack" → use "toolkit" or "setup"
- "Architecture" → use "structure" or "setup"
- "Stakeholder" → use "partners" or "contacts"
- "Platform" → use "solution" or "system"
- "Layer" → use "level" or "area"
- "KPI Dashboard" → use "success metrics"
- "Rollout" → use "introduction"
- "Scaling" → use "growth"
- "Team" / "Department" → use "you" / "your work"
- "Project team" → use "your capacity"
- "Employees" → DO NOT use (Solo = 1 person)
- "Onboarding" → use "getting started"
- "Stakeholder Management" → DO NOT use
- "Change Management" → use "transition"
- "Governance Framework" → use "basic rules"

### SOLO - ALLOWED TERMS (Whitelist)
Prefer these terms:
- "Toolkit" instead of "stack"
- "Setup" instead of "architecture"
- "Checklist" instead of "framework"
- "Routine" instead of "process"
- "Introduction" instead of "rollout"
- "Growth" instead of "scaling"
- "Simple success metrics" instead of "KPI dashboard"
- "You" instead of "the team"
- "Your daily work" instead of "operations"
- "Your business" instead of "the organization"

### SOLO - TONE AND STYLE
- Direct address with "you" (single person)
- No team or department logic
- No roles like "project manager", "IT department", "HR"
- Pragmatic and actionable, no enterprise complexity
- Governance = 1-page checklist, no programs
- Realistic budget for solopreneurs (max. 3,000 EUR/phase)

{% elif COMPANY_SIZE == "team" %}
<!--
=============================================================================
TEAM MODE: For small teams (2-10 people)
=============================================================================
-->

### TEAM - FORBIDDEN TERMS (Blacklist)
NEVER use these terms:
- "Division" / "Unit" / "Corporation" → too large
- "Enterprise" → too large
- "Solo terms": "individual", "alone", "just you"
- "C-Level" / "Board" → too formal for small teams
- "Stakeholder Management" → use "coordination"

### TEAM - ALLOWED TERMS (Whitelist)
Prefer these terms:
- "Team" / "colleagues" / "teammates"
- "Responsible person" instead of "owner"
- "Together" / "jointly"
- "Quick sync" instead of "meeting series"
- "Clear task distribution"
- "Peer review" for quality checks

### TEAM - TONE AND STYLE
- "You and your team"
- Simple role assignments (max. 2-3 roles)
- Pragmatic coordination processes
- Realistic budget for small teams (max. 15,000 EUR/phase)

{% else %}
<!--
=============================================================================
SME MODE: For SMEs (11-100 people)
=============================================================================
-->

### SME - FORBIDDEN TERMS (Blacklist)
NEVER use these terms:
- "Corporation" / "Division" / "Unit" → too large
- "Solo terms": "individual", "alone"
- "Startup speak" without substance

### SME - ALLOWED TERMS (Whitelist)
These terms are appropriate:
- "Departments" / "Teams"
- "Project team" / "Core team"
- "Leads" / "Responsible persons"
- "Governance" / "Policies"
- "Processes" / "Workflows"
- "Coordination meetings" / "Approvals"

### SME - TONE AND STYLE
- "Your company" / "your organization"
- Clear roles and responsibilities
- Structured processes with documentation
- Four-eyes principle for important decisions
- Realistic budget for SMEs (max. 60,000 EUR/phase)

{% endif %}

<!--
=============================================================================
UNIVERSAL RULES (for all sizes)
=============================================================================
-->

### UNIVERSAL STYLE RULES

1. **Main service first**: All recommendations relate to "{{hauptleistung}}"
2. **No assumptions**: Only use what's in the JSON
3. **Concrete over abstract**: Examples instead of generalities
4. **GDPR-aware**: Data protection pragmatic, not legalistic
5. **AI Act-aware**: No high-risk applications without notice

### ANTI-PATTERNS (NEVER)
- No placeholders like "[Insert here]" or "{{variable}}"
- No meta-language like "This section describes..."
- No developer comments in output
- No generic phrases without reference to main service
- No contradictions to questionnaire answers
