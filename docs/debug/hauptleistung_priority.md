# Hauptleistung Priority - System Documentation

**Version:** v14.35.19
**Datum:** 2026-01-14

## Übersicht

Dieses Dokument beschreibt die Implementierung der "Hauptleistung-First" Priorität für die Report-Individualisierung.

### Prioritäts-Reihenfolge

1. **Hauptleistung** (primäres Individualisierungs-Kriterium)
2. **Unternehmensgröße** (3 Stufen: solo, team, kmu)
3. **Branche** (13 Optionen)

---

## Datenfluss

### 1. Input (API/Formular)

```
Request → /api/briefings/submit
├── hauptleistung: "KI-Beratung und Assessment-Tools"
├── unternehmensgroesse: "solo" | "team" | "kmu"
└── branche: "beratung" | "it_software" | ... (13 Optionen)
```

### 2. Normalisierung (`services/answers_normalizer.py`)

```python
# Line 269-270
out["HAUPTLEISTUNG"] = out.get("hauptleistung", "") or "—"
out["HAUPTLEISTUNG_SHORT"] = _shorten_hauptleistung(out["HAUPTLEISTUNG"])

# Line 252-258
out["BRANCHE_LABEL"] = BRANCHEN_LABELS.get(branche, branche)
out["UNTERNEHMENSGROESSE_LABEL"] = UNTERNEHMENSGROESSEN_LABELS.get(size, size)
```

### 3. Strategic Context Block (`gpt_analyze.py`)

```python
# Line 1102-1178: build_strategic_context_block()
# v14.35.19: HAUPTLEISTUNG ist jetzt ERSTES Feld

def build_strategic_context_block(answers, lang="de"):
    lines = []

    # HAUPTLEISTUNG ZUERST - primäres Individualisierungs-Kriterium
    if answers.get("hauptleistung"):
        lines.append(f"🎯 Kernleistung (Hauptleistung):\n{val}")

    # Dann weitere Felder...
    if answers.get("strategische_ziele"):
        lines.append(f"Strategische Prioritäten:\n{val}")
```

### 4. Prompt Injection (`services/prompt_enhancer.py`)

```python
# Line 1383-1534: build_context_block()
# v14.35.19: hauptleistung wird als ERSTES injiziert

def build_context_block(briefing_data):
    hauptleistung = briefing_data.get("hauptleistung", "")
    # ...
    return hauptleistung_html + branch_html + size_html
```

### 5. Validation (`services/report_validator.py`)

```python
# Line 1781-1870: _check_hauptleistung_limits()
# Prüft Vorkommen von hauptleistung in Executive Summary und Recommendations

def _check_hauptleistung_limits():
    # Executive Summary: Minimum 3x
    # Recommendations: Minimum 2x
    # Warning bei Überschreitung
```

### 6. Enforcement (`services/content_quality_enforcer.py`)

```python
# Line 267-520: HAUPTLEISTUNG-ENFORCER
# Injiziert hauptleistung wenn unter Minimum

def inject_hauptleistung_executive(html, hauptleistung, current_count, target=4):
    # Ersetzt generische Phrasen durch hauptleistung-Version

def inject_hauptleistung_recommendations(html, hauptleistung, current_count, target=3):
    # Injiziert hauptleistung in Recommendations
```

---

## Kanonische Werte

### Unternehmensgröße (3 Stufen)

| Key | Label | Beschreibung |
|-----|-------|--------------|
| `solo` | Solo | 1 (Solo-Selbstständig/Freiberuflich) |
| `team` | 2–10 (Kleines Team) | Kleines Team mit 2-10 Mitarbeitern |
| `kmu` | 11–100 (KMU) | KMU mit 11-100 Mitarbeitern |

### Branche (13 Optionen)

| Key | Label |
|-----|-------|
| `beratung` | Beratung & Dienstleistungen |
| `marketing` | Marketing & Werbung |
| `it_software` | IT & Software |
| `finanzen` | Finanzen & Versicherungen |
| `handel` | Handel & E-Commerce |
| `bildung` | Bildung |
| `verwaltung` | Verwaltung |
| `gesundheit` | Gesundheit & Pflege |
| `bau` | Bauwesen & Architektur |
| `medien` | Medien & Kreativwirtschaft |
| `industrie` | Industrie & Produktion |
| `logistik` | Transport & Logistik |
| `gastronomie` | Gastronomie & Tourismus |

---

## Acceptance Criteria

### Go/No-Go Checklist

- [ ] Hauptleistung bleibt identisch (Input = Output)
- [ ] Branch/Size werden korrekt gemappt
- [ ] Hauptleistung ist im Executive nachweisbar (≥3x)
- [ ] Hauptleistung ist in Recommendations nachweisbar (≥2x)
- [ ] Keine "silent fallback" Überschreibungen ohne Log

### Test-Kommandos

```bash
# Unit Tests
pytest tests/test_hauptleistung_priority.py -v

# Grep Acceptance auf final_html
grep -n "hauptleistung\|HAUPTLEISTUNG" artifacts/debug_final.html | head -20
```

---

## Änderungshistorie

### v14.35.19 (2026-01-14)

1. **BRANCHEN_LABELS**: 13. Branche "Gastronomie & Tourismus" hinzugefügt
2. **build_strategic_context_block()**: Hauptleistung jetzt an ERSTER Position
3. **build_context_block()**: Hauptleistung-HTML-Block vor Branch/Size injiziert
4. **Tests**: 39 Kombinationen (3 Größen × 13 Branchen) implementiert
