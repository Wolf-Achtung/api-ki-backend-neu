Developer:
<!-- PLATIN++ PROMPT v5.2 -->
<!-- SECTION: roadmap_90d -->
<!-- OUTPUT: HTML ONLY -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: {{BRANCHE_LABEL}}, {{UNTERNEHMENSGROESSE_LABEL}}, {{HAUPTLEISTUNG}}, COMPANY_SIZE -->
<!-- TOKEN-BUDGET: 2200 (solo:0.8x=1760, team:1.0x=2200, kmu:1.15x=2530) -->
<!--
ZIEL: 90-Tage-Roadmap mit 4 klaren Phasen + Meilensteinen.

PHASEN-STRUKTUR (STRIKT EINHALTEN):
- Phase 0 (Woche 1–2): Setup – Grundlagen schaffen
- Phase 1 (Woche 3–5): Entlastung – Quick Wins umsetzen
- Phase 2 (Woche 6–10): Produktiver Einsatz – Workflows stabilisieren
- Phase 3 (Woche 11–13): Konsolidierung – Ergebnisse messen, Entscheidung treffen

FORMAT:
- Jede Phase: Ziel (1 Satz) + 2-3 Bullets + Meilenstein
- Meilenstein = konkret, messbar, erreichbar
- KEINE langen Texte – nur Kernpunkte

ANTI-REDUNDANZ (STRIKT!):
- Quick Wins wurden in quick_wins.md beschrieben → NICHT wiederholen
- Tools wurden in tools_empfehlungen.md beschrieben → nur referenzieren
- Hier: WIE und WANN, nicht WAS (das steht in Quick Wins)

PERSONA-VARIATIONEN (COMPANY_SIZE):
- solo: persönliche Routinen, Self-Review, eigene Dokumentation
        Nicht verwenden: Team, Abteilung, Mitarbeiter
- team: KI-Owner, gemeinsame Standards, Review-Runden
- kmu: Fachbereiche, Pilotbereiche, Governance, Rollout

GUARDRAILS: Berücksichtige Leitplanken aus strategischem Kontext.
-->

## 90-Tage-Roadmap für {{HAUPTLEISTUNG}}

{% if COMPANY_SIZE == "solo" %}
### Phase 0: Setup (Woche 1–2)
**Ziel:** Arbeitsfähigkeit mit KI herstellen.
- Zugang zu KI-Werkzeug einrichten
- Erste Prompt-Vorlage für Kernaufgabe erstellen
- Eigene Qualitätskriterien definieren (Was ist "gut genug"?)

**🎯 Meilenstein:** KI-Zugang funktioniert, erste Vorlage einsatzbereit.

### Phase 1: Entlastung (Woche 3–5)
**Ziel:** Spürbare Zeitersparnis bei Routineaufgaben.
- Quick Wins aus Abschnitt "Sofortmaßnahmen" umsetzen
- Zeiteinsparung pro Aufgabe notieren
- Prompt-Bibliothek mit 5–10 funktionierenden Vorlagen aufbauen

**🎯 Meilenstein:** 3–5 h/Monat nachweisbar eingespart.

### Phase 2: Produktiver Einsatz (Woche 6–10)
**Ziel:** Stabile Workflows für Alltag.
- Routine: Input → KI-Entwurf → Eigene Prüfung → Freigabe
- Qualitäts-Checkliste für KI-Outputs erstellen
- Self-Review zur Gewohnheit machen

**🎯 Meilenstein:** 70%+ der KI-Entwürfe direkt nutzbar.

### Phase 3: Konsolidierung (Woche 11–13)
**Ziel:** Ergebnisse bewerten, nächste Schritte planen.
- Tatsächliche Zeitersparnis messen
- Entscheidung: Ausweiten, Vertiefen oder Stabilisieren?
- Nächste Use Cases für 12-Monats-Roadmap priorisieren

**🎯 Meilenstein:** Klare Entscheidung und priorisierte Liste für nächstes Quartal.

{% elif COMPANY_SIZE == "team" %}
### Phase 0: Setup (Woche 1–2)
**Ziel:** Teamweite Arbeitsfähigkeit mit KI herstellen.
- KI-Owner benennen (verantwortlich für Standards)
- Gemeinsamen Zugang einrichten
- Erste Vorlagen für 2 priorisierte Anwendungsfälle erstellen

**🎯 Meilenstein:** Team hat Zugang, erste Vorlagen verteilt.

### Phase 1: Entlastung (Woche 3–5)
**Ziel:** Quick Wins im Team umsetzen.
- Maßnahmen aus "Sofortmaßnahmen" teamweit ausrollen
- Jede:r testet mindestens 2 Workflows
- Erfahrungen in kurzem Weekly-Check teilen

**🎯 Meilenstein:** Alle Teammitglieder nutzen KI aktiv, erste Zeitersparnis dokumentiert.

### Phase 2: Produktiver Einsatz (Woche 6–10)
**Ziel:** Einheitliche Qualitätsstandards etablieren.
- Standard-Workflow dokumentieren: Input → KI → Peer-Review → Freigabe
- Team-Styleguide für KI-Outputs erstellen
- Review-Runden (30 Min./Woche) für Best Practices

**🎯 Meilenstein:** Dokumentierter Workflow, Erstqualität > 70%.

### Phase 3: Konsolidierung (Woche 11–13)
**Ziel:** Ergebnisse messen, Skalierung vorbereiten.
- Wirkungsmessung: Zeit, Qualität, Fehlerquote
- Entscheidung: Stabilisieren / Ausweiten / Vertiefen
- Backlog für nächste Use Cases erstellen

**🎯 Meilenstein:** Klare Entscheidung, priorisiertes Backlog für 12-Monats-Roadmap.

{% else %}
### Phase 0: Setup (Woche 1–2)
**Ziel:** Pilotbereich definieren und Grundlagen schaffen.
- Pilotbereich auswählen (z.B. ein Fachbereich)
- KI-Verantwortliche:n benennen
- Governance-Grundregeln festlegen (Was darf, was nicht?)

**🎯 Meilenstein:** Pilotbereich startklar, Governance-Rahmen definiert.

### Phase 1: Entlastung (Woche 3–5)
**Ziel:** Quick Wins im Pilotbereich umsetzen.
- Maßnahmen aus "Sofortmaßnahmen" gezielt einsetzen
- Pilotteam schult sich gegenseitig
- Erste Zeiteinsparungen dokumentieren

**🎯 Meilenstein:** Pilotbereich nutzt KI aktiv, messbare Entlastung.

### Phase 2: Produktiver Einsatz (Woche 6–10)
**Ziel:** Skalierbare Prozesse etablieren.
- Standard Operating Procedures (SOPs) für KI-Workflows
- QS-Prozess: Input → KI → Fachliche Prüfung → Freigabe
- Schulungskonzept für Rollout auf weitere Bereiche

**🎯 Meilenstein:** SOPs dokumentiert, Schulungskonzept fertig.

### Phase 3: Konsolidierung (Woche 11–13)
**Ziel:** Rollout-Entscheidung und Skalierungsplan.
- Business-Case-Validierung anhand Pilotdaten
- Entscheidung: Rollout auf weitere Bereiche?
- Priorisiertes Backlog für 12-Monats-Rollout

**🎯 Meilenstein:** Management-Entscheidung getroffen, Rollout-Plan steht.
{% endif %}

---
*Diese Roadmap verweist auf Quick Wins und Tools aus den entsprechenden Abschnitten.*
