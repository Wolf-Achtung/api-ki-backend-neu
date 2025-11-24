<!-- foerderpotenzial.md - v2.3 GOLD STANDARD+ (mit Fördermatrix-Integration 2025/2026) -->
<!-- Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im Output.
     VERSION: 2.3 GOLD STANDARD+ (Funding + Business-Case Alignment + Fördermatrix) -->

# PROMPT: Förderpotenzial - Finanzierungs-Möglichkeiten

## ZWECK
Erstelle eine kompakte, aber konkrete Übersicht der wichtigsten Förderprogramme für das geplante KI-/Digitalisierungsprojekt mit Fokus auf:

1. **{{BUNDESLAND_LABEL}}** (Landesprogramme)
2. **{{BRANCHE_LABEL}}** (branchenrelevante Programme, falls vorhanden)
3. **Bundes- und EU-Programme** für KI & Digitalisierung

Die Section soll Entscheider:innen helfen,
- **2–3 realistische Programme** zu identifizieren und
- den **Einfluss der Förderung auf Payback & ROI** des Business Case grob zu verstehen.

**Zielgruppe:** Geschäftsführung, CFO, förderaffine Berater:innen  
**Stil:** Prägnant, seriös, faktenbasiert, leicht scanbar.

---

## VERFÜGBARE KONTEXTDATEN

Du kannst – je nach Implementierung – u.a. auf folgende Variablen und Datenquellen zugreifen (falls gesetzt):

- `{{BRANCHE_LABEL}}`, `{{BUNDESLAND_LABEL}}`, `{{UNTERNEHMENSGROESSE_LABEL}}`
- `{{CAPEX_REALISTISCH_EUR}}` – einmalige Investition für das KI-Projekt
- `{{OPEX_REALISTISCH_EUR}}` – laufende Mehrkosten pro Monat
- `{{PAYBACK_MONTHS}}` – Amortisationsdauer **ohne** Förderung
- `{{ROI_12M}}` – ROI in % nach 12 Monaten **ohne** Förderung
- Kontextblock mit Research-Ergebnissen aus Tavily/Perplexity (Bund, Land, EU-Förderprogramme)
- **Interne Förder-Matrix / Förder-Übersicht 2025/2026**, z. B. mit Spalten:
  - Programm
  - Änderungen 2025
  - Ko-Finanzierungsquote 2025
  - Fristen / Calls 2025
  - Ausblick 2026 (z. B. erwartete Anpassungen, mögliche Verlängerungen, programmatische Trends)

**Wichtig:**

- Wenn bestimmte Werte/Variablen nicht verfügbar sind, **nichts erfinden**. Dann qualitativ bleiben („Payback dürfte sich spürbar verkürzen“) statt pseudo-genauer Zahlen.
- Wenn es Abweichungen zwischen Research und interner Fördermatrix gibt:
  - **Research-Stand hat Vorrang** für die Frage „aktuell offen / geschlossen?“.
  - Die Matrix kann als **Trend-/Kontextquelle** für Änderungen 2025 und den Ausblick 2026 genutzt werden (z. B. Hinweis auf ausgelaufene Programme, Quotenverschiebungen, erwartete Reformen).

---

## ⚠️ KRITISCHE REGELN

1. **Aktualität & Relevanz**
   - Nutze nur Programme, die im Research als aktuell/offen erkennbar sind.
   - Programme, die klar ausgelaufen sind (z. B. bestimmte Digitalisierungsprogramme), maximal als Hinweis mit Kennzeichnung („nicht mehr für Neuanträge geöffnet“) – insbesondere, wenn die Fördermatrix sie als „eingestellt“ oder „ausgelaufen“ markiert.
   - Keine Beispiele aus weit zurückliegenden Jahren ohne aktuellen Call.

2. **Kein „Förderdschungel“-Listen-Spam**
   - Maximal **4–6 Programme gesamt**, davon typischerweise:
     - 2–3 auf Bundesebene
     - 1–2 im Bundesland {{BUNDESLAND_LABEL}}
     - optional 1 EU-Programm (wenn sinnvoll)
   - Nur Programme, die realistisch zur **Unternehmensgröße**, **Branche** und zum **Projektumfang** passen.

3. **Jedes Programm braucht:**
   - 1–2 Sätze Beschreibung („wofür ist das Programm gedacht?“)
   - Förderquote / Maximalbetrag, soweit im Research oder in der Fördermatrix enthalten
   - Zielgruppe (z. B. KMU, Solo-Selbstständige, Beratungen)
   - Aussage, warum es **genau zu diesem Projekt** passt (nicht nur „für Digitalisierung allgemein“)
   - Einen **klickbaren Link** zur offiziellen Programmseite

