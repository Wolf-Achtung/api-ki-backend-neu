# PROMPT: Roadmap 90 Tage - Konkrete Umsetzungs-Roadmap

## ZWECK
Erstelle eine detaillierte 90-Tage-Roadmap mit **konkreten Deliverables und messbaren Meilensteinen** - nicht mit generischen Phasen wie "Analyse" oder "Konzeption". Jeder Meilenstein MUSS ein greifbares Ergebnis liefern.

---

## ⚠️ KRITISCHE REGELN - ZWINGEND BEACHTEN!

### ❌ VERBOTEN - Folgendes NIEMALS in Roadmap aufnehmen:

1. **KEINE generischen Phasen ohne konkretes Deliverable:**
   - ❌ "Woche 1-2: Analyse der Ist-Situation"
   - ❌ "Woche 3-4: Konzeptentwicklung"
   - ❌ "Woche 5-6: Evaluierung verschiedener Tools"
   - ❌ "Woche 7-8: Strategie-Workshop mit Team"

2. **KEINE Entwicklung von Dingen die schon existieren:**
   - ❌ "Fragebogen-Entwicklung" wenn Kunde schon Fragebogen hat
   - ❌ "CRM-Auswahl" wenn Kunde bereits CRM nutzt
   - ❌ "Website-Konzeption" wenn Kunde bereits Website hat
   - ❌ "API-Integration planen" wenn API bereits integriert ist

3. **KEINE vagen Erfolgs-Kriterien:**
   - ❌ "Erfolg: Bessere Effizienz erreicht"
   - ❌ "KPI: Zufriedene Kunden"
   - ❌ "Ziel: Optimierte Prozesse"
   - ❌ "Messung: Qualitative Verbesserung"

4. **KEINE Meilensteine ohne Ressourcen/Kosten:**
   - ❌ Nur "Was" ohne "Wer", "Wie viel", "Womit"
   - ❌ Keine Budget-Angaben
   - ❌ Keine Team-Allokation
   - ❌ Keine Tool-Kosten

### ✅ STATTDESSEN - Fokus auf:

1. **Konkrete Deliverables mit messbaren Ergebnissen:**
   - ✅ "Woche 1-2: Batch-Processing MVP → 50 statt 5 Reports/Tag"
   - ✅ "Woche 3-4: 20 Branchen-Templates → -60% Erstellungszeit"
   - ✅ "Woche 5-6: Self-Service-Portal → 100 Sign-ups in Woche 1"

2. **Skalierung & Automatisierung des Bestehenden:**
   - ✅ "10× API-Durchsatz durch Batch-Processing"
   - ✅ "Template-Bibliothek aus 50 bisherigen Projekten"
   - ✅ "Automatisches Reporting statt manueller Reports"

3. **Messbare KPIs für jeden Meilenstein:**
   - ✅ "+200% Durchsatz", "-50% Zeit", "100 neue Nutzer"
   - ✅ "€10k MRR erreicht", "5 Partner onboardet"
   - ✅ "1000 API-Calls/Tag", "NPS 45+ erreicht"

4. **Vollständige Ressourcen-Planung:**
   - ✅ Team: 1× Dev (20h/Woche), 1× Designer (5h/Woche)
   - ✅ Budget: €2.500 Tools, €5.000 Entwicklung
   - ✅ Tools: Make.com (€99/Monat), Supabase (Free Tier)

---

## 💡 BEISPIELE: GUT vs. SCHLECHT

### Beispiel-Unternehmen: "KI-Sicherheit.jetzt"
**Aktueller Stand:** Manuelle GPT-4-Assessments, 5 Reports/Tag Kapazität, bereits: Fragebogen, GPT-4 API, PostgreSQL

#### ❌ SCHLECHT (v2.0 - generische Phasen):

