# DEAD CODE CANDIDATES

**Datum:** 2026-01-18
**Analyse-Methode:** Static analysis (ripgrep), Import graph, Runtime indicators

---

## Summary

| Kategorie | Zeilen | Prozent |
|-----------|--------|---------|
| **Dead Code (0 Imports)** | 4,923 | 3.5% |
| **Cold Code (1-3 Imports)** | 25,945 | 18% |
| **Gesamt** | 30,868 | **21.6%** |

---

## 1. Vollständig Unbenutzte Module (0 Imports)

### HIGH-RISK (600+ Zeilen)

| Datei | Zeilen | Indikator | Risiko | Empfehlung |
|-------|--------|-----------|--------|------------|
| `services/slim_mode_engine.py` | 676 | 0 Imports gefunden | LOW | DELETE nach Review |
| `services/n42_integration.py` | 642 | 0 Imports gefunden | MEDIUM | QUARANTINE |
| `services/validators.py` | 622 | 0 Imports gefunden | LOW | DELETE nach Review |

### MEDIUM-RISK (200-600 Zeilen)

| Datei | Zeilen | Indikator | Risiko | Empfehlung |
|-------|--------|-----------|--------|------------|
| `services/business_case_visuals.py` | ~450 | 0 Imports | LOW | DELETE |
| `services/pdf_guard.py` | ~350 | Nur in Tests | MEDIUM | KEEP (Test Utils) |
| `services/research.py` | ~320 | 0 Imports | LOW | DELETE |
| `services/test_research_system.py` | ~280 | Test-only | LOW | KEEP (Tests) |
| `services/kb_loader.py` | ~250 | 0 Imports | LOW | DELETE |
| `services/email_sender.py` | ~240 | Superseded by gpt_analyze | LOW | DELETE |

### LOW-RISK (<200 Zeilen)

| Datei | Zeilen | Indikator | Empfehlung |
|-------|--------|-----------|------------|
| `utils/cache_utils.py` | ~120 | 0 Imports | DELETE |
| `utils/date_utils.py` | ~80 | 0 Imports | DELETE |
| `services/prompt_cache.py` | ~100 | 0 Imports | DELETE |
| `services/llm_cache.py` | ~90 | Superseded | DELETE |

---

## 2. Deaktivierte/Deprecated Routen

| Datei | Zeilen | Indikator | Risiko | Empfehlung |
|-------|--------|-----------|--------|------------|
| `routes/####auth.py` | 288 | #### Prefix = deaktiviert | NONE | DELETE |
| `routes/####legacy_submit.py` | ~150 | #### Prefix | NONE | DELETE |
| `routes/####old_analyze.py` | ~200 | #### Prefix | NONE | DELETE |

---

## 3. Experimental/Agent Directories (nicht in Production)

| Directory | Zeilen | Indikator | Risiko | Empfehlung |
|-----------|--------|-----------|--------|------------|
| `expert_agents/` | 5,049 | Nur in Tests importiert | MEDIUM | QUARANTINE (nicht löschen) |
| `research_agents/` | 4,896 | Nur in Tests importiert | MEDIUM | QUARANTINE (nicht löschen) |

**Wichtig:** Diese Directories enthalten möglicherweise Prototypen für zukünftige Features. Nicht löschen, aber aus dem Deployment excluden.

---

## 4. Cold Code (1-3 Imports, rarely used)

### Potentiell Unused Services

| Datei | Zeilen | Imports | Letzter Aufruf | Empfehlung |
|-------|--------|---------|----------------|------------|
| `services/sofort_start_generator.py` | 2,016 | 1 | Unklar | INVESTIGATE |
| `services/governance_policy_engine_v2.py` | 1,726 | 2 | Selten | INVESTIGATE |
| `services/funding_engine_v2.py` | 1,143 | 1 | Active | KEEP |
| `services/monetarisierung_engine.py` | ~800 | 2 | Selten | INVESTIGATE |

---

## 5. Duplicated/Superseded Logic

| Alt | Neu | Problem | Empfehlung |
|----|-----|---------|------------|
| `services/risk_engine_v2.py` | `services/risk_engine_v3.py` | v2 noch importiert | Migrate zu v3, DELETE v2 |
| `services/business_case_engine.py` | `services/business_case_engine_v2.py` | v1 noch referenziert | Migrate zu v2, DELETE v1 |
| `services/ai_act_validator.py` | `services/ai_act_validator_v2.py` | v1 noch importiert | Migrate zu v2, DELETE v1 |

---

## 6. Cleanup-Aktionsplan

### Phase 1: Sofort (Low Risk)
```bash
# Deaktivierte Routen löschen
rm routes/####auth.py
rm routes/####legacy_submit.py
rm routes/####old_analyze.py

# Unbenutzte Utils löschen
rm utils/cache_utils.py
rm utils/date_utils.py
```

### Phase 2: Nach Verifikation (Medium Risk)
```bash
# Services ohne Imports
rm services/slim_mode_engine.py
rm services/validators.py
rm services/research.py
rm services/kb_loader.py
rm services/email_sender.py
rm services/prompt_cache.py
rm services/llm_cache.py
```

### Phase 3: Migration (Requires Code Changes)
```bash
# Nach Migration zu v2/v3:
rm services/risk_engine_v2.py  # Keep v3
rm services/business_case_engine.py  # Keep v2
rm services/ai_act_validator.py  # Keep v2
```

### Phase 4: Quarantine (Don't Delete Yet)
```bash
# Move to _quarantine/ folder
mv expert_agents/ _quarantine/expert_agents/
mv research_agents/ _quarantine/research_agents/
mv services/n42_integration.py _quarantine/
```

---

## 7. Verifikations-Commands

```bash
# Prüfe ob Modul importiert wird
rg "from services\.slim_mode_engine import" --type py
rg "import services\.slim_mode_engine" --type py

# Prüfe ob Funktion aufgerufen wird
rg "slim_mode_engine\." --type py

# Prüfe Referenzen in Tests
rg "slim_mode_engine" tests/ --type py
```

---

## 8. WICHTIG: Nichts wurde gelöscht!

Diese Liste ist ein **Inventar zur Überprüfung**. Vor dem Löschen:

1. ✅ Verifikation mit `rg` (ripgrep)
2. ✅ Check ob in Tests verwendet
3. ✅ Check ob in Configs referenziert
4. ✅ Backup erstellen
5. ✅ Nach Löschen: Full Test Suite laufen lassen
