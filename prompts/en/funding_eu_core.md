<!-- PLATIN+++ PROMPT v6.0 - EU CORE FUNDING OVERVIEW -->
<!-- SECTION: eu_core_funding -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- TOKEN-BUDGET: 500 (solo:0.8x=400, team:1.0x=500, kmu:1.15x=575) -->
<!-- INPUT: {{BRANCH_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{COMPANY_SIZE}}, {{BRANCH_SHORT_LABEL}}, {{BUNDESLAND}}, {{HAUPTLEISTUNG}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->

=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- [✓] Provide a concise overview of core EU funding programmes relevant for AI and digital transformation.
- [✓] Include between 3 and 5 programmes depending on company size (solo/team ≤ 3; SME up to 5) and industry relevance.
- [✓] For each programme, provide the official name, issuing body, typical funding rate, maximum grant amount, eligibility notes and one sentence on alignment with {{HAUPTLEISTUNG}}.
- [✓] Use full programme names (e.g. “Horizon Europe – Digital Technologies”, “Digital Europe Programme”, “EIC Accelerator”) and avoid generic labels.
- [✓] Mention that EU programmes often require co‑financing and consortium participation; point to national contact points for detailed guidance.
- [✓] Conclude with a note reminding the reader to verify current deadlines and eligibility criteria.
- [✓] Avoid marketing language, placeholders or invented programme names. Use HTML structure only (<section>, <h2–h3>, <p>, <ul>, <li>, <strong>, <em>). No variables inside programme descriptions.
=============================================================================

<section class="section funding-eu-core">
  <h2>Core EU Funding Programmes</h2>

  <p>
    The European Union offers several flagship programmes that support digital transformation and AI initiatives across member states. As a <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in the <strong>{{BRANCH_LABEL}}</strong> sector, you may benefit from these opportunities to accelerate your AI projects.
  </p>

  <h3>Relevant Programmes</h3>
  <ul>
    <li>
      <strong>Horizon Europe – Cluster 4 (Digital, Industry &amp; Space)</strong><br>
      Funding body: European Commission. Supports research and innovation actions in AI, data and robotics. Typical funding rate: 70 %–100 % depending on project type. Maximum grant: varies; often €2–3 million. Aligns with your ambitions to develop advanced AI capabilities in {{HAUPTLEISTUNG}}.
    </li>
    <li>
      <strong>Digital Europe Programme – AI &amp; Data Spaces</strong><br>
      Funding body: European Commission. Focuses on the deployment of AI and the creation of common European data spaces. Funding rate: 50 %–75 %. Grants up to €2 million. Suitable for projects implementing AI infrastructure or participating in sector‑specific data spaces.
    </li>
    <li>
      <strong>EIC Accelerator</strong><br>
      Funding body: European Innovation Council. Provides blended finance (grant + equity) for breakthrough innovations. Grants cover 70 % of project costs up to €2.5 million, with potential equity investments. Best suited for high‑risk, high‑impact AI products with significant market potential.
    </li>
    {% if COMPANY_SIZE == "team" or COMPANY_SIZE == "kmu" %}
    <li>
      <strong>Innovation Fund – Small Projects</strong><br>
      Funding body: Innovation Fund. Supports projects that reduce greenhouse gas emissions, including AI solutions in manufacturing and energy management. Funding rate up to 60 %. Grants up to €7.5 million. Relevant if your AI project contributes to sustainability goals in {{BRANCH_LABEL}}.
    </li>
    {% endif %}
    {% if COMPANY_SIZE == "kmu" %}
    <li>
      <strong>Eurostars</strong><br>
      Funding bodies: EUREKA network and national agencies. Provides funding for innovative SMEs collaborating on R&amp;D projects. Funding rates and amounts vary by country; typically 50 %–70 % of project costs up to €1 million. Suitable for consortia developing AI‑enabled products or services.
    </li>
    {% endif %}
  </ul>

  <p>
    Note that EU programmes usually require co‑financing and, in many cases, collaboration with partners from other member states. Deadlines and calls vary throughout the year; consult the official portals or your national contact point to confirm current opportunities and eligibility.
  </p>
</section>
