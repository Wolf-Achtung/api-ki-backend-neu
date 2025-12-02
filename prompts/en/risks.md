risks.md
Developer: <!--
  risks.md – v6.0 PLATIN+ STREAMLINED
  Goal: 5 sections with 140-180 words each (= 800-1000 words total).
  Respond exclusively with valid HTML. No Markdown fences.

  STRUCTURE (5 Required Sections):
    H3 1. Strategic and Organizational Risks (4 risks + measures)
    H3 2. Data, Security, and Compliance Risks (4 risks + measures)
    H3 3. Quality, Transparency, and Acceptance Risks (4 risks + measures)
    H3 4. Dependencies, Operations, and Vendor Risks (4 risks + measures)
    H3 5. Risk Matrix (Table with 5 rows)

  VARIABLES – use all at least once:
    {{HAUPTLEISTUNG}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}},
    {{score_governance}}, {{score_sicherheit}}

  SIZE-AWARE (COMPANY_SIZE):
    solo: personal overload, single point of failure, no backup
    team: role clarification, coordination, knowledge silos
    sme: governance, processes, documentation, compliance

  RULES:
    - Each risk: 2-3 sentences + concrete measure
    - Actively interpret scores (e.g., "The security score of X shows...")
    - Emphasize industry-specific compliance for regulated industries
    - Factual, concrete, no filler phrases
    - No placeholders, no developer language
-->

