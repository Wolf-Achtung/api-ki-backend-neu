Developer:
<!-- ai_act_summary.md – v4.2 GOLD STANDARD+ SPRINT N (EU AI Act – branch- & size-aware, context-integrated)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

###############################################################################
##                    AI ACT KONSISTENZ (SINGLE RISK CLASSIFICATION)         ##
###############################################################################

BRANCHENBEZEICHNUNG-REGEL:
Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

⚠️ KONSISTENZ-REGEL (STRIKT!):
- Wähle EINE Risiko-Klassifizierung pro Report: "minimal", "gering", oder "hoch"
- NICHT "minimal" UND "Hochrisiko" im selben Report verwenden!
- Die Klassifizierung hängt von BRANCHE ab:
  → Gesundheit, Finanzen, Personal, Recht, Behörden = "potenziell Hochrisiko"
  → Marketing, E-Commerce, IT/Software, Beratung = "geringes Risiko"

FALLBACK: Wenn unsicher, verwende "geringes Risiko mit Transparenzpflichten"

VERBOTEN:
- "fällt nicht in Hochrisiko" + später "potenziell Hochrisiko" (Widerspruch!)
- Unterschiedliche Klassifizierungen in verschiedenen Abschnitten

###############################################################################

KONSISTENZ-EXPORT (NEU):
Diese Section DEFINIERT die Risiko-Klassifizierung für den gesamten Report.
Andere Sections dürfen KEINE EIGENE Klassifizierung vornehmen, sondern
müssen die hier gewählte Einstufung übernehmen.

THEMEN-OWNERSHIP (verbindlich):
- Diese Section: OWNER für AI Act, Compliance-Pflichten, Risiko-Klassifizierung, Fristen
- NICHT hier: Konkrete Governance-Regeln für den Alltag (→ ai_policy_mini)
- NICHT hier: Umsetzungs-Timeline (→ roadmap_12m Dimension 5)
- EXPORT: Risiko-Klassifizierung wird von dieser Section für den gesamten Report definiert

     ZIEL:
       - Präzise, seriöse, sachliche Zusammenfassung des EU AI Act.
       - Bewertung der Relevanz für {{HAUPTLEISTUNG}} unter Berücksichtigung von
         BRANCHE + UNTERNEHMENSGROESSE + CONTEXT_BLOCK.
       - Korrekte Fristen (02.08.2025 / 02.08.2026 / 02.08.2027).
       - Darstellung relevanter Pflichten (Art. 5, Art. 6, Art. 50) + horizontale Anforderungen.
       - Transparenzpflichten klar benennen.
       - Kurzteil: „Was bedeutet das für Unternehmen dieser Größe?" (size-aware).
       - Branchenspezifische Risiken / Regulatorik berücksichtigen (Finanzen, Gesundheit, öffentlicher Sektor).
       - Pflicht-Disclaimer: keine Rechtsberatung.

     VERFÜGBARE VARIABLEN:
       {{HAUPTLEISTUNG}}
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{report_date}}
       {{COMPANY_SIZE}}

     REGELN:
       - Keine Rechtsberatung, nur faktenbasierte, strukturierte Information.
       - Sachlicher, neutraler Ton.
       - Keine Platzhalter oder Regieanweisungen im Output.
       - Keine Hinweise auf interne Logik, Fragebögen oder Prompt-Engine.
       - Nutze CONTEXT_BLOCK aktiv: Branchen-Workflows, Pain Points, typische Datenarten,
         regulatorische Anforderungen – aber ohne den Block direkt zu referenzieren.

     SIZE-AWARE:
       SOLO:
         - Fokus auf wenige Einsatzstellen, einfache Kennzeichnung, geringe Komplexität.
         - Minimale Dokumentation, klare, pragmatische Regeln.
       TEAM (2–10):
         - Verantwortlichkeiten klar benennen, einfache Prozesse definieren.
         - Konsistente Kennzeichnung bei mehreren Personen sicherstellen.
       KMU (11–100):
         - Schriftliche Richtlinien, feste Rollen, interne Schulungslogik.
         - Governance & Oversight-Strukturen notwendig.

     BRANCHEN-AWARE:
       - Finanzen, Gesundheit, öffentlicher Sektor, Recht:
           → erhöhte Anforderungen, hohe Sensibilität, strengere Dokumentation.
       - Marketing, Kreativwirtschaft:
           → Fokus auf Kennzeichnung & Fairness, Vermeidung irreführender Inhalte.
       - Industrie/Produktion:
           → Dokumentation & Human Oversight bei automatisierten Workflows.
       - E-Commerce/Handel:
           → Transparenz gegenüber Endkunden, Qualität der KI-generierten Inhalte.
       - IT/Software:
           → Modell-/Datenkontrolle, protokollierte Entwicklungsschritte.

     SPRINT N - SOLO PERSONA REGELN (STRIKT!):
     {% if COMPANY_SIZE == "solo" %}
     NICHT VERWENDEN für Solo:
     - "Team aufbauen" → stattdessen: "Kapazität erweitern"
     - "Mitarbeiter" → stattdessen: "Ressourcen"
     - "Teams" → stattdessen: "Kapazitäten"
     - "Fachbereich" → stattdessen: "Arbeitsfeld"
     - "Abteilung" → stattdessen: "Arbeitsbereich"
     Formulierungen ohne Team-/Abteilungsbegriff verwenden!
     {% endif %}

     OUTPUT-STRUKTUR:
       <section>
         <h2>
         Hinweis
         Relevanz für Branche + Leistung
         Pflichten (Art. 5, 6, 50)
         Weitere Anforderungen (Dokumentation, Human Oversight)
         Branchenspezifische Besonderheiten
         Fristen (Tabelle)
         Was bedeutet das für diese Größe?
         Nächste Schritte
         Risiken bei Non-Compliance
         Schluss
