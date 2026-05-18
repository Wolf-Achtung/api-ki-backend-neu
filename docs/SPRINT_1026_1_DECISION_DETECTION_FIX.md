# Sprint 1026.1 — Decision-Section Detection-Fix

**Status:** Detection-Pattern erweitert um zwei Failure-Modi (Scenario C + E), Pipeline-Reihenfolge unverändert.

**Auslöser:** KIS-1187 / Briefing 1070 — derselbe Mid-Sentence-Cutoff-Bug auf R1 S.4 wie KIS-1186, obwohl PR #1026 produktiv ist. Bullet endete mit "...dem Schema Input", kein Ellipsis, semantisch eindeutig truncated, aber Detection feuerte nicht.

---

## Sektion 1: Diagnose (Phase 1)

### 1.1 Section-Key-Verhalten — ✅ kein Mismatch

`_DECISION_SECTION_KEYS` in `services/report_healer.py:3514-3518` enthielt bereits beide Varianten:
```python
_DECISION_SECTION_KEYS = {
    "executive_decision", "EXECUTIVE_DECISION_HTML",
    "roadmap_90d_decision", "ROADMAP_90D_DECISION_HTML",
    "gamechanger_decision", "GAMECHANGER_DECISION_HTML",
}
```

Die Loop `for _exec_key in list(result.keys())` iterierte korrekt über alle Keys. **Hypothese 1 (Section-Key-Mismatch) entkräftet.**

### 1.2 Ausführungsreihenfolge — ✅ kein Root Cause

`heal_report_html` Pipeline (Step-by-Step):

| Step | Fix | Location |
|---:|---|---|
| 2 | KEYS normalize | `normalize_section_keys` |
| 3 | A: Template phrases | `_apply_fix_a_recursive` |
| 4 | B: Persona language | `_apply_fix_b_recursive` |
| **5** | **C: Redundancy reduction** | **`reduce_redundancy` (`_extract_blocks`)** |
| 6 | D: ROI rules | `enforce_roi_rules` |
| 7 | F: Payback consistency | `enforce_payback_consistency` |
| **9** | **G: Segment budget** | **`apply_segment_budget` ← `[FIX-EXEC-DECISION-CLEAN]` lebt hier** |
| 10 | E: Trim incomplete | `trim_incomplete_sentences` |

FIX-C läuft VOR der Detection. Aber FIX-C entfernt nur **Duplikate** (via `_extract_blocks` über `<p>`, `<li>`, `<div class="callout|box|card">`) — keine einzelnen broken Bullets. Synthetic-Test Szenario B (FIX-C entfernt alle Siblings, broken Bullet bleibt als einziger übrig) bestätigt: Detection würde korrekt feuern. **Hypothese 2 (FIX-C räumt broken Bullet weg) entkräftet.**

### 1.3 Detection-Pattern — ⚠️ ROOT CAUSE

PR #1026 nutzte einen strikten Regex:
```python
_li_pattern = re.compile(r'<li\b[^>]*>(.*?)</li>', re.DOTALL | re.IGNORECASE)
```

Synthetic-Test mit 5 Szenarien gegen diesen Regex:

| Szenario | Beschreibung | Detection? | Repair? |
|---|---|:---:|:---:|
| A | Proper `<li>...</li>` mit truncated Tun | ✅ | ✅ |
| B | Nach FIX-C: nur truncated Bullet übrig | ✅ | ✅ |
| **C** | **LLM emittierte `<p>` statt `<li>`** | **❌** | **❌** |
| D | Loose `<li>` ohne `<ul>`-Parent | ✅ | ✅ |
| **E** | **`<li>` mit `</p>` geschlossen (Tag-Salat)** | **❌** | **❌** |

**Scenario C** (KIS-1187 vermutete Variante): Prompt-Vertrag-Violation — LLM emittierte `<p><strong>Tun:</strong>...</p>`-Bullets. Strict-Regex matcht 0× `<li>` → keine Detection.

