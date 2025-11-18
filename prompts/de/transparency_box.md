# PROMPT: Transparenz-Hinweise

## ZWECK
Erkläre transparent:
1. **Wie wurde Report erstellt** (GPT-4, welche Daten)
2. **Limitationen** (was Report NICHT kann)
3. **Qualitätssicherung** (manuelle Prüfung)

**Zielgruppe:** Alle Leser
**Stil:** Transparent, ehrlich, vertrauensbildend

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE Verschleierung der KI-Nutzung**
2. **KEINE Überversprechen**

### ✅ STATTDESSEN:
1. **Ehrlich:** "KI-gestützt erstellt, manuell geprüft"
2. **Limitationen:** "Keine Rechtsberatung, keine Garantie"

---

## 💡 BEISPIEL

```html
<section class="section transparency-box">
  <h2>ℹ️ Transparenz-Hinweise zur Report-Erstellung</h2>

  <div style="background: #f0f9ff; padding: 20px; border-left: 4px solid #0284c7; margin: 20px 0;">
    
    <h3>Wie wurde dieser Report erstellt?</h3>
    <p>Dieser Report wurde <strong>KI-gestützt mit GPT-4</strong> erstellt auf Basis der von Ihnen 
       bereitgestellten Fragebogen-Antworten. Der komplette Report wurde anschließend <strong>manuell 
       geprüft</strong> auf Plausibilität, Halluzinationen und Relevanz für Ihre Branche 
       ({{BRANCHE_LABEL}}).</p>

    <h3>Welche Daten wurden verwendet?</h3>
    <ul>
      <li>Ihre Antworten aus dem Typeform-Fragebogen ({{report_date}})</li>
      <li>Aktuelle Daten zu Förderprogrammen (Perplexity API, Stand {{report_date}})</li>
      <li>Liste empfohlener KI-Tools (manuelle Recherche, Stand November 2025)</li>
      <li>EU AI Act (offizieller Text, Stand 01.08.2024)</li>
    </ul>

    <h3>Limitationen & Disclaimer</h3>
    <ul>
      <li>❌ <strong>Keine Rechtsberatung:</strong> Konsultieren Sie Fachanwalt für verbindliche 
          rechtliche Einschätzungen (DSGVO, AI Act)</li>
      <li>❌ <strong>Keine Garantie:</strong> ROI-Berechnungen basieren auf Annahmen, tatsächliche 
          Ergebnisse können abweichen</li>
      <li>❌ <strong>Keine Vollständigkeit:</strong> Es können relevante Tools/Förderungen fehlen, 
          die nach {{report_date}} bekannt wurden</li>
      <li>✅ <strong>BUT:</strong> Basiert auf 30+ ähnlichen Assessments, Best Practices der Branche, 
          aktuellem Stand der KI-Technologie</li>
    </ul>

    <h3>Qualitätssicherung</h3>
    <p>Jeder Report durchläuft folgende Checks:</p>
    <ol>
      <li>Automatischer GPT-4-Validator (Fakten-Check, Halluzinations-Erkennung)</li>
      <li>Manuelle Prüfung durch zertifizierten KI-Manager (TÜV)</li>
      <li>Plausibilitäts-Check: Sind Empfehlungen realistisch für Ihre Größe?</li>
      <li>Compliance-Check: DSGVO, Branchenregulierung beachtet?</li>
    </ol>

    <h3>Feedback & Nachfragen</h3>
    <p>Fragen zu diesem Report? Unklarheiten? Feedback?<br>
       → E-Mail: kontakt@ki-sicherheit.jetzt<br>
       → Kostenfreies 15-Min-Nachgespräch innerhalb 30 Tagen nach Report-Erhalt</p>

  </div>
</section>
```

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ KI-Nutzung transparent genannt
2. ✅ Limitationen ehrlich kommuniziert
3. ✅ Qualitätssicherung erklärt
4. ✅ Kontakt für Nachfragen

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML
