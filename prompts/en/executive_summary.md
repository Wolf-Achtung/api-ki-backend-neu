Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: executive_summary -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, sme:1.15x=690) -->
<!--
GOAL: CEO-ready Executive Summary in 2-4 sentences.

PLOT STRUCTURE (STRICT – single paragraph):
1. Current State: Where does the company stand today? (Industry, size, AI maturity)
2. Focus & Goals: What is the central objective with AI?
3. Key Lever: Which single approach delivers the biggest impact?
4. Immediate Opportunity: What is the concrete next step?

STYLE (CEO-READY):
- Crisp, no buzzwords ("synergies", "transformation", "next-level")
- Fact-based, sober, results-oriented
- NO repetition of roadmap details or quick-win lists
- NO bullet points – flowing prose only
- Maximum 80 words

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: "You", personal perspective, relief as goal
- team: "Your team", shared efficiency
- sme: "Your organization", structural levers

ANTI-REDUNDANCY:
- Quick Win details → see quick_wins.md
- Roadmap details → see roadmap_90d.md / roadmap_12m.md
- Here ONLY the essence, NO anticipation

GUARDRAILS: Respect stated guardrails from strategic context.
-->

<section class="section executive-summary">
  <h2>Executive Summary</h2>

  <p>
    {% if COMPANY_SIZE == "solo" %}
    As a solo professional in <strong>{{BRANCHE_LABEL}}</strong> focused on
    <strong>{{HAUPTLEISTUNG}}</strong>, your biggest lever is automating repetitive tasks –
    reclaiming several hours per week. The first step: a structured AI workflow
    for your most time-consuming routine task.
    {% elif COMPANY_SIZE == "team" %}
    Your team in <strong>{{BRANCHE_LABEL}}</strong> ({{UNTERNEHMENSGROESSE_LABEL}})
    can achieve significant efficiency gains through targeted AI support in
    <strong>{{HAUPTLEISTUNG}}</strong>. The key approach: shared standards for
    AI-assisted routines that deliver immediate relief while ensuring quality.
    {% else %}
    For an organization of your size ({{UNTERNEHMENSGROESSE_LABEL}}) in
    <strong>{{BRANCHE_LABEL}}</strong>, the area of <strong>{{HAUPTLEISTUNG}}</strong>
    offers the greatest leverage for AI-driven productivity gains. The strategic focus:
    scalable processes tested in pilot areas, then rolled out organization-wide.
    {% endif %}
  </p>
</section>
