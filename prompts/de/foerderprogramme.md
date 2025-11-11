
# Förderprogramme – strukturierte Tabelle (DE)

Erzeuge eine **prägnante HTML‑Tabelle** zu 4–10 **relevanten** Förderprogrammen für den Standort **{{BUNDESLAND_LABEL}}** (zusätzlich gern **Bund/EU**).
**Kein Markdown**, nur valides HTML ohne `<html>/<body>`.

**Spalten (in dieser Reihenfolge):**
1. **Prio** (100–0, abgeleitet aus Nähe zur Zielgruppe & Deadline)
2. **Programm**
3. **Förderung** (Zuschuss/Darlehen, Quote/Budget wenn verfügbar)
4. **Zielgruppe** (z. B. KMU, Solo, Startups)
5. **Deadline** (Datum oder „laufend“)
6. **Fit** (Solo/Team/KMU)
7. **Quelle** (Link auf die offizielle Seite, **ein Link je Zeile**)

**Eingabekontext:**
- Bundesland: {{BUNDESLAND_LABEL}}
- Größe: {{UNTERNEHMENSGROESSE_LABEL}}
- Branche: {{BRANCHE_LABEL}}
- Hauptleistung: {{HAUPTLEISTUNG}}

**Regeln:**
- Bevorzuge **offizielle Quellen** (berlin.de, ibb.de, bayern.de, bmwk.de, foerderdatenbank.de, europa.eu).
- Keine Werbung, keine doppelten Programme; **max. 1 Link** pro Zeile.
- Wenn Fristen nicht klar sind: „laufend“.
- Sprache: **knapp & sachlich**.

**Ausgabeformat:**

<table class="table">
  <thead><tr><th>Prio</th><th>Programm</th><th>Förderung</th><th>Zielgruppe</th><th>Deadline</th><th>Fit</th><th>Quelle</th></tr></thead>
  <tbody>
    <!-- Zeilen -->
  </tbody>
</table>

<p class="stand">Stand: {{report_date}}</p>
