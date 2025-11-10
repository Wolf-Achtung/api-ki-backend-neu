Antworte ausschließlich mit **validem HTML** (kein <html>, <head> oder <body>, keine Markdown-Fences).

<section class="executive-summary" data-branche="{{BRANCHE_LABEL}}" data-groesse="{{UNTERNEHMENSGROESSE_LABEL}}" data-bundesland="{{BUNDESLAND_LABEL}}" data-hauptleistung="{{HAUPTLEISTUNG}}">
  <h2>Executive Summary</h2>
  <p><strong>Stand:</strong> {{heute_iso}}</p>
  <p><strong>Kontext:</strong> {{BRANCHE_LABEL}} · {{UNTERNEHMENSGROESSE_LABEL}} · {{BUNDESLAND_LABEL}} · {{HAUPTLEISTUNG}}</p>

  <ul class="key-points">
    <li><strong>KI‑Reifegrad (0–100):</strong> Gesamt {{score_gesamt}} · Governance {{score_gov}} · Sicherheit {{score_sec}} · Wertschöpfung {{score_val}} · Befähigung {{score_enable}}.</li>
    <li><strong>Stärken:</strong> <!-- 2–3 Kernaussagen, branchenspezifisch --></li>
    <li><strong>Entwicklungsbereiche:</strong> <!-- 2–3 Lücken mit kurzer Begründung --></li>
  </ul>

  <h3>Nächste Schritte (0–90 Tage)</h3>
  <ol>
    <li><!-- Schritt 1 (Woche 1–3) --></li>
    <li><!-- Schritt 2 (Woche 4–6) --></li>
    <li><!-- Schritt 3 (Woche 7–9) --></li>
  </ol>

  <aside class="transparency-box">
    <h4>Transparenz</h4>
    <ul>
      <li>Genutzte Dienste/Modelle: <!-- OpenAI API, Perplexity API, Tavily API, ggf. Mistral --></li>
      <li>Recherchefenster: <!-- z. B. letzte 7–14 Tage --></li>
      <li>Build/Report‑ID: {{build_id}}</li>
    </ul>
  </aside>
</section>
