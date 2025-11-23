<!-- strategie_governance.md - v2.4 GOLD STANDARD+ -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.
     VERSION: 2.4 GOLD STANDARD+ (Size-Awareness + Score-Sync Fix) -->

# PROMPT: Strategie & Governance - KI-Governance-Strukturen

## ⚠️ SIZE-AWARENESS - ABSOLUT PFLICHT!

**Mögliche Unternehmensgrößen (NUR diese 3!):**
- `{{COMPANY_SIZE}}` = "solo" → Label: "1 (Solo-Selbstständig/Freiberuflich)"
- `{{COMPANY_SIZE}}` = "team" → Label: "2-10 (Kleines Team)"  
- `{{COMPANY_SIZE}}` = "kmu"  → Label: "11-100 (KMU)"

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

Erstelle konkrete Governance-Empfehlungen, die:

1. **Score-Gaps adressieren** (z.B. Governance < 60 → DSGVO-Prozesse priorisieren)
2. **Spezifisch für {{HAUPTLEISTUNG}}** sind (nicht generisch!)
3. **Rollen & Verantwortlichkeiten SIZE-AWARE** definieren
4. **Konkrete Prozesse** beschreiben (nicht nur: „etablieren Sie …“)

**Zielgruppe:** Geschäftsführung, Compliance-Officer, Risk-Owner  
**Stil:** Strukturiert, compliance-fokussiert, pragmatisch, größen-angemessen

---

## ⛔ ABSOLUT VERBOTEN

### ❌ GENERISCHE Governance-Tipps
- ❌ "KI-Beirat einrichten"
- ❌ "Regelmäßige Reviews durchführen"
- ❌ "Richtlinien erstellen"
- ❌ "Governance-Strukturen aufbauen"

### ❌ UNREALISTISCHE Rollen für die Größe
- ❌ "Chief AI Officer" bei Solo/Klein
- ❌ "PMO-Team" bei Solo oder Team (2-10 MA)
- ❌ "KI-Steuerungsausschuss" bei Solo
- ❌ "Change Manager" bei Team (2-10 MA)

### ❌ SCORE-CHAOS
- ❌ Feste Beispielzahlen wie "Score Governance: 55/100" oder "58/100"
- ❌ Abweichende Governance-Scores in Text vs. Scorecard
- ❌ Eigene Scores erfinden

---

## ✅ STATTDESSEN: SIZE-APPROPRIATE!

### ✅ Solo (1 MA)
- "Geschäftsführer (Sie)"
- "Externe Auditoren: DSGVO-Anwalt, Security-Pentest nach Bedarf"
- "Checklisten statt Prozess-Handbücher"
- Review-Zyklus: "Jährlich" oder "Bei Bedarf"
- Budget-Richtwert: max. €10.000 CAPEX, €500/Monat OPEX

### ✅ Klein (2-10 MA)
- "Geschäftsführer + verantwortlicher Mitarbeiter"
- "Externe Unterstützung für komplexe Themen (Anwalt, Auditor)"
- "Einfache Prozess-Dokumente (1-2 Seiten)"
- Review-Zyklus: "Halbjährlich"
- Budget-Richtwert: max. €50.000 CAPEX, €2.000/Monat OPEX

### ✅ KMU (11-100 MA)
- "Compliance-Verantwortlicher" oder "Projektleiter KI"
- "Internes Audit-Team" (ab ~50 MA)
- "Formelle Governance-Struktur / Steering Committee"
- Review-Zyklus: "Quartalsweise"
- Budget-Richtwert: max. €200.000 CAPEX, €10.000/Monat OPEX

---

## 💡 BEISPIEL (Solo – Score-Sync!)

**Kontext:** Score Governance {{score_governance}}, GPT-4-Nutzung, Solo-Selbstständig

```html
<section class="section strategie-governance">
  <h2>Strategie &amp; Governance</h2>
  
  <p>Basierend auf Ihrem Governance-Score von {{score_governance}}/100 und der Hauptleistung
     "{{HAUPTLEISTUNG}}" werden folgende Governance-Strukturen empfohlen:</p>

  <h3>1. DSGVO-Compliance für GPT-4-Datenverarbeitung</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer (Sie – Verantwortlicher i.S.d. DSGVO)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>AVV (Auftragsverarbeitungsvertrag) mit OpenAI im Dashboard prüfen/abschließen</li>
        <li>DSFA (Datenschutz-Folgenabschätzung) für Assessment-Daten erstellen (Template anpassen)</li>
        <li>Datenschutz-Hinweise im Fragebogen ergänzen (Checkbox: „Einwilligung Datenverarbeitung“)</li>
        <li>Datenfluss dokumentieren: Typeform → Backend → OpenAI → Datenbank → PDF</li>
      </ul>
    </li>
    <li><strong>Review-Zyklus:</strong> Jährlich oder bei OpenAI-AGB-Änderungen</li>
    <li><strong>Externe Unterstützung:</strong> DSGVO-Anwalt mit KI-Expertise (Pauschalhonorar)</li>
  </ul>

  <h3>2. Quality-Gate für generierte Reports</h3>
  <ul>
    <li><strong>Verantwortlich:</strong> Geschäftsführer (manuelle Endabnahme)</li>
    <li><strong>Prozess:</strong>
      <ul>
        <li>Jeder Report wird vor Versand kurz geprüft (ca. 20–30 Min/Report)</li>
        <li>Checkliste: Zahlenkonsistenz, Halluzinationen, Förderprogramme, Compliance-Hinweise</li>
        <li>Fehler-Log führen (z.B. Tabelle): Welche Fehler treten auf, wie oft, in welchem Abschnitt?</li>
      </ul>
    </li>
    <li><strong>Ziel:</strong> 0 fehlerhafte Reports beim Kunden, &lt; 5&nbsp;% Nachbesserungsquote</li>
  </ul>

  <h3>3. Leichtgewichtige KI-Governance</h3>
  <ul>
    <li><strong>Policy:</strong> 1-seitige KI-Nutzungsrichtlinie (zulässige Tools, Datentypen, No-Gos)</li>
    <li><strong>Dokumentation:</strong> Einfache Liste aller genutzten KI-Tools (Zweck, Daten, Risiken)</li>
    <li><strong>Review:</strong> Halbjährliches Kurz-Review: Passen Tools, Kosten, Risiken noch?</li>
  </ul>
</section>
