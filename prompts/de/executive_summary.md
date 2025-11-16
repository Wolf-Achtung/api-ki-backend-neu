<!-- Executive Summary (DE) -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown‑Fences.
     Nutze die Platzhalter:
     - {BRANCHE_LABEL}, {UNTERNEHMENSGROESSE_LABEL}, {BUNDESLAND_LABEL}, {HAUPTLEISTUNG}
     - {report_date}, {report_year}, {kundencode}, {report_id}
     - KPI/Scores: {score_gesamt}, {score_befaehigung}, {score_governance}, {score_sicherheit}, {score_nutzen}
     Schreibe präzise, fachlich und motivierend – kein Marketing‑Sprech.
-->

<section class="section executive-summary">
  <h2>Executive Summary</h2>
  <p><strong>Unternehmen:</strong> {{BRANCHE_LABEL}} – {{UNTERNEHMENSGROESSE_LABEL}} – {{BUNDESLAND_LABEL}}.<br>
     <strong>Hauptleistung/Produkt:</strong> {{HAUPTLEISTUNG}}</p>

  <p>Diese Kurzfassung fasst die wichtigsten Ergebnisse der KI‑Analyse zusammen (Stand: {{report_date}}): Stärken, Chancen, Risiken
     sowie die empfohlenen Quick Wins und Startprojekte mit realistischen Zeit‑ und Aufwandsangaben.</p>

  <div class="kpi-cards">
    <div class="kpi"><div class="kpi-label">Gesamt</div><div class="kpi-value">{{score_gesamt}}</div></div>
    <div class="kpi"><div class="kpi-label">Befähigung</div><div class="kpi-value">{{score_befaehigung}}</div></div>
    <div class="kpi"><div class="kpi-label">Governance</div><div class="kpi-value">{{score_governance}}</div></div>
    <div class="kpi"><div class="kpi-label">Sicherheit</div><div class="kpi-value">{{score_sicherheit}}</div></div>
    <div class="kpi"><div class="kpi-label">Wertschöpfung</div><div class="kpi-value">{{score_nutzen}}</div></div>
  </div>

  <h3>Top‑3 Quick Wins (30–60 Tage)</h3>
  <p>Nutze die Quick‑Wins aus dem Abschnitt „Quick Wins (0–90 Tage)“ und fasse die drei wichtigsten in je 1–2 Sätzen zusammen. Jede Zeile sollte Titel, Nutzen und geschätzte Ersparnis enthalten.</p>
  <ol>
    <li><strong>Quick Win 1:</strong> Titel – Kernaussage; Nutzen und geschätzte Zeitersparnis.</li>
    <li><strong>Quick Win 2:</strong> Titel – Kernaussage; Nutzen und geschätzte Zeitersparnis.</li>
    <li><strong>Quick Win 3:</strong> Titel – Kernaussage; Nutzen und geschätzte Zeitersparnis.</li>
  </ol>

  <h3>Startpunkt (Pilot)</h3>
  <p>Empfohlener Pilotbereich mit Zielbild, Verantwortlichkeiten, Minimalumfang (MVP) und Erfolgskriterien. Leite diesen aus den identifizierten Quick Wins und der Vision des Unternehmens ab.</p>
</section>