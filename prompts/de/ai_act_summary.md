Developer:
<!-- ai_act_summary.md – v3.2 GOLD STANDARD+ (EU AI Act – rechtliche Zusammenfassung, size-aware)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
       - Präzise und sachliche Zusammenfassung des EU AI Act.
       - Bewertung der Relevanz für {{HAUPTLEISTUNG}}.
       - Korrekte Fristen (02.08.2025 / 02.08.2026 / 02.08.2027).
       - Darstellung relevanter Pflichten (insb. Art. 5, Art. 6, Art. 50).
       - Klare Empfehlung zu Transparenzpflichten.
       - Pflicht-Disclaimer: „Keine Rechtsberatung“.
       - Kurzer Abschnitt: „Was bedeutet das für Unternehmen Ihrer Größe?“.

     VERFÜGBARE VARIABLEN:
       {{HAUPTLEISTUNG}}
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{report_date}}

     REGELN:
       - Keine Rechtsberatung, nur strukturierte Information.
       - Sachlicher, präziser Ton, keine Panikmache.
       - Keine Platzhalterwörter („Platzhalter“, „Freitextfeld“, „TODO“).
       - Keine Hinweise auf Fragebögen oder interne Systemlogik.
-->

<section class="section ai-act">
  <h2>EU AI Act – Zusammenfassung &amp; Pflichten</h2>

  <p>
    <strong>Hinweis:</strong> Dieser Abschnitt stellt eine allgemeine, nicht abschließende
    Zusammenfassung des EU AI Act dar und ersetzt keine Rechtsberatung.
    Für verbindliche Auskünfte sollten spezialisierte Rechtsberater:innen hinzugezogen werden.
  </p>

  <h3>Relevanz für „{{HAUPTLEISTUNG}}“ in der Branche {{BRANCHE_LABEL}}</h3>
  <p>
    Nach derzeitiger Einschätzung fällt der Einsatz von KI im Bereich
    <strong>{{HAUPTLEISTUNG}}</strong> in der Branche <strong>{{BRANCHE_LABEL}}</strong>
    typischerweise <strong>nicht in die Hochrisiko-Kategorie</strong> gemäß Art.&nbsp;6 EU AI Act.
    Das gilt insbesondere, wenn KI vor allem für Textgenerierung, Analysen, interne
    Unterstützung und Dokumentation genutzt wird und keine vollautomatisierten
    Entscheidungen über Personen (z.&nbsp;B. Kreditvergabe, Beschäftigung, Strafverfolgung)
    getroffen werden.
  </p>
  <p>
    Dennoch greifen <strong>Transparenzpflichten</strong> und Anforderungen an eine
    sorgfältige Nutzung. Sobald KI Ergebnisse erzeugt, die gegenüber Kund:innen,
    Partnern oder Behörden verwendet werden, ist Transparenz darüber erforderlich,
    dass KI im Prozess mitwirkt.
  </p>

  <h3>Relevante Pflichten nach EU AI Act (Auszug)</h3>
  <ul>
    <li><strong>Transparenz (Art.&nbsp;50):</strong> KI-generierte Inhalte müssen erkennbar gemacht werden.</li>
    <li><strong>Dokumentation:</strong> Kurzbeschreibung, an welchen Stellen KI im Prozess eingesetzt wird.</li>
    <li><strong>Hinweise:</strong> Verständliche Kennzeichnung in Reports, Präsentationen oder Kundenkommunikation.</li>
    <li><strong>Human Oversight:</strong> Ergebnisse müssen weiterhin menschlich geprüft werden.</li>
    <li><strong>Hochrisiko-Systeme (falls später relevant):</strong> würden zusätzliche Pflichten nach Art.&nbsp;9–15 auslösen
        (Risikomanagement, Datenqualität, Überwachung, Protokollierung).</li>
  </ul>

  <h3>Wichtige Fristen</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Datum</th>
        <th>Pflichtbereich</th>
        <th>Relevanz</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>02.08.2025</td>
        <td>Verbotene KI-Praktiken (Art.&nbsp;5)</td>
        <td>Ab diesem Datum sind bestimmte Praktiken (z.&nbsp;B. manipulative Systeme) untersagt.</td>
      </tr>
      <tr>
        <td>02.08.2026</td>
        <td>Hochrisiko-Systeme</td>
        <td>Strengere Vorgaben für KI-Systeme mit erheblichem Risiko für Grundrechte.</td>
      </tr>
      <tr>
        <td>02.08.2027</td>
        <td>Transparenzpflichten (Art.&nbsp;50)</td>
        <td>Umsetzung von Kennzeichnungspflichten für KI-generierte Inhalte.</td>
      </tr>
    </tbody>
  </table>

  <h3>Was bedeutet das für Unternehmen Ihrer Größe?</h3>
  <p>
    Für ein Unternehmen mit der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> steht
    im Vordergrund, die Anforderungen pragmatisch in den Alltag zu übersetzen:
    wenige, klar dokumentierte Einsatzstellen für KI, verständliche Hinweise und eine
    nachvollziehbare Prüfung der Ergebnisse.
  </p>
  <ul>
    <li><strong>Sehr kleine Setups / Solo:</strong> Fokus auf einfache, wiederkehrende Hinweise
        (z.&nbsp;B. in Angeboten oder Reports) und eine kurze Liste, wo KI genutzt wird.</li>
    <li><strong>Kleine Teams:</strong> zusätzlich kurze Abstimmung, wer für Dokumentation und
        Kennzeichnung verantwortlich ist, und wie im Zweifel Entscheidungen nachvollzogen werden.</li>
    <li><strong>KMU:</strong> Ergänzend klare interne Richtlinien, wer KI einsetzen darf, wie
        Ergebnisse geprüft werden und wie Transparenz gegenüber Kund:innen gewährleistet wird.</li>
  </ul>

  <h3>Empfohlene nächste Schritte</h3>
  <ol>
    <li>Überblick erstellen, an welchen Stellen KI im Prozess <strong>{{HAUPTLEISTUNG}}</strong> eingesetzt wird.</li>
    <li>Standard-Hinweistext definieren, der auf KI-Unterstützung hinweist (z.&nbsp;B. in Reports oder Präsentationen).</li>
    <li>Kurze interne Leitlinie zur Nutzung von KI formulieren (Daten, Freigaben, Prüfung).</li>
    <li>Regelmäßig prüfen, ob geplante Anwendungen in den Bereich „Hochrisiko-Systeme“ fallen könnten.</li>
    <li>Optional: spezialisierte rechtliche Beratung einholen, insbesondere bei neuen, komplexeren Anwendungen.</li>
  </ol>

  <h3>Risiken bei Non-Compliance</h3>
  <ul>
    <li>Bußgelder im Rahmen von Art.&nbsp;99 – abhängig von Art und Schwere eines Verstoßes.</li>
    <li>Reputationsrisiken durch unklare oder fehlende Kennzeichnung von KI-Einsatz.</li>
    <li>Vertrauensverlust bei Kund:innen, Partnern oder Mitarbeitenden.</li>
  </ul>

  <p class="small muted">
    Stand: {{report_date}}. Der EU AI Act befindet sich teilweise noch in der Ausgestaltung;
    Details können sich durch Durchführungsverordnungen und Leitlinien weiter präzisieren.
  </p>
</section>
