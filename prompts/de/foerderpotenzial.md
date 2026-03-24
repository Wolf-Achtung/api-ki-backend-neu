Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT TRUNCATION-FIX -->
<!-- SECTION: foerderpotenzial -->
<!-- OUTPUT: HTML ONLY -->

## ABSOLUTE LÄNGENREGEL (VOR ALLEM ANDEREN!)
{% if COMPANY_SIZE == "solo" %}
**SOLO-HARD-LIMIT: Maximal 450 Wörter / 4.500 Zeichen HTML gesamt.**
Schreibe kompakt: nur die 2 relevantesten Förderkategorien, keine langen Erklärungen. Max 3 Bullets pro Sektion.
{% elif COMPANY_SIZE == "team" %}
**TEAM-HARD-LIMIT: Maximal 700 Wörter / 7.500 Zeichen HTML gesamt.**
{% else %}
**KMU-HARD-LIMIT: Maximal 900 Wörter / 10.000 Zeichen HTML gesamt.**
{% endif %}
JEDES WORT ÜBER DEM LIMIT WIRD BRUTAL ABGESCHNITTEN — der Report endet dann mitten im Satz!

## ROI-Regel (vor allem anderen beachten)
Prozentwerte (ROI, Rendite, Effizienz) NIEMALS über 200% angeben. Bei höheren Werten "200% (gedeckelt)" schreiben. Alle Zahlen KONSERVATIV.

ANTI-SCHEINPRÄZISION (VERBINDLICH): Keine exakten Zahlen, Fristen, Marktanteile, Prozentsätze, Tool-Preise oder Förderbeträge nennen, wenn sie nicht ausdrücklich im Input oder in der Recherche stehen. Bei fehlender Exaktheit lieber Spannbreite, Einordnung oder qualitative Formulierung nutzen. VERBOTEN: erfundene Prozentwerte, Monatszahlen, Eurobeträge, Rankings oder scheinbar exakte Benchmarks.

