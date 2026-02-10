# Railway Log Analyse & Projekt-Dokumentation

**Datum:** 2026-02-10
**Log-Zeitraum:** 2026-02-10 19:45:52 - 19:54:17 UTC
**Briefing-ID:** 618 | **Worker-ID:** worker-59cf288c-618-df92
**Ergebnis:** Pipeline FEHLGESCHLAGEN (1 kritischer Fehler)

---

## 1. Projekt-Architektur (Gesamtdokumentation)

### 1.1 Technologie-Stack

| Komponente | Technologie | Version |
|---|---|---|
| Framework | FastAPI | 0.111-0.115 |
| Runtime | Python / Uvicorn | python-3.12 |
| Datenbank | PostgreSQL (SQLAlchemy 2.0) | psycopg 3.1 |
| LLM-Provider | OpenAI (GPT-5.2), Anthropic (Claude) | openai 1.51+ |
| Research | Tavily, Perplexity (sonar-pro) | tavily-python 0.3 |
| E-Mail | Resend API | resend 2.0 |
| Hosting | Railway (Web + Worker Dyno) | Procfile-basiert |
| Auth | JWT (PyJWT) + Login-Code per E-Mail | passwordless |

### 1.2 Projektstruktur

```
api-ki-backend-neu/
├── main.py                    # FastAPI App, CORS, Router Mounting, Health Checks
├── gpt_analyze.py             # KERN: 16.951 Zeilen - Analyse-Pipeline (PLATIN+++ v5.4.3)
├── models.py                  # SQLAlchemy Models (User, Briefing, Analysis, Report, etc.)
├── settings.py                # Konfiguration via Env-Variablen
├── field_registry.py          # Feld-Registry fur Briefing-Daten
├── setup_database.py          # DB-Initialisierung / Migrationen
│
├── routes/                    # API-Endpunkte (12 Router)
│   ├── auth.py                # /api/auth/request-code, /api/auth/login
│   ├── briefings.py           # /api/briefings/submit (Briefing einreichen)
│   ├── analyze.py             # /api/analyze (Analyse starten)
│   ├── report.py              # /api/report (Report abrufen/diagnostics)
│   ├── feedback.py            # /api/feedback (Feedback speichern)
│   ├── monitoring.py          # /api/monitoring/status, /alerts, /metrics
│   ├── smoke.py               # /api/smoke (System-Check)
│   ├── dashboard.py           # /api/dashboard (KPI-Dashboard)
│   ├── reports_registry.py    # /api/reports (Versionierung)
│   ├── funding.py             # /api/funding (Foerderprogramme)
│   ├── feedback_dashboard.py  # Feedback-Loop Dashboard
│   └── tools_dashboard.py     # Tools-Dashboard
│
├── workers/
│   └── briefings_worker.py    # DB-Poll Worker: Holt Briefings mit status=accepted
│
├── services/                  # ~200 Module, 5.6 MB Geschaeftslogik
│   ├── auth.py                # Login-Code Generation, JWT
│   ├── mailer.py              # Resend E-Mail-Versand
│   ├── report_validator.py    # Qualitaets-Gate (CRITICAL/WARNING Validierung)
│   ├── zero_leak_engine.py    # Prompt-Leak Erkennung (FAIL-CLOSED Mechanismus)
│   ├── content_quality_enforcer.py  # Post-Processing Pipeline (179 KB)
│   ├── prompt_loader.py       # Prompt-Template System (Jinja2, Manifest)
│   ├── prompt_enhancer.py     # Kontext-Anreicherung fuer Prompts
│   ├── research_pipeline.py   # Hybrid Research (Tavily + Perplexity + RSS)
│   ├── business_case_engine_v2.py   # ROI/Payback Berechnung
│   ├── risk_engine_v2.py / v3.py    # Risiko-Bewertung, DPIA, AI Act
│   ├── benchmark_engine.py    # Branchenvergleich
│   ├── automation_roadmap_engine.py  # Automatisierungs-Roadmap
│   ├── consistency_engine.py  # Cross-Section Konsistenz (235 KB!)
│   ├── report_healer.py       # Report Auto-Reparatur (133 KB)
│   ├── branch_profile_engine.py     # Branchenprofile
│   ├── solo_compact_engine.py # Solo/Team/KMU Anpassung
│   ├── quickwins_renderer.py  # Quick-Win HTML-Rendering
│   ├── guardrails.py          # Input Guardrails
│   ├── openai_retry.py        # LLM Retry-Logik (Backoff)
│   ├── anthropic_client.py    # Claude Integration
│   └── ... (weitere ~170 Module)
│
├── prompts/                   # Prompt-Templates (Markdown)
│   ├── de/                    # 40+ Deutsche Prompt-Templates
│   ├── en/                    # Englische Templates
│   └── prompt_manifest.json   # Manifest fuer alle Prompts
│
├── config/
│   ├── size_profiles.py       # Solo/Team/KMU Konfiguration
│   ├── solo_terms.json        # Solo-spezifische Terminologie
│   └── tool_whitelist.yaml    # Erlaubte Tools pro Groesse
│
├── data/                      # Statische Daten (Branchen, Foerderungen)
├── templates/                 # Jinja2 HTML-Templates fuer Reports
├── migrations/                # SQL-Migrationen
├── tests/                     # Test Suite
├── Procfile                   # Railway: web + worker
└── requirements.txt           # Dependencies
```

