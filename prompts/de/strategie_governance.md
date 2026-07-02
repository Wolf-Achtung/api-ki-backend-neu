Developer:
<!-- PLATIN++ PROMPT v5.3 G17.S - SPRINT TRUNCATION-FIX -->
<!-- SECTION: strategie_governance -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{COMPANY_SIZE}}, {{BRANCH_SHORT_LABEL}}, {{GOVERNANCE_RICHTLINIEN_LABEL}}, {{CHANGE_MANAGEMENT_LABEL}}, {{MELDEWEGE_LABEL}}, {{DATENSCHUTZ_LABEL}}, {{LOESCHREGELN_LABEL}}, {{DATENSCHUTZBEAUFTRAGTER_LABEL}}, {{FOLGENABSCHAETZUNG_LABEL}}, {{INTERNE_KI_KOMPETENZEN_LABEL}} -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, kmu:1.15x=2530) -->
<!--
BRANCHENBEZEICHNUNG-REGEL:
Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

HÖCHSTLÄNGE (STRIKT! — Überschreitung wird automatisch getruncated!):
- Solo: max. 2.500 Zeichen (400 Wörter) | Team: max. 7.500 Zeichen (800 Wörter) | KMU: max. 9.000 Zeichen (1100 Wörter)
- WARNUNG: Solo-Budget ist NUR 3.000 Zeichen! Bei 5.5K+ Output = 48% Verlust!
- Solo: Strategische Leitlinien max. 4 Punkte à 1-2 Sätze + Mini-Governance max. 60 Wörter
- Steuerung & KI-Kultur: Solo max. je 40 Wörter
-->
**HARD-LIMITS (Solo: 400 Wörter / 2.500 Zeichen | Team: 800 / 7.500 | KMU: 1100 / 9.000)**
Kürze lieber als zu überziehen — abgeschnittener Content ist wertlos!
<!-- WORD_MINIMUM_SOLO: 150 (G17.S: erhöht von 130 wg. Mini-Governance-Booster) -->
<!--
ZIEL: Strategische Einordnung zu KI-Strategie & Governance.
Ergebnis = 10–14 Sätze + 1 strukturierte Liste.
SPRINT G17.S: Solo erhält zusätzlichen "Mini-Governance für Solo"-Unterabschnitt

PERSONA-VARIATIONEN (COMPANY_SIZE) – STRIKT EINHALTEN:

SOLO:
  Empfohlen: "Checkliste", "Minimale Regeln", "Ein-Personen-Standard",
             "Dokumentation light", "persönliche Routine", "eigene Prüfpunkte"
  Nicht verwenden: "Organisationsentwicklung", "Verantwortlichkeitsmatrix",
                   "Governance Framework", "Rollenmodell", "Gremium", "Board",
                   "Steuerungskreis", "Abteilung", "Team aufbauen", "Mitarbeiter"

TEAM:
  Empfohlen: "Teamabsprache", "gemeinsame Regeln", "KI-Koordinator",
             "kurze Review-Runde", "geteilte Verantwortung"
  Nicht verwenden: "Governance Board", "Matrix-Organisation", "Division"

KMU:
  Empfohlen: "Fachbereichsverantwortliche", "abgestimmte Prozesse",
             "bereichsübergreifende Standards", "Governance-Regeln"
  Nicht verwenden: Konzernjargon ("Business Unit", "Division", "C-Level")

SPRINT G17.S – MINI-GOVERNANCE FÜR SOLO (PFLICHT bei solo!):
Zusätzlicher Unterabschnitt für Solo (~60-80 Wörter):
1. 2-3 leicht umsetzbare KI-Regeln:
   - Versionsführung: Prompts/Outputs mit Datum speichern
   - Transparenz: Kennzeichnung KI-generierter Inhalte vor Versand
   - Abnahme vor Auslieferung: Eigene Prüfung vor Kundenübergabe
