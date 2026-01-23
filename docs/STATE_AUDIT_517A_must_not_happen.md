# STATE-AUDIT-517A: Must-Not-Happen Liste (FIX-517B Ziel)

## Datum: 2026-01-23
## Zweck: Konkrete Logzeilen die nach FIX-517B verschwinden MÜSSEN

---

## MUST NOT HAPPEN (nach FIX-517B)

### 1. Section=unknown ValueError
```
ValueError: [FIX-517][PROMPT][SECTION] section=unknown — Pass section=<prompt_key> to render_prompt for usage+cycle tracking
```
**Root Cause**: `_interpolate(enhanced_prompt, vars_dict)` ohne `section=` Parameter
**Exakte Stelle**: `gpt_analyze.py:10752`
**Fix**: `section=prompt_key, lang=prompt_lang` Parameter ergänzen

---

### 2. QUICK_WINS Legacy Fallback
```
[PROMPT][LEGACY] QUICK_WINS using legacy fallback prompts due to exception
```
**Root Cause**: ValueError aus #1 wird von `except Exception` gefangen → Legacy-Path
**Exakte Stelle**: `gpt_analyze.py:11058` (Log-Zeile)
**Fix**: Mit Fix #1 entfällt der Exception-Path → Legacy wird nicht mehr erreicht

---

### 3. SECTION_TOO_SHORT: tools_empfehlungen
```
[SECTION_TOO_SHORT] tools_empfehlungen: 27 Wörter (Minimum für solo: 80 Wörter)
```
**Root Cause**: Legacy-Dict hat keinen Eintrag für tools_empfehlungen → leerer Prompt → ~27 Wörter
**Exakte Stelle**: `services/report_validator.py:1119-1130` (Validator); Generator-Lücke: `platin_min_words` hat keinen Eintrag für tools_empfehlungen
**Fix**: Root Cause #1 fixen + platin_min_words ergänzen als Safety Net

---

### 4. SECTION_TOO_SHORT: gamechanger
```
[SECTION_TOO_SHORT] gamechanger: 84 Wörter (Minimum für solo: 100 Wörter)
```
**Root Cause**: Legacy-Prompt ist 1-Zeiler (~30 Wörter Instruktion) → LLM generiert ~84 Wörter
**Exakte Stelle**: `services/report_validator.py:1119-1130` (Validator); Legacy-Prompt: `gpt_analyze.py:11270`
**Fix**: Root Cause #1 fixen → Enhanced-Prompt (597 Zeilen, v7.2) wird korrekt genutzt

---

### 5. QUALITY GATE BLOCKED
```
🚫 QUALITY GATE BLOCKED: 2 critical errors
```
**Root Cause**: Konsequenz aus #3 + #4 (beide sind CRITICAL_LENGTH_SECTIONS)
**Exakte Stelle**: `gpt_analyze.py:14034` (raise ValueError)
**Fix**: Wenn #3 und #4 nicht mehr auftreten, entfällt auch der Block

---

## Zusammenfassung: Kausalitätskette

```
_interpolate(...) ohne section=prompt_key     [ROOT CAUSE]
    ↓
ValueError: section=unknown (STRICT mode)
    ↓
except Exception → Legacy-Fallback
    ↓
tools_empfehlungen: kein Legacy-Prompt → 27 Wörter
gamechanger: Mini-Legacy-Prompt → 84 Wörter
    ↓
Validator: SECTION_TOO_SHORT × 2 (CRITICAL)
    ↓
QUALITY GATE BLOCKED: 2 critical errors
```

## FIX-517B: Minimaler Patch (1 Zeile + 1 Safety-Net Zeile)

```python
# Zeile 10752 in gpt_analyze.py (Section-Propagation Fix):
prompt_text = _interpolate(enhanced_prompt, vars_dict, lang=prompt_lang, section=prompt_key)

# Zeile 10929 in gpt_analyze.py (Safety Net für platin_min_words):
"tools_empfehlungen": 80,  # Solo-Minimum als Auffangnetz
```

## Verifizierung nach FIX-517B

1. `grep -c "section=unknown" logs` → **0**
2. `grep -c "LEGACY.*QUICK_WINS" logs` → **0** (für Enhanced-Path Sections)
3. `grep -c "SECTION_TOO_SHORT.*tools_empfehlungen" logs` → **0**
4. `grep -c "SECTION_TOO_SHORT.*gamechanger" logs` → **0**
5. `grep -c "QUALITY GATE BLOCKED" logs` → **0** (für diesen Fehlertyp)
