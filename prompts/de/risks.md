Developer: # Risks & Mitigation - Risiken & Gegenmaßnahmen

## Zweck
Erstelle eine Risiko-Matrix (5-8 Risiken), die:
1. **Konkrete Risiken** für {{HAUPTLEISTUNG}} identifiziert (nicht generisch)
2. **Wahrscheinlichkeit** & **Auswirkung** realistisch einschätzt
3. **Konkrete Gegenmaßnahmen** definiert (keine vagen Formulierungen wie "mehr testen")
4. **Score-basierte Risiken** priorisiert (z.B. Governance < 60 → DSGVO-Risiko)

**Zielgruppe:** Risk-Owner, Geschäftsführung, Compliance-Verantwortliche  
**Stil:** Sachlich, konkret und lösungsorientiert – keine Panikmache!

---

## ⚠️ Kritische Regeln

### ❌ Verboten:
1. **Keine generischen Risiken:**
   - "Mangelnde Akzeptanz bei Mitarbeitern"
   - "Unzureichende Ressourcen"
   - "Technische Probleme möglich"
2. **Keine vagen Gegenmaßnahmen:**
   - "Regelmäßig überwachen"
   - "Schulungen durchführen"
   - "Prozesse optimieren"
3. **Keine Überdramatisierung:**
   - Wahrscheinlichkeit "Hoch" für seltene Events
   - Auswirkung "Kritisch" für kleine Probleme

### ✅ Stattdessen:
1. **Spezifisch für {{HAUPTLEISTUNG}}:**
   - "GPT-4 API Ausfall während Assessment-Batch"
   - "DSGVO-Verstoß bei Kundendaten-Verarbeitung"
   - "Halluzinationen in generierten Reports"
2. **Konkrete Maßnahmen:**
   - "Fallback auf Azure OpenAI implementieren"
   - "DSGVO-Anwalt Audit (€1.500), AVV mit OpenAI"
   - "Human-Review für alle Reports, Fact-Checking-Prozess"

---

## 💡 Beispiel: Gut vs. Schlecht

**Kontext:** GPT-4-basierte Assessments

⚠️ **Wichtig:** Die tatsächlichen Scores _müssen_ aus den Variablen `{{score_governance}}` und `{{score_sicherheit}}` übernommen werden! Niemals Beispiel-Zahlen (58, 65) verwenden!

#### ❌ Schlecht:
```html
<tr>
  <td>Technische Probleme</td>
  <td>Mittel</td>
  <td>Hoch</td>
  <td>Regelmäßige Tests durchführen</td>
</tr>
```

#### ✅ Gut:
```html
<tr>
  <td>GPT-4 API Ausfall (>1h) während Batch-Verarbeitung von 50 Assessments</td>
  <td>Mittel (1×/Quartal laut OpenAI SLA)</td>
  <td>Hoch (Lieferverzug, SLA-Breach gegenüber Kunden)</td>
  <td>Azure OpenAI als Fallback (€50/Monat Standby), automatisches Failover implementieren, SLA mit Kunden anpassen (24h statt 2h bei Batch-Processing)</td>
</tr>
```

---

## 🎯 Instruktionen

### Schritt 1: Score-basierte Risiken identifizieren

**Wenn Score < 60:**
- Governance < 60 → DSGVO/Compliance-Risiko
- Sicherheit < 60 → Data Breach, Hack-Risiko
- Befähigung < 60 → Skill-Gap, Qualitätsrisiko
- Nutzen < 60 → ROI-Verfehlungs-Risiko

### Schritt 2: Hauptleistungs-spezifische Risiken ermitteln

**Kategorien:**
1. **Technische Risiken** (API-Ausfälle, Bugs, Skalierungsprobleme)
2. **Compliance-Risiken** (DSGVO, AI Act, Branchenregulierung)
3. **Qualitätsrisiken** (Halluzinationen, Fehlerquoten, Kundenzufriedenheit)
4. **Geschäftsrisiken** (Vendor Lock-in, Kosten-Explosion, ROI-Verfehlung)
5. **Sicherheits-Risiken** (Data Breach, Unauthorized Access, DDoS)

### Schritt 3: HTML-Format

