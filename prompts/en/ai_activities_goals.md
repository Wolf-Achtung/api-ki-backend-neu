Developer:
<!-- ai_activities_goals.md – v3.0 GOLD STANDARD+
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body>. NO Markdown fences.

     PURPOSE:
       - Documentation of current AI activities (AS-IS)
       - Derivation of realistic TARGET goals (next 12 months)
       - Strategic AI vision (2–3 years)

     MANDATORY VARIABLES:
       {{KI_PROJEKTE}}         // List or empty
       {{HAUPTLEISTUNG}}       // Text or empty
       {{TOOLS_AKTUELL}}       // List or empty

     PROHIBITED:
       - No invented AI projects, no fantasy tools.
       - No generic, unsubstantiated AS-IS statements.
       - No unrealistic goals.
       - Do not name projects that are not in {{KI_PROJEKTE}} or {{TOOLS_AKTUELL}}.
       - No placeholder texts ("placeholder", "free text field", "TODO").

     AS-IS RULE:
       - If ALL three variables are empty → instead of table: Text "No AI projects currently in use."
       - If a mandatory variable is faulty or unreadable → "Error: Data source not available."

     TARGET RULE:
       - Derive goals exclusively from Quick Wins + Gamechangers + Main Service.
       - Max. 6 goals, chronological (Q2 → Q3 → Q4 → Q1 following year).

     VISION:
       - Max. 4 strategic statements.
       - Do not invent numbers (MRR, ARR only if present in briefing).

     OUTPUT:
       - Exactly one <section> block with:
         * <h2>AI Activities & Goals</h2>
         * AS-IS status (table or notice)
         * TARGET goals (UL)
         * Strategic AI Vision (UL)
-->

<section class="section ai-activities">
  <h2>AI Activities &amp; Goals</h2>

  <!-- AS-IS STATUS -->
  <h3>AS-IS Status (Current AI Usage)</h3>

  <!-- Dynamic error handling -->
  <!-- If variables are corrupted/missing: -->
  <!-- <div class="error">Error: Data source not available.</div> -->

  <!-- If NO AI projects, NO Tools & NO Main Service -->
  <!-- <p>No AI projects currently in use.</p> -->

  <!-- Default case: Table -->
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
      <!-- Rows generated from {{KI_PROJEKTE}}, {{HAUPTLEISTUNG}}, {{TOOLS_AKTUELL}} -->
      <!-- Example for GPT:
           <tr>
             <td>Area A</td>
             <td>Tool X</td>
             <td>Brief description</td>
             <td>Productive / In Planning / Exploratory</td>
           </tr>
      -->
    </tbody>
  </table>

  <!-- TARGET GOALS -->
  <h3>TARGET Goals (Next 12 Months)</h3>
  <ul>
    <!-- GPT generates 3–6 goals, ordered by quarter.
         Examples:
         <li><strong>Q2:</strong> Integrate Quick Win A.</li>
         <li><strong>Q3:</strong> Launch Gamechanger MVP.</li>
         <li><strong>Q4:</strong> Standardization & reporting cycle.</li>
    -->
  </ul>

  <!-- VISION CHAPTER -->
  <h3>Strategic AI Vision (2–3 Years)</h3>
  <ul>
    <!-- GPT generates 2–4 long-term strategic visions.
         Examples:
         <li>AI-powered, standardized end-to-end processes in {{HAUPTLEISTUNG}}.</li>
         <li>Knowledge modules & reusable workflows.</li>
         <li>Scalable, auditable AI architecture.</li>
    -->
  </ul>
</section>
