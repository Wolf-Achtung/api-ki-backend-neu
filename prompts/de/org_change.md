Developer: <!-- org_change.md – v4.0 GOLD STANDARD+ (validator-sicher, keine Platzhalter). Antworte ausschließlich mit validem HTML. KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT. -->

<!-- Plan First: Begin with einer knappen Aufgaben-Checkliste (3–7 Punkte, konzeptionell) zu deiner Vorgehensweise, bevor du mit der eigentlichen Arbeit startest. Beispiel: (1) Eingaben analysieren, (2) Größenlogik anwenden, (3) Sektion branchenspezifisch ausarbeiten, (4) Fahrplan anpassen. -->

# ORGANISATIONALER WANDEL – Menschen, Arbeitsweisen & Lernen

## GRÖSSENBEZOGENE REGELN

**Definierte Unternehmensgrößen:**
<ul>
  <li><code>{{COMPANY_SIZE}} = "solo"</code> → 1 Person</li>
  <li><code>{{COMPANY_SIZE}} = "team"</code> → 2–10 Personen</li>
  <li><code>{{COMPANY_SIZE}} = "kmu"</code> → 11–100 Personen</li>
</ul>

### SOLO – Vorgaben
<ul>
  <li>Fokus: individuelle Arbeitsweise und Selbstorganisation</li>
  <li>Keine Abteilungen, keine differenzierten Rollen, keine Change-Programme</li>
  <li>Formate: Micro-Trainings, Checklisten, Self-Learning</li>
</ul>

### TEAM – Vorgaben
<ul>
  <li>Fokus: gemeinsames Arbeiten am Kernprozess <code>{{HAUPTLEISTUNG}}</code></li>
  <li>Typischerweise 1 Owner und 1–2 Mitwirkende</li>
  <li>Regelmäßige kurze Formate wie Show & Tell, Weekly Review</li>
  <li>Keine komplexen Projekt- oder Change-Strukturen</li>
</ul>

### KMU – Vorgaben
<ul>
  <li>Fokus: Skalierung über mehrere Funktionen und Teams</li>
  <li>Mögliche Rollen: Projektleitung, Fach-Owner, KI-Owner</li>
  <li>Klare Kommunikations- und Entscheidungswege</li>
  <li>Geplante Maßnahmen, strukturierte Kommunikation</li>
</ul>

---

## ZIEL DES PROMPTS

Stelle eine praxiskurze, nach Unternehmensgröße und Branchen konzipierte Change-Sektion bereit für:
<ul>
  <li>Branche: <strong>{{BRANCHE_LABEL}}</strong></li>
  <li>Größe: <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong></li>
  <li>Kernprozess: <strong>{{HAUPTLEISTUNG}}</strong></li>
  <li>Bundesland: <strong>{{BUNDESLAND_LABEL}}</strong> (nur falls für Beispiele/Regulatorik erforderlich)</li>
</ul>

Anforderungen an die Sektion:
<ol>
  <li>Konkrete Erläuterung, wie KI den Arbeitsalltag verändert</li>
  <li>Klare, floskelarme Darstellung von Rollen, Prozessen und Routinen</li>
  <li>Direkte, konkrete Quick-Wins, Pilotplan und Governance-Logik ohne Platzhalter</li>
  <li>Klarer 30/60/90-Tage-Change-Fahrplan</li>
</ol>

---

## VERBOTEN (Strenge Regeln)
<ul>
  <li>Keine Platzhalter wie <code>{...}</code> oder <code>[...]</code></li>
  <li>Keine Framework-Namen (z.B. Kotter, ADKAR, Lewin)</li>
  <li>Keine unkonkreten Phrasen wie „Mitarbeitende abholen“ oder „Kulturwandel“ verwenden</li>
  <li>Verwende nur angemessene Begriffe gemäß Größe (z. B. keine „Abteilung“ bei Solo)</li>
</ul>

---

## AUSGABESTRUKTUR

Antwort muss ausschließlich als valider HTML-Block im folgenden Format erfolgen. Passe die Abschnitte strikt an die jeweilige Unternehmensgröße an:
<ul>
  <li>Für <strong>solo</strong>: Keine Rollenvielfalt. Alle Inhalte individualisiert und auf Selbstorganisation einer Person bezogen. Keine Begriffe wie Team, Abteilung, Owner etc.</li>
  <li>Für <strong>team</strong>: Maximal ein Owner und 1–2 Mitwirkende. Keine komplexen Rollen oder Hinweise auf größere Strukturen.</li>
  <li>Für <strong>kmu</strong>: Differenzierte Rollen, strukturierte Prozesse sind möglich.</li>
</ul>

Außerdem:
<ul>
  <li>Keine Platzhalter wie <code>{{...}}</code>, <code>[...]</code> im Output. Variablen immer mit konkreten Werten befüllen. Bei fehlenden Werten valide HTML-Fehlermeldung im gleichen Format ausgeben.</li>
  <li>Der Output muss streng der HTML-Struktur entsprechen. Inhalte der Abschnitte müssen die Größenregeln einhalten.</li>
</ul>

<!-- Post-action Validation: Nach jeder wesentlichen Ausgabe kurz validieren, ob die HTML-Struktur und die Größenlogik korrekt eingehalten wurden. Bei Fehlern sofort minimal selbstkorrigieren oder Fehlermeldung generieren. -->

<!-- Agentic Balance: Arbeite autonom entlang der Checkliste. Bei fehlenden oder widersprüchlichen Eingaben stoppe und gib eine passende HTML-Fehlermeldung gemäß Format aus. Vermeide Annahmen bei fehlenden Variablen. -->

### STRUKTURBEISPIEL

<section class="section org-change">
  <h2>Organisation & Change-Management</h2>
  <p>Die Einführung von KI in <strong>[Kernprozess]</strong> innerhalb der Branche <strong>[Branche]</strong> verändert Aufgaben, Arbeitsweisen und Verantwortlichkeiten. Die folgenden Empfehlungen sind speziell auf <strong>[Unternehmensgröße]</strong> abgestimmt und zeigen, wie der Wandel realistisch gelingen kann.</p>
  <h3>1. Rollen & Verantwortlichkeiten</h3>
  <ul>
    <li>Für solo: „Ich übernehme selbst alle Entscheidungen und die Umsetzung der KI-Integration.“</li>
    <li>Für team: „Eine Person steuert (Owner), 1–2 Mitwirkende unterstützen gezielt.“</li>
    <li>Für kmu: Differenzierte Rollen sind möglich.</li>
  </ul>
  <h3>2. Arbeitsweisen & Prozesse</h3>
  <ul>...</ul>
  <h3>3. Lernen & Qualifizierung</h3>
  <ul>...</ul>
  <h3>4. Change-Fahrplan 30/60/90 Tage</h3>
  <ol class="next-steps">...</ol>
  <p class="small muted">Hinweis: Der Veränderungsumfang richtet sich nach der Größe: Solo – minimalistisch, Team – pragmatisch, KMU – strukturiert.</p>
</section>

### FEHLERFALL

Fehlt eine notwendige Angabe (Branche, Größe, Kernprozess o.ä.), antworte wie folgt:

<section class="section org-change-error">
  <p>Organisations-Change-Ausgabe nicht möglich: Fehlender Wert für <strong>[fehlende Variable]</strong>. Bitte Eingabe prüfen.</p>
</section>