<!-- PLATIN+++ PROMPT v7.1 - SPRINT FINALIZATION -->
<!-- SECTION: risks -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE‑AWARE: solo/team/sme -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{score_governance}}, {{score_sicherheit}}, {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{KI_GUARDRAILS}}, {{VISION_3_JAHRE}}, COMPANY_SIZE, {{RISK_MATRIX}}, {{HIGH_PRIORITY_RISKS}}, {{MITIGATION_STRATEGIES}} -->
<!-- TOKEN‑BUDGET: 3000 (solo:0.8x=2400, team:1.0x=3000, sme:1.15x=3450) -->
<!--
=============================================================================
PLATIN+++ CONTENT DOD (mandatory):
=============================================================================
- Cover five categories of risks: Technical, Data & Privacy, Organizational,
  Vendor & Dependencies, Compliance & Legal.
- For each category: list 3–4 specific risks and corresponding mitigation measures.
- Provide a risk matrix summarizing probability and impact for the most important
  risks and prioritize them (low/medium/high).
- Integrate inputs from the Risk Engine v3: {{RISK_MATRIX}},
  {{HIGH_PRIORITY_RISKS}}, {{MITIGATION_STRATEGIES}} where available.
- Explicitly address {{KI_GUARDRAILS}} and align with {{VISION_3_JAHRE}} in
  mitigation strategies.
- Respect persona hard‑guards (no team language in solo mode, etc.).
=============================================================================

PERSONALIZATION CONTEXT:
- {{hauptleistung}} – core business of the user
- {{ZEITERSPARNIS_PRIORITAET}} – biggest time saver priority
- {{KI_GUARDRAILS}} – AI guardrails and no‑gos
- {{VISION_3_JAHRE}} – long‑term vision (3 years)

RISK ENGINE INTEGRATION:
If the variables {{RISK_MATRIX}}, {{HIGH_PRIORITY_RISKS}}, and
{{MITIGATION_STRATEGIES}} are provided, incorporate them into the matrix and
highlight the top five risks with recommended actions.
-->

