Developer:
<!-- strategie_governance.md – v4.2 GOLD STANDARD+ (size-aware, strategic, validator-safe)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
     - Eine klare, strategische Einordnung zu KI-Strategie & Governance liefern.
     - Verbindung aus: aktuellem Reifegrad, vorhandenen Richtlinien, Datenschutzstatus,
       Verantwortlichkeiten, Risiken, organisatorischer Struktur.
     - Anwendungen des AI-Act, Change-Management und Verantwortlichkeiten müssen realistisch
       für Solo, kleine Teams oder KMU beschrieben sein.
     - Ergebnis = 12–18 Sätze + 1–2 strukturierte Listen.

     VERFÜGBARE LABEL-VARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{COMPANY_SIZE}}  // "solo", "team", "kmu"
       {{GOVERNANCE_RICHTLINIEN_LABEL}}
       {{CHANGE_MANAGEMENT_LABEL}}
       {{MELDEWEGE_LABEL}}
       {{DATENSCHUTZ_LABEL}}
       {{LOESCHREGELN_LABEL}}
       {{DATENSCHUTZBEAUFTRAGTER_LABEL}}
       {{FOLGENABSCHAETZUNG_LABEL}}
       {{INTERNE_KI_KOMPETENZEN_LABEL}}

     OFFIZIELLE GRÖSSENLOGIK (einheitlich mit allen Prompts):
       SOLO (COMPANY_SIZE="solo"):
         - Keine Abteilungen/Teams. Eine Owner-Rolle, persönliche Routinen, einfache Standards.
         - Governance = pragmatische, kleine Struktur.

       TEAM (2–10, COMPANY_SIZE="team"):
         - „Team“, „Kolleg:innen“, klare Rollen.
         - Governance = leichtgewichtige Struktur: Teamlead + KI-Owner + Anwender:innen.

       KMU (11–100, COMPANY_SIZE="kmu"):
         - „Teams“, „Fachbereiche“, „Verantwortliche“.
         - Kein Konzernjargon („Business Unit“, „Division“).
         - Governance = abgestimmte Struktur über mehrere Bereiche.

     VERBOTEN IM HTML-OUTPUT:
       - "Platzhalter", "Freitextfeld", TODO, technische Systemhinweise.
       - Kein Verweis auf Variablennamen oder Prompt-Anweisungen.
-->

<section class="section governance-strategy">
  <h2>KI-Strategie &amp; Governance</h2>

  <p>
    Für ein Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in der Branche
    <strong>{{BRANCHE_LABEL}}</strong> ist eine klare, pragmatische Governance für den KI-Einsatz
    entscheidend, um Qualität, Sicherheit und Verantwortlichkeiten zu sichern. Die aktuelle Einschätzung
    zeigt, wie weit Richtlinien, Meldewege, Datenschutzregeln und vorhandene Kompetenzen bereits greifen
    und an welchen Stellen strukturelle Weiterentwicklungen nötig sind.
  </p>

  <h3>Rahmenbedingungen &amp; aktueller Status</h3>
  <ul>
    <li>
      <strong>Richtlinien &amp; Policy:</strong>
      Die vorhandenen Regeln werden derzeit als {{GOVERNANCE_RICHTLINIEN_LABEL}} beschrieben.
      Sie bilden einen ersten Rahmen, müssen aber – je nach Größe – weiter präzisiert,
      vereinfacht oder erweitert werden.
    </li>
    <li>
      <strong>Change-Management &amp; Kommunikation:</strong>
      Der Umgang mit Veränderungen wird als {{CHANGE_MANAGEMENT_LABEL}} bewertet.
      Bedeutung und Nutzen von KI sollten konsistent kommuniziert werden, um Akzeptanz zu steigern.
    </li>
    <li>
      <strong>Meldewege &amp; Vorfälle:</strong>
      Aktuelle Strukturen werden als {{MELDEWEGE_LABEL}} beschrieben.
      Klare Ansprechpersonen und einfache Abläufe erhöhen Sicherheit und Transparenz.
    </li>
    <li>
      <strong>Datenschutz &amp; Löschregeln:</strong>
      Die Angaben zu Datenschutz ({{DATENSCHUTZ_LABEL}}) und Löschregeln
      ({{LOESCHREGELN_LABEL}}) zeigen, dass Grundstrukturen vorhanden sind,
      jedoch noch stärker formalisiert werden sollten.
    </li>
    <li>
      <strong>Verantwortlichkeiten &amp; Kompetenzen:</strong>
      Die Benennung eines/einer Datenschutzbeauftragten ({{DATENSCHUTZBEAUFTRAGTER_LABEL}}),
      die vorhandene KI-Kompetenz ({{INTERNE_KI_KOMPETENZEN_LABEL}}) und der Status von
      Folgenabschätzungen ({{FOLGENABSCHAETZUNG_LABEL}}) liefern Hinweise auf Rollen,
      Zuständigkeiten und vorhandenes Know-how.
    </li>
  </ul>

  <h3>Strategische Leitlinien für die nächsten 12–24 Monate</h3>
  <ol>
    <li>
      <strong>Klare Einsatzregeln etablieren:</strong>
      Festlegung verbindlicher Spielregeln für Eingaben, Datenarten und Qualitätsstandards
      – bei Solo kompakt in Form persönlicher Routinen, bei Teams als gemeinsame Leitlinie,
      im KMU als abgestimmtes Regelwerk mit Verantwortlichkeiten.
    </li>
    <li>
      <strong>Verantwortlichkeiten definieren:</strong>
      Solo: eine Owner-Rolle für Nutzung & Qualität.<br>
      Team: Teamlead + KI-Owner + Anwender:innen.<br>
      KMU: Prozessverantwortliche in Fachbereichen + Datenschutz/IT.
    </li>
    <li>
      <strong>Transparenz &amp; Risikoabsicherung erhöhen:</strong>
      Kurze Dokumentation, einfache Meldewege und einheitliche Freigabepunkte sorgen dafür,
      dass Ergebnisse nachvollziehbar und sicher genutzt werden können.
    </li>
    <li>
      <strong>Kompetenzen gezielt aufbauen:</strong>
      Mini-Trainings, Leitfäden und kurze Reviews schaffen Sicherheit im Umgang mit KI.
      In KMU zusätzlich rollenspezifische Schulungen.
    </li>
  </ol>

  <h3>Verantwortung &amp; Steuerung</h3>
  <p>
    Die Steuerung des KI-Einsatzes sollte zur Organisationsstruktur passen:
    Solo-Unternehmen arbeiten mit einer klar definierten Owner-Rolle und
    festen Routinen; kleine Teams nutzen einen kompakten Steuerungskreis aus
    Teamlead und Anwender:innen; KMU setzen auf abgestimmte Verantwortlichkeiten
    zwischen Fachbereichen, Management und Datenschutz/IT.
    Transparenz, kurze Entscheidungswege und regelmäßige Reviews sind für alle
    Größen zentral, um Qualität und Sicherheit zu gewährleisten.
  </p>

  <p class="small muted">
    Eine realistische, gut kommunizierte Governance sichert nachhaltige Wirkung,
    unterstützt die Roadmap-Umsetzung und schafft Vertrauen bei Mitarbeitenden und
    Kund:innen gleichermaßen.
  </p>
</section>
