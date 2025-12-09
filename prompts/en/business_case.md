Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G17.P -->
<!-- SECTION: business_case -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{COMPANY_SIZE}}, {{HAUPTLEISTUNG}}, {{BUNDESLAND_LABEL}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}} -->
<!-- TOKEN-BUDGET: 1800 (solo:0.8x=1440, team:1.0x=1800, sme:1.15x=2070) -->
<!--
GOAL: Clear, realistic Business Case with ROI, CAPEX/OPEX.

REALISM RULES (STRICT!):
- NO 90% efficiency promises – realistic 15–30% savings
- NO invented numbers – use only provided variables
- "approximately / around / roughly" allowed for context
- NO funding rates (see foerderpotenzial.md)
- Size affects ONLY narrative context, not the numbers

PAYBACK EXPLANATION (SIMPLIFIED):
- Simple formula: Investment ÷ monthly savings = months
- NO complex financial calculations
- Communicate transparent assumptions

ANTI-REDUNDANCY:
- Business Case numbers stated ONCE HERE
- In foerderpotenzial.md only reference these numbers, don't repeat
- In executive_summary only mention as hint

SPRINT G18 - ANTI-REDUNDANCY (STRICT!):
- DO NOT describe data situation/Data Readiness again – belongs in data_readiness.md
- Maximum ONE brief reference to Data Readiness is allowed (e.g., "→ see Data Readiness")
- CAPEX/OPEX blocks ONLY HERE – do not repeat in other sections
- Focus: ROI, Payback, Investment – NO data situation analysis

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: personal ROI, time relief, pragmatic assessment
- team: Team ROI, shared efficiency gains
- sme: Department ROI, scalable effects
-->

<section class="section business-case">
  <h2>Business Case – Investment and Expected Return</h2>

  <!-- G17.P: New intro without redundancy, with cross-references -->
  <p>
    The Business Case connects your Quick Wins (→ see Quick Wins section) with the realistic
    ROI forecast and shows how investments amortize over time. The focus lies on time savings,
    quality gains, and the impact of your AI-Readiness roadmap on CAPEX, OPEX, and payback
    for <strong>{{OFFERING_LABEL}}</strong>.
  </p>

  <h3>Investment and Operating Costs</h3>
  <p>
    The one-time setup and implementation costs are approximately
    <strong>{{CAPEX_REALISTISCH_EUR}}&nbsp;€</strong>. Monthly operating costs of around
    <strong>{{OPEX_REALISTISCH_EUR}}&nbsp;€</strong> are added – mainly for AI usage,
    infrastructure, tools, and potential licenses.
  </p>

  <h3>Monthly Impact on Core Business</h3>
  <p>
    In daily operations, realistic relief of around
    <strong>{{EINSPARUNG_MONAT_EUR}}&nbsp;€ per month</strong> is achievable. This results from
    time savings, fewer manual loops, and more consistent result quality.
    The prerequisite is that the new workflow is consistently used in daily work.
  </p>

  <h3>Payback and ROI</h3>
  <p>
    <strong>Simple calculation:</strong> Investment ({{CAPEX_REALISTISCH_EUR}} €) divided by
    monthly savings ({{EINSPARUNG_MONAT_EUR}} €) results in payback after approximately
    <strong>{{PAYBACK_MONTHS}} months</strong>. The 12-month ROI is
    <strong>{{ROI_12M}}&nbsp;%</strong> – a realistic value with consistent usage.
  </p>

  <h3>Assessment by Company Size</h3>
  <p>
    For <strong>{{COMPANY_SIZE}}</strong>: The more the process
    <strong>{{HAUPTLEISTUNG}}</strong> relies on recurring, standardizable tasks,
    the faster the investment pays off. With consistent use, the
    payback period shortens noticeably; with lower utilization, it extends accordingly.
  </p>

  <h3>Connection to Funding Opportunities</h3>
  <p>
    In <strong>{{BUNDESLAND_LABEL}}</strong>, programs exist that can support AI and
    digitalization projects. If parts of the one-time investment are funded,
    the business case improves through shortened payback periods and higher effective ROI.
    Specific programs and details are explained in the Funding chapter.
  </p>

  <h3>Additional Revenue Potential (Monetization)</h3>
  <p>
    Beyond efficiency gains, AI-powered processes also offer revenue potential:
    Digital products (e.g., automated analyses, reports), new service formats
    (workshops, consulting), or scalable offerings can further improve ROI.
    Details on pricing models can be found in the "Monetization" chapter.
  </p>

  <p class="small muted">
    These values are based on typical experience for {{BRANCHE_LABEL}} companies.
    Actual results depend on usage intensity and process maturity.
  </p>
</section>

<!-- OUTPUT RULES:
     - Respond only with the HTML fragment above.
     - No additional comments or explanations.
     - Total length ≤ 2,400 characters.
-->
