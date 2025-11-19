<!-- roadmap_90d.md - v2.3 GOLD STANDARD+ FIXED -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.
     VERSION: 2.3 GOLD STANDARD+ (Template-Text Problem DEFINITIV gefixt) -->

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
- ❌ NIEMALS: "PMO-Team", "Projektleiter", "Entwicklerteam", "Abteilung"

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

## 🚨 KRITISCHER FIX: KEINE TEMPLATE-ÜBERSCHRIFTEN!

### ❌ DIESE WÖRTER/PHRASEN DÜRFEN NIEMALS ALS ÜBERSCHRIFT ERSCHEINEN:

**VERBOTENE ÜBERSCHRIFTEN (werden vom Validator als Fehler erkannt!):**
- ❌ **"Risiken & Mitigation:"** oder **"Risiken:"** als Heading
- ❌ **"Was wird gebaut:"** als Heading
- ❌ **"Messbarer Erfolg:"** als Heading  
- ❌ **"Team & Ressourcen:"** als Heading
- ❌ **"Abhängigkeiten:"** als Heading

### ✅ SO IST ES RICHTIG - ALLES IN FLIEßTEXT:

**FALSCH (wird als FEHLER markiert):**
```html
<h5>Risiken & Mitigation:</h5>  <!-- ❌ FEHLER! -->
<ul>
  <li>API-Ausfall → Fallback nutzen</li>
</ul>
```

**RICHTIG (im Fließtext eingebettet):**
```html
<p>Mögliche Herausforderungen wie API-Ausfälle werden durch einen Fallback 
auf die Standard-API abgefangen. Das Team plant präventiv alternative 
Lösungswege ein.</p>  <!-- ✅ GUT! -->
```

---

## ✅ DAS RICHTIGE FORMAT: PROSE OHNE TEMPLATE-ARTEFAKTE

**Jedes Deliverable = 3 Absätze in zusammenhängendem Text:**

```html
<div class="deliverable">
  <h4>Phase 1: Batch-Processing MVP implementieren</h4>
  
  <p><strong>Was wir umsetzen:</strong> Die Integration der OpenAI Batch API 
  ermöglicht die parallele Verarbeitung von 50 Assessments gleichzeitig, 
  kombiniert mit einem Redis-Queue-System für die Warteschlangenverwaltung. 
  Nach Batch-Abschluss erfolgt die automatische PDF-Generierung und 
  E-Mail-Versand an die Kunden.</p>
  
  <p><strong>Team und Investment:</strong> Ein Backend-Entwickler (Freelance, 20h) 
  implementiert die Batch-Logic, während ein Frontend-Entwickler (8h) das 
  Admin-Dashboard für die Batch-Überwachung erstellt. Das Budget beträgt 
  €2.000 einmalig, die Tools (OpenAI Batch API und Redis Cloud) nutzen 
  kostenlose Tiers.</p>
  
  <p><strong>Erfolgskriterien:</strong> Die Lösung ist erfolgreich wenn 50 
  Assessments in 2 Stunden verarbeitet werden (statt 10 Stunden einzeln), 
  die API-Kosten um 50% sinken und PDFs automatisch ohne manuellen Eingriff 
  generiert werden. Falls die Batch-API Verzögerungen aufweist, läuft die 
  Standard-API parallel als Backup weiter.</p>
</div>
```

**WICHTIGE REGELN:**
1. ✅ Nutze "Was wir umsetzen" statt "Was wird gebaut"
2. ✅ Nutze "Team und Investment" statt "Team & Ressourcen"
3. ✅ Nutze "Erfolgskriterien" statt "Messbarer Erfolg"
4. ✅ Erwähne Herausforderungen im Fließtext, NICHT als eigene Überschrift
5. ✅ Alles in vollständigen Sätzen, keine Stichpunkt-Listen

---

## 📋 STRUKTUR DER 90-TAGE-ROADMAP