### 1.3 Pipeline-Ablauf (Briefing -> Report)

```
1. Benutzer: POST /api/auth/request-code → Login-Code per E-Mail
2. Benutzer: POST /api/auth/login → JWT Token (httpOnly Cookie)
3. Benutzer: POST /api/briefings/submit → Briefing in DB (status=accepted)
4. Worker: briefings_worker.py pollt DB → Claim Briefing (status=processing)
5. Worker: gpt_analyze.run_briefing_pipeline() → analyze_briefing()
   a. Konfiguration laden (Guardrails, Prompt-System, Branch-Mapping)
   b. Solo/Team/KMU Erkennung → Size-Profile
   c. Scores berechnen (Governance, Security, Value, Enablement)
   d. Score-Kalibrierung (Realismus-Faktor)
   e. Business Case Berechnung (CAPEX, OPEX, ROI, Payback)
   f. 35 Sektionen PARALLEL generieren (max_workers=4)
   g. 2-Pass Expand fuer zu kurze Sektionen
   h. Post-Processing Pipeline:
      - Quick-Win Rendering (JSON -> HTML)
      - Sofort-Start Generator
      - Siezen-Guard (du -> Sie)
      - Content Quality Enforcer (Grammatik, Dedupe, etc.)
      - AI Act Module (Harmonisierung)
      - Zero-Leak Engine (Prompt-Leak Erkennung)
      - Report Validator (CRITICAL/WARNING)
   i. Research Pipeline (Tavily + Perplexity)
   j. Engine-Generierung (Risk, Business Case, Benchmark, etc.)
   k. HTML Rendering (Jinja2 Template)
   l. Final Validation → Quality Gate
6. Bei Erfolg: Report in DB speichern
7. Bei Fehler: Status=failed + Error in DB
```

---

## 2. Railway Log Analyse

### 2.1 Zusammenfassung des Log-Ablaufs

