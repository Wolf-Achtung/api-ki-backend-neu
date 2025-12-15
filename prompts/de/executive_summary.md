Developer:
<!-- PLATIN+++ PROMPT v6.1 - SPRINT INHALTLICHE FINALISIERUNG -->
<!-- SECTION: executive_summary -->
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
<!-- INPUT: {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{HAUPTUMSATZTREIBER}}, {{STRATEGISCHE_ZIELE}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 1500 -->
<!-- WORD_MINIMUM: 250 -->
<!--
=============================================================================
EXECUTIVE SUMMARY v6.0 — STRATEGISCHE EINORDNUNG
=============================================================================

DIE EXECUTIVE SUMMARY IST:
- KEINE Inhaltsangabe des Reports
- KEINE technische Erklärung
- KEINE Auflistung von Scores oder Analysen

DIE EXECUTIVE SUMMARY IST:
Eine strategische Einordnung, die implizit beantwortet:
"Was ist hier die eigentliche Entscheidung – und warum jetzt?"

ZIELGRUPPE:
Eine entscheidungsverantwortliche Person, die nicht täglich operativ mit KI arbeitet.
Sachlich, strategisch, souverän. Keine Beratungssprache. Keine Tool-Euphorie.

=============================================================================
VERBINDLICHE STRUKTUR — GENAU 3 ABSÄTZE:
=============================================================================

ABSATZ 1: AUSGANGSLAGE (konzentriert)
- Wo steht das Unternehmen im Kontext KI?
- Welche strukturelle Herausforderung ist relevant für {{OFFERING_LABEL}}?
- KEINE Detailanalyse, KEIN Score-Listing
- 3-4 Sätze. Nüchtern. Faktisch.

ABSATZ 2: ZENTRALE STRATEGISCHE WEICHENSTELLUNG
- Bezug auf den Gamechanger (ohne ihn zu wiederholen)
- Was würde sich grundlegend ändern?
- Warum ist das keine Optimierung, sondern eine Richtungsentscheidung?
- 4-5 Sätze. Kernaussage des Reports.

ABSATZ 3: KONSEQUENZ & HALTUNG
- Was bedeutet das für Prioritäten, Tempo, Risiko?
- Betonung des Sicherheitsgeländers (Governance, Kontrolle, Verantwortung)
- Kein CTA, keine Empfehlung, keine Einladung
- 3-4 Sätze. Abschließend. Ruhig.

PFLICHT (v6.1) - HALTUNGSSATZ im 3. Absatz:
Ein Satz MUSS klar abgrenzen:
- Tool-Euphorie → Nein ("Es geht nicht um das nächste KI-Tool")
- Verantwortung → Ja ("Entscheidungen bleiben bei Menschen")
- Kontrolle → Ja ("Governance-Rahmen vor Geschwindigkeit")
Beispiel: "Die Transformation verändert Arbeitslogik, nicht die
Verantwortlichkeit – Entscheidungen bleiben dort, wo sie hingehören."

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
    ABSATZ 1: AUSGANGSLAGE
    Wo steht das Unternehmen im KI-Kontext?
    Welche strukturelle Herausforderung ist relevant?
    Bezug zu {{BRANCH_CONTEXT_LABEL}} und {{OFFERING_LABEL}}.
    3-4 Sätze. Faktisch. Keine Scores.
    -->
  </p>

  <p>
    <!--
    ABSATZ 2: STRATEGISCHE WEICHENSTELLUNG
    Was ist die zentrale Entscheidung?
    Bezug zum Gamechanger (implizit, nicht wiederholen).
    Warum Richtungsentscheidung, nicht Optimierung?
    4-5 Sätze. Das Herzstück.
    -->
  </p>

  <p>
    <!--
    ABSATZ 3: KONSEQUENZ & HALTUNG
    Was bedeutet das für Prioritäten und Tempo?
    Sicherheitsgeländer: Governance, Kontrolle, Verantwortung.
    PFLICHT: Ein Haltungssatz, der Tool-Euphorie abgrenzt und
    Verantwortung/Kontrolle betont (keine CTA, keine Ansprache).
    Kein CTA. Ruhiger Abschluss.
    3-4 Sätze.
    -->
  </p>

</section>

<!--
=============================================================================
QUALITÄTS-SELBSTCHECK VOR OUTPUT:
=============================================================================
□ Genau 3 Absätze?
□ Kein Score-Listing oder Report-Inhaltsverzeichnis?
□ Bezug zum Gamechanger ohne Wiederholung?
□ Sicherheitsgeländer (Governance) erwähnt?
□ NULL direkte Anreden?
□ KEINE Empfehlungen oder CTAs?
□ Liest sich wie strategische Einordnung, nicht wie Analyse?
=============================================================================
-->