```html
<section class="roadmap-90d">
  <h2>90-Tage Roadmap - Konkrete Umsetzungsplanung</h2>
  
  <p>Ziel: [Konkretes Hauptziel basierend auf {{HAUPTLEISTUNG}}] über 3 Phasen.</p>
  
  <p><strong>Executive Summary:</strong> Phase 1 - Quick Wins (Woche 1-4): 
  [Zusammenfassung]. Phase 2 - Skalierung (Woche 5-8): [Zusammenfassung]. 
  Phase 3 - Gamechanger MVP (Woche 9-12): [Zusammenfassung]. 
  Gesamt-Investment: €X CAPEX + €Y/Monat OPEX | Erwarteter ROI: Z% in 12M</p>
  
  <h3>PHASE 1: Quick Wins (Woche 1-4)</h3>
  
  <div class="deliverable">
    <h4>Woche 1-2: [Konkretes Deliverable 1]</h4>
    <p>[Was wir umsetzen - 2-3 Sätze]</p>
    <p>[Team und Investment - 2-3 Sätze]</p>
    <p>[Erfolgskriterien - 2-3 Sätze, inkl. Umgang mit Herausforderungen]</p>
  </div>
  
  <div class="deliverable">
    <h4>Woche 3-4: [Konkretes Deliverable 2]</h4>
    <p>[Was wir umsetzen - 2-3 Sätze]</p>
    <p>[Team und Investment - 2-3 Sätze]</p>
    <p>[Erfolgskriterien - 2-3 Sätze, inkl. Umgang mit Herausforderungen]</p>
  </div>
  
  <h3>PHASE 2: Skalierung (Woche 5-8)</h3>
  [2-3 Deliverables wie oben]
  
  <h3>PHASE 3: Gamechanger MVP (Woche 9-12)</h3>
  [2-3 Deliverables wie oben]
  
  <h3>Meilenstein-Übersicht</h3>
  <table class="table">
    <thead>
      <tr><th>Woche</th><th>Deliverable</th><th>Team</th><th>Budget</th><th>Key KPIs</th></tr>
    </thead>
    <tbody>
      <tr><td>1-2</td><td>[Name]</td><td>[Wer]</td><td>€X</td><td>[Metrik]</td></tr>
      <!-- etc. -->
    </tbody>
  </table>
  
  <h3>Kritische Erfolgsfaktoren</h3>
  <p><strong>Abhängigkeiten:</strong> Phase 2 benötigt die Ergebnisse aus Phase 1, 
  speziell [konkret]. Die Verfügbarkeit von Freelancern sollte 2 Wochen im 
  Voraus gesichert werden.</p>
  
  <p><strong>Herausforderungen und Lösungsansätze:</strong> Die größte Herausforderung 
  ist [konkret]. Wir begegnen dem durch [konkrete Lösung]. Falls [Szenario], 
  aktivieren wir [Fallback-Plan].</p>
  
  <p><strong>Go/No-Go Entscheidungspunkte:</strong> Ende Woche 4 prüfen wir 
  ob [Kriterium]. Falls nicht erreicht, [Alternative]. Ende Woche 8 evaluieren 
  wir [Metrik] für die Entscheidung über Phase 3.</p>
</section>
```

---

## 🎯 PRE-OUTPUT VALIDATION CHECKLIST

**VOR DEM OUTPUT, PRÜFE:**

1. [ ] **KEINE verbotenen Überschriften?**
   - Suche nach "Risiken & Mitigation:" als Heading → MUSS WEG!
   - Suche nach "Was wird gebaut:" als Heading → MUSS WEG!
   - Suche nach "Team & Ressourcen:" als Heading → MUSS WEG!

2. [ ] **Size-appropriate?**
   - Bei solo: Kein "Projektleiter", keine "Abteilung"
   - Bei team: Kein "PMO-Team"
   - Bei kmu: Alles OK

3. [ ] **Alles in Prose?**
   - Vollständige Sätze statt Stichpunkte
   - Zusammenhängender Text statt Listen

4. [ ] **Konkrete Zahlen?**
   - Budgets in €
   - Zeitangaben in Stunden/Wochen
   - Team-Größen in Personen

---

## 🚨 FINALE WARNUNG

**Der Report-Validator prüft EXAKT auf diese Strings:**
- `"Risiken & Mitigation:"` → CRITICAL ERROR wenn gefunden!
- `"Was wird gebaut:"` → CRITICAL ERROR wenn gefunden!
- `"Team & Ressourcen:"` → CRITICAL ERROR wenn gefunden!

**Diese Phrasen dürfen NUR im Fließtext vorkommen, NIEMALS als Überschrift!**

---

**VERSION:** v2.3 GOLD STANDARD+ (Template-Text definitiv gefixt)  
**AUSGABE:** Valides HTML ohne Template-Artefakte!
