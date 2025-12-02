Developer:
<!-- executive_summary.md – v3.0 GOLD STANDARD+ (Summary + Size-Layer + Context-Integration)
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body>. NO Markdown fences in OUTPUT.

     GOAL:
     - Generate a perfectly structured, one-page Executive Summary
       that condenses all core aspects of the AI Status Report into 3-5 concise sections.

     FORBIDDEN:
     - No placeholder strings ("Placeholder", "[...]", "{XYZ}").
     - No technical pipeline terms (CONTEXT_..., SCORE_..., etc.).
     - No raw variable names in output ({{BRANCHE_LABEL}} etc. may remain in HTML).

     CONTEXT SOURCES (provided as plain text):
     - Quick Wins (CONTEXT_QUICK_WINS)
     - 90-Day Roadmap (CONTEXT_ROADMAP_90D)
     - 12-Month Roadmap (CONTEXT_ROADMAP_12M)
     - Business Case (CAPEX, OPEX, Payback, ROI_12M)
     - Tool Recommendations
     - Scores: Governance, Security, Value Creation, Enablement, Overall

     AVAILABLE QUESTIONNAIRE VARIABLES (Labels):
     - {{BRANCHE_LABEL}}
     - {{UNTERNEHMENSGROESSE_LABEL}}
     - {{HAUPTLEISTUNG}}
     - {{BUNDESLAND_LABEL}}

     SIZE LOGIC (Solo / Team / SME)
     --------------------------------------------------------------
     INTERNAL: COMPANY_SIZE ∈ {"solo","team","kmu"}.

     SOLO ("1 (Solo" in label):
       - Direct "you" address.
       - No terms like department, division, team.
       - Focus: personal relief, quick results, pragmatic implementation.
       - Measures always realistic for a single person.

     TEAM (2-10):
       - Light organizational language allowed ("team", "colleagues").
       - Responsibilities = roles, not departments.
       - Focus: shared routines, quick coordination, clear priorities.

     SME (11-100):
       - Organizational language allowed: teams, departments, responsible parties.
       - No corporate vocabulary ("division", "business unit").
       - Focus: scalable implementation, governance, cross-functional coordination.

     STYLE:
       - Clear, precise, business-oriented.
       - No buzzwords, no marketing text.
       - Maximum 5 paragraphs, each max. 4 sentences.
       - Condensation over repetition: 3-5 strongest messages of the report.

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
