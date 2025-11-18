# PROMPT: Tool-Empfehlungen - KI & Automatisierungs-Tools

## ZWECK
Empfehle 8-12 konkrete Tools die die **Hauptleistung ERGÄNZEN und erweitern** - nicht Tools die bereits genutzt werden oder generische Produktivitäts-Tools. Jedes Tool MUSS einen klaren Use Case zur Skalierung der Hauptleistung haben.

---

## ⚠️ KRITISCHE REGELN - ZWINGEND BEACHTEN!

### ❌ VERBOTEN - Folgende Tools NIEMALS empfehlen:

1. **KEINE Tools die bereits in `{{TOOLS_AKTUELL}}` vorhanden sind:**
   - ❌ GPT-4 API wenn Hauptleistung "GPT-basierte Analysen" enthält
   - ❌ Typeform/Google Forms wenn digitaler Fragebogen schon existiert
   - ❌ PostgreSQL/MySQL wenn Datenbank bereits im Einsatz
   - ❌ Shopify wenn E-Commerce-Shop schon läuft
   - ❌ Slack wenn Kunde bereits Slack erwähnt

2. **KEINE generischen Produktivitäts-Tools (außer DIREKT für Hauptleistung):**
   - ❌ Calendly (Terminbuchung ist Support-Prozess!)
   - ❌ Grammarly (E-Mail-Korrektur ist Nebenaufgabe!)
   - ❌ LastPass (Passwort-Management irrelevant für Hauptleistung!)
   - ❌ Trello (Projekt-Management ist kein Tool für Hauptleistung!)

3. **KEINE Tools ohne konkreten ROI-Bezug zur Hauptleistung:**
   - ❌ Loom (Video-Nachrichten) wenn Hauptleistung nicht Video ist
   - ❌ Miro (Whiteboard) wenn keine kollaborative Design-Arbeit
   - ❌ Notion (Dokumentation) wenn nicht Kern-Geschäft
   - ❌ Asana (Task-Management) wenn nicht direkt für Hauptleistung

4. **KEINE Tools die "nice to have" sind statt "must have":**
   - ❌ Tools ohne messbare Impact-Kennzahl
   - ❌ Tools die nur "ein bisschen schneller" machen
   - ❌ Tools für Prozesse die 1× pro Monat passieren

### ✅ STATTDESSEN - Fokus auf:

1. **Tools die die HAUPTLEISTUNG direkt skalieren:**
   - ✅ Make.com/Zapier wenn Haupt-Workflow automatisiert werden kann
   - ✅ APIs die Hauptleistung erweitern (z.B. Perplexity für Research)
   - ✅ Batch-Processing Tools für parallelisierte Hauptaufgaben

2. **Tools die vorhandene Daten/Assets repurposen:**
   - ✅ Buffer/Hootsuite wenn Content aus Hauptleistung generiert werden kann
   - ✅ Synthesia/Heygen wenn Kundenprojekte zu Video-Content werden
   - ✅ Canva API wenn Design-Assets automatisch skaliert werden

3. **Tools die Integration/Orchestrierung ermöglichen:**
   - ✅ n8n wenn verschiedene bestehende Tools verbunden werden
   - ✅ Retool wenn Admin-Interfaces für Hauptleistung fehlen
   - ✅ Supabase wenn Backend für Hauptleistung fehlt (aber DB schon da!)

4. **Tools mit klarem Use Case UND messbarem ROI:**
   - ✅ Jedes Tool MUSS zeigen: "Erspart X Stunden/Woche bei [Hauptleistung]"
   - ✅ Oder: "Ermöglicht +Y% Durchsatz bei [Hauptleistung]"
   - ✅ Oder: "Generiert Z neue Leads für [Hauptleistung]"

---

## 💡 BEISPIELE: GUT vs. SCHLECHT

