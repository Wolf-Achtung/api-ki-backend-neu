Developer:
<!-- gamechanger.md – v6.0 PLATIN+ (branch-aware, size-aware, context-integrated, business-case-linked)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZIEL:
       - 2–3 realistische Gamechanger für {{HAUPTLEISTUNG}}.
       - Basierend auf: Branche, Größe, strategische Ziele, Vision, Geschäftsmodellentwicklung.
       - Jeder Gamechanger = klarer, konkreter Wertschöpfungshebel + erster Schritt + erwarteter Nutzen.
       - Verknüpfung mit Business Case und Roadmap.

     VARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{HAUPTLEISTUNG}}
       {{STRATEGISCHE_ZIELE}}
       {{GESCHAEFTSMODELL_EVOLUTION}}
       {{VISION_3_JAHRE}}
       COMPANY_SIZE = "solo" | "team" | "kmu"

     SIZE-LOGIK (UNTERNEHMENSGROESSE_LABEL):
       SOLO:
         - Fokus: Automatisierung, persönliche Entlastung, skalierbare Vorlagen.
         - Keine Teams, keine Abteilungen.
       TEAM (2–10):
         - Fokus: arbeitsteilige Workflows, Rollen, einfache Governance.
       KMU (11–100):
         - Fokus: skalierbare Prozesse, klare Verantwortlichkeiten, Pilotbereiche.

     BRANCHEN-LOGIK:
       - Nutzt typische branchenspezifische Workflows, Pain Points, Daten & Tools aus CONTEXT_BLOCK.
       - Keine erfundenen Daten; rein generische Trends & Muster.

     PFLICHTSTRUKTUR (ALLE 3 Gamechanger mit vollständiger Struktur):
       Pro Gamechanger MUSS enthalten sein:
       1. Kernidee (2-3 Sätze)
       2. Betroffene Wertschöpfung (konkret benennen)
       3. Nutzen (quantifizierbar wenn möglich)
       4. Voraussetzungen (size-aware)
       5. Erster Schritt in den nächsten 90 Tagen

     MINDESTLÄNGE: 800 Zeichen (ohne HTML-Tags) – unterschreite diese NIEMALS!

     VERBOTEN:
       - "TODO", "Freitextfeld", generische Formulierungen ohne Substanz.
       - Gamechanger ohne konkreten Bezug zu {{HAUPTLEISTUNG}}.
       - Bei SOLO: keine "Abteilungen", "Teams", "Bereiche".
-->

