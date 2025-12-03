Developer:
<!-- roadmap_90d.md – v7.0 SIZE-AWARE MARKDOWN
     Output: Markdown (wird serverseitig zu HTML konvertiert)

     **Ziellänge nach Größe:**
     - Solo: ~280 Wörter (akzeptabel: 250–320)
     - Team: ~330 Wörter (akzeptabel: 300–370)
     - KMU: ~380 Wörter (akzeptabel: 350–420)

     STRUKTUR (6 Phasen):
       Phase 1: Woche 1-2 – Zielbild & Prioritäten
       Phase 2: Woche 3-4 – Datenqualität & Workflow-Grundlagen
       Phase 3: Woche 5-6 – Quick-Wins & erste Wirkung
       Phase 4: Woche 7-8 – Qualitätsstandards
       Phase 5: Woche 9-10 – Monitoring & Iteration
       Phase 6: Woche 11-13 – Konsolidierung & Skalierungsvorbereitung

     Pro Phase: ~40-60 Wörter (Solo: ~35-45)

     VARIABLEN:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE

     SIZE-AWARE (COMPANY_SIZE):
       solo: persönliche Routinen, eigene Dokumentation, keine Teams
       team: Rollen, gemeinsame Standards, Abstimmung
       kmu: Fachbereiche, Governance, Pilotflächen

     FORMAT: Markdown (## für Phasen, - für Bullets), KEIN HTML
-->

## Strategische 90-Tage-Roadmap

Diese Roadmap zeigt, wie ein Unternehmen der Größe **{{UNTERNEHMENSGROESSE_LABEL}}** innerhalb von 90 Tagen KI-gestützte Arbeitsweisen im Bereich **{{HAUPTLEISTUNG}}** strukturiert etabliert. Sie nutzt typische Workflows, Datenarten und Pain Points der Branche **{{BRANCHE_LABEL}}** und verbindet schnelle Wirkung mit soliden Grundlagen.

Die folgenden Phasen schaffen Klarheit, reduzieren Reibungspunkte und sorgen dafür, dass KI nach 90 Tagen dauerhaft, stabil und messbar Mehrwert liefert.

## Woche 1–2: Zielbild, Use-Case-Rahmen & Prioritäten

**Ziel:** Klar definieren, wo KI im Bereich {{HAUPTLEISTUNG}} den stärksten Nutzen bringt.

**Deliverables:**
- Fokus-Definition: 1–2 priorisierte Aufgaben mit hohem Wirkungspotenzial
- Übersicht branchentypischer Beispiele (5–10 Fälle)
- Mini-Checkliste für Qualität, Fakten, Tonalität

**Verantwortlich:** {% if COMPANY_SIZE == "solo" %}Persönliche Priorisierung{% elif COMPANY_SIZE == "team" %}Teamlead + KI-Owner{% else %}Fachbereich + Prozessverantwortliche{% endif %}

**KPI:** Priorisierte Use Cases + erste Qualitätskriterien definiert.

## Woche 3–4: Datenqualität, Beispiele & Workflow-Grundlagen

**Ziel:** Saubere Basis schaffen, damit KI stabile, belastbare Ergebnisse liefert.

**Deliverables:**
- Sammlung typischer Fälle (mind. 10) – real, vollständig, strukturiert
- Erste stabile Workflow-Schritte (Input → KI → Review → Freigabe)
- Definition messbarer Kriterien: Vollständigkeit, Korrektheit, Stil

**Verantwortlich:** {% if COMPANY_SIZE == "solo" %}Eigene Dokumentation{% elif COMPANY_SIZE == "team" %}Gemeinsame Qualitätsdefinition{% else %}Fachbereich + Qualitätssicherung{% endif %}

**KPI:** Dokumentierte Workflows + strukturierte Beispiele vorhanden.

## Woche 5–6: Quick-Wins & erste messbare Wirkung

**Ziel:** Spürbare Entlastung durch die ersten 1–2 KI-gestützten Quick-Wins.

**Deliverables:**
- Implementierung der 1–2 wirkungsstärksten Quick-Wins
- Kurztests: Zeitersparnis, Konsistenz, Risikominderung
- Lern-/Fehlerliste für spätere Standards

**Verantwortlich:** {% if COMPANY_SIZE == "solo" %}Umsetzung durch Inhaber:in{% elif COMPANY_SIZE == "team" %}KI-Owner + direkt Beteiligte{% else %}Fachbereich + Prozessverantwortliche{% endif %}

**KPI:** Erste Wirkung (10–25% Zeitgewinn).

## Woche 7–8: Qualitätsstandards & einheitliche Arbeitsweise

**Ziel:** Reproduzierbare Ergebnisse sicherstellen.

**Deliverables:**
- Kurz-Styleguide für KI-Ergebnisse (Stil, Fakten, Fachlichkeit)
- Dokumentation der neuen Arbeitsweise
- Abstimmung zwischen beteiligten Rollen

**Verantwortlich:** {% if COMPANY_SIZE == "solo" %}Self-Review-Prozesse{% elif COMPANY_SIZE == "team" %}Teamreview + Qualitätsverantwortliche{% else %}Fachbereich + Qualitätssicherung + IT{% endif %}

**KPI:** Höhere Ersttrefferquote, weniger Korrekturen.

## Woche 9–10: Monitoring, Reporting & iterative Verbesserung

**Ziel:** Wirkung sichtbar machen und Optimierungen ableiten.

**Deliverables:**
- Einfaches Monitoring (Zeit, Qualität, Fehler, Konsistenz)
- Kurzbericht zu Fortschritt und offenen Herausforderungen
- Optimierte Templates und Workflows

**Verantwortlich:** {% if COMPANY_SIZE == "solo" %}Persönliche Analyse{% elif COMPANY_SIZE == "team" %}Owner + Teamreview{% else %}Fachbereich + ggf. Controlling{% endif %}

**KPI:** Dokumentierte Verbesserungen + Trendlinien.

## Woche 11–13: Entscheidung, Konsolidierung & Vorbereitung der Skalierung

**Ziel:** Auf Basis echter Ergebnisse entscheiden, wie KI weiter ausgebaut wird.

**Deliverables:**
- Bewertung der KI-Eignung und Wirkung für {{HAUPTLEISTUNG}}
- Strategische Entscheidung: Stabilisieren / Ausweiten / Vertiefen
- Skalierungs-Backlog (Use Cases, Automatisierungen)

**Verantwortlich:** {% if COMPANY_SIZE == "solo" %}Geschäftsführung{% elif COMPANY_SIZE == "team" %}Führung + KI-Owner{% else %}Management + Bereichsleitung{% endif %}

**KPI:** Priorisiertes Backlog + klare Entscheidung für die nächsten 6–12 Monate.

---

Diese 90-Tage-Roadmap legt die strukturelle Grundlage für eine stabile, sichere und wirkungsorientierte Einführung von KI in **{{HAUPTLEISTUNG}}**. Sie schafft klare Arbeitsweisen, schnelle Vorteile und eine belastbare Basis für Pilotprojekte und Skalierung im Folgejahr.
