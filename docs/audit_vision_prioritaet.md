# Ergebnis: vision_prioritaet Audit

**Datum:** 2026-03-22
**Scope:** api-ki-backend-neu (inkl. adapter/)
**Methode:** Vollständiger Grep über alle Dateitypen (.py, .js, .json, .yaml, .md, .j2, .html, .txt)

---

## Treffer-Übersicht

| # | Datei | Zeile | Kontext | Typ erwartet | Verwendung | Report-Ziel |
|---|-------|-------|---------|--------------|------------|-------------|
| 1 | `gpt_analyze.py` | 1730 | `roi = answers.get("vision_prioritaet", "")` | **String** | Scoring: mapped zu `roi_expected` (high/medium/low) | Alle (Scoring-Pipeline) |
| 2 | `gpt_analyze.py` | 1731 | `m["roi_expected"] = "high" if roi in [...]` | String (Vergleich via `in`) | Scoring: String-Vergleich gegen bekannte Werte | Alle (Scoring-Pipeline) |
| 3 | `gpt_analyze.py` | 1791–1792 | `roi = m.get("roi_expected", ""); val += 7 if roi in ["high","medium"]` | String (indirekt) | Scoring: Punktevergabe für Value-Dimension | Alle (Score) |
| 4 | `gpt_analyze.py` | 9080 | `"VISION_PRIORITAET": vision_3_jahre` | ⚠️ **Achtung: Wird auf `vision_3_jahre` gemapped, NICHT auf `vision_prioritaet`!** | Prompt-Variable (Namenskollision/Legacy) | Prompt-Context |
| 5 | `adapter/context_adapter.js` | 58 | `ctx.VISION_PRIORITAET = form.vision_prioritaet \|\| ""` | **String** | Context-Adapter: Übergibt Formularwert als String in Prompt-Context | Prompt-Context |
| 6 | `services/profile_box.py` | 41 | `"vision_prioritaet": "Strategischer Hebel"` | String (Label-Mapping) | Display-Label für Profil-Box im Report | Alle Reports (Profil-Box) |
| 7 | `services/profile_box.py` | 65 | In `ORDER`-Liste | String (Reihenfolge-Definition) | Anzeigereihenfolge in der Profil-Box | Alle Reports (Profil-Box) |
| 8 | `services/coverage_guard.py` | 28 | In `EXPECTED_FIELDS`-Liste | String (Feld-Name) | Validierung: Prüft ob Feld im Briefing vorhanden ist | Validierung |
| 9 | `data/test_profiles_gold/*.json` | div. | `"vision_prioritaet": "hoch"` / `"high"` / `"medium"` | **String** (immer Single-Value) | Test-Daten (Gold-Profile) | Test |
| 10 | `data/test_profiles_en/*.json` | div. | `"vision_prioritaet": "high"` / `"medium"` | **String** (immer Single-Value) | Test-Daten (EN-Profile) | Test |
| 11 | `data/test_profiles_gold_optimized/*.json` | div. | `"vision_prioritaet": "hoch"` / `"high"` | **String** (immer Single-Value) | Test-Daten (optimierte Gold-Profile) | Test |

---

## Detail-Analyse je Fundstelle

### 1. Scoring-Pipeline (`gpt_analyze.py:1730–1731`)

```python
roi = answers.get("vision_prioritaet", "")
m["roi_expected"] = "high" if roi in ["marktfuehrerschaft", "gpt_services", "datenprodukte"] else ("medium" if roi and roi != "keine_angabe" else "low")
```

**Kritisch:** Der Wert wird direkt als **String** gegen eine Liste bekannter Werte verglichen (`in ["marktfuehrerschaft", "gpt_services", "datenprodukte"]`). Ein Array würde hier **niemals matchen** — `["marktfuehrerschaft"] in ["marktfuehrerschaft", ...]` ist `False` in Python.

**Downstream-Effekt:** `roi_expected` fließt in die **Value-Scoring-Dimension** (Zeile 1791–1792), wo es 7 Punkte bei "high"/"medium" oder 3 Punkte bei "low" gibt. Dies beeinflusst den **Gesamtscore aller Reports**.

### 2. Prompt-Variable (`gpt_analyze.py:9080`)

```python
"VISION_PRIORITAET": vision_3_jahre,
```

**Achtung — Namenskollision:** Die Prompt-Variable `VISION_PRIORITAET` wird **nicht** mit dem Formularfeld `vision_prioritaet` befüllt, sondern mit `vision_3_jahre` (einem Freetext-Feld). Das ist vermutlich ein Legacy-Mapping. Das tatsächliche `vision_prioritaet` Formularfeld wird in Prompts **nicht direkt injiziert** — es wirkt nur indirekt über den Score.

