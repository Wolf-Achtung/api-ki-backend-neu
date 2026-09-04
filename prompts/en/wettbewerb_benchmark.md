**IMPORTANT – Length limit: Your response must not exceed 700 words. Cut rather than exceed.**

<!-- PLATIN++ PROMPT v5.3 - SPRINT N -->
<!-- SECTION: wettbewerb_benchmark -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{report_date}}, {{score_gesamt}}, {{score_befaehigung}}, {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 2500 (solo:0.8x=2000, team:1.0x=2500, kmu:1.15x=2875) -->
<!-- RESEARCH: Can integrate market data from {{RESEARCH_PROVENANCE_HTML}} -->
<!--
PURPOSE: Position the score against internal guide values (Ø guide value and top-10% guide value).

GUIDE VALUES (DO NOT CHANGE!) — internal synthesis, not a measurement, not a study (KIS-1294).
Call them "guide value" in the text, never "industry average", "study" or "assessments":
  Overall: Ø 65, Top 10% = 82
  Enablement: Ø 68, Top 10% = 85
  Governance: Ø 58, Top 10% = 78
  Security: Ø 62, Top 10% = 80
  Value Creation: Ø 70, Top 10% = 88

SCORE LOGIC:
  > Top 10% → "well above the guide value"
  between Ø and Top 10% → "above the guide value"
  < Ø → "below the guide value"

PERSONA VARIATIONS (SIZE-AWARE STRATEGY):
- solo: personal routines, pragmatic standards, direct benefit effects
- team: roles, coordination, shared workflows & reviews
- kmu: cross-functional coordination, governance, scalable processes

BRANCH MODIFIERS:
  FINANCE/HEALTH/PUBLIC SECTOR = Focus on Governance & Security
  MARKETING/CREATIVE = Focus on Value Creation & Enablement
  INDUSTRY/PRODUCTION = Focus on Data Quality & Process Integration
  E-COMMERCE/RETAIL = Focus on Consistency, Data Feeds, Automation
  MEDIA/CREATIVE by segment: post/audio = throughput and rights chain; publishing/agency = approvals and labelling; games = localisation and live ops

ANTI-REDUNDANCY:
- Benchmark data presented HERE in full
- In other sections only reference the benchmark

SPRINT N - SOLO PERSONA RULES (STRICT!):
{% if COMPANY_SIZE == "solo" %}
DO NOT USE for Solo:
- "build team" → instead: "expand capacity"
- "employee" → instead: "resources"
- "teams" → instead: "your peer group"
- "department" → instead: "work area"
Use phrasing without team/department terms!
{% endif %}
-->

<section class="section competition-benchmark">
  <h2>Competition &amp; Benchmarking</h2>

  <p>
    <strong>Data basis:</strong> Internal guide values (synthesis 2024/25, not a measurement) for
    <strong>{{BRANCHE_LABEL}}</strong>, as of <strong>{{report_date}}</strong>.
  </p>

  <h3>Score Comparison (Company vs. guide value)</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Category</th>
        <th>Your Score</th>
        <th>Ø guide value</th>
        <th>Top&nbsp;10%</th>
        <th>Position</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Overall</td>
        <td>{{score_gesamt}}</td>
        <td>65</td>
        <td>82</td>
        <td>
          <!-- automatically derivable -->
          {% if (score_gesamt|default(0)) > 82 %}well above the guide value
          {% elif (score_gesamt|default(0)) > 65 %}above the guide value
          {% else %}below the guide value{% endif %}
        </td>
      </tr>

      <tr>
        <td>Enablement</td>
        <td>{{score_befaehigung}}</td>
        <td>68</td>
        <td>85</td>
        <td>
          {% if (score_befaehigung|default(0)) > 85 %}well above the guide value
          {% elif (score_befaehigung|default(0)) > 68 %}above the guide value
          {% else %}below the guide value{% endif %}
        </td>
      </tr>

      <tr>
        <td>Governance</td>
        <td>{{score_governance}}</td>
        <td>58</td>
        <td>78</td>
        <td>
          {% if (score_governance|default(0)) > 78 %}well above the guide value
          {% elif (score_governance|default(0)) > 58 %}above the guide value
          {% else %}below the guide value{% endif %}
        </td>
      </tr>

      <tr>
        <td>Security</td>
        <td>{{score_sicherheit}}</td>
        <td>62</td>
        <td>80</td>
        <td>
          {% if (score_sicherheit|default(0)) > 80 %}well above the guide value
          {% elif (score_sicherheit|default(0)) > 62 %}above the guide value
          {% else %}below the guide value{% endif %}
        </td>
      </tr>

      <tr>
        <td>Value Creation</td>
        <td>{{score_nutzen}}</td>
        <td>70</td>
        <td>88</td>
        <td>
          {% if (score_nutzen|default(0)) > 88 %}well above the guide value
          {% elif (score_nutzen|default(0)) > 70 %}above the guide value
          {% else %}below the guide value{% endif %}
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Your Biggest Gaps</h3>
  <p>
    The following areas show the largest distance to the guide value and offer
    correspondingly high improvement potential:
  </p>
  <ul>
    {% if (score_befaehigung|default(0)) < 68 %}
      <li><strong>Enablement:</strong> significant gap compared to the Ø guide value ({{score_befaehigung}} vs. 68).</li>
    {% endif %}
    {% if (score_governance|default(0)) < 58 %}
      <li><strong>Governance:</strong> significant gap compared to the Ø guide value ({{score_governance}} vs. 58).</li>
    {% endif %}
    {% if (score_sicherheit|default(0)) < 62 %}
      <li><strong>Security:</strong> significant gap compared to the Ø guide value ({{score_sicherheit}} vs. 62).</li>
    {% endif %}
    {% if (score_nutzen|default(0)) < 70 %}
      <li><strong>Value Creation:</strong> significant gap compared to the Ø guide value ({{score_nutzen}} vs. 70).</li>
    {% endif %}
  </ul>

  <h3>Your Strongest Strengths</h3>
  <p>
    These areas are noticeably above the guide value and can serve as a
    foundation for further development:
  </p>
  <ul>
    {% if (score_befaehigung|default(0)) > 68 %}
      <li><strong>Enablement:</strong> noticeable lead over guide value ({{score_befaehigung}} vs. 68).</li>
    {% endif %}
    {% if (score_governance|default(0)) > 58 %}
      <li><strong>Governance:</strong> noticeable lead over guide value ({{score_governance}} vs. 58).</li>
    {% endif %}
    {% if (score_sicherheit|default(0)) > 62 %}
      <li><strong>Security:</strong> noticeable lead over guide value ({{score_sicherheit}} vs. 62).</li>
    {% endif %}
    {% if (score_nutzen|default(0)) > 70 %}
      <li><strong>Value Creation:</strong> noticeable lead over guide value ({{score_nutzen}} vs. 70).</li>
    {% endif %}
  </ul>

  <h3>Catch-Up Strategy (Next 12 Months – size-aware)</h3>
  <ol>
    <li>
      <strong>Q2:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Focus on your personal standardisation: document 2–3 core processes, use simple AI checklists for yourself.
      {% elif COMPANY_SIZE == "team" %}
        Clarify roles (AI owner, reviewer), uniform templates and short review loops.
      {% else %}
        Define cross-functional pilot area (e.g., marketing, production, back office); anchor first governance standards.
      {% endif %}
    </li>

    <li>
      <strong>Q3:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Workflow optimization: solidify your AI-supported routines, integrate your most important industry tools.
      {% elif COMPANY_SIZE == "team" %}
        Shared documentation + regular team reviews; reduce tool duplication.
      {% else %}
        Harmonize area-specific processes, clear data interfaces, uniform approvals.
      {% endif %}
    </li>

    <li>
      <strong>Q4:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Routine consolidation: recurring usage + annual planning for the coming year.
      {% elif COMPANY_SIZE == "team" %}
        Scaling in the team: automated quality control + uniform AI communication.
      {% else %}
        Scaling program: expand governance, audit routines, cross-functional standards.
      {% endif %}
    </li>
  </ol>

  <p>
    <strong>Strategic target corridor:</strong>
    {% if (score_gesamt|default(0)) >= 80 %}
      Towards top 5% of the industry.
    {% elif (score_gesamt|default(0)) >= 60 %}
      Towards top 10% of the industry.
    {% else %}
      Towards top 25% – focus on stabilization and structured development.
    {% endif %}
  </p>
</section>