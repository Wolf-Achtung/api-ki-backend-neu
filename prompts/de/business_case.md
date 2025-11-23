# PROMPT: Business Case - ROI & Wirtschaftlichkeit

## ZWECK
Erstelle eine sachliche Business-Case-Analyse, die:
1. **bereitgestellte Zahlen** korrekt interpretiert (KEINE Erfindungen!)
2. eine **einfache Sensitivitätsanalyse** für ±20 % Abweichungen beschreibt
3. **konkrete ROI-Hebel-Empfehlungen** gibt (spezifisch für {{HAUPTLEISTUNG}})
4. **realistische Erwartungen** setzt (keine Schönfärberei)

**Zielgruppe:** CFO, Geschäftsführung, Investitions-Entscheider  
**Stil:** Sachlich, konservativ, transparent – KEINE Marketing-Sprache!

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE Zahlen erfinden oder „optimieren“:**
   - ❌ ROI „schöner“ rechnen als durch die Variablen vorgegeben
   - ❌ Einsparungen hochrechnen ohne Basis
   - ❌ zusätzliche Umsatz-Annahmen einbauen, die nicht im Kontext stehen

2. **KEINE vagen Hebelungs-Tipps:**
   - ❌ „Prozesse optimieren“
   - ❌ „Effizienz steigern“
   - ❌ „Mehr Automatisierung“

3. **KEINE unrealistischen Versprechungen:**
   - ❌ „Garantierte Amortisation in X Monaten“
   - ❌ „ROI von 500 % erreichbar“

### ✅ STATTDESSEN:

1. **Nur bereitgestellte Variablen verwenden:**
   - ✅ {{CAPEX_REALISTISCH_EUR}} – einmalige Investition (CAPEX, in €)
   - ✅ {{OPEX_REALISTISCH_EUR}} – laufende Kosten/Monat (OPEX, in €)
   - ✅ {{EINSPARUNG_MONAT_EUR}} – Einsparungen/Monat (in €)
   - ✅ {{PAYBACK_MONTHS}} – Amortisationszeit in Monaten
   - ✅ {{ROI_12M}} – ROI nach 12 Monaten in Prozent (z. B. 85,0 = 85,0 %)

2. **Spezifische Hebel aus dem Kontext:**
   - ✅ konkrete Kostenhebel (z. B. „Batch API statt Standard API (-50 % OpenAI-Kosten)“)
   - ✅ vorhandene Lizenzen sinnvoller nutzen (z. B. „Typeform Pro“, vorhandene Datenbanken)
   - ✅ Preis-/Stundensatz-Anpassung **nur**, wenn das Geschäftsmodell auf Abrechnung nach Zeit basiert

3. **Transparente Einordnung:**
   - ✅ ausdrücklich erwähnen, dass die Berechnung auf den Quick-Win-Werten basiert
   - ✅ offen mit Unsicherheiten umgehen (z. B. „konservative Annahme“, „ohne zusätzliche Umsatzpotenziale“)

---

## 💡 BEISPIEL (STRUKTUR – KEINE FIXEN ZAHLEN ÜBERNEHMEN!)

> WICHTIG: Dieses Beispiel zeigt nur **Struktur und Ton**.  
> Im echten Output dürfen **keine** Beispielzahlen aus diesem Prompt übernommen werden –  
> verwende ausschließlich die Variablenwerte.

```html
<section class="section business-case">
  <h3>Business-Case (Ergebnis)</h3>

  <p>
    <strong>Monatliche Einsparung:</strong> {{EINSPARUNG_MONAT_EUR}} €/Monat<br>
    <strong>CAPEX:</strong> {{CAPEX_REALISTISCH_EUR}} € (einmalig) ·
    <strong>OPEX:</strong> {{OPEX_REALISTISCH_EUR}} €/Monat<br>
    <strong>Amortisation:</strong> {{PAYBACK_MONTHS}} Monate ·
    <strong>ROI (12 Monate):</strong> {{ROI_12M}} %
  </p>

  <h4>Interpretation</h4>
  <p>
    Die Quick-Win-Einsparungen von {{EINSPARUNG_MONAT_EUR}} €/Monat decken die laufenden Kosten
    (OPEX: {{OPEX_REALISTISCH_EUR}} €/Monat) deutlich ab und amortisieren die einmalige Investition
    (CAPEX: {{CAPEX_REALISTISCH_EUR}} €) nach {{PAYBACK_MONTHS}} Monaten.
    Der ROI nach 12&nbsp;Monaten von {{ROI_12M}} % basiert ausschließlich auf den bereitgestellten
    Quick-Win-Zahlen – ohne zusätzliche Umsatz-Annahmen.
  </p>

  <h4>Sensitivität (±20 %)</h4>
  <ul>
    <li>
      <strong>Einsparung −20 %:</strong>
      beschreibe in Worten, wie sich Payback und ROI verschlechtern würden
      (z. B. „Payback verlängert sich um einige Monate, ROI sinkt spürbar, bleibt aber positiv“).
    </li>
    <li>
      <strong>Einsparung +20 %:</strong>
      beschreibe, wie sich Payback und ROI verbessern (z. B. „Amortisation deutlich schneller,
      ROI steigt um einen zweistelligen Prozentbereich“).
    </li>
    <li>
      <strong>Kosten +20 %:</strong>
      beschreibe, wie empfindlich der Case auf höhere OPEX reagiert
      (z. B. „ROI sinkt moderat, Case bleibt aber tragfähig“).
    </li>
  </ul>

  <h4>Empfehlungen zur ROI-Hebelung (konkret)</h4>
  <ol>
    <li>
      <strong>Konkreter Kostenhebel im Kernprozess:</strong>
      z. B. Batch-Verarbeitung, effizientere Prompt-Struktur, Reduktion doppelter Schritte.
      Beschreibe den Effekt knapp (z. B. „ca. −X % Toolkosten“).
    </li>
    <li>
      <strong>Besserer Einsatz bestehender Lizenzen:</strong>
      z. B. vorhandene Formulare/Tools tiefer integrieren statt neue Software zu kaufen.
    </li>
    <li>
      <strong>Preis-/Stundensatz-Hebel (falls passend):</strong>
      Nur wenn {{HAUPTLEISTUNG}} typischerweise auf Stunden- oder Projekthonoraren basiert
      (Beratung/Agentur). Keine solche Empfehlung für klassische Produkt-/SaaS-/Medien-Modelle.
    </li>
    <li>
      <strong>MVP-First statt Big-Bang:</strong>
      kurzfristig umsetzbarer Scope mit klarem ROI-Review nach wenigen Monaten,
      bevor größere Invests ausgelöst werden.
    </li>
  </ol>

  <p>
    <em>Optionaler Hinweis für Solo-Unternehmen:</em>
    Nur wenn {{UNTERNEHMENSGROESSE_LABEL}} klar auf Solo-Selbstständigkeit hinweist:
    ergänze einen kurzen Hinweis, dass die Berechnung auf einem konservativen
    Stundensatz basiert und sich mit höherer Positionierung entsprechend verschieben kann.
  </p>
</section>
