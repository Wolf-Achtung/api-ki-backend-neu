Developer:
<!-- PLATIN++ PROMPT v5.3 - SPRINT N -->
<!-- SECTION: foerderpotenzial -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BUNDESLAND_LABEL}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 3200 (solo:0.8x, team:1.0x, kmu:1.15x) -->
<!-- FOERDERLOGIK: DE-Bundesprogramme + Landesprogramme (KEINE EU-Core-Hinweise) -->
<!--
ZIEL: 4 Abschnitte mit je 180-220 Wörtern (= 720-880 Wörter gesamt).

STRUKTUR (4 Pflicht-Abschnitte):
  H3 1. Einordnung des Business Case ohne Förderung
  H3 2. Wie Fördermittel den Business Case verbessern
  H3 3. Passende Förderschwerpunkte für Ihr Vorhaben
  H3 4. Nächste Schritte für die Förderprüfung

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: niedrige Hürden, <10.000€, Beratungs-/Gründerförderung, BAFA, ERP-Gründerkredit
- team: Prozessdigitalisierung, KMU-innovativ, go-digital
- kmu: Digital Jetzt, ZIM, strukturelle Förderung

ANTI-REDUNDANZ:
- Business-Case-Zahlen EINMAL nennen, nicht wiederholen
- KEINE Wiederholung der Zahlen aus business_case.md – nur Förder-Kontext

SPRINT G18 - NARRATIVE VERBINDUNGEN:
- Bezug zu Tools herstellen: "Besonders relevant für die empfohlenen Tools und Starter Kits..."
- Tools × Funding Alignment erwähnen wo passend
- Bezug zu Roadmap: "Die Investitionen in Phase 1 der Roadmap..."

REGELN:
- Förderquoten nur als Bereiche (z.B. "30-50%")
- Sachlich, neutral, keine Werbung
- Keine Platzhalter, keine Developer-Sprache

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
-->

