<!-- Executive Summary (DE) -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown‑Fences.
     Nutze die Platzhalter:
     - {BRANCHE_LABEL}, {UNTERNEHMENSGROESSE_LABEL}, {BUNDESLAND_LABEL}, {HAUPTLEISTUNG}
     - {report_date}, {report_year}, {kundencode}, {report_id}
     - KPI/Scores: {score_gesamt}, {score_befaehigung}, {score_governance}, {score_sicherheit}, {score_nutzen}
     Schreibe präzise, fachlich und motivierend – kein Marketing‑Sprech. -->

<section class="section executive-summary">
  <h2>Executive Summary</h2>
  <p><strong>Unternehmen:</strong> {{BRANCHE_LABEL}} – {{UNTERNEHMENSGROESSE_LABEL}} – {{BUNDESLAND_LABEL}}.<br>
     <strong>Hauptleistung/Produkt:</strong> {{HAUPTLEISTUNG}}</p>

  <p>Diese Kurzfassung fasst die wichtigsten Ergebnisse der KI‑Analyse zusammen (Stand: {{report_date}}): Stärken, Chancen, Risiken
     sowie die empfohlenen Quick Wins und Startprojekte mit realistischen Zeit- und Aufwandsangaben.</p>

  <div class="kpi-cards">
    <div class="kpi"><div class="kpi-label">Gesamt</div><div class="kpi-value">{{score_gesamt}}</div></div>
    <div class="kpi"><div class="kpi-label">Befähigung</div><div class="kpi-value">{{score_befaehigung}}</div></div>
    <div class="kpi"><div class="kpi-label">Governance</div><div class="kpi-value">{{score_governance}}</div></div>
    <div class="kpi"><div class="kpi-label">Sicherheit</div><div class="kpi-value">{{score_sicherheit}}</div></div>
    <div class="kpi"><div class="kpi-label">Wertschöpfung</div><div class="kpi-value">{{score_nutzen}}</div></div>
  </div>

  <h3>Top‑3 Quick Wins (30–60 Tage)</h3>
  <p>Fasse bis zu drei der wichtigsten Quick‑Wins aus dem Abschnitt „Quick Wins (0–90 Tage)“ prägnant zusammen. Gib pro Eintrag den Titel, den zentralen Nutzen für das Unternehmen und die geschätzte monatliche Einsparung in Stunden an. Verwende einen sachlichen, zuversichtlichen Ton. Wenn weniger als drei Quick Wins identifiziert wurden, liste nur die verfügbaren auf.</p>
  <ul>
    <!-- Das Modell soll hier 1–3 Listeneinträge mit realen Quick‑Wins generieren. Jeder Eintrag soll den Titel, Nutzen und die monatliche Einsparung enthalten. -->
  </ul>

  <h3>Startpunkt (Pilot)</h3>
  <p>Leite aus den Quick Wins und der Vision des Unternehmens einen konkreten Pilotbereich ab. Beschreibe Zielbild, Verantwortlichkeiten, Minimalumfang (MVP) und Erfolgskriterien in 2–3 Sätzen. Achte auf einen motivierenden, aber fachlich soliden Ton.</p>
</section>
