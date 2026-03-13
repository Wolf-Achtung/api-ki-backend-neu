{% if COMPANY_SIZE == "solo" %}
**WICHTIG – Längenlimit: Deine Antwort darf maximal 450 Wörter / 4.000 Zeichen HTML umfassen.**
{% elif COMPANY_SIZE == "team" %}
**WICHTIG – Längenlimit: Deine Antwort darf maximal 700 Wörter / 6.500 Zeichen HTML umfassen.**
{% else %}
**WICHTIG – Längenlimit: Deine Antwort darf maximal 1000 Wörter umfassen.**
{% endif %}
Kürze lieber als zu überziehen — abgeschnittener Content ist wertlos!

Developer:
<!-- PLATIN++ PROMPT v5.5 - SPRINT TRUNCATION-FIX -->
<!-- SECTION: org_change -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{KI_ZIELE_LABELS}}, {{KI_HEMMNISSE_LABELS}}, {{ki_kompetenz}}, {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}, {{score_befaehigung}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, kmu:1.15x=2530) -->
<!--
HÖCHSTLÄNGE (STRIKT!):
- Solo: max. 4.000 Zeichen (450 Wörter) | Team: max. 6.500 Zeichen (700 Wörter) | KMU: max. 8.000 Zeichen (1000 Wörter)
- Solo: Alle 4 Abschnitte, aber je max. 70-90 Wörter. 3 Bullets pro Abschnitt max.
- Lieber prägnant als ausschweifend — jeder Satz muss Mehrwert liefern
-->
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
- KEINE Textbausteine aus anderen Sections übernehmen
- Jeder Satz muss für diese Section EINZIGARTIG formuliert sein
- Prüfe vor Ausgabe: Enthält dieser Text Formulierungen, die wörtlich in roadmap_90d oder gamechanger vorkommen könnten? Falls ja, umformulieren

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

THEMEN-OWNERSHIP (verbindlich):
- Diese Section: NUR Veränderungsfähigkeit, Lernkultur, Widerstandsmanagement, Rollen & Routinen
- NICHT hier: Konkrete 90-Tage-Maßnahmen im Detail (→ roadmap_90d)
- NICHT hier: Governance-Regeln/Rollen im Detail (→ ai_policy_mini)
- NICHT hier: Datenquellen, Datenqualität, IT-Infrastruktur, Systemreife (→ data_readiness)
- NICHT hier: Datenlandkarte, Schnittstellen, Datenbenennung (→ data_readiness)
- NICHT hier: Tool-Listen, Tool-Bewertung (→ tools_empfehlungen)
- Prinzip: WIE der Wandel gelingt, nicht WAS umgesetzt wird

ABGRENZUNG ZU DATA_READINESS (STRIKT!):
- ORG_CHANGE = Menschen, Prozesse, Akzeptanz, Arbeitsroutinen, Schulung
- DATA_READINESS = Daten, Systeme, Infrastruktur, Datenqualität
- Überlappungsgefahr: "Standards einführen" → hier NUR Arbeits-Standards (Routinen, Reviews)
- DATA_READINESS kümmert sich um Daten-Standards (Benennung, Ablage, Zugriffsrechte)
- NICHT über "vorhandene Datenquellen" oder "IT-Infrastruktur" schreiben — das ist DATA_READINESS
-->

<section class="section org-change">
  <h2>Veränderungsfähigkeit &amp; Lernen</h2>

  <p>
    Für {{BRANCH_CONTEXT_LABEL}} erfordert die KI-Einführung neue Arbeitsweisen.
    Die aktuelle Selbsteinschätzung zeigt vorhandenes Potenzial.
  </p>
  <p>
    Hemmnisse wie <strong>{{KI_HEMMNISSE_LABELS}}</strong> erfordern geschärfte
    Strukturen und klare Verantwortlichkeiten.
  </p>

  <h3>1. Wo Sie heute stehen</h3>
  <p>
    <strong>Score-Übersicht:</strong> Governance ({{score_governance}}), Sicherheit ({{score_sicherheit}}),
    Nutzen ({{score_nutzen}}), Befähigung ({{score_befaehigung}}).
  </p>
  <p>
    Einige Routinen funktionieren bereits. Es braucht klarere Entscheidungswege und einheitliche Standards.
  </p>
  <p>
    {% if COMPANY_SIZE == "solo" %}
      In Solo-Setups zählen persönliche Routinen und konsequente Selbstorganisation.
    {% elif COMPANY_SIZE == "team" %}
      In kleinen Teams sind saubere Rollendefinitionen und kurze Abstimmungen entscheidend.
    {% else %}
      In KMU stehen koordinierte Prozesse und Verantwortlichkeiten pro Fachbereich im Fokus.
    {% endif %}
  </p>

  <h3>2. Wichtigste Veränderungsfelder</h3>
  <ul>
    <li>
      <strong>Arbeitsroutinen vereinheitlichen:</strong>
      KI muss an klaren Stellen in den branchentypischen Workflows eingesetzt werden
      – wie bei wiederkehrenden Analysen, Dokumentationen, Qualitätskontrollen oder
      inhaltlichen Entwürfen. Einheitliche Vorlagen und klare Input-Regeln senken
      Fehlerquoten und steigern die Verlässlichkeit.
    </li>
    <li>
      <strong>Rollen &amp; Verantwortlichkeiten klären:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Eine klare persönliche Aufteilung der „Hüte" – wie Erstellung, Prüfung, Freigabe –
        schafft Fokus und Kontrolle.
      {% elif COMPANY_SIZE == "team" %}
        Eine eindeutige Rollenverteilung (Teamlead, KI-Owner, Review-Rolle) vermeidet
        Doppelarbeit und sorgt für transparente Abläufe.
      {% else %}
        Fachbereiche benötigen definierte Verantwortliche für KI-Einsatz,
        Qualitätssicherung und Freigaben, damit die Erweiterung gelingt.
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

  <h3>3. Veränderungsschritte in den ersten 90 Tagen</h3>
  <p>
    Die konkreten Umsetzungsschritte sind im 90-Tage-Fahrplan beschrieben.
    Aus Change-Perspektive sind drei Schwerpunkte entscheidend:
  </p>

  <ul>
    <li>
      <strong>Monat 1 — Orientierung schaffen:</strong>
      Neue Arbeitsweisen an 2–3 konkreten Stellen einführen, nicht flächendeckend.
      Erwartungen klar kommunizieren.
    </li>

    <li>
      <strong>Monat 2 — Qualität sichern:</strong>
      Erste Erfahrungen auswerten, Feedback einholen, Routinen anpassen.
    </li>

    <li>
      <strong>Monat 3 — Verbindlichkeit herstellen:</strong>
      Erfolgreiche Workflows in den Regelbetrieb überführen, Kennzahlen festlegen.
    </li>
  </ul>

  <h3>4. Umgang mit Widerständen</h3>
  <p>
    Widerstände entstehen durch Unsicherheit über Qualität, Datenschutz oder veränderte Arbeitsweisen.
  </p>
  <p>
    {% if COMPANY_SIZE == "solo" %}
      Klare, überprüfbare Routinen schaffen Vertrauen.
    {% elif COMPANY_SIZE == "team" %}
      Offene Abstimmungen und klare Rollen stabilisieren neue Arbeitsweisen.
    {% else %}
      Verständliche Kommunikation und fachbereichsnahe Verantwortlichkeiten reduzieren Vorbehalte.
    {% endif %}
  </p>
  <p>
    Kontinuierliches Feedback sorgt dafür, dass KI als verlässlicher Bestandteil akzeptiert wird.
  </p>
</section>
