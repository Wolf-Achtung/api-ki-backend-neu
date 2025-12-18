Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: foerderprogramme (EN bridge) -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, FUNDING_PROGRAMMES_EU_CORE, FUNDING_PROGRAMMES -->
<!-- TOKEN-BUDGET: 1500 -->
<!--
PURPOSE: English-language funding overview for EN profiles requesting "foerderprogramme".
Bridge file for kmu_france and other EU-core EN profiles.

PRIORITY LOGIC:
  1. If FUNDING_PROGRAMMES_EU_CORE is present and non-empty → use EU core programmes
  2. Else if FUNDING_PROGRAMMES is present → use that
  3. Else → generic EU funding guidance

OUTPUT CONSTRAINTS:
  - 5-10 bullet points maximum
  - Short eligibility note
  - No German text in output
  - Professional, factual tone

ANTI-REDUNDANCY:
- This is the SOLE funding section for EN profiles using German section names
- Does NOT duplicate funding_eu_core.md or funding.md
-->

<section class="section funding-programmes">
  <h2>Funding Programmes</h2>

  <p>
    Based on your company profile as a <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in
    <strong>{{BRANCHE_LABEL}}</strong>, the following funding opportunities may support
    your AI and digitalisation initiatives:
  </p>

  {% if FUNDING_PROGRAMMES_EU_CORE %}
  <h3>EU Core Funding Programmes</h3>
  <ul class="funding-list compact">
    {% for p in FUNDING_PROGRAMMES_EU_CORE[:7] %}
    <li>
      <strong>{{ p.name_en or p.name }}</strong>
      {% if p.summary_en %} – {{ p.summary_en }}{% endif %}
      {% if p.funding_rate_en %} ({{ p.funding_rate_en }}){% endif %}
    </li>
    {% endfor %}
  </ul>

  <p class="eligibility-note">
    <strong>Eligibility:</strong> EU programmes typically require companies registered
    in EU member states. Funding rates range from 50-100% depending on programme and
    project type. Check the
    <a href="https://ec.europa.eu/info/funding-tenders/opportunities/portal/" target="_blank">EU Funding Portal</a>
    for current calls and deadlines.
  </p>

  {% elif FUNDING_PROGRAMMES %}
  <h3>Available Funding Programmes</h3>
  <ul class="funding-list compact">
    {% for p in FUNDING_PROGRAMMES[:7] %}
    <li>
      <strong>{{ p.name_en or p.name }}</strong>
      {% if p.summary_en %} – {{ p.summary_en }}{% endif %}
      {% if p.funding_rate_en %} ({{ p.funding_rate_en }}){% endif %}
    </li>
    {% endfor %}
  </ul>

  <p class="eligibility-note">
    <strong>Eligibility:</strong> Requirements vary by programme. Contact your national
    innovation agency or the programme administrator for specific eligibility criteria.
  </p>

  {% else %}
  <h3>General EU Funding Guidance</h3>
  <p>
    For companies in the EU seeking AI and digitalisation funding, consider:
  </p>
  <ul class="funding-list compact">
    <li><strong>Horizon Europe</strong> – EU research and innovation framework</li>
    <li><strong>Digital Europe Programme</strong> – Supports digital transformation</li>
    <li><strong>EIC Accelerator</strong> – For high-impact startups and SMEs</li>
    <li><strong>Eurostars</strong> – R&D funding for innovative SMEs</li>
    <li><strong>National Innovation Agencies</strong> – Country-specific support</li>
  </ul>

  <p class="eligibility-note">
    <strong>Eligibility:</strong> Visit the
    <a href="https://ec.europa.eu/info/funding-tenders/opportunities/portal/" target="_blank">EU Funding &amp; Tenders Portal</a>
    to explore programmes matching your profile. Requirements vary by call.
  </p>
  {% endif %}

  <h3>Next Steps</h3>
  <ul>
    <li>Review programme requirements against your project scope</li>
    <li>Prepare a project outline with clear objectives and timeline</li>
    <li>Contact your national contact point (NCP) for application guidance</li>
  </ul>

  <p class="small muted">
    Note: Funding availability, rates, and deadlines change regularly. Verify all
    information against official programme documentation before applying.
  </p>
</section>
