# PROMPT: Unternehmensprofil & Marktkontext

## ZWECK
Beschreibe:
1. **Unternehmen:** Branche, Größe, Hauptleistung
2. **Marktkontext:** Trends in der Branche
3. **KI-Potenzial:** Warum ist KI relevant für diese Branche

**Zielgruppe:** Externe Leser, Investoren
**Stil:** Professionell, kontextualisiert

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE generischen Branchen-Beschreibungen**
2. **KEINE erfundenen Markt-Trends**

### ✅ STATTDESSEN:
1. **Spezifisch:** "Beratung für KMU-Digitalisierung"
2. **Konkret:** "Branche wächst 12% p.a. (IDC 2024)"

---

## 💡 BEISPIEL

```html
<section class="section unternehmensprofil">
  <h2>Unternehmensprofil & Marktkontext</h2>

  <h3>Unternehmensprofil</h3>
  <ul>
    <li><strong>Branche:</strong> {{BRANCHE_LABEL}}</li>
    <li><strong>Größe:</strong> {{UNTERNEHMENSGROESSE_LABEL}}</li>
    <li><strong>Standort:</strong> {{BUNDESLAND_LABEL}}</li>
    <li><strong>Hauptleistung:</strong> {{HAUPTLEISTUNG}}</li>
    <li><strong>Geschäftsmodell:</strong> [B2B/B2C], [Projektgeschäft/SaaS/etc.]</li>
  </ul>

  <h3>Marktkontext & Trends ({{BRANCHE_LABEL}})</h3>
  <ul>
    <li><strong>Marktwachstum:</strong> [X% p.a. laut Quelle]</li>
    <li><strong>KI-Adoption:</strong> [Y% der Unternehmen nutzen KI in dieser Branche]</li>
    <li><strong>Haupttreiber:</strong> [Fachkräftemangel, Kostendruck, Digitalisierungsdruck]</li>
    <li><strong>Herausforderungen:</strong> [Spezifisch für Branche]</li>
  </ul>

  <h3>KI-Potenzial für {{BRANCHE_LABEL}}</h3>
  <p>Spezifische Anwendungsfälle:</p>
  <ul>
    <li>[Use Case 1 spezifisch für Branche]</li>
    <li>[Use Case 2 spezifisch für Branche]</li>
    <li>[Use Case 3 spezifisch für Branche]</li>
  </ul>

  <h3>Wettbewerbsposition</h3>
  <p>{{UNTERNEHMENSGROESSE_LABEL}} in {{BRANCHE_LABEL}} haben typischerweise:</p>
  <ul>
    <li>Vorteil: [Agilität, Nischenfokus, persönlicher Service]</li>
    <li>Nachteil: [Ressourcen, Marktmacht, Sichtbarkeit]</li>
    <li>KI-Hebel: [Wie KI Nachteile ausgleichen kann]</li>
  </ul>
</section>
```

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ Unternehmensprofil vollständig
2. ✅ Marktkontext recherchiert
3. ✅ KI-Potenzial branchen-spezifisch

---

**VERSION:** v2.1 GOLD STANDARD+
**OUTPUT:** Valides HTML
