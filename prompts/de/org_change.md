Developer:
<!-- PLATIN++ PROMPT v5.4 - SPRINT G5 -->
<!-- SECTION: org_change -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{KI_ZIELE_LABELS}}, {{KI_HEMMNISSE_LABELS}}, {{ki_kompetenz}}, {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}, {{score_befaehigung}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, kmu:1.15x=2530) -->
<!--
ZIEL: Präziser Abschnitt „Veränderungsfähigkeit & Lernen".

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern

PFLICHTSTRUKTUR (4 Abschnitte):
1. "Wo Sie heute stehen" (Score-Interpretation, 2-3 Absätze)
2. "Wichtigste Veränderungsfelder" (min. 3 Bulletpoints)
3. "Fahrplan für die nächsten 90 Tage" (3 Phasen: 0-30, 31-60, 61-90)
4. "Umgang mit Widerständen" (size-aware)

ANTI-REDUNDANZ (STRIKT!):
- Change-Aspekte HIER behandeln
- NICHT in strategie_governance wiederholen (→ Querverweis)
- 90-Tage-Fahrplan ergänzt roadmap_90d, wiederholt nicht
- Bei Überschneidung: Querverweis nutzen

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: persönliche Routinen, Self-Review, eigene Prüfpunkte
- team: Teamabsprachen, KI-Koordinator, gemeinsame Review-Runden
- kmu: Fachbereichs-Koordination, bereichsübergreifende Standards

