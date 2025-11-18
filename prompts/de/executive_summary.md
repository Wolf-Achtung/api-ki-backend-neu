# PROMPT: Executive Summary - Erste Seite des KI-Readiness Reports

## ZWECK
Erstelle eine prägnante, entscheiderfreundliche Executive Summary (max. 1 Seite) die:
1. Die **wichtigsten Erkenntnisse** aus ALLEN Report-Sections auf einen Blick zusammenfasst
2. **Konkrete Zahlen** (Scores, ROI, Payback, Quick-Win-Einsparungen) prominent platziert
3. Einen **klaren Startpunkt** (Pilot) und nächste Schritte (30/60/90 Tage) definiert
4. Die **Top 3 Quick Wins** hervorhebt (falls vorhanden)

**Zielgruppe:** Geschäftsführung, Entscheider:innen (5 Min Lesezeit)
**Stil:** Professionell, prägnant, motivierend - KEINE Marketing-Sprache!

---

## ⚠️ KRITISCHE REGELN - ZWINGEND BEACHTEN!

### ❌ VERBOTEN - Folgendes NIEMALS in Executive Summary:

1. **KEINE erfundenen Zahlen - NUR bereitgestellte Variablen verwenden:**
   - ❌ Eigene ROI-Berechnungen erfinden
   - ❌ Einsparungen schätzen die nicht aus Quick Wins kommen
   - ❌ Scores runden oder "verschönern"
   - ❌ Prozent-Verbesserungen ohne Quelldaten nennen

2. **KEINE vagen Aussagen - immer konkret:**
   - ❌ "Großes Potenzial für KI-Einsatz"
   - ❌ "Deutliche Verbesserungsmöglichkeiten"
   - ❌ "Signifikante Effizienzsteigerung erwartet"
   - ❌ "Mittelfristig positive Entwicklung"

3. **KEINE generischen Ratschläge - immer spezifisch für Hauptleistung:**
   - ❌ "KI-Schulungen für Mitarbeiter durchführen" (zu generisch!)
   - ❌ "KI-Strategie entwickeln" (was genau?)
   - ❌ "Change-Management initiieren" (für was?)
   - ❌ "Pilot-Projekte starten" (welche konkret?)

4. **KEINE Marketing-Sprache oder Übertreibungen:**
   - ❌ "Revolutionäre KI-Transformation"
   - ❌ "Game-Changing Opportunity"
   - ❌ "Einmalige Chance jetzt nutzen"
   - ❌ "Marktführer werden mit KI"

5. **KEINE Top-3 Quick Wins Liste wenn keine Quick Wins im Context:**
   - ❌ Quick Wins erfinden wenn `{CONTEXT_QUICK_WINS}` leer ist
   - ❌ Generische "Chatbot, Automatisierung, Tool X" auflisten
   - ✅ Wenn keine Quick Wins vorhanden: Ganzer Abschnitt weglassen!

### ✅ STATTDESSEN - Fokus auf:

1. **Nur bereitgestellte Zahlen verwenden:**
   - ✅ {{score_gesamt}}, {{score_befaehigung}}, etc. (exakt wie bereitgestellt)
   - ✅ {{qw_hours_total}}, {{CAPEX_REALISTISCH_EUR}}, {{OPEX_REALISTISCH_EUR}}
   - ✅ {{PAYBACK_MONTHS}}, {{ROI_12M}}
   - ✅ {{EINSPARUNG_MONAT_EUR}}

2. **Konkrete Aussagen mit Zahlen:**
   - ✅ "Score Gesamt: 67/100 - Solide Basis vorhanden"
   - ✅ "Quick-Win-Einsparungen: 45h/Monat = €4.500/Monat"
   - ✅ "Amortisation nach 8 Monaten, ROI 12M: 85%"

3. **Spezifisch für {{HAUPTLEISTUNG}}:**
   - ✅ "Pilot: GPT-4 Batch-Processing für Assessment-Skalierung"
   - ✅ "Ziel: Von 5 auf 50 Assessments/Tag"
   - ✅ "Verantwortlich: CTO + 1 Backend-Dev"

4. **Sachlich-professioneller Ton:**
   - ✅ "Die Analyse zeigt solides Fundament (Score: 67/100)"
   - ✅ "Drei Quick Wins ermöglichen schnelle Erfolge (8 Monate Payback)"
   - ✅ "Empfohlener Start: Automatisierung der Kern-Leistung"

---

