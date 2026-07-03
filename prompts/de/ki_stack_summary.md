<!-- G20 – KI-Stack Summary Card (DE) -->
<!-- FIX-506: STRICT CANONICAL CONTRACT -->
<!--
###############################################################################
##                    STRICT CANONICAL CONTRACT                              ##
###############################################################################

You MUST NOT:
- invent, estimate or restate KPI values
- use example numbers, ranges or scenarios
- include conversational phrases
- explain ROI/Payback with numbers

You MAY:
- reference canonical KPIs symbolically ("laut Business Case")
- explain logic and implications WITHOUT numbers
- defer numeric details explicitly to KPI or Simulation sections

If a number is required:
→ write: "siehe Business Case / Simulation"

DE-PRIMED EXCLUSION (Fail-Closed):
Vermeide Beratungs-/Chat-Floskeln und technische Architektur-Begriffe.
Formuliere umsetzungsnah für Solo-/KMU-Betrieb.
Keine Annahmen, keine Beispielmarker, keine Enterprise-Terminologie.

###############################################################################
-->
AUSGABEREGEL (zwingend): Schreibe ausschließlich deklarative Berichtssätze. Keine Anrede, keine Fragen, keine Meta-Kommentare, keine Hinweise auf fehlende Eingaben, keine Imperative. Beginne niemals mit Verben wie „beschreibe", „schreibe", „antworte", „hilf". Kein Bezug auf den Leser oder auf „Nachrichten/Fragen".

STARTFORMAT: Beginne mit einem neutralen Substantivsatz (wie „Der aktuelle Zustand…", „Die empfohlene Vorgehensweise…", „Der strategische Rahmen…").

NICHT ERLAUBT: Hilfsangebote, Gesprächseinstiege, Eingabeaufforderungen, Rückfragen an den Nutzer, Begrüßungsfloskeln, Chat-Formulierungen jeder Art.

WICHTIG: Verwenden Sie keine Anrede, keine Fragen, keine Assistenz- oder Chat-Formulierungen. Keine Meta-Kommentare über fehlende Eingaben. Schreiben Sie ausschließlich in neutraler Berichtssprache.

<!-- G20 – KI-Stack Summary Card (DE) -->

AKTUALITÄTS-REGEL (KIS-1234, zwingend):
- Nenne KEINE LLM-Modellversionen aus eigenem Trainingswissen (kein "GPT-4",
  "Claude 3", "Gemini 1.5" o. Ä.) — solche Angaben veralten und beschädigen
  die Glaubwürdigkeit des Reports.
- Schreibe versionslos und anbieterbezogen ("OpenAI-API", "Anthropic
  Claude-API") ODER übernimm Modell-/Produktnamen EXAKT aus dem
  bereitgestellten Kontext (Tools Engine / Recherche), falls dort vorhanden.

AUFGABE
Erzeuge eine kompakte, C-Level-taugliche „KI-Stack Summary Card" als HTML-Block ohne <h1> oder <h2>.
Der Block wird direkt nach dem Executive Summary in einem PDF-Report eingesetzt.

KONTEXTQUELLEN (oberhalb verfügbar):
- Fragebogen-Auswertung
- Branch-Profil (inkl. {{BRANCH_SHORT_LABEL}})
- Tools Engine 3.0 Ergebnisse
- Funding-Analyse (Förderprogramme)
- Starter-Kit / Quick-Wins
- Business-Case-Kennzahlen (ROI, Payback, Zeitersparnis/Monat)

WICHTIG
- Schreibe in sachlich-professionellem, motivierendem Ton.
- Neutrale Formulierungen – kein Duzen oder Siezen.
- Nur die HTML-Struktur ausgeben, keine Einleitung.

INHALTLICHE STRUKTUR (5 feste Bausteine)

1) Top-3 Tools (Score-basiert aus der Tools Engine 3.0)
   - Die drei relevantesten Tools aus dem vorhandenen Kontext.
   - Pro Tool ausgeben:
     - Name
     - Kategorie: Automation / Analysis / Collaboration / Compliance / Research
     - Kurzsatz zum Nutzen (genau 1 Zeile, klar und konkret, ohne Buzzwords).

2) Top-2 Förderprogramme (aus Funding Alignment)
   - Zwei Programme, die für das vorliegende Profil (Größe + Branche + Vorhaben) besonders passend sind.
   - NUR Programme verwenden, die im bereitgestellten Kontext (Funding-Analyse)
     tatsächlich vorkommen — KEINE Programme aus eigenem Wissen ergänzen und
     keine ausländischen Programme für deutsche Unternehmen. Fehlen Programme
     im Kontext: diesen Baustein weglassen.
   - Pro Programm ZWINGEND:
     - Name (die pair-card-name-Zeile MUSS gefüllt sein — niemals eine Karte
       ohne Programmnamen ausgeben)
     - geschätzte Förderquote ODER klarer Relevanzindikator
     - Kurzsatz zum Mehrwert im Kontext der geplanten KI-Einführung.

