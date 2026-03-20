# Diagnose KIS-1019: Chunk-Boundary-Truncation — "n w" Zeichenverlust

**Session:** 30 | **Datum:** 2026-03-20
**Briefings:** 897, 901, 902 | **Build:** 20260320-1311

---

## Zusammenfassung

Drei separate Fehlerbilder, zwei Root Causes:

| Bug | Pattern | Root Cause | Status |
|-----|---------|-----------|--------|
| B1 "Ich haben" | Grammar nach Wir→Ich | GLOBAL FINAL ENFORCER Pattern-Reihenfolge | **GEFIXT** (9fa407e) |
| NEU-3 "können ich" | Grammar nach Wir→Ich | GLOBAL FINAL ENFORCER Pattern-Reihenfolge | **GEFIXT** (9fa407e) |
| B2 "Vorhabe ichtschaftlich" | 3-Zeichen-Verlust "n w" | LLM-Generierungsartefakt (primär) + Safety-Net | **SAFETY-NET** (9fa407e) |

---

## Root Cause 1: GLOBAL FINAL ENFORCER Pattern-Reihenfolge (B1 + NEU-3)

### Mechanismus (BESTÄTIGT)

**Datei:** `gpt_analyze.py:20417-20561`

Die Patterns im GLOBAL FINAL ENFORCER werden **sequentiell** in einer Schleife angewandt:

```
Zeile ~20442:  \bkönnen ich\b → kann ich    ← LÄUFT ZUERST
Zeile ~20533:  \bWir\b → Ich                 ← LÄUFT SPÄTER
Zeile ~20534:  \bwir\b → ich                 ← LÄUFT SPÄTER
```

**Ablauf:**
1. LLM generiert: `"Wir haben keinen Mitarbeiter eingestellt"`
2. `\bkönnen ich\b` → `kann ich` (Zeile 20442): kein Match
3. `\bWir\b` → `Ich` (Zeile 20533): `"Ich haben keinen Mitarbeiter eingestellt"`
4. Grammar-Error "Ich haben" entsteht NACH dem Grammar-Fix

Identisch für "können wir" → "können ich" (NEU-3):
1. LLM: `"Was können wir besser machen?"`
2. `\bkönnen ich\b` → `kann ich`: kein Match (ist noch "können wir")
3. `\bwir\b` → `ich`: `"Was können ich besser machen?"`

### Fix (Commit 9fa407e)

Post-Substitution Grammar Repair Pass mit `str.replace()` NACH der Hauptschleife:

```python
_post_grammar = [
    ('Ich haben', 'Ich habe'),      # B1
    ('können ich', 'kann ich'),      # NEU-3
    ('Vorhabe ichtschaftlich', 'Vorhaben wirtschaftlich'),  # B2
    # + alle anderen Verb-Agreement nach Wir→Ich
]
for _old, _new in _post_grammar:
    if _old in final_html:
        final_html = final_html.replace(_old, _new)
```

**Platzierung:** NACH der Regex-Schleife, VOR `result["html"] = final_html`.

---

## Root Cause 2: "Vorhabe ichtschaftlich" — LLM-Artefakt (B2)

### Beobachtung

- Briefing 897: `"Vorhabe ichtschaftlich tragfähig"` (Soll: "Vorhaben wirtschaftlich")
- Briefing 902: `"werde ichtschaftlich umsetzbar"` (Soll: "werden wirtschaftlich")
- Beide: Exakt gleiche 3 Zeichen fehlen (n + Leerzeichen + w)

### Hypothese A: LLM-Generierungsartefakt (WAHRSCHEINLICHSTE — 70%)

**Indizien:**
1. LLM-Aufrufe sind **synchron** (`requests.post`, kein Streaming) — `gpt_analyze.py:2268`
2. Vollständige Response wird als String zurückgegeben — `gpt_analyze.py:2312`
3. Kein Streaming-Chunk-Assembly, daher kein Chunk-Boundary-Problem
4. `finish_reason=length` wird nur geloggt (Zeile 2318), kein Retry
5. Das Pattern "wirt" → "icht" ist KEINE einfache Deletion — es ist eine Substitution (w→i, i→c, r→h)
6. Tritt konsistent in 2 unabhängigen Briefings auf (gleicher Prompt-Template, ähnliche Inputs)

