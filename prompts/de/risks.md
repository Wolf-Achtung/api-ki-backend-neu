Developer:
<!-- PLATIN++ PROMPT v5.5 - SPRINT TRUNCATION-FIX -->
<!-- SECTION: risks -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCH_CORE_LABEL}}, {{BRANCH_CONTEXT_LABEL}}, {{OFFERING_LABEL}}, {{score_governance}}, {{score_sicherheit}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 4500 (solo:0.85x=3800, team:1.0x=4500, kmu:1.1x=5000) -->

## ABSOLUTE LÄNGENREGEL (VOR ALLEM ANDEREN!)
{% if COMPANY_SIZE == "solo" %}
**SOLO-HARD-LIMIT: Maximal 700 Wörter / 5.500 Zeichen HTML gesamt.**
Pro Risikokategorie: NUR 3 Risiken (nicht 4!) mit je max. 50 Wörtern. Risiko-Matrix: max. 4 Zeilen.
{% elif COMPANY_SIZE == "team" %}
**TEAM-HARD-LIMIT: Maximal 1000 Wörter / 7.500 Zeichen HTML gesamt.**
Pro Risikokategorie: 4 Risiken mit je max. 60 Wörtern.
{% else %}
**KMU-HARD-LIMIT: Maximal 1300 Wörter / 9.000 Zeichen HTML gesamt.**
{% endif %}
JEDES WORT ÜBER DEM LIMIT WIRD BRUTAL ABGESCHNITTEN — der Report endet dann mitten im Satz!
<!--
HÖCHSTLÄNGE (STRIKT! — Überschreitung wird automatisch getruncated!):
- Solo: max. 5.500 Zeichen (700 Wörter) | Team: max. 7.500 Zeichen (1000 Wörter) | KMU: max. 9.000 Zeichen (1300 Wörter)
- Solo-Budget ist 35.000 Zeichen (exempt) — aber kompakter Output ist besser!
- LIEBER KOMPAKT UND VOLLSTÄNDIG als ausführlich und dann abgeschnitten
- Solo: 3 Risiken × 50 Wörter × 4 Kategorien = 600 Wörter + Matrix 100 Wörter = 700 max
- Team: 4 Risiken × 60 Wörter × 4 Kategorien = 960 Wörter + Matrix = 1000 max
- Risiko-Matrix: Solo max. 4 Zeilen, Team/KMU max. 5 Zeilen
- GESAMT-ZIEL: Solo 600-700, Team 800-1000, KMU 1000-1300 Wörter
-->
<!--
{% if COMPANY_SIZE == "solo" %}
ZIEL: 5 Abschnitte, je max. 140 Wörter (= 600-700 Wörter gesamt). Solo: NUR 3 Risiken pro Kategorie!
{% elif COMPANY_SIZE == "team" %}
ZIEL: 5 Abschnitte, je max. 200 Wörter (= 800-1000 Wörter gesamt).
{% else %}
ZIEL: 5 Abschnitte mit je 200-260 Wörtern (= 1000-1300 Wörter gesamt).
{% endif %}
WICHTIG: Alle Sätze MÜSSEN vollständig sein - keine Abbrüche!

KURZLABELS (VERPFLICHTEND!):
- {{BRANCH_CORE_LABEL}} = Branche in 8-12 Wörtern
- {{BRANCH_CONTEXT_LABEL}} = Branche in 4-6 Wörtern
- {{OFFERING_LABEL}} = Hauptleistung in 6-10 Wörtern

STRUKTUR (5 Pflicht-Abschnitte):
  H3 1. Strategische und organisatorische Risiken (4 Risiken + Maßnahmen)
  H3 2. Daten-, Sicherheits- und Compliance-Risiken (4 Risiken + Maßnahmen)
  H3 3. Qualitäts-, Transparenz- und Akzeptanzrisiken (4 Risiken + Maßnahmen)
  H3 4. Abhängigkeiten, Betriebs- und Lieferantenrisiken (4 Risiken + Maßnahmen)
  H3 5. Risiko-Matrix (Tabelle mit 5 Zeilen)

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: persönliche Überlastung, Single-Point-of-Failure, keine Vertretung
- team: Rollenklärung, Abstimmung, Wissensinseln
- kmu: Governance, Prozesse, Dokumentation, Compliance

ANTI-REDUNDANZ (STRIKT!):
- Risiken NICHT in Guardrails-Sektion wiederholen (→ Querverweis)
- Maßnahmen kurz, nicht in org_change wiederholen (→ Querverweis)
- Bei Überschneidung: Querverweis nutzen

THEMEN-OWNERSHIP (verbindlich):
- Diese Section: OWNER für Risikoanalyse, Risiko-Matrix, Gegenmaßnahmen-Übersicht
- NICHT hier: Governance-Regeln im Detail (→ ai_policy_mini)
- NICHT hier: Change Management / Widerstände (→ org_change)
- NICHT hier: Compliance-Details / AI Act (→ ai_act_summary)
- Maßnahmen: NUR Kurzbeschreibung (1 Satz), keine Umsetzungsplanung

SPRINT G5 - PERSONA HARD-GUARDS (STRIKT!):
{% if COMPANY_SIZE == "solo" %}
SOLO-MODUS - VERBOTEN:
- "Team/Teams/Abteilung/Mitarbeiter" → nicht verwenden
- "Fachbereich" → "Arbeitsfeld"
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

REGELN:
- Scores aktiv interpretieren
- Branchenspezifische Compliance bei regulierten Branchen
- Sachlich, konkret, keine Floskeln

=============================================================================
ANTI-TEXTWÜSTEN REGELN v2.0 (AGGRESSIV - PFLICHT!)
=============================================================================
PROBLEM: Risiko-Bullets werden zu Mini-Aufsätzen. UNLESBAR!
LÖSUNG: STRENGE Wortlimits pro Risiko-Bullet.

HARTE LIMITS PRO RISIKO-BULLET:
┌─────────────────────────────────────────────────────────┐
│ Teil                  │ Max Wörter │ Max Sätze        │
├─────────────────────────────────────────────────────────┤
│ Risiko-Beschreibung   │ 50 Wörter  │ 2-3 Sätze        │
│ Maßnahme              │ 35 Wörter  │ 1-2 Sätze        │
│ Gesamt pro Bullet     │ 85 Wörter  │ 3-5 Sätze        │
└─────────────────────────────────────────────────────────┘

FORMAT PRO RISIKO (PFLICHT - KEIN ABWEICHEN!):
<li><strong>[Risiko in 2-4 Wörtern]:</strong> [Problem in 30-50 Wörtern, vollständige Sätze ohne Abbrüche].
<strong>Maßnahme:</strong> [Lösung in 20-35 Wörtern, vollständige Sätze ohne Abbrüche].</li>

VERBOTEN (STRIKT!):
❌ Risiko-Beschreibungen über 55 Wörter
❌ Maßnahmen über 40 Wörter
❌ Verschachtelte Sätze
❌ Mehr als 1 Maßnahme pro Risiko
❌ Fließtext unter/über der Bullet-Liste

BEISPIEL - SO NICHT:
❌ "Ein wesentliches Risiko besteht in der mangelnden Transparenz bezüglich der
    KI-gestützten Entscheidungsprozesse, was zu Misstrauen bei Kunden führen kann
    und langfristig die Akzeptanz der Lösungen gefährdet..." [= vollständiger Satz = OK wenn nötig]

BEISPIEL - SO JA:
✅ <li><strong>Fehlende Transparenz:</strong> Kunden verstehen KI-Entscheidungen nicht.
   <strong>Maßnahme:</strong> KI-Methoden einfach dokumentieren.</li> [= Kompakt UND vollständig = PERFEKT!]

SEKTION-LIMITS:
- Pro Risiko-Kategorie: Exakt 4 Bullets (nicht mehr, nicht weniger)
- Keine Einleitungstexte zwischen Überschrift und Liste
- Keine Abschlusstexte nach der Liste
=============================================================================
-->

<section class="section risks">
  <h2>Wesentliche Risiken beim Einsatz von KI in {{OFFERING_LABEL}}</h2>

  <p>
    Governance-Score: <strong>{{score_governance}}/100</strong>,
    Sicherheits-Score: <strong>{{score_sicherheit}}/100</strong>.
  </p>

  <h3>1. Strategische und organisatorische Risiken</h3>
  <ul>
    <li>
      <strong>Unklare Zielbilder:</strong>
      Risiko von Insellösungen. Maßnahme: 2–3 priorisierte Use Cases definieren.
    </li>
    <li>
      <strong>Abhängigkeit von Einzelpersonen:</strong>
      Know-how-Konzentration. Maßnahme: Dokumentation + Checklisten.
    </li>
    <li>
      <strong>Fehlende Rollenklarheit:</strong>
      Unklare Zuständigkeiten. Maßnahme: KI-Verantwortliche:n benennen.
    </li>
    <li>
      <strong>Überlastung:</strong>
      KI „on top" scheitert. Maßnahme: Kleine Piloten mit klarem Umfang.
    </li>
  </ul>

  <h3>2. Daten-, Sicherheits- und Compliance-Risiken</h3>
  <ul>
    <li>
      <strong>Datenkontrolle:</strong>
      Sensible Daten in KI-Systemen. Maßnahme: Richtlinien + Zugriffsbeschränkungen.
    </li>
    <li>
      <strong>Sicherheitslücken:</strong>
      Score {{score_sicherheit}}/100. Maßnahme: Sicherheitskonzept + regelmäßige Reviews.
    </li>
    <li>
      <strong>Rechtliche Verantwortung:</strong>
      Datenschutz/Urheberrecht. Maßnahme: Benannte Zuständigkeit + Leitlinien.
    </li>
    <li>
      <strong>Transparenz:</strong>
      Vertrauensverlust bei unklarer KI-Nutzung. Maßnahme: Hinweise + Dokumentation.
    </li>
  </ul>

  <h3>3. Qualitäts-, Transparenz- und Akzeptanzrisiken</h3>
  <ul>
    <li>
      <strong>Inkonsistente Ergebnisse:</strong>
      Qualitätsstreuung ohne Templates. Maßnahme: Einheitliche Vorlagen + Reviews.
    </li>
    <li>
      <strong>Übervertrauen:</strong>
      Halluzinationen in Kundendokumenten. Maßnahme: Prüfpflicht + Checklisten.
    </li>
    <li>
      <strong>Akzeptanzprobleme:</strong>
      Widerstand bei unklarem Nutzen. Maßnahme: Piloten + Feedback einholen.
    </li>
    <li>
      <strong>Nachvollziehbarkeit:</strong>
      Unklare KI-Rolle. Maßnahme: Dokumentation „Wo unterstützt KI?".
    </li>
  </ul>

  <h3>4. Abhängigkeiten, Betriebs- und Lieferantenrisiken</h3>
  <ul>
    <li>
      <strong>Tool-Abhängigkeit:</strong>
      Vendor Lock-in. Maßnahme: Fallback-Szenarien + Datenexport.
    </li>
    <li>
      <strong>Dienstleister-Regelungen:</strong>
      Lücken in Haftung/SLA. Maßnahme: Klare Verträge + Reaktionszeiten.
    </li>
    <li>
      <strong>Notfallplanung:</strong>
      Kein Wiederanlauf definiert. Maßnahme: Backups + Notfallkontakte.
    </li>
    <li>
      <strong>Tool-Komplexität:</strong>
      Zu viele Parallel-Tools. Maßnahme: Konsolidierung auf Kernlösungen.
    </li>
  </ul>

  <h3>5. Risiko-Matrix – Überblick über zentrale Risiken</h3>
  <p>
    Die folgende Übersicht zeigt die wichtigsten Risikofelder nach Eintrittswahrscheinlichkeit
    und Auswirkungsstärke, um die Priorisierung von Gegenmaßnahmen zu erleichtern.
  </p>
  <table class="table">
    <thead>
      <tr>
        <th>Risikobereich</th>
        <th>Typische Auswirkung</th>
        <th>Eintrittswahrscheinlichkeit</th>
        <th>Auswirkungsstärke</th>
        <th>Empfohlene Schwerpunkt-Maßnahmen</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Strategie & Organisation</td>
        <td>Verzettelung, ausbleibende Wirkung, Frust im Alltag</td>
        <td>mittel</td>
        <td>hoch</td>
        <td>Klares Zielbild, priorisierte Use Cases, benannte Verantwortung für KI.</td>
      </tr>
      <tr>
        <td>Daten & Sicherheit</td>
        <td>Fehlende Transparenz, potenzielle Datenschutz-Verstöße</td>
        <td>mittel bis hoch</td>
        <td>hoch</td>
        <td>Kurzleitlinie für Datennutzung, Zugriffs- und Passwortkonzept, Dokumentation der Dienste.</td>
      </tr>
      <tr>
        <td>Qualität & Akzeptanz</td>
        <td>Uneinheitliche Ergebnisse, Misstrauen oder Blindvertrauen in KI</td>
        <td>mittel</td>
        <td>mittel bis hoch</td>
        <td>Standards für Templates, Review-Loops, verständliche Kommunikation von Nutzen und Grenzen.</td>
      </tr>
      <tr>
        <td>Abhängigkeiten & Betrieb</td>
        <td>Unterbrechungen im Betrieb, Mehrkosten, Lock-in-Effekte</td>
        <td>niedrig bis mittel</td>
        <td>mittel</td>
        <td>Fallback-Szenarien, Konsolidierung der Tool-Landschaft, klare Vereinbarungen mit Dienstleistern.</td>
      </tr>
      <tr>
        <td>KI-spezifisch: Halluzinationen</td>
        <td>Fehlerhafte Informationen in Kundendokumenten, Reputationsschaden</td>
        <td>mittel bis hoch</td>
        <td>hoch</td>
        <td>Vier-Augen-Prinzip, Faktenprüfung, klare Qualitätsrichtlinien für KI-Output.</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    Diese Risikoanalyse zeigt die wichtigsten Handlungsfelder für KI in
    {{OFFERING_LABEL}}. Im nächsten Schritt sollten die Risiken
    nach Eintrittswahrscheinlichkeit und Auswirkung priorisiert werden.
    Details zur Maßnahmenplanung → siehe Roadmap und Governance-Abschnitt.
  </p>
</section>

<!-- DEV: PDF-SLIMDOWN v2.1 - TRUNCATION-FIX: Solo 600-700, Team 800-1000, KMU 1000-1300 Wörter -->
<!-- FINAL CHECK VOR OUTPUT: Zähle deine Wörter. Solo >750? KÜRZEN! Team >1100? KÜRZEN! -->

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