4. **Keine Erfindungen**
   - Wenn im Research etwas unklar bleibt, transparent formulieren („laut aktueller Recherche in Überarbeitung“).
   - Keine fiktiven Programmnamen, Budgets oder Fristen.
   - Die Fördermatrix 2025/2026 darf nur genutzt werden, um **bestehende Programme besser einzuordnen** (z. B. Änderungen, Quoten, Ausblick) – nicht, um neue Programme „herbeizuerfinden“.

5. **Integration der Fördermatrix 2025/2026 (falls vorhanden)**
   - Nutze die Informationen aus der Fördermatrix zur **qualitativen Einordnung**:
     - Welche Programme haben sich 2025 relevant verändert (z. B. Wegfall, neue Ausrichtung, geänderte Quoten)?
     - Wo wurden Ko-Finanzierungsquoten angepasst (z. B. EFRE-Aufteilung national/EU, KMU-Bonus bei Innovationsprogrammen)?
     - Welche Programme haben laut Ausblick 2026 voraussichtlich Bestand oder werden eher reformiert statt eingestellt?
   - Übernimm Informationen aus der Matrix **nicht 1:1**, sondern übersetze sie in:
     - kurze Einschätzungen („laut aktueller Fördermatrix wurde das Programm 2025 eingestellt und ist für Neuanträge nicht mehr relevant“)
     - oder knappe Hinweise im Kontext („2025 wurden die Ko-Finanzierungsquoten zugunsten eines höheren Eigenanteils angepasst“).
   - Wenn die Matrix auf ein ausgelaufenes Programm hinweist, kannst du es im Fließtext erwähnen, aber **nicht als aktives Programm in Tabellen/Listen** aufführen.

---

## ZUSÄTZLICHER SPEZIAL-KONTEXT: Fördermatrix 2025/2026 (Beispiele für Nutzung)

Wenn eine strukturierte Fördermatrix mit den Spalten „Programm, Änderungen 2025, Quote, Fristen, Ausblick 2026“ bereitsteht, nutze sie wie folgt:

- **Programme filtern und priorisieren:**
  - Bevorzuge Programme, die:
    - für {{UNTERNEHMENSGROESSE_LABEL}} und {{BRANCHE_LABEL}} geeignet sind und
    - laut Matrix für 2025/2026 weiterhin relevant sind (z. B. keine klar dokumentierte Einstellung).
- **Änderungen 2025 sichtbar machen:**
  - Markiere wesentliche Veränderungen aus der Matrix, z. B.:
    - „Programm X wurde 2025 eingestellt – für dieses Projekt daher nur noch historisch relevant.“
    - „Programm Y hat 2025 seine Förderschwerpunkte deutlich stärker auf KI-Qualifizierung und digitale Souveränität ausgerichtet.“
- **Ko-Finanzierungsquote & Fristen:**
  - Nutze Quoten/Fristen aus der Matrix, sofern diese:
    - zur aktuellen Research-Lage passen oder
    - sich zumindest nicht widersprechen.
  - Wenn du Quoten nur qualitativ nutzen kannst, formuliere entsprechend vorsichtig:
    - „Typischerweise werden 30–50 % der förderfähigen Kosten bezuschusst (bitte aktuelle Programmbedingungen prüfen).“
- **Ausblick 2026:**
  - Nutze die Ausblick-Spalte, um **Trends und Planbarkeit** einzuordnen, z. B.:
    - „Das Programm ist als Teil eines mehrjährigen EU-/Bundesrahmens angelegt und dürfte auch 2026 noch verfügbar sein.“
    - „Laut derzeitiger Planung werden die Schwerpunkte in Richtung Green- und KI-Projekte verschoben – für Ihr Vorhaben eher vorteilhaft.“

Wenn keine Fördermatrix vorliegt, ignoriere diesen Abschnitt und arbeite ausschließlich mit den Research-Ergebnissen.

---

## OUTPUT-FORMAT

Antworte ausschließlich mit **valide­m HTML** in folgender Struktur (Beispiele dienen nur der Orientierung – im echten Output mit aktuellen Daten aus dem Research und, falls vorhanden, der Fördermatrix 2025/2026 füllen):

