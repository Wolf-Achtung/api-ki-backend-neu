<!-- PLATIN+++ PROMPT v6.1 - AI Stack Recommendations -->
<!-- SECTION: tools_recommendations -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- TOKEN-BUDGET: 2800 (solo:0.8x=2240, team:1.0x=2800, kmu:1.15x=3220) -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{BRANCH_SHORT_LABEL}}, {{OFFERING_LABEL}}, {{COMPANY_SIZE}}, {{hauptleistung}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->

=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- [✓] Provide a clear, structured AI tool recommendation section (the “AI stack”) tailored to the branch context {{BRANCH_CONTEXT_LABEL}} and the main service {{OFFERING_LABEL}}/"{{hauptleistung}}".
- [✓] Use short labels: {{BRANCH_CORE_LABEL}} (8–12 words), {{BRANCH_CONTEXT_LABEL}} (4–6 words), {{BRANCH_SHORT_LABEL}} (3–5 words), {{OFFERING_LABEL}} (6–10 words). Do not translate variable names.
- [✓] Meet the minimum word counts: ≥150 words (Solo), ≥200 words (Team), ≥250 words (KMU). Keep paragraphs to 2–3 sentences and avoid dense text blocks.
- [✓] Structure the AI stack into tool clusters by company size:
  * **Solo:** Four clusters, each with 2–3 examples: (1) AI assistant & basic stack, (2) Core process tools for {{OFFERING_LABEL}}, (3) Quality & documentation, (4) Responsible AI & governance tools.
  * **Team:** Five clusters: (1) Collaboration & shared workspace, (2) Core process tools for {{OFFERING_LABEL}}, (3) Reporting & analytics, (4) Governance & quality, (5) Responsible AI & governance tools. In regulated industries (finance, health, law), add subsections on data platforms, risk & compliance tools, and reporting & collaboration.
  * **KMU:** Six clusters: (1) Enterprise foundation (platform, knowledge store), (2) Department-specific tools for {{OFFERING_LABEL}}, (3) Reporting/BI integration, (4) Compliance & governance, (5) Roll-out & training, (6) Responsible AI & governance tools.
- [✓] Include a mandatory sub-section “Responsible AI & Governance Tools” for all sizes, describing audit trails, versioning and review mechanisms. Length: Solo 30–50 words, Team 40–60 words, KMU 50–70 words. Describe tool classes, not specific brands.
- [✓] Use narrative connections: reference how these tool categories support the phases of the 90‑day and 12‑month roadmaps, and link to the Starter Kit and relevant funding programmes where appropriate.
- [✓] Maintain a neutral, product‑agnostic tone: focus on tool categories and their purpose; do not mention brand names. Describe the purpose and integration logic of each cluster. Avoid generic meta-sentences, placeholder text and developer language.
- [✓] Respect persona vocabulary rules: In Solo mode avoid “department”, “project team”, “employees”; in Team mode avoid corporate jargon (“division”, “unit”); in KMU mode avoid solo or enterprise terms. Use “capacity”, “resources”, “team” etc. accordingly.
=============================================================================

<section class="section tools">
  <h2>Recommended AI Stack for {{BRANCH_CONTEXT_LABEL}}</h2>

  <p>
    {% if hauptleistung %}
    For "{{hauptleistung}}" we recommend a clearly structured AI stack that directly supports this core service, saves time and can be expanded step by step.
    {% else %}
    For {{OFFERING_LABEL}} we recommend a clearly structured AI stack that delivers tangible relief and can be scaled in stages as needed.
    {% endif %}
  </p>

  <h3>Orientation by Company Size</h3>
  <ul>
    <li>
      <strong>Solo professionals:</strong>
      A lean stack with 3–5 core components is sufficient – an AI assistant, a structured knowledge store and simple automations. Keep complexity low and maintenance minimal.
    </li>
    <li>
      <strong>Small teams (2–10):</strong>
      Focus on a shared workspace, clear responsibilities and straightforward task coordination. Tools should support collaboration, shared knowledge and aligned workflows.
    </li>
    <li>
      <strong>SMEs (11–100):</strong>
      A defined AI stack with roles, permissions and monitoring is key. Departments need autonomous yet compatible solutions embedded in an overarching governance framework.
    </li>
  </ul>

  {% if COMPANY_SIZE == "solo" %}
  <h3>1. AI Assistant &amp; Basics</h3>
  <p>
    Begin with a versatile AI assistant for drafting, editing and summarising text as well as organising notes. Couple this with a lightweight knowledge store for templates and prompts, and simple automation to streamline repetitive tasks.
  </p>

  <h3>2. Core Process Tools for {{OFFERING_LABEL}}</h3>
  <p>
    Choose a form or questionnaire tool to capture client data structured for {{OFFERING_LABEL}}. Pair it with a reporting tool that leverages AI to generate analyses and reports. Add a basic automation tool to link form input, analysis and result delivery.
  </p>

  <h3>3. Quality &amp; Documentation</h3>
  <p>
    Implement a simple routine for documenting your AI usage: note which tools are used for which purpose, the types of data processed and any protection measures. Establish a quick review process (e.g. a second look at management reports) to ensure consistency and correctness.
  </p>

  <h3>4. Responsible AI &amp; Governance Tools</h3>
  <p>
    Introduce mechanisms for audit trails, version control and review. Tools should log AI requests and responses, track prompt versions and provide simple checklists for approving outputs before delivery. These foundations ensure transparency and facilitate future scaling.
  </p>
  {% elif COMPANY_SIZE == "team" %}
  <h3>1. Collaboration &amp; Shared Workspace</h3>
  <p>
    Use a unified workspace that allows your team to store templates, prompts and best practices in a central knowledge base. Integrate task management to assign responsibilities and deadlines, supporting shared workflows and visibility.
  </p>

  <h3>2. Core Process Tools for {{OFFERING_LABEL}}</h3>
  <p>
    Implement a multi‑user form tool to collect structured data and a reporting engine that transforms inputs into consistent AI‑generated analyses. Add an automation layer to connect submissions, evaluations and report creation.
  </p>

  <h3>3. Reporting &amp; Analytics</h3>
  <p>
    Deploy a business intelligence solution to visualise outcomes and track key metrics related to your AI initiatives. This allows teams to review results, share insights and adjust processes collaboratively.
  </p>

  <h3>4. Governance &amp; Quality</h3>
  <p>
    Establish short written guidelines on which data may be entered into AI tools, how outputs should be reviewed and who has the final say. Set up brief documentation of AI usage and appoint a coordinator to oversee quality and compliance.
  </p>

  <h3>5. Responsible AI &amp; Governance Tools</h3>
  <p>
    Require audit trails for AI interactions, versioning systems for prompts and models, and defined review workflows. For regulated industries (finance, health, law) add subsections on data platforms, risk & compliance tools and secure reporting and collaboration mechanisms to meet industry standards.
  </p>
  {% else %}
  <h3>1. Enterprise Foundation</h3>
  <p>
    Build your stack on an AI platform and central knowledge repository that support multi‑user access, version control and scalable infrastructure. This foundation should integrate with existing enterprise systems and support knowledge sharing across departments.
  </p>

  <h3>2. Department‑Specific Tools for {{OFFERING_LABEL}}</h3>
  <p>
    Equip each functional area with tailored tools for {{OFFERING_LABEL}}. For example, form tools for structured data capture, analysis engines for automated insights and specialist applications aligned with departmental needs. Ensure all tools adhere to common standards and integrate into the central platform.
  </p>

  <h3>3. Reporting &amp; BI Integration</h3>
  <p>
    Adopt reporting and business intelligence solutions that consolidate data from across the organisation. These tools should provide dashboards and KPIs to monitor progress and support strategic decision‑making.
  </p>

  <h3>4. Compliance &amp; Governance</h3>
  <p>
    Implement enterprise‑grade compliance and governance modules: policy management, data protection controls, risk monitoring and audit capabilities. Align these with industry regulations and internal guardrails.
  </p>

  <h3>5. Roll‑out &amp; Training</h3>
  <p>
    Plan a phased roll‑out of your AI stack. Start with core components, then add process‑specific tools and finally integrate automation and governance modules. Include role‑specific training to ensure adoption across all levels of the organisation.
  </p>

  <h3>6. Responsible AI &amp; Governance Tools</h3>
  <p>
    Adopt tools that provide audit trails, version management and review workflows. Ensure that AI interactions are logged, prompt and model changes are tracked and approvals are obtained before critical outputs are released. These measures build trust and accountability across your organisation.
  </p>
  {% endif %}

  <p class="small muted">
    These AI tool categories align with the phases of your 90‑day and 12‑month roadmaps and complement the curated selections in your Starter Kit. Funding programmes may support investments in compliance and training tools – refer to the funding overview for details. Introduce each component in stages to maximise impact and maintain control.
  </p>
</section>