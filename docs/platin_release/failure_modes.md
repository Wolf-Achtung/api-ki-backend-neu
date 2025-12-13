# PLATIN+++ Failure-Modes & Auto-Healing-Grenzen

**Version:** 1.0.0
**Datum:** 2025-12-13
**Status:** Verbindlich

---

## 1. Zweck dieses Dokuments

Dieses Dokument definiert die verbindlichen Grenzen für automatische Korrekturen (Auto-Healing) im PLATIN+++ System. Es dient als:

- **Audit-Referenz** für Compliance-Prüfungen
- **Entwickler-Leitfaden** für Erweiterungen des Auto-Healing-Systems
- **Governance-Dokument** für Release-Validierung

---

## 2. Erlaubte Auto-Heals

Die folgenden automatischen Korrekturen sind **ERLAUBT** und dürfen ohne manuelle Prüfung durchgeführt werden:

### 2.1 Wortbasierte Inkonsistenzen

| Mechanismus | Beschreibung | Implementierung |
|-------------|--------------|-----------------|
| **MIN_WORDS_CHECK** | Sections mit < 50 Wörtern werden durch Fallback-Content ergänzt | `services/auto_healing.py:auto_recover_section()` |
| **Content Enhancement** | Kurze Inhalte werden mit kontextuell passenden Ergänzungen erweitert | `services/auto_healing.py:_enhance_short_content()` |
| **Section Fallback** | Bei Generierungsfehler wird Template-basierter Fallback verwendet | `services/auto_healing.py:_get_fallback_content()` |

**Bedingungen:**
- Fallback-Anzahl wird protokolliert (`SectionRecoveryManager`)
- Bei > 3 Fallbacks pro Report: Alert wird ausgelöst
- Fallback-Content ist vordefiniert und geprüft

### 2.2 Section-Mismatch (G22)

| Mechanismus | Beschreibung | Implementierung |
|-------------|--------------|-----------------|
| **G22 Consistency Check** | Cross-Section-Konsistenz wird validiert und korrigiert | `services/consistency_engine.py` |
| **G22-X Cross-Language** | Sprachübergreifende Konsistenz (max. 8% Drift für Executive Summary) | `services/consistency_engine_g22x.py` |
| **Format Normalisierung** | HTML-Struktur und CSS werden standardisiert | `services/layout_consistency_engine.py` |

**Bedingungen:**
- Semantischer Drift ≤ 0.08 (8%) für Executive Sections
- Roadmap-Drift ≤ 0.05 (5%)
- KPI-Werte dürfen NICHT verändert werden

### 2.3 Format-Normalisierung

| Mechanismus | Beschreibung | Implementierung |
|-------------|--------------|-----------------|
| **HTML Minification** | HTML wird für PDF-Rendering optimiert | `services/html_minifier.py` |
| **Leak Phrase Removal** | LLM-typische Phrasen werden entfernt | `services/report_validator.py` |
| **Token Overflow Fix** | Zu lange Inhalte werden gekürzt (Beispiele entfernen, Truncation) | `services/auto_healing.py:auto_fix_token_overflow()` |
| **Persona Rewrite** | Persona-spezifische Begriffe werden angepasst | `services/auto_healing.py:apply_persona_rewrite_filter()` |

**Bedingungen:**
- Keine inhaltliche Bedeutungsänderung
- Nur vordefinierte Ersetzungen aus `PERSONA_REPLACEMENT_TERMS`
- Logging aller Änderungen

---

## 3. NICHT Erlaubte Auto-Heals

Die folgenden automatischen Korrekturen sind **VERBOTEN** und erfordern manuellen Eingriff oder Report-Abbruch:

### 3.1 Inhaltliche Bedeutungsänderungen

| Verboten | Begründung | Erkennung |
|----------|------------|-----------|
| **Semantische Neuformulierung** | Könnte Fachaussagen verfälschen | Drift-Threshold-Check |
| **Faktenkorrektur** | System hat keine Faktenprüfungs-Autorität | Nicht implementiert |
| **Numerische Anpassungen** | Könnte Business-Entscheidungen beeinflussen | KPI-Validierung |

**Beispiele für verbotene Änderungen:**
```
VERBOTEN: "ROI von 150%" → "ROI von 120%" (Zahlenänderung)
VERBOTEN: "hohes Risiko" → "mittleres Risiko" (Risikoeinschätzung)
VERBOTEN: "nicht compliant" → "teilweise compliant" (Compliance-Aussage)
```

### 3.2 Governance-Aussagen

| Verboten | Begründung | Erkennung |
|----------|------------|-----------|
| **AI Act Risiko-Level** | Rechtlich relevant, muss vom Validator stammen | `ai_act_override_risk_level` Check |
| **Compliance-Status** | Audit-relevant, keine Auto-Korrektur | Governance Policy Engine |
| **DSGVO-Einschätzungen** | Rechtlich bindend | Manual Review Required |

