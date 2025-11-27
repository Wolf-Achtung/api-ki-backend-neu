Developer:
<!-- wettbewerb_benchmark.md – v4.0 GOLD STANDARD+ (Benchmarking, size-aware, validator-safe)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZWECK:
       - Vergleich des Unternehmens mit dem Branchendurchschnitt und den Top 10%.
       - Ableitung der Position je Kategorie, 2+ Gaps, 2+ Stärken.
       - Erstellung einer size-aware Überholungsstrategie (Q2/Q3/Q4).

     PFLICHTVARIABLEN:
       {{BRANCHE_LABEL}}
       {{report_date}}
       {{score_gesamt}}
       {{score_befaehigung}}
       {{score_governance}}
       {{score_sicherheit}}
       {{score_nutzen}}

     BENCHMARK-ZAHLEN (NICHT ÄNDERN!):
       Gesamt: Ø 65, Top 10% = 82
       Befähigung: Ø 68, Top 10% = 85
       Governance: Ø 58, Top 10% = 78
       Sicherheit: Ø 62, Top 10% = 80
       Wertschöpfung: Ø 70, Top 10% = 88

     SIZE-AWARE STRATEGIELOGIK:
       COMPANY_SIZE ∈ {"solo","team","kmu"}

       SOLO:
         - Fokus auf persönliche Routinen, einfache Standards, direkter ROI.
         - Gaps: Kapazität, Priorisierung, Dokumentation.
         - Stärken: Flexibilität, schnelle Iteration.
         - Maßnahmen Q2–Q4: kleine, realistische Schritte; keine „Bereiche“, keine „Teams“.

       TEAM (2–10):
         - Fokus auf kollaborative Abstimmung, vereinheitlichte Workflows, Rollen.
         - Gaps: inkonsistente Prozesse, fehlende Verantwortlichkeiten.
         - Stärken: geteiltes Wissen, Team-Leverage.
         - Maßnahmen: klare Rollen (Teamlead, KI-Owner), kurze Review-Loops.

       KMU (11–100):
         - Fokus auf skalierbare Prozesse, Bereichskoordinierung, Governance.
         - Gaps: Silos, Datenqualität, fehlende Standards.
         - Stärken: Ressourcen, Skalierungspotenzial, Spezialisierung.
         - Maßnahmen: fachbereichsspezifische Pilotflächen, strukturierte Prozessharmonisierung.

     REGELN:
       - KEINE erfundenen Wettbewerber, KEINE erfundenen Zahlen.
       - Positionierungen & Gaps werden ausschließlich aus Scores abgeleitet.
       - <section>…</section> als einziger sichtbarer HTML-Block.
       - Keine Platzhaltertexte im Output (keine „Gap 1“, keine Eckklammern).
-->

<section class="section wettbewerb-benchmark">
  <h2>Wettbewerb &amp; Benchmarking</h2>

  <p><strong>Datenbasis:</strong> Benchmark aus 30 Assessments in <strong>{{BRANCHE_LABEL}}</strong>, Stand <strong>{{report_date}}</strong>.</p>

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
        <td><!-- Position Gesamt wird aus Score abgeleitet --></td>
      </tr>
      <tr>
        <td>Befähigung</td>
        <td>{{score_befaehigung}}</td>
        <td>68</td>
        <td>85</td>
        <td><!-- Position Befähigung --></td>
      </tr>
      <tr>
        <td>Governance</td>
        <td>{{score_governance}}</td>
        <td>58</td>
        <td>78</td>
        <td><!-- Position Governance --></td>
      </tr>
      <tr>
        <td>Sicherheit</td>
        <td>{{score_sicherheit}}</td>
        <td>62</td>
        <td>80</td>
        <td><!-- Position Sicherheit --></td>
      </tr>
      <tr>
        <td>Wertschöpfung</td>
        <td>{{score_nutzen}}</td>
        <td>70</td>
        <td>88</td>
        <td><!-- Position Wertschöpfung --></td>
      </tr>
    </tbody>
  </table>

  <h3>Best Practices der Top&nbsp;10%</h3>
  <ul>
    <li><strong>Technologie:</strong> Automatisiertes Batch-Processing statt Einzelfallbearbeitung.</li>
    <li><strong>Governance:</strong> Klare Richtlinien, definierte Freigaben, regelmäßige Audits.</li>
    <li><strong>Qualität:</strong> Human-in-the-Loop mit faktenbasierten Prüfmechanismen.</li>
    <li><strong>Wertschöpfung:</strong> Wiederverwendbare Templates und standardisierte Workflows.</li>
  </ul>

  <h3>Ihre Gaps (Aufholbedarf)</h3>
  <ul>
    <li><!-- Gap 1: Score < Branchen-Ø → z. B. Governance/Sicherheit --></li>
    <li><!-- Gap 2: weiteres relevantes Gap → z. B. Wertschöpfung/Befähigung --></li>
  </ul>

  <h3>Ihre Stärken (Vorsprung nutzen)</h3>
  <ul>
    <li><!-- Stärke 1: Score > Branchen-Ø → z. B. Befähigung/Wertschöpfung --></li>
    <li><!-- Stärke 2: zusätzliche Stärke → z. B. Sicherheit/Qualität --></li>
  </ul>

  <h3>Überholungs-Strategie (nächste 12 Monate – size-aware)</h3>
  <ol>
    <li><strong>Q2:</strong> <!-- Solo: persönliche Standardisierung; Team: Rollen & Review-Loops; KMU: Pilotfläche definieren --></li>
    <li><strong>Q3:</strong> <!-- Solo: Workflow-Optimierung; Team: Team-Dokumentation; KMU: Bereichsübergreifende Harmonisierung --></li>
    <li><strong>Q4:</strong> <!-- Solo: Routine-Festigung; Team: Skalierung im Team; KMU: Governance + Skalierungsprogramm --></li>
  </ol>

  <p><strong>Strategischer Zielkorridor:</strong>
    <!-- Zielbereich abhängig vom Score:
         ≥ 80 → Top 5%
         ≥ 60 → Richtung Top 10%
         < 60 → Richtung Top 25%
    -->
  </p>
</section>
