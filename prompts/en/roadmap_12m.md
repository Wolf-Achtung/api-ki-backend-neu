Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G5 -->
<!-- SECTION: roadmap_12m -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2800 (solo:0.8x=2240, team:1.0x=2800, sme:1.15x=3220) -->
<!--
GOAL: 12-Month Roadmap with milestones, building on 90-day results.

MINIMUM LENGTH (SPRINT G18 - STRICTLY MANDATORY!):
- Solo: at least 500 words (including Q1-Q4 phases)
- Team: at least 600 words (including roles and standards)
- SME: at least 700 words (including 5-dimension rollout)

IMPORTANT: These minimum lengths are mandatory and will be validated!

SHORT LABELS (MANDATORY!):
- {{BRANCH_CORE_LABEL}} = Industry in 8-12 words
- {{BRANCH_CONTEXT_LABEL}} = Industry in 4-6 words
- {{OFFERING_LABEL}} = Main service in 6-10 words
- NO long industry texts in output!

STRUCTURE BY SIZE (max 3 main sections):
- Solo: Time-based phases (Q1, Q2, Q3-4)
- Team: Time-based phases with roles
- SME: Block structure (Tech, Data, Org, Product, Compliance) + Rollout

FORMAT:
- Milestones instead of long texts
- Each block: 2-3 concrete measures + 1 milestone
- Realistic time horizons

ANTI-REDUNDANCY (STRICT!):
- 90-day content → DO NOT repeat (already done there)
- Quick Wins → DO NOT repeat
- Tools → DO NOT repeat
- Focus: WHAT COMES AFTER the first 90 days?
- On overlap: use cross-reference (→ see Section X)

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: own workflows, self-review, personal routine
- team: AI coordinator, shared standards, review rounds
- sme: departments, governance board, rollout plan, compliance

SPRINT G5 - PERSONA HARD-GUARDS (STRICT!):
{% if COMPANY_SIZE == "solo" %}
SOLO MODE - FORBIDDEN:
- "Team/Teams" → "Capacity/Resources"
- "Department" → "Work area"
- "Employees" → "external support"
- "HR/Division" → do not use
{% elif COMPANY_SIZE == "team" %}
TEAM MODE - FORBIDDEN:
- "Department/Division" → "Area"
- "Unit/Corporation" → do not use
- "Governance Board" → "Team Lead"
- Solo terms: "individual", "alone"
{% else %}
SME MODE - FORBIDDEN:
- "Corporation/Division/Unit" → do not use
- Solo terms: "individual", "alone", "personal"
- Avoid governance jargon overload
{% endif %}
-->

## 12-Month Roadmap for {{OFFERING_LABEL}}

{% if COMPANY_SIZE == "solo" %}
Building on the first 90 days – focus on sustainable integration and expansion.

### Q1 (Months 1–3): Solidify Foundation
- Turn successful workflows from 90-day phase into routine
- Test 2–3 additional use cases from {{BRANCH_CONTEXT_LABEL}}
- Expand personal prompt library to 20+ templates

**🎯 Milestone Q1:** 10+ h/month stable time savings.

### Q2 (Months 4–6): Increase Quality
- Apply quality checklist to all AI outputs
- Systematically integrate first data sources (CRM, notes, documents)
- Create workflow documentation for backup/scaling

**🎯 Milestone Q2:** 90%+ first-pass rate on standard tasks.

### Q3–Q4 (Months 7–12): Expand & Optimize
- Open new application areas (marketing, customer communication, reporting)
- Systematically measure and document time savings
- Annual review: calculate ROI, set priorities for year 2

**🎯 Milestone Year-End:** Demonstrable ROI, clear priorities for next year.

{% elif COMPANY_SIZE == "team" %}
Building on the first 90 days – focus on team scaling.

### Q1 (Months 1–3): Establish Team Standards
- Designate AI Coordinator (responsible for quality & standards)
- Build shared prompt library with 30+ templates
- Introduce weekly 15-min reviews for best practices

**🎯 Milestone Q1:** All team members using AI regularly.

### Q2 (Months 4–6): Quality & Data
- Formalize QA process: Input → AI → Review → Release
- Create team style guide for AI outputs
- First data integration (shared documents, CRM)

**🎯 Milestone Q2:** Consistent quality, error rate < 10%.

### Q3–Q4 (Months 7–12): Scaling & ROI
- Explore new use cases from adjacent areas
- Expand success measurement (time, costs, quality)
- Annual review: budget and priorities for year 2

**🎯 Milestone Year-End:** Demonstrable ROI, Roadmap 2.0 established.

{% else %}
Building on the first 90 days – professional rollout across 5 dimensions.

### Dimension 1: Technology (Q1–Q2)
- Finalize tool stack (licenses, access, integrations)
- Review data interfaces to existing systems
- Create technical documentation

**🎯 Milestone:** Tech stack stable, integrations functional.

### Dimension 2: Data (Q1–Q2)
- Identify and connect relevant data sources
- Ensure data quality for AI usage
- Clarify access rights and data protection

**🎯 Milestone:** Core data available for AI and compliant.

### Dimension 3: Organization (Q2–Q3)
- Designate AI responsibles in each department
- Roll out training concept
- Establish governance board (quarterly review)

**🎯 Milestone:** Clear responsibilities, trained employees.

### Dimension 4: Product/Process (Q2–Q4)
- Rollout to 2–3 additional departments after pilot success
- Standard Operating Procedures (SOPs) for all AI processes
- Impact measurement per area (time, costs, quality)

**🎯 Milestone:** 3+ areas productive, measurable efficiency gains.

### Dimension 5: Compliance (Q3–Q4)
- Review and document AI Act relevance
- Conduct risk assessment for AI applications
- Implement transparency requirements (where AI is in use)

**🎯 Milestone:** Compliance documentation complete.

### Year-End Review
- Management review with ROI proof
- Budget planning for year 2
- Roadmap 2.0 with scaling goals

**🎯 Milestone Year-End:** Board decision for year 2, rollout plan established.
{% endif %}

---
*This roadmap builds on 90-day results and references Quick Wins and Tools from the corresponding sections.*
