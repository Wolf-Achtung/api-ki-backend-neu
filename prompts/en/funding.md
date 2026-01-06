<!-- ALIAS FOR: foerderprogramme.md -->
<!-- PLATIN+++ PROMPT v7.0 - SPRINT INHALTLICHE FINALISIERUNG -->
<!-- SECTION: Funding Programmes Overview -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, kmu:1.15x=690) -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT VARS: {{FOERDERPROGRAMME_HTML}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{ZEITERSPARNIS_PRIORITAET}}, {{ki_projekte}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->

=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- [✓] Provide a compact funding overview tailored to the company size and industry.
- [✓] Insert the funding matrix via {{FOERDERPROGRAMME_HTML}} and ensure the number of programmes matches the size‑aware limits (max 3 for solo/team, max 5 for KMU).
- [✓] Include an introduction mentioning {{UNTERNEHMENSGROESSE_LABEL}} and {{BRANCHE_LABEL}}.
- [✓] State the typical funding rate (30–50 %) and, for Solo/Team, add a note directing readers to the appendix for detailed descriptions.
- [✓] Provide a “Next Step” paragraph that ties the funding overview back to the main service {{HAUPTLEISTUNG}} and encourages a compact funding check.
- [✓] Conclude with a small cautionary note about changing funding rates and deadlines.
- [✓] Maintain a single <section> element with clear headings; no German text and no tool lists.
=============================================================================

<section class="section funding">
  <h2>Funding Programmes for Your AI Project</h2>

  <p>
    As a <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> operating in the <strong>{{BRANCHE_LABEL}}</strong> sector, there are suitable funding programmes available that can make your AI initiatives more economically viable.
  </p>

  <h3>Relevant Programmes</h3>
  <!-- SIZE-AWARE: Solo/Team = max 3 programmes, KMU = max 5 programmes -->
  {{FOERDERPROGRAMME_HTML}}

  <p>
    <strong>Typical funding rate:</strong> 30–50 % of eligible costs.
    {% if COMPANY_SIZE == "solo" or COMPANY_SIZE == "team" %}
    <em>Detailed programme descriptions can be found in the appendix.</em>
    {% endif %}
  </p>

  <h3>Next Step</h3>
  <p>
    Review the programmes best suited for your AI initiative in the core process <strong>{{HAUPTLEISTUNG}}</strong> and begin with a compact funding check.
  </p>

  <p class="small muted">
    Note: Funding rates and deadlines may change; always consult the official programme documentation before submitting an application.
  </p>
</section>