Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: roadmap_12m -->
<!-- VERSION: v12.0 PLATIN++ V5 -->
<!-- OUTPUT: Markdown -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2800 (solo:0.8x=2240, team:1.0x=2800, kmu:1.15x=3220) -->
<!--
ZIEL: 12-Monats-Roadmap mit 4 Phasen, max 4 Bullets pro Phase.

ZIELLÄNGE nach Größe (PDF-SLIMDOWN):
- solo: ~200 Wörter (180–240)
- team: ~280 Wörter (250–320)
- kmu: ~360 Wörter (320–400)

STRUKTUR: 4 Phasen
1. Monate 1–3: Fundament
2. Monate 4–6: Pilotierung
3. Monate 7–12: Skalierung
4. Abschluss: Verstetigung

ANTI-REDUNDANZ (STRIKT!):
- KEINE Wiederholung aus roadmap_90d
- KEINE Pain-Point-Wiederholung (siehe Quick Wins)
- KEINE Tool-Beschreibungen (siehe tools_empfehlungen)
- Fokus: WAS KOMMT NACH den ersten 90 Tagen?

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: "eigene Workflows", "persönliche Routine", "Self-Review"
        VERBOTEN: "Abteilung", "Team aufbauen", "Mitarbeiter", "HR"
- team: "Teammitglieder", "KI-Koordinator", "gemeinsame Standards"
- kmu: "Fachbereichsleitung", "Governance-Board", "bereichsübergreifend"

FORMAT: Markdown, KEIN HTML
-->

---

### VARIABLEN (aus Briefing)

- **{{BRANCHE_LABEL}}** – Branchenbezeichnung
- **{{UNTERNEHMENSGROESSE_LABEL}}** – Unternehmensgröße
- **{{HAUPTLEISTUNG}}** – Kernleistung/Hauptprozess
- **COMPANY_SIZE** – `solo` | `team` | `kmu`

---

### SIZE-AWARE LOGIK (STRENG EINHALTEN!)

**COMPANY_SIZE == "solo":**
- NIEMALS: "Abteilung", "Team aufbauen", "Mitarbeiter", "HR", "Projektteam"
- STATTDESSEN: "eigene Workflows", "persönliche Routine", "Self-Review"
- Max 4 Bullets pro Phase, ~50 Wörter pro Phase

**COMPANY_SIZE == "team":**
- Kleine Gruppen (2-10), informelle Strukturen
- "Teammitglieder", "KI-Koordinator", "gemeinsame Standards"
- Max 4 Bullets pro Phase, ~70 Wörter pro Phase

**COMPANY_SIZE == "kmu":**
- Formale Strukturen, Fachbereiche, Governance
- "Fachbereichsleitung", "Governance-Board", "bereichsübergreifend"
- Max 4 Bullets pro Phase, ~90 Wörter pro Phase

---

### PFLICHTSTRUKTUR (STRENG KOMPAKT)

## Strategische 12-Monats-Roadmap

Diese Roadmap zeigt die Weiterentwicklung nach den ersten 90 Tagen für **{{HAUPTLEISTUNG}}** in der Branche **{{BRANCHE_LABEL}}** mit Größe **{{UNTERNEHMENSGROESSE_LABEL}}**.

## Monate 1–3: Fundament & erste Use Cases

- Prioritäts-Workflow etablieren (aufbauend auf 90-Tage-Erfolgen)
- Qualitätskriterien schärfen
- Erste Erfolgsmessung (Zeit, Qualität)
- {% if COMPANY_SIZE == "solo" %}Persönliche KI-Routine festigen{% elif COMPANY_SIZE == "team" %}Team-Standards dokumentieren{% else %}Pilotbereich evaluieren{% endif %}

**KPI:** Mindestens 2 stabile Use Cases produktiv.

## Monate 4–6: Pilotierung & Qualitätssicherung

- Workflow-Optimierung basierend auf Learnings
- Konsistente Review-Prozesse einführen
- Monitoring-Dashboard aufsetzen
- {% if COMPANY_SIZE == "solo" %}Qualitäts-Checkliste erstellen{% elif COMPANY_SIZE == "team" %}Qualitätsverantwortliche benennen{% else %}QS-Prozess formalisieren{% endif %}

**KPI:** Messbare Zeitersparnis, Fehlerquote < 10%.

## Monate 7–12: Ausbau & Skalierung

- Neue Use Cases aus Nachbarbereichen erschließen
- {% if COMPANY_SIZE == "kmu" %}Governance-Framework finalisieren{% else %}Leitplanken dokumentieren{% endif %}
- Erfolgsmessung ausweiten (ROI-Nachweis)
- Wissenstransfer und Best Practices sichern

**KPI:** ROI nachweisbar, mindestens 3 produktive Use Cases.

## Abschluss & Verstetigung

- Jahresreview durchführen
- Budget für Jahr 2 planen
- Roadmap 2.0 mit neuen Prioritäten erstellen
- {% if COMPANY_SIZE == "kmu" %}Compliance-Status dokumentieren{% else %}Learnings festhalten{% endif %}

**Ausblick:** Basis für kontinuierliche Weiterentwicklung geschaffen.

---

### FORMAT-REGELN

- **Nur Markdown:** `## ` für Phasen-Titel
- Bullet-Listen mit `- ` (MAX 4 pro Phase!)
- Kurzer KPI-Absatz pro Phase
- **Kein HTML**, keine Code-Fences
- **MAX 900 Wörter gesamt!**

---

### STIL-VORGABEN

- Sachlich, konkret, keine Floskeln
- Strategisch fokussiert, nicht erzählerisch
- Keine Wiederholungen aus 90-Tage-Roadmap
- Keine Entwickler-Sprache, keine Platzhalter
- Beende nach "Abschluss & Verstetigung"
