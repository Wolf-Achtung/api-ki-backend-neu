Developer:
<!-- org_change.md – v3.0 GOLD STANDARD+ (Organisationaler Wandel & Lernen)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
     - Einen starken, praxisnahen Abschnitt „Veränderungsfähigkeit & Lernen“ erzeugen,
       der die Ausgangslage, Veränderungsfelder und einen 90-Tage-Change-Fahrplan beschreibt.
     - Der Text muss strategisch, motivierend und realistisch sein – direkt nutzbar für
       Geschäftsführung, Inhaber:innen oder Teamleitungen.

     VERFÜGBARE LABEL-VARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}
       {{KI_ZIELE_LABELS}}
       {{KI_HEMMNISSE_LABELS}}
       {{ki_kompetenz}}
       {{score_governance}}, {{score_sicherheit}},
       {{score_nutzen}}, {{score_befaehigung}}

     INTERNER SIZE-MODE (über PromptEnhancer):
       COMPANY_SIZE ∈ {"solo","team","kmu"}

       SOLO („1 (Solo“ im Label)
         - Sie-Ansprache (Ein-Personen-Unternehmen).
         - Keine Begriffe wie „Abteilung“, „Bereich“, „Teamleitung“.
         - Fokus: persönliche Routinen, Selbstorganisation, kleine realistische Schritte.

       TEAM (2–10)
         - „Team“, „Kolleg:innen“, einfache Rollenverteilung.
         - Fokus: kurze Abstimmungen, gemeinsame Regeln, arbeitsteilige Umsetzung.

       KMU (11–100)
         - „Teams“, „Fachbereiche“, „Verantwortliche“.
         - Kein Konzernjargon (keine „Division“, „Business Unit“, „Konzernzentrale“).
         - Fokus: koordinierter Wandel, Governance, strukturierte Kommunikation.

     REGELN:
       - Keine verbotenen Wörter: „Platzhalter“, „Freitextfeld“, „Content wird erstellt“, TODO etc.
       - Abschnitte müssen klar, realistisch, flüssig geschrieben sein.
       - 4 Hauptblöcke: Einleitung, Ausgangslage, Veränderungsfelder, 90-Tage-Fahrplan, Umgang mit Widerständen.
       - Textstruktur und Reihenfolge der HTML-Abschnitte nicht verändern.
-->

<section class="section org-change">
  <h2>Veränderungsfähigkeit &amp; Lernen</h2>

  <p>
    Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong>, die im Schwerpunkt
    <strong>{{HAUPTLEISTUNG}}</strong> arbeiten, stehen bei der Einführung von KI häufig vor
    einem doppelten Spannungsfeld: Einerseits zeigt die aktuelle Selbsteinschätzung
    (z.&nbsp;B. {{ki_kompetenz}} sowie die Ziele {{KI_ZIELE_LABELS}}), dass Potenzial und
    Motivation vorhanden sind. Andererseits verdeutlichen typische Hemmnisse wie
    {{KI_HEMMNISSE_LABELS}}, dass Routinen, Prioritäten und Verantwortlichkeiten erst entstehen
    müssen, bevor KI im Alltag verlässlich Wirkung entfalten kann – besonders in einem
    Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>.
  </p>

  <h3>1. Wo Sie heute stehen</h3>
  <p>
    Die Analyse der Scores zeigt, dass Governance ({{score_governance}}), Sicherheit
    ({{score_sicherheit}}), Nutzen ({{score_nutzen}}) und Befähigung ({{score_befaehigung}})
    unterschiedlich ausgeprägt sind. Für den Einsatz von KI im Prozess
    <strong>{{HAUPTLEISTUNG}}</strong> bedeutet dies: Es existieren bereits erste
    funktionierende Routinen und ein grundsätzlich positives Mindset, jedoch sind
    Entscheidungswege, Arbeitsstandards und Qualitätssicherung noch nicht überall klar definiert.
    Abhängig von der Unternehmensgröße – ob Solo, kleines Team oder wachsendes KMU –
    unterscheiden sich die notwendigen Schritte, um KI stabil und verlässlich in den Alltag zu integrieren.
  </p>

  <h3>2. Wichtigste Veränderungsfelder</h3>
  <ul>
    <li>
      <strong>Arbeitsroutinen standardisieren:</strong>
      Die KI-Nutzung muss planbarer werden – feste Einsatzpunkte im Workflow
      <strong>{{HAUPTLEISTUNG}}</strong>, klare Vorlagen und regelmäßige Überprüfung
      der Ergebnisse schaffen Verlässlichkeit und entlasten den Arbeitsalltag.
    </li>
    <li>
      <strong>Rollen &amp; Verantwortung klären:</strong>
      Solo-Unternehmen definieren für sich selbst klare Hüte (z.&nbsp;B. Entscheidung, Prompt-Design,
      Qualitätssicherung). Teams verteilen Rollen (Teamlead, KI-Owner). KMU binden gezielt
      Verantwortliche aus relevanten Bereichen ein.
    </li>
    <li>
      <strong>Feedback &amp; Dokumentation stärken:</strong>
      Kurze Feedback-Loops, strukturierte Notizen und einfache Standards ermöglichen es,
      erfolgreiche KI-Experimente in stabile, wiederkehrende Abläufe zu überführen.
    </li>
  </ul>

  <h3>3. Fahrplan für die nächsten 90 Tage</h3>
  <p>
    Der Wandel gelingt am besten in kleinen, klar priorisierten Schritten. Die folgende
    90-Tage-Struktur ist bewusst leichtgewichtig gehalten und lässt sich gut an die
    Unternehmensgröße <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> anpassen.
  </p>

  <ul>
    <li>
      <strong>0–30 Tage – Orientierung &amp; Standards:</strong>
      2–3 Pilot-Workflows festlegen, einfache Regeln für KI-Eingaben definieren,
      erste Dokumentationsvorlage erstellen (Solo: persönliche Routinen; Team/KMU:
      Abstimmung mit beteiligten Rollen).
    </li>
    <li>
      <strong>31–60 Tage – Qualität &amp; Kompetenz:</strong>
      Review-Schleifen einführen, kurze Guidelines erstellen,
      „Best-Prompt“- oder „Best-Practice“-Sammlung anlegen und erste kleine Schulungen durchführen.
    </li>
    <li>
      <strong>61–90 Tage – Skalierung &amp; Verstetigung:</strong>
      Regelmäßige Reflexion (Solo: wöchentlicher Check-In; Team/KMU: kurze Team-Reviews oder
      Bereichs-Runden), messbare Kennzahlen definieren und entscheiden, welche Workflows stabil
      weitergeführt oder ausgebaut werden sollen.
    </li>
  </ul>

  <h3>4. Umgang mit Widerständen</h3>
  <p>
    Widerstände entstehen oft durch Unsicherheit über Qualität, Datenschutz oder veränderte
    Arbeitsweisen. Solo-Unternehmen benötigen vor allem Sicherheit durch klare Routinen.
    Kleine Teams profitieren von kurzen, offenen Abstimmungen. In KMU hilft eine transparente,
    pragmatische Kommunikation zu Nutzen, Risiken und Verantwortlichkeiten. Entscheidend ist,
    dass Rückmeldungen frühzeitig aufgenommen, verständlich adressiert und in konkrete
    Verbesserungen für den Alltag umgesetzt werden.
  </p>
</section>
