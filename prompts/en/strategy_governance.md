<!-- ALIAS FOR: strategie_governance.md -->
<!-- PLATIN+++ PROMPT v6.1 - GOVERNANCE STRATEGY -->
<!-- SECTION: governance_strategy -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, kmu:1.15x=2530) -->
<!-- PHASE 3: Maximum personalization using ALL 5 Goldnuggets -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{COMPANY_SIZE}}, {{BRANCH_SHORT_LABEL}}, {{GOVERNANCE_RICHTLINIEN_LABEL}}, {{CHANGE_MANAGEMENT_LABEL}}, {{MELDEWEGE_LABEL}}, {{DATENSCHUTZ_LABEL}}, {{LOESCHREGELN_LABEL}}, {{DATENSCHUTZBEAUFTRAGTER_LABEL}}, {{FOLGENABSCHAETZUNG_LABEL}}, {{INTERNE_KI_KOMPETENZEN_LABEL}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}} -->

=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- [✓] Deliver a strategic assessment of AI strategy and governance that includes 10–14 well‑formed sentences and at least one structured list.
- [✓] Begin with two short paragraphs introducing the importance of pragmatic governance for AI deployment in the context of {{UNTERNEHMENSGROESSE_LABEL}} and {{BRANCHE_LABEL}}.
- [✓] Provide a bullet list describing current status across five areas: guidelines & policy, change management & communication, reporting channels & incidents, data protection & deletion rules, and responsibilities & competencies (using the provided labels).
- [✓] Offer an ordered list of 4–5 strategic guidelines for the next 12–24 months, tailored by company size (solo/team/kmu). Include establishing clear rules, defining responsibilities, increasing transparency, building competencies, and optionally evaluating monetisation potential.
- [✓] Include a section on responsibility & steering with size‑specific steering models and a persona‑dependent paragraph on AI culture and adoption.
- [✓] If COMPANY_SIZE is "solo", append a dedicated “Mini‑Governance for Solo” subsection (~60–80 words) with three actionable rules (version control, transparency, approval) and a note on documentation routines and scalability.
- [✓] Follow persona vocabulary rules: for solo avoid organisational jargon and team terminology; for teams emphasise shared responsibility and coordination; for KMU highlight cross‑functional standards and avoid corporate jargon.
- [✓] Do not duplicate governance content in other prompts (org_change, risks) and respect guardrails from {{KI_GUARDRAILS}}.
- [✓] Maintain a professional, neutral tone. Avoid marketing language and ensure clarity. Minimum word count for solo is 150 words due to the Mini‑Governance booster.
=============================================================================

