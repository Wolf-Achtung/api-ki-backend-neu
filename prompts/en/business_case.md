<!-- PLATIN+++ PROMPT v6.1 - SPRINT G17.P -->
<!-- SECTION: business_case -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{COMPANY_SIZE}}, {{HAUPTLEISTUNG}}, {{BUNDESLAND_LABEL}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}, {{OFFERING_LABEL}} -->
<!-- TOKEN-BUDGET: 1800 (solo:0.8x=1440, team:1.0x=1800, kmu:1.15x=2070) -->
<!-- WORD_MINIMUM_SOLO: 130 -->
<!-- WORD_MINIMUM_TEAM: 150 -->
<!-- WORD_MINIMUM_KMU: 180 -->
<!--
GOAL: Clear, realistic business case with ROI and CAPEX/OPEX.

REALISM RULES (STRICT!):
- NO 90% efficiency promises – realistic 15–30% savings.
- NO made‑up numbers – use only the provided variables.
- "around / approx. / about" may be used to qualify numbers.
- NO funding rates (see foerderpotenzial.md).
- Company size influences ONLY the narrative context, not the numbers.

PAYBACK EXPLANATION (SIMPLIFIED):
- Simple formula: Investment ÷ monthly savings = months.
- NO complex financial calculations.
- Communicate assumptions transparently.

ANTI‑REDUNDANCY:
- Mention business case numbers ONLY HERE.
- In foerderpotenzial.md only refer to these numbers, do not repeat them.
- In executive_summary.md just mention them as an indication.

SPRINT G18 – ANTI‑REDUNDANCY (STRICT!):
- Do NOT describe data readiness again – belongs in data_readiness.md.
- Maximum ONE brief reference to data readiness is allowed (e.g. "→ see data readiness").
- CAPEX/OPEX blocks ONLY HERE – do not repeat in other sections.
- Focus on ROI, payback, investment – NO data readiness analysis.

SPRINT G18 – NARRATIVE CONNECTIONS:
- Reference the starter kit: "The starter kits enable a cost‑efficient implementation of the quick wins..."
- Reference the roadmap: "Amortisation already occurs in Phase 2 of the 90‑day roadmap..."
- Announce funding potential: "Details on possible funding → see funding potential".

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: Personal ROI, time relief, pragmatic assessment.
- team: Team ROI, joint efficiency gains.
- kmu: Departmental ROI, scalable effects.

SPRINT N – SOLO PERSONA RULES (STRICT!):
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

  <!-- G17.P: New introduction without redundancy, with cross‑references -->
  <p>
    For <strong>{{OFFERING_LABEL}}</strong> in the <strong>{{BRANCHE_LABEL}}</strong> sector
    a specific investment framework can be derived. The business case shows what
    setup and ongoing operational efforts are realistic and over what period they will
    amortise. The focus is on time savings, quality gains and a transparent payback period.
    The quick wins from the roadmap accelerate the ROI in addition – see immediate measures.
  </p>

  <h3>Investment and ongoing costs</h3>
  <p>
    One‑time setup and introduction costs are around
    <strong>{{CAPEX_REALISTISCH_EUR}}&nbsp;€</strong>. In addition there are monthly operating costs
    of about <strong>{{OPEX_REALISTISCH_EUR}}&nbsp;€</strong> – mainly for AI use,
    infrastructure, tools and potential licences.
  </p>

  <h3>Monthly effect in the core business</h3>
  <p>
    In day‑to‑day use a realistic relief of around
    <strong>{{EINSPARUNG_MONAT_EUR}}&nbsp;€ per month</strong> is achievable. This arises from
    time gains, fewer manual loops and more consistent result quality.
    A prerequisite is that the new workflow is used consistently in everyday life.
  </p>

  <h3>Payback and ROI</h3>
  <p>
    <strong>Simple calculation:</strong> Investment ({{CAPEX_REALISTISCH_EUR}} €) divided by
    monthly savings ({{EINSPARUNG_MONAT_EUR}} €) yields amortisation after approximately
    <strong>{{PAYBACK_MONTHS}} months</strong>. The ROI after 12 months is
    <strong>{{ROI_12M}}&nbsp;%</strong> – a realistic value with consistent use.
  </p>

  <h3>Orientation by company size</h3>
  {% if COMPANY_SIZE == "solo" %}
  <p>
    The more <strong>{{HAUPTLEISTUNG}}</strong> relies on recurring tasks,
    the faster your investment has an effect.
  </p>
  {% elif COMPANY_SIZE == "team" %}
  <p>
    The more <strong>{{HAUPTLEISTUNG}}</strong> relies on recurring tasks,
    the faster the team investment has an effect.
  </p>
  {% else %}
  <p>
    The more <strong>{{HAUPTLEISTUNG}}</strong> relies on standardisable tasks,
    the faster the amortisation.
  </p>
  {% endif %}

  <h3>Link to funding opportunities</h3>
  <p>
    In <strong>{{BUNDESLAND_LABEL}}</strong> there are funding programmes for AI projects.
    A subsidy shortens the payback period. Details → see funding chapter.
  </p>

  <h3>Additional revenue potentials</h3>
  <p>
    In addition to efficiency gains AI processes offer revenue potentials:
  </p>
  <ul>
    <li>Digital products (automated analyses, reports)</li>
    <li>New service formats (workshops, consulting)</li>
    <li>Scalable offers</li>
  </ul>

  <p class="small muted">
    These values are based on typical experiences for {{BRANCHE_LABEL}} companies.
    Actual results depend on usage intensity and process maturity.
  </p>
</section>

<!-- OUTPUT GUIDELINES:
     - Respond only with the HTML fragment above.
     - No additional comments or explanations.
     - Total length ≤ 2,400 characters.
 -->
