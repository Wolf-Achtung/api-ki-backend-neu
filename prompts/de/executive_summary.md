Developer:
<!-- PLATIN++ PROMPT v8.0 — KIS-PROMPT P3 (Sanierung: 493→~140 Zeilen, widerspruchsfrei)
SECTION: executive_summary
OUTPUT: HTML ONLY
SIZE-AWARE: solo/team/kmu
TOKEN-BUDGET: 1500

Kompatibilitäts-Marker (Test-/Tool-Verträge, nicht entfernen):
SPRINT G18 - BRANCHENSÄTZE HARMONISIEREN | BRANCH_CORE_LABEL | BRANCH_SHORT_LABEL
INPUT: {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{HAUPTUMSATZTREIBER}}, COMPANY_SIZE

Hinweis für Entwickler: Zahlen-Disziplin, Terminologie-Kanon und
Anti-Assistenten-Sprache stehen im kanonischen System-Prompt
(services/report_system_prompt.py) und werden hier NICHT wiederholt.
-->

{% include '_report_grundregeln.md' %}

# AUFGABE

Schreibe die Executive Summary des KI-Status-Reports: eine knappe strategische
Einordnung, in unter 60 Sekunden lesbar. Sie beantwortet genau zwei Fragen:
**Was ist die Entscheidung — und was ist der erste Schritt?**

Zielleser: eine entscheidungsverantwortliche Person ohne KI-Vorwissen und mit
wenig Zeit. Verständlich, sachlich, handlungsorientiert — kein Berater-Jargon.

Die Executive Summary ist KEINE Inhaltsangabe des Reports, KEIN Score-Listing
und KEINE Aufzählung generischer KI-Vorteile.

# INDIVIDUALISIERUNGS-KONTEXT (verbindlich)

Diese Briefing-Daten sind die Grundlage jeder Aussage:

- Kerngeschäft (wichtigste Variable): {{hauptleistung}}
- Größter Zeitfresser: {{ZEITERSPARNIS_PRIORITAET}}
- Strategische Ziele: {{STRATEGISCHE_ZIELE}}
- Guardrails/No-Gos: {{KI_GUARDRAILS}}

Regeln:
- {{hauptleistung}} erscheint WÖRTLICH an genau vier Stellen: Profil-Satz,
  Entscheidung 1, Nächster Schritt, Takeaway-Satz. An allen anderen Stellen
  Synonyme verwenden („diese Leistung", „das Kerngeschäft") — mehr als fünf
  wörtliche Nennungen wirken mechanisch.
- Fehlt ein Input oder ist er unkonkret: nichts erfinden, die Aussage auf den
  belastbaren Kern reduzieren. Keine Meta-Sätze über die Datenlage.

# STRUKTUR (genau diese vier Elemente)

**Element 1 — Profil-Satz (1 Satz, max. 25 Wörter):**
Situation + So-what. Nicht nur „steht vor der Aufgabe", sondern was die
Ausgangslage für DIESES Unternehmen konkret bedeutet.
Muster: „[Branche] mit {{hauptleistung}} hat [Einordnung] — das bedeutet [Konsequenz]."

**Element 2 — Drei Entscheidungen (nummerierte Liste `<ol>`):**
Jeder Punkt ist eine Entscheidung (kein Analyse-Satz), Format
„[Verb] + [Was] — [Warum in 5–7 Wörtern]", 15–25 Wörter.
- Entscheidung 1: Wie wird {{hauptleistung}} durch KI effizienter? (wörtliche Nennung)
- Entscheidung 2: Welcher konkrete Prozess wird zuerst verändert? (Synonym)
- Entscheidung 3: Qualitätssicherung/Governance — mit einem Halbsatz zur
  realistischen Konsequenz bei Nicht-Handeln (keine Panikmache).

**Element 3 — Konkreter nächster Schritt (1 Satz, 20–30 Wörter):**
GENAU EIN Schritt, diese Woche machbar, bezogen auf {{hauptleistung}}.
Falls {{KI_GUARDRAILS}} vorhanden: Einschränkung einbauen (z. B. „ohne
Kundendaten", „mit Freigabe-Regel"). Pflicht-Nebensatz: Entscheidungen
bleiben bei Menschen, nicht bei Tools.

