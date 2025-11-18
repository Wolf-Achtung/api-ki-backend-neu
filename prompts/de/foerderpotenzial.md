# PROMPT: Förderpotenzial - Finanzierungs-Möglichkeiten

## ZWECK
Liste relevante Förderprogramme für:
1. **{{BUNDESLAND_LABEL}}** (Landes-Förderungen)
2. **{{BRANCHE_LABEL}}** (Branchen-Förderungen)
3. **KI-Projekte** (Bund/EU)

**Zielgruppe:** CFO, Geschäftsführung
**Stil:** Prägnant, mit Links, Antragsfristen

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE veralteten Programme (vor 2024)**
2. **KEINE generischen Listen ohne Relevanz-Check**
3. **KEINE Förderungen ohne Antragslink**

### ✅ STATTDESSEN:
1. **Aktuell & relevant:**
   - "Digital Jetzt (BMWi): Bis €100k, Antragsfrist 31.12.2025"
   - Link: www.innovation-beratung-foerderung.de

2. **Konkrete Zahlen:**
   - "50% Zuschuss auf Beratung (max. €10k)"
   - "Zinsfreies Darlehen bis €500k"

---

## 💡 BEISPIEL (kompakt)

```html
<section class="section foerderpotenzial">
  <h2>Förderpotenzial & Finanzierung</h2>
  
  <p><strong>Relevante Programme für:</strong> {{BRANCHE_LABEL}}, {{BUNDESLAND_LABEL}}</p>

  <h3>Bundes-Programme (Deutschland)</h3>
  <table class="table">
    <thead><tr><th>Programm</th><th>Förderung</th><th>Frist</th><th>Link</th></tr></thead>
    <tbody>
      <tr>
        <td>Digital Jetzt</td>
        <td>Bis €100k (50% Zuschuss)</td>
        <td>Laufend bis 31.12.2025</td>
        <td><a href="https://www.innovation-beratung-foerderung.de/INNO/Navigation/DE/Digital-Jetzt/digital-jetzt.html">Beantragen</a></td>
      </tr>
      <tr>
        <td>go-digital</td>
        <td>50% auf IT-Beratung (max. €16.500)</td>
        <td>Laufend</td>
        <td><a href="https://www.bmwk.de/Redaktion/DE/Artikel/Mittelstand/go-digital.html">Beantragen</a></td>
      </tr>
    </tbody>
  </table>

  <h3>Landes-Programme ({{BUNDESLAND_LABEL}})</h3>
  <ul>
    <li><strong>Berlin:</strong> IBB Digitalisierungskredit (bis €500k, 0,5% Zinsen)</li>
    <li><strong>Bayern:</strong> Bayern Digital II (bis €50k Zuschuss)</li>
    <li>[Programm spezifisch für {{BUNDESLAND_LABEL}} recherchieren]</li>
  </ul>

  <h3>Empfohlene nächste Schritte</h3>
  <ol>
    <li>Digital Jetzt prüfen: Passt für Batch-Processing-Projekt (€5k Investment)</li>
    <li>go-digital: DSGVO-Beratung fördern lassen (€1.500 → €750 Eigenanteil)</li>
    <li>Fördermittel-Berater kontaktieren (€200/h, aber spart 40h Recherche)</li>
  </ol>
</section>
```

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ Aktuell (2024/2025)
2. ✅ Relevant für Bundesland
3. ✅ Mit Links & Fristen
4. ✅ Konkrete Empfehlungen

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML
