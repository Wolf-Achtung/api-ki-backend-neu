**IMPORTANT – Length limit: Your response must not exceed 1200 words. Cut rather than exceed.**

<!-- PLATIN++ PROMPT v5.4 - Funding Potential (Germany) -->
<!-- SECTION: funding_potential -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- TOKEN-BUDGET: 3200 (solo:0.8x=2560, team:1.0x=3200, sme:1.15x=3680) -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT: {{BUNDESLAND_LABEL}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}, COMPANY_SIZE, {{VISION_3_JAHRE}}, {{KI_GUARDRAILS}} -->

<!--
=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- [✓] 4 sections (1. Business Case without Funding, 2. How Funding Improves,
      3. Relevant Funding Focus Areas, 4. Next Steps for Assessment)
      with 180-220 words each. Per section: intro sentence, bullet list (3-5 points),
      optional closing sentence
- [✓] Avoid long paragraphs (max 3 sentences). After each paragraph:
      blank line or bullet list. No text walls (>80 words/paragraph)
- [✓] Do NOT repeat business case numbers throughout – summarize CAPEX, OPEX,
      savings, ROI once and focus on funding context
- [✓] Funding ranges as percentages (e.g. "30-50%"), factual neutral tone,
      avoid marketing language
- [✓] Size-specific focus:
      * Solo: Low barriers, small budgets (<10k), consulting & starter grants (BAFA, ERP start loans)
        Vocabulary: No "team", "department", "employees" → "capacity", "resources"
      * Team (2-10): Process digitization, SME-innovativ, go-digital, team efficiency
      * SME (11-100): Larger programs (ZIM, KfW digitization), structural funding, pilot projects
- [✓] Mention connections to recommended tools and starter kit,
      alignment with 90-day roadmap phases and 3-year vision
- [✓] Conclude with neutral note that funding rates & requirements may change;
      refer to official guidelines before application
=============================================================================
-->

