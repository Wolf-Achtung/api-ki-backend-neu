<!-- Empfehlungen – Branchenspezifisch (Branch Override) -->
<!-- Output NUR als valides HTML; erlaubt: p, ul, ol, li, table, thead, tbody, tr, th, td, div, h4, strong, em, small, br -->
<!-- Keine Bilder, iframes, Skripte, externes CSS. Keine Fantasiezahlen. -->
<!-- Nutze die Variablen: {BRANCHE_LABEL}, {UNTERNEHMENSGROESSE_LABEL}, {BUNDESLAND_LABEL}, {hauptleistung}, {ki_ziele}, {anwendungsfaelle}, {ki_projekte}, {trainings_interessen}, {zeitersparnis_prioritaet}. -->
<!-- Zahlen nur aus gelieferten Variablen (z. B. Stunden-/Budgetwerte), sonst qualitative Einschätzung. -->
    <div>
      <h4>Top‑Empfehlungen für {BRANCHE_LABEL} (90&nbsp;Tage)</h4>
      <p>Fokussieren Sie auf Umsetzbarkeit für {UNTERNEHMENSGROESSE_LABEL}. Verweisen Sie auf <em>{{ hauptleistung }}</em> und vorhandene {ki_projekte}.</p>
      <table><thead><tr><th>Maßnahme</th><th>Nutzen</th><th>Kennzahl</th><th>Aufwand</th><th>Risiko</th></tr></thead>
      <tbody>
        <tr><td>Standard‑Vorlagen & Wissensbausteine (RAG)</td><td>Weniger Such‑/Schreibzeit</td><td>−X% Bearbeitungszeit</td><td>niedrig</td><td>gering</td></tr>
        <tr><td>Assistent für {BRANCHE_LABEL}‑Alltag</td><td>Antwortqualität, Konsistenz</td><td>NPS/CSAT ↑</td><td>niedrig‑mittel</td><td>gering</td></tr>
        <tr><td>Reporting/Analyse‑Starter</td><td>Schnellere Entscheidungen</td><td>Time‑to‑Insight ↓</td><td>mittel</td><td>mittel</td></tr>
      </tbody></table>
      <p class="small muted">Kennzahlen nur schätzen, falls Variablen fehlen; nie erfinden.</p>
    </div>