**Geschützte Felder:**
- `ai_act_risk_level`
- `compliance_status`
- `dsgvo_konformitaet`
- `governance_score`
- Alle Felder mit Präfix `_audit_`

### 3.3 Risiko-Scores

| Verboten | Begründung | Erkennung |
|----------|------------|-----------|
| **Risiko-Score-Änderung** | Grundlage für Investitionsentscheidungen | `CRITICAL_KPI_FIELDS` |
| **Readiness-Score** | Zentraler Bewertungsindikator | Score-Validierung |
| **Finanzielle KPIs** | ROI, NPV, IRR, Payback | Numerische Integritätsprüfung |

**CRITICAL_KPI_FIELDS (unveränderbar):**
```python
[
    "roi_percentage", "roi",
    "payback_months", "payback",
    "time_savings_hours", "time_savings",
    "risk_score", "readiness_score",
    "npv", "irr", "cost_savings"
]
```

---

## 4. Verhalten bei Verstoß

### 4.1 Hard-Fail Bedingungen

Ein **Hard-Fail** (sofortiger Abbruch) tritt auf bei:

| Bedingung | Fehlercode | Verhalten |
|-----------|------------|-----------|
| KPI-Mismatch zwischen Sprachen | `G22-X001-FAIL` | Report-Abbruch, Logging |
| Executive Summary Drift > 10% | `G22-X002-FAIL` | Report-Abbruch, Alert |
| Governance-Feld-Manipulation erkannt | `GOV-INTEGRITY-FAIL` | Report-Abbruch, Audit-Log |
| Zero-Leak-Guarantee verletzt | `LEAK-DETECT-FAIL` | Report-Abbruch, Cleanup |

### 4.2 Report-Abbruch

Bei Hard-Fail:

1. **Sofortiger Stopp** der Report-Generierung
2. **Fehler-Logging** mit vollständigem Context
3. **Alert** an Monitoring-System
4. **Keine Teil-Auslieferung** des Reports
5. **Cleanup** aller temporären Artifacts

```python
# Beispiel aus services/report_pipeline.py
if hard_fail_detected:
    log.error(f"[HARD-FAIL] {error_code}: {message}")
    record_hard_fail(error_code, context)
    raise ReportGenerationError(error_code, message)
```

### 4.3 CI-Fehler

Im Release-Check-Modus (`--release-check`):

| Prüfung | Erwartung | Bei Verstoß |
|---------|-----------|-------------|
| Hash-Vergleich | 100% Match mit Golden Reports | Exit Code 1 |
| Consistency-Score | = 100% | Exit Code 1 |
| Fallback-Count | = 0 | Exit Code 1 (Release-Modus) |

---

## 5. PLATIN+++ Guarantees

Die folgenden Garantien bleiben durch dieses Dokument **unangetastet**:

### 5.1 Zero-Leak Guarantee

- **Definition:** Keine LLM-typischen Phrasen im finalen Output
- **Implementierung:** `services/report_validator.py`
- **Prüfung:** Pre-Render + Post-Render Check

### 5.2 Zero-Fallback Guarantee (Release-Modus)

- **Definition:** Im Release-Modus werden keine Fallbacks akzeptiert
- **Implementierung:** `--release-check` Flag
- **Prüfung:** `SectionRecoveryManager.get_fallback_count() == 0`

### 5.3 Cross-Section-Consistency

- **Definition:** Alle Sections sind semantisch konsistent
- **Implementierung:** `services/consistency_engine.py`, `services/consistency_kernel_v7.py`
- **Prüfung:** G22 Rule Set + G22-X Cross-Language Rules

---

## 6. Monitoring & Audit

### 6.1 Logging-Anforderungen

Alle Auto-Healing-Aktivitäten müssen protokolliert werden:

```json
{
  "timestamp": "2025-12-13T10:30:00Z",
  "event_type": "auto_heal",
  "mechanism": "section_fallback",
  "section": "roadmap_90d",
  "original_word_count": 23,
  "final_word_count": 87,
  "fallback_used": true,
  "briefing_id": "12345"
}
```

### 6.2 Audit-Trail

Für Release-Reports:

1. **Input-Hash:** SHA-256 des Release-Profils
2. **Output-Hash:** SHA-256 des generierten Reports
3. **Healing-Log:** Alle Auto-Healing-Aktivitäten
4. **Validation-Result:** G22 + G22-X Prüfergebnisse

---

## 7. Änderungsprotokoll

| Version | Datum | Änderung | Autor |
|---------|-------|----------|-------|
| 1.0.0 | 2025-12-13 | Initiale Version | Claude |

---

## 8. Referenzen

- `services/auto_healing.py` - Haupt-Auto-Healing-Logik
- `services/consistency_engine.py` - G22 Consistency Engine
- `services/consistency_engine_g22x.py` - Cross-Language Consistency
- `services/report_validator.py` - Leak Detection & Validation
- `services/numerical_integrity_engine_v4.py` - KPI-Validierung
