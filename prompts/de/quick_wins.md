# PROMPT: Quick Wins - 6 Sofort umsetzbare Maßnahmen

## ZWECK
Entwickle 6 spezifische, sofort umsetzbare Quick Wins, die die **Hauptleistung des Unternehmens DIREKT verbessern**, nicht nur allgemeine Prozesse optimieren.

---

## ⚠️ KRITISCHE REGELN - ZWINGEND BEACHTEN!

### ❌ VERBOTEN - Folgendes NIEMALS empfehlen:

1. **KEINE redundanten Tools wenn Kunde BEREITS System hat:**
   - ❌ Typeform/Google Forms wenn Unternehmen schon digitalen Fragebogen hat
   - ❌ GPT-4 API wenn Hauptleistung bereits "GPT-basierte Analyse" enthält
   - ❌ Zapier/Make.com wenn Unternehmen schon Workflow-Automatisierung nutzt
   - ❌ CRM-Tools wenn Kunde bereits CRM-System erwähnt

2. **KEINE generischen Effizienz-Maßnahmen wenn Fokus Hauptleistung ist:**
   - ❌ "LinkedIn Helper für Akquise" (ist nicht Kern-Leistung!)
   - ❌ "Fireflies.ai für Meeting-Notizen" (Nebenaufgabe!)
   - ❌ "Grammarly für E-Mails" (allgemeine Produktivität!)
   - ❌ "Calendly für Terminbuchung" (Support-Prozess!)

3. **KEINE "Quick Wins" die eigentlich Projekte sind:**
   - ❌ "Entwickle neue Website" (Wochen-Projekt!)
   - ❌ "Implementiere CRM-System" (Monate-Projekt!)
   - ❌ "Schulung aller Mitarbeiter" (zu breit!)

### ✅ STATTDESSEN - Fokus auf:

1. **Skalierung des BESTEHENDEN Hauptprodukts/Service:**
   - ✅ Batch-Processing wenn einzelne Analysen gemacht werden
   - ✅ Template-Bibliothek wenn Custom-Erstellung passiert
   - ✅ Self-Service-Portal wenn manuelle Übergaben erfolgen

2. **Repurposing vorhandener Assets:**
   - ✅ Blog-Content aus Kundenprojekten generieren
   - ✅ LinkedIn-Posts aus Analyse-Insights erstellen
   - ✅ Sales-Material aus bestehenden Reports ableiten

3. **Automatisierung DER HAUPTLEISTUNG:**
   - ✅ Reporting-Prozess automatisieren
   - ✅ Standard-Anfragen mit AI beantworten
   - ✅ Qualitätschecks automatisch durchführen

---

## 💡 BEISPIELE: GUT vs. SCHLECHT

### Beispiel-Unternehmen: "KI-Sicherheit.jetzt"
**Hauptleistung:** GPT-4-basierte KI-Readiness-Assessments für deutsche KMUs mit 30-seitigem PDF-Report

#### ❌ SCHLECHT (v2.0 - generisch & redundant):

```markdown
## Quick Win 1: Typeform für Kundenfragebögen
Nutze Typeform für professionelle Fragebögen...
→ FEHLER: Unternehmen HAT bereits digitalen Fragebogen!
→ Verschwendet Budget für redundantes Tool!

## Quick Win 2: LinkedIn Helper für Akquise
Automatisiere LinkedIn-Outreach mit Dux-Soup...
→ FEHLER: Verbessert NICHT die Hauptleistung (Assessments)!
→ Ist generische Marketing-Maßnahme!

## Quick Win 3: Fireflies.ai für Meeting-Notizen
Automatische Transkription von Kundengesprächen...
→ FEHLER: Nebenaufgabe, nicht Kern-Geschäft!
→ Skaliert nicht die Hauptleistung!
```

#### ✅ GUT (v2.1 GOLD - hochspezifisch für Hauptleistung):

```markdown
## Quick Win 1: GPT-4 Batch-Processing für 10× Skalierung
**Problem:** Aktuell werden Assessments einzeln verarbeitet (5/Tag)
**Lösung:** Nutze OpenAI Batch API für parallele Verarbeitung von 50+ Assessments/Tag
**Umsetzung:**
- Bestehenden GPT-4 Code anpassen für Batch-Input
- Queue-System für wartende Assessments
- Automatisches Report-PDF-Generation nach Batch-Ende
**Aufwand:** 4-6h Entwicklung | **Kosten:** -50% API-Kosten | **Impact:** +900% Kapazität

## Quick Win 2: Assessment-Template-Bibliothek
**Problem:** Jedes Assessment startet von Null, keine Wiederverwendung
**Lösung:** 20 branchen-spezifische Templates für häufigste Use Cases
**Umsetzung:**
- Analyse der Top 10 Branchen aus bisherigen Assessments
- Extraktion wiederkehrender Patterns & Best Practices
- Vorausgefüllte Sektionen für Standard-Szenarien
**Aufwand:** 8h | **Kosten:** 0€ | **Impact:** -60% Erstellungszeit pro Assessment

## Quick Win 3: LinkedIn-Content aus Assessment-Insights
**Problem:** Vorhandene Analyse-Daten werden nicht für Marketing genutzt
**Lösung:** Automatische Generierung von 20 LinkedIn-Posts aus jedem Assessment
**Umsetzung:**
- GPT-Prompt: "Extrahiere 3 Key Insights aus Report für LinkedIn"
- Buffer/Hootsuite-Integration für automatisches Posten
- Anonymisierte Case Studies (mit Kunden-Freigabe)
**Aufwand:** 2-3h Setup | **Kosten:** 0€ | **Impact:** 20× Content-Output
```

