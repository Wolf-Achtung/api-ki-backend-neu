Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: prompt_framework -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}} -->
<!-- TOKEN-BUDGET: 700 (solo:0.8x=560, team:1.0x=700, kmu:1.15x=805) -->
<!--
ZIEL: Kompaktes 5-Schritte-Framework für effektive KI-Prompts.

BRANCHENBEZEICHNUNG-REGEL:
Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

PFLICHTSTRUKTUR:
1. Die 5 Schritte (Kontext, Rolle, Aufgabe, Constraints, Format)
2. Vollständiges Beispiel
3. Troubleshooting-Tabelle
4. Variablen-Nutzung

PROMPT-LEAK VERMEIDEN (KRITISCH!):
- NICHT "Ihr Ziel (z. B. ...)" schreiben → triggert Validator
- NICHT "Platzhalter" oder "Beispieltext" verwenden
- Stattdessen: Konkrete, fertige Beispiele ohne "z. B." Pattern

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: Schnell anwendbar, 1 Beispiel reicht, keine Theorie
- team: Gemeinsame Prompt-Bibliothek aufbauen, Best Practices teilen
- kmu: Standardisierte Prompts für wiederkehrende Aufgaben, Qualitätssicherung

SIZE-AWARE VERANTWORTLICHKEITEN:
- solo: Eigene Prompts, learning-by-doing
- team: Prompt-Sharing im Team, Peer-Review
- kmu: Zentrale Prompt-Bibliothek, Qualitätskontrolle

ANTI-REDUNDANZ:
- Prompt-Technik HIER, nicht in Skillplan (dort allgemeiner Kompetenzaufbau)
- Fokus auf STRUKTUR, nicht auf spezifische Anwendungsfälle
- Keine Überschneidung mit Tools (dort Tool-Auswahl, hier Prompt-Technik)

STIL:
- Textumfang: 150-200 Wörter
- Praktisch, mit konkretem Beispiel
- Keine theoretischen Abhandlungen

Nicht verwenden:
- Keine Template-Variablen oder Marker im Ausgabetext
- Keine Wiederholung von Skillplan-Inhalten
- Keine Tool-spezifischen Anleitungen
-->

<section class="section prompt-framework">
  <h2>Prompt-Framework: 5 Schritte zum perfekten Prompt</h2>

  <p>
    Effektive Prompts für <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    in <strong>{{BRANCHE_LABEL}}</strong>.
  </p>

  <div class="framework-steps">
    <h4>Die 5 Elemente eines guten Prompts</h4>
    <table class="table">
      <thead>
        <tr>
          <th>#</th>
          <th>Element</th>
          <th>Funktion</th>
          <th>Beispiel</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>1</td>
          <td><strong>Kontext</strong></td>
          <td>Hintergrund für die KI</td>
          <td>"Du arbeitest für ein Beratungsunternehmen."</td>
        </tr>
        <tr>
          <td>2</td>
          <td><strong>Rolle</strong></td>
          <td>Expertise der KI</td>
          <td>"Agiere als erfahrener Prozessberater."</td>
        </tr>
        <tr>
          <td>3</td>
          <td><strong>Aufgabe</strong></td>
          <td>Was erreicht werden soll</td>
          <td>"Fasse die Meeting-Ergebnisse zusammen."</td>
        </tr>
        <tr>
          <td>4</td>
          <td><strong>Constraints</strong></td>
          <td>Einschränkungen</td>
          <td>"Max. 5 Punkte, keine Fachbegriffe."</td>
        </tr>
        <tr>
          <td>5</td>
          <td><strong>Format</strong></td>
          <td>Ausgabeform</td>
          <td>"Nummerierte Liste mit Priorität."</td>
        </tr>
      </tbody>
    </table>

    <h4>Troubleshooting</h4>
    <table class="table">
      <thead>
        <tr>
          <th>Problem</th>
          <th>Lösung</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Ergebnis zu vage</td>
          <td>Mehr Kontext + konkretere Constraints</td>
        </tr>
        <tr>
          <td>Ergebnis zu lang</td>
          <td>Format-Vorgabe (z.B. "max. 200 Wörter")</td>
        </tr>
        <tr>
          <td>Falscher Tonfall</td>
          <td>Rolle definieren (z.B. "formell", "locker")</td>
        </tr>
        <tr>
          <td>Unpassende Beispiele</td>
          <td>Branche/Kontext explizit nennen</td>
        </tr>
      </tbody>
    </table>
  </div>

  <p class="small muted">
    Tipp: Prompts iterativ verbessern. Erste Version → Ergebnis prüfen → Prompt anpassen.
  </p>
</section>
