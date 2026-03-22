**IMPORTANT – Length limit: Your response must not exceed 1200 words. Cut rather than exceed.**

<!-- PLATIN+++ PROMPT v6.1 - SPRINT FINAL CONTENT -->
<!-- SECTION: roadmap_12m -->
<!--
=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- Transformation report WITH safety & governance guardrails
- Clearly state the central strategic switch
- Explicitly replace the old logic (formula: "No longer X, but Y")
- Use the main revenue driver ({{HAUPTUMSATZTREIBER}}) as a reference point
- Describe DECISIONS, not tools
- NO consulting language, NO CTAs
- Short paragraphs: one thought per paragraph, 2–4 sentences

MICRO‑CONSISTENCY (mandatory):
The strategic switch named in the executive summary must be elaborated in the Gamechanger and referenced linguistically in the roadmaps (use the same terms, the same logic).

HTML CONTRACT (mandatory):
ALLOWED: <p>, <ul>, <ol>, <li>, <strong>, <em>
FORBIDDEN: <h1>, <h2>, <h3>, <h4>, <section>, <article>
→ Headings are set by the template, not by the GPT output
=============================================================================
-->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE‑AWARE: solo/team/kmu -->
<!-- SPRINT G18 -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE, {{MASSNAHMEN_KOMPLEXITAET}} -->
<!-- TOKEN‑BUDGET: 4200 (solo:0.8x=3360, team:1.0x=4200, kmu:1.15x=4830) -->
<!-- WORD_MINIMUM_SOLO: 500 -->
<!-- WORD_MINIMUM_TEAM: 600 -->
<!-- WORD_MINIMUM_KMU: 700 -->
<!--
GOAL: 12‑month roadmap as a strategic chain of decisions (not a tool rollout).

=============================================================================
LANGUAGE SHIFT v6.0 — DECISIONS INSTEAD OF IMPLEMENTATIONS:
=============================================================================

FORBIDDEN PHRASES → REPLACEMENTS:
❌ "Implementation/rollout"  → ✅ "Definition/setting/clarification"
❌ "Roll out a tool"            → ✅ "Establish standards"
❌ "Integrate a system"         → ✅ "Clarify responsibilities"
❌ "Automate a workflow"        → ✅ "Create decision frameworks"
❌ "Drive digitalisation"       → ✅ "Set priorities"

The roadmap shows WHICH DECISIONS need to be made, not WHICH TOOLS need to be introduced.

READABILITY (v6.1 NEW):
- Maximum ONE abstract thought per paragraph
- 2–4 sentences per paragraph (no more)
- No convoluted sentences – one main clause, at most one subordinate clause
- Max. 3 sentences per bullet point

=============================================================================

MINIMUM LENGTH (STRICTLY REQUIRED!):
- Solo: at least 500 words (including Q1–Q4 phases)
- Team: at least 600 words (including roles and standards)
- SME: at least 700 words (including 5‑dimension rollout)

IMPORTANT: These minimum lengths are mandatory and will be validated!

SHORT LABELS (MANDATORY!):
- {{BRANCH_CORE_LABEL}} = industry in 8–12 words
- {{BRANCH_CONTEXT_LABEL}} = industry in 4–6 words
- {{OFFERING_LABEL}} = main service in 6–10 words
- DO NOT use long industry texts in the output!

STRUCTURE BY SIZE (max. 3 main sections):
- Solo: time‑based phases (Q1, Q2, Q3–4)
- Team: time‑based phases with roles
- SME: block structure (tech, data, organisation, product, compliance) + rollout

LEADING DECISIONS PER QUARTER (v6.1 NEW – embed implicitly, not as headings):
- Q1: “Foundation before expansion” – secure the quality of the base
- Q2: “Standards before scaling” – establish unified rules
- Q3–Q4: “Responsibility before speed” – accompany governance
These principles should flow into the quarter descriptions linguistically.

COMPLEXITY PREFERENCE:
- Desired implementation effort: {{MASSNAHMEN_KOMPLEXITAET}}
- Adjust complexity and timeline of recommendations accordingly.

FORMAT:
- Milestones instead of long text
- Each block: 2–3 concrete measures + 1 milestone
- Realistic time horizons

