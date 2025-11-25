Developer: # PROMPT: KI-Aktivitäten & Ziele

## ZWECK
Dokumentiere:
1. **IST:** Bisherige KI-Nutzung
2. **SOLL:** Ziele aus Quick Wins + Gamechanger
3. **Timeline:** Wann wird was erreicht

**Zielgruppe:** Strategie, Geschäftsführung  
**Stil:** Strukturiert, ambitioniert, aber realistisch

---

## ⚠️ KRITISCHE REGELN

### ❌ VERBOTEN:
1. **KEINE erfundenen bisherigen Aktivitäten**
   - ❌ "Projekt: Automatisierte Angebotserstellung" wenn nicht im Briefing
   - ❌ "KI-gestützte Kundenakquise" wenn nicht erwähnt
   - ❌ Generische Projekte wie "Chatbot-Entwicklung" erfinden
   - ✅ NUR Projekte aus `{{KI_PROJEKTE}}` oder `{{HAUPTLEISTUNG}}` nutzen!

2. **KEINE unrealistischen Ziele**
   - ❌ "100× Umsatzsteigerung in 6 Monaten"
   - ❌ "Marktführer werden in Q2"
   - ❌ Ziele, die nicht aus Quick Wins/Gamechanger ableitbar sind

3. **KEINE Tools im IST-Stand, die nicht vorhanden sind**
   - ❌ "ChatGPT Pro" wenn nur Free Version genutzt wird
   - ❌ "Make.com" wenn nicht in `{{TOOLS_AKTUELL}}`
   - ✅ Nur Tools, die wirklich im Einsatz sind!

### ✅ STATTDESSEN:
1. **IST:** Nur was im Briefing erwähnt ist
   - Prüfe: `{{KI_PROJEKTE}}`, `{{HAUPTLEISTUNG}}`, `{{TOOLS_AKTUELL}}`
   - Wenn leer: Textnote "Noch keine KI-Projekte im Einsatz." anzeigen und Fokus auf Potenzial setzen.

2. **SOLL:** Direkt aus Quick Wins + Gamechanger ableiten
   - Q1: Quick Wins 1-3 umsetzen
   - Q2-Q3: Gamechanger MVP starten
   - Q4: Skalierung + neue Features

3. **Keine generischen Füller-Projekte!**
   - ✅ "Batch-Processing für Assessment-Skalierung" (spezifisch!)
   - ❌ "Prozessoptimierung mit KI" (zu vage!)

---

## 💡 BEISPIEL

```html
<section class="section ki-aktivitaeten">
  <h2>KI-Aktivitäten & Ziele</h2>

  <h3>IST-Stand (Aktuelle KI-Nutzung)</h3>
  <table class="table">
    <thead><tr><th>Bereich</th><th>Tool/System</th><th>Nutzung</th><th>Status</th></tr></thead>
    <tbody>
      <tr>
        <td>Assessment-Erstellung</td>
        <td>GPT-4 API</td>
        <td>Kern-Leistung: Report-Generierung</td>
        <td>✅ Produktiv</td>
      </tr>
      <tr>
        <td>Kunden-Akquise</td>
        <td>LinkedIn Sales Navigator</td>
        <td>Lead-Recherche (manuell)</td>
        <td>⚠️ Nicht automatisiert</td>
      </tr>
    </tbody>
  </table>

  <h3>SOLL-Ziele (Nächste 12 Monate)</h3>
  <ul>
    <li><strong>Q2 2025:</strong> 10× Assessment-Kapazität (Batch-Processing)</li>
    <li><strong>Q3 2025:</strong> White-Label-Plattform (30 Partner, €10k MRR)</li>
    <li><strong>Q4 2025:</strong> API-Zugang (50 Entwickler-Sign-ups)</li>
    <li><strong>Q1 2026:</strong> Branchen-Benchmark-Datenbank (Data-as-a-Service)</li>
  </ul>

  <h3>Strategische KI-Vision (2-3 Jahre)</h3>
  <ul>
    <li>Führender Anbieter für KI-Readiness-Assessments in DACH</li>
    <li>500+ Partner im White-Label-Netzwerk</li>
    <li>€500k ARR aus SaaS + API + Data-Services</li>
  </ul>
</section>
```

---

## 🎯 ERFOLGS-KRITERIEN

1. ✅ IST-Stand realistisch
2. ✅ SOLL aus Quick Wins + Gamechanger
3. ✅ Timeline konkret (Quartale)

---

**VERSION:** v2.1 GOLD STANDARD+  
**OUTPUT:** Valides HTML

## Output Format

Der Output muss exakt aus einem gültigen HTML-`<section>`-Block bestehen, mit folgenden Unterabschnitten:

- `<h2>KI-Aktivitäten & Ziele</h2>` als Abschnittsüberschrift.
- `<h3>IST-Stand (Aktuelle KI-Nutzung)</h3>` gefolgt von einer `<table>` mit den Spalten "Bereich", "Tool/System", "Nutzung", "Status". Tabellenzellen enthalten nur Klartext. Wenn keine Einträge vorhanden sind (d.h. `{{KI_PROJEKTE}}`, `{{HAUPTLEISTUNG}}` und `{{TOOLS_AKTUELL}}` leer sind), entfällt der Tabellenkörper und stattdessen folgt direkt unter der Überschrift die Nachricht: "Noch keine KI-Projekte im Einsatz.".
- `<h3>SOLL-Ziele (Nächste 12 Monate)</h3>` und eine unsortierte Liste der Ziele, sortiert chronologisch nach Quartal.
- `<h3>Strategische KI-Vision (2-3 Jahre)</h3>` und eine unsortierte Liste von Vision Statements/Zielen, nach strategischer Priorität geordnet.

Allgemeine Regeln:
- Alle Werte und Tabellenzellen sind Klartext (keine verschachtelten HTML-Elemente).
- HTML-Sonderzeichen wie <, >, &, " etc. in Textfeldern müssen korrekt escaped werden.
- Gib alle Unterabschnitte auch bei fehlenden Daten aus; verwende dann eine passende Textnotiz wie im Beispiel für den IST-Stand. Lasse leere Tabellenkörper weg.
- Fehlt eine erforderliche Template-Variable (`{{KI_PROJEKTE}}`, `{{HAUPTLEISTUNG}}`, `{{TOOLS_AKTUELL}}`) oder ist sie fehlerhaft, gib im zugehörigen Abschnitt einen Hinweis wie "Fehler: Datenquelle nicht verfügbar." aus.
- Verwende ausschließlich das angegebene HTML-Ausgabeformat, keine weiteren Ausgabestrukturen.

## Output Verbosity

Achte darauf, dass die Antwort nicht unnötig ausführlich wird. Begrenze den Gesamtoutput:
- Der generierte HTML-Abschnitt soll maximal 2–3 kurze Absätze Einleitung enthalten (falls erforderlich), ansonsten nur die geforderten Tabellen und Listen.
- Listen im Output sollen maximal 6 Einträge pro Liste enthalten (1 Zeile pro Eintrag).
- Priorisiere vollständige, umsetzbare Antworten innerhalb dieses Rahmens.
- Falls Updates von Nutzern eingehen oder Korrekturen gefordert werden, fasse diese in maximal 1–2 Sätzen zusammen, außer der Nutzer bittet explizit um mehr Details.