<!-- quick_wins.md – v2.4 GOLD STANDARD+ (placeholder‑sicher)
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.
     VERSION: 2.4 GOLD STANDARD+ (Size-Awareness, Branchenlogik, keine Platzhalter im Output)
-->

# PROMPT: Quick Wins – 6 sofort umsetzbare Maßnahmen

## ZWECK

Erstelle 6 konkrete „Quick Wins“, die:

1. direkt am Kernprozess **{{HAUPTLEISTUNG}}** ansetzen,
2. zur Branche **{{BRANCHE_LABEL}}** und zur Unternehmensgröße **{{UNTERNEHMENSGROESSE_LABEL}}** passen,
3. innerhalb von **1–14 Tagen** umsetzbar sind,
4. klaren **wirtschaftlichen Impact** (Zeit, Kosten, Qualität, Umsatz) haben,
5. gute Anschlussfähigkeit an **Business Case, Roadmap und Tool‑Empfehlungen** haben.

Die Quick Wins sollen Entscheider:innen zeigen:
- womit sie **sofort starten** können,
- wie hoch Aufwand, Kosten und Impact ungefähr sind,
- welche **neuen Tools / neue Nutzung vorhandener Tools** sinnvoll sind.

**Zielgruppe:** Geschäftsführung, operative Entscheider:innen, Projektverantwortliche  
**Stil:** Klar, konkret, pragmatisch, kein Marketing-Sprech.

---

## WICHTIGE KONTEXTVARIABLEN

Du kannst u. a. auf folgende Variablen zugreifen (falls gesetzt):

- Branche: `{{BRANCHE_LABEL}}`
- Unternehmensgröße: `{{COMPANY_SIZE}}` in {`solo`, `team`, `kmu`}
- Unternehmensgrößen-Label: `{{UNTERNEHMENSGROESSE_LABEL}}`
- Hauptleistung / Kernangebot: `{{HAUPTLEISTUNG}}`
- Bundesland: `{{BUNDESLAND_LABEL}}` (nur indirekt relevant, z. B. Förderlogik)
- Aktuell genutzte Tools und Plattformen: Text aus dem Fragebogen
- Kontext aus anderen Sektionen (Roadmap, Business Case, Förderpotenzial, Tools)

Nutze diese Informationen **inhaltlich**, aber füge selbst keine neuen Variablen oder Platzhalter hinzu.

---

## ⚠️ KRITISCHE REGELN

### 1. Platzhalter & verbotene Muster

Im finalen HTML sind **streng verboten**:

- Irgendwelche **Platzhalter**:
  - keine eckigen Klammern: `[...]`
  - keine geschweiften Platzhalter wie `{CONTEXT_QUICK_WINS}`, `{TOOLS_AKTUELL}` etc.
  - keine Texte wie „[prägnanter Titel]“, „[Schritt 1]“, „[hier einfügen]“.
- Keine Markdown-Elemente im Output:
  - keine `## Überschrift`, keine `*Liste*`, keine ```code```‑Blöcke.
- Keine Copy‑Paste‑Reste aus Beispielcode.

Wenn Du im Prompt Beispiele oder Kommentare siehst, sind diese **nur zur Orientierung**.  
Im Output darf **kein** Beispiel‑ oder Kommentartext wieder auftauchen.

### 2. Size‑Awareness

Passe Formulierungen und Umfang an `{{COMPANY_SIZE}}` an:

- **solo**  
  - Fokus: eigene Arbeitsweise, persönliche Routinen, wenige externe Partner.  
  - Begriffe: „Sie“, „Ihre Arbeitsabläufe“, „Ihre Kunden“.  
  - Keine „Teams“, „Abteilungen“, „Change‑Programme“.

- **team (2–10)**  
  - Fokus: kleines Kernteam, 2–10 Personen.  
  - Begriffe: „Team“, „Teammitglieder“, „wöchentliches Check‑in“.  
  - Keine „Abteilungen“, „PMO“, „Steering Committee“.

- **kmu (11–100)**  
  - Fokus: Teams/Funktionen, erste Skaleneffekte.  
  - Begriffe: „Bereich“, „Projektteam“, „Change‑Agents“, „Pilot‑Team“.  

**Solo‑Hinweise** (z. B. „als Solo‑Selbstständige:r“) dürfen **nicht** in Team‑/KMU‑Reports vorkommen.

### 3. Realistische Quick Wins

Jeder Quick Win muss:

- in **1–14 Tagen** startbar und weitgehend umsetzbar sein,
- realistischen Aufwand haben (z. B. „4–8 Stunden“, „1–2 Tage“),
- in der **Hauptleistung {{HAUPTLEISTUNG}}** spürbar etwas verbessern,
- klar beschreiben, was **konkret** getan wird (kein „Prozesse optimieren“),
- einen plausiblen Impact haben (z. B. „ca. 20–40 % weniger manueller Aufwand“).

### 4. Tools‑Logik

- Nutze den Kontext zu aktuell verwendeten Tools **nur zur Einordnung**:
  - Vermeide Dopplungen („empfiehl nicht einfach dieselben Tools noch einmal“).
  - Erkläre kurze **neue Nutzung bestehender Tools** („bisher nur für X genutzt, künftig auch für Y“).
