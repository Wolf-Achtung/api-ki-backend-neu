<!-- ALIAS FOR: foerderpotenzial.md -->
<!-- PLATIN+++ PROMPT v6.0 - FUNDING POTENTIAL (Germany) -->
<!-- SECTION: funding_potential -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- TOKEN-BUDGET: 3200 (solo:0.8x=2560, team:1.0x=3200, kmu:1.15x=3680) -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT: {{BUNDESLAND_LABEL}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}, COMPANY_SIZE, {{VISION_3_JAHRE}}, {{KI_GUARDRAILS}} -->

=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- [✓] Write four sections (1. Business Case without Funding, 2. How Funding Improves the Case, 3. Relevant Funding Focus Areas, 4. Next Steps for Assessment) with 180–220 words each. Each section must include an introductory sentence, a bullet list of 3–5 items, and an optional concluding sentence.
- [✓] Avoid long paragraphs (no more than 3 sentences per paragraph). After each paragraph, use a blank line or a bullet list. No wall of text (>80 words per paragraph).
- [✓] Do not repeat business case numbers multiple times; summarise the CAPEX, OPEX, savings and ROI once and then focus on funding context.
- [✓] Provide funding ranges as percentages (e.g., "30–50%"), use a factual and neutral tone, and avoid marketing language.
- [✓] Tailor content to company size:
  * **Solo:** highlight low barriers and small budgets (<€10k); reference consulting and starter grants (BAFA, ERP start-up loans). Avoid terms like "team", "department" or "employees"; use "capacity" and "resources" instead.
  * **Team (2–10):** focus on process digitalisation, SME‑innovative and go‑digital programs; mention collaboration and team efficiency.
  * **KMU (11–100):** emphasise larger programs such as ZIM and KfW digitalisation loans; address structural funding and potential for pilot projects.
- [✓] Mention connections to recommended tools and starter kits where appropriate, and align with the phases of the 90‑day roadmap and the company’s 3‑year vision. Ensure the section on funding focus areas reflects {{HAUPTLEISTUNG}} and {{BRANCHE_LABEL}}.
- [✓] Conclude with a neutral note that funding rates and requirements may change and advise readers to check official guidelines before applying.
=============================================================================

<section class="section funding-potential">
  <h2>Funding Potential for Your AI Project</h2>

  <p>
    Companies in the <strong>{{BRANCHE_LABEL}}</strong> sector located in <strong>{{BUNDESLAND_LABEL}}</strong> and classified as <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> pursuing projects related to <strong>{{HAUPTLEISTUNG}}</strong> often meet the prerequisites for German federal and state funding. Below is a structured analysis of your funding potential.
  </p>

  <h3>1. Business Case Without Funding</h3>
  <p><strong>The project is economically viable even without external funding:</strong></p>
  <ul>
    <li><strong>Investment level:</strong> One‑time CAPEX of {{CAPEX_REALISTISCH_EUR}} € and ongoing costs of {{OPEX_REALISTISCH_EUR}} €/month represent a manageable budget for {{UNTERNEHMENSGROESSE_LABEL}}.</li>
    <li><strong>Payback:</strong> With monthly savings of {{EINSPARUNG_MONAT_EUR}} €, payback is achievable in around {{PAYBACK_MONTHS}} months.</li>
    <li><strong>Risk profile:</strong> The project involves a modular approach, limiting downside risk for the {{BRANCHE_LABEL}} sector.</li>
    <li><strong>Self‑financing:</strong> The business case is sustainable from existing operations, meaning funding is an improvement rather than a requirement.</li>
  </ul>
  <p>The baseline ROI of {{ROI_12M}}% is attractive; funding can further enhance this position.</p>

  <h3>2. How Funding Can Improve Your Business Case</h3>
  <p>
    Federal and regional programmes in {{BUNDESLAND_LABEL}} support AI and digitalisation initiatives by subsidising a portion of eligible investment costs. Typical grant rates range between <strong>30–50%</strong>, depending on programme, company size and project focus.
  </p>
  <ul>
    <li><strong>Shortened payback:</strong> Co‑financing reduces the self‑contribution and shortens the payback period.</li>
    <li><strong>Enhanced ROI:</strong> A lower net investment improves the overall economics — details in the Business Case section.</li>
    <li><strong>Reduced financial risk:</strong> Grants enable more ambitious projects without straining liquidity.</li>
    <li><strong>Capacity for upskilling:</strong> Savings free up budget for training and capacity building, aligning with your {{VISION_3_JAHRE}}.</li>
    <li><strong>Improved planning security:</strong> Approved funding allows more reliable budget planning and absorption of unexpected costs.</li>
  </ul>

  <h3>3. Relevant Funding Focus Areas</h3>
  <p>
    Based on your industry <strong>{{BRANCHE_LABEL}}</strong>, core service <strong>{{HAUPTLEISTUNG}}</strong> and company size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>, the following funding categories are particularly relevant:
  </p>
  <ul>
    <li><strong>Digitalisation funding:</strong> Programs for AI‑supported process optimisation, automation and digital tools – especially pertinent for {{HAUPTLEISTUNG}}.</li>
    <li><strong>Innovation funding:</strong> Grants for novel AI applications, pilot projects and technology development tailored to {{BRANCHE_LABEL}}.</li>
    <li><strong>Training funding:</strong> Resources for education and building AI competencies to support sustainable adoption.</li>
    <li><strong>Consulting funding:</strong> Support for external expertise in AI strategy and implementation.
      {% if COMPANY_SIZE == "solo" %}
      Starter grants such as BAFA or ERP loans reduce the entry barrier for individual founders.
      {% elif COMPANY_SIZE == "team" %}
      Programmes like SME‑innovativ or go‑digital focus on process digitalisation for growing teams.
      {% else %}
      Larger programmes (e.g. ZIM, KfW Digitalisation) support structural projects and scaling efforts.
      {% endif %}
    </li>
  </ul>

  <h3>4. Next Steps for Funding Assessment</h3>
  <ol>
    <li><strong>Programme selection:</strong> Identify 1–2 programmes that match <strong>{{BRANCHE_LABEL}}</strong>, <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> and <strong>{{HAUPTLEISTUNG}}</strong>.</li>
    <li><strong>Project description:</strong> Document goals, measures, timeline and anticipated benefits, referencing {{CAPEX_REALISTISCH_EUR}} € and {{OPEX_REALISTISCH_EUR}} €/month.</li>
    <li><strong>Combination check:</strong> Clarify whether regional programmes can be combined with federal schemes; EU programmes are out of scope here.</li>
    <li><strong>Seek advice:</strong> Consider consulting funding advisors, chambers of commerce or local economic development agencies.</li>
    <li><strong>Timeline planning:</strong> Allow 4–8 weeks lead time for funding applications and coordinate this with your 90‑day roadmap.
    </li>
  </ol>

  <p class="small muted">
    Note: Funding rates, deadlines and programme requirements may change. Always review the official guidelines before submitting an application.
  </p>
</section>