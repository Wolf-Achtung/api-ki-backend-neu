Developer:
<!-- roadmap_90d.md – v9.0 PDF-SLIMDOWN-STRICT
     Output: Markdown (converted to HTML server-side)

     **STRICT TOKEN LIMIT (CRITICAL!):**
     MAXIMUM 350-450 words output.

     **Word Limits (STRICTLY REDUCED):**
     - Solo: ~180 words (acceptable: 150–200)
     - Team: ~220 words (acceptable: 200–250)
     - SME: ~280 words (acceptable: 260–320)

     STRUCTURE: ONLY 3 phases! (not 6)
       1. Week 1–4: Setup & first wins (~120 words)
       2. Week 5–8: Quality & workflows (~120 words)
       3. Week 9–13: Consolidation (~100 words)

     **FOCUS: ONLY 3 QUICK-IMPACT MEASURES**
     - No vision, no meta sections
     - No detailed explanations
     - Directly actionable steps

     VARIABLES:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE

     SIZE-AWARE (COMPANY_SIZE):
       solo: personal routines, own documentation, no teams
       team: roles, shared standards, coordination
       sme: departments, governance, pilot areas

     FORMAT: Markdown (## for phases, - for bullets), NO HTML
-->

## Strategic 90-Day Roadmap

Structured plan for **{{HAUPTLEISTUNG}}** in the **{{BRANCHE_LABEL}}** industry ({{UNTERNEHMENSGROESSE_LABEL}}).

## Week 1–4: Setup & First Wins

**Goal:** Start AI usage, realize first Quick Wins.

- Define 1–2 prioritized use cases from {{BRANCHE_LABEL}}
- Test first prompts/workflows for {{HAUPTLEISTUNG}}
- Establish quality criteria (facts, tone, approval)

**Responsible:** {% if COMPANY_SIZE == "solo" %}Owner{% elif COMPANY_SIZE == "team" %}Team lead + AI Owner{% else %}Department + process owners{% endif %}

**KPI:** 2 use cases tested, first time savings measurable.

## Week 5–8: Quality & Stable Workflows

**Goal:** Ensure reproducible results.

- Document standard workflows (Input → AI → Review → Approval)
- Create brief style guide for AI outputs
- {% if COMPANY_SIZE == "solo" %}Self-review routine{% elif COMPANY_SIZE == "team" %}Establish team review{% else %}Coordinate QA processes{% endif %}

**Responsible:** {% if COMPANY_SIZE == "solo" %}Own documentation{% elif COMPANY_SIZE == "team" %}Quality responsible{% else %}Department + QA{% endif %}

**KPI:** Documented workflows, first-pass rate > 70%.

## Week 9–13: Consolidation & Decision

**Goal:** Evaluate results, prepare scaling.

- Impact measurement (time, quality, error rate)
- Decision: Stabilize / Expand / Deepen
- Prioritize {% if COMPANY_SIZE == "kmu" %}scaling backlog{% else %}next use cases{% endif %}

**Responsible:** {% if COMPANY_SIZE == "solo" %}Management{% elif COMPANY_SIZE == "team" %}Leadership + AI Owner{% else %}Management + department heads{% endif %}

**KPI:** Clear decision for next 6–12 months, prioritized backlog.

---

This 90-day roadmap creates the foundation for stable AI usage in **{{HAUPTLEISTUNG}}** and prepares scaling.