3) Starter-Kit Kurzpfad (verdichtetes Starter Kit)
   - Exakt drei Schritte:
     1. Setup (Grundlage schaffen)
     2. Workflow (konkrete Einbindung in Prozesse)
     3. Optimierung (Feintuning, Standards, Governance)
   - Jeder Schritt: 1–2 Sätze, klar verständlich und umsetzungsorientiert.

4) 3 wichtigste Business-Case KPIs (NUR diese kanonischen Werte verwenden!)
   - ROI-Rate: {{ROI_CAPPED_PCT}}% (EXAKT diesen Wert verwenden)
   - Payback: {{PAYBACK_MONTHS}} Monate (EXAKT diesen Wert verwenden)
   - Zeitersparnis: {{ROI_STUNDEN_MONAT}} Stunden/Monat (EXAKT diesen Wert verwenden)
   - Kurz kommentieren, was diese KPIs für die Entscheidungsebene bedeuten.
   - KEINE eigenen KPI-Werte erfinden oder berechnen!
   - WICHTIG: ROI bezieht sich IMMER auf 12 Monate. Schreibe "nach 12 Monaten", NIEMALS "24 Monate" oder andere Zeiträume.
   - WICHTIG: Wenn du Zeitersparnis, Stunden oder Entlastung in Fließtext erwähnst, verwende EXAKT {{ROI_STUNDEN_MONAT}} Stunden — NIEMALS andere Zahlen erfinden!

5) Branch Badge + Risikoindikator
   - Branch-Label: {{BRANCH_SHORT_LABEL}}.
   - AI-Act Risikoklasse: übernimm EXAKT den kanonischen Wert {{AI_ACT_RISK_LEVEL}}
     (genau einer von: minimal / limited / high-risk). NICHT frei schätzen und NICHT
     auf eine eigene niedrig/mittel/hoch-Skala übersetzen — der Wert MUSS mit Cover
     und AI-Act-Kompakt übereinstimmen.
   - Badge-Klasse passend zum Wert: minimal → risk-low, limited → risk-medium,
     high-risk → risk-high.
   - 1–2 Sätze, was diese Risikoklasse konkret bedeutet.

SIZE-AWARE LOGIK

- SOLO (Ein-Personen-Setup):
  - Fokus auf Machbarkeit, Fokus, wenige Tools und klare Prioritäten.
  - Starter-Kit auf persönliche Arbeitsweise und Zeitersparnis ausrichten.
  - Textumfang: mindestens 150 Wörter.

- TEAM (kleine Teams, 2–15 Personen):
  - Fokus auf Zusammenarbeit, Rollen, erste Governance-Ansätze und einfache Standards.
  - Tools und Förderprogramme so wählen, dass Team-Workflows profitieren.
  - Textumfang: mindestens 180 Wörter.

- KMU:
  - Fokus auf Erweiterung, Standardisierung, Verantwortlichkeiten, Risikomanagement.
  - Förderprogramme und KPIs strategisch und investitionsorientiert darstellen.
  - Textumfang: mindestens 200 Wörter.

Maximale Gesamtlänge: 350 Wörter (alle Bausteine zusammen).

HTML-ANFORDERUNGEN & DESIGN (G21 PLATIN++)

**Verfügbare CSS-Klassen:**
- `.pair-card` – Card für einzelne Tools oder Förderprogramme
- `.pair-card-icon` – Icon-Container (passende SVG Icons)
- `.pair-card-content` – Hauptinhalt der Card
- `.pair-card-name` – Name des Tools/Programms (fett)
- `.pair-card-category` – Kategorie-Badge
- `.pair-card-description` – Beschreibung (1 Zeile)

- `.step-cards` – Grid für 3 Schritte (Starter Kit)
- `.step-card` – Einzelne Step-Card
- `.step-card-number` – Schritt-Nummer (1, 2, 3)
- `.step-card-title` – Titel des Schritts
- `.step-card-body` – Beschreibung des Schritts

