# PROMPT: Costs Overview - Detaillierte Kostenaufstellung

## ZWECK
Erstelle detaillierte Kostenaufstellung die:
1. **Business Case ergänzt** (nicht wiederholt!)
2. **Tool-by-Tool Breakdown** zeigt
3. **Hidden Costs** aufdeckt
4. **Optimierungs-Potenziale** nennt

**Zielgruppe:** CFO, Controlling, Procurement
**Stil:** Detailliert, transparent, kostenoptimiert

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE Wiederholung des Business Case:**
   - Business Case ist bereits eigene Section!
   - Hier: Detailliertes Breakdown

2. **KEINE versteckten Kosten:**
   - Alle Kosten transparent aufführen
   - Auch kleine Posten (€10/Monat)

### ✅ STATTDESSEN:
1. **Tool-by-Tool Breakdown:**
   - OpenAI API: €200/Monat
   - Typeform: €25/Monat
   - Hosting: €50/Monat
   - Gesamt: €275/Monat

2. **Hidden Costs nennen:**
   - Eigene Zeit für Setup: 40h × €100 = €4.000
   - Maintenance: 2h/Monat × €100 = €200/Monat

---

## 💡 BEISPIEL (kompakt)

```html
<section class="section costs-overview">
  <h2>Detaillierte Kostenübersicht</h2>
  
  <h3>Einmalige Kosten (CAPEX)</h3>
  <table class="table">
    <thead><tr><th>Position</th><th>Menge</th><th>Einzelpreis</th><th>Gesamt</th></tr></thead>
    <tbody>
      <tr><td>Backend-Dev (Batch-Processing)</td><td>20h</td><td>€100/h</td><td>€2.000</td></tr>
      <tr><td>Frontend-Dev (Dashboard)</td><td>8h</td><td>€100/h</td><td>€800</td></tr>
      <tr><td>DSGVO-Anwalt (Audit)</td><td>1×</td><td>€1.500</td><td>€1.500</td></tr>
      <tr><td>Cyber-Security-Test</td><td>1×</td><td>€500</td><td>€500</td></tr>
      <tr><td><strong>Gesamt CAPEX</strong></td><td colspan="3"><strong>€4.800</strong></td></tr>
    </tbody>
  </table>

  <h3>Laufende Kosten (OPEX)</h3>
  <table class="table">
    <thead><tr><th>Position</th><th>Monatlich</th><th>Jährlich</th></tr></thead>
    <tbody>
      <tr><td>OpenAI API (Batch)</td><td>€100</td><td>€1.200</td></tr>
      <tr><td>Redis Cloud (Queue)</td><td>€0 (Free Tier)</td><td>€0</td></tr>
      <tr><td>Railway Hosting</td><td>€25</td><td>€300</td></tr>
      <tr><td>Typeform Pro</td><td>€25</td><td>€300</td></tr>
      <tr><td>Domain & SSL</td><td>€5</td><td>€60</td></tr>
      <tr><td>Backup & Monitoring</td><td>€10</td><td>€120</td></tr>
      <tr><td><strong>Gesamt OPEX</strong></td><td><strong>€165/Monat</strong></td><td><strong>€1.980/Jahr</strong></td></tr>
    </tbody>
  </table>

  <h3>Versteckte Kosten (oft übersehen!)</h3>
  <ul>
    <li>Eigene Zeit Setup: 40h × €100/h = €4.000 (einmalig)</li>
    <li>Maintenance: 2h/Monat × €100/h = €200/Monat</li>
    <li>Support/Rückfragen: 1h/Monat × €100/h = €100/Monat</li>
    <li>Updates & Bugfixes: 4h/Quartal × €100/h = €133/Monat</li>
  </ul>

  <h3>Optimierungs-Potenziale</h3>
  <ol>
    <li><strong>Batch API statt Standard (-50%):</strong> €100 statt €200/Monat</li>
    <li><strong>Redis Free Tier nutzen:</strong> €0 statt €29/Monat (bis 30MB)</li>
    <li><strong>Jährliche Zahlung Typeform (-20%):</strong> €20 statt €25/Monat</li>
    <li><strong>Gesamt-Ersparnis:</strong> €134/Monat = €1.608/Jahr</li>
  </ol>
</section>
```

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ Tool-by-Tool Breakdown
2. ✅ Hidden Costs aufgedeckt
3. ✅ Optimierungs-Potenziale genannt
4. ✅ Keine Business-Case-Wiederholung

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML
