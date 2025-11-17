<!--
Executive Summary (DE) — Steuerung & Regeln
Eingaben (numerisch, bereits berechnet und im Template-Kontext verfügbar):
  - qw_hours_total (h/Monat)
  - CAPEX_REALISTISCH_EUR (€, einmalig)
  - OPEX_REALISTISCH_EUR (€/Monat)
  - PAYBACK_MONTHS (Monate)
  - ROI_12M (0..1, als Anteil)

WICHTIG:
  - Keine Zahlen erfinden. Immer nur die bereitgestellten Variablen verwenden.
  - Antworte ausschließlich mit gültigem HTML. KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.
  - Verwende die vorhandenen Platzhalter (Jinja): {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{BUNDESLAND_LABEL}},
    {{HAUPTLEISTUNG}}, {{report_date}}, {{report_year}}, {{kundencode}}, {{report_id}} und KPI/Scores:
    {{score_gesamt}}, {{score_befaehigung}}, {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}.
  - Zahlenformat: Tausenderpunkt, Dezimalkomma; Prozent mit % (z. B. 35,0 %).
  - Ton: professionell, prägnant, motivierend – keine Marketingsprache.
  - Quick-Wins-Liste nur dann ausgeben, wenn entsprechende Inhalte im Kontext vorhanden sind.
-->

<section class="section executive-summary">
  <h2>Executive Summary</h2>
  <p><strong>Unternehmen:</strong> {{BRANCHE_LABEL}} – {{UNTERNEHMENSGROESSE_LABEL}} – {{BUNDESLAND_LABEL}}.<br>
     <strong>Hauptleistung/Produkt:</strong> {{HAUPTLEISTUNG}}</p>

  <p>Diese Kurzfassung fasst die wichtigsten Ergebnisse der KI‑Analyse zusammen (Stand: {{report_date}}): Stärken, Chancen,
     Risiken sowie die empfohlenen Quick Wins und ein praxistauglicher Startplan.</p>

  <div class="kpi-cards">
    <div class="kpi"><div class="kpi-label">Gesamt</div><div class="kpi-value">{{score_gesamt}}</div></div>
    <div class="kpi"><div class="kpi-label">Befähigung</div><div class="kpi-value">{{score_befaehigung}}</div></div>
    <div class="kpi"><div class="kpi-label">Governance</div><div class="kpi-value">{{score_governance}}</div></div>
    <div class="kpi"><div class="kpi-label">Sicherheit</div><div class="kpi-value">{{score_sicherheit}}</div></div>
    <div class="kpi"><div class="kpi-label">Wertschöpfung</div><div class="kpi-value">{{score_nutzen}}</div></div>
  </div>

  <h3>Wirtschaftliche Eckdaten</h3>
  <ul>
    <li><strong>Quick‑Win‑Einsparungen:</strong> {{qw_hours_total}} h/Monat</li>
    <li><strong>Invest (CAPEX):</strong> {{CAPEX_REALISTISCH_EUR}} €; <strong>laufende Kosten (OPEX):</strong> {{OPEX_REALISTISCH_EUR}} €/Monat</li>
    <li><strong>Amortisation:</strong> {{PAYBACK_MONTHS}} Monate; <strong>ROI (12 Monate):</strong> {{ (ROI_12M*100)|round(1) }} %</li>
  </ul>

  <h3>Top‑3 Quick Wins (30–60 Tage)</h3>
  <ul>
    <!-- Erzeuge bis zu drei Einträge basierend auf dem Abschnitt „Quick Wins (0–90 Tage)“ dieses Reports.
         Jeder Eintrag: <li><strong>Titel</strong> – zentraler Nutzen; ≈X h/Monat</li>.
         Wenn keine Quick‑Wins im Kontext vorliegen, lasse diese Liste komplett weg. -->
  </ul>

  <h3>Startpunkt (Pilot)</h3>
  <p><!-- Formuliere 2–3 Sätze mit einem konkreten Pilotbereich (Zielbild, verantwortliche Rollen, MVP‑Umfang, Erfolgskriterien).
           Verweise prägnant auf die oben genannten wirtschaftlichen Eckdaten. --></p>

  <h3>Nächste Schritte (30/60/90 Tage)</h3>
  <ol>
    <li><strong>30 Tage:</strong> Pilot auswählen, Datengrundlage sichern, Verantwortlichkeiten klären.</li>
    <li><strong>60 Tage:</strong> Pilot umsetzen (MVP), Messgrößen tracken, Schulungen für beteiligte Rollen.</li>
    <li><strong>90 Tage:</strong> Review (ROI/Payback), Skalierungsentscheidung, Standards (Prozess, Compliance) festlegen.</li>
  </ol>
</section>
