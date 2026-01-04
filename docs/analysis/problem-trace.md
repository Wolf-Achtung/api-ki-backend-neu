# Problem-Trace: Root Causes der 7 Qualitätsprobleme

## Zusammenfassung

| # | Problem | Root Cause | Datei:Zeile |
|---|---------|-----------|-------------|
| 1 | Digital Jetzt (eingestellt) | Hardcodierte veraltete Daten | `data/funding_programs.json:1-9` |
| 2 | 91.500€ für Solo unrealistisch | Fehlende Solo-Filterung bei Summierung | `services/funding_engine_v2.py:182-265` |
| 3 | ROI 284% / 20h ohne Herleitung | Hardcodierte Fallback-Werte | `services/roi_calculator.py:42-43` |
| 4 | 90% AI-First Markttrend | Hardcodierte Trend-Daten ohne Quelle | `services/branch_profile_engine.py:144-151` |
| 5 | Handlungsempfehlungen doppelt | Separate Sektionen ohne Deduplizierung | `gpt_analyze.py:8045-8046` |
| 6 | Enterprise-Sprache für Solo | LLM ignoriert Persona-Constraints | LLM-Output, nicht im Code |
| 7 | 42 Seiten für Solo | Keine Gesamtseiten-Begrenzung | Architektur-Problem |

---

## Problem #1: "Digital Jetzt" wird empfohlen (seit 12/2023 eingestellt)

### Root Cause
Das Förderprogramm "Digital Jetzt" ist in **drei Stellen** hardcodiert:

**Quelle 1:** `data/funding_programs.json` (Zeile 1-9)
```json
{
  "name": "Digital Jetzt (BMWK)",
  "region": "DE",
  "target": "KMU (bis 499 MA)",
  "amount": "bis 50.000 € (bis 50%)",
  "deadline": "31.03.2026",  // ← FALSCH! Programm endete 12/2023
  "url": "https://www.bmwk.de",
  "notes": "Investitionen in digitale Technologien & Qualifizierung"
}
```

**Quelle 2:** `services/funding_parser.py` (Zeile 10-18)
```python
FALLBACK_FUNDING_PROGRAMS = [
    {
        "name": "Digital Jetzt (BMWK)",
        ...
        "deadline": "31.03.2026",  // ← Gleicher Fehler
    },
    ...
]
```

**Quelle 3:** `prompts/de/foerderpotenzial.md` (Zeile 21-22)
```markdown
PERSONA-VARIATIONEN (COMPANY_SIZE):
- kmu: Digital Jetzt, ZIM, strukturelle Förderung
```

### Warum passiert das?
- Keine automatische Validierung von Förderprogramm-Deadlines
- Keine externe Datenquelle (API) für aktuelle Programme
- Manuelle Pflege der JSON-Dateien, keine regelmäßigen Updates

---

## Problem #2: "Förderpotenzial bis 91.500€" für Solo unrealistisch

### Root Cause
Die Förder-Summierung in `services/business_case_engine_v2.py` addiert ALLE passenden Programme ohne Solo-spezifische Limitierung.

**Datei:** `services/funding_engine_v2.py` (Zeile 60-116)
```python
@dataclass
class FundingProgramme:
    # Size fit scores (0.0-1.0)
    fit_solo: float = 0.5   # ← Default 0.5, nicht streng genug
    fit_team: float = 0.5
    fit_kmu: float = 0.5
```

**Problem-Stelle:** `services/business_case_engine_v2.py` (Zeile 747-760)
```python
total_funding = 0.0
for prog in programmes:
    # Addiert alle Programme ohne strikte Solo-Filterung
    funding_amount = _extract_funding_amount(prog)
    total_funding += funding_amount
    # ← FEHLT: if company_size == "solo" and funding_amount > 20000: skip
```

### Warum passiert das?
- `fit_solo` Werte werden bei Empfehlung berücksichtigt, aber nicht bei der Summenberechnung
- Programme wie "EIC Accelerator" (2,5 Mio €) mit `fit_solo: 0.3` werden trotzdem gezählt
- Keine realistische Obergrenze für Solo-Fördersummen

---

