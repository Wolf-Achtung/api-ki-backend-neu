<!-- business_case.md - v2.2 GOLD STANDARD+ -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.
     VERSION: 2.2 GOLD STANDARD+ (Size-Awareness, Budget-/Einspar-Skalierung, Solo-Hinweise gefixt) -->

# PROMPT: Business Case - ROI & Wirtschaftlichkeit

## ⚠️ SIZE-AWARENESS FÜR BUDGET & EINSPARUNGEN

**Mögliche Unternehmensgrößen (NUR diese 3!):**
- `{{COMPANY_SIZE}}` = "solo" → "1 (Solo-Selbstständig/Freiberuflich)"
- `{{COMPANY_SIZE}}` = "team" → "2-10 (Kleines Team)"
- `{{COMPANY_SIZE}}` = "kmu"  → "11-100 (KMU)"

**Leitplanken für Interpretation (KEINE eigenen Rechnungen!):**

- **Solo:**
  - Typischer Fokus: Zeiteinsparung bei der eigenen Arbeit.
  - CAPEX eher im Bereich bis ca. 10.000 € sinnvoll.
  - Einsparungen von einigen Tagen/Monat (nicht "ganze Abteilungen").

- **Team (2–10):**
  - Fokus: Hebel über mehrere Personen (Teamprozesse).
  - CAPEX typischerweise bis ca. 50.000 € sinnvoll.
  - Einsparungen verteilt auf Team (z. B. 5–15 Tage/Monat).

- **KMU (11–100):**
  - Fokus: Teams/Funktionen, Skaleneffekte über viele Personen.
  - CAPEX bis ca. 200.000 € denkbar, wenn Zahlen es hergeben.
  - Einsparungen können deutlich höher liegen (z. B. ganze FTE-Bandbreiten).

👉 WICHTIG: Du **interpretierst** nur die gelieferten Variablen – du erfindest keine Zahlen
und überschreibst keine Berechnungen aus der Pipeline.

---

## ZWECK

Erstelle eine sachliche Business-Case-Analyse, die:

1. Die bereitgestellten Zahlen korrekt interpretiert (KEINE Eigen-Erfindung).
2. Eine einfache Sensitivitätsbetrachtung (±20 %) verbal beschreibt.
3. 3–5 konkrete ROI-Hebel benennt, spezifisch für {{HAUPTLEISTUNG}}.
4. Realistische Erwartungen setzt (konservativ, keine Übertreibungen).

**Zielgruppe:** CFO, Geschäftsführung, Investitions-Entscheider:innen.  
**Stil:** Sachlich, konservativ, transparent – kein Marketing-Sprech.

---

## VERFÜGBARE VARIABLEN (NUR DIESE NUTZEN!)

- Einmalige Investition (CAPEX): `{{CAPEX_REALISTISCH_EUR}}`
- Laufende Kosten pro Monat (OPEX): `{{OPEX_REALISTISCH_EUR}}`
- Monatliche Einsparung: `{{EINSPARUNG_MONAT_EUR}}`
- Amortisationsdauer in Monaten: `{{PAYBACK_MONTHS}}`
- ROI im ersten Jahr (in %): `{{ROI_12M}}`

Du darfst diese Zahlen sprachlich zusammenfassen, aber NICHT neu berechnen.

---

## ⛔ KRITISCHE REGELN

### ❌ VERBOTEN

1. **Zahlen erfinden oder „schöner rechnen“**
   - Kein Hochskalieren von Einsparungen ohne Basis.
   - Keine zusätzlichen Umsatzannahmen erfinden.

2. **Unrealistische Versprechen**
   - Keine „Garantie“-Formulierungen.
   - Kein „extremer“ ROI ohne Bezug zu `{{ROI_12M}}`.

3. **Falsche Größenlogik**
   - Bei Solo: keine Einsparung „mehrerer Abteilungen“ o. Ä.
   - Bei Team/KMU: nicht so tun, als gäbe es nur eine Einzelperson.

4. **Solo-Hinweise in Nicht-Solo-Reports**
   - Formulierungen wie „Hinweis für Solo-Beratung“ oder „als Solo-Unternehmer:in“
     sind **nur** zulässig, wenn `{{COMPANY_SIZE}} = "solo"`.
   - Bei `team`/`kmu` IMMER neutrale Formulierungen wie
     „Hinweis: Bei höheren internen Stundensätzen …“.

---

## ✅ ERWÜNSCHT

1. **Klare Zusammenfassung der Kennzahlen**
   - Investition, laufende Kosten, Einsparung, Payback, ROI 12M.

2. **Interpretation nach Größenklasse**
   - Z. B. bei Solo: „konservativ, aber tragfähig“, bei KMU: „solider Business Case
     auf Bereichsebene“.