<section class="section funding-potential">
  <h2>Funding Potential for Your AI Project</h2>

  <p>
    Companies in the <strong>{{BRANCHE_LABEL}}</strong> industry in <strong>{{BUNDESLAND_LABEL}}</strong>
    with the classification <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    and project focus <strong>{{HAUPTLEISTUNG}}</strong>
    often meet the prerequisites for German federal and state funding programs.
    Below is a structured assessment of your funding potential.
  </p>

  <h3>1. Business Case Without Funding</h3>
  <p><strong>The project is economically viable even without external funding:</strong></p>
  <ul>
    <li>
      <strong>Investment amount:</strong> One-time CAPEX of {{CAPEX_REALISTISCH_EUR}} €
      plus ongoing costs of {{OPEX_REALISTISCH_EUR}} €/month represent a manageable budget
      for {{UNTERNEHMENSGROESSE_LABEL}}.
    </li>
    <li>
      <strong>Amortization:</strong> With monthly savings of {{EINSPARUNG_MONAT_EUR}} €,
      amortization is achievable in approximately {{PAYBACK_MONTHS}} months.
    </li>
    <li>
      <strong>Risk profile:</strong> The project involves a modular approach
      that limits downside risk for the {{BRANCHE_LABEL}} industry.
    </li>
    <li>
      <strong>Self-financing:</strong> The business case is sustainable from existing operations,
      meaning funding is an enhancement rather than a prerequisite.
    </li>
  </ul>
  <p>
    The baseline ROI of {{ROI_12M}}% is attractive;
    funding can further improve this position.
  </p>

  <h3>2. How Funding Improves Your Business Case</h3>
  <p>
    Federal and state programs in {{BUNDESLAND_LABEL}} support AI and digitization initiatives
    by co-financing a portion of eligible investment costs.
    Typical grant rates are between <strong>30-50%</strong>,
    depending on program, company size, and project focus.
  </p>
  <ul>
    <li>
      <strong>Shorter amortization:</strong> Co-financing reduces the self-contribution
      and shortens the amortization period to below {{PAYBACK_MONTHS}} months.
    </li>
    <li>
      <strong>Higher ROI:</strong> A lower net investment improves the overall economics — details in the Business Case section.
    </li>
    <li>
      <strong>Lower financial risk:</strong> Grants enable more ambitious projects
      without straining liquidity.
    </li>
    <li>
      <strong>Budget for training:</strong> Savings free up capacity for
      training and skill development, aligned with your {{VISION_3_JAHRE}}.
    </li>
    <li>
      <strong>Improved planning certainty:</strong> Approved funding enables
      more reliable budget planning and absorption of unexpected costs.
    </li>
  </ul>

  <h3>3. Relevant Funding Focus Areas</h3>
  <p>
    Based on your industry <strong>{{BRANCHE_LABEL}}</strong>, main service <strong>{{HAUPTLEISTUNG}}</strong>,
    and company size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>,
    the following funding categories are particularly relevant:
  </p>
  <ul>
    <li>
      <strong>Digitization funding:</strong> Programs for AI-supported process optimization,
      automation, and digital tools – especially suitable for {{HAUPTLEISTUNG}}.
    </li>
    <li>
      <strong>Innovation funding:</strong> Grants for novel AI applications,
      pilot projects, and technology development in {{BRANCHE_LABEL}}.
    </li>
    <li>
      <strong>Training funding:</strong> Funds for education and AI competency building
      to ensure sustainable adoption.
    </li>
    <li>
      <strong>Consulting funding:</strong> Support for external expertise
      in AI strategy and implementation.
      {% if COMPANY_SIZE == "solo" %}
      Starter grants like BAFA or ERP loans reduce the entry barrier for solo founders.
      {% elif COMPANY_SIZE == "team" %}
      Programs like SME-innovativ or go-digital focus on process digitization for growing teams.
      {% else %}
      Larger programs (e.g., ZIM, KfW Digitization) support structural projects and scaling.
      {% endif %}
    </li>
  </ul>

  <h3>4. Next Steps for Funding Assessment</h3>
  <ol>
    <li>
      <strong>Program selection:</strong> Identify 1-2 programs
      that match <strong>{{BRANCHE_LABEL}}</strong>, <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>,
      and <strong>{{HAUPTLEISTUNG}}</strong>.
    </li>
    <li>
      <strong>Project description:</strong> Document objectives, measures, timeline, and expected benefits
      with reference to {{CAPEX_REALISTISCH_EUR}} € and {{OPEX_REALISTISCH_EUR}} €/month.
    </li>
    <li>
      <strong>Combination check:</strong> Clarify whether regional programs
      can be combined with federal programs; EU programs are out of scope here.
    </li>
    <li>
      <strong>Seek advice:</strong> Consider funding advisors, chambers of commerce,
      or local economic development agencies.
    </li>
    <li>
      <strong>Timeline planning:</strong> Allow 4-8 weeks lead time for funding applications
      and coordinate with your 90-day roadmap.
    </li>
  </ol>

  <p class="small muted">
    Note: Funding rates, deadlines, and program requirements may change.
    Always check the official guidelines before application.
  </p>
</section>

<!-- SPRINT G18 - ANTI-REDUNDANCY (STRICT!):
- Business case numbers ONLY ONCE HERE – do not repeat
- Reference to business_case.md for detailed ROI explanation
- Maximum ONE brief mention "→ see Business Case for detailed calculation"
- Funding focus ONLY HERE – do not repeat in other sections
-->

<!-- SPRINT G18 - NARRATIVE CONNECTIONS:
- Reference roadmap: "Funding applications align with Phase 1 of the 90-day roadmap..."
- Reference tools: "Investments in starter kit tools can be partially funded..."
- Reference training: "Training measures are often eligible for separate funding..."
-->

<!-- SPRINT N - SOLO PERSONA RULES (STRICT!):
{% if COMPANY_SIZE == "solo" %}
DO NOT USE for solo:
- "build team" → instead: "expand capacity"
- "employees" → instead: "resources" or "external support"
- "teams" → instead: "capacities"
- "department" → instead: "work area"
- "division" → instead: "work area"
Use formulations without team/department concepts!
{% endif %}
-->

<!-- ZERO-LEAK POLICY (N4.6) -->
<!--
FORBIDDEN – NEVER USE:
- No questions to the reader ("Do you have questions?", "Would you like to learn more?")
- No prompts ("If you would like...", "Contact us...")
- No assistant language ("I can help you...", "I'm happy to explain...")
- No offers ("If needed...", "If desired...")
- No interactive elements ("Click here...", "Select...")
- No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
- No meta-comments ("This section...", "In the following...")

The output is a FINAL REPORT SECTION, not a conversation.
-->
