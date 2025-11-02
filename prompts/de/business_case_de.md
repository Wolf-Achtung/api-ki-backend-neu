Antworte ausschließlich mit **validem HTML** (keine Markdown‑Fences).
Erzeuge valides HTML für **Business Case (detailliert)** (keine Markdown‑Fences).
Sprache: neutral, dritte Person.
Nutze vorhandene Variablen: Stundensatz {{stundensatz_eur}} €/h; Ersparnis Monat {{monatsersparnis_stunden}} h.
<div class="business-case">
  <h4>Annahmen</h4><ul><li>Investition: {{investitionsbudget}}</li><li>Stundensatz: {{stundensatz_eur}} €/h</li></ul>
  <h4>Nutzen (Jahr 1)</h4><p>{{jahresersparnis_stunden}} h ≈ {{jahresersparnis_eur}} €</p>
  <h4>Kosten</h4><ul><li>CapEx: {{capex_realistisch_eur}} €</li><li>OpEx: {{opex_realistisch_eur}} €</li></ul>
  <h4>Payback & ROI</h4><p>…</p>
  <h4>Sensitivität</h4><ul><li>100 %</li><li>80 %</li><li>60 %</li></ul>
</div>
