# Executive Summary – Prompt (DE)

**Ziel:** Erzeuge eine prägnante Executive Summary **als valides HTML** (ohne Markdown-Fences). Keine Platzhalter oder Mustache‑Variablen in der Ausgabe.

**Kontext (bereits aufgelöst):**
- Branche: {{BRANCHE_LABEL}}
- Unternehmensgröße: {{UNTERNEHMENSGROESSE_LABEL}}
- Bundesland: {{BUNDESLAND_LABEL}}
- Hauptleistung/Produkt: {{HAUPTLEISTUNG}}
- Scores (0–100): Gesamt {{score_gesamt}}, Governance {{score_governance}}, Sicherheit {{score_security}}, Wertschöpfung {{score_value}}, Befähigung {{score_enablement}}
- Stand: {{report_date}}

**Ausgabeformat (exakt ein <section>):**
<section class="executive-summary" data-branche="{{BRANCHE_LABEL}}" data-groesse="{{UNTERNEHMENSGROESSE_LABEL}}" data-bundesland="{{BUNDESLAND_LABEL}}" data-hauptleistung="{{HAUPTLEISTUNG}}">
  <p class="stand"><strong>Stand:</strong> {{report_date}}</p>
  <p><strong>Kontext:</strong> {{BRANCHE_LABEL}} · {{UNTERNEHMENSGROESSE_LABEL}} · {{BUNDESLAND_LABEL}} · {{HAUPTLEISTUNG}}</p>

  <ul class="key-points">
    <li><strong>KI‑Reifegrad:</strong> Gesamt {{score_gesamt}}/100 · Governance {{score_governance}} · Sicherheit {{score_security}} · Wertschöpfung {{score_value}} · Befähigung {{score_enablement}}</li>
    <li><strong>Stärken:</strong>
      <ul>
        <li>1–2 branchenspezifische Stärken knapp benennen.</li>
        <li>Konkreter Bezug zu Größe/Team (Machbarkeit).</li>
      </ul>
    </li>
    <li><strong>Entwicklungsbereiche:</strong>
      <ul>
        <li>1–2 Lücken mit kurzer Begründung und Nutzen.</li>
      </ul>
    </li>
  </ul>

  <h3>Nächste Schritte (0–90 Tage)</h3>
  <ol>
    <li>Woche 1–3: eine konkrete Maßnahme mit Verantwortlichem.</li>
    <li>Woche 4–6: eine konkrete Maßnahme mit Verantwortlichem.</li>
    <li>Woche 7–9: eine konkrete Maßnahme mit Verantwortlichem.</li>
  </ol>

  <aside class="transparency-box">
    <h4>Transparenz</h4>
    <ul>
      <li>Genutzte Dienste/Modelle (z. B. OpenAI API, Tavily; optional Perplexity).</li>
      <li>Recherchefenster: letzte 7–14 Tage.</li>
      <li>Report‑ID/Build wird separat im Dokument geführt.</li>
    </ul>
  </aside>
</section>

**Stil:** Klar, knapp, ohne übertriebenes Marketing‑Sprech. Deutsche Sprache.
