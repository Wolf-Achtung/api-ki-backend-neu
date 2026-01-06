<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: kickoff_vorlage -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE‑AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN‑BUDGET: 700 (solo:0.8x=560, team:1.0x=700, kmu:1.15x=805) -->
<!--
GOAL: Structured kickoff template for starting an AI project.

MANDATORY STRUCTURE:
1. Agenda (7 points with times)
2. Preparation questionnaire (4 areas)
3. Result template

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: Quick self‑check, 30 minutes, focus on quick wins
- team: Joint workshop, clarify roles, 60–90 minutes
- kmu: Structured kickoff, involve stakeholders, 2–3 hours

SIZE‑AWARE RESPONSIBILITIES:
- solo: “You yourself”, no complex roles
- team: “Project lead”, “team”, peer alignment
- kmu: “Project management”, “department”, “IT”, “controlling”

ANTI‑REDUNDANCY:
- Kickoff HERE, not in the 90‑day roadmap (that is for initial implementation steps)
- Focus on PREPARATION, not implementation
- No overlap with Quick Wins (there: concrete first actions)

STYLE:
- Text length: 120–180 words
- Practical, immediately usable
- No theory, only structure

Do not use:
- No placeholders or template markers
- No repetition of roadmap content
- No unrealistic time specifications for the company size
-->

<section class="section kickoff-template">
  <h2>Kickoff template: Starting an AI project</h2>

  <p>
    Structured project start for
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="kickoff-content">
    <h4>Agenda (customisable)</h4>
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
        <tr><td>1</td><td>Welcome & goals</td><td>5–10 min</td><td>Project lead</td></tr>
        <tr><td>2</td><td>Current situation & pain points</td><td>15–20 min</td><td>All</td></tr>
        <tr><td>3</td><td>Identify AI potentials</td><td>15–20 min</td><td>Department/subject area</td></tr>
        <tr><td>4</td><td>Clarify data situation</td><td>10–15 min</td><td>IT / data owners</td></tr>
        <tr><td>5</td><td>Define quick wins</td><td>15–20 min</td><td>All</td></tr>
        <tr><td>6</td><td>Roles & responsibilities</td><td>10 min</td><td>Project lead</td></tr>
        <tr><td>7</td><td>Next steps & timeline</td><td>10 min</td><td>Project lead</td></tr>
      </tbody>
    </table>

    <h4>Preparation questionnaire</h4>
    <ul>
      <li><strong>Goals:</strong> What should be improved/faster/cheaper through AI?</li>
      <li><strong>Data:</strong> Which data is digitally available? Are there data‑protection restrictions?</li>
      <li><strong>Resources:</strong> Who has time? What budget is available?</li>
      <li><strong>Roles:</strong> Who decides? Who implements? Who reviews?</li>
    </ul>

    <h4>Document after the kickoff</h4>
    <ul>
      <li>Project goal (clearly formulated)</li>
      <li>Top 3 pain points</li>
      <li>First quick win + responsible person</li>
      <li>Next milestone + date</li>
    </ul>
  </div>

  <p class="small muted">
    Tip: Keep the kickoff short, document results immediately, plan follow‑up.
  </p>
</section>