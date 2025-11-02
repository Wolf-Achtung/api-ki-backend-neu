Antworte ausschließlich mit **validem HTML** (keine Markdown‑Fences).
# Kostenübersicht & ROI – Prompt (DE)
**Ziel:** Erzeuge zwei **HTML‑Snippets** (ohne Codefences): (A) ROI_HTML, (B) COSTS_OVERVIEW_HTML.

**Eingaben**
- Stundensatz: {{stundensatz_eur}} €/h
- Nutzen: {{monatsersparnis_stunden}} h/Monat (≈ {{monatsersparnis_eur}} €), Jahr: {{jahresersparnis_stunden}} h (≈ {{jahresersparnis_eur}} €)
- Kosten: konservativ {{capex_konservativ_eur}}+{{opex_konservativ_eur}} €, realistisch {{capex_realistisch_eur}}+{{opex_realistisch_eur}} €

**Anforderungen**
1) ROI_HTML: kurze Erläuterung + <ul> mit Payback (Monate) – Formel: (CapEx+OpEx)/{{monatsersparnis_eur}}.
2) COSTS_OVERVIEW_HTML: kleine Tabelle (CapEx/OpEx konservativ vs. realistisch) + Rechenweg als Fußnote.
3) Keine abweichenden Zahlen; keine Codefences.

**Ausgabe:** Zwei HTML‑Snippets.
