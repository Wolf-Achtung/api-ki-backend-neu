Developer: <!-- org_change.md – v2.0 GOLD STANDARD+ – ORG CHANGE & Veränderungsfähigkeit
Zweck: Erzeuge einen praxisnahen Abschnitt "Veränderungsfähigkeit & Lernen" für den KI-Status-Report.
Fokus-Case: Beratung & Dienstleistungen, Unternehmensgröße solo (aber Prompt skaliert sauber auf Team/KMU).
Output: Reines HTML-Snippet ohne Markdown-Fences, mit <section>-Wrapper.
Validator-Ziele:
- Länge: Mindestens 3 Absätze mit je 4–6 Sätzen (de facto > 700 Zeichen)
- Keine Platzhalter wie "Content wird erstellt"
- Keine Begriffe wie "Abteilung" oder "Abteilungsleitung" bei Solo-Unternehmen
-->

# ORG CHANGE – Veränderungsfähigkeit & Lernen

## Zweck des Abschnitts

Erzeuge einen verständlichen, motivierenden Abschnitt zur **organisationalen Veränderungsfähigkeit** rund um KI-Einführung.  
Der Abschnitt soll zeigen:

1. Wo das Unternehmen heute steht (Mindset, Strukturen, Routinen).
2. Welche **konkreten Veränderungen** nötig sind, damit KI im Alltag wirkt.
3. Welche **Lern- und Kommunikationsformate** helfen, Widerstände abzubauen.
4. Wie groß die **Umsetzungslast** realistisch ist – speziell für kleine Unternehmen/solo.

Zielgruppe: Geschäftsführung / Inhaber:in, ggf. Teamleitung.  
Stil: Klar, ermutigend, realistisch. Kein Beraterdeutsch, keine Floskeln.

---

## Kontextvariablen, die du nutzen darfst

- Branche: `{{BRANCHE_LABEL}}`
- Unternehmensgröße (Label): `{{UNTERNEHMENSGROESSE_LABEL}}`
- Hauptleistung: `{{HAUPTLEISTUNG}}`
- KI-Ziele (Labels): `{{KI_ZIELE_LABELS}}`
- Hemmnisse/Barrieren (Labels): `{{KI_HEMMNISSE_LABELS}}`
- Aktuelle KI-Kompetenz: `{{ki_kompetenz}}`
- Reifegrad-Scores (Governance, Sicherheit, Nutzen, Befähigung):  
  `{{score_governance}}`, `{{score_sicherheit}}`, `{{score_nutzen}}`, `{{score_befaehigung}}`

Bau diese Informationen natürlich in die Einleitung und Begründungen ein. Keine Roh-Listen der Variablen ausgeben, sondern in Fließtext integrieren.

---

## Größenlogik (Solo / Team / KMU)

Nutze die Variable `{{UNTERNEHMENSGROESSE_LABEL}}` für Formulierungen und Beispiele:

- **Solo (enthält "Solo" im Label):**
  - Sprich von „Sie“ bzw. „Ihr Unternehmen“ – es handelt sich im Kern um eine Person.
  - Vermeide Wörter wie „Abteilung“, „Abteilungsleitung“, „HR-Abteilung“, „Fachabteilung“.
  - Fokus auf: persönliche Routinen, Priorisierung, Selbstorganisation, Templates, Checklisten.
  - Betonung: kleine, realistische Schritte, die sich in den eigenen Kalender integrieren lassen.

- **Kleines Team (enthält „2–10“ im Label):**
  - Erlaube Begriffe wie „Team“, „Kolleg:innen“, „gemeinsame Routinen“.
  - Fokus: kurze Jour-Fixe, gemeinsame Tool-Standards, geteilte Prompt-Bibliothek.

- **KMU (enthält „11–100“ im Label):**
  - Du darfst Begriffe wie „Team“, „Führung“, „Rollen“ und „Prozessverantwortliche“ verwenden.
  - Trotzdem **kein Konzern-Vokabular** (keine „Division“, „Business Unit“, „Konzernzentrale“).

Wenn du dir unsicher bist: orientiere dich am **konservativen, eher kleinen Setup** und vermeide Konzernbegriffe.

---

## Inhaltliche Leitplanken

### 1. Ausgangssituation & Spannungsfeld

Beschreibe zu Beginn kurz:

- Welche Rolle {{HAUPTLEISTUNG}} im Geschäftsmodell spielt.
- Wie der aktuelle Stand der KI-Nutzung ist (abgeleitet aus `{{ki_kompetenz}}`, `{{KI_AKTIVITAETEN_ZIELE_HTML}}`, {{KI_ZIELE_LABELS}}).
- Welche typischen Hemmnisse für diese Kombination aus Branche {{BRANCHE_LABEL}} und Größe auftreten (z. B. Zeitmangel, Unsicherheit bzgl. Qualität, Datenschutzfragen).

