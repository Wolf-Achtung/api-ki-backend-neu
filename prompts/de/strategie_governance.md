<!-- strategie_governance.md - v2.2 GOLD STANDARD+ -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.
     VERSION: 2.2 GOLD STANDARD+ (Size-Awareness Fix) -->

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

**Kontext:** Score Governance 58, GPT-4-Nutzung, Solo-Selbstständig

```html
<section class="section strategie-governance">
  <h2>Strategie & Governance</h2>
  
  <p>Basierend auf Score Governance: 58/100 (ausbaufähig) und der Hauptleistung "{{HAUPTLEISTUNG}}" 
     werden folgende Governance-Strukturen empfohlen:</p>

  <h3>1. DSGVO-Compliance für GPT-4-Datenverarbeitung</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer (Sie - als Verantwortlicher i.S.d. DSGVO)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>AVV mit OpenAI unterschreiben (via OpenAI-Dashboard → DPA Download)</li>
        <li>DSFA für Assessment-Datenverarbeitung erstellen (€500 Template + Anpassung)</li>
        <li>Datenschutz-Hinweise im Fragebogen ergänzen (Checkbox: "Einwilligung Datenverarbeitung")</li>
        <li>Datenfluss dokumentieren: Typeform → Backend → OpenAI → PostgreSQL → PDF</li>
      </ul>
    </li>
    <li><strong>Review-Zyklus:</strong> Jährlich oder bei OpenAI-AGB-Änderungen</li>
    <li><strong>Externe Unterstützung:</strong> DSGVO-Anwalt mit KI-Expertise (€2.000 einmalig)</li>
    <li><strong>Kosten:</strong> €2.000 einmalig (DSGVO-Anwalt), €0 laufend</li>
  </ul>

  <h3>2. Quality-Gate für generierte Reports</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer (Sie - manuelle Review)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>JEDER Report wird vor Kunden-Versand manuell geprüft (30 Min/Report)</li>
        <li>Checkliste: Halluzinationen? Zahlen korrekt? Empfehlungen sinnvoll? Compliance OK?</li>
        <li>Bei Batch-Processing: Stichproben-Review (10% der Reports = 5 von 50)</li>
        <li>Fehler-Log führen (Excel): Welche GPT-Fehler treten auf? Pattern erkennbar?</li>
      </ul>
    </li>
    <li><strong>Ziel:</strong> 0 fehlerhafte Reports an Kunden, < 5% Revisions-Rate</li>
  </ul>

  <h3>3. Vendor-Management & API-Monitoring</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer + Backend-Freelancer (bei Bedarf)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>OpenAI-Kosten monatlich tracken (Simple Excel/Google Sheet, Target: < €200/Monat)</li>
        <li>API-Uptime monitoren (Simple Uptime Monitor, kostenlos)</li>
        <li>Azure OpenAI als Fallback vorbereiten (Standby-Account anlegen, API-Keys hinterlegen)</li>
        <li>Jährliche Review: OpenAI noch bester Anbieter? Alternative Modelle testen?</li>
      </ul>
    </li>
  </ul>

  <h3>4. AI Act Compliance (Vorbereitung für 2026)</h3>
  <ul>
    <li><strong>Status:</strong> Assessments sind "Kein Hochrisiko-System" (Art. 6 AI Act)</li>
    <li><strong>Aber:</strong> Transparenzpflichten beachten (Art. 50: KI-generierte Inhalte kennzeichnen)</li>
    <li><strong>Maßnahme:</strong> Footer in jedem Report: "Dieser Report wurde KI-gestützt erstellt und 
        manuell geprüft" (ab 02.08.2026 verpflichtend)</li>
    <li><strong>Verantwortlich:</strong> Geschäftsführer (Sie)</li>
  </ul>
</section>
```

---

## 💡 BEISPIEL (Klein 2-10 MA)