## 💡 BEISPIELE: GUT vs. SCHLECHT

### Beispiel-Unternehmen: "KI-Sicherheit.jetzt"
**Kontext:**
- Hauptleistung: GPT-4-basierte KI-Readiness-Assessments
- Score Gesamt: 67/100
- Quick Wins: 3 identifiziert, 45h/Monat Einsparung
- CAPEX: €5.000, OPEX: €500/Monat
- Payback: 8 Monate, ROI 12M: 85%

#### ❌ SCHLECHT (v2.0 - vage & generisch):

```html
<section class="section executive-summary">
  <h2>Executive Summary</h2>
  <p>Das Unternehmen zeigt großes Potenzial für KI-Einsatz. Die Analyse ergab 
     deutliche Verbesserungsmöglichkeiten in allen Bereichen.</p>

  <div class="kpi-cards">
    <div class="kpi"><div class="kpi-value">Gut</div></div>
  </div>

  <h3>Top-3 Quick Wins</h3>
  <ul>
    <li><strong>KI-Chatbot einführen</strong> – Für besseren Kundenservice</li>
    <li><strong>Prozessautomatisierung</strong> – Effizienzsteigerung</li>
    <li><strong>Mitarbeiter-Schulungen</strong> – KI-Kompetenzen aufbauen</li>
  </ul>

  <h3>Startpunkt</h3>
  <p>Wir empfehlen einen KI-Piloten zu starten. Dies wird mittelfristig zu 
     signifikanten Verbesserungen führen.</p>

  <h3>Nächste Schritte</h3>
  <ol>
    <li><strong>30 Tage:</strong> KI-Strategie entwickeln</li>
    <li><strong>60 Tage:</strong> Pilot umsetzen</li>
    <li><strong>90 Tage:</strong> Ergebnisse evaluieren</li>
  </ol>
</section>
```

→ **FEHLER 1:** "Gut" statt konkreter Score (67/100)! Keine Zahlen!
→ **FEHLER 2:** Quick Wins sind ERFUNDEN! Nicht aus Context!
→ **FEHLER 3:** "KI-Strategie entwickeln" ist zu vage! Was konkret?
→ **FEHLER 4:** Keine ROI/Payback-Zahlen erwähnt!
→ **FEHLER 5:** Nicht spezifisch für Hauptleistung (Assessments)!

#### ✅ GUT (v2.1 GOLD - konkret & zahlenbasiert):

