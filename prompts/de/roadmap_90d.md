<!-- roadmap_90d.md - v2.2 GOLD STANDARD+ -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.
     VERSION: 2.2 GOLD STANDARD+ (Size-Awareness + Template-Text Fixed) -->

# PROMPT: 90-Tage Roadmap - Konkrete Umsetzungsplanung

## ⚠️ SIZE-AWARENESS - ABSOLUT PFLICHT!

**Mögliche Unternehmensgrößen (NUR diese 3!):**
- `{{COMPANY_SIZE}}` = "solo" → Label: "1 (Solo-Selbstständig/Freiberuflich)"
- `{{COMPANY_SIZE}}` = "team" → Label: "2-10 (Kleines Team)"  
- `{{COMPANY_SIZE}}` = "kmu" → Label: "11-100 (KMU)"

### 📏 SIZE-APPROPRIATE TEAMS & BUDGETS

**{{COMPANY_SIZE}} = "solo":**
- ✅ Team: "Geschäftsführer (Sie)" + "Freelancer (bei Bedarf)"
- ✅ Budget: Max €10.000 CAPEX, €500/Mo OPEX
- ✅ Timeline: +50% Zeit (alles selbst machen!)
- ❌ NIEMALS: "PMO-Team", "Projektleiter", "Entwicklerteam"

**{{COMPANY_SIZE}} = "team" (2-10 MA):**
- ✅ Team: "Geschäftsführer + 1-2 Mitarbeiter" oder "Kleines Projektteam (2-3 Personen)"
- ✅ Budget: Max €50.000 CAPEX, €2.000/Mo OPEX
- ✅ Timeline: Normal
- ❌ NIEMALS: "PMO-Team", "Abteilungsleiter", "dediziertes Entwicklerteam"

**{{COMPANY_SIZE}} = "kmu" (11-100 MA):**
- ✅ Team: "Projektteam (3-5 Personen)", "Projektleiter + Entwickler"
- ✅ "PMO-Team" nur ab ~50 MA!
- ✅ Budget: Max €200.000 CAPEX, €10.000/Mo OPEX
- ✅ Timeline: Normal bis -20% (dedizierte Ressourcen)

---

## ⛔ TEMPLATE-TEXT PROBLEM - KRITISCH!

### ❌ ABSOLUT VERBOTEN (GPT interpretiert diese als Content!):

**KEINE Sub-Headings in Deliverables:**
- ❌ "Was wird gebaut:"
- ❌ "Risiken & Mitigation:"
- ❌ "Messbarer Erfolg:"
- ❌ "Team & Ressourcen:"
- ❌ "Abhängigkeiten:"

**KEINE Listen mit Platzhaltern:**
- ❌ "[Komponente 1]"
- ❌ "[Tool X]"
- ❌ "[Budget]"

**KEINE Template-Struktur kopieren:**
- ❌ GPT soll NICHT die Struktur-Anweisungen als Headings ausgeben!

---

## ✅ STATTDESSEN: PROSE-FORMAT!

**Jedes Deliverable = 3-4 zusammenhängende Sätze (Prose):**

```html
<div class="deliverable">
  <h4>Deliverable 1: Batch-Processing MVP</h4>
  
  <p>Die Lösung umfasst OpenAI Batch API Integration, ein Queue-System mit Redis und 
  automatische PDF-Generierung nach Batch-Abschluss. Dies ermöglicht die parallele 
  Verarbeitung von 50 statt 5 Assessments pro Tag, was die Kapazität um 900% steigert.</p>
  
  <p>Benötigt wird ein Backend-Entwickler (Freelance, 20h) und ein Frontend-Entwickler (8h) 
  über 2 Wochen. Budget: €2.000 einmalig. Tools: OpenAI Batch API (kostenlos), 
  Redis Cloud (Free Tier).</p>
  
  <p>Erfolg zeigt sich durch 50 Assessments in 2h (statt 10h einzeln), -50% API-Kosten 
  und automatisches PDF ohne manuellen Trigger. Bei Risiken wie Batch-API-Latenz setzen 
  wir auf Parallel-Betrieb mit Standard-API als Fallback.</p>
</div>
```