### Beispiel-Unternehmen: "KI-Sicherheit.jetzt"
**Hauptleistung:** GPT-4-basierte KI-Readiness-Assessments mit PDF-Report-Generierung
**Tools aktuell:** GPT-4 API, Typeform (Fragebogen), PostgreSQL, FastAPI, React

#### ❌ SCHLECHT (v2.0 - redundant & generisch):

| Tool | Kategorie | Preis | Use Case | ROI |
|------|-----------|-------|----------|-----|
| **GPT-4 API** | KI-Analyse | $20/Mio Tokens | Für Assessment-Auswertung | Hocheffizient |
| **Typeform** | Fragebögen | €25/Monat | Professionelle Kundenfragebögen | Conversion +30% |
| **Calendly** | Terminbuchung | €10/Monat | Automatische Terminvereinbarung | -2h/Woche |
| **Grammarly** | Schreibassistent | €12/Monat | Fehlerfreie E-Mails & Reports | Professionalität |

→ **FEHLER 1:** GPT-4 + Typeform sind BEREITS im Einsatz! (Check `{{TOOLS_AKTUELL}}` ignoriert!)
→ **FEHLER 2:** Calendly + Grammarly verbessern nicht die Hauptleistung (Assessments)!
→ **FEHLER 3:** Generische Produktivitäts-Tools ohne direkten ROI-Bezug zu Kern-Geschäft!

#### ✅ GUT (v2.1 GOLD - ergänzend & spezifisch für Hauptleistung):

| Tool | Kategorie | Preis | Use Case für HAUPTLEISTUNG | ROI |
|------|-----------|-------|----------------------------|-----|
| **Make.com** | Workflow-Automation | €99/Monat | Automatisiert gesamten Assessment-Flow: Typeform → GPT-4 Batch → PDF → E-Mail. Skaliert von 5 auf 50 Reports/Tag | +900% Kapazität, -40% manuelle Arbeit |
| **Perplexity API** | Research-Upgrade | $50/Monat | Erweitert Assessments um Live-Daten: Aktuelle Förderprogramme, neueste KI-Tools, Competitor-Analysis → Reports immer aktuell statt statisch | +50% Report-Qualität, Kunden zahlen 30% mehr für "Live Data"-Version |
| **Docraptor API** | PDF-Generation | €30/Monat | Professionelle PDF-Layouts mit Custom-Branding für White-Label-Partner. Ersetzt einfache Text-PDFs durch Magazine-Qualität | +200% Conversion für White-Label-Angebote |
| **Supabase** | Auth + Storage | Free→€25/Monat | Self-Service-Portal für Kunden: Login, Assessment-Status-Tracking, Report-Download → Reduziert Support-Anfragen | -70% "Wo ist mein Report?"-Anfragen, ermöglicht 10× mehr Kunden ohne mehr Support |
| **Buffer** | Content-Automation | €15/Monat | Automatische LinkedIn-Posts aus Assessment-Insights: Jeder Report = 5 Posts mit anonymisierten Learnings → Marketing ohne Zusatzarbeit | 20× Content-Output, 0 Extra-Stunden |
| **Stripe Billing** | Recurring Revenue | 0.5% + €0.25 | Subscription-Modell für monatliche Mini-Assessments (€99/Monat) statt einmalig €2.500 → Predictable Revenue | €10k MRR nach 6 Monaten (100 Subscribers) |
| **Retool** | Admin-Interface | €50/Monat | Internes Dashboard: Batch-Status, Partner-Verwaltung, Report-Qualitäts-Checks → ersetzt manuelle PostgreSQL-Queries | -5h/Woche Admin-Arbeit |
| **Zapier** | Integration-Fallback | €50/Monat | Backup wenn Make.com ausfällt + Integration mit Tools die Make nicht hat (z.B. spezielle CRMs) | Business Continuity |

→ **RICHTIG:** ALLE Tools erweitern die Hauptleistung (Assessments)!
→ **RICHTIG:** KEINE redundanten Tools (alle ergänzen Bestehendes)!
→ **RICHTIG:** Klare ROI-Kennzahlen für jedes Tool bezogen auf Kern-Geschäft!