3. **Sensitivitätsbetrachtung**
   - Verbale Beschreibung, was passiert, wenn Einsparung 20 % niedriger/höher ausfällt.

4. **Konkrete Hebel zur Verbesserung von ROI**
   - Z. B. höhere Auslastung der Lösung, mehr Nutzer im Unternehmen, leichte Preisanpassung.

---

## BEISPIEL-STRUKTUR (HTML)

Nutze eine Section mit klaren Unterüberschriften, z. B.:

- Ergebnis-Zusammenfassung
- Interpretation nach Unternehmensgröße
- Sensitivitätsbetrachtung
- Hebel zur ROI-Verbesserung
- Fazit

Beispielhafte Struktur (nur als Muster, Inhalte an Variablen anpassen):

    <section class="section business-case">
      <h2>Business-Case – Wirtschaftlichkeit der KI-Lösung</h2>

      <p><strong>Investition & Kosten:</strong> Einmalig rund {{CAPEX_REALISTISCH_EUR}} für
         Implementierung, Setup und erste Anpassungen. Laufende Betriebskosten von
         etwa {{OPEX_REALISTISCH_EUR}} pro Monat.</p>

      <p><strong>Monatliche Einsparung:</strong> Basierend auf den Angaben ergibt sich
         eine realistische Entlastung von ungefähr {{EINSPARUNG_MONAT_EUR}} pro Monat.
         Daraus folgt eine Amortisation nach rund {{PAYBACK_MONTHS}} Monaten und ein
         erwarteter ROI von etwa {{ROI_12M}} % im ersten Jahr.</p>

      <h3>Einordnung nach Unternehmensgröße</h3>
      <p>[Hier kurz erklären, warum diese Relation aus CAPEX, OPEX, Einsparung und ROI
         für {{COMPANY_SIZE}} sinnvoll bzw. konservativ ist. Bei Solo Fokus auf
         persönliche Arbeitszeit, bei Team/KMU Fokus auf mehrere Personen/Teams.]</p>

      <h3>Sensitivität (+/– 20 %)</h3>
      <p>Wenn die tatsächliche Einsparung etwa 20 % niedriger ausfällt, verlängert sich
         die Amortisationsdauer entsprechend, bleibt mit {{PAYBACK_MONTHS}} Monaten
         jedoch voraussichtlich im vertretbaren Rahmen. Bei 20 % höherer Einsparung
         verbessert sich der ROI deutlich, sodass die Investition schneller wieder
         eingespielt ist.</p>

      <h3>Hebel zur Verbesserung des ROI</h3>
      <ul>
        <li>[Hebel 1: z. B. höhere Nutzung der automatisierten Prozesse
            in {{HAUPTLEISTUNG}}]</li>
        <li>[Hebel 2: z. B. zusätzliche Use Cases auf derselben Infrastruktur]</li>
        <li>[Hebel 3: z. B. leichte Preisanpassung / Premium-Angebot,
            falls zum Geschäftsmodell passend]</li>
      </ul>

      <h3>Fazit</h3>
      <p>[Kurze, nüchterne Bewertung: „konservativer, aber tragfähiger Business Case“,
         „lohnt sich vor allem bei konsequenter Nutzung“ etc. Keine Garantie,
         keine Übertreibung.]</p>
    </section>

---

## INSTRUKTIONEN FÜR DIE GENERIERUNG

1. Nutze **ausschließlich** die gelieferten Variablen `{{CAPEX_REALISTISCH_EUR}}`,
   `{{OPEX_REALISTISCH_EUR}}`, `{{EINSPARUNG_MONAT_EUR}}`,
   `{{PAYBACK_MONTHS}}`, `{{ROI_12M}}` plus Kontext (Branche, Größe).
2. Interpretiere die Zahlen konservativ, benenne auch Schwächen
   (z. B. langer Payback) klar.
3. Passe Sprache und Beispiele an `{{COMPANY_SIZE}}` an.
4. Verwende deutsches Zahlenformat (4.500 € statt 4500 EUR).
5. Keine Solo-Hinweise in Team/KMU-Reports (siehe Regeln oben).

---

## ERFOLGS-KRITERIEN (GOLD STANDARD+)

Ein Business Case ist GOLD STANDARD+, wenn:

1. Alle Zahlen korrekt aus den Variablen übernommen sind.
2. Die Relation von CAPEX/OPEX/Einsparung/ROI verständlich erklärt ist.
3. Die Interpretation zur Unternehmensgröße passt (Solo/Team/KMU).
4. Eine klare ±20 %-Sensitivität beschrieben wird.
5. Mindestens 3 konkrete ROI-Hebel genannt werden.
6. Keine Solo-Hinweise in Nicht-Solo-Reports vorkommen.

**Output:** Valides HTML, keine Markdown-Fences, keine verbleibenden Platzhalter.
