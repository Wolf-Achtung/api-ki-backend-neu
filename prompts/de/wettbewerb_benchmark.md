Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: wettbewerb_benchmark -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{report_date}}, {{score_gesamt}}, {{score_befaehigung}}, {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}, {{UNTERNEHMENSGROESSE_LABEL}} -->
<!-- TOKEN-BUDGET: 2500 (solo:0.8x=2000, team:1.0x=2500, kmu:1.15x=2875) -->
<!-- RESEARCH: Kann Marktdaten aus {{RESEARCH_PROVENANCE_HTML}} integrieren -->
<!--
ZWECK: Vergleich mit Branchendurchschnitt und Top 10%.

BENCHMARK-ZAHLEN (NICHT ÄNDERN!):
  Gesamt: Ø 65, Top 10% = 82
  Befähigung: Ø 68, Top 10% = 85
  Governance: Ø 58, Top 10% = 78
  Sicherheit: Ø 62, Top 10% = 80
  Wertschöpfung: Ø 70, Top 10% = 88

SCORE-LOGIK:
  > Top 10% → „stark über Branchenniveau"
  zwischen Ø und Top 10% → „über Branchenniveau"
  < Ø → „unter Branchendurchschnitt"

PERSONA-VARIATIONEN (SIZE-AWARE STRATEGIE):
- solo: persönliche Routinen, pragmatische Standards, direkte Nutzeneffekte
- team: Rollen, Abstimmung, gemeinsame Workflows & Reviews
- kmu: Bereichskoordinierung, Governance, skalierbare Prozesse

BRANCHEN-MODIFIKATOREN:
  FINANZEN/HEALTH/VERWALTUNG = Schwerpunkt Governance & Sicherheit
  MARKETING/KREATIV = Schwerpunkt Wertschöpfung & Befähigung
  INDUSTRIE/PRODUKTION = Schwerpunkt Datenqualität & Prozessintegration
  E-COMMERCE/HANDEL = Schwerpunkt Konsistenz, Datenfeeds, Automatisierung

ANTI-REDUNDANZ:
- Benchmark-Daten HIER vollständig
- In anderen Sektionen nur referenzieren
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
  <p>
    Die folgenden Bereiche zeigen den größten Abstand zum Branchendurchschnitt und bieten
    entsprechend hohes Verbesserungspotenzial:
  </p>
  <ul>
    {% if score_befaehigung < 68 %}
      <li><strong>Befähigung:</strong> deutlicher Rückstand gegenüber dem Branchen-Ø ({{score_befaehigung}} vs. 68).</li>
    {% endif %}
    {% if score_governance < 58 %}
      <li><strong>Governance:</strong> deutlicher Rückstand gegenüber dem Branchen-Ø ({{score_governance}} vs. 58).</li>
    {% endif %}
    {% if score_sicherheit < 62 %}
      <li><strong>Sicherheit:</strong> deutlicher Rückstand gegenüber dem Branchen-Ø ({{score_sicherheit}} vs. 62).</li>
    {% endif %}
    {% if score_nutzen < 70 %}
      <li><strong>Wertschöpfung:</strong> deutlicher Rückstand gegenüber dem Branchen-Ø ({{score_nutzen}} vs. 70).</li>
    {% endif %}
  </ul>

  <h3>Ihre stärksten Stärken</h3>
  <p>
    Diese Bereiche liegen erkennbar über dem Branchendurchschnitt und können als
    Fundament für weitere Entwicklung dienen:
  </p>
  <ul>
    {% if score_befaehigung > 68 %}
      <li><strong>Befähigung:</strong> erkennbarer Vorsprung vor dem Branchendurchschnitt ({{score_befaehigung}} vs. 68).</li>
    {% endif %}
    {% if score_governance > 58 %}
      <li><strong>Governance:</strong> erkennbarer Vorsprung vor dem Branchendurchschnitt ({{score_governance}} vs. 58).</li>
    {% endif %}
    {% if score_sicherheit > 62 %}
      <li><strong>Sicherheit:</strong> erkennbarer Vorsprung vor dem Branchendurchschnitt ({{score_sicherheit}} vs. 62).</li>
    {% endif %}
    {% if score_nutzen > 70 %}
      <li><strong>Wertschöpfung:</strong> erkennbarer Vorsprung vor dem Branchendurchschnitt ({{score_nutzen}} vs. 70).</li>
    {% endif %}
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