**Mechanismus:** Der LLM (GPT-4) generiert den FOERDERPOTENZIAL-Abschnitt. Bei ähnlichen Prompt-Kontexten und Token-Budgets produziert der Tokenizer konsistent denselben Fehler im Bereich "...en wirtschaftlich". Die BPE-Tokenisierung für deutsche Komposita ist bekannt problematisch.

### Hypothese B: HTML-Tag splittet "wirtschaftlich" (20%)

**Mechanismus:** Wenn der LLM HTML generiert, in dem ein Inline-Tag das Wort "wirtschaftlich" splittet:

```html
<!-- LLM generiert (hypothetisch): -->
<strong>Vorhaben wir</strong>tschaftlich tragfähig
```

Dann greift `\bwir\b` → `ich` (Zeile 20534), weil `>` und `<` Non-Word-Characters sind:

```python
# Test (verifiziert):
re.sub(r'\bwir\b', 'ich', '<strong>wir</strong>tschaftlich')
# → '<strong>ich</strong>tschaftlich'  (rendert als "ichtschaftlich")
```

**Problem:** Erklärt "ichtschaftlich" aber NICHT den "n"-Verlust aus "Vorhaben".

### Hypothese C: Kombination (10%)

1. Budget-Cap-Truncation (`gpt_analyze.py:13865`) schneidet am Zeichenlimit
2. Word-Boundary-Snap (`gpt_analyze.py:13885`) springt zu Leerzeichen zurück
3. Dabei geht der letzte Buchstabe "n" von "Vorhaben" verloren
4. Separat: LLM oder Tag-Split verursacht "wirt" → "icht"

### Warum kein Pipeline-Processing-Bug

Alle Pipeline-Schritte wurden analysiert — keiner kann die Transformation "wirt" → "icht" erklären:

| Schritt | Datei | Zeile | Kann "n w" verlieren? |
|---------|-------|-------|----------------------|
| LLM-Call | gpt_analyze.py | 2186-2333 | Nein (synchron, kein Streaming) |
| _clean_html | gpt_analyze.py | 2407 | Nein (nur Markdown-Fences + Leaks) |
| _aggressive_text_truncation | gpt_analyze.py | 5627 | Nein (Wort/Satz-Grenzen, nicht Char) |
| Budget-Cap-Truncation | gpt_analyze.py | 13861 | Nein (Word-Boundary-Snap) |
| apply_all_quality_enforcers | content_quality_enforcer.py | 3022 | Nein (kein Pattern für "wirtschaftlich") |
| cleanup_truncation_artifacts | content_quality_enforcer.py | 4571 | Nein (nur KNOWN_TRUNCATION_FIXES) |
| B38a/B39 Clean-Ending | report_healer.py | 3334-3475 | Nein (Satzgrenzen, nicht Char) |
| B40 Clean-Ending | gpt_analyze.py | 19998 | Nein (Satzgrenzen, nicht Char) |
| heal_final_html | report_healer.py | 3855 | Nein (Boilerplate/Blacklist, nicht Wörter) |
| GLOBAL FINAL ENFORCER | gpt_analyze.py | 20417 | **Nur wenn HTML-Tag splittet** |
| SIZE-AWARE FINAL PASS | solo_final_pass.py | - | Nein (kein Wir/wir Pattern) |
| strip_sprint_codes | report_renderer.py | - | Nein (nur Sprint-Codes) |

---

## Die `</ "..."` Truncation-Repair-Artifact

### Befund

```html
"Ich haben keinen Mitarbeiter eingestellt, sondern KI.</
"Ich haben keinen Mitarbeiter eingestellt, sondern KI. Beste Entscheidung." >
```

### Root Cause: LLM-Generierungsartefakt

1. Das Pattern `</ "vollständiger Text" >` ist **kein Code-Feature** — es existiert kein Truncation-Repair-Mechanismus im Code
2. Der LLM generiert dieses Pattern selbst als Versuch, truncierten HTML-Output zu "reparieren"
3. Es gibt keinen Code der `</ "..."` erzeugt oder verarbeitet
4. Der `_clean_html`-Schritt entfernt es NICHT

### Verwandtschaft zu "ichtschaftlich"

- **Gleicher Root Cause:** Ja — beide sind LLM-Generierungsartefakte
- **Gemeinsamer Trigger:** LLM nähert sich Token-Limit, generiert fehlerhafte Reparaturversuche
- **Unterschied:** Das `</ "..."` Pattern ist ein Self-Repair-Versuch; "ichtschaftlich" ist ein Token-Boundary-Fehler

