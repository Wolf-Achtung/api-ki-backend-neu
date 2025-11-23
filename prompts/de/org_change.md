<!-- org_change.md - v2.6 GOLD STANDARD+ -->
<!-- Antworte ausschließlich mit **validem HTML**.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences im OUTPUT.
     VERSION: 2.6 GOLD STANDARD+ (Size-Awareness verschärft, Solo-Hinweise sauber getrennt) -->

# PROMPT: Organizational Change - Change-Management

## ⚠️ SIZE-AWARENESS - ABSOLUT PFLICHT!

**Mögliche Unternehmensgrößen (NUR diese 3!):**
- `{{COMPANY_SIZE}}` = "solo" → Label: "1 (Solo-Selbstständig/Freiberuflich)"
- `{{COMPANY_SIZE}}` = "team" → Label: "2-10 (Kleines Team)"
- `{{COMPANY_SIZE}}` = "kmu"  → Label: "11-100 (KMU)"

### 📏 SIZE-APPROPRIATE CHANGE-ANSÄTZE

**{{COMPANY_SIZE}} = "solo":**
- ✅ Fokus: eigene Arbeitsweise, Routinen, Angebotsstruktur
- ✅ Begriffe wie "Sie", "Ihre Arbeitsweise", "Ihre Kund:innen"
- ✅ Optional: "Freelancer oder Partner" für spätere Skalierung
- ❌ NIEMALS: "Team", "Mitarbeitende", "Abteilung", "Change-Agents", "Town Hall"

**{{COMPANY_SIZE}} = "team" (2-10 MA):**
- ✅ Fokus: Team-Alignment und gemeinsame Nutzung von KI
- ✅ Begriffe wie "Team", "Teammitglieder", "kleines Kernteam", "Weekly-Meeting"
- ✅ Informelle Formate (Show & Tell, Buddy-System, KI-Sprechstunde)
- ❌ NIEMALS: "Abteilung", "PMO-Team", "Steering Committee", "Konzernstrukturen"

**{{COMPANY_SIZE}} = "kmu" (11-100 MA):**
- ✅ Fokus: strukturiertes Change-Programm über mehrere Teams/Bereiche
- ✅ Begriffe wie "Projektteam", "Führungskräfte", "Change-Agents", "Pilotbereich"
- ✅ Formelle Trainings, Change-Kommunikation, Governance-Gremien (wenn sinnvoll)
- ✅ "Change Manager" oder "Projektleiter Change" (ab ~50 MA realistisch)

---

## 🔒 SIZE-CHECK: Solo-Hinweise strikt begrenzen

Bevor du Text erzeugst:

1. Lies `{{COMPANY_SIZE}}` bewusst.
2. Wenn `{{COMPANY_SIZE}} = "solo"`:
   - Du-Ansprache ist erlaubt.
   - Solo-spezifische Hinweise wie "als Solo-Beratung" sind OK.
3. Wenn `{{COMPANY_SIZE}} = "team"` oder `"kmu"`:
   - KEINE Formulierungen wie:
     - "Hinweis für Solo-Unternehmer:innen"
     - "wenn Sie später ein Team aufbauen"
     - "aktuell noch allein, später Mitarbeitende"
   - Sprich stattdessen konsequent von "Team", "Unternehmen", "Mitarbeitenden".

---

## 🎯 ZWECK

Erstelle realistische Change-Management-Empfehlungen, die:

1. Zur Unternehmensgröße passen (Solo ≠ Team ≠ KMU).
2. Spezifisch für {{HAUPTLEISTUNG}} sind.
3. Konkrete Maßnahmen statt Theorie nennen.
4. Quick Wins, Roadmap und Business Case als Katalysatoren nutzen
   (z. B. Trainings rund um Quick Wins, Rollenklärung für Roadmap-Deliverables).

**Zielgruppe:** Geschäftsführung, HR, Team-Leads (bei Solo: die/der Inhaber:in selbst).  
**Stil:** Pragmatisch, menschenzentriert, realistisch, wachstumsorientiert.

---

## ⛔ ABSOLUT VERBOTEN

### ❌ Change-Theorie bei Solo/Team
- "Change-Management-Prozess nach Kotter"
- "Stakeholder-Analyse durchführen"
- "Change-Readiness-Assessment"
- "Transformationsprogramm" ohne konkrete Bezugspunkte
- "Kulturelle Transformation" als Selbstzweck

### ❌ Unpassende Größenlogik
- Bei Solo: "Abteilungen", "Mitarbeitende", "PMO", "HR-Abteilung"
- Bei Team: "Konzernweites Programm", "globales Change-Office"
- Bei KMU: so tun, als gäbe es nur eine einzelne Person

### ❌ Widerspruch zum Business Case
- Change-Programm empfehlen, das offensichtlich mehr kostet als der Business Case hergibt.
- Zusätzliche Vollzeitstellen vorschlagen, wenn Business Case Einsparung dafür nicht reicht.

---

## 🔧 STRUKTUR DER ANTWORT

Erzeuge eine HTML-Section:

- Kurze Einleitung (1 Absatz) mit Bezug auf:
  - {{HAUPTLEISTUNG}}
  - {{COMPANY_SIZE}} (implizit über Sprache)
  - wichtigste Quick Wins / Roadmap-Phasen

- 3–5 thematische Blöcke, z. B.:
  1. Mindset & Kommunikation
  2. Skills & Training
  3. Prozesse & Routinen
  4. Rollen & Verantwortlichkeiten
  5. Verstetigung und Feedback-Schleifen

Jeder Block:

- Überschrift `<h3>` oder `<h4>` (max. 6–8 Wörter).
- 1–2 Absätze mit konkreten Maßnahmen.
- Optional eine kurze Liste (max. 3–5 Punkte) für sehr konkrete Beispiele.

---

## 🧪 QUALITÄTS-CHECK VOR OUTPUT

Prüfe vor dem finalen HTML:

1. **Size-Check:**  
   - Kein "Solo"-Wording bei `team`/`kmu`.  
   - Bei Solo keine erfundenen Teams.

2. **Konkretheit:**  
   - Jede Maßnahme klar: Wer, was, wann, mit welchem Ziel?

3. **Anschlussfähigkeit:**  
   - Verweist sinnvoll auf Quick Wins, Roadmap, Business Case.
   - Z. B. "Trainings entlang der Quick Wins" oder "Change-Kommunikation rund um den Gamechanger".

4. **Realismus:**  
   - Aufwand & Umfang passen zur Unternehmensgröße.
   - Keine Großprogramme für Solo / Mini-Teams.

**Output:** Valides HTML, keine Markdown-Fences, keine Platzhalter mehr im finalen Text.
