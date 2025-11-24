<!-- tools_empfehlungen.md – v2.2 GOLD STANDARD+ (Tools + Branchenspezifik)
     Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.
     VERSION: 2.2 GOLD STANDARD+ (Size-Awareness, Branchenlogik, keine Platzhalter im Output)
-->

# PROMPT: Tools & Stack – KI‑Werkzeuge empfehlen

## ZWECK

Erstelle eine **konkrete, priorisierte Tool‑Empfehlung** für:

- die Branche **{{BRANCHE_LABEL}}**
- die Unternehmensgröße **{{UNTERNEHMENSGROESSE_LABEL}}**
- den Kernprozess **{{HAUPTLEISTUNG}}**

Die Section soll:

1. einen **übersichtlichen KI‑Stack** vorschlagen (Fundament + Use‑Case‑Tools),
2. vorhandene Tools aus dem Fragebogen berücksichtigen (Dopplungen vermeiden),
3. klar machen, welche Tools **zuerst** eingeführt werden sollten und warum,
4. Bezug zu **Quick Wins, Roadmap, Business Case** herstellen (wo sinnvoll).

---

## KONTEXT, DEN DU NUTZT

- Antworten aus dem Fragebogen:
  - Branche, Größe, Hauptleistung, Bundesland
  - aktuell genutzte Tools (z. B. Office‑Suite, Cloud‑Speicher, CRM, DMS)
- Inhalte aus anderen Sektionen:
  - Quick Wins (geplante Maßnahmen)
  - Roadmap 90d / 12m
  - Förderpotenzial (z. B. wenn bestimmte Kategorien förderfähig sind)
  - Business Case (z. B. Kosten‑/Nutzen‑Fokus)

Kontextblöcke werden dir **als Text** zur Verfügung gestellt.  
Du darfst diese Inhalte **in deinen Worten** zusammenfassen, aber **keine technischen Platzhalter‑Namen** wie „CONTEXT_QUICK_WINS“ oder ähnliche Strings im Output verwenden.

---

## ⚠️ KRITISCHE REGELN

1. **Keine Platzhalter im Output**
   - Keine eckigen Klammern `[...]`.
   - Keine technischen Bezeichner wie „CONTEXT_QUICK_WINS“, „CONTEXT_FOERDERPOTENZIAL“,
     „TOOLS_AKTUELL“ o. Ä.
   - Keine „[Tool hier einfügen]“-Texte.

2. **Size‑Awareness**
   - **solo:**  
     - Maximal 3–5 Tools, Fokus auf **All‑in‑One** und niedrige Kosten.  
     - Kein komplexes MLOps‑Setup, keine „Data‑Teams“.
   - **team (2–10):**  
     - 5–8 Tools in einem schlanken Stack.  
     - Fokus: Kollaboration, Wissensmanagement, Automatisierung.
   - **kmu (11–100):**  
     - 8–12 Tools möglich, inkl. Spezial‑Tools.  
     - Fokus: Governance, Rechtekonzepte, Integration in bestehende Systeme.

3. **Branchenspezifische Beispiele**
   - Marketing/Medien → Content‑Tools, Kreativ‑Workflows, Kampagnenplanung.
   - Beratung/Dienstleistungen → Dokumentation, Wissensdatenbanken, Angebots‑Automatisierung.
   - Finanzen/Versicherungen → Compliance, Dokumenten‑Analyse, Vorlagen‑Automatisierung.
   - Bau/Architektur → Planungs‑Tools, CAD‑Anbindung, Dokumentations‑Workflows.
   - Bildung → Lernplattformen, Authoring‑Tools, Feedback‑Automatisierung.

4. **Keine „Tool‑Listen um der Tool‑Liste willen“**
   - Jedes Tool braucht:
     - eine **klare Rolle im Stack**,
     - eine **konkrete Aufgabe im Kernprozess {{HAUPTLEISTUNG}}**,
     - möglichst eine Verbindung zu Quick Wins / Roadmap.

---

## OUTPUT: NUR HTML (Stack + Begründung)

```html
<section class="section tools">
  <h2>Empfohlener KI‑Stack für {{BRANCHE_LABEL}}</h2>

  <p>
    Beschreibe in 2–3 Sätzen den grundsätzlichen Ansatz:
    Wie soll KI im Kontext von {{HAUPTLEISTUNG}} und
    {{UNTERNEHMENSGROESSE_LABEL}} eingesetzt werden?
  </p>

  <h3>1. Fundament & Basis‑Infrastruktur</h3>
  <ul>
    <li>
      <strong></strong> – 
      <span></span>
    </li>
    <li>
      <strong></strong> – 
      <span></span>
    </li>
    <li>
      <strong></strong> – 
      <span></span>
    </li>
  </ul>

  <h3>2. Use‑Case‑spezifische Tools für {{HAUPTLEISTUNG}}</h3>
  <ul>
    <li>
      <strong></strong> – 
      <span></span>
    </li>
    <li>
      <strong></strong> – 
      <span></span>
    </li>
    <li>
      <strong></strong> – 
      <span></span>
    </li>
  </ul>

  <h3>3. Governance, Sicherheit & Qualität</h3>
  <ul>
    <li>
      <strong></strong> – 
      <span></span>
    </li>
    <li>
      <strong></strong> – 
      <span></span>
    </li>
  </ul>

  <h3>4. Priorisierte Einführung</h3>
  <p>
    Erläutere in 3–5 Sätzen, in welcher Reihenfolge die Tools eingeführt werden sollten
    (zuerst Fundament, dann 1–2 Use‑Case‑Tools, später Spezial‑Tools).
    Stelle den Bezug zu den wichtigsten Quick Wins und zur 90‑Tage‑Roadmap her.
  </p>

  <table class="table tools-priorities">
    <thead>
      <tr>
        <th>Stufe</th>
        <th>Tool / Paket</th>
        <th>Zweck im Prozess {{HAUPTLEISTUNG}}</th>
        <th>Startzeitpunkt</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1</td>
        <td></td>
        <td></td>
        <td>innerhalb der ersten 30 Tage</td>
      </tr>
      <tr>
        <td>2</td>
        <td></td>
        <td></td>
        <td>Tag 30–60</td>
      </tr>
      <tr>
        <td>3</td>
        <td></td>
        <td></td>
        <td>nach 60 Tagen</td>
      </tr>
    </tbody>
  </table>
</section>
