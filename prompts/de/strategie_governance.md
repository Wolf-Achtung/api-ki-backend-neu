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
      Sie bilden einen ersten Rahmen, müssen aber – je nach Größe – weiter präzisiert,
      vereinfacht oder erweitert werden.
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
      ({{LOESCHREGELN_LABEL}}) zeigen, dass Grundstrukturen vorhanden sind,
      jedoch noch stärker formalisiert werden sollten.
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
      KI-gestützte Prozesse können neue Erlösquellen erschließen – wie durch
      digitale Produkte, erweiterbare Service-Formate oder automatisierte Analysen.
      Eine strategische Bewertung lohnt sich insbesondere bei stabilen Kern-Workflows.
    </li>
  </ol>

  <h3>Verantwortung &amp; Steuerung</h3>
  <p>
    Die Steuerung sollte zur Organisationsstruktur passen:
  </p>
  <ul>
    <li><strong>Solo:</strong> Owner-Rolle + feste Routinen</li>
    <li><strong>Team:</strong> Kompakter Kreis aus Teamlead + Anwender:innen</li>
    <li><strong>KMU:</strong> Abgestimmte Verantwortlichkeiten zwischen Fachbereichen und IT</li>
  </ul>
  <p>
    Transparenz und kurze Entscheidungswege sind für alle Größen zentral.
  </p>

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
