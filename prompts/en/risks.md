Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G5 -->
<!-- SECTION: risks -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{score_governance}}, {{score_sicherheit}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 3000 (solo:0.8x=2400, team:1.0x=3000, sme:1.15x=3450) -->
<!--
GOAL: 5 sections with 120-160 words each (= 600-800 words total).

SHORT LABELS (MANDATORY!):
- {{BRANCH_CORE_LABEL}} = Industry in 8-12 words
- {{BRANCH_CONTEXT_LABEL}} = Industry in 4-6 words
- {{OFFERING_LABEL}} = Main service in 6-10 words

STRUCTURE (5 mandatory sections):
  H3 1. Strategic and Organizational Risks (4 risks + measures)
  H3 2. Data, Security and Compliance Risks (4 risks + measures)
  H3 3. Quality, Transparency and Acceptance Risks (4 risks + measures)
  H3 4. Dependencies, Operational and Vendor Risks (4 risks + measures)
  H3 5. Risk Matrix (Table with 5 rows)

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: personal overload, single point of failure, no backup
- team: role clarity, coordination, knowledge silos
- sme: governance, processes, documentation, compliance

ANTI-REDUNDANCY (STRICT!):
- Do NOT repeat risks in guardrails section (→ cross-reference)
- Keep measures brief, do not repeat in org_change (→ cross-reference)
- When overlapping: use cross-reference

SPRINT G5 - PERSONA HARD-GUARDS (STRICT!):
{% if COMPANY_SIZE == "solo" %}
SOLO MODE - FORBIDDEN:
- "Team/Teams/Department/Employees" → do not use
- "Division" → "Work area"
{% elif COMPANY_SIZE == "team" %}
TEAM MODE - FORBIDDEN:
- "Division/Unit/Corporate" → do not use
- "Department" → "Area"
- Solo terms: "Individual", "alone"
{% else %}
SME MODE - FORBIDDEN:
- "Corporate/Division/Unit" → do not use
- Solo terms: "Individual", "alone"
{% endif %}

RULES:
- Actively interpret scores
- Industry-specific compliance for regulated industries
- Factual, concrete, no platitudes

=============================================================================
ANTI-TEXT-DESERT RULES v2.0 (AGGRESSIVE - MANDATORY!)
=============================================================================
PROBLEM: Risk bullets become mini-essays. UNREADABLE!
SOLUTION: STRICT word limits per risk bullet.

HARD LIMITS PER RISK BULLET:
┌─────────────────────────────────────────────────────────┐
│ Part                  │ Max Words  │ Max Sentences      │
├─────────────────────────────────────────────────────────┤
│ Risk Description      │ 15 words   │ 1 sentence         │
│ Measure               │ 12 words   │ 1 sentence         │
│ Total per Bullet      │ 30 words   │ 2 sentences        │
└─────────────────────────────────────────────────────────┘

FORMAT PER RISK (MANDATORY - NO DEVIATION!):
<li><strong>[Risk in 2-4 words]:</strong> [Problem in 10-15 words].
<strong>Measure:</strong> [Solution in 10-12 words].</li>

FORBIDDEN (STRICT!):
❌ Risk descriptions over 15 words
❌ Measures over 12 words
❌ Explanations with "whereby", "since", "because", "so that"
❌ Nested sentences
❌ More than 1 measure per risk
❌ Running text below/above the bullet list

EXAMPLE - NOT LIKE THIS:
❌ "A significant risk lies in the lack of transparency regarding
    AI-supported decision processes, which can lead to distrust among customers
    and jeopardize long-term acceptance of the solutions..." [= 35 words = REJECTED!]

EXAMPLE - LIKE THIS:
✅ <li><strong>Lack of transparency:</strong> Customers don't understand AI decisions.
   <strong>Measure:</strong> Document AI methods simply.</li> [= 12 words = PERFECT!]

SECTION LIMITS:
- Per risk category: Exactly 4 bullets (no more, no less)
- No introductory texts between heading and list
- No closing texts after the list
=============================================================================
-->

<section class="section risks">
  <h2>Key Risks When Using AI in {{OFFERING_LABEL}}</h2>

  <p>
    Governance Score: <strong>{{score_governance}}/100</strong>,
    Security Score: <strong>{{score_sicherheit}}/100</strong>.
  </p>

  <h3>1. Strategic and Organizational Risks</h3>
  <ul>
    <li>
      <strong>Unclear objectives:</strong>
      Risk of isolated solutions. Measure: Define 2–3 prioritized use cases.
    </li>
    <li>
      <strong>Key person dependency:</strong>
      Knowledge concentration. Measure: Documentation + checklists.
    </li>
    <li>
      <strong>Unclear roles:</strong>
      Unclear responsibilities. Measure: Appoint AI responsible person.
    </li>
    <li>
      <strong>Overload:</strong>
      AI "on top" fails. Measure: Small pilots with clear scope.
    </li>
  </ul>

  <h3>2. Data, Security and Compliance Risks</h3>
  <ul>
    <li>
      <strong>Data control:</strong>
      Sensitive data in AI systems. Measure: Guidelines + access restrictions.
    </li>
    <li>
      <strong>Security gaps:</strong>
      Score {{score_sicherheit}}/100. Measure: Security concept + regular reviews.
    </li>
    <li>
      <strong>Legal responsibility:</strong>
      Data protection/copyright. Measure: Named responsibility + guidelines.
    </li>
    <li>
      <strong>Transparency:</strong>
      Loss of trust with unclear AI usage. Measure: Disclosures + documentation.
    </li>
  </ul>

  <h3>3. Quality, Transparency and Acceptance Risks</h3>
  <ul>
    <li>
      <strong>Inconsistent results:</strong>
      Quality variance without templates. Measure: Uniform templates + reviews.
    </li>
    <li>
      <strong>Over-reliance:</strong>
      Hallucinations in customer documents. Measure: Review requirement + checklists.
    </li>
    <li>
      <strong>Acceptance issues:</strong>
      Resistance with unclear benefit. Measure: Pilots + gather feedback.
    </li>
    <li>
      <strong>Traceability:</strong>
      Unclear AI role. Measure: Documentation "Where does AI support?".
    </li>
  </ul>

  <h3>4. Dependencies, Operational and Vendor Risks</h3>
  <ul>
    <li>
      <strong>Tool dependency:</strong>
      Vendor lock-in. Measure: Fallback scenarios + data export.
    </li>
    <li>
      <strong>Service provider terms:</strong>
      Gaps in liability/SLA. Measure: Clear contracts + response times.
    </li>
    <li>
      <strong>Emergency planning:</strong>
      No recovery defined. Measure: Backups + emergency contacts.
    </li>
    <li>
      <strong>Tool complexity:</strong>
      Too many parallel tools. Measure: Consolidation to core solutions.
    </li>
  </ul>

  <h3>5. Risk Matrix – Overview of Key Risks</h3>
  <p>
    The following overview shows the main risk areas by probability of occurrence
    and impact strength to facilitate prioritization of countermeasures.
  </p>
  <table class="table">
    <thead>
      <tr>
        <th>Risk Area</th>
        <th>Typical Impact</th>
        <th>Probability</th>
        <th>Impact Strength</th>
        <th>Recommended Focus Measures</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Strategy & Organization</td>
        <td>Fragmentation, lack of impact, daily frustration</td>
        <td>medium</td>
        <td>high</td>
        <td>Clear objectives, prioritized use cases, named AI responsibility.</td>
      </tr>
      <tr>
        <td>Data & Security</td>
        <td>Lack of transparency, potential data protection violations</td>
        <td>medium to high</td>
        <td>high</td>
        <td>Brief data usage guideline, access and password concept, service documentation.</td>
      </tr>
      <tr>
        <td>Quality & Acceptance</td>
        <td>Inconsistent results, distrust or blind trust in AI</td>
        <td>medium</td>
        <td>medium to high</td>
        <td>Template standards, review loops, clear communication of benefits and limits.</td>
      </tr>
      <tr>
        <td>Dependencies & Operations</td>
        <td>Operational interruptions, additional costs, lock-in effects</td>
        <td>low to medium</td>
        <td>medium</td>
        <td>Fallback scenarios, tool landscape consolidation, clear vendor agreements.</td>
      </tr>
      <tr>
        <td>AI-specific: Hallucinations</td>
        <td>Incorrect information in customer documents, reputation damage</td>
        <td>medium to high</td>
        <td>high</td>
        <td>Four-eyes principle, fact-checking, clear quality guidelines for AI output.</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    This risk analysis shows the key action areas for AI in
    {{OFFERING_LABEL}}. In the next step, risks should be prioritized
    by probability and impact.
    Details on measure planning → see Roadmap and Governance section.
  </p>
</section>

<!-- DEV: PDF-SLIMDOWN v2.0 - Target: 600-800 words, compact but complete -->

<!-- ZERO-LEAK POLICY (N4.6) -->
<!--
FORBIDDEN – NEVER USE:
- No questions to the reader ("Do you have questions?", "Would you like to learn more?")
- No prompts ("If you would like...", "Contact us...")
- No assistant language ("I can help you...", "I'm happy to explain...")
- No offers ("If needed...", "If desired...")
- No interactive elements ("Click here...", "Select...")
- No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
- No meta-comments ("This section...", "In the following...")

The output is a FINAL REPORT SECTION, not a conversation.
-->