| Zeitstempel | Ereignis | Status |
|---|---|---|
| 19:45:49 | Login-Code E-Mail gesendet | OK |
| 19:46:07 | Login erfolgreich | OK |
| 19:46:39 | Briefing 618 eingereicht (status=accepted) | OK |
| 19:46:39 | Worker claimed Briefing 618 | OK |
| 19:46:40 | 35 Sektionen parallel gestartet | OK |
| 19:46:40 - 19:50:26 | LLM-Generierung (~226s parallel vs ~525s sequentiell) | OK |
| 19:50:26 | Quick-Wins JSON erfolgreich gerendert (5 Items) | OK |
| 19:50:37 | next_actions: `reason=length` (Token-Limit 600 erreicht) | WARNING |
| 19:50:37 - 19:50:51 | 23 One-Liner parallel generiert (~12.6s) | OK |
| 19:50:51 - 19:50:53 | Post-Processing (Truncation, Siezen, Quality Enforcer) | OK |
| 19:50:53 | Zero-Leak: `EXECUTIVE_DECISION_HTML` FAIL-CLOSED | REGENERIERT |
| 19:50:53 | Zero-Leak: `credential` in RISKS_HTML erkannt | WARNING |
| 19:50:57 | EXECUTIVE_DECISION regeneriert (erfolgreich) | OK |
| 19:51:07 | **QUALITY GATE BLOCKED: 1 Critical Error** | **FEHLER** |
| 19:51:07 | `GAMECHANGER_HTML`: 503 Woerter (Minimum: 750) | **CRITICAL** |
| 19:51:07 | Pipeline FAILED - Report nicht generiert | **FEHLER** |

### 2.2 Gesamtdauer: ~4 Minuten 28 Sekunden (19:46:39 - 19:51:07)

---

## 3. Identifizierte Fehler und Probleme

### 3.1 KRITISCH: GAMECHANGER_HTML zu kurz (Pipeline-Blocker)

**Fehler:**
```
[SECTION_TOO_SHORT] GAMECHANGER_HTML: Section zu kurz: 503 Woerter (Minimum fuer team: 750 Woerter)
ValueError: Report validation failed with 1 critical errors
```

**Ursache:**
1. LLM generierte nur 260 Woerter fuer `gamechanger` (initial)
2. 2-Pass Expand wurde ausgefuehrt: 260 -> 1032 Woerter (erfolgreich laut Log)
3. ABER: Die Truncation-Engine kuerzte den Inhalt danach aggressiv
4. Der `GAMECHANGER_HTML`-Abschnitt lief durch `[CI-DESIGN] Gamechanger compact: 5964 chars` (von 9845 chars)
5. Nach allen Post-Processing-Schritten blieben nur 503 Woerter uebrig

**Root Cause:** Die Expand-Logik in `gpt_analyze.py:11108` setzt `min_words=700` fuer gamechanger, aber der Validator (`report_validator.py:752`) erfordert 750 Woerter fuer `team`. Zusaetzlich kuerzt die CI-Design Compact-Funktion den Inhalt zu aggressiv.

**Diskrepanz:**
| Stelle | gamechanger min_words |
|---|---|
| gpt_analyze.py (Expand-Trigger) | 700 |
| report_validator.py (team) | 750 |
| **Luecke** | **50 Woerter** |

### 3.2 WARNING: next_actions Token-Limit erreicht

**Fehler:**
```
⚠️ LLM section=next_actions finished with reason=length (hit token limit 600) – risk of truncation
```

**Ursache:** In `gpt_analyze.py:12145` wird `max_tokens` auf 600 gedeckelt:
```python
max_tokens=min(params["max_tokens"], 600),
```
Das LLM erreicht dieses Limit und bricht mitten im Output ab (`reason=length` statt `reason=stop`). Der Inhalt kann unvollstaendige HTML-Tags oder abgeschnittenen Text enthalten.

### 3.3 WARNING: Zero-Leak FAIL-CLOSED fuer EXECUTIVE_DECISION_HTML

**Fehler:**
```
[leak_blacklist] EXECUTIVE_CRITICAL phrase="wobei kann ich helfen" hits=1 section=EXECUTIVE_DECISION_HTML → FAIL-CLOSED
[zero-leak] FAIL-CLOSED critical_hits=1 section=EXECUTIVE_DECISION_HTML
```

