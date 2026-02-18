Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: kickoff_vorlage -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 700 (solo:0.8x=560, team:1.0x=700, kmu:1.15x=805) -->
<!--
ZIEL: Strukturierte Kickoff-Vorlage für den Start eines KI-Projekts.

PFLICHTSTRUKTUR:
1. Agenda (7 Punkte mit Zeiten)
2. Vorbereitungs-Fragenkatalog (4 Bereiche)
3. Ergebnis-Template

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: Schneller Selbst-Check, 30 Min., fokussiert auf Quick Wins
- team: Gemeinsamer Workshop, Rollen klären, 60-90 Min.
- kmu: Strukturierter Kickoff, Stakeholder einbinden, 2-3 Stunden

SIZE-AWARE VERANTWORTLICHKEITEN:
- solo: "Sie selbst", keine komplexen Rollen
- team: "Projektverantwortlicher", "Team", Peer-Abstimmung
- kmu: "Projektleitung", "Fachbereich", "IT", "Controlling"

ANTI-REDUNDANZ:
- Kickoff HIER, nicht in Roadmap 90d (dort erste Umsetzungsschritte)
- Fokus auf VORBEREITUNG, nicht auf Umsetzung
- Keine Überschneidung mit Quick Wins (dort konkrete erste Aktionen)

STIL:
- Textumfang: 120-180 Wörter
- Praktisch, sofort nutzbar
- Keine Theorie, nur Struktur

Nicht verwenden:
- Keine Platzhalter oder Template-Marker
- Keine Wiederholung von Roadmap-Inhalten
- Keine unrealistischen Zeitvorgaben für die Unternehmensgröße
-->

<section class="section kickoff-vorlage">
  <h2>Kickoff-Vorlage: KI-Projekt starten</h2>

  <p>
    Strukturierter Projektstart für
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="kickoff-content">
    <h4>Agenda (anpassbar)</h4>
    <table class="table">
      <thead>
        <tr>
          <th>#</th>
          <th>Thema</th>
          <th>Dauer</th>
          <th>Verantwortlich</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>1</td><td>Begrüßung & Ziele</td><td>5-10 Min.</td><td>Projektleitung</td></tr>
        <tr><td>2</td><td>Ausgangslage & Pain Points</td><td>15-20 Min.</td><td>Alle</td></tr>
        <tr><td>3</td><td>KI-Potenziale identifizieren</td><td>15-20 Min.</td><td>Fachbereich</td></tr>
        <tr><td>4</td><td>Datenlage klären</td><td>10-15 Min.</td><td>IT / Datenverantwortliche</td></tr>
        <tr><td>5</td><td>Quick Wins definieren</td><td>15-20 Min.</td><td>Alle</td></tr>
        <tr><td>6</td><td>Rollen & Verantwortlichkeiten</td><td>10 Min.</td><td>Projektleitung</td></tr>
        <tr><td>7</td><td>Nächste Schritte & Timeline</td><td>10 Min.</td><td>Projektleitung</td></tr>
      </tbody>
    </table>

    <h4>Fragenkatalog zur Vorbereitung</h4>
    <ul>
      <li><strong>Ziele:</strong> Was soll durch KI besser/schneller/günstiger werden?</li>
      <li><strong>Daten:</strong> Welche Daten liegen digital vor? Gibt es Datenschutz-Einschränkungen?</li>
      <li><strong>Ressourcen:</strong> Wer hat Zeit? Welches Budget steht zur Verfügung?</li>
      <li><strong>Rollen:</strong> Wer entscheidet? Wer setzt um? Wer prüft?</li>
    </ul>

    <h4>Nach dem Kickoff dokumentieren</h4>
    <ul>
      <li>Projektziel (klar formuliert)</li>
      <li>Top 3 Pain Points</li>
      <li>Erster Quick Win + Verantwortlicher</li>
      <li>Nächster Meilenstein + Datum</li>
    </ul>
  </div>

  <p class="small muted">
    Tipp: Kickoff kurz halten, Ergebnisse sofort dokumentieren, Follow-up planen.
  </p>
</section>
