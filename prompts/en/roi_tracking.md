<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: roi_tracking -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE‑AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN‑BUDGET: 600 (solo:0.8x=480, team:1.0x=600, kmu:1.15x=690) -->
<!--
GOAL: Compact ROI tracking framework for monthly success measurement of AI projects.

MANDATORY STRUCTURE (3 sections):
1. Define KPIs (3–5 measurable metrics)
2. Tracking method (how to measure, who measures, how often)
3. Review cycle (when to evaluate, how to adjust)

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: 2–3 simple KPIs (time savings, cost savings), self‑tracking, no dashboards
- team: 3–4 KPIs including quality improvement, team review monthly
- kmu: 4–5 KPIs including scaling potential, structured KPI review with project lead

SIZE‑AWARE RESPONSIBILITIES:
- solo: “You yourself”, “Managing director (you)”
- team: “Project responsible”, “Team lead”
- kmu: “Project manager”, “Controlling”, “KPI responsible”

ANTI‑REDUNDANCY:
- ROI tracking supplements the business case; do not repeat CAPEX/OPEX/payback numbers
- Focus on ONGOING measurement, not initial calculation
- No overlap with Next Actions (there: specific 30‑day actions)

STYLE:
- Text length: 100–150 words
- Concrete and actionable
- No abstract management phrases

Do not use:
- No placeholders or template markers
- No repetition of business case numbers
- No unrealistic KPIs for the company size
-->

<section class="section roi-tracking">
  <h2>ROI tracking: monthly success measurement</h2>

  <p>
    A structured tracking framework secures project success for
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="tracking-framework">
    <h4>1. Define core KPIs</h4>
    <table class="table">
      <thead>
        <tr>
          <th>KPI</th>
          <th>Description</th>
          <th>Measurement method</th>
          <th>Target value</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Time savings</strong></td>
          <td>Hours per month saved through AI automation</td>
          <td>Before/after comparison</td>
          <td>+10–20 %</td>
        </tr>
        <tr>
          <td><strong>Error rate</strong></td>
          <td>Reduction of manual errors</td>
          <td>Sample checking</td>
          <td>‑30 %</td>
        </tr>
        <tr>
          <td><strong>Output increase</strong></td>
          <td>More results with the same effort</td>
          <td>Volume measurement</td>
          <td>+15–25 %</td>
        </tr>
        <tr>
          <td><strong>Cost savings</strong></td>
          <td>Direct savings through automation</td>
          <td>Cost comparison</td>
          <td>Individual</td>
        </tr>
      </tbody>
    </table>

    <h4>2. Tracking method</h4>
    <ul>
      <li><strong>Tool:</strong> Simple Excel/Google sheet or project management tool</li>
      <li><strong>Frequency:</strong> Weekly quick entry, monthly evaluation</li>
      <li><strong>Responsible:</strong> Project responsible or managing director</li>
    </ul>

    <h4>3. Review cycle</h4>
    <ul>
      <li><strong>Monthly:</strong> KPI evaluation, trend analysis</li>
      <li><strong>Quarterly:</strong> Adjust targets, lessons learned</li>
      <li><strong>Decision:</strong> Scale, optimise or pivot</li>
    </ul>
  </div>

  <p class="small muted">
    Tip: Start with two to three KPIs and expand gradually. Consistency is more important than perfection.
  </p>
</section>