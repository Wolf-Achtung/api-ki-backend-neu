<section class="section transparency-box">
  <h2>Transparenz-Hinweise zur Report-Erstellung</h2>

  <div class="transparency-panel">
    <h3>Wie wurde dieser Report erstellt?</h3>
    <p>
      Dieser Report wurde <strong>KI-gestützt</strong> aus den Angaben Ihres Fragebogens
      vom <strong>{{report_date}}</strong> erzeugt. Die Inhalte basieren auf einer
      mehrstufigen Analyse, bestehend aus strukturierten Prompts, branchenspezifischen
      Kontextinformationen und internen Qualitätsprüfungen. Der Branchenkontext für diesen
      Report lautet: <strong>{{BRANCHE_LABEL}}</strong>.
    </p>

    <h3>Welche Daten fließen ein?</h3>
    <ul>
      <li>Antworten aus Ihrem digital ausgefüllten Fragebogen (Stand: {{report_date}}).</li>
      <li>Recherche-Snippets zu Markt, Trends und Förderlandschaft (z. B. Perplexity/Tavily).</li>
      <li>Relevante rechtliche Rahmenbedingungen, u. a. EU AI Act (Stand 01.08.2024).</li>
      <li>Interne Benchmarks aus vergleichbaren Unternehmensprofilen.</li>
    </ul>

    <h3>Limitationen & Hinweise</h3>
    <ul>
      <li><strong>Keine Rechtsberatung:</strong> Die rechtlichen Einschätzungen (DSGVO, AI Act) dienen der Orientierung und ersetzen keine juristische Prüfung.</li>
      <li><strong>Keine Garantie:</strong> Wirtschaftlichkeitsangaben (ROI, Amortisation) sind realistische Schätzungen auf Basis Ihrer Eingaben, jedoch keine verbindlichen Prognosen.</li>
      <li><strong>Stand der Informationen:</strong> Förderprogramme, Tools und regulatorische Vorgaben können sich nach {{report_date}} geändert haben.</li>
      <li><strong>Fachliche Prüfung empfohlen:</strong> KI-Ergebnisse sollten vor Umsetzung stets manuell überprüft werden.</li>
    </ul>

    <h3>Qualitätssicherung</h3>
    <p>Dieser Report durchläuft eine mehrstufige Sicherung:</p>
    <ol>
      <li>Automatische Konsistenz- und Plausibilitätsprüfung.</li>
      <li>Manuelle Validierung der Kernaussagen durch eine fachkundige Person.</li>
      <li>Abgleich der Vorschläge mit der Unternehmensgröße <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>.</li>
      <li>Überprüfung zentraler regulatorischer Hinweise (z. B. Datenschutz, EU AI Act).</li>
    </ol>

    <h3>Kontakt & Rückfragen</h3>
    <p>
      Bei Fragen oder Rückmeldungen können Sie uns jederzeit erreichen unter:<br>
      <strong>kontakt@ki-sicherheit.jetzt</strong><br>
      Optional bieten wir ein kurzes Nachgespräch innerhalb der ersten 30 Tage nach Report-Erhalt an.
    </p>
  </div>

  <style>
    .transparency-panel {
      background: #f6fafe;
      padding: 18px 24px;
      border-left: 4px solid #0284c7;
      margin: 24px 0;
    }
  </style>
</section>
