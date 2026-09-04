**WICHTIG – Längenlimit: Deine Antwort darf maximal 700 Wörter umfassen. Kürze lieber als zu überziehen.**

Developer:
<!-- PLATIN++ PROMPT v5.3 - SPRINT N -->
<!-- SECTION: wettbewerb_benchmark -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{report_date}}, {{score_gesamt}}, {{score_befaehigung}}, {{score_governance}}, {{score_sicherheit}}, {{score_nutzen}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{COMPANY_SIZE}} -->
<!-- TOKEN-BUDGET: 2500 (solo:0.8x=2000, team:1.0x=2500, kmu:1.15x=2875) -->
<!-- RESEARCH: Kann Marktdaten aus {{RESEARCH_PROVENANCE_HTML}} integrieren -->

UMGANG MIT LÜCKENHAFTEN EINGABEN: Wenn ein Input fehlt oder unkonkret ist: - nichts erfinden, - die Aussage auf den belastbaren Kern reduzieren, - und nur den Teil formulieren, der fachlich tragfähig bleibt. Nutze keine Meta-Sätze über fehlende Datenquellen. Lieber präzise knapp als breit spekulativ.

<!--
BRANCHENBEZEICHNUNG-REGEL:
Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

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
- kmu: Bereichskoordinierung, Governance, erweiterbare Prozesse

BRANCHEN-MODIFIKATOREN:
  FINANZEN/HEALTH/VERWALTUNG = Schwerpunkt Governance & Sicherheit
  MARKETING/KREATIV = Schwerpunkt Wertschöpfung & Befähigung
  INDUSTRIE/PRODUKTION = Schwerpunkt Datenqualität & Prozessintegration
  E-COMMERCE/HANDEL = Schwerpunkt Konsistenz, Datenfeeds, Automatisierung
  MEDIEN/KREATIV nach Sparte: Post/Audio = Durchsatz und Rechtekette; Verlag/Agentur = Freigaben und Kennzeichnung; Games = Lokalisierung und Live-Betrieb

ANTI-REDUNDANZ:
- Benchmark-Daten HIER vollständig
- In anderen Sektionen nur referenzieren

ANTI-SCHEINPRÄZISION (VERBINDLICH): Keine exakten Zahlen, Fristen, Marktanteile, Prozentsätze, Tool-Preise oder Förderbeträge nennen, wenn sie nicht ausdrücklich im Input oder in der Recherche stehen. Bei fehlender Exaktheit lieber Spannbreite, Einordnung oder qualitative Formulierung nutzen. VERBOTEN: erfundene Prozentwerte, Monatszahlen, Eurobeträge, Rankings oder scheinbar exakte Benchmarks.

