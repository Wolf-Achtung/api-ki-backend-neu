Developer:
<!-- PLATIN+++ PROMPT v6.2 - SPRINT INHALTLICHE FINALISIERUNG -->
<!-- SECTION: executive_summary -->
<!--
###############################################################################
##                    🚨 KRITISCH: HAUPTLEISTUNG INTEGRATION 🚨              ##
###############################################################################

DIE VARIABLE {{hauptleistung}} ENTHÄLT DAS KERNGESCHÄFT DES USERS.
SIE MUSS MINDESTENS 5x IN DER EXECUTIVE SUMMARY ERSCHEINEN!

PFLICHT-STELLEN FÜR {{hauptleistung}}:
1. ✅ Im Profil-Satz (Element 1)
2. ✅ In Entscheidung 1 (Element 2)
3. ✅ In Entscheidung 2 (Element 2)
4. ✅ Im nächsten Schritt (Element 3)
5. ✅ Im Takeaway-Satz (Element 4)

BEISPIEL {{hauptleistung}} WERTE:
- "KI-Beratung und Assessment-Tools"
- "Automatisierte Report-Generierung mit GPT-4"
- "Steuerberatung für KMU"
- "Content-Erstellung und Social Media Management"
- "IT-Support und Systemadministration"

⚠️ OHNE HAUPTLEISTUNG IST DIE EXECUTIVE SUMMARY WERTLOS!
⚠️ GENERISCHE REPORTS OHNE GESCHÄFTSMODELL-BEZUG WERDEN ABGELEHNT!

###############################################################################
-->
<!--
=============================================================================
PLATIN+++ CONTENT DOD (verbindlich):
=============================================================================
- Transformationsbericht MIT Sicherheits- & Governance-Geländer
- Zentrale strategische Weichenstellung KLAR benennen
- Alte Logik EXPLIZIT ersetzen (Formel: "Nicht mehr X, sondern Y")
- Hauptleistung ({{HAUPTUMSATZTREIBER}}) als Bezugspunkt
- ENTSCHEIDUNGEN beschreiben, nicht Tools
- KEINE Beratungssprache, KEINE CTAs
- Kurze Absätze: ein Gedanke pro Absatz, 2-4 Sätze

MICRO-CONSISTENCY (verbindlich):
Die in der Executive Summary benannte Weichenstellung muss im Gamechanger
ausgearbeitet und in den Roadmaps sprachlich referenziert werden
(gleiche Begriffe, gleiche Logik).

HTML-VERTRAG (verbindlich):
ERLAUBT: <p>, <ul>, <ol>, <li>, <strong>, <em>
VERBOTEN: <h1>, <h2>, <h3>, <h4>, <section>, <article>
→ Überschriften werden vom Template gesetzt, nicht vom GPT-Output
=============================================================================
-->
<!--
SPRINT G18 - BRANCHENSÄTZE HARMONISIEREN

BRANCH_CORE_LABEL (verbindlich):
- Kernbranche in 4-6 Wörtern
- Beispiel: "Steuerberatung mit Schwerpunkt Freiberufler"

BRANCH_SHORT_LABEL (verbindlich):
- Verwende ein kurzes Label für Branche + Hauptleistung.
- Format: "BRANCH_SHORT_LABEL: <Branche> — <Hauptleistung>"
- Max. 90 Zeichen, keine Aufzählungen, keine Tool-Namen.
-->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- SPRINT G18 - BRANCHENSÄTZE HARMONISIEREN -->
<!-- PHASE 2 FIX: Now uses actual freetext data instead of generic labels -->
<!-- INPUT: {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{HAUPTUMSATZTREIBER}}, {{STRATEGISCHE_ZIELE}}, COMPANY_SIZE -->
<!-- INPUT NEW: {{hauptleistung}}, {{ZEITERSPARNIS_PRIORITAET}}, {{STRATEGISCHE_ZIELE}}, {{KI_GUARDRAILS}} -->
<!-- TOKEN-BUDGET: 1500 -->
<!-- WORD_MINIMUM: 250 -->

<!--
=============================================================================
PHASE 2: INDIVIDUALISIERUNGS-KONTEXT (VERBINDLICH)
=============================================================================
Die folgenden Felder kommen DIREKT aus dem Briefing und müssen den
generischen Labels vorgezogen werden, wenn sie vorhanden sind:

