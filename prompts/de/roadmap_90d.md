<!-- PLATIN+++ PROMPT v6.0 - SPRINT PRODUKT-SCHÄRFUNG -->
<!-- SECTION: roadmap_90d -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2800 (solo:0.8x=2240, team:1.0x=2800, kmu:1.15x=3220) -->
<!--
ZIEL: 90-Tage-Roadmap als Abfolge von ENTSCHEIDUNGEN (nicht Tool-Einführungen).

=============================================================================
SPRACHSHIFT v6.0 — ENTSCHEIDUNGEN STATT IMPLEMENTIERUNGEN:
=============================================================================

Die Roadmap ist KEINE To-do-Liste für Tool-Rollouts.
Die Roadmap ist eine Abfolge von bewussten Entscheidungen.

VERBOTENE FORMULIERUNGEN → ERSETZUNGEN:
❌ "Einführung eines KI-Tools"     → ✅ "Festlegung, welche Aufgaben automatisiert werden"
❌ "Tool implementieren"           → ✅ "Grenzen des KI-Einsatzes definieren"
❌ "KI-System einrichten"          → ✅ "Entscheidungsrahmen für KI-Nutzung schaffen"
❌ "Automatisierung aufsetzen"     → ✅ "Kriterien für Automatisierung festlegen"
❌ "Workflow digitalisieren"       → ✅ "Abgrenzung zwischen manuell und automatisiert"
❌ "Software ausrollen"            → ✅ "Standards für den Einsatz etablieren"
❌ "Integration durchführen"       → ✅ "Schnittstellen-Verantwortlichkeiten klären"

TONALITÄT:
- Entscheidungsorientiert, nicht technisch
- Strategisch, nicht operativ
- Abgrenzend, nicht aufzählend

=============================================================================

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern

MINDESTLÄNGE (STRIKT EINHALTEN - SPRINT G18!):
- Solo: Mindestens 180–230 Wörter, klar strukturiert.
- Team: Mindestens 220–280 Wörter, inklusive Change-Kommunikation.
- KMU: Mindestens 250–300 Wörter, inkl. Führung/Stakeholder-Hinweisen.

WICHTIG: Bei Unterschreitung wird Section abgelehnt!

