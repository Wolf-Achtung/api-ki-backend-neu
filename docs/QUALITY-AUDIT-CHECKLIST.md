# Quality Audit Checklist — KI-Sicherheit.jetzt Report-Validierung

**Zweck:** Diese Checkliste wird bei JEDEM Testrun durchlaufen — zusätzlich zur Fix-Validierung. Sie prüft das gesamte PDF aus Kundenperspektive.

**Regel:** Jedes Problem wird mit Seite, Schwere (HIGH/MEDIUM/LOW), Kategorie und vermuteter Ursache dokumentiert.

---

## 1. Layout & Visuelles

### 1.1 Seitenumbrüche
- [ ] Jedes Hauptkapitel startet auf einer neuen Seite
- [ ] Keine Überschrift allein am Seitenende ohne Folgetext
- [ ] Cards/Boxen werden nicht durch Seitenumbrüche getrennt
- [ ] Tabellen bleiben auf einer Seite (oder umbrechen sauber an Zeilen)
- [ ] Transitions bleiben am Ende ihrer Section

### 1.2 Weißraum
- [ ] Keine Seite ist zu >40% leer (Weißraum-Wüste)
- [ ] Kein unnötiger Leerraum zwischen Elementen
- [ ] Seitenzahl ist ≤ 30 (Tradeoff Page Breaks vs. Kompaktheit)

### 1.3 Typografie & Konsistenz
- [ ] Überschriften-Hierarchie konsistent (h1→h2→h3)
- [ ] Schriftgrößen einheitlich innerhalb gleicher Ebenen
- [ ] Farbige Boxen haben konsistente Ränder und Padding
- [ ] Alle Tabellen vollständig sichtbar (keine abgeschnittenen Spalten)

### 1.4 Footer/Header
- [ ] "Seite X / Y" auf jeder Seite korrekt
- [ ] Report-ID und Datum konsistent
- [ ] Seitenzählung nach Page Breaks korrekt

---

## 2. Inhaltliche Konsistenz

### 2.1 Score-Konsistenz
- [ ] Gesamtscore (92/100) überall identisch
- [ ] Dimensions-Scores (Gov 88, Sich 85, Wert 94, Bef 93) überall gleich
- [ ] Score-Interpretation stimmt mit Cover überein
- [ ] Advisor Note stimmt mit Cover überein
- [ ] Reifegrad-Label ("Leader", "exzellent") konsistent

### 2.2 ROI-Konsistenz
- [ ] ROI-Wert überall als "200%" oder "200% (gedeckelt)"
- [ ] Amortisation überall identisch (1,6 Monate)
- [ ] Investitionszahlen widerspruchsfrei
- [ ] Zeitersparnis überall 36h/Monat (= 9h/Woche × 4)

### 2.3 Branchenstring
- [ ] "Beratung und Unterstützung für Unternehmen" ≤ 5x im gesamten PDF
- [ ] Keine Stellen wo der String grammatikalisch nicht passt
- [ ] Keine robotisch wirkenden Wiederholungen im Fließtext

---

## 3. Textqualität

### 3.1 Filler & Generisches
- [ ] Keine Absätze die für jede Branche passen würden (austauschbar)
- [ ] Konkrete Bezüge zur Branche/Unternehmensgröße vorhanden
- [ ] Empfehlungen sind spezifisch, nicht generisch

### 3.2 Wiederholungen
- [ ] Keine identischen Empfehlungen in verschiedenen Kapiteln
- [ ] Keine Copy-Paste-artigen Textblöcke
- [ ] Querverweise statt Wiederholung ("siehe Business Case")

### 3.3 Tonalität
- [ ] Durchgehend "Sie"-Anrede
- [ ] Professionell aber nicht steif
- [ ] Nicht zu werblich, nicht zu trocken
- [ ] Advisor Note hat authentischen Wolf-Hohl-Ton

### 3.4 Prompt-Leaks
- [ ] Keine sichtbaren Variablen-Namen (z.B. `{{score_gesamt}}`)
- [ ] Keine System-Instruktionen im Text
- [ ] Keine Platzhalter die nicht aufgelöst wurden
- [ ] Kein `Developer:` oder ähnliche Prompt-Marker

---

## 4. Technische Artefakte

### 4.1 Rendering
- [ ] Keine HTML-Tags als sichtbarer Text (`<strong>`, `<br>`, `&amp;`)
- [ ] Keine Encoding-Probleme (Umlaute korrekt)
- [ ] Keine broken-image-Icons

### 4.2 Logos
- [ ] Status dokumentieren (aktuell: nicht deployed, erwartet: 0 loaded)
- [ ] Falls Platzhalter-Bilder sichtbar → notieren

### 4.3 Links
- [ ] TOC-Links klickbar
- [ ] "Feedback geben" / "Web-Version" Links funktional

### 4.4 Pipeline
- [ ] Pipeline Grade = A
- [ ] Consistency Grade = A
- [ ] 0 Fallbacks
- [ ] 0 Heals
- [ ] HARD-BLOCK Eingriffe = 0 (für score_interpretation und advisor_note)

---

## 5. Issue-Tracking

Bei jedem Testrun diese Tabelle fortführen:

| Issue | TR2 | TR3 | TR4 | TR5 | TR6 | Trend |
|---|---|---|---|---|---|---|
| ROI Cappings | 20 | 18 | 14 | | | |
| Logos loaded | 0 | 0 | 0 | | | |
| Branchenstring Vorkommen | 10+ | ~10 | 5 | | | |
| HARD-BLOCK Eingriffe | 4 | 4 | 1 | | | |
| Seitenzahl | 23 | 22 | 22 | | | |
| Weißraum-Seiten (>40% leer) | ? | ? | ? | | | |
| Prompt-Leaks | ? | ? | 1 | | | |

---

## 6. Findings-Template

Für jedes gefundene Problem:

```
Finding F-XX
* Seite: X
* Schwere: HIGH / MEDIUM / LOW
* Kategorie: Layout / Inhalt / Technik / Konsistenz
* Beschreibung: Was ist das Problem?
* Vermutete Ursache: Template / CSS / Prompt / Pipeline
* Fix-Aufwand: Quick Fix (1h) / Mittlerer Fix (halber Tag) / Größerer Umbau
* Screenshot/Zitat: [falls vorhanden]
```

---

## Nutzung

1. Bei jedem Testrun: Checkliste Punkt für Punkt durchgehen
2. Findings im Validierungs-Report dokumentieren
3. Issue-Tracking-Tabelle aktualisieren
4. Neue HIGH-Findings → sofort ins nächste Claude-Code-Briefing
5. MEDIUM/LOW-Findings → sammeln für nächsten Batch-Fix
