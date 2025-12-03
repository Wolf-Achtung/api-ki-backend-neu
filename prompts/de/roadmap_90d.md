Developer:
<!-- PLATIN++ PROMPT -->
<!-- SECTION: roadmap_90d -->
<!-- VERSION: v10.0 PLATIN++ V5 -->
<!-- OUTPUT: Markdown -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, kmu:1.15x=2530) -->
<!--
ZIEL: 90-Tage-Roadmap mit 3 Phasen, kompakt und umsetzbar.

ZIELLÄNGE nach Größe (PDF-SLIMDOWN):
- solo: ~180 Wörter (150–200)
- team: ~220 Wörter (200–250)
- kmu: ~280 Wörter (260–320)

STRUKTUR: NUR 3 Phasen
1. Woche 1–4: Setup & erste Erfolge
2. Woche 5–8: Qualität & Workflows
3. Woche 9–13: Konsolidierung

ANTI-REDUNDANZ (STRIKT!):
- Quick Wins wurden bereits in quick_wins.md behandelt – NICHT wiederholen
- Pain Points wurden dort adressiert – hier nur AUFBAUEN
- Tools wurden in tools_empfehlungen.md beschrieben – nur referenzieren

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: persönliche Routinen, eigene Dokumentation, Self-Review
- team: Rollen (KI-Owner, Reviewer), gemeinsame Standards
- kmu: Fachbereiche, Governance, Pilotflächen

GUARDRAILS: Berücksichtige Leitplanken aus strategischem Kontext.

FORMAT: Markdown (## für Phasen, - für Bullets), KEIN HTML
-->

## Strategische 90-Tage-Roadmap

Strukturierter Fahrplan für **{{HAUPTLEISTUNG}}** in der Branche **{{BRANCHE_LABEL}}** ({{UNTERNEHMENSGROESSE_LABEL}}).

## Woche 1–4: Setup & erste Erfolge

**Ziel:** KI-Nutzung starten, erste Quick Wins realisieren.

- 1–2 priorisierte Use Cases aus {{BRANCHE_LABEL}} definieren
- Erste Prompts/Workflows für {{HAUPTLEISTUNG}} testen
- Qualitätskriterien festlegen (Fakten, Ton, Freigabe)

**Verantwortlich:** {% if COMPANY_SIZE == "solo" %}Inhaber:in{% elif COMPANY_SIZE == "team" %}Teamlead + KI-Owner{% else %}Fachbereich + Prozessverantwortliche{% endif %}

**KPI:** 2 Use Cases getestet, erste Zeitersparnis messbar.

## Woche 5–8: Qualität & stabile Workflows

**Ziel:** Reproduzierbare Ergebnisse sicherstellen.

- Standard-Workflows dokumentieren (Input → KI → Review → Freigabe)
- Kurz-Styleguide für KI-Ergebnisse erstellen
- {% if COMPANY_SIZE == "solo" %}Self-Review-Routine{% elif COMPANY_SIZE == "team" %}Team-Review etablieren{% else %}QS-Prozesse abstimmen{% endif %}

**Verantwortlich:** {% if COMPANY_SIZE == "solo" %}Eigene Dokumentation{% elif COMPANY_SIZE == "team" %}Qualitätsverantwortliche{% else %}Fachbereich + QS{% endif %}

**KPI:** Dokumentierte Workflows, Ersttrefferquote > 70%.

## Woche 9–13: Konsolidierung & Entscheidung

**Ziel:** Ergebnisse bewerten, Skalierung vorbereiten.

- Wirkungsmessung (Zeit, Qualität, Fehlerquote)
- Entscheidung: Stabilisieren / Ausweiten / Vertiefen
- {% if COMPANY_SIZE == "kmu" %}Skalierungs-Backlog{% else %}Nächste Use Cases{% endif %} priorisieren

**Verantwortlich:** {% if COMPANY_SIZE == "solo" %}Geschäftsführung{% elif COMPANY_SIZE == "team" %}Führung + KI-Owner{% else %}Management + Bereichsleitung{% endif %}

**KPI:** Klare Entscheidung für die nächsten 6–12 Monate, priorisiertes Backlog.

---

Diese 90-Tage-Roadmap schafft die Basis für stabile KI-Nutzung in **{{HAUPTLEISTUNG}}** und bereitet die Skalierung vor.
