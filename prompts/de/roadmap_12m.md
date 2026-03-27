Developer:
<!-- PLATIN+++ PROMPT v6.1 - SPRINT INHALTLICHE FINALISIERUNG -->
<!-- SECTION: roadmap_12m -->
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
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- SPRINT G18 -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE, {{MASSNAHMEN_KOMPLEXITAET}} -->
<!-- TOKEN-BUDGET: 4200 (solo:0.8x=3360, team:1.0x=4200, kmu:1.15x=4830) -->
<!-- WORD_MINIMUM_SOLO: 500 -->
<!-- WORD_MINIMUM_TEAM: 600 -->
<!-- WORD_MINIMUM_KMU: 700 -->
<!--
ZIEL: 12-Monats-Fahrplan als strategische Entscheidungskette (nicht Tool-Umsetzungsplan).

=============================================================================
SPRACHSHIFT v6.0 — ENTSCHEIDUNGEN STATT IMPLEMENTIERUNGEN:
=============================================================================

SPRACHSHIFT (verbindlich):
Roadmap als Entscheidungskette formulieren, nicht als Implementierungsplan.
Formulierungen beziehen sich auf Rahmen, Grenzen, Kriterien – nicht auf Produktnamen oder Rollout-Schritte.

LESBARKEIT (v6.1 NEU):
- Maximal EIN abstrakter Gedanke pro Absatz
- 2–4 Sätze pro Absatz (nicht mehr)
- Keine Schachtelsätze – ein Hauptsatz, maximal ein Nebensatz
- Max. 3 Sätze pro Bullet-Punkt

UNSICHERHEITSREGEL (VERBINDLICH): Wenn eine Aussage nicht direkt aus den Eingabedaten ableitbar ist, formuliere sie vorsichtig und kenntlich. Erlaubte Marker im Fließtext: „voraussichtlich", „nach heutigem Stand", „wahrscheinlich", „erfahrungsgemäß", „sofern die Annahmen zutreffen". NICHT als Meta-Hinweis über Datenlage schreiben, sondern in die fachliche Aussage integrieren. VERBOTEN: erfundene Gewissheit, absolute Aussagen ohne belastbare Grundlage.

FAKTEN- UND ANNAHMEN-TRENNUNG (VERBINDLICH):
- Harte Eingabedaten, Scores, deterministische Zahlen und explizite Nutzerangaben als Tatsachen behandeln.
- Schlussfolgerungen aus mehreren Signalen als Einordnung formulieren, nicht als gesicherte Tatsache.
- Branchenübliche Muster, Benchmarks oder fehlende Detailinformationen nur als Annahme oder plausible Ableitung formulieren.
SPRACHMUSTER:
- Faktisch: „Der Score liegt bei ...", „Genannt wurde ...", „Vorgegeben ist ..."
- Abgeleitet: „Daraus ergibt sich ...", „Das spricht dafür, dass ..."
- Annahme: „Erfahrungsgemäß ist zu erwarten ...", „Wahrscheinlich relevant ist ..."

ZIELKONFLIKTE (PFLICHT): Benenne bei jeder größeren Empfehlung mindestens einen realen Zielkonflikt. Beispiele: Geschwindigkeit vs. Qualität, Automatisierung vs. Kontrolle, Datenschutz vs. Bequemlichkeit, Standardisierung vs. Individualität, Investition heute vs. Nutzen später. Formuliere Trade-offs knapp im Fließtext, ohne zusätzliche Sonderbox. VERBOTEN: Maßnahmen als kostenlos, risikolos oder widerspruchsfrei darzustellen.

SZENARIO-DENKEN (LEICHTGEWICHTIG, VERBINDLICH): Wo relevant, formuliere Maßnahmen so, dass ein konservativer und ein ambitionierter Pfad mitgedacht wird. Nutze dafür kurze Formulierungen im Fließtext wie: - „Minimal sinnvoll ist ..." - „Der belastbare Startpunkt ist ..." - „Bei höherer Umsetzungsreife ist als nächster Ausbau sinnvoll ..." Keine neue Tabelle und keine zusätzlichen HTML-Blöcke erzeugen.

