**IMPORTANT – Length limit: Your response must not exceed 1100 words. Cut rather than exceed.**

Developer:
<!-- unternehmensprofil_markt.md – v5.0 GOLD STANDARD+ (branch-aware, size-aware, context-integrated)
     Respond exclusively with valid HTML.
     NO <html>, <head> or <body>. NO Markdown fences.

     PURPOSE:
       - Precise company profile (industry, size, location, main service, business model).
       - Compact, generic market context ONLY from CONTEXT_BLOCK (no hallucination).
       - Industry-related AI potentials (2–4 typical use cases).
       - Competitive position depending on company size (solo/team/sme).
       - No invented numbers, names, market shares or specific competitors.

     AVAILABLE VARIABLES:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{BUNDESLAND_LABEL}}
       {{HAUPTLEISTUNG}}
       {{GESCHAEFTSMODELL_EVOLUTION}}

     IF A VARIABLE IS EMPTY OR FAULTY:
       - Use "Not specified" or a neutral generic substitute.
       - NEVER output <p class="error">...</p> in the final report.
       - Ensure the section remains meaningful and complete.

     RESEARCH-CONTEXT (CONTEXT_BLOCK):
       - GENERIC INFORMATION ALLOWED:
         - Industry trends
         - Typical pain points
         - Typical workflows
         - Typical tools
       - NOT ALLOWED:
         - Specific market shares, revenues, names of competitors
         - Exact growth rates, exact AI adoption rates
       - IF insufficient information available:
         - Write "Not specified" in the appropriate place.

     SIZE-AWARE LOGIC (COMPANY_SIZE ∈ {"solo","team","sme"}):
       SOLO:
         - Focus: Speed, flexibility, personal decision-making.
         - Challenges: Capacity, prioritization, dependence on one person.
         - AI leverage: Personal automation, assistants, templates.

       TEAM (2–10):
         - Focus: Collaborative work, shared knowledge, clear responsibilities.
         - Challenges: Resource scarcity, priority alignment, coordination.
         - AI leverage: Knowledge management, templates, unified workflows, common standards.

       SME (11–100):
         - Focus: Scalable processes, multiple areas, structured procedures.
         - Challenges: Coordination, data silos, internal alignment, governance.
         - AI leverage: Data-driven decisions, scaling, policies & governance.

     OUTPUT RULES:
       - Exactly one <section> block with the following blocks in this order:
         1) Company Profile
         2) Market Context & Trends
         3) AI Potential
         4) Competitive Position
       - NO placeholder texts in visible output (e.g., "Title …", "Example …").
       - No reference to CONTEXT_BLOCK or internal logic.
       - Tone: sober, factual, strategic, easily readable for management.

-->

