Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: tools_recommendations -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 2500 (solo:0.8x=2000, team:1.0x=2500, sme:1.15x=2875) -->
<!-- RESEARCH: Tools can be referenced from {{RESEARCH_PROVENANCE_HTML}} -->
<!--
GOAL: Clearly structured tool recommendation section ("AI Stack") for {{BRANCHE_LABEL}}.

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: 3–5 tools, simple operation, low integration effort
        FORBIDDEN: "department", "project team", "area"
- team: shared workspace, collaboration, rights/roles concepts
- sme: defined stack with governance, roles, monitoring, area-specific

ANTI-REDUNDANCY:
- Tool details explained fully HERE
- In Roadmaps only reference: "Tools (see AI Stack)"

STYLE & RULES:
- Product-neutral (no brand names)
- Focus on tool categories and purpose
- No placeholders or developer language
-->

<section class="section tools">
  <h2>Recommended AI Stack for {{BRANCHE_LABEL}}</h2>

  <p>
    For the core process <strong>{{HAUPTLEISTUNG}}</strong>, a clearly structured
    AI stack is recommended that fits the size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>.
    It should noticeably relieve daily work without overwhelming the organization, and be
    expandable step by step as needed.
  </p>

  <p>
    In practice, a multi-stage approach has proven effective: First a lightweight
    foundation that solo businesses, small teams, and SMEs can all use, then
    targeted building blocks for the core process, and finally supplementary elements for governance
    and quality.
  </p>

  <h3>Alignment by Company Size</h3>
  <ul>
    <li>
      <strong>Solo Businesses:</strong>
      A lean stack with 3–5 core building blocks is sufficient – an AI assistant,
      a well-structured knowledge store, and simple automations. Important are
      low complexity and minimal maintenance effort.
    </li>
    <li>
      <strong>Small Teams (2–10 people):</strong>
      The focus is on a shared workspace, clear responsibilities, and
      simple task coordination. Tools should support collaboration, shared knowledge,
      and coordinated workflows.
    </li>
    <li>
      <strong>SMEs (11–100 people):</strong>
      Here a defined AI stack with roles, rights, and monitoring is the priority.
      Functional areas need independent but compatible solutions that are embedded in an
      overarching governance framework.
    </li>
  </ul>

  <h3>1. Foundation &amp; Basic Infrastructure</h3>
  <ul>
    <li>
      <strong>AI Assistant for Daily Tasks</strong> –
      for drafts, text revision, note structuring, workshop preparation,
      or condensing questionnaire responses in the context of {{HAUPTLEISTUNG}}.
      For solo businesses, a central assistant is sufficient; in teams and SMEs, it should be
      integrated so that multiple people can use it consistently.
    </li>
    <li>
      <strong>Knowledge and Document Store</strong> –
      a central place for questionnaires, report templates, best practice examples,
      protocols, and AI prompt collections. A clear structure is important so that content
      is quickly found and understood by all participants.
    </li>
    <li>
      <strong>Collaboration or Task Tool</strong> –
      for planning tasks, deadlines, and responsibilities in the {{HAUPTLEISTUNG}} process.
      Solo businesses use simple task lists; small teams and SMEs should additionally
      be able to transparently display responsibilities, status, and dependencies.
    </li>
  </ul>

  <h3>2. Tools for the Core Process {{HAUPTLEISTUNG}}</h3>
  <ul>
    <li>
      <strong>Form or Survey Tool</strong> –
      for structured capture of customer data and responses, e.g., via online forms
      with clear scales and open fields. For solo setups, a compact solution is sufficient;
      teams and SMEs benefit from multi-user capability and simple evaluation options.
    </li>
    <li>
      <strong>Evaluation and Reporting Tool</strong> –
      supports processing responses with AI, creating maturity analyses,
      action recommendations, and reports in a uniform layout.
      A clear template approach ensures that all reports in {{BRANCHE_LABEL}}
      appear professional and consistent.
    </li>
    <li>
      <strong>Automation Tool</strong> –
      connects survey, evaluation, and report creation. Typical workflows are:
      form submission, automatic report creation, sending via email
      or filing in the knowledge store. Solo businesses use simple automations,
      SMEs integrate them into existing workflows.
    </li>
    <li>
      <strong>Industry-Specific Specialized Tools</strong> –
      depending on {{BRANCHE_LABEL}}, additional solutions may be useful, e.g., for
      scheduling, document approvals, media production, or business metrics analysis.
      These tools should complement the AI stack, not unnecessarily complicate it.
    </li>
  </ul>

  <h3>3. Governance, Security &amp; Quality</h3>
  <ul>
    <li>
      <strong>Simple Guidelines &amp; Roles</strong> –
      brief, written rules about what data may be entered into AI tools,
      how results are reviewed and approved, and who decides in case of doubt.
      Solo businesses formulate a compact checklist; small teams and SMEs
      name responsible parties for quality, data protection, and usage.
    </li>
    <li>
      <strong>Documentation of AI Usage</strong> –
      an overview of which tools are used for what, with what data volume
      and what protective measures. This documentation facilitates adaptations to new
      regulatory requirements and creates transparency toward employees
      and external partners.
    </li>
    <li>
      <strong>Quality Control</strong> –
      brief review processes for important AI results, e.g., a second look at
      management reports, spot-check reviews, or minimum standards for structure
      and tone. The larger the company, the more important a clear definition of
      when a review is mandatory.
    </li>
  </ul>

  <h3>4. Introduction in Stages</h3>
  <p>
    Instead of introducing all tools simultaneously, the AI stack should be built up in manageable
    stages. First a stable foundation of assistant, knowledge store, and task management,
    then a form and evaluation setup for {{HAUPTLEISTUNG}}, and finally targeted automations
    and governance building blocks.
  </p>

  <table class="table tools-priorities">
    <thead>
      <tr>
        <th>Stage</th>
        <th>Building Block</th>
        <th>Role in {{HAUPTLEISTUNG}} Process</th>
        <th>Recommended Timing</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1</td>
        <td>Assistant, knowledge store, task management</td>
        <td>
          Supports daily work, secures knowledge, and creates transparency
          about tasks and priorities.
        </td>
        <td>within the first 30 days</td>
      </tr>
      <tr>
        <td>2</td>
        <td>Form tool &amp; evaluation setup</td>
        <td>
          Makes customer data in the context of {{HAUPTLEISTUNG}} usable in a structured way and
          enables AI-powered evaluations and reports.
        </td>
        <td>Day 30–60</td>
      </tr>
      <tr>
        <td>3</td>
        <td>Automation &amp; governance building blocks</td>
        <td>
          Reduces manual intermediate steps, strengthens security and quality, and makes
          the overall process scalable – especially relevant for growing teams and SMEs.
        </td>
        <td>from about 60 days</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    The recommended AI stack is deliberately kept lean: For {{UNTERNEHMENSGROESSE_LABEL}},
    the priority is to quickly generate value in the core process {{HAUPTLEISTUNG}} and
    add further building blocks step by step as needed. This keeps costs and
    complexity manageable while laying the foundation for later scaling.
  </p>
</section>