<section class="section governance-strategy">
  <h2>AI Strategy &amp; Governance</h2>

  <p>
    For an organisation classified as <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in the <strong>{{BRANCHE_LABEL}}</strong> industry, clear, pragmatic governance is essential to ensure quality, security and accountability. A realistic AI strategy takes into account existing structures while setting the stage for sustainable innovation.
  </p>
  <p>
    This assessment summarises the current state of your AI governance and outlines strategic guidelines for the next 12–24 months. It highlights where guidelines are effective, where improvements are needed and how roles and responsibilities should evolve as your AI initiatives mature.
  </p>

  <h3>Framework Conditions &amp; Current Status</h3>
  <ul>
    <li>
      <strong>Guidelines &amp; Policy:</strong> Existing rules are currently described as {{GOVERNANCE_RICHTLINIEN_LABEL}}. They form an initial framework but need to be further specified, simplified or expanded depending on your organisation’s size.
    </li>
    <li>
      <strong>Change Management &amp; Communication:</strong> The way changes are managed is assessed as {{CHANGE_MANAGEMENT_LABEL}}. The importance and benefits of AI should be communicated consistently to increase acceptance and anchor AI in everyday routines.
    </li>
    <li>
      <strong>Reporting Channels &amp; Incidents:</strong> Current structures are described as {{MELDEWEGE_LABEL}}. Clear points of contact and simple reporting processes increase security and transparency when issues arise.
    </li>
    <li>
      <strong>Data Protection &amp; Deletion Rules:</strong> Information on data protection ({{DATENSCHUTZ_LABEL}}) and deletion rules ({{LOESCHREGELN_LABEL}}) shows that basic structures exist but should be more formally documented.
    </li>
    <li>
      <strong>Responsibilities &amp; Competencies:</strong> The appointment of a data protection officer ({{DATENSCHUTZBEAUFTRAGTER_LABEL}}), existing AI competency ({{INTERNE_KI_KOMPETENZEN_LABEL}}) and the status of impact assessments ({{FOLGENABSCHAETZUNG_LABEL}}) provide insights into roles, responsibilities and know‑how.
    </li>
  </ul>

  <h3>Strategic Guidelines for the Next 12–24 Months</h3>
  <ol>
    <li>
      <strong>Establish clear usage rules:</strong> Define binding rules for inputs, data types and quality standards – for solo professionals as compact personal routines, for teams as shared guidelines, and for KMUs as coordinated rulebooks with defined responsibilities.
    </li>
    <li>
      <strong>Define responsibilities:</strong> Solo professionals should designate an owner for usage and quality; teams should assign a team lead, AI owner and users; KMUs should appoint process owners in functional areas and include data protection/IT roles.
    </li>
    <li>
      <strong>Increase transparency &amp; risk mitigation:</strong> Brief documentation, simple reporting channels and uniform approval points ensure results can be used traceably and securely. Tailor these practices to your organisation’s size.
    </li>
    <li>
      <strong>Build competencies systematically:</strong> Provide mini‑trainings, guidelines and short reviews to build confidence in handling AI. For KMUs, add role‑specific training to address diverse needs.
    </li>
    <li>
      <strong>Evaluate monetisation potential (optional):</strong> AI‑powered processes can unlock new revenue streams through digital products, scalable service formats or automated analyses. A strategic evaluation is worthwhile, particularly when your core workflows are stable.
    </li>
  </ol>

  <h3>Responsibility &amp; Steering</h3>
  <p>
    Steering of AI deployment should fit your organisational structure. Solo businesses work with a clearly defined owner role and fixed routines. Small teams use a compact steering circle of team lead, AI owner and users. KMUs rely on coordinated responsibilities between functional areas, management and data protection/IT. Transparency, short decision paths and regular reviews are central for all sizes to ensure quality and security.
  </p>

  <h3>AI Culture &amp; Adoption</h3>
  <p>
    {% if COMPANY_SIZE == "solo" %}
    View AI as a tool for relief, not a replacement for your expertise. Regular self‑reflection on the quality and limitations of AI outputs strengthens your judgement and prevents over‑reliance on automated results.
    {% elif COMPANY_SIZE == "team" %}
    Encourage open exchange about successful and failed AI applications. Brief experience reports in existing meetings create shared learning and reduce reservations without generating additional overhead.
    {% else %}
    Establish a positive error culture around AI usage: Open sharing of learnings accelerates organisation‑wide learning. Champions in functional areas can act as multipliers and sustainably increase adoption.
    {% endif %}
  </p>

  {% if COMPANY_SIZE == "solo" %}
  <h3>Mini‑Governance for Solo</h3>
  <p>
    Even without formal governance structures, you benefit from simple rules that ensure quality and can scale to future team contexts:
  </p>
  <ul>
    <li><strong>Version control:</strong> Save key prompts and outputs with dates and context – this keeps track of which results were produced under which conditions.</li>
    <li><strong>Transparency:</strong> Label AI‑generated content before sending to clients or partners, at least internally, so you can keep oversight.</li>
    <li><strong>Approval before delivery:</strong> Perform a brief self‑check on important outputs – a personal review routine before handing over to customers safeguards quality.</li>
  </ul>
  <p>
    A short weekly or monthly documentation routine (e.g. an “AI logbook”) helps you identify patterns and gradually improve your usage. These fundamentals can easily be transferred to a small team as you grow.
  </p>
  {% endif %}

  <p class="small muted">
    A realistic, well‑communicated governance framework ensures sustainable impact, supports the implementation of your roadmap and builds trust with employees and customers alike.
  </p>
</section>