<section class="section funding-potential">
  <h2>Förderpotenzial für Ihr KI-Projekt</h2>

  <p>
    Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong> im Bundesland
    <strong>{{BUNDESLAND_LABEL}}</strong> und der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> verfügen für Vorhaben im Bereich
    <strong>{{HAUPTLEISTUNG}}</strong> häufig über gute Voraussetzungen für eine Förderung.
    Die Kombination aus Digitalisierungsfokus, KI-Unterstützung und klarer Prozessverbesserung
    entspricht den Schwerpunkten vieler Programme auf Landes- und Bundesebene.
  </p>

  <h3>1. Einordnung des Business Case ohne Förderung</h3>
  <p>
    Wie im vorherigen Kapitel "Business Case" dargestellt, weist das KI-Projekt eine
    solide wirtschaftliche Grundlage auf: Die Investition amortisiert sich innerhalb eines
    überschaubaren Zeitraums und erzielt einen positiven ROI im ersten Jahr.
  </p>
  <p>
    Diese Ausgangslage ist für viele Förderstellen attraktiv: Das Projekt ist betriebswirtschaftlich
    plausibel, der Nutzen klar erkennbar und der Eigenbeitrag grundsätzlich tragfähig. Fördermittel
    können diese Situation verbessern, indem sie einen Teil der Investitionsbelastung abfedern –
    das Projekt rechnet sich bereits ohne externe Unterstützung; mit Förderung wird die Rentabilität
    noch attraktiver.
  </p>

  <h3>2. Wie Fördermittel den Business Case verbessern können</h3>
  <p>
    Viele Programme in {{BUNDESLAND_LABEL}} und auf Bundesebene unterstützen KI- und
    Digitalisierungsinitiativen, indem sie einen Teil der förderfähigen Investitionskosten
    bezuschussen. Je nach Programm, Unternehmensgröße und Projektschwerpunkt bewegen sich
    die Zuschussquoten typischerweise im Bereich von etwa <strong>30–50&nbsp;%</strong>
    der anerkannten Kosten.
  </p>
  <ul>
    <li><strong>Kürzere Amortisationsdauer:</strong> Durch eine Beteiligung an den Investitionskosten
      sinkt der Eigenanteil; die im Business Case berechnete Amortisation kann sich
      deutlich verkürzen, ohne dass der erwartete Nutzen verändert wird.</li>
    <li><strong>Höherer effektiver ROI:</strong> Wenn ein Teil der Investitionen über Zuschüsse
      abgedeckt wird, steigt der Effektiv-Ertrag je eingesetztem Euro – bei 40% Förderung kann
      sich der ROI auf über das Doppelte des Basiswertes erhöhen.</li>
    <li><strong>Reduziertes finanzielles Risiko:</strong> Für <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
      kann ein Zuschuss den Schritt in ein ambitionierteres Projekt erleichtern, ohne die Liquidität
      unnötig zu belasten.</li>
    <li><strong>Mehr Spielraum für Qualität und Schulung:</strong> Einsparungen durch Förderung können
      genutzt werden, um zusätzliche Maßnahmen für Qualität, Sicherheit oder Qualifizierung vorzusehen.</li>
    <li><strong>Bessere Planungssicherheit:</strong> Mit bewilligter Förderung lässt sich das Projektbudget
      verlässlicher planen und das Risiko bei unerwarteten Mehrkosten besser abfedern.</li>
  </ul>

  <h3>3. Passende Förderschwerpunkte für Ihr Vorhaben</h3>
  <p>
    Basierend auf der Branche <strong>{{BRANCHE_LABEL}}</strong>, dem Schwerpunkt
    <strong>{{HAUPTLEISTUNG}}</strong> und der Unternehmensgröße
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> kommen folgende Förderkategorien in Frage:
  </p>
  <ul>
    <li><strong>Digitalisierungsförderung:</strong> Programme für KI-gestützte Prozessoptimierung,
      Automatisierung und digitale Werkzeuge. Besonders relevant für {{HAUPTLEISTUNG}}.</li>
    <li><strong>Innovationsförderung:</strong> Zuschüsse für neuartige KI-Anwendungen, Pilotprojekte
      und Technologieentwicklung, abgestimmt auf die Branche {{BRANCHE_LABEL}}.</li>
    <li><strong>Qualifizierungsförderung:</strong> Mittel für Schulungen, Weiterbildungen und den
      Aufbau von KI-Kompetenzen – wichtig für nachhaltige Nutzung.</li>
    <li><strong>Beratungsförderung:</strong> Unterstützung für externe Expertise bei der
      KI-Strategieentwicklung und Umsetzung.</li>
  </ul>

  <h3>4. Nächste Schritte für die Förderprüfung</h3>
  <ol>
    <li><strong>Programmauswahl:</strong> 1–2 Programme auswählen, die zu
      <strong>{{BRANCHE_LABEL}}</strong>, <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
      und <strong>{{HAUPTLEISTUNG}}</strong> passen.</li>
    <li><strong>Projektbeschreibung:</strong> Eine kompakte Projektbeschreibung erstellen
      (Ziele, Maßnahmen, Zeitplan, erwarteter Nutzen, grobe Kosten gemäß Business Case).</li>
    <li><strong>Kumulierungsprüfung:</strong> Prüfen, ob Programme aus {{BUNDESLAND_LABEL}}
      mit Bundes- oder EU-Programmen kombiniert werden dürfen.</li>
    <li><strong>Beratung einholen:</strong> Optional Rücksprache mit Förderberatungen, Kammern
      oder Finanzierungspartnern halten.</li>
    <li><strong>Zeitplanung:</strong> Förderanträge benötigen typischerweise 4–8 Wochen Vorlauf –
      dies bei der Projektplanung berücksichtigen.</li>
  </ol>

  <p class="small muted">
    Hinweis: Förderquoten, Fristen und Anforderungen können sich ändern. Vor Antragstellung
    sollten die offiziellen Richtlinien und Konditionen der jeweiligen Programme im Detail geprüft werden.
  </p>
</section>

<!-- DEV: PDF-SLIMDOWN v2.0 - Ziel: 720-880 Wörter, kompakt aber vollständig -->
