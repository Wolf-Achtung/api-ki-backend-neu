# STATE-AUDIT-517A: Prompt Section Propagation Forensik

## Datum: 2026-01-23
## Status: IST-ZUSTAND Dokumentation (kein Behavior-Change)

---

## Call-Graph

```
gpt_analyze._generate_content_section(section_name, briefing, scores)
  │
  ├─ prompt_key = prompt_map.get(section_name)         # z.B. "tools_empfehlungen"
  │
  ├─ enhanced_prompt = _prompt_enhancer.enhance_prompt(prompt_key, briefing)
  │     └─ Liefert interpolierten Prompt-String MIT Jinja-Tags
  │
  ├─ vars_dict = _build_prompt_vars(briefing, scores)
  │
  ├─ *** ROOT CAUSE ***
  │   prompt_text = _interpolate(enhanced_prompt, vars_dict)
  │     │
  │     │  PROBLEM: Kein section= oder lang= Parameter übergeben!
  │     │  _interpolate Signatur: _interpolate(obj, vars_dict, lang="de", section="unknown", ...)
  │     │
  │     └─ _interpolate_text(s, vars_dict, lang="de", section="unknown")
  │           │
  │           ├─ CHECK: section == "unknown" → True
  │           │   ├─ RELEASE_STRICT_MODE=1 → raises ValueError
  │           │   └─ RELEASE_STRICT_MODE=0 → log.warning, continues
  │           │
  │           └─ (bei STRICT): ValueError propagiert nach oben
  │
  └─ except Exception:  (gpt_analyze.py:11039)
        └─ Fällt zurück auf Legacy-Prompts (Zeile 11055+)
```

## Exakte Fehlerstelle

| Datei | Zeile | Code |
|-------|-------|------|
| `gpt_analyze.py` | **10752** | `prompt_text = _interpolate(enhanced_prompt, vars_dict)` |
| `services/prompt_loader.py` | **523** | `if not section or section == "unknown":` |
| `services/prompt_loader.py` | **529** | `raise ValueError(msg)` (nur bei STRICT) |

## Warum section "unknown" wird

Die `_interpolate` Funktion hat folgende Signatur:

```python
def _interpolate(
    obj: Any,
    vars_dict: Optional[Dict[str, Any]],
    lang: str = "de",          # <-- default
    section: str = "unknown",  # <-- default = "unknown"
    strict_mode: Optional[bool] = None,
) -> Any:
```

In `gpt_analyze.py:10752` wird `_interpolate` NUR mit 2 Argumenten aufgerufen:

```python
prompt_text = _interpolate(enhanced_prompt, vars_dict)
#                          ^^^^^^^^^^^^^^^^  ^^^^^^^^^
#                          obj               vars_dict
#                                            lang → "de" (default)
#                                            section → "unknown" (default) ← BUG
```

Die verfügbaren Variablen `prompt_key` und `prompt_lang` werden NICHT übergeben,
obwohl sie im selben Scope verfügbar sind (Zeile 10712 / 10724).

## Kaskaden-Effekt

```
section="unknown" in _interpolate_text
    │
    ├─ STRICT MODE ON (Railway):
    │   └─ ValueError → except Exception → Legacy-Fallback
    │       ├─ quick_wins: Legacy-Prompt vorhanden (lang) → OK
    │       ├─ tools_empfehlungen: NICHT im Legacy-Dict → "" → 27 Wörter
    │       └─ gamechanger: Mini-Legacy-Prompt (1 Zeile) → 84 Wörter
    │
    └─ STRICT MODE OFF:
        └─ log.warning → Interpolation läuft mit section="unknown"
           └─ Cycle-Detection + Usage-Tracking broken (but content generated)
```

## Minimaler Fix-Vorschlag für FIX-517B

```python
# gpt_analyze.py, Zeile 10752 (aktuell):
prompt_text = _interpolate(enhanced_prompt, vars_dict)

# FIX-517B (1 Zeile):
prompt_text = _interpolate(enhanced_prompt, vars_dict, lang=prompt_lang, section=prompt_key)
```

Dies stellt sicher, dass:
1. `section` korrekt an die Cycle-Detection und Usage-Tracking durchgereicht wird
2. `lang` korrekt an den Jinja2 FileSystemLoader durchgereicht wird
3. Kein ValueError mehr in STRICT mode
4. Kein Legacy-Fallback mehr für Enhanced-Path Sections

## Debug-Nachweis

Mit `DEBUG_PROMPT_TRACE=1` wird folgendes geloggt:

```
[PROMPT-TRACE] key=tools_empfehlungen section_arg=<MISSING> lang=de manifest=True template_engine=jinja enhanced_bytes=12345
[PROMPT-TRACE][ERROR] section=unknown caller=gpt_analyze.py:10752:_generate_content_section <- prompt_loader.py:655:_interpolate key_hint=<unknown>
```

## Betroffene Sections

Alle Sections die über den Enhanced-Path (`USE_PROMPT_SYSTEM=1 + _prompt_enhancer`) laufen:
- executive_summary, quick_wins, roadmap_90d, roadmap_12m
- gamechanger, tools_empfehlungen, foerderpotenzial
- strategie_governance, wettbewerb_benchmark, technologie_prozesse
- risks, recommendations, org_change, data_readiness
- monetarisierung, ki_skillplan, transparency_box
- (alle Einträge in prompt_map, Zeile 10676-10710)
