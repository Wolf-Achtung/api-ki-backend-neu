# ANALYSE: FIX-B36b Trigger-Bug & TRUNCATED Root Cause

**Datum:** 2026-03-01
**Analyst:** Claude (Session kdeFo)
**Status:** Analyse abgeschlossen, wartet auf Wolf-Freigabe

---

## 1. PLATIN+++ TRUNCATED-Detection: Exakter Code

**Datei:** `services/report_validator.py`
**Funktion:** `_check_sentence_completeness()` (Zeile 3250-3272)

```python
# Zeile 3250-3272:
def _check_sentence_completeness(self) -> None:
    for section_key, html in self.sections.items():
        if not isinstance(html, str) or section_key.startswith("_"):
            continue
        if section_key in self.TRUNCATED_SAFE_SECTIONS:   # 10 Sections ausgenommen
            continue
        text = re.sub(r'<[^>]+>', '', html).strip()       # HTML-Tags entfernen
        if text and len(text) > 50:
            if not text[-1] in '.!?:)"\u00BB\u201D':      # ← DAS IST DER CHECK
                # Safe-Ending-Liste prüfen (17 Einträge)
                _is_safe = False
                _text_end = text[-40:]
                for _safe in self.TRUNCATED_SAFE_ENDINGS:
                    if _text_end.endswith(_safe):
                        _is_safe = True
                        break
                # Regex-Safe: Zahlen, Bindestriche, %, €, Jahreszahlen
                if not _is_safe and re.search(r'(?:\d+[).]|\w+[-–]\w+|%|€|\d{4})$', _text_end):
                    _is_safe = True
                if not _is_safe:
                    self.warnings.append(f"TRUNCATED: {section_key} ends with '...{text[-20:]}'")
```

### TRUNCATED-Kriterium (Zeile 3260):
```
text[-1] NOT IN {'.', '!', '?', ':', ')', '"', '»', '\u201D'}
```

**Der Validator prüft NICHT auf "..."!**
Er prüft ob das **letzte Zeichen** des Plain-Texts (nach HTML-Strip) ein Satzschluss-Zeichen ist.

### Safe-Sections (nicht geprüft, Zeile 3237-3248):
```
BUSINESS_CASE_TABLE_HTML, TOOLS_HTML, KI_STACK_SUMMARY_HTML,
BENCHMARK_ENGINE_HTML, TRANSPARENCY_BOX_HTML, transparency_box,
AI_ACT_COMPLIANCE_HTML, DUTY_MATRIX_HTML, ROADMAP_90D_HTML,
NINETY_DAY_PLAN_HTML
```

### Safe-Endings (Zeile 3216-3234):
```
Cap: 200%, Business Case, Erweiterbarkeit, [anonymisiert],
Risiko Niedrig, Monat 4-6/7-12, Phase 1/2/3, KI-Stack,
Quick Wins, Roadmap, Förderprogramme, Governance
```

---

## 2. ELLIPSIS-FIX Interaktion

**Datei:** `services/content_quality_enforcer.py`
**Funktion:** `fix_truncation_ellipsis()` (Zeile 896-923)
**Aufgerufen von:** `apply_ellipsis_fix()` (Zeile 925-947)

### Was passiert:
1. Findet Wörter die mit `…` oder `...` enden: `r'\b\w+[…..]{1,3}(?=\s|<|$|\*)'`
2. **ENTFERNT das ganze Wort** (nicht ersetzen durch Punkt!)
3. Räumt doppelte Leerzeichen auf
4. Betrifft nur 8 Sections: RISKS, RECOMMENDATIONS, QUICK_WINS, GAMECHANGER

### Beispiel:
```
VORHER:  "Die Lösung ist daue…"
NACHHER: "Die Lösung ist"         ← KEIN Punkt! Endet auf "ist"
```

### Konsequenz:
ELLIPSIS-FIX erzeugt Sätze die **ohne Satzzeichen enden**, weil es das abgeschnittene
Wort entfernt aber KEINEN Punkt hinzufügt. Das verstärkt das TRUNCATED-Problem sogar!

---

## 3. Pipeline-Reihenfolge (bestätigte Sequenz mit Zeilennummern)

