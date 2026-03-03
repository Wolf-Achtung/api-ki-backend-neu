Developer:
<!-- PLATIN++ PROMPT v5.3 - SPRINT N -->
<!-- SECTION: foerderpotenzial -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BUNDESLAND_LABEL}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 4200 (solo:0.8x, team:1.0x, kmu:1.15x) -->
<!-- FIX-B23-P1: Increased from 3200→4200, word targets raised to avoid SECTION_TOO_SHORT -->
<!--
BRANCHENBEZEICHNUNG-REGEL:
Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

HÖCHSTLÄNGE (STRIKT! — Überschreitung wird automatisch getruncated!):
- Budget: 11000 Zeichen HTML-Output — NICHT überschreiten!
- Solo: max. 8000 Zeichen | Team: max. 10000 Zeichen | KMU: max. 12000 Zeichen
- B714: 14.802 Zeichen generiert, auf 8.261 getruncated → 44% VERLUST!
- 4 Abschnitte × 200-275 Wörter = 800-1100 Wörter gesamt
- Pro Bullet-Liste: max. 5-6 Punkte à 1-2 Sätze
- GESAMT-ZIEL: 850-1100 Wörter (steht auch unten bei PDF-SLIMDOWN)
-->
<!-- FOERDERLOGIK: DE-Bundesprogramme + Landesprogramme (KEINE EU-Core-Hinweise) -->
<!--
###############################################################################
**WICHTIG – Längenlimit: Deine Antwort soll 850-1100 Wörter umfassen, maximal 1400 Wörter. Kürze lieber als zu überziehen.**

##                    STANDORT KONSISTENZ (KRITISCH!)                        ##
###############################################################################

⚠️ KEINE FALSCHEN BUNDESLÄNDER NENNEN!

Das Bundesland des Users ist: {{BUNDESLAND_LABEL}}
- NUR dieses Bundesland in Förder-Kontexten verwenden
- KEINE anderen Bundesländer halluzinieren!
- NICHT "Berlin" schreiben wenn {{BUNDESLAND_LABEL}} = "Nordrhein-Westfalen"

VERBOTEN:
❌ Ein anderes Bundesland als {{BUNDESLAND_LABEL}} nennen
❌ Förderprogramme eines anderen Bundeslandes empfehlen
❌ "Berlin", "Bayern", "NRW" etc. wenn nicht {{BUNDESLAND_LABEL}}

ERLAUBT:
✅ {{BUNDESLAND_LABEL}} verwenden (der echte Wert)
✅ "Ihr Bundesland" als generische Alternative
✅ Bundesprogramme (gelten überall)

###############################################################################
-->
<!--
ZIEL: 4 Abschnitte mit je 200-275 Wörtern (= 850-1100 Wörter gesamt).

STRUKTUR (4 Pflicht-Abschnitte):
  H3 1. Einordnung des Business Case ohne Förderung
  H3 2. Wie Fördermittel den Business Case verbessern
  H3 3. Passende Förderschwerpunkte für Ihr Vorhaben
  H3 4. Nächste Schritte für die Förderprüfung

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: niedrige Hürden, <10.000€, Beratungs-/Gründerförderung, BAFA, ERP-Gründerkredit
- team: Prozessdigitalisierung, KMU-innovativ, go-digital
- kmu: ZIM, KfW-Digitalisierung, strukturelle Förderung

ANTI-REDUNDANZ:
- Business-Case-Zahlen EINMAL nennen, nicht wiederholen
- KEINE Wiederholung der Zahlen aus business_case.md – nur Förder-Kontext

THEMEN-OWNERSHIP (verbindlich):
- Diese Section: OWNER für Förderpotenzial, Förderkategorien, Nächste Schritte Förderantrag
- NICHT hier: Business Case Details (→ business_case)
- NICHT hier: Compliance/AI Act (→ ai_act_summary)
- NICHT hier: Tool-Kosten (→ tools_empfehlungen)

SPRINT G18 - NARRATIVE VERBINDUNGEN:
- Bezug zu Tools herstellen: "Besonders relevant für die empfohlenen Tools und Starter Kits..."
- Tools × Funding Alignment erwähnen wo passend
- Bezug zu Roadmap: "Die Investitionen in Phase 1 der Roadmap..."

REGELN:
- Förderquoten nur als Bereiche (z.B. "30-50%")
- Sachlich, neutral, keine Werbung
- Keine Platzhalter, keine Developer-Sprache

