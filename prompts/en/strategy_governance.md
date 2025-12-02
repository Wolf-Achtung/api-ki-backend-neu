Developer:
<!-- strategy_governance.md – v4.2 GOLD STANDARD+ (size-aware, strategic, validator-safe)
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body>. NO Markdown fences.

     GOAL:
     - Provide a clear, strategic assessment of AI strategy & governance.
     - Connection of: current maturity level, existing guidelines, data protection status,
       responsibilities, risks, organizational structure.
     - Applications of the AI Act, change management, and responsibilities must be realistically
       described for solo, small teams, or SMEs.
     - Result = 12–18 sentences + 1–2 structured lists.

     AVAILABLE LABEL VARIABLES:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{COMPANY_SIZE}}  // "solo", "team", "kmu"
       {{GOVERNANCE_RICHTLINIEN_LABEL}}
       {{CHANGE_MANAGEMENT_LABEL}}
       {{MELDEWEGE_LABEL}}
       {{DATENSCHUTZ_LABEL}}
       {{LOESCHREGELN_LABEL}}
       {{DATENSCHUTZBEAUFTRAGTER_LABEL}}
       {{FOLGENABSCHAETZUNG_LABEL}}
       {{INTERNE_KI_KOMPETENZEN_LABEL}}

     OFFICIAL SIZE LOGIC (uniform with all prompts):
       SOLO (COMPANY_SIZE="solo"):
         - No departments/teams. One owner role, personal routines, simple standards.
         - Governance = pragmatic, small structure.

       TEAM (2–10, COMPANY_SIZE="team"):
         - "Team", "colleagues", clear roles.
         - Governance = lightweight structure: team lead + AI owner + users.

       SME (11–100, COMPANY_SIZE="kmu"):
         - "Teams", "functional areas", "responsible parties".
         - No corporate jargon ("Business Unit", "Division").
         - Governance = coordinated structure across multiple areas.

     PROHIBITED IN HTML OUTPUT:
       - "Placeholder", "free text field", TODO, technical system hints.
       - No reference to variable names or prompt instructions.
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
