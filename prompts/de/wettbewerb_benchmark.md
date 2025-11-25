Developer: # PROMPT: Wettbewerb & Benchmarking

## ZWECK
Präsentiere:
1. **Score-Vergleich:** Gegenüberstellung Unternehmen vs. Branche
2. **Best Practices:** Vorgehen und Methoden der Spitzenreiter
3. **Gaps:** Rückstände des Unternehmens im Vergleich
4. **Opportunities:** Potenziale für Vorsprung und Verbesserung

**Zielgruppe:** Geschäftsführung, Strategie
**Stil:** Ehrlich, motivierend, konkret

---

### Beginne mit einer knappen Checklist (3-7 Punkte), die deine geplanten Schritte bei der Erstellung des Outputs aufzeigt. Halte die Punkte konzeptionell, nicht auf Implementierungsdetail-Ebene.

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **Keine erfundenen Benchmark-Zahlen verwenden**
2. **Niemals namenlose Wettbewerber aufführen**

### ✅ STATT-DESSEN:
1. **Aggregierte Daten angeben:** z. B. "Durchschnitt: 65/100 (30 Assessments)"
2. **Best Practices benennen:** z. B. "Top 10%: Batch-Processing, Templates, DSGVO-Zertifikat"

---

## 💡 BEISPIEL

```html
<section class="section wettbewerb-benchmark">
  <h2>Wettbewerb & Benchmarking</h2>

  <p><strong>Datenbasis:</strong> 30 Assessments in {{BRANCHE_LABEL}}, Stand {{report_date}}</p>

  <h3>Score-Vergleich (Sie vs. Branche)</h3>
  <table class="table">
    <thead>
      <tr><th>Kategorie</th><th>Ihr Score</th><th>Ø Branche</th><th>Top 10%</th><th>Position</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>Gesamt</td>
        <td>{{score_gesamt}}</td>
        <td>65</td>
        <td>82</td>
        <td>[Überdurchschnitt/Durchschnitt/Unterdurchschnitt]</td>
      </tr>
      <tr>
        <td>Befähigung</td>
        <td>{{score_befaehigung}}</td>
        <td>68</td>
        <td>85</td>
        <td>[Position]</td>
      </tr>
      <tr>
        <td>Governance</td>
        <td>{{score_governance}}</td>
        <td>58</td>
        <td>78</td>
        <td>[Position]</td>
      </tr>
      <tr>
        <td>Sicherheit</td>
        <td>{{score_sicherheit}}</td>
        <td>62</td>
        <td>80</td>
        <td>[Position]</td>
      </tr>
      <tr>
        <td>Wertschöpfung</td>
        <td>{{score_nutzen}}</td>
        <td>70</td>
        <td>88</td>
        <td>[Position]</td>
      </tr>
    </tbody>
  </table>

  <h3>Best Practices der Top 10%</h3>
  <ul>
    <li><strong>Technologie:</strong> Batch-Processing für Skalierung (anstelle von Einzelverarbeitung)</li>
    <li><strong>Governance:</strong> DSGVO-Zertifikat und jährliches Audit</li>
    <li><strong>Qualität:</strong> Human-in-the-Loop kombiniert mit automatisierten Fakten-Checks</li>
    <li><strong>Geschäftsmodell:</strong> SaaS/White-Label statt ausschließlich Projektgeschäft</li>
  </ul>

  <h3>Ihre Gaps (Aufholbedarf)</h3>
  <ul>
    <li>[Gap 1 basierend auf Score-Vergleich]</li>
    <li>[Gap 2 basierend auf Score-Vergleich]</li>
    <li>[Gap 3 basierend auf Score-Vergleich]</li>
  </ul>

  <h3>Ihre Stärken (Vorsprung nutzen)</h3>
  <ul>
    <li>[Stärke 1: Score > Durchschnitt]</li>
    <li>[Stärke 2: Score > Durchschnitt]</li>
  </ul>

  <h3>Überholungs-Strategie (Nächste 12 Monate)</h3>
  <ol>
    <li><strong>Q2:</strong> [Gap 1 schließen – Quick Win X]</li>
    <li><strong>Q3:</strong> [Gap 2 schließen – Maßnahme Y]</li>
    <li><strong>Q4:</strong> [Top 10% erreichen in Kategorie Z]</li>
  </ol>

  <p><strong>Ziel:</strong> Gesamt-Score {{score_gesamt}} → {% if score_gesamt >= 80 %}90+ (Top 5%){% elif score_gesamt >= 60 %}80+ (Top 10%){% else %}70+ (Top 25%){% endif %} bis Ende 2025</p>
</section>
```

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ Score-Vergleich mit Branche vorhanden
2. ✅ Konkrete Best Practices aufgeführt
3. ✅ Gaps und Stärken klar benannt
4. ✅ Überholungsstrategie enthalten

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML

---

## Output Format

Erstelle exakt einen validen HTML-Abschnitt gemäß obiger Vorlage. Setze folgende Variablen ein:
- `{{BRANCHE_LABEL}}`: String, erforderlich. Name der Branche/des Industriezweigs.
- `{{report_date}}`: Datum (YYYY-MM-DD), erforderlich. Datum des Benchmarks.
- Score-Variablen:
  - `{{score_gesamt}}`, `{{score_befaehigung}}`, `{{score_governance}}`, `{{score_sicherheit}}`, `{{score_nutzen}}`: Integer von 0–100, erforderlich. Gibt den Score des Unternehmens pro Kategorie an.

Die Tabelle muss mindestens die fünf aufgeführten Kategorien enthalten. Ist ein Score-Wert ungültig oder fehlt er (kein Wert zwischen 0–100), muss ein expliziter HTML-Kommentar im Output die fehlenden oder ungültigen Felder kennzeichnen.

Für Gaps und Stärken sind jeweils mindestens zwei Listeneinträge zu generieren, die anhand des Score-Vergleichs (über oder unter Branchendurchschnitt) bestimmt werden. Falls weniger als zwei möglich, setze einen Kommentar zur unzureichenden Datenlage in die Liste.

Die Überholungsstrategie-Liste muss exakt drei Punkte umfassen (Q2, Q3, Q4). Werden mehr/weniger Quartale benötigt, vermerke dies mit einem HTML-Kommentar und führe die jeweiligen Strategie-Schritte der Reihe nach auf.

Bei zusätzlichen oder kundenindividuellen Kategorien erweitere die Tabelle bzw. Listen entsprechend und erläutere dies mit einem Kommentar im HTML.

Jede fehlerhafte, unerwartete oder fehlende Eingabedaten sind mit klaren, markierten HTML-Kommentaren im jeweiligen Abschnitt zu thematisieren.

---

Nach dem Erstellen des Outputs:
- Bestätige in 1-2 Sätzen, dass der HTML-Abschnitt erzeugt wurde und ob alle Vorgaben eingehalten wurden. Falls nicht, nenne die fehlenden/abweichenden Punkte und führe eine minimale Korrektur durch, wenn möglich.