SPRINT G5 - PERSONA HARD-GUARDS (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
SOLO-MODUS - VERBOTEN:
- "Team/Teams/Abteilung/Mitarbeiter" → nicht verwenden
- "Fachbereich" → "Arbeitsfeld"
- "HR" → nicht verwenden
{% elif COMPANY_SIZE == "team" %}
TEAM-MODUS - VERBOTEN:
- "Division/Unit/Konzern" → nicht verwenden
- "Abteilung" → "Bereich"
- Solo-Begriffe: "Einzelperson", "allein"
{% else %}
KMU-MODUS - VERBOTEN:
- "Konzern/Division/Unit" → nicht verwenden
- Solo-Begriffe: "Einzelperson", "allein"
{% endif %}

REGELN:
- Scores AKTIV interpretieren
- Keine generischen Aussagen ohne klaren Nutzen
-->

<section class="section org-change">
  <h2>Veränderungsfähigkeit &amp; Lernen</h2>

  <p>
    Für {{BRANCH_CONTEXT_LABEL}} mit Schwerpunkt <strong>{{OFFERING_LABEL}}</strong>
    erfordert die KI-Einführung neue Arbeitsweisen und Routinenanpassung. Die aktuelle
    Selbsteinschätzung – KI-Kompetenz (<strong>{{ki_kompetenz}}</strong>) und Ziele
    <strong>{{KI_ZIELE_LABELS}}</strong> – zeigt vorhandenes Potenzial.
    Hemmnisse wie <strong>{{KI_HEMMNISSE_LABELS}}</strong> erfordern geschärfte
    Strukturen, Prioritäten und Verantwortlichkeiten.
  </p>

  <h3>1. Wo Sie heute stehen</h3>
  <p>
    Die Analyse der Scores zeigt ein differenziertes Bild:
    Governance (<strong>{{score_governance}}</strong>), Sicherheit
    (<strong>{{score_sicherheit}}</strong>), Nutzen (<strong>{{score_nutzen}}</strong>)
    und Befähigung (<strong>{{score_befaehigung}}</strong>) sind unterschiedlich ausgeprägt.
    Für {{OFFERING_LABEL}} bedeutet das: Einige Routinen funktionieren,
    jedoch braucht es klarere Entscheidungswege und einheitliche Qualitätsstandards.
  </p>

  <p>
    Die notwendigen Schritte unterscheiden sich je nach Unternehmensgröße:
    {% if COMPANY_SIZE == "solo" %}
      In Solo-Setups hängt alles an klaren persönlichen Routinen, einfachen Standards und
      konsequenter Selbstorganisation.
    {% elif COMPANY_SIZE == "team" %}
      In kleinen Teams ist entscheidend, Rollen sauber zu definieren und kurze,
      verlässliche Abstimmungen zu etablieren.
    {% else %}
      In KMU stehen koordinierte Prozesse, Verantwortlichkeiten pro Fachbereich
      und eine konsistente Kommunikation im Vordergrund.
    {% endif %}
  </p>

  <h3>2. Wichtigste Veränderungsfelder</h3>
  <ul>
    <li>
      <strong>Arbeitsroutinen vereinheitlichen:</strong>
      KI muss an klaren Stellen in den branchentypischen Workflows eingesetzt werden
      – etwa bei wiederkehrenden Analysen, Dokumentationen, Qualitätskontrollen oder
      inhaltlichen Entwürfen. Einheitliche Vorlagen und klare Input-Regeln senken
      Fehlerquoten und steigern die Verlässlichkeit.
    </li>
    <li>
      <strong>Rollen &amp; Verantwortlichkeiten klären:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Eine klare persönliche Aufteilung der „Hüte“ – z. B. Erstellung, Prüfung, Freigabe –
        schafft Fokus und Kontrolle.
      {% elif COMPANY_SIZE == "team" %}
        Eine eindeutige Rollenverteilung (Teamlead, KI-Owner, Review-Rolle) vermeidet
        Doppelarbeit und sorgt für transparente Abläufe.
      {% else %}
        Fachbereiche benötigen definierte Verantwortliche für KI-Einsatz,
        Qualitätssicherung und Freigaben, damit die Skalierung gelingt.
      {% endif %}
    </li>
    <li>
      <strong>Feedback &amp; Dokumentation stärken:</strong>
      Kurze Feedback-Schleifen, strukturierte Notizen und ein kompakter Standard
      helfen, erfolgreiche KI-Experimente in wiederkehrende, belastbare Abläufe
      umzuwandeln. Dies gilt besonders in {{BRANCH_CONTEXT_LABEL}},
      wo typische Pain Points eng mit Datenqualität, Zeitdruck oder komplexen
      Entscheidungswegen zusammenhängen.
    </li>
  </ul>

  <h3>3. Fahrplan für die nächsten 90 Tage</h3>
  <p>
    Der Wandel gelingt am besten durch klar priorisierte Schritte. Die folgende
    90-Tage-Struktur ergänzt die Roadmap (→ siehe Roadmap-Abschnitt).
  </p>

  <ul>
    <li>
      <strong>0–30 Tage – Orientierung &amp; Standards:</strong>
      2–3 zentrale KI-Einsatzstellen definieren, einfache Input-Regeln formulieren,
      branchentypische Beispiele sammeln und eine erste, kurze Dokumentationsvorlage anlegen.
      {% if COMPANY_SIZE == "solo" %}
        Fokus auf persönliche Wiederholbarkeit und realistische Routinen.
      {% elif COMPANY_SIZE == "team" %}
        Abstimmung zwischen Teamlead und KI-Owner zur gemeinsamen Nutzung der neuen Standards.
      {% else %}
        Einbindung relevanter Fachbereiche zur Abstimmung von Qualitäts- und Freigaberegeln.
      {% endif %}
    </li>

    <li>
      <strong>31–60 Tage – Qualität &amp; Kompetenz:</strong>
      Review-Schleifen etablieren, einfache Guidelines zu Stil, Vollständigkeit und
      Prüfschritten definieren und eine kleine interne Best-Practice-Sammlung starten.
      {% if COMPANY_SIZE == "solo" %}
        Fokus auf schnelle Lernzyklen und konsequente Vereinfachung.
      {% elif COMPANY_SIZE == "team" %}
        Team-Reviews zur Harmonisierung der Ergebnisse.
      {% else %}
        Fachbereichsübergreifende kurze Formate (Quality-Runden, Mini-Workshops).
      {% endif %}
    </li>

    <li>
      <strong>61–90 Tage – Stabilisierung &amp; erste Skalierung:</strong>
      Regelmäßige Reflexion (Solo: kurzer Wochen-Check; Team: kurze Team-Reviews;
      KMU: Bereichs- oder Prozessrunden), Kennzahlen für Zeitersparnis und Qualität
      festlegen und entscheiden, welche Workflows in den Regelbetrieb überführt werden.
    </li>
  </ul>

  <h3>4. Umgang mit Widerständen</h3>
  <p>
    Widerstände entstehen meist durch Unsicherheit über Qualität, Datenschutz oder
    veränderte Arbeitsweisen. Entscheidend ist ein transparenter Umgang mit den neuen
    KI-gestützten Routinen – und zwar size-aware:
    {% if COMPANY_SIZE == "solo" %}
      Solo-Unternehmen profitieren vor allem von klaren, leicht überprüfbaren persönlichen
      Routinen, die Vertrauen schaffen.
    {% elif COMPANY_SIZE == "team" %}
      Kleine Teams benötigen offene, kurze Abstimmungen und klare Rollen, damit sich die
      neuen Arbeitsweisen im Alltag stabilisieren.
    {% else %}
      In KMU sind verständliche Kommunikation, transparente Vorgaben und fachbereichsnahe
      Verantwortlichkeiten entscheidend, um Vorbehalte zu reduzieren.
    {% endif %}
    Kontinuierliches Feedback – verbunden mit konkreten kleinen Verbesserungen –
    sorgt dafür, dass KI als verlässlicher Bestandteil der Wertschöpfung akzeptiert wird.
  </p>
</section>