2. Kurze Dokumentationsroutine (wöchentlich/monatlich)
3. Hinweis auf Skalierbarkeit für zukünftige Teamkontexte

WICHTIG:
- Keine Team-Vokabeln bei Solo
- Keine Overlaps mit AI_POLICY_MINI

ANTI-REDUNDANZ:
- Strategische Governance HIER behandeln (12-24 Monate Ausrichtung)
- NICHT in org_change wiederholen (→ dort: Change-Perspektive)
- NICHT in risks duplizieren (→ dort: Risikoanalyse)

THEMEN-OWNERSHIP (verbindlich):
- Diese Section: OWNER für KI-Strategie, strategische Governance, Steuerungsmodell, KI-Kultur
- Abgrenzung zu ai_policy_mini: HIER = strategische Ausrichtung & Steuerung,
  DORT = operative Alltagsregeln (5 Spielregeln). KEINE Regel-Details hier wiederholen!
- Abgrenzung zu org_change: HIER = Governance-Strukturen,
  DORT = Veränderungsfähigkeit & Widerstände. KEINE Change-Details hier!
- NICHT hier: Compliance/AI Act Details (→ ai_act_summary)
- NICHT hier: Konkrete Maßnahmen-Timeline (→ roadmap_12m)
- NICHT hier: Risiko-Details (→ risks)

GUARDRAILS: Berücksichtige Leitplanken aus strategischem Kontext.
-->

FAKTEN- UND ANNAHMEN-TRENNUNG (VERBINDLICH):
- Harte Eingabedaten, Scores, deterministische Zahlen und explizite Nutzerangaben als Tatsachen behandeln.
- Schlussfolgerungen aus mehreren Signalen als Einordnung formulieren, nicht als gesicherte Tatsache.
- Branchenübliche Muster, Benchmarks oder fehlende Detailinformationen nur als Annahme oder plausible Ableitung formulieren.
SPRACHMUSTER:
- Faktisch: „Der Score liegt bei ...", „Genannt wurde ...", „Vorgegeben ist ..."
- Abgeleitet: „Daraus ergibt sich ...", „Das spricht dafür, dass ..."
- Annahme: „Erfahrungsgemäß ist zu erwarten ...", „Wahrscheinlich relevant ist ..."

ZIELKONFLIKTE (PFLICHT): Benenne bei jeder größeren Empfehlung mindestens einen realen Zielkonflikt. Beispiele: Geschwindigkeit vs. Qualität, Automatisierung vs. Kontrolle, Datenschutz vs. Bequemlichkeit, Standardisierung vs. Individualität, Investition heute vs. Nutzen später. Formuliere Trade-offs knapp im Fließtext, ohne zusätzliche Sonderbox. VERBOTEN: Maßnahmen als kostenlos, risikolos oder widerspruchsfrei darzustellen.

BEGRIFFSKONSISTENZ (VERBINDLICH — OPT-A7):
Verwende diese Begriffe einheitlich im gesamten Report:
- „KI-Governance" = Oberbegriff für Regeln, Rollen, Freigaben rund um KI-Nutzung. „KI-Richtlinie" = das konkrete Dokument.
- „ROI" = immer „ROI", bei erster Nennung pro Abschnitt „Return on Investment (ROI)".
- „Break-Even" = Zeitpunkt der Amortisation im Fließtext. „Amortisation" nur in Tabellen/KPIs.
- „EU AI Act" = immer, bei erster Nennung „EU AI Act (KI-Verordnung der EU)". NICHT standalone „KI-Verordnung".
- „AVV" = bei erster Nennung „AV-Vertrag (AVV)", danach nur „AVV".
- „KI-Ausgabe" = allgemein für KI-Ergebnisse. „KI-Entwurf" = Text, der noch geprüft werden muss. NICHT „KI-Output".
- „Prüfschritt" = allgemein. „Freigabe" = formaler Akt. „Vier-Augen-Prinzip" = zwei Personen prüfen. NICHT „Review".
- „DSGVO" = nie ausschreiben. „Tool" = Software. „Werkzeug" = nur in Metaphern. Nicht im selben Absatz wechseln.

