Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: executive_summary -->
<!-- VERSION: v5.0 PLATIN++ V5 -->
<!-- OUTPUT: HTML -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{BUNDESLAND_LABEL}} -->
<!-- TOKEN-BUDGET: 800 (solo:0.8x, team:1.0x, sme:1.15x) -->
<!-- FUNDING: EN-Germany (Phase 1) or EN-EU (Phase 2) -->
<!--
GOAL:
- Perfectly structured Executive Summary in 3-5 concise sections.
- Maximum 5 paragraphs, each max. 4 sentences.

FORBIDDEN:
- Placeholder strings, technical pipeline terms
- DE-specific examples (use EN-appropriate examples)

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: Direct "you" address, personal relief, quick results
        FORBIDDEN: department, division, team
- team: Light org language ("team", "colleagues"), shared routines
- sme: Teams, departments, responsible parties allowed
        FORBIDDEN: corporate jargon ("division", "business unit")

GUARDRAILS: Respect any no-gos/guardrails from strategic context.

STYLE:
- Clear, precise, business-oriented
- No buzzwords, no marketing text
- Condensation over repetition
-->

<section class="section executive-summary">
  <h2>Executive Summary</h2>

  <p>
    This Executive Summary outlines the current AI positioning of a company in the
    <strong>{{BRANCHE_LABEL}}</strong> industry – tailored to company size
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> and core process
    <strong>{{HAUPTLEISTUNG}}</strong>. It provides a clear overview of the current situation,
    strengths, key levers, and next steps that are critical for effective AI adoption.
  </p>

  <h3>Current State & Scores</h3>
  <p>
    The score results show a differentiated picture: Governance, Security,
    Value Creation Potential, and Enablement indicate where the company already
    has solid foundations and where structural or organizational gaps still exist.
    The combination of strengths – such as clearly defined work routines or initial digital
    standards – and individual development areas forms the basis for the following recommendations.
  </p>

  <h3>Key Quick Wins & Short-term Measures</h3>
  <p>
    The Quick Wins primarily address those steps in the <strong>{{HAUPTLEISTUNG}}</strong> process
    that can be standardized or partially automated in the short term. These include typical
    recurring tasks that can deliver noticeable relief within the next 90 days through
    clearly defined workflows, better templates, or AI-assisted support.
    These measures are the direct entry point to a more stable and efficient way of working.
  </p>

  <h3>Business Case</h3>
  <p>
    The business case shows a realistic relationship between investment (CAPEX/OPEX),
    monthly savings, and payback period. The expected impact is clearly positive –
    both in time savings and qualitative gains.
  </p>

  <h3>Next Steps for Leadership</h3>
  <p>
    Leadership should prioritize implementation in three steps: First, the
    short-term Quick Wins; second, a clearly defined pilot process as a real-world test under
    everyday conditions; third, establishing light governance and documentation standards
    to ensure result quality on an ongoing basis. These three building blocks lay the
    foundation for the subsequent 12-month initiatives and scalable AI utilization.
  </p>
</section>