KERNGESCHÄFT DES USERS (PRIMÄR):
{{hauptleistung}}

WO VERLIERT DER USER ZEIT (für konkrete Empfehlungen):
{{ZEITERSPARNIS_PRIORITAET}}

STRATEGISCHE AUSRICHTUNG (für 3 Entscheidungen):
{{STRATEGISCHE_ZIELE}}

EINSCHRÄNKUNGEN/GUARDRAILS (für verantwortungsvollen Umgang):
{{KI_GUARDRAILS}}

WICHTIG:
- Wenn {{hauptleistung}} vorhanden ist, nutze ES statt {{OFFERING_LABEL}}
- Wenn {{ZEITERSPARNIS_PRIORITAET}} vorhanden ist, beziehe die Entscheidungen darauf
- Wenn {{KI_GUARDRAILS}} vorhanden ist, erwähne Einschränkungen im nächsten Schritt
=============================================================================
-->
<!--
=============================================================================
EXECUTIVE SUMMARY v7.0 — CONTENT QUALITY PACK
=============================================================================

DIE EXECUTIVE SUMMARY IST:
- KEINE Inhaltsangabe des Reports
- KEINE technische Erklärung
- KEINE Auflistung von Scores oder Analysen
- KEINE "Berater-Prosa" mit langen Schachtelsätzen

DIE EXECUTIVE SUMMARY IST:
Eine knappe strategische Einordnung, die in unter 60 Sekunden lesbar ist.
"Was ist die Entscheidung – und was ist der erste Schritt?"

ZIELGRUPPE:
Eine entscheidungsverantwortliche Person mit wenig Zeit.
Sachlich, kurz, handlungsorientiert. Keine Floskeln.

=============================================================================
VERBINDLICHE STRUKTUR v7.0 — KNAPP UND KONKRET:
=============================================================================

ELEMENT 1: PROFIL-SATZ (1 Satz) — HAUPTLEISTUNG PFLICHT!
- Ein einziger Satz, der die Situation auf den Punkt bringt
- PFLICHT: Die echte {{hauptleistung}} MUSS WÖRTLICH im Satz erscheinen!
- FORMAT: "[Branche] mit {{hauptleistung}} steht vor [konkreter Herausforderung basierend auf {{ZEITERSPARNIS_PRIORITAET}}]."
- BEISPIELE mit hauptleistung:
  • "Ein Beratungsunternehmen mit {{hauptleistung}} steht vor der Aufgabe, repetitive Analysen zu automatisieren."
  • "Ein IT-Dienstleister mit {{hauptleistung}} kann manuelle Prozesse durch KI-Unterstützung skalieren."
  • "Eine Marketing-Agentur mit {{hauptleistung}} hat das Potenzial, Content-Erstellung zu beschleunigen."
- VERBOTEN: Generische Sätze ohne explizite Nennung von {{hauptleistung}}!
- Maximal 25 Wörter

ELEMENT 2: DREI ENTSCHEIDUNGEN (Bullet-Liste) — HAUPTLEISTUNG IN JEDEM PUNKT!
- Genau 3 Bullets, nummeriert
- Jeder Bullet = 1 klare Entscheidung (nicht Analyse)
- PFLICHT: Mindestens 2 der 3 Bullets MÜSSEN {{hauptleistung}} explizit referenzieren!
- Format pro Bullet: "[Verb] + [Was für {{hauptleistung}}] + [Warum in 5-7 Wörtern]"

  STRUKTUR DER DREI ENTSCHEIDUNGEN:
  • ENTSCHEIDUNG 1 (PFLICHT mit {{hauptleistung}}): Wie wird {{hauptleistung}} durch KI effizienter?
  • ENTSCHEIDUNG 2 (PFLICHT mit {{hauptleistung}}): Welcher Prozess in {{hauptleistung}} wird automatisiert?
  • ENTSCHEIDUNG 3: Qualitätssicherung oder Governance-Aspekt

  KONKRETE BEISPIELE mit {{hauptleistung}}:
  • KI-Beratung: "1. Für {{hauptleistung}} Template-Bibliothek statt Custom-Code – wiederverwendbare Assessment-Module."
  • Steuerberatung: "1. Bei {{hauptleistung}} Dokumente vorab klassifizieren – eliminiert manuelle Sortierung."
  • Marketing-Agentur: "1. In {{hauptleistung}} Batch-Produktion einführen – skaliert Content ohne Qualitätsverlust."
  • IT-Dienstleistung: "1. {{hauptleistung}} durch automatisierte Ticket-Triage beschleunigen – Reaktionszeit halbieren."

  VERBOTEN:
  - "Minimal-Stack festlegen" (zu generisch!)
  - Entscheidungen ohne Bezug zu {{hauptleistung}}
  - Allgemeine KI-Aussagen ohne Geschäftsmodell-Kontext

