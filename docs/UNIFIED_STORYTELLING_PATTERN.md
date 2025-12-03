# Unified Storytelling Pattern (USP) – PLATIN++ V5

## Zweck
Dieses Dokument definiert das einheitliche Storytelling-Muster für alle PLATIN++ Prompts. Es sorgt für Konsistenz, vermeidet Wiederholungen und garantiert CEO-taugliche Outputs.

---

## 1. Kapitel-Hierarchie & Verantwortlichkeiten

| Kapitel | Funktion | Besitzt exklusiv | Referenziert von |
|---------|----------|------------------|------------------|
| **Executive Summary** | CEO-Überblick (2-4 Sätze) | Plot-Struktur, Kernaussage | – |
| **Quick Wins** | Sofortmaßnahmen | Pain Points, Zeitersparnis | Roadmap 90d |
| **Roadmap 90d** | WIE & WANN | Phasen-Struktur, Meilensteine | 12m-Roadmap |
| **Roadmap 12m** | Langfrist-Planung | Dimensionen (KMU), Q-Phasen | Business Case |
| **Business Case** | ROI & Investition | Zahlen, Payback-Formel | Förderpotenzial |
| **Gamechanger** | Strategische Vision | Transformationsideen | – |
| **Tools** | Werkzeugempfehlungen | Tool-Beschreibungen | Roadmaps |
| **Risks** | Risiken & Compliance | Risiko-Matrix | Roadmap 12m |
| **Förderpotenzial** | Förderungen | Programme, Quoten | Business Case |

---

## 2. Anti-Redundanz-Matrix

```
REGEL: Jede Information wird EINMAL an der richtigen Stelle genannt.

Quick Wins     → besitzt Pain Points & Zeitersparnis
                 Roadmap REFERENZIERT, wiederholt NICHT

Roadmap 90d    → besitzt Phasen & Meilensteine
                 BAUT AUF Quick Wins auf, listet sie NICHT erneut

Roadmap 12m    → besitzt Langfrist-Dimensionen
                 SETZT 90d-Erfolge voraus, wiederholt NICHT

Business Case  → besitzt Zahlen (CAPEX, OPEX, ROI)
                 Förderpotenzial REFERENZIERT, wiederholt NICHT

Tools          → besitzt Tool-Beschreibungen
                 Roadmaps REFERENZIEREN, beschreiben NICHT
```

---

## 3. Persona-Matrix (SIZE-AWARE)

### Solo (1 Person)
- **Sprache:** "Sie", "Ihr Workflow", "persönlich"
- **VERBOTEN:** Team, Abteilung, Mitarbeiter, HR, Governance-Board
- **Token-Multiplikator:** 0.8x
- **Fokus:** Zeitentlastung, Self-Review, eigene Routinen

### Team (2-10 Personen)
- **Sprache:** "Ihr Team", "gemeinsam", "KI-Owner"
- **Token-Multiplikator:** 1.0x (Basis)
- **Fokus:** Shared Standards, Peer-Review, Rollenverteilung

### KMU/SME (11+ Personen)
- **Sprache:** "Fachbereiche", "Governance", "Rollout"
- **Token-Multiplikator:** 1.15x
- **Fokus:** Skalierung, SOPs, Compliance, Pilotbereiche

---

## 4. Executive Summary – Plot-Struktur

```
AUFBAU (2-4 Sätze, 1 Absatz):

1. AUSGANGSLAGE: Wo steht das Unternehmen heute?
   "Als [Größe] in [Branche] mit Fokus auf [Hauptleistung]..."

2. FOKUS & ZIELE: Was ist das zentrale Ziel?
   "...liegt der größte Hebel in..."

3. WICHTIGSTER ANSATZPUNKT: Was bringt den größten Effekt?
   "...durch [konkreter Ansatz]..."

4. SOFORTIGE CHANCE: Was ist der nächste Schritt?
   "Der erste Schritt: [Quick Win]."
```

---

## 5. Quick Wins – Struktur

