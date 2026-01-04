# KI-Sicherheit.jetzt Backend - Projektstruktur

## Übersicht
FastAPI/Python Backend für KI-Readiness-Report-Generierung.
Stack: FastAPI + GPT-4/Claude + Railway Deployment

---

## Hauptkomponenten

```
api-ki-backend-neu/
├── gpt_analyze.py          # 509KB! HAUPTDATEI - Orchestriert gesamte Report-Generierung
├── main.py                 # FastAPI Endpoints
├── models.py               # SQLAlchemy Models (Analysis, Briefing, Report, User)
├── settings.py             # Konfiguration
├── field_registry.py       # Briefing-Feld-Definitionen
│
├── prompts/                # GPT/Claude Prompt-Templates
│   ├── de/                 # Deutsche Prompts (46 Dateien)
│   │   ├── executive_summary.md
│   │   ├── recommendations.md     # Handlungsempfehlungen
│   │   ├── foerderpotenzial.md    # Förderprogramme
│   │   ├── gamechanger.md         # Strategischer Bruchpunkt
│   │   ├── risks.md
│   │   ├── roadmap_90d.md
│   │   ├── roadmap_12m.md
│   │   └── ... (40+ weitere)
│   ├── en/                 # English Prompts
│   └── prompt_manifest.json
│
├── services/               # 150+ Service-Module
│   ├── funding_engine_v2.py       # Förderprogramm-Matching
│   ├── roi_calculator.py          # ROI/Business-Case-Berechnung
│   ├── recommendations_engine.py  # Empfehlungs-Generierung
│   ├── redundancy_detector.py     # Duplikat-Erkennung
│   ├── branch_profile_engine.py   # Branchenprofile + Markttrends
│   ├── prompt_loader.py           # Prompt-Template-Loader
│   ├── prompt_enhancer.py         # Persona-Anpassung (solo/team/kmu)
│   ├── anthropic_client.py        # Claude API Client
│   ├── llm_client.py              # OpenAI API Client
│   └── ...
│
├── data/                   # Statische Daten
│   ├── funding_programs.json           # ⚠️ ENTHÄLT "Digital Jetzt"!
│   ├── funding_programmes_core_2025.json
│   ├── benchmarks.json
│   └── branch_contexts/
│
├── templates/              # Jinja2 HTML-Templates
│   └── partials/
│
├── knowledge/              # Wissens-Snippets
│   ├── de/
│   └── en/
│
└── tests/                  # Umfangreiche Test-Suite
```

---

## Report-Generierungs-Pipeline

```
[Briefing] → [gpt_analyze.py] → [GPT-4/Claude] → [Services] → [HTML/PDF]
     │              │                  │              │
     ▼              ▼                  ▼              ▼
 Fragebogen   Prompt-Loading    Content-Gen    Post-Processing
 (main.py)    (prompt_loader)   (LLM Calls)   (Sanitizer, Formatter)
```

### Kernfunktionen in gpt_analyze.py:
- `analyze_briefing()` - Haupteinstiegspunkt (Zeile ~9500+)
- `_get_fallback_content()` - Fallback bei LLM-Fehlern
- `_build_top_3_massnahmen_html()` - Top-3 Empfehlungen (Zeile 10849)
- `_generate_sections_parallel()` - Parallele LLM-Aufrufe

---

## Externe APIs

| API | Zweck | Client-Datei |
|-----|-------|--------------|
| OpenAI GPT-4 | Primäre Content-Generierung | `services/llm_client.py` |
| Anthropic Claude | Dual-Model-Absicherung | `services/anthropic_client.py` |
| Perplexity | Research/Marktdaten | `services/provider_perplexity.py` |
| Tavily | Research/Marktdaten | `services/provider_tavily.py` |
| PDF Renderer | HTML→PDF | `services/pdf_client.py` |

---

## Kritische Dateien für die 7 Probleme

| Problem | Hauptdatei | Zeile |
|---------|-----------|-------|
| #1 Digital Jetzt | `data/funding_programs.json` | 1-9 |
| #2 Fördersumme Solo | `services/funding_engine_v2.py` | 60-70 (fit_solo) |
| #3 ROI 284% / 20h | `services/roi_calculator.py` | 42-43 |
| #4 90% AI-First | `services/branch_profile_engine.py` | 144-151 |
| #5 Duplikate | `gpt_analyze.py` | 8045-8046 |
| #6 Enterprise-Sprache | `prompts/de/gamechanger.md` | 97-136 |
| #7 42 Seiten | Keine explizite Begrenzung | - |

---

## Wichtige Konfigurationen

### Persona-Größen (COMPANY_SIZE)
- `solo` - Einzelunternehmer
- `team` - 2-10 Mitarbeiter
- `kmu` - 11-100+ Mitarbeiter

### Token-Budgets (in Prompts definiert)
- recommendations: 600 (solo: 0.8x = 480)
- foerderpotenzial: 3200 (solo: 0.8x)
- gamechanger: 350-450 Wörter

### Mindest-Wortlängen (in gpt_analyze.py:47-63)
- roadmap_12m: solo=500, team=600, kmu=700
- gamechanger: 750 (alle)
- foerderpotenzial: 720-880
- recommendations: 800+
