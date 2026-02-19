**IMPORTANT – Length limit: Your response must not exceed 1100 words. Cut rather than exceed.**

<!-- PLATIN+++ PROMPT v7.1 - SPRINT INHALTLICHE FINALISIERUNG -->
<!-- SECTION: Technology & Processes -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- TOKEN-BUDGET: 800 (solo:0.8x=640, team:1.0x=800, kmu:1.15x=920) -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT VARS: COMPANY_SIZE, {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->

=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- [✓] Provide a concise overview of the underlying report generation architecture.
- [✓] Structure your output into four sections: introduction, system architecture (table), data flows & integrations (ordered list), quality assurance (bullet list).
- [✓] For team and KMU contexts include paragraphs on operations & scaling, and data security & compliance.
- [✓] Focus on process chains and decision points, not lists of tools.
- [✓] Respect persona-specific privacy and compliance guidelines according to COMPANY_SIZE.
- [✓] Write in clear, professional English. Use 2–4 sentences per paragraph and avoid filler text.
=============================================================================

<section class="section technology-processes">
  <h2>Technology & Processes</h2>

  <p>
    The data flow from questionnaire to finished PDF report follows a multi‑layer architecture designed for reliability and compliance. This overview focuses on the process chain and key decision points rather than specific tools.
  </p>

  <h3>System Architecture</h3>
  <table class="table">
    <thead>
      <tr><th>Layer</th><th>Function</th></tr>
    </thead>
    <tbody>
      <tr><td>Frontend</td><td>User questionnaire capture, validation, autosave and submission</td></tr>
      <tr><td>Backend</td><td>Prompt orchestration, report builder and business case logic</td></tr>
      <tr><td>AI/Analysis</td><td>Multi‑layer prompt analysis, research integration and industry context injection</td></tr>
      <tr><td>PDF Service</td><td>HTML→PDF rendering, layout optimisation and branding</td></tr>
      <tr><td>Delivery</td><td>Secure email delivery, archiving and tracking</td></tr>
    </tbody>
  </table>

  <h3>Data Flows &amp; Integrations</h3>
  <ol>
    <li>Questionnaire completion with autosave and interim storage</li>
    <li>Submission triggers validation and secure storage in the database</li>
    <li>Prompt engine injects industry, size and persona context</li>
    <li>AI generates the report sections (Executive Summary, 90‑day roadmap, risks, business case, etc.)</li>
    <li>Business case logic calculates CAPEX/OPEX/ROI based on user inputs</li>
    <li>Validator checks HTML quality, consistency and persona compliance</li>
    <li>PDF service renders the final report with corporate layout</li>
    <li>Secure delivery via email and archiving with delivery confirmation</li>
  </ol>

  <h3>Quality Assurance</h3>
  <ul>
    <li>Automatic consistency checks of all report sections prior to PDF creation</li>
    <li>Size‑mismatch detection ensures that solo, team and KMU specific content is validated</li>
    <li>Plausibility checks for business case numbers (ROI, payback period, CAPEX)</li>
    <li>Template text recognition ensures no placeholders remain in the final report</li>
  </ul>

  {% if COMPANY_SIZE == "team" or COMPANY_SIZE == "kmu" %}
  <h3>Operations &amp; Scaling</h3>
  <p>
    The architecture is built for parallel report generation. European hosting ensures GDPR compliance. Ongoing monitoring tracks latency and error rates to support continuous improvement and scalability.
  </p>

  <h3>Data Security &amp; Compliance</h3>
  <p>
    {% if COMPANY_SIZE == "team" %}
    Define clear rules about which data types may be used in AI tools. A central guideline for all team members prevents unintentional data protection violations and ensures legal certainty.
    {% else %}
    Integrate AI usage guidelines into existing data protection processes. Regular audits of tools and data flows ensure compliance. Document processing activities in accordance with Art. 30 GDPR.
    {% endif %}
  </p>
  {% endif %}

  {% if COMPANY_SIZE == "solo" %}
  <h3>Data Security &amp; Compliance</h3>
  <p>
    Use only GDPR‑compliant tools with EU data processing. Avoid entering sensitive customer data into AI systems without prior anonymisation or explicit consent.
  </p>
  {% endif %}

  <p class="small muted">
    This architecture ensures traceable, quality‑assured reports and forms the backbone for reliable AI‑assisted decision support.
  </p>
</section>