### 3. Context-Adapter (`adapter/context_adapter.js:58`)

```javascript
ctx.VISION_PRIORITAET = form.vision_prioritaet || "";
```

Hier wird der **tatsächliche** Formularwert als String in den Context gelegt. Falls `VISION_PRIORITAET` in Prompt-Templates referenziert wird, käme hier der echte Wert an. **Allerdings:** In keinem einzigen Prompt-Template unter `prompts/` wird `VISION_PRIORITAET` oder `vision_prioritaet` referenziert. Die Variable ist also aktuell in Prompts **ungenutzt**.

### 4. Profile-Box (`services/profile_box.py:41, 65`)

Die `_fmt()`-Funktion (Zeile 70–73) hat bereits Array-Support:
```python
def _fmt(v):
    if isinstance(v, list):
        return ", ".join([str(x) for x in v if str(x).strip()])
    return str(v or "").strip()
```

**→ Profile-Box funktioniert bereits mit Arrays!** Keine Änderung nötig.

### 5. Coverage-Guard (`services/coverage_guard.py:28`)

Prüft nur ob das Feld **existiert** (nicht leer/None), nicht den Typ. **→ Kein Problem bei Array-Umstellung.**

### 6. Nicht betroffen (explizit geprüft)

| Datei | Ergebnis |
|-------|----------|
| `services/extra_sections.py` | Kein Treffer |
| `services/html_enhancer.py` | Kein Treffer |
| `services/budget_calculator.py` | Existiert nicht |
| `services/quality_enforcer.py` | Existiert nicht |
| `prompts/**/*` | Kein Treffer (weder als Variable noch als Feldname) |
| `tests/**/*.py` | Kein Treffer |

---

## Analyse

- **Gesamtzahl Stellen die bei Änderung zu Array angepasst werden müssten: 3**
  1. `gpt_analyze.py:1730–1731` — Scoring-Logik (KRITISCH)
  2. `adapter/context_adapter.js:58` — Context-Adapter (NIEDRIG)
  3. `data/test_profiles_*/*.json` — ca. 19 Testprofile (MECHANISCH)

- **Risikobewertung: NIEDRIG**
  - Nur eine einzige kritische Code-Stelle (Scoring)
  - Keine direkte Prompt-Injection
  - Profile-Box + Coverage-Guard sind bereits Array-kompatibel

- **Betroffene Reports:** Alle (über Scoring-Pipeline), aber **kein Report** nutzt den Wert direkt in Prompts

---

## Stellen die brechen würden wenn Array statt String kommt

| # | Datei | Zeile | Warum es bricht | Fix |
|---|-------|-------|-----------------|-----|
| 1 | `gpt_analyze.py` | 1730–1731 | `roi in ["marktfuehrerschaft", ...]` — Array matcht nie gegen String-Liste | Iteration über Array + `any()` |
| 2 | `gpt_analyze.py` | 1731 | `roi != "keine_angabe"` und `roi and ...` — Truthiness-Check funktioniert mit Array, aber Vergleich ist falsch | Intersection-Check statt `==` |
| 3 | `adapter/context_adapter.js` | 58 | `form.vision_prioritaet || ""` gibt Array-Objekt statt String zurück | `.join(", ")` oder `JSON.stringify()` |

---

## Empfehlung

**Aufwand für Umstellung auf Checkbox (Mehrfachauswahl): GERING (ca. 1–2h)**

Konkret anzupassen:

1. **`gpt_analyze.py:1730–1731`** — Scoring-Logik:
   ```python
   # Vorher:
   roi = answers.get("vision_prioritaet", "")
   m["roi_expected"] = "high" if roi in [...] else ...

   # Nachher:
   roi_raw = answers.get("vision_prioritaet", "")
   roi_list = roi_raw if isinstance(roi_raw, list) else ([roi_raw] if roi_raw else [])
   high_values = {"marktfuehrerschaft", "gpt_services", "datenprodukte"}
   m["roi_expected"] = "high" if high_values & set(roi_list) else ("medium" if roi_list and "keine_angabe" not in roi_list else "low")
   ```

2. **`adapter/context_adapter.js:58`** — Array-zu-String:
   ```javascript
   ctx.VISION_PRIORITAET = Array.isArray(form.vision_prioritaet)
     ? form.vision_prioritaet.join(", ")
     : (form.vision_prioritaet || "");
   ```

3. **19 Test-Profile** — Werte von String zu Array ändern (mechanisch, via Skript möglich)

4. **Keine Änderung nötig** in: `profile_box.py`, `coverage_guard.py`, Prompts
