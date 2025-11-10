Antworte ausschließlich mit **validem HTML** (keine Markdown-Fences). Keine <html>, <head> oder <body>-Tags.

<div class="quick-wins-section" data-branche="{{BRANCHE_LABEL}}" data-groesse="{{UNTERNEHMENSGROESSE_LABEL}}" data-bundesland="{{BUNDESLAND_LABEL}}" data-hauptleistung="{{HAUPTLEISTUNG}}">
  <h3>Quick Wins (0–90 Tage) – {{BRANCHE_LABEL}} · {{UNTERNEHMENSGROESSE_LABEL}} · {{BUNDESLAND_LABEL}}</h3>
  <p class="intro">Sofort wirksame Maßnahmen für {{HAUPTLEISTUNG}} mit schnellem, messbarem Nutzen.</p>

  <ul class="quick-wins-list">
    <!-- Erzeuge GENAU 4–6 LI-Elemente; jedes LI enthält ALLE 7 Pflichtpunkte -->
    <li><strong>…Titel…</strong> – …WIE/Nutzen…
      <em>Ersparnis: {{qw1_monat_stunden}} h/Monat (~{{qw1_jahr_eur}} €/Jahr).</em>
      Aufwand: … Tage. Tool: <a href="PRODUCT_URL" target="_blank" rel="noopener">Tool</a> ·
      <a href="TRUST_URL" target="_blank" rel="noopener">Trust/Privacy</a>.
      ROI: … Monate. DSGVO/AI‑Act: … (AVV/DPA, Transparenz, Datenminimierung).
    </li>
    <!-- qw2..qw6 analog -->
  </ul>

  <div class="total-potential">
    <h4>Gesamt‑Potential</h4>
    <ul>
      <li><strong>Zeitersparnis:</strong> {{qw_gesamt_monat_stunden}} h/Monat</li>
      <li><strong>Kosteneinsparung:</strong> {{qw_gesamt_jahr_eur}} €/Jahr ({{stundensatz_eur}} €/h)</li>
      <li><strong>ROI:</strong> 3–6 Monate</li>
      <li><strong>Stand:</strong> {{heute_iso}}</li>
    </ul>
  </div>
</div>

<!-- QUALITÄTSGATES (HART)
- Genau 4–6 LI-Elemente.
- 7 Pflichtpunkte je LI: Titel · Nutzen/WIE · Ersparnis (h/Monat & €/Jahr) · Aufwand (Tage) · Tool (EU‑first, 2 Links) · DSGVO/AI‑Act‑Satz · ROI.
- Nutze NUR Variablen: qw1..qw6_monat_stunden, stundensatz_eur. Jahresersparnis = h/Monat × stundensatz_eur × 12.
- Solo/Kleinbetrieb berücksichtigen (SaaS‑First).
- Keine {…} im End‑HTML; keine Widersprüche.
- Bei fehlenden Variablen: EIN Block <div class="validation-error">…</div> mit Liste fehlender Variablen ausgeben.
-->
