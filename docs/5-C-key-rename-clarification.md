# 5-C — Spec-Drift Schlüsselname (KIS-1200 NO-GO)

**Status (1027.5.1):** Wolf-Entscheid α bestätigt — finaler Name bleibt
`_chat_blocks_skipped`. **Kein Code-Patch in 1027.5.1.**

## Anlass

Handover-Spec für 5-C nannte den Ziel-Schlüsselnamen
`_chat_blocks_without_freetext`. Das Production-DB-Audit am 30.05.2026
zeigte:

| Schlüsselname | Briefings (Anzahl) | Status |
|---|---|---|
| `_chat_unsurveyed_blocks` | 23 | alter Name, pre-1027.5 |
| `_chat_blocks_without_freetext` | 0 | **Handover-Spec-Name, nirgends** |
| `_chat_blocks_skipped` | 1 (KIS-1200) | **post-1027.5-Patch** |
| `_chat_surveyed_blocks` | 24 | paralleler, nicht betroffener Schlüssel |

Timeline:
- briefing 1082 (30.05. 11:37, pre-Deploy): `_chat_unsurveyed_blocks`
- briefing 1083 (30.05. 13:01, post-Deploy): `_chat_blocks_skipped`

→ Der 1027.5-Patch hat den Rename durchgeführt, aber unter Name
`_chat_blocks_skipped` statt `_chat_blocks_without_freetext`.

**Wolf-Entscheid:** `_chat_blocks_skipped` bleibt der finale Name
(kürzer, semantisch klarer als `_chat_blocks_without_freetext`).

## Code-Bestätigung

### 1. Finaler Schlüssel im Code

**Schreibseite (routes/chat.py):**

```python
# routes/chat.py:3096 (in _complete_r1)
if unsurveyed:
    answers["_chat_blocks_skipped"] = unsurveyed
    answers["_chat_surveyed_blocks"] = surveyed_blocks
    log.info("[CHAT] Complete R1: skipped blocks %s → defaults applied", unsurveyed)
```

```python
# routes/chat.py:3112 (in _complete_r1, KIS-1136 Fix 3-Pfad)
answers["_chat_blocks_skipped"] = unsurveyed
answers["_chat_surveyed_blocks"] = surveyed_blocks
```

**Leseseite (gpt_analyze.py):**

```python
# gpt_analyze.py:1283-1289
# KIS-1124 Sprint 4 S4-BE-2: Signal unsurveyed areas to LLM.
# FIX-KIS-1027.5-C: Field renamed from _chat_unsurveyed_blocks to
# _chat_blocks_skipped (clearer semantics: "user opted out / never entered").
# Backward-compat read covers existing DB rows with the old key.
unsurveyed = (
    answers.get("_chat_blocks_skipped")
    or answers.get("_chat_unsurveyed_blocks")
    or []
)
```

### 2. `_chat_blocks_without_freetext` nirgends im Code

```bash
$ grep -rn "_chat_blocks_without_freetext" .
# (kein Treffer)
```

Bestätigt: der Handover-Spec-Name wird nirgendwo im Code geschrieben
ODER gelesen. Keine Spec-Konformitäts-Korrektur nötig — der Code ist
in sich konsistent.

### 3. Backward-Compat-Read

`gpt_analyze.py:1287-1289` liest **beide** Namen via `or`-Verkettung:

- `_chat_blocks_skipped` (neuer Name, 1 Briefing seit Deploy)
- `_chat_unsurveyed_blocks` (alter Name, 23 Briefings vor Deploy)

→ Alte und neue DB-Rows sind beide funktional. Alte Rows werden über
die Zeit organisch durch neue Briefings ersetzt; keine DB-Migration
nötig.

## Begründung Spec-Drift

Bei Sprint 1027.5-Item-C wurde `_chat_blocks_skipped` als Rename-Ziel
gewählt:
- Kürzer (2 statt 3 Wörter)
- Semantisch identisch ("user hat Block übersprungen" ≡ "Block ohne
  Freetext-Antwort"), aber prägnanter
- Konsistent mit dem komplementären `_chat_surveyed_blocks` (gleiche
  Wortform "blocks_X" statt "blocks_X_Y")

Handover-Spec wurde nachträglich von Wolf bestätigt; der gewählte
Name bleibt.

## Empfehlung für künftige Sprints

Bei Schlüsselnamen-Änderungen, die DB-State betreffen:

1. **Doku-Sync vor Merge:** Final-Name in Sprint-Briefing AKTIV
   einfrieren, nicht aus der Beschreibung "rückwärts" ableiten.
2. **DB-Audit-Tabelle im Sprint-Daily-Report:** Anzahl Rows je
   Schlüsselname vor + nach Deploy.
3. **Sprint-Pre-Commitment-Check:** "Heißt der finale Schlüsselname
   X oder Y? Wenn unklar, Wolf-Ping vor Patch."

Diese drei Punkte würden den drift von `_chat_blocks_without_freetext`
↔ `_chat_blocks_skipped` schon im 1027.5-Sprint sichtbar gemacht haben.

## Wolf-Ping — Befund

- **Code-Konsistenz:** ✓ Final-Name `_chat_blocks_skipped` wird sauber
  geschrieben und gelesen.
- **Backward-Compat:** ✓ Alte Rows mit `_chat_unsurveyed_blocks` bleiben
  funktional via `or`-Verkettung in `gpt_analyze.py:1287-1289`.
- **Handover-Spec-Konformität:** **abgelehnt** — Spec-Name
  `_chat_blocks_without_freetext` wird nicht eingeführt (Wolf-Entscheid α).
- **Aktion:** Doku abgeschlossen, kein Code-Patch.
