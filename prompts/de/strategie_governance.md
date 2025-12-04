Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: strategie_governance -->
<!-- VERSION: v6.0 PLATIN++ V5 -->
<!-- OUTPUT: HTML -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{COMPANY_SIZE}}, {{GOVERNANCE_RICHTLINIEN_LABEL}}, {{CHANGE_MANAGEMENT_LABEL}}, {{MELDEWEGE_LABEL}}, {{DATENSCHUTZ_LABEL}}, {{LOESCHREGELN_LABEL}}, {{DATENSCHUTZBEAUFTRAGTER_LABEL}}, {{FOLGENABSCHAETZUNG_LABEL}}, {{INTERNE_KI_KOMPETENZEN_LABEL}} -->
<!-- TOKEN-BUDGET: 2000 (solo:0.8x=1600, team:1.0x=2000, kmu:1.15x=2300) -->
<!--
ZIEL: Strategische Einordnung zu KI-Strategie & Governance.
Ergebnis = 10–14 Sätze + 1 strukturierte Liste.

PERSONA-VARIATIONEN (COMPANY_SIZE) – STRIKT EINHALTEN:

SOLO:
  Empfohlen: "Checkliste", "Minimale Regeln", "Ein-Personen-Standard",
             "Dokumentation light", "persönliche Routine", "eigene Prüfpunkte"
  Nicht verwenden: "Organisationsentwicklung", "Verantwortlichkeitsmatrix",
                   "Governance Framework", "Rollenmodell", "Gremium", "Board",
                   "Steuerungskreis", "Abteilung", "Team aufbauen", "Mitarbeiter"

TEAM:
  Empfohlen: "Teamabsprache", "gemeinsame Regeln", "KI-Koordinator",
             "kurze Review-Runde", "geteilte Verantwortung"
  Nicht verwenden: "Governance Board", "Matrix-Organisation", "Division"

KMU:
  Empfohlen: "Fachbereichsverantwortliche", "abgestimmte Prozesse",
             "bereichsübergreifende Standards", "Governance-Regeln"
  Nicht verwenden: Konzernjargon ("Business Unit", "Division", "C-Level")

ANTI-REDUNDANZ:
- Governance HIER vollständig behandeln
- NICHT in org_change wiederholen
- NICHT in risks duplizieren

GUARDRAILS: Berücksichtige Leitplanken aus strategischem Kontext.
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
    <li>
      <strong>Monetarisierungspotenziale evaluieren (optional):</strong>
      KI-gestützte Prozesse können neue Erlösquellen erschließen – etwa durch
      digitale Produkte, skalierbare Service-Formate oder automatisierte Analysen.
      Eine strategische Bewertung lohnt sich insbesondere bei stabilen Kern-Workflows.
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