<!-- SPRINT 2: OPT-B3 Strategische Analyse vertiefen -->
Formuliere verständlich für einen Geschäftsführer ohne KI-Vorwissen. Fachbegriffe bei erster Verwendung in einem Halbsatz erklären.

STRATEGISCHE EINORDNUNG DER HANDLUNGSFELDER (PFLICHT):
Ordne jedes Handlungsfeld und jede Leitlinie im Fließtext natürlich ein — als Stärke, Schwäche, Chance oder Bedrohung. NICHT als separate SWOT-Tabelle oder -Box, sondern eingebettet in den bestehenden Text.
Muster:
- Stärke (worauf aufgebaut werden kann): „Sie haben bereits X — das ist eine solide Grundlage für ..."
- Schwäche (was geschlossen werden muss): „Was fehlt: Y. Ohne diese Grundlage ..."
- Chance (was KI eröffnet): „KI kann hier Z ermöglichen, etwa ..."
- Bedrohung (was bei Nicht-Handeln passiert): „Ohne Handlung riskieren Sie, dass W ..."

Pro Leitlinie (unter „Strategische Leitlinien") mindestens EINE dieser Einordnungen vornehmen.
Im Abschnitt „Rahmenbedingungen & aktueller Status" die bestehenden Angaben (Richtlinien, Change-Management, Meldewege, Datenschutz, Kompetenzen) jeweils als Stärke ODER Schwäche einordnen — basierend auf dem konkreten Label-Wert.
CONSTRAINT: Kein separates SWOT-Kapitel. Max. 1-2 Zusatzsätze pro Listenpunkt. Bestehende Wortlimits einhalten.
<!-- /SPRINT 2 -->

<!-- SPRINT 2: OPT-B5 Governance-Tiefe stärken -->
Formuliere verständlich für einen Geschäftsführer ohne KI-Vorwissen. Fachbegriffe bei erster Verwendung in einem Halbsatz erklären.

GOVERNANCE ALS BETRIEBSMODELL (PFLICHT — im Abschnitt „Verantwortung & Steuerung"):
(a) STEUERUNGSKREIS: Beschreibe segment-gerecht, wer KI-Themen steuert und wie oft:
- Solo: monatliche Selbst-Reflexion (15 Min.), halbjährlich Regeln prüfen.
- Team: KI-Koordinator + monatlicher Kurz-Check (30 Min.) zu Nutzung, Qualität, Regeln.
- KMU: Steuerungskreis aus Fachbereich + IT + Datenschutz, quartalsweise Governance-Runde mit fester Agenda (Nutzungsstatus, Vorfälle, Regelanpassungen).
(b) ESKALATIONSPFAD BEI KI-VORFÄLLEN: Ergänze einen konkreten Eskalationspfad: Vorfall erkannt → Meldung an [Rolle] innerhalb [Zeitrahmen] → Bewertung → Maßnahme. Segment-gerecht formulieren.
(c) ENTSCHEIDUNGSMATRIX: Wer gibt neue KI-Tools frei? Wer ändert die KI-Richtlinie? Wer stoppt einen KI-Prozess? In 2-3 Sätzen klären.
CONSTRAINT: Bestehende Wortlimits einhalten. Max. 3-4 Zusatzsätze im Steuerungs-Abschnitt. Keine Konzern-Vokabeln bei Solo/Team.
<!-- /SPRINT 2 -->

<section class="section governance-strategy">
  <h2>KI-Strategie &amp; Governance</h2>

  <p>
    Für <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in <strong>{{BRANCHE_LABEL}}</strong>
    ist pragmatische Governance entscheidend.
  </p>
  <p>
    Die aktuelle Einschätzung zeigt, wo Richtlinien greifen und wo Weiterentwicklung nötig ist.
  </p>

  <h3>Rahmenbedingungen &amp; aktueller Status</h3>
  <ul>
    <li>
      <strong>Richtlinien &amp; Policy:</strong>
      Die vorhandenen Regeln werden derzeit als {{GOVERNANCE_RICHTLINIEN_LABEL}} beschrieben.
      [P4: Bewerte AUF BASIS dieses Label-Werts als Stärke ODER Schwäche —
      bei gutem Status: worauf sich aufbauen lässt und was beibehalten wird;
      bei schwachem Status: was konkret fehlt und was das ohne Handlung kostet.
      KEIN pauschales „muss weiter präzisiert werden".]
    </li>
    <li>
      <strong>Change-Management &amp; Kommunikation:</strong>
      Der Umgang mit Veränderungen wird als {{CHANGE_MANAGEMENT_LABEL}} bewertet.
      Bedeutung und Nutzen von KI sollten konsistent kommuniziert werden, um Akzeptanz zu steigern.
    </li>
    <li>
      <strong>Meldewege &amp; Vorfälle:</strong>
      Aktuelle Strukturen werden als {{MELDEWEGE_LABEL}} beschrieben.
      Klare Ansprechpersonen und einfache Abläufe erhöhen Sicherheit und Transparenz.
    </li>
    <li>
      <strong>Datenschutz &amp; Löschregeln:</strong>
      Die Angaben zu Datenschutz ({{DATENSCHUTZ_LABEL}}) und Löschregeln
      ({{LOESCHREGELN_LABEL}}).
      [P4: Einordnung aus den Label-Werten ableiten — Stärke benennen, wenn
      der Status gut ist; nur bei tatsächlicher Lücke Formalisierung fordern.]
    </li>
    <li>
      <strong>Verantwortlichkeiten &amp; Kompetenzen:</strong>
      Die Benennung eines/einer Datenschutzbeauftragten ({{DATENSCHUTZBEAUFTRAGTER_LABEL}}),
      die vorhandene KI-Kompetenz ({{INTERNE_KI_KOMPETENZEN_LABEL}}) und der Status von
      Folgenabschätzungen ({{FOLGENABSCHAETZUNG_LABEL}}) liefern Hinweise auf Rollen,
      Zuständigkeiten und vorhandenes Know-how.
    </li>
  </ul>

  <h3>Strategische Leitlinien für die nächsten 12–24 Monate</h3>
  <ol>
    <li>
      <strong>Klare Einsatzregeln etablieren:</strong>
      Festlegung verbindlicher Spielregeln für Eingaben, Datenarten und Qualitätsstandards
      – bei Solo kompakt in Form persönlicher Routinen, bei Teams als gemeinsame Leitlinie,
      im KMU als abgestimmtes Regelwerk mit Verantwortlichkeiten.
    </li>
    <li>
      <strong>Verantwortlichkeiten definieren:</strong>
      Solo: eine Owner-Rolle für Nutzung & Qualität.<br>
      Team: Teamlead + KI-Owner + Anwender:innen.<br>
      KMU: Prozessverantwortliche in Fachbereichen + Datenschutz/IT.
    </li>
    <li>
      <strong>Transparenz &amp; Risikoabsicherung erhöhen:</strong>
      Kurze Dokumentation, einfache Meldewege und einheitliche Freigabepunkte sorgen dafür,
      dass Ergebnisse nachvollziehbar und sicher genutzt werden können.
    </li>
    <li>
      <strong>Kompetenzen gezielt aufbauen:</strong>
      Mini-Trainings, Leitfäden und kurze Reviews schaffen Sicherheit im Umgang mit KI.
      In KMU zusätzlich rollenspezifische Schulungen.
    </li>
    <li>
      <strong>Monetarisierungspotenziale evaluieren (optional):</strong>
      [P4: KEINE generische Erlösquellen-Aufzählung. Benenne EINE zur
      Hauptleistung passende Monetarisierungs-Option mit So-what (warum
      gerade diese, worauf sie aufsetzt) und einem Kill-Kriterium, wann sie
      NICHT weiterverfolgt wird — z. B. solange der Kern-Workflow nicht
      stabil läuft oder die Nachfrage im Bestand nicht validiert ist.]
    </li>
  </ol>

  <h3>Verantwortung &amp; Steuerung</h3>
  <!-- P4: Slots für OPT-B5 — vorher forderte der B5-Block Steuerungskreis/
       Eskalationspfad/Entscheidungsmatrix, das Template hatte aber keinen
       Platz dafür; das Modell musste Zusatzsätze „hineinschmuggeln". -->
  <p>[STEUERUNGSKREIS gemäß OPT-B5(a): wer steuert KI-Themen in dieser
     Unternehmensgröße, in welchem Rhythmus — 1–2 Sätze, segment-gerecht.]</p>
  <p>[ESKALATIONSPFAD gemäß OPT-B5(b): Vorfall erkannt → Meldung an konkrete
     Rolle innerhalb konkretem Zeitrahmen → Bewertung → Maßnahme. 1–2 Sätze.]</p>
  <p>[ENTSCHEIDUNGSMATRIX gemäß OPT-B5(c): wer gibt neue Tools frei, wer
     ändert die KI-Richtlinie, wer stoppt einen KI-Prozess — 2–3 Sätze.]</p>

  <h3>KI-Kultur &amp; Akzeptanz</h3>
  <p>
    {% if COMPANY_SIZE == "solo" %}
    KI ist Werkzeug zur Entlastung, nicht Ersatz eigener Expertise.
    Regelmäßige Selbstreflexion stärkt die Urteilsfähigkeit.
    {% elif COMPANY_SIZE == "team" %}
    Offener Austausch über KI-Erfahrungen schafft gemeinsames Lernen.
    Kurze Berichte in bestehenden Meetings bauen Vorbehalte ab.
    {% else %}
    Positive Fehlerkultur beschleunigt den Lernprozess.
    Champions in Fachbereichen wirken als Multiplikatoren.
    {% endif %}
  </p>

  {% if COMPANY_SIZE == "solo" %}
  <!-- G17.S: Mini-Governance für Solo (Booster-Abschnitt) -->
  <h3>Mini-Governance für Solo</h3>
  <p>
    Auch ohne formale Governance-Strukturen profitieren Sie von einfachen Regeln,
    die Qualität sichern und sich bei Bedarf auf zukünftige Teamkontexte skalieren lassen:
  </p>
  <ul>
    <li>
      <strong>Versionsführung:</strong>
      Speichern Sie wichtige Prompts und Outputs mit Datum und Kontext – so bleibt
      nachvollziehbar, welche Ergebnisse unter welchen Bedingungen entstanden.
    </li>
    <li>
      <strong>Transparenz nach außen:</strong>
      Kennzeichnen Sie KI-generierte Inhalte vor dem Versand an Kunden oder Partner,
      zumindest intern für sich selbst, um den Überblick zu behalten.
    </li>
    <li>
      <strong>Abnahme vor Auslieferung:</strong>
      Führen Sie bei wichtigen Outputs einen kurzen Eigencheck durch – eine
      persönliche Prüfroutine vor jeder Kundenübergabe sichert Qualität.
    </li>
  </ul>
  <p>
    Eine kurze wöchentliche oder monatliche Dokumentation (z.&nbsp;B. "KI-Logbuch")
    hilft, Muster zu erkennen und die eigene Nutzung schrittweise zu verbessern.
    Diese Grundlagen lassen sich bei Wachstum leicht auf ein kleines Team übertragen.
  </p>
  {% endif %}

  <p class="small muted">
    Eine realistische, gut kommunizierte Governance sichert nachhaltige Wirkung,
    unterstützt die Roadmap-Umsetzung und schafft Vertrauen bei Mitarbeitenden und
    Kund:innen gleichermaßen.
  </p>
</section>