```html
<section class="section risks">
  <h2>Risiken & Gegenmaßnahmen</h2>
  <p>Basierend auf den Scores (Governance: {{score_governance}}, Sicherheit: {{score_sicherheit}}) und der Hauptleistung "{{HAUPTLEISTUNG}}" wurden 5-8 Risiken identifiziert mit konkreten Mitigations-Strategien.</p>
  <table class="table">
    <thead>
      <tr>
        <th>Risiko</th>
        <th>Wahrscheinlichkeit</th>
        <th>Auswirkung</th>
        <th>Gegenmaßnahme</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>[Konkretes Risiko für Hauptleistung, 1-2 Sätze]</td>
        <td>[Niedrig/Mittel/Hoch mit Begründung]</td>
        <td>[Niedrig/Mittel/Hoch/Kritisch mit Business Impact]</td>
        <td>[Konkrete technische/organisatorische Maßnahmen, Kosten wenn relevant]</td>
      </tr>
      <!-- 4-7 weitere Risiken -->
    </tbody>
  </table>
  <p><strong>Empfohlene Priorisierung:</strong> Sofort adressieren: [Risiken mit Wahrscheinlichkeit Mittel/Hoch + Auswirkung Hoch/Kritisch]. Monitoring: [Niedrige Wahrscheinlichkeit]. Akzeptieren: [Niedrige Auswirkung].</p>
</section>
```

---

## 🎯 Erfolgskriterien

1. 5-8 Risiken spezifisch für {{HAUPTLEISTUNG}}
2. Score-Gaps < 60 als Risiken erfasst
3. Wahrscheinlichkeit/Auswirkung realistisch
4. Gegenmaßnahmen konkret & umsetzbar
5. Kosten für Maßnahmen genannt, wenn relevant

---

**Version:** v2.1 GOLD STANDARD+
**Output:** Valides HTML (ohne Markdown-Fences!)

---

## Output Format & Verbosity

**Erforderliche HTML Output-Struktur:**
- Die Ausgabe MUSS ein einziger, gültiger HTML-Codeblock sein (keine Markdown-Fences!), der der obigen Tabellenvorlage entspricht.
- Du MUSST genau die Platzhalter {{score_governance}}, {{score_sicherheit}} und {{HAUPTLEISTUNG}} verwenden. Sie müssen als Platzhalter in der Ausgabe erscheinen oder korrekt ersetzt werden. Wenn einer dieser Werte fehlt oder kein Zahlenwert ist (bei Scores), gib ein HTML `<p class="error">` mit einer präzisen Fehlermeldung auf Deutsch aus und brich die weitere Verarbeitung ab.
- Füge NUR 5–8 der relevantesten und kritischsten Risiken ein (Priorität zuerst: score-basiert sowie höchste Auswirkung/Wahrscheinlichkeit). Falls weniger als 5 Risiken: Ergänze mit "Kein weiteres spezifisches Risiko identifiziert."-Zeilen. Bei mehr als 8 Risiken: Nur die Top 8 nach kombinierter Auswirkung und Wahrscheinlichkeit aufnehmen.
- Risiken in der Tabelle nach Kritikalität (Auswirkung: Kritisch/Hoch zuerst), dann Wahrscheinlichkeit (Hoch/Mittel/Niedrig) sortieren.
- Nur die Spalten Risiko, Wahrscheinlichkeit, Auswirkung, Gegenmaßnahme zeigen. Weitere Felder (wie Risiko-Owner, Kategorie) nur auf Anforderung einbauen.
- Für Fehler (fehlt eine Variable):
  ```html
  <p class="error">Fehler: Der Wert für "score_governance" fehlt oder ist ungültig. Bitte prüfen Sie Ihre Eingabe.</p>
  ```
- Gib IMMER ein valides HTML aus, das direkt im Browser gerendert werden kann.

**Antwortlänge:**
- Schreibe alle Risiken und Gegenmaßnahmen als kurze, präzise Einträge (pro Zelle maximal 2 Sätze/1-2 Zeilen).
- Gesamte Tabelle: höchstens 8 Risiken.
- Zusätzliche Hinweise und Priorisierung: je maximal 2 Sätze.

**Antwort muss vollständig und direkt umsetzbar sein, nicht vorzeitig abbrechen. Priorisiere vollständige, umsetzbare Antworten innerhalb dieses Längenrahmens.**