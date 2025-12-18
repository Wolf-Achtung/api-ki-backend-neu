<!-- PLATIN++ PROMPT v5.4 - SPRINT G6 -->
<!-- SECTION: tools_recommendations -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 2500 (solo:0.8x=2000, team:1.0x=2500, sme:1.15x=2875) -->
<!-- WORD_MINIMUM_SOLO: 130 -->
<!-- WORD_MINIMUM_TEAM: 190 -->
<!-- WORD_MINIMUM_SME: 220 -->
<!--
GOAL: Clearly structured tool recommendation section ("AI Stack") for {{BRANCH_CONTEXT_LABEL}}.

SHORT LABELS (MANDATORY!):
- {{BRANCH_CORE_LABEL}} = Industry in 8-12 words
- {{BRANCH_CONTEXT_LABEL}} = Industry in 4-6 words
- {{OFFERING_LABEL}} = Core offering in 6-10 words

MINIMUM LENGTH (STRICT!):
- Solo: ≥130 words
- Team: ≥190 words (especially for regulated industries!)
- SME: ≥220 words

STRUCTURE BY SIZE:
{% if COMPANY_SIZE == "solo" %}
SOLO: 3–5 tool clusters with 2-3 examples each:
1. AI Assistant & Basics (2-3 examples)
2. Core Process Tools for {{OFFERING_LABEL}} (2-3 examples)
3. Quality & Documentation (1-2 examples)

{% elif COMPANY_SIZE == "team" %}
TEAM: 4 tool clusters with 2-3 examples each (min. 190 words!):
1. Collaboration & Shared Workspace (2-3 examples)
2. Core Process Tools for {{OFFERING_LABEL}} (2-3 examples)
3. Reporting & Analytics (2-3 examples)
4. Governance & Quality (2 examples)

For regulated industries (Finance, Healthcare, Legal) additionally:
- Compliance/RegTech tools
- Audit trail features
- Access control & logging

{% else %}
SME: 5 tool clusters with 2-3 examples each (min. 220 words!):
1. Enterprise Foundation (AI platform, knowledge base)
2. Department-specific tools for {{OFFERING_LABEL}}
3. Reporting/BI integration
4. Compliance & Governance
5. Rollout & Training
{% endif %}

ANTI-REDUNDANCY:
- Explain tool details fully HERE
- In Roadmaps only reference: "Tools (→ see AI Stack)"
- No generic meta-sentences ("This section explains...")

STYLE & RULES:
- Product-neutral (no brand names)
- Focus on tool categories and purpose
- Name specific use cases per tool type
- No placeholders or developer language

SPRINT G6 - PERSONA HARD-GUARDS (STRICT!):
{% if COMPANY_SIZE == "solo" %}
SOLO MODE - FORBIDDEN:
- "Department" → "work area"
- "Project team" → "project capacity"
- "Teams" → "resources"
{% elif COMPANY_SIZE == "team" %}
TEAM MODE - FORBIDDEN:
- "Division/Unit/Corporation" → do not use
- Solo terms: "individual", "alone"
{% else %}
SME MODE - FORBIDDEN:
- "Corporation/Division/Unit" → do not use
- Solo terms: "individual", "alone"
{% endif %}
-->

<section class="section tools">
  <h2>Recommended AI Stack for {{BRANCH_CONTEXT_LABEL}}</h2>

  <p>
    For {{OFFERING_LABEL}}, a clearly structured AI stack is recommended
    that noticeably relieves daily work and can be expanded step by step as needed.
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
      for drafts, text revision, note structuring, and condensing inputs.
      For solo setups, a central assistant is sufficient; in teams and SMEs,
      it should be integrated so multiple people can use it consistently.
    </li>
    <li>
      <strong>Knowledge and Document Store</strong> –
      a central place for templates, best practice examples, and prompt collections.
      Clear structure enables quick finding and shared understanding.
    </li>
    <li>
      <strong>Collaboration or Task Tool</strong> –
      for planning tasks, deadlines, and responsibilities.
      Solo: simple task lists; Teams/SMEs: responsibilities and dependencies.
    </li>
  </ul>

  <h3>2. Tools for the Core Process {{OFFERING_LABEL}}</h3>
  <ul>
    <li>
      <strong>Form or Survey Tool</strong> –
      for structured capture of customer data and responses, e.g., via online forms
      with clear scales and open fields. For solo setups, a compact solution is sufficient;
      teams and SMEs benefit from multi-user capability and simple evaluation options.
    </li>
    <li>
      <strong>Evaluation and Reporting Tool</strong> –
      supports processing with AI assistance and creating analyses and reports.
      Template approach for professional, consistent results.
    </li>
    <li>
      <strong>Automation Tool</strong> –
      connects input, evaluation, and result creation. Typical workflows:
      Form → Analysis → Report → Delivery. Solo: simple automations;
      SMEs: integration into existing workflows.
    </li>
    <li>
      <strong>Industry-Specific Tools</strong> –
      depending on {{BRANCH_CONTEXT_LABEL}}, additional solutions may be useful,
      e.g., for scheduling, document approvals, or specialized analyses.
      These should complement the stack, not complicate it.
    </li>
  </ul>

  <h3>3. Governance, Security &amp; Quality</h3>
  <ul>
    <li>
      <strong>Simple Guidelines &amp; Roles</strong> –
      brief, written rules about what data may be entered into AI tools,
      how results are reviewed and approved, and who decides in case of doubt.
      Solo businesses formulate a compact checklist; teams and SMEs
      name responsible parties for quality, data protection, and usage.
    </li>
    <li>
      <strong>Documentation of AI Usage</strong> –
      an overview of which tools are used for what, with what data volume
      and what protective measures. This documentation facilitates adaptations to new
      regulatory requirements and creates transparency.
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
    then a form and evaluation setup, and finally targeted automations and governance building blocks.
  </p>

  <table class="table tools-priorities">
    <thead>
      <tr>
        <th>Stage</th>
        <th>Building Block</th>
        <th>Role in Process</th>
        <th>Recommended Timing</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1</td>
        <td>Assistant, knowledge store, task management</td>
        <td>
          Supports daily work, secures knowledge, and creates transparency.
        </td>
        <td>within the first 30 days</td>
      </tr>
      <tr>
        <td>2</td>
        <td>Form tool &amp; evaluation setup</td>
        <td>
          Makes data for {{OFFERING_LABEL}} usable in a structured way and
          enables AI-powered evaluations.
        </td>
        <td>Day 30–60</td>
      </tr>
      <tr>
        <td>3</td>
        <td>Automation &amp; governance building blocks</td>
        <td>
          Reduces manual steps, strengthens security and quality, and makes
          the overall process scalable – especially relevant for growing teams and SMEs.
        </td>
        <td>from about 60 days</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    The recommended AI stack is deliberately kept lean: quickly generate value for
    {{OFFERING_LABEL}} and add further building blocks step by step as needed.
    Details on implementation → see Roadmap.
  </p>
</section>
