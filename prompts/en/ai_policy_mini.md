Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: ai_policy_mini -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 700 (solo:0.8x=560, team:1.0x=700, kmu:1.15x=805) -->
<!--
GOAL: Compact, immediately applicable AI usage rules without bureaucratic overhead.

REQUIRED STRUCTURE (7 core rules):
1. Data usage (what AI can/cannot do)
2. Review requirement (human verification)
3. Transparency (labeling)
4. No automated decisions
5. Tool approval
6. Learning culture
7. Updates

PERSONA VARIATIONS (COMPANY_SIZE):
- solo: 5 simple rules, immediately applicable, no bureaucracy
- team: Clear roles (creator, reviewer), handover rules
- sme: Structured policy, responsibilities, documentation requirements

SIZE-AWARE RESPONSIBILITIES:
- solo: Self-check, simple checklist
- team: Team lead reviews, peer review established
- sme: Compliance officer, documented approval processes

ANTI-REDUNDANCY:
- Governance rules HERE, not in Strategy/Governance section
- No overlap with AI Act Summary (legal details there)
- Complements Risks section (risks there, rules here)

STYLE:
- Text length: 120-180 words
- Practical, immediately actionable
- No legal advice, pragmatic guardrails instead

Do not use:
- No placeholders or template markers
- No legal jargon
- No repetition of guardrails from Risks section
-->

<section class="section ai-policy-mini">
  <h2>AI Mini-Policy: 7 Core Rules</h2>

  <p>
    Compact guidelines for daily AI usage at
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="policy-rules">
    <div class="rule">
      <h4>1. Data Usage</h4>
      <p><strong>Allowed:</strong> Internal, non-personal data.</p>
      <p><strong>Not allowed:</strong> Customer data, employee data, or confidential documents without approval.</p>
    </div>

    <div class="rule">
      <h4>2. Review Requirement</h4>
      <p>Every AI output is reviewed by a human before sharing with third parties.</p>
    </div>

    <div class="rule">
      <h4>3. Transparency</h4>
      <p>Label customer-facing content when AI assisted in creation.</p>
    </div>

    <div class="rule">
      <h4>4. No Automated Decisions</h4>
      <p>AI provides suggestions – humans decide. Applies to: HR matters, contracts, finances.</p>
    </div>

    <div class="rule">
      <h4>5. Tool Approval</h4>
      <p>Only use approved AI tools. Don't feed unknown tools with company data.</p>
    </div>

    <div class="rule">
      <h4>6. Learning Culture</h4>
      <p>Document mistakes, learn from them, adjust processes. No blame.</p>
    </div>

    <div class="rule">
      <h4>7. Updates</h4>
      <p>This policy is reviewed quarterly and adjusted as needed.</p>
    </div>
  </div>

  <div class="quick-check">
    <h4>Quick Check Before Every AI Use</h4>
    <ul>
      <li>Data suitable? (no sensitive personal data)</li>
      <li>Tool approved?</li>
      <li>Output reviewed?</li>
      <li>Transparency ensured?</li>
    </ul>
  </div>

  <p class="small muted">
    This mini-policy does not replace legal advice. When uncertain: consult experts.
  </p>
</section>
