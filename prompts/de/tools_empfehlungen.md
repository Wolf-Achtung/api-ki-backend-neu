<!-- tools_empfehlungen.md – v3.0 GOLD STANDARD+ BRANCHENLOGIK -->
<!-- Ausgabe: valides HTML, KEIN <html>, <head> oder <body>, KEINE Markdown-Fences. -->

# PROMPT: Tool-Empfehlungen – KI- & Automatisierungs-Tools

## ZWECK

Erstelle eine **konkrete Tool-Empfehlungsliste (8–12 Tools)**, die:

1. die **Hauptleistung {{HAUPTLEISTUNG}} direkt skaliert oder erweitert**,  
2. zur **Branche {{BRANCHE_LABEL}}** passt (siehe Branchengruppen unten),  
3. die **bestehende Tool-Landschaft {{TOOLS_AKTUELL}} sinnvoll ergänzt** (keine Duplikate),  
4. pro Tool einen **klaren, messbaren Use Case** und einen **Impact-/ROI-Hinweis** liefert.

Ausgabe als **HTML-Sektion mit Tabelle**.

---

## VARIABLEN

Du erhältst mindestens:

- `{{BRANCHE_LABEL}}` – z. B. „Marketing & Werbung“, „Beratung & Dienstleistungen“,  
  „Finanzen & Versicherungen“, „Medien & Kreativwirtschaft“, „Bildung“, „Bauwesen & Architektur“ …
- `{{BRANCHE}}` – interner Branchencode laut `mappings.json` (z. B. `marketing`, `medien`, `bau`, `finanzen`). :contentReference[oaicite:2]{index=2}  
- `{{UNTERNEHMENSGROESSE_LABEL}}` – z. B. „Solo-Selbstständig“, „2–10 (Kleines Team)“, „11–100 (KMU)“
- `{{COMPANY_SIZE}}` – `solo`, `team` oder `kmu`
- `{{HAUPTLEISTUNG}}` – textuelle Beschreibung der Hauptleistung
- `{{TOOLS_AKTUELL}}` – Liste vorhandener Tools (Text)
- `{CONTEXT_QUICK_WINS}` – optional: Hinweise, welche Quick Wins welche Tools benötigen

---

## ⚠️ GLOBALE VERBOTE

### 1. Keine redundanten Tools

**Niemals** ein Tool empfehlen, das in `{{TOOLS_AKTUELL}}` bereits vorkommt oder dieselbe Kernfunktion erfüllt.

- ❌ GPT‑4 / GPT‑4o API, wenn schon in `{{TOOLS_AKTUELL}}`  
- ❌ Typeform/Google Forms/Tally, wenn bereits ein Online-Fragebogen genutzt wird  
- ❌ Standarddatenbanken (PostgreSQL/MySQL/SQLite), wenn Datenbank schon im Stack  
- ❌ Slack/Teams/Notion/Jira, wenn diese oder funktional identische Tools genannt sind

Wenn ein vorhandenes Tool relevant ist, **empfiehl bessere Nutzung**, kein alternatives Werkzeug.

### 2. Keine generischen Produktivitäts-Tools als Kernempfehlung

- ❌ Calendly, Meeting-Planer  
- ❌ Grammarly, Rechtschreibhilfen  
- ❌ reine To‑Do-/Task‑Manager  
- ❌ „Allzweck“-Notiz-Apps  

Ausnahme: **nur**, wenn sie **direkt** den Kernprozess von {{HAUPTLEISTUNG}} verbessern.

### 3. Keine Tools ohne klaren Business Case

- ❌ „Nice to have“ ohne messbaren Hebel  
- ❌ reine „Experimentier-Tools“ ohne Integration in den Hauptprozess  
- ❌ Tools, die nur allgemeine „Produktivität“ versprechen

---

## ✅ GLOBALER FOKUS

1. **Kernprozess-Hebel:** Tools, die den **zentralen Wertschöpfungsprozess von {{HAUPTLEISTUNG}}** beschleunigen, stabilisieren oder skalieren.  
2. **Daten/Assets mehrfach nutzen:** Tools, die vorhandene Daten, Reports, Medien oder Prozesse mehrfach verwertbar machen (z. B. Content-Pipeline, Self-Service-Portal).  
3. **Integration & Orchestrierung:** Tools, die vorhandene Systeme verbinden oder einen stabilen Tech‑Stack bilden (siehe `starter_stacks.json`). :contentReference[oaicite:3]{index=3}  
4. **Messbarer Impact:** Jedes Tool erhält eine Impact-Aussage: Zeitersparnis, Kapazitätshebel, Umsatzchance oder Risiko-/Compliance-Effekt.

---

## 🌍 BRANCHENSPEZIFISCHE LEITPLANKEN

Nutze diese Leitplanken, um Tools **branchenpassend** zu wählen. Branchencodes sind in `mappings.json` definiert. :contentReference[oaicite:4]{index=4}  

### A) Beratung & Dienstleistungen / Agenturen / Marketing (`beratung`, `dienstleistungen`, `marketing`)

**Fokus-Tools:**