**Siehst du den Unterschied?**
- ✅ Verbessert die **HAUPTLEISTUNG** (Assessments) direkt
- ✅ Nutzt **BESTEHENDE** Systeme & Daten
- ✅ Skaliert das **KERN-GESCHÄFT**, nicht Nebenaufgaben
- ✅ Konkrete Zahlen: 10× Skalierung, -60% Zeit, 20× Content

---

## 🎯 INSTRUKTIONEN FÜR GPT-4

Du erhältst folgende Variablen:
- `{{BRANCHE}}` - z.B. "Beratung", "Handel", "Produktion"
- `{{MITARBEITER}}` - z.B. "Solo-Selbstständig", "Team (6-50 MA)"
- `{{HAUPTLEISTUNG}}` - z.B. "KI-Readiness-Assessments", "CNC-Frästeile", "Steuerberatung"
- `{{TOOLS_AKTUELL}}` - z.B. "GPT-4, Typeform, PostgreSQL" (WICHTIG für Redundanz-Check!)

### SCHRITT 1: Analyse der Hauptleistung (2 Min Denken!)

**BEVOR du Quick Wins erstellst, analysiere:**

1. **Was ist die KERN-TÄTIGKEIT?**
   - Was verkauft der Kunde tatsächlich?
   - Wo entsteht der Hauptumsatz?
   - Was muss skaliert werden für mehr Revenue?

2. **Welche Systeme/Tools sind SCHON vorhanden?**
   - Check `{{TOOLS_AKTUELL}}`
   - Empfehle KEINE redundanten Tools!
   - Fokus auf Ergänzung & Skalierung

3. **Wo sind Engpässe bei der Hauptleistung?**
   - Manuelle Prozesse im Kern-Business?
   - Keine Wiederverwendung von Assets?
   - Single-Processing statt Batch?

### SCHRITT 2: Erstelle 6 Quick Wins nach diesem Schema

**Für JEDEN Quick Win:**

```markdown
## Quick Win [1-6]: [Prägnanter Titel - max. 8 Wörter]

**Problem:** [Welcher Engpass bei der HAUPTLEISTUNG? 1 Satz]

**Lösung:** [Konkrete Maßnahme die DIREKT die Hauptleistung verbessert, 1 Satz]

**Umsetzung:**
- [Schritt 1 - konkret & technisch]
- [Schritt 2 - konkret & technisch]
- [Schritt 3 - konkret & technisch]

**Aufwand:** [X Stunden/Tage] | **Kosten:** [€ oder "0€"] | **Impact:** [Messbare Verbesserung mit %/× Faktor]

**Tools:** [Nur wenn NICHT schon in {{TOOLS_AKTUELL}} vorhanden!]
```

### SCHRITT 3: Qualitäts-Check JEDES Quick Wins

**Bevor du einen Quick Win ausgibst, prüfe:**

✅ **Hauptleistungs-Test:**
- Verbessert dieser Quick Win die **Kern-Tätigkeit** des Unternehmens?
- Oder ist es nur eine generische Produktivitäts-Maßnahme?
- → Wenn generisch: **VERWERFEN & neu erstellen!**

✅ **Redundanz-Test:**
- Ist das empfohlene Tool bereits in `{{TOOLS_AKTUELL}}`?
- Macht der Quick Win etwas, was der Kunde schon tut?
- → Wenn redundant: **VERWERFEN & neu erstellen!**

✅ **Quick-Test:**
- Ist das wirklich in 1-14 Tagen umsetzbar?
- Oder ist es eigentlich ein Wochen-Projekt?
- → Wenn zu groß: **Runterbrechen auf echten Quick Win!**

✅ **Impact-Test:**
- Gibt es eine messbare Verbesserung? (z.B. +200%, -50% Zeit, 10× Output)
- Ist der ROI sofort sichtbar?
- → Wenn Impact unklar: **Konkretere Zahlen nennen!**

---

## 📋 OUTPUT-FORMAT

```markdown
# 🚀 Quick Wins - 6 Sofort Umsetzbare Maßnahmen

> **Fokus:** Diese Maßnahmen verbessern Ihre **{{HAUPTLEISTUNG}}** direkt und sind in 1-14 Tagen umsetzbar.

---

## Quick Win 1: [Titel]
[Kompletter Quick Win nach Schema]

## Quick Win 2: [Titel]
[Kompletter Quick Win nach Schema]

## Quick Win 3: [Titel]
[Kompletter Quick Win nach Schema]

## Quick Win 4: [Titel]
[Kompletter Quick Win nach Schema]

## Quick Win 5: [Titel]
[Kompletter Quick Win nach Schema]

## Quick Win 6: [Titel]
[Kompletter Quick Win nach Schema]

---

## 📊 Zusammenfassung

| Quick Win | Aufwand | Kosten | Impact |
|-----------|---------|--------|--------|
| 1. [Titel] | [X Tage] | [€] | [Messbarer Impact] |
| 2. [Titel] | [X Tage] | [€] | [Messbarer Impact] |
| 3. [Titel] | [X Tage] | [€] | [Messbarer Impact] |
| 4. [Titel] | [X Tage] | [€] | [Messbarer Impact] |
| 5. [Titel] | [X Tage] | [€] | [Messbarer Impact] |
| 6. [Titel] | [X Tage] | [€] | [Messbarer Impact] |

**Gesamt-Impact:** [Zusammenfassung der wichtigsten Verbesserungen]
```

---

## 🎯 ERFOLGS-KRITERIEN

Ein Quick Win ist GOLD STANDARD+ wenn:

1. ✅ Er die **HAUPTLEISTUNG** direkt verbessert (nicht Nebenaufgaben)
2. ✅ Er **KEINE redundanten Tools** empfiehlt die in `{{TOOLS_AKTUELL}}` sind
3. ✅ Er **bestehende Systeme skaliert** statt neue einzuführen
4. ✅ Er in **1-14 Tagen** realistisch umsetzbar ist
5. ✅ Er einen **messbaren Impact** hat (mit konkreten Zahlen)
6. ✅ Er **konkrete Umsetzungsschritte** enthält (nicht nur "nutze Tool X")

**Mindestens 5/6 Kriterien MÜSSEN erfüllt sein!**

---

## 🚨 HÄUFIGE FEHLER - UNBEDINGT VERMEIDEN!

### ❌ Fehler 1: Generische Marketing-Tools bei Service-Business
**Schlecht:** "Quick Win: LinkedIn Helper für mehr Leads"
**Warum:** Verbessert nicht die Hauptleistung (z.B. Beratung, Assessments)

### ❌ Fehler 2: Redundante Tools empfehlen
**Schlecht:** "Quick Win: Typeform für Fragebögen" (wenn Kunde schon Formulare hat)
**Warum:** Check `{{TOOLS_AKTUELL}}` ignoriert!

### ❌ Fehler 3: Zu große "Quick" Wins
**Schlecht:** "Quick Win: Entwickle neue Website mit KI-Integration"
**Warum:** Das ist ein Wochen-Projekt, kein Quick Win!

### ❌ Fehler 4: Vager Impact
**Schlecht:** "Impact: Bessere Effizienz"
**Warum:** Nicht messbar! Besser: "Impact: +200% Durchsatz, -50% Zeit"

### ❌ Fehler 5: Fokus auf Nebenaufgaben
**Schlecht:** "Quick Win: Fireflies.ai für Meeting-Notizen"
**Warum:** Verbessert Support-Prozess, nicht Hauptleistung!

---

## 🔍 VALIDIERUNGS-BEISPIELE

### Beispiel A: Solo-Steuerberater (10 MA)
- **Hauptleistung:** Jahresabschlüsse & Steuererklärungen
- **Tools aktuell:** DATEV, Excel, Lexoffice

**❌ FALSCH:**
```
Quick Win 1: Calendly für Terminbuchung
Quick Win 2: Grammarly für E-Mail-Korrektur
Quick Win 3: Typeform für Kunden-Onboarding
```
→ KEINER verbessert Hauptleistung (Buchhaltung/Steuern)!

**✅ RICHTIG:**
```
Quick Win 1: DATEV-GPT für automatische Beleganaylse
→ -70% Zeit bei Belegprüfung (Kern-Tätigkeit!)

Quick Win 2: Mandanten-Self-Service-Portal
→ Kunden können Status selbst prüfen, -40% Rückfragen

Quick Win 3: Template-Bibliothek für Standard-Jahresabschlüsse
→ 20 Branchen-Templates, -50% Erstellungszeit
```
→ ALLE verbessern die Kern-Tätigkeit direkt!

---

**VERSION:** v2.1 GOLD STANDARD+
**ERSTELLT:** 2025-11-18
**FÜR:** KI-Sicherheit.jetzt - KI-Readiness-Assessment-Reports
**ZIEL:** Hochspezifische Quick Wins die Hauptleistung skalieren, nicht generische Produktivitäts-Tipps!