**Ursache:** Das LLM hat die Chatbot-Phrase "Wobei kann ich helfen" in den Executive Decision Text eingebaut. Die Zero-Leak-Engine behandelt dies als CRITICAL (trotz dass die Phrase auch in `DETERMINISTIC_PRESCRUB_PHRASES` in `zero_leak_engine.py:314` steht). Die Phrase wurde offenbar erst nach dem Prescrub-Schritt erkannt, was auf ein Race-Condition oder Duplikat-Problem hinweist.

**Regeneration:** Die Pipeline hat erfolgreich eine Regeneration durchgefuehrt (Attempt 1/2 erfolgreich, 625 Zeichen).

### 3.4 WARNING: "credential" Pattern in RISKS_HTML

**Fehler:**
```
[leak_blacklist] CRITICAL pattern="credential" hits=1 section=RISKS_HTML
[leak_blacklist] CRITICAL pattern="credential" hits=1 section=risks
```

**Ursache:** Das Wort "credential" erscheint im Risiko-Abschnitt als legitimer Fachbegriff (z.B. "Credential Management", "Credential Theft"). Die Zero-Leak-Engine erkennt dies faelschlicherweise als potenzielle Prompt-Leakage. In diesem Fall wurde kein FAIL-CLOSED ausgeloest (da es ein isolierter Hit ist), aber es erzeugt unnoetige Warnungen.

### 3.5 WARNING: 9 Validierungs-Warnungen

```
[SECTION_TOO_SHORT] strategie_governance: 153 Woerter (Minimum: 200)
[SECTION_TOO_SHORT] foerderpotenzial: 45 Woerter (Minimum: 600)
[REDUNDANCY_DETECTED] PILOT_PLAN_HTML, ROADMAP_HTML, ROADMAP_90D_HTML
[REDUNDANCY_DETECTED] PILOT_PLAN_HTML, roadmap, ROADMAP_HTML
[REDUNDANCY_DETECTED] DATA_READINESS_HTML, data_readiness
```

**Ursache bei foerderpotenzial (45 Woerter):**
- Das 2-Pass Expand ergab 1657 Woerter fuer foerderpotenzial (erfolgreich)
- Die `[AGGRESSIVE-TRUNCATION]` kuerzte von 17094 auf 8025 chars (53% reduziert)
- Aber die Validierung meldet 45 Woerter fuer die Shadow-Key `foerderpotenzial` (nicht `FOERDERPOTENZIAL_HTML`)
- Dies ist ein **Shadow-Key vs. HTML-Key Problem**: Die Validierung prueft den kuerzeren Shadow-Key statt den erweiterten HTML-Key

### 3.6 INFO: Logging-Level Konfiguration

**Beobachtung:** Alle `INFO`-Level Logs werden als `[err]` (stderr) an Railway gemeldet, waehrend nur HTTP-Access-Logs als `[inf]` (stdout) erscheinen. Dies ist kein technischer Fehler, aber macht das Log schwer lesbar, da INFO-Meldungen wie Fehler aussehen.

**Ursache:** Python `logging` schreibt standardmaessig auf `stderr`. Uvicorn Access-Logs gehen auf `stdout`. Railway kennzeichnet diese unterschiedlich.

---

## 4. Loesungsvorschlaege

### 4.1 FIX: Gamechanger Min-Words Alignment (KRITISCH)

**Problem:** gpt_analyze.py setzt Expand-Trigger bei 700 Woertern, Validator erfordert 750 fuer `team`.

**Loesung A (empfohlen): Expand-Trigger an Validator angleichen**

In `gpt_analyze.py` Zeile ~11108:
```python
# VORHER:
"gamechanger": 700,
# NACHHER:
"gamechanger": 800,  # 750 (Validator) + 50 Sicherheitsmarge fuer Post-Processing
```

**Loesung B: CI-Design Compact weniger aggressiv**

