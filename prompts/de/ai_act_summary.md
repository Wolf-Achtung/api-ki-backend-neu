# PROMPT: EU AI Act - Rechtliche Zusammenfassung

## ZWECK
Erstelle eine prägnante AI Act-Zusammenfassung die:
1. **Relevanz für {{HAUPTLEISTUNG}}** prüft (Hochrisiko-System ja/nein?)
2. **Konkrete Fristen** nennt (02.08.2025, 02.08.2026, 02.08.2027)
3. **Pflichten** spezifisch für das Unternehmen auflistet
4. **KEINE Rechtsberatung** (Disclaimer!)

**Zielgruppe:** Compliance-Officer, Geschäftsführung, Legal
**Stil:** Sachlich, präzise, keine Panikmache

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE Rechtsberatung geben:**
   - ❌ "Sie müssen X tun"
   - ✅ "Laut AI Act könnte X relevant sein (Anwalt konsultieren!)"

2. **KEINE falsche Risikoklasse:**
   - ❌ Jedes KI-System als "Hochrisiko" einstufen
   - ✅ Realistische Bewertung basierend auf Art. 6 AI Act

3. **KEINE veralteten Fristen:**
   - ❌ Fristen von vor 2024 nutzen
   - ✅ Finale Fristen: 02.08.2025 (verbotene Systeme), 02.08.2026 (Hochrisiko), 02.08.2027 (GPAI)

### ✅ STATTDESSEN:
1. **Spezifische Bewertung:**
   - "GPT-4-Assessments: KEIN Hochrisiko-System (Art. 6)"
   - "Aber: Transparenzpflicht (Art. 50)"

2. **Konkrete nächste Schritte:**
   - "Footer in Reports: 'KI-gestützt erstellt' (ab 02.08.2026)"
   - "Anwalt mit AI Act-Expertise konsultieren (€500-1.500)"

---

## 💡 BEISPIEL

**Kontext:** GPT-4-basierte Assessments

#### ✅ GUT:

```html
<section class="section ai-act">
  <h2>EU AI Act – Zusammenfassung & Termine</h2>
  
  <p><strong>Hinweis:</strong> Dies ist keine Rechtsberatung. Konsultieren Sie einen 
     Fachanwalt für IT-Recht mit AI Act-Expertise.</p>

  <h3>Relevanz für "{{HAUPTLEISTUNG}}"</h3>
  <p><strong>Bewertung:</strong> "GPT-4-basierte KI-Readiness-Assessments" sind nach aktueller 
     Einschätzung <strong>KEIN Hochrisiko-System</strong> gemäß Art. 6 AI Act, da:</p>
  <ul>
    <li>Keine Biometrie / kein Social Scoring</li>
    <li>Keine kritische Infrastruktur</li>
    <li>Keine Strafverfolgung / Migration / Rechtsprechung</li>
    <li>Keine Beschäftigungsentscheidungen (nur Analyse, kein Hiring-Tool)</li>
  </ul>
  
  <p><strong>ABER:</strong> Transparenzpflichten greifen!</p>

  <h3>Relevante Pflichten (Art. 50: Transparenz)</h3>
  <ul>
    <li><strong>Ab 02.08.2026:</strong> KI-generierte Inhalte MÜSSEN als solche gekennzeichnet werden</li>
    <li><strong>Konkret:</strong> Footer in jedem Assessment-Report: 
        "Dieser Report wurde KI-gestützt (GPT-4) erstellt und manuell geprüft."</li>
    <li><strong>Aufwand:</strong> 1h Entwicklung, €0 Kosten</li>
  </ul>

  <h3>Wichtige Fristen</h3>
  <table class="table">
    <thead><tr><th>Datum</th><th>Was gilt?</th><th>Relevanz für uns?</th></tr></thead>
    <tbody>
      <tr>
        <td>02.08.2025</td>
        <td>Verbotene KI-Systeme (Art. 5)</td>
        <td>Nicht relevant (keine Social Scoring, Manipulation, etc.)</td>
      </tr>
      <tr>
        <td>02.08.2026</td>
        <td>Hochrisiko-Systeme (Art. 6) + Transparenz (Art. 50)</td>
        <td><strong>RELEVANT:</strong> Transparenzpflicht ab diesem Datum!</td>
      </tr>
      <tr>
        <td>02.08.2027</td>
        <td>GPAI-Modelle (Art. 51-56)</td>
        <td>Nicht relevant (nutzen GPT-4, entwickeln nicht selbst)</td>
      </tr>
    </tbody>
  </table>

  <h3>Empfohlene nächste Schritte</h3>
  <ol>
    <li><strong>Jetzt (Monat 1):</strong> Anwalt mit AI Act-Expertise konsultieren (€500-1.500 für Erstberatung), 
        Risikoklasse final bestätigen lassen</li>
    <li><strong>Bis 01.06.2026:</strong> Footer-Text in Report-Template ergänzen, Tests durchführen</li>
    <li><strong>Ab 02.08.2026:</strong> Alle Reports mit AI-Kennzeichnung versenden</li>
  </ol>

  <h3>Risiken bei Non-Compliance</h3>
  <ul>
    <li>Bußgelder bis €35 Mio oder 7% des weltweiten Jahresumsatzes (Art. 99)</li>
    <li>Für KMUs: Faktisch €10.000-50.000 bei Transparenzverletzungen (erfahrungsbasiert)</li>
    <li>Reputationsrisiko: Kunden fordern AI Act-Compliance</li>
  </ul>

  <p><strong>Hinweis:</strong> Stand {{report_date}}. AI Act ist seit 01.08.2024 in Kraft, 
     Details können sich durch Durchführungsverordnungen ändern. Jährliche Review empfohlen.</p>
</section>
```

---

## 🎯 INSTRUKTIONEN

### SCHRITT 1: Risikoklasse bestimmen

**Art. 6 AI Act - Hochrisiko-Systeme:**
- Biometrische Identifikation
- Kritische Infrastruktur
- Bildung & Beschäftigung (Hiring, Performance-Bewertung)
- Strafverfolgung, Migration, Rechtsprechung

**Für {{HAUPTLEISTUNG}} prüfen:**
- Trifft System automatische Entscheidungen über Menschen?
- Wird es für Hiring, Firing, Beförderungen genutzt?
- → Wenn JA: Hochrisiko! Wenn NEIN: Nur Transparenz!

### SCHRITT 2: Relevante Pflichten ableiten

**Transparenzpflichten (Art. 50):**
- ALLE KI-generierten Texte, Bilder, Videos, Audio
- MÜSSEN als KI-generiert gekennzeichnet sein
- Ab 02.08.2026 verpflichtend

**Hochrisiko-Pflichten (Art. 9-15):**
- Risikomanagementsystem
- Datenqualität & Governance
- Technische Dokumentation
- Human Oversight
- Nur wenn Hochrisiko-System!

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ Risikoklasse korrekt für {{HAUPTLEISTUNG}}
2. ✅ Konkrete Fristen genannt
3. ✅ Umsetzbare nächste Schritte
4. ✅ Disclaimer "Keine Rechtsberatung"
5. ✅ Realistische Bußgeld-Risiken

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML (keine Markdown-Fences!)