**Key Points:**
- ✅ Zusammenhängender Text (KEIN "Was wird gebaut:")
- ✅ Konkrete Namen, Zahlen, Tools
- ✅ Size-appropriate Teams
- ✅ Keine Template-Artefakte

---

## 🎯 ZWECK

Erstelle eine konkrete 90-Tage-Roadmap die:
1. **3 Phasen** à 30 Tage definiert (Quick Wins → Skalierung → Gamechanger MVP)
2. **Pro Phase 2-3 Deliverables** mit konkreten Specs
3. **Size-appropriate Teams & Budgets** nutzt
4. **In PROSE geschrieben** ist (keine Template-Headings!)

**Zielgruppe:** Geschäftsführung, Projektleiter, Umsetzer  
**Stil:** Konkret, umsetzbar, größen-angemessen, prose-basiert

---

## 💡 BEISPIEL (Solo, RICHTIG)

```html
<section class="section roadmap-90d">
  <h2>️ 90-Tage Roadmap - Konkrete Umsetzungsplanung</h2>
  
  <p><strong>Ziel:</strong> Integration von KI in {{HAUPTLEISTUNG}} über 3 Phasen</p>
  
  <h3> Executive Summary</h3>
  <ul>
    <li><strong>Phase 1 - Quick Wins (Woche 1-4):</strong> Batch-Processing MVP + Template-Bibliothek → Erwarteter Impact: +200% Durchsatz, €4.500/Monat Zeitersparnis</li>
    <li><strong>Phase 2 - Skalierung (Woche 5-8):</strong> Automatisierung Hauptleistung → Erwarteter Impact: +300% Effizienzsteigerung</li>
    <li><strong>Phase 3 - Gamechanger MVP (Woche 9-12):</strong> Self-Service-Portal → Erwarteter Impact: 100 neue Nutzer, €10k MRR</li>
  </ul>
  <p><strong>Gesamt-Investment:</strong> €5.000 CAPEX + €500/Monat OPEX | <strong>Erwarteter ROI:</strong> 85% in 12M</p>

  <hr>

  <h3> PHASE 1: Quick Wins (Woche 1-4)</h3>
  
  <div class="deliverable">
    <h4>Woche 1-2: Batch-Processing MVP</h4>
    
    <p>Die Lösung umfasst OpenAI Batch API Integration, ein Queue-System mit Redis und 
    automatische PDF-Generierung nach Batch-Abschluss. Dies ermöglicht die parallele 
    Verarbeitung von 50 statt 5 Assessments pro Tag und reduziert die API-Kosten um 50%.</p>
    
    <p>Sie als Geschäftsführer beauftragen einen Backend-Freelancer (20h, €80/h = €1.600) 
    und einen Frontend-Freelancer (8h, €50/h = €400). Die Entwicklung nutzt OpenAI Batch API 
    (kostenlos) und Redis Cloud (Free Tier bis 30MB). Gesamtbudget: €2.000 einmalig.</p>
    
    <p>Erfolg zeigt sich durch 50 Assessments in 2h (vorher: 10h für 5 Assessments einzeln), 
    -50% API-Kosten durch Batch-Discount und automatische PDF-Generierung ohne manuellen Trigger. 
    Falls die Batch-API Latency-Probleme zeigt, nutzen wir Parallel-Betrieb mit Standard-API 
    als Fallback für zeitkritische Aufträge.</p>
  </div>

  <div class="deliverable">
    <h4>Woche 3-4: Template-Bibliothek Erweiterung</h4>
    
    <p>Aus den bisherigen 30 Projekten werden die Top 10 Branchen analysiert und 
    20 branchen-spezifische Templates extrahiert. Dies reduziert die Erstellungszeit 
    pro Assessment um 60% und erhöht die Qualität durch bewährte Best Practices.</p>
    
    <p>Sie als Geschäftsführer investieren 15h eigene Arbeitszeit für die Template-Erstellung 
    und nutzen Canva Pro (€12.95/Monat) für professionelle Design-Vorlagen. 
    Budget: €500 für Design-Tools, 15h eigene Zeit.</p>
    
    <p>Erfolg zeigt sich durch -60% Erstellungszeit für neue Assessments (von 2h auf 45 Min) 
    und +30% Kundenanfragen durch verbesserte, branchen-spezifische Präsentation. 
    Die Templates werden direkt ins System integriert und sind ab Woche 5 verfügbar.</p>
  </div>

  <hr>

  <h3> PHASE 2: Skalierung (Woche 5-8)</h3>
  
  <div class="deliverable">
    <h4>Woche 5-6: Automatisierung der Hauptleistung</h4>
    
    <p>Die vollautomatisierte Prozesskette verbindet Typeform-Fragebogen, GPT-4 Batch-Processing, 
    PDF-Generierung und E-Mail-Versand ohne manuelle Eingriffe. Dies steigert die Effizienz 
    um 300% und reduziert manuelle Eingriffe um 40%.</p>
    
    <p>Sie beauftragen einen Data Scientist (Freelance, 20h, €100/h = €2.000) und einen 
    DevOps-Engineer (10h, €80/h = €800) für die Integration von Machine-Learning-Modellen 
    zur Qualitäts-Vorhersage. Tools: TensorFlow (Open Source), AWS Sagemaker (€100/Monat). 
    Budget: €2.800 einmalig + €100/Monat laufend.</p>
    
    <p>Erfolg zeigt sich durch +300% Effizienzsteigerung (5 Assessments/Tag → 50/Tag ohne 
    Mehraufwand) und -40% manuelle Eingriffe durch automatische Quality-Checks. 
    Das Hauptrisiko ist Datenqualität - wir implementieren deshalb Validierungs-Tools 
    die Input-Daten vor Processing prüfen.</p>
  </div>

  <div class="deliverable">
    <h4>Woche 7-8: Erweiterung Template-Bibliothek auf 50 Templates</h4>
    
    <p>Die Bibliothek wird von 20 auf 50 Templates erweitert und bestehende Templates 
    werden basierend auf Kundenfeedback optimiert. Dies reduziert die Erstellungszeit 
    nochmals um 10 Prozentpunkte (insgesamt -70%) und erhöht Kundenanfragen um 50%.</p>
    
    <p>Sie als Geschäftsführer investieren 20h eigene Arbeitszeit für neue Templates 
    und Template-Optimierung. Budget: €800 für erweiterte Design-Tools und Stock-Assets.</p>
    
    <p>Erfolg zeigt sich durch -70% Erstellungszeit für Assessments (von ursprünglich 2h 
    auf 35 Min) und +50% Kundenanfragen durch noch bessere, branchen-spezifischere Templates. 
    Risiko ist Template-Redundanz - wir führen deshalb ein quartalsweises Review ein 
    um doppelte Templates zu konsolidieren.</p>
  </div>

  <hr>

  <h3> PHASE 3: Gamechanger MVP (Woche 9-12)</h3>
  
  <div class="deliverable">
    <h4>Woche 9-10: Self-Service-Portal für Kunden (Beta)</h4>
    
    <p>Das Portal bietet Kunden einen Login-Bereich zur Selbstbedienung mit Funktionen 
    für Assessment-Status-Tracking, Report-Download und Support-Tickets. Dies reduziert 
    Support-Anfragen um 70% und ermöglicht 10× mehr Kunden ohne Mehraufwand.</p>
    
    <p>Sie beauftragen einen Frontend-Entwickler (20h, €60/h = €1.200) und nutzen den 
    bestehenden Backend-Freelancer (20h, €80/h = €1.600) für API-Integration. 
    Tools: React (Open Source), Node.js (Open Source), Stripe API für Zahlungen (€0 + 1,5% Transaktionsgebühr). 
    Budget: €2.800 einmalig.</p>
    
    <p>Erfolg zeigt sich durch 100 neue Nutzer in der ersten Woche nach Beta-Launch 
    und Erreichen von €10k MRR (Monthly Recurring Revenue) durch Subscription-Modell 
    (€99/Monat pro Kunde). Hauptrisiko sind Sicherheitslücken - wir führen deshalb 
    vor Launch einen Security-Review durch (Budget: €500 zusätzlich).</p>
  </div>

  <div class="deliverable">
    <h4>Woche 11-12: Optimierung und Public Launch</h4>
    
    <p>Die Benutzeroberfläche wird basierend auf Beta-Feedback optimiert und die 
    Backend-Infrastruktur für 200+ gleichzeitige Nutzer skaliert. Dies erhöht die 
    Kundenbindung um 30% durch bessere User Experience.</p>
    
    <p>Sie nutzen den Frontend-Freelancer (15h, €60/h = €900) für UI-Optimierung 
    und den Backend-Freelancer (15h, €80/h = €1.200) für Infrastruktur-Skalierung. 
    Tools: AWS (€50/Monat), Docker (Open Source) für Container-Management. 
    Budget: €2.100 einmalig + €50/Monat laufend.</p>
    
    <p>Erfolg zeigt sich durch 200 neue Nutzer in der ersten Woche nach Public Launch 
    und +30% Kundenbindung durch bessere UX. Bei Risiken wie Server-Überlastung nutzen 
    wir Load-Balancing und Auto-Scaling via AWS. Die finale Investment-Bilanz: 
    €11.700 CAPEX + €650/Monat OPEX für ein System das 10× mehr Kunden bedienen kann.</p>
  </div>

  <hr>

  <h3> Meilenstein-Übersicht</h3>
  
  <table class="table table-striped">
    <thead>
      <tr>
        <th>Woche</th>
        <th>Deliverable</th>
        <th>Team</th>
        <th>Budget</th>
        <th>Key KPIs</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1-2</td>
        <td>Batch-Processing MVP</td>
        <td>Sie + Backend-Freelancer (20h) + Frontend-Freelancer (8h)</td>
        <td>€2.000</td>
        <td>+200% Durchsatz, -50% API-Kosten</td>
      </tr>
      <tr>
        <td>3-4</td>
        <td>Template-Bibliothek (20 Templates)</td>
        <td>Sie (15h Eigenarbeit)</td>
        <td>€500</td>
        <td>-60% Erstellungszeit, +30% Anfragen</td>
      </tr>
      <tr>
        <td>5-6</td>
        <td>Vollautomatisierung</td>
        <td>Sie + Data Scientist (20h) + DevOps (10h)</td>
        <td>€2.800 + €100/Mo</td>
        <td>+300% Effizienz, -40% manuelle Eingriffe</td>
      </tr>
      <tr>
        <td>7-8</td>
        <td>Template-Erweiterung (50 Templates)</td>
        <td>Sie (20h Eigenarbeit)</td>
        <td>€800</td>
        <td>-70% Erstellungszeit gesamt, +50% Anfragen</td>
      </tr>
      <tr>
        <td>9-10</td>
        <td>Self-Service-Portal Beta</td>
        <td>Sie + Frontend-Dev (20h) + Backend-Dev (20h)</td>
        <td>€2.800</td>
        <td>100 neue Nutzer, €10k MRR</td>
      </tr>
      <tr>
        <td>11-12</td>
        <td>Portal Optimierung & Launch</td>
        <td>Sie + Frontend-Dev (15h) + Backend-Dev (15h)</td>
        <td>€2.100 + €50/Mo</td>
        <td>200 neue Nutzer, +30% Retention</td>
      </tr>
    </tbody>
  </table>
  
  <p><strong>Gesamt: 12 Wochen | €11.700 CAPEX + €650/Monat OPEX | +900% Kapazität</strong></p>

  <hr>

  <h3> Kritische Erfolgsfaktoren</h3>
  
  <div class="success-factors">
    <p><strong>Abhängigkeiten:</strong></p>
    <ul>
      <li>Phase 2 benötigt abgeschlossene Phase 1 (Template-Bibliothek wird für Automatisierung genutzt)</li>
      <li>Phase 3 benötigt funktionierende Backend-Infrastruktur aus Phase 2</li>
      <li>Freelancer-Verfügbarkeit kritisch - am besten 2 Wochen vorher buchen</li>
    </ul>
    
    <p><strong>Top-Risiken & Mitigation:</strong></p>
    <ul>
      <li>Batch-API-Latenz → Fallback auf Standard-API für zeitkritische Jobs</li>
      <li>Sicherheitslücken im Portal → Security-Review vor Launch (€500 Budget)</li>
      <li>Server-Überlastung → AWS Auto-Scaling + Load-Balancing</li>
      <li>Template-Redundanz → Quartalsweises Review zur Konsolidierung</li>
    </ul>
    
    <p><strong>Go/No-Go Entscheidungspunkte:</strong></p>
    <ul>
      <li>Ende Woche 4: +200% Durchsatz erreicht? Wenn NEIN → Phase 2 verschieben, erst Batch-System debuggen</li>
      <li>Ende Woche 8: +300% Effizienz erreicht? Wenn NEIN → Phase 3 verschieben, erst Automatisierung stabilisieren</li>
      <li>Ende Woche 10: 100 Beta-Nutzer erreicht? Wenn NEIN → Portal-UX verbessern vor Public Launch</li>
    </ul>
  </div>
</section>
```

