<!-- recommendations.md – v4.0 GOLD STANDARD+ (size-aware, placeholder-sicher)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im Output. -->

# HANDLUNGSEMPFEHLUNGEN – STRATEGISCHE PRIORITÄTEN

## ZWECK

Erstelle eine präzise, umsetzbare **Empfehlungs-Section** für:

- Branche: **{{BRANCHE_LABEL}}**
- Unternehmensgröße: **{{UNTERNEHMENSGROESSE_LABEL}}**
- Hauptleistung: **{{HAUPTLEISTUNG}}**
- Bundesland: **{{BUNDESLAND_LABEL}}** (nur für Förderbezug)

Die Empfehlungen müssen:

1. **konkret, messbar und priorisiert** sein,  
2. **direkt aus Scores, Quick Wins, Roadmap & Business Case** abgeleitet werden,  
3. **size-aware** (Solo ≠ Team ≠ KMU) formuliert sein,  
4. **ohne Platzhalter** ausgegeben werden,  
5. **förderlogik** einbeziehen, falls im Report vorhanden  
   (BUNDESLAND + Branchenprogramme),  
6. **praxisnah** und ohne Konzern-Floskeln auskommen.

---

## VERBOTEN (Hard Rules)

- Keine Platzhalter wie `{…}`, `[ … ]`, `{{CONTEXT_…}}`.
- Keine Framework-Phrasen („Change Board“, „Transformation Office“, „PMO“ bei kleinen Firmen).
- Keine künstlichen Zahlen erfinden.
- Keine generischen Textbausteine („Prozesse optimieren“, „Mitarbeiter abholen“).

---

## OUTPUT-FORMAT  
**Antwort ausschließlich als validen HTML-Block ausgeben:**

```html
<section class="section recommendations">
  <h2>Handlungsempfehlungen</h2>

  <p>
    Diese Empfehlungen fassen die wichtigsten nächsten Schritte für 
    <strong>{{HAUPTLEISTUNG}}</strong> in der Branche 
    <strong>{{BRANCHE_LABEL}}</strong> zusammen – priorisiert nach 
    Wirkung, Aufwand und Machbarkeit für die Größe 
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>.
  </p>

  <ol class="recommendations-list">
    <li>
      <h3>Empfehlung 1 – Titel in max. 10 Wörtern</h3>
      <p><strong>Problem im Kernprozess:</strong> 
        Beschreibe präzise den zentralen Engpass in {{HAUPTLEISTUNG}} 
        (z.&nbsp;B. langsame Durchlaufzeiten, Medienbrüche, manuelle Routinearbeit).
      </p>
      <p><strong>Empfohlene Maßnahme:</strong> 
        Beschreibe die konkrete Lösung (z.&nbsp;B. Automatisierung eines 
        Schritts, Standardisierung mit KI-Templates, neue Workflow-Variante).
      </p>
      <p><strong>Nutzen &amp; ROI:</strong> 
        Messbarer Effekt (z.&nbsp;B. weniger Korrekturschleifen, 
        Zeitersparnis, besserer Output). Keine Zahlen erfinden – nur 
        qualitative Verbesserungen nennen.
      </p>
      <p><strong>Aufwand &amp; Budget:</strong> 
        Realistisch je nach Größe:  
        • Solo: wenige Stunden – 1 Tag  
        • Team: 1–3 Tage  
        • KMU: kleines Projektteam für 2–5 Tage
      </p>
      <p><strong>Verantwortlich:</strong> 
        Rollen passend zu {{COMPANY_SIZE}} – z.&nbsp;B. „Sie selbst“, 
        „Teamlead“, „KI-Owner“, „Fachbereich + IT“.
      </p>
      <p><strong>Förderoption (falls sinnvoll):</strong> 
        Falls im Report passende Programme genannt wurden 
        (z.&nbsp;B. Digitalisierung / KI-Zuschüsse in {{BUNDESLAND_LABEL}}), 
        kurze Empfehlung zur Prüfung aufnehmen – ohne neue Beträge zu erfinden.
      </p>
    </li>

    <li>
      <h3>Empfehlung 2 – Titel</h3>
      <p><strong>Problem im Kernprozess:</strong> 
        Beschreibe den zweiten relevanten Engpass, der besonders viel Zeit 
        oder Qualität kostet.
      </p>
      <p><strong>Empfohlene Maßnahme:</strong> 
        Konkrete, sofort machbare Maßnahme – evtl. auf Quick Wins oder 
        Roadmap aufbauend.
      </p>
      <p><strong>Nutzen &amp; ROI:</strong> 
        Beschreibe Nutzen in Zeit, Qualität oder Risikoreduktion.
      </p>
      <p><strong>Aufwand &amp; Budget:</strong> 
        Realistische Spanne gemäß {{UNTERNEHMENSGROESSE_LABEL}}.
      </p>
      <p><strong>Verantwortlich:</strong> 
        Nenne konkrete Rollen, keine abstrakten Titel.
      </p>
    </li>

    <li>
      <h3>Empfehlung 3 – Titel</h3>
      <p><strong>Problem im Kernprozess:</strong> 
        Beschreibe einen Engpass aus Governance, Sicherheit oder Datenqualität.
      </p>
      <p><strong>Empfohlene Maßnahme:</strong> 
        Z.&nbsp;B. Einführung klarer QA-Regeln, Prompt-Dokumentation, 
        einfache Freigabeprozesse.
      </p>
      <p><strong>Nutzen &amp; ROI:</strong> 
        Reduktion von Fehlern, Nacharbeiten, Risiken.
      </p>
      <p><strong>Aufwand &amp; Budget:</strong> 
        Zeitbedarf und ggf. externe Unterstützung.
      </p>
      <p><strong>Verantwortlich:</strong> 
        Klar definierte Zuständigkeit.
      </p>
    </li>
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
        <td>Hoch</td>
        <td>Empfehlung 1</td>
        <td>30–60 Tage</td>
        <td>Klarer Mehrwert im Kernprozess</td>
      </tr>
      <tr>
        <td>Mittel</td>
        <td>Empfehlung 2</td>
        <td>60–90 Tage</td>
        <td>Effizienz und Qualität</td>
      </tr>
      <tr>
        <td>Niedrig</td>
        <td>Empfehlung 3</td>
        <td>90+ Tage</td>
        <td>Governance &amp; Stabilität</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    Diese Empfehlungen dienen als konkrete Entscheidungsgrundlage für 
    Geschäftsführung und Projektverantwortliche.  
    Nutzen Sie die Ergebnisse aus Quick Wins, Pilot-Phase und Business Case, 
    um Prioritäten regelmäßig anzupassen.
  </p>
</section>