**Element 4 — Takeaway (1 Satz, max. 30 Wörter):**
Beginnt wörtlich mit „Wenn Sie nur eines tun:" — die wichtigste
Startmaßnahme, konkret (klarer Workflow oder Prozessschritt), branchen- und
größenbezogen, risikobewusst. Keine neue Empfehlung erfinden, sondern die
wichtigste aus den priorisierten Maßnahmen verdichten.

# LÄNGE UND ANREDE (eindeutig)

- Zielkorridor: 250–350 Wörter. Hartes Minimum 200, hartes Maximum 400.
- Fließtext in dritter Person („das Unternehmen", „die Organisation") oder
  mit unpersönlichen Konstruktionen. Direkte „Sie"-Anrede ist NUR im
  Takeaway-Satz (Element 4) erlaubt — dort ist sie Pflicht.
- Satzlänge im Schnitt unter 22 Wörtern, ein Hauptsatz + maximal ein
  Nebensatz, ein Gedanke pro Absatz.
- Keine Floskeln („fundamental", „ganzheitlich", „exponentiell",
  „Transformation", „Disruption"), keine Tool-Namen, keine CTAs.

# FINANZZAHLEN (Owner-Prinzip)

Diese Sektion nennt KEINE konkreten Finanzwerte: kein ROI-Prozentsatz, keine
Investitionssummen, keine Payback-Monate, keine Fördersummen. Diese Zahlen
haben Owner-Sektionen (Business Case, Förderpotenzial) — qualitativer Verweis
ist erlaubt („Details im Business Case"). Der KI-Readiness-Score darf genannt
werden (kommt als Variable).

# PERSONA (COMPANY_SIZE)

{% if COMPANY_SIZE == "solo" %}
SOLO: Fokus auf die persönliche strategische Positionierung — die Entscheidung
betrifft die Ausrichtung der eigenen Arbeit.
{% elif COMPANY_SIZE == "team" %}
TEAM: Fokus auf die kollektive Arbeitsweise — die Entscheidung betrifft
Zusammenarbeit und gemeinsame Standards.
{% else %}
KMU: Fokus auf die organisatorische Ausrichtung — die Entscheidung betrifft
die strategische Positionierung im Markt.
{% endif %}

# OUTPUT-FORMAT

Erlaubte Tags: `<section>`, `<p>`, `<ol>`, `<li>`, `<strong>`, `<em>`.
Keine Überschriften-Tags (setzt das Template).

```
<section class="section executive-summary">
  <p>[Element 1: Profil-Satz]</p>
  <ol>
    <li>[Entscheidung 1]</li>
    <li>[Entscheidung 2]</li>
    <li>[Entscheidung 3]</li>
  </ol>
  <p><strong>Konkreter nächster Schritt:</strong> [Element 3]</p>
  <p class="takeaway"><strong>Wenn Sie nur eines tun:</strong> [Element 4]</p>
</section>
```

# BEISPIEL (Niveau-Anker — Solo-Beratung, nicht kopieren)

<section class="section executive-summary">
  <p>Eine Solo-Beratung mit KI-Assessments für Mittelständler verliert die meiste Zeit an manuelle Fragebogen-Auswertung — das begrenzt derzeit die Zahl parallel betreubarer Kunden.</p>
  <ol>
    <li>KI-Assessments auf eine Template-Bibliothek umstellen — wiederverwendbare Bausteine statt Einzelanfertigung senken die Vorbereitungszeit pro Mandat.</li>
    <li>Die Auswertung als geführten KI-Workflow standardisieren — gleiche Qualität bei wachsender Kundenzahl.</li>
    <li>Freigabe-Regel vor Ausbau festlegen: jede KI-Ausgabe wird geprüft, bevor sie den Kunden erreicht — sonst wächst mit dem Volumen auch das Fehlerrisiko.</li>
  </ol>
  <p><strong>Konkreter nächster Schritt:</strong> Den zeitintensivsten Auswertungsschritt der KI-Assessments dokumentieren und mit einem Template standardisieren — diese Woche; die fachliche Entscheidung bleibt dabei beim Menschen, nicht beim Tool.</p>
  <p class="takeaway"><strong>Wenn Sie nur eines tun:</strong> Standardisieren Sie einen wiederkehrenden Auswertungs-Workflow Ihrer KI-Assessments mit klarer Freigabe-Regel und ohne Kundendaten in externen Tools.</p>
</section>
