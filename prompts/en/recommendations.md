Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: recommendations -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, kmu:1.15x=690) -->
<!--
GOAL: 5 strategic recommendations for {{HAUPTLEISTUNG}}.

STRUCTURE (Required elements):
1. Brief introduction (30-40 words)
2. EXACTLY 5 recommendations, each with:
   - Focus (1 sentence)
   - Action (1-2 sentences)
   - Benefit (1 sentence)
   - Effort (1 sentence, size-aware)
3. Compact priorities table (5 rows)

ANTI-REDUNDANCY (STRICT!):
- NO repetition of Quick Wins (already covered there)
- NO repetition of Roadmap content
- Focus on COMPLEMENTARY strategic recommendations

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: Owner, personal steps, low budget
- team: Team lead/AI Owner, shared workflows, medium budget
- kmu: Departments, governance, structured investments
-->

<section class="section recommendations">
  <h2>Recommendations</h2>

  <p>
    For <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in the <strong>{{BRANCHE_LABEL}}</strong> industry,
    the following strategic recommendations apply for <strong>{{HAUPTLEISTUNG}}</strong>.
  </p>

  <ol class="recommendations-list">

    <li>
      <h3>Recommendation 1: Establish Standard Workflow</h3>
      <p><strong>Focus:</strong> Build a central AI-powered workflow for {{HAUPTLEISTUNG}}.</p>
      <p><strong>Action:</strong> Define clear input/output rules, integrate quality check.</p>
      <p><strong>Benefit:</strong> Direct relief, consistent results.</p>
      <p><strong>Effort:</strong> {% if COMPANY_SIZE == "solo" %}1-2 days{% elif COMPANY_SIZE == "team" %}3-5 days{% else %}1-2 weeks{% endif %}.</p>
    </li>

    <li>
      <h3>Recommendation 2: Systematize Quality Assurance</h3>
      <p><strong>Focus:</strong> AI-powered consistency check for documents and outputs.</p>
      <p><strong>Action:</strong> Introduce review step before approval (facts, tone, compliance).</p>
      <p><strong>Benefit:</strong> Less rework, lower error risk.</p>
      <p><strong>Effort:</strong> {% if COMPANY_SIZE == "solo" %}1-2 days{% elif COMPANY_SIZE == "team" %}3-5 days{% else %}1-2 weeks{% endif %}.</p>
    </li>

    <li>
      <h3>Recommendation 3: Build Knowledge Management</h3>
      <p><strong>Focus:</strong> Central knowledge base for templates, standards, best practices.</p>
      <p><strong>Action:</strong> Create AI-powered library for recurring materials.</p>
      <p><strong>Benefit:</strong> Faster onboarding, stable result quality.</p>
      <p><strong>Effort:</strong> {% if COMPANY_SIZE == "solo" %}2-3 days{% elif COMPANY_SIZE == "team" %}1 week{% else %}2-3 weeks{% endif %}.</p>
    </li>

    <li>
      <h3>Recommendation 4: Pilot Industry-Specific Use Case</h3>
      <p><strong>Focus:</strong> One clearly defined pilot use case from {{BRANCHE_LABEL}}.</p>
      <p><strong>Action:</strong> Implement a use case with high visibility and quick ROI.</p>
      <p><strong>Benefit:</strong> Visible success, momentum for further steps.</p>
      <p><strong>Effort:</strong> {% if COMPANY_SIZE == "solo" %}1-3 days{% elif COMPANY_SIZE == "team" %}3-7 days{% else %}1-3 weeks{% endif %}.</p>
    </li>

    <li>
      <h3>Recommendation 5: Define Governance & Guidelines</h3>
      <p><strong>Focus:</strong> Clear rules for AI usage, data protection, approvals.</p>
      <p><strong>Action:</strong> Create {% if COMPANY_SIZE == "solo" %}personal checklist{% elif COMPANY_SIZE == "team" %}team guideline{% else %}policy document{% endif %}.</p>
      <p><strong>Benefit:</strong> Legal certainty, customer trust.</p>
      <p><strong>Effort:</strong> {% if COMPANY_SIZE == "solo" %}1-2 days{% elif COMPANY_SIZE == "team" %}3-5 days{% else %}2-4 weeks{% endif %}.</p>
    </li>

  </ol>

  <h3>Priorities Overview</h3>
  <table class="table">
    <thead>
      <tr><th>Priority</th><th>Recommendation</th><th>Timeframe</th><th>Main Benefit</th></tr>
    </thead>
    <tbody>
      <tr><td>1</td><td>Standard Workflow</td><td>{% if COMPANY_SIZE == "solo" %}0–3 mo.{% else %}0–6 mo.{% endif %}</td><td>Relief & Quality</td></tr>
      <tr><td>2</td><td>Quality Assurance</td><td>{% if COMPANY_SIZE == "solo" %}3–6 mo.{% else %}3–9 mo.{% endif %}</td><td>Less Rework</td></tr>
      <tr><td>3</td><td>Knowledge Management</td><td>{% if COMPANY_SIZE == "solo" %}6–12 mo.{% else %}6–9 mo.{% endif %}</td><td>Stable Results</td></tr>
      <tr><td>4</td><td>Pilot Use Case</td><td>{% if COMPANY_SIZE == "kmu" %}9–12 mo.{% else %}6–12 mo.{% endif %}</td><td>Visible Success</td></tr>
      <tr><td>5</td><td>Governance</td><td>{% if COMPANY_SIZE == "solo" %}3–6 mo.{% else %}6–9 mo.{% endif %}</td><td>Legal Certainty</td></tr>
    </tbody>
  </table>
</section>
