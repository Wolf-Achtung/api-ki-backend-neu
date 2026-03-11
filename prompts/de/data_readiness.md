## ABSOLUTE LÄNGENREGEL (VOR ALLEM ANDEREN!)
{% if COMPANY_SIZE == "solo" %}
**SOLO-HARD-LIMIT: Maximal 400 Wörter / 3.000 Zeichen HTML gesamt.**
Alle 4 Unterabschnitte behalten, aber kompakt: je max. 3 Bullets à 1 Satz.
{% elif COMPANY_SIZE == "team" %}
**TEAM-HARD-LIMIT: Maximal 700 Wörter / 6.500 Zeichen HTML gesamt.**
{% else %}
**KMU-HARD-LIMIT: Maximal 900 Wörter / 8.500 Zeichen HTML gesamt.**
{% endif %}
JEDES WORT ÜBER DEM LIMIT WIRD BRUTAL ABGESCHNITTEN — der Report endet dann mitten im Satz!

Developer: <!-- data_readiness.md – v3.3 TRUNCATION-FIX (Daten & Systemreife, multi-size) – SPRINT N1
  Antworte ausschließlich mit validem HTML.
  KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

  ZIEL:
  - Eine klare, praxisnahe Einschätzung zu Datenlage und Systemreife für KI liefern:
    * Wo stehen Daten, Tools und Prozesse heute?
    * Was ist bereits ausreichend für KI-Piloten?
    * Welche Lücken sollten in den nächsten 6–12 Monaten geschlossen werden?

  SPRINT N1 - TEMPLATE-PHRASEN VERMEIDEN:
  - KEINE generischen Einleitungen wie "Dieser Abschnitt fasst zusammen..."
  - KEINE redundanten Verweise auf andere Abschnitte in der Einleitung
  - DIREKT mit branchenspezifischem Kontext beginnen
  BRANCHENBEZEICHNUNG-REGEL:
  Die Branchenbezeichnung "{{BRANCHE_LABEL}}" darf MAXIMAL 2x im gesamten Text vorkommen.
  Ab der 3. Verwendung NUR noch Kurzformen: "Ihr Unternehmen", "Ihre Branche", "Ihr Geschäftsfeld".

  ANTI-REDUNDANZ (RUN-622 - KRITISCH):
  - Verwende KEINE Textbausteine, die in anderen Sections vorkommen könnten
  - Vermeide Wiederholung von: ROI-Zahlen, Payback-Werten, Branchenbeschreibungen, Tool-Listen
  - Jeder Absatz muss EINZIGARTIG für Datenreife sein — nicht recycelbar für Risks/Governance/Tools
  - Statt "Das Unternehmen aus der Branche X..." → direkt zur Datenlage: "Die vorhandenen Datenquellen..."
  - KEINE Aufzählung von Tools die bereits im Tools-Abschnitt stehen — stattdessen BEWERTUNG der Datenqualität

  VERFÜGBARE VARIABLEN (Labels/Nutzereingaben aus dem Fragebogen):
  - {{BRANCHE_LABEL}}
  - {{UNTERNEHMENSGROESSE_LABEL}}
  - {{HAUPTLEISTUNG}}
  - {{IT_INFRASTRUKTUR_LABEL}}          → z. B. "Cloudbasiert", "lokal", "Mischform"
  - {{PROZESSE_PAPIERLOS_LABEL}}        → Digitalisierungsgrad der Abläufe
  - {{AUTOMATISIERUNGSGRAD_LABEL}}      → Einschätzung Automatisierungsgrad
  - {{DATENQUELLEN_LABELS}}             → Liste typischer Datenquellen (CRM, ERP, Tickets etc.)
  - {{VORHANDENE_TOOLS_LABELS}}         → Liste vorhandener Tools/Plattformen (z. B. M365, CRM, DMS)
  - {{REGULIERTE_BRANCHE_LABELS}}       → Hinweise auf Regulierung (z. B. Gesundheitsdaten)
  - {{DATENQUELLEN_LABELS}} kann leer oder sehr kurz sein. Dann mit typischen Quellen für Branche/Größe arbeiten.

  GRÖSSENLOGIK:
  - "1 (Solo":
      * Daten oft verstreut in wenigen Tools (E-Mail, Office, einfache SaaS-Tools).
      * Fokus: Ordnung schaffen, einfache Standards, möglichst wenig Overhead.
  - "2–10":
      * Kleine Tool-Landschaft, aber erste Rollen-/Zugriffslogik.
      * Fokus: einheitliche Ablage, saubere Rechte, einfache Datenpipelines.
  - "11–100":
      * Mehrere Systeme/Abteilungen, ggf. Schatten-IT.
      * Fokus: verbindliche Daten-Governance, Schnittstellen, Rollen und Verantwortlichkeiten.

  REGELN:
  - Keine Hinweise auf Fragebogen/Fragen, keine technischen Platzhaltertexte.
  - Immer so schreiben, als würde die Einschätzung direkt an Geschäftsführung/Projektleitung gehen.
  - Klarer, nüchterner Ton: Chancen + Risiken, keine Übertreibungen.

  SPRINT G18 - ANTI-REDUNDANZ (STRIKT!):
  - ROI/Investitionen/Business Case NICHT erneut erwähnen – diese Themen gehören in business_case.md
  - Maximal EIN kurzer Verweis auf den Business Case ist erlaubt (z.B. "→ siehe Business Case")
  - CAPEX/OPEX-Blöcke gehören NICHT hierher
  - Fokus: Datenqualität, Systemreife, Datenquellen – KEINE Finanzperspektive

  FIX-629 - DEDUPLIZIERUNG (STRIKT!):
  - KEINE wiederholten Textbausteine oder Standardfloskeln in verschiedenen Abschnitten.
  - Jeder Absatz und jeder Listenpunkt muss einzigartige, neue Information enthalten.
  - Wiederhole NICHT dieselbe Aussage in unterschiedlicher Formulierung.
  - Wenn ein Punkt bereits gemacht wurde, erwähne ihn NICHT erneut.
  - Vermeide generische Wiederholungen wie "solide Basis für KI" oder "KI-Pilotprojekte starten".
  - Jeder Unterabschnitt (Stärken, Lücken, Empfehlungen) muss klar abgegrenzte Inhalte haben.

  THEMEN-OWNERSHIP (verbindlich):
  - Diese Section: NUR Datenlage, Systemreife, Datenqualität, Schnittstellen, Daten-Governance
  - NICHT hier: KI-Pilotprojekte starten (→ roadmap_90d)
  - NICHT hier: Governance/Rollen (→ ai_policy_mini, org_change)
  - NICHT hier: Tool-Empfehlungen (→ tools_empfehlungen)
  - NICHT hier: Compliance/AI Act (→ ai_act_summary)
  - NICHT hier: Change-Management, Lernkultur, Widerstände, Schulung (→ org_change)
  - NICHT hier: Arbeitsroutinen, Rollenverteilung, Feedback-Kultur (→ org_change)
  - Querverweis-Format: "→ siehe [Section-Name]"

  ABGRENZUNG ZU ORG_CHANGE (STRIKT!):
  - DATA_READINESS = WO stehen Daten und Systeme? (Technik, Infrastruktur, Qualität)
  - ORG_CHANGE = WIE gelingt der Wandel? (Menschen, Prozesse, Akzeptanz)
  - Überlappungsgefahr: "Standards einführen" → hier NUR Daten-Standards (Benennung, Ablage)
  - ORG_CHANGE kümmert sich um Arbeits-Standards (Routinen, Review-Zyklen, Rollen)