BOOSTER-SEKTIONEN (NEU - SPRINT G17.R):
- Solo: KPI-Tracking & Mini-Dashboard Setup, Micro-Change-Management
- Team: Team-Kommunikation & Rollout-Rituale, Dokumentation & Wissensspeicher
- KMU: Change-Kommunikation auf Führungsebene, KPI-Framework für Arbeitsbereiche

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

  <h3>KPI-Tracking & Mini-Dashboard Setup</h3>
  <p>
    Als Einzelunternehmer:in benötigen Sie ein pragmatisches, zeitsparendes Reporting-System.
    Fokussieren Sie sich auf diese drei Kern-KPIs für Ihren KI-Einsatz:
  </p>
  <ul>
    <li><strong>Zeitersparnis pro Woche:</strong> Notieren Sie für jede KI-gestützte Aufgabe die
    eingesparte Zeit im Vergleich zur manuellen Bearbeitung. Eine einfache Strichliste oder
    Tabelle genügt – Ziel: 3–5 Stunden Ersparnis pro Monat.</li>
    <li><strong>Output-Menge:</strong> Wie viele Texte, E-Mails, Konzepte oder andere Deliverables
    haben Sie mit KI-Unterstützung erstellt? Tracken Sie die Produktivitätssteigerung
    quantitativ (z. B. „12 LinkedIn-Posts statt 4 ohne KI").</li>
    <li><strong>Qualitätsbewertung:</strong> Bewerten Sie Ihre KI-Outputs auf einer Skala von
    1–5 Sternen. Wie oft konnten Sie einen Entwurf direkt verwenden? Ziel: 70%+ Erstqualität.</li>
  </ul>
  <p>
    <strong>Mini-Dashboard einrichten:</strong> Nutzen Sie ein einfaches Tool wie Notion, Excel
    oder sogar ein Notizbuch. Legen Sie eine wöchentliche Tabelle an mit Spalten für Aufgabentyp,
    Zeitaufwand (mit/ohne KI), Qualitätssterne und kurze Learnings. Reservieren Sie jeden Freitag
    15–20 Minuten für die Dokumentation. Nach 90 Tagen haben Sie belastbare Daten für Ihre
    Investitionsentscheidung und können ROI konkret nachweisen.
  </p>

  <h3>Micro-Change-Management (1-Person-Betrieb)</h3>
  <p>
    Die Einführung neuer KI-Workflows erfordert bewusste Integration in Ihren Arbeitsalltag –
    auch wenn Sie allein arbeiten. Ohne strukturiertes Vorgehen besteht das Risiko, dass
    neue Tools nach anfänglicher Begeisterung wieder in Vergessenheit geraten.
  </p>
  <ul>
    <li><strong>Routine-Anker setzen:</strong> Verknüpfen Sie KI-Nutzung mit bestehenden
    Gewohnheiten. Beispiel: „Nach dem Morgenkaffee starte ich mit dem KI-gestützten
    E-Mail-Entwurf" oder „Vor jedem Kundengespräch lasse ich mir eine Gesprächsvorbereitung
    generieren". Feste Trigger erhöhen die Umsetzungswahrscheinlichkeit deutlich.</li>
    <li><strong>Selbstkontrolle ohne Druck:</strong> Führen Sie eine „Erfolgs-Checkliste" mit
    3–5 KI-Aufgaben pro Woche. Haken Sie ab, was Sie geschafft haben – ohne sich bei
    Auslassungen zu kritisieren. Der visuelle Fortschritt motiviert zur Kontinuität.</li>
    <li><strong>Wöchentliches Self-Review (30 Min.):</strong> Jeden Freitagmorgen oder
    Sonntagabend: Was hat gut funktioniert? Wo gab es Hürden? Welche Prompts brauchen
    Verfeinerung? Notieren Sie 2–3 konkrete Verbesserungsideen für die Folgewoche.</li>
    <li><strong>Iterative Anpassung:</strong> Ihr KI-Workflow ist ein lebendes System.
    Passen Sie Vorlagen und Routinen monatlich an veränderte Anforderungen in
    {{OFFERING_LABEL}} an. Was im ersten Monat funktioniert hat, muss im dritten
    Monat nicht mehr optimal sein.</li>
  </ul>
  <p>
    <strong>Erfolgsfaktor:</strong> Setzen Sie sich realistische Zwischenziele. Starten Sie
    mit einer KI-Aufgabe täglich, steigern Sie nach 2 Wochen auf 2–3. So vermeiden Sie
    Überforderung und bauen nachhaltige Kompetenz auf.
  </p>

  <h3>Content & Marketing-Systematik</h3>
  <p>
    Konzentrieren Sie sich auf 1–2 Kanäle, die zu {{OFFERING_LABEL}} passen (z. B. LinkedIn, Newsletter).
    Etablieren Sie eine feste Content-Routine: Einmal pro Woche einen kurzen Beitrag mit KI-Unterstützung
    erstellen. Nutzen Sie Ihre eigenen KI-Readiness-Reports als Marketing-Asset – sie zeigen Kompetenz
    und bieten echten Mehrwert für potenzielle Kunden. So verbinden Sie Ihre KI-Einführung direkt
    mit Ihrer Sichtbarkeit als Expert:in in {{BRANCH_CONTEXT_LABEL}}.
  </p>

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

  <h3>Team-Kommunikation & Rollout-Rituale</h3>
  <p>
    Die erfolgreiche KI-Einführung im Bereich erfordert strukturierte Kommunikation und
    wiederkehrende Formate, die Akzeptanz und Kompetenzaufbau fördern. Etablieren Sie
    folgende Rituale:
  </p>
  <ul>
    <li><strong>KI-Standup (15 Min./Woche):</strong> Kurzer Austausch zu Beginn jeder
    Woche: Was habe ich mit KI ausprobiert? Was hat funktioniert? Welche Hürden gab es?
    Der KI-Owner moderiert und sammelt Themen für Vertiefung.</li>
    <li><strong>Feedback-Loop etablieren:</strong> Richten Sie einen dedizierten Kanal ein
    (Slack-Channel, Teams-Gruppe oder geteiltes Dokument), in dem Beteiligte Erfahrungen,
    Prompts und Tipps teilen. Niedrigschwelliger Austausch beschleunigt den Lernprozess.</li>
    <li><strong>Mini-Demos (30 Min. alle 2 Wochen):</strong> Ein Beteiligter zeigt einen
    erfolgreichen KI-Workflow live. Konkrete Anwendungsfälle motivieren mehr als
    theoretische Schulungen. Rotieren Sie die Präsentierenden.</li>
    <li><strong>Akzeptanz-Maßnahmen:</strong> Holen Sie Skeptiker:innen gezielt ab.
    Lassen Sie sie bei der Auswahl von Use Cases mitbestimmen. Zeigen Sie frühe Erfolge
    transparent – nichts überzeugt mehr als messbare Zeitersparnis bei Kolleg:innen.</li>
    <li><strong>Tool-Onboarding strukturieren:</strong> Erstellen Sie eine 1-Seiten-Anleitung
    für neue Beteiligte: Zugang, erste Schritte, wichtigste Prompts, Ansprechpartner.
    So wird niemand abgehängt, wenn er oder sie später einsteigt.</li>
  </ul>

  <h3>Dokumentation & Wissensspeicher</h3>
  <p>
    Wissen, das nur in einzelnen Köpfen existiert, geht verloren. Bauen Sie von Beginn an
    einen strukturierten KI-Wissensspeicher für Ihren Bereich auf:
  </p>
  <ul>
    <li><strong>KI-Handbuch anlegen:</strong> Ein lebendes Dokument mit Best Practices,
    bewährten Prompts, Qualitätskriterien und typischen Fehlern. Aktualisierung monatlich
    durch den KI-Owner, Input von allen Beteiligten.</li>
    <li><strong>Prompt-Bibliothek:</strong> Sammeln Sie alle funktionierenden Prompt-Vorlagen
    in einer gemeinsamen Ablage (Notion, Confluence, SharePoint). Kategorisieren Sie nach
    Anwendungsfall: Texterstellung, Recherche, Analyse, E-Mail etc.</li>
    <li><strong>Rollen & Verantwortlichkeiten klären:</strong>
      <ul>
        <li><em>KI-Owner:</em> Koordiniert Standards, pflegt Wissensspeicher, ist erster
        Ansprechpartner bei Fragen.</li>
        <li><em>Beteiligte:</em> Testen Workflows, geben Feedback, teilen Learnings.</li>
        <li><em>Qualitäts-Reviewer:</em> Prüft kritische KI-Outputs vor Freigabe.</li>
      </ul>
    </li>
    <li><strong>Lessons Learned dokumentieren:</strong> Nach jeder Phase (Setup, Entlastung,
    Produktiver Einsatz) kurz festhalten: Was haben wir gelernt? Was würden wir anders
    machen? Diese Erkenntnisse sind Gold wert für die Skalierung.</li>
  </ul>
  <p>
    <strong>Tipp:</strong> Halten Sie die Dokumentation schlank. Lieber 10 funktionierende
    Prompts gut beschrieben als 50 ungeprüfte Vorlagen ohne Kontext.
  </p>

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

  <h3>Change-Kommunikation auf Führungsebene</h3>
  <p>
    Die KI-Einführung in einem mittelständischen Unternehmen erfordert strategische
    Kommunikation auf Führungsebene. Ohne aktive Einbindung der Entscheidungsträger
    scheitern selbst erfolgreiche Pilotprojekte an fehlender Unterstützung für die Skalierung.
  </p>
  <ul>
    <li><strong>Stakeholder-Mapping durchführen:</strong> Identifizieren Sie alle relevanten
    Entscheidungsträger und Einflusspersonen: Geschäftsführung, Bereichsleitungen,
    Betriebsrat (falls vorhanden), IT-Leitung. Verstehen Sie deren Perspektive: Wer sieht
    Chancen, wer hat Bedenken? Passen Sie Ihre Kommunikation entsprechend an.</li>
    <li><strong>Chancen & Risiken transparent kommunizieren:</strong> Präsentieren Sie
    eine ausgewogene Analyse: Welche konkreten Effizienzgewinne sind realistisch?
    Welche Risiken (Datenschutz, Qualität, Abhängigkeiten) bestehen und wie werden sie
    adressiert? Ehrliche Kommunikation schafft Vertrauen und vermeidet spätere Enttäuschungen.</li>
    <li><strong>Mitbestimmung einbinden:</strong> Falls ein Betriebsrat existiert, holen
    Sie ihn frühzeitig ins Boot. Klären Sie gemeinsam: Welche Daten werden verarbeitet?
    Gibt es Auswirkungen auf Arbeitsplätze oder -inhalte? Proaktive Einbindung verhindert
    Widerstände und Verzögerungen.</li>
    <li><strong>Regelmäßige Status-Updates:</strong> Etablieren Sie einen monatlichen
    Kurzbericht an die Geschäftsführung: Pilotfortschritt, erreichte Meilensteine,
    gemessene Effekte, nächste Schritte. Keine Überraschungen – kontinuierliche
    Transparenz ist der Schlüssel zu nachhaltigem Management-Support.</li>
    <li><strong>Erfolgsgeschichten nutzen:</strong> Dokumentieren Sie konkrete Erfolge
    aus dem Pilotbereich mit messbaren Zahlen. Diese „Proof Points" sind Ihre beste
    Argumentationsgrundlage für die Rollout-Entscheidung.</li>
  </ul>

  <h3>KPI-Framework für Arbeitsbereiche</h3>
  <p>
    Ein strukturiertes KPI-Framework ermöglicht die objektive Bewertung des KI-Einsatzes
    über verschiedene Arbeitsbereiche hinweg. Definieren Sie Messgrößen, die ohne
    Interpretationsspielraum erfasst werden können:
  </p>
  <ul>
    <li><strong>Effizienz-KPIs:</strong>
      <ul>
        <li><em>Zeitersparnis pro Vorgang:</em> Vergleich der Bearbeitungszeit mit und ohne
        KI-Unterstützung (Ziel: 20–35% Reduktion)</li>
        <li><em>Durchsatz:</em> Anzahl bearbeiteter Vorgänge pro Zeiteinheit (Steigerung
        messbar machen)</li>
        <li><em>Automatisierungsgrad:</em> Anteil der Aufgaben, die vollständig oder
        teilautomatisiert ablaufen</li>
      </ul>
    </li>
    <li><strong>Qualitäts-KPIs:</strong>
      <ul>
        <li><em>Erstqualitätsrate:</em> Anteil der KI-Outputs, die ohne Nacharbeit
        verwendbar sind (Ziel: >70%)</li>
        <li><em>Fehlerquote:</em> Anzahl der Korrekturen oder Reklamationen pro 100
        KI-gestützte Vorgänge</li>
        <li><em>Kundenzufriedenheit:</em> Bewertung der Ergebnisqualität durch interne
        oder externe Empfänger</li>
      </ul>
    </li>
    <li><strong>Compliance-KPIs:</strong>
      <ul>
        <li><em>Governance-Einhaltung:</em> Anteil der Vorgänge, die nach definierten
        Standards geprüft wurden</li>
        <li><em>Datenschutz-Konformität:</em> Null-Toleranz bei Verstößen, regelmäßige
        Audits dokumentieren</li>
        <li><em>Dokumentationsgrad:</em> Vollständigkeit der Prozessdokumentation für
        regulatorische Anforderungen</li>
      </ul>
    </li>
    <li><strong>Akzeptanz-KPIs:</strong>
      <ul>
        <li><em>Nutzungsquote:</em> Anteil der Mitarbeitenden, die KI-Tools aktiv nutzen</li>
        <li><em>Schulungsabdeckung:</em> Prozent der geschulten Mitarbeitenden im Pilotbereich</li>
        <li><em>Feedback-Score:</em> Regelmäßige Zufriedenheitsbefragung (NPS oder 1–5 Skala)</li>
      </ul>
    </li>
  </ul>
  <p>
    <strong>Umsetzungshinweis:</strong> Starten Sie mit 3–5 Kern-KPIs, die Sie zuverlässig
    messen können. Erweitern Sie das Framework erst, wenn die Basismessung funktioniert.
    Vermeiden Sie KPI-Überflutung – weniger, aber aussagekräftige Kennzahlen sind wertvoller
    als umfangreiche Dashboards ohne Konsequenzen.
  </p>

  {% endif %}

  <h3>Risikominimierung während der Einführung</h3>
  <p>
    {% if COMPANY_SIZE == "solo" %}
    Beginnen Sie mit Aufgaben niedriger Kritikalität, um Erfahrung zu sammeln. Halten Sie bei wichtigen Outputs stets einen manuellen Prüfschritt ein. Dokumentieren Sie früh auftretende Fehlerquellen, um Ihre Prompts iterativ zu verbessern.
    {% elif COMPANY_SIZE == "team" %}
    Starten Sie mit klar abgegrenzten Pilotaufgaben im Bereich. Etablieren Sie Peer-Reviews als festen Bestandteil des Workflows. Sammeln Sie Feedback systematisch und passen Sie Vorlagen basierend auf konkreten Erfahrungen an.
    {% else %}
    Begrenzen Sie den initialen Pilotbereich auf unkritische Prozesse. Definieren Sie klare Eskalationswege bei unerwarteten Ergebnissen. Führen Sie regelmäßige Retrospektiven durch und skalieren Sie erst nach validierter Qualität in weitere Bereiche.
    {% endif %}
  </p>

  <!-- SPRINT G18: Narrative Verbindungen -->
  <p class="small muted">
    Nutzen Sie das <strong>Starter Kit</strong>, um Phase 1 technisch umzusetzen (→ siehe Starter Kit).
    Diese Roadmap verweist auf Quick Wins (→ siehe Sofortmaßnahmen) und
    Tools (→ siehe KI-Stack). Details zum Change-Management → siehe Veränderungsfähigkeit.
  </p>
</section>
