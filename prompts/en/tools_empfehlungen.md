**IMPORTANT – Length limit: Your response must not exceed 1200 words. Cut rather than exceed.**

<!-- PLATIN++ PROMPT v5.4 - AI Stack Recommendations -->
<!-- SECTION: tools_recommendations -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- TOKEN-BUDGET: 2800 (solo:0.8x=2240, team:1.0x=2800, sme:1.15x=3220) -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{BRANCH_SHORT_LABEL}}, {{OFFERING_LABEL}}, {{COMPANY_SIZE}}, {{hauptleistung}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->

<!--
=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- [✓] Clear, structured AI tool recommendation section ("AI stack")
      for the industry context {{BRANCH_CONTEXT_LABEL}}
      and main service {{OFFERING_LABEL}} / "{{hauptleistung}}"
- [✓] Short labels: {{BRANCH_CORE_LABEL}} (8-12 words), {{BRANCH_CONTEXT_LABEL}} (4-6 words), {{BRANCH_SHORT_LABEL}} (3-5 words), {{OFFERING_LABEL}} (6-10 words)
      → no translation of variable names
- [✓] Minimum word counts: ≥150 words (Solo), ≥200 words (Team), ≥250 words (SME)
      Short paragraphs: 2-3 sentences per paragraph (no text blocks)
- [✓] AI stack structured by company size:
      * Solo: 4 clusters with 2-3 examples each – (1) AI assistant & basic stack,
        (2) Core tools for {{OFFERING_LABEL}}, (3) Quality & documentation, (4) Responsible AI & Governance
      * Team: 5 clusters – (1) Collaboration & shared workspace, (2) Core tools for {{OFFERING_LABEL}},
        (3) Reporting & Analytics, (4) Governance & Quality, (5) Responsible AI & Governance.
        In regulated industries (finance, healthcare, legal): add subsections Data Platforms,
        Risk & Compliance, Reporting & Collaboration
      * SME: 6 clusters – (1) Enterprise Foundation (platform, knowledge store),
        (2) Department-specific tools for {{OFFERING_LABEL}}, (3) Reporting/BI integration,
        (4) Compliance & Governance, (5) Rollout & training, (6) Responsible AI & Governance
- [✓] Mandatory "Responsible AI & Governance" sub-section (for all sizes):
      - Focus: Audit trail, versioning, review mechanisms
      - Length: Solo 30-50 words, Team 40-60 words, SME 50-70 words
      - Describe tool CLASSES, not brands
- [✓] Narrative connections: Reference to 90-day roadmap phases, 12-month roadmap,
      starter kit and suitable funding programs
- [✓] Neutral, product-agnostic tone: Tool categories only, no brand names
      Describe purpose and integration logic of each cluster
      Avoid generic meta-sentences, placeholder text, and developer language
- [✓] Persona vocabulary rules:
      Solo: No "department", "project team", "employees"
      Team: No corporate language ("division", "unit")
      SME: No solo or enterprise vocabulary
      Instead use: "capacity", "resources", "team"
=============================================================================
-->

<section class="section tools">
  <h2>Recommended AI Stack for {{BRANCH_CONTEXT_LABEL}}</h2>

  <p>
    {% if hauptleistung %}
    For "{{hauptleistung}}" a clearly structured AI stack is recommended
    that directly supports this main service, creates time savings,
    and can be systematically expanded.
    {% else %}
    For {{OFFERING_LABEL}} a clearly structured AI stack is recommended
    that creates tangible relief and can be scaled step by step.
    {% endif %}
  </p>

  <h3>Assessment by Company Size</h3>
  <ul>
    <li>
      <strong>Solo operators:</strong>
      A lean stack with 3-5 components is sufficient – AI assistant, structured knowledge storage,
      and simple automations. Complexity and maintenance effort remain minimal.
    </li>
    <li>
      <strong>Small teams (2-10):</strong>
      Focus on shared workspace, clear responsibilities, and simple task coordination.
      Tools should support collaboration, shared knowledge, and coordinated workflows.
    </li>
    <li>
      <strong>SMEs (11-100):</strong>
      A defined AI stack with roles, permissions, and monitoring is central. Areas need
      autonomous yet compatible solutions within a governance framework.
    </li>
  </ul>

  {% if COMPANY_SIZE == "solo" %}
  <h3>1. AI Assistant & Basics</h3>
  <p>
    Start with a versatile AI assistant for drafting, editing, and summarizing texts
    as well as organizing notes. Add a lightweight knowledge storage for templates and prompts,
    plus simple automation tools to minimize repetitive tasks.
  </p>

  <h3>2. Core Tools for {{OFFERING_LABEL}}</h3>
  <p>
    Use a form or questionnaire tool to capture client data in a structured way
    appropriate to {{OFFERING_LABEL}}. Combine this with an analysis tool
    that uses AI to generate evaluations and reports. Add basic automation
    to link form input, analysis, and result delivery.
  </p>

  <h3>3. Quality & Documentation</h3>
  <p>
    Establish a simple routine to document AI usage: Which tools are used for what purposes?
    What types of data are processed, and with what protection? Define a brief review process
    (e.g., a second look at reports) to ensure consistency and correctness.
  </p>

  <h3>4. Responsible AI & Governance</h3>
  <p>
    Introduce mechanisms for audit trails, version control, and review.
    Log AI queries and responses, track prompt versions, and use simple checklists
    to approve results before delivery. These foundations ensure transparency
    and facilitate later scaling.
  </p>
  {% elif COMPANY_SIZE == "team" %}
  <h3>1. Collaboration & Shared Workspace</h3>
  <p>
    Use a unified workspace where your team can centrally store templates, prompts,
    and best practices in a knowledge base. Integrate task management
    for responsibilities and deadlines to support shared workflows and visibility.
  </p>

  <h3>2. Core Tools for {{OFFERING_LABEL}}</h3>
  <p>
    Implement multi-user form tools to capture structured data
    and an analysis engine that transforms inputs into consistent AI-supported evaluations.
    Add an automation layer that connects submissions, evaluations, and report creation.
  </p>

  <h3>3. Reporting & Analytics</h3>
  <p>
    Deploy a business intelligence solution to visualize results
    and track key metrics of your AI initiatives. This enables results review,
    sharing insights, and collaborative process adjustments.
  </p>

  <h3>4. Governance & Quality</h3>
  <p>
    Establish brief written rules on which data may go into AI tools,
    how outputs should be reviewed, and who has final responsibility.
    Provide a short documentation of AI usage and appoint a coordinator
    for quality and compliance.
  </p>

  <h3>5. Responsible AI & Governance Tools</h3>
  <p>
    Require audit trails for AI interactions, versioning systems for prompts and models,
    and defined review workflows. For regulated industries (finance, healthcare, legal):
    Add subsections for data platforms, risk & compliance tools, and
    secure reporting and collaboration mechanisms to meet industry standards.
  </p>
  {% else %}
  <h3>1. Enterprise Foundation</h3>
  <p>
    Build your stack on an AI platform and central knowledge repository
    with multi-user access, version control, and scalable infrastructure.
    The foundation should integrate with existing enterprise systems and
    enable knowledge sharing across departments.
  </p>

  <h3>2. Department-Specific Tools for {{OFFERING_LABEL}}</h3>
  <p>
    Equip each area with tailored tools for {{OFFERING_LABEL}}:
    Form tools for structured data capture, analysis engines for automated evaluations,
    and specialized applications aligned with departmental needs.
    All tools should adhere to common standards and integrate into the central platform.
  </p>

  <h3>3. Reporting & BI Integration</h3>
  <p>
    Adopt reporting and business intelligence solutions
    that consolidate organization-wide data.
    These tools should provide dashboards and KPIs
    to monitor progress and support strategic decisions.
  </p>

  <h3>4. Compliance & Governance</h3>
  <p>
    Implement enterprise-grade compliance and governance modules:
    Policy management, data protection controls, risk monitoring, and audit capabilities.
    Align these with industry regulations and internal guardrails.
  </p>

  <h3>5. Rollout & Training</h3>
  <p>
    Plan a phased rollout of your AI stack: First core components,
    then process-specific tools, and finally automation and governance modules.
    Include role-specific training to ensure adoption across all organizational levels.
  </p>

  <h3>6. Responsible AI & Governance Tools</h3>
  <p>
    Adopt tools that enable audit trails, version management, and review workflows.
    Ensure that AI interactions are logged, prompt and model changes are tracked,
    and approvals are obtained before critical outputs are released.
    These measures build trust and accountability across your organization.
  </p>
  {% endif %}

  <p class="small muted">
    These AI tool categories align with your 90-day roadmap phases
    and 12-month roadmap and complement the curated selection in your starter kit.
    Funding programs may support investments in compliance and training tools –
    refer to the funding overview for details.
    Introduce each component step by step for maximum impact and control.
  </p>
</section>

<!-- SPRINT G18 - ANTI-REDUNDANCY (STRICT!):
- Do NOT describe tools already mentioned in Quick Wins (→ cross-reference)
- Maximum ONE brief mention "→ see Quick Wins for immediate tool recommendations"
- Tool stack structure ONLY HERE – do not repeat in other sections
- Focus: Strategic AI stack planning – NO ad-hoc tool tips
-->

<!-- SPRINT G18 - NARRATIVE CONNECTIONS:
- Reference roadmap phases: "The basic stack tools are part of Phase 1 (Safe Start)..."
- Reference starter kit: "The starter kit contains curated selections from these categories..."
- Announce funding potential: "Investments in governance tools can be co-funded → see funding potential"
-->

<!-- SPRINT N - SOLO PERSONA RULES (STRICT!):
{% if COMPANY_SIZE == "solo" %}
DO NOT USE for solo:
- "build team" → instead: "expand capacity"
- "employees" → instead: "resources" or "external support"
- "teams" → instead: "capacities"
- "department" → instead: "work area"
- "division" → instead: "work area"
Use formulations without team/department concepts!
{% endif %}
-->

<!-- ZERO-LEAK POLICY (N4.6) -->
<!--
FORBIDDEN – NEVER USE:
- No questions to the reader ("Do you have questions?", "Would you like to learn more?")
- No prompts ("If you would like...", "Contact us...")
- No assistant language ("I can help you...", "I'm happy to explain...")
- No offers ("If needed...", "If desired...")
- No interactive elements ("Click here...", "Select...")
- No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
- No meta-comments ("This section...", "In the following...")

The output is a FINAL REPORT SECTION, not a conversation.
-->