<section class="section unternehmensprofil-markt">
  <h2>Company Profile &amp; Market Context</h2>

  <div class="profil-box">
    <h3>Company Profile</h3>
    <ul>
      <li><strong>Industry:</strong> {{BRANCHE_LABEL}}</li>
      <li><strong>Size:</strong> {{UNTERNEHMENSGROESSE_LABEL}}</li>
      <li><strong>Location:</strong> {{BUNDESLAND_LABEL}}</li>
      <li><strong>Main Service:</strong> {{HAUPTLEISTUNG}}</li>
      <li>
        <strong>Business Model:</strong>
        <!-- Business model evolution: if empty or "Not specified" → formulate neutrally -->
        {{GESCHAEFTSMODELL_EVOLUTION}}
      </li>
    </ul>
  </div>

  <div class="markt-context">
    <h3>Market Context &amp; Trends ({{BRANCHE_LABEL}})</h3>

    <p>
      The <strong>{{BRANCHE_LABEL}}</strong> industry is currently shaped by several
      recurring developments that also influence the use of AI in the area of
      <strong>{{HAUPTLEISTUNG}}</strong>. These include, depending on available information,
      increased digitalization, rising expectations for quality and speed, as well as
      growing pressure to make processes more efficient and data-driven.
      Where no reliable data is available, trends are noted as <em>not specified</em>.
    </p>

    <ul>
      <li><strong>Market Dynamics:</strong> If industry data is available in the context, briefly describe whether the market is stable, growing, or in transition; otherwise: <em>Not specified</em>.</li>
      <li><strong>AI Adoption:</strong> Typically, AI usage in {{BRANCHE_LABEL}} is increasing in areas such as analysis, text production, support, or decision support – without specific percentages; if no data available: <em>Not specified</em>.</li>
      <li><strong>Key Drivers:</strong> Industry-typical drivers include cost pressure, skills shortage, rising quality requirements, or regulatory demands; if no context information: <em>Not specified</em>.</li>
      <li><strong>Challenges:</strong> Common challenges include data quality, system interfaces, limited internal resources, or regulatory uncertainty; if not substantiated: <em>Not specified</em>.</li>
    </ul>
  </div>

  <div class="ki-potenzial">
    <h3>AI Potential for {{BRANCHE_LABEL}}</h3>
    <p>
      Based on typical workflows and pain points in the <strong>{{BRANCHE_LABEL}}</strong>
      industry, several generic AI application areas emerge for the process of
      <strong>{{HAUPTLEISTUNG}}</strong>. These can be derived without detailed specialist
      knowledge and serve as orientation for further development.
    </p>
    <ul>
      <li>Support for recurring tasks such as drafts, summaries, or standard analyses to save time and stabilize quality.</li>
      <li>Structuring and condensing existing information, e.g., from emails, documents, protocols, or specialist systems, to better prepare decisions.</li>
      <li>Quality and consistency checks of texts, data, or reports, aligned with industry-typical requirements and internal standards.</li>
    </ul>
  </div>

  <div class="wettbewerb">
    <h3>Competitive Position</h3>
    <p>
      Companies of size <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in the
      <strong>{{BRANCHE_LABEL}}</strong> industry often operate between specialized
      niche providers and larger market participants. The role of AI strongly depends
      on organizational structure and available capacities.
    </p>

    <ul>
      <li>
        <strong>Advantage:</strong>
        {% if COMPANY_SIZE == "solo" %}
          High flexibility and quick decision-making; AI adjustments can be implemented directly without lengthy coordination.
        {% elif COMPANY_SIZE == "team" %}
          Short communication paths and shared responsibility; new AI workflows can be tested and gradually refined within the team.
        {% else %}
          Greater scaling potential and more resources; AI solutions can be rolled out across multiple areas and systematically anchored.
        {% endif %}
      </li>
      <li>
        <strong>Disadvantage:</strong>
        {% if COMPANY_SIZE == "solo" %}
          Limited time and capacity; without clear prioritization, AI potential often remains untapped.
        {% elif COMPANY_SIZE == "team" %}
          Coordination effort and resource constraints; without clear roles, AI can get lost in daily operations.
        {% else %}
          Coordination overhead between teams and data silos; without governance, inconsistent solutions and duplicate structures may emerge.
        {% endif %}
      </li>
      <li>
        <strong>AI Leverage:</strong>
        {% if COMPANY_SIZE == "solo" %}
          Focused automation of recurring tasks and building personal AI-supported routines that quickly deliver noticeable relief.
        {% elif COMPANY_SIZE == "team" %}
          Shared templates, unified workflows, and knowledge management so all participants use AI similarly and learn from each other.
        {% else %}
          Establishing standardized processes, data-driven decisions, and clear policies to consistently scale AI across multiple areas.
        {% endif %}
      </li>
    </ul>
  </div>
</section>


<!-- ZERO-LEAK POLICY (N4.6) -->
<!--
FORBIDDEN – NEVER USE:
- No questions to the reader ("Do you have questions?", "Want to learn more?")
- No calls to action ("If you would like...", "Contact us...")
- No assistant language ("I can help you...", "Happy to explain...")
- No offers ("If needed...", "If desired...")
- No interactive elements ("Click here...", "Select...")
- No placeholders ("[Insert here]", "{{VARIABLE}}" except defined ones)
- No meta-comments ("This section...", "In the following...")

The output is a FINAL REPORT SECTION, not a conversation.
-->
