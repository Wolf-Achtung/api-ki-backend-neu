# Executive Summary – Prompt (DE)
**Ziel:** Liefere ein prägnantes **HTML‑Snippet** (ohne Codefences) mit <ul>/<li>, <p>, <strong>. Keine Inline‑Styles.

**Eingaben**
- Profil: {{unternehmen_name}}, {{branche}}, {{bundesland}}, {{unternehmensgroesse}}, {{jahresumsatz}}, {{ki_knowhow}}
- Scores: {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}, {{score_befaehigung}}, {{score_gesamt}}
- Benchmarks (optional): {{benchmark_avg}}/{{benchmark_top}}
- Stand: {{report_date}}
- Transparenz: {{transparency_text}}

**Anforderungen**
1) Struktur (kurz, prägnant): Reifegrad-Kernaussage → 2–3 Quick Wins (Zeit/€) → Risiken & Mitigation (3) → Nächste Schritte (0–90 Tage).
2) Ton: Klar, ohne Marketing‑Sprech.
3) Compliance: Verwende exakt den Text aus **{{transparency_text}}** (einmal, am Ende).
4) **Keine** Codefences, keine Überschrift „Executive Summary“ ausgeben.

**Ausgabe:** Nur das HTML‑Snippet.
