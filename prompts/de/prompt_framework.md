# Prompt-Framework – 5 Schritte zum perfekten Prompt

<!-- persona:solo -->
<!-- Solo: Schnell anwendbar, 1 Beispiel reicht, keine Theorie -->
<!-- persona:team -->
<!-- Team: Gemeinsame Prompt-Bibliothek aufbauen, Best Practices teilen -->
<!-- persona:kmu -->
<!-- KMU: Standardisierte Prompts für wiederkehrende Aufgaben, Qualitätssicherung -->

## Das 5-Schritte-Framework

Jeder gute Prompt enthält diese fünf Elemente:

### 1. Kontext
*Hintergrundinformationen für die KI*

> „Du arbeitest für ein mittelständisches Beratungsunternehmen im DACH-Raum."

### 2. Rolle
*Welche Expertise soll die KI annehmen?*

> „Agiere als erfahrener Unternehmensberater mit Fokus auf Prozessoptimierung."

### 3. Ziel
*Was soll erreicht werden?*

> „Erstelle eine Zusammenfassung der wichtigsten Erkenntnisse aus dem Meeting-Protokoll."

### 4. Constraints
*Einschränkungen und Qualitätskriterien*

> „Maximal 5 Bullet Points. Keine Fachbegriffe ohne Erklärung. Fokus auf umsetzbare Maßnahmen."

### 5. Format
*Wie soll das Ergebnis aussehen?*

> „Ausgabe als nummerierte Liste mit Prioritätsangabe (hoch/mittel/niedrig)."

---

## Beispiel-Prompt (komplett)

```
Kontext: Du unterstützt ein 20-köpfiges Team bei der Einführung von KI-Tools.

Rolle: Du bist ein KI-Trainer mit Erfahrung in Change Management.

Ziel: Erstelle einen Schulungsplan für die ersten 4 Wochen.

Constraints:
- Max. 2 Stunden Schulung pro Woche
- Fokus auf praktische Übungen
- Keine Vorkenntnisse voraussetzen

Format: Tabelle mit Woche, Thema, Dauer, Lernziel
```

---

## Tipps für bessere Prompts

| Problem | Lösung |
|---------|--------|
| Ergebnis zu vage | Mehr Kontext + konkretere Constraints |
| Ergebnis zu lang | Format-Vorgabe (z.B. „max. 200 Wörter") |
| Falscher Tonfall | Rolle definieren (z.B. „formell", „locker") |
| Unpassende Beispiele | Branche/Kontext explizit nennen |

---

## Variablen nutzen

Für wiederkehrende Prompts: Platzhalter einbauen.

```
Erstelle einen [DOKUMENTTYP] für [ZIELGRUPPE]
zum Thema [THEMA].
Länge: [LÄNGE]. Tonalität: [TONALITÄT].
```

---
*Tipp: Prompts iterativ verbessern. Erste Version → Ergebnis prüfen → Prompt anpassen.*
