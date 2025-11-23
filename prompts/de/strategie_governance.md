<!-- strategie_governance.md - v2.3 GOLD STANDARD+ -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.
     VERSION: 2.3 GOLD STANDARD+ (Size-Awareness + Score-Variablen Fix) -->

# PROMPT: Strategie & Governance - KI-Governance-Strukturen

## ⚠️ SIZE-AWARENESS - ABSOLUT PFLICHT!

**Mögliche Unternehmensgrößen (NUR diese 3!):**
- `{{COMPANY_SIZE}}` = "solo" → Label: "1 (Solo-Selbstständig/Freiberuflich)"
- `{{COMPANY_SIZE}}` = "team" → Label: "2-10 (Kleines Team)"  
- `{{COMPANY_SIZE}}` = "kmu" → Label: "11-100 (KMU)"

### 📏 SIZE-APPROPRIATE LANGUAGE - PFLICHT!

**{{COMPANY_SIZE}} = "solo":**
- ✅ "Geschäftsführer" oder "Sie als Freiberufler"
- ✅ "Externe Auditoren" (Anwalt, Berater)
- ✅ "Checklisten" statt komplexe Prozess-Dokumente
- ❌ NIEMALS: "Team", "PMO", "Abteilung", "Führungskräfte", "Steering Committee"

**{{COMPANY_SIZE}} = "team" (2-10 MA):**
- ✅ "Geschäftsführer + Team"
- ✅ "Verantwortlicher Mitarbeiter für KI/Compliance"
- ✅ "Externe Unterstützung für Audits"
- ❌ NIEMALS: "PMO-Team", "Abteilungsleiter", "Change Manager"

**{{COMPANY_SIZE}} = "kmu" (11-100 MA):**
- ✅ "Projektleiter", "Führungskraft", "Compliance-Verantwortlicher"
- ✅ "Projektteam (3-5 Personen)"
- ✅ "Abteilung", "Steering Committee"
- ✅ "PMO-Team" oder "Abteilungsleiter" (ab ~50 MA)

---

## 🎯 ZWECK

Erstelle konkrete Governance-Empfehlungen die:
1. **Score-Gaps adressieren** (z.B. Governance < 60 → DSGVO-Prozesse)
2. **Spezifisch für {{HAUPTLEISTUNG}}** sind (nicht generisch!)
3. **Rollen & Verantwortlichkeiten SIZE-AWARE** definieren
4. **Konkrete Prozesse** beschreiben (nicht "etablieren Sie...")

**Zielgruppe:** Geschäftsführung, Compliance-Officer, Risk-Owner  
**Stil:** Strukturiert, compliance-fokussiert, pragmatisch, größen-angemessen

---

## ⛔ ABSOLUT VERBOTEN

### ❌ GENERISCHE Governance-Tipps:
- ❌ "KI-Beirat einrichten"
- ❌ "Regelmäßige Reviews durchführen"
- ❌ "Richtlinien erstellen"

### ❌ UNREALISTISCHE Rollen für Größe:
- ❌ "Chief AI Officer ernennen" (bei Solo/Klein!)
- ❌ "PMO-Team" bei Solo oder Klein (2-10 MA)!
- ❌ "KI-Steuerungsausschuss" bei Solo!
- ❌ "Change Manager" bei Klein!

---

## ✅ STATTDESSEN: SIZE-APPROPRIATE!

### ✅ Solo (1 MA):
- "Geschäftsführer (Sie)" 
- "Externe Auditoren: DSGVO-Anwalt (€2.000), Security-Pentest (€2.500)"
- "Checklisten statt Prozess-Handbücher"
- Review-Zyklus: "Jährlich" oder "Bei Bedarf"
- Budget: Max €10.000 CAPEX, €500/Monat OPEX

### ✅ Klein (2-10 MA):
- "Geschäftsführer + verantwortlicher Mitarbeiter"
- "Externe Unterstützung für komplexe Themen (Anwalt, Auditor)"
- "Einfache Prozess-Dokumente (1-2 Seiten)"
- Review-Zyklus: "Halbjährlich"
- Budget: Max €50.000 CAPEX, €2.000/Monat OPEX