<section class="section risks">
  <h2>Key Risk Analysis for {{OFFERING_LABEL}}</h2>

  <p>
    Introducing AI into {{BRANCH_CONTEXT_LABEL}} unlocks new opportunities but also
    exposes your organization to a variety of risks. The governance score
    (<strong>{{score_governance}}/100</strong>) and security score
    (<strong>{{score_sicherheit}}/100</strong>) reflect the maturity of your current
    structures. The following sections outline the major risk categories, detail
    specific vulnerabilities and provide tailored mitigation measures to ensure
    alignment with your guardrails ({{KI_GUARDRAILS}}) and your
    <strong>{{VISION_3_JAHRE}}</strong>.
  </p>

  <h3>1. Technical Risks</h3>
  <ul>
    <li>
      <strong>Model hallucinations and unreliable outputs.</strong> When AI tools generate
      incorrect or fabricated information, it can lead to wrong decisions and loss
      of trust. Mitigation: introduce a four‑eyes principle, integrate fact‑checking
      routines and establish clear criteria for manual review.
    </li>
    <li>
      <strong>Insufficient performance on edge cases.</strong> Generic models may not
      handle specialized tasks within {{hauptleistung}}. Countermeasures include
      continuous prompt refinement, creation of custom templates, and evaluation of
      domain‑specific models.
    </li>
    <li>
      <strong>Lack of transparency in decision logic.</strong> AI systems often operate as
      black boxes. To reduce risk, implement explainability tools and document
      prompts and outputs, ensuring decisions can be audited.
    </li>
    <li>
      <strong>Technical debt in automation.</strong> Rapidly built solutions can become
      brittle. Regularly review code and workflows, refactor when necessary, and
      ensure knowledge transfer among stakeholders.
    </li>
  </ul>

  <h3>2. Data & Privacy Risks</h3>
  <ul>
    <li>
      <strong>Unauthorized disclosure of sensitive data.</strong> Without clear guidance
      on what data may be fed into AI systems, confidential information could be
      exposed. Mitigation: define allowed data types, implement access controls
      and provide clear instructions to users.
    </li>
    <li>
      <strong>Non‑compliance with GDPR and AI Act.</strong> Processing personal data in
      AI systems without proper legal basis can result in fines. Ensure data
      minimization, maintain records of processing activities and consult legal
      experts when in doubt.
    </li>
    <li>
      <strong>Weak security practices.</strong> Poor password hygiene or lack of multi‑factor
      authentication increases the risk of breaches. Establish a robust security
      policy, enforce strong authentication and conduct regular audits.
    </li>
    <li>
      <strong>Inadequate data retention and deletion.</strong> Keeping data longer than
      necessary increases exposure. Define retention periods and implement
      automated deletion routines.
    </li>
  </ul>

  <h3>3. Organizational Risks</h3>
  <ul>
    <li>
      <strong>Unclear roles and responsibilities.</strong> Ambiguity about who owns AI
      initiatives leads to stalled projects. Assign a designated AI owner and
      define decision rights clearly.
    </li>
    <li>
      <strong>Resistance to change.</strong> Teams may hesitate to adopt new workflows.
      Mitigate by communicating benefits transparently, starting with pilots and
      providing training and support.
    </li>
    <li>
      <strong>Knowledge silos and single point of failure.</strong> If only one person
      holds the expertise, absence or overload can halt progress. Encourage
      documentation, cross‑training and regular knowledge sharing sessions.
    </li>
    <li>
      <strong>Overload due to additional tasks.</strong> Introducing AI on top of daily
      responsibilities can lead to burnout. Plan for resource allocation and
      relieve other duties to create space for experimentation.
    </li>
  </ul>

  <h3>4. Vendor & Dependency Risks</h3>
  <ul>
    <li>
      <strong>Vendor lock‑in.</strong> Relying on a single provider limits flexibility.
      Mitigation: explore alternative models, maintain export options and ensure
      contractual clauses cover future changes.
    </li>
    <li>
      <strong>Unclear service agreements.</strong> Without explicit SLAs and data
      processing agreements, you risk compliance violations and outages. Negotiate
      clear contracts specifying response times, responsibilities and data
      protection measures.
    </li>
    <li>
      <strong>Operational downtime.</strong> If AI systems go offline, business
      operations can grind to a halt. Develop fallback scenarios, maintain
      redundant processes and schedule regular backups.
    </li>
    <li>
      <strong>Complex tool landscape.</strong> Too many specialized tools increase
      maintenance costs. Consolidate to core solutions and evaluate the total
      cost of ownership regularly.
    </li>
  </ul>

  <h3>5. Compliance & Legal Risks</h3>
  <ul>
    <li>
      <strong>Violation of sector‑specific regulations.</strong> Industries such as
      healthcare or finance have additional requirements. Work with legal and
      compliance teams to ensure AI use adheres to all applicable laws.
    </li>
    <li>
      <strong>Intellectual property issues.</strong> Improper use of third‑party content
      in prompts can lead to copyright disputes. Train users on fair use and
      implement monitoring.
    </li>
    <li>
      <strong>Ethical considerations.</strong> Bias and discrimination in AI outputs can
      damage your reputation. Regularly audit for fairness and involve diverse
      stakeholders in reviewing outputs.
    </li>
    <li>
      <strong>Litigation risks.</strong> Decisions made with AI assistance must be
      traceable. Document AI involvement and maintain clear logs for audits.
    </li>
  </ul>

  <h3>Risk Matrix</h3>
  <p>
    The table below summarizes the most important risk areas with their
    probability of occurrence and impact strength to help prioritize mitigation
    efforts. If {{RISK_MATRIX}} and {{HIGH_PRIORITY_RISKS}} are provided, they
    will be reflected here along with the recommended mitigation strategies
    from {{MITIGATION_STRATEGIES}}.
  </p>
  <table class="table">
    <thead>
      <tr>
        <th>Risk Area</th>
        <th>Typical Impact</th>
        <th>Probability</th>
        <th>Impact Strength</th>
        <th>Recommended Priority Measures</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Technical</td>
        <td>Incorrect outputs, system errors</td>
        <td>medium</td>
        <td>high</td>
        <td>Fact‑checking, explainability, code reviews</td>
      </tr>
      <tr>
        <td>Data & Privacy</td>
        <td>Data breaches, fines</td>
        <td>medium to high</td>
        <td>high</td>
        <td>Access controls, GDPR compliance, deletion routines</td>
      </tr>
      <tr>
        <td>Organizational</td>
        <td>Stalled projects, change resistance</td>
        <td>medium</td>
        <td>medium to high</td>
        <td>Clear roles, training, resource allocation</td>
      </tr>
      <tr>
        <td>Vendor & Dependency</td>
        <td>Downtime, cost increases</td>
        <td>low to medium</td>
        <td>medium</td>
        <td>Diversification, SLAs, fallback plans</td>
      </tr>
      <tr>
        <td>Compliance & Legal</td>
        <td>Regulatory penalties, reputational damage</td>
        <td>medium</td>
        <td>high</td>
        <td>Legal review, ethical audits, documentation</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    This risk analysis identifies key action areas for AI in
    {{OFFERING_LABEL}}. The next step is to prioritize risks based on their
    likelihood and impact, drawing on the insights provided by your risk
    engine. For implementation details refer to the Roadmap and Governance
    sections.
  </p>
</section>