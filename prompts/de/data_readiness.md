
---

## 4️⃣ `data_readiness.md` – jetzt size- & tool-sensitiv

Hier habe ich eine neue Section „SIZE- & TOOL-AWARENESS“ ergänzt, damit bei `solo` + „keine Tools“ nicht wieder CRM-Text entsteht.  

```md
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

## ⚠️ SIZE- & TOOL-AWARENESS (PFLICHT)

**Unternehmensgröße (aus Briefing):**
- Solo-Selbstständig/Freiberuflich
- 2–10 (Kleines Team)
- 11–100 (KMU)

**Tools (aus Briefing, z.B. `vorhandene_tools`):**
- z.B. "keine", "Notion", "Excel", "Hubspot", "Pipedrive", …

### Regeln:

- 🔹 **Solo + "keine" Tools**  
  - ❌ KEIN CRM-System erfinden ("Salesforce", "Hubspot" etc.), wenn nichts dergleichen im Briefing steht.  
  - ❌ KEIN Data Lake / Data Warehouse vorschlagen.  
  - ✅ Datenquellen sind typischerweise: E-Mails, einfache Listen (Excel/Sheets/Notion), Formular-Exports (z.B. Typeform), PDFs.  
  - ✅ Quick Wins: einfache Strukturierung (Liste, Tags, ein Dashboard), kein großer Architektur-Wurf.

- 🔹 **Kleines Team (2–10) ohne explizites CRM**  
  - ✅ Du darfst von geteilten Dateien/Ordnern, einfachen Tools (Notion, Trello, Google Drive) ausgehen.  
  - ❌ Kein ausgewachsenes CRM behaupten, wenn im Briefing keins steht.  
  - ✅ Wenn im Kontext ein Tool genannt ist (z.B. Hubspot), nutze GENAU dieses.

- 🔹 **KMU (11–100) mit CRM im Briefing**  
  - ✅ CRM-System (z.B. "Kundendaten (CRM-System)") ist OK, ABER immer am Briefing ausrichten.  
  - ✅ Daten-Architektur darf etwas ambitionierter sein (Dashboards, BI-Tool).  
  - ❌ Keine Enterprise-Übertreibung (kein "Data Lake" o.Ä.), wenn nicht explizit erwähnt.

- 🔹 **Allgemein**  
  - Schreibe IMMER so, dass es zur Kombination aus Unternehmensgröße und tatsächlichen Tools im Briefing passt.  
  - Wenn du unsicher bist, wähle die **einfachere** Variante (Listen, Logs, einfache Dashboards) statt Enterprise-Stack.

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

**Kontext:** GPT-4-Assessments, einfache DB/Logs, Solo oder kleines Team

```html
<section class="section data-readiness">
  <h2>Data Readiness</h2>
  
  <p>Bewertung der Daten-Infrastruktur für die Hauptleistung "{{HAUPTLEISTUNG}}":</p>

  <h3>1. Vorhandene Daten (IST-Stand)</h3>
  <table class="table">
    <thead>
      <tr><th>Datenquelle</th><th>Struktur</th><th>Qualität</th><th>Nutzung</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>Assessment-Daten (z.B. PostgreSQL / Tabellen / Exporte)</td>
        <td>Strukturiert (z.B. Tabellen: users, assessments, reports)</td>
        <td>Hoch (validiert durch Formular-Logik)</td>
        <td>Genutzt für Report-Generierung, aber kaum für Analytics</td>
      </tr>
      <tr>
        <td>GPT-4 Responses</td>
        <td>Semi-strukturiert (JSON/Textfelder)</td>
        <td>Mittel (enthält auch Halluzinationen)</td>
        <td>Gespeichert, aber nicht systematisch ausgewertet</td>
      </tr>
      <tr>
        <td>Kundenfeedback</td>
        <td>Unstrukturiert (E-Mails, Telefonnotizen)</td>
        <td>Niedrig (nicht systematisch erfasst)</td>
        <td>Nur ad hoc für Verbesserungen genutzt</td>
      </tr>
      <tr>
        <td>API-Kosten (OpenAI)</td>
        <td>Externe Plattform (Dashboard), einfache Logs</td>
        <td>Mittel (Gesamtwerte, wenig Detail)</td>
        <td>Manuell geprüft, kein automatisches Monitoring</td>
      </tr>
    </tbody>
  </table>

  <h3>2. Daten-Gaps & Impact</h3>
  <ul>
    <li><strong>Gap 1:</strong> Keine Analytics auf vorhandenen Assessment-Daten → 
        Branchen-Trends bleiben unsichtbar, Potenzial für Benchmarks ungenutzt.</li>
    <li><strong>Gap 2:</strong> Kundenfeedback unstrukturiert → Qualität kann nicht systematisch verbessert werden.</li>
    <li><strong>Gap 3:</strong> API-Kosten nur grob sichtbar → Teure Prompts und Einsparpotenziale bleiben verborgen.</li>
  </ul>

  <h3>3. Quick Wins für Daten-Qualität (30-60 Tage)</h3>
  <ol>
    <li><strong>API-Cost-Logging implementieren (4h, €0):</strong> Middleware oder Logging-Layer, der 
        OpenAI-Requests (Prompt-Länge, Modell, Kosten, Response-Time) in einer Tabelle oder Datei erfasst. 
        <strong>Nutzen:</strong> Transparenz über Kosten, Batch-Ersparnis messbar.</li>
    
    <li><strong>Feedback-Formular in jedem Report-PDF verlinken (2h, €0):</strong> QR-Code oder Link zu einem 
        kurzen Formular mit 3 Fragen ("Wie hilfreich? (1-5)", "Was fehlt?", "Würden Sie weiterempfehlen?"). 
        <strong>Nutzen:</strong> Strukturiertes Feedback, NPS und Zufriedenheit trackbar.</li>
    
    <li><strong>Einfaches Analytics-Dashboard (8h, €0 mit z.B. Metabase/Looker Studio):</strong> 
        Verbindung auf bestehende Datenbank oder Exporte, Dashboards: Top-Branchen, Durchschnitts-Scores, Zeitverläufe. 
        <strong>Nutzen:</strong> Sofortige Insights für Marketing und Produkt-Entscheidungen.</li>
    
    <li><strong>GPT-Response-Validator (12h):</strong> Zweiter GPT-Call, der Reports auf offensichtliche 
        Widersprüche und Halluzinationen prüft. <strong>Nutzen:</strong> Qualitätssicherung vor manuellem Review, 
        reduzierte Review-Zeit.</li>
  </ol>

  <h3>4. Langfristige Daten-Strategie (Monate 6-12)</h3>
  <ul>
    <li><strong>Branchen-Benchmark-Datenbank:</strong> Anonymisierte Assessment-Daten aggregieren, 
        "KI-Readiness-Index" pro Branche berechnen und als Produkt (z.B. für Partner, Medien, Investoren) anbieten.</li>
    <li><strong>Predictive Analytics:</strong> Ab einer kritischen Masse (z.B. 200+ Assessments) 
        ein Modell trainieren: "Welche Unternehmen haben den höchsten ROI mit KI?" → Bessere Quick-Win-Empfehlungen.</li>
  </ul>
</section>
