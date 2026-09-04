<!-- ai_act_summary.md – v4.1 GOLD STANDARD+ SPRINT N (EU AI Act – branch- & size-aware, context-integrated)
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body>. NO Markdown fences.

     GOAL:
       - Precise, professional, factual summary of the EU AI Act.
       - Assessment of relevance for {{HAUPTLEISTUNG}} considering
         BRANCH + COMPANY SIZE + CONTEXT_BLOCK.
       - Correct deadlines (02.08.2025 / 02.08.2026 / 02.08.2027).
       - Presentation of relevant obligations (Art. 5, Art. 6, Art. 50) + horizontal requirements.
       - Clearly name transparency obligations.
       - Short section: "What does this mean for companies of this size?" (size-aware).
       - Consider industry-specific risks / regulation (finance, healthcare, public sector).
       - Mandatory disclaimer: no legal advice.

     AVAILABLE VARIABLES:
       {{HAUPTLEISTUNG}}
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{report_date}}
       {{COMPANY_SIZE}}

     RULES:
       - No legal advice, only fact-based, structured information.
       - Factual, neutral tone.
       - No placeholders or stage directions in output.
       - No references to internal logic, questionnaires, or prompt engine.
       - Actively use CONTEXT_BLOCK: industry workflows, pain points, typical data types,
         regulatory requirements – but without directly referencing the block.

     SIZE-AWARE:
       SOLO:
         - Focus on few deployment points, simple labelling, low complexity.
         - Minimal documentation, clear, pragmatic rules.
       TEAM (2–10):
         - Clearly name responsibilities, define simple processes.
         - Ensure consistent labelling across multiple people.
       SME (11–100):
         - Written guidelines, fixed roles, internal training logic.
         - Governance & oversight structures necessary.

     BRANCH-AWARE:
       - Finance, Healthcare, Public Sector, Legal:
           → Increased transparency, documentation, and verification requirements; careful data use,
             clear internal approvals; potentially close to high-risk use cases.
       - Media & Creative Industries (film/TV, post, audio, agency, publishing, games, content creation):
           → Labelling of synthetic content (Art. 50), rights chain for AI output,
             personality rights in voice and face; publishing: reader transparency;
             games: store disclosure and youth protection.
       - Manufacturing/Production:
           → Documentation & human oversight for automated workflows.
       - E-Commerce/Retail:
           → Transparency towards end customers, quality of AI-generated content.
       - IT/Software:
           → Model/data control, documented development steps.

     SPRINT N - SOLO PERSONA RULES (STRICT!):
     {% if COMPANY_SIZE == "solo" %}
     DO NOT USE for Solo:
     - "build team" → instead: "expand capacity"
     - "employee" → instead: "resource"
     - "teams" → instead: "capacities"
     - "department" → instead: "work area"
     Use phrasing without team/department terms!
     {% endif %}

     OUTPUT STRUCTURE:
       <section>
         <h2>
         Note
         Relevance for branch + service
         Obligations (Art. 5, 6, 50)
         Further requirements (Documentation, Human Oversight)
         Industry-specific notes
         Deadlines (table)
         What does this mean for this company size?
         Next steps
         Risks of non-compliance
         Conclusion
-->

