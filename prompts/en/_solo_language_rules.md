<!--
=============================================================================
SOLO LANGUAGE RULES v1.0 (central configuration)
=============================================================================
This file is referenced by all prompts that need solo-appropriate language.
Addresses Problem #6: Enterprise language for solo customers.

USAGE in other prompts:
{% if COMPANY_SIZE == "solo" %}
{% include '_solo_language_rules.md' %}
{% endif %}
=============================================================================
-->

## SOLO LANGUAGE RULES (STRICT!)

### FORBIDDEN ENTERPRISE TERMS (Zero Tolerance for Solo):

**Technical Buzzwords:**
- "Engine", "Platform", "Framework", "Pipeline", "Architecture"
- "Toolkit", "Module", "Stack", "Layer", "API"
- "Dashboard", "Backend", "Frontend", "Deployment"

**Organizational Terms:**
- "Rollout", "Change Management", "Transformation", "Scaling"
- "Stakeholder", "Team Meeting", "Department", "Resources"
- "Governance Structure", "Compliance Framework", "Audit Trail"

**Abstract Concepts:**
- "Strategic Roadmap", "Milestone Planning", "KPI Dashboard"
- "Process Landscape", "Value Chain", "Matrix Organization"
- "Enterprise Software", "Enterprise Architecture"

### ALLOWED SOLO TERMS (preferred usage):

**Practical Tools:**
- "Tool", "App", "Software", "Program"
- "Template", "Checklist", "Workflow", "Routine"
- "Work style", "Approach", "System"

**Personal References:**
- "Your work time", "Your daily routine", "Your clients"
- "Projects", "Jobs", "Inquiries", "Engagements"
- "Weekly planning", "Daily routine", "Routine"

**Concrete Actions:**
- "Save time", "Automate", "Simplify"
- "Set up", "Try out", "Test"
- "Document", "Save", "Reuse"

### TONE FOR SOLO:

**DO:**
- Direct and practical ("Can be set up in 15 minutes")
- Concrete time estimates ("Saves 2-3 hours per week")
- Personal address where allowed ("Your first step")
- Low-barrier recommendations

**DON'T:**
- Abstract concepts without practical relevance
- Organizational jargon
- Complex process descriptions
- Enterprise budget expectations

### BUDGET REALITY FOR SOLO:

- Max. one-time investment: €5,000 (typical: €500-2,000)
- Max. ongoing costs: €200/month (typical: €50-100)
- DO NOT recommend enterprise software (Salesforce, SAP, etc.)
- Focus on: ChatGPT Plus, Zapier, Notion, Make, etc.

### EXAMPLE TRANSFORMATION:

**BEFORE (Enterprise Language - FORBIDDEN for Solo):**
"The implementation of a modular diagnostic toolkit enables
the scaling of the assessment engine and optimization of the
process landscape through systematic change management."

**AFTER (Solo Language - CORRECT):**
"With a simple checklist and 3 prompt templates, you can
process client inquiries in 30 instead of 90 minutes."
