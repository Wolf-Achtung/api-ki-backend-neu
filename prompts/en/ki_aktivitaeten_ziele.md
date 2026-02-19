**IMPORTANT – Length limit: Your response must not exceed 400 words. Cut rather than exceed.**

<!-- ki_aktivitaeten_ziele.md – v3.0 GOLD STANDARD+
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body> tags. NO markdown fences.

     PURPOSE:
       - Documentation of current AI activities (CURRENT state)
       - Derivation of real TARGET goals (next 12 months)
       - Strategic AI vision (2–3 years)

     MANDATORY VARIABLES:
       {{KI_PROJEKTE}}         // List or empty
       {{HAUPTLEISTUNG}}       // Text or empty
       {{TOOLS_AKTUELL}}       // List or empty

     Do not use:
       - No invented AI projects, no fictional tools.
       - No generic, unsubstantiated CURRENT statements.
       - No unrealistic goals.
       - Do not mention projects that are not contained in {{KI_PROJEKTE}} or {{TOOLS_AKTUELL}}.
       - No placeholder text ("Placeholder", "TODO" or other template markers).

     CURRENT‑STATE RULE:
       - If ALL three variables are empty → instead of a table: text "No AI projects in use yet."
       - If a mandatory variable is corrupted or unavailable → "Error: Data source not available."

     TARGET‑STATE RULE:
       - Derive goals exclusively from Quick Wins + Gamechanger + main service.
       - Max. 6 goals, chronological (Q2 → Q3 → Q4 → Q1 of following year).

     VISION:
       - Max. 4 strategic statements.
       - Do not invent numbers (e.g. MRR, ARR only if present in the briefing).

     OUTPUT:
       - Exactly one <section> block with:
         * <h2>AI Activities & Goals</h2>
         * Current state (table or note)
         * Target goals (unordered list)
         * Strategic AI vision (unordered list)
-->

<section class="section ai-activities">
  <h2>AI Activities &amp; Goals</h2>

  <!-- CURRENT STATE -->
  <h3>Current state (Current AI usage)</h3>

  <!-- Dynamic error handling -->
  <!-- If variables are corrupted/missing: -->
  <!-- <div class="error">Error: Data source not available.</div> -->

  <!-- If NO AI projects, NO tools &amp; NO main service -->
  <!-- <p>No AI projects in use yet.</p> -->

  <!-- Standard case: Table -->
  <table class="table">
    <thead>
      <tr>
        <th>Area</th>
        <th>Tool/System</th>
        <th>Usage</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <!-- Generated rows from {{KI_PROJEKTE}}, {{HAUPTLEISTUNG}}, {{TOOLS_AKTUELL}} -->
      <!-- Example for GPT:
           <tr>
             <td>Area A</td>
             <td>Tool X</td>
             <td>Short description</td>
             <td>Productive / In planning / Exploratory</td>
           </tr>
      -->
    </tbody>
  </table>

  <!-- TARGET GOALS -->
  <h3>Target goals (Next 12 months)</h3>
  <ul>
    <!-- GPT generates 3–6 goals, ordered by quarter.
         Examples:
         <li><strong>Q2:</strong> Integrate Quick Win A.</li>
         <li><strong>Q3:</strong> Start Gamechanger MVP.</li>
         <li><strong>Q4:</strong> Standardisation &amp; reporting cycle.</li>
    -->
  </ul>

  <!-- VISION CHAPTER -->
  <h3>Strategic AI vision (2–3 years)</h3>
  <ul>
    <!-- GPT generates 2–4 long‑term strategic visions.
         Examples:
         <li>AI‑assisted, standardised end‑to‑end processes in the area {{HAUPTLEISTUNG}}.</li>
         <li>Knowledge modules &amp; reusable workflows.</li>
         <li>Scalable, auditable AI architecture.</li>
    -->
  </ul>
</section>