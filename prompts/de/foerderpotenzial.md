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
    Unternehmen der Branche <strong>{{BRANCHE_LABEL}}</strong> in <strong>{{BUNDESLAND_LABEL}}</strong>
    mit der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> erfüllen für Vorhaben im Bereich
    <strong>{{HAUPTLEISTUNG}}</strong> oft die Grundvoraussetzungen für Förderprogramme.
  </p>

  <h3>1. Einordnung des Business Case ohne Förderung</h3>
  <p>
    Das KI-Projekt weist eine solide wirtschaftliche Grundlage auf. Die Investition amortisiert sich
    in überschaubarem Zeitraum bei positivem ROI im ersten Jahr.
  </p>
  <p>
    Das Projekt ist betriebswirtschaftlich plausibel und der Eigenbeitrag tragfähig.
    Fördermittel können die Investitionsbelastung reduzieren und die Rentabilität verbessern.
  </p>

  <h3>2. Wie Fördermittel den Business Case verbessern können</h3>
  <p>
    Programme in {{BUNDESLAND_LABEL}} und auf Bundesebene bezuschussen förderfähige Investitionskosten.
    Zuschussquoten liegen typischerweise bei <strong>30–50&nbsp;%</strong> der anerkannten Kosten.
  </p>
  <ul>
    <li><strong>Kürzere Amortisation:</strong> Durch geringeren Eigenanteil verkürzt sich die Amortisationsdauer.</li>
    <li><strong>Höherer effektiver ROI:</strong> Bei 40% Förderung kann sich der ROI verdoppeln.</li>
    <li><strong>Reduziertes Risiko:</strong> Zuschüsse erleichtern ambitioniertere Projekte ohne Liquiditätsbelastung.</li>
    <li><strong>Spielraum für Qualifizierung:</strong> Einsparungen ermöglichen zusätzliche Schulungsmaßnahmen.</li>
    <li><strong>Bessere Planungssicherheit:</strong> Bewilligte Förderung macht das Budget verlässlicher planbar.</li>
  </ul>

  <h3>3. Passende Förderschwerpunkte für Ihr Vorhaben</h3>
  <p>
    Für <strong>{{BRANCHE_LABEL}}</strong> mit Schwerpunkt <strong>{{HAUPTLEISTUNG}}</strong>
    kommen folgende Förderkategorien in Frage:
  </p>
  <ul>
    <li><strong>Digitalisierungsförderung:</strong> Programme für KI-gestützte Prozessoptimierung und digitale Werkzeuge.</li>
    <li><strong>Innovationsförderung:</strong> Zuschüsse für KI-Pilotprojekte und Technologieentwicklung.</li>
    <li><strong>Qualifizierungsförderung:</strong> Mittel für Schulungen und Aufbau von KI-Kompetenzen.</li>
    <li><strong>Beratungsförderung:</strong> Unterstützung für externe Expertise bei KI-Strategie und Umsetzung.</li>
  </ul>

  <h3>4. Nächste Schritte für die Förderprüfung</h3>
  <ol>
    <li><strong>Programmauswahl:</strong> 1–2 passende Programme für {{BRANCHE_LABEL}} und {{UNTERNEHMENSGROESSE_LABEL}} identifizieren.</li>
    <li><strong>Projektbeschreibung:</strong> Ziele, Maßnahmen, Zeitplan und Kosten kompakt dokumentieren.</li>
    <li><strong>Kumulierungsprüfung:</strong> Kombinierbarkeit von Landes- und Bundesprogrammen klären.</li>
    <li><strong>Beratung einholen:</strong> Optional Rücksprache mit Förderberatungen oder Kammern.</li>
    <li><strong>Zeitplanung:</strong> Förderanträge benötigen 4–8 Wochen Vorlauf.</li>
  </ol>

  <p class="small muted">
    Hinweis: Förderquoten und Anforderungen können sich ändern. Vor Antragstellung die aktuellen Richtlinien prüfen.
  </p>
</section>

<!-- DEV: PDF-SLIMDOWN v2.0 - Ziel: 720-880 Wörter, kompakt aber vollständig -->

<!-- ZERO-LEAK POLICY (N4.6) -->
<!--
VERBOTEN – NIEMALS VERWENDEN:
- Keine Fragen an den Leser ("Haben Sie Fragen?", "Möchten Sie mehr erfahren?")
- Keine Aufforderungen ("Wenn Sie möchten...", "Kontaktieren Sie uns...")
- Keine Assistenten-Sprache ("Ich kann Ihnen helfen...", "Gerne erkläre ich...")
- Keine Angebote ("Bei Bedarf...", "Falls gewünscht...")
- Keine interaktiven Elemente ("Klicken Sie hier...", "Wählen Sie...")
- Keine Platzhalter ("[Hier einfügen]", "{{VARIABLE}}" außer definierten)
- Keine Meta-Kommentare ("Dieser Abschnitt...", "Im Folgenden...")

Der Output ist ein FINALER REPORT-ABSCHNITT, kein Gespräch.
-->