```html
<section class="section executive-summary">
  <h2>Executive Summary</h2>
  <p><strong>Unternehmen:</strong> Beratung – Solo-Selbstständig – Berlin<br>
     <strong>Hauptleistung:</strong> GPT-4-basierte KI-Readiness-Assessments für deutsche KMUs</p>

  <p>Diese Kurzfassung fasst die wichtigsten Ergebnisse der KI-Analyse zusammen 
     (Stand: 18.11.2025): Solide KI-Basis vorhanden (Score: 67/100), drei Quick Wins 
     identifiziert mit 45h/Monat Zeitersparnis, klarer Startpunkt durch 
     Automatisierung der Kern-Leistung.</p>

  <div class="kpi-cards">
    <div class="kpi"><div class="kpi-label">Gesamt</div><div class="kpi-value">67</div></div>
    <div class="kpi"><div class="kpi-label">Befähigung</div><div class="kpi-value">72</div></div>
    <div class="kpi"><div class="kpi-label">Governance</div><div class="kpi-value">58</div></div>
    <div class="kpi"><div class="kpi-label">Sicherheit</div><div class="kpi-value">65</div></div>
    <div class="kpi"><div class="kpi-label">Wertschöpfung</div><div class="kpi-value">70</div></div>
  </div>

  <h3>Wirtschaftliche Eckdaten</h3>
  <ul>
    <li><strong>Quick-Win-Einsparungen:</strong> 45 h/Monat = €4.500/Monat (€100/h Stundensatz)</li>
    <li><strong>Invest (CAPEX):</strong> €5.000; <strong>laufende Kosten (OPEX):</strong> €500/Monat</li>
    <li><strong>Amortisation:</strong> 8 Monate; <strong>ROI (12 Monate):</strong> 85%</li>
  </ul>

  <h3>Top-3 Quick Wins (30-60 Tage)</h3>
  <ul>
    <li><strong>GPT-4 Batch-Processing</strong> – 10× Skalierung der Assessment-Kapazität 
        (von 5 auf 50 Reports/Tag); -50% API-Kosten; 15 h/Monat</li>
    <li><strong>Assessment-Template-Bibliothek</strong> – 20 branchen-spezifische Templates 
        für häufigste Use Cases; -60% Erstellungszeit; 20 h/Monat</li>
    <li><strong>LinkedIn-Content aus Insights</strong> – Automatische Generierung von 
        20 Posts pro Assessment; 20× Content-Output; 10 h/Monat</li>
  </ul>

  <h3>Startpunkt (Pilot)</h3>
  <p><strong>Ziel:</strong> Automatisierung des Assessment-Workflows (Typeform → GPT-4 Batch → PDF → E-Mail) 
     für 10× höhere Kapazität. <strong>Verantwortlich:</strong> Geschäftsführer + 1 Backend-Entwickler (Freelance). 
     <strong>MVP-Umfang:</strong> Batch-Verarbeitung von 50 Assessments parallel. 
     <strong>Erfolgskriterien:</strong> 50 Assessments in 2h (statt 10h einzeln), -50% API-Kosten, 
     automatisches PDF ohne manuellen Trigger. <strong>Investment:</strong> €5.000 CAPEX (Entwicklung), 
     €500 OPEX (Tools), Amortisation nach 8 Monaten.</p>

  <h3>Nächste Schritte (30/60/90 Tage)</h3>
  <ol>
    <li><strong>30 Tage:</strong> Batch-Processing MVP entwickeln (OpenAI Batch API + Redis Queue), 
        Freelance-Backend-Dev beauftragen (20h), Admin-Dashboard für Batch-Status aufsetzen.</li>
    <li><strong>60 Tage:</strong> MVP mit ersten 50 Assessments testen, API-Kosten-Ersparnis messen, 
        Template-Bibliothek aus bisherigen 30 Projekten extrahieren.</li>
    <li><strong>90 Tage:</strong> ROI-Review (Target: €4.500/Monat Zeitersparnis erreicht), 
        Skalierungs-Entscheidung für White-Label-Plattform (siehe Gamechanger-Section), 
        DSGVO-Compliance für Batch-Verarbeitung dokumentieren.</li>
  </ol>
</section>
```

**Siehst du den Unterschied?**
- ✅ **Konkrete Scores:** 67/100 statt "Gut"
- ✅ **Echte Quick Wins:** Aus Context, nicht erfunden!
- ✅ **Spezifisch:** Batch-Processing für Assessments, nicht "KI-Strategie"
- ✅ **Alle Zahlen:** ROI, Payback, Einsparungen prominent
- ✅ **Konkrete nächste Schritte:** Backend-Dev beauftragen, nicht "Pilot starten"

---

## 📋 CONTEXT-BLOCK - Integration anderer Report-Sections

**Wichtig:** Die Executive Summary fasst Ergebnisse aus ANDEREN Report-Sections zusammen!

### Verfügbare Context-Variablen:

**1. Unternehmens-Kontext:**
- `{{BRANCHE_LABEL}}` - z.B. "Beratung", "Handel", "Produktion"
- `{{UNTERNEHMENSGROESSE_LABEL}}` - z.B. "Solo-Selbstständig", "Team (6-50 MA)"
- `{{BUNDESLAND_LABEL}}` - z.B. "Berlin", "Bayern", "NRW"
- `{{HAUPTLEISTUNG}}` - z.B. "GPT-4-basierte KI-Readiness-Assessments"

**2. Report-Metadaten:**
- `{{report_date}}` - z.B. "18.11.2025"
- `{{report_year}}` - z.B. "2025"
- `{{kundencode}}` - Unique Identifier
- `{{report_id}}` - Report-ID

**3. KI-Readiness Scores (IMMER vorhanden):**
- `{{score_gesamt}}` - Gesamt-Score (0-100)
- `{{score_befaehigung}}` - Befähigungs-Score (0-100)
- `{{score_governance}}` - Governance-Score (0-100)
- `{{score_sicherheit}}` - Sicherheits-Score (0-100)
- `{{score_nutzen}}` - Nutzen/Wertschöpfungs-Score (0-100)

**4. Business-Case Zahlen (IMMER vorhanden):**
- `{{qw_hours_total}}` - Quick-Win Zeitersparnis in h/Monat
- `{{CAPEX_REALISTISCH_EUR}}` - Einmalige Investition in €
- `{{OPEX_REALISTISCH_EUR}}` - Laufende Kosten in €/Monat
- `{{EINSPARUNG_MONAT_EUR}}` - Monatliche Einsparungen in €
- `{{PAYBACK_MONTHS}}` - Amortisationszeit in Monaten
- `{{ROI_12M}}` - ROI nach 12 Monaten (als Dezimalzahl 0-1, z.B. 0.85 = 85%)