### ✅ KMU (11-100 MA):
- "Compliance-Verantwortlicher" oder "Projektleiter KI"
- "Internes Audit-Team" (ab ~50 MA)
- "PMO-Team" (ab ~50 MA, nicht vorher!)
- "Formelle Governance-Struktur"
- Review-Zyklus: "Quartalsweise"
- Budget: Max €200.000 CAPEX, €10.000/Monat OPEX

---

## 💡 BEISPIEL (Solo)

**Kontext:** Score Governance {{score_governance}}, GPT-4-Nutzung, Solo-Selbstständig

```html
<section class="section strategie-governance">
  <h2>Strategie & Governance</h2>
  
  <p>Basierend auf Ihrem Governance-Score von {{score_governance}}/100 und der Hauptleistung "{{HAUPTLEISTUNG}}" 
     werden folgende Governance-Strukturen empfohlen:</p>

  <h3>1. DSGVO-Compliance für GPT-4-Datenverarbeitung</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer (Sie - als Verantwortlicher i.S.d. DSGVO)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>AVV (Auftragsverarbeitungsvertrag) mit OpenAI unterschreiben (via OpenAI-Dashboard → DPA Download)</li>
        <li>DSFA (Datenschutz-Folgenabschätzung) für Assessment-Datenverarbeitung erstellen (Template + Anpassung)</li>
        <li>Datenschutz-Hinweise im Fragebogen ergänzen (Checkbox: "Einwilligung Datenverarbeitung")</li>
        <li>Datenfluss dokumentieren: Typeform → Backend → OpenAI → Datenbank → PDF</li>
      </ul>
    </li>
    <li><strong>Review-Zyklus:</strong> Jährlich oder bei OpenAI-AGB-Änderungen</li>
    <li><strong>Externe Unterstützung:</strong> DSGVO-Anwalt mit KI-Expertise (Pauschalhonorar)</li>
  </ul>

  <h3>2. Quality-Gate für generierte Reports</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer (Sie - manuelle Review)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>JEDER Report wird vor Kunden-Versand manuell geprüft (ca. 30 Min/Report)</li>
        <li>Checkliste: Halluzinationen? Zahlen korrekt? Empfehlungen sinnvoll? Compliance OK?</li>
        <li>Bei Batch-Processing: Stichproben-Review (z.B. 10% der Reports)</li>
        <li>Fehler-Log führen (z.B. Excel): Welche GPT-Fehler treten auf? Muster erkennbar?</li>
      </ul>
    </li>
    <li><strong>Ziel:</strong> 0 fehlerhafte Reports an Kunden, &lt; 5% Revisions-Rate</li>
  </ul>

  <h3>3. Vendor-Management & API-Monitoring</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer + Backend-Freelancer (bei Bedarf)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>OpenAI-Kosten monatlich tracken (Einfaches Sheet, Ziel: Budget einhalten)</li>
        <li>API-Uptime monitoren (z.B. kostenloser Uptime-Monitor)</li>
        <li>Azure OpenAI als Fallback vorbereiten (Account anlegen, API-Keys hinterlegen)</li>
        <li>Jährliche Review: OpenAI noch bester Anbieter? Alternativen testen?</li>
      </ul>
    </li>
  </ul>

  <h3>4. AI Act Compliance (Vorbereitung für 2026)</h3>
  <ul>
    <li><strong>Status:</strong> Assessments sind voraussichtlich "kein Hochrisiko-System" (Art. 6 AI Act)</li>
    <li><strong>Aber:</strong> Transparenzpflichten beachten (Art. 50: KI-generierte Inhalte kennzeichnen)</li>
    <li><strong>Maßnahme:</strong> Footer in jedem Report: "Dieser Report wurde KI-gestützt erstellt und 
        manuell geprüft" (ab 02.08.2026 verpflichtend)</li>
    <li><strong>Verantwortlich:</strong> Geschäftsführer (Sie)</li>
  </ul>
</section>
