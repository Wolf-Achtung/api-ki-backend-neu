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