Die Funktion, die `gamechanger` von 9845 auf 5964 chars kuerzt (39% Reduktion), muss die Mindest-Wortanzahl respektieren.

**Loesung C: Validator-Toleranz fuer Post-Processed Content**

In `report_validator.py` koennte eine Toleranz von 10% eingefuehrt werden, wenn der Content durch Post-Processing-Schritte gekuerzt wurde.

### 4.2 FIX: next_actions Token-Limit erhoehen

In `gpt_analyze.py` Zeile ~12145:
```python
# VORHER:
max_tokens=min(params["max_tokens"], 600),
# NACHHER:
max_tokens=min(params["max_tokens"], 1200),  # Genuegend Platz fuer 5-7 Actions
```

### 4.3 FIX: "credential" als False-Positive in RISKS

In `services/zero_leak_engine.py`, die Pattern-Liste `CRITICAL_LEAK_PATTERNS` anpassen:
- Entweder "credential" nur im Kontext von API/Secrets erkennen (Regex statt Substring)
- Oder eine Whitelist fuer bekannte Sections wie `RISKS_HTML` einfuehren, in denen Sicherheitsbegriffe erwartet werden

```python
# Beispiel: Kontext-sensitives Pattern
"credential" -> nur matchen wenn gefolgt von ": ", "=", oder "leak"
```

### 4.4 FIX: Shadow-Key Validierung fuer foerderpotenzial

In `report_validator.py` sicherstellen, dass `foerderpotenzial` immer gegen `FOERDERPOTENZIAL_HTML` validiert wird (nicht gegen den Shadow-Key). Die `SECTION_KEY_MAP` muss vollstaendig sein:

```python
SECTION_KEY_MAP = {
    ...
    "foerderpotenzial": "FOERDERPOTENZIAL_HTML",  # Explicit HTML key
    ...
}
```

### 4.5 FIX: Zero-Leak Prescrub-Reihenfolge

Die Phrase "wobei kann ich helfen" steht sowohl in `DETERMINISTIC_PRESCRUB_PHRASES` als auch in `SUPPORT_LEAKS`. Sie sollte zuverlaessig im Prescrub entfernt werden, BEVOR die Critical-Scan laeuft. Pruefung, ob der Prescrub-Schritt tatsaechlich auf den EXECUTIVE_DECISION_HTML Key angewendet wird.

---

## 5. Optimierungsvorschlaege

### 5.1 Performance

| Bereich | Aktuell | Vorschlag | Erwarteter Effekt |
|---|---|---|---|
| Parallele LLM-Calls | max_workers=4 | max_workers=6-8 | ~30% schneller bei 35 Sektionen |
| Expand-Passes | Sequentiell nach Haupt-Generation | In Parallel-Pool integrieren | Eliminiert Warte-Engpaesse |
| Post-Processing | 2x Quality Enforcer Pipeline | 1x mit kombiniertem Pass | ~2s gespart |
| Research | Nach Content-Generierung | Parallel zur Content-Generierung | ~10s gespart |

### 5.2 Architektur

1. **gpt_analyze.py aufteilen (16.951 Zeilen):** Die Datei ist extrem gross und schwer wartbar. Empfehlung:
   - `gpt_analyze_sections.py` - Sektions-Generierung
   - `gpt_analyze_pipeline.py` - Pipeline-Orchestrierung
   - `gpt_analyze_postprocess.py` - Post-Processing
   - `gpt_analyze_validation.py` - Validierung & Quality Gate

2. **Consistency zwischen Expand und Validator:** Eine zentrale `min_words_config.py` einfuehren, die sowohl vom Expand-Trigger als auch vom Validator genutzt wird. Derzeit sind die Werte an zwei verschiedenen Stellen definiert und divergieren.

