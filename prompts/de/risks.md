# PROMPT: Risks & Mitigation - Risiken & Gegenmaßnahmen

## ZWECK
Erstelle eine Risiko-Matrix (5-8 Risiken) die:
1. **Konkrete Risiken** für {{HAUPTLEISTUNG}} identifiziert (nicht generisch!)
2. **Wahrscheinlichkeit** & **Auswirkung** realistisch einschätzt
3. **Konkrete Gegenmaßnahmen** definiert (nicht "mehr testen")
4. **Score-basierte Risiken** priorisiert (z.B. Governance < 60 → DSGVO-Risiko)

**Zielgruppe:** Risk-Owner, Geschäftsführung, Compliance-Verantwortliche
**Stil:** Sachlich, konkret, lösungsorientiert - KEINE Panikmache!

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE generischen Risiken:**
   - ❌ "Mangelnde Akzeptanz bei Mitarbeitern"
   - ❌ "Unzureichende Ressourcen"
   - ❌ "Technische Probleme möglich"
   
2. **KEINE vagen Gegenmaßnahmen:**
   - ❌ "Regelmäßig überwachen"
   - ❌ "Schulungen durchführen"
   - ❌ "Prozesse optimieren"

3. **KEINE Überdramatisierung:**
   - ❌ Wahrscheinlichkeit "Hoch" für seltene Events
   - ❌ Auswirkung "Kritisch" für kleine Probleme

### ✅ STATTDESSEN:
1. **Spezifisch für {{HAUPTLEISTUNG}}:**
   - ✅ "GPT-4 API Ausfall während Assessment-Batch"
   - ✅ "DSGVO-Verstoß bei Kundendaten-Verarbeitung"
   - ✅ "Halluzinationen in generierten Reports"

2. **Konkrete Maßnahmen:**
   - ✅ "Fallback auf Azure OpenAI implementieren"
   - ✅ "DSGVO-Anwalt Audit (€1.500), AVV mit OpenAI"
   - ✅ "Human-Review für alle Reports, Fact-Checking-Prozess"

---

## 💡 BEISPIEL: GUT vs. SCHLECHT

**Kontext:** GPT-4-basierte Assessments, Score Governance 58, Score Sicherheit 65

#### ❌ SCHLECHT:
```html
<tr>
  <td>Technische Probleme</td>
  <td>Mittel</td>
  <td>Hoch</td>
  <td>Regelmäßige Tests durchführen</td>
</tr>
```

#### ✅ GUT:
```html
<tr>
  <td>GPT-4 API Ausfall (>1h) während Batch-Verarbeitung von 50 Assessments</td>
  <td>Mittel (1×/Quartal laut OpenAI SLA)</td>
  <td>Hoch (Lieferverzug, SLA-Breach gegenüber Kunden)</td>
  <td>Azure OpenAI als Fallback (€50/Monat Standby), automatisches Failover implementieren, 
      SLA mit Kunden anpassen (24h statt 2h bei Batch-Processing)</td>
</tr>
```

---

## 🎯 INSTRUKTIONEN

### SCHRITT 1: Score-basierte Risiken identifizieren

**Wenn Score < 60:**
- Governance < 60 → DSGVO/Compliance-Risiko!
- Sicherheit < 60 → Data Breach, Hack-Risiko!
- Befähigung < 60 → Skill-Gap, Qualitäts-Risiko!
- Nutzen < 60 → ROI-Verfehlung-Risiko!

### SCHRITT 2: Hauptleistungs-spezifische Risiken

**Kategorien:**
1. **Technische Risiken** (API-Ausfälle, Bugs, Skalierungsprobleme)
2. **Compliance-Risiken** (DSGVO, AI Act, Branchenregulierung)
3. **Qualitäts-Risiken** (Halluzinationen, Fehlerquoten, Kundenzufriedenheit)
4. **Geschäfts-Risiken** (Vendor Lock-in, Kosten-Explosion, ROI-Verfehlung)
5. **Sicherheits-Risiken** (Data Breach, Unauthorized Access, DDoS)

### SCHRITT 3: HTML-Format

```html
<section class="section risks">
  <h2>Risiken & Gegenmaßnahmen</h2>
  
  <p>Basierend auf den Scores (Governance: {{score_governance}}, Sicherheit: {{score_sicherheit}}) 
     und der Hauptleistung "{{HAUPTLEISTUNG}}" wurden 5-8 Risiken identifiziert mit konkreten 
     Mitigations-Strategien.</p>
  
  <table class="table">
    <thead>
      <tr>
        <th>Risiko</th>
        <th>Wahrscheinlichkeit</th>
        <th>Auswirkung</th>
        <th>Gegenmaßnahme</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>[Konkretes Risiko für Hauptleistung, 1-2 Sätze]</td>
        <td>[Niedrig/Mittel/Hoch mit Begründung]</td>
        <td>[Niedrig/Mittel/Hoch/Kritisch mit Business Impact]</td>
        <td>[Konkrete technische/organisatorische Maßnahmen, Kosten wenn relevant]</td>
      </tr>
      <!-- 4-7 weitere Risiken -->
    </tbody>
  </table>
  
  <p><strong>Empfohlene Priorisierung:</strong> Sofort adressieren: [Risiken mit Wahrscheinlichkeit 
     Mittel/Hoch + Auswirkung Hoch/Kritisch]. Monitoring: [Niedrige Wahrscheinlichkeit]. 
     Akzeptieren: [Niedrige Auswirkung].</p>
</section>
```

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ 5-8 Risiken SPEZIFISCH für {{HAUPTLEISTUNG}}
2. ✅ Score-Gaps < 60 als Risiken erfasst
3. ✅ Wahrscheinlichkeit/Auswirkung realistisch
4. ✅ Gegenmaßnahmen konkret & umsetzbar
5. ✅ Kosten für Maßnahmen genannt wenn relevant

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML (keine Markdown-Fences!)
