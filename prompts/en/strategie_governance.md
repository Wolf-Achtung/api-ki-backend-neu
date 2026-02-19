**IMPORTANT – Length limit: Your response must not exceed 1200 words. Cut rather than exceed.**

Developer:
<!-- PLATIN++ PROMPT v5.3 - SPRINT G17.S -->
<!-- SECTION: strategie_governance -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{COMPANY_SIZE}}, {{BRANCH_SHORT_LABEL}}, {{GOVERNANCE_RICHTLINIEN_LABEL}}, {{CHANGE_MANAGEMENT_LABEL}}, {{MELDEWEGE_LABEL}}, {{DATENSCHUTZ_LABEL}}, {{LOESCHREGELN_LABEL}}, {{DATENSCHUTZBEAUFTRAGTER_LABEL}}, {{FOLGENABSCHAETZUNG_LABEL}}, {{INTERNE_KI_KOMPETENZEN_LABEL}} -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, kmu:1.15x=2530) -->
<!-- WORD_MINIMUM_SOLO: 150 (G17.S: increased from 130 for Mini-Governance-Booster) -->
<!--
GOAL: Strategic assessment of AI strategy & governance.
Result = 10–14 sentences + 1 structured list.
SPRINT G17.S: Solo receives additional "Mini-Governance for Solo" subsection

PERSONA VARIATIONS (COMPANY_SIZE) – STRICTLY OBSERVE:

SOLO:
  Recommended: "Checklist", "Minimal rules", "One-person standard",
               "Documentation light", "personal routine", "own review points"
  Do not use: "Organizational development", "Responsibility matrix",
              "Governance framework", "Role model", "Committee", "Board",
              "Steering circle", "Department", "Build team", "Employees"

TEAM:
  Recommended: "Team agreement", "shared rules", "AI coordinator",
               "short review round", "shared responsibility"
  Do not use: "Governance board", "Matrix organization", "Division"

SME:
  Recommended: "Functional area leads", "coordinated processes",
               "cross-functional standards", "Governance rules"
  Do not use: Corporate jargon ("Business Unit", "Division", "C-Level")

SPRINT G17.S – MINI-GOVERNANCE FOR SOLO (MANDATORY for solo!):
Additional subsection for Solo (~60-80 words):
1. 2-3 easily implementable AI rules:
   - Version control: Save prompts/outputs with date
   - Transparency: Label AI-generated content before sending
   - Approval before delivery: Own review before customer handover
2. Short documentation routine (weekly/monthly)
3. Note on scalability for future team contexts

IMPORTANT:
- No team vocabulary for Solo
- No overlaps with AI_POLICY_MINI

ANTI-REDUNDANCY:
- Governance FULLY covered HERE
- DO NOT repeat in org_change
- DO NOT duplicate in risks

GUARDRAILS: Consider guardrails from strategic context.
-->

