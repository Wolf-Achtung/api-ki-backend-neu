<!-- PLATIN++ PROMPT v5.4 - SPRINT G6 -->
<!-- SECTION: next_actions -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{COMPANY_SIZE}} -->
<!-- INPUT NEW: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->
<!-- TOKEN-BUDGET: 800 (solo:0.8x=640, team:1.0x=800, kmu:1.15x=920) -->

<!--
=============================================================================
PHASE 3: PERSONALISATION OF ACTION RECOMMENDATIONS (MANDATORY!)
=============================================================================

The recommended actions MUST be tailored to the specific user.
Generic actions are FORBIDDEN.

PERSONALISATION CONTEXT (available from briefing):
- {{hauptleistung}} = What the user specifically offers
- {{ZEITERSPARNIS_PRIORITAET}} = Where the user loses the most time
- {{KI_GUARDRAILS}} = Restrictions/no‑gos for AI usage
- {{VISION_3_JAHRE}} = The user's long‑term vision

INDIVIDUAL ACTIONS – FORMULATE CONCRETELY:

EXAMPLE for briefing 369 (AI consultant creating questionnaires):
- hauptleistung: "Questionnaire creation and GPT‑supported evaluation"
- zeitersparnis_prioritaet: "Implementation/programming"
- ki_guardrails: "No health predictions, no financial advice"

EXPECTED ACTIONS for briefing 369:
❌ FORBIDDEN: "Set up AI access and create first template"
✅ CORRECT: "Create first questionnaire template library – document three basic structures for {{hauptleistung}}"

❌ FORBIDDEN: "Implement first Quick Win and measure time"
✅ CORRECT: "Standardise GPT evaluation prompts – measure programming effort on next analysis"

❌ FORBIDDEN: "Create simple quality checklist"
✅ CORRECT: "Create review checklist with {{KI_GUARDRAILS}} – include checkpoints like: No health predictions, no financial advice"

EXPECTED EFFECT – PERSONALISE:
❌ FORBIDDEN: "Time savings: 4–8 hours in the first month"
✅ CORRECT: "Time savings: 40–60% at {{ZEITERSPARNIS_PRIORITAET}} through template reuse"
=============================================================================
-->

<section class="section next-actions">
  <h2>Next Actions (30 Days)</h2>

  <ul class="checklist">
    {% if COMPANY_SIZE == "solo" %}
    <!-- PHASE 3 SOLO PERSONALISATION: All actions MUST address {{hauptleistung}} and {{ZEITERSPARNIS_PRIORITAET}}! -->
    <li>
      <strong>[DYNAMIC: Create first {{hauptleistung}} template library]</strong> (Week 1–2)<br/>
      Base structures for {{hauptleistung}} documented – create three reusable templates.
    </li>
    <li>
      <strong>[DYNAMIC: Test {{ZEITERSPARNIS_PRIORITAET}} with first template]</strong> (Week 2–3)<br/>
      Apply the template to {{hauptleistung}} and measure time savings at {{ZEITERSPARNIS_PRIORITAET}}.
    </li>
    <li>
      <strong>[DYNAMIC: Create review checklist with {{KI_GUARDRAILS}}]</strong> (Week 3–4)<br/>
      Document {{KI_GUARDRAILS}} as checkpoints to validate {{hauptleistung}} outputs.
    </li>
    {% elif COMPANY_SIZE == "team" %}
    <!-- PHASE 3 TEAM PERSONALISATION: All actions MUST address {{hauptleistung}} and {{ZEITERSPARNIS_PRIORITAET}}! -->
    <li>
      <strong>[DYNAMIC: Assign AI owner for {{hauptleistung}}]</strong> (Week 1–2)<br/>
      Clarify responsibility for {{hauptleistung}} standards and quality, build team templates.
    </li>
    <li>
      <strong>[DYNAMIC: Address {{ZEITERSPARNIS_PRIORITAET}} in the team]</strong> (Week 2–3)<br/>
      Test the template library for {{hauptleistung}} across the team and measure time savings at {{ZEITERSPARNIS_PRIORITAET}}.
    </li>
    <li>
      <strong>[DYNAMIC: Establish team review with {{KI_GUARDRAILS}}]</strong> (Week 3–4)<br/>
      Introduce a weekly review with {{KI_GUARDRAILS}} checkpoints and improve {{hauptleistung}} templates.
    </li>
    {% else %}
    <!-- PHASE 3 SME PERSONALISATION: All actions MUST address {{hauptleistung}} and {{ZEITERSPARNIS_PRIORITAET}}! -->
    <li>
      <strong>[DYNAMIC: Define pilot area for {{hauptleistung}}]</strong> (Week 1–2)<br/>
      Choose a department with high {{ZEITERSPARNIS_PRIORITAET}} potential, set {{KI_GUARDRAILS}} as governance.
    </li>
    <li>
      <strong>[DYNAMIC: Test {{hauptleistung}} templates in the pilot area]</strong> (Week 2–4)<br/>
      Pilot the template library for {{hauptleistung}} and quantify time savings at {{ZEITERSPARNIS_PRIORITAET}}.
    </li>
    <li>
      <strong>[DYNAMIC: Document SOPs with {{KI_GUARDRAILS}}]</strong> (Week 3–4)<br/>
      Record {{hauptleistung}} workflows with {{KI_GUARDRAILS}} review as standard operating procedures and prepare training.
    </li>
    {% endif %}
  </ul>

  <div class="roi-tracking">
    <h4>Expected Impact After 30 Days</h4>
    <!-- PHASE 3: Expected effects MUST reference {{ZEITERSPARNIS_PRIORITAET}}! -->
    <ul>
      {% if COMPANY_SIZE == "solo" %}
      <li><strong>Time Savings:</strong> 30–50% at {{ZEITERSPARNIS_PRIORITAET}} through template reuse</li>
      <li><strong>Routine:</strong> {{hauptleistung}} templates become a fixed part of daily work</li>
      <li><strong>Compliance:</strong> {{KI_GUARDRAILS}} established as a review checklist</li>
      {% elif COMPANY_SIZE == "team" %}
      <li><strong>Time Savings:</strong> 30–50% at {{ZEITERSPARNIS_PRIORITAET}} across the team</li>
      <li><strong>Clarity:</strong> {{hauptleistung}} standards and team templates defined</li>
      <li><strong>Compliance:</strong> {{KI_GUARDRAILS}} established as a team review</li>
      {% else %}
      <li><strong>Time Savings:</strong> 30–50% at {{ZEITERSPARNIS_PRIORITAET}} in the pilot area</li>
      <li><strong>Governance:</strong> {{KI_GUARDRAILS}} documented as SOPs</li>
      <li><strong>Scalability:</strong> {{hauptleistung}} templates prepared for roll‑out</li>
      {% endif %}
    </ul>
  </div>

  <p class="small muted">
    These actions build on the Quick Wins and the Roadmap. Details → see respective sections.
  </p>
</section>