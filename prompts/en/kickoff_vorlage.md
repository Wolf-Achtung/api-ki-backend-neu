Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: kickoff_template -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 700 (solo:0.8x=560, team:1.0x=700, kmu:1.15x=805) -->
<!--
GOAL: Structured kickoff template for starting an AI project.

REQUIRED STRUCTURE:
1. Agenda (7 items with times)
2. Preparation questionnaire (4 areas)
3. Results template

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: Quick self-check, 30 min, focused on quick wins
- team: Collaborative workshop, clarify roles, 60-90 min
- sme: Structured kickoff, stakeholder involvement, 2-3 hours

SIZE-AWARE RESPONSIBILITIES:
- solo: "yourself", no complex roles
- team: "project lead", "team", peer alignment
- sme: "project management", "domain experts", "IT", "controlling"

ANTI-REDUNDANCY:
- Kickoff HERE, not in Roadmap 90d (implementation steps there)
- Focus on PREPARATION, not implementation
- No overlap with Quick Wins (concrete first actions there)

STYLE:
- Text length: 120-180 words
- Practical, immediately usable
- No theory, structure only

Do not use:
- No placeholders or template markers
- No repetition of roadmap content
- No unrealistic timeframes for company size
-->

<section class="section kickoff-template">
  <h2>Kickoff Template: Starting Your AI Project</h2>

  <p>
    Structured project start for
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="kickoff-content">
    <h4>Agenda (Adjustable)</h4>
    <table class="table">
      <thead>
        <tr>
          <th>#</th>
          <th>Topic</th>
          <th>Duration</th>
          <th>Responsible</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>1</td><td>Welcome & Objectives</td><td>5-10 min</td><td>Project Lead</td></tr>
        <tr><td>2</td><td>Current State & Pain Points</td><td>15-20 min</td><td>All</td></tr>
        <tr><td>3</td><td>Identify AI Potential</td><td>15-20 min</td><td>Domain Experts</td></tr>
        <tr><td>4</td><td>Data Assessment</td><td>10-15 min</td><td>IT / Data Owners</td></tr>
        <tr><td>5</td><td>Define Quick Wins</td><td>15-20 min</td><td>All</td></tr>
        <tr><td>6</td><td>Roles & Responsibilities</td><td>10 min</td><td>Project Lead</td></tr>
        <tr><td>7</td><td>Next Steps & Timeline</td><td>10 min</td><td>Project Lead</td></tr>
      </tbody>
    </table>

    <h4>Preparation Questionnaire</h4>
    <ul>
      <li><strong>Goals:</strong> What should AI make better/faster/cheaper?</li>
      <li><strong>Data:</strong> What data is available digitally? Any privacy restrictions?</li>
      <li><strong>Resources:</strong> Who has time? What budget is available?</li>
      <li><strong>Roles:</strong> Who decides? Who implements? Who reviews?</li>
    </ul>

    <h4>Document After Kickoff</h4>
    <ul>
      <li>Project goal (clearly stated)</li>
      <li>Top 3 pain points</li>
      <li>First quick win + responsible person</li>
      <li>Next milestone + date</li>
    </ul>
  </div>

  <p class="small muted">
    Tip: Keep kickoff short, document results immediately, plan follow-up.
  </p>
</section>