-->

<section class="section data-readiness">
  <h2>Datenlage & Systemreife für KI</h2>

  <p>
    In <strong>{{BRANCH_CONTEXT_LABEL}}</strong> basiert erfolgreiche KI-Implementierung auf
    einer soliden Datenbasis. Die vorhandenen Datenquellen, Strukturen und Schnittstellen sind
    der Ausgangspunkt für erste KI-Workflows – und zeigen gleichzeitig, wo gezielt nachgebessert werden sollte.
  </p>

  <h3>Wo heute Daten und Systeme liegen</h3>
  <p>
    Aktuell werden Informationen überwiegend in folgenden Systemen verarbeitet:
    <strong>{{DATENQUELLEN_LABELS}}</strong> sowie in den eingesetzten Tools
    <strong>{{VORHANDENE_TOOLS_LABELS}}</strong>.
    Die IT-Infrastruktur ist <strong>{{IT_INFRASTRUKTUR_LABEL}}</strong>, der
    Digitalisierungsgrad der Abläufe wird als <strong>{{PROZESSE_PAPIERLOS_LABEL}}</strong>
    mit einem Automatisierungsgrad von <strong>{{AUTOMATISIERUNGSGRAD_LABEL}}</strong> beschrieben.
  </p>

  <ul>
    <li>Für ein {{UNTERNEHMENSGROESSE_LABEL}}-Unternehmen sind die genutzten Systeme typisch und ausreichend, um erste KI-Pilotprojekte zu starten.</li>
    <li>Gleichzeitig fehlen teilweise durchgängige Datenketten – z.&nbsp;B. zwischen Lead-Gewinnung, Angebotserstellung und Leistungserbringung.</li>
    <li>In regulierten Bereichen ({{REGULIERTE_BRANCHE_LABELS}}) müssen Datenschutz, Aufbewahrung und Zugriffsrechte gezielt mitgedacht werden.</li>
  </ul>

  <h3>Stärken der aktuellen Datenbasis</h3>
  <ul>
    <li>Relevante Informationen liegen bereits digital vor (z.&nbsp;B. in {{VORHANDENE_TOOLS_LABELS}}), was KI-Prototypen mit realen Daten ermöglicht.</li>
    <li>Viele Prozesse folgen wiederkehrenden Mustern, die sich gut für KI-gestützte Automatisierung eignen.</li>
    <li>Die bestehende Infrastruktur {{IT_INFRASTRUKTUR_LABEL}} erlaubt es, neue KI-Tools ohne große Vorlaufzeit zu testen.</li>
  </ul>

  <h3>Typische Lücken & Risiken</h3>
  <ul>
    <li>Daten sind häufig auf mehrere Systeme verteilt, ohne einheitliche Struktur oder zentrale „Single Source of Truth“.</li>
    <li>Prozessschritte werden nicht immer konsequent dokumentiert, was die Nachvollziehbarkeit für KI-Modelle einschränkt.</li>
    <li>Regeln für Datenzugriff, Löschung und Aufbewahrung sind teilweise unklar oder nur mündlich vereinbart.</li>
  </ul>

  <h3>Empfohlene Schritte in den nächsten 6–12 Monaten</h3>
  <ol>
    <li><strong>Datenlandkarte erstellen:</strong> Übersicht über alle relevanten Datenquellen und Systeme, inkl. Verantwortlichen und Datenqualität.</li>
    <li><strong>Standard für Ablage & Benennung definieren:</strong> Einfache, aber verbindliche Regeln, die zu {{UNTERNEHMENSGROESSE_LABEL}} passen.</li>
    <li><strong>Datenschutz & Zugriffsrechte klären:</strong> Zuständigkeiten, Rollen und Freigaben für KI-Nutzung festlegen – besonders in regulierten Bereichen.</li>
    <li><strong>Pilotfähigen Datenschnitt identifizieren:</strong> Einen Prozess auswählen, bei dem Daten bereits vollständig und strukturiert vorliegen — als Grundlage für den 90-Tage-Fahrplan.</li>
  </ol>

  <p class="small muted">
    Für eine nachhaltige KI-Nutzung sollten Datenstruktur und -qualität
    schrittweise verbessert werden. Konkrete Umsetzungsschritte
    → siehe 90-Tage-Fahrplan.
  </p>
</section>

     - 1 Einleitung, 4 Unterabschnitte (Status, Stärken, Lücken, nächste Schritte).
     - Pro Listenpunkt maximal 2 kurze Sätze.
     - Schreibe direkt finalen, kundentauglichen Inhalt. -->