-->

<section class="section ai-act">
  <h2>EU AI Act – Zusammenfassung &amp; Pflichten</h2>

  <p>
    <strong>Hinweis:</strong> Dieser Abschnitt stellt eine allgemeine, nicht abschließende
    Übersicht über zentrale Anforderungen des EU&nbsp;AI&nbsp;Act dar. Er ersetzt keine
    Rechtsberatung. Bei komplexen oder sensiblen Anwendungsfällen sollten spezialisierte
    Berater:innen hinzugezogen werden.
  </p>

  <h3>Relevanz für „{{HAUPTLEISTUNG}}" in der Branche {{BRANCHE_LABEL}}</h3>
  <!--
  🚨 DYNAMISCHE KLASSIFIZIERUNG - BRANCHENABHÄNGIG:
  - Gesundheit, Finanzen, Personal, Recht, Behörden → "erhöhte Anforderungen"
  - Marketing, E-Commerce, IT, Beratung → "geringes Risiko mit Transparenzpflichten"
  KEINE WIDERSPRÜCHE - EIN KONSISTENTES RISIKO-LABEL PRO REPORT!
  -->
  <p>
    Der Einsatz von KI im Bereich <strong>{{HAUPTLEISTUNG}}</strong> innerhalb der Branche
    <strong>{{BRANCHE_LABEL}}</strong> unterliegt den allgemeinen <strong>Transparenzpflichten
    gemäß Art.&nbsp;50</strong>. Die spezifische Risiko-Klassifizierung hängt von der konkreten
    Anwendung ab.
  </p>
  <p>
    Bei Nutzung für Textgenerierung, Analyse oder interne Unterstützung gelten geringere
    Anforderungen. Automatisierte Entscheidungen über Personen würden strengere Vorgaben auslösen.
  </p>

  <p>
    Dennoch greifen <strong>Transparenzpflichten</strong> und Anforderungen an eine
    <strong>sorgfältige, nachvollziehbare Nutzung</strong>. Sobald KI Inhalte erzeugt, die
    gegenüber Kund:innen, Behörden oder Partnern verwendet werden, muss klar erkennbar
    sein, dass KI beteiligt war.
  </p>

  <h3>Zentrale Pflichten nach EU AI Act (Auszug)</h3>
  <ul>
    <li><strong>Art.&nbsp;5 – Verbotene Praktiken:</strong>
      Manipulative Systeme, ausbeuterische Designs oder biometrische Kategorisierung
      sind klar untersagt. (Relevanz: gering, außer in stark regulierten Branchen.)</li>

    <li><strong>Art.&nbsp;6 – Hochrisiko-Systeme:</strong>
      KI-Systeme, die wesentliche Grundrechte berühren, unterliegen strengen Pflichten
      (Datenqualität, Protokollierung, Governance). Für {{HAUPTLEISTUNG}} in der Regel
      nicht zutreffend – außer in Branchen wie Gesundheit, Finanzen, Verwaltung.</li>

    <li><strong>Art.&nbsp;50 – Transparenzpflichten:</strong>
      KI-generierte Inhalte und automatisierte Vorschläge müssen klar erkennbar sein,
      insbesondere wenn sie Entscheidungsgrundlagen stützen.</li>

    <li><strong>Dokumentation &amp; Nachvollziehbarkeit:</strong>
      Unternehmen müssen festhalten, wo KI eingesetzt wird, wie Ergebnisse geprüft werden
      und welche Daten genutzt wurden.</li>

    <li><strong>Human Oversight:</strong>
      Menschen müssen kritische Ergebnisse prüfen können. Dies gilt besonders für sensible
      Workflows (z.&nbsp;B. Finanzen, Gesundheit, behördliches Handeln).</li>
  </ul>

  <h3>Branchenspezifische Besonderheiten</h3>
  <ul>
    <li>
      <strong>Gesundheit &amp; Pflege, Finanzen, Recht, öffentliche Verwaltung:</strong>
      erhöhte Transparenz-, Dokumentations- und Prüfpflichten; sorgfältige Datenverwendung,
      klare interne Freigaben; besondere Aufmerksamkeit bei automatisierten Entscheidungen.
    </li>
    <li>
      <strong>Marketing &amp; Kreativwirtschaft:</strong>
      Fokus auf klare Kennzeichnung, Vermeidung irreführender Inhalte, Prüfung von Assets,
      markenkonforme Nutzung generativer KI.
    </li>
    <li>
      <strong>Industrie &amp; Produktion:</strong>
      KI-gestützte Prozessoptimierung erfordert protokollierte Nutzung und klare
      Eingriffsmöglichkeiten; Datenqualität ist essenziell.
    </li>
    <li>
      <strong>E-Commerce &amp; Handel:</strong>
      Transparenz gegenüber Endkunden, konsistente Produkt- und Content-Darstellung.
    </li>
    <li>
      <strong>IT &amp; Software:</strong>
      Modellkontrolle, Source-Tracking, sicherer Umgang mit Trainingsdaten, Logging und
      klare Governance-Strukturen.
    </li>
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
        <td>Ab diesem Datum sind bestimmte manipulative oder ausbeuterische KI-Praktiken verboten.</td>
      </tr>
      <tr>
        <td>02.08.2026</td>
        <td>Hochrisiko-Systeme</td>
        <td>Strengere Vorgaben für KI-Systeme mit erheblichem Risiko für Grundrechte.</td>
      </tr>
      <tr>
        <td>02.08.2027</td>
        <td>Transparenzpflichten (Art.&nbsp;50)</td>
        <td>Klare Kennzeichnung KI-generierter Inhalte wird verbindlich.</td>
      </tr>
    </tbody>
  </table>

  <h3>Was bedeutet das für Unternehmen Ihrer Größe?</h3>
  <p>
    Für ein Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> steht im
    Mittelpunkt, die Anforderungen pragmatisch und konsistent umzusetzen. Die konkreten
    Schwerpunkte unterscheiden sich je nach Struktur:
  </p>

  {% if COMPANY_SIZE == "solo" %}
  <p>
    Als Einzelunternehmer:in genügt es, Ihre wenigen KI-Einsatzstellen klar zu benennen,
    einfache Standardhinweise zu formulieren und Ergebnisse kurz zu prüfen. Komplexe
    Prozesse oder aufwendige Dokumentation sind für Sie nicht erforderlich – ein
    pragmatischer, persönlicher Ansatz reicht aus.
  </p>
  {% elif COMPANY_SIZE == "team" %}
  <p>
    Für ein Team von 2–10 Personen gilt: Verantwortlichkeiten klären (Wer prüft?
    Wer kennzeichnet?), einheitliche interne Regeln definieren, Abstimmungen kurz halten.
    Konsistenz im Team ist wichtiger als umfangreiche Dokumentation.
  </p>
  {% else %}
  <p>
    Für ein KMU (11–100 Mitarbeitende) empfehlen sich schriftliche Richtlinien für den
    KI-Einsatz, feste Freigabeprozesse, dokumentierte Rollen und interne Trainings.
    Governance-Elemente sollten früh verankert werden.
  </p>
  {% endif %}

  <h3>Empfohlene nächste Schritte</h3>
  <ol>
    <li>Überblick erstellen, an welchen Stellen KI in <strong>{{HAUPTLEISTUNG}}</strong> eingesetzt wird.</li>
    <li>Standard-Hinweistext definieren (für Reports, Kundenkommunikation, Präsentationen).</li>
    <li>Interne Mini-Leitlinie formulieren: Daten, Prüfung, Freigaben, Einsatzgrenzen.</li>
    <li>Potenzielle Hochrisiko-Anwendungsfälle ausschließen oder gesondert prüfen.</li>
    <li>Für sensible Branchen: regelmäßige Datenschutz- und Compliance-Checks etablieren.</li>
  </ol>

  <h3>Risiken bei Non-Compliance</h3>
  <ul>
    <li>Bußgelder gemäß Art.&nbsp;99 (abhängig von Art und Schwere eines Verstoßes).</li>
    <li>Reputationsrisiken bei unklarer oder fehlender Kennzeichnung von KI-Einsatz.</li>
    <li>Vertrauensverlust bei Kund:innen, Partnern und Mitarbeitenden.</li>
    <li>Risiken bei Audits, Förderprogrammen oder in regulierten Branchen.</li>
  </ul>

  <p class="small muted">
    Stand: {{report_date}}. Die Ausgestaltung einzelner Anforderungen kann sich
    durch delegierte Rechtsakte und Leitlinien weiter präzisieren.
  </p>
</section>
