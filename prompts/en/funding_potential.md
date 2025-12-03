Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: funding_potential -->
<!-- VERSION: v2.0 PLATIN++ V5 -->
<!-- OUTPUT: HTML -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BUNDESLAND_LABEL}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}} -->
<!-- TOKEN-BUDGET: 3200 (solo:0.8x, team:1.0x, sme:1.15x) -->
<!-- FUNDING: EN-Germany (Phase 1) - German federal + state programs in English -->
<!--
TARGET: English-speaking users with companies based in Germany.

STRUCTURE (4 sections):
  H3 1. Business Case Without Funding
  H3 2. How Funding Can Improve Your Business Case
  H3 3. Relevant Funding Focus Areas
  H3 4. Next Steps for Funding Assessment

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: low barriers, <10,000€, consulting/starter grants
- team: process digitalization, SME-innovativ, go-digital
- sme: Digital Jetzt, ZIM, structural funding

ANTI-REDUNDANCY:
- Business case numbers ONCE here, reference in other sections
- NO repetition from business_case.md

RULES:
- Funding rates only as ranges (e.g., "30-50%")
- Factual, neutral tone, no marketing
- NO EU-Core hints here (see funding_eu_core.md for EU)
-->

<section class="section funding-potential">
  <h2>Funding Potential for Your AI Project</h2>

  <p>
    Companies in the <strong>{{BRANCHE_LABEL}}</strong> sector located in
    <strong>{{BUNDESLAND_LABEL}}</strong> with size category
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> pursuing projects related to
    <strong>{{HAUPTLEISTUNG}}</strong> often have good prerequisites for funding.
    The combination of digitalization focus, AI support, and clear process improvements
    aligns with priorities of many federal and state programs in Germany.
  </p>

  <h3>1. Business Case Without Funding</h3>
  <p>
    The current business case shows one-time investments of approximately
    <strong>{{CAPEX_REALISTISCH_EUR}} €</strong> and ongoing costs of around
    <strong>{{OPEX_REALISTISCH_EUR}} € per month</strong>. The expected monthly
    savings are approximately <strong>{{EINSPARUNG_MONAT_EUR}} €</strong>,
    resulting in a payback period of about <strong>{{PAYBACK_MONTHS}} months</strong>
    and a realistic ROI of around <strong>{{ROI_12M}}%</strong> in the first year.
  </p>
  <p>
    This baseline is attractive for many funding agencies: the project is economically
    plausible, the benefits are clearly identifiable, and the self-contribution is
    fundamentally sustainable. Funding can improve this situation by reducing
    part of the investment burden – the project is already viable without external
    support; with funding, profitability becomes even more attractive.
  </p>

  <h3>2. How Funding Can Improve Your Business Case</h3>
  <p>
    Many programs in {{BUNDESLAND_LABEL}} and at the federal level support AI and
    digitalization initiatives by subsidizing a portion of eligible investment costs.
    Depending on the program, company size, and project focus, grant rates typically
    range from approximately <strong>30–50%</strong> of recognized costs. For an
    investment volume of {{CAPEX_REALISTISCH_EUR}} €, this could mean relief of
    several thousand euros.
  </p>
  <ul>
    <li><strong>Shorter payback period:</strong> By co-financing investment costs,
      the self-contribution decreases; payback can shorten from {{PAYBACK_MONTHS}} months
      to significantly less without changing the expected benefits.</li>
    <li><strong>Higher effective ROI:</strong> When part of the investment is covered by
      grants, the effective return per euro invested increases – the current ROI of
      {{ROI_12M}}% can more than double with 40% funding.</li>
    <li><strong>Reduced financial risk:</strong> For <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>,
      a grant can facilitate moving forward with a more ambitious project without
      unnecessarily straining liquidity. The ongoing costs of {{OPEX_REALISTISCH_EUR}} €/month
      remain manageable.</li>
    <li><strong>More flexibility for quality and training:</strong> Savings from funding
      can be used for additional quality, security, or training measures.</li>
    <li><strong>Better planning reliability:</strong> With approved funding, the project
      budget can be planned more reliably and unexpected additional costs can be better absorbed.</li>
  </ul>

  <h3>3. Relevant Funding Focus Areas</h3>
  <p>
    Based on your industry <strong>{{BRANCHE_LABEL}}</strong>, focus area
    <strong>{{HAUPTLEISTUNG}}</strong>, and company size
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>, the following funding categories
    may be relevant:
  </p>
  <ul>
    <li><strong>Digitalization funding:</strong> Programs for AI-supported process optimization,
      automation, and digital tools. Particularly relevant for {{HAUPTLEISTUNG}}.</li>
    <li><strong>Innovation funding:</strong> Grants for novel AI applications, pilot projects,
      and technology development, tailored to the {{BRANCHE_LABEL}} sector.</li>
    <li><strong>Training funding:</strong> Resources for training, continuing education,
      and building AI competencies – important for sustainable adoption.</li>
    <li><strong>Consulting funding:</strong> Support for external expertise in AI strategy
      development and implementation.</li>
  </ul>

  <h3>4. Next Steps for Funding Assessment</h3>
  <ol>
    <li><strong>Program selection:</strong> Select 1-2 programs that match
      <strong>{{BRANCHE_LABEL}}</strong>, <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>,
      and <strong>{{HAUPTLEISTUNG}}</strong>.</li>
    <li><strong>Project description:</strong> Create a concise project description
      (goals, measures, timeline, expected benefits, approximate costs referencing
      the calculated {{CAPEX_REALISTISCH_EUR}} €).</li>
    <li><strong>Combination check:</strong> Verify whether programs from {{BUNDESLAND_LABEL}}
      can be combined with federal or EU programs.</li>
    <li><strong>Seek advice:</strong> Optionally consult with funding advisors, chambers
      of commerce, or financing partners.</li>
    <li><strong>Timeline planning:</strong> Funding applications typically require 4-8 weeks
      lead time – factor this into project planning.</li>
  </ol>

  <p class="small muted">
    Note: Funding rates, deadlines, and requirements may change. Before applying,
    the official guidelines and conditions of respective programs should be reviewed in detail.
  </p>
</section>