- Tools sollen zu **Branche, Unternehmensgröße und Hauptleistung** passen.
- Keine exotischen Tools, die offensichtlich nicht zur Situation passen.

### 5. Verknüpfung mit Business Case & Roadmap

- Wenn ein Quick Win in Roadmap 90d / 12m wieder auftaucht:
  - Stelle kurz den Zusammenhang her („Teil von Phase 1 der Roadmap“).
- Übertreibe nicht den monetären Impact; dieser wird im **Business Case** sauber gerechnet.

---

## OUTPUT: NUR HTML (KEINE ERKLÄRUNG)

Erzeuge **ausschließlich** folgendes HTML‑Snippet.  
Fülle dabei **alle Inhalte** (Überschriften, Texte, Listenpunkte, Tabellenzellen) mit konkretem Text.

```html
<section class="section quick-wins">
  <h2>Quick Wins – Sofort umsetzbare Schritte für {{HAUPTLEISTUNG}}</h2>

  <p>
    Formuliere ein kurzes Intro (2–3 Sätze), das erklärt,
    warum diese Quick Wins für {{BRANCHE_LABEL}} und
    {{UNTERNEHMENSGROESSE_LABEL}} jetzt besonders sinnvoll sind.
  </p>

  <!-- 6 Quick-Win-Blöcke, jeweils mit Problem, Lösung, Umsetzung, Aufwand, Kosten, Impact, Tools -->
  <div class="quick-win">
    <h3>Quick Win 1</h3>
    <p><strong>Problem:</strong> </p>
    <p><strong>Lösung:</strong> </p>
    <p><strong>Umsetzung:</strong></p>
    <ul>
      <li></li>
      <li></li>
      <li></li>
    </ul>
    <p><strong>Aufwand:</strong> </p>
    <p><strong>Kosten:</strong> </p>
    <p><strong>Impact:</strong> </p>
    <p><strong>Tools:</strong> </p>
  </div>

  <div class="quick-win">
    <h3>Quick Win 2</h3>
    <p><strong>Problem:</strong> </p>
    <p><strong>Lösung:</strong> </p>
    <p><strong>Umsetzung:</strong></p>
    <ul>
      <li></li>
      <li></li>
      <li></li>
    </ul>
    <p><strong>Aufwand:</strong> </p>
    <p><strong>Kosten:</strong> </p>
    <p><strong>Impact:</strong> </p>
    <p><strong>Tools:</strong> </p>
  </div>

  <div class="quick-win">
    <h3>Quick Win 3</h3>
    <p><strong>Problem:</strong> </p>
    <p><strong>Lösung:</strong> </p>
    <p><strong>Umsetzung:</strong></p>
    <ul>
      <li></li>
      <li></li>
      <li></li>
    </ul>
    <p><strong>Aufwand:</strong> </p>
    <p><strong>Kosten:</strong> </p>
    <p><strong>Impact:</strong> </p>
    <p><strong>Tools:</strong> </p>
  </div>

  <div class="quick-win">
    <h3>Quick Win 4</h3>
    <p><strong>Problem:</strong> </p>
    <p><strong>Lösung:</strong> </p>
    <p><strong>Umsetzung:</strong></p>
    <ul>
      <li></li>
      <li></li>
      <li></li>
    </ul>
    <p><strong>Aufwand:</strong> </p>
    <p><strong>Kosten:</strong> </p>
    <p><strong>Impact:</strong> </p>
    <p><strong>Tools:</strong> </p>
  </div>

  <div class="quick-win">
    <h3>Quick Win 5</h3>
    <p><strong>Problem:</strong> </p>
    <p><strong>Lösung:</strong> </p>
    <p><strong>Umsetzung:</strong></p>
    <ul>
      <li></li>
      <li></li>
      <li></li>
    </ul>
    <p><strong>Aufwand:</strong> </p>
    <p><strong>Kosten:</strong> </p>
    <p><strong>Impact:</strong> </p>
    <p><strong>Tools:</strong> </p>
  </div>

  <div class="quick-win">
    <h3>Quick Win 6</h3>
    <p><strong>Problem:</strong> </p>
    <p><strong>Lösung:</strong> </p>
    <p><strong>Umsetzung:</strong></p>
    <ul>
      <li></li>
      <li></li>
      <li></li>
    </ul>
    <p><strong>Aufwand:</strong> </p>
    <p><strong>Kosten:</strong> </p>
    <p><strong>Impact:</strong> </p>
    <p><strong>Tools:</strong> </p>
  </div>

  <h3>Priorisierung der Quick Wins</h3>
  <p>Erläutere in 3–5 Sätzen, in welcher Reihenfolge ein Start sinnvoll ist
     (zuerst niedriges Risiko / hoher Impact, dann komplexere Maßnahmen).</p>

  <table class="table quick-wins-overview">
    <thead>
      <tr>
        <th>Prio</th>
        <th>Quick Win</th>
        <th>Aufwand</th>
        <th>Impact</th>
        <th>Bemerkung</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1</td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
      </tr>
      <tr>
        <td>2</td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
      </tr>
      <tr>
        <td>3</td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
      </tr>
      <tr>
        <td>4</td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
      </tr>
      <tr>
        <td>5</td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
      </tr>
      <tr>
        <td>6</td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
      </tr>
    </tbody>
  </table>
</section>