<section class="section gamechanger">
  <h2>KI als Gamechanger für Ihr Geschäftsmodell</h2>

  <p>
    Für ein Unternehmen in der Branche <strong>{{BRANCHE_LABEL}}</strong> mit der Größe
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> und dem Schwerpunkt
    <strong>{{HAUPTLEISTUNG}}</strong> ergeben sich mehrere KI-Szenarien, die die
    Wertschöpfung in den kommenden Jahren spürbar verändern können. Die folgenden
    Vorschläge knüpfen direkt an Ihre strategischen Ziele
    ({{STRATEGISCHE_ZIELE}}) sowie die geplante Weiterentwicklung des Geschäftsmodells
    ({{GESCHAEFTSMODELL_EVOLUTION}}) und Ihre Vision für die nächsten drei Jahre
    ({{VISION_3_JAHRE}}) an.
  </p>

  <ol class="gamechanger-list">

    <!-- GAMECHANGER 1 -->
    <li>
      <h3>1. KI-gestützte Standardisierung & Automatisierung zentraler Kernprozesse</h3>
      <p><strong>Kernidee:</strong>
        Wiederkehrende Aufgaben in {{HAUPTLEISTUNG}} werden über KI-gestützte Vorlagen,
        Automatisierungen und strukturierte Entscheidungswege so standardisiert, dass
        Qualität und Geschwindigkeit deutlich steigen.
      </p>
      <p><strong>Betroffene Wertschöpfung:</strong>
        Erstellung, Analyse, interne Abstimmungen, Kundendokumentation.
      </p>
      <p><strong>Nutzen:</strong>
        Weniger manuelle Routinearbeit, stabilere Ergebnisse und eine konsistente
        Kundenerfahrung – unabhängig von Tagesform oder Auslastung.
      </p>
      <p><strong>Voraussetzungen:</strong>
        5–10 typische Beispiele, definierte Qualitätskriterien, klare Input-Regeln;
        {% if UNTERNEHMENSGROESSE_LABEL.startswith("1") %}persönliche Routinen{% elif UNTERNEHMENSGROESSE_LABEL.startswith("2") %}Teamrollenzuordnung{% else %}beteiligte Fachbereiche{% endif %}.
      </p>
      <p><strong>Erster Schritt in den nächsten 90 Tagen:</strong>
        Einen priorisierten Teilprozess auswählen und mit KI-Vorlagen + Review-Schritten
        als Mini-Pilot stabilisieren.
      </p>
    </li>

    <!-- GAMECHANGER 2 -->
    <li>
      <h3>2. Aufbau eines KI-gestützten Wissenspools für Entscheidungen & Angebotserstellung</h3>
      <p><strong>Kernidee:</strong>
        Zentrale Informationen, Beispiele, Best Practices und interne Expertise werden
        KI-unterstützt gebündelt, sodass Recherchen, Angebotsprozesse oder Analysen
        deutlich schneller und konsistenter erfolgen.
      </p>
      <p><strong>Betroffene Wertschöpfung:</strong>
        Angebotsentwicklung, Planung, interne Abstimmungen, Wissenstransfer.
      </p>
      <p><strong>Nutzen:</strong>
        Weniger Suchaufwand, deutliche Zeitersparnis, bessere Entscheidungsqualität und
        höherer Wiedererkennungswert für Kund:innen.
      </p>
      <p><strong>Voraussetzungen:</strong>
        Strukturierte Beispiele und interne Inhalte; kurze Regeln für Qualität und
        Aktualisierung; {% if COMPANY_SIZE == "solo" %}persönliche Sortierung{% elif COMPANY_SIZE == "team" %}Teamabstimmung{% else %}bereichsübergreifende Koordination{% endif %}.
      </p>
      <p><strong>Erster Schritt in den nächsten 90 Tagen:</strong>
        10–15 reale Inhalte bündeln, erste KI-gestützte Zusammenfassungen erzeugen und
        diese als Wissensbasis in den Arbeitsalltag integrieren.
      </p>
    </li>

    <!-- GAMECHANGER 3 -->
    <li>
      <h3>3. KI-basierte Qualitätssicherung & konsistente Kundenergebnisse</h3>
      <p><strong>Kernidee:</strong>
        Qualität, Präzision und Konsistenz werden über KI-gestützte Prüfmechanismen
        verbessert, die branchenspezifische Anforderungen berücksichtigen
        (z.&nbsp;B. Tonalität, Struktur, Vollständigkeit, Risiken, sensible Inhalte).
      </p>
      <p><strong>Betroffene Wertschöpfung:</strong>
        Kundenkommunikation, inhaltliche Produktion, interne Reviews, finaler Output.
      </p>
      <p><strong>Nutzen:</strong>
        Weniger Fehler, weniger Korrekturschleifen und eine deutlich höhere
        Ersttrefferquote – besonders relevant bei Zeitdruck oder hoher Auslastung.
      </p>
      <p><strong>Voraussetzungen:</strong>
        5–7 klare Prüfkriterien, einheitliche Vorlagen, definierte Eskalationslogik;
        {% if COMPANY_SIZE == "solo" %}persönliche Routine{% elif COMPANY_SIZE == "team" %}Review-Rollen{% else %}Qualitätssicherung + Fachbereiche{% endif %}.
      </p>
      <p><strong>Erster Schritt in den nächsten 90 Tagen:</strong>
        Eine KI-gestützte Mini-Checkliste einführen und bei jedem Output anwenden,
        bevor Ergebnisse intern oder extern genutzt werden.
      </p>
    </li>

  </ol>

  <h3>Was diese Gamechanger gemeinsam haben</h3>
  <ul>
    <li>Sie bauen auf bestehenden Stärken von {{HAUPTLEISTUNG}} auf und verstärken diese mit KI.</li>
    <li>Sie berücksichtigen die Ressourcen und Entscheidungswege eines {{UNTERNEHMENSGROESSE_LABEL}}-Unternehmens.</li>
    <li>Sie lassen sich mit überschaubarem Risiko pilotieren und bei Erfolg schrittweise skalieren.</li>
  </ul>

  <p class="small muted">
    Die Gamechanger dienen als strategische Leitplanken und unterstützen Ihr Unternehmen
    dabei, von ersten KI-Schritten hin zu nachhaltiger, skalierbarer Wertschöpfung zu kommen.
  </p>
</section>
