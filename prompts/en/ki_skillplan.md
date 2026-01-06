<!-- ki_skillplan.md – v1.1 PLATIN++ SPRINT N (AI skill roadmap)
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body>. NO markdown fences.

     GOAL:
     - Clear, comprehensible skill‑building plan for AI usage.
     - 3 levels: Basic → Pro → Expert (with time frames).
     - Practical, jargon‑free, immediately actionable.
     - Text length: 100–150 words (STRICTLY FOLLOWED!)

     AVAILABLE VARIABLES:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{COMPANY_SIZE}}

     SIZE‑AWARE LOGIC:
       SOLO: focus on self‑learning, online resources, learning by doing
       TEAM: joint learning, peer reviews, internal workshops
       KMU: structured training, external trainers, certifications

     MANDATORY STRUCTURE (3 levels):
     1. Basic (0–3 months)
        - Prompting foundations
        - Text automation (emails, templates)
        - First workflows to test
     2. Pro (3–9 months)
        - Workflow automation
        - Data quality & structuring
        - Build analysis chains
     3. Expert (9–18 months)
        - RAG (retrieval‑augmented generation)
        - AI agents & automation
        - Governance & quality assurance

     STYLE:
       - Very understandable, no technical terms without explanation
       - Concrete examples instead of theory
       - Motivating but realistic

     Do not use:
       - No placeholders or template markers
       - No technical pipeline jargon
       - No exaggerated promises

     SPRINT N - SOLO PERSONA RULES (STRICT!):
     {% if COMPANY_SIZE == "solo" %}
     NOT TO USE for Solo:
     - "build a team" → instead: "expand capacity"
     - "train employees" → instead: "develop yourself"
     - "teams" → instead: "capacities"
     - "department" → instead: "work area"
     - "division" → instead: "work field"
     Use wording without team/department references!
     {% endif %}
-->

<section class="section skill-plan">
  <h2>AI skill roadmap</h2>

  <p>
    For <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>
    a structured skill‑building plan in three stages is recommended.
  </p>

  <div class="skill-levels">
    <div class="level basis">
      <h4>Stage 1: Basic (0–3 months)</h4>
      <ul>
        <li><strong>Learn prompting:</strong> formulate clear instructions, check results</li>
        <li><strong>Text automation:</strong> email templates, standard replies, document drafts</li>
        <li><strong>First tests:</strong> try AI in everyday work, learn its limits</li>
      </ul>
    </div>

    <div class="level pro">
      <h4>Stage 2: Pro (3–9 months)</h4>
      <ul>
        <li><strong>Automation:</strong> speed up recurring processes with AI support</li>
        <li><strong>Data quality:</strong> structured inputs, consistent formats, checking routines</li>
        <li><strong>Analysis chains:</strong> multi‑step tasks (e.g. research → summary → recommendations)</li>
      </ul>
    </div>

    <div class="level expert">
      <h4>Stage 3: Expert (9–18 months)</h4>
      <ul>
        <li><strong>RAG systems:</strong> connect AI with your own documents/databases</li>
        <li><strong>AI agents:</strong> automated assistants for complex tasks</li>
        <li><strong>Governance:</strong> quality assurance, policies, continuous improvement</li>
      </ul>
    </div>
  </div>

  <p class="small muted">
    Tip: Build each stage before starting the next – solid foundations enable faster progress.
  </p>
</section>