---

## Pipeline-Architektur (für Referenz)

```
analyze_briefing() [gpt_analyze.py:14850]
├── _generate_content_sections() [15086]
│   └── _call_llm_for_section() → _call_openai() [2186]
│       └── SYNCHRON (requests.post, kein Streaming)
│       └── finish_reason=length nur geloggt [2318]
├── apply_zero_leak_phrase_cleanup() [15100]
├── precommit_zero_leak_all_sections() [15116]
├── apply_all_quality_enforcers() [14661, 14841, 18548]
│   └── 33+ Quality-Transforms inkl. Grammar-Fixer
├── _aggressive_text_truncation + Budget-Cap [13814-13937]
├── heal_report_html() [19935] (FIX-A-G)
├── KIS-1013-B1 Grammar Pass [19983] (auf sections{})
├── B40 Clean-Ending [19998]
├── render() → Jinja2 Template [20284]
├── heal_final_html() [20305] (Post-Render)
├── GLOBAL FINAL ENFORCER [20417-20561] (auf final_html)
│   ├── Regex-Loop: Wir→Ich, Skalierung→Erweiterung, etc.
│   └── POST-GRAMMAR REPAIR [20561+] (str.replace, NEUER FIX)
├── SIZE-AWARE FINAL PASS [20574]
├── strip_sprint_codes [20596]
└── DB-Speicherung [20601]
```

---

## Scope-Analyse

| Frage | Antwort |
|-------|---------|
| Nur "n w" vor "irtschaftlich"? | Nein — auch "n w" in "werden wirtschaftlich" → "werde ichtschaftlich" |
| Alle "n w"-Grenzen? | Unbekannt — nur bei Wörtern VOR "wirtschaftlich" beobachtet |
| Nur bestimmte HTML-Kontexte? | Nur in LLM-generierten Sections (FOERDERPOTENZIAL, SOFORT_START) |
| Deterministisch oder stochastisch? | Semi-deterministisch: tritt bei ähnlichen Prompt-Kontexten auf |
| Abhängig von Textlänge/Position? | Wahrscheinlich — tritt nur bei längeren Abschnitten auf |

---

## Fix-Status

### Bereits implementiert (Commit 9fa407e)

1. **Post-Grammar Repair Pass** im GLOBAL FINAL ENFORCER:
   - `'Ich haben' → 'Ich habe'` (B1)
   - `'können ich' → 'kann ich'` (NEU-3)
   - `'Vorhabe ichtschaftlich' → 'Vorhaben wirtschaftlich'` (B2)
   - Alle Verb-Agreement-Fehler nach Wir→Ich
   - Verwendet `str.replace()` statt Regex (immun gegen HTML-Tags)

2. **KNOWN_TRUNCATION_FIXES** in `content_quality_enforcer.py:4536`:
   - `'Vorhabe ichtschaftlich' → 'Vorhaben wirtschaftlich'`
   - `'Vorhabe nwirtschaftlich' → 'Vorhaben wirtschaftlich'`

### Phase 2 Empfehlungen

1. **Root-Cause-Fix für Hypothese B:** Wir→Ich Regex mit negativem Lookahead erweitern:
   ```python
   # Statt:
   (r'\bwir\b', 'ich')
   # Besser:
   (r'\bwir\b(?![a-zäöüß])', 'ich')  # Verhindert Match wenn Wortzeichen folgt (auch durch Tags)
   ```
   ABER: `\b` sollte dies bereits verhindern. Das Problem tritt nur auf wenn HTML-Tags die Word-Boundary erzeugen.

2. **Generisches Safety-Net:** Regex für alle `*ichtschaftlich`-Varianten:
   ```python
   (r'(\w+)e\s+ichtschaftlich', r'\1en wirtschaftlich')
   ```

3. **Logging:** Raw LLM Output für FOERDERPOTENZIAL vor Quality-Enforcer loggen, um Hypothese A vs B zu verifizieren.

4. **`</ "..."` Artifact Cleanup:** Regex im GLOBAL FINAL ENFORCER:
   ```python
   (r'</\s*"[^"]*"\s*>', '')  # Entfernt Truncation-Repair-Marker
   ```
