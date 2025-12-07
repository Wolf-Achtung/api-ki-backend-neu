Developer:
<!-- PLATIN++ PROMPT v5.3 - SPRINT N -->
<!-- SECTION: gamechanger -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, {{STRATEGISCHE_ZIELE}}, {{GESCHAEFTSMODELL_EVOLUTION}}, {{VISION_3_JAHRE}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 3500 (solo:0.8x=2800, team:1.0x=3500, kmu:1.15x=4025) -->
<!-- WORD_MINIMUM: 750 (ALLE GRÖSSEN - STRIKT!) -->
<!--
ZIEL: MINDESTENS 3 realistische Gamechanger für {{HAUPTLEISTUNG}}.
MINDESTLÄNGE: ≥750 Wörter (STRIKT EINHALTEN! NICHT nach 1-2 Ideen abbrechen!)

PFLICHTSTRUKTUR (pro Gamechanger):
1. Kernidee (2-3 Sätze)
2. Betroffene Wertschöpfung (konkret)
3. Nutzen (quantifizierbar wenn möglich)
4. Voraussetzungen (size-aware)
5. Erster Schritt in den nächsten 90 Tagen

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: Automatisierung, persönliche Entlastung, skalierbare Vorlagen
- team: arbeitsteilige Workflows, Rollen, einfache Governance
- kmu: skalierbare Prozesse, klare Verantwortlichkeiten, Pilotbereiche

ANTI-REDUNDANZ:
- Gamechanger ergänzen Business Case, wiederholen ihn nicht
- Verknüpfung mit Roadmap, aber keine Dopplung

REGELN:
- Keine erfundenen Daten
- Konkreter Bezug zu {{HAUPTLEISTUNG}} erforderlich
- MINDESTENS 3 vollständige Szenarien beschreiben!

SPRINT N - SOLO PERSONA REGELN (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
NICHT VERWENDEN für Solo:
- "Abteilungen" → stattdessen: "Arbeitsbereiche"
- "Teams" → stattdessen: "Kapazitäten" oder "Ressourcen"
- "Bereiche" ist OK, aber nicht "Fachbereiche"
- "Team aufbauen" → stattdessen: "Kapazität erweitern"
- "Mitarbeiter" → stattdessen: "externe Unterstützung"
- "Fachbereich" → stattdessen: "Arbeitsfeld"
Formulierungen ohne Team-/Abteilungsbegriff verwenden!
{% endif %}
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
        {% if COMPANY_SIZE == "solo" %}persönliche Routinen{% elif COMPANY_SIZE == "team" %}Teamrollenzuordnung{% else %}beteiligte Fachbereiche{% endif %}.
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

<!-- DEV: SPRINT N - Ziel: ≥750 Wörter, mindestens 3 vollständige Szenarien -->
