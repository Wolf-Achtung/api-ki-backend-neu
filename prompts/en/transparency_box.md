<section class="section transparency-box">
  <h2>Transparency Notes on Report Creation</h2>

  <div class="transparency-panel">
    <h3>How was this report created?</h3>
    <p>
      This report was generated <strong>AI-assisted</strong> from your questionnaire responses
      dated <strong>{{report_date}}</strong>. The content is based on a
      multi-stage analysis consisting of structured prompts, industry-specific
      context information, and internal quality checks. The industry context for this
      report is: <strong>{{BRANCHE_LABEL}}</strong>.
    </p>

    <h3>What data is incorporated?</h3>
    <ul>
      <li>Responses from your digitally completed questionnaire (as of: {{report_date}}).</li>
      <li>Research snippets on market, trends, and landscape (e.g., Perplexity/Tavily).</li>
      <li>Relevant legal framework conditions, including EU AI Act (as of August 1, 2024).</li>
      <li>Internal benchmarks from comparable company profiles.</li>
    </ul>

    <h3>Limitations & Notes</h3>
    <ul>
      <li><strong>No legal advice:</strong> The legal assessments (GDPR, AI Act) serve as orientation and do not replace legal review.</li>
      <li><strong>No guarantee:</strong> Economic figures (ROI, payback) are realistic estimates based on your inputs, but not binding forecasts.</li>
      <li><strong>Information as of date:</strong> Tools and regulatory requirements may have changed after {{report_date}}.</li>
      <li><strong>Professional review recommended:</strong> AI results should always be manually reviewed before implementation.</li>
    </ul>

    <h3>Quality Assurance</h3>
    <p>This report undergoes multi-stage assurance:</p>
    <ol>
      <li>Automatic consistency and plausibility check.</li>
      <li>Manual validation of key statements by a qualified person.</li>
      <li>Alignment of recommendations with company size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>.</li>
      <li>Review of key regulatory notes (e.g., data protection, EU AI Act).</li>
    </ol>

    <h3>Contact & Questions</h3>
    <p>
      For questions or feedback, you can reach us anytime at:<br>
      <strong>contact@ai-security.now</strong><br>
      Optionally, we offer a brief follow-up call within the first 30 days after report receipt.
    </p>
  </div>

  <style>
    .transparency-panel {
      background: #f6fafe;
      padding: 18px 24px;
      border-left: 4px solid #0284c7;
      margin: 24px 0;
    }
  </style>
</section>