```
gpt_analyze.py:
│
├─ Zeile 14188:  apply_all_quality_enforcers()
│                └─ ELLIPSIS-FIX: Entfernt "daue…" → "daue" (kein Punkt!)
│                └─ Betrifft 8 Sections
│
├─ Zeile 14368:  apply_all_quality_enforcers() (2. Durchlauf)
│
├─ Zeile 17589:  heal_report_html() ← CONDITIONAL (nur Grade C/D)
│
├─ Zeile 17644:  ██ PLATIN+++ VALIDATOR ██
│                └─ _check_sentence_completeness()
│                └─ Prüft: text[-1] in '.!?:)"»"'
│                └─ Erzeugt: "TRUNCATED: SECTION ends with '...xyz'"
│                └─ Speichert: sections["_PLATIN_WARNINGS"] = count
│                ⚠️ PRÜFT PRE-HEALER CONTENT!
│
├─ ... (1400 Zeilen weiterer Code) ...
│
└─ Zeile 19070:  ██ MAIN HEALER ██
                 └─ FIX-G: Sentence-Trimming (Zeile 3190-3213)
                 └─ FIX-B36b: endswith('...') Check (Zeile 3220)
                    ⚠️ LÄUFT NACH DEM VALIDATOR!
                    ⚠️ TRIGGER GREIFT NIE (siehe Root Cause)
```

---

## 4. Root Cause Diagramm

```
                    ┌──────────────────────────────┐
                    │     LLM generiert Content     │
                    │  (einige Sections enden ohne  │
                    │   Satzzeichen oder mit "…")   │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  ELLIPSIS-FIX (Zeile 14188)   │
                    │  Entfernt "daue…" → ""        │
                    │  ⚠️ KEIN Punkt hinzugefügt!   │
                    │  → Satz endet auf "ist" o.ä.  │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  PLATIN VALIDATOR (Zeile 17644)│
                    │  Prüft: text[-1] ∈ {.!?:)"»"} │
                    │                                │
                    │  "...Mita"      → TRUNCATED ❌ │
                    │  "...Compliance" → TRUNCATED ❌ │
                    │  "...nötig"     → TRUNCATED ❌ │
                    │                                │
                    │  → 10 TRUNCATED Warnings!      │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  MAIN HEALER (Zeile 19070)    │
                    │                                │
                    │  FIX-G: Trimmt an Satzgrenzen  │
                    │  → Endet auf ".", "!", "?"      │
                    │                                 │
                    │  FIX-B36b: endswith('...')?     │
                    │  → NEIN! (endet auf Wörter)     │
                    │  → B36b triggert NIE             │
                    │                                  │
                    │  ⚠️ ZU SPÄT: Warnings sind      │
                    │     bereits geloggt!             │
                    └──────────────────────────────────┘

    ROOT CAUSE SUMMARY:
    ═══════════════════
    Problem 1: PIPELINE-ORDERING
       Validator (17644) läuft VOR dem Healer (19070)
       → Warnings werden auf PRE-HEALER Content erzeugt
       → Healer-Fixes können Warnings nicht verhindern

    Problem 2: B36b TRIGGER-MISMATCH
       B36b prüft:   endswith('...') oder endswith('…')
       Validator prüft: text[-1] NOT IN {.!?:)"»"}
       → B36b-Trigger matcht KEIN reales Szenario:
         - ELLIPSIS-FIX hat "..." schon entfernt
         - FIX-G schneidet an Satzgrenzen (→ endet auf ".")
         - LLM-Output endet auf Wörtern, nicht auf "..."

    Problem 3: ELLIPSIS-FIX VERSCHÄRFT
       Entfernt "daue…" aber fügt keinen Punkt hinzu
       → Erzeugt NEUE Sätze ohne Satzschluss
       → ELLIPSIS-FIX ist MITVERURSACHER der TRUNCATED Warnings
```

---

## 5. Empfohlener Fix-Ansatz: D (Kombination) — 2 Teile

### Warum Ansatz D?

| Ansatz | Löst Ordering? | Löst Trigger? | Risiko | Aufwand |
|--------|---------------|---------------|--------|---------|
| A: B36b Trigger erweitern | ❌ (Healer läuft nach Validator) | ✅ | LOW | LOW |
| B: Post-Healer Clean Ending | ❌ (Validator hat Warnings schon) | ✅ | LOW | LOW |
| C: Validator anpassen | ✅ (weniger false positives) | ❌ (Content bleibt kaputt) | MEDIUM | LOW |
| **D: Kombination** | **✅** | **✅** | **LOW** | **MEDIUM** |

Ansatz A oder B allein lösen das Ordering-Problem nicht — die TRUNCATED Warnings
werden VOR dem Healer geloggt und zählen für den Report Score.

### Teil 1: FIX-B38a — Clean-Ending im Healer (report_healer.py)

**Was:** B36b-Trigger von `endswith('...')` auf Validator-Kriterium umstellen.

**Wo:** `services/report_healer.py`, nach Zeile 3213 (nach FIX-G Trimming)