**5. Quick Wins Content (OPTIONAL - kann leer sein!):**
- `{CONTEXT_QUICK_WINS}` - Enthält die generierten Quick Wins aus quick_wins.md
- **WICHTIG:** Wenn leer → Top-3 Quick Wins Section komplett weglassen!
- Wenn vorhanden → Die 3 wichtigsten extrahieren (höchste h/Monat Ersparnis)

**6. Gamechanger Content (OPTIONAL):**
- `{CONTEXT_GAMECHANGER}` - Enthält die generierten Gamechanger aus gamechanger.md
- Für Executive Summary: NUR erwähnen wenn explizit relevant für Pilot

### Wie du Context nutzt:

**Scores interpretieren:**
```
0-40: "Grundlegende Defizite, strukturierter Aufbau notwendig"
41-60: "Ausbaufähige Basis, gezielte Verbesserungen möglich"
61-75: "Solide Grundlage, Optimierungspotenzial vorhanden"
76-90: "Sehr gute Ausgangslage, Feintuning empfohlen"
91-100: "Exzellente KI-Readiness, kontinuierliche Weiterentwicklung"
```

**Quick Wins extrahieren:**
```python
# Pseudo-Code (für dein Verständnis)
if CONTEXT_QUICK_WINS:
    # Extrahiere Top 3 Quick Wins sortiert nach h/Monat
    # Format: <li><strong>Titel</strong> – Nutzen; X h/Monat</li>
else:
    # Ganzer "Top-3 Quick Wins" Abschnitt weglassen!
```

**Pilot definieren:**
- Nutze den Quick Win mit HÖCHSTEM Impact
- ODER: Ersten Gamechanger-MVP wenn kein passender Quick Win
- Muss spezifisch für `{{HAUPTLEISTUNG}}` sein!

---

## 🎯 INSTRUKTIONEN FÜR GPT-4

### SCHRITT 1: Context analysieren (2 Min Denken!)

**BEVOR du die Executive Summary schreibst:**

1. **Sind Quick Wins vorhanden?**
   - Check `{CONTEXT_QUICK_WINS}`
   - Wenn leer → "Top-3 Quick Wins" Section weglassen!
   - Wenn vorhanden → Top 3 nach h/Monat sortiert extrahieren

2. **Welche Scores sind kritisch?**
   - Alle Scores < 60 = Kritische Gaps
   - Governance < 50 = DSGVO/Compliance-Risiko
   - Sicherheit < 50 = Cyber-Risiko
   - → In Executive Summary erwähnen!

3. **Ist der ROI positiv?**
   - ROI_12M > 0 → Positiv darstellen
   - ROI_12M < 0 → Ehrlich kommunizieren, längere Payback-Zeit
   - PAYBACK_MONTHS > 24 → Als langfristiges Investment framen

4. **Was ist der beste Pilot?**
   - Analysiere Quick Wins: Welcher hat höchsten Impact?
   - MUSS für `{{HAUPTLEISTUNG}}` relevant sein
   - MUSS in 30-60 Tagen umsetzbar sein

### SCHRITT 2: Executive Summary schreiben

**HTML-Struktur (ZWINGEND einhalten):**

