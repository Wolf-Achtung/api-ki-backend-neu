<!-- foerderpotenzial.md - v2.2 GOLD STANDARD+ (ohne Research-Datum-Platzhalter) -->
<!-- Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im Output.
     VERSION: 2.2 GOLD STANDARD+ (Funding + Business-Case Alignment) -->

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

Du kannst – je nach Implementierung – u.a. auf folgende Variablen zugreifen (falls gesetzt):

- `{{BRANCHE_LABEL}}`, `{{BUNDESLAND_LABEL}}`, `{{UNTERNEHMENSGROESSE_LABEL}}`
- `{{CAPEX_REALISTISCH_EUR}}` – einmalige Investition für das KI-Projekt
- `{{OPEX_REALISTISCH_EUR}}` – laufende Mehrkosten pro Monat
- `{{PAYBACK_MONTHS}}` – Amortisationsdauer **ohne** Förderung
- `{{ROI_12M}}` – ROI in % nach 12 Monaten **ohne** Förderung
- Kontextblock mit Research-Ergebnissen aus Tavily/Perplexity (Bund, Land, EU-Förderprogramme)

**Wichtig:**  
Wenn bestimmte Werte/Variablen nicht verfügbar sind, **nichts erfinden**. Dann qualitativ bleiben („Payback dürfte sich spürbar verkürzen“) statt pseudo-genauer Zahlen.

---

## ⚠️ KRITISCHE REGELN

1. **Aktualität & Relevanz**
   - Nutze nur Programme, die im Research als aktuell/offen erkennbar sind.
   - Programme, die klar ausgelaufen sind, maximal als Hinweis mit Kennzeichnung („nicht mehr für Neuanträge geöffnet“).
   - Keine Beispiele aus weit zurückliegenden Jahren ohne aktuellen Call.

2. **Kein „Förderdschungel“-Listen-Spam**
   - Maximal **4–6 Programme gesamt**, davon typischerweise:
     - 2–3 auf Bundesebene
     - 1–2 im Bundesland {{BUNDESLAND_LABEL}}
     - optional 1 EU-Programm (wenn sinnvoll)
   - Nur Programme, die realistisch zur **Unternehmensgröße**, **Branche** und zum **Projektumfang** passen.

3. **Jedes Programm braucht:**
   - 1–2 Sätze Beschreibung („wofür ist das Programm gedacht?“)
   - Förderquote / Maximalbetrag, soweit im Research enthalten
   - Zielgruppe (z.B. KMU, Solo-Selbstständige, Beratungen)
   - Aussage, warum es **genau zu diesem Projekt** passt (nicht nur „für Digitalisierung allgemein“)
   - Einen **klickbaren Link** zur offiziellen Programmseite

4. **Keine Erfindungen**
   - Wenn im Research etwas unklar bleibt, transparent formulieren („laut aktueller Recherche in Überarbeitung“).
   - Keine fiktiven Programmnamen, Budgets oder Fristen.

---

## OUTPUT-FORMAT

Antworte ausschließlich mit **valide­m HTML** in folgender Struktur (Beispiele dienen nur der Orientierung – im echten Output mit aktuellen Daten aus dem Research füllen):

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
      <!-- 2–3 konkrete Programme, z.&nbsp;B. „Digital Jetzt“, „go-digital“ – nur wenn laut Research aktuell -->
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
    <!-- 1–2 Programme aus dem Bundesland, z.&nbsp;B. IBB-Programme in Berlin – mit kurzer Beschreibung &amp; Link -->
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
    <li><strong>Mit typischer Förderung (Beispiel 40–50&nbsp;% Zuschuss):</strong> Der Eigenanteil an den Investitionskosten sinkt deutlich; die Amortisationsdauer verkürzt sich je nach Förderquote typischerweise auf etwa 50–70&nbsp;% des ursprünglichen Wertes.</li>
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
      Hinweis: Alle Angaben zu Förderquoten, Summen und Fristen basieren auf öffentlich zugänglichen Informationen zum Zeitpunkt der letzten Recherche 
      und müssen vor Antragstellung auf den offiziellen Programmseiten geprüft werden.
    </em>
  </p>
</section>
```

---

## ERFOLGS-KRITERIEN

Ein Förderabschnitt gilt als GOLD STANDARD+, wenn:

1. ✅ Nur **aktuelle und zum Projekt passende Programme** genannt werden.  
2. ✅ Jedes Programm einen klaren Bezug zur geplanten KI-/Digitalisierungsmaßnahme hat.  
3. ✅ Alle Programme mit **kurzer Beschreibung, Zielgruppe, Förderlogik und Link** aufgeführt sind.  
4. ✅ Der Zusammenhang zu **Payback & ROI** verständlich erläutert wird (mindestens qualitativ, besser mit grober Zahl).  
5. ✅ Transparenz über Unsicherheiten gewahrt bleibt (keine ausgedachten Budgets, klare Hinweise auf Prüfpflicht).  

**OUTPUT:** Valides HTML (keine Markdown-Fences, kein `<html>`/`<body>`).
