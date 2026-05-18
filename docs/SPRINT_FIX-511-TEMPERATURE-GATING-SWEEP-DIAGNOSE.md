# Sprint Diagnose: FIX-511 Temperature-Gating Sweep
**Status:** No-op (Pre-#1020-Artefakt verifiziert)
**Datum:** 2026-05-18
**Trigger:** Briefing 1067 Crash 2026-05-16 13:53:47 UTC

## Frage
Existiert in gpt_analyze.py ein OpenAI-Direkt-Call, der das Temperature-Gating
aus PR #1020 umgeht?

## Antwort
Nein. Alle 5 OpenAI-Pfade sind gegated. Crash 1067 ist Pre-#1020 (26min vor Merge).

## Sweep-Tabelle

### `gpt_analyze.py`

| # | Datei:Line | Codepfad | OpenAI-Aufruf | Hardcoded Temp | Gating aktiv? |
|---|---|---|---|---|---|
| 1 | `gpt_analyze.py:2360` | `_call_openai` (zentral) | `requests.post /v1/chat/completions` | nein (Parameter) | **JA** — Zeile 2307–2314 via `maybe_openai_temperature` (PR #1020) |
| 2 | `gpt_analyze.py:2488` | `_call_llm_for_section` → `_call_openai` | indirekt | nein | JA (via #1) |
| 3 | `gpt_analyze.py:12832` | C1-REGEN | `_call_openai`, `temperature=0.7` default | nein (params) | JA (via #1) |
| 4 | `gpt_analyze.py:19382` | ROADMAP_90D SG-REGEN | `_call_openai`, `temperature=0.5` | **ja, 0.5** | JA (via #1) |
| 5 | `gpt_analyze.py:19630` | **KI_STACK_SUMMARY SG-REGEN** | `_call_openai`, `temperature=0.5` | **ja, 0.5** | JA (via #1) |
| 6 | `gpt_analyze.py:19900` | GAMECHANGER SG-REGEN | `_call_openai`, `temperature=0.5` | **ja, 0.5** | JA (via #1) |

Vollständigkeit verifiziert via
`grep -n "requests\.post\|httpx\|openai\.OpenAI\|client\.chat\|from openai\|import openai" gpt_analyze.py`
→ genau ein Treffer (Zeile 2360, im gegateten `_call_openai`).

### Weitere OpenAI-Pfade im Repo (außerhalb Sprint-Scope, zur Vollständigkeit)

| Pfad | Datei | Gating-Quelle |
|---|---|---|
| `openai_request_simple` | `services/openai_retry.py:523–530` | PR #1020 — `maybe_openai_temperature` |
| `strategy_pipeline._call_openai` | `services/strategy_pipeline.py:762–770` | PR #1020 — `maybe_openai_temperature` |
| `gamechanger_deep_dive` | `services/gamechanger_deep_dive.py:619–645` | inline `_is_new_model` (älter als PR #1020) |
| Anthropic-Pfad | `services/anthropic_client.py:53` | PR #1018/#1020 — `build_anthropic_create_kwargs` |

## Zeitachsen-Evidenz
- Crash: 2026-05-16 13:53:47 UTC (Briefing 1067)
- PR #1020 Merge: 2026-05-16 14:19:52 UTC (commit 2cb9715)
- Differenz: 26min — Crash zwingend in Pre-Patch-Zustand

## Bewusst akzeptierter Audit-Punkt
services/gamechanger_deep_dive.py:619–645 nutzt inline `_is_new_model` statt
des llm_client-Helpers. Semantisch identisch (gleiche 4 Präfixe).
Kein Bug, kein Refactor-Bedarf — markiert für zukünftige Reviewer.

## Folge-Themen (eigene Sprints)
- KI_STACK_SUMMARY-Nullung zwischen 13:53:05 (B25-CANONICAL ok) und 13:53:47
  (len=0). Hypothese: QUALITY-ENFORCER-Stakeholder-Solo-Leak. Nicht in diesem
  Sprint diagnostiziert.
- Falls je wieder Crash mit dieser Signatur: erste Frage ist Railway-Deploy-Hash
  gegen 2cb9715, nicht Code-Bypass-Suche.
