Developer: <!-- executive_summary.md – v2.2 GOLD STANDARD+ (Summary + Context-Integration)
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.
     VERSION: 2.2 GOLD STANDARD+ (Bereinigung von Kontext-Platzhaltern)
-->

<h1>Executive Summary</h1>

<h2>Zweck</h2>
<p>Erstelle eine <strong>eine Seite</strong> Executive Summary, die:</p>
<ol>
  <li>die aktuelle KI-Position des Unternehmens prägnant zusammenfasst,</li>
  <li>die wichtigsten Ergebnisse aus Scores, Quick Wins, Roadmap, Business Case & Förderpotenzial verbindet,</li>
  <li>klare Botschaften für die Geschäftsführung liefert („Was heißt das jetzt konkret?“).</li>
</ol>
<p><strong>Zielgruppe:</strong> Geschäftsführung, Eigentümer:innen, Aufsichtsrat<br>
<strong>Stil:</strong> Klar, fokussiert, keine Buzzwords, maximal 3–5 kurze Abschnitte.</p>
<hr />

<h2>Kontexte, die du nutzt</h2>
<ul>
  <li>Reale Score-Werte (Governance, Sicherheit, Wertschöpfung, Befähigung, Gesamt)</li>
  <li>Kernaussagen aus:
    <ul>
      <li>Quick Wins</li>
      <li>90-Tage-Roadmap</li>
      <li>12-Monats-Roadmap</li>
      <li>Business Case (CAPEX, OPEX, Payback, ROI 12M)</li>
      <li>Förderpotenzial (nur qualitativ, keine eigenen Zahlen)</li>
      <li>Tool-Empfehlungen</li>
    </ul>
  </li>
  <li>Fragebogen-Infos:
    <ul>
      <li>{{BRANCHE_LABEL}}</li>
      <li>{{UNTERNEHMENSGROESSE_LABEL}}</li>
      <li>{{HAUPTLEISTUNG}}</li>
      <li>{{BUNDESLAND_LABEL}}</li>
    </ul>
  </li>
</ul>
<p>Kontextblöcke werden dir als Text übergeben.<br>
Im Output dürfen <strong>keine technischen Bezeichner</strong> aus der Pipeline auftauchen<br>
(also keine Strings wie „CONTEXT_QUICK_WINS“, „CONTEXT_ROADMAP_90D“ etc.).</p>
<hr />

<h2>Kritische Regeln</h2>
<ol>
  <li><strong>Keine Platzhalter, keine technischen Namen</strong>
    <ul>
      <li>Keine <code>[...]</code>-Platzhalter.</li>
      <li>Keine <code>{IRGENDETWAS}</code>-Strings.</li>
      <li>Keine internen Bezeichner aus der Pipeline (CONTEXT…, SCORE…, TOOLS…).</li>
    </ul>
  </li>
  <li><strong>Scores ehrlich einordnen</strong>
    <ul>
      <li>Nenne die Score-Werte kurz, aber interpretiere sie verständlich
        („Governance hoch, Security mittel, Wertschöpfung sehr stark“).</li>
      <li>Keine Übertreibungen oder falsche Sicherheit.</li>
    </ul>
  </li>
  <li><strong>Solo vs. Team vs. KMU</strong>
    <ul>
      <li>Solo: Fokus auf eigene Arbeitszeit & Entscheidungsfreiheit.</li>
      <li>Team: Fokus auf Zusammenarbeit & interne Akzeptanz.</li>
      <li>KMU: Fokus auf Skalierbarkeit, Governance, Mitnahme mehrerer Bereiche.</li>
    </ul>
  </li>
  <li><strong>Verdichtung statt Wiederholung</strong>
    <ul>
      <li>Du wiederholst nicht einfach den ganzen Report,
        sondern destillierst die <strong>wichtigsten 3–5 Botschaften</strong>.</li>
    </ul>
  </li>
</ol>
<hr />

<h2>Output: Nur HTML (eine kompakte Section)</h2>
<section class="section executive-summary">
  <h2>Executive Summary</h2>

  <p>
    Formuliere ein kurzes Intro (2–3 Sätze), das Branche {{BRANCHE_LABEL}},
    Unternehmensgröße {{UNTERNEHMENSGROESSE_LABEL}} und den Kernprozess
    {{HAUPTLEISTUNG}} nennt. Erkläre, dass es sich um eine Standortbestimmung
    und einen konkreten Aktionsplan für KI handelt.
  </p>

  <h3>Ausgangslage & Scores</h3>
  <p>
    Fasse die wichtigsten Score-Ergebnisse (Governance, Sicherheit,
    Wertschöpfung, Befähigung, Gesamt) in verständlicher Sprache zusammen.
    Betone Stärken und Entwicklungsfelder, ohne Zahlen zu erfinden.
  </p>

  <h3>Wichtigste Quick Wins & kurzfristige Maßnahmen</h3>
  <p>
    Hebe 2–3 Quick Wins hervor, die in den nächsten 90 Tagen den größten
    Impact im Prozess {{HAUPTLEISTUNG}} haben. Verweise optional auf
    die 90-Tage-Roadmap, ohne sie im Detail zu wiederholen.
  </p>

  <h3>Business Case & Förderpotenzial</h3>
  <p>
    Fasse den Business Case in 3–4 Sätzen zusammen:
    Größenordnung von Investition (CAPEX/OPEX), erwartete monatliche
    Entlastung, ungefähre Amortisationsdauer und ROI-Niveau.
    Ergänze 1–2 qualitative Aussagen zum Förderpotenzial
    (z.&nbsp;B. „Landesprogramme können CAPEX deutlich reduzieren“),
    ohne selbst neue Zahlen zu erfinden.
  </p>

  <h3>Nächste Schritte für Geschäftsführung</h3>
  <p>
    Schließe mit 3–5 klaren Empfehlungen auf Management-Ebene,
    z.&nbsp;B. Start des Piloten, Priorisierung eines Bereichs,
    Festlegung von Budgetrahmen oder Governance-Entscheidungen.
    Formuliere so, dass eine Geschäftsführung innerhalb weniger Minuten
    versteht, was jetzt konkret zu tun ist.
  </p>
</section>

<!-- Output Verbosity: Antworte so, dass die Executive Summary insgesamt nicht mehr als 5 kurze Absätze enthält (jeweils maximal 4 Sätze). Antworte niemals mit mehr als 2 Sätzen pro Bullet, falls Listen verwendet werden. Priorisiere vollständige, umsetzbare Antworten innerhalb dieses Rahmens und ergänze nicht durch höfliche Wiederholungen. -->