SPRINT N - SOLO PERSONA REGELN (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
NICHT VERWENDEN für Solo:
- "Team aufbauen" → stattdessen: "Kapazität erweitern"
- "Mitarbeiter" → stattdessen: "Ressourcen"
- "Teams" → stattdessen: "Ihre Vergleichsgruppe"
- "Fachbereich" → stattdessen: "Arbeitsfeld"
- "Abteilung" → stattdessen: "Arbeitsbereich"
Formulierungen ohne Team-/Abteilungsbegriff verwenden!
{% endif %}
-->

FAKTEN- UND ANNAHMEN-TRENNUNG (VERBINDLICH):
- Harte Eingabedaten, Scores, deterministische Zahlen und explizite Nutzerangaben als Tatsachen behandeln.
- Schlussfolgerungen aus mehreren Signalen als Einordnung formulieren, nicht als gesicherte Tatsache.
- Branchenübliche Muster, Benchmarks oder fehlende Detailinformationen nur als Annahme oder plausible Ableitung formulieren.
SPRACHMUSTER:
- Faktisch: „Der Score liegt bei ...", „Genannt wurde ...", „Vorgegeben ist ..."
- Abgeleitet: „Daraus ergibt sich ...", „Das spricht dafür, dass ..."
- Annahme: „Erfahrungsgemäß ist zu erwarten ...", „Wahrscheinlich relevant ist ..."

<!-- SPRINT 2: OPT-B2 Wettbewerbs-Framework stärken -->
Formuliere verständlich für einen Geschäftsführer ohne KI-Vorwissen. Nicht „Wettbewerbsmatrix", sondern „Wie Sie sich von anderen in Ihrer Branche abheben können."

WETTBEWERBSTIEFE (PFLICHT):
(a) KONKRETE WETTBEWERBSPOSITION: Ordne die Score-Vergleichswerte (Ø vs. Top 10%) nicht nur tabellarisch, sondern im Fließtext ein: „In der Kategorie [X] liegen Sie [über/unter] dem Durchschnitt — das bedeutet konkret: [was das Unternehmen bereits kann / wo es zurückliegt]." Pro Score-Kategorie 1 Satz Einordnung.
(b) DIFFERENZIERUNGSHEBEL DURCH KI: Formuliere mindestens einen konkreten Differenzierungshebel — wie kann KI dieses Unternehmen von Wettbewerbern abheben? Basierend auf den Stärken aus der Score-Tabelle. Muster: „Ihre Stärke in [Kategorie] ermöglicht es, [konkreter Vorteil] schneller als Wettbewerber zu erreichen."
(c) DRINGLICHKEITSDIMENSION (realistisch, nicht alarmistisch): Ergänze in der Überholungs-Strategie einen konkreten Hinweis, was bei Nicht-Handeln passiert. Formulierung mit Unsicherheits-Hedge: „Erfahrungsgemäß ist zu erwarten, dass Wettbewerber, die [konkreter Schritt] umsetzen, einen Vorsprung aufbauen, der sich [konkrete Konsequenz]."
CONSTRAINT: Keine erfundenen Marktanteile oder Adoptionszahlen. Bestehende Benchmark-Zahlen (Ø 65, Top 10% = 82 etc.) unverändert.

CONFIDENCE-HINWEIS (BEI BEDARF): Wo Datenlage oder Marktvergleich erkennbar unsicher ist (z.B. regionale Benchmarks, branchenspezifische Studien, Förderprogramm-Verfügbarkeit), füge einen kurzen Absatz ein: <p><strong>Wichtig:</strong> Diese Einordnung ist belastbar in der Richtung, aber einzelne Markt- oder Wettbewerbsdetails können je nach Region, Segment und Aktualität abweichen.</p> Nutze diesen Hinweis nur dort, wo tatsächlich Unsicherheit besteht — nicht pauschal in jeder Section.

ANNAHMEN-ABSATZ (PFLICHT AM SECTION-ENDE): Füge am Ende der Section, vor dem Quellenblock (falls vorhanden), genau einen kurzen Absatz ein: <p><strong>Annahmen:</strong> [1-3 zentrale fachliche Annahmen, auf denen die Einordnung dieser Section beruht]</p> Regeln: - Nur fachliche Annahmen, keine Meta-Hinweise zu Quellen, Prompting oder Datenlage. - Maximal 2-3 Sätze. - Beispiel: "Annahmen: Stabiles Marktumfeld in den nächsten 12 Monaten; aktuelle Teamgröße bleibt bestehen; keine regulatorischen Verschärfungen über den EU AI Act hinaus."
<!-- /SPRINT 2 -->

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
        <td>{{score_gesamt|default(0)}}</td>
        <td>65</td>
        <td>82</td>
        <td>
          <!-- automatisch ableitbar -->
          {% if (score_gesamt|default(0)) > 82 %}stark über Branchenniveau
          {% elif (score_gesamt|default(0)) > 65 %}über Branchenniveau
          {% else %}unter Branchendurchschnitt{% endif %}
        </td>
      </tr>

      <tr>
        <td>Befähigung</td>
        <td>{{score_befaehigung|default(0)}}</td>
        <td>68</td>
        <td>85</td>
        <td>
          {% if (score_befaehigung|default(0)) > 85 %}stark über Branchenniveau
          {% elif (score_befaehigung|default(0)) > 68 %}über Branchenniveau
          {% else %}unter Branchendurchschnitt{% endif %}
        </td>
      </tr>

      <tr>
        <td>Governance</td>
        <td>{{score_governance|default(0)}}</td>
        <td>58</td>
        <td>78</td>
        <td>
          {% if (score_governance|default(0)) > 78 %}stark über Branchenniveau
          {% elif (score_governance|default(0)) > 58 %}über Branchenniveau
          {% else %}unter Branchendurchschnitt{% endif %}
        </td>
      </tr>

      <tr>
        <td>Sicherheit</td>
        <td>{{score_sicherheit|default(0)}}</td>
        <td>62</td>
        <td>80</td>
        <td>
          {% if (score_sicherheit|default(0)) > 80 %}stark über Branchenniveau
          {% elif (score_sicherheit|default(0)) > 62 %}über Branchenniveau
          {% else %}unter Branchendurchschnitt{% endif %}
        </td>
      </tr>

      <tr>
        <td>Wertschöpfung</td>
        <td>{{score_nutzen|default(0)}}</td>
        <td>70</td>
        <td>88</td>
        <td>
          {% if (score_nutzen|default(0)) > 88 %}stark über Branchenniveau
          {% elif (score_nutzen|default(0)) > 70 %}über Branchenniveau
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
    {% if (score_befaehigung|default(0)) < 68 %}
      <li><strong>Befähigung:</strong> deutlicher Rückstand gegenüber dem Branchen-Ø ({{score_befaehigung|default(0)}} vs. 68).</li>
    {% endif %}
    {% if (score_governance|default(0)) < 58 %}
      <li><strong>Governance:</strong> deutlicher Rückstand gegenüber dem Branchen-Ø ({{score_governance|default(0)}} vs. 58).</li>
    {% endif %}
    {% if (score_sicherheit|default(0)) < 62 %}
      <li><strong>Sicherheit:</strong> deutlicher Rückstand gegenüber dem Branchen-Ø ({{score_sicherheit|default(0)}} vs. 62).</li>
    {% endif %}
    {% if (score_nutzen|default(0)) < 70 %}
      <li><strong>Wertschöpfung:</strong> deutlicher Rückstand gegenüber dem Branchen-Ø ({{score_nutzen|default(0)}} vs. 70).</li>
    {% endif %}
  </ul>

  <h3>Ihre stärksten Stärken</h3>
  <p>
    Diese Bereiche liegen erkennbar über dem Branchendurchschnitt und können als
    Fundament für weitere Entwicklung dienen:
  </p>
  <ul>
    {% if (score_befaehigung|default(0)) > 68 %}
      <li><strong>Befähigung:</strong> erkennbarer Vorsprung vor dem Branchendurchschnitt ({{score_befaehigung|default(0)}} vs. 68).</li>
    {% endif %}
    {% if (score_governance|default(0)) > 58 %}
      <li><strong>Governance:</strong> erkennbarer Vorsprung vor dem Branchendurchschnitt ({{score_governance|default(0)}} vs. 58).</li>
    {% endif %}
    {% if (score_sicherheit|default(0)) > 62 %}
      <li><strong>Sicherheit:</strong> erkennbarer Vorsprung vor dem Branchendurchschnitt ({{score_sicherheit|default(0)}} vs. 62).</li>
    {% endif %}
    {% if (score_nutzen|default(0)) > 70 %}
      <li><strong>Wertschöpfung:</strong> erkennbarer Vorsprung vor dem Branchendurchschnitt ({{score_nutzen|default(0)}} vs. 70).</li>
    {% endif %}
  </ul>

  <h3>Überholungs-Strategie (nächste 12 Monate – size-aware)</h3>
  <ol>
    <li>
      <strong>Q2:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Fokus auf Ihre persönliche Standardisierung: 2–3 Kernprozesse dokumentieren, einfache KI-Checklisten für sich selbst nutzen.
      {% elif COMPANY_SIZE == "team" %}
        Rollen klären (KI-Owner, Reviewer), einheitliche Templates und kurze Review-Loops.
      {% else %}
        Bereichsübergreifende Pilotfläche definieren (z. B. Marketing, Produktion, Backoffice); erste Governance-Standards verankern.
      {% endif %}
    </li>

    <li>
      <strong>Q3:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Workflow-Optimierung: Ihre KI-gestützten Routinen festigen, Integration Ihrer wichtigsten Branchentools.
      {% elif COMPANY_SIZE == "team" %}
        Gemeinsame Dokumentation + regelmäßige Team-Reviews; Tool-Reduktion bei Doppelstrukturen.
      {% else %}
        Harmonisierung bereichsspezifischer Prozesse, klare Datenschnittstellen, einheitliche Freigaben.
      {% endif %}
    </li>

    <li>
      <strong>Q4:</strong>
      {% if COMPANY_SIZE == "solo" %}
        Routine-Festigung: Ihre wiederkehrende Nutzung + Jahresplanung für das kommende Jahr.
      {% elif COMPANY_SIZE == "team" %}
        Erweiterung im Team: automatisierte Qualitätskontrolle + einheitliche KI-Kommunikation.
      {% else %}
        Erweiterungsprogramm: Governance erweitern, Auditroutinen, bereichsübergreifende Standards.
      {% endif %}
    </li>
  </ol>

  <p>
    <strong>Strategischer Zielkorridor:</strong>
    {% if (score_gesamt|default(0)) >= 80 %}
      Richtung Top 5 % der Branche.
    {% elif (score_gesamt|default(0)) >= 60 %}
      Richtung Top 10 % der Branche.
    {% else %}
      Richtung Top 25 % – Schwerpunkt auf Stabilisierung und strukturierter Weiterentwicklung.
    {% endif %}
  </p>
</section>
