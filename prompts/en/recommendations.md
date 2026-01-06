<!-- PLATIN+++ PROMPT v7.1 - SPRINT FINALIZATION -->
<!-- SECTION: recommendations -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE‑AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE, {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->
<!-- TOKEN‑BUDGET: 1200 (solo:0.8x=960, team:1.0x=1200, sme:1.15x=1380) -->
<!--
=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- 3–5 concrete, actionable recommendations
- Each recommendation includes: What, Why, How, When
- Priority labeling: Must‑Do, Should‑Do, Nice‑to‑Have
- Effort estimation: Quick win / Medium / Long‑term
- Risk flagging: What could go wrong?
- Success metrics: How to measure impact?
=============================================================================

INDIVIDUALIZATION CONTEXT:
- {{hauptleistung}} – The user’s core service/product
- {{ZEITERSPARNIS_PRIORITAET}} – The biggest time drain for the user
- {{KI_GUARDRAILS}} – Restrictions/No‑Gos for AI usage
- {{VISION_3_JAHRE}} – 3‑year vision of the user

Rules:
- Use the personalization context in each recommendation.
- Avoid generic advice; tie actions directly to {{hauptleistung}} and
  {{ZEITERSPARNIS_PRIORITAET}}.
- Respect {{KI_GUARDRAILS}} and align recommendations with {{VISION_3_JAHRE}}.
- Follow persona hard‑guards: no team language in solo mode, etc.
- Keep sentences concise (max. 18–22 words) and avoid jargon like
  “fundamental”, “holistic” or “exponential”.
-->

<section class="section recommendations">
  <h2>Recommendations</h2>

  <p>
    For {{BRANCH_CONTEXT_LABEL}}, the following prioritized recommendations apply to
    <strong>{{OFFERING_LABEL}}</strong>. These actions are designed to relieve
    <strong>{{ZEITERSPARNIS_PRIORITAET}}</strong>, strengthen your core
    offering {{hauptleistung}} and move you towards your
    <strong>{{VISION_3_JAHRE}}</strong>, while respecting your
    {{KI_GUARDRAILS}}.
  </p>

  <!-- SECTION 1: MUST‑DO RECOMMENDATIONS (exactly 3) -->
  <h3>Must‑Do Recommendations</h3>
  <ol class="recommendations-must">
    <li>
      <h4>Recommendation 1: [Title – max 8 words]</h4>
      <p><strong>Priority:</strong> Must‑Do</p>
      <p><strong>Effort:</strong> [Quick Win/Medium/Long‑term]</p>
      <p><strong>Impact:</strong> [High/Medium/Low]</p>
      <p><strong>What:</strong> [Concrete action addressing {{ZEITERSPARNIS_PRIORITAET}}]</p>
      <p><strong>Why:</strong> [Business case tied to {{VISION_3_JAHRE}}]</p>
      <p><strong>How:</strong> [Implementation steps referencing {{hauptleistung}} and
        {{KI_GUARDRAILS}}]</p>
      <p><strong>When:</strong> [Timeframe, e.g. immediately, Month 1–2]</p>
      <p><strong>Risk:</strong> [Potential challenges, consider {{KI_GUARDRAILS}}]</p>
      <p><strong>Success Metric:</strong> [How to measure impact]</p>
    </li>
    <li>
      <h4>Recommendation 2: [Title – max 8 words]</h4>
      <p><strong>Priority:</strong> Must‑Do</p>
      <p><strong>Effort:</strong> [Quick Win/Medium/Long‑term]</p>
      <p><strong>Impact:</strong> [High/Medium/Low]</p>
      <p><strong>What:</strong> [Concrete action optimizing {{hauptleistung}}]</p>
      <p><strong>Why:</strong> [Reason this improves your core service]</p>
      <p><strong>How:</strong> [Process steps for {{OFFERING_LABEL}}]</p>
      <p><strong>When:</strong> [Timeframe]</p>
      <p><strong>Risk:</strong> [Challenges and mitigations]</p>
      <p><strong>Success Metric:</strong> [Measurement approach]</p>
    </li>
    <li>
      <h4>Recommendation 3: [Title – max 8 words]</h4>
      <p><strong>Priority:</strong> Must‑Do</p>
      <p><strong>Effort:</strong> [Quick Win/Medium/Long‑term]</p>
      <p><strong>Impact:</strong> [High/Medium/Low]</p>
      <p><strong>What:</strong> [Quality or risk measure matching {{KI_GUARDRAILS}}]</p>
      <p><strong>Why:</strong> [Reason this minimizes risk or ensures quality]</p>
      <p><strong>How:</strong> [Checklist or approval process]</p>
      <p><strong>When:</strong> [Timeframe]</p>
      <p><strong>Risk:</strong> [What could go wrong if not implemented]</p>
      <p><strong>Success Metric:</strong> [How to track risk reduction]</p>
    </li>
  </ol>

  <!-- SECTION 2: OPTIONS (additional 2‑3 recommendations for later phases) -->
  <h3>Options – Phase 2/3</h3>
  <ul class="recommendations-options">
    <li>
      <strong>[Title – e.g. Build Knowledge Management]</strong> – Central library for templates and best practices.
      <span class="option-timing">{% if COMPANY_SIZE == "solo" %}From Month 3{% else %}From Month 4–6{% endif %}</span>
    </li>
    <li>
      <strong>[Title – e.g. Expand Pilot Use Case]</strong> – Visible success for further use cases.
      <span class="option-timing">{% if COMPANY_SIZE == "solo" %}From Month 6{% else %}From Month 6–9{% endif %}</span>
    </li>
    <li>
      <strong>[Title – e.g. Formalize Governance]</strong> – {% if COMPANY_SIZE == "solo" %}Personal checklist{% elif COMPANY_SIZE == "team" %}Team guideline{% else %}Policy document{% endif %} for AI use.
      <span class="option-timing">{% if COMPANY_SIZE == "solo" %}From Month 3{% else %}From Month 6{% endif %}</span>
    </li>
  </ul>

  <h3>Priorities Overview</h3>
  <table class="table">
    <thead>
      <tr><th>Priority</th><th>Recommendation</th><th>Effort</th><th>Main Benefit</th></tr>
    </thead>
    <tbody>
      <tr><td><strong>Must</strong></td><td>[Short form of Recommendation 1]</td><td>[Quick Win/Medium/Long]</td><td>[Key benefit, e.g. Time Savings]</td></tr>
      <tr><td><strong>Must</strong></td><td>[Short form of Recommendation 2]</td><td>[Quick Win/Medium/Long]</td><td>[Key benefit, e.g. Quality Improvement]</td></tr>
      <tr><td><strong>Must</strong></td><td>[Short form of Recommendation 3]</td><td>[Quick Win/Medium/Long]</td><td>[Key benefit, e.g. Risk Reduction]</td></tr>
      <tr><td>Option</td><td>Knowledge Management</td><td>{% if COMPANY_SIZE == "solo" %}Month 3+{% else %}Month 4–6{% endif %}</td><td>Stable Results</td></tr>
      <tr><td>Option</td><td>Expand Pilot Use Case</td><td>{% if COMPANY_SIZE == "solo" %}Month 6+{% else %}Month 6–9{% endif %}</td><td>Visible Success</td></tr>
      <tr><td>Option</td><td>Formalize Governance</td><td>{% if COMPANY_SIZE == "solo" %}Month 3+{% else %}Month 6+{% endif %}</td><td>Legal Certainty</td></tr>
    </tbody>
  </table>

  <!-- PERSONA HARD‑GUARDS: adjust language per COMPANY_SIZE -->
  <!-- SOLO MODE: avoid team or department language -->
  <!-- TEAM MODE: avoid corporate terms and solo terms -->
  <!-- SME MODE: avoid corporate terms and solo terms -->

</section>