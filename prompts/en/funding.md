Developer:
<!-- funding.md – v1.0 EN Funding for Germany
     Target: English-speaking users with companies based in Germany.
     Output: Valid HTML only. No Markdown fences.

     STRUCTURE (3-4 sections):
       H3 1. Available Programs Overview
       H3 2. What This Means for Your Business Case
       H3 3. Next Steps for Funding

     VARIABLES:
       - {{FOERDERPROGRAMME_HTML}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}
       - If {{FOERDERPROGRAMME_HTML}} is empty: provide generic guidance.

     SIZE-AWARE LOGIC (COMPANY_SIZE):
       SOLO: Focus on low-barrier programs, consulting grants, starter vouchers.
       TEAM (2-10): Programs for process digitalization, training, pilot projects.
       SME (11-100): Additional programs for investments, cooperation projects.

     STYLE:
       - Professional, factual, no marketing language
       - German program names with English explanations
       - No placeholder text, no "content being created"
-->

<section class="section funding">
  <h2>Funding Opportunities (Germany)</h2>

  <p>
    For organizations of size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in the
    <strong>{{BRANCHE_LABEL}}</strong> sector, German federal and state funding programs
    can significantly support AI and digitalization initiatives. Depending on company size,
    options range from consulting grants and innovation vouchers to substantial investment subsidies.
  </p>

  <h3>German Funding Programs for Your Profile</h3>
  <p>
    The following programs are selected based on your company profile and are available
    to businesses operating in Germany:
  </p>

  {{FOERDERPROGRAMME_HTML}}

  <h3>What This Means for Your Business Case</h3>
  <p>
    Appropriate funding can reduce the investment costs outlined in your business case
    and accelerate project payback. For <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>, this means:
  </p>
  <ul>
    <li>Solo entrepreneurs & freelancers: Lower entry barriers, support for consulting and setup costs.</li>
    <li>Small teams: Support for process digitalization, training, and pilot projects.</li>
    <li>SMEs: Additional flexibility for structural investments, pilot implementations, and scaling.</li>
  </ul>
  <p>
    Actual funding rates depend on the specific program, project content, and application requirements.
    Typical grant rates range from <strong>30–50%</strong> of eligible expenses.
  </p>

  <h3>Next Steps</h3>
  <ul>
    <li>
      Review the programs above and identify 1-2 that match your industry
      (<strong>{{BRANCHE_LABEL}}</strong>) and company size (<strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>).
    </li>
    <li>
      Define a fundable project – ideally a clearly scoped AI pilot or digitalization
      initiative in your core process <strong>{{HAUPTLEISTUNG}}</strong>.
    </li>
    <li>
      Prepare a concise project description (goals, measures, timeline, expected benefits,
      approximate costs) as a basis for application documents.
    </li>
    <li>
      Consider reaching out to regional business support organizations or funding advisors
      to realistically assess eligibility and application effort.
    </li>
  </ul>

  <p class="small muted">
    Note: Funding rates, deadlines, and focus areas may change. The overview presented here
    is based on current information at the time of report generation and should be verified
    against official program documentation before applying.
  </p>
</section>
