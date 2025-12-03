Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: funding_eu_core -->
<!-- VERSION: v2.0 PLATIN++ V5 -->
<!-- OUTPUT: HTML -->
<!-- SIZE-AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, FUNDING_PROGRAMMES_EU_CORE -->
<!-- TOKEN-BUDGET: 2500 (solo:0.8x, team:1.0x, sme:1.15x) -->
<!-- FUNDING: EN-EU (Phase 2) - EU-wide programs for non-German companies -->
<!--
TARGET: English-speaking users with companies in EU countries (excluding Germany).

STRUCTURE (3 sections):
  H3 1. EU Core Programmes Overview (Jinja2 loop)
  H3 2. What This Means for Your Business
  H3 3. Next Steps

TARGET GROUP LOGIC:
  startup: EIC Accelerator, EIC Pathfinder, Horizon Europe
  sme: Digital Europe, Horizon Europe, Eurostars
  large: Horizon Europe, Digital Europe, InnovFin
  research: Horizon Europe, EIC Pathfinder
  public: Digital Europe, ESF+, Interreg

ANTI-REDUNDANCY:
- EU funding details HERE only
- NO German federal/state programs (see funding_potential.md)

STYLE:
- Professional, factual, cautious language
- No guaranteed amounts ("typically", "up to", "varies")
- Clear that details vary by call/year
-->

<section class="section funding eu-core">
  <h2>EU Funding Opportunities</h2>

  <p>
    The European Union offers several funding programmes that support AI adoption,
    digitalisation, and innovation across member states. These programmes are
    generally open to organisations based in EU member states and, in some cases,
    associated countries.
  </p>

  <p>
    For a <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in the
    <strong>{{BRANCHE_LABEL}}</strong> sector, the following EU-wide programmes
    may be relevant for your AI initiative:
  </p>

  <h3>Relevant EU Core Programmes</h3>

  {% if FUNDING_PROGRAMMES_EU_CORE %}
  <div class="funding-programmes eu-core">
    {% for p in FUNDING_PROGRAMMES_EU_CORE %}
    <div class="funding-programme">
      <h4>{{ p.name_en }}</h4>
      {% if p.summary_en %}
      <p class="summary">{{ p.summary_en }}</p>
      {% endif %}
      <ul class="details">
        {% if p.funding_type_en %}<li><strong>Funding type:</strong> {{ p.funding_type_en }}</li>{% endif %}
        {% if p.funding_rate_en %}<li><strong>Typical co-funding rate:</strong> {{ p.funding_rate_en }}</li>{% endif %}
        {% if p.max_amount_en %}<li><strong>Typical amount:</strong> {{ p.max_amount_en }}</li>{% endif %}
        {% if p.target_groups_en %}<li><strong>Target groups:</strong> {{ p.target_groups_en | join(', ') }}</li>{% endif %}
        {% if p.ai_relevance_en %}<li><strong>AI relevance:</strong> {{ p.ai_relevance_en }}</li>{% endif %}
      </ul>
      {% if p.notes_en %}
      <p class="notes"><em>{{ p.notes_en }}</em></p>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% else %}
  <p>
    At this point, there are no specific EU core programmes we can confidently
    recommend based on your profile. We suggest consulting your national
    innovation agency or the EU Funding &amp; Tenders Portal for current
    opportunities in your sector.
  </p>
  {% endif %}

  <h3>What This Means for Your Business</h3>
  <p>
    EU funding programmes can significantly reduce the financial risk of AI and
    digitalisation projects. Depending on the programme and your organisation type,
    co-funding rates typically range from <strong>50% to 100%</strong> of eligible costs.
  </p>
  <ul>
    <li>
      <strong>Startups &amp; scale-ups:</strong> The EIC Accelerator offers both
      grants and equity investment for high-impact innovation projects.
    </li>
    <li>
      <strong>SMEs:</strong> Horizon Europe, Digital Europe, and Eurostars provide
      collaborative funding opportunities, often requiring consortium partnerships.
    </li>
    <li>
      <strong>Research collaborations:</strong> Partnering with universities or
      research institutes can open access to additional funding streams.
    </li>
  </ul>
  <p>
    Note that most EU programmes require a clearly defined project scope,
    measurable objectives, and often cross-border collaboration.
  </p>

  <h3>Next Steps</h3>
  <ul>
    <li>
      Review the programmes above and identify 1-2 that align with your project
      scope and organisation profile.
    </li>
    <li>
      Visit the <a href="https://ec.europa.eu/info/funding-tenders/opportunities/portal/" target="_blank">EU Funding &amp; Tenders Portal</a>
      to check current calls and deadlines.
    </li>
    <li>
      Contact your national contact point (NCP) for guidance on eligibility
      and application procedures in your country.
    </li>
    <li>
      Consider potential consortium partners if the programme requires
      cross-border collaboration.
    </li>
  </ul>

  <p class="small muted">
    Note: EU funding programmes have specific eligibility criteria, deadlines,
    and call-based requirements that vary by year and work programme. The
    information above provides general guidance based on current programmes
    and should be verified against official documentation before applying.
  </p>
</section>