```markdown
## Woche 1-2: Analyse & Konzeption
**Ziel:** Ist-Situation analysieren und Konzept entwickeln
**Aktivitäten:**
- Workshop mit Team zur Anforderungsanalyse
- Evaluierung verschiedener KI-Tools
- Erstellung eines Konzeptpapiers
**Erfolg:** Konzept steht
```
→ **FEHLER:** Keine konkreten Deliverables! Was genau wird gebaut?
→ **FEHLER:** "Konzept entwickeln" für System das schon läuft? Redundant!
→ **FEHLER:** Keine messbaren KPIs! Was bedeutet "Konzept steht"?

#### ✅ GUT (v2.1 GOLD - konkrete Deliverables):

```markdown
## Woche 1-2: Batch-Processing MVP für 10× Skalierung

**Deliverable:** Funktionierende Batch-Verarbeitung von 50 Assessments parallel

**Was wird gebaut:**
- OpenAI Batch API Integration (ersetzt einzelne API-Calls)
- Queue-System für wartende Assessments (Redis)
- Automatisches PDF-Generation nach Batch-Abschluss
- Admin-Dashboard: Batch-Status live verfolgen

**Messbarer Erfolg:**
- ✅ 50 Assessments in 2h verarbeitet (statt 10h einzeln)
- ✅ -50% API-Kosten (Batch API günstiger als Standard)
- ✅ Automatisches PDF-Generation ohne manuellen Trigger

**Ressourcen:**
- Team: 1× Backend-Dev (20h), 1× Frontend-Dev (8h)
- Budget: €0 (nutzt bestehende OpenAI API, Redis Free Tier)
- Tools: OpenAI Batch API, Redis Cloud (Free), bestehende FastAPI

**Risiken & Mitigation:**
- Risiko: Batch API Latency (24h statt 2 Min) → Parallel-Betrieb mit Standard-API für Express-Service
- Risiko: Redis Downtime → Fallback auf PostgreSQL Queue

**Abhängigkeiten:** Keine - nutzt bestehende Infrastruktur
```

**Siehst du den Unterschied?**
- ✅ **Konkretes Deliverable:** "Batch-Processing MVP" statt "Analyse-Phase"
- ✅ **Messbare KPIs:** "50 Assessments in 2h, -50% Kosten" statt "Konzept steht"
- ✅ **Vollständige Ressourcen:** Team, Budget, Tools konkret benannt
- ✅ **Risiko-Management:** Potenzielle Probleme + Lösungen genannt

---

## 🎯 INSTRUKTIONEN FÜR GPT-4

Du erhältst folgende Variablen:
- `{{BRANCHE}}` - z.B. "Beratung", "Handel", "Produktion"
- `{{MITARBEITER}}` - z.B. "Solo-Selbstständig", "Team (6-50 MA)"
- `{{HAUPTLEISTUNG}}` - z.B. "KI-Readiness-Assessments", "CNC-Frästeile"
- `{{TOOLS_AKTUELL}}` - z.B. "GPT-4, Typeform, PostgreSQL"
- `{{QUICK_WINS}}` - Die 6 Quick Wins aus vorherigem Schritt
- `{{GAMECHANGER}}` - Die 3 Gamechanger aus vorherigem Schritt

### SCHRITT 1: Priorisierung der Maßnahmen (3 Min Denken!)

**BEVOR du die Roadmap erstellst, priorisiere:**

1. **Welche Quick Wins haben höchste Impact/Aufwand-Ratio?**
   - Filtere die Top 3-4 Quick Wins aus `{{QUICK_WINS}}`
   - Fokus auf: Skalierung der Hauptleistung, nicht Nebenaufgaben

2. **Welcher Gamechanger ist realistisch in 90 Tagen startbar?**
   - Meist ist nur 1 Gamechanger in 90d machbar (MVP-Phase)
   - Wähle den mit schnellstem Break-Even

3. **Was existiert bereits und darf NICHT neu entwickelt werden?**
   - Check `{{TOOLS_AKTUELL}}` genau!
   - Fokus: Skalierung des Bestehenden, nicht Neu-Entwicklung

### SCHRITT 2: 90-Tage-Struktur definieren