```python
# FIX-B38a: Clean-Ending Check — matcht exakt PLATIN+++ Validator-Kriterium
# B36b prüfte auf endswith('...') was nie zutrifft (ELLIPSIS-FIX entfernt "..."
# vorher, FIX-G schneidet an Satzgrenzen). Der Validator prüft aber auf
# fehlendes Satzschluss-Zeichen: text[-1] not in '.!?:)"»"'
_text_for_check = re.sub(r'<[^>]+>', '', processed).strip()
if _text_for_check and len(_text_for_check) > 50:
    _last_char = _text_for_check[-1]
    if _last_char not in '.!?:)"\u00BB\u201D':
        # Text endet ohne Satzschluss → letzten vollständigen Satz finden
        _clean = re.sub(r'(</(?:p|li|div|span|td|tr|section)>\s*)*$', '', processed).rstrip()
        _last_period = max(_clean.rfind('. '), _clean.rfind('.</'), _clean.rfind('.'))
        _last_excl = max(_clean.rfind('! '), _clean.rfind('!</'), _clean.rfind('!'))
        _last_quest = max(_clean.rfind('? '), _clean.rfind('?</'), _clean.rfind('?'))
        _best_end = max(_last_period, _last_excl, _last_quest)
        if _best_end > len(_clean) * 0.7:  # Keep at least 70%
            processed = _clean[:_best_end + 1]
            # Re-close open HTML tags
            _open_tags = re.findall(r'<(p|li|ul|ol|div|section|span|td|tr|table)(?:\s[^>]*)?>', processed)
            _close_tags = re.findall(r'</(p|li|ul|ol|div|section|span|td|tr|table)>', processed)
            _tag_counts: dict = {}
            for _t in _open_tags:
                _tag_counts[_t] = _tag_counts.get(_t, 0) + 1
            for _t in _close_tags:
                _tag_counts[_t] = _tag_counts.get(_t, 0) - 1
            for _tag, _cnt in reversed(list(_tag_counts.items())):
                for _ in range(max(0, _cnt)):
                    processed += f"</{_tag}>"
            log.info(
                "[FIX-B38a] Section '%s' clean-ending applied: "
                "ends with '%s' (no terminal punctuation)",
                section_name, _last_char
            )
```

**Problem:** Healer läuft NACH dem Validator → behebt Content, aber nicht die Warnings.

### Teil 2: FIX-B38b — Validator NACH Healer verschieben (gpt_analyze.py)

**Was:** Den PLATIN+++ Validator-Block von Zeile 17644 nach Zeile ~19108 verschieben.

**Wo:** `gpt_analyze.py`

**Warum sicher:**
- `_p_passed`, `_p_errors`, `_p_warnings` werden NUR in `sections[]` gespeichert
- Sie werden NICHT für Control-Flow verwendet (kein `if _p_passed`)
- `total_warnings` und `unified_grade` werden VOR dem Validator berechnet (Zeile 17458-17542)
- Der Validator ist rein diagnostisch — er loggt und speichert Metadaten

**Vorher:**
```
Zeile 17644: PLATIN+++ Validator  ← prüft pre-healer Content
Zeile 19070: Main Healer           ← fixt Content, zu spät für Validator
```

**Nachher:**
```
Zeile 19070: Main Healer           ← fixt Content (inkl. B38a Clean-Ending)
Zeile ~19108: PLATIN+++ Validator  ← prüft post-healer Content → TRUNCATED ≤ 2
```

### Erwartetes Ergebnis nach B38a + B38b:

```
VORHER:  TRUNCATED = 10 (alle 3 Segmente)
NACHHER: TRUNCATED ≤ 2
  - B38a: Sections enden auf vollständigem Satz (Content-Fix)
  - B38b: Validator prüft den geheilten Content (korrektes Counting)

Verbleibende TRUNCATED wären nur:
  - Sections die keine Satzgrenze bei 70%+ haben
  - Sections die by-design ohne Punkt enden (→ SAFE_ENDINGS erweitern)
```

---

## 6. Konkreter Code-Vorschlag

### Datei 1: `services/report_healer.py` — FIX-B38a

**Position:** Nach Zeile 3213 (nach FIX-G Logging), VOR dem bestehenden FIX-B36b Block.