ELEMENT 3: KONKRETER NÄCHSTER SCHRITT (1 Satz) — HAUPTLEISTUNG KONTEXT!
- Ein einziger Satz mit dem sofort umsetzbaren ersten Schritt
- PFLICHT: Der nächste Schritt MUSS sich auf {{hauptleistung}} beziehen!
- Format: "Konkreter nächster Schritt: [Was genau für {{hauptleistung}} tun] [in welchem Zeitrahmen]."
- BEISPIELE mit {{hauptleistung}}:
  • "Konkreter nächster Schritt: Für {{hauptleistung}} den zeitintensivsten Prozess identifizieren und mit einem Template standardisieren – diese Woche."
  • "Konkreter nächster Schritt: In {{hauptleistung}} einen wiederkehrenden Workflow mit KI-Unterstützung testen – erste Session heute."
  • "Konkreter nächster Schritt: {{hauptleistung}}-Workflow dokumentieren und Automatisierungspotenzial markieren – Freitag abgeschlossen."
- FALLS {{KI_GUARDRAILS}} vorhanden: Einschränkungen beachten (z.B. "ohne Kundendaten", "mit Review-Regel")

=============================================================================
STILREGELN v7.0 (STRIKT):
=============================================================================
- Durchschnittliche Satzlänge: maximal 18-22 Wörter
- Mehr Verben, weniger Nominalstil
- VERBOTEN: "fundamental", "exponentiell", "kritische Schwelle", "ganzheitlich"
- Jeder Absatz braucht eine Handlungsaussage: Entscheiden / Stoppen / Starten / Prüfen

HALTUNGSSATZ (PFLICHT) im Element 3:
Ein Nebensatz MUSS betonen: Entscheidungen bleiben bei Menschen, nicht bei Tools.

=============================================================================
TONALITÄT (STRIKT):
=============================================================================
- Ruhig, nicht drängend
- Entscheidungsorientiert, nicht verkaufend
- Strategisch nüchtern, nicht enthusiastisch
- Sachlich-souverän, nicht beratend

LESBARKEIT (v6.1 NEU):
- Maximal EIN abstrakter Gedanke pro Absatz
- 2–4 Sätze pro Absatz (nicht mehr)
- Keine Schachtelsätze – ein Hauptsatz, maximal ein Nebensatz
- Ton: analytisch, souverän, entscheidungsorientiert

=============================================================================
LEAK-PREVENTION — ABSOLUT VERBOTEN:
=============================================================================
NIEMALS VERWENDEN:
- Direkte Anrede: "Sie", "Ihr", "du", "wir"
- Hilfsangebote: "helfen", "unterstützen", "begleiten"
- Einladungen: "bei Bedarf", "falls gewünscht"
- CTA-Sprache: "kontaktieren", "anfragen"
- Service-Phrasen: "gerne", "selbstverständlich"
- Fragen an den Leser
- Beratungsformeln: "empfehlen wir", "sollten Sie"
- Tool-Namen oder Feature-Listen

STATTDESSEN:
- Dritte Person: "das Unternehmen", "die Organisation"
- Passive Konstruktionen: "lässt sich", "ergibt sich", "entsteht"
- Substantivierungen: "die Entscheidung", "die Ausrichtung"