<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BUNDESLAND_LABEL}}, {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}, {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 4200 (solo:0.8x, team:1.0x, kmu:1.15x) -->
<!-- FIX-B23-P1: Increased from 3200→4200, word targets raised to avoid SECTION_TOO_SHORT -->

UMGANG MIT LÜCKENHAFTEN EINGABEN: Wenn ein Input fehlt oder unkonkret ist: - nichts erfinden, - die Aussage auf den belastbaren Kern reduzieren, - und nur den Teil formulieren, der fachlich tragfähig bleibt. Nutze keine Meta-Sätze über fehlende Datenquellen. Lieber präzise knapp als breit spekulativ.

<!--
BRANCHENBEZEICHNUNG-REGEL:
Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

HÖCHSTLÄNGE (STRIKT! — Überschreitung wird automatisch getruncated!):
- Solo: max. 4.500 Zeichen (450 Wörter) | Team: max. 7.500 Zeichen (700 Wörter) | KMU: max. 10.000 Zeichen (900 Wörter)
- Solo: 4 kurze Abschnitte × 90-110 Wörter = 380-450 Wörter gesamt
- Team: 4 Abschnitte × 150-175 Wörter = 600-700 Wörter gesamt
- Pro Bullet-Liste: Solo max. 3 Punkte, Team/KMU max. 5 Punkte
- GESAMT-ZIEL: Solo 380-450, Team 600-700, KMU 800-1000 Wörter
-->
<!-- FOERDERLOGIK: DE-Bundesprogramme + Landesprogramme (KEINE EU-Core-Hinweise) -->
<!--
###############################################################################
{% if COMPANY_SIZE == "solo" %}
**WICHTIG – Längenlimit: Deine Antwort soll 380-450 Wörter umfassen, maximal 500 Wörter.**
{% elif COMPANY_SIZE == "team" %}
**WICHTIG – Längenlimit: Deine Antwort soll 600-700 Wörter umfassen, maximal 800 Wörter.**
{% else %}
**WICHTIG – Längenlimit: Deine Antwort soll 800-1000 Wörter umfassen, maximal 1100 Wörter.**
{% endif %}
Kürze lieber als zu überziehen — abgeschnittener Content ist wertlos!

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
{% if COMPANY_SIZE == "solo" %}
ZIEL: 4 Abschnitte mit je 90-110 Wörtern (= 380-450 Wörter gesamt). KÜRZER IST BESSER!
{% elif COMPANY_SIZE == "team" %}
ZIEL: 4 Abschnitte mit je 150-175 Wörtern (= 600-700 Wörter gesamt).
{% else %}
ZIEL: 4 Abschnitte mit je 200-250 Wörtern (= 800-1000 Wörter gesamt).
{% endif %}

STRUKTUR (4 Pflicht-Abschnitte):
  H3 1. Einordnung des Business Case ohne Förderung
  H3 2. Wie Fördermittel den Business Case verbessern
  H3 3. Passende Förderschwerpunkte für Ihr Vorhaben
  H3 4. Nächste Schritte für die Förderprüfung

###############################################################################
##              KONDITIONALE FÖRDER-LOGIK (L4/L5/L8)                        ##
###############################################################################

INTERESSE AN FÖRDERUNG ({{INTERESSE_FOERDERUNG_LABEL}}):
{% if INTERESSE_FOERDERUNG_LABEL == "nein" or INTERESSE_FOERDERUNG_LABEL == "Kein Bedarf" %}
  → KURZ-VERSION: Das gesamte Förderpotenzial-Kapitel auf MAX 150 Wörter reduzieren.
  → Nur 1-2 Sätze: "Fördermittel stehen zur Verfügung, wurden aber aktuell nicht als
    Priorität angegeben. Bei zukünftigem Interesse: BAFA-Beratungsförderung und
    Digitalbonus/Landesprogramme wären erste Anlaufstellen."
  → KEINE 4 Abschnitte, KEINE ausführliche Analyse.
{% elif INTERESSE_FOERDERUNG_LABEL == "unklar" %}
  → Einleitung ergänzen: "Auch wenn Sie sich noch unsicher sind — folgende Programme
    könnten für Ihr Vorhaben relevant sein und eine Prüfung lohnt sich:"
  → Volle Section beibehalten.
{% endif %}

BISHERIGE FÖRDERMITTEL ({{BISHERIGE_FOERDERMITTEL}}):
{% if BISHERIGE_FOERDERMITTEL == "ja" %}
  → Im Abschnitt "Nächste Schritte" einen DE-MINIMIS-HINWEIS einbauen:
  → "<li><strong>De-minimis-Prüfung:</strong> Da bereits Fördermittel bezogen wurden:
     De-minimis-Grenze beachten (300.000 € innerhalb von 3 Kalenderjahren).
     Alle erhaltenen Beihilfen der letzten 3 Jahre zusammenstellen.
     Kumulierungsverbot: Nicht dieselben Kosten doppelt fördern lassen.</li>"
{% endif %}

BERATUNGSERFAHRUNG ({{ERFAHRUNG_BERATUNG}}):
{% if ERFAHRUNG_BERATUNG == "nein" %}
  → Im Abschnitt "Passende Förderschwerpunkte" die BAFA-Beratungsförderung
    BESONDERS hervorheben:
  → "Da bisher keine externe Beratung zu Digitalisierung/KI stattfand, ist die
     BAFA-Förderung von Unternehmensberatungen ein idealer Einstiegspunkt
     ({{BAFA_FOERDERQUOTE}}% Zuschuss, max. {{BAFA_MAX_FOERDERUNG}})."
{% endif %}

###############################################################################

DETERMINISTISCHE BAFA-DATEN (verwende EXAKT diese Werte, KEINE eigenen Schätzungen):
- Programm: BAFA "Förderung von Unternehmensberatungen für KMU"
- Förderquote für {{BUNDESLAND_LABEL}}: {{BAFA_FOERDERQUOTE}}%
- Maximaler Zuschuss für {{BUNDESLAND_LABEL}}: {{BAFA_MAX_FOERDERUNG}}
- WICHTIG: Verwende für BAFA NUR diese Werte. Erfinde KEINE anderen BAFA-Beträge.

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: niedrige Hürden, <10.000€, Beratungs-/Gründerförderung, BAFA ({{BAFA_FOERDERUNG_DISPLAY}}), ERP-Gründerkredit
- team: Prozessdigitalisierung, KMU-innovativ, BAFA ({{BAFA_FOERDERUNG_DISPLAY}})
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

<!-- DEV: PDF-SLIMDOWN v2.2 - TRUNCATION-FIX: Solo 380-450, Team 600-700, KMU 800-1000 Wörter -->
<!-- FINAL CHECK VOR OUTPUT: Zähle deine Wörter. Solo >500? KÜRZEN! Team >800? KÜRZEN! KMU >1100? KÜRZEN! -->

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
