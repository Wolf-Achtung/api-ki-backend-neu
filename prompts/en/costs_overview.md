<!-- costs_overview.md – v4.0 GOLD STANDARD+ (CFO‑level cost breakdown, size‑ & branch‑aware)
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body> tags. NO markdown fences.

     PURPOSE:
       - Supplement to the business case without repeating its content.
       - Clearly state cost dynamics dependent on industry and company size.
       - Provide a structure usable by CFOs and finance leads (transparency + levers for control).
       - Use the data from the CONTEXT_BLOCK (branch + size) injected by the PromptEnhancer.

     VARIABLES:
       - {{BRANCHE_LABEL}}
       - {{UNTERNEHMENSGROESSE_LABEL}}
       - {{HAUPTLEISTUNG}}

     Do not use:
       - Repetition of the business case (no ROI or payback calculation).
       - Directions, placeholder text or sample phrases like "xxx".
       - Unstructured outputs – always use sections, tables and lists.

     SIZE‑AWARE LOGIC (mandatory):
       - SOLO:
           - Very lean tool landscape.
           - Focus on base models, 1–2 core tools, low recurring costs.
           - Training = minimal + self‑learning component.
       - TEAM (2–10):
           - Multiple users → licence multipliers.
           - Typical risks: tool sprawl, duplicate licences, missing responsibilities.
           - Training effort distributed.
       - KMU (11–100):
           - Multi‑domain structures, procurement relevance.
           - Necessity: tool consolidation, standardisation, licence & rights management.
           - Training/enablement as a recurring item.

     BRANCH‑AWARE (mandatory):
       - Use industry‑specific tools, workflows, pain points and typical data sources from the CONTEXT_BLOCK.
       - Variations by industry:
           - specialist tools (e.g. editing and grading software, DAW and voice synthesis, editorial system, game engine, media asset management)
           - compliance/regulatory efforts (e.g. finance, health)
           - data preparation costs (e.g. archive tagging vs. text-based work)
           - integration costs (ERP/CRM/industry systems)

     GOAL:
       - At the end, a CFO or managing director should clearly understand:
           1) Which cost blocks typically occur in their industry.
           2) How company size affects the cost structure.
           3) Where realistic savings and consolidation potentials lie.

     OUTPUT STRUCTURE:
       - <section class="section costs-overview">
           - h2
           - Introduction (branch + size)
           - 1) Concept checklist
           - 2) Tool‑by‑tool breakdown
           - 3) Hidden costs (branch‑ & size‑aware)
           - 4) Optimisation potentials (clear CFO focus)
           - Closing note
-->

<section class="section costs-overview">
  <h2>Detailed cost overview</h2>

  <p>
    This cost overview supplements the business case with a transparent,
    industry‑ and size‑dependent presentation of recurring and one‑off expenses
    related to <strong>{{HAUPTLEISTUNG}}</strong> in the
    <strong>{{BRANCHE_LABEL}}</strong> sector. The structure is tailored to
    the company size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>:
    In small setups, a few clearly selected core tools are central, while in
    teams and SMEs factors such as licence multipliers, compliance efforts and
    tool consolidation carry more weight.
  </p>

  <!-- 1) SHORT CONCEPT CHECKLIST -->
  <ul class="concept-checklist">
    <li>Separate one‑off investments (setup, onboarding) from ongoing costs (licences, infrastructure).</li>
    <li>Include industry‑specific specialist tools (according to the CONTEXT_BLOCK).</li>
    <li>Identify size‑dependent cost drivers (Solo: core tools; KMU: multi‑user licences, compliance efforts).</li>
    <li>Systematically plan hidden costs (time, alignment, governance).</li>
    <li>Clearly assign optimisation potentials: reduction, standardisation, automation.</li>
  </ul>

  <!-- 2) TOOL‑BY‑TOOL BREAKDOWN -->
  <h3>Cost overview by tool / system</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Item</th>
        <th>Type</th>
        <th>Quantity / users</th>
        <th>Monthly costs</th>
        <th>Annual costs</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Base AI platform / model access</td>
        <td>Recurring</td>
        <td>
          <!-- size‑aware -->
          {{UNTERNEHMENSGROESSE_LABEL}}:<br>
          Solo: 1 account<br>
          Team: 2–5 accounts<br>
          KMU: 5–20 accounts
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Workflow/automation tools</td>
        <td>Recurring</td>
        <td>
          Industry‑typical (according to CONTEXT_BLOCK):<br>
          e.g. marketing: content automation;<br>
          IT/tech: API/script automation;<br>
          health/finance: compliance workflow tools.
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Specialist AI or industry tools</td>
        <td>Recurring</td>
        <td>
          Varies by industry (e.g. ERP, CRM, CAD, diagnostics, e‑commerce, marketing automation)
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Storage & infrastructure costs (cloud/hosting)</td>
        <td>Recurring</td>
        <td>Depending on data volume & workflows ({{BRANCHE_LABEL}})</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Data preparation & integration (one‑off/periodic)</td>
        <td>One‑off / periodic</td>
        <td>Depending on source systems (CRM, ERP, production, etc.)</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>Training & enablement</td>
        <td>One‑off / recurring</td>
        <td>
          Solo: self‑learning focus<br>
          Team: short workshops<br>
          KMU: training series + policies
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>

      <tr>
        <td>External consulting / implementation</td>
        <td>One‑off</td>
        <td>Project scope (use‑case design, integration, documentation)</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
    </tbody>
  </table>

  <!-- 3) HIDDEN COSTS -->
  <h3>Hidden and indirect costs</h3>
  <ul class="hidden-costs">
    <li>Internal alignment times: more pronounced in team/SME structures.</li>
    <li>Adjusting existing workflows to AI‑driven processes.</li>
    <li>Effort for maintaining and updating templates, prompts and documentation.</li>
    <li>Industry‑specific additional efforts:
      <ul>
        <li>Film/TV and post-production: archive tagging, rights metadata, storage for raw footage.</li>
        <li>Publishing and agencies: asset management, brand guidelines, approval processes.</li>
        <li>Audio and games: licence checks for voices and assets, quality assurance.</li>
      </ul>
    </li>
    <li>Smaller additional licences (e.g. storage, plug‑ins, optional add‑ons).</li>
    <li>Context switching and learning times for new tools.</li>
  </ul>

  <!-- 4) OPTIMISATION POTENTIALS -->
  <h3>Approaches to optimise ongoing costs</h3>
  <ol class="optimization-list">
    <li><strong>Tool consolidation:</strong> reduce parallel systems (especially relevant for teams and SMEs).</li>
    <li><strong>Licence review:</strong> active vs. paid users, annual instead of monthly billing.</li>
    <li><strong>Standardisation:</strong> fixed templates, clear governance minimise alignment time.</li>
    <li><strong>Automation:</strong> reduce workload and costs for recurring tasks with low‑code/AI workflows.</li>
    <li><strong>Data optimisation:</strong> better data quality lowers integration and error costs.</li>
  </ol>

  <p class="small muted">
    This cost overview serves as a structured framework for planning, controlling and prioritisation. Depending on
    company size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>, the focus shifts between lean core costs (Solo),
    avoiding duplicate structures (Team) and standardisation across multiple domains (KMU).
  </p>
</section>