```html
<section class="section foerderpotenzial">
  <h2>Förderpotenzial &amp; Finanzierung</h2>

  <p><strong>Fokus:</strong> Förderprogramme für {{BRANCHE_LABEL}} in {{BUNDESLAND_LABEL}} mit Bezug zu Ihrem geplanten KI-/Digitalisierungsprojekt.</p>

  <h3>Bundesprogramme (Deutschland)</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Programm</th>
        <th>Förderung</th>
        <th>Für wen geeignet?</th>
        <th>Link</th>
      </tr>
    </thead>
    <tbody>
      <!-- 2–3 konkrete Programme, z.&nbsp;B. „Digital Jetzt“, KMU-innovativ, GRW – nur wenn laut Research aktuell/offen -->
      <!-- Nutze hier ggf. die Fördermatrix, um Änderungen 2025 (z.&nbsp;B. Quoten, Ausrichtung, Auslaufen) knapp zu spiegeln. -->
      <!-- Beispiel-Struktur: 
      <tr>
        <td>Digital Jetzt (BMWK)</td>
        <td>Zuschuss für Investitionen in digitale Technologien und Qualifizierung; Förderquote laut aktueller Programmbeschreibung angeben.</td>
        <td>Für KMU und Solo-Selbstständige, die in digitale Prozesse und KI-Lösungen investieren.</td>
        <td><a href="https://www.innovation-beratung-foerderung.de">Programmseite</a></td>
      </tr>
      -->
    </tbody>
  </table>

  <h3>Landesprogramme ({{BUNDESLAND_LABEL}})</h3>
  <ul>
    <!-- 1–2 Programme aus dem Bundesland, z.&nbsp;B. spezifische Digitalisierungs- oder Innovationsprogramme – mit kurzer Beschreibung &amp; Link -->
    <!-- Nutze die Fördermatrix, wenn sie landesspezifische EFRE-/Digitalprogramme und Quotenänderungen 2025/2026 enthält. -->
    <!-- Beispiel-Struktur:
    <li>
      <strong>IBB-Digitalisierungsförderung (Berlin):</strong>
      Zuschuss oder zinsgünstiges Darlehen für Digitalisierungs- und KI-Projekte im Dienstleistungssektor.
      <a href="https://www.ibb.de">Programmübersicht</a>
    </li>
    -->
  </ul>

  <h3>EU-Programme (optional)</h3>
  <ul>
    <!-- Nur aufnehmen, wenn Research zeigt, dass ein Call realistisch ist (z.B. Horizon Europe / Digital Europe). -->
    <!-- Die Fördermatrix kann hier Trends liefern (z.B. geplante Calls 2026, Schwerpunkte auf KI &amp; Digitalisierung). -->
    <!-- Beispiel:
    <li>
      <strong>Horizon Europe – KI &amp; Digitalisierung:</strong>
      Förderaufrufe für Verbundprojekte zu generativer KI, Datenplattformen oder KMU-Digitalisierung.
      <a href="https://ec.europa.eu/info/funding-tenders/opportunities/portal">EU Funding &amp; Tenders Portal</a>
    </li>
    -->
  </ul>

  <h3>Einfluss auf Business Case</h3>
  <p>Auf Basis der Business-Case-Zahlen lässt sich der Effekt einer Förderung grob abschätzen:</p>
  <ul>
    <li><strong>Ausgangswert ohne Förderung:</strong> CAPEX ca. {{CAPEX_REALISTISCH_EUR}} €, Payback etwa {{PAYBACK_MONTHS}} Monate, ROI nach 12 Monaten rund {{ROI_12M}} %.</li>
    <li><strong>Mit typischer Förderung (Beispiel 30–50&nbsp;% Zuschuss):</strong> Der Eigenanteil an den Investitionskosten sinkt deutlich; die Amortisationsdauer verkürzt sich je nach Förderquote typischerweise auf etwa 50–70&nbsp;% des ursprünglichen Wertes.</li>
    <li><strong>Praxis-Einordnung:</strong> Hervorheben, welche 1–2 Programme den größten Hebel haben (z.&nbsp;B. Zuschuss für Beratung + Implementierung) und wie stark diese den Payback realistisch verkürzen können (qualitativ, ggf. mit grober Zahl, wenn Daten verfügbar sind).</li>
  </ul>

  <h3>Empfohlene nächste Schritte</h3>
  <ol>
    <li>Aus den genannten Programmen 1–2 Favoriten auswählen, die am besten zu Unternehmensgröße, Branche und Projektumfang passen.</li>
    <li>Kurzbeschreibung des Projekts (1–2 Seiten) erstellen, die für Förderanträge wiederverwendet werden kann (Ziele, Maßnahmen, Kosten, erwarteter Nutzen).</li>
    <li>Prüfen, ob eine Kombination aus Bundes- und Landesprogramm möglich ist (Kumulierbarkeit laut Programmbedingungen beachten).</li>
    <li>Optional: Gespräch mit einer Fördermittel-Expertin/einem Fördermittel-Experten führen, um Erfolgschancen zu erhöhen und Formfehler zu vermeiden.</li>
  </ol>

  <p class="small">
    <em>
      Hinweis: Alle Angaben zu Förderquoten, Summen, Fristen und programmatischen Ausblicken basieren auf öffentlich zugänglichen Informationen sowie ggf. einer internen Fördermatrix 2025/2026 zum Zeitpunkt der letzten Recherche
      und müssen vor Antragstellung auf den offiziellen Programmseiten geprüft werden.
    </em>
  </p>
</section>
