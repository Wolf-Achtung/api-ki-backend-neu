
---

## 3) `prompts/de/foerderprogramme.md` – Förderprogramme (empfohlene Programme aus Research-Engine)

```markdown
Developer: <!-- foerderprogramme.md – v1.5 GOLD STANDARD+ – Förderprogramme
Zweck: Erzeuge eine kompakte, realistische Übersicht der wichtigsten Förderprogramme aus {{FOERDERPROGRAMME_HTML}}.
Wichtig:
- Keine eigenen Programme erfinden, keine Zahlen ergänzen.
- Größenbewusste Einordnung (Solo / Team / KMU).
- Kein "Content wird erstellt", keine Platzhalter.
-->

# FOERDERPROGRAMME – Relevante Förderoptionen

## Ziel des Abschnitts

Erzeuge einen Abschnitt, der:

1. die aus der Research-Pipeline gelieferten Förderprogramme (`{{FOERDERPROGRAMME_HTML}}`) kurz einordnet,
2. erklärt, **warum** diese Programme zur Branche {{BRANCHE_LABEL}} und Größe {{UNTERNEHMENSGROESSE_LABEL}} passen,
3. eine realistische Erwartungshaltung schafft (Aufwand, Förderquoten, Bearbeitungszeiten),
4. konkrete **nächste Schritte** nennt, wie das Unternehmen starten kann.

Ton: nüchtern, hilfreich, ohne Verkaufs-Pathos. Keine Rechts- oder Steuerberatung suggerieren.

---

## Regeln zur Datenbasis

- Nutze **ausschließlich** Inhalte aus `{{FOERDERPROGRAMME_HTML}}` als Quelle für Programme, Konditionen und Links.
- Erfinde keine zusätzlichen Programme, Fördersätze oder Budgets.
- Wenn keine oder nur sehr wenige Programme geliefert werden, erkläre dies transparent im Text („Aktuell wurden nur wenige passende Programme gefunden …“).

---

## Größenlogik

Passe Beispiele und Sprache an `{{UNTERNEHMENSGROESSE_LABEL}}` an:

- **Solo:**  
  Fokus auf niedrigschwellige, schlanke Programme (z. B. Einstiegsberatung, Innovationsgutscheine, Beratungsförderung).  
  Betone einfachen Einstieg und begrenzten Aufwand.

- **Kleines Team (2–10):**  
  Erwähne Programme, die Prozessdigitalisierung, Weiterbildung und erste KI-Pilotprojekte unterstützen.

- **KMU (11–100):**  
  Ergänzend: Programme für größere Investitionen, Verbundprojekte, Kooperation mit Forschungseinrichtungen – aber nur, wenn im Research-HTML enthalten.

---

## HTML-Struktur

Erzeuge genau einen `<section>`-Block:

```html
<section class="section funding">
  <h2>Förderprogramme für Ihr KI-Vorhaben</h2>

  <p>Einleitender Absatz (3–4 Sätze), der kurz erklärt, warum Förderprogramme für {{BRANCHE_LABEL}} und die Unternehmensgröße {{UNTERNEHMENSGROESSE_LABEL}} relevant sind und dass nur Programme berücksichtigt werden, die aktuell in {{FOEDER_REGION}} bzw. dem im Fragebogen angegebenen Bundesland verfügbar sind (falls im Datensatz enthalten).</p>

  <h3>Ausgewählte Programme im Überblick</h3>
  <!-- Hier wird der von der Research-Engine vorbereitete HTML-Block eingebettet -->
  {{FOERDERPROGRAMME_HTML}}

  <h3>Was das für Ihren Business Case bedeutet</h3>
  <p>2–4 Sätze dazu, wie eine mögliche Förderung (z. B. anteilige Förderung von Beratungsleistungen oder Investitionen) die Amortisationszeit und den ROI des unter Abschnitt "Business Case" beschriebenen Szenarios verbessern kann – bewusst ohne zusätzliche Zahlen zu erfinden.</p>

  <h3>Nächste Schritte</h3>
  <ul>
    <li>Kurzfristig: 1–2 konkrete Schritte (z. B. Fördercheck mit Ansprechpersonen, Unterlagen sichten, Fristen prüfen).</li>
    <li>Mittelfristig: 1–2 Schritte zur Integration von Förderung in Ihre KI-Roadmap (z. B. Pilotprojekt als förderfähiges Vorhaben definieren).</li>
    <li>Hinweis: Ein Satz, dass detaillierte Antragsberatung durch entsprechende Stellen/Expert:innen erfolgen sollte.</li>
  </ul>
</section>
