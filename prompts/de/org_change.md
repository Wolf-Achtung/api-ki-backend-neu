<!-- org_change.md – v4.0 GOLD STANDARD+ (placeholder-frei, validator-sicher)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT. -->

# ORGANIZATIONAL CHANGE – Menschen, Arbeitsweisen & Lernen

## SIZE-AWARENESS (zwingende Regeln)

**Unternehmensgrößen (nur diese drei):**
- `{{COMPANY_SIZE}} = "solo"`  → 1 Person
- `{{COMPANY_SIZE}} = "team"`  → 2–10 Personen
- `{{COMPANY_SIZE}} = "kmu"`   → 11–100 Personen

### SOLO – Regeln
- Fokus: persönliche Arbeitsweise, Selbstorganisation
- Keine Abteilungen, keine Rollenvielfalt, keine Change-Programme
- Kleinstformate: Micro-Trainings, Checklisten, Self-Learning

### TEAM – Regeln
- Fokus: kollaboratives Arbeiten im Kernprozess von {{HAUPTLEISTUNG}}
- 1 Owner + 1–2 Mitwirkende
- Regelmäßige kurze Formate (Show & Tell, Weekly Review)
- Keine großen PMO- oder Change-Strukturen

### KMU – Regeln
- Fokus: Skalierung über mehrere Funktionen/Teams hinweg
- Rollen wie Projektleitung, Fachbereichs-Owner, KI-Owner möglich
- Klar definierte Eskalations- und Entscheidungswege
- Geplante Maßnahmen & geregelte Kommunikation

---

## ZWECK DES PROMPTS

Erstelle eine **praxisnahe, größen- & branchenspezifische Change-Sektion** für:

- Branche: **{{BRANCHE_LABEL}}**
- Größe: **{{UNTERNEHMENSGROESSE_LABEL}}**
- Kernprozess: **{{HAUPTLEISTUNG}}**
- Bundesland: **{{BUNDESLAND_LABEL}}** (nur für Beispiele/Regulatorik)

Die Sektion soll:

1. direkt erklären, **wie KI die Arbeitsweise konkret verändert**,  
2. Rollen, Prozesse, Routinen **klar und ohne Floskeln** darstellen,  
3. Quick-Wins, Pilot-Plan und Governance-Logik **ohne Platzhalter** reflektieren,  
4. einen **konkreten 30/60/90-Tage-Change-Fahrplan** liefern.

---

## VERBOTEN (Hard-Rules)

- Keine Platzhalter wie `{…}` oder `[…]`
- Keine Framework-Namen (Kotter, ADKAR, Lewin, etc.)
- Keine unkonkreten Phrasen wie „Mitarbeitende abholen“, „Kulturwandel starten“
- Keine Begriffe, die nicht zur Größe passen (z. B. „Abteilung“ bei Solo)

---

## OUTPUT-FORMAT  
**Antwort ausschließlich als validen HTML-Block ausgeben:**

```html
<section class="section org-change">
  <h2>Organisation &amp; Change-Management</h2>

  <p>
    Die Einführung von KI in <strong>{{HAUPTLEISTUNG}}</strong> innerhalb der Branche 
    <strong>{{BRANCHE_LABEL}}</strong> verändert Aufgaben, Arbeitsweisen und Verantwortlichkeiten.
    Die folgenden Empfehlungen sind speziell auf <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> 
    abgestimmt und zeigen, wie der Wandel realistisch gelingen kann.
  </p>

  <h3>1. Rollen &amp; Verantwortlichkeiten</h3>
  <ul>
    <li>
      <strong>KI-Owner für den Kernprozess:</strong> 
      Person, die Richtung, Prioritäten und Qualität des KI-Einsatzes verantwortet.
    </li>
    <li>
      <strong>Fachliche Ansprechperson:</strong> 
      definiert Anforderungen, bewertet Ergebnisse, gibt Feedback aus der Praxis.
    </li>
    <li>
      <strong>Technische Unterstützung:</strong> 
      interne IT, externer Partner oder Freelancer – abhängig von {{COMPANY_SIZE}}.
    </li>
  </ul>

  <h3>2. Arbeitsweisen &amp; Prozesse</h3>
  <ul>
    <li>Konkrete Beschreibung, welche Schritte im Prozess {{HAUPTLEISTUNG}} durch KI vereinfacht werden.</li>
    <li>Klare Definition neuer Qualitätsprüfungen, z.&nbsp;B. Vier-Augen-Checks bei kritischen Ergebnissen.</li>
    <li>Etablierung einer einfachen Dokumentation für Prompts, Entscheidungen &amp; Freigaben.</li>
  </ul>

  <h3>3. Lernen &amp; Qualifizierung</h3>
  <ul>
    <li>Kurze Lernformate passend zu {{COMPANY_SIZE}} (z.&nbsp;B. 3×60-Minuten Sessions oder Self-Learning-Module).</li>
    <li>Konkrete Kompetenzfelder: Prompting, Tool-Bedienung, Ergebnisbewertung, Datenschutz.</li>
    <li>Eindeutige Materialien für neue Mitarbeitende oder Freelancer (Checklisten, Mini-Guides).</li>
  </ul>

  <h3>4. Change-Fahrplan 30/60/90 Tage</h3>
  <ol class="next-steps">
    <li>
      <strong>0–30 Tage:</strong> Rollen definieren, Erwartungen klären, 
      ersten KI-Workflow im Alltag testen und wöchentlich Feedback sammeln.
    </li>
    <li>
      <strong>31–60 Tage:</strong> Erfolgreiche Ansätze stabilisieren, 
      interne Regeln &amp; Dokumentation ergänzen, Lernformate durchführen.
    </li>
    <li>
      <strong>61–90 Tage:</strong> Funktionierende Methoden auf weitere Aufgaben/Teams ausweiten,
      Verantwortlichkeiten fest verankern, Ergebnisse für die 12-Monats-Roadmap aufbereiten.
    </li>
  </ol>

  <p class="small muted">
    Hinweis: Die Intensität des Change-Ansatzes soll proportional zur Größe von 
    {{UNTERNEHMENSGROESSE_LABEL}} bleiben – klein starten, schnell testen, 
    Wirkung messen und Schritt für Schritt ausbauen.
  </p>
</section>
