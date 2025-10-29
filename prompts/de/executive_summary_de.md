# Executive Summary – Prompt (DE)
**Ziel:** Liefere ein kurzes, faktenbasiertes **HTML‑Snippet** (ohne Codefences) mit <ul>/<li>, <p>, <strong>. Keine Inline‑Styles.

**Eingaben**
- Profil: {{unternehmen_name}}, {{branche}}, {{bundesland}}, {{unternehmensgroesse}}, {{jahresumsatz}}, {{ki_knowhow}}
- Scores: {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}, {{score_befaehigung}}, {{score_gesamt}}
- Vision: {{vision}}
- Benchmarks (optional): {{benchmark_avg}}, {{benchmark_top}}
- Stand: {{report_date}}

**Anforderungen**
1) Struktur (kurz, prägnant):
   - Profil & Zielbild (1–2 Sätze, branchenspezifisch).
   - Reifegrad-Kernaussage (Gesamt + stärkste/schwächste Säule).
   - 2–3 Quick Wins mit Nutzen (Zeit/€) und Payback‑Hinweis.
   - Top‑Risiken (3) + knappe Mitigation.
   - Nächste Schritte (0–90 Tage) als 3–4 Stichpunkte.
2) Ton: Klar, ohne Marketing‑Sprech.
3) Compliance: Satz einbauen – „Dieser Report wurde teilweise mit KI‑Unterstützung erstellt.“
4) **Keine** Codefences, keine Überschrift „Executive Summary“ ausgeben.

**Ausgabe:** Nur das HTML‑Snippet.
