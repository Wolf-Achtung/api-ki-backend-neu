<!-- ALIAS FOR: monetarisierung.md -->
<!-- PLATIN++ PROMPT v5.3 - SPRINT N -->
<!-- SECTION: monetarisierung -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE‑AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{COMPANY_SIZE}} -->
<!-- TOKEN‑BUDGET: 800 (solo:0.8x=640, team:1.0x=800, kmu:1.15x=920) -->
<!--
GOAL: Compact overview of 3 pricing models for AI services.

MANDATORY STRUCTURE (3 models):
1. Productised service light (fixed price) – target group, time, price band, outcome
2. Retainer model (monthly) – target group, time, price band, outcome
3. Workshop + setup (one‑off + follow‑up) – target group, time, price band, outcome

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: focus on productised services and workshops (easy to scale)
- team: retainer + workshops
- kmu: all three models equally

ANTI‑REDUNDANCY:
- Monetisation supplements the business case, do not repeat it
- Pricing logic HERE, not in other sections

STYLE:
- Text length: 120–180 words
- No concrete € amounts (only ranges)
- No marketing phrases

SPRINT N - SOLO PERSONA RULES (STRICT!):
{% if COMPANY_SIZE == "solo" %}
DO NOT USE for Solo:
- "build a team" → instead: "expand capacity"
- "employees" → instead: "resources"
- "teams" → instead: "capacities"
- "functional area" → instead: "work field"
- "department" → instead: "work area"
Use wording without team/department terms!
{% endif %}
-->

<section class="section monetization">
  <h2>Monetisation: 3 pricing models for AI services</h2>

  <div class="pricing-models">
    <div class="model">
      <h4>1. Productised service light (fixed price)</h4>
      <ul>
        <li><strong>Target group:</strong> Clients with clearly defined needs</li>
        <li><strong>Time investment:</strong> 2–8 hours per assignment</li>
        <li><strong>Price band:</strong> Lower to mid range</li>
        <li><strong>Outcome:</strong> Standardised deliverable (e.g. prompt set, mini audit)</li>
      </ul>
    </div>

    <div class="model">
      <h4>2. Retainer model (monthly)</h4>
      <ul>
        <li><strong>Target group:</strong> Regular clients with ongoing needs</li>
        <li><strong>Time investment:</strong> 4–20 hours per month</li>
        <li><strong>Price band:</strong> Mid to upper range</li>
        <li><strong>Outcome:</strong> Continuous support, updates, optimisations</li>
      </ul>
    </div>

    <div class="model">
      <h4>3. Workshop + setup (one‑off + follow‑up)</h4>
      <ul>
        <li><strong>Target group:</strong> Teams/SMEs needing an introduction</li>
        <li><strong>Time investment:</strong> 1‑day workshop + 2–4 hours follow‑up</li>
        <li><strong>Price band:</strong> Mid to upper range</li>
        <li><strong>Outcome:</strong> Empowerment of the team + documented setup</li>
      </ul>
    </div>
  </div>

  <p class="small muted">
    The choice of model depends on your capacity and target group.
    Combinations (e.g. workshop → retainer) increase customer lifetime value.
  </p>
</section>