<section class="section technology-processes">
  <h2>Technology &amp; Processes</h2>

  <h3>Conceptual Checklist</h3>
  <ul>
    <li>Complete transparency over all deployed systems – frontend, backend, AI, data storage.</li>
    <li>Clear assignment of responsibilities per layer.</li>
    <li>Traceable data flow from user input to final PDF report.</li>
    <li>Clear technical integration points between frontend, backend, AI, and PDF service.</li>
    <li>Distinction between current stack and planned extensions.</li>
    <li>Technically precise, audit-ready, and without unnecessary abstraction.</li>
  </ul>

  <h3>Tech Stack (Current)</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Layer</th>
        <th>Technologies</th>
        <th>Purpose</th>
        <th>Hosting</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Frontend</td>
        <td>React, TailwindCSS</td>
        <td>Interactive AI readiness questionnaire, UI logic, autosave, submit flow</td>
        <td>Netlify</td>
      </tr>
      <tr>
        <td>Backend</td>
        <td>FastAPI (Python)</td>
        <td>
          Receiving & validating form data, prompt orchestration (multi-layered),
          report builder, business case calculations, research integration, validator & replacer.
        </td>
        <td>Railway</td>
      </tr>
      <tr>
        <td>Database</td>
        <td>PostgreSQL</td>
        <td>Briefings, user profiles, scores, reports, system logs</td>
        <td>Railway</td>
      </tr>
      <tr>
        <td>AI / Models</td>
        <td>OpenAI GPT-4.1 / GPT-5.x, Perplexity, Tavily</td>
        <td>
          Multi-stage prompt analysis, research snippets, industry context,
          size-aware logic, content validation.
        </td>
        <td>OpenAI / Perplexity / Tavily API</td>
      </tr>
      <tr>
        <td>Form</td>
        <td>Custom React form builder (Frontend + Backend Submit)</td>
        <td>
          Capture all inputs; dynamic validation; multi-page wizard;
          webhook-free, direct API communication.
        </td>
        <td>Netlify / Railway</td>
      </tr>
      <tr>
        <td>PDF Service</td>
        <td>WeasyPrint (dedicated render worker)</td>
        <td>Rendering HTML reports as PDF (A4, corporate layout)</td>
        <td>Railway</td>
      </tr>
      <tr>
        <td>Email</td>
        <td>Resend API</td>
        <td>Sending finished reports, login codes, internal system messages</td>
        <td>Resend</td>
      </tr>
    </tbody>
  </table>

  <h3>Data Flow (Main Process)</h3>
  <ol>
    <li>Users fill out the web-based form builder (React frontend with autosave).</li>
    <li>Submit sends data via HTTPS to FastAPI; validation & storage in PostgreSQL.</li>
    <li>
      FastAPI starts the analysis:
      <ul>
        <li>PromptEnhancer injects industry and size context (CONTEXT_BLOCK).</li>
        <li>Multi-layered GPT prompts generate Executive Summary, Roadmaps, Risks, Recommendations, etc.</li>
        <li>Research pipeline calls Perplexity/Tavily and integrates snippets in a controlled manner.</li>
      </ul>
    </li>
    <li>Business case logic calculates CAPEX/OPEX/ROI based on inputs.</li>
    <li>Report validator checks HTML quality, size mismatch, forbidden tokens & consistency.</li>
    <li>The final HTML report is passed to the dedicated PDF service.</li>
    <li>WeasyPrint renders the PDF; FastAPI sends it via Resend by email to users.</li>
  </ol>

  <h3>Planned Changes (Q1–Q4)</h3>
  <ul>
    <li>
      <strong>Q1:</strong> Introduction of Redis queue for parallel GPT jobs,
      stabilization of bulk generations and timeouts.
    </li>
    <li>
      <strong>Q2:</strong> Integration of Supabase-based auth for partner access
      (e.g., consultants, resellers, white-label instances).
    </li>
    <li>
      <strong>Q3:</strong> Unified system logs (analysis, PDF service, research)
      for better auditability and troubleshooting.
    </li>
    <li>
      <strong>Q4:</strong> Retool-based admin dashboard for monitoring,
      report management, billing runs, and audit exports.
    </li>
  </ul>

  <p class="small muted">
    This overview represents the complete technology and process framework and
    supports technical development toward scalability,
    stability, and auditability.
  </p>
</section>