=============================================================================
PERSONA-ANPASSUNG (COMPANY_SIZE):
=============================================================================
{% if COMPANY_SIZE == "solo" %}
SOLO: Fokus auf persönliche strategische Positionierung.
Die Entscheidung betrifft die Ausrichtung der eigenen Arbeit.
{% elif COMPANY_SIZE == "team" %}
TEAM: Fokus auf kollektive Arbeitsweise.
Die Entscheidung betrifft die Zusammenarbeit und gemeinsame Standards.
{% else %}
KMU: Fokus auf organisatorische Ausrichtung.
Die Entscheidung betrifft die strategische Positionierung im Markt.
{% endif %}

=============================================================================
ANTI-PATTERNS:
=============================================================================
- KEINE Aufzählung von Report-Inhalten ("In diesem Report finden Sie...")
- KEINE Score-Listings ("Der Governance-Score liegt bei...")
- KEINE Vorwegnahme von Roadmap oder Quick Wins
- KEINE generischen KI-Vorteile
- KEINE Buzzwords ("Transformation", "Disruption", "Next Level")
=============================================================================
-->

<section class="section executive-summary">
  <!-- KEINE h2 hier - Template stellt Überschrift bereit -->

  <p>
    <!--
    ELEMENT 1: PROFIL-SATZ (1 Satz, max. 25 Wörter)
    "[Branche] mit Fokus auf [Hauptleistung] steht vor [Kernherausforderung]."
    -->
  </p>

  <ol>
    <!--
    ELEMENT 2: DREI ENTSCHEIDUNGEN (nummerierte Liste)
    Genau 3 Bullets. Format: "[Verb] + [Was] + [Warum in 5-7 Wörtern]"
    Beispiel: "Standardisieren statt improvisieren – konsistente Qualität ohne Mehraufwand."
    -->
    <li><!-- Entscheidung 1: [Verb] + [Was] – [Warum] --></li>
    <li><!-- Entscheidung 2: [Verb] + [Was] – [Warum] --></li>
    <li><!-- Entscheidung 3: [Verb] + [Was] – [Warum] --></li>
  </ol>

  <p>
    <!--
    ELEMENT 3: KONKRETER NÄCHSTER SCHRITT (1 Satz)
    "Konkreter nächster Schritt: [Was] [Zeitrahmen]."
    PFLICHT: Nebensatz mit "Entscheidungen bleiben bei Menschen".
    -->
    <strong>Konkreter nächster Schritt:</strong>
    <!-- [Handlung in 30 Minuten umsetzbar] – Entscheidungen bleiben bei Menschen, nicht bei Tools. -->
  </p>

</section>

<!--
=============================================================================
ELEMENT 4: INDIVIDUELLER STARTPUNKT (PFLICHT) — Content Quality Pack v1.2
=============================================================================

Formuliere am Ende der Executive Summary **genau einen einzelnen Satz**, der mit
**„Wenn Sie nur eines tun:"** beginnt.