```html
<h3>1. DSGVO-Compliance für KI-Datenverarbeitung</h3>
<ul>
  <li><strong>Verantwortlich:</strong> Geschäftsführer + designierter Datenschutz-Verantwortlicher (1 Mitarbeiter)</li>
  <li><strong>Prozess:</strong>
    <ul>
      <li>AVV mit AI-Providern unterschreiben</li>
      <li>DSFA durch externen Datenschutzbeauftragten (€3.000)</li>
      <li>Internes Datenschutz-Briefing für Team (2h Workshop)</li>
    </ul>
  </li>
  <li><strong>Review-Zyklus:</strong> Halbjährlich durch Datenschutz-Verantwortlichen</li>
</ul>
```

---

## 💡 BEISPIEL (KMU 11-100 MA)

```html
<h3>1. DSGVO-Compliance & KI-Governance-Framework</h3>
<ul>
  <li><strong>Verantwortlich:</strong> Compliance-Officer + IT-Leiter</li>
  <li><strong>Governance-Struktur:</strong>
    <ul>
      <li>KI-Steering Committee (GF, Compliance, IT, Fachbereich) - quartalsweise</li>
      <li>Projektleiter KI verantwortet Umsetzung</li>
      <li>Interner Datenschutzbeauftragter prüft alle KI-Projekte</li>
    </ul>
  </li>
  <li><strong>Prozess:</strong>
    <ul>
      <li>Formelles KI-Projekt-Register (alle KI-Systeme erfassen)</li>
      <li>DSFA-Prozess für Hochrisiko-Systeme</li>
      <li>Vierteljährliche Compliance-Reviews</li>
    </ul>
  </li>
  <li><strong>Review-Zyklus:</strong> Quartalsweise durch Steering Committee</li>
</ul>
```

---

## 🎯 INSTRUKTIONEN

### SCHRITT 1: Score-Gap-Analyse

**Wenn Governance-Score < 60:**
- Fokus auf DSGVO-Compliance!
- Prozesse für Datenverarbeitung definieren
- AVV mit Providern prüfen

**Wenn Sicherheit-Score < 60:**
- Cyber-Security-Maßnahmen
- Penetration-Tests
- Access-Control

### SCHRITT 2: Hauptleistungs-spezifische Governance

**Wenn GPT-Nutzung:**
- DSGVO-AVV
- Quality-Gates
- Halluzinations-Prävention

**Wenn Kundendaten:**
- Datenschutz-Prozesse
- Einwilligungen
- Datenminimierung

### SCHRITT 3: SIZE-AWARE Rollen zuweisen

**Nutze die SIZE-APPROPRIATE LANGUAGE Tabelle oben!**

1. Check {{COMPANY_SIZE}}
2. Wähle passende Rollen aus der Tabelle
3. Passe Budget-Ranges an
4. Passe Review-Zyklen an

---

## ✅ PRE-OUTPUT VALIDATION

**PRÜFE JEDEN PUNKT:**

1. [ ] **Rollen passen zur Größe {{COMPANY_SIZE}}?**
   - Solo: KEIN "PMO-Team", KEIN "Change Manager"
   - Klein: KEIN "Abteilungsleiter", KEIN "Steering Committee"
   - KMU: OK für formelle Strukturen

2. [ ] **Budget-Ranges realistisch?**
   - Solo: Max €10k CAPEX, €500/Mo OPEX
   - Klein: Max €50k CAPEX, €2k/Mo OPEX
   - KMU: Max €200k CAPEX, €10k/Mo OPEX

3. [ ] **Review-Zyklen größen-angemessen?**
   - Solo: Jährlich
   - Klein: Halbjährlich
   - KMU: Quartalsweise

4. [ ] **Governance spezifisch für {{HAUPTLEISTUNG}}?**
   - NICHT generisch!

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ Adressiert Score-Gaps < 60
2. ✅ Spezifisch für {{HAUPTLEISTUNG}}
3. ✅ Rollen SIZE-AWARE und realistisch
4. ✅ Konkrete Prozesse (nicht "etablieren Sie...")
5. ✅ Kosten & Review-Zyklen größen-angemessen

**Wenn ALLE ✅ → Output generieren!**

---

**VERSION:** v2.2 GOLD STANDARD+ (Size-Awareness Fixed)  
**AUSGABE:** Valides HTML (keine Markdown-Fences!)