## Problem #3: ROI 284% und "20h Zeitersparnis/Monat" ohne Herleitung

### Root Cause
Der `roi_calculator.py` verwendet **hardcodierte Fallback-Werte**:

**Datei:** `services/roi_calculator.py` (Zeile 42-51)
```python
def calc_roi(briefing, quickwins=None):
    # konservativ 40 h/Monat Einsparung ohne Quickwins-Angaben
    hours = 40.0  # ← HARDCODIERT! Quelle unklar
    if quickwins:
        s = 0.0
        for q in quickwins:
            try:
                s += float(q.get("time_saved_monthly_hours") or 0.0)
            except Exception:
                pass
        hours = max(10.0, s) if s > 0 else hours  # ← Fallback auf 40h
```

**ROI-Formel:** (Zeile 59)
```python
roi12_rate = ((monthly * 12) - invest) / max(invest, 1.0)
roi12_pct = roi12_rate * 100.0
# Bei 40h * 80€ = 3.200€/Monat und 3.000€ Invest:
# ROI = ((3.200 * 12) - 3.000) / 3.000 = 1.180% (!!)
```

### Warum 284% entstehen kann:
```
Stundensatz (geschätzt): 80€ (aus Umsatzklasse abgeleitet)
Zeitersparnis: 40h/Monat (Fallback)
Monatlicher Wert: 40 * 80 = 3.200€
Investment: 3.000€ (aus Budget-Range)
ROI 12M = ((3.200 * 12) - 3.000) / 3.000 * 100 = 1.180%
```

Mit kleineren Werten (z.B. 20h bei 60€ und 5.000€ Invest):
```
ROI = ((1.200 * 12) - 5.000) / 5.000 * 100 = 188%
```

**Zusätzliches Problem:** Die "20h Zeitersparnis" erscheint in Quick-Win-Templates:

**Datei:** `gpt_analyze.py` (Zeile 7717, 7744, 7765)
```html
<p><em>Zeitersparnis: [X]-[Y] h/Monat</em></p>
```
Das `[X]-[Y]` wird vom LLM gefüllt, aber ohne Validierung gegen realistische Werte.

---

## Problem #4: Markttrend "90% AI-First Beratung" - Quelle unklar

### Root Cause
Trends sind in `branch_profile_engine.py` **hardcodiert mit erfundenen Konfidenzwerten**:

**Datei:** `services/branch_profile_engine.py` (Zeile 144-154)
```python
"trends_de": [
    ("AI-First Beratung", "Beratungshäuser integrieren KI als Core-Service", 0.9),
    # ← 0.9 (90%) KONFIDENZ - WOHER KOMMT DIESE ZAHL?
    ("Outcome-Based Pricing", "Shift von Stundensätzen zu Value-Based-Modellen", 0.75),
    ("Remote-First Delivery", "Hybride Beratungsmodelle werden Standard", 0.85),
    ("Data-Driven Insights", "Analysen basieren zunehmend auf Echtzeit-Daten", 0.8),
],
"trends_en": [
    ("AI-First Consulting", "Consulting firms integrate AI as core service", 0.9),
    ...
],
```

### Warum passiert das?
- Keine externe Research-API für aktuelle Marktdaten
- Konfidenzwerte (0.9, 0.85, etc.) sind willkürlich gesetzt
- Keine Quellenangaben im generierten Report
- Perplexity/Tavily Research wird nicht für Trends genutzt

---

## Problem #5: Handlungsempfehlungen erscheinen doppelt (S.10 + S.23)

### Root Cause
Zwei separate Sektionen generieren ähnliche Inhalte:

**Datei:** `gpt_analyze.py` (Zeile 8045-8046)
```python
("top_3_massnahmen", "TOP_3_MASSNAHMEN_HTML"),  # ← Seite 2
...
("recommendations", "RECOMMENDATIONS_HTML"),      # ← Später im Report
```

**Seite 2 generiert:** `_build_top_3_massnahmen_html()` (Zeile 10849)
```python
def _build_top_3_massnahmen_html(top_3_recommendations: List, lang: str = "de") -> str:
    # Baut eigene HTML-Liste aus recommendations_engine Ergebnissen
```