- `.kpi-triple` – Grid für 3 KPIs
- `.kpi` – Einzelner KPI-Block
- `.kpi-label` – KPI-Bezeichnung
- `.kpi-value` – KPI-Wert (groß, fett, blau)
- `.kpi-sub` – Zusatzinformation

- `.badge-block` – Container für Branch + Risk
- `.badge-block-item` – Einzelnes Badge
- `.badge-block-label` – Label
- `.badge-block-value` – Wert
- `.risk-low`, `.risk-medium`, `.risk-high` – Risiko-Farben

**SVG Icons (inline verwenden):**
- Automation: `<svg viewBox="0 0 24 24" fill="none"><path d="M9.75 17L3.75 11L9.75 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M14.25 17L20.25 11L14.25 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
- Analysis: `<svg viewBox="0 0 24 24" fill="none"><path d="M3 13L9 7L13 11L21 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 9V3H15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
- Collaboration: `<svg viewBox="0 0 24 24" fill="none"><circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="1.5"/><circle cx="17" cy="17" r="3" stroke="currentColor" stroke-width="1.5"/><path d="M13 12H19C20.1046 12 21 12.8954 21 14V14.5M3 18V17C3 14.7909 4.79086 13 7 13H9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`
- Funding: `<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/><path d="M12 6V18M15 9C15 7.34315 13.6569 6 12 6C10.3431 6 9 7.34315 9 9C9 10.6569 10.3431 12 12 12C13.6569 12 15 13.3431 15 15C15 16.6569 13.6569 18 12 18C10.3431 18 9 16.6569 9 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`

**Struktur-Beispiel:**

```html
<div class="ki-stack-summary">
  <!-- Top-3 Tools -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Top-3 empfohlene Tools</strong></p>

    <div class="pair-card">
      <div class="pair-card-icon">[SVG Icon]</div>
      <div class="pair-card-content">
        <p class="pair-card-name"><strong>Tool-Name</strong></p>
        <span class="pair-card-category">Automation</span>
        <p class="pair-card-description">Kurzbeschreibung in einem Satz.</p>
      </div>
    </div>
  </div>

  <!-- Förderprogramme -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Passende Förderprogramme</strong></p>
    [2 pair-cards mit funding icon...]
  </div>

  <!-- Starter Kit -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Starter-Kit in 3 Schritten</strong></p>
    <div class="step-cards">
      <div class="step-card">
        <div class="step-card-number">1</div>
        <p class="step-card-title"><strong>Setup</strong></p>
        <div class="step-card-body">Beschreibung...</div>
      </div>
    </div>
  </div>

  <!-- KPIs -->
  <div class="stack-section">
    <p class="stack-section-title"><strong>Business-Case Kennzahlen</strong></p>
    <div class="kpi-triple">
      <div class="kpi">
        <span class="kpi-label">ROI</span>
        <span class="kpi-value">45%</span>
        <span class="kpi-sub">nach 12 Monaten</span>
      </div>
    </div>
  </div>

  <!-- Branch + Risk -->
  <div class="stack-section">
    <div class="badge-block">
      <div class="badge-block-item">
        <span class="badge-block-label">Branche</span>
        <span class="badge-block-value">{{BRANCH_SHORT_LABEL}}</span>
      </div>
      <div class="badge-block-item risk-low">
        <span class="badge-block-label">AI Act Risiko</span>
        <span class="badge-block-value">minimal</span>
      </div>
    </div>
    <p>Erklärung zum Risikoniveau...</p>
  </div>
</div>
```

AUSGABEFORMAT

Gib ausschließlich den fertigen HTML-Block aus mit den fünf Bausteinen:
1. Top-3 Tools
2. Top-2 Förderprogramme
3. Starter-Kit Kurzpfad
4. Business-Case KPIs
5. Branch Badge + AI-Act Risk Level

<!-- ZERO-LEAK POLICY (N4.6) -->
VERBOTEN – NIEMALS VERWENDEN:
- Keine Fragen an den Leser
- Keine Aufforderungen
- Keine Assistenten-Sprache
- Keine Angebote
- Keine interaktiven Elemente
- Keine Platzhalter (außer definierten)
- Keine Meta-Kommentare

Der Output ist ein FINALER REPORT-ABSCHNITT, kein Gespräch.
