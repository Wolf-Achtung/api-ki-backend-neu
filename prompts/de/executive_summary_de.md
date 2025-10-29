# Executive Summary – Prompt (DE)

**Rolle:** Senior-KI-Berater:in für KMU.  
**Ziel:** Erzeuge eine prägnante Executive Summary **ohne Codefences** (keine ```-Blöcke), als **HTML-Snippet** mit <ul>/<li>, <p>, <strong> etc. – **kein** Inline-CSS.

## Eingaben (Variablen)
- **Profil**: {{unternehmen_name}}, {{branche}}, {{bundesland}}, {{unternehmensgroesse}}, {{jahresumsatz}}, {{ki_knowhow}}
- **Scores**: {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}, {{score_befaehigung}}, {{score_gesamt}}
- **Vision**: {{vision}}
- **Top-Quick-Wins**: aus separatem Prompt (Stunden-/€-Ersparnis konsistent)
- **Benchmarks (optional)**: {{benchmark_avg}}, {{benchmark_top}}
- **Stand**: {{report_date}}

## Anforderungen
1. **Struktur** (nutze <ul>/<li> + kurze Sätze):
   - **Profil & Zielbild** (1–2 Sätze) – branchen- & regionsspezifisch (z. B. „KMU in {{bundesland}}“).
   - **Reifegrad-Kernaussage** mit Scores (Gesamt + stärkste/schwächste Säule).
   - **2–3 Quick Wins** mit kompaktem Nutzen (Zeit/€) und ROI‑Hinweis (z. B. „Payback < 2 Monate“).
   - **Top‑Risiken** (3 Punkte) + **Mitigation** in Stichworten.
   - **Nächste Schritte (0–90 Tage)** als 3–4 fokussierte Punkte.
2. **Tonalität:** Klar, faktenorientiert, **ohne Marketing‑Sprech**.
3. **Compliance:** Transparenzsatz einbauen: *„Dieser Report wurde teilweise mit KI‑Unterstützung erstellt.“*
4. **Konsistenz:** Verwende exakt die **globalen Metriken** aus Quick Wins/ROI (keine neuen Zahlen erfinden).
5. **Keine Codefences**, keine Präfixe wie „Executive Summary:“ in der Ausgabe.

## Ausgabe
Gib **nur** das HTML‑Snippet zurück (ohne <html>…).