**Scenario E:** LLM emittierte `<li><strong>Tun:</strong>...</p><li>...</li><li>...</li>` (mismatched closing). Non-greedy `(.*?)</li>` matcht vom ersten `<li>` bis zum nächsten echten `</li>` — schluckt also bis "Lassen: ... Standards." als EINEN Bullet, dessen letztes Zeichen `.` ist → kein Trigger.

**Hypothese 3 (Detection-Pattern unzureichend) = ROOT CAUSE.**

---

## Sektion 2: Patch (Phase 2)

### 2.1 Drei-Pass-Detection in `services/report_healer.py`

Detection-Block in `apply_segment_budget` (Position unverändert, **kein Reorder gegen FIX-C**) entscheidet anhand der `<li>`-Tag-Balance, welcher Pass läuft:

```python
_open_count = len(_li_open_pattern.findall(_exec_content))
_close_count = len(_li_close_pattern.findall(_exec_content))

if _open_count == 0:
    # Pass 3: <p>-fallback (Scenario C)
    _new_content, _total, _truncated = _exec_heal_p_bullets(_exec_content)
    _bullet_tag = "p"
elif _open_count == _close_count:
    # Pass 1: strict <li>...</li> (existing PR #1026 logic)
    _new_content, _total, _truncated = _exec_heal_strict_li(_exec_content)
    _bullet_tag = "li"
else:
    # Pass 2: tag-salat — split on <li>-boundaries (Scenario E)
    _new_content, _total, _truncated = _exec_heal_tag_salad(_exec_content)
    _bullet_tag = "li-salad"
```

#### Pass 2 (`_exec_heal_tag_salad`) — Tag-Salat-Handling

Findet alle `<li[^>]*>`-Öffnungspositionen via `finditer`. Jeder Bullet erstreckt sich von einer `<li>`-Öffnung bis zur nächsten oder zum schließenden `</ul>`/`</ol>`. Wenn der Bullet-Text truncated ist, wird der gesamte Bullet-Span durch `_LI_BULLET_FALLBACK` ersetzt. Andernfalls wird ein well-formed `<li>...</li>` mit dem Original-Open-Tag re-emittiert.

#### Pass 3 (`_exec_heal_p_bullets`) — `<p>`-Fallback

Iteriert über `<p>...</p>`-Matches. **Gate via `_bullet_prefix_re`**:
```python
_bullet_prefix_re = re.compile(
    r'<strong\b[^>]*>\s*(?:Tun|Lassen|Risiko|Stop)', re.IGNORECASE,
)
```
Nur `<p>`-Blöcke deren Body mit `<strong>Tun:|Lassen:|Risiko|Stop` beginnt werden als Bullet behandelt. Verhindert False-Positives auf Header (`<p><strong>Ihre Entscheidung in 3 Punkten</strong></p>`) und Intro-Text.

Bei Detection wird der `<p>` durch `_P_BULLET_FALLBACK = '<p><em>Weitere Punkte siehe Business Case und Roadmap.</em></p>'` ersetzt (struktur-analog).

### 2.2 Marker-Erweiterung

`[FIX-EXEC-DECISION-CLEAN]` bekommt neues Feld `bullet_tag` für Diagnose:

```
[FIX-EXEC-DECISION-CLEAN] section=executive_decision bullet_tag=p total=3 truncated=1 dropped=1
[FIX-EXEC-DECISION-CLEAN] section=executive_decision bullet_tag=li-salad total=3 truncated=1 dropped=1
[FIX-EXEC-DECISION-CLEAN] section=executive_decision bullet_tag=li total=3 truncated=1 dropped=1
```

Production-Filter können damit pro Bullet-Tag Statistiken bilden und LLM-Prompt-Compliance über die Zeit messen.

### 2.3 Validator-Parität in `services/report_validator.py`

`PlatinValidator._check_sentence_completeness` bekommt dieselbe Drei-Pass-Logik. Emittiert `TRUNCATED_LI`-Warnings für:
- `<p>-bullet ends with '...{text}'` (Scenario C)
- `bullet ends with '...{text}'` (Scenario A/E)

