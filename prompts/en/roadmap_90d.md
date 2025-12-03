Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: roadmap_90d -->
<!-- VERSION: v10.0 PLATIN++ V5 -->
<!-- OUTPUT: Markdown -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, sme:1.15x=2530) -->
<!--
GOAL: 90-Day Roadmap with 3 phases, compact and actionable.

WORD LIMITS (PDF-SLIMDOWN):
- solo: ~180 words (150–200)
- team: ~220 words (200–250)
- sme: ~280 words (260–320)

STRUCTURE: ONLY 3 phases
1. Week 1–4: Setup & first wins
2. Week 5–8: Quality & workflows
3. Week 9–13: Consolidation

ANTI-REDUNDANCY (STRICT!):
- Quick Wins already covered in quick_wins.md – DO NOT repeat
- Pain Points addressed there – only BUILD on them here
- Tools described in tools_recommendations.md – only reference

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: personal routines, own documentation, self-review
- team: roles (AI Owner, Reviewer), shared standards
- sme: departments, governance, pilot areas

GUARDRAILS: Consider guardrails from strategic context.

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
