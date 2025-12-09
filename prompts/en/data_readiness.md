Developer: <!-- data_readiness.md – v3.1 GOLD STANDARD+ (Data & System Readiness, multi-size) – SPRINT G17.P
  Respond exclusively with valid HTML.
  NO <html>, <head> or <body>. NO Markdown fences.

  GOAL:
  - Provide a clear, practical assessment of data situation and system readiness for AI:
    * Where do data, tools, and processes stand today?
    * What is already sufficient for AI pilots?
    * What gaps should be closed in the next 6-12 months?

  AVAILABLE VARIABLES (Labels/Free text from questionnaire):
  - {{BRANCHE_LABEL}}
  - {{UNTERNEHMENSGROESSE_LABEL}}
  - {{HAUPTLEISTUNG}}
  - {{IT_INFRASTRUKTUR_LABEL}}          → e.g., "Cloud-based", "local", "hybrid"
  - {{PROZESSE_PAPIERLOS_LABEL}}        → Digitalization level of processes
  - {{AUTOMATISIERUNGSGRAD_LABEL}}      → Automation level assessment
  - {{DATENQUELLEN_LABELS}}             → List of typical data sources (CRM, ERP, tickets, etc.)
  - {{VORHANDENE_TOOLS_LABELS}}         → List of existing tools/platforms (e.g., M365, CRM, DMS)
  - {{REGULIERTE_BRANCHE_LABELS}}       → Hints on regulation (e.g., health data)
  - {{DATENQUELLEN_LABELS}} can be empty or very short. Then work with typical sources for branch/size.

  SIZE LOGIC:
  - "1 (Solo":
      * Data often scattered in few tools (email, Office, simple SaaS tools).
      * Focus: Create order, simple standards, minimal overhead.
  - "2-10":
      * Small tool landscape, but initial role/access logic.
      * Focus: Unified storage, clean permissions, simple data pipelines.
  - "11-100":
      * Multiple systems/departments, possibly shadow IT.
      * Focus: Binding data governance, interfaces, roles and responsibilities.

  RULES:
  - No references to questionnaire/questions, no technical placeholder texts.
  - Always write as if the assessment goes directly to management/project leadership.
  - Clear, sober tone: Opportunities + risks, no exaggerations.

  SPRINT G18 - ANTI-REDUNDANCY (STRICT!):
  - DO NOT mention ROI/Investments/Business Case again – these topics belong in business_case.md
  - Maximum ONE brief reference to Business Case is allowed (e.g., "→ see Business Case")
  - CAPEX/OPEX blocks do NOT belong here
  - Focus: Data quality, system readiness, data sources – NO financial perspective
-->

<section class="section data-readiness">
  <h2>Data Situation & System Readiness for AI</h2>

  <!-- G17.P: New intro without redundancy, with cross-references -->
  <p>
    Your data readiness assessment directly aligns with the process analysis and early Quick Wins
    (→ see 90-Day Roadmap, → Quick Wins). This section summarizes which existing data sources,
    structures, and integrations in <strong>{{BRANCH_CONTEXT_LABEL}}</strong> can be used
    immediately for AI workflows — and where targeted improvements are required.
  </p>

  <h3>Where Data and Systems Stand Today</h3>
  <p>
    Currently, information is primarily processed in the following systems:
    <strong>{{DATENQUELLEN_LABELS}}</strong> as well as in the deployed tools
    <strong>{{VORHANDENE_TOOLS_LABELS}}</strong>.
    The IT infrastructure is <strong>{{IT_INFRASTRUKTUR_LABEL}}</strong>, the
    digitalization level of processes is described as <strong>{{PROZESSE_PAPIERLOS_LABEL}}</strong>
    with an automation level of <strong>{{AUTOMATISIERUNGSGRAD_LABEL}}</strong>.
  </p>

  <ul>
    <li>For a {{UNTERNEHMENSGROESSE_LABEL}} company, the systems used are typical and sufficient to start initial AI pilot projects.</li>
    <li>At the same time, continuous data chains are partially missing – e.g., between lead generation, proposal creation, and service delivery.</li>
    <li>In regulated areas ({{REGULIERTE_BRANCHE_LABELS}}), data protection, retention, and access rights must be specifically considered.</li>
  </ul>

  <h3>Strengths of Current Data Foundation</h3>
  <ul>
    <li>Relevant information is already available digitally (e.g., in {{VORHANDENE_TOOLS_LABELS}}), enabling AI prototypes with real data.</li>
    <li>Many processes follow recurring patterns that are well-suited for AI-powered automation.</li>
    <li>The existing infrastructure {{IT_INFRASTRUKTUR_LABEL}} allows testing new AI tools without significant lead time.</li>
  </ul>

  <h3>Typical Gaps & Risks</h3>
  <ul>
    <li>Data is often distributed across multiple systems without unified structure or central "single source of truth."</li>
    <li>Process steps are not always consistently documented, limiting traceability for AI models.</li>
    <li>Rules for data access, deletion, and retention are partially unclear or only verbally agreed.</li>
  </ul>

  <h3>Recommended Steps for the Next 6-12 Months</h3>
  <ol>
    <li><strong>Create data map:</strong> Overview of all relevant data sources and systems, including owners and data quality.</li>
    <li><strong>Define storage & naming standards:</strong> Simple but binding rules that fit {{UNTERNEHMENSGROESSE_LABEL}}.</li>
    <li><strong>Clarify data protection & access rights:</strong> Define responsibilities, roles, and approvals for AI usage – especially in regulated areas.</li>
    <li><strong>Start AI pilot project with "clean" data slice:</strong> Choose a process where data is relatively complete and structured.</li>
  </ol>

  <p class="small muted">
    The data situation is thus sufficient to start targeted AI pilots.
    For sustainable scaling, however, structure, responsibilities, and data quality
    should be improved step by step.
  </p>
</section>

<!-- Output scope:
     - 1 introduction, 4 subsections (Status, Strengths, Gaps, Next Steps).
     - Maximum 2 short sentences per list item.
     - Write directly final, client-ready content. -->
