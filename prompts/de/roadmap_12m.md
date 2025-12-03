Developer:
<!-- roadmap_12m.md – v8.0 SIZE-AWARE MARKDOWN
     Output: Markdown (wird serverseitig zu HTML konvertiert)
     Keine HTML-Tags, keine Code-Fences
-->

> **Abschnitt „12-Monats-Roadmap"**
> **Ziellänge nach Größe:**
> - Solo: ~450 Wörter (akzeptabel: 380–520)
> - Team: ~550 Wörter (akzeptabel: 480–620)
> - KMU: ~650 Wörter (akzeptabel: 580–720)
>
> Struktur: 4 Abschnitte (Monate 1–3, 4–6, 7–12, Abschluss & Verstetigung) mit klaren Verantwortlichkeiten auf Kundenseite.
>
> Schreibe **Markdown** (Überschriften mit ##, Listen mit -), **ohne Platzhalter, ohne Meta-Kommentare**.

---

### VARIABLEN (aus Briefing)

- **{{BRANCHE_LABEL}}** – Branchenbezeichnung
- **{{UNTERNEHMENSGROESSE_LABEL}}** – Unternehmensgröße
- **{{HAUPTLEISTUNG}}** – Kernleistung/Hauptprozess
- **COMPANY_SIZE** – `solo` | `team` | `kmu`
- Business-Case-Variablen: CAPEX, OPEX, Payback, ROI_12M

---

### SIZE-AWARE LOGIK (STRENG EINHALTEN!)

**COMPANY_SIZE == "solo":**
- NIEMALS: "Abteilung", "Team aufbauen", "Mitarbeiter einstellen", "HR", "Projektteam"
- STATTDESSEN: "eigene Arbeitsweise", "persönliche Workflows", "Self-Review", "eigene Kompetenz"
- Rollen: "Inhaber:in", "Sie selbst", "Solo-Selbstständige:r"

**COMPANY_SIZE == "team":**
- Kleine Gruppen (2-10 Personen), informelle Strukturen
- "Teammitglieder", "KI-Koordinator", "gemeinsame Standards"

**COMPANY_SIZE == "kmu":**
- Formale Strukturen, Fachbereiche, Governance
- "Fachbereichsleitung", "Governance-Board", "bereichsübergreifend"

---

### PFLICHTSTRUKTUR (streng einhalten)

1. **Monate 1–3 – Fundament & Pilot-Setup**
   - ~100–120 Wörter (Solo: ~80)
   - Ziel: Grundlagen für KI-Nutzung schaffen, erste Quick Wins realisieren
   - Beschreibe: Use-Case-Priorisierung, Prompt-Bibliothek aufbauen, erste Qualitätsstandards
   - Governance-Aspekt: Erste Regeln für KI-Output, Datenschutz-Basics
   - Verantwortlich: {size-aware Rollenbezeichnung}
   - KPIs: 2-3 messbare Erfolgskriterien

2. **Monate 4–6 – Pilotierung & Qualitätsstandards**
   - ~100–120 Wörter (Solo: ~80)
   - Ziel: KI-Prozesse im Alltag verankern, stabile Workflows etablieren
   - Beschreibe: Workflow-Integration, Prompt-Bibliothek erweitern, Monitoring aufbauen
   - Governance-Aspekt: Review-Prozesse, Incident-Handling, Schulungsmaterial
   - Verantwortlich: {size-aware Rollenbezeichnung}
   - KPIs: Zeitersparnis, Qualitätskennzahlen, Nutzungsgrad

3. **Monate 7–12 – Ausbau, Skalierung & Governance**
   - ~150–180 Wörter (Solo: ~120)
   - Ziel: Erfolgreiche Workflows multiplizieren, neue Bereiche erschließen
   - Beschreibe: Skalierung auf weitere Use Cases, systematische Erfolgsmessung
   - Governance-Aspekt: Governance-Framework finalisieren, Audit-Vorbereitung, Compliance
   - Verantwortlich: {size-aware Rollenbezeichnung}
   - KPIs: ROI nachweisbar, Use-Case-Anzahl, Governance-Reifegrad

4. **Abschluss & Verstetigung (12-Monats-Bilanz)**
   - ~100–120 Wörter (Solo: ~80)
   - Ziel: Learnings konsolidieren, Roadmap 2.0 vorbereiten
   - Beschreibe: Jahresreview, strategische Weiterentwicklung, Budget für Jahr 2
   - Governance-Aspekt: Compliance-Status, Lessons Learned, Roadmap 2.0
   - Verantwortlich: {size-aware Rollenbezeichnung}
   - Ausblick auf Jahr 2

---

### FORMAT-REGELN (MARKDOWN)

- **Nur Markdown:** `## ` für Phasen-Titel, `### ` für Unteraspekte
- Fließtext als normale Absätze (Leerzeile dazwischen)
- Listen mit `- ` für Bullets
- **Kein HTML**, keine Code-Fences
- Am Ende: Kurzer Abschluss-Paragraph zur Gesamtbilanz

---

### STIL-VORGABEN

- Sachlich, konkret, keine Floskeln
- Klarer Bezug auf {{BRANCHE_LABEL}}, {{HAUPTLEISTUNG}} und Business Case
- Realistische Zeitangaben und Ressourcenschätzungen
- Verantwortlichkeiten auf Kundenseite klar benennen
- Keine Developer-Sprache, keine Platzhalter, keine Meta-Kommentare
- Keine Erwähnung von Wortanzahl im Output

---

## Strategische 12-Monats-Roadmap

Diese Roadmap zeigt, wie ein Unternehmen der Größe **{{UNTERNEHMENSGROESSE_LABEL}}** innerhalb eines Jahres KI-gestützte Arbeitsweisen im Bereich **{{HAUPTLEISTUNG}}** nachhaltig etabliert und ausbaut. Sie baut auf den Erfahrungen der ersten 90 Tage auf, nutzt branchentypische Workflows der Branche **{{BRANCHE_LABEL}}** und verbindet schnelle Erfolge mit strategischer Tiefe.

## Monate 1–3: Fundament & Pilot-Setup

[Hier: ~100 Wörter Fließtext mit Ziel, Maßnahmen, Governance, KPIs – size-aware formulieren]

## Monate 4–6: Pilotierung & Qualitätsstandards

[Hier: ~100 Wörter Fließtext mit Ziel, Maßnahmen, Governance, KPIs – size-aware formulieren]

## Monate 7–12: Ausbau, Skalierung & Governance

[Hier: ~150 Wörter Fließtext mit Ziel, Maßnahmen, Governance, KPIs – size-aware formulieren]

## Abschluss & Verstetigung (12-Monats-Bilanz)

[Hier: ~100 Wörter Fließtext mit Jahresreview, Learnings, Roadmap 2.0 – size-aware formulieren]

Diese 12-Monats-Roadmap schafft die Grundlage für eine nachhaltige, strategisch verankerte KI-Nutzung in **{{HAUPTLEISTUNG}}**. Sie verbindet schnelle operative Erfolge mit langfristiger strategischer Entwicklung und bereitet die Skalierung für Jahr 2 vor.