<section class="section governance-strategy">
  <h2>AI Strategy &amp; Governance</h2>

  <p>
    For <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>,
    pragmatic governance is decisive.
  </p>
  <p>
    The current assessment shows where guidelines are effective and where further development
    is needed.
  </p>

  <h3>Framework Conditions &amp; Current Status</h3>
  <ul>
    <li>
      <strong>Guidelines &amp; Policy:</strong>
      Existing rules are currently described as {{GOVERNANCE_RICHTLINIEN_LABEL}}.
      They form an initial framework but need to be further specified,
      simplified or expanded depending on size.
    </li>
    <li>
      <strong>Change Management &amp; Communication:</strong>
      The handling of changes is assessed as {{CHANGE_MANAGEMENT_LABEL}}.
      The importance and benefits of AI should be communicated consistently to increase
      acceptance.
    </li>
    <li>
      <strong>Reporting Channels &amp; Incidents:</strong>
      Current structures are described as {{MELDEWEGE_LABEL}}.
      Clear contact persons and simple processes increase security and transparency.
    </li>
    <li>
      <strong>Data Protection &amp; Deletion Rules:</strong>
      Information on data protection ({{DATENSCHUTZ_LABEL}}) and deletion rules
      ({{LOESCHREGELN_LABEL}}) shows that basic structures exist,
      but should be more formally documented.
    </li>
    <li>
      <strong>Responsibilities &amp; Competencies:</strong>
      The appointment of a data protection officer ({{DATENSCHUTZBEAUFTRAGTER_LABEL}}),
      existing AI competency ({{INTERNE_KI_KOMPETENZEN_LABEL}}) and the status of
      impact assessments ({{FOLGENABSCHAETZUNG_LABEL}}) provide insights into roles,
      responsibilities and know-how.
    </li>
  </ul>

  <h3>Strategic Guidelines for the Next 12–24 Months</h3>
  <ol>
    <li>
      <strong>Establish clear usage rules:</strong>
      Define binding rules for inputs, data types and quality standards
      – for solo as compact personal routines, for teams as shared guidelines,
      for SMEs as coordinated rulebooks with responsibilities.
    </li>
    <li>
      <strong>Define responsibilities:</strong>
      Solo: one owner role for usage &amp; quality.<br>
      Team: team lead + AI owner + users.<br>
      SME: process owners in functional areas + data protection/IT.
    </li>
    <li>
      <strong>Increase transparency &amp; risk mitigation:</strong>
      Brief documentation, simple reporting channels and uniform approval points ensure
      that results can be used traceably and securely.
    </li>
    <li>
      <strong>Build competencies systematically:</strong>
      Mini-trainings, guidelines and short reviews create confidence in handling AI.
      For SMEs add role-specific training.
    </li>
    <li>
      <strong>Evaluate monetisation potential (optional):</strong>
      AI-powered processes can unlock new revenue streams – through
      digital products, scalable service formats or automated analyses.
      A strategic evaluation is worthwhile especially with stable core workflows.
    </li>
  </ol>

  <h3>Responsibility &amp; Steering</h3>
  <p>
    Steering should match your organisational structure:
  </p>
  <ul>
    <li><strong>Solo:</strong> Owner role + fixed routines</li>
    <li><strong>Team:</strong> Compact circle of team lead + users</li>
    <li><strong>SME:</strong> Coordinated responsibilities between functional areas and IT</li>
  </ul>
  <p>
    Transparency and short decision paths are central for all sizes.
  </p>

  <h3>AI Culture &amp; Adoption</h3>
  <p>
    {% if COMPANY_SIZE == "solo" %}
    View AI as a tool for relief, not a replacement for your expertise. Regular self‑reflection on the quality and limitations of AI outputs strengthens your judgement and prevents over‑reliance on automated results.
    {% elif COMPANY_SIZE == "team" %}
    Encourage open exchange about successful and failed AI applications. Brief experience reports in existing meetings create shared learning and reduce reservations without generating additional overhead.
    {% else %}
    Establish a positive error culture around AI usage: Open sharing of learnings accelerates organisation‑wide learning. Champions in functional areas can act as multipliers and sustainably increase adoption.
    {% endif %}
  </p>

  {% if COMPANY_SIZE == "solo" %}
  <!-- G17.S: Mini-Governance for Solo (Booster section) -->
  <h3>Mini-Governance for Solo</h3>
  <p>
    Even without formal governance structures, you benefit from simple rules
    that ensure quality and can scale to future team contexts:
  </p>
  <ul>
    <li>
      <strong>Version control:</strong>
      Save key prompts and outputs with date and context – this keeps track of
      which results were produced under which conditions.
    </li>
    <li>
      <strong>Transparency externally:</strong>
      Label AI-generated content before sending to clients or partners,
      at least internally for yourself, to keep oversight.
    </li>
    <li>
      <strong>Approval before delivery:</strong>
      Perform a brief self-check on important outputs – a personal review
      routine before customer handover safeguards quality.
    </li>
  </ul>
  <p>
    A short weekly or monthly documentation routine (e.g. an "AI logbook")
    helps you identify patterns and gradually improve your usage.
    These fundamentals can easily be transferred to a small team as you grow.
  </p>
  {% endif %}

  <p class="small muted">
    A realistic, well-communicated governance ensures sustainable impact,
    supports the roadmap implementation and builds trust with employees and
    customers alike.
  </p>
</section>