**Später im Report:** `prompts/de/recommendations.md` generiert vollständige Sektion
- Hat Anti-Redundanz-Hinweis (Zeile 104-108):
```markdown
ANTI-REDUNDANZ (STRIKT!):
- KEINE Wiederholung von Quick Wins (→ siehe Abschnitt Quick Wins)
- KEINE Wiederholung von Roadmap-Inhalten (→ siehe Roadmap)
```

### Warum Duplikate entstehen:
1. `top_3_massnahmen` auf Seite 2 zeigt Top-3 aus `recommendations_engine.py`
2. Später generiert das LLM mit `recommendations.md` neue Empfehlungen
3. Das LLM kennt den Inhalt von Seite 2 nicht (kein Cross-Section-Context)
4. `redundancy_detector.py` existiert, prüft aber nicht `TOP_3_MASSNAHMEN_HTML` gegen `RECOMMENDATIONS_HTML`

**Datei:** `services/redundancy_detector.py` (Zeile 48-65)
```python
REDUNDANCY_SECTIONS: List[str] = [
    "exec_summary",
    "recommendations",  # ← Checked
    ...
]
# ← FEHLT: "top_3_massnahmen" in der Liste!
```

---

## Problem #6: "Strategischer Bruchpunkt" mit Enterprise-Sprache für Solo

### Root Cause
Das Problem liegt **NICHT im Code**, sondern im **LLM-Output**:

**Prompt versucht Solo-Anpassung:** `prompts/de/gamechanger.md` (Zeile 224-234)
```markdown
PERSONA-ANPASSUNG (COMPANY_SIZE):
{% if COMPANY_SIZE == "solo" %}
SOLO: Der Bruchpunkt bezieht sich auf persönliche Skalierungsgrenzen.
Die Transformation verändert, wie Wert geschaffen wird – nicht nur wie schnell.
{% elif COMPANY_SIZE == "team" %}
...
```

**Aber:** Das LLM (GPT-4/Claude) generiert trotzdem Enterprise-Begriffe wie:
- "Auswertungs-Engine"
- "skalierbare Analyse-Pipelines"
- "automatisierte Reporting-Infrastruktur"

### Warum passiert das?
1. GPT-4 wurde mit Enterprise-Consulting-Texten trainiert
2. Der Prompt gibt keine explizite **Wortverbots-Liste** für Solo
3. `services/prompt_enhancer.py` hat Solo-Filter (Zeile 1257-1260):
```python
"team_structure": "Sie + maximal 1–2 Freelancer",
"example_team": "1 Backend-Dev (Freelance, 20h)",
```
Aber: Begriffe wie "Engine", "Pipeline", "Infrastruktur" werden nicht gefiltert.

---

## Problem #7: 42 Seiten für Solo-Berater - zu lang

### Root Cause
**Architektur-Problem:** Keine globale Seitenbegrenzung.

**Einzelne Token-Budgets existieren:** (z.B. in `prompts/de/recommendations.md`)
```markdown
<!-- TOKEN-BUDGET: 600 (solo:0.8x=480, team:1.0x=600, kmu:1.15x=690) -->
```

**Aber:**
1. Es gibt 46 Sektionen, jede mit eigenem Budget
2. Keine Aggregat-Kontrolle: "Solo-Report maximal 15 Seiten"
3. `services/slim_mode_engine.py` existiert, wird aber nicht für Solo aktiviert:

**Datei:** `services/slim_mode_engine.py` (Zeile 1)
```python
"""
Sprint G22: Slim Mode Engine - Optimized Report Generation
...
"""
```
Dieses Modul scheint für schlanke Reports gedacht, aber der Trigger fehlt.

### Seitenzahl-Berechnung:
```
46 Sektionen × 0.8 Solo-Faktor = ~37 Seiten Content
+ Deckblatt, Inhaltsverzeichnis, Anhänge = ~42 Seiten
```

### Fehlende Kontrollmechanismen:
- Kein `MAX_PAGES_SOLO = 15` Parameter
- Kein dynamisches Weglassen von Sektionen basierend auf Größe
- Keine PDF-Längen-Validierung vor Auslieferung
