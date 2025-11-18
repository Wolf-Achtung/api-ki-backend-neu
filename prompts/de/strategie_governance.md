# PROMPT: Strategie & Governance - KI-Governance-Strukturen

## ZWECK
Erstelle konkrete Governance-Empfehlungen die:
1. **Score-Gaps adressieren** (z.B. Governance < 60 → DSGVO-Prozesse)
2. **Spezifisch für {{HAUPTLEISTUNG}}** sind (nicht generisch!)
3. **Rollen & Verantwortlichkeiten** definieren
4. **Konkrete Prozesse** beschreiben (nicht "etablieren Sie...")

**Zielgruppe:** Geschäftsführung, Compliance-Officer, Risk-Owner
**Stil:** Strukturiert, compliance-fokussiert, pragmatisch

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE generischen Governance-Tipps:**
   - ❌ "KI-Beirat einrichten"
   - ❌ "Regelmäßige Reviews durchführen"
   - ❌ "Richtlinien erstellen"

2. **KEINE Rollen für Solo/Kleine Teams:**
   - ❌ "Chief AI Officer ernennen" (bei 1-5 MA!)
   - ❌ "KI-Steuerungsausschuss" (unrealistisch!)

### ✅ STATTDESSEN:
1. **Spezifisch für {{HAUPTLEISTUNG}}:**
   - ✅ "DSGVO-Prozess für GPT-4-Assessment-Daten"
   - ✅ "Quality-Gate für generierte Reports"
   - ✅ "AVV mit OpenAI unterschreiben"

2. **Realistisch für Unternehmensgröße:**
   - ✅ Solo: Externe Auditoren, Checklisten
   - ✅ Team 5-50: Ein Verantwortlicher + externe Unterstützung
   - ✅ Team 50+: Dedizierte Governance-Rolle

---

## 💡 BEISPIEL

**Kontext:** Score Governance 58, GPT-4-Nutzung, Solo-Selbstständig

#### ✅ GUT:

```html
<section class="section strategie-governance">
  <h2>Strategie & Governance</h2>
  
  <p>Basierend auf Score Governance: 58/100 (ausbaufähig) und der Hauptleistung "GPT-4-basierte Assessments" 
     werden folgende Governance-Strukturen empfohlen:</p>

  <h3>1. DSGVO-Compliance für GPT-4-Datenverarbeitung</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer (als Verantwortlicher i.S.d. DSGVO)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>AVV mit OpenAI unterschreiben (via OpenAI-Dashboard → DPA Download)</li>
        <li>DSFA für Assessment-Datenverarbeitung erstellen (€500 Template + Anpassung)</li>
        <li>Datenschutz-Hinweise im Fragebogen ergänzen (Checkbox: "Einwilligung Datenverarbeitung")</li>
        <li>Datenfluss dokumentieren: Typeform → Backend → OpenAI → PostgreSQL → PDF</li>
      </ul>
    </li>
    <li><strong>Review-Zyklus:</strong> Jährlich oder bei OpenAI-AGB-Änderungen</li>
    <li><strong>Kosten:</strong> €2.000 einmalig (DSGVO-Anwalt), €0 laufend</li>
  </ul>

  <h3>2. Quality-Gate für generierte Reports</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer (manuelle Review)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>JEDER Report wird vor Kunden-Versand manuell geprüft (30 Min/Report)</li>
        <li>Checkliste: Halluzinationen? Zahlen korrekt? Empfehlungen sinnvoll? Compliance OK?</li>
        <li>Bei Batch-Processing: Stichproben-Review (10% der Reports = 5 von 50)</li>
        <li>Fehler-Log führen: Welche GPT-Fehler treten auf? Pattern erkennbar?</li>
      </ul>
    </li>
    <li><strong>Ziel:</strong> 0 fehlerhafte Reports an Kunden, < 5% Revisions-Rate</li>
  </ul>

  <h3>3. Vendor-Management & API-Monitoring</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer + Backend-Dev (Freelance)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>OpenAI-Kosten monatlich tracken (Target: < €200/Monat)</li>
        <li>API-Uptime monitoren (Simple Uptime Monitor, kostenlos)</li>
        <li>Azure OpenAI als Fallback vorbereiten (Standby-Account anlegen, API-Keys hinterlegen)</li>
        <li>Quartalweise Review: OpenAI noch bester Anbieter? Alternative Modelle testen?</li>
      </ul>
    </li>
  </ul>

  <h3>4. AI Act Compliance (Vorbereitung für 2026)</h3>
  <ul>
    <li><strong>Status:</strong> Assessments sind "Kein Hochrisiko-System" (Art. 6 AI Act)</li>
    <li><strong>Aber:</strong> Transparenzpflichten beachten (Art. 50: KI-generierte Inhalte kennzeichnen)</li>
    <li><strong>Maßnahme:</strong> Footer in jedem Report: "Dieser Report wurde KI-gestützt erstellt und 
        manuell geprüft" (ab 02.08.2026 verpflichtend)</li>
  </ul>
</section>
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

### SCHRITT 3: Realistische Rollen

**Solo/Klein (1-5 MA):**
- Geschäftsführer als Hauptverantwortlicher
- Externe Auditoren (Anwalt, Security-Firma)
- Checklisten statt Prozess-Dokumente

**Mittel (6-50 MA):**
- 1 Verantwortlicher für KI/Compliance
- Externe Unterstützung für Audits
- Einfache Prozess-Dokumente

**Groß (50+ MA):**
- Dedizierte Compliance/Governance-Rolle
- Internes Audit-Team
- Formelle Governance-Struktur

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ Adressiert Score-Gaps < 60
2. ✅ Spezifisch für {{HAUPTLEISTUNG}}
3. ✅ Rollen realistisch für Unternehmensgröße
4. ✅ Konkrete Prozesse (nicht "etablieren Sie...")
5. ✅ Kosten & Review-Zyklen genannt

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML (keine Markdown-Fences!)
