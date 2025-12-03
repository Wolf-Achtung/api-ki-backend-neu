Developer:
<!-- roadmap_90d.md – v9.0 PDF-SLIMDOWN-STRICT
     Output: Markdown (wird serverseitig zu HTML konvertiert)

     **STRIKTE TOKEN-BEGRENZUNG (KRITISCH!):**
     MAXIMAL 350-450 Wörter Output.

     **Ziellänge nach Größe (STRENG REDUZIERT):**
     - Solo: ~180 Wörter (akzeptabel: 150–200)
     - Team: ~220 Wörter (akzeptabel: 200–250)
     - KMU: ~280 Wörter (akzeptabel: 260–320)

     STRUKTUR: NUR 3 Phasen! (nicht 6)
       1. Woche 1–4: Setup & erste Erfolge (~120 Wörter)
       2. Woche 5–8: Qualität & Workflows (~120 Wörter)
       3. Woche 9–13: Konsolidierung (~100 Wörter)

     **FOKUS: NUR 3 QUICK-IMPACT MASSNAHMEN**
     - Keine Vision, keine Meta-Abschnitte
     - Keine ausführlichen Erklärungen
     - Direkt umsetzbare Schritte

     VARIABLEN:
       {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE

     SIZE-AWARE (COMPANY_SIZE):
       solo: persönliche Routinen, eigene Dokumentation, keine Teams
       team: Rollen, gemeinsame Standards, Abstimmung
       kmu: Fachbereiche, Governance, Pilotflächen

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