```html
<section class="section executive-summary">
  <h2>Executive Summary</h2>
  
  <!-- 1. UNTERNEHMEN & HAUPTLEISTUNG -->
  <p><strong>Unternehmen:</strong> {{BRANCHE_LABEL}} – {{UNTERNEHMENSGROESSE_LABEL}} – {{BUNDESLAND_LABEL}}<br>
     <strong>Hauptleistung:</strong> {{HAUPTLEISTUNG}}</p>

  <!-- 2. ZUSAMMENFASSUNG (2-3 Sätze) -->
  <p>[Fasse die Kernaussagen zusammen: Score-Interpretation, Anzahl Quick Wins, 
      Zeitersparnis, Startpunkt. Max. 3 Sätze!]</p>

  <!-- 3. KPI-CARDS (IMMER mit exakten Scores!) -->
  <div class="kpi-cards">
    <div class="kpi"><div class="kpi-label">Gesamt</div><div class="kpi-value">{{score_gesamt}}</div></div>
    <div class="kpi"><div class="kpi-label">Befähigung</div><div class="kpi-value">{{score_befaehigung}}</div></div>
    <div class="kpi"><div class="kpi-label">Governance</div><div class="kpi-value">{{score_governance}}</div></div>
    <div class="kpi"><div class="kpi-label">Sicherheit</div><div class="kpi-value">{{score_sicherheit}}</div></div>
    <div class="kpi"><div class="kpi-label">Wertschöpfung</div><div class="kpi-value">{{score_nutzen}}</div></div>
  </div>

  <!-- 4. WIRTSCHAFTLICHE ECKDATEN (IMMER mit Zahlen!) -->
  <h3>Wirtschaftliche Eckdaten</h3>
  <ul>
    <li><strong>Quick-Win-Einsparungen:</strong> {{qw_hours_total}} h/Monat = {{EINSPARUNG_MONAT_EUR}} €/Monat</li>
    <li><strong>Invest (CAPEX):</strong> {{CAPEX_REALISTISCH_EUR}} €; <strong>laufende Kosten (OPEX):</strong> {{OPEX_REALISTISCH_EUR}} €/Monat</li>
    <li><strong>Amortisation:</strong> {{PAYBACK_MONTHS}} Monate; <strong>ROI (12 Monate):</strong> {{ (ROI_12M*100)|round(1) }} %</li>
  </ul>

  <!-- 5. TOP-3 QUICK WINS (NUR wenn vorhanden!) -->
  {% if CONTEXT_QUICK_WINS %}
  <h3>Top-3 Quick Wins (30-60 Tage)</h3>
  <ul>
    <li><strong>[Titel QW1]</strong> – [Nutzen konkret]; [X h/Monat]</li>
    <li><strong>[Titel QW2]</strong> – [Nutzen konkret]; [Y h/Monat]</li>
    <li><strong>[Titel QW3]</strong> – [Nutzen konkret]; [Z h/Monat]</li>
  </ul>
  {% endif %}

  <!-- 6. STARTPUNKT/PILOT (3-4 Sätze, SEHR konkret!) -->
  <h3>Startpunkt (Pilot)</h3>
  <p><strong>Ziel:</strong> [Was genau wird automatisiert/optimiert? Für welche Hauptleistung?]
     <strong>Verantwortlich:</strong> [Rolle + ggf. externe Ressource]
     <strong>MVP-Umfang:</strong> [Konkrete Beschreibung]
     <strong>Erfolgskriterien:</strong> [Messbare KPIs: X% schneller, Y€ Ersparnis, Z neue Kapazität]
     <strong>Investment:</strong> [CAPEX/OPEX, Amortisation]</p>

  <!-- 7. NÄCHSTE SCHRITTE (IMMER konkret, NIEMALS vage!) -->
  <h3>Nächste Schritte (30/60/90 Tage)</h3>
  <ol>
    <li><strong>30 Tage:</strong> [Konkrete Aktivitäten: Tool installieren, Dev beauftragen, Dashboard aufsetzen, etc.]</li>
    <li><strong>60 Tage:</strong> [MVP-Test mit konkreten Zahlen, Messgrößen tracken]</li>
    <li><strong>90 Tage:</strong> [ROI-Review mit Target-Zahlen, Skalierungs-Entscheidung, Compliance-Check]</li>
  </ol>
</section>
```

### SCHRITT 3: Qualitäts-Check

**Prüfe JEDE dieser Fragen:**

✅ **Zahlen-Test:**
- Sind ALLE Scores exakt wie in Variablen angegeben?
- Sind ROI/Payback/CAPEX/OPEX korrekt formatiert?
- Sind Quick-Win h/Monat korrekt übernommen?
- → Wenn EINE Zahl erfunden: **VERWERFEN & neu!**

✅ **Quick-Wins-Test:**
- Wenn `{CONTEXT_QUICK_WINS}` leer → Ist die ganze Section weg?
- Wenn vorhanden → Sind es die 3 mit höchster h/Monat Ersparnis?
- Sind die Titel & Nutzen aus Context übernommen (nicht erfunden)?
- → Wenn erfunden: **Aus Context extrahieren!**

✅ **Pilot-Spezifität-Test:**
- Bezieht sich Pilot auf `{{HAUPTLEISTUNG}}`?
- Sind Verantwortlichkeiten konkret benannt (nicht "Team")?
- Sind Erfolgskriterien messbar (+X%, Y€, Z Kapazität)?
- → Wenn vage: **Konkretisieren!**