3. **Structured Logging:** Statt alle Logs auf stderr, ein strukturiertes Logging-Format (JSON) verwenden, das Railway korrekt als INFO/WARNING/ERROR klassifiziert:
   ```python
   logging.basicConfig(stream=sys.stdout, ...)  # stdout statt stderr
   ```

### 5.3 Zuverlaessigkeit

1. **Retry fuer fehlgeschlagene Briefings:** Aktuell wird bei einem Quality-Gate-Fehler das Briefing als `failed` markiert. Eine automatische Retry-Logik (max 2 Versuche) mit leicht angepassten Parametern (z.B. +100 max_tokens) wuerde die Erfolgsrate erhoehen.

2. **Graceful Degradation bei Section-Failures:** Statt die gesamte Pipeline zu stoppen, wenn eine Section zu kurz ist, koennte ein Fallback-Content eingesetzt werden (der bereits existiert, aber nur VOR dem Quality Gate greift).

3. **Monitoring-Alerts:** Bei Pipeline-Failures automatisch einen Alert senden (E-Mail oder Webhook), damit das Team zeitnah reagieren kann.

### 5.4 Sicherheit

1. **"credential" Pattern verbessern:** Kontext-sensitives Matching statt einfacher Substring-Suche, um False Positives in Risiko-Abschnitten zu vermeiden.

2. **Rate-Limiting:** Der Legacy-Endpoint `/api/briefing_async` hat ein Rate-Limit, aber der aktive Endpoint `/api/briefings/submit` sollte ebenfalls eins haben.

3. **Database Checkpoints:** Die PostgreSQL-Checkpoints im Log sind normal, aber die `distance=71 kB` und `estimate=297 kB` deuten auf wenig DB-Aktivitaet hin. Das ist fuer den aktuellen Umfang angemessen.

---

## 6. Zusammenfassung der Prioritaeten

| Prioritaet | Problem | Loesung | Aufwand |
|---|---|---|---|
| **P0 - KRITISCH** | gamechanger min_words Diskrepanz | Expand-Trigger auf 800+ erhoehen | Klein |
| **P0 - KRITISCH** | CI-Design Compact ignoriert min_words | Compact-Logik mit min_words Guard | Mittel |
| **P1 - HOCH** | next_actions Token-Limit 600 | Auf 1200 erhoehen | Klein |
| **P1 - HOCH** | foerderpotenzial Shadow-Key Validierung | SECTION_KEY_MAP vervollstaendigen | Klein |
| **P2 - MITTEL** | "credential" False-Positive | Kontext-sensitives Pattern | Mittel |
| **P2 - MITTEL** | Zero-Leak Prescrub Race-Condition | Prescrub-Reihenfolge pruefen | Mittel |
| **P3 - NIEDRIG** | Logging stderr vs stdout | Stream-Konfiguration aendern | Klein |
| **P3 - NIEDRIG** | gpt_analyze.py Groesse | Modularisierung planen | Gross |

---

## 7. Positive Beobachtungen

1. **Parallele Generierung funktioniert gut:** 226s parallel vs. geschaetzte 525s sequentiell (57% Zeitersparnis)
2. **2-Pass Expand ist effektiv:** Alle expandierten Sektionen (roadmap_12m, recommendations, foerderpotenzial, unternehmensprofil_markt) erreichten ihre Ziel-Wortanzahl
3. **Zero-Leak Regeneration funktioniert:** EXECUTIVE_DECISION wurde erfolgreich in einem Versuch regeneriert
4. **Quality Enforcer ist gruendlich:** 159 Grammatik-Fixes, 32 du->Sie Korrekturen, 5 Chat-Artefakte entfernt, 72 Duplikat-Absaetze entfernt
5. **Research Pipeline ist stabil:** Tavily (8 Tools, 8 Funding) und Perplexity (5 Market, 4 Competitors) lieferten alle Ergebnisse
6. **E-Mail-System funktioniert:** Resend API Response 200, E-Mail-ID erfolgreich zurueckgegeben
