# STATE-AUDIT-517A: SECTION_TOO_SHORT Forensik

## Datum: 2026-01-23
## Betroffene Sections: tools_empfehlungen, gamechanger
## Company Size: solo

---

## Pipeline-Phasen Vergleich

### tools_empfehlungen (27 Wörter, Minimum solo: 80)

| Phase | Wörter | Erklärung |
|-------|--------|-----------|
| Prompt-Template (prompts/de/tools_empfehlungen.md) | ~2100 Wörter (inkl. HTML+Comments) | Vollständiges Template mit 316 Zeilen |
| Nach PromptEnhancer.enhance_prompt() | ~2100+ | Branche/Größe-Kontext hinzugefügt |
| _interpolate() Aufruf | **FAILS** (section=unknown) | ValueError in STRICT mode |
| Legacy-Fallback Prompt | **0 Wörter** | tools_empfehlungen NICHT im Legacy-Dict (Zeile 11253) |
| LLM-Generierung (leerer Prompt) | ~27 Wörter | LLM generiert minimalen Output |
| platin_min_words Check | **PASSIERT** | Default 10 Wörter (kein Eintrag für tools_empfehlungen) |
| Validator (_check_empty_or_short_sections) | **BLOCKED** | solo min=80, actual=27 → CRITICAL |

### gamechanger (84 Wörter, Minimum solo: 100)

| Phase | Wörter | Erklärung |
|-------|--------|-----------|
| Prompt-Template (prompts/de/gamechanger.md) | ~3500 Wörter (inkl. HTML+Comments) | Vollständiges v7.2 Template, 597 Zeilen |
| Nach PromptEnhancer.enhance_prompt() | ~3500+ | Branche/Größe-Kontext hinzugefügt |
| _interpolate() Aufruf | **FAILS** (section=unknown) | ValueError in STRICT mode |
| Legacy-Fallback Prompt | ~30 Wörter | 1-Zeiler: "Skizziere einen Gamechanger-Use Case..." |
| LLM-Generierung (Mini-Prompt) | ~84 Wörter | LLM generiert kurzen Output |
| platin_min_words Check | 700 Wörter min | **84 < 700** → versucht 2-pass expand |
| 2-Pass Expand (EXPAND_ELIGIBLE_SECTIONS) | ? | gamechanger ist eligible, aber Expand mit 84-Wort-Basis reicht nicht |
| PLATIN-Fallback (_get_fallback_content) | ~110 Wörter | Statischer Fallback-HTML (Zeile 10555) |
| Validator (_check_empty_or_short_sections) | solo min=100 | **Fallback ~110 > 100 → sollte passen** |

**ACHTUNG**: Die 84 Wörter im Error-Log deuten darauf hin, dass entweder:
1. Der 2-Pass-Expand ebenfalls fehlschlägt (bei leerem Basis-Text)
2. ODER der PLATIN-Fallback nicht greift (weil word_count=84 > platin_min_words default=10 für einen Bug-Path)

### Diagnose: Wo wird der Text "real" zu kurz?

**Primäre Ursache**: Der Text wird NICHT im Postprocessing/Strip zu kurz gemacht.
Der Text ist bereits bei der **Generierung zu kurz**, weil:

1. `section=unknown` ValueError → Enhanced-Path Exception
2. Legacy-Fallback hat keinen/minimalen Prompt für diese Sections
3. LLM generiert mit leerem/minimalem Prompt nur wenige Wörter
4. Generator-eigene Mindestlänge (`platin_min_words`) hat:
   - `tools_empfehlungen`: KEINEN Eintrag → Default 10 Wörter (27 > 10 → passiert!)
   - `gamechanger`: 700 Wörter → würde Expand/Fallback triggern

---

## Validator-Schwellen (report_validator.py)

### MIN_SECTION_LENGTH_WORDS (Basis):
- tools_empfehlungen: 120
- gamechanger: 750

### MIN_SECTION_LENGTH_BY_SIZE["solo"]:
- tools_empfehlungen: **80** (Zeile 648)
- gamechanger: **100** (Zeile 650)

### CRITICAL_LENGTH_SECTIONS:
- tools_empfehlungen: **JA** → CRITICAL severity
- gamechanger: **JA** → CRITICAL severity

### SECTION_KEY_MAP:
- tools_empfehlungen → "tools_empfehlungen" (direkt)
- gamechanger → "gamechanger" (direkt)

---

## Generator-eigene Checks (platin_min_words, gpt_analyze.py:10929)

```python
platin_min_words = {
    "roadmap": 100,
    "roadmap_90d": 100,
    "roadmap_12m": 800,
    "foerderpotenzial": 900,
    "org_change": 100,
    "strategie_governance": 120,
    "risks": 800,
    "recommendations": 800,
    "gamechanger": 700,           # ← vorhanden
    "unternehmensprofil_markt": 600,
}
# tools_empfehlungen: NICHT vorhanden → default 10!
```

**Lücke**: `tools_empfehlungen` fehlt in `platin_min_words`. Dadurch passiert
ein 27-Wörter-Output den Generator-Check, wird aber vom Validator geblockt.

---

## FIX-517B Vorschlag (minimaler Patch)

### Fix 1: Section-Propagation (behebt Root Cause)
```python
# gpt_analyze.py:10752
prompt_text = _interpolate(enhanced_prompt, vars_dict, lang=prompt_lang, section=prompt_key)
```

### Fix 2: platin_min_words ergänzen (Safety Net)
```python
# gpt_analyze.py:10929, im platin_min_words dict:
"tools_empfehlungen": 80,   # Mindestens solo-min
```

---

## Debug-Artefakte (bei DEBUG_RENDER=1 oder DEBUG_PROMPT_TRACE=1)

Werden VOR dem Quality-Gate-Raise erzeugt:
- `/tmp/debug_517_short_sections.json` — Pro Blocker: Wortzählungen je Phase
- `/tmp/debug_517_short_sections_excerpt.html` — Final HTML mit BEGIN/END anchors
