Developer:
<!-- costs_overview.md – v4.0 GOLD STANDARD+ (CFO-Level Cost Breakdown, size- & branch-aware)
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body>. NO Markdown fences.

     PURPOSE:
       - Supplement to Business Case, but WITHOUT repeating its content.
       - Clearly identify branch- and size-dependent cost dynamics.
       - Provide CFO- and commercially usable structure (transparency + control levers).
       - Use data from CONTEXT_BLOCK (branch + size) injected by PromptEnhancer.

     VARIABLES:
       - {{BRANCHE_LABEL}}
       - {{UNTERNEHMENSGROESSE_LABEL}}
       - {{HAUPTLEISTUNG}}

     PROHIBITED:
       - Repetition of Business Case (no ROI/Payback calculations).
       - Stage directions, placeholder texts, example texts like "xxx".
       - Unstructured outputs – always use section / table / lists.

     SIZE-AWARE LOGIC (mandatory):
       - SOLO:
           - Very lean tool landscape.
           - Focus on base models, 1-2 core tools, low operating costs.
           - Training = minimal + self-learning component.
       - TEAM (2-10):
           - Multiple users → license multipliers.
           - Typical risks: tool sprawl, duplicate licenses, unclear responsibilities.
           - Training effort distributed.
       - SME (11-100):
           - Multi-department structures, procurement-relevant.
           - Necessity: tool consolidation, standardization, license & rights management.
           - Training/enablement as recurring item.

     BRANCH-AWARE (mandatory):
       - Use industry-specific tools, workflows, pain points and typical data sources from CONTEXT_BLOCK.
       - Branch-dependent variations:
           - Specialized tools (e.g., CAD/architecture, e-commerce, healthcare IT, marketing automation)
           - Compliance/regulatory costs (e.g., finance, healthcare)
           - Data preparation costs (e.g., manufacturing vs. services)
           - Integration costs (ERP/CRM/industry systems)

     GOAL:
       - At the end, a CFO or managing director should clearly understand:
           1) Which cost blocks typically occur in their industry.
           2) How company size affects the cost structure.
           3) Where realistic savings and consolidation potentials lie.
-->

<section class="section costs-overview">
  <h2>Detailed Cost Overview</h2>

  <p>
    This cost overview supplements the Business Case with a transparent,
    branch- and size-dependent presentation of operating and one-time costs
    related to <strong>{{HAUPTLEISTUNG}}</strong> in the
    <strong>{{BRANCHE_LABEL}}</strong> industry. The structure is tailored to company size
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>:
    In small setups, a few clearly selected core tools are the focus,
    while in teams and SMEs, factors like license multipliers, compliance costs,
    and tool consolidation carry more weight.
  </p>

  <!-- 1) BRIEF CONCEPT CHECKLIST -->
  <ul class="concept-checklist">
    <li>Separation between one-time investments (setup, onboarding) and operating costs (licenses, infrastructure).</li>
    <li>Consider industry-specific specialized tools (per CONTEXT_BLOCK).</li>
    <li>Identify size-dependent cost drivers (Solo: core tools; SME: multi-user licenses, compliance costs).</li>
    <li>Systematically plan for hidden costs (time, coordination, governance).</li>
    <li>Clearly allocate optimization potentials: reduction, standardization, automation.</li>
  </ul>

  <!-- 2) TOOL-BY-TOOL BREAKDOWN -->
  <h3>Cost Overview per Tool / System</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Item</th>
        <th>Type</th>
        <th>Quantity / Users</th>
        <th>Monthly Cost</th>
        <th>Annual Cost</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Base AI Platform / Model Access</td>
        <td>Recurring</td>
        <td>
          {{UNTERNEHMENSGROESSE_LABEL}}:<br>
          Solo: 1 account<br>
          Team: 2-5 accounts<br>
          SME: 5-20 accounts
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>Workflow/Automation Tools</td>
        <td>Recurring</td>
        <td>
          Industry-typical (per CONTEXT_BLOCK):<br>
          e.g., Marketing: content automation;<br>
          IT/Tech: API/script automation;<br>
          Healthcare/Finance: compliance workflow tools.
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>Industry-Specific AI or Specialized Tools</td>
        <td>Recurring</td>
        <td>
          Varies by industry (e.g., ERP, CRM, CAD, diagnostics, e-commerce, marketing automation)
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>Storage & Infrastructure Costs (Cloud/Hosting)</td>
        <td>Recurring</td>
        <td>Depends on data volume & workflows ({{BRANCHE_LABEL}})</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>Data Preparation & Integration (one-time/periodic)</td>
        <td>One-time / periodic</td>
        <td>Depends on source systems (CRM, ERP, production, etc.)</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>Training & Enablement</td>
        <td>One-time / recurring</td>
        <td>
          Solo: self-learning focus<br>
          Team: short workshops<br>
          SME: training series + guidelines
        </td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
      <tr>
        <td>External Consulting / Implementation</td>
        <td>One-time</td>
        <td>Project scope (use case design, integration, documentation)</td>
        <td>€&nbsp;XX</td>
        <td>€&nbsp;XX</td>
      </tr>
    </tbody>
  </table>

  <!-- 3) HIDDEN COSTS -->
  <h3>Hidden and Indirect Costs</h3>
  <ul class="hidden-costs">
    <li>Internal coordination time: more pronounced in team/SME structures.</li>
    <li>Adaptation of existing workflows to AI-powered processes.</li>
    <li>Effort for maintaining and updating templates, prompts, and documentation.</li>
    <li>Industry-specific additional costs:
      <ul>
        <li>Healthcare/Finance: Data protection/compliance reviews.</li>
        <li>Manufacturing/Logistics: Data cleanup, sensor/machine data.</li>
        <li>Marketing/Creative: Asset management, brand guidelines.</li>
      </ul>
    </li>
    <li>Minor additional licenses (e.g., storage, plug-ins, optional add-ons).</li>
    <li>Context switching and learning time for new tools.</li>
  </ul>

  <!-- 4) OPTIMIZATION POTENTIALS -->
  <h3>Optimization Approaches for Operating Costs</h3>
  <ol class="optimization-list">
    <li><strong>Tool Consolidation:</strong> Reduce parallel systems (especially relevant for teams and SMEs).</li>
    <li><strong>License Review:</strong> Active vs. paid users, annual instead of monthly billing.</li>
    <li><strong>Standardization:</strong> Fixed templates, clear governance, minimizes coordination time.</li>
    <li><strong>Automation:</strong> Recurring tasks with low-code/AI workflows reduce workload & costs.</li>
    <li><strong>Data Optimization:</strong> Better data quality reduces integration and error costs.</li>
  </ol>

  <p class="small muted">
    This cost overview serves as a structured framework for planning, controlling, and
    prioritization. Depending on company size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>,
    the focus shifts between lean core costs (Solo), avoiding duplicate structures (Team),
    and standardization across multiple areas (SME).
  </p>
</section>
