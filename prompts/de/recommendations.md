Developer:
<!-- recommendations.md – v3.0 GOLD STANDARD+ (size-aware, strategic, validator-safe)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.

     ZIEL:
     - Erzeuge 3–6 klare, priorisierte Handlungsempfehlungen für KI-Einsatz im Unternehmen.
     - Jede Empfehlung muss sofort nutzbar sein: Problem → Maßnahme → Nutzen → Aufwand → Verantwortlich → Förderoption.
     - Zusätzlich eine kompakte Prioritäten-Tabelle mit 3–6 Einträgen.
     - Alle Empfehlungen müssen zu Branche, Hauptleistung und Unternehmensgröße passen.

     VERFÜGBARE LABEL-VARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}
       {{BUNDESLAND_LABEL}}
       {{COMPANY_SIZE}}   // über PromptEnhancer: "solo", "team", "kmu"

     GRÖSSENLOGIK (einheitlich für alle Prompts):
       SOLO ("solo"):
         - Direkte Sie-Ansprache; Fokus: persönliche Entlastung & Effizienz.
         - Keine "Abteilungen", "Teams", "Bereiche".
         - Maßnahmen klein, realistisch, schnell umsetzbar.

       TEAM ("team"):   // 2–10 Personen
         - Leichte Organisationssprache erlaubt: "Team", "Kolleg:innen".
         - Verantwortlichkeiten als Rollen, nicht Bereiche.
         - Fokus: arbeitsteilige Umsetzung, klare Owner, gute Abstimmung.

       KMU ("kmu"):     // 11–100 Personen
         - Organisationssprache: "Teams", "Fachbereiche", "Verantwortliche".
         - Kein Konzernjargon (keine "Division", "Business Unit").
         - Fokus: koordinierte Umsetzung, Governance, skalierbare Prozesse.

     VERBOTEN:
       - Keine Wörter wie "Platzhalter", "Freitextfeld", "TODO", "Content wird erstellt".
       - Keine Beispielmarkierungen („Titel der Empfehlung …“).
       - Keine Rohvariablen im sichtbaren Content.

     STIL:
       - Klar, geschäftsorientiert, umsetzbar.
       - Jede Empfehlung: max. 3–5 kurze Sätze.
       - Realistische Maßnahmen (keine Übertreibungen).
       - Einfache, lesbare Struktur für PDF-Report.

-->

<section class="section recommendations">
  <h2>Handlungsempfehlungen – Ihre nächsten Schritte mit KI</h2>

  <p>
    Für ein Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong> mit der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> ergeben sich mehrere konkrete Hebel,
    um KI im Prozess <strong>{{HAUPTLEISTUNG}}</strong> wirksam einzusetzen.
    Die folgenden Empfehlungen fokussieren auf schnelle Wirkung, klare Verantwortlichkeiten
    und eine stabile Einführung im Alltag.
  </p>

  <ol class="recommendations-list">
    <!-- Mindestens 3, maximal 6 Empfehlungen – jeweils vollständig ausgeführt -->
    <li>
      <h3>Empfehlung&nbsp;1</h3>
      <p><strong>Schwerpunkt:</strong> Beschreibung des zu optimierenden Teilprozesses im Bereich {{HAUPTLEISTUNG}}.</p>
      <p><strong>Maßnahme:</strong> Konkrete KI-gestützte Veränderung, die in 3–6 Monaten realisierbar ist.</p>
      <p><strong>Nutzen &amp; Wirkung:</strong> Direkter geschäftlicher Effekt (Zeitersparnis, Qualitätssteigerung oder geringeres Risiko).</p>
      <p><strong>Aufwand &amp; Budget:</strong> Realistische Größenordnung abgestimmt auf {{UNTERNEHMENSGROESSE_LABEL}}.</p>
      <p><strong>Verantwortlich:</strong> Solo: Geschäftsführung; Team: Teamlead/KI-Owner; KMU: zuständiger Bereich + Verantwortliche.</p>
      <p><strong>Förderchance:</strong> Kurzer Hinweis, ob Programme im Bundesland {{BUNDESLAND_LABEL}} typischerweise passen.</p>
    </li>

    <li>
      <h3>Empfehlung&nbsp;2</h3>
      <p><strong>Schwerpunkt:</strong> Prozess oder Bereich, in dem KI Datenaufbereitung, Analyse oder Textarbeit unterstützt.</p>
      <p><strong>Maßnahme:</strong> Umsetzung eines klar definierten Workflows für wiederkehrende Aufgaben.</p>
      <p><strong>Nutzen &amp; Wirkung:</strong> Höhere Konsistenz, weniger manuelle Schleifen, schnellere Ergebnisse.</p>
      <p><strong>Aufwand &amp; Budget:</strong> Einführungsaufwand in Tagen; laufende Kosten im niedrigen zweistelligen bis mittleren dreistelligen Bereich.</p>
      <p><strong>Verantwortlich:</strong> Verantwortlichkeit abhängig von {{UNTERNEHMENSGROESSE_LABEL}} (Solo/Team/KMU).</p>
      <p><strong>Förderchance:</strong> Hinweis auf mögliche Zuschussprogramme, sofern relevant.</p>
    </li>

    <li>
      <h3>Empfehlung&nbsp;3</h3>
      <p><strong>Schwerpunkt:</strong> Verbesserung der Zusammenarbeit, Dokumentation oder Qualitätssicherung.</p>
      <p><strong>Maßnahme:</strong> Einführung klarer Vorlagen, kurzer Review-Loops oder KI-gestützter Prüfmechanismen.</p>
      <p><strong>Nutzen &amp; Wirkung:</strong> Höhere Ersttrefferquote, weniger Überarbeitungsschleifen, stabilere Ergebnisse.</p>
      <p><strong>Aufwand &amp; Budget:</strong> Leichtgewichtige Umsetzung passend zu {{UNTERNEHMENSGROESSE_LABEL}}.</p>
      <p><strong>Verantwortlich:</strong> Größe-spezifische Rolle (Solo: Inhaber; Team: Owner; KMU: Bereich + Quality).</p>
      <p><strong>Förderchance:</strong> Optionaler kurzer Hinweis auf passende Programme.</p>
    </li>

    <!-- Optional 1–3 weitere Empfehlungen, gleiche Struktur -->
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
      <tr>
        <td>1</td>
        <td>Kurzform der wichtigsten Empfehlung</td>
        <td>0–3 Monate</td>
        <td>Schnelle Entlastung / Sofortwirkung</td>
      </tr>
      <tr>
        <td>2</td>
        <td>Zweitwichtigste Empfehlung</td>
        <td>3–6 Monate</td>
        <td>Bessere Qualität / geringeres Risiko</td>
      </tr>
      <tr>
        <td>3</td>
        <td>Drittwichtigste Empfehlung</td>
        <td>6–12 Monate</td>
        <td>Neue Angebote oder zusätzliche Wertschöpfung</td>
      </tr>
      <!-- Bis zu 3 weitere Zeilen möglich -->
    </tbody>
  </table>

  <p class="small muted">
    Die Empfehlungen sind so formuliert, dass sie unmittelbar in die Projektplanung übernommen
    werden können und konsistent mit Roadmap, Business Case und Quick Wins wirken.
  </p>
</section>
