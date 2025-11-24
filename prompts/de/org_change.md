<!-- org_change.md – v2.8 GOLD STANDARD+ SIZE & BRANCHE
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences. -->

# PROMPT: Organizational Change – Menschen, Arbeitsweisen & Lernen

## ⚠️ SIZE-AWARENESS – ABSOLUT PFLICHT!

**Mögliche Unternehmensgrößen (NUR diese 3):**
- `{{COMPANY_SIZE}} = "solo"`  → Label: "1 (Solo-Selbstständig/Freiberuflich)"
- `{{COMPANY_SIZE}} = "team"`  → Label: "2-10 (Kleines Team)"
- `{{COMPANY_SIZE}} = "kmu"`   → Label: "11-100 (KMU)"

### Solo (`solo`)
- Fokus: eigene Arbeitsweise & persönliche Routinen anpassen
- KI als „virtueller Mitarbeiter“ für wiederkehrende Aufgaben
- Lernformate: Self-Learning, kurze Micro-Trainings, Checklisten
- Keine formalen Change-Strukturen, keine Abteilungen

### Team (`team`)
- Fokus: gemeinsamer Umgang mit KI im Kernprozess von {{HAUPTLEISTUNG}}
- Regelmäßige kurze Formate („Show & Tell“, Weekly-Review)
- Klar definierte Verantwortlichkeiten (1 Owner + 1–2 Mitwirkende)
- Keine großen Change-Programme, kein PMO

### KMU (`kmu`)
- Fokus: strukturierter Wandel über mehrere Bereiche
- Rollen wie Projektleitung, Change-Agents, Fachbereichs-Owner
- Geplante Trainings und Kommunikationsmaßnahmen
- Eskalations- und Entscheidungswege klar benennen

---

## 🎯 ZWECK & KONTEXT

Erstelle eine **praxisnahe Organisations- und Change-Seite** für:

- Branche: `{{BRANCHE_LABEL}}`
- Unternehmensgröße: `{{UNTERNEHMENSGROESSE_LABEL}}` (`{{COMPANY_SIZE}}`)
- Hauptleistung: `{{HAUPTLEISTUNG}}`
- Bundesland (für Beispiele/Regulatorik, falls sinnvoll): `{{BUNDESLAND_LABEL}}`

Nutze die bereits empfohlenen Quick Wins, Roadmap‑Schritte und Governance‑Empfehlungen im Hintergrund, aber **ohne** Platzhalter im Text zu nennen.

---

## ⛔ VERBOTEN

- Theoretische Change-Modelle ohne Bezug zum konkreten Vorhaben
- Vage Formulierungen wie „Mitarbeitende abholen“, „Kulturwandel starten“
- Rollen, die nicht zur Größe passen (z. B. „Change Board“ bei Solo/Team)
- Generische Schulungsfloskeln („Mitarbeitende schulen“) ohne Inhalte

---

## ✅ WAS ERWARTET WIRD

1. Klarer Bezug auf {{HAUPTLEISTUNG}} und die dort betroffenen Rollen
2. Konkrete Formulierungen pro Größenklasse (Solo/Team/KMU)
3. Sichtbare Verbindung zu Quick Wins & Roadmap (ohne Platzhalter-Namen)
4. Konkrete 30/60/90‑Tage-Schritte für Veränderung & Qualifizierung

---

## 📝 OUTPUT-FORMAT

Antworte ausschließlich mit **validem HTML** in genau dieser Struktur
(Beispieltexte in eckigen Klammern bitte branchenspezifisch ausformulieren):

```html
<section class="section org-change">
  <h2>Organisation &amp; Change-Management</h2>

  <p>
    Die Einführung von KI in <strong>{{HAUPTLEISTUNG}}</strong> in der Branche
    <strong>{{BRANCHE_LABEL}}</strong> verändert Arbeitsweisen, Rollen und
    Verantwortlichkeiten. Die folgenden Empfehlungen sind auf
    <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> zugeschnitten.
  </p>

  <h3>1. Rollen &amp; Verantwortlichkeiten</h3>
  <ul>
    <li><strong>Owner für KI im Kernprozess:</strong> [konkrete Rolle, z. B. Inhaber, Teamlead, Bereichsleiter]</li>
    <li><strong>Fachliche Ansprechperson:</strong> [Person/Rolle, die Anforderungen sammelt und priorisiert]</li>
    <li><strong>Technische Unterstützung:</strong> [Freelancer, interne IT oder externer Dienstleister – abhängig von {{COMPANY_SIZE}}]</li>
  </ul>

  <h3>2. Arbeitsweisen &amp; Prozesse</h3>
  <ul>
    <li>[Wie ändert sich der tägliche Ablauf im Kernprozess von {{HAUPTLEISTUNG}} konkret?]</li>
    <li>[Welche manuellen Schritte entfallen, welche neuen Qualitätschecks kommen hinzu?]</li>
    <li>[Wie wird dokumentiert, was mit KI gemacht wird (z. B. Prompts, Workflows, Freigaben)?]</li>
  </ul>

  <h3>3. Lernen &amp; Qualifizierung</h3>
  <ul>
    <li>[Konkrete Lernformate passend zu {{COMPANY_SIZE}} – z. B. 3x 60‑Minuten‑Sessions, Self-Learning, interne Mini‑Workshops]</li>
    <li>[Welche Kompetenzen müssen aufgebaut werden (z. B. Prompting, Toolbedienung, Datenschutz)?]</li>
    <li>[Wie wird sichergestellt, dass neue Mitarbeitende/Freelancer schnell startklar sind?]</li>
  </ul>

  <h3>4. Change-Fahrplan 30/60/90 Tage</h3>
  <ol class="next-steps">
    <li><strong>0–30 Tage:</strong> [Pilot-Team/Rollen festlegen, erste Abläufe mit KI testen, Feedbackschleife etablieren]</li>
    <li><strong>31–60 Tage:</strong> [Pilot stabilisieren, Dokumentation &amp; Leitlinien ergänzen, Lernformate durchführen]</li>
    <li><strong>61–90 Tage:</strong> [Funktionierende Ansätze auf weitere Aufgaben/Teams ausrollen, Verantwortlichkeiten verankern]</li>
  </ol>

  <p class="small muted">
    Hinweis: Passen Sie Intensität und Formalität des Change-Ansatzes immer an
    Ihre tatsächliche Größe und Ressourcen an – lieber klein starten und
    konsequent durchziehen als ein überdimensioniertes Programm aufsetzen.
  </p>
</section>
