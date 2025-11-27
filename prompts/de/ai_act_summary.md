Developer:
<!-- ai_act_summary.md – v3.1 GOLD STANDARD+ (EU AI Act – rechtliche Zusammenfassung)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
       - Präzise und sachliche Zusammenfassung des EU AI Act.
       - Bewertung der Relevanz für {{HAUPTLEISTUNG}}.
       - Korrekte Fristen (02.08.2025 / 02.08.2026 / 02.08.2027).
       - Darstellung relevanter Pflichten (insb. Art. 5, Art. 6, Art. 50).
       - Klare Empfehlung zu Transparenzpflichten.
       - Pflicht-Disclaimer: „Keine Rechtsberatung“.

     VERFÜGBARE VARIABLEN:
       {{HAUPTLEISTUNG}}
       {{report_date}}

     PFLICHTSEKTIONEN (Reihenfolge MUSS eingehalten werden):
       1. Hinweis/Disclaimer
       2. Relevanz für Hauptleistung
       3. Relevante Pflichten
       4. Wichtige Fristen (Tabelle)
       5. Empfohlene nächste Schritte
       6. Risiken bei Non-Compliance
       7. Hinweis zum Stand/Datum

     VERBOTEN:
       - Keine Rechtsberatung („Sie müssen …“).
       - Keine falsche Hochrisiko-Einstufung (Art. 6 beachten!).
       - Keine veralteten Fristen.
       - Keine Platzhalterwörter („Platzhalter“, „Freitextfeld“, „TODO“).
       - Keine technischen Prompt-Hinweise im Output.

     FEHLERBEHANDLUNG (Pflichtfelder):
       - Wenn `hauptleistung` oder `report_date` fehlen oder `report_date`
         nicht im Format YYYY-MM-DD: HTML-Fehlerblock ausgeben:
           <div class="error">Fehler: Das Pflichtfeld 'hauptleistung' und/oder 'report_date' fehlt oder ist ungültig.</div>

     OUTPUT-VERBOSE:
       - Jede Sektion max. 2 kurze Absätze oder 6 Listenpunkte/Tabellenzeilen.
       - Ton: sachlich, präzise, ohne Panikmache.
-->

<section class="section ai-act">
  <!-- 1. DISCLAIMER -->
  <h2>EU AI Act – Zusammenfassung &amp; Pflichten</h2>
  <p><strong>Hinweis:</strong> Dies ist keine Rechtsberatung. Für eine verbindliche Prüfung sollten Sie eine Fachanwältin oder einen Fachanwalt für IT-Recht mit AI-Act-Expertise konsultieren.</p>

  <!-- 2. RELEVANZ -->
  <h3>Relevanz für „{{HAUPTLEISTUNG}}“</h3>
  <p>
    Nach heutiger Einschätzung fällt der Einsatz von KI im Bereich
    <strong>{{HAUPTLEISTUNG}}</strong> <strong>nicht unter die Hochrisiko-Kategorie</strong>
    gemäß Art. 6 EU AI Act. Der Grund: Es werden keine automatisierten Entscheidungen
    über Personen getroffen (z.&nbsp;B. Recruiting, Kreditvergabe, Strafverfolgung) und
    keine biometrischen Systeme eingesetzt.
  </p>
  <p>
    <strong>ABER:</strong> Die Anwendung unterliegt den <strong>Transparenzpflichten</strong> gemäß Art. 50,
    weil KI-generierte Inhalte eingesetzt werden.
  </p>

  <!-- 3. PFLICHTEN -->
  <h3>Relevante Pflichten</h3>
  <ul>
    <li><strong>Transparenz (Art. 50):</strong> KI-generierte Inhalte müssen erkennbar gemacht werden.</li>
    <li><strong>Dokumentation:</strong> Kurzbeschreibung, an welchen Stellen KI im Prozess eingesetzt wird.</li>
    <li><strong>Hinweistext:</strong> Klare Kennzeichnung in Reports, Präsentationen oder Kundenkommunikation.</li>
    <li><strong>Human Oversight:</strong> Ergebnisse müssen weiterhin manuell geprüft werden.</li>
    <li><strong>Bei Hochrisiko (falls später relevant):</strong> Zusätzliche Pflichten gemäß Art. 9–15 (Risikomanagement, Datenqualität, Überwachung).</li>
  </ul>

  <!-- 4. FRISTEN -->
  <h3>Wichtige Fristen</h3>
  <table class="table">
    <thead>
      <tr><th>Datum</th><th>Pflichtbereich</th><th>Relevanz</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>02.08.2025</td>
        <td>Verbotene KI-Systeme (Art. 5)</td>
        <td>Nicht relevant – {{HAUPTLEISTUNG}} fällt nicht darunter.</td>
      </tr>
      <tr>
        <td>02.08.2026</td>
        <td>Transparenzpflichten (Art. 50)</td>
        <td><strong>Relevante Frist:</strong> KI-generierte Inhalte müssen ab diesem Datum gekennzeichnet sein.</td>
      </tr>
      <tr>
        <td>02.08.2026</td>
        <td>Hochrisiko-Pflichten (Art. 6 &amp; 9–15)</td>
        <td>Nur relevant, falls sich der Einsatzzweck später ändert.</td>
      </tr>
      <tr>
        <td>02.08.2027</td>
        <td>Regeln für GPAI-Modelle (Art. 51–56)</td>
        <td>Nicht relevant, da keine eigenen Modelle entwickelt werden.</td>
      </tr>
    </tbody>
  </table>

  <!-- 5. NÄCHSTE SCHRITTE -->
  <h3>Empfohlene nächste Schritte</h3>
  <ol>
    <li>Kurze interne Dokumentation, wo KI in {{HAUPTLEISTUNG}} eingesetzt wird.</li>
    <li>Entwicklung eines standardisierten Hinweises zur KI-Kennzeichnung für Reports und Präsentationen.</li>
    <li>Interne Abstimmung, dass KI-Ergebnisse weiterhin manuell geprüft werden.</li>
    <li>Optional: Rechtliche Beratung zur finalen Risikoklassifizierung.</li>
  </ol>

  <!-- 6. RISIKEN -->
  <h3>Risiken bei Non-Compliance</h3>
  <ul>
    <li>Bußgelder im Rahmen von Art. 99 – abhängig von Schwere und Art des Verstoßes.</li>
    <li>Reputationsrisiken durch unklare KI-Kennzeichnung.</li>
    <li>Vertrauensverlust bei Kund:innen oder Partnern.</li>
  </ul>

  <!-- 7. STAND -->
  <p><strong>Hinweis:</strong> Stand {{report_date}}. Der EU AI Act ist seit 01.08.2024 in Kraft; einzelne Details können sich durch Durchführungsverordnungen noch ändern.</p>
</section>