**Siehst du den Unterschied?**
- ✅ **Ergänzend statt redundant:** Kein Tool ersetzt vorhandene Systeme
- ✅ **Hauptleistungs-Fokus:** Alle Tools skalieren Assessments, nicht Nebenaufgaben
- ✅ **Messbarer ROI:** "+900% Kapazität", "-70% Support", "20× Content"
- ✅ **Use Case konkret:** Nicht "Tool X ist gut", sondern "Tool X macht Y für Hauptleistung Z"

---

## 🎯 INSTRUKTIONEN FÜR GPT-4

Du erhältst folgende Variablen:
- `{{BRANCHE}}` - z.B. "Beratung", "Handel", "Produktion"
- `{{MITARBEITER}}` - z.B. "Solo-Selbstständig", "Team (6-50 MA)"
- `{{HAUPTLEISTUNG}}` - z.B. "KI-Readiness-Assessments", "Steuerberatung"
- `{{TOOLS_AKTUELL}}` - **KRITISCH:** Diese Tools NIEMALS empfehlen!
- `{{QUICK_WINS}}` - Welche Quick Wins brauchen welche Tools?

### SCHRITT 1: Tool-Kategorien basierend auf Hauptleistung definieren (3 Min Denken!)

**BEVOR du Tools empfiehlst, analysiere:**

1. **Welche Tool-Kategorien braucht diese Hauptleistung?**
   - Assessment/Analyse-Business → Research-APIs, Automation, PDF-Tools
   - E-Commerce → Personalisierung, Chatbots, Analytics
   - Produktion → CAD-Integration, Qualitätskontrolle, Predictive Maintenance
   - Beratung → CRM-Erweiterung, Proposal-Automation, Knowledge-Management

2. **Welche Tools sind SCHON vorhanden und müssen vermieden werden?**
   - Checke `{{TOOLS_AKTUELL}}` SEHR genau!
   - Suche auch nach Synonymen (z.B. "Fragebögen" = Typeform wahrscheinlich da)
   - NIEMALS redundante Tools empfehlen!

3. **Welche Gaps gibt es bei der Hauptleistung?**
   - Manuelle Prozesse die automatisiert werden können?
   - Datenquellen die fehlen?
   - Integration-Bedarf zwischen vorhandenen Tools?
   - Self-Service-Optionen die fehlen?

### SCHRITT 2: 8-12 Tools mit spezifischen Use Cases

**Typische Tool-Kategorien (je nach Hauptleistung):**

**A) WORKFLOW-AUTOMATISIERUNG** (wenn manuelle Prozesse existieren)
- Make.com, Zapier, n8n
- Use Case: End-to-End Automatisierung der Hauptleistung
- Nicht für: Generische "Effizienz", sondern konkret für Hauptprozess!

**B) DATEN & RESEARCH** (wenn Hauptleistung Analysen/Insights liefert)
- Perplexity API, Tavily API, ScraperAPI
- Use Case: Live-Daten statt statische Info
- Nicht für: "Besseres Googeln", sondern Integration in Hauptprodukt!

**C) CONTENT-REPURPOSING** (wenn Hauptleistung Content generiert)
- Buffer, Canva API, Synthesia
- Use Case: Kundenprojekte werden zu Marketing-Content
- Nicht für: "Social Media Management" generisch!

**D) KUNDENSCHNITTSTELLE** (wenn Self-Service möglich)
- Supabase, Retool, Chatbase
- Use Case: Kunden-Portal, Chatbots für Hauptleistung
- Nicht für: FAQ-Bots die nur Support entlasten!

**E) MONETARISIERUNG** (wenn neue Revenue-Modelle möglich)
- Stripe Billing, Lemonsqueezy, Chargebee
- Use Case: Von Projekt zu Subscription
- Nicht für: "Bessere Rechnungen" (Admin-Tool!)

