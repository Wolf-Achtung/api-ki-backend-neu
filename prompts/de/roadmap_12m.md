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
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 4200 (solo:0.8x=3360, team:1.0x=4200, kmu:1.15x=4830) -->
<!-- WORD_MINIMUM_SOLO: 500 -->
<!-- WORD_MINIMUM_TEAM: 600 -->
<!-- WORD_MINIMUM_KMU: 700 -->
<!--
ZIEL: 12-Monats-Roadmap als strategische Entscheidungskette (nicht Tool-Rollout).

=============================================================================
SPRACHSHIFT v6.0 — ENTSCHEIDUNGEN STATT IMPLEMENTIERUNGEN:
=============================================================================

VERBOTENE FORMULIERUNGEN → ERSETZUNGEN:
❌ "Einführung / Implementierung"  → ✅ "Festlegung / Definition / Abgrenzung"
❌ "Tool ausrollen"                → ✅ "Standards etablieren"
❌ "System integrieren"            → ✅ "Verantwortlichkeiten klären"
❌ "Workflow automatisieren"       → ✅ "Entscheidungsrahmen schaffen"
❌ "Digitalisierung vorantreiben"  → ✅ "Prioritäten setzen"

Die Roadmap zeigt WELCHE ENTSCHEIDUNGEN zu treffen sind,
nicht WELCHE TOOLS einzuführen sind.

LESBARKEIT (v6.1 NEU):
- Maximal EIN abstrakter Gedanke pro Absatz
- 2–4 Sätze pro Absatz (nicht mehr)
- Keine Schachtelsätze – ein Hauptsatz, maximal ein Nebensatz
- Max. 3 Sätze pro Bullet-Punkt

=============================================================================

MINDESTLÄNGE (STRIKT VERPFLICHTEND!):
- Solo: mind. 500 Wörter (inkl. Q1-Q4 Phasen)
- Team: mind. 600 Wörter (inkl. Rollen und Standards)
- KMU: mind. 700 Wörter (inkl. 5-Dimensionen-Rollout)

WICHTIG: Diese Mindestlängen sind verpflichtend und werden validiert!

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern
- KEINE langen Branchentexte im Output verwenden!

STRUKTUR NACH GRÖSSE (max 3 Hauptabschnitte):
- Solo: Zeitbasierte Phasen (Q1, Q2, Q3-4)
- Team: Zeitbasierte Phasen mit Rollen
- KMU: Block-Struktur (Tech, Data, Org, Product, Compliance) + Rollout

LEITENTSCHEIDUNGEN PRO QUARTAL (v6.1 NEU - implizit verankern, nicht als Überschrift):
- Q1: "Fundament vor Fläche" – Qualität der Basis sichern
- Q2: "Standards vor Skalierung" – einheitliche Regeln etablieren
- Q3-Q4: "Verantwortung vor Geschwindigkeit" – Governance mitführen
Diese Prinzipien sprachlich in die Quartals-Beschreibungen einfließen lassen.

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

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: eigene Workflows, Self-Review, persönliche Routine
- team: KI-Koordinator, gemeinsame Standards, Review-Runden
- kmu: Fachbereiche, Governance-Board, Rollout-Plan, Compliance

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

## 12-Monats-Roadmap für {{OFFERING_LABEL}}

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
- Workflow-Dokumentation für Vertretung/Skalierung erstellen

**🎯 Meilenstein Q2:** 90%+ Ersttrefferquote bei Standard-Aufgaben.

### Q3–Q4 (Monate 7–12): Ausweiten & Optimieren
- Neue Anwendungsfelder erschließen (Marketing, Kundenkommunikation, Reporting)
- Zeitersparnis systematisch messen und dokumentieren
- Jahresreview: ROI berechnen, Prioritäten für Jahr 2 setzen

**🎯 Meilenstein Jahresende:** Nachweisbarer ROI, klare Prioritäten für nächstes Jahr.

{% elif COMPANY_SIZE == "team" %}
Aufbauend auf den ersten 90 Tagen – Fokus auf Skalierung im Team.

### Q1 (Monate 1–3): Team-Standards etablieren
- KI-Koordinator:in festlegen (verantwortlich für Qualität & Standards)
- Gemeinsame Prompt-Bibliothek mit 30+ Vorlagen aufbauen
- Wöchentliche 15-Min-Reviews für Best Practices einführen

**🎯 Meilenstein Q1:** Alle Teammitglieder nutzen KI regelmäßig.

### Q2 (Monate 4–6): Qualität & Daten
- QS-Prozess formalisieren: Input → KI → Review → Freigabe
- Team-Styleguide für KI-Outputs erstellen
- Erste Datenintegration (gemeinsame Dokumente, CRM)

**🎯 Meilenstein Q2:** Einheitliche Qualität, Fehlerquote < 10%.

### Q3–Q4 (Monate 7–12): Skalierung & ROI
- Neue Use Cases aus benachbarten Bereichen erschließen
- Erfolgsmessung ausweiten (Zeit, Kosten, Qualität)
- Jahresreview: Budget und Prioritäten für Jahr 2

**🎯 Meilenstein Jahresende:** Nachweisbarer ROI, Roadmap 2.0 steht.

{% else %}
Aufbauend auf den ersten 90 Tagen – professioneller Rollout über 5 Dimensionen.

### Dimension 1: Technologie (Q1–Q2)
- Tool-Stack finalisieren (Lizenzen, Zugänge, Integrationen)
- Datenschnittstellen zu bestehenden Systemen prüfen
- Technische Dokumentation erstellen

**🎯 Meilenstein:** Tech-Stack stabil, Integrationen funktionsfähig.

### Dimension 2: Daten (Q1–Q2)
- Relevante Datenquellen identifizieren und anbinden
- Datenqualität für KI-Nutzung sicherstellen
- Zugriffsrechte und Datenschutz klären

**🎯 Meilenstein:** Kerndaten für KI verfügbar und regelkonform nutzbar.

### Dimension 3: Organisation (Q2–Q3)
- KI-Verantwortliche in jedem Fachbereich benennen
- Schulungskonzept ausrollen
- Governance-Board etablieren (Quartalsweise Review)

**🎯 Meilenstein:** Klare Verantwortlichkeiten, geschulte Mitarbeitende.

### Dimension 4: Produkt/Prozess (Q2–Q4)
- Rollout auf 2–3 weitere Fachbereiche nach Pilot-Erfolg
- Standard Operating Procedures (SOPs) für alle KI-Prozesse
- Wirkungsmessung pro Bereich (Zeit, Kosten, Qualität)

**🎯 Meilenstein:** 3+ Bereiche produktiv, messbare Effizienzgewinne.

### Dimension 5: Compliance (Q3–Q4)
- AI-Act-Relevanz prüfen und dokumentieren
- Risiko-Assessment für KI-Anwendungen durchführen
- Transparenzpflichten umsetzen (wo KI im Einsatz)

**🎯 Meilenstein:** Compliance-Dokumentation vollständig.

### Jahresabschluss
- Management-Review mit ROI-Nachweis
- Budget-Planung für Jahr 2
- Roadmap 2.0 mit Skalierungszielen

**🎯 Meilenstein Jahresende:** Board-Entscheidung für Jahr 2, Rollout-Plan steht.
{% endif %}

---
*Diese Roadmap baut auf den 90-Tage-Ergebnissen auf und verweist auf Quick Wins und Tools aus den entsprechenden Abschnitten.*


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