Ton: Anerkennend („Sie haben bereits …“, „Gleichzeitig zeigen die Antworten, dass …“).

### 2. Drei zentrale Veränderungsfelder

Identifiziere **drei konkrete Felder**, z. B.:

1. **Arbeitsroutinen & Prozesse**  
   – z. B. vom spontanen KI-Einsatz zu klar definierten Einsatzpunkten im Workflow.

2. **Kompetenzen & Verantwortlichkeiten**  
   – wer wofür zuständig ist (bei Solo: Sie selbst in klaren Rollen, z. B. „Berater“, „Prompt-Designer“, „Qualitätssicherung“).

3. **Dokumentation & Feedback-Schleifen**  
   – wie KI-Experimente eingefangen und in stabile Standards überführt werden.

Für jedes Feld: 2–4 Sätze, was sich konkret ändern muss – immer mit Bezug auf {{HAUPTLEISTUNG}}.

### 3. Konkreter 90-Tage-Fahrplan (high level)

Beschreibe in einem Absatz und einer Liste, wie der Wandel praktisch angegangen werden kann:

- **Phase 1 (0–30 Tage):** Orientierung & erste Standards  
  – z. B. 2–3 Pilot-Workflows festlegen, einfache Dokumentationsvorlage, Grundregeln für KI-Nutzung.

- **Phase 2 (31–60 Tage):** Vertiefung & Qualitätssicherung  
  – z. B. Review-Schleifen, „Best Prompt“-Sammlung, erste interne Guidelines.

- **Phase 3 (61–90 Tage):** Skalierung & Verstetigung  
  – z. B. regelmäßige Retrospektive, Kennzahlen (z. B. gesparte Stunden, Fehlerquote).

Bei **Solo**: machen klar, dass es eher um wiederkehrende Termine im eigenen Kalender (z. B. „Montag 30 Minuten KI-Werkbank“) geht – nicht um große Change-Projekte.

### 4. Umgang mit Widerständen & Risiken

- Nenne 2–3 typische Widerstände (angepasst an die Größe) und wie man ihnen pragmatisch begegnet.
- Verweise auf Risikoteil, aber wiederhole keine komplette Risikoanalyse.
- Keine abstrakten Formulierungen wie „Stakeholder-Management optimieren“ – immer ein konkretes Beispiel geben.

---

## HTML-Ausgabeformat

Erzeuge **ausschließlich** folgenden Aufbau (kein zusätzliches `<html>`, `<body>` etc.):

```html
<section class="section org-change">
  <h2>Veränderungsfähigkeit & Lernen</h2>

  <p>Ein einleitender Absatz, der Ausgangslage, Unternehmensgröße und Spannungsfeld zwischen Tagesgeschäft und KI-Veränderung beschreibt (4–6 Sätze).</p>

  <h3>1. Wo Sie heute stehen</h3>
  <p>Beschreibung der aktuellen Situation rund um Mindset, Routinen und KI-Kompetenz – konkret bezogen auf {{HAUPTLEISTUNG}} und die Branche {{BRANCHE_LABEL}} (4–6 Sätze).</p>

  <h3>2. Wichtigste Veränderungsfelder</h3>
  <ul>
    <li><strong>Veränderungsfeld A:</strong> 1–2 Sätze, was sich konkret ändern muss und warum das für das Geschäftsmodell relevant ist.</li>
    <li><strong>Veränderungsfeld B:</strong> 1–2 Sätze mit Fokus auf Kompetenzen/Verantwortung.</li>
    <li><strong>Veränderungsfeld C:</strong> 1–2 Sätze mit Fokus auf Feedback, Standards und Dokumentation.</li>
  </ul>

  <h3>3. Fahrplan für die nächsten 90 Tage</h3>
  <p>Kurze Einordnung (2–3 Sätze), warum ein leichter Einstieg sinnvoll ist – speziell für {{UNTERNEHMENSGROESSE_LABEL}}.</p>
  <ul>
    <li><strong>0–30 Tage:</strong> Konkrete erste Schritte, die ohne große Projektstruktur machbar sind.</li>
    <li><strong>31–60 Tage:</strong> Maßnahmen zur Qualitätssicherung und zum Aufbau stabiler Routinen.</li>
    <li><strong>61–90 Tage:</strong> Schritte zur Skalierung und Verstetigung (z. B. Kennzahlen, regelmäßige Reflexion).</li>
  </ul>

  <h3>4. Umgang mit Widerständen</h3>
  <p>2–4 Sätze zu typischen Bedenken und wie man sie pragmatisch adressiert – angepasst an {{UNTERNEHMENSGROESSE_LABEL}} und den Beratungsfokus.</p>
</section>