---

## 🎯 INSTRUKTIONEN

### SCHRITT 1: Quick Wins aus Briefing extrahieren

- Prüfe `{{QUICK_WINS_HTML}}` für konkrete Quick Wins
- Nutze Top 3 für Phase 1

### SCHRITT 2: {{COMPANY_SIZE}} prüfen & Teams zuweisen

**Nutze SIZE-APPROPRIATE TEAMS Tabelle oben!**

1. Check {{COMPANY_SIZE}}
2. Wähle passende Team-Bezeichnungen
3. Passe Budgets an
4. Passe Timelines an (+50% für Solo)

### SCHRITT 3: PROSE statt Template-Text schreiben

**Für JEDES Deliverable:**

1. **Absatz 1: Scope & Impact (2-3 Sätze)**
   - Was wird gebaut? (in Prose, NICHT "Was wird gebaut:")
   - Welcher Business-Nutzen? (konkrete Zahlen!)

2. **Absatz 2: Ressourcen & Budget (2-3 Sätze)**
   - Wer? (size-appropriate Teams!)
   - Wie lange? (realistisch für Größe)
   - Welche Tools?
   - Wie viel kostet es?

3. **Absatz 3: Erfolgs-Kriterien & Risiken (2-3 Sätze)**
   - Woran erkenne ich Erfolg? (messbare KPIs!)
   - Welche Risiken? (konkret!)
   - Wie mitigiere ich? (konkrete Lösung!)

