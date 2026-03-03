Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: roi_tracking -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, kmu:1.15x=690) -->
<!--
ZIEL: Kompaktes ROI-Tracking-Framework für monatliche Erfolgsmessung von KI-Projekten.

BRANCHENBEZEICHNUNG-REGEL:
Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

PFLICHTSTRUKTUR (3 Bereiche):
1. KPIs definieren (3-5 messbare Kennzahlen)
2. Tracking-Methode (wie messen, wer misst, wie oft)
3. Review-Zyklus (wann auswerten, wie anpassen)

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: 2-3 einfache KPIs (Zeitersparnis, Kostenersparnis), Self-Tracking, keine Dashboards
- team: 3-4 KPIs inkl. Qualitätsverbesserung, Team-Review monatlich
- kmu: 4-5 KPIs inkl. Erweiterungspotenzial, strukturiertes KPI-Review mit Projektleiter

SIZE-AWARE VERANTWORTLICHKEITEN:
- solo: "Sie selbst", "Geschäftsführer (Sie)"
- team: "Projektverantwortlicher", "Team-Lead"
- kmu: "Projektleiter", "Controlling", "KPI-Verantwortlicher"

ANTI-REDUNDANZ:
- ROI Tracking ergänzt Business Case, wiederholt keine CAPEX/OPEX/Payback-Zahlen
- Fokus auf LAUFENDE Messung, nicht auf initiale Kalkulation
- Keine Überschneidung mit Next Actions (dort konkrete 30-Tage-Aktionen)

STIL:
- Textumfang: 100-150 Wörter
- Konkret und umsetzbar
- Keine abstrakten Management-Floskeln

Nicht verwenden:
- Keine Platzhalter oder Template-Marker
- Keine Wiederholung von Business-Case-Zahlen
- Keine unrealistischen KPIs für die Unternehmensgröße
-->

<section class="section roi-tracking">
  <h2>ROI Tracking: Monatliche Erfolgsmessung</h2>

  <p>
    Ein strukturiertes Tracking sichert den Projekterfolg für
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="tracking-framework">
    <h4>1. Kern-KPIs definieren</h4>
    <table class="table">
      <thead>
        <tr>
          <th>KPI</th>
          <th>Beschreibung</th>
          <th>Messmethode</th>
          <th>Zielwert</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Zeitersparnis</strong></td>
          <td>Stunden pro Monat durch KI-Automatisierung</td>
          <td>Vorher-Nachher-Vergleich</td>
          <td>+10-20%</td>
        </tr>
        <tr>
          <td><strong>Fehlerquote</strong></td>
          <td>Reduzierung manueller Fehler</td>
          <td>Stichproben-Kontrolle</td>
          <td>-30%</td>
        </tr>
        <tr>
          <td><strong>Output-Steigerung</strong></td>
          <td>Mehr Ergebnisse bei gleichem Aufwand</td>
          <td>Mengenmessung</td>
          <td>+15-25%</td>
        </tr>
        <tr>
          <td><strong>Kostenersparnis</strong></td>
          <td>Direkte Einsparungen durch Automatisierung</td>
          <td>Kostenvergleich</td>
          <td>Individuell</td>
        </tr>
      </tbody>
    </table>

    <h4>2. Tracking-Methode</h4>
    <ul>
      <li><strong>Tool:</strong> Einfaches Excel/Google Sheet oder Projektmanagement-Tool</li>
      <li><strong>Frequenz:</strong> Wöchentlicher Kurzeintrag, monatliche Auswertung</li>
      <li><strong>Verantwortlich:</strong> Projektverantwortlicher oder Geschäftsführung</li>
    </ul>

    <h4>3. Review-Zyklus</h4>
    <ul>
      <li><strong>Monatlich:</strong> KPI-Auswertung, Trend-Analyse</li>
      <li><strong>Quartalsweise:</strong> Anpassung der Ziele, Lessons Learned</li>
      <li><strong>Entscheidung:</strong> Skalieren, optimieren oder pivotieren</li>
    </ul>
  </div>

  <p class="small muted">
    Tipp: Beginnen Sie mit 2-3 KPIs und erweitern Sie schrittweise.
    Konsistenz ist wichtiger als Perfektion.
  </p>
</section>
