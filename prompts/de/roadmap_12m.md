Developer:
<!-- roadmap_12m.md – v7.0 PLATIN+ STABILIZED
     Antworte ausschließlich mit validem HTML. Keine Markdown-Fences.
-->

> **PLATIN+ – Abschnitt „12-Monats-Roadmap"**
> Mindestlänge: **mindestens 900 Wörter**
> Struktur: 4 Abschnitte (Monate 1–3, 4–6, 7–12, Abschluss & Verstetigung) mit klaren Verantwortlichkeiten auf Kundenseite.
>
> Schreibe direkt PDF-fertigen Fließtext (nur HTML-Paragraphen und Zwischenüberschriften), **ohne Platzhalter, ohne Meta-Kommentare, ohne Hinweise auf Wortanzahl oder „dieser Abschnitt…"**.

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
   - Mindestens 200 Wörter Fließtext
   - Ziel: Grundlagen für KI-Nutzung schaffen, erste Quick Wins realisieren
   - Beschreibe: Use-Case-Priorisierung, Prompt-Bibliothek aufbauen, erste Qualitätsstandards
   - Governance-Aspekt: Erste Regeln für KI-Output, Datenschutz-Basics
   - Verantwortlich: {size-aware Rollenbezeichnung}
   - KPIs: 2-3 messbare Erfolgskriterien

2. **Monate 4–6 – Pilotierung & Qualitätsstandards**
   - Mindestens 200 Wörter Fließtext
   - Ziel: KI-Prozesse im Alltag verankern, stabile Workflows etablieren
   - Beschreibe: Workflow-Integration, Prompt-Bibliothek erweitern, Monitoring aufbauen
   - Governance-Aspekt: Review-Prozesse, Incident-Handling, Schulungsmaterial
   - Verantwortlich: {size-aware Rollenbezeichnung}
   - KPIs: Zeitersparnis, Qualitätskennzahlen, Nutzungsgrad

3. **Monate 7–12 – Ausbau, Skalierung & Governance**
   - Mindestens 250 Wörter Fließtext
   - Ziel: Erfolgreiche Workflows multiplizieren, neue Bereiche erschließen
   - Beschreibe: Skalierung auf weitere Use Cases, systematische Erfolgsmessung
   - Governance-Aspekt: Governance-Framework finalisieren, Audit-Vorbereitung, Compliance
   - Verantwortlich: {size-aware Rollenbezeichnung}
   - KPIs: ROI nachweisbar, Use-Case-Anzahl, Governance-Reifegrad

4. **Abschluss & Verstetigung (12-Monats-Bilanz)**
   - Mindestens 200 Wörter Fließtext
   - Ziel: Learnings konsolidieren, Roadmap 2.0 vorbereiten
   - Beschreibe: Jahresreview, strategische Weiterentwicklung, Budget für Jahr 2
   - Governance-Aspekt: Compliance-Status, Lessons Learned, Roadmap 2.0
   - Verantwortlich: {size-aware Rollenbezeichnung}
   - Ausblick auf Jahr 2

---

### FORMAT-REGELN

- **Nur HTML:** `<h3>`, `<h4>`, `<p>` – keine Listen, keine Bullets
- Jeder Abschnitt beginnt mit `<h3>` für die Phase
- Unteraspekte mit `<h4>` strukturieren
- Fließtext in `<p>`-Tags
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

<section class="section roadmap-12m">
  <h2>Strategische 12-Monats-Roadmap</h2>

  <p>
    Diese Roadmap zeigt, wie ein Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    innerhalb eines Jahres KI-gestützte Arbeitsweisen im Bereich
    <strong>{{HAUPTLEISTUNG}}</strong> nachhaltig etabliert und ausbaut. Sie baut auf den
    Erfahrungen der ersten 90 Tage auf, nutzt branchentypische Workflows der Branche
    <strong>{{BRANCHE_LABEL}}</strong> und verbindet schnelle Erfolge mit strategischer Tiefe.
  </p>

  <!-- Phase 1: Monate 1-3 -->
  <h3>Monate 1–3: Fundament & Pilot-Setup</h3>
  <!-- Mindestens 200 Wörter Fließtext mit Ziel, Maßnahmen, Governance, KPIs -->

  <!-- Phase 2: Monate 4-6 -->
  <h3>Monate 4–6: Pilotierung & Qualitätsstandards</h3>
  <!-- Mindestens 200 Wörter Fließtext mit Ziel, Maßnahmen, Governance, KPIs -->

  <!-- Phase 3: Monate 7-12 -->
  <h3>Monate 7–12: Ausbau, Skalierung & Governance</h3>
  <!-- Mindestens 250 Wörter Fließtext mit Ziel, Maßnahmen, Governance, KPIs -->

  <!-- Phase 4: Abschluss -->
  <h3>Abschluss & Verstetigung (12-Monats-Bilanz)</h3>
  <!-- Mindestens 200 Wörter Fließtext mit Jahresreview, Learnings, Roadmap 2.0 -->

  <p class="small muted">
    Diese 12-Monats-Roadmap schafft die Grundlage für eine nachhaltige, strategisch verankerte
    KI-Nutzung in <strong>{{HAUPTLEISTUNG}}</strong>. Sie verbindet schnelle operative Erfolge
    mit langfristiger strategischer Entwicklung und bereitet die Skalierung für Jahr 2 vor.
  </p>
</section>

<!-- PLATIN+ REINFORCEMENT: Dieser Abschnitt MUSS mindestens 900 Wörter enthalten.
     Prüfe deine Ausgabe: Zähle die Wörter und erweitere jede Phase mit zusätzlichen
     Details zu Zielen, Maßnahmen, Governance und KPIs, falls die Mindestlänge nicht erreicht wird.
     Kürze NIEMALS – liefere immer vollständige, ausführliche Inhalte pro Phase. -->