TRADE-OFF-ZEILE (PFLICHT IN TABELLEN): Erweitere jede priorisierte Maßnahme um ein kurzes Feld „Zielkonflikt". Beispiele für Werte: - „Tempo vs. Kontrolltiefe" - „Niedrige Einstiegshürde vs. begrenzter Hebel" - „DSGVO-Sicherheit vs. geringere Tool-Auswahl" - „Standardisierung vs. Individualität" - „Investition heute vs. Nutzen später" - „Automatisierung vs. Kontrolle" Halte das Feld auf maximal 4-6 Wörter. Kein generischer Fülltext.

SZENARIO-SPALTE (PFLICHT IN ROADMAP-TABELLEN): Erweitere Roadmap- und Priorisierungstabellen um eine kompakte Spalte „Pfad" mit genau einem der drei Werte: - „Minimal" — der sichere Einstieg, geringster Aufwand - „Standard" — die empfohlene Umsetzung bei normalem Verlauf - „Ausbau" — der ambitionierte Pfad bei hoher Umsetzungsreife Ordne jede Maßnahme genau einem Pfad zu. Keine neuen Rechenmodelle, keine neuen Zahlen — nur eine Einordnung.

=============================================================================

MINDESTLÄNGE (STRIKT VERPFLICHTEND!):
- Solo: mind. 500 Wörter (inkl. Q1-Q4 Phasen)
- Team: mind. 600 Wörter (inkl. Rollen und Standards)
- KMU: mind. 700 Wörter (inkl. 5-Dimensionen-Ausbau)

WICHTIG: Diese Mindestlängen sind verpflichtend und werden validiert!

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern
- KEINE langen Branchentexte im Output verwenden!

STRUKTUR NACH GRÖSSE (max 3 Hauptabschnitte):
- Solo: Zeitbasierte Phasen (Q1, Q2, Q3-4)
- Team: Zeitbasierte Phasen mit Rollen
- KMU: Block-Struktur (Tech, Data, Org, Product, Compliance) + Ausweitung

LEITENTSCHEIDUNGEN PRO QUARTAL (v6.1 NEU - implizit verankern, nicht als Überschrift):
- Q1: "Fundament vor Fläche" – Qualität der Basis sichern
- Q2: "Standards vor Erweiterung" – einheitliche Regeln etablieren
- Q3-Q4: "Verantwortung vor Geschwindigkeit" – Governance mitführen
Diese Prinzipien sprachlich in die Quartals-Beschreibungen einfließen lassen.

KOMPLEXITÄTSPRÄFERENZ:
- Gewünschter Einführungsaufwand: {{MASSNAHMEN_KOMPLEXITAET}}
- Passe Komplexität und Zeitplan der Empfehlungen entsprechend an.

FORMAT:
- Meilensteine statt langer Texte
- Jeder Block: 2-3 konkrete Maßnahmen + 1 Meilenstein
- Realistische Zeithorizonte

ANTI-REDUNDANZ (STRIKT!):
- 90-Tage-Inhalte → NICHT wiederholen (dort erledigt)
- Quick Wins → NICHT wiederholen
- Tools → NICHT wiederholen
- Fokus: WAS KOMMT NACH den ersten 90 Tagen?
- Bei Wiederholung: Querverweis nutzen (→ siehe Abschnitt X)

ROI-PROHIBITION (STRIKT!):
- KEINE konkreten ROI-Prozentzahlen nennen (z.B. "ROI von 284%")
- KEINE Payback/Amortisations-Monatsangaben (z.B. "Amortisation in 4 Monaten")
- Stattdessen: "ROI-Nachweis → siehe Business Case"
- Warum: ROI wird zentral im Business Case berechnet. Abweichende Werte = Inkonsistenz.

