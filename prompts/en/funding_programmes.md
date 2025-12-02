Developer:
<!-- funding_programmes.md (EN) – v1.0 EU Funding Module
     Output valid HTML only. No Markdown fences.

     PURPOSE:
       - Provide a qualitative overview of funding potential for AI/digitalization projects
       - {{FOERDERPROGRAMME_HTML}} contains the pre-built funding table from FundingService
       - Add context and guidance, but DO NOT invent new programs

     AVAILABLE VARIABLES:
       - {{FOERDERPROGRAMME_HTML}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}
       - {{COUNTRY_CODE}}, {{COUNTRY_NAME}} (if available)
       - If {{FOERDERPROGRAMME_HTML}} is empty:
           Provide a neutral, generic note (e.g., "Funding research is in progress.")
           NEVER output <p class="error">...</p> in the final report.

     SIZE-AWARE LOGIC (COMPANY_SIZE ∈ {"solo","team","kmu"}):
       SOLO:
         - Focus: small programs, starter grants, innovation vouchers
         - Language: clear, pragmatic, low bureaucratic burden
       TEAM (2–10):
         - Programs for process digitalization, training, pilot projects
         - Language: team roles, simple coordination
       SME/KMU (11–100):
         - Additional programs for investments, consortium projects, partnerships
         - Language: departments, responsibilities, structured application steps

     STYLE:
       - 3-4 structured sections: Introduction, Programs, Business Case Impact, Next Steps
       - No marketing tone, no hyperbole, no exaggerated promises
       - No placeholder text, no "Content is being generated"

     HTML STRUCTURE (exactly one <section> block):
       <section class="section funding"> … </section>
-->

<section class="section funding">
  <h2>Funding Programs for Your AI Project</h2>

  <p>
    For companies of size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in the
    <strong>{{BRANCHE_LABEL}}</strong> sector, funding programs can play an important
    role in making AI and digitalization projects economically viable. Depending on
    company size, options range from starter and consulting programs to grants for
    process digitalization and larger investment or collaboration projects.
  </p>

  <h3>Selected Programs Overview</h3>
  <p>
    The following programs are based on current funding research and consider
    regional as well as thematic priorities:
  </p>

  {{FOERDERPROGRAMME_HTML}}

  <h3>What This Means for Your Business Case</h3>
  <p>
    Appropriate funding can reduce the investment costs outlined in your business case
    and accelerate project payback. For <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>,
    this means specifically:
  </p>
  <ul>
    <li>Solo entrepreneurs: Lower entry barriers and relief for consulting or setup costs.</li>
    <li>Small teams: Support for process digitalization, training, and pilot projects.</li>
    <li>SMEs: Additional room for structural investments, pilot facilities, and scaling projects.</li>
  </ul>
  <p>
    The actual funding rate depends on the specific program, project content, and
    application requirements, and must be verified in detail before application.
    Typical grant ranges—depending on the program—fall in the spectrum of approximately
    <strong>30–50%</strong> of eligible expenses.
  </p>

  <h3>Next Steps</h3>
  <ul>
    <li>
      Conduct a structured funding check: Match programs from the overview with
      <strong>{{BRANCHE_LABEL}}</strong> and <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>,
      and review deadlines and eligible activities.
    </li>
    <li>
      Define an eligible project—ideally a clearly scoped AI pilot or digitalization
      project in the core process <strong>{{HAUPTLEISTUNG}}</strong>.
    </li>
    <li>
      Prepare a compact project description (goals, measures, timeline, expected
      benefits, approximate costs) to serve as a basis for application documents.
    </li>
    <li>
      Optionally, seek advice from regional business support organizations or
      relevant contacts to realistically assess eligibility, combination options, and effort.
    </li>
  </ul>

  <p class="small muted">
    Note: Funding rates, deadlines, and content focus of programs may change.
    The overview presented here is based on funding research current at the time of
    report generation and should always be verified against official program documentation
    before applying.
  </p>
</section>
