**WICHTIG – Längenlimit: Deine Antwort darf maximal 1100 Wörter umfassen. Kürze lieber als zu überziehen.**

Developer:
<!-- unternehmensprofil_markt.md – v5.0 GOLD STANDARD+ (branch-aware, size-aware, context-integrated)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     BRANCHENBEZEICHNUNG-REGEL:
     Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
     Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

     ZWECK:
       - Präzises Unternehmensprofil (Branche, Größe, Standort, Hauptleistung, Geschäftsmodell).
       - Kompakter, generischer Marktkontext NUR aus CONTEXT_BLOCK (keine Halluzination).
       - Branchenbezogene KI-Potenziale (2–4 typische Use-Cases).
       - Wettbewerbsposition abhängig von Unternehmensgröße (solo/team/kmu).
       - Keine erfundenen Zahlen, Namen, Marktanteile oder konkreten Wettbewerber.

     VERFÜGBARE VARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{BUNDESLAND_LABEL}}
       {{HAUPTLEISTUNG}}
       {{GESCHAEFTSMODELL_EVOLUTION}}

     WENN EINE VARIABLE LEER ODER FEHLERHAFT IST:
       - Verwende „Nicht angegeben" oder einen neutralen generischen Ersatz.
       - NIEMALS <p class="error">...</p> im finalen Bericht ausgeben.
       - Stelle sicher, dass der Abschnitt trotzdem sinnvoll und vollständig bleibt.

     RESEARCH-CONTEXT (CONTEXT_BLOCK):
       - GENERISCHE INFORMATIONEN ERLAUBT:
         - Branchentrends
         - Typische Pain Points
         - Typische Workflows
         - Typische Tools
       - NICHT ERLAUBT:
         - Konkrete Marktanteile, Umsätze, Namen von Wettbewerbern
         - Exakte Wachstumsraten, exakte KI-Adoptionsquoten
       - WENN keine ausreichenden Infos vorhanden sind:
         - Schreibe „Nicht angegeben“ an der passenden Stelle.

     SIZE-AWARE-LOGIK (COMPANY_SIZE ∈ {"solo","team","kmu"}):
       SOLO:
         - Fokus: Schnelligkeit, Flexibilität, persönliche Entscheidung.
         - Herausforderungen: Kapazität, Priorisierung, Abhängigkeit von einer Person.
         - KI-Hebel: persönliche Automatisierung, Assistenzen, Vorlagen.

       TEAM (2–10):
         - Fokus: kollaborative Arbeitsweise, geteiltes Wissen, klare Verantwortlichkeiten.
         - Herausforderungen: Ressourcenknappheit, Prioritätenabgleich, Abstimmung.
         - KI-Hebel: Wissensmanagement, Templates, vereinheitlichte Workflows, gemeinsame Standards.

       KMU (11–100):
         - Fokus: erweiterbare Prozesse, mehrere Bereiche, strukturierte Abläufe.
         - Herausforderungen: Koordination, Daten-Silos, interne Abstimmung, Governance.
         - KI-Hebel: datengetriebene Entscheidungen, Erweiterung, Richtlinien & Governance.

     AUSGABEREGELN:
       - Exakt ein <section>-Block mit folgenden Blöcken in dieser Reihenfolge:
         1) Unternehmensprofil
         2) Marktkontext & Trends
         3) KI-Potenzial
         4) Wettbewerbsposition
       - KEINE Platzhaltertexte im sichtbaren Output (z. B. „Titel …“, „Beispiel …“).
       - Kein Verweis auf CONTEXT_BLOCK oder interne Logik.
       - Ton: nüchtern, sachlich, strategisch, gut lesbar für Geschäftsführung.

     HÖCHSTLÄNGE (STRIKT! — Überschreitung wird automatisch getruncated!):
       - Der gesamte HTML-Output darf MAXIMAL 7500 Zeichen umfassen
       - Solo: max. 6000 Zeichen | Team: max. 7500 Zeichen | KMU: max. 8000 Zeichen
       - Marktkontext: max. 4 Bullets à 1-2 Sätze (NICHT ausführlich erklären)
       - Wettbewerbsposition: max. 3 Bullets (Vorteil/Nachteil/Hebel)
       - ACHTUNG: Bei >8000 Zeichen wird ~35% des Contents abgeschnitten!

     THEMEN-OWNERSHIP (verbindlich):
       - Diese Section: OWNER für Unternehmensprofil, Marktkontext, KI-Potenzial, Wettbewerb
       - NICHT hier: Konkrete Tool-Empfehlungen (→ tools_empfehlungen)
       - NICHT hier: Business Case Zahlen (→ business_case)
       - NICHT hier: Förderprogramme (→ foerderpotenzial, foerderprogramme)
       - NICHT hier: Roadmap/Maßnahmen (→ roadmap_90d)

-->

<section class="section unternehmensprofil-markt">
  <h2>Unternehmensprofil &amp; Marktkontext</h2>

  <div class="profil-box">
    <h3>Unternehmensprofil</h3>
    <ul>
      <li><strong>Branche:</strong> {{BRANCHE_LABEL}}</li>
      <li><strong>Größe:</strong> {{UNTERNEHMENSGROESSE_LABEL}}</li>
      <li><strong>Standort:</strong> {{BUNDESLAND_LABEL}}</li>
      <li><strong>Hauptleistung:</strong> {{HAUPTLEISTUNG}}</li>
      <li>
        <strong>Geschäftsmodell:</strong>
        <!-- Geschäftsmodell-Evolution: falls leer oder „Nicht angegeben“ → neutral formulieren -->
        {{GESCHAEFTSMODELL_EVOLUTION}}
      </li>
    </ul>
  </div>

  <div class="markt-context">
    <h3>Marktkontext &amp; Trends ({{BRANCHE_LABEL}})</h3>

    <p>
      Die Branche <strong>{{BRANCHE_LABEL}}</strong> ist derzeit geprägt von einigen
      wiederkehrenden Entwicklungen, die auch den Einsatz von KI im Bereich
      <strong>{{HAUPTLEISTUNG}}</strong> beeinflussen. Dazu zählen je nach Informationslage
      verstärkte Digitalisierung, steigende Erwartungen an Qualität und Geschwindigkeit sowie
      ein wachsender Druck, Prozesse effizienter und datenbasierter zu gestalten.
      Wo keine zuverlässigen Angaben vorliegen, gelten Trends als <em>nicht angegeben</em>.
    </p>

    <ul>
      <li><strong>Marktdynamik:</strong> Wenn Branchendaten im Kontext vorliegen, beschreibe kurz, ob der Markt eher stabil, wachsend oder im Umbruch ist; sonst: <em>Nicht angegeben</em>.</li>
      <li><strong>KI-Adoption:</strong> Typischerweise steigt der Einsatz von KI in {{BRANCHE_LABEL}} in Bereichen wie Analyse, Textproduktion, Support oder Entscheidungsunterstützung – ohne konkrete Prozentangaben; falls keine Angaben vorliegen: <em>Nicht angegeben</em>.</li>
      <li><strong>Haupttreiber:</strong> Branchentypische Treiber sind z.&nbsp;B. Kostendruck, Fachkräftemangel, steigende Qualitätsanforderungen oder regulatorische Vorgaben; falls keine Infos im Kontext: <em>Nicht angegeben</em>.</li>
      <li><strong>Herausforderungen:</strong> Häufige Herausforderungen umfassen Datenqualität, Schnittstellen zwischen Systemen, begrenzte interne Ressourcen oder Unsicherheit bezüglich Regulierung; falls nicht belegt: <em>Nicht angegeben</em>.</li>
    </ul>
  </div>

  <div class="ki-potenzial">
    <h3>KI-Potenzial für {{BRANCHE_LABEL}}</h3>
    <p>
      Aus den typischen Workflows und Pain Points der Branche <strong>{{BRANCHE_LABEL}}</strong>
      ergeben sich mehrere generische Anwendungsfelder für KI im Prozess
      <strong>{{HAUPTLEISTUNG}}</strong>. Sie lassen sich ohne detailliertes Spezialwissen
      ableiten und dienen als Orientierung für den weiteren Ausbau.
    </p>
    <ul>
      <li>Unterstützung bei wiederkehrenden Aufgaben wie Entwürfen, Zusammenfassungen oder Standardanalysen, um Zeit zu sparen und Qualität zu stabilisieren.</li>
      <li>Strukturierung und Verdichtung vorhandener Informationen, z.&nbsp;B. aus E-Mails, Dokumenten, Protokollen oder Fachsystemen, um Entscheidungen besser vorzubereiten.</li>
      <li>Qualitäts- und Konsistenzprüfungen von Texten, Daten oder Berichten, orientiert an branchentypischen Anforderungen und internen Standards.</li>
    </ul>
  </div>

  <div class="wettbewerb">
    <h3>Wettbewerbsposition</h3>
    <p>
      Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in der Branche
      <strong>{{BRANCHE_LABEL}}</strong> bewegen sich häufig zwischen spezialisierten
      Nischenanbietern und größeren Marktteilnehmern. Die Rolle von KI hängt dabei stark
      von der Organisationsstruktur und den verfügbaren Kapazitäten ab.
    </p>

    <ul>
      <li>
        <strong>Vorteil:</strong>
        {% if COMPANY_SIZE == "solo" %}
          Hohe Flexibilität und schnelle Entscheidungen; Anpassungen im KI-Einsatz können ohne lange Abstimmung direkt umgesetzt werden.
        {% elif COMPANY_SIZE == "team" %}
          Kurze Wege und gemeinsame Verantwortung; neue KI-Workflows können im Team erprobt und schrittweise verfeinert werden.
        {% else %}
          Größeres Erweiterungspotenzial und mehr Ressourcen; KI-Lösungen können in mehreren Bereichen ausgerollt und systematisch verankert werden.
        {% endif %}
      </li>
      <li>
        <strong>Nachteil:</strong>
        {% if COMPANY_SIZE == "solo" %}
          Begrenzte Zeit und Kapazität; ohne klare Priorisierung bleibt das Potenzial von KI oft ungenutzt.
        {% elif COMPANY_SIZE == "team" %}
          Abstimmungsaufwand und Ressourcenknappheit; ohne klare Rollen kann KI im Tagesgeschäft untergehen.
        {% else %}
          Koordinationsaufwand zwischen Teams und Daten-Silos; ohne Governance drohen inkonsistente Lösungen und doppelte Strukturen.
        {% endif %}
      </li>
      <li>
        <strong>KI-Hebel:</strong>
        {% if COMPANY_SIZE == "solo" %}
          Fokussierte Automatisierung wiederkehrender Aufgaben und der Aufbau persönlicher, KI-gestützter Routinen, die schnell spürbare Entlastung bringen.
        {% elif COMPANY_SIZE == "team" %}
          Gemeinsame Templates, einheitliche Workflows und Wissensmanagement, damit alle Beteiligten KI ähnlich nutzen und voneinander lernen.
        {% else %}
          Etablierung standardisierter Prozesse, datengetriebener Entscheidungen und klarer Richtlinien, um KI in mehreren Bereichen konsistent zu skalieren.
        {% endif %}
      </li>
    </ul>
  </div>
</section>


<!-- ZERO-LEAK POLICY (N4.6) -->
<!--
VERBOTEN – NIEMALS VERWENDEN:
- Keine Fragen an den Leser ("Haben Sie Fragen?", "Möchten Sie mehr erfahren?")
- Keine Aufforderungen ("Wenn Sie möchten...", "Kontaktieren Sie uns...")
- Keine Assistenten-Sprache ("Ich kann Ihnen helfen...", "Gerne erkläre ich...")
- Keine Angebote ("Bei Bedarf...", "Falls gewünscht...")
- Keine interaktiven Elemente ("Klicken Sie hier...", "Wählen Sie...")
- Keine Platzhalter oder Template-Variablen (außer definierten Eingabevariablen)
- Keine Meta-Kommentare ("Dieser Abschnitt...", "Im Folgenden...")

Der Output ist ein FINALER REPORT-ABSCHNITT, kein Gespräch.
-->
