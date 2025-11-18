# PROMPT: Wettbewerb & Benchmarking

## ZWECK
Zeige:
1. **Score-Vergleich:** Wie steht Unternehmen vs. Branche
2. **Best Practices:** Was machen die Besten anders
3. **Gaps:** Wo liegt Unternehmen zurück
4. **Opportunities:** Wo kann überholt werden

**Zielgruppe:** Geschäftsführung, Strategie
**Stil:** Ehrlich, motivierend, konkret

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE erfundenen Benchmark-Zahlen**
2. **KEINE namenlosen Wettbewerber**

### ✅ STATTDESSEN:
1. **Aggregierte Daten:** "Durchschnitt: 65/100 (30 Assessments)"
2. **Best Practice:** "Top 10%: Batch-Processing, Templates, DSGVO-Zertifikat"

---

## 💡 BEISPIEL

```html
<section class="section wettbewerb-benchmark">
  <h2>Wettbewerb & Benchmarking</h2>

  <p><strong>Datenbasis:</strong> 30 Assessments in {{BRANCHE_LABEL}}, Stand {{report_date}}</p>

  <h3>Score-Vergleich (Sie vs. Branche)</h3>
  <table class="table">
    <thead><tr><th>Kategorie</th><th>Ihr Score</th><th>Ø Branche</th><th>Top 10%</th><th>Position</th></tr></thead>
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
    <li><strong>Technologie:</strong> Batch-Processing für Skalierung (nicht Einzelverarbeitung)</li>
    <li><strong>Governance:</strong> DSGVO-Zertifikat + jährliches Audit</li>
    <li><strong>Qualität:</strong> Human-in-the-Loop + automatisierte Fakten-Checks</li>
    <li><strong>Geschäftsmodell:</strong> SaaS/White-Label statt nur Projektgeschäft</li>
  </ul>

  <h3>Ihre Gaps (Aufholbedarf)</h3>
  <ul>
    <li>[Gap 1 basierend auf Score-Vergleich]</li>
    <li>[Gap 2 basierend auf Score-Vergleich]</li>
    <li>[Gap 3 basierend auf Score-Vergleich]</li>
  </ul>

  <h3>Ihre Stärken (Vorsprung nutzen)</h3>
  <ul>
    <li>[Stärke 1 wo Score > Durchschnitt]</li>
    <li>[Stärke 2 wo Score > Durchschnitt]</li>
  </ul>

  <h3>Überholungs-Strategie (Nächste 12 Monate)</h3>
  <ol>
    <li><strong>Q2:</strong> [Gap 1 schließen durch Quick Win X]</li>
    <li><strong>Q3:</strong> [Gap 2 schließen durch Maßnahme Y]</li>
    <li><strong>Q4:</strong> [Top 10% erreichen in Kategorie Z]</li>
  </ol>

  <p><strong>Ziel:</strong> Gesamt-Score {{score_gesamt}} → 80+ (Top 10%) bis Ende 2025</p>
</section>
```

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ Score-Vergleich vs. Branche
2. ✅ Best Practices konkret
3. ✅ Gaps + Stärken benannt
4. ✅ Überholungs-Strategie

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML
