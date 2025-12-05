Developer:
<!-- PLATIN++ PROMPT v5.3 - SPRINT N -->
<!-- SECTION: roadmap_12m -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 4200 (solo:0.8x=3360, team:1.0x=4200, kmu:1.15x=4830) -->
<!-- WORD_MINIMUM_SOLO: 500 -->
<!-- WORD_MINIMUM_TEAM: 600 -->
<!-- WORD_MINIMUM_KMU: 700 -->
<!--
ZIEL: 12-Monats-Roadmap mit Meilensteinen, aufbauend auf 90-Tage-Ergebnissen.
MINDESTLÄNGE: solo≥500, team≥600, kmu≥700 Wörter (STRIKT EINHALTEN!)

STRUKTUR NACH GRÖSSE:
- Solo: Zeitbasierte Phasen (Q1, Q2, Q3-4)
- Team: Zeitbasierte Phasen mit Rollen
- KMU: Block-Struktur (Tech, Data, Org, Product, Compliance) + Rollout

FORMAT:
- Meilensteine statt langer Texte
- Jeder Block: 2-3 konkrete Maßnahmen + 1 Meilenstein
- Realistische Zeithorizonte

ANTI-REDUNDANZ (STRIKT!):
- 90-Tage-Inhalte → NICHT wiederholen (dort erledigt)
- Quick Wins → NICHT wiederholen
- Tools → NICHT wiederholen
- Fokus: WAS KOMMT NACH den ersten 90 Tagen?

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: eigene Workflows, Self-Review, persönliche Routine
- team: KI-Koordinator, gemeinsame Standards, Review-Runden
- kmu: Fachbereiche, Governance-Board, Rollout-Plan, Compliance

SPRINT N - SOLO PERSONA REGELN (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
NICHT VERWENDEN für Solo:
- "Team" → stattdessen: "Kapazität" oder "Ressourcen"
- "Abteilung" → stattdessen: "Arbeitsbereich"
- "Mitarbeiter" → stattdessen: "externe Unterstützung"
- "HR" → nicht verwenden
- "Fachbereich" → stattdessen: "Arbeitsfeld"
- "Team aufbauen" → stattdessen: "Kapazität erweitern"
- "Teams" → stattdessen: "Kapazitäten"
Formulierungen ohne Team-/Abteilungsbegriff verwenden!
{% endif %}
-->

## 12-Monats-Roadmap für {{HAUPTLEISTUNG}}

{% if COMPANY_SIZE == "solo" %}
Aufbauend auf den ersten 90 Tagen – Fokus auf nachhaltige Integration und Erweiterung.

### Q1 (Monate 1–3): Fundament festigen
- Erfolgreiche Workflows aus 90-Tage-Phase zur Routine machen
- 2–3 weitere Use Cases aus {{BRANCHE_LABEL}} testen
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
