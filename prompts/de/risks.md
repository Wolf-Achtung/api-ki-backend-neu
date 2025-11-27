
---

## 2) `prompts/de/risks.md` – RISKS (Risiken & Gegenmaßnahmen) – Solo-ready

```markdown
Developer: # Risks & Mitigation – Risiken & Gegenmaßnahmen
<!--
Zweck: Erzeuge eine Risiko-Matrix (5–8 Risiken) für den KI-Status-Report.
Fokus: Konkrete, score-basierte Risiken mit umsetzbaren Gegenmaßnahmen.
Gold-Ziele:
- Spezifisch für {{HAUPTLEISTUNG}} und {{BRANCHE_LABEL}}
- Größenbewusst (Solo vs. Team vs. KMU)
- Keine Platzhalter, kein "Content wird erstellt"
- Keine Verwendung des Wortes "Freitextfeld" (oder Varianten); nutze "offene Textantworten" o. Ä.
-->

## Zweck

Erstelle eine Risiko-Matrix (5–8 Einträge), die:

1. **konkrete Risiken** für {{HAUPTLEISTUNG}} identifiziert (keine generischen Phrasen),
2. **Wahrscheinlichkeit** & **Auswirkung** realistisch einschätzt – basierend auf den Scores  
   `{{score_governance}}` und `{{score_sicherheit}}`,
3. **klare Gegenmaßnahmen** beschreibt, die für {{UNTERNEHMENSGROESSE_LABEL}} umsetzbar sind,
4. score-basierte Risiken bewusst priorisiert (z. B. Governance < 60 → DSGVO-Risiko).

Zielgruppe: Geschäftsführung / Inhaber:in, ggf. Risk-Owner oder Compliance-Verantwortliche.  
Stil: Sachlich, ruhig, lösungsorientiert – keine Panikmache.

---

## Größenlogik (Solo / Team / KMU)

Nutze die Variable `{{UNTERNEHMENSGROESSE_LABEL}}` für Tonalität und Maßnahmen:

- **Solo (Label enthält „Solo“)**  
  - Schreibe aus Perspektive einer einzelnen verantwortlichen Person.  
  - Vermeide Begriffe wie „Abteilung“, „IT-Abteilung“, „HR-Abteilung“, „Fachabteilung“.  
  - Gegenmaßnahmen: Fokus auf pragmische Schritte mit vertretbarem Aufwand (z. B. Standard-Checkliste, einfache Backups, externe Beratung „auf Abruf“).

- **Kleines Team (2–10)**  
  - Du darfst von „Team“, „Kolleg:innen“ und „gemeinsamen Standards“ sprechen.  
  - Gegenmaßnahmen können kleine Rollenaufteilungen enthalten (z. B. „eine Person für Datenschutz“, „eine Person für Tool-Administration“).

- **KMU (11–100)**  
  - Du kannst zusätzlich Rollen wie „IT-Verantwortliche:r“, „Datenschutz-Ansprechperson“ verwenden.  
  - Trotzdem keine Konzernbegriffe und keine Annahme mehrerer Hierarchieebenen.

---

## ⚠️ Kritische Regeln

### ❌ Verboten

1. **Generische Risiken:**
   - „Mangelnde Akzeptanz bei Mitarbeitern“
   - „Unzureichende Ressourcen“
   - „Technische Probleme möglich“

2. **Vage Gegenmaßnahmen:**
   - „Regelmäßig überwachen“
   - „Schulungen durchführen“
   - „Prozesse optimieren“

3. **Überdramatisierung:**
   - Wahrscheinlichkeit „Hoch“ für seltene Events ohne Beleg.
   - Auswirkung „Kritisch“ für kleine, leicht kompensierbare Themen.

4. **Verbotene Begriffe / Muster:**
   - Das Wort „Freitextfeld“ bzw. Varianten davon.  
     Verwende stattdessen Formulierungen wie „offene Textantworten“ oder „freie Beschreibungen“.
   - Bei Solo-Unternehmen: keine „Abteilung“, „Abteilungsleitung“, „Fachabteilung“ usw.

### ✅ Stattdessen

1. **Spezifische Risiken für {{HAUPTLEISTUNG}}:**
   - z. B. „Fehlinterpretation offener Textantworten im Fragebogen führt zu falscher Reifegrad-Einstufung.“
   - „Fehlende Dokumentation von Prompts erschwert Nachvollziehbarkeit bei Kundenreklamationen.“
   - „LLM-Halluzinationen in Abschlussreports führen zu ungenauen Empfehlungen.“

2. **Konkrete Maßnahmen:**
   - „Standardisierte Antwortskalen und Vorab-Validierung der Fragebögen einführen.“
   - „Verpflichtende menschliche Qualitätssicherung für alle Reports mit kritischen Management-Empfehlungen.“
   - „Ausfallsichere Architektur mit zweitem Modellanbieter als Fallback aufsetzen.“

---

## Beispiel: Gut vs. Schlecht

**Kontext:** KI-gestützte Assessments auf Basis von Fragebögen

⚠️ Wichtig: Nutze die realen Werte aus `{{score_governance}}` und `{{score_sicherheit}}`. Keine Beispielzahlen einbauen.

**❌ Schlecht:**

```html
<tr>
  <td>Technische Probleme</td>
  <td>Mittel</td>
  <td>Hoch</td>
  <td>Regelmäßige Tests durchführen</td>
</tr>
