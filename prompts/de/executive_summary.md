<!-- executive_summary.md – v3.1 GOLD STANDARD+ BRANCHE, SIZE & KPIs
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences. -->

<!-- KONTEXT-VARIABLEN
     {{BRANCHE_LABEL}}
     {{UNTERNEHMENSGROESSE_LABEL}}
     {{BUNDESLAND_LABEL}}
     {{HAUPTLEISTUNG}}
     {{score_gesamt}}, {{score_befaehigung}}, {{score_governance}},
     {{score_sicherheit}}, {{score_nutzen}}
     {{qw_hours_total}}, {{EINSPARUNG_MONAT_EUR}}
     {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}
     {{PAYBACK_MONTHS}}, {{ROI_12M}}
     {CONTEXT_QUICK_WINS}, {CONTEXT_ROADMAP_90D}
-->

<section class="section executive-summary">
  <h2>Executive Summary</h2>

  <!-- Freundlicher Einstieg -->
  <p>
    Vielen Dank, dass Sie sich die Zeit für diese KI-Status-Analyse genommen haben.
    Ihre Antworten zeigen, dass Sie Ihr Geschäft in {{BRANCHE_LABEL}} sehr gut kennen
    und bereits wichtige Grundlagen für den Einsatz von KI in
    <strong>{{HAUPTLEISTUNG}}</strong> geschaffen haben.
    Dieser Report fasst die wichtigsten Ergebnisse zusammen und zeigt,
    welche nächsten Schritte für {{UNTERNEHMENSGROESSE_LABEL}} besonders sinnvoll sind.
  </p>

  <!-- Profil -->
  <p>
    <strong>Ihr Profil:</strong>
    {{BRANCHE_LABEL}} – {{UNTERNEHMENSGROESSE_LABEL}} – {{BUNDESLAND_LABEL}}<br>
    <strong>Kern-Leistung:</strong> {{HAUPTLEISTUNG}}
  </p>

  <!-- Kurz-Zusammenfassung -->
  <p>
    Die Analyse ergibt einen Gesamt-Score von {{score_gesamt}}/100 und zeigt,
    dass insbesondere der Bereich Wertschöpfung ({{score_nutzen}}/100) und
    Befähigung ({{score_befaehigung}}/100) gute Ansatzpunkte bieten.
    Gleichzeitig gibt es bei Governance ({{score_governance}}/100) und
    Sicherheit ({{score_sicherheit}}/100) klare, gut adressierbare
    Entwicklungsfelder.
  </p>

  <!-- Key Facts -->
  <div class="key-facts">
    <h4>Auf einen Blick</h4>
    <ul>
      <li><strong>KI-Readiness gesamt:</strong> {{score_gesamt}}/100 – kurze verbale Einordnung (z. B. „stabile Ausgangsbasis“)</li>
      <li><strong>Quick-Win-Potenzial:</strong> {{qw_hours_total}} h/Monat ≈ {{EINSPARUNG_MONAT_EUR}} €/Monat</li>
      <li><strong>Investition:</strong> ca. {{CAPEX_REALISTISCH_EUR}} € einmalig + {{OPEX_REALISTISCH_EUR}} €/Monat laufend</li>
      <li><strong>Amortisation:</strong> {{PAYBACK_MONTHS}} Monate · <strong>ROI (12 Monate):</strong> {{ROI_12M}} %</li>
      <li><strong>Empfohlener Startpunkt:</strong> ein klar umrissener Pilot direkt im Kernprozess von {{HAUPTLEISTUNG}}</li>
    </ul>
  </div>

  <!-- KPI-Kacheln -->
  <div class="kpi-cards">
    <div class="kpi"><div class="kpi-label">Gesamt</div><div class="kpi-value">{{score_gesamt}}</div></div>
    <div class="kpi"><div class="kpi-label">Befähigung</div><div class="kpi-value">{{score_befaehigung}}</div></div>
    <div class="kpi"><div class="kpi-label">Governance</div><div class="kpi-value">{{score_governance}}</div></div>
    <div class="kpi"><div class="kpi-label">Sicherheit</div><div class="kpi-value">{{score_sicherheit}}</div></div>
    <div class="kpi"><div class="kpi-label">Wertschöpfung</div><div class="kpi-value">{{score_nutzen}}</div></div>
  </div>

  <!-- Wirtschaftliche Eckdaten (interpretierend, nicht nur Wiederholung) -->
  <h3>Wirtschaftliche Eckdaten</h3>
  <p>
    Mit {{qw_hours_total}} eingesparten Stunden pro Monat
    (≈ {{EINSPARUNG_MONAT_EUR}} €/Monat) und einer realistischen Investition von
    {{CAPEX_REALISTISCH_EUR}} € plus {{OPEX_REALISTISCH_EUR}} €/Monat
    ergibt sich eine Amortisation nach rund {{PAYBACK_MONTHS}} Monaten.
    Ein ROI von {{ROI_12M}} % im ersten Jahr ist für ein
    {{UNTERNEHMENSGROESSE_LABEL}} in {{BRANCHE_LABEL}} konservativ, aber attraktiv –
    insbesondere, wenn die Quick Wins konsequent genutzt werden.
  </p>

  <!-- Top-3 Quick Wins (nur falls vorhanden) -->
  {% if CONTEXT_QUICK_WINS %}
  <h3>Top-3 Quick Wins (30–60 Tage)</h3>
  <p>
    Aus den identifizierten Quick Wins stechen drei Maßnahmen besonders hervor,
    weil sie direkt in {{HAUPTLEISTUNG}} eingreifen und schnell messbare
    Effekte bringen. Sie bilden den Kern der 90-Tage-Roadmap und sind
    in {{UNTERNEHMENSGROESSE_LABEL}} ohne große Zusatzressourcen umsetzbar.
  </p>
  <ul>
    <!-- Nutze CONTEXT_QUICK_WINS, um echte Quick Wins kurz zu beschreiben -->
    <li>[Quick Win 1 – Titel + Kerneffekt in h/Monat oder %]</li>
    <li>[Quick Win 2 – Titel + Kerneffekt]</li>
    <li>[Quick Win 3 – Titel + Kerneffekt]</li>
  </ul>
  {% endif %}

  <!-- Startpunkt/Pilot -->
  <h3>Startpunkt (Pilot)</h3>
  <p>
    Als Pilot empfiehlt sich ein klar abgegrenzter Use Case im Kernprozess
    von {{HAUPTLEISTUNG}}, der sich mit überschaubarem Aufwand testen lässt
    (siehe 90-Tage-Roadmap). Ziel ist, die oben beschriebenen Einsparungen
    möglichst schnell sichtbar zu machen und gleichzeitig Governance-
    und Sicherheitsanforderungen zu berücksichtigen.
  </p>

  <!-- Nächste Schritte -->
  <h3>Nächste Schritte (30/60/90 Tage)</h3>
  <ol>
    <li><strong>30 Tage:</strong> Pilot-Use-Case auswählen, Tools konfigurieren,
        Verantwortliche benennen, erste Fälle durch den neuen Workflow laufen lassen.</li>
    <li><strong>60 Tage:</strong> Pilot im Echtbetrieb, Effekte messen,
        Feedback sammeln, Quick Wins stabilisieren.</li>
    <li><strong>90 Tage:</strong> ROI-Review, Entscheidung über Skalierung
        und – falls sinnvoll – Nutzung von Förderprogrammen in {{BUNDESLAND_LABEL}}.</li>
  </ol>
</section>
