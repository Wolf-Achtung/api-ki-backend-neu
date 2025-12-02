Developer:
<!-- recommendations.md – v8.0 PLATIN+ STREAMLINED
     Goal: 5-6 recommendations with 100-120 words each (= 800-1000 words total).
     Respond exclusively with valid HTML. No Markdown fences.

     STRUCTURE (Mandatory elements):
       1. Introduction (50-80 words)
       2. 5-6 recommendations, each with:
          - Focus (1-2 sentences)
          - Action (2-3 sentences, specific)
          - Benefit & Impact (2 sentences)
          - Effort & Budget (1-2 sentences, size-aware)
          - Responsible (1 sentence, size-aware)
       3. Priorities table (5 rows)

     VARIABLES – use all at least once:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}},
       {{COMPANY_SIZE}}

     SIZE-AWARE (COMPANY_SIZE):
       solo: Owner, personal steps, low budget
       team: Team lead/AI Owner, shared workflows, medium budget
       kmu: Functional areas, governance, structured investments

     RULES:
       - Recommendations industry-specific and actionable
       - Timeframes size-aware (solo: 0-3/3-6/6-12, team/kmu: 0-6/6-9/9-12)
       - Factual, concrete, no platitudes
       - No placeholders, no developer language
-->

<section class="section recommendations">
  <h2>Recommendations – Your Next Steps with AI</h2>

  <p>
    For a company in the <strong>{{BRANCHE_LABEL}}</strong> industry with size
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>, several immediately
    actionable levers emerge to effectively deploy AI in the process
    <strong>{{HAUPTLEISTUNG}}</strong>. The following recommendations are
    prioritized, practical, and aligned with realistic resources.
  </p>

  <ol class="recommendations-list">

    <!-- RECOMMENDATION 1 – branch- & size-aware -->
    <li>
      <h3>Recommendation&nbsp;1: Quick Win – Introduce Standard Workflow</h3>
      <p><strong>Focus:</strong> Improvement of a central, recurring step in {{HAUPTLEISTUNG}} that typically consumes time according to industry workflows.</p>
      <p><strong>Action:</strong>
        Introduction of an AI-powered standard workflow (e.g., analysis, text drafting, quality check) with clear rules for inputs and review steps.
      </p>
      <p><strong>Benefit &amp; Impact:</strong>
        Directly measurable relief, higher consistency, and more stable quality, especially during fluctuating workload.
      </p>
      <p><strong>Effort &amp; Budget:</strong>
        Low – achievable in a few days; tool costs depend on platform used (typically two-digit to low three-digit range/month).
      </p>
      <p><strong>Responsible:</strong>
        {% if COMPANY_SIZE == "solo" %}Owner{% elif COMPANY_SIZE == "team" %}Team lead or AI Owner{% else %}Functional area + responsible leadership{% endif %}.
      </p>
    </li>

    <!-- RECOMMENDATION 2 -->
    <li>
      <h3>Recommendation&nbsp;2: Quality Assurance – AI-Powered Consistency Check</h3>
      <p><strong>Focus:</strong>
        AI-powered consistency check for documents, content, or data structures, aligned with industry-typical requirements.
      </p>
      <p><strong>Action:</strong>
        Setting up an automated review step (e.g., fact check, tone, brand guidelines, compliance) that runs before approval.
      </p>
      <p><strong>Benefit &amp; Impact:</strong>
        Less rework, lower risk of errors, more stable quality across multiple assignments.
      </p>
      <p><strong>Effort &amp; Budget:</strong>
        Medium – 2–5 days setup; licenses depend on user count.
      </p>
      <p><strong>Responsible:</strong>
        {% if COMPANY_SIZE == "solo" %}Owner{% elif COMPANY_SIZE == "team" %}Team lead or quality responsible{% else %}Quality management + functional area{% endif %}.
      </p>
    </li>

    <!-- RECOMMENDATION 3 -->
    <li>
      <h3>Recommendation&nbsp;3: Knowledge Management – Documentation &amp; Knowledge Base</h3>
      <p><strong>Focus:</strong>
        Improve documentation & knowledge management – a typical pain point according to industry context.
      </p>
      <p><strong>Action:</strong>
        Build an AI-powered knowledge library (e.g., templates, standards, checklists) that centralizes and simplifies work materials.
      </p>
      <p><strong>Benefit &amp; Impact:</strong>
        Faster onboarding, higher first-time-right rate, fewer questions, and more consistent results in daily business.
      </p>
      <p><strong>Effort &amp; Budget:</strong>
        Low to medium – depends on existing material; ongoing costs are low.
      </p>
      <p><strong>Responsible:</strong>
        {% if COMPANY_SIZE == "solo" %}Owner{% elif COMPANY_SIZE == "team" %}AI Owner or team lead{% else %}Knowledge management / process owners{% endif %}.
      </p>
    </li>

    <!-- RECOMMENDATION 4 – industry-specific -->
    <li>
      <h3>Recommendation&nbsp;4: Industry-Specific Use Case</h3>
      <p><strong>Focus:</strong> An industry-specific use case from the CONTEXT_BLOCK (e.g., content automation, data analysis, compliance, production optimization).</p>
      <p><strong>Action:</strong>
        Pilot a one-time, clearly defined AI use case that promises high visibility and quick ROI.
      </p>
      <p><strong>Benefit &amp; Impact:</strong>
        Visible benefit immediately in daily work, momentum for further digitalization steps.
      </p>
      <p><strong>Effort &amp; Budget:</strong>
        Depends on size:
        {% if COMPANY_SIZE == "solo" %}1–3 days{% elif COMPANY_SIZE == "team" %}3–7 days{% else %}1–3 weeks including coordination{% endif %}.
      </p>
      <p><strong>Responsible:</strong>
        {% if COMPANY_SIZE == "solo" %}Owner{% elif COMPANY_SIZE == "team" %}Pilot responsible + team{% else %}Project management + functional area{% endif %}.
      </p>
    </li>

    <!-- RECOMMENDATION 5 – Governance & Security -->
    <li>
      <h3>Recommendation&nbsp;5: Governance &amp; Security</h3>
      <p><strong>Focus:</strong>
        Establish clear guidelines and controls for AI deployment to minimize risks and ensure compliance.
      </p>
      <p><strong>Action:</strong>
        Create a compact AI guideline with rules on data protection, quality review, and approval processes. Define responsibilities and escalation paths.
      </p>
      <p><strong>Benefit &amp; Impact:</strong>
        Higher legal certainty, transparent processes, and strengthened trust with customers and partners.
      </p>
      <p><strong>Effort &amp; Budget:</strong>
        {% if COMPANY_SIZE == "solo" %}Low – personal checklist in 1-2 days{% elif COMPANY_SIZE == "team" %}Medium – team workshop + documentation in 3-5 days{% else %}Medium to high – structured policy development in 2-4 weeks{% endif %}.
      </p>
      <p><strong>Responsible:</strong>
        {% if COMPANY_SIZE == "solo" %}Owner{% elif COMPANY_SIZE == "team" %}AI Owner + team lead{% else %}Governance responsible + data protection/IT{% endif %}.
      </p>
    </li>

  </ol>

  <h3>Priorities Overview</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Priority</th>
        <th>Recommendation</th>
        <th>Timeframe</th>
        <th>Main Benefit</th>
      </tr>
    </thead>
    <tbody>

      <tr>
        <td>1</td>
        <td>Introduce standard workflow for {{HAUPTLEISTUNG}}</td>
        <td>
          {% if COMPANY_SIZE == "solo" %}0–3 months{% else %}0–6 months{% endif %}
        </td>
        <td>Immediate relief & quality improvement</td>
      </tr>

      <tr>
        <td>2</td>
        <td>Establish AI-powered consistency & quality check</td>
        <td>
          {% if COMPANY_SIZE == "solo" %}3–6 months{% else %}3–9 months{% endif %}
        </td>
        <td>Less rework & lower risk</td>
      </tr>

      <tr>
        <td>3</td>
        <td>Centralize knowledge library/standards</td>
        <td>
          {% if COMPANY_SIZE == "solo" %}6–12 months{% else %}6–9 months{% endif %}
        </td>
        <td>Faster onboarding & stable results</td>
      </tr>

      <tr>
        <td>4</td>
        <td>Implement industry-specific AI pilot</td>
        <td>
          {% if COMPANY_SIZE == "kmu" %}9–12 months{% else %}6–12 months{% endif %}
        </td>
        <td>Visible benefit & momentum for scaling</td>
      </tr>

      <tr>
        <td>5</td>
        <td>Establish governance & security guidelines</td>
        <td>
          {% if COMPANY_SIZE == "solo" %}3–6 months{% else %}6–9 months{% endif %}
        </td>
        <td>Legal certainty & trust</td>
      </tr>

    </tbody>
  </table>

  <p class="small muted">
    The recommendations are formulated so they can be directly incorporated into project planning
    and work consistently with roadmap, business case, benchmarking, and quick wins.
  </p>
</section>

<!-- PLATIN+ REINFORCEMENT: This section MUST contain at least 800 words.
     Check your output: Count the words and expand each recommendation with additional
     details on actions, benefits, and effort if the minimum length is not reached.
     NEVER shorten – always deliver complete, detailed content. -->
