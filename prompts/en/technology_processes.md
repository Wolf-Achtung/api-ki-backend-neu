<!-- technology_processes.md – v2.0 PDF-SLIMDOWN-STRICT
     Respond with valid HTML only.

     **STRICT TOKEN LIMIT:**
     MAXIMUM 300-400 words output.

     **STRUCTURE (compact):**
     1. Brief introduction (2 sentences)
     2. Process chain focus (main data flow)
     3. Short table: 4-5 layers with purpose
     4. Planned changes (3-4 points brief)

     **FORBIDDEN:**
     - NO tool list (covered in tools_recommendations)
     - Focus on PROCESS CHAINS, not specific tools
     - No redundant tech details
-->

<section class="section technology-processes">
  <h2>Technology & Processes</h2>

  <p>
    This overview shows the data flow from questionnaire to finished PDF report.
    Focus is on process chains, not individual tools.
  </p>

  <h3>System Architecture</h3>
  <table class="table">
    <thead>
      <tr><th>Layer</th><th>Function</th></tr>
    </thead>
    <tbody>
      <tr><td>Frontend</td><td>Questionnaire capture, validation, submit</td></tr>
      <tr><td>Backend</td><td>Prompt orchestration, report builder, business case calculation</td></tr>
      <tr><td>AI/Analysis</td><td>Multi-layer prompt analysis, research integration</td></tr>
      <tr><td>PDF Service</td><td>HTML→PDF rendering, layout optimization</td></tr>
      <tr><td>Delivery</td><td>Email delivery of finished report</td></tr>
    </tbody>
  </table>

  <h3>Data Flow (Main Process)</h3>
  <ol>
    <li>User fills out questionnaire (autosave active)</li>
    <li>Submit → Validation → Storage</li>
    <li>Prompt engine injects industry and size context</li>
    <li>AI generates sections (Executive Summary, Roadmaps, Risks, etc.)</li>
    <li>Business case logic calculates CAPEX/OPEX/ROI</li>
    <li>Validator checks HTML quality and consistency</li>
    <li>PDF service renders final report</li>
    <li>Delivery via email</li>
  </ol>

  <h3>Quality Assurance</h3>
  <ul>
    <li>Automatic consistency check of all sections</li>
    <li>Size mismatch detection (Solo/Team/SME)</li>
    <li>Plausibility check of business case figures</li>
  </ul>

  <p class="small muted">
    This architecture ensures traceable, quality-assured reports.
  </p>
</section>