<section class="section risks">
  <h2>Key Risks in AI Deployment for {{HAUPTLEISTUNG}}</h2>

  <p>
    Deploying AI in <strong>{{HAUPTLEISTUNG}}</strong> in the <strong>{{BRANCHE_LABEL}}</strong>
    industry – with its typical workflows, data types, and pain points – offers significant opportunities
    but also brings different risk profiles depending on company size
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>. The current governance score of
    <strong>{{score_governance}}/100</strong> and security score of
    <strong>{{score_sicherheit}}/100</strong> show how far structures for control,
    documentation, and protection mechanisms have already been developed. The following sections
    consolidate the most important risk areas and outline concrete countermeasures.
  </p>

  <h3>1. Strategic and Organizational Risks</h3>
  <ul>
    <li>
      <strong>Unclear goals and priorities for AI.</strong>
      Without clearly defined goals for {{HAUPTLEISTUNG}}, there is a risk that AI experiments
      fizzle out, isolated solutions emerge, or important opportunities remain unused.
      Countermeasures include a concise vision with 2-3 prioritized use cases,
      a simple implementation plan, and regular review of whether measures align with
      the overall business model.
    </li>
    <li>
      <strong>Dependency on individual persons.</strong>
      In very small setups up to solo structures, know-how is often concentrated
      in one person. If this person is unavailable or permanently overloaded, experiments
      and implementation stall. This can be addressed through brief documentation of central workflows,
      simple checklists, and conscious anchoring of AI routines in daily work.
    </li>
    <li>
      <strong>Lack of role and responsibility clarity.</strong>
      In teams and growing companies, it is often unclear who prioritizes AI initiatives,
      who is responsible for quality, and who selects tools.
      Sensible countermeasures include a clearly designated role for AI responsibility,
      a lean decision process for tool introduction, and transparent communication
      of responsibilities.
    </li>
    <li>
      <strong>Overload from additional tasks.</strong>
      When AI introduction runs "on top" of daily business, new workflows are not
      established permanently. Small, well-plannable pilots with clearly
      limited scope help, as does conscious relief elsewhere so that time
      for experiments and learning phases is available.
    </li>
  </ul>

  <h3>2. Data, Security, and Compliance Risks</h3>
  <ul>
    <li>
      <strong>Insufficient control over input and output data.</strong>
      When it is not regulated which information may be entered into AI systems,
      confidential customer data, internal documents, or sensitive content can be processed
      uncontrollably. Countermeasures include clear guidelines for data usage,
      a brief guide for all participants, and technical protection mechanisms
      such as access restrictions or separate work areas.
    </li>
    <li>
      <strong>Gaps in information security and access protection.</strong>
      A medium or low security score (e.g., {{score_sicherheit}}/100)
      indicates that passwords, access rights, or backup concepts are not
      consistently regulated. Required are a compact security concept,
      regular password and rights reviews, and clear documentation of
      deployed cloud and AI services.
    </li>
    <li>
      <strong>Unclear responsibility for legal requirements.</strong>
      Without defined responsibility, there is a risk that data protection,
      copyright, or industry-specific regulatory requirements are only addressed sporadically.
      Useful is a designated point that bundles minimum requirements, formulates practical
      guidelines, and obtains external expert advice when uncertain.
    </li>
    <li>
      <strong>Lack of transparency towards customers and partners.</strong>
      When it remains unclear where AI contributes, this can lead to
      loss of trust. Countermeasures include brief, understandable notices
      about AI usage and traceable documentation in the background.
    </li>
  </ul>

  <h3>3. Quality, Transparency, and Acceptance Risks</h3>
  <ul>
    <li>
      <strong>Inconsistent results and quality variation.</strong>
      If prompts, templates, and workflows are not documented, quality and
      style depend heavily on the respective person. This makes reproducible results difficult.
      Remedies include unified templates, brief guides, and regular reviews
      of sample outputs.
    </li>
    <li>
      <strong>Over-reliance on AI results.</strong>
      When texts, analyses, or assessments are adopted unchecked,
      errors or hallucinations can flow directly into customer documents and decisions.
      Necessary are clear rules for manual review, four-eyes principle
      for critical content, and simple quality control checklists.
    </li>
    <li>
      <strong>Acceptance problems in daily operations.</strong>
      In teams and larger organizations, resistance arises when the benefit of AI
      is not understandable or workflows are perceived as too complex.
      Countermeasures include understandable communication of goals, small pilot projects
      with visible benefit, and actively soliciting feedback to adjust routines.
    </li>
    <li>
      <strong>Unclear traceability of decisions.</strong>
      When it is not documented what role AI plays in preparing proposals,
      reports, or decisions, it becomes difficult to reconstruct decision paths in disputes.
      Brief internal documentation of "Where does AI support?" significantly reduces
      this risk.
    </li>
  </ul>

  <h3>4. Dependencies, Operations, and Vendor Risks</h3>
  <ul>
    <li>
      <strong>Strong dependency on individual tools or platforms.</strong>
      When central workflows rely exclusively on one service or one model,
      price changes, outages, or changed terms of use quickly lead to
      disruptions. Countermeasures include simple fallback scenarios, export options
      for data, and monitoring alternatives.
    </li>
    <li>
      <strong>Unclear agreements with service providers.</strong>
      When contractual relationships, data processing, or service levels are not explicitly
      agreed, gaps in liability and availability can arise.
      Useful are clear contracts, agreed response times, and transparent
      information on data storage.
    </li>
    <li>
      <strong>Missing emergency and recovery planning.</strong>
      When it is not clarified in advance how to respond in case of system failures, data loss, or
      misconfigurations, recovery is delayed.
      Recommended are simple emergency plans, regular backups, and defined
      contact channels for critical incidents.
    </li>
    <li>
      <strong>Overly complex tool landscape.</strong>
      When too many specialized AI tools are introduced in parallel, the effort
      for maintenance, training, and coordination increases. Countermeasures include consolidation on
      a few core solutions and a consciously lean tool strategy.
    </li>
  </ul>

  <h3>5. Risk Matrix – Overview of Key Risks</h3>
  <p>
    The following overview shows the most important risk areas by probability of occurrence
    and impact strength to facilitate prioritization of countermeasures.
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
        <td>Strategy & Organization</td>
        <td>Fragmentation, lack of impact, frustration in daily work</td>
        <td>medium</td>
        <td>high</td>
        <td>Clear vision, prioritized use cases, designated AI responsibility.</td>
      </tr>
      <tr>
        <td>Data & Security</td>
        <td>Lack of transparency, potential data protection violations</td>
        <td>medium to high</td>
        <td>high</td>
        <td>Brief data usage guideline, access and password concept, service documentation.</td>
      </tr>
      <tr>
        <td>Quality & Acceptance</td>
        <td>Inconsistent results, distrust or blind trust in AI</td>
        <td>medium</td>
        <td>medium to high</td>
        <td>Template standards, review loops, understandable communication of benefits and limits.</td>
      </tr>
      <tr>
        <td>Dependencies & Operations</td>
        <td>Operational disruptions, additional costs, lock-in effects</td>
        <td>low to medium</td>
        <td>medium</td>
        <td>Fallback scenarios, tool landscape consolidation, clear vendor agreements.</td>
      </tr>
      <tr>
        <td>AI-specific: Hallucinations</td>
        <td>Erroneous information in customer documents, reputation damage</td>
        <td>medium to high</td>
        <td>high</td>
        <td>Four-eyes principle, fact checking, clear quality guidelines for AI output.</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    This risk analysis shows the most important action areas for AI in
    <strong>{{HAUPTLEISTUNG}}</strong> in a company of size
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>. In the next step, risks should be
    prioritized by probability and impact and transferred into concrete
    action planning for the next 3-6 months.
  </p>
</section>

<!-- PLATIN+ REINFORCEMENT: This section MUST contain at least 800 words.
     Check your output: Count the words and expand each risk area with additional
     details, examples, and concrete measures if the minimum length is not reached.
     NEVER shorten – always deliver complete, detailed content. -->