```
REIHENFOLGE (immer einhalten!):
1. Zeitersparnis
2. Produktivitätssprünge
3. Qualitätsverbesserung
4. Kostensenkung (nur Team/KMU)

ANZAHL nach Größe:
- Solo: 3-4 Quick Wins
- Team: 4-5 Quick Wins
- KMU:  5-7 Quick Wins

FORMAT pro Quick Win:
- **[Konkrete Maßnahme]:** [1 Satz Beschreibung]. *Effekt: [X h/Monat oder %]*
```

---

## 6. Roadmap-Struktur

### 90 Tage – 4 Phasen
| Phase | Zeitraum | Fokus | Meilenstein |
|-------|----------|-------|-------------|
| Phase 0 | Woche 1-2 | Setup | Zugang + erste Vorlage |
| Phase 1 | Woche 3-5 | Entlastung | 3-5 h/Monat gespart |
| Phase 2 | Woche 6-10 | Produktiver Einsatz | 70%+ Ersttrefferquote |
| Phase 3 | Woche 11-13 | Konsolidierung | Entscheidung getroffen |

### 12 Monate – Nach Größe

**Solo/Team:** Quartalsbasiert (Q1, Q2, Q3-4)

**KMU:** 5-Dimensionen-Modell
1. Technologie (Q1-Q2)
2. Daten (Q1-Q2)
3. Organisation (Q2-Q3)
4. Produkt/Prozess (Q2-Q4)
5. Compliance (Q3-Q4)

---

## 7. Business Case – Realismus-Regeln

```
STRIKT VERBOTEN:
- 90% Effizienzversprechen
- Erfundene Zahlen
- Komplexe Finanzformeln

ERLAUBT:
- 15-30% realistische Einsparungen
- Nur übergebene Variablen nutzen
- "rund / etwa / ca." für Einordnung

PAYBACK-ERKLÄRUNG (vereinfacht):
Investition ÷ monatliche Einsparung = Monate bis Amortisation
```

---

## 8. Header-Format (alle Prompts)

```markdown
<!-- PLATIN++ PROMPT -->
<!-- SECTION: [section_name] -->
<!-- VERSION: v[X.0] PLATIN++ V5 [VARIANT] -->
<!-- OUTPUT: [HTML|Markdown] -->
<!-- SIZE-AWARE: solo/team/kmu -->
<!-- INPUT: [Variablen] -->
<!-- TOKEN-BUDGET: [base] (solo:0.8x=[X], team:1.0x=[Y], kmu:1.15x=[Z]) -->
<!--
ZIEL: [1 Satz]

[SPEZIFISCHE REGELN]

ANTI-REDUNDANZ:
- [Was HIER steht]
- [Was woanders steht → nur referenzieren]

PERSONA-VARIATIONEN:
- solo: [Regeln]
- team: [Regeln]
- kmu: [Regeln]
-->
```

---

## 9. Qualitätscheckliste

Vor Freigabe eines Prompts prüfen:

- [ ] Header vollständig und korrekt
- [ ] Token-Budget mit SIZE_MULTIPLIERS angegeben
- [ ] Anti-Redundanz-Regeln dokumentiert
- [ ] Persona-Variationen für alle 3 Größen
- [ ] Keine REINFORCEMENT-Kommentare (PDF-SLIMDOWN v2.0)
- [ ] Realistische Werte (keine 90% Versprechen)
- [ ] Jinja2-Syntax korrekt (`{% if %}`, `{% elif %}`, `{% else %}`)

---

## 10. Versionierung

| Version | Datum | Änderungen |
|---------|-------|------------|
| v1.0 | 2024-12 | Initiale USP-Dokumentation |
| | | Executive Summary: CEO-EDITION |
| | | Quick Wins: Geordnete Kategorien |
| | | Roadmaps: 4-Phasen + 5-Dimensionen |
| | | Business Case: Realismus-Regeln |

---

*Dieses Dokument ist die zentrale Referenz für alle PLATIN++ Prompt-Entwicklungen.*
