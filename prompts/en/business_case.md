Developer:
<!-- business_case.md – v3.0 GOLD STANDARD+ (ROI, CAPEX/OPEX, size-aware)
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body>. NO Markdown fences.

     AVAILABLE VARIABLES:
       {{BRANCHE_LABEL}}
       {{COMPANY_SIZE}}            // solo | team | kmu
       {{HAUPTLEISTUNG}}
       {{BUNDESLAND_LABEL}}
       {{CAPEX_REALISTISCH_EUR}}
       {{OPEX_REALISTISCH_EUR}}
       {{EINSPARUNG_MONAT_EUR}}
       {{PAYBACK_MONTHS}}
       {{ROI_12M}}

     RULES:
       - Do not invent numbers. Use only the variables provided.
       - "approximately / around / roughly" allowed for linguistic context.
       - Do not mention funding rates (separate chapter for that).
       - Output = valid HTML fragment.
       - Size (solo/team/sme) only affects narrative context, not the numbers.
-->

<section class="section business-case">
  <h2>Business Case – Investment and Expected Return</h2>

  <p>
    For a company in the <strong>{{BRANCHE_LABEL}}</strong> industry with size
    <strong>{{COMPANY_SIZE}}</strong>, the process <strong>{{HAUPTLEISTUNG}}</strong>
    is a central lever for value creation. The following business case shows
    what financial impact a systematic use of AI can realistically achieve.
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
    Under these assumptions, the investment pays back after approximately
    <strong>{{PAYBACK_MONTHS}} months</strong>. Calculated over twelve months, an
    expected return on investment of <strong>{{ROI_12M}}&nbsp;%</strong> emerges.
    This value serves as a realistic orientation and demonstrates the economic viability of the initiative.
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
    Note: This presentation serves as transparent guidance. For investment decisions,
    supplementation with conservative, baseline, and optimistic scenarios is recommended.
  </p>
</section>

<!-- OUTPUT RULES:
     - Respond only with the HTML fragment above.
     - No additional comments or explanations.
     - Total length ≤ 2,400 characters.
-->
