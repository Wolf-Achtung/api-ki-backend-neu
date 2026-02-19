**IMPORTANT – Length limit: Your response must not exceed 1100 words. Cut rather than exceed.**

Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G17.P -->
<!-- SECTION: business_case -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{COMPANY_SIZE}}, {{HAUPTLEISTUNG}}, {{BUNDESLAND_LABEL}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}, {{OFFERING_LABEL}} -->
<!-- TOKEN-BUDGET: 1800 (solo:0.8x=1440, team:1.0x=1800, sme:1.15x=2070) -->
<!-- WORD_MINIMUM_SOLO: 130 -->
<!-- WORD_MINIMUM_TEAM: 150 -->
<!-- WORD_MINIMUM_SME: 180 -->
<!--
GOAL: Clear, realistic business case with ROI, CAPEX/OPEX.

REALISM RULES (STRICT!):
- NO 90% efficiency promises – realistic 15–30% savings
- NO made-up numbers – only use provided variables
- "around / approx. / about" for qualification allowed
- NO funding rates (see foerderpotenzial.md)
- Size influences ONLY narrative context, not the numbers

PAYBACK EXPLANATION (SIMPLIFIED):
- Simple formula: Investment ÷ monthly savings = months
- NO complex financial calculations
- Communicate assumptions transparently

ANTI-REDUNDANCY:
- Business case numbers ONCE HERE
- In foerderpotenzial.md only reference these numbers, don't repeat
- In executive_summary only mention as indication

SPRINT G18 - ANTI-REDUNDANCY (STRICT!):
- Do NOT describe data readiness again – belongs in data_readiness.md
- Maximum ONE brief reference to data readiness allowed (e.g. "→ see data readiness")
- CAPEX/OPEX blocks ONLY HERE – do not repeat in other sections
- Focus: ROI, payback, investment – NO data readiness analysis

SPRINT G18 - NARRATIVE CONNECTIONS:
- Reference starter kit: "The starter kits enable cost-efficient implementation of quick wins..."
- Reference roadmap: "Amortization already occurs in Phase 2 of the 90-day roadmap..."
- Announce funding potential: "Details on possible funding → see funding chapter"

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: personal ROI, time relief, pragmatic assessment
- team: Team ROI, shared efficiency gains
- sme: Departmental ROI, scalable effects

SPRINT N - SOLO PERSONA RULES (STRICT!):
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

<section class="section business-case">
  <h2>Business Case – Investment and Expected Value</h2>

  <!-- G17.P: New introduction without redundancy, with cross-references -->
  <p>
    For <strong>{{OFFERING_LABEL}}</strong> in the <strong>{{BRANCHE_LABEL}}</strong> industry
    a specific investment framework can be derived. The business case shows what
    setup and ongoing operational expenses are realistic and over what period they
    will amortize. The focus is on time savings, quality gains, and a
    transparent payback period. The quick wins from the roadmap additionally accelerate
    ROI → see immediate measures.
  </p>

  <h3>Investment and Ongoing Costs</h3>
  <p>
    One-time expenses for setup and introduction are around
    <strong>{{CAPEX_REALISTISCH_EUR}}&nbsp;€</strong>. Monthly operating costs
    of about <strong>{{OPEX_REALISTISCH_EUR}}&nbsp;€</strong> are added – mainly for AI usage,
    infrastructure, tools, and potential licenses.
  </p>

  <h3>Monthly Effect in Core Business</h3>
  <p>
    In daily use, a realistic relief of around
    <strong>{{EINSPARUNG_MONAT_EUR}}&nbsp;€ per month</strong> is achievable. This results from
    time gains, fewer manual loops, and more consistent result quality.
    Prerequisite is that the new workflow is consistently used in daily operations.
  </p>

  <h3>Amortization and ROI</h3>
  <p>
    <strong>Simple calculation:</strong> Investment ({{CAPEX_REALISTISCH_EUR}} €) divided by
    monthly savings ({{EINSPARUNG_MONAT_EUR}} €) yields amortization after approximately
    <strong>{{PAYBACK_MONTHS}} months</strong>. The 12-month ROI is
    <strong>{{ROI_12M}}&nbsp;%</strong> – a realistic value with consistent use.
  </p>

  <h3>Assessment by Company Size</h3>
  {% if COMPANY_SIZE == "solo" %}
  <p>
    The more <strong>{{HAUPTLEISTUNG}}</strong> relies on recurring tasks,
    the faster your investment pays off.
  </p>
  {% elif COMPANY_SIZE == "team" %}
  <p>
    The more <strong>{{HAUPTLEISTUNG}}</strong> relies on recurring tasks,
    the faster the team investment pays off.
  </p>
  {% else %}
  <p>
    The more <strong>{{HAUPTLEISTUNG}}</strong> relies on standardizable tasks,
    the faster the amortization.
  </p>
  {% endif %}

  <h3>Connection to Funding Opportunities</h3>
  <p>
    In <strong>{{BUNDESLAND_LABEL}}</strong> funding programs exist for AI projects.
    Funding shortens the amortization period. Details → see funding chapter.
  </p>

  <h3>Additional Revenue Potentials</h3>
  <p>
    Beyond efficiency gains, AI processes offer revenue potentials:
  </p>
  <ul>
    <li>Digital products (automated analyses, reports)</li>
    <li>New service formats (workshops, consulting)</li>
    <li>Scalable offerings</li>
  </ul>

  <p class="small muted">
    These values are based on typical experience for {{BRANCHE_LABEL}} companies.
    Actual results depend on usage intensity and process maturity.
  </p>
</section>

<!-- OUTPUT GUIDELINES:
     - Respond only with the HTML fragment above.
     - No additional comments or explanations.
     - Total length ≤ 2,400 characters.
-->