=============================================================================
ANTI-TEXTWÜSTEN REGELN v1.0 (STRIKT - PFLICHT!)
=============================================================================
PROBLEM: Lange Textblöcke sind im PDF unlesbar, auch mit farbiger Box.
LÖSUNG: Jede Sektion MUSS strukturiert sein mit Bullets.

ABSATZ-REGELN (PFLICHT):
- Maximal 3 Sätze pro Absatz
- Nach jedem Absatz: Leerzeile ODER Bullet-Liste
- KEINE Absätze über 80 Wörter
- KEINE Sektion ohne Bullet-Liste

STRUKTUR PRO SEKTION (PFLICHT):
1. Einleitungssatz (1-2 Sätze max)
2. Bullet-Liste mit 3-5 Punkten (PFLICHT in JEDER Sektion!)
3. Optional: Kurzer Abschlusssatz

FORMAT-TEMPLATE:
<p><strong>[Kernaussage]</strong></p>
<ul>
  <li><strong>[Stichwort]:</strong> [Erklärung in 1 Satz]</li>
  <li><strong>[Stichwort]:</strong> [Erklärung in 1 Satz]</li>
  <li><strong>[Stichwort]:</strong> [Erklärung in 1 Satz]</li>
</ul>

VERBOTEN - TEXTWÜSTEN-MUSTER:
❌ Absätze mit mehr als 4 Sätzen
❌ Mehrere Absätze hintereinander ohne Bullet-Liste
❌ Sektionen die NUR aus Fließtext bestehen
❌ Fließtext über 100 Wörter am Stück

BEISPIEL Sektion 1 - SO NICHT:
❌ "Das Geschäftsmodell basiert auf einem erweiterbaren Angebot, das verschiedene
    Komponenten kombiniert und dabei die Wirtschaftlichkeit im Blick behält,
    wobei die Investitionen sich über einen planbaren Zeitraum amortisieren
    und gleichzeitig Spielraum für weitere Entwicklung lassen..." [= TEXTWÜSTE!]

BEISPIEL Sektion 1 - SO JA:
✅ <p><strong>Der Business Case ist auch ohne Förderung tragfähig:</strong></p>
   <ul>
     <li><strong>Investition:</strong> Überschaubare Anfangsinvestition mit klarem Scope</li>
     <li><strong>Amortisation:</strong> Rückfluss innerhalb von X Monaten realistisch</li>
     <li><strong>Risiko:</strong> Geringes Ausfallrisiko durch modularen Ansatz</li>
   </ul>
   <p>Fördermittel verbessern diese Ausgangslage zusätzlich.</p>
=============================================================================

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
  <p><strong>Der Business Case trägt sich auch ohne Fördermittel:</strong></p>
  <ul>
    <li><strong>Investitionshöhe:</strong> [Einordnung der Kosten für {{COMPANY_SIZE}}]</li>
    <li><strong>Amortisation:</strong> Rückfluss in überschaubarem Zeitraum realistisch</li>
    <li><strong>Risikoprofil:</strong> [Einordnung des Risikos für {{BRANCHE_LABEL}}]</li>
    <li><strong>Eigenbeitrag:</strong> Aus laufendem Betrieb finanzierbar</li>
  </ul>
  <p>Fördermittel sind kein Muss, verbessern aber die Ausgangslage deutlich.</p>

  <h3>2. Wie Fördermittel den Business Case verbessern können</h3>
  <p>
    Programme in {{BUNDESLAND_LABEL}} und auf Bundesebene bezuschussen förderfähige Investitionskosten.
    Zuschussquoten liegen in der Regel bei <strong>30–50&nbsp;%</strong> der anerkannten Kosten.
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

<!-- DEV: PDF-SLIMDOWN v2.1 - Ziel: 850-1100 Wörter, kompakt aber vollständig (FIX-B23-P1) -->

<!-- ZERO-LEAK POLICY (N4.6) -->
<!--
VERBOTEN – NIEMALS VERWENDEN:
- Keine Fragen an den Leser ("Haben Sie Fragen?", "Möchten Sie mehr erfahren?")
- Keine Aufforderungen ("Wenn Sie möchten...", "Kontaktieren Sie uns...")
- Keine Assistenten-Sprache ("Ich kann Ihnen helfen...", "Gerne erkläre ich...")
- Keine Angebote ("Bei Bedarf...", "Falls gewünscht...")
- Keine interaktiven Elemente ("Klicken Sie hier...", "Wählen Sie...")
- Keine Platzhalter oder Template-Variablen (außer definierten Eingabevariablen)
- Keine Meta-Kommentare ("Dieser Abschnitt...", "Im Folgenden...")

Der Output ist ein FINALER REPORT-ABSCHNITT, kein Gespräch.
-->
