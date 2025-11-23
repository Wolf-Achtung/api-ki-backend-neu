
---

## `prompts/de/executive_summary.md` (neu)

:contentReference[oaicite:1]{index=1}  

```markdown
# PROMPT: Executive Summary – Erste Seite des KI-Readiness-Reports

## ZWECK
Erstelle eine **einladende, freundliche** Executive Summary (max. 1 Seite), die:
1. den Leser **positiv abholt** mit einem warmen Einstieg (2–3 Sätze Fließtext)
2. die **wichtigsten Erkenntnisse** verständlich und ermutigend zusammenfasst
3. **konkrete Zahlen** (Scores, ROI, Payback, Quick-Win-Einsparungen) in Kontext setzt
4. einen **klaren Startpunkt** (Pilot) und nächste Schritte (30/60/90 Tage) definiert
5. die **Top 3 Quick Wins** hervorhebt (falls vorhanden)

**Zielgruppe:** Geschäftsführung, Entscheider:innen (≈ 5 Min Lesezeit)  
**Stil:** freundlich-professionell, ermutigend, klar – keine Marketing-Sprache, aber auch kein trockener Prüfbericht.

---

## 🎯 WICHTIG: Einstieg

- Starte mit 2–3 Sätzen **warmem Fließtext**, der:
  - die Situation des Unternehmens würdigt
  - zeigt, dass die Analyse ernst genommen wurde
  - Mut macht, die nächsten Schritte anzugehen
- Erst danach kommen Zahlen/Fakten.
- Kein „Sie wurden geprüft“-Ton, sondern ein hilfreiches Beratungsgespräch.

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN – niemals in der Executive Summary:

1. **Keine erfundenen Zahlen – nur bereitgestellte Variablen nutzen:**
   - ❌ eigene ROI-/Payback-Berechnungen erfinden
   - ❌ Einsparungen schätzen, die nicht aus den Quick Wins stammen
   - ❌ Scores runden oder „schöner machen“
   - ❌ Prozentverbesserungen ohne klare Quelle nennen

2. **Keine vagen Aussagen:**
   - ❌ „Großes Potenzial für KI-Einsatz“
   - ❌ „deutliche Verbesserungsmöglichkeiten“
   - ❌ „signifikante Effizienzsteigerung erwartet“

3. **Keine generischen Ratschläge:**
   - ❌ „KI-Strategie entwickeln“ ohne Konkretisierung
   - ❌ „Change-Management initiieren“ ohne Bezug auf ein konkretes Projekt
   - ❌ „Pilot-Projekte starten“ ohne Benennung des Piloten

4. **Keine Marketing-Sprache/Übertreibungen:**
   - ❌ „revolutionäre KI-Transformation“
   - ❌ „game-changing opportunity“
   - ❌ „einmalige Chance“

5. **Keine Quick-Wins-Liste, wenn keine Quick Wins vorhanden sind:**
   - ❌ Quick Wins erfinden
   - ✅ Wenn `{CONTEXT_QUICK_WINS}` leer ist → gesamten Quick-Win-Block weglassen.

### ✅ STATTDESSEN – Fokus auf:

1. **Nur bereitgestellte Zahlen verwenden:**
   - ✅ {{score_gesamt}}, {{score_befaehigung}}, {{score_governance}},
      {{score_sicherheit}}, {{score_nutzen}}
   - ✅ {{qw_hours_total}} – Zeitersparnis durch Quick Wins (h/Monat)
   - ✅ {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}
   - ✅ {{PAYBACK_MONTHS}}
   - ✅ {{ROI_12M}} – ROI nach 12 Monaten in Prozent (z. B. 85,0 = 85,0 %)
   - ✅ {{EINSPARUNG_MONAT_EUR}} – Einsparungen/Monat in €

2. **Konkrete Aussagen mit Zahlen:**
   - ✅ „Gesamt-Score: 67/100 – solide Grundlage“
   - ✅ „Quick-Win-Einsparungen: 45 h/Monat = 4.500 €/Monat“
   - ✅ „Amortisation nach 8 Monaten, ROI 12M: 85 %“

3. **Spezifischer Bezug auf {{HAUPTLEISTUNG}}:**
   - ✅ Pilot und Quick Wins immer an die Hauptleistung anbinden
   - ✅ keine Beispiele verwenden, die nicht zum Geschäftsmodell passen

4. **Sachlich-professioneller Ton:**
   - ✅ positive, aber ehrliche Sprache („solide Basis“, „sehr gute Ausgangslage“)
   - ✅ Scores kurz interpretieren (z. B. „exzellente KI-Readiness“)

---

## 💡 BEISPIEL (Struktur, ohne feste Zahlen)

> Dieses Beispiel zeigt Struktur und Ton.  
> Verwende im echten Output **immer die Variablenwerte** – keine Zahlen aus dem Beispiel übernehmen.

```html
<section class="section executive-summary">
  <h2>Executive Summary</h2>

  <!-- 1. Freundlicher Einstieg -->
  <p>
    Vielen Dank, dass Sie sich die Zeit für diese Analyse genommen haben.
    Ihre Antworten zeigen, dass Sie Ihr Geschäft sehr gut kennen und bereits wichtige
    Grundlagen für den Einsatz von KI gelegt haben. Mit diesem Report erhalten Sie
    einen klaren, umsetzbaren Fahrplan, der zu Ihrer aktuellen Situation passt.
  </p>

  <!-- 2. Unternehmensprofil -->
  <p>
    <strong>Ihr Profil:</strong> {{BRANCHE_LABEL}} – {{UNTERNEHMENSGROESSE_LABEL}} – {{BUNDESLAND_LABEL}}<br>
    <strong>Ihre Kern-Leistung:</strong> {{HAUPTLEISTUNG}}
  </p>

  <!-- 3. Kurze Zusammenfassung -->
  <p>
    Die Analyse zeigt eine starke Ausgangsbasis (Score gesamt: {{score_gesamt}}/100).
    Besonders wichtig: Wir konnten konkrete Quick Wins identifizieren, mit denen Sie
    {{qw_hours_total}} Stunden pro Monat einsparen können. Damit haben Sie einen klaren
    Startpunkt für die nächsten 90 Tage.
  </p>

  <!-- 4. Key Facts -->
  <div class="key-facts">
    <h4>Auf einen Blick:</h4>
    <ul>
      <li><strong>KI-Readiness:</strong> {{score_gesamt}}/100 – kurze verbale Einordnung (z. B. „sehr gute Ausgangslage“)</li>
      <li><strong>Quick Wins:</strong> Anzahl &nbsp;– {{qw_hours_total}} h/Monat ≈ {{EINSPARUNG_MONAT_EUR}} €/Monat</li>
      <li><strong>Payback:</strong> {{PAYBACK_MONTHS}} Monate bei {{CAPEX_REALISTISCH_EUR}} € Invest</li>
      <li><strong>ROI (12 Monate):</strong> {{ROI_12M}} %</li>
      <li><strong>Empfohlener Startpunkt:</strong> kurz beschriebener Pilot passend zu {{HAUPTLEISTUNG}}</li>
    </ul>
  </div>

  <!-- 5. KPI-Cards -->
  <div class="kpi-cards">
    <div class="kpi"><div class="kpi-label">Gesamt</div><div class="kpi-value">{{score_gesamt}}</div></div>
    <div class="kpi"><div class="kpi-label">Befähigung</div><div class="kpi-value">{{score_befaehigung}}</div></div>
    <div class="kpi"><div class="kpi-label">Governance</div><div class="kpi-value">{{score_governance}}</div></div>
    <div class="kpi"><div class="kpi-label">Sicherheit</div><div class="kpi-value">{{score_sicherheit}}</div></div>
    <div class="kpi"><div class="kpi-label">Wertschöpfung</div><div class="kpi-value">{{score_nutzen}}</div></div>
  </div>

  <!-- 6. Wirtschaftliche Eckdaten -->
  <h3>Wirtschaftliche Eckdaten</h3>
  <ul>
    <li><strong>Quick-Win-Einsparungen:</strong> {{qw_hours_total}} h/Monat = {{EINSPARUNG_MONAT_EUR}} €/Monat</li>
    <li><strong>Invest (CAPEX):</strong> {{CAPEX_REALISTISCH_EUR}} € ·
        <strong>laufende Kosten (OPEX):</strong> {{OPEX_REALISTISCH_EUR}} €/Monat</li>
    <li><strong>Amortisation:</strong> {{PAYBACK_MONTHS}} Monate ·
        <strong>ROI (12 Monate):</strong> {{ROI_12M}} %</li>
  </ul>

  <!-- 7. Top-3 Quick Wins (nur falls vorhanden) -->
  {% if CONTEXT_QUICK_WINS %}
  <h3>Top-3 Quick Wins (30–60 Tage)</h3>
  <ul>
    <li><strong>[Quick Win 1]</strong> – konkreter Nutzen & h/Monat-Ersparnis aus dem Quick-Win-Kontext</li>
    <li><strong>[Quick Win 2]</strong> – konkreter Nutzen & h/Monat-Ersparnis</li>
    <li><strong>[Quick Win 3]</strong> – konkreter Nutzen & h/Monat-Ersparnis</li>
  </ul>
  {% endif %}

  <!-- 8. Startpunkt/Pilot -->
  <h3>Startpunkt (Pilot)</h3>
  <p>
    <strong>Ziel:</strong> Beschreibe ein konkretes Pilotprojekt, das direkt auf {{HAUPTLEISTUNG}} einzahlt
    (z. B. Automatisierung des Kern-Workflows).<br>
    <strong>Verantwortlich:</strong> Konkrete Rolle(n) (z. B. Geschäftsführung, Fachbereich, externer Tech-Partner).<br>
    <strong>MVP-Umfang:</strong> Kurz beschreiben, was in 30–60 Tagen realistisch implementiert werden kann.<br>
    <strong>Erfolgskriterien:</strong> Messbare KPIs (z. B. X h/Monat weniger, Y % schnellere Durchlaufzeit,
    Z € Kosteneinsparung).<br>
    <strong>Investment:</strong> Bezug auf {{CAPEX_REALISTISCH_EUR}} € und {{OPEX_REALISTISCH_EUR}} €/Monat
    und die Amortisation in {{PAYBACK_MONTHS}} Monaten.
  </p>

  <!-- 9. Nächste Schritte 30/60/90 Tage -->
  <h3>Nächste Schritte (30/60/90 Tage)</h3>
  <ol>
    <li><strong>30 Tage:</strong> Sehr konkrete Aktivitäten (z. B. Tools konfigurieren, Pilot-Use-Case auswählen,
        Verantwortliche benennen).</li>
    <li><strong>60 Tage:</strong> Pilot umsetzen und erste Ergebnisse messen
        (z. B. Anzahl durchgeführter Vorgänge, Zeit- und Kosteneffekte).</li>
    <li><strong>90 Tage:</strong> ROI-Review mit Bezug auf {{ROI_12M}} %, Entscheidung über Skalierung
        und ggf. Ausweitung auf weitere Bereiche.</li>
  </ol>
</section>