**Typischer 90-Tage-Plan:**

```
🏃 QUICK WINS PHASE (Woche 1-4)
→ 3-4 Quick Wins parallel umsetzen
→ Schnelle Erfolge zeigen, Team motivieren
→ Revenue-Impact innerhalb von 4 Wochen

🚀 SKALIERUNGS-PHASE (Woche 5-8)
→ Automatisierung der Hauptleistung
→ Template-Bibliotheken, Batch-Processing
→ 2-5× Durchsatz erreichen

💎 GAMECHANGER MVP (Woche 9-12)
→ Erste Version des neuen Geschäftsmodells
→ 10-20 Beta-Kunden/Partner onboarden
→ Break-Even-Pfad validieren
```

### SCHRITT 3: Jede Woche als konkreten Meilenstein definieren

**Für JEDE Woche (oder 2-Wochen-Sprint):**

```markdown
## Woche [X-Y]: [Konkretes Deliverable - max. 8 Wörter]

**Deliverable:** [Was GENAU wird gebaut/geliefert? 1 Satz]

**Was wird gebaut:**
- [Feature/System 1 - technisch konkret]
- [Feature/System 2 - technisch konkret]
- [Feature/System 3 - technisch konkret]

**Messbarer Erfolg:**
- ✅ [KPI 1 mit Zahl: "+200% Durchsatz"]
- ✅ [KPI 2 mit Zahl: "-50% Zeit"]
- ✅ [KPI 3 mit Zahl: "100 neue User"]

**Ressourcen:**
- Team: [Rolle + Stunden, z.B. "1× Dev (20h)"]
- Budget: [€-Betrag oder "€0"]
- Tools: [Konkrete Tools mit Preisen]

**Risiken & Mitigation:**
- Risiko: [Potentielles Problem] → [Lösungsansatz]

**Abhängigkeiten:** [Von welchen vorherigen Meilensteinen hängt das ab?]
```

### SCHRITT 4: Qualitäts-Check JEDES Meilensteins

**Bevor du einen Meilenstein ausgibst, prüfe:**

✅ **Deliverable-Test:**
- Ist das ein **konkretes, greifbares Ergebnis**?
- Oder eine vage Phase wie "Analyse" oder "Konzeption"?
- → Wenn vage: **Konkretisieren oder verwerfen!**

✅ **Redundanz-Test:**
- Wird etwas entwickelt das in `{{TOOLS_AKTUELL}}` schon existiert?
- Wird ein System neu gebaut das der Kunde schon hat?
- → Wenn redundant: **Fokus auf Skalierung des Bestehenden!**

✅ **Messbarkeits-Test:**
- Gibt es **konkrete KPIs mit Zahlen**?
- Oder nur vage Formulierungen wie "bessere Effizienz"?
- → Wenn nicht messbar: **Konkrete Zahlen hinzufügen!**

✅ **Ressourcen-Test:**
- Sind Team, Budget und Tools konkret benannt?
- Oder fehlen diese Angaben komplett?
- → Wenn fehlend: **Vollständige Ressourcen-Planung ergänzen!**

✅ **Realismus-Test:**
- Ist das in der angegebenen Zeit machbar?
- Oder zu ambitioniert für die Wochenzahl?
- → Wenn unrealistisch: **Scope reduzieren oder Zeit verlängern!**

---

## 📋 OUTPUT-FORMAT

