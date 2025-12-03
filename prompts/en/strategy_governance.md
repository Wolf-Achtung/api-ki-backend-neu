Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: strategy_governance -->
<!-- VERSION: v6.0 PLATIN++ V5 -->
<!-- OUTPUT: HTML -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{COMPANY_SIZE}}, {{GOVERNANCE_RICHTLINIEN_LABEL}}, {{CHANGE_MANAGEMENT_LABEL}}, {{MELDEWEGE_LABEL}}, {{DATENSCHUTZ_LABEL}}, {{LOESCHREGELN_LABEL}}, {{DATENSCHUTZBEAUFTRAGTER_LABEL}}, {{FOLGENABSCHAETZUNG_LABEL}}, {{INTERNE_KI_KOMPETENZEN_LABEL}} -->
<!-- TOKEN-BUDGET: 2000 (solo:0.8x=1600, team:1.0x=2000, sme:1.15x=2300) -->
<!--
GOAL: Strategic assessment of AI strategy & governance.
Result = 10–14 sentences + 1 structured list.

PERSONA VARIATIONS (COMPANY_SIZE) – STRICTLY FOLLOW:

SOLO:
  ✅ ALLOWED: "checklist", "minimal rules", "one-person standard",
              "documentation light", "personal routine", "own checkpoints"
  ❌ FORBIDDEN: "organizational development", "responsibility matrix",
              "governance framework", "role model", "committee", "board",
              "steering committee", "department", "build team", "employees"

TEAM:
  ✅ ALLOWED: "team agreement", "shared rules", "AI coordinator",
              "short review round", "shared responsibility"
  ❌ FORBIDDEN: "governance board", "matrix organization", "division"

SME:
  ✅ ALLOWED: "department leads", "coordinated processes",
              "cross-functional standards", "governance rules"
  ❌ FORBIDDEN: Corporate jargon ("business unit", "division", "C-level")

ANTI-REDUNDANCY:
- Governance fully covered HERE
- NOT repeated in org_change
- NOT duplicated in risks

GUARDRAILS: Respect guardrails from strategic context.
-->

<section class="section governance-strategy">
  <h2>AI Strategy &amp; Governance</h2>

  <p>
    For a company of size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in the
    <strong>{{BRANCHE_LABEL}}</strong> industry, clear, pragmatic governance for AI deployment
    is essential to ensure quality, security, and accountability. The current assessment
    shows how far guidelines, reporting channels, data protection rules, and existing competencies
    are already effective and where structural developments are necessary.
  </p>

  <h3>Framework Conditions &amp; Current Status</h3>
  <ul>
    <li>
      <strong>Guidelines &amp; Policy:</strong>
      Existing rules are currently described as {{GOVERNANCE_RICHTLINIEN_LABEL}}.
      They form an initial framework but need to be – depending on size – further specified,
      simplified, or expanded.
    </li>
    <li>
      <strong>Change Management &amp; Communication:</strong>
      The handling of changes is assessed as {{CHANGE_MANAGEMENT_LABEL}}.
      The significance and benefits of AI should be communicated consistently to increase acceptance.
    </li>
    <li>
      <strong>Reporting Channels &amp; Incidents:</strong>
      Current structures are described as {{MELDEWEGE_LABEL}}.
      Clear contact persons and simple processes increase security and transparency.
    </li>
    <li>
      <strong>Data Protection &amp; Deletion Rules:</strong>
      The information on data protection ({{DATENSCHUTZ_LABEL}}) and deletion rules
      ({{LOESCHREGELN_LABEL}}) shows that basic structures exist,
      but should be more formally documented.
    </li>
    <li>
      <strong>Responsibilities &amp; Competencies:</strong>
      The designation of a data protection officer ({{DATENSCHUTZBEAUFTRAGTER_LABEL}}),
      existing AI competency ({{INTERNE_KI_KOMPETENZEN_LABEL}}), and the status of
      impact assessments ({{FOLGENABSCHAETZUNG_LABEL}}) provide insights into roles,
      responsibilities, and existing know-how.
    </li>
  </ul>

  <h3>Strategic Guidelines for the Next 12–24 Months</h3>
  <ol>
    <li>
      <strong>Establish clear usage rules:</strong>
      Define binding rules for inputs, data types, and quality standards
      – for solo as compact personal routines, for teams as shared guidelines,
      in SMEs as coordinated rulebook with responsibilities.
    </li>
    <li>
      <strong>Define responsibilities:</strong>
      Solo: one owner role for usage & quality.<br>
      Team: team lead + AI owner + users.<br>
      SME: process owners in functional areas + data protection/IT.
    </li>
    <li>
      <strong>Increase transparency &amp; risk mitigation:</strong>
      Brief documentation, simple reporting channels, and uniform approval points ensure
      that results can be used traceably and securely.
    </li>
    <li>
      <strong>Build competencies systematically:</strong>
      Mini-trainings, guidelines, and brief reviews create confidence in handling AI.
      In SMEs additionally role-specific training.
    </li>
    <li>
      <strong>Evaluate monetization potential (optional):</strong>
      AI-powered processes can unlock new revenue streams – through digital products,
      scalable service formats, or automated analyses. Strategic evaluation is
      particularly worthwhile with stable core workflows.
    </li>
  </ol>

  <h3>Responsibility &amp; Steering</h3>
  <p>
    Steering of AI deployment should fit the organizational structure:
    Solo businesses work with a clearly defined owner role and
    fixed routines; small teams use a compact steering circle of
    team lead and users; SMEs rely on coordinated responsibilities
    between functional areas, management, and data protection/IT.
    Transparency, short decision paths, and regular reviews are central for all
    sizes to ensure quality and security.
  </p>

  <p class="small muted">
    Realistic, well-communicated governance ensures sustainable impact,
    supports roadmap implementation, and builds trust with employees and
    customers alike.
  </p>
</section>