ANTI‑REDUNDANCY (STRICT!):
- 90‑day contents → DO NOT repeat (addressed there)
- Quick Wins → DO NOT repeat
- Tools → DO NOT repeat
- Focus: WHAT COMES AFTER the first 90 days?
- If repetition is necessary: use a cross‑reference (→ see section X)

PERSONA VARIATIONS (COMPANY_SIZE):
- Solo: own workflows, self‑review, personal routine
- Team: AI coordinator, shared standards, review rounds
- SME: departments, governance board, rollout plan, compliance

SPRINT G5 - PERSONA HARD‑GUARDS (STRICT!):
{% if COMPANY_SIZE == "solo" %}
SOLO MODE – FORBIDDEN:
- "team/teams" → "capacity/capacities"
- "department" → "work area"
- "employees" → "external support"
- "HR/functional area" → do not use
- "build a team" → "expand capacity"
{% elif COMPANY_SIZE == "team" %}
TEAM MODE – FORBIDDEN:
- "department/functional area" → "area"
- "division/unit" → do not use
- "governance board" → "team lead"
- "corporate" → do not use
- Solo terms: "individual", "alone"
{% else %}
SME MODE – FORBIDDEN:
- "corporate/division/unit" → do not use
- Solo terms: "individual", "alone", "personal"
- Avoid overloading with governance jargon
{% endif %}
-->

<p><strong>12‑month roadmap for {{OFFERING_LABEL}}</strong></p>

{% if COMPANY_SIZE == "solo" %}
<p>Building on the first 90 days – focus on sustainable integration and expansion.</p>

<p><strong>Q1 (months 1–3): Consolidate the foundation</strong></p>
<ul>
  <li>Make successful workflows from the 90‑day phase routine and document personal lessons learned.</li>
  <li>Test two to three additional use cases from {{BRANCH_CONTEXT_LABEL}} to broaden experience without overloading capacity.</li>
  <li>Expand your personal prompt library to over twenty templates tailored to {{OFFERING_LABEL}}.</li>
</ul>
<p><em>🎯 Q1 milestone:</em> Achieve a stable time saving of 10+ hours per month.</p>

<p><strong>Q2 (months 4–6): Improve quality</strong></p>
<ul>
  <li>Apply a quality checklist to all AI outputs to ensure consistency and reliability.</li>
  <li>Systematically integrate first data sources such as CRM entries, notes and documents to enrich AI prompts.</li>
  <li>Create workflow documentation that enables representation and scaling without additional team structures.</li>
</ul>
<p><em>🎯 Q2 milestone:</em> Achieve a first‑time accuracy rate above 90 % for standard tasks.</p>

<p><strong>Q3–Q4 (months 7–12): Expand and optimise</strong></p>
<ul>
  <li>Open up new application fields such as marketing, customer communication and reporting within your work area.</li>
  <li>Measure and document time savings systematically to identify the most effective routines.</li>
  <li>Conduct an annual review: calculate ROI, set priorities for the second year and decide which capacities to expand.</li>
</ul>
<p><em>🎯 End‑of‑year milestone:</em> Demonstrable ROI and clear priorities for the next year.</p>

{% elif COMPANY_SIZE == "team" %}
<p>Building on the first 90 days – focus on scaling across the team.</p>

<p><strong>Q1 (months 1–3): Establish team standards</strong></p>
<ul>
  <li>Appoint an AI coordinator responsible for quality and standards and clarify responsibilities for {{BRANCH_CONTEXT_LABEL}}.</li>
  <li>Build a shared prompt library with at least thirty templates that cover core processes of {{OFFERING_LABEL}}.</li>
  <li>Introduce weekly 15‑minute review sessions to share best practices and align outputs.</li>
</ul>
<p><em>🎯 Q1 milestone:</em> All team members regularly use AI within their workflows.</p>

<p><strong>Q2 (months 4–6): Quality & data</strong></p>
<ul>
  <li>Formalise the quality‑assurance process: input → AI → review → approval to ensure traceability.</li>
  <li>Create a team style guide for AI outputs to align tone and formatting across roles.</li>
  <li>Start integrating shared data sources (e.g. common documents, CRM) to improve context quality.</li>
</ul>
<p><em>🎯 Q2 milestone:</em> Unified quality, error rate below 10 %.</p>

