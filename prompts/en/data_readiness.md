<!-- PLATIN+++ PROMPT v3.2 – Data Readiness & System Maturity (multi-size) – SPRINT N1 -->
<!-- SECTION: data_readiness -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CONTEXT_LABEL}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{IT_INFRASTRUKTUR_LABEL}}, {{PROZESSE_PAPIERLOS_LABEL}}, {{AUTOMATISIERUNGSGRAD_LABEL}}, {{DATENQUELLEN_LABELS}}, {{VORHANDENE_TOOLS_LABELS}}, {{REGULIERTE_BRANCHE_LABELS}} -->
<!-- TOKEN-BUDGET: 1600 (solo:0.8x=1280, team:1.0x=1600, kmu:1.15x=1840) -->
<!-- WORD_MINIMUM_SOLO: 110 -->
<!-- WORD_MINIMUM_TEAM: 130 -->
<!-- WORD_MINIMUM_KMU: 150 -->
<!--
GOAL: Provide a clear, practical assessment of data readiness and system maturity for AI:
  * Where do data, tools and processes stand today?
  * What is already sufficient for AI pilots?
  * Which gaps should be closed within the next 6–12 months?

SPRINT N1 – TEMPLATE PHRASES TO AVOID:
- No generic introductions like "This section summarises..."
- No redundant references to other sections in the introduction.
- Start directly with sector‑specific context.

AVAILABLE VARIABLES (labels/user inputs):
- {{BRANCH_CONTEXT_LABEL}} – Sector context for narrative introduction.
- {{BRANCHE_LABEL}} – Branch label (e.g. media & creative industries).
- {{UNTERNEHMENSGROESSE_LABEL}} – Company size label.
- {{HAUPTLEISTUNG}} – Main service/product.
- {{IT_INFRASTRUKTUR_LABEL}} – e.g. "cloud‑based", "on‑premises", "hybrid".
- {{PROZESSE_PAPIERLOS_LABEL}} – Degree of process digitalisation.
- {{AUTOMATISIERUNGSGRAD_LABEL}} – Degree of automation.
- {{DATENQUELLEN_LABELS}} – List of typical data sources (CRM, ERP, tickets etc.).
- {{VORHANDENE_TOOLS_LABELS}} – List of existing tools/platforms (e.g. M365, CRM, DMS).
- {{REGULIERTE_BRANCHE_LABELS}} – Indicators for regulation (e.g. health data).
  {{DATENQUELLEN_LABELS}} may be empty or very short. Then use typical sources for the branch/size context.

SIZE LOGIC:
- "1 (Solo)": Data often scattered across a few tools (email, Office, simple SaaS tools).
    * Focus: create order, simple standards, minimal overhead.
- "2–10": Small tool landscape, but initial roles/access logic.
    * Focus: unified storage, clean rights, simple data pipelines.
- "11–100": Multiple systems/departments, possible shadow IT.
    * Focus: binding data governance, interfaces, roles and responsibilities.

RULES:
- No references to questionnaire/questions, no technical placeholder texts.
- Always write as if the assessment goes directly to management/project leadership.
- Clear, sober tone: opportunities + risks, no exaggerations.

SPRINT G18 – ANTI‑REDUNDANCY (STRICT!):
- Do NOT mention ROI/investments/business case – these topics belong in business_case.md.
- Maximum ONE brief reference to the Business Case is allowed (e.g., "→ see Business Case").
- CAPEX/OPEX blocks do NOT belong here.
- Focus: data quality, system maturity, data sources – no financial perspective.
-->

<section class="section data-readiness">
  <h2>Data Readiness & System Maturity for AI</h2>

  <!-- SPRINT N1: Direct sector-specific introduction without template phrases -->
  <p>
    In <strong>{{BRANCH_CONTEXT_LABEL}}</strong> successful AI implementation is based on
    a solid data foundation. The existing data sources, structures and interfaces are
    the starting point for initial AI workflows – and show at the same time where targeted improvements should be made.
  </p>

  <h3>Where data and systems lie today</h3>
  <p>
    Information is currently processed mainly in the following systems:
    <strong>{{DATENQUELLEN_LABELS}}</strong> and in the tools used
    <strong>{{VORHANDENE_TOOLS_LABELS}}</strong>.
    The IT infrastructure is <strong>{{IT_INFRASTRUKTUR_LABEL}}</strong>, the
    digitisation degree of processes is described as <strong>{{PROZESSE_PAPIERLOS_LABEL}}</strong>
    with an automation degree of <strong>{{AUTOMATISIERUNGSGRAD_LABEL}}</strong>.
  </p>

  <ul>
    <li>For a {{UNTERNEHMENSGROESSE_LABEL}} company the systems in use are typical and sufficient to start initial AI pilot projects.</li>
    <li>At the same time continuous data chains are partially missing – e.g. between lead capture, quote creation and service delivery.</li>
    <li>In regulated areas ({{REGULIERTE_BRANCHE_LABELS}}) data protection, retention and access rights must be explicitly considered.</li>
  </ul>

  <h3>Strengths of the current data basis</h3>
  <ul>
    <li>Relevant information is already available digitally (e.g. in {{VORHANDENE_TOOLS_LABELS}}), enabling AI prototypes with real data.</li>
    <li>Many processes follow recurring patterns that are well suited for AI‑driven automation.</li>
    <li>The existing infrastructure {{IT_INFRASTRUKTUR_LABEL}} allows new AI tools to be tested without long lead times.</li>
  </ul>

  <h3>Typical gaps & risks</h3>
  <ul>
    <li>Data is often spread across multiple systems, without a unified structure or a central “single source of truth”.</li>
    <li>Process steps are not always consistently documented, which limits the traceability for AI models.</li>
    <li>Rules for data access, deletion and retention are partly unclear or only verbally agreed.</li>
  </ul>

  <h3>Recommended steps for the next 6–12 months</h3>
  <ol>
    <li><strong>Create a data map:</strong> Overview of all relevant data sources and systems, including responsible persons and data quality.</li>
    <li><strong>Define a standard for storage & naming:</strong> Simple but binding rules that match {{UNTERNEHMENSGROESSE_LABEL}}.</li>
    <li><strong>Clarify data protection & access rights:</strong> Define responsibilities, roles and approvals for AI use – especially in regulated areas.</li>
    <li><strong>Start an AI pilot project with a “clean” data slice:</strong> Choose a process where data is relatively complete and structured.</li>
  </ol>

  <p class="small muted">
    The data situation is therefore sufficient to start targeted AI pilots.
    For sustainable scaling, however, structure, responsibilities and data quality
    should be improved step by step.
  </p>
</section>

<!-- Output scope:
     - 1 introduction, 4 subsections (status, strengths, gaps, next steps).
     - Maximum 2 short sentences per list item.
     - Write directly final, customer‑ready content. -->
