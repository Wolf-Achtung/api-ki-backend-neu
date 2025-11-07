<!-- Quick Wins – Branchenspezifisch (Branch Override) -->
<!-- Output NUR als valides HTML; erlaubt: p, ul, ol, li, table, thead, tbody, tr, th, td, div, h4, strong, em, small, br -->
<!-- Keine Bilder, iframes, Skripte, externes CSS. Keine Fantasiezahlen. -->
<!-- Nutze die Variablen: {BRANCHE_LABEL}, {UNTERNEHMENSGROESSE_LABEL}, {BUNDESLAND_LABEL}, {hauptleistung}, {ki_ziele}, {anwendungsfaelle}, {ki_projekte}, {trainings_interessen}, {zeitersparnis_prioritaet}. -->
<!-- Zahlen nur aus gelieferten Variablen (z. B. Stunden-/Budgetwerte), sonst qualitative Einschätzung. -->
    <div>
      <h4>Sofort wirksame Quick Wins (0–90&nbsp;Tage) für {BRANCHE_LABEL}</h4>
      <p>Beziehen Sie sich explizit auf die Hauptleistung <em>{{ hauptleistung }}</em> und die Zeithebel <em>{{ zeitersparnis_prioritaet }}</em>. Für Solo/kleine Teams: Maßnahmen mit geringem Setup.</p>
      <ul>
        <li>Issue‑Triage & Ticket‑Summaries</li>
        <li>Dokumentations‑Extraktion & Tech‑Q&A (RAG)</li>
        <li>Code‑Review‑Snippets (ohne vertraulichen Code)</li>
        <li>Runbook‑Assistent</li>
      </ul>
      <small class="muted">Hinweis: Aufwand klein halten; DSGVO/AI‑Act beachten; keine personenbezogenen Daten in offenen Drittsystemen.</small>
    </div>