✅ **Nächste-Schritte-Test:**
- Sind alle 3 Schritte KONKRET (nicht "Strategie entwickeln")?
- Enthalten sie messbare Zahlen/Deliverables?
- Sind sie in 30/60/90 Tagen realistisch machbar?
- → Wenn vage: **Konkretisieren!**

✅ **HTML-Format-Test:**
- Ist es valides HTML (keine Markdown-Fences!)?
- Keine `<html>`, `<head>`, `<body>` Tags?
- Alle Variablen mit `{{}}` Syntax?
- → Wenn falsch formatiert: **Korrigieren!**

---

## 🎯 ERFOLGS-KRITERIEN

Eine Executive Summary ist GOLD STANDARD+ wenn:

1. ✅ ALLE Zahlen aus Variablen stammen (KEINE erfundenen Zahlen!)
2. ✅ Top-3 Quick Wins entweder aus Context ODER Section komplett weg
3. ✅ Pilot ist SPEZIFISCH für `{{HAUPTLEISTUNG}}` mit messbaren Zielen
4. ✅ Nächste Schritte sind KONKRET (Aktivitäten, nicht Phasen)
5. ✅ Scores werden interpretiert (nicht nur angezeigt)
6. ✅ HTML-Format korrekt (keine Markdown-Fences!)

**Mindestens 5/6 Kriterien MÜSSEN erfüllt sein!**

---

## 🚨 HÄUFIGE FEHLER - UNBEDINGT VERMEIDEN!

### ❌ Fehler 1: Zahlen erfinden oder schönen
**Schlecht:** Score 67 wird zu "Gut" oder "Über Durchschnitt"
**Warum:** Manipuliert Daten! Zeige exakte Zahl!
**Besser:** "Score Gesamt: 67/100 - Solide Grundlage vorhanden"

### ❌ Fehler 2: Quick Wins erfinden wenn Context leer
**Schlecht:** "Top-3: Chatbot, Automatisierung, Tool X" (ohne Context!)
**Warum:** Erfundene Empfehlungen ohne Basis!
**Besser:** Ganzer Abschnitt weglassen wenn `{CONTEXT_QUICK_WINS}` leer

### ❌ Fehler 3: Vager Pilot ohne Zahlen
**Schlecht:** "Empfohlener Pilot: KI-Tool einführen und testen"
**Warum:** Was genau? Wer? Mit welchem Ziel?
**Besser:** "Pilot: Batch-Processing für 10× Assessment-Skalierung, CTO + 1 Dev, 50 Reports/Tag in 2h"

### ❌ Fehler 4: Generische nächste Schritte
**Schlecht:** "30 Tage: Strategie entwickeln"
**Warum:** Zu vage! Was konkret tun?
**Besser:** "30 Tage: Backend-Dev beauftragen (20h), OpenAI Batch API integrieren, Admin-Dashboard aufsetzen"

### ❌ Fehler 5: Markdown statt HTML
**Schlecht:** Verwendet ```html Fences oder Markdown-Syntax
**Warum:** Output muss reines HTML sein!
**Besser:** Nur HTML Tags, keine Markdown-Syntax

---

## 🔍 ZAHLEN-FORMAT - WICHTIG!

**Deutsch-Format (ZWINGEND!):**
- Tausender-Punkt: 5.000 (nicht 5,000!)
- Dezimal-Komma: 85,5 (nicht 85.5!)
- Prozent mit %: 35,0% (nicht 35.0%!)
- Währung nach Zahl: €5.000 (nicht €5,000!)

**Beispiele:**
```html
✅ RICHTIG:
<li><strong>CAPEX:</strong> 5.000 €</li>
<li><strong>ROI 12M:</strong> 85,5%</li>
<li><strong>Einsparung:</strong> 4.500 €/Monat</li>

❌ FALSCH:
<li><strong>CAPEX:</strong> €5,000</li>
<li><strong>ROI 12M:</strong> 85.5%</li>
<li><strong>Einsparung:</strong> €4,500/month</li>
```

---

**VERSION:** v2.1 GOLD STANDARD+
**ERSTELLT:** 2025-11-18
**FÜR:** KI-Sicherheit.jetzt - Executive Summary (Seite 1)
**ZIEL:** Prägnante, zahlenbasierte 1-Seiten-Zusammenfassung mit konkretem Startpunkt!
**OUTPUT:** Valides HTML (keine Markdown-Fences!)