<section class="section ai-act">
  <h2>EU AI Act – Summary &amp; Obligations</h2>

  <p>
    <strong>Note:</strong> This section provides a general, non-exhaustive
    overview of key requirements of the EU&nbsp;AI&nbsp;Act. It does not
    constitute legal advice. For complex or sensitive use cases, specialized
    advisors should be consulted.
  </p>

  <h3>Relevance for "{{HAUPTLEISTUNG}}" in the {{BRANCHE_LABEL}} Industry</h3>
  <p>
    The use of AI in <strong>{{HAUPTLEISTUNG}}</strong> within the
    <strong>{{BRANCHE_LABEL}}</strong> industry typically <strong>does not fall into the high-risk
    category under Art.&nbsp;6</strong>.
  </p>
  <p>
    This applies particularly for AI used in text generation, analysis, or internal support.
    Automated individual decisions about people (credit, medical diagnoses, HR) would trigger
    stricter requirements.
  </p>

  <p>
    Nevertheless, <strong>transparency obligations</strong> and requirements for
    <strong>careful, traceable use</strong> apply. Whenever AI generates content used
    towards customers, authorities, or partners, it must be clearly recognizable
    that AI was involved.
  </p>

  <h3>Key Obligations under EU AI Act (Excerpt)</h3>
  <ul>
    <li><strong>Art.&nbsp;5 – Prohibited Practices:</strong>
      Manipulative systems, exploitative designs, or biometric categorization
      are clearly prohibited. (Relevance: low, except in heavily regulated industries.)</li>

    <li><strong>Art.&nbsp;6 – High-Risk Systems:</strong>
      AI systems that significantly affect fundamental rights are subject to strict obligations
      (data quality, logging, governance). For {{HAUPTLEISTUNG}} typically not applicable
      – except in industries like healthcare, finance, public administration.</li>

    <li><strong>Art.&nbsp;50 – Transparency Obligations:</strong>
      AI-generated content and automated suggestions must be clearly identifiable,
      especially when supporting decision-making.</li>

    <li><strong>Documentation &amp; Traceability:</strong>
      Companies must document where AI is used, how results are reviewed,
      and what data was utilized.</li>

    <li><strong>Human Oversight:</strong>
      Humans must be able to review critical results. This applies especially to sensitive
      workflows (e.g., finance, healthcare, government actions).</li>
  </ul>

  <h3>Industry-Specific Considerations</h3>
  <ul>
    <li>
      <strong>Healthcare &amp; Care, Finance, Legal, Public Administration:</strong>
      Increased transparency, documentation, and verification requirements; careful data use,
      clear internal approvals; potentially close to high-risk use cases.
    </li>
    <li>
      <strong>Media &amp; Creative Industries:</strong>
      Labelling of synthetic content (Art. 50), rights chain for AI-generated assets,
      personality rights in voice and face, approvals towards clients and broadcasters.
    </li>
    <li>
      <strong>Manufacturing &amp; Production:</strong>
      AI-powered process optimisation requires documented use and clear
      intervention options; data quality is essential.
    </li>
    <li>
      <strong>E-Commerce &amp; Retail:</strong>
      Transparency towards end customers, consistent product and content presentation.
    </li>
    <li>
      <strong>IT &amp; Software:</strong>
      Model control, source tracking, secure handling of training data, logging, and
      clear governance structures.
    </li>
  </ul>

  <h3>Important Deadlines</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Date</th>
        <th>Obligation Area</th>
        <th>Relevance</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>02.08.2025</td>
        <td>Prohibited AI Practices (Art.&nbsp;5)</td>
        <td>From this date, certain manipulative or exploitative AI practices are prohibited.</td>
      </tr>
      <tr>
        <td>02.08.2026</td>
        <td>High-Risk Systems</td>
        <td>Stricter requirements for AI systems with significant risk to fundamental rights.</td>
      </tr>
      <tr>
        <td>02.08.2027</td>
        <td>Transparency Obligations (Art.&nbsp;50)</td>
        <td>Clear labelling of AI-generated content becomes mandatory.</td>
      </tr>
    </tbody>
  </table>

  <h3>What Does This Mean for Companies of Your Size?</h3>
  <p>
    For a company of size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>, the focus is on
    implementing the requirements pragmatically and consistently. The specific
    priorities differ by structure:
  </p>

  {% if COMPANY_SIZE == "solo" %}
  <p>
    As a solo entrepreneur, it suffices to clearly identify your few AI deployment points,
    formulate simple standard notices, and briefly review results. Complex processes or
    extensive documentation are not required – a pragmatic, personal approach is sufficient.
  </p>
  {% elif COMPANY_SIZE == "team" %}
  <p>
    For a team of 2–10 people, clarify responsibilities (Who reviews? Who labels?),
    define uniform internal rules, and keep coordination short. Consistency within the team
    matters more than extensive documentation.
  </p>
  {% else %}
  <p>
    For an SME (11–100 employees), written guidelines for AI use, fixed approval processes,
    documented roles and internal training are recommended. Governance elements should be
    anchored early.
  </p>
  {% endif %}

  <h3>Recommended Next Steps</h3>
  <ol>
    <li>Create an overview of where AI is used in <strong>{{HAUPTLEISTUNG}}</strong>.</li>
    <li>Define standard notice text (for reports, customer communication, presentations).</li>
    <li>Formulate an internal mini-guideline: data, review, approvals, usage limits.</li>
    <li>Exclude or separately review potential high-risk use cases.</li>
    <li>For sensitive industries: establish regular data protection and compliance checks.</li>
  </ol>

  <h3>Risks of Non-Compliance</h3>
  <ul>
    <li>Fines under Art.&nbsp;99 (depending on type and severity of violation).</li>
    <li>Reputation risks with unclear or missing labelling of AI use.</li>
    <li>Loss of trust with customers, partners, and employees.</li>
    <li>Risks in audits, funding programmes, or in regulated industries.</li>
  </ul>

  <p class="small muted">
    As of: {{report_date}}. The implementation of individual requirements may be
    further specified through delegated acts and guidelines.
  </p>
</section>