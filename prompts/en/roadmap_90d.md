Developer:
<!-- PLATIN+++ PROMPT v7.0 - PHASE 3 HYPER-PERSONALIZATION -->
<!-- SECTION: roadmap_90d -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}}, {{BRANCHE_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2000 (solo:0.8x=1600, team:1.0x=2000, sme:1.15x=2300) -->
<!--
=============================================================================
PLATIN+++ v7.0: HYPER-PERSONALIZED 90-DAY ROADMAP (Phase 3 Sprint 1)
=============================================================================

CRITICAL v7.0 CHANGES:
1. ALL 5 Goldnuggets (freetext fields) MUST be used
2. Phase 1 MUST reference {{ZEITERSPARNIS_PRIORITAET}} in title
3. Phase 3 MUST reference {{VISION_3_JAHRE}} and {{ki_projekte}}
4. {{KI_GUARDRAILS}} MUST appear in Phase 0 and Phase 2
5. COMPACT format - max 1-1.5 pages

=============================================================================
THE 5 GOLDNUGGETS - USE ALL OF THEM!
=============================================================================

1. {{hauptleistung}} - Core business/offering
   → Use in ALL phases as context

2. {{ZEITERSPARNIS_PRIORITAET}} - Where time is lost
   → Phase 1 title MUST include this

3. {{ki_projekte}} - Planned AI projects
   → Phase 3 MUST reference this for next steps

4. {{KI_GUARDRAILS}} - What's off-limits
   → Phase 0: Document as review checklist
   → Phase 2: Include in quality checks

5. {{VISION_3_JAHRE}} - Long-term vision
   → Phase 3 title and goal MUST reference this

=============================================================================
COMPACT PHASE STRUCTURE (STRICT!)
=============================================================================

Each phase MUST have:
- Dynamic title with Goldnugget reference
- Goal (1 sentence)
- 3 bullet points (checkboxes ☐)
- Milestone (1 sentence)

FORBIDDEN:
- Long paragraphs
- Generic phrases like "implement Quick Wins"
- Booster sections (KPI Tracking, Change Management) - REMOVED for compactness
- More than 3 bullets per phase

=============================================================================
PERSONA VARIATIONS:
=============================================================================

{% if COMPANY_SIZE == "solo" %}
SOLO: "You", personal routines, max €50/month tools
FORBIDDEN: team, department, employees, stakeholders
{% elif COMPANY_SIZE == "team" %}
TEAM: "You/Your team", shared standards, AI Owner role
FORBIDDEN: division, corporation, stakeholders
{% else %}
SME: "Your organization", pilot area, governance
FORBIDDEN: corporation, division, stakeholders
{% endif %}

=============================================================================
-->

<section class="section roadmap-90d">
  <h2>90-Day Roadmap for {{hauptleistung}}</h2>

  <p>
    Your personalized implementation plan for AI in {{BRANCHE_LABEL}} –
    focused on relieving <strong>{{ZEITERSPARNIS_PRIORITAET}}</strong>
    and building toward <strong>{{VISION_3_JAHRE}}</strong>.
  </p>

  {% if COMPANY_SIZE == "solo" %}
  <!--
  =============================================================================
  SOLO VERSION - COMPACT & PERSONAL
  =============================================================================
  -->
  <h3>Phase 0: Setup for {{hauptleistung}} (Week 1–2)</h3>
  <p><strong>Goal:</strong> Get AI working for your {{hauptleistung}} workflow.</p>
  <ul>
    <li>☐ Set up AI access (Claude Pro €18/month or ChatGPT Plus €20/month)</li>
    <li>☐ Create first prompt template for {{hauptleistung}}</li>
    <li>☐ Document your guardrails as review checklist: <em>{{KI_GUARDRAILS}}</em></li>
  </ul>
  <p><strong>Milestone:</strong> AI access works, first {{hauptleistung}} template ready.</p>

  <h3>Phase 1: Relieve "{{ZEITERSPARNIS_PRIORITAET}}" (Week 3–5)</h3>
  <p><strong>Goal:</strong> Noticeable time savings on your biggest bottleneck.</p>
  <ul>
    <li>☐ Build template library with 3-5 templates for {{hauptleistung}}</li>
    <li>☐ Track time saved on {{ZEITERSPARNIS_PRIORITAET}} (simple tally)</li>
    <li>☐ Establish daily routine: One {{hauptleistung}} task with AI</li>
  </ul>
  <p><strong>Milestone:</strong> 3-5 hours/month saved on {{ZEITERSPARNIS_PRIORITAET}}.</p>

  <h3>Phase 2: Stabilize {{hauptleistung}} Workflow (Week 6–10)</h3>
  <p><strong>Goal:</strong> Reliable AI workflow you can trust.</p>
  <ul>
    <li>☐ Solidify workflow: Input → AI draft → Review against <em>{{KI_GUARDRAILS}}</em> → Release</li>
    <li>☐ Refine templates based on what works</li>
    <li>☐ Achieve 70%+ first-draft quality</li>
  </ul>
  <p><strong>Milestone:</strong> AI is part of daily {{hauptleistung}} work.</p>

  <h3>Phase 3: Scale Toward "{{VISION_3_JAHRE}}" (Week 11–13)</h3>
  <p><strong>Goal:</strong> Decide next steps toward your vision.</p>
  <ul>
    <li>☐ Measure actual impact: time saved, quality, ROI</li>
    {% if ki_projekte %}
    <li>☐ Evaluate starting <em>{{ki_projekte}}</em> as next project</li>
    {% else %}
    <li>☐ Identify next 2-3 areas for AI expansion</li>
    {% endif %}
    <li>☐ Create prioritized roadmap toward {{VISION_3_JAHRE}}</li>
  </ul>
  <p><strong>Milestone:</strong> Clear decision and next steps toward {{VISION_3_JAHRE}}.</p>

  <h3>Expected Effects after 90 Days</h3>
  <ul>
    <li><strong>Time Savings:</strong> 40-60% reduction on {{ZEITERSPARNIS_PRIORITAET}}</li>
    <li><strong>Quality:</strong> Consistent {{hauptleistung}} outputs</li>
    <li><strong>Compliance:</strong> {{KI_GUARDRAILS}} systematically checked</li>
    <li><strong>Clarity:</strong> Foundation for scaling toward {{VISION_3_JAHRE}}</li>
  </ul>

  {% elif COMPANY_SIZE == "team" %}
  <!--
  =============================================================================
  TEAM VERSION - SHARED STANDARDS
  =============================================================================
  -->
  <h3>Phase 0: Team Setup for {{hauptleistung}} (Week 1–2)</h3>
  <p><strong>Goal:</strong> Team-wide AI capability for {{hauptleistung}}.</p>
  <ul>
    <li>☐ Designate AI Owner for {{hauptleistung}} standards</li>
    <li>☐ Set up shared access and first templates</li>
    <li>☐ Document {{KI_GUARDRAILS}} as team review checklist</li>
  </ul>
  <p><strong>Milestone:</strong> Team has access, first {{hauptleistung}} templates distributed.</p>

  <h3>Phase 1: Team Relief for "{{ZEITERSPARNIS_PRIORITAET}}" (Week 3–5)</h3>
  <p><strong>Goal:</strong> Measurable time savings across the team.</p>
  <ul>
    <li>☐ Roll out template library for {{hauptleistung}} team-wide</li>
    <li>☐ Everyone tests at least 2 workflows</li>
    <li>☐ Document time savings on {{ZEITERSPARNIS_PRIORITAET}} in weekly check</li>
  </ul>
  <p><strong>Milestone:</strong> All team members using AI, savings documented.</p>

  <h3>Phase 2: Establish {{hauptleistung}} Standard (Week 6–10)</h3>
  <p><strong>Goal:</strong> Unified quality standards for {{hauptleistung}}.</p>
  <ul>
    <li>☐ Document workflow: Input → AI → Review against {{KI_GUARDRAILS}} → Release</li>
    <li>☐ Create style guide for {{hauptleistung}} outputs</li>
    <li>☐ Establish review rounds with {{KI_GUARDRAILS}} checks</li>
  </ul>
  <p><strong>Milestone:</strong> Documented {{hauptleistung}} workflow, 70%+ first-pass quality.</p>

  <h3>Phase 3: Scale Toward "{{VISION_3_JAHRE}}" (Week 11–13)</h3>
  <p><strong>Goal:</strong> Measure results, prepare scaling.</p>
  <ul>
    <li>☐ Impact measurement: time, quality, satisfaction</li>
    {% if ki_projekte %}
    <li>☐ Evaluate <em>{{ki_projekte}}</em> as next team project</li>
    {% else %}
    <li>☐ Prioritize next use cases for expansion</li>
    {% endif %}
    <li>☐ Decision: Stabilize / Expand toward {{VISION_3_JAHRE}} / Deepen</li>
  </ul>
  <p><strong>Milestone:</strong> Clear team decision, roadmap toward {{VISION_3_JAHRE}}.</p>

  <h3>Expected Effects after 90 Days</h3>
  <ul>
    <li><strong>Time Savings:</strong> 30-50% on {{ZEITERSPARNIS_PRIORITAET}} team-wide</li>
    <li><strong>Quality:</strong> Consistent {{hauptleistung}} through shared standards</li>
    <li><strong>Compliance:</strong> {{KI_GUARDRAILS}} in all team reviews</li>
    <li><strong>Scalability:</strong> Ready to expand toward {{VISION_3_JAHRE}}</li>
  </ul>

  {% else %}
  <!--
  =============================================================================
  SME VERSION - PILOT & GOVERNANCE
  =============================================================================
  -->
  <h3>Phase 0: Pilot Setup for {{hauptleistung}} (Week 1–2)</h3>
  <p><strong>Goal:</strong> Define pilot area and governance framework.</p>
  <ul>
    <li>☐ Select pilot area for {{hauptleistung}} (high relief potential)</li>
    <li>☐ Designate AI responsible and document {{KI_GUARDRAILS}} as governance rules</li>
    <li>☐ Set up access and first templates for pilot</li>
  </ul>
  <p><strong>Milestone:</strong> Pilot area ready, {{KI_GUARDRAILS}} governance defined.</p>

  <h3>Phase 1: Pilot Relief for "{{ZEITERSPARNIS_PRIORITAET}}" (Week 3–5)</h3>
  <p><strong>Goal:</strong> Measurable relief in pilot area.</p>
  <ul>
    <li>☐ Deploy template library for {{hauptleistung}} in pilot</li>
    <li>☐ Train pilot area through peer learning</li>
    <li>☐ Quantify time savings on {{ZEITERSPARNIS_PRIORITAET}}</li>
  </ul>
  <p><strong>Milestone:</strong> Pilot actively using AI, measurable relief documented.</p>

  <h3>Phase 2: Establish {{hauptleistung}} SOPs (Week 6–10)</h3>
  <p><strong>Goal:</strong> Scalable processes with quality assurance.</p>
  <ul>
    <li>☐ Document SOPs: Input → AI → Review against {{KI_GUARDRAILS}} → Release</li>
    <li>☐ Define quality criteria and KPIs for {{hauptleistung}}</li>
    <li>☐ Develop training concept for rollout</li>
  </ul>
  <p><strong>Milestone:</strong> SOPs documented, training concept ready, KPIs defined.</p>

  <h3>Phase 3: Rollout Decision Toward "{{VISION_3_JAHRE}}" (Week 11–13)</h3>
  <p><strong>Goal:</strong> Management decision on scaling.</p>
  <ul>
    <li>☐ Validate business case with pilot data</li>
    {% if ki_projekte %}
    <li>☐ Evaluate <em>{{ki_projekte}}</em> for organization-wide rollout</li>
    {% else %}
    <li>☐ Prioritize areas for {{VISION_3_JAHRE}} expansion</li>
    {% endif %}
    <li>☐ Present rollout recommendation to leadership</li>
  </ul>
  <p><strong>Milestone:</strong> Management decision made, rollout plan toward {{VISION_3_JAHRE}}.</p>

  <h3>Expected Effects after 90 Days</h3>
  <ul>
    <li><strong>Time Savings:</strong> 30-50% on {{ZEITERSPARNIS_PRIORITAET}} in pilot</li>
    <li><strong>Quality:</strong> Standardized {{hauptleistung}} processes</li>
    <li><strong>Governance:</strong> {{KI_GUARDRAILS}} as clear organizational rules</li>
    <li><strong>Business Case:</strong> Validated ROI for {{VISION_3_JAHRE}} decision</li>
  </ul>
  {% endif %}

  <p class="small muted">
    This roadmap focuses on your specific bottleneck ({{ZEITERSPARNIS_PRIORITAET}})
    and builds toward your vision ({{VISION_3_JAHRE}}).
    Tools and Quick Wins are detailed in their respective sections.
  </p>
</section>
