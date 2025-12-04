Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: roi_tracking -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, kmu:1.15x=690) -->
<!--
GOAL: Compact ROI tracking framework for monthly AI project success measurement.

REQUIRED STRUCTURE (3 areas):
1. Define KPIs (3-5 measurable indicators)
2. Tracking method (how to measure, who measures, how often)
3. Review cycle (when to evaluate, how to adjust)

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: 2-3 simple KPIs (time savings, cost savings), self-tracking, no dashboards
- team: 3-4 KPIs including quality improvement, monthly team review
- sme: 4-5 KPIs including scaling potential, structured KPI review with project lead

SIZE-AWARE RESPONSIBILITIES:
- solo: "yourself", "owner (you)"
- team: "project lead", "team lead"
- sme: "project manager", "controlling", "KPI owner"

ANTI-REDUNDANCY:
- ROI Tracking complements Business Case, doesn't repeat CAPEX/OPEX/Payback numbers
- Focus on ONGOING measurement, not initial calculation
- No overlap with Next Actions (concrete 30-day actions there)

STYLE:
- Text length: 100-150 words
- Concrete and actionable
- No abstract management jargon

Do not use:
- No placeholders or template markers
- No repetition of Business Case numbers
- No unrealistic KPIs for company size
-->

<section class="section roi-tracking">
  <h2>ROI Tracking: Monthly Success Measurement</h2>

  <p>
    Structured tracking ensures project success for
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="tracking-framework">
    <h4>1. Define Core KPIs</h4>
    <table class="table">
      <thead>
        <tr>
          <th>KPI</th>
          <th>Description</th>
          <th>Measurement</th>
          <th>Target</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Time Saved</strong></td>
          <td>Hours per month through AI automation</td>
          <td>Before-after comparison</td>
          <td>+10-20%</td>
        </tr>
        <tr>
          <td><strong>Error Rate</strong></td>
          <td>Reduction in manual errors</td>
          <td>Sample checks</td>
          <td>-30%</td>
        </tr>
        <tr>
          <td><strong>Output Increase</strong></td>
          <td>More results with same effort</td>
          <td>Quantity measurement</td>
          <td>+15-25%</td>
        </tr>
        <tr>
          <td><strong>Cost Savings</strong></td>
          <td>Direct savings from automation</td>
          <td>Cost comparison</td>
          <td>Individual</td>
        </tr>
      </tbody>
    </table>

    <h4>2. Tracking Method</h4>
    <ul>
      <li><strong>Tool:</strong> Simple Excel/Google Sheet or project management tool</li>
      <li><strong>Frequency:</strong> Weekly brief entry, monthly evaluation</li>
      <li><strong>Responsible:</strong> Project lead or management</li>
    </ul>

    <h4>3. Review Cycle</h4>
    <ul>
      <li><strong>Monthly:</strong> KPI evaluation, trend analysis</li>
      <li><strong>Quarterly:</strong> Goal adjustment, lessons learned</li>
      <li><strong>Decision:</strong> Scale, optimize, or pivot</li>
    </ul>
  </div>

  <p class="small muted">
    Tip: Start with 2-3 KPIs and expand gradually.
    Consistency matters more than perfection.
  </p>
</section>
