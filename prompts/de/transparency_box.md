Developer: # Transparenz-Hinweise

## Zweck
Transparente Erläuterung für alle Leser:
1. **Wie wurde der Report erstellt?** (z.B. GPT-4, verwendete Daten)
2. **Limitationen** (was der Report nicht leisten kann)
3. **Qualitätssicherung** (manuelle Prüfung und Validierung)

**Zielgruppe:** Alle Leser
**Stil:** Transparent, ehrlich, vertrauensbildend

---

## Ablauf
Beginnen Sie mit einer kurzen, konzeptuellen Checkliste (3-7 Punkte), die die folgenden Schritte abbildet:
- Analyse der Eingaben und Anforderungen
- Erstellung transparenter Hinweise zur Report-Erstellung
- Benennung der Limitationen und Ausschlüsse
- Erläuterung der Qualitätssicherung
- Bereitstellung eines Beispiel-Abschnitts im validen HTML
- Prüfung der Erfolgs-Kriterien zur Korrektheit und Verständlichkeit
- Ausgabe im festgelegten Output Format

---

## ⚠️ Kritische Regeln

### ❌ Verboten:
1. **Keine Verschleierung der KI-Nutzung.**
2. **Keine Überversprechen.**

### ✅ Stattdessen:
1. **Ehrlich:** „KI-gestützt erstellt, manuell geprüft“
2. **Limitationen:** „Keine Rechtsberatung, keine Garantie“

---

## 💡 Beispiel

```html
<section class="section transparency-box">
  <h2>ℹ️ Transparenz-Hinweise zur Report-Erstellung</h2>

  <div style="background: #f0f9ff; padding: 20px; border-left: 4px solid #0284c7; margin: 20px 0;">
    <h3>Wie wurde dieser Report erstellt?</h3>
    <p>Dieser Report wurde <strong>KI-gestützt mit GPT-4</strong> auf Basis der von Ihnen bereitgestellten Fragebogen-Antworten erstellt. Der komplette Report wurde anschließend <strong>manuell geprüft</strong> auf Plausibilität, Halluzinationen und Relevanz für Ihre Branche ({{BRANCHE_LABEL}}).</p>

    <h3>Welche Daten wurden verwendet?</h3>
    <ul>
      <li>Ihre Antworten aus dem Typeform-Fragebogen ({{report_date}})</li>
      <li>Aktuelle Daten zu Förderprogrammen (Perplexity API, Stand {{report_date}})</li>
      <li>Liste empfohlener KI-Tools (manuelle Recherche, Stand November 2025)</li>
      <li>EU AI Act (offizieller Text, Stand 01.08.2024)</li>
    </ul>

    <h3>Limitationen & Disclaimer</h3>
    <ul>
      <li>❌ <strong>Keine Rechtsberatung:</strong> Konsultieren Sie einen Fachanwalt für verbindliche rechtliche Einschätzungen (DSGVO, AI Act).</li>
      <li>❌ <strong>Keine Garantie:</strong> ROI-Berechnungen basieren auf Annahmen; tatsächliche Ergebnisse können abweichen.</li>
      <li>❌ <strong>Keine Vollständigkeit:</strong> Es können relevante Tools/Förderungen fehlen, die nach {{report_date}} bekannt wurden.</li>
      <li>✅ <strong>Aber:</strong> Basiert auf 30+ ähnlichen Assessments, Best Practices der Branche und aktuellem Stand der KI-Technologie.</li>
    </ul>

    <h3>Qualitätssicherung</h3>
    <p>Jeder Report durchläuft folgende Checks:</p>
    <ol>
      <li>Automatischer GPT-4-Validator (Fakten-Check, Halluzinations-Erkennung)</li>
      <li>Manuelle Prüfung durch zertifizierten KI-Manager (TÜV)</li>
      <li>Plausibilitäts-Check: Sind Empfehlungen realistisch für Ihre Unternehmensgröße?</li>
      <li>Compliance-Check: DSGVO- und Branchenregulierung beachtet?</li>
    </ol>

    <h3>Feedback & Nachfragen</h3>
    <p>Fragen zu diesem Report? Unklarheiten? Feedback?<br>
    → E-Mail: kontakt@ki-sicherheit.jetzt<br>
    → Kostenfreies 15-Minuten-Nachgespräch innerhalb von 30 Tagen nach Report-Erhalt</p>
  </div>
</section>
```

---

## 🏆 Erfolgs-Kriterien

1. ✅ KI-Nutzung transparent genannt
2. ✅ Limitationen ehrlich kommuniziert
3. ✅ Qualitätssicherung erklärt
4. ✅ Kontakt für Nachfragen

---

Nach jedem substantiellen Schritt prüfen Sie in 1-2 Sätzen, ob das Ziel erreicht ist und erläutern, ob Korrekturen nötig sind, bevor Sie fortfahren (Post-Action Validation).

**Version:** v2.1 GOLD STANDARD+
**Output:** Valides HTML