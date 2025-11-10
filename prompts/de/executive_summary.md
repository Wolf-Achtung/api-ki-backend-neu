# Executive Summary – Prompt (DE)
Antworte ausschließlich mit **validem HTML** (keine <html>/<head>/<body>-Tags, keine Markdown-Fences).

## Kontext (Zahlen bitte exakt übernehmen)
- Branche: {{BRANCHE_LABEL}}
- Größe: {{UNTERNEHMENSGROESSE_LABEL}}
- Bundesland: {{BUNDESLAND_LABEL}}
- Hauptleistung: {{HAUPTLEISTUNG}}
- Stand: {{report_date}}
- Scores (0–100): Gesamt {{score_gesamt}}, Governance {{score_governance}}, Sicherheit {{score_sicherheit}}, Wertschöpfung {{score_wertschoepfung}}, Befähigung {{score_befaehigung}}

## Aufgabe
Erzeuge eine kompakte Executive‑Summary mit:
- Kerndatenzeile mit obigen Zahlen (konkret einsetzen – KEINE Platzhalter in geschweiften Klammern).
- 3 Stichpunkte „Stärken“ und 3 „Entwicklungsbereiche“ (branchenspezifisch).
- „Nächste Schritte (0–90 Tage)“ als 3‑Punkte‑Liste.
- Transparenz‑Box mit: genutzte Dienste/Modelle (OpenAI API; Tavily; ggf. Perplexity), Recherchefenster (z. B. 7–14 Tage), Report‑ID ({{report_id}}).

## Format
<section class="executive-summary" data-branche="{{BRANCHE_LABEL}}" data-groesse="{{UNTERNEHMENSGROESSE_LABEL}}" data-bundesland="{{BUNDESLAND_LABEL}}" data-hauptleistung="{{HAUPTLEISTUNG}}">
  <p class="stand"><strong>Stand:</strong> {{report_date}}</p>
  <p><strong>Kontext:</strong> {{BRANCHE_LABEL}} · {{UNTERNEHMENSGROESSE_LABEL}} · {{BUNDESLAND_LABEL}} · {{HAUPTLEISTUNG}}</p>
  <ul class="key-points">
    <li><strong>KI‑Reifegrad (0–100):</strong> Gesamt {{score_gesamt}} · Governance {{score_governance}} · Sicherheit {{score_sicherheit}} · Wertschöpfung {{score_wertschoepfung}} · Befähigung {{score_befaehigung}}</li>
    <li><strong>Stärken:</strong> <ul><li>—</li><li>—</li><li>—</li></ul></li>
    <li><strong>Entwicklungsbereiche:</strong> <ul><li>—</li><li>—</li><li>—</li></ul></li>
  </ul>
  <h3>Nächste Schritte (0–90 Tage)</h3>
  <ol><li>…</li><li>…</li><li>…</li></ol>
  <aside class="transparency-box">
    <h4>Transparenz</h4>
    <ul>
      <li>Genutzte Dienste/Modelle: OpenAI API; Tavily; optional Perplexity</li>
      <li>Recherchefenster: letzte 7–14 Tage</li>
      <li>Report‑ID: {{report_id}}</li>
    </ul>
  </aside>
</section>