**F) SKALIERUNGS-ENABLER** (wenn Durchsatz-Problem existiert)
- OpenAI Batch API, AWS Lambda, Cloudflare Workers
- Use Case: Parallelisierung der Hauptleistung
- Nicht für: Generische "Cloud-Migration"!

### SCHRITT 3: Jedes Tool im Detail beschreiben

**Für JEDES Tool:**

```markdown
| Tool | Kategorie | Preis | Use Case für HAUPTLEISTUNG | ROI |
|------|-----------|-------|----------------------------|-----|
| **[Tool-Name]** | [Kategorie] | [€X/Monat] | [SPEZIFISCH: Was macht es für die Hauptleistung? Nicht generisch! 1-2 Sätze mit konkreten Details.] | [Messbare Verbesserung: +X% Durchsatz, -Y Stunden/Woche bei HAUPTLEISTUNG, €Z zusätzliche Revenue] |
```

**Wichtig:**
- **Use Case:** MUSS sich auf `{{HAUPTLEISTUNG}}` beziehen, nicht auf allgemeine Produktivität!
- **ROI:** MUSS messbar sein (+X%, -Y Stunden, €Z Revenue), nicht "Verbesserung" o.ä.!
- **Kategorie:** Klar definiert (nicht "Productivity" sondern "Workflow-Automation")
- **Preis:** Konkret recherchiert, nicht geschätzt

### SCHRITT 4: Budget-Zusammenfassung & Priorisierung

**Am Ende der Tabelle:**

```markdown
---

## 💰 Budget-Zusammenfassung

**Gesamt-Investment:** €[Summe]/Monat

**Priorisierung (Must-Have → Nice-to-Have):**

**Stufe 1 - MUST-HAVE (Start sofort):** €[X]/Monat
- [Tool 1]: [Begründung warum Must-Have für Hauptleistung]
- [Tool 2]: [Begründung]

**Stufe 2 - SHOULD-HAVE (Start nach 3 Monaten):** €[Y]/Monat
- [Tool 3]: [Begründung]
- [Tool 4]: [Begründung]

**Stufe 3 - NICE-TO-HAVE (Evaluieren nach 6 Monaten):** €[Z]/Monat
- [Tool 5]: [Begründung]

**Erwarteter ROI gesamt:** [Berechnung basierend auf Zeitersparnis + Revenue-Uplift bei Hauptleistung]
```

### SCHRITT 5: Qualitäts-Check JEDES Tools

**Bevor du ein Tool empfiehlst, prüfe:**

✅ **Redundanz-Test:**
- Ist das Tool bereits in `{{TOOLS_AKTUELL}}`?
- Macht das Tool etwas, was ein vorhandenes Tool schon kann?
- → Wenn redundant: **VERWERFEN & durch ergänzendes Tool ersetzen!**

✅ **Hauptleistungs-Test:**
- Verbessert dieses Tool die **HAUPTLEISTUNG** direkt?
- Oder nur eine Nebenaufgabe (Support, Admin, Dokumentation)?
- → Wenn Nebenaufgabe: **VERWERFEN** (außer klar begründet warum relevant)!

✅ **ROI-Test:**
- Gibt es eine **messbare Verbesserung** (+X%, -Y h, €Z)?
- Oder nur vage "Verbesserung" / "Effizienz"?
- → Wenn nicht messbar: **Konkrete Zahlen recherchieren oder verwerfen!**

✅ **Use-Case-Test:**
- Ist der Use Case **spezifisch für diese Hauptleistung**?
- Oder generisch ("bessere Produktivität")?
- → Wenn generisch: **Spezifizieren oder verwerfen!**

✅ **Budget-Test:**
- Ist das Tool das Budget wert für dieses Unternehmen?
- Solo-Selbstständig: Eher Free/Low-Cost-Tools
- Team 50+MA: Auch €500+/Monat Tools möglich
- → Wenn zu teuer für Größe: **Günstigere Alternative suchen!**

