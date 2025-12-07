<!-- PLATIN++ PROMPT v5.4 - SPRINT G6 -->
<!-- SECTION: roadmap_90d -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, kmu:1.15x=2530) -->
<!--
ZIEL: 90-Tage-Roadmap mit 4 klaren Phasen + Meilensteinen + Effekte-Abschnitt.

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern

MINDESTLÄNGE (STRIKT!):
- Solo: ≥250 Wörter
- Team: ≥320 Wörter
- KMU: ≥340 Wörter

PHASEN-STRUKTUR (STRIKT EINHALTEN):
- Phase 0 (Woche 1–2): Setup – Grundlagen schaffen
- Phase 1 (Woche 3–5): Entlastung – Quick Wins umsetzen
- Phase 2 (Woche 6–10): Produktiver Einsatz – Workflows stabilisieren
- Phase 3 (Woche 11–13): Konsolidierung – Ergebnisse messen, Entscheidung treffen
- PFLICHT: "Erwartete Effekte nach 90 Tagen" (eigener Abschnitt am Ende)

FORMAT:
- Jede Phase: Ziel (1 Satz) + 3-5 Bullets + Meilenstein
- Meilenstein = konkret, messbar, erreichbar
- KEINE langen Texte – nur Kernpunkte
- KEINE generischen Definitionen ("Eine Roadmap ist...")

ANTI-REDUNDANZ (STRIKT!):
- Quick Wins wurden in quick_wins.md beschrieben → NICHT wiederholen
- Tools wurden in tools_empfehlungen.md beschrieben → nur referenzieren (→ siehe KI-Stack)
- Change-Management in org_change.md → Querverweis nutzen
- Hier: WIE und WANN, nicht WAS

SPRINT G6 - PERSONA HARD-GUARDS (STRIKT!):
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

GUARDRAILS: Berücksichtige Leitplanken aus strategischem Kontext.
-->