```python
        # --- FIX-B38a: Clean-Ending für PLATIN+++ TRUNCATED-Prevention ---
        # B36b prüfte endswith('...') — triggert nie, weil:
        #   1) ELLIPSIS-FIX entfernt "..." vor dem Healer
        #   2) FIX-G schneidet an Satzgrenzen (endet auf ".", "!", "?")
        # Der PLATIN+++ Validator prüft: text[-1] NOT IN {.!?:)"»"}
        # B38a matcht exakt dieses Kriterium.
        _text_for_check = re.sub(r'<[^>]+>', '', processed).strip()
        if _text_for_check and len(_text_for_check) > 50:
            _last_char = _text_for_check[-1]
            if _last_char not in '.!?:)"\u00BB\u201D':
                # Text endet ohne Satzschluss → am letzten vollständigen Satz abschneiden
                _ce_clean = re.sub(r'(</(?:p|li|div|span|td|tr|section)>\s*)*$', '', processed).rstrip()
                _ce_period = max(_ce_clean.rfind('. '), _ce_clean.rfind('.</'), _ce_clean.rfind('.'))
                _ce_excl = max(_ce_clean.rfind('! '), _ce_clean.rfind('!</'), _ce_clean.rfind('!'))
                _ce_quest = max(_ce_clean.rfind('? '), _ce_clean.rfind('?</'), _ce_clean.rfind('?'))
                _ce_best = max(_ce_period, _ce_excl, _ce_quest)
                if _ce_best > len(_ce_clean) * 0.7:
                    processed = _ce_clean[:_ce_best + 1]
                    # Re-close open HTML tags
                    _ce_open = re.findall(r'<(p|li|ul|ol|div|section|span|td|tr|table)(?:\s[^>]*)?>', processed)
                    _ce_close = re.findall(r'</(p|li|ul|ol|div|section|span|td|tr|table)>', processed)
                    _ce_counts: dict = {}
                    for _t in _ce_open:
                        _ce_counts[_t] = _ce_counts.get(_t, 0) + 1
                    for _t in _ce_close:
                        _ce_counts[_t] = _ce_counts.get(_t, 0) - 1
                    for _tag, _cnt in reversed(list(_ce_counts.items())):
                        for _ in range(max(0, _cnt)):
                            processed += f"</{_tag}>"
                    log.info(
                        "[FIX-B38a] Section '%s' clean-ending applied: "
                        "ends with '%s' (no terminal punctuation)",
                        section_name, _last_char
                    )
```

### Datei 2: `gpt_analyze.py` — FIX-B38b

**Aktion:** Block Zeile 17644-17656 ausschneiden und nach Zeile ~19108 einfügen.

**Ausschnitt (unverändert, nur verschoben):**
```python
    # === PLATIN+++ PRE-RENDER VALIDATION ===
    # FIX-B38b: Moved AFTER healer (was line 17644) so validator checks
    # post-healer content. Previously, TRUNCATED warnings were counted on
    # pre-healer content, making FIX-B36b/B38a ineffective.
    try:
        from services.report_validator import validate_platin_ppp
        _canon_bc = sections.get("_canonical_bc", {})
        _p_scores = {"governance": sections.get("gov_score", 50), "security": sections.get("sec_score", 50)}
        _p_meta = {"hauptleistung": answers.get("hauptleistung", ""), "bundesland": answers.get("bundesland", "")}
        _p_passed, _p_errors, _p_warnings = validate_platin_ppp(sections, _canon_bc, _p_scores, _p_meta)
        sections["_PLATIN_VALIDATION_PASSED"] = _p_passed
        sections["_PLATIN_ERRORS"] = len(_p_errors)
        sections["_PLATIN_WARNINGS"] = len(_p_warnings)
        log.info(f"[{run_id}] [PLATIN+++] Post-healer validation: passed={_p_passed}, errors={len(_p_errors)}, warnings={len(_p_warnings)}")
    except Exception as pv_err:
        log.warning(f"[{run_id}] [PLATIN+++] Validation failed to run: {pv_err}")
```

---

## 7. Offene Fragen für Wolf

1. **ELLIPSIS-FIX Verbesserung:** Soll `fix_truncation_ellipsis()` nach dem Entfernen
   eines Worts einen Punkt hinzufügen? Das würde eine zweite TRUNCATED-Quelle eliminieren.
   (Unabhängig von B38a/B38b)

2. **SAFE_SECTIONS erweitern:** Gibt es Sections die by-design ohne Punkt enden und
   noch nicht in `TRUNCATED_SAFE_SECTIONS` stehen?

3. **Validator verschieben (B38b):** Gibt es externe Systeme die die PLATIN-Ergebnisse
   VOR dem Healer erwarten? (Railway-Logs, Monitoring, Dashboards?)

4. **Risiko-Appetit:** B38a allein fixt den Content aber nicht die Warnings.
   B38b dazu macht die Warnings korrekt. Beides zusammen oder nur B38a?