---

## 📋 OUTPUT-FORMAT

```markdown
# 🛠️ Tool-Empfehlungen - KI & Automatisierung

> **Fokus:** Diese Tools erweitern Ihre **{{HAUPTLEISTUNG}}** und ermöglichen höhere Skalierung, Automatisierung und neue Revenue-Quellen.

---

## 🎯 Empfohlene Tools im Überblick

| Tool | Kategorie | Preis | Use Case für HAUPTLEISTUNG | ROI |
|------|-----------|-------|----------------------------|-----|
| **[Tool 1]** | [Kat] | €X/mo | [Spezifischer Use Case] | [Messbare Kennzahl] |
| **[Tool 2]** | [Kat] | €X/mo | [Spezifischer Use Case] | [Messbare Kennzahl] |
| **[Tool 3]** | [Kat] | €X/mo | [Spezifischer Use Case] | [Messbare Kennzahl] |
| **[Tool 4]** | [Kat] | €X/mo | [Spezifischer Use Case] | [Messbare Kennzahl] |
| **[Tool 5]** | [Kat] | €X/mo | [Spezifischer Use Case] | [Messbare Kennzahl] |
| **[Tool 6]** | [Kat] | €X/mo | [Spezifischer Use Case] | [Messbare Kennzahl] |
| **[Tool 7]** | [Kat] | €X/mo | [Spezifischer Use Case] | [Messbare Kennzahl] |
| **[Tool 8]** | [Kat] | €X/mo | [Spezifischer Use Case] | [Messbare Kennzahl] |

[Optional: Tool 9-12 wenn relevant für Hauptleistung]

---

## 💰 Budget-Zusammenfassung

**Gesamt-Investment:** €[Summe]/Monat

**Priorisierung:**

**Stufe 1 - MUST-HAVE (Start sofort):** €[X]/Monat
- [Tools mit Begründung]

**Stufe 2 - SHOULD-HAVE (Start nach 3 Monaten):** €[Y]/Monat
- [Tools mit Begründung]

**Stufe 3 - NICE-TO-HAVE (Evaluieren nach 6 Monaten):** €[Z]/Monat
- [Tools mit Begründung]

**Erwarteter ROI gesamt:** [Berechnung]

---

## 🔗 Quick Links & Ressourcen

- [Tool 1]: [URL]
- [Tool 2]: [URL]
- ...

**Hinweis:** Alle Preise Stand [Datum], Free Tiers verfügbar für [Tools X, Y, Z]
```

---

## 🎯 ERFOLGS-KRITERIEN

Tool-Empfehlungen sind GOLD STANDARD+ wenn:

1. ✅ **KEINE redundanten Tools** aus `{{TOOLS_AKTUELL}}` empfohlen werden
2. ✅ **Jedes Tool** hat konkreten Use Case für `{{HAUPTLEISTUNG}}` (nicht generisch!)
3. ✅ **Jedes Tool** hat messbaren ROI (+X%, -Y h, €Z) bezogen auf Hauptleistung
4. ✅ **Budget-Check** am Ende mit Priorisierung (Must/Should/Nice-to-Have)
5. ✅ **8-12 Tools** gesamt, alle relevant für Skalierung der Hauptleistung
6. ✅ **Fokus auf Integration** & Orchestrierung bestehender Tools, nicht Ersatz!

**Mindestens 5/6 Kriterien MÜSSEN erfüllt sein!**

---

## 🚨 HÄUFIGE FEHLER - UNBEDINGT VERMEIDEN!

### ❌ Fehler 1: Redundante Tools empfehlen
**Schlecht:** GPT-4 empfehlen wenn in `{{TOOLS_AKTUELL}}` schon vorhanden
**Warum:** Kunde nutzt es bereits! Check `{{TOOLS_AKTUELL}}` ignoriert!