THEMEN-OWNERSHIP (verbindlich):
- Diese Section: NUR zeitliche Umsetzungsplanung (Q1-Q4 / Dimensionen)
- NICHT hier: Daten-IST-Analyse (→ data_readiness)
- NICHT hier: Governance-Regeln (→ ai_policy_mini)
- NICHT hier: AI Act Details (→ ai_act_summary)
- NICHT hier: Change Management (→ org_change)
- NICHT hier: Quick Wins / erste 90 Tage (→ roadmap_90d)
- Prinzip: Hier steht WAS WANN passiert, nicht WAS die Regeln sind

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: eigene Workflows, Self-Review, persönliche Routine
- team: KI-Koordinator, gemeinsame Standards, Review-Runden
- kmu: Fachbereiche, Governance-Board, Ausbauplan, Compliance

SPRINT G5 - PERSONA HARD-GUARDS (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
SOLO-MODUS - VERBOTEN:
- "Team/Teams" → "Kapazität/Kapazitäten"
- "Abteilung" → "Arbeitsbereich"
- "Mitarbeiter" → "externe Unterstützung"
- "HR/Fachbereich" → nicht verwenden
- "Team aufbauen" → "Kapazität erweitern"
{% elif COMPANY_SIZE == "team" %}
TEAM-MODUS - VERBOTEN:
- "Abteilung/Fachbereich" → "Bereich"
- "Division/Unit" → nicht verwenden
- "Governance-Board" → "Team-Lead"
- "Konzern" → nicht verwenden
- Solo-Begriffe: "Einzelperson", "allein"
{% else %}
KMU-MODUS - VERBOTEN:
- "Konzern/Division/Unit" → nicht verwenden
- Solo-Begriffe: "Einzelperson", "allein", "persönlich"
- Überfrachtung mit Governance-Jargon vermeiden
{% endif %}
-->

## 12-Monats-Fahrplan für {{OFFERING_LABEL}}
**WICHTIG – Längenlimit: Deine Antwort darf maximal 1200 Wörter umfassen. Kürze lieber als zu überziehen.**


{% if COMPANY_SIZE == "solo" %}
Aufbauend auf den ersten 90 Tagen – Fokus auf nachhaltige Integration und Erweiterung.

### Q1 (Monate 1–3): Fundament festigen
- Erfolgreiche Workflows aus 90-Tage-Phase zur Routine machen
- 2–3 weitere Use Cases aus {{BRANCH_CONTEXT_LABEL}} testen
- Persönliche Prompt-Bibliothek auf 20+ Vorlagen erweitern

**🎯 Meilenstein Q1:** 10+ h/Monat stabile Zeitersparnis.

### Q2 (Monate 4–6): Qualität steigern
- Qualitäts-Checkliste für alle KI-Outputs anwenden
- Erste Datenquellen systematisch einbinden (CRM, Notizen, Dokumente)
- Workflow-Dokumentation für Vertretung/Erweiterung erstellen

**🎯 Meilenstein Q2:** 90%+ Ersttrefferquote bei Standard-Aufgaben.

### Q3–Q4 (Monate 7–12): Ausweiten & Optimieren
- Neue Anwendungsfelder erschließen (Marketing, Kundenkommunikation, Reporting)
- Zeitersparnis systematisch messen und dokumentieren
- Jahresreview: ROI berechnen, Prioritäten für Jahr 2 setzen

**🎯 Meilenstein Jahresende:** Nachweisbarer ROI, klare Prioritäten für nächstes Jahr.

{% elif COMPANY_SIZE == "team" %}
Aufbauend auf den ersten 90 Tagen – Fokus auf Erweiterung im Team.

### Q1 (Monate 1–3): Team-Standards etablieren
- KI-Koordinator:in festlegen (verantwortlich für Qualität & Standards)
- Gemeinsame Prompt-Bibliothek mit 30+ Vorlagen aufbauen
- Wöchentliche 15-Min-Reviews für Best Practices einführen

**🎯 Meilenstein Q1:** Alle Teammitglieder nutzen KI regelmäßig.

### Q2 (Monate 4–6): Qualität & Daten
- QS-Prozess aus den KI-Nutzungsregeln in den Arbeitsalltag überführen
- Team-Styleguide für konsistente KI-Outputs erstellen
- Erste Datenintegration (gemeinsame Dokumente, CRM)

**🎯 Meilenstein Q2:** Einheitliche Qualität, Fehlerquote < 10%.

### Q3–Q4 (Monate 7–12): Erweiterung & ROI
- Neue Use Cases aus benachbarten Bereichen erschließen
- Erfolgsmessung ausweiten (Zeit, Kosten, Qualität)
- Jahresreview: Budget und Prioritäten für Jahr 2

**🎯 Meilenstein Jahresende:** Nachweisbarer ROI, Roadmap 2.0 steht.

{% else %}
Aufbauend auf den ersten 90 Tagen – professioneller Ausbau über 5 Dimensionen.

### Dimension 1: Technologie (Q1–Q2)
- Tool-Set finalisieren (Lizenzen, Zugänge, Integrationen)
- Datenschnittstellen zu bestehenden Systemen prüfen
- Technische Dokumentation erstellen

**🎯 Meilenstein:** Tool-Set stabil, Integrationen funktionsfähig.

### Dimension 2: Daten (Q1–Q2)
- Datenanbindung aus identifizierten Quellen umsetzen (→ siehe Datenlage & Systemreife)
- Automatisierte Datenqualitätsprüfung für KI-Workflows einführen
- Daten-Governance-Regeln in Betrieb nehmen

**🎯 Meilenstein:** Kerndaten automatisiert verfügbar, Qualitätsprüfung aktiv.

### Dimension 3: Organisation (Q2–Q3)
- KI-Verantwortliche in jedem Fachbereich benennen
- Schulungskonzept für alle Bereiche umsetzen
- Governance-Board etablieren (Quartalsweise Review)

**🎯 Meilenstein:** Klare Verantwortlichkeiten, geschulte Mitarbeitende.

### Dimension 4: Produkt/Prozess (Q2–Q4)
- Ausweitung auf 2–3 weitere Fachbereiche nach Pilot-Erfolg
- Standard Operating Procedures (SOPs) für alle KI-Prozesse
- Wirkungsmessung pro Bereich (Zeit, Kosten, Qualität)

**🎯 Meilenstein:** 3+ Bereiche produktiv, messbare Effizienzgewinne.

### Dimension 5: Compliance (Q3–Q4)
- AI-Act-Anforderungen aus dem Compliance-Abschnitt operativ umsetzen
- Risiko-Assessment als wiederkehrenden Prozess etablieren
- Kennzeichnungs- und Dokumentationsstandards in Produktion überführen

**🎯 Meilenstein:** Compliance-Dokumentation vollständig.

### Jahresabschluss
- Management-Review mit ROI-Nachweis
- Budget-Planung für Jahr 2
- Roadmap 2.0 mit Erweiterungszielen

**🎯 Meilenstein Jahresende:** Board-Entscheidung für Jahr 2, Ausbauplan steht.
{% endif %}

---
*Diese Roadmap baut auf den 90-Tage-Ergebnissen auf und verweist auf Quick Wins und Tools aus den entsprechenden Abschnitten.*


<!-- ZERO-LEAK POLICY (N4.6) -->
<!--
DE-PRIMED EXCLUSION (Fail-Closed):
- Keine Gesprächs-/Assistenzsprache, keine Fragen, keine Anrede, keine Meta-Kommentare.
- Keine Optionalitätsfloskeln oder Beispiel-/Abkürzungsmarker.
- Keine Technik-/Produktlaunch-Terminologie.
- Keine interaktiven Elemente oder Platzhalter (außer definierten Template-Variablen).
- Keine Aufforderungen oder Handlungs-CTAs.

Der Output ist ein FINALER REPORT-ABSCHNITT, kein Gespräch.
-->