Dieser Satz muss:
- die **wichtigste Startmaßnahme** aus den priorisierten Empfehlungen aufgreifen,
- **konkret** sein (klarer Workflow oder klarer Prozessschritt),
- **branchen- und größenbezogen** formuliert sein,
- **risikobewusst** sein (z. B. ohne Kundendaten, mit Review-Regel, keine automatisierten Entscheidungen),
- **keine allgemeinen Aussagen** enthalten (z. B. „Starten Sie mit KI" ist unzulässig).

Der Satz darf **maximal 25–30 Wörter** lang sein.
Keine Bulletpoints. Kein zweiter Satz.

WICHTIG:
- Der Satz ist eine Verdichtung von Top-3-MUSS / Safe-Start / Roadmap Phase 0
- KEINE neue Empfehlung erfinden
- Kein Marketing-Wording

BEISPIELE (nur zur Orientierung – nicht kopieren):

Finance / Team:
„Wenn Sie nur eines tun: Starten Sie mit einer internen KI-Assistenz für Regelwerks- und Risikoanalysen ohne Kundendaten, mit fester Review-Regel für alle Ergebnisse."

Solo-Beratung:
„Wenn Sie nur eines tun: Standardisieren Sie einen wiederkehrenden Analyse- oder Reporting-Workflow mit KI-Unterstützung und klarer Freigabe, bevor Sie weitere Tools einsetzen."

=============================================================================
PHASE 2b: VERBESSERTE INDIVIDUALISIERUNG (STRIKT!) — HAUPTLEISTUNG = KERN!
=============================================================================

⚠️ KRITISCHE ANFORDERUNG: {{hauptleistung}} MUSS in diesem Abschnitt 2x erscheinen!

STRUKTUR MUSS SEIN (exakt 3 Komponenten, max 50 Wörter gesamt):

SATZ 1: Was macht der User? (max 15 Wörter) — HAUPTLEISTUNG PFLICHT!
→ NUTZE: {{hauptleistung}} WÖRTLICH (nicht paraphrasieren!)
→ FORMAT: "Ein [Branchentyp] mit {{hauptleistung}} [kurze Beschreibung]."
→ BEISPIELE:
  • "Ein Beratungsunternehmen mit {{hauptleistung}} erstellt KI-Readiness-Assessments für Mittelständler."
  • "Ein IT-Dienstleister mit {{hauptleistung}} betreut Geschäftskunden bei der Digitalisierung."
  • "Eine Marketing-Agentur mit {{hauptleistung}} produziert Content für B2B-Kunden."
→ VERBOTEN: Abstrakte Umschreibungen wie "bietet Dienstleistungen an"

SATZ 2: Was ist das Hauptproblem? (max 15 Wörter)
→ NUTZE: {{ZEITERSPARNIS_PRIORITAET}} EXPLIZIT
→ FORMAT: "Größter Zeitfresser in {{hauptleistung}}: [wörtlich aus {{ZEITERSPARNIS_PRIORITAET}}]."
→ BEISPIEL: "Größter Zeitfresser in {{hauptleistung}}: Umsetzung/Programmierung individueller Kundenprojekte."
→ VERBOTEN: "steht vor Herausforderungen" (zu vage!)

SATZ 3: Kernempfehlung (max 20 Wörter) — HAUPTLEISTUNG PFLICHT!
→ FORMAT: "Kernempfehlung für {{hauptleistung}} → [Strategischer Shift]: [3-5 konkrete Maßnahmen]."
→ BEISPIELE:
  • "Kernempfehlung für {{hauptleistung}} → Von Custom-Code zu Templates: Fragebogen-Bibliothek, Prompt-Standards, Review-Checkliste."
  • "Kernempfehlung für {{hauptleistung}} → Von Einzelprojekt zu Skalierung: Workflow-Automation, Qualitäts-Checks, Batch-Processing."
→ VERBOTEN: Theorie wie "skalierbare Prozesse etablieren"

VERBOTENE PHRASEN:
- "steht vor der Herausforderung"
- "Skalierbare Prozesse"
- "End-to-End-System"
- "Standardisierung der Abläufe"
- Jede Phrase die zu JEDEM User passt
- Sätze OHNE {{hauptleistung}}!

HTML-FORMAT für Element 4:
<p class="takeaway">
  <strong>Wenn Sie nur eines tun:</strong> [individueller Satz MIT {{hauptleistung}} hier]
</p>

=============================================================================
-->

<!--
=============================================================================
QUALITÄTS-SELBSTCHECK v7.2 VOR OUTPUT — HAUPTLEISTUNG VALIDIERUNG:
=============================================================================
□ Genau 1 Profil-Satz (max. 25 Wörter)?
□ {{hauptleistung}} im Profil-Satz WÖRTLICH enthalten? ⚠️ PFLICHT!
□ Genau 3 nummerierte Entscheidungen?
□ {{hauptleistung}} in mindestens 2 der 3 Entscheidungen? ⚠️ PFLICHT!
□ Genau 1 "Konkreter nächster Schritt" Satz?
□ {{hauptleistung}} im nächsten Schritt referenziert? ⚠️ PFLICHT!
□ Haltungssatz zu menschlicher Kontrolle vorhanden?
□ Genau 1 "Wenn Sie nur eines tun:" Satz (Element 4)?
□ {{hauptleistung}} im Takeaway-Satz? ⚠️ PFLICHT!
□ Durchschnittliche Satzlänge unter 22 Wörtern?
□ Keine Floskeln ("fundamental", "ganzheitlich", "exponentiell")?
□ NULL direkte Anreden (außer im Takeaway-Satz)?
□ In unter 60 Sekunden lesbar?

HAUPTLEISTUNG MINIMUM: 5x in der Executive Summary!
Falls weniger: Überarbeiten bis Minimum erreicht.
=============================================================================
-->
