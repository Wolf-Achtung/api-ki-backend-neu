<!-- PLATIN++ PROMPT v5.4 - SPRINT G6 -->
<!-- SECTION: next_actions -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 800 (solo:0.8x=640, team:1.0x=800, kmu:1.15x=920) -->
<!--
GOAL: 3 concrete action recommendations for the next 30 days.

MINIMUM LENGTH (STRICT!):
- Solo: ≥60 words
- Team: ≥80 words
- SME: ≥100 words

STRUCTURE (STRICT!):
- Exactly 3 bullets (NOT more, NOT fewer)
- Each bullet: Action + timeframe (Week 1-2, 2-4, etc.)
- NO meta-sentences ("In this section...", "The following actions...")
- Start directly with the first action

FORMAT PER BULLET:
<li>
  <strong>[Concrete Action]</strong> (Week [X–Y])<br/>
  [1 sentence concrete benefit or expected outcome]
</li>

ANTI-REDUNDANCY (STRICT!):
- NO repetition from Quick Wins or Roadmap
- Focus on NEXT concrete steps, not on summary
- Use cross-references: "→ see Roadmap", "→ see Quick Wins"

SPRINT G6 - PERSONA HARD-GUARDS (STRICT!):
{% if COMPANY_SIZE == "solo" %}
SOLO MODE - FORBIDDEN:
- "Team/Teams/Department/Employees" → do not use
- "PMO Team/Project Manager" → do not use
- Instead: "You", "Owner", "external support"
{% elif COMPANY_SIZE == "team" %}
TEAM MODE - FORBIDDEN:
- "Division/Unit/Corporation/Department Head" → do not use
- Instead: "Team", "Project lead", "Team member"
{% else %}
SME MODE - FORBIDDEN:
- "Corporation/Division/Unit" → do not use
- Instead: "Project Manager", "Department", "Compliance Officer"
{% endif %}

SIZE-AWARE RESPONSIBILITIES:
- Solo: "You", "Owner (You)", "External support: [Role]"
- Team: "Project lead", "Owner + [Role]", "Team (2-3 people)"
- SME: "Project Manager", "Compliance Officer", "Department Head"
-->

<section class="section next-actions">
  <h2>Next Actions (30 Days)</h2>

  <ul class="checklist">
    {% if COMPANY_SIZE == "solo" %}
    <li>
      <strong>Set up AI access and create first template</strong> (Week 1–2)<br/>
      Establish foundation for {{OFFERING_LABEL}} – test access, create first prompt template for core task.
    </li>
    <li>
      <strong>Implement first Quick Win and measure time</strong> (Week 2–3)<br/>
      Complete recurring task with AI support, document time savings (→ see Quick Wins).
    </li>
    <li>
      <strong>Create simple quality checklist</strong> (Week 3–4)<br/>
      Define 3-5 checkpoints to validate AI outputs before use.
    </li>
    {% elif COMPANY_SIZE == "team" %}
    <li>
      <strong>Designate AI owner and set up shared access</strong> (Week 1–2)<br/>
      Clarify responsibility for standards and quality, equip all team members with access.
    </li>
    <li>
      <strong>Implement first team-wide Quick Win</strong> (Week 2–3)<br/>
      Test selected task from {{OFFERING_LABEL}} with AI, share experiences within the team (→ see Quick Wins).
    </li>
    <li>
      <strong>Establish short review process</strong> (Week 3–4)<br/>
      Introduce weekly 15-minute review: What works, what doesn't? Adjust templates as needed.
    </li>
    {% else %}
    <li>
      <strong>Define pilot area and designate AI lead</strong> (Week 1–2)<br/>
      Select department with high potential, establish governance rules, set up access.
    </li>
    <li>
      <strong>Start Quick Wins in pilot area and document</strong> (Week 2–4)<br/>
      Test 2-3 prioritized use cases from {{OFFERING_LABEL}}, quantify initial time savings (→ see Quick Wins).
    </li>
    <li>
      <strong>Establish weekly reviews and collect learnings</strong> (Week 3–4)<br/>
      Introduce feedback loops in pilot area, create foundation for SOPs and training concept.
    </li>
    {% endif %}
  </ul>

  <div class="roi-tracking">
    <h4>Expected Impact After 30 Days</h4>
    <ul>
      {% if COMPANY_SIZE == "solo" %}
      <li><strong>Time Savings:</strong> 4–8 hours in the first month</li>
      <li><strong>Routine:</strong> AI is a fixed part of daily work</li>
      {% elif COMPANY_SIZE == "team" %}
      <li><strong>Time Savings:</strong> 10–20 hours total across team</li>
      <li><strong>Clarity:</strong> Roles, responsibilities and first standards defined</li>
      {% else %}
      <li><strong>Time Savings:</strong> 15–30 hours in pilot area</li>
      <li><strong>Governance:</strong> Clear rules, initial documentation, measurable baseline</li>
      {% endif %}
    </ul>
  </div>

  <p class="small muted">
    These actions build on the Quick Wins and Roadmap. Details → see respective sections.
  </p>
</section>
