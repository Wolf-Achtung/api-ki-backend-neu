# PROMPT: Business Case - ROI & Wirtschaftlichkeit

## ZWECK
Erstelle eine sachliche Business-Case-Analyse die:
1. **Bereitgestellte Zahlen** korrekt interpretiert (KEINE Erfindungen!)
2. **Sensitivitätsanalyse** für ±20% Abweichungen zeigt
3. **Konkrete ROI-Hebelungs-Empfehlungen** gibt (spezifisch für {{HAUPTLEISTUNG}})
4. **Realistische Erwartungen** setzt (keine Schönfärberei!)

**Zielgruppe:** CFO, Geschäftsführung, Investitions-Entscheider
**Stil:** Sachlich, konservativ, transparent - KEINE Marketing-Sprache!

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE Zahlen erfinden oder "optimieren":**
   - ❌ ROI schöner rechnen
   - ❌ Einsparungen hochrechnen ohne Basis
   - ❌ Zusätzliche Revenue-Annahmen einfügen
   
2. **KEINE vagen Hebelungs-Tipps:**
   - ❌ "Prozesse optimieren"
   - ❌ "Effizienz steigern"
   - ❌ "Mehr Automatisierung"

3. **KEINE unrealistischen Versprechungen:**
   - ❌ "Garantierte Amortisation in X Monaten"
   - ❌ "ROI von 500% erreichbar"

### ✅ STATTDESSEN:
1. **Nur bereitgestellte Variablen:**
   - ✅ {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}
   - ✅ {{EINSPARUNG_MONAT_EUR}}, {{PAYBACK_MONTHS}}, {{ROI_12M}}

2. **Spezifische Hebel:**
   - ✅ "Batch API statt Standard API (-50% Kosten)"
   - ✅ "Vorhandene Lizenzen nutzen (Typeform Pro)"
   - ✅ "Stundensatz von €80 auf €100 erhöhen"

---

## 💡 BEISPIEL

**Kontext:**
- CAPEX: €5.000
- OPEX: €500/Monat
- Einsparung: €4.500/Monat
- Payback: 8 Monate
- ROI 12M: 85%

#### ✅ GUT:

```html
<section class="section business-case">
  <h3>Business-Case (Ergebnis)</h3>

  <p><strong>Monatliche Einsparung:</strong> €4.500 (45h × €100/h Stundensatz)<br>
     <strong>CAPEX:</strong> €5.000 (einmalig) · <strong>OPEX:</strong> €500/Monat<br>
     <strong>Amortisation:</strong> 8 Monate · <strong>ROI (12 Monate):</strong> 85%</p>

  <h4>Interpretation</h4>
  <p>Die Quick-Win-Einsparungen von €4.500/Monat decken die laufenden Kosten (OPEX: €500/Monat) 
     mit Faktor 9× und amortisieren die einmalige Investition (CAPEX: €5.000) nach 8 Monaten. 
     Der ROI nach 12 Monaten von 85% basiert ausschließlich auf den bereitgestellten Quick-Win-Zahlen 
     - ohne zusätzliche Revenue-Annahmen (z.B. White-Label-Geschäft).</p>

  <h4>Sensitivität (±20%)</h4>
  <ul>
    <li><strong>Einsparung -20%:</strong> €3.600/Monat → Payback 10 Monate, ROI 12M: 64%. 
        Aussage bleibt positiv.</li>
    <li><strong>Einsparung +20%:</strong> €5.400/Monat → Payback 7 Monate, ROI 12M: 106%. 
        Sehr starkes Ergebnis.</li>
    <li><strong>Kosten +20%:</strong> OPEX €600/Monat → Payback 9 Monate, ROI verschlechtert sich 
        um ~5 Prozentpunkte. Business Case bleibt robust.</li>
  </ul>

  <h4>Empfehlungen zur ROI-Hebelung (konkret)</h4>
  <ol>
    <li><strong>Batch API statt Standard API (-50% OpenAI-Kosten):</strong> Aktuell: €200/Monat, 
        mit Batch: €100/Monat. Spart €1.200/Jahr ohne Qualitätsverlust.</li>
    <li><strong>Stundensatz-Anpassung (€100 → €120):</strong> Bei gleicher Zeitersparnis (45h/Monat) 
        steigt Einsparung auf €5.400/Monat (+20%), Payback 7 Monate, ROI 12M: 106%.</li>
    <li><strong>Vorhandene Tools maximieren:</strong> Typeform Pro bereits vorhanden (€25/Monat), 
        PostgreSQL Free Tier ausreichend (€0), FastAPI Open Source (€0). Keine zusätzlichen Tools kaufen!</li>
    <li><strong>MVP-First statt Big-Bang:</strong> Start mit Batch-Processing (€2.000 CAPEX) statt 
        vollem Gamechanger (€15.000). Nach 4 Monaten ROI-Review, dann Skalierungs-Entscheidung.</li>
  </ol>

  <p><em>Hinweis für Solo-Beratung:</em> Berechnungen basieren auf konservativem €100/h Stundensatz. 
     Bei Premium-Positionierung (€150/h) steigt Einsparung auf €6.750/Monat, Payback 5 Monate.</p>
</section>
```

---

## 🎯 INSTRUKTIONEN

### SCHRITT 1: Zahlen validieren

**Prüfe bereitgestellte Variablen:**
- Ist `{{EINSPARUNG_MONAT_EUR}}` > `{{OPEX_REALISTISCH_EUR}}`? → Positiv!
- Ist `{{PAYBACK_MONTHS}}` < 24? → Akzeptabel!
- Ist `{{ROI_12M}}` > 0? → Break-Even erreicht!

### SCHRITT 2: Sensitivität berechnen

**Formeln (für Interpretation, nicht Output!):**
```
Einsparung -20%: {{EINSPARUNG_MONAT_EUR}} × 0.8
Einsparung +20%: {{EINSPARUNG_MONAT_EUR}} × 1.2
Payback bei -20%: {{CAPEX}} / (Einsparung_neu - {{OPEX}})
```

### SCHRITT 3: Spezifische Hebel finden

**Basierend auf {{HAUPTLEISTUNG}}:**
- **Wenn GPT-Nutzung:** Batch API, Prompt-Optimierung
- **Wenn manuelle Arbeit:** Automatisierung, Templates
- **Wenn Stundensatz:** Premium-Positioning
- **Wenn Tools:** Vorhandene maximieren, keine neuen

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ ALLE Zahlen aus bereitgestellten Variablen
2. ✅ Sensitivität für ±20% berechnet
3. ✅ 3-4 SPEZIFISCHE ROI-Hebel für {{HAUPTLEISTUNG}}
4. ✅ Konservative, ehrliche Interpretation
5. ✅ Format korrekt (deutsches Zahlenformat!)

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML (keine Markdown-Fences!)