<p><strong>Q3–Q4 (months 7–12): Scaling & ROI</strong></p>
<ul>
  <li>Explore new use cases from adjacent areas and document their impact on efficiency and quality.</li>
  <li>Expand success measurement to cover time, cost and quality metrics at team level.</li>
  <li>Conduct an annual review: align budget and set priorities for year 2, ensuring governance accompanies further scaling.</li>
</ul>
<p><em>🎯 End‑of‑year milestone:</em> Demonstrable ROI and a prepared Roadmap 2.0.</p>

{% else %}
<p>Building on the first 90 days – professional rollout across five dimensions.</p>

<p><strong>Dimension 1: Technology (Q1–Q2)</strong></p>
<ul>
  <li>Finalise the tool stack: confirm licences, access rights and integrations to essential systems.</li>
  <li>Review data interfaces to existing systems and address any technical gaps early.</li>
  <li>Create technical documentation to standardise maintenance and onboarding.</li>
</ul>
<p><em>🎯 Milestone:</em> Stable tech stack, integrations functioning.</p>

<p><strong>Dimension 2: Data (Q1–Q2)</strong></p>
<ul>
  <li>Identify and connect relevant data sources (CRM, ERP, process systems) that support {{OFFERING_LABEL}}.</li>
  <li>Ensure data quality for AI use: establish validation routines and consistent formats.</li>
  <li>Clarify access rights and data‑protection requirements in line with industry standards.</li>
</ul>
<p><em>🎯 Milestone:</em> Core data available for AI use and compliant.</p>

<p><strong>Dimension 3: Organisation (Q2–Q3)</strong></p>
<ul>
  <li>Appoint AI leads in each functional area to embed ownership and knowledge.</li>
  <li>Roll out the training concept: provide targeted workshops and ensure continuous learning.</li>
  <li>Establish a governance board with quarterly reviews to oversee standards and risks.</li>
</ul>
<p><em>🎯 Milestone:</em> Clear responsibilities and a trained workforce.</p>

<p><strong>Dimension 4: Product/Process (Q2–Q4)</strong></p>
<ul>
  <li>Roll out to two to three additional areas after pilot success, focusing on processes closely tied to {{OFFERING_LABEL}}.</li>
  <li>Define standard operating procedures (SOPs) for all AI processes to ensure repeatability and quality.</li>
  <li>Measure impact per area (time, cost, quality) and align priorities accordingly.</li>
</ul>
<p><em>🎯 Milestone:</em> Three or more areas live with measurable efficiency gains.</p>

<p><strong>Dimension 5: Compliance (Q3–Q4)</strong></p>
<ul>
  <li>Check AI Act relevance and document obligations for each use case.</li>
  <li>Conduct a risk assessment for all AI applications, integrating results from the risk engine.</li>
  <li>Implement transparency obligations wherever AI is in use and update stakeholders regularly.</li>
</ul>
<p><em>🎯 Milestone:</em> Compliance documentation complete.</p>

<p><strong>Year‑end</strong></p>
<ul>
  <li>Hold a management review with ROI proof to decide on further investments.</li>
  <li>Plan the budget for year 2 based on measured outcomes and strategic priorities.</li>
  <li>Define Roadmap 2.0 with scaling goals and governance enhancements.</li>
</ul>
<p><em>🎯 End‑of‑year milestone:</em> Board decision for year 2, rollout plan in place.</p>

{% endif %}

<hr/>
<p class="small muted">This roadmap builds on the results of the 90‑day plan and references quick wins and tools from the corresponding sections.</p>

<!-- ZERO‑LEAK POLICY (N4.6) -->
<!--
FORBIDDEN – NEVER USE:
- No questions to the reader (“Do you have questions?”, “Would you like to know more?”)
- No prompts (“If you want to…”, “Contact us…”) 
- No assistant language (“I can help you…”, “I’d be happy to explain…”) 
- No offers (“If desired…”, “As needed…”) 
- No interactive elements (“Click here…”, “Choose…”) 
- No placeholders (“[Insert here]”, “{{VARIABLE}}” except defined ones) 
- No meta comments (“This section…”, “In the following…”) 

The output is a FINAL REPORT SECTION, not a conversation.
-->