```markdown
# 🗓️ 90-Tage Roadmap - Konkrete Umsetzungsplanung

> **Ziel:** In 90 Tagen die Hauptleistung skalieren und ein neues Geschäftsmodell-MVP launchen.

---

## 📊 Executive Summary

**Phase 1 - Quick Wins (Woche 1-4):**
- [3-4 Quick Wins]
- Erwarteter Impact: [Konkrete Zahlen]

**Phase 2 - Skalierung (Woche 5-8):**
- [Automatisierungs-Maßnahmen]
- Erwarteter Impact: [Konkrete Zahlen]

**Phase 3 - Gamechanger MVP (Woche 9-12):**
- [Neues Geschäftsmodell]
- Erwarteter Impact: [Konkrete Zahlen]

**Gesamt-Investment:** [€X Budget] | **Erwarteter ROI:** [X× in 12 Monaten]

---

## 🏃 PHASE 1: Quick Wins (Woche 1-4)

### Woche 1-2: [Deliverable 1]
[Kompletter Meilenstein nach Schema]

---

### Woche 3-4: [Deliverable 2]
[Kompletter Meilenstein nach Schema]

---

## 🚀 PHASE 2: Skalierung (Woche 5-8)

### Woche 5-6: [Deliverable 3]
[Kompletter Meilenstein nach Schema]

---

### Woche 7-8: [Deliverable 4]
[Kompletter Meilenstein nach Schema]

---

## 💎 PHASE 3: Gamechanger MVP (Woche 9-12)

### Woche 9-10: [Deliverable 5]
[Kompletter Meilenstein nach Schema]

---

### Woche 11-12: [Deliverable 6]
[Kompletter Meilenstein nach Schema]

---

## 📈 Meilenstein-Übersicht

| Woche | Deliverable | Team | Budget | KPIs |
|-------|-------------|------|--------|------|
| 1-2 | [Name] | [Rollen] | [€] | [Zahlen] |
| 3-4 | [Name] | [Rollen] | [€] | [Zahlen] |
| 5-6 | [Name] | [Rollen] | [€] | [Zahlen] |
| 7-8 | [Name] | [Rollen] | [€] | [Zahlen] |
| 9-10 | [Name] | [Rollen] | [€] | [Zahlen] |
| 11-12 | [Name] | [Rollen] | [€] | [Zahlen] |

**Gesamt:** [X Wochen] | [€Y Budget] | [Z erwarteter Impact]

---

## 🎯 Kritische Erfolgsfaktoren

**Abhängigkeiten:**
- [Kritische Abhängigkeit 1]
- [Kritische Abhängigkeit 2]

**Top-Risiken:**
- [Risiko 1] → [Mitigation]
- [Risiko 2] → [Mitigation]

**Go/No-Go Entscheidungspunkte:**
- Ende Woche 4: [Kriterium für Weitermachen]
- Ende Woche 8: [Kriterium für Gamechanger-Start]
```

---

## 🎯 ERFOLGS-KRITERIEN

Eine Roadmap ist GOLD STANDARD+ wenn:

1. ✅ Jeder Meilenstein hat ein **konkretes Deliverable** (nicht "Analyse-Phase")
2. ✅ Jeder Meilenstein hat **messbare KPIs mit Zahlen** (+X%, -Y€, Z neue User)
3. ✅ Jeder Meilenstein hat **vollständige Ressourcen** (Team, Budget, Tools)
4. ✅ Keine **redundante Entwicklung** von Dingen die in `{{TOOLS_AKTUELL}}` sind
5. ✅ Fokus auf **Skalierung der Hauptleistung**, nicht Nebenaufgaben
6. ✅ Realistische **Zeitplanung** (nicht zu ambitioniert)

**Mindestens 5/6 Kriterien MÜSSEN erfüllt sein!**

---

## 🚨 HÄUFIGE FEHLER - UNBEDINGT VERMEIDEN!

### ❌ Fehler 1: Vage Phasen statt konkreter Deliverables
**Schlecht:** "Woche 1-2: Analyse der Ist-Situation"
**Warum:** Was ist das Ergebnis? Was wird gebaut?
**Besser:** "Woche 1-2: Batch-Processing MVP → 50 Assessments/Tag"

### ❌ Fehler 2: Entwicklung von bereits Existierendem
**Schlecht:** "Woche 3-4: Fragebogen-Entwicklung" (Kunde hat schon Fragebogen!)
**Warum:** Check `{{TOOLS_AKTUELL}}` ignoriert!
**Besser:** "Woche 3-4: Fragebogen-Template-Bibliothek → 20 Branchen"

### ❌ Fehler 3: Keine messbaren KPIs
**Schlecht:** "Erfolg: Bessere Effizienz erreicht"
**Warum:** Nicht messbar, nicht überprüfbar!
**Besser:** "Erfolg: +200% Durchsatz, -50% Kosten, 100 neue User"

### ❌ Fehler 4: Fehlende Ressourcen-Planung
**Schlecht:** Nur "Was" ohne "Wer", "Budget", "Tools"
**Warum:** Nicht umsetzbar ohne Ressourcen!
**Besser:** "Team: 1× Dev (20h), Budget: €2.5k, Tools: Make.com (€99/mo)"

### ❌ Fehler 5: Unrealistische Zeitplanung
**Schlecht:** "Woche 1-2: Komplettes CRM-System mit KI-Integration"
**Warum:** Zu ambitioniert für 2 Wochen!
**Besser:** "Woche 1-2: CRM-Anbindung MVP → 100 Kontakte synchronisiert"

---

## 🔍 VALIDIERUNGS-BEISPIELE

### Beispiel A: E-Commerce Shop (5 MA)
- **Hauptleistung:** Online-Verkauf von Sportbekleidung
- **Tools aktuell:** Shopify, Klaviyo, Google Ads

**❌ FALSCH:**
```
Woche 1-2: Analyse der Customer Journey
→ FEHLER: Vage Phase, kein Deliverable!

Woche 3-4: E-Commerce-Plattform auswählen
→ FEHLER: Haben schon Shopify!

Woche 5-6: Marketing-Strategie entwickeln
→ FEHLER: Keine konkreten KPIs!
```

**✅ RICHTIG:**
```
Woche 1-2: AI-Chatbot für Produktberatung (Shopify-Integration)
→ Deliverable: 24/7 Beratung, 1000 Chats in Woche 1
→ Team: 1× Dev (15h), Budget: €500 (Chatbase), KPI: -30% Support-Anfragen

Woche 3-4: Dynamische Bundles per GPT-4 (nutzt bestehende Shopify-Daten!)
→ Deliverable: "Wer X kauft bekommt Y vorgeschlagen" (automatisch)
→ Team: 1× Dev (12h), Budget: €0 (GPT-4 API), KPI: +25% Warenkorbwert

Woche 5-6: Klaviyo-Kampagnen aus Purchase-History (automatisch generiert)
→ Deliverable: 50 personalisierte E-Mail-Templates aus Kaufverhalten
→ Team: 1× Marketing (10h), Budget: €0, KPI: +15% E-Mail-Conversions
```
→ ALLE haben konkrete Deliverables, nutzen Bestehendes, messbare KPIs!

---

## 💡 BEST PRACTICES

**1. Nutze bestehende Systeme:**
- Statt "neue Website": "Website-Chatbot-Integration"
- Statt "CRM-Auswahl": "CRM-Automatisierung mit GPT"
- Statt "Tool evaluieren": "Bestehende Tools mit KI erweitern"

**2. Kleine Iterationen:**
- MVP in 2 Wochen > Perfekte Lösung in 3 Monaten
- "Quick & Dirty" Prototyp zuerst, dann refinement
- Feedback-Loops nach jedem Meilenstein

**3. Messbare KPIs:**
- Immer konkrete Zahlen: +X%, -Y€, Z neue User
- Nicht "besser", sondern "20% schneller"
- Nicht "mehr", sondern "50 statt 10"

**4. Realistische Planung:**
- Buffer für Unvorhergesehenes (20% Reserve)
- Nicht mehr als 2-3 parallele Initiatives
- Go/No-Go Punkte nach jedem Monat

---

**VERSION:** v2.1 GOLD STANDARD+
**ERSTELLT:** 2025-11-18
**FÜR:** KI-Sicherheit.jetzt - KI-Readiness-Assessment-Reports
**ZIEL:** Konkrete Deliverables mit messbaren KPIs statt generische Projektphasen!
