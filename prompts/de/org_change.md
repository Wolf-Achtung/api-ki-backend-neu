Developer:
<!-- org_change.md – v5.0 GOLD STANDARD+ (branch-aware, size-aware, strategic, context-integrated)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
       - Präziser, motivierender und gleichzeitig realistischer Abschnitt „Veränderungsfähigkeit & Lernen“.
       - Nutzt ACTIV den CONTEXT_BLOCK: typische Workflows, Pain Points, Datenstellen der Branche.
       - Size-aware Anpassung für solo/team/kmu – mit klaren Rollen & Routinen.
       - 4 Blöcke: Einleitung → Ausgangslage → Veränderungsfelder → 90-Tage-Fahrplan → Umgang mit Widerständen.
       - Keine generischen Aussagen; jeder Absatz muss klaren geschäftlichen Wert haben.

     VARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}
       {{KI_ZIELE_LABELS}}
       {{KI_HEMMNISSE_LABELS}}
       {{ki_kompetenz}}
       {{score_governance}}, {{score_sicherheit}},
       {{score_nutzen}}, {{score_befaehigung}}
       COMPANY_SIZE = "solo" | "team" | "kmu"

     VERBOTEN:
       - Platzhalterwörter („Platzhalter“, „Freitextfeld“, „TODO“, …)
       - Konzernsprache (Division, Unit) bei KMU
       - Teams/Abteilungen in SOLO
       - generische Aussagen ohne klaren Nutzen

-->

<section class="section org-change">
  <h2>Veränderungsfähigkeit &amp; Lernen</h2>

  <p>
    Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong>, die im Schwerpunkt
    <strong>{{HAUPTLEISTUNG}}</strong> arbeiten, müssen bei der Einführung von KI sowohl
    neue Arbeitsweisen etablieren als auch bestehende Routinen anpassen. Die aktuelle
    Selbsteinschätzung – etwa die KI-Kompetenz (<strong>{{ki_kompetenz}}</strong>) und die Ziele
    <strong>{{KI_ZIELE_LABELS}}</strong> – zeigt, dass Potenzial und Motivation klar vorhanden sind.
    Gleichzeitig machen typische Hemmnisse wie <strong>{{KI_HEMMNISSE_LABELS}}</strong> deutlich,
    dass Strukturen, Prioritäten und Verantwortlichkeiten weiter geschärft werden müssen.
    Besonders in einem Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong>
    entscheidet ein bedachter Umgang mit Wandel darüber, wie schnell KI zuverlässig Wirkung zeigt.
  </p>

  <h3>1. Wo Sie heute stehen</h3>
  <p>
    Die Analyse der Scores zeigt ein differenziertes Bild:
    Governance (<strong>{{score_governance}}</strong>), Sicherheit
    (<strong>{{score_sicherheit}}</strong>), Nutzen (<strong>{{score_nutzen}}</strong>)
    und Befähigung (<strong>{{score_befaehigung}}</strong>) sind unterschiedlich ausgeprägt.
    Für den Einsatz von KI in <strong>{{HAUPTLEISTUNG}}</strong> bedeutet das:
    Einige grundlegende Routinen funktionieren bereits, jedoch braucht es klarere
    Entscheidungswege, einheitliche Qualitätsstandards und eine engere Verzahnung
    zwischen menschlicher Expertise und KI-gestützten Workflows.
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
      umzuwandeln. Dies gilt besonders in <strong>{{BRANCHE_LABEL}}</strong>,
      wo typische Pain Points eng mit Datenqualität, Zeitdruck oder komplexen
      Entscheidungswegen zusammenhängen.
    </li>
  </ul>

  <h3>3. Fahrplan für die nächsten 90 Tage</h3>
  <p>
    Der Wandel gelingt am besten durch klar priorisierte Schritte. Die folgende
    90-Tage-Struktur passt sich automatisch den Möglichkeiten eines Unternehmens der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> an.
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
