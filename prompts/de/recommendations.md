Developer: <!-- recommendations.md – v4.0 GOLD STANDARD+ (size-aware, placeholder-sicher)
  Antworte ausschließlich mit validem HTML.
  KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im Output. -->

<!--
  Ziel: Eine präzise und umsetzbare Empfehlungen-Section generieren
  Kontext-Parameter (alle Platzhalter müssen zum Zeitpunkt der Ausgabe durch konkrete Werte ersetzt werden):
    - Branche: {{BRANCHE_LABEL}}
    - Unternehmensgröße: {{UNTERNEHMENSGROESSE_LABEL}}
    - Hauptleistung: {{HAUPTLEISTUNG}}
    - Bundesland: {{BUNDESLAND_LABEL}} (nur wenn Förderbezug im Report relevant)
    - Company Size: {{COMPANY_SIZE}}
-->

<section class="section recommendations">
  <h2>Handlungsempfehlungen – Strategische Prioritäten</h2>

  <p>
    Generiere eine Empfehlungen-Sektion für:
    <strong>Branche:</strong> {{BRANCHE_LABEL}},
    <strong>Unternehmensgröße:</strong> {{UNTERNEHMENSGROESSE_LABEL}},
    <strong>Leistungsschwerpunkt:</strong> {{HAUPTLEISTUNG}}<span style="display: {{BUNDESLAND_LABEL?'':'none'}};">, <strong>Bundesland:</strong> {{BUNDESLAND_LABEL}}</span>.
    Empfehlungen müssen spezifisch, messbar und priorisiert sein sowie sämtlich Platzhalter durch konkrete Werte ersetzen. Falls Werte für einzelne Variablen fehlen, ist ein passender, inhaltlich stimmiger Alternativtext zu verwenden.
  </p>

  <ol class="recommendations-list">
    <!--
      Für jede Empfehlung:
        <li>
          <h3>{{Empfehlungs-Titel}}</h3>
          <p><strong>Problem im Kernprozess:</strong> {{Problem}}</p>
          <p><strong>Empfohlene Maßnahme:</strong> {{Maßnahme}}</p>
          <p><strong>Nutzen & ROI:</strong> {{Nutzen}}</p>
          <p><strong>Aufwand & Budget:</strong> {{Aufwand}}</p>
          <p><strong>Verantwortlich:</strong> {{Verantwortlicher}}</p>
          <p><strong>Förderoption:</strong> {{Förderhinweis}}</p>
        </li>
    -->
    <!-- Mindestens drei praxistaugliche, priorisierte Empfehlungen – keine Floskeln, keine Platzhalter. -->
  </ol>

  <h3>Prioritäten-Überblick</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Priorität</th>
        <th>Empfehlung</th>
        <th>Zeitrahmen</th>
        <th>Hauptnutzen</th>
      </tr>
    </thead>
    <tbody>
      <!-- Jede Empfehlung (aus <ol>) taucht konsistent in dieser Übersicht auf. -->
    </tbody>
  </table>

  <p class="small muted">
    Diese Empfehlungen sind für Geschäftsführung und Projektverantwortliche als konkrete Entscheidungsgrundlage formuliert.
    Ziehen Sie Quick Wins, Pilotprojekte und Business Cases zur Priorisierung regelmäßig hinzu.
  </p>
</section>

<!--
Output Verbosity:
- Erstelle ausschließlich validen HTML-Code gemäß dieser Struktur.
- Die Empfehlungen-Liste muss aus mindestens 3, maximal 6 Einträgen bestehen.
- Beschreibungen in den einzelnen Feldern (z.B. Problem, Maßnahme) dürfen maximal 2 kurze Sätze umfassen.
- Antworte immer kompakt und direkt, vermeide ausschweifende Erklärungen oder Wiederholungen.
- Priorisiere vollständige, umsetzbare Empfehlungen innerhalb dieser Längenvorgaben.
-->