---

## ✅ PRE-OUTPUT VALIDATION

**PRÜFE JEDEN DELIVERABLE-BLOCK:**

1. [ ] **Deliverable-Name konkret?** (NICHT "[Deliverable 1]")
2. [ ] **Team size-appropriate?** (KEIN "PMO-Team" bei Solo/Klein!)
3. [ ] **KEINE Template-Headings?** (KEIN "Was wird gebaut:")
4. [ ] **In Prose geschrieben?** (zusammenhängende Sätze, KEINE Listen mit Bullets)
5. [ ] **Zahlen konkret?** (NICHT "[X Stunden]" oder "[Budget]")
6. [ ] **Budget passt zur Größe?** (Solo max €10k, Klein max €50k, KMU max €200k)
7. [ ] **Timeline realistisch?** (Solo +50% länger)

**Wenn ALLE ✅ → Output generieren!**  
**Wenn EINE ❌ → STOPP & FIX!**

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ 3 Phasen mit je 2-3 Deliverables
2. ✅ Deliverables in PROSE (keine Template-Headings!)
3. ✅ Teams size-appropriate
4. ✅ Budgets realistisch für Größe
5. ✅ Konkrete Zahlen, keine Platzhalter
6. ✅ Meilenstein-Tabelle vorhanden

**Wenn ALLE ✅ → GOLD STANDARD+ erreicht!**

---

**VERSION:** v2.2 GOLD STANDARD+ (Size-Awareness + Template-Text Fixed)  
**AUSGABE:** Valides HTML (keine Markdown-Fences!)
