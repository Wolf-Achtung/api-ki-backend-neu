Developer:
<!-- wettbewerb_benchmark.md – v5.0 GOLD STANDARD+ (branch-aware, size-aware, score-aware)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>; KEINE Kommentare im Output.

     ZWECK:
       - Vergleich des Unternehmens mit dem Branchendurchschnitt und den Top 10%.
       - Ableitung der Position je Kategorie ausschließlich aus den Scores.
       - Identifikation der zwei größten Gaps & zwei stärksten Stärken.
       - Erstellung einer size-aware Überholungsstrategie (Q2–Q4).
       - Nutzung des CONTEXT_BLOCK (Tools, Workflows, Pain Points) zur Branchenschärfung.

     PFLICHTVARIABLEN:
       {{BRANCHE_LABEL}}
       {{report_date}}
       {{score_gesamt}}
       {{score_befaehigung}}
       {{score_governance}}
       {{score_sicherheit}}
       {{score_nutzen}}
       {{UNTERNEHMENSGROESSE_LABEL}}

     BENCHMARK-ZAHLEN (NICHT ÄNDERN!):
       Gesamt: Ø 65, Top 10% = 82
       Befähigung: Ø 68, Top 10% = 85
       Governance: Ø 58, Top 10% = 78
       Sicherheit: Ø 62, Top 10% = 80
       Wertschöpfung: Ø 70, Top 10% = 88

     SCORE-LOGIK (verbindlich):
       Positionierung (je Kategorie):
         - "> Top 10%" → „stark über Branchenniveau“
         - "zwischen Ø und Top 10%" → „über Branchenniveau“
         - "< Ø" → „unter Branchendurchschnitt“

       Gaps:
         - Wähle die zwei Kategorien mit größtem Abstand zum Ø, nur wenn Score < Ø.
       Stärken:
         - Wähle die zwei Kategorien mit größtem Abstand nach oben (Score > Ø).

     BRANCHEN-AWARE:
       - Nutze CONTEXT_BLOCK: branchentypische Prozesse, Pain Points, Datenarten.
       - Branchenmodifikatoren:
         FINANZEN/HEALTH/VERWALTUNG = Schwerpunkt auf Governance & Sicherheit.
         MARKETING/KREATIV = Schwerpunkt auf Wertschöpfung & Befähigung.
         INDUSTRIE/PRODUKTION = Schwerpunkt Datenqualität & Prozessintegration.
         E-COMMERCE/HANDEL = Schwerpunkt Konsistenz, Datenfeeds, Automatisierung.

     SIZE-AWARE STRATEGIE:
       SOLO:
         - Fokus auf persönliche Routinen, pragmatische Standards, direkte Nutzeneffekte.
       TEAM (2–10):
         - Fokus auf Rollen, Abstimmung, gemeinsame Workflows & Reviews.
       KMU (11–100):
         - Fokus auf Bereichskoordinierung, Governance, skalierbare Prozesse.

     OUTPUT:
       Ein einziger HTML-Block mit <section>…</section>.
-->

<section class="section wettbewerb-benchmark">
  <h2>Wettbewerb &amp; Benchmarking</h2>

  <p>
    <strong>Datenbasis:</strong> Benchmark aus 30 Assessments in
    <strong>{{BRANCHE_LABEL}}</strong>, Stand <strong>{{report_date}}</strong>.
  </p>

  <h3>Score-Vergleich (Unternehmen vs. Branche)</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Kategorie</th>
        <th>Ihr Score</th>
        <th>Ø Branche</th>
        <th>Top&nbsp;10%</th>
        <th>Position</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Gesamt</td>
        <td>{{score_gesamt}}</td>
        <td>65</td>
        <td>82</td>
        <td>
          <!-- automatisch ableitbar -->
          {% if score_gesamt > 82 %}stark über Branchenniveau
          {% elif score_gesamt > 65 %}über Branchenniveau
          {% else %}unter Branchendurchschnitt{% endif %}
        </td>
      </tr>

      <tr>
        <td>Befähigung</td>
        <td>{{score_befaehigung}}</td>
        <td>68</td>
        <td>85</td>
        <td>
          {% if score_befaehigung > 85 %}stark über Branchenniveau
          {% elif score_befaehigung > 68 %}über Branchenniveau
          {% else %}unter Branchendurchschnitt{% endif %}
        </td>
      </tr>

      <tr>
        <td>Governance</td>
        <td>{{score_governance}}</td>
        <td>58</td>
        <td>78</td>
        <td>
          {% if score_governance > 78 %}stark über Branchenniveau
          {% elif score_governance > 58 %}über Branchenniveau
          {% else %}unter Branchendurchschnitt{% endif %}
        </td>
      </tr>

      <tr>
        <td>Sicherheit</td>
        <td>{{score_sicherheit}}</td>
        <td>62</td>
        <td>80</td>
        <td>
          {% if score_sicherheit > 80 %}stark über Branchenniveau
          {% elif score_sicherheit > 62 %}über Branchenniveau
          {% else %}unter Branchendurchschnitt{% endif %}
        </td>
      </tr>

      <tr>
        <td>Wertschöpfung</td>
        <td>{{score_nutzen}}</td>
        <td>70</td>
        <td>88</td>
        <td>
          {% if score_nutzen > 88 %}stark über Branchenniveau
          {% elif score_nutzen > 70 %}über Branchenniveau
          {% else %}unter Branchendurchschnitt{% endif %}
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Ihre größten Gaps</h3>
  <ul>
    {% set gaps = [
      ('Befähigung', score_befaehigung, 68),
      ('Governance', score_governance, 58),
      ('Sicherheit', score_sicherheit, 62),
      ('Wertschöpfung', score_nutzen, 70)
    ] %}
    {% set sorted_gaps = gaps | selectattr(1, '<', 2) | map(attribute=0) %}
    {% for cat, s, avg in gaps|sort(attribute=lambda x: avg - s, reverse=True) if s < avg %}
      <li><strong>{{cat}}:</strong> deutlicher Rückstand gegenüber dem Branchen-Ø ({{s}} vs. {{avg}}).</li>
    {% endfor %}
  </ul>

  <h3>Ihre stärksten Stärken</h3>
  <ul>
    {% for cat, s, avg in gaps|sort(attribute=lambda x: s - avg, reverse=True) if s > avg %}
      <li><strong>{{cat}}:</strong> erkennbarer Vorsprung vor dem Branchendurchschnitt ({{s}} vs. {{avg}}).</li>
    {% endfor %}
  </ul>

  <h3>Überholungs-Strategie (nächste 12 Monate – size-aware)</h3>
  <ol>
    <li>
      <strong>Q2:</strong>
      {% if UNTERNEHMENSGROESSE_LABEL.startswith('1') %}
        Fokus auf persönliche Standardisierung: 2–3 Kernprozesse dokumentieren, einfache KI-Checklisten nutzen.
      {% elif UNTERNEHMENSGROESSE_LABEL.startswith('2') %}
        Rollen klären (KI-Owner, Reviewer), einheitliche Templates und kurze Review-Loops.
      {% else %}
        Bereichsübergreifende Pilotfläche definieren (z. B. Marketing, Produktion, Backoffice); erste Governance-Standards verankern.
      {% endif %}
    </li>

    <li>
      <strong>Q3:</strong>
      {% if UNTERNEHMENSGROESSE_LABEL.startswith('1') %}
        Workflow-Optimierung: KI-gestützte Routinen festigen, Integration der wichtigsten Branchentools.
      {% elif UNTERNEHMENSGROESSE_LABEL.startswith('2') %}
        Gemeinsame Dokumentation + regelmäßige Team-Reviews; Tool-Reduktion bei Doppelstrukturen.
      {% else %}
        Harmonisierung bereichsspezifischer Prozesse, klare Datenschnittstellen, einheitliche Freigaben.
      {% endif %}
    </li>

    <li>
      <strong>Q4:</strong>
      {% if UNTERNEHMENSGROESSE_LABEL.startswith('1') %}
        Routine-Festigung: wiederkehrende Nutzung + Jahresplanung.
      {% elif UNTERNEHMENSGROESSE_LABEL.startswith('2') %}
        Skalierung im Team: automatisierte Qualitätskontrolle + einheitliche KI-Kommunikation.
      {% else %}
        Skalierungsprogramm: Governance erweitern, Auditroutinen, bereichsübergreifende Standards.
      {% endif %}
    </li>
  </ol>

  <p>
    <strong>Strategischer Zielkorridor:</strong>
    {% if score_gesamt >= 80 %}
      Richtung Top 5 % der Branche.
    {% elif score_gesamt >= 60 %}
      Richtung Top 10 % der Branche.
    {% else %}
      Richtung Top 25 % – Schwerpunkt auf Stabilisierung und strukturierter Weiterentwicklung.
    {% endif %}
  </p>
</section>
