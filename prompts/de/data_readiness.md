# PROMPT: Data Readiness - Daten-Infrastruktur-Bewertung

## ZWECK
Erstelle eine Daten-Readiness-Analyse die:
1. **Vorhandene Daten bewertet** (Qualität, Struktur, Zugänglichkeit)
2. **Spezifisch für {{HAUPTLEISTUNG}}** ist
3. **Konkrete Gaps** identifiziert
4. **Quick Wins für Daten-Qualität** empfiehlt

**Zielgruppe:** CTO, Data Engineers, Geschäftsführung
**Stil:** Technisch, konkret, lösungsorientiert

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE generische Daten-Theorie:**
   - ❌ "Data Governance Framework etablieren"
   - ❌ "Data Lake aufbauen"
   - ❌ "Master Data Management implementieren"

2. **KEINE Daten-Projekte ohne Nutzen:**
   - ❌ "Alle Daten in Data Warehouse migrieren"
   - ❌ "ETL-Pipelines für alle Systeme bauen"

3. **KEINE Überkomplexität:**
   - ❌ "Enterprise Data Architecture" bei Solo/Klein
   - ❌ "Data Scientists einstellen"

### ✅ STATTDESSEN:
1. **Spezifisch für {{HAUPTLEISTUNG}}:**
   - ✅ "Assessment-Daten: 30 Reports in PostgreSQL, strukturiert"
   - ✅ "Kundenfeedback: Unstrukturiert in E-Mails, nicht nutzbar"
   - ✅ "API-Logs: Nicht vorhanden, OpenAI-Kosten unklar"

2. **Quick Wins für Daten:**
   - ✅ "Logging für API-Costs implementieren (2h)"
   - ✅ "Kundenfeedback in Typeform sammeln (strukturiert)"
   - ✅ "Assessment-Daten für Branchen-Benchmark nutzen"

---

## 💡 BEISPIEL

**Kontext:** GPT-4-Assessments, PostgreSQL, 30 Reports generiert

#### ✅ GUT:

```html
<section class="section data-readiness">
  <h2>Data Readiness</h2>
  
  <p>Bewertung der Daten-Infrastruktur für die Hauptleistung "GPT-4-basierte Assessments":</p>

  <h3>1. Vorhandene Daten (IST-Stand)</h3>
  <table class="table">
    <thead>
      <tr><th>Datenquelle</th><th>Struktur</th><th>Qualität</th><th>Nutzung</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>Assessment-Daten (PostgreSQL)</td>
        <td>Strukturiert (Tabellen: users, assessments, reports)</td>
        <td>Hoch (validiert durch Typeform)</td>
        <td>Report-Generierung, aber nicht Analytics!</td>
      </tr>
      <tr>
        <td>GPT-4 Responses (PostgreSQL)</td>
        <td>Semi-strukturiert (JSON in TEXT-Feld)</td>
        <td>Mittel (enthält auch Halluzinationen)</td>
        <td>Gespeichert aber nicht analysiert</td>
      </tr>
      <tr>
        <td>Kundenfeedback</td>
        <td>Unstrukturiert (E-Mails, Telefonate)</td>
        <td>Niedrig (nicht systematisch erfasst)</td>
        <td>Nicht nutzbar für Verbesserungen</td>
      </tr>
      <tr>
        <td>API-Costs (OpenAI)</td>
        <td>Externe Plattform (OpenAI-Dashboard)</td>
        <td>Mittel (nur Gesamt-Kosten, kein Detail)</td>
        <td>Manuelles Tracking, kein Monitoring</td>
      </tr>
    </tbody>
  </table>

  <h3>2. Daten-Gaps & Impact</h3>
  <ul>
    <li><strong>Gap 1:</strong> Keine Analytics auf vorhandenen Assessment-Daten → 
        Können Branchen-Trends nicht erkennen, White-Label-Partner erhalten keine Benchmarks</li>
    <li><strong>Gap 2:</strong> Kundenfeedback unstrukturiert → Können Qualität nicht systematisch verbessern, 
        wissen nicht welche Empfehlungen gut ankommen</li>
    <li><strong>Gap 3:</strong> API-Costs nicht detailliert getrackt → Wissen nicht welche Prompts teuer sind, 
        können Batch-Ersparnis nicht messen</li>
    <li><strong>Gap 4:</strong> GPT-4 Responses nicht validiert → Halluzinationen werden erst manuell 
        beim Review entdeckt, könnten automatisch erkannt werden</li>
  </ul>

  <h3>3. Quick Wins für Daten-Qualität (30-60 Tage)</h3>
  <ol>
    <li><strong>API-Cost-Logging implementieren (4h, €0):</strong> FastAPI-Middleware die 
        OpenAI-Requests loggt (Prompt-Length, Model, Cost, Response-Time) → PostgreSQL-Tabelle. 
        Nutzen: Wissen wo Kosten entstehen, Batch-Ersparnis messbar.</li>
    
    <li><strong>Feedback-Formular in jedem Report-PDF (2h, €0):</strong> QR-Code → Typeform 
        mit 3 Fragen: "Wie hilfreich? (1-5)", "Was fehlt?", "Würden Sie weiterempfehlen?". 
        Nutzen: Strukturiertes Feedback, NPS trackbar.</li>
    
    <li><strong>Assessment-Analytics-Dashboard (8h, €0 mit Metabase):</strong> Metabase auf 
        PostgreSQL connecten, Dashboards: Top-Branchen, Avg-Scores, Zeitverläufe. 
        Nutzen: Branchen-Insights für Marketing, White-Label-Partner erhalten Benchmarks.</li>
    
    <li><strong>GPT-Response-Validator (12h, €50/Monat GPT-4):</strong> Zweiter GPT-Call: 
        "Prüfe Report auf Halluzinationen, faktische Fehler, widersprüchliche Aussagen". 
        Nutzen: Qualitäts-Sicherung vor manuellem Review, -50% Review-Zeit.</li>
  </ol>

  <h3>4. Langfristige Daten-Strategie (Monate 6-12)</h3>
  <ul>
    <li><strong>Branchen-Benchmark-Datenbank:</strong> Anonymisierte Assessment-Daten aggregieren, 
        "KI-Readiness-Index" pro Branche berechnen, an Investoren/Medien verkaufen (€10k/Jahr/Kunde)</li>
    <li><strong>Predictive Analytics:</strong> Aus 500+ Assessments ML-Modell trainieren: 
        "Welche Unternehmen haben höchsten ROI mit KI?" → Bessere Quick-Win-Empfehlungen</li>
  </ul>
</section>
```

---

## 🎯 INSTRUKTIONEN

### SCHRITT 1: Daten-Inventar

**Welche Daten fallen bei {{HAUPTLEISTUNG}} an?**
- Kundendaten?
- Transaktionsdaten?
- Produktdaten?
- Nutzungsdaten?
- Feedback-Daten?

### SCHRITT 2: Daten-Bewertung

**Für jede Datenquelle:**
- **Struktur:** Strukturiert / Semi-strukturiert / Unstrukturiert
- **Qualität:** Hoch / Mittel / Niedrig
- **Nutzung:** Aktiv genutzt / Gespeichert aber ungenutzt / Nicht erfasst

### SCHRITT 3: Gap-Analyse

**Welche Daten fehlen für:**
- Bessere Quick Wins?
- Gamechanger-Geschäftsmodelle (z.B. Data-as-a-Service)?
- Qualitäts-Verbesserung?
- Kosten-Optimierung?

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ Daten-Inventar spezifisch für {{HAUPTLEISTUNG}}
2. ✅ Gaps konkret benannt mit Impact
3. ✅ Quick Wins für Daten-Qualität (< 60 Tage)
4. ✅ Langfrist-Strategie (Data-as-a-Service?)
5. ✅ Realistisch für Unternehmensgröße

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML (keine Markdown-Fences!)
