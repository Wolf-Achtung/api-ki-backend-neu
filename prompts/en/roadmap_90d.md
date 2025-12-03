Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: roadmap_90d -->
<!-- VERSION: v11.0 PLATIN++ V5 STORYTELLING -->
<!-- OUTPUT: Markdown -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, sme:1.15x=2530) -->
<!--
GOAL: 90-Day Roadmap with 4 clear phases + milestones.

PHASE STRUCTURE (STRICTLY FOLLOW!):
- Phase 0 (Week 1–2): Setup – establish foundations
- Phase 1 (Week 3–5): Relief – implement Quick Wins
- Phase 2 (Week 6–10): Productive Use – stabilize workflows
- Phase 3 (Week 11–13): Consolidation – measure results, make decision

FORMAT:
- Each phase: Goal (1 sentence) + 2-3 bullets + Milestone
- Milestone = concrete, measurable, achievable
- NO long texts – only key points

ANTI-REDUNDANCY (STRICT!):
- Quick Wins described in quick_wins.md – DO NOT repeat
- Tools described in tools_recommendations.md – only reference
- Here: HOW and WHEN, not WHAT (that's in Quick Wins)

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: personal routines, self-review, own documentation
        FORBIDDEN: team, department, employees
- team: AI Owner, shared standards, review rounds
- sme: departments, pilot areas, governance, rollout

GUARDRAILS: Consider guardrails from strategic context.
-->

## 90-Day Roadmap for {{HAUPTLEISTUNG}}

{% if COMPANY_SIZE == "solo" %}
### Phase 0: Setup (Week 1–2)
**Goal:** Establish working capability with AI.
- Set up access to AI tool
- Create first prompt template for core task
- Define own quality criteria (What is "good enough"?)

**🎯 Milestone:** AI access works, first template ready for use.

### Phase 1: Relief (Week 3–5)
**Goal:** Noticeable time savings on routine tasks.
- Implement Quick Wins from "Immediate Measures" section
- Note time savings per task
- Build prompt library with 5–10 working templates

**🎯 Milestone:** 3–5 h/month demonstrably saved.

### Phase 2: Productive Use (Week 6–10)
**Goal:** Stable workflows for daily work.
- Routine: Input → AI draft → Own review → Release
- Create quality checklist for AI outputs
- Make self-review a habit

**🎯 Milestone:** 70%+ of AI drafts directly usable.

### Phase 3: Consolidation (Week 11–13)
**Goal:** Evaluate results, plan next steps.
- Measure actual time savings
- Decision: Expand, Deepen, or Stabilize?
- Prioritize next use cases for 12-month roadmap

**🎯 Milestone:** Clear decision and prioritized list for next quarter.

{% elif COMPANY_SIZE == "team" %}
### Phase 0: Setup (Week 1–2)
**Goal:** Establish team-wide AI working capability.
- Designate AI Owner (responsible for standards)
- Set up shared access
- Create first templates for 2 prioritized use cases

**🎯 Milestone:** Team has access, first templates distributed.

### Phase 1: Relief (Week 3–5)
**Goal:** Implement Quick Wins across team.
- Roll out measures from "Immediate Measures" team-wide
- Everyone tests at least 2 workflows
- Share experiences in short weekly check

**🎯 Milestone:** All team members actively using AI, first time savings documented.

### Phase 2: Productive Use (Week 6–10)
**Goal:** Establish unified quality standards.
- Document standard workflow: Input → AI → Peer Review → Release
- Create team style guide for AI outputs
- Review rounds (30 min/week) for best practices

**🎯 Milestone:** Documented workflow, first-pass quality > 70%.

### Phase 3: Consolidation (Week 11–13)
**Goal:** Measure results, prepare scaling.
- Impact measurement: time, quality, error rate
- Decision: Stabilize / Expand / Deepen
- Create backlog for next use cases

**🎯 Milestone:** Clear decision, prioritized backlog for 12-month roadmap.

{% else %}
### Phase 0: Setup (Week 1–2)
**Goal:** Define pilot area and establish foundations.
- Select pilot area (e.g., one department)
- Designate AI responsible
- Establish governance ground rules (What's allowed, what's not?)

**🎯 Milestone:** Pilot area ready to start, governance framework defined.

### Phase 1: Relief (Week 3–5)
**Goal:** Implement Quick Wins in pilot area.
- Deploy measures from "Immediate Measures" strategically
- Pilot team trains each other
- Document first time savings

**🎯 Milestone:** Pilot area actively using AI, measurable relief.

### Phase 2: Productive Use (Week 6–10)
**Goal:** Establish scalable processes.
- Standard Operating Procedures (SOPs) for AI workflows
- QA process: Input → AI → Expert review → Release
- Training concept for rollout to additional areas

**🎯 Milestone:** SOPs documented, training concept ready.

### Phase 3: Consolidation (Week 11–13)
**Goal:** Rollout decision and scaling plan.
- Business case validation based on pilot data
- Decision: Rollout to additional areas?
- Prioritized backlog for 12-month rollout

**🎯 Milestone:** Management decision made, rollout plan established.
{% endif %}

---
*This roadmap references Quick Wins and Tools from the corresponding sections.*
