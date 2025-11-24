<!-- quick_wins.md – v3.1 GOLD STANDARD+ BRANCHE, SIZE & ROI
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head>, <body>. KEINE Markdown-Fences. -->

<!-- KONTEXT-VARIABLEN
     {{BRANCHE}} / {{BRANCHE_LABEL}}
     {{COMPANY_SIZE}} in {solo, team, kmu}
     {{UNTERNEHMENSGROESSE_LABEL}}
     {{HAUPTLEISTUNG}}
     {{BUNDESLAND_LABEL}}
     {{TOOLS_AKTUELL}}  (Liste der vorhandenen Tools)
-->

<section class="section quick-wins">
  <h2>Quick Wins – 6 sofort umsetzbare Hebel</h2>

  <p>
    Die folgenden Quick Wins sind so gewählt, dass sie den Kern Ihrer Leistung
    <strong>{{HAUPTLEISTUNG}}</strong> in der Branche <strong>{{BRANCHE_LABEL}}</strong>
    direkt verbessern. Jeder Quick Win ist in {{UNTERNEHMENSGROESSE_LABEL}}
    mit überschaubarem Aufwand realistisch umsetzbar.
  </p>

  <!-- Quick Win [1–6] – wiederholtes Muster -->
  <!-- KEINE Platzhalter im finalen Output (keine [...], keine "Schritt 1"). -->

  <div class="quick-win">
    <h3>Quick Win 1: [prägnanter Titel – max. 8 Wörter]</h3>
    <p><strong>Problem:</strong> [konkreter Engpass im Kernprozess von {{HAUPTLEISTUNG}} – 1 Satz]</p>
    <p><strong>Lösung:</strong> [konkrete Maßnahme, die direkt am Kernprozess ansetzt – 1–2 Sätze]</p>
    <p><strong>Umsetzung:</strong></p>
    <ul>
      <li>[technischer/organisatorischer Schritt 1 – z. B. Template, Workflow, Automatisierung]</li>
      <li>[Schritt 2 – z. B. Einbindung bestehender Tools aus {{TOOLS_AKTUELL}}]</li>
      <li>[Schritt 3 – z. B. kurzer Testlauf mit echten Fällen]</li>
    </ul>
    <p>
      <strong>Aufwand:</strong> [realistische Spanne – z. B. „4–8 Stunden“ oder „1–2 Tage“] ·
      <strong>Kosten:</strong> [Schätzung, z. B. „0 €“ oder „≈ 1.000 €“] ·
      <strong>Impact:</strong> [messbare Verbesserung – z. B. „−50 % Bearbeitungszeit“,
      „+200 % Output“]
    </p>
    <p>
      <strong>Tools:</strong> [nur nennen, wenn sie NICHT bereits in {{TOOLS_AKTUELL}} genutzt werden
      oder bestehende Tools auf neue Weise eingesetzt werden; immer so konkret wie möglich
      (Produktnamen statt „ein KI-Tool“).]
    </p>
  </div>

  <!-- Quick Wins 2–6 folgen im gleichen Muster -->

  <h3>Zusammenfassung der Quick Wins</h3>
  <table class="table">
    <thead>
      <tr>
        <th>#</th>
        <th>Kurzbeschreibung</th>
        <th>Aufwand</th>
        <th>geschätzte Einsparung/Monat</th>
        <th>Hauptnutzen</th>
      </tr>
    </thead>
    <tbody>
      <!-- 6 Zeilen, je Quick Win -->
    </tbody>
  </table>

  <p class="small">
    <strong>Qualitäts-Check:</strong>
    Alle Quick Wins greifen direkt in den Kernprozess von {{HAUPTLEISTUNG}} ein,
    verwenden wo sinnvoll vorhandene Tools ({{TOOLS_AKTUELL}}) weiter und
    enthalten echte Zahlen (Stunden, Prozent, €) statt Platzhaltern.
    Für {{COMPANY_SIZE}} sind Aufwand und Nutzen realistisch.
  </p>
</section>