### ❌ Fehler 2: Generische Produktivitäts-Tools ohne Hauptleistungs-Bezug
**Schlecht:** Calendly, Grammarly, Notion (allgemeine Tools)
**Warum:** Verbessern nicht die Hauptleistung direkt!

### ❌ Fehler 3: Vage Use Cases
**Schlecht:** "Tool X verbessert Effizienz"
**Warum:** Wie genau? Bei welchem Prozess? Nicht spezifisch!
**Besser:** "Tool X automatisiert Report-Generierung → -5h/Woche bei Hauptleistung"

### ❌ Fehler 4: Kein messbarer ROI
**Schlecht:** "ROI: Höhere Qualität"
**Warum:** Nicht messbar, nicht überprüfbar!
**Besser:** "ROI: +30% Kunden-Satisfaction (NPS), -40% Revision-Requests"

### ❌ Fehler 5: Falsche Budget-Kategorie
**Schlecht:** €500/Monat Tools für Solo-Selbstständigen
**Warum:** Nicht verhältnismäßig zum Unternehmen!
**Besser:** Free-Tier oder €50/Monat Maximum für Solos

---

## 🔍 VALIDIERUNGS-BEISPIELE

### Beispiel A: Architekturbüro (12 MA)
- **Hauptleistung:** Architektur-Planung für Wohnimmobilien
- **Tools aktuell:** AutoCAD, Revit, Adobe Suite

**❌ FALSCH:**
| Tool | Use Case |
|------|----------|
| AutoCAD | Für 3D-Planung |
| Notion | Projekt-Dokumentation |
| Calendly | Terminbuchung mit Kunden |

→ **FEHLER:** AutoCAD ist schon vorhanden! Notion + Calendly sind generisch!

**✅ RICHTIG:**
| Tool | Use Case für HAUPTLEISTUNG | ROI |
|------|----------------------------|-----|
| **Midjourney + API** | Automatische Exterior-Visualisierungen aus CAD-Daten → erspart 3h/Projekt Rendering-Arbeit | -30% Visualisierungs-Zeit, Kunden sehen Entwürfe 3 Tage früher |
| **Speckle** | AutoCAD/Revit-Sync für Remote-Teams → Echtzeit-Kollaboration statt E-Mail-Ping-Pong | -50% Abstimmungs-Zeit, +3 Projekte parallel möglich |
| **TestFit** | Automatische Grundriss-Optimierung (Flächennutzung, Baukosten) → Kunden erhalten 5 Varianten statt 1 | +200% Kundenzufriedenheit, Kunden upgraden häufiger zu Premium |

→ **RICHTIG:** Alle Tools erweitern Hauptleistung (Architektur), keine Redundanz!

---

## 💡 RECHERCHE-TIPPS FÜR GPT-4

**Wenn du dir bei einem Tool unsicher bist:**

1. **Check Redundanz:**
   - Lies `{{TOOLS_AKTUELL}}` SEHR sorgfältig
   - Suche nach Synonymen (z.B. "digitaler Fragebogen" = wahrscheinlich Typeform)
   - Im Zweifel: NICHT empfehlen!

2. **Check Hauptleistungs-Relevanz:**
   - Frage: "Skaliert dieses Tool die HAUPTLEISTUNG direkt?"
   - Wenn "Nein" → VERWERFEN (außer klar begründet)

3. **Check ROI:**
   - Frage: "Kann ich konkrete Zahlen nennen (+X%, -Y h)?"
   - Wenn "Nein" → Bessere Recherche oder anderes Tool wählen

4. **Check Budget:**
   - Solo: Max €100/Monat Tools total
   - Team 5-10: Max €300/Monat
   - Team 10-50: Max €1000/Monat
   - Team 50+: €2000+/Monat möglich

---

**VERSION:** v2.1 GOLD STANDARD+
**ERSTELLT:** 2025-11-18
**FÜR:** KI-Sicherheit.jetzt - KI-Readiness-Assessment-Reports
**ZIEL:** Ergänzende Tools für Hauptleistung statt redundante oder generische Tools!