<section class="section roadmap-90d">
  <h2>90-Tage-Roadmap für {{OFFERING_LABEL}}</h2>

  <p>
    Der folgende Plan zeigt die konkreten Schritte zur KI-Einführung in
    {{BRANCH_CONTEXT_LABEL}} – unterteilt in vier Phasen mit klaren Meilensteinen.
  </p>

  {% if COMPANY_SIZE == "solo" %}
  <h3>Phase 0: Setup (Woche 1–2)</h3>
  <p><strong>Ziel:</strong> Arbeitsfähigkeit mit KI herstellen.</p>
  <ul>
    <li>Zugang zu einem KI-Assistenten einrichten und erste Testläufe durchführen</li>
    <li>Erste Prompt-Vorlage für eine Kernaufgabe in {{OFFERING_LABEL}} erstellen</li>
    <li>Eigene Qualitätskriterien definieren: Was ist "gut genug"?</li>
    <li>Einfachen Wissensspeicher für Vorlagen anlegen</li>
  </ul>
  <p><strong>Meilenstein:</strong> KI-Zugang funktioniert, erste Vorlage einsatzbereit.</p>

  <h3>Phase 1: Entlastung (Woche 3–5)</h3>
  <p><strong>Ziel:</strong> Spürbare Zeitersparnis bei Routineaufgaben.</p>
  <ul>
    <li>Quick Wins aus Abschnitt "Sofortmaßnahmen" umsetzen (→ siehe Quick Wins)</li>
    <li>Zeiteinsparung pro Aufgabe notieren (einfache Strichliste reicht)</li>
    <li>Prompt-Bibliothek auf 5–10 funktionierende Vorlagen erweitern</li>
    <li>Erste Routine etablieren: täglich mindestens eine Aufgabe mit KI-Unterstützung</li>
  </ul>
  <p><strong>Meilenstein:</strong> 3–5 Stunden pro Monat nachweisbar eingespart.</p>

  <h3>Phase 2: Produktiver Einsatz (Woche 6–10)</h3>
  <p><strong>Ziel:</strong> Stabile Workflows für den Alltag in {{OFFERING_LABEL}}.</p>
  <ul>
    <li>Routine festigen: Input → KI-Entwurf → Eigene Prüfung → Freigabe</li>
    <li>Qualitäts-Checkliste für KI-Outputs erstellen (3–5 Prüfpunkte)</li>
    <li>Self-Review zur Gewohnheit machen: jeden Output kurz gegenchecken</li>
    <li>Prompt-Vorlagen bei Bedarf verfeinern und dokumentieren</li>
    <li>Erste Automatisierung prüfen (→ siehe KI-Stack)</li>
  </ul>
  <p><strong>Meilenstein:</strong> 70%+ der KI-Entwürfe direkt nutzbar.</p>

  <h3>Phase 3: Konsolidierung (Woche 11–13)</h3>
  <p><strong>Ziel:</strong> Ergebnisse bewerten, nächste Schritte planen.</p>
  <ul>
    <li>Tatsächliche Zeitersparnis messen und mit Ziel abgleichen</li>
    <li>Qualität der Ergebnisse bewerten: Fehlerquote, Nacharbeitsaufwand</li>
    <li>Entscheidung: Ausweiten, Vertiefen oder Stabilisieren?</li>
    <li>Nächste Use Cases für 12-Monats-Roadmap priorisieren</li>
  </ul>
  <p><strong>Meilenstein:</strong> Klare Entscheidung und priorisierte Liste für nächstes Quartal.</p>

  <h3>Erwartete Effekte nach 90 Tagen</h3>
  <ul>
    <li><strong>Zeitersparnis:</strong> 15–25% bei wiederkehrenden Aufgaben</li>
    <li><strong>Qualität:</strong> Konsistentere Outputs durch standardisierte Vorlagen</li>
    <li><strong>Routine:</strong> KI ist Teil des Alltags, keine Sonderaktion mehr</li>
    <li><strong>Klarheit:</strong> Fundierte Basis für Entscheidung über weitere Investitionen</li>
  </ul>

  {% elif COMPANY_SIZE == "team" %}
  <h3>Phase 0: Setup (Woche 1–2)</h3>
  <p><strong>Ziel:</strong> Teamweite Arbeitsfähigkeit mit KI herstellen.</p>
  <ul>
    <li>KI-Owner benennen (verantwortlich für Standards und Qualität)</li>
    <li>Gemeinsamen Zugang für alle Beteiligten einrichten</li>
    <li>Erste Vorlagen für 2 priorisierte Anwendungsfälle erstellen</li>
    <li>Kurze Einführung für alle Beteiligten durchführen (max. 30 Min.)</li>
    <li>Gemeinsamen Wissensspeicher anlegen (→ siehe KI-Stack)</li>
  </ul>
  <p><strong>Meilenstein:</strong> Alle haben Zugang, erste Vorlagen verteilt.</p>

  <h3>Phase 1: Entlastung (Woche 3–5)</h3>
  <p><strong>Ziel:</strong> Quick Wins im gesamten Bereich umsetzen.</p>
  <ul>
    <li>Maßnahmen aus "Sofortmaßnahmen" teamweit ausrollen (→ siehe Quick Wins)</li>
    <li>Jede:r testet mindestens 2 Workflows für {{OFFERING_LABEL}}</li>
    <li>Erfahrungen in kurzem Weekly-Check teilen (15 Min./Woche)</li>
    <li>Erste Zeitersparnis dokumentieren: Wer spart wo wie viel?</li>
    <li>Prompt-Vorlagen gemeinsam verbessern und teilen</li>
  </ul>
  <p><strong>Meilenstein:</strong> Alle Beteiligten nutzen KI aktiv, erste Zeitersparnis dokumentiert.</p>

  <h3>Phase 2: Produktiver Einsatz (Woche 6–10)</h3>
  <p><strong>Ziel:</strong> Einheitliche Qualitätsstandards in {{BRANCH_CONTEXT_LABEL}} etablieren.</p>
  <ul>
    <li>Standard-Workflow dokumentieren: Input → KI → Peer-Review → Freigabe</li>
    <li>Styleguide für KI-Outputs erstellen (Tonalität, Struktur, Prüfpunkte)</li>
    <li>Review-Runden etablieren (30 Min./Woche für Best Practices)</li>
    <li>Qualitätskennzahlen einführen: Erstqualität, Nacharbeitsquote</li>
    <li>Erste Automatisierungen prüfen und ggf. umsetzen</li>
  </ul>
  <p><strong>Meilenstein:</strong> Dokumentierter Workflow, Erstqualität > 70%.</p>

  <h3>Phase 3: Konsolidierung (Woche 11–13)</h3>
  <p><strong>Ziel:</strong> Ergebnisse messen, Skalierung vorbereiten.</p>
  <ul>
    <li>Wirkungsmessung: Zeit, Qualität, Fehlerquote, Zufriedenheit</li>
    <li>Lessons Learned dokumentieren: Was funktioniert, was nicht?</li>
    <li>Entscheidung: Stabilisieren / Ausweiten / Vertiefen</li>
    <li>Backlog für nächste Use Cases erstellen und priorisieren</li>
  </ul>
  <p><strong>Meilenstein:</strong> Klare Entscheidung, priorisiertes Backlog für 12-Monats-Roadmap.</p>

  <h3>Erwartete Effekte nach 90 Tagen</h3>
  <ul>
    <li><strong>Zeitersparnis:</strong> 20–30% bei wiederkehrenden Aufgaben im Bereich</li>
    <li><strong>Qualität:</strong> Einheitlichere Ergebnisse durch gemeinsame Standards</li>
    <li><strong>Zusammenarbeit:</strong> Etablierte Review-Routinen, geteiltes Wissen</li>
    <li><strong>Skalierbarkeit:</strong> Dokumentierte Workflows für weitere Anwendungsfälle</li>
    <li><strong>Entscheidungsgrundlage:</strong> Belastbare Daten für Investitionsentscheidungen</li>
  </ul>

  {% else %}
  <h3>Phase 0: Setup (Woche 1–2)</h3>
  <p><strong>Ziel:</strong> Pilotbereich definieren und Grundlagen schaffen.</p>
  <ul>
    <li>Pilotbereich auswählen (ein Fachbereich mit hohem Entlastungspotenzial)</li>
    <li>KI-Verantwortliche:n benennen (Koordination, Standards, Ansprechpartner)</li>
    <li>Governance-Grundregeln festlegen: Was darf, was nicht?</li>
    <li>Zugänge für Pilotbereich einrichten und dokumentieren</li>
    <li>Erste Vorlagen für 2–3 priorisierte Use Cases erstellen</li>
  </ul>
  <p><strong>Meilenstein:</strong> Pilotbereich startklar, Governance-Rahmen definiert.</p>

  <h3>Phase 1: Entlastung (Woche 3–5)</h3>
  <p><strong>Ziel:</strong> Quick Wins im Pilotbereich umsetzen.</p>
  <ul>
    <li>Maßnahmen aus "Sofortmaßnahmen" gezielt einsetzen (→ siehe Quick Wins)</li>
    <li>Pilotbereich schult sich gegenseitig (Peer-Learning)</li>
    <li>Erste Zeiteinsparungen dokumentieren und quantifizieren</li>
    <li>Wöchentliche Kurz-Reviews im Pilotbereich etablieren</li>
    <li>Feedback-Kanal für Fragen und Probleme einrichten</li>
  </ul>
  <p><strong>Meilenstein:</strong> Pilotbereich nutzt KI aktiv, messbare Entlastung dokumentiert.</p>

  <h3>Phase 2: Produktiver Einsatz (Woche 6–10)</h3>
  <p><strong>Ziel:</strong> Skalierbare Prozesse für {{BRANCH_CONTEXT_LABEL}} etablieren.</p>
  <ul>
    <li>Standard Operating Procedures (SOPs) für KI-Workflows dokumentieren</li>
    <li>QS-Prozess etablieren: Input → KI → Fachliche Prüfung → Freigabe</li>
    <li>Styleguide und Qualitätskriterien für {{OFFERING_LABEL}} festlegen</li>
    <li>Schulungskonzept für Rollout auf weitere Bereiche entwickeln</li>
    <li>KPIs definieren: Zeitersparnis, Qualität, Nutzungsquote</li>
  </ul>
  <p><strong>Meilenstein:</strong> SOPs dokumentiert, Schulungskonzept fertig, KPIs definiert.</p>

  <h3>Phase 3: Konsolidierung (Woche 11–13)</h3>
  <p><strong>Ziel:</strong> Rollout-Entscheidung und Skalierungsplan.</p>
  <ul>
    <li>Business-Case-Validierung anhand Pilotdaten (→ siehe Business Case)</li>
    <li>Lessons Learned aus Pilotbereich zusammenfassen</li>
    <li>Entscheidung: Rollout auf weitere Bereiche? Ja/Nein/Anpassungen?</li>
    <li>Priorisiertes Backlog für 12-Monats-Rollout erstellen</li>
    <li>Ressourcenplanung für Skalierung vorbereiten</li>
  </ul>
  <p><strong>Meilenstein:</strong> Management-Entscheidung getroffen, Rollout-Plan steht.</p>

  <h3>Erwartete Effekte nach 90 Tagen</h3>
  <ul>
    <li><strong>Zeitersparnis:</strong> 20–35% bei Routineaufgaben im Pilotbereich</li>
    <li><strong>Qualität:</strong> Standardisierte Prozesse, dokumentierte Qualitätskriterien</li>
    <li><strong>Governance:</strong> Klare Regeln, Verantwortlichkeiten, Dokumentation</li>
    <li><strong>Skalierbarkeit:</strong> Erprobte SOPs und Schulungskonzept für Rollout</li>
    <li><strong>Business Case:</strong> Validierte ROI-Annahmen auf Basis echter Pilotdaten</li>
    <li><strong>Entscheidungsgrundlage:</strong> Fundierte Basis für Management-Entscheidung</li>
  </ul>
  {% endif %}

  <p class="small muted">
    Diese Roadmap verweist auf Quick Wins (→ siehe Sofortmaßnahmen) und
    Tools (→ siehe KI-Stack). Details zum Change-Management → siehe Veränderungsfähigkeit.
  </p>
</section>