- Angebots-/Proposal-Automation (z. B. aus Briefing → Angebot → Vertrag)  
- Report-Generierung aus KI-Analysen (PDF/Slides)  
- Wissensmanagement & Prompt-Bibliotheken für wiederkehrende Use Cases  
- CRM-Erweiterungen für Lead-Qualifizierung, Forecasting, Upselling  
- Self-Service-Assessments/Portale (z. B. mit Tally + Make + LLM) :contentReference[oaicite:5]{index=5}  

**Nicht empfehlen:**

- reine Social-Media-Planer ohne Bezug zu {{HAUPTLEISTUNG}}  
- Tools, die nur interne Organisation verbessern (Kanban, Notizen), ohne direkten Kundennutzen.

### B) Marketing & Werbung / Medien & Kreativwirtschaft (`marketing`, `medien`)

**Fokus-Tools:**

- KI‑gestützte Content-Pipeline (Text/Bild/Video/Audio)  
- Asset-Management / Digital Asset Management, ggf. mit RAG-Suche auf Assets :contentReference[oaicite:6]{index=6}  
- Automatisierte Varianten-Erzeugung (Formate, Kanäle, Sprachen)  
- Review-/Freigabe-Workflows mit Brand-Guidelines und Guardrails  
- Analyse-Tools für Kampagnenperformance und A/B-Tests

**Nicht empfehlen:**

- Fragebogen-/Assessment-Tools als Kernempfehlung, wenn {{HAUPTLEISTUNG}} primär Produktion ist.  
- reine Standard-„KI-Chatbots“ ohne Bezug zu Content-Produktion.

### C) Finanzen & Versicherungen (`finanzen`)

**Fokus-Tools:**

- Dokument-/Vertragsanalyse mit Logging & Audit-Trail  
- Workflow-Engines mit Vier-Augen-Prinzip und Rollenrechten  
- Risiko-Scoring, Fraud-Detection, KYC/AML-Lösungen  
- RegTech-Tools für Reporting, Governance, Audit-Pfade  
- PII-Masking, Data-Loss-Prevention, Modellfreigabe-Prozesse :contentReference[oaicite:7]{index=7}  

**Nicht empfehlen:**

- Tools ohne nachvollziehbare Sicherheits-/Compliance-Story  
- Social-/Content-Tools als zentrale Empfehlung.

### D) Bildung (`bildung`)

**Fokus-Tools:**

- Authoring-Tools für Lerninhalte und interaktive Übungen  
- KI‑gestützte Feedback-/Korrektur-Systeme  
- Lernanalyse, Kompetenzprofile und adaptive Aufgaben  
- Integrationen in bestehende LMS (Moodle, ILIAS, itslearning etc.)

**Nicht empfehlen:**

- reine Sales-/Marketing-Tools als Hauptempfehlung.

### E) Bauwesen & Architektur (`bau`)

**Fokus-Tools:**

- BIM-/Planungs-Erweiterungen, Modellprüfung, Kollisionschecks  
- Baufortschritts- und Mängeldoku (mobile Apps + KI-Bildauswertung)  
- Termin- & Kostenrisiko-Prognose  
- Sprach-/Fotoerfassung auf der Baustelle mit automatischer Strukturierung

**Nicht empfehlen:**

- generische Büro-/Organisationstools ohne direkten Bezug zu Planung, Baustelle oder Dokumentation.

### F) Sonstige Branchen (Industrie, Handel, Gesundheit, Logistik, Verwaltung)

**Fokus-Tools:**

- Automatisierung des jeweiligen Kernprozesses (Produktion, Fulfillment, Support etc.)  
- Qualitäts- und Sicherheitskontrollen, Observability, Logging  
- Supply-Chain-/Prozess-Analyse, RAG auf Fachdokumenten  
- Compliance & Nachvollziehbarkeit (vor allem in Verwaltung/Gesundheit)

---

## 🎯 OUTPUT-FORMAT

Antworte mit **einer HTML-Sektion**:

```html
<section class="section tools">
  <h2>Tool-Empfehlungen für {{HAUPTLEISTUNG}}</h2>

  <p>Kurze Einleitung (2–3 Sätze), warum die folgenden Tools
     gut zu {{BRANCHE_LABEL}} und {{UNTERNEHMENSGROESSE_LABEL}} passen
     und wie sie die Hauptleistung konkret skalieren.</p>

  <table class="table">
    <thead>
      <tr>
        <th>Tool</th>
        <th>Kategorie</th>
        <th>Einsatz im Kernprozess</th>
        <th>Integrationen</th>
        <th>Impact / ROI</th>
      </tr>
    </thead>
    <tbody>
      <!-- 8–12 Zeilen -->
      <tr>
        <td><strong>[Tool-Name]</strong></td>
        <td>[Kategorie]</td>
        <td>[konkreter Use Case für {{HAUPTLEISTUNG}} in {{BRANCHE_LABEL}}]</td>
        <td>[Anbindung an bestehende Tools aus {{TOOLS_AKTUELL}}]</td>
        <td>[messbare Wirkung: Zeitersparnis, Durchsatz, Umsatz, Risikoreduktion]</td>
      </tr>
    </tbody>
  </table>

  <p><strong>Hinweis:</strong> Preise/Pläne sind grobe Orientierungswerte und
     dienen nur zur relativen Einordnung. Entscheidend ist der erwartete Hebel
     auf Zeit, Qualität, Umsatz und Risiko in Ihrem konkreten Geschäftsmodell.</p>
</section>