---

## Sektion 3: Tests

`tests/test_exec_decision_clean.py` wächst von 8 auf 18 Tests:

### Bestehend (PR #1026, alle weiter grün)

| Test | Verifikation |
|---|---|
| `test_truncated_bullet_dropped_and_replaced` | KIS-1186 strict `<li>` Reproduktion |
| `test_clean_section_unchanged` | No-Op auf sauberen Sektionen |
| `test_non_decision_section_ignored` | Scope-Isolation |
| `test_short_bullet_below_threshold_preserved` | 25-char Floor |
| `test_all_three_decision_sections_covered` | Alle 3 Sektionen |
| `test_truncated_li_emits_warning_despite_clean_section_end` | Validator strict |
| `test_clean_section_no_truncated_li_warning` | Validator False-Positive-Schutz |
| `test_non_decision_section_not_checked_per_li` | Validator-Scope |

### Neu (Sprint 1026.1)

| Test | Verifikation |
|---|---|
| `test_kis1187_p_bullets_scenario_c` | KIS-1187 Reproduktion — `<p>`-Bullets |
| `test_tag_salad_scenario_e` | Tag-Salat `<li>...</p><li>...` |
| `test_non_decision_p_bullets_not_repaired` | Scope-Isolation für `<p>`-Pass |
| `test_p_bullets_all_clean_no_repair` | No-Op `<p>`-only sauber |
| `test_p_bullets_only_non_bullet_p_unchanged` | Header-`<p>` ohne Prefix |
| `test_tag_salad_all_clean_no_repair` | Tag-Salat aber alle terminal |
| `test_p_bullet_truncation_emits_warning` | Validator Scenario C |
| `test_tag_salad_truncation_emits_warning` | Validator Scenario E |
| `test_p_bullet_clean_section_no_warning` | Validator False-Positive |
| `test_non_bullet_p_in_decision_section_not_flagged` | Validator Scope |

Local full suite: **6410 passed, 10 skipped, 0 failed.**

---

## Sektion 4: Validierungsplan (Production-Smoke)

1. Test-Briefing absenden (Solo + Beratung + `ki_kompetenz=hoch`)
2. R1-PDF S.4 prüfen:
   - **Best Case (LLM hält Vertrag):** kein Marker, saubere Bullets
   - **Healing Case Scenario A/B (well-formed):** `bullet_tag=li` + Fallback an Position des truncated Bullet
   - **Healing Case Scenario C (`<p>`-Bullets):** `bullet_tag=p` + Fallback als `<p>`-Element analog
   - **Healing Case Scenario E (Tag-Salat):** `bullet_tag=li-salad` + Fallback + re-emittierte well-formed Siblings
3. Production-Logs nach `[FIX-EXEC-DECISION-CLEAN]` filtern, `bullet_tag`-Distribution prüfen
4. Nach 48 h / ≥10 Briefings: wenn `bullet_tag=p` oder `bullet_tag=li-salad` > 10% → LLM-Compliance-Issue → C2.2 (Re-Gen) priorisieren

---

## Sektion 5: Geänderte Dateien

| Datei | Δ |
|---|---|
| `services/report_healer.py` | +112 / −44 LOC (3-Pass-Detection + Helper-Funktionen) |
| `services/report_validator.py` | +43 / −6 LOC (Validator-Parität) |
| `tests/test_exec_decision_clean.py` | +148 LOC (10 neue Tests, 8 bestehende unverändert) |
| `docs/SPRINT_1026_1_DECISION_DETECTION_FIX.md` | +160 (neu) |

---

## Sektion 6: Out-of-Scope (bestätigt aus Briefing)

- KEINE C2.2 H1 Re-Gen Logik (separates Sprint)
- KEINE Quick-Wins-Tile-Header-Bugs
- KEINE Compact-Engine-Effizienz
- KEINE TRANSPARENCY_BOX Email-Leak-Refinement
- Fokus ausschließlich auf executive_decision Detection-Robustheit
