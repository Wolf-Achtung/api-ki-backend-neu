# Forensik: Teams → Kapazitäten Root Cause Analysis

**Version:** v14.35.19+
**Datum:** 2026-01-14
**Status:** ✅ FIXED (Protection implemented)

---

## Executive Summary

Die Transformation "Microsoft Teams" → "Microsoft Kapazitäten" wurde durch den **Solo-Persona-Filter** verursacht, der alle Vorkommen von "Teams" durch "Kapazitäten" ersetzt.

**Fix:** PROTECTED_PRODUCT_NAMES Liste schützt jetzt Produktnamen wie "Microsoft Teams".

---

## 1. Fundstelle

| Attribut | Wert |
|----------|------|
| **Datei** | `services/prompt_enhancer.py` |
| **Zeilen** | 810-811 (Replacement), 840-845 (Protection) |
| **Funktion** | `apply_solo_persona_filter()` |
| **Pipeline-Stufe** | Stage 1: Solo Persona Filter |

---

## 2. Codeblock der Regel (vor Fix)

```python
# services/prompt_enhancer.py, Zeile 810-811
SOLO_GOVERNANCE_REPLACEMENTS: Dict[str, str] = {
    # ...
    "teams": "Kapazitäten",   # ← DIESER EINTRAG
    "team": "Kapazität",      # ← DIESER EINTRAG
    # ...
}
```

**Problem:** Diese Regel ersetzt ALLE Vorkommen von "Teams"/"Team", unabhängig vom Kontext.

---

## 3. Fix Implementation (v14.35.19+)

```python
# services/prompt_enhancer.py, Zeile 840-845
PROTECTED_PRODUCT_NAMES: List[str] = [
    "Microsoft Teams",
    "Google Teams",
    "Teams Copilot",
    "MS Teams",
]
```

**Protection Logic (Zeile 905-918):**
```python
def apply_solo_persona_filter(text: str) -> str:
    # ...
    # v14.35.19+: Protect product names before replacement
    protected_map: Dict[str, str] = {}
    for i, product_name in enumerate(PROTECTED_PRODUCT_NAMES):
        placeholder = f"__PROTECTED_PRODUCT_{i}__"
        if product_name.lower() in result.lower():
            pattern = re.compile(re.escape(product_name), re.IGNORECASE)
            match = pattern.search(result)
            if match:
                original = match.group(0)
                protected_map[placeholder] = original
                result = pattern.sub(placeholder, result)

    # ... apply replacements ...

    # v14.35.19+: Restore protected product names
    for placeholder, original in protected_map.items():
        result = result.replace(placeholder, original)
```

---

## 4. Repro: Input → Output

### Test-Script

```bash
python scripts/debug_team_leak.py
```

### Ergebnisse

| Input | Output | Status |
|-------|--------|--------|
| `"Zoom / Microsoft Teams für Online-Meetings"` | `"Zoom / Microsoft Teams für Online-Meetings"` | ✅ PROTECTED |
| `"Microsoft Teams"` | `"Microsoft Teams"` | ✅ PROTECTED |
| `"MS Teams"` | `"MS Teams"` | ✅ PROTECTED |
| `"Nutzen Sie Teams für die Kommunikation."` | `"Nutzen Sie Kapazitäten für die Kommunikation."` | ✅ CORRECTLY REPLACED (standalone) |
| `"Das Team arbeitet zusammen."` | `"Ihre Kapazität arbeitet zusammen."` | ✅ CORRECTLY REPLACED (standalone) |

---

## 5. Pipeline-Reihenfolge

```
1. prompt_enhancer.apply_solo_persona_filter()  ← FIX HIER
   ├── Step 1: Protect product names (PROTECTED_PRODUCT_NAMES)
   ├── Step 2: Apply phrase replacements (SOLO_PHRASE_REPLACEMENTS)
   ├── Step 3: Apply word replacements (SOLO_GOVERNANCE_REPLACEMENTS)
   └── Step 4: Restore protected names

2. prompt_enhancer.simplify_solo_governance()
3. content_quality_enforcer.apply_grammar_fixes()
4. text_healing.heal_text_block()
```

---

## 6. Step-by-Step Trace

**Input:** `"Zoom / Microsoft Teams für Online-Meetings"`

```
--- Step 1: Protect product names ---
  ✓ Protected: 'Microsoft Teams' → __PROTECTED_PRODUCT_0__
  After: 'Zoom / __PROTECTED_PRODUCT_0__ für Online-Meetings'

--- Step 2: Apply phrase replacements ---
  (no matches)
  After: 'Zoom / __PROTECTED_PRODUCT_0__ für Online-Meetings'

--- Step 3: Apply word-based replacements ---
  (no matches - "Teams" is protected as placeholder)
  After: 'Zoom / __PROTECTED_PRODUCT_0__ für Online-Meetings'

--- Step 4: Restore protected names ---
  ✓ Restored: __PROTECTED_PRODUCT_0__ → 'Microsoft Teams'

  FINAL: 'Zoom / Microsoft Teams für Online-Meetings'
```

---

## 7. Relevante Dateien

| Datei | Beschreibung |
|-------|--------------|
| `services/prompt_enhancer.py` | Solo Persona Filter (Fix implementiert) |
| `scripts/debug_team_leak.py` | Forensik Debug Script |
| `tests/test_report_467_fixes.py` | Unit Tests für Protection |

---

## 8. Acceptance Criteria

| Kriterium | Status |
|-----------|--------|
| Datei/Zeile/Regex bekannt | ✅ `prompt_enhancer.py:810-811` |
| Pipeline-Stufe bekannt | ✅ Stage 1: `apply_solo_persona_filter()` |
| Reproduzierbarer Minicase | ✅ `scripts/debug_team_leak.py` |
| Fix implementiert | ✅ v14.35.19+ (PROTECTED_PRODUCT_NAMES) |
| Tests vorhanden | ✅ `test_report_467_fixes.py` |

---

## 9. Empfehlung für zukünftige Erweiterungen

Falls weitere Produktnamen geschützt werden müssen:

```python
# services/prompt_enhancer.py
PROTECTED_PRODUCT_NAMES: List[str] = [
    "Microsoft Teams",
    "Google Teams",
    "Teams Copilot",
    "MS Teams",
    # Neue Einträge hier hinzufügen:
    # "Slack Teams",
    # "Zoom Team Chat",
]
```

---

## Appendix: Vollständige Replacement-Tabellen

### SOLO_GOVERNANCE_REPLACEMENTS (Teams-related)

| Key | Replacement |
|-----|-------------|
| `"team aufbauen"` | `"Arbeitsweise strukturieren"` |
| `"teams"` | `"Kapazitäten"` |
| `"team"` | `"Kapazität"` |
| `"projektteam"` | `"Projektstruktur"` |
| `"belegschaft"` | `"Kapazität"` |

### SOLO_PHRASE_REPLACEMENTS (Teams-related)

| Key | Replacement |
|-----|-------------|
| `"team aufbauen"` | `"Kapazität aufbauen"` |
| `"teams aufbauen"` | `"Kapazitäten erweitern"` |
| `"team einbinden"` | `"externe Expertise einbinden"` |
| `"teams einbinden"` | `"Kooperationspartner einbinden"` |
| `"im team"` | `"gemeinsam mit Partnern"` |
| `"das team"` | `"Ihre Kapazität"` |
| `"ihr team"` | `"Ihre Kapazität"` |
| `"unser team"` | `"unsere Kapazität"` |
| `"führungsteam"` | `"Ihre Entscheidungsfindung"` |
| `"management-team"` | `"Ihre strategische Planung"` |
