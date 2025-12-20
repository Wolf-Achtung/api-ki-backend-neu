# -*- coding: utf-8 -*-
"""
gpt_analyze.py – v5.3.0-PLATIN+++
---------------------------------------------------------------------
🎯 PLATIN+++ MULTI-LANGUAGE INTELLIGENCE (N4.2):
- ✅ Native Executive-Tonality in 5 languages (DE, EN, FR, IT, ES)
- ✅ Language-specific Layout-Adjustments with expansion factors
- ✅ Dual-Model-Absicherung (GPT+Claude → Semantic Merge)
- ✅ Zero-Drift Guarantee for Executive Summary + Roadmaps
- ✅ Cross-language KPI consistency validation
- ✅ Consulting glossary with language-specific terminology
- ✅ Multi-pass translation pipeline (Literal → Executive → Semantic → KPI Fix)
- ✅ Language-aware model selection per section

Version History:
- 4.13.5-gs: Original mit Research-Integration
- 4.14.0-PLATIN++: Prompt-System aktiviert, dynamische Daten
- 4.14.1-PLATIN++: Size-aware Fallbacks, Platzhalter-Fix, Aliasing-Korrektur
- 4.14.2-PLATIN++: Roadmap-Fallbacks inline, HAUPTLEISTUNG-Integration
- 5.2.0-PLATIN+++: N4.2 Multi-Language Intelligence Layer
- 5.3.0-PLATIN+++: N4.3 Governance Layer 2.0 / Enterprise Safety Layer

=============================================================================
Sprint N4.2: LLM SECTION FALLBACK DOCUMENTATION
=============================================================================

ARCHITEKTUR: Primäre Prompts + Fallback-System

1. PRIMÄRE PROMPTS (LLM-generiert via GPT/Anthropic):
   Location: prompts/de/*.md, prompts/en/*.md
   Loader: services/prompt_loader.py (load_prompt function)

   Key Sections mit Mindestlängen (PLATIN++ v5.3):
   ┌──────────────────────┬─────────────┬────────────────────────────────┐
   │ Section              │ Word Min    │ Prompt File                    │
   ├──────────────────────┼─────────────┼────────────────────────────────┤
   │ roadmap_12m          │ solo:500    │ prompts/de/roadmap_12m.md      │
   │                      │ team:600    │                                │
   │                      │ kmu:700     │                                │
   ├──────────────────────┼─────────────┼────────────────────────────────┤
   │ gamechanger          │ 750 (all)   │ prompts/de/gamechanger.md      │
   ├──────────────────────┼─────────────┼────────────────────────────────┤
   │ foerderpotenzial     │ 720-880     │ prompts/de/foerderpotenzial.md │
   ├──────────────────────┼─────────────┼────────────────────────────────┤
   │ recommendations      │ 800+        │ prompts/de/recommendations.md  │
   ├──────────────────────┼─────────────┼────────────────────────────────┤
   │ risks                │ 800+        │ prompts/de/risks.md            │
   ├──────────────────────┼─────────────┼────────────────────────────────┤
   │ unternehmensprofil   │ 500+        │ prompts/de/unternehmensprofil  │
   │   _markt             │             │   _markt.md                    │
   └──────────────────────┴─────────────┴────────────────────────────────┘

2. FALLBACK-SYSTEM (Hardcoded Templates):
   Function: _get_fallback_content(section_key, briefing, scores)
   Location: This file (gpt_analyze.py)

   Trigger-Bedingungen für Fallback:
   a) LLM API Fehler (Timeout, Rate Limit, etc.)
   b) Output unter Word-Minimum (nach Parsing)
   c) Static Sections (direkt Fallback ohne LLM-Call)
   d) max_fallbacks überschritten → Hard-Stop

   Fallback Word Targets (PLATIN+):
   - foerderpotenzial: 900+ Wörter (size-aware)
   - risks: 800+ Wörter (size-aware)
   - recommendations: 800+ Wörter (size-aware)
   - roadmap_12m: 900+ Wörter (size-aware)
   - roadmap/roadmap_90d: 1000+ Zeichen (size-aware)
   - gamechanger: 700+ Wörter

3. PERSONA-VARIATIONS (COMPANY_SIZE):
   - solo: Persönliche Formulierungen, keine Teams/Abteilungen
   - team: KI-Koordinator, gemeinsame Standards
   - kmu: Fachbereiche, Governance-Board, Rollout-Plan

4. SIZE-FILTERING (Sprint N):
   Zusätzlicher Solo-Filter in services/prompt_enhancer.py:
   apply_solo_persona_filter() entfernt unpassende Begriffe für Solo.

5. QUALITY GATES:
   - Word-Count Validierung nach LLM-Response
   - ErrorGate tracking für Fallback-Count
   - HARD_STOP_MAX_FALLBACKS = 5 (configurable)

=============================================================================
---------------------------------------------------------------------
"""
from __future__ import annotations

# === IMPORTS FIRST ===
import json
import logging
import os
import re
import threading
import uuid
import html
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from sqlalchemy.orm import Session
from jinja2 import Environment, BaseLoader

try:
    import resend as _resend  # echtes Modul, wenn vorhanden
except ImportError:  # pragma: no cover
    _resend = None

resend: Any = _resend  # für mypy ist resend jetzt immer definiert (Typ Any)

import core.db as core_db

from field_registry import fields  # added by Patch03
from models import Analysis, Briefing, Report, User
from services.report_renderer import render
from services.pdf_client import render_pdf_from_html, build_footer_template
from services.email_templates import render_report_ready_email
from settings import settings
from services.coverage_guard import analyze_coverage, build_html_report
from services.prompt_loader import load_prompt
from services.prompt_enhancer import PromptEnhancer, get_platin_config
from services.html_sanitizer import sanitize_sections_dict
from services.lang_utils import normalize_lang
from utils.hotfix_gold_standard import apply_hotfix, UTF8Handler
from utils.encoding_fixer import clean_briefing_data
from services.anthropic_client import call_anthropic, should_use_anthropic
from services.guardrails import (
    detect_guardrails_v5,
    format_guardrail_hits_for_context,
    GuardrailHit,
    # G-2 FIX: Import centralized keywords from guardrails.py (v5.0)
    GUARDRAIL_KEYWORDS_DE,
    GUARDRAIL_KEYWORDS_EN,
    NEGATION_WORDS_DE,
    NEGATION_WORDS_EN,
    ACTION_WORDS_DE,
    ACTION_WORDS_EN,
    SENSITIVE_AREAS_DE,
    SENSITIVE_AREAS_EN,
)
from services.alerts import (
    get_alert_manager,
    AlertType,
    AlertSeverity,
    MAX_FALLBACKS_PER_REPORT,
)
from services.monitoring import _metrics
from services.ai_act_module import (
    build_ai_act_sections,
    build_ai_act_sections_optimized,
    validate_ai_act_sections,
    ai_act_harmonize,
    validate_ai_act_persona_compliance,
)

# Und direkt nach Zeile 61, vor try:
UTF8Handler.setup_encoding()  # Global UTF-8 fix beim Start
try:
    from services.extra_sections import (
        calc_business_case,
        build_benchmarks_section,
        build_starter_stacks,
        build_responsible_ai_section,
        get_score_context,
        get_research_provenance,
        validate_business_case_plausibility,
        apply_ai_act_modifiers_to_business_case,  # G8.1
    )
except Exception:
    calc_business_case = None
    build_benchmarks_section = None
    build_starter_stacks = None
    build_responsible_ai_section = None
    get_score_context = None
    get_research_provenance = None
    validate_business_case_plausibility = None
    apply_ai_act_modifiers_to_business_case = None  # G8.1

# G8.2: Import centralized validation config
try:
    from services.config_validation import (
        ValidationConfig,
        get_min_words,
        validate_business_case_with_ai_act,
    )
except ImportError:

    class ValidationConfig:  # type: ignore[no-redef]
        """Fallback stub when config_validation not available."""
        AI_ACT_APPLY_BC_MODIFIERS = False

    def get_min_words(size: str, section_key: str) -> int:
        return 100

    def validate_business_case_with_ai_act(
        business_case: Dict[str, Any], risk_level: str = "minimal"
    ) -> list:
        return []

# G9.1: Import AI Act BC monitoring
try:
    from services.monitoring_ai_act import track_bc_modification
except ImportError:
    track_bc_modification = None

# N3.9: Enterprise Hardening Layer imports
try:
    from services.tenant_manager import (
        process_tenant_isolation,
        get_tenant_registry,
        TenantConfig as TenantConfigClass,
    )
    TENANT_MANAGER_AVAILABLE = True
except ImportError:
    process_tenant_isolation = None
    get_tenant_registry = None
    TenantConfigClass = None  # type: ignore[misc]
    TENANT_MANAGER_AVAILABLE = False

try:
    from services.audit_trace_engine import (
        get_audit_engine,
        AuditContext as AuditContextClass,
        EngineType as EngineTypeClass,
    )
    AUDIT_ENGINE_AVAILABLE = True
except ImportError:
    get_audit_engine = None
    AuditContextClass = None  # type: ignore[misc]
    EngineTypeClass = None  # type: ignore[misc]
    AUDIT_ENGINE_AVAILABLE = False

try:
    from services.safety_tuner import (
        process_safety_tuning,
        get_safety_tuner,
    )
    SAFETY_TUNER_AVAILABLE = True
except ImportError:
    process_safety_tuning = None
    get_safety_tuner = None
    SAFETY_TUNER_AVAILABLE = False

try:
    from services.performance_layer_v6 import (
        get_performance_layer,
        process_with_performance_layer,
    )
    PERFORMANCE_V6_AVAILABLE = True
except ImportError:
    get_performance_layer = None
    process_with_performance_layer = None
    PERFORMANCE_V6_AVAILABLE = False

try:
    from services.executive_narrative_engine import (
        process_executive_narrative_v2,
        analyze_executive_narrative_v2,
    )
    EXECUTIVE_NARRATIVE_V2_AVAILABLE = True
except ImportError:
    process_executive_narrative_v2 = None
    analyze_executive_narrative_v2 = None
    EXECUTIVE_NARRATIVE_V2_AVAILABLE = False

# G17.3: Import FT Signal Extractor
try:
    from services.ft_signal_extractor import (
        extract_llm_signals,
        FT_SIGNAL_EXTRACTION_ENABLED,
        FT_BUILD_DATASET_ON_REPORT,
    )
    from services.ft_dataset_builder import (
        accumulate_signals,
        build_training_dataset,
    )
except ImportError:
    extract_llm_signals = None
    FT_SIGNAL_EXTRACTION_ENABLED = False
    FT_BUILD_DATASET_ON_REPORT = False
    accumulate_signals = None
    build_training_dataset = None

# N4.0: Autonomous Engine Layer imports
try:
    from services.meta_engine_scheduler import (
        get_scheduler,
        process_meta_scheduling,
        get_engine_status,
    )
    META_SCHEDULER_AVAILABLE = True
except ImportError:
    get_scheduler = None
    process_meta_scheduling = None
    get_engine_status = None
    META_SCHEDULER_AVAILABLE = False

try:
    from services.model_strategy_layer import (
        get_model_strategy,
        select_model,
        dual_generate,
        semantic_merge,
    )
    MODEL_STRATEGY_AVAILABLE = True
except ImportError:
    get_model_strategy = None
    select_model = None
    dual_generate = None
    semantic_merge = None
    MODEL_STRATEGY_AVAILABLE = False

try:
    from services.simulation_engine import (
        get_simulation_engine,
        run_monte_carlo,
        run_scenario_analysis,
        run_operational_simulation,
    )
    SIMULATION_ENGINE_AVAILABLE = True
except ImportError:
    get_simulation_engine = None
    run_monte_carlo = None
    run_scenario_analysis = None
    run_operational_simulation = None
    SIMULATION_ENGINE_AVAILABLE = False

try:
    from services.knowledge_fusion_engine import (
        get_knowledge_fusion_engine,
        fuse_research_insights,
        cluster_insights,
        extract_key_signals,
        build_market_thesis,
    )
    KNOWLEDGE_FUSION_AVAILABLE = True
except ImportError:
    get_knowledge_fusion_engine = None
    fuse_research_insights = None
    cluster_insights = None
    extract_key_signals = None
    build_market_thesis = None
    KNOWLEDGE_FUSION_AVAILABLE = False

try:
    from services.governance_engine import (
        get_governance_engine,
        assess_ai_governance,
        get_governance_maturity_score,
        generate_raci_matrix,
        get_risk_controls,
    )
    GOVERNANCE_ENGINE_AVAILABLE = True
except ImportError:
    get_governance_engine = None
    assess_ai_governance = None
    get_governance_maturity_score = None
    generate_raci_matrix = None
    get_risk_controls = None
    GOVERNANCE_ENGINE_AVAILABLE = False

try:
    from services.prompt_evolution_engine import (
        get_prompt_evolution_engine,
        register_prompt_for_evolution,
        evolve_prompt,
        get_evolved_prompt,
        get_prompt_evolution_map,
    )
    PROMPT_EVOLUTION_AVAILABLE = True
except ImportError:
    get_prompt_evolution_engine = None
    register_prompt_for_evolution = None
    evolve_prompt = None
    get_evolved_prompt = None
    get_prompt_evolution_map = None
    PROMPT_EVOLUTION_AVAILABLE = False

# N4.1: Executive Experience Layer imports
try:
    from services.executive_navigation_engine import (
        get_navigation_engine,
        build_executive_navigation,
        get_bookmark_map,
        get_executive_flow_map,
    )
    NAVIGATION_ENGINE_AVAILABLE = True
except ImportError:
    get_navigation_engine = None
    build_executive_navigation = None
    get_bookmark_map = None
    get_executive_flow_map = None
    NAVIGATION_ENGINE_AVAILABLE = False

try:
    from services.executive_summary_investment import (
        get_executive_summary_engine,
        generate_executive_summary_v6,
        get_investment_thesis,
        get_ninety_day_mandate,
    )
    EXEC_SUMMARY_V6_AVAILABLE = True
except ImportError:
    get_executive_summary_engine = None
    generate_executive_summary_v6 = None
    get_investment_thesis = None
    get_ninety_day_mandate = None
    EXEC_SUMMARY_V6_AVAILABLE = False

try:
    from services.insight_compression_engine import (
        get_compression_engine,
        compress_to_pyramid,
        get_key_insight,
        validate_mece_compliance,
    )
    INSIGHT_COMPRESSION_AVAILABLE = True
except ImportError:
    get_compression_engine = None
    compress_to_pyramid = None
    get_key_insight = None
    validate_mece_compliance = None
    INSIGHT_COMPRESSION_AVAILABLE = False

try:
    from services.executive_layout_engine import (
        get_layout_engine,
        process_layout,
        create_card,
        get_font_spec,
    )
    LAYOUT_ENGINE_AVAILABLE = True
except ImportError:
    get_layout_engine = None
    process_layout = None
    create_card = None
    get_font_spec = None
    LAYOUT_ENGINE_AVAILABLE = False

try:
    from services.executive_transformation_roadmap import (
        get_roadmap_engine,
        build_transformation_roadmap,
        get_decision_checkpoints_by_horizon,
    )
    TRANSFORMATION_ROADMAP_AVAILABLE = True
except ImportError:
    get_roadmap_engine = None
    build_transformation_roadmap = None
    get_decision_checkpoints_by_horizon = None
    TRANSFORMATION_ROADMAP_AVAILABLE = False

try:
    from services.executive_clarity_engine import (
        get_clarity_engine,
        clarify_text,
        clarify_sections,
        validate_report_clarity,
        get_clarity_score,
    )
    CLARITY_ENGINE_AVAILABLE = True
except ImportError:
    get_clarity_engine = None
    clarify_text = None
    clarify_sections = None
    validate_report_clarity = None
    get_clarity_score = None
    CLARITY_ENGINE_AVAILABLE = False

# N4.3: Governance Layer 2.0 / Enterprise Safety Layer imports
try:
    from services.n43_integration import (
        process_n43_governance,
        validate_n43_dod,
        get_n43_status,
        N43Report,
    )
    N43_GOVERNANCE_AVAILABLE = True
except ImportError:
    process_n43_governance = None
    validate_n43_dod = None
    get_n43_status = None
    N43Report = None  # type: ignore[misc]
    N43_GOVERNANCE_AVAILABLE = False

# Initialize logger
log = logging.getLogger(__name__)

# =============================================================================
# HARD STOP & ERROR-GATE ARCHITECTURE (Sprint A)
# =============================================================================

# Environment-controlled hard stop settings
HARD_STOP_ON_SIZE_MISMATCH = os.getenv("HARD_STOP_ON_SIZE_MISMATCH", "0") in ("1", "true", "True")
HARD_STOP_MAX_FALLBACKS = int(os.getenv("HARD_STOP_MAX_FALLBACKS", str(MAX_FALLBACKS_PER_REPORT)))

# Placeholder detection pattern - blocks report if found
PLACEHOLDER_PATTERN = re.compile(
    r"\[(Name|Placeholder|Beispiel.*?)\]|"
    r"Freitextfeld|"
    r"Template-Marker|"
    r"\{\{PLACEHOLDER\}\}|"
    r"\{\{[A-Z_]+\}\}",  # Any unresolved Jinja variable
    re.IGNORECASE
)

# Size-specific forbidden terms (solo should not have team/department terms)
SOLO_FORBIDDEN_TERMS = [
    "Team aufbauen", "Mitarbeiter einstellen", "Abteilung", "Abteilungen",
    "Fachbereich", "Fachbereiche", "Projektteam", "Teams"
]

# =============================================================================
# TEIL 3.1.4: UI_STRINGS - Language-aware UI labels for EN/DE
# =============================================================================
# Maps German UI strings to English equivalents for locale-aware fallback content
UI_STRINGS: Dict[str, Dict[str, str]] = {
    # Section headers
    "recommendations_title": {"de": "Handlungsempfehlungen – Ihre nächsten Schritte mit KI", "en": "Recommendations – Your Next Steps with AI"},
    "recommendations_h2": {"de": "Handlungsempfehlungen", "en": "Recommendations"},
    "overview": {"de": "Überblick", "en": "Overview"},
    "risk_matrix": {"de": "Risiko-Matrix – Überblick über zentrale Risiken", "en": "Risk Matrix – Overview of Key Risks"},
    "priorities_overview": {"de": "Prioritäten-Überblick", "en": "Priorities Overview"},
    "company_overview": {"de": "Ihr Unternehmen im Überblick", "en": "Your Company at a Glance"},
    "summary": {"de": "Zusammenfassung", "en": "Summary"},
    "assessment": {"de": "Bewertung", "en": "Assessment"},
    "maturity_level": {"de": "Reifegrad", "en": "Maturity Level"},
    "key_metrics": {"de": "Kennzahlen", "en": "Key Metrics"},
    "risks": {"de": "Risiken", "en": "Risks"},
    "measures": {"de": "Maßnahmen", "en": "Measures"},
    "primary_goal": {"de": "Hauptziel", "en": "Primary Goal"},
    "next_steps": {"de": "Nächste Schritte", "en": "Next Steps"},

    # Table headers and labels
    "company_size": {"de": "Unternehmensgröße", "en": "Company Size"},
    "report_date": {"de": "Reportdatum", "en": "Report Date"},
    "industry": {"de": "Branche", "en": "Industry"},
    "comparison": {"de": "Vergleich", "en": "Comparison"},
    "value": {"de": "Wert", "en": "Value"},
    "source": {"de": "Quelle", "en": "Source"},
    "estimate": {"de": "Schätzung (konservativ)", "en": "Estimate (conservative)"},

    # Compliance terms
    "gdpr": {"de": "DSGVO", "en": "GDPR"},
    "gdpr_compliant": {"de": "DSGVO-konforme", "en": "GDPR-compliant"},
    "gdpr_recommendation": {"de": "DSGVO-konforme Empfehlung (ohne Rechtsberatung)", "en": "GDPR-compliant recommendation (without legal advice)"},

    # Notes and estimates
    "note": {"de": "Hinweis", "en": "Note"},
    "estimates": {"de": "Näherungen", "en": "Estimates"},
    "example": {"de": "Beispiel", "en": "Example"},
    "hint": {"de": "Hinweis", "en": "Note"},

    # Business case labels
    "costs": {"de": "Kosten", "en": "Costs"},
    "benefits": {"de": "Nutzen", "en": "Benefits"},
    "investment": {"de": "Investition", "en": "Investment"},
    "savings": {"de": "Einsparungen", "en": "Savings"},
    "conservative": {"de": "Konservativ", "en": "Conservative"},
    "realistic": {"de": "Realistisch", "en": "Realistic"},
    "optimistic": {"de": "Optimistisch", "en": "Optimistic"},
    "time_horizon": {"de": "Zeithorizont", "en": "Time Horizon"},
    "priority": {"de": "Priorität", "en": "Priority"},
    "ownership": {"de": "Verantwortung", "en": "Ownership"},
    "responsible": {"de": "Verantwortlich", "en": "Responsible"},

    # Recommendation labels
    "focus": {"de": "Schwerpunkt", "en": "Focus"},
    "action": {"de": "Maßnahme", "en": "Action"},
    "benefit_impact": {"de": "Nutzen & Wirkung", "en": "Benefit & Impact"},
    "effort_budget": {"de": "Aufwand & Budget", "en": "Effort & Budget"},
    "funding_opportunity": {"de": "Förderchance", "en": "Funding Opportunity"},
    "recommended_actions": {"de": "Empfohlene Schwerpunkt-Maßnahmen", "en": "Recommended Focus Actions"},

    # Quick wins / Roadmap
    "quick_win": {"de": "Quick Win", "en": "Quick Win"},
    "roadmap": {"de": "Roadmap", "en": "Roadmap"},
    "implementation": {"de": "Umsetzung", "en": "Implementation"},

    # Risk labels
    "risk_level": {"de": "Risiko-Level", "en": "Risk Level"},
    "probability": {"de": "Eintrittswahrscheinlichkeit", "en": "Probability"},
    "impact": {"de": "Auswirkung", "en": "Impact"},

    # Time/Size terms
    "month": {"de": "Monat", "en": "Month"},
    "months": {"de": "Monate", "en": "Months"},
    "quarter": {"de": "Quartal", "en": "Quarter"},
    "your_company": {"de": "Ihr Unternehmen", "en": "Your Company"},
    "your_region": {"de": "Ihrem Bundesland", "en": "your region"},

    # Misc fallback texts
    "size_hint_note": {"de": "Hinweis: Größenwerte sind konservative Schätzungen (mangels belastbarer Daten). Branchenwerte stammen aus aktuellen Studien; siehe Quelle.", "en": "Note: Size values are conservative estimates (due to lack of reliable data). Industry values are from current studies; see source."},
}


def ui(key: str, lang: str = "de") -> str:
    """Get UI string for the given key in the specified language."""
    entry = UI_STRINGS.get(key, {})
    return entry.get(lang, entry.get("de", key))


class ReportErrorGate:
    """
    Standardized error container for report generation.
    Tracks all errors, warnings, and failures during report generation.
    """

    def __init__(self, run_id: str = ""):
        self.run_id = run_id
        self.critical_errors: List[str] = []
        self.warnings: List[str] = []
        self.sections_failed: List[str] = []
        self.fallback_count: int = 0
        self.prompt_failures: List[str] = []
        self.guardrail_leaks: List[str] = []
        self.placeholder_violations: List[str] = []
        self.size_mismatches: List[str] = []

    def add_critical(self, error: str) -> None:
        """Add a critical error that will block report generation."""
        self.critical_errors.append(error)
        log.error("[%s] CRITICAL: %s", self.run_id, error)

    def add_warning(self, warning: str) -> None:
        """Add a warning (logged but may not block)."""
        self.warnings.append(warning)
        log.warning("[%s] WARNING: %s", self.run_id, warning)

    def add_section_failure(self, section: str, reason: str) -> None:
        """Track a failed section."""
        self.sections_failed.append(f"{section}: {reason}")
        log.error("[%s] SECTION FAILED: %s - %s", self.run_id, section, reason)

    def add_prompt_failure(self, prompt_name: str, reason: str) -> None:
        """Track a prompt loading failure."""
        self.prompt_failures.append(f"{prompt_name}: {reason}")
        log.error("[%s] PROMPT FAILED: %s - %s", self.run_id, prompt_name, reason)

    def add_guardrail_leak(self, section: str) -> None:
        """Track a GuardrailHit object that leaked into sections."""
        self.guardrail_leaks.append(section)
        log.error("[%s] GUARDRAIL LEAK: GuardrailHit object in section %s", self.run_id, section)

    def add_placeholder_violation(self, section: str, placeholder: str) -> None:
        """Track an unresolved placeholder."""
        self.placeholder_violations.append(f"{section}: {placeholder}")
        log.error("[%s] PLACEHOLDER: Unresolved '%s' in section %s", self.run_id, placeholder, section)

    def add_size_mismatch(self, section: str, term: str, persona: str) -> None:
        """Track a size/persona term mismatch."""
        self.size_mismatches.append(f"{section}: '{term}' invalid for {persona}")
        log.warning("[%s] SIZE MISMATCH: '%s' in %s (persona=%s)", self.run_id, term, section, persona)

    def increment_fallback(self) -> None:
        """Increment fallback counter."""
        self.fallback_count += 1

    def has_blockers(self) -> bool:
        """Check if there are any blocking errors."""
        return bool(
            self.critical_errors or
            self.sections_failed or
            self.prompt_failures or
            self.guardrail_leaks or
            self.placeholder_violations or
            self.fallback_count > HARD_STOP_MAX_FALLBACKS or
            (HARD_STOP_ON_SIZE_MISMATCH and self.size_mismatches)
        )

    def get_block_reason(self) -> str:
        """Get the primary reason for blocking."""
        if self.critical_errors:
            return f"Critical errors: {self.critical_errors[0]}"
        if self.sections_failed:
            return f"Section failed: {self.sections_failed[0]}"
        if self.prompt_failures:
            return f"Prompt failure: {self.prompt_failures[0]}"
        if self.guardrail_leaks:
            return f"GuardrailHit leak in: {self.guardrail_leaks[0]}"
        if self.placeholder_violations:
            return f"Placeholder violation: {self.placeholder_violations[0]}"
        if self.fallback_count > HARD_STOP_MAX_FALLBACKS:
            return f"Too many fallbacks: {self.fallback_count} > {HARD_STOP_MAX_FALLBACKS}"
        if HARD_STOP_ON_SIZE_MISMATCH and self.size_mismatches:
            return f"Size mismatch: {self.size_mismatches[0]}"
        return "Unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/alerts."""
        return {
            "run_id": self.run_id,
            "critical_errors": self.critical_errors,
            "warnings": self.warnings,
            "sections_failed": self.sections_failed,
            "fallback_count": self.fallback_count,
            "prompt_failures": self.prompt_failures,
            "guardrail_leaks": self.guardrail_leaks,
            "placeholder_violations": self.placeholder_violations,
            "size_mismatches": self.size_mismatches,
            "has_blockers": self.has_blockers(),
        }


# Thread-local storage for error gate (accessible during parallel execution)
_error_gate_local = threading.local()


def get_error_gate() -> Optional[ReportErrorGate]:
    """Get the current error gate from thread-local storage."""
    gate: Any = getattr(_error_gate_local, "gate", None)
    if isinstance(gate, ReportErrorGate):
        return gate
    return None


def set_error_gate(gate: ReportErrorGate) -> None:
    """Set the error gate in thread-local storage."""
    _error_gate_local.gate = gate


def guardrails_to_text(hits: List[GuardrailHit]) -> str:
    """
    Serialize GuardrailHit objects to plain text for safe inclusion in sections.
    This prevents 'Object of type GuardrailHit is not JSON serializable' errors.
    """
    if not hits:
        return ""

    lines = []
    for hit in hits:
        conf_pct = int(hit.confidence * 100)
        lines.append(f"• {hit.sentence} (Confidence: {conf_pct}%, Reason: {hit.reason})")

    return "\n".join(lines)


def check_section_for_placeholders(section_name: str, content: str, gate: ReportErrorGate) -> bool:
    """
    Check section content for unresolved placeholders.
    Returns True if placeholders found (blocking), False if clean.
    """
    if not content or not isinstance(content, str):
        return False

    matches = PLACEHOLDER_PATTERN.findall(content)
    if matches:
        for match in matches[:3]:  # Log first 3 matches
            gate.add_placeholder_violation(section_name, str(match))
        return True
    return False


def check_section_for_size_mismatch(
    section_name: str,
    content: str,
    persona: str,
    gate: ReportErrorGate
) -> bool:
    """
    Check section content for persona/size term mismatches.
    Returns True if mismatch found, False if clean.
    """
    if not content or not isinstance(content, str):
        return False

    if persona != "solo":
        return False

    content_lower = content.lower()
    for term in SOLO_FORBIDDEN_TERMS:
        if term.lower() in content_lower:
            gate.add_size_mismatch(section_name, term, persona)
            return True
    return False


def hard_stop_if_invalid(
    sections: Dict[str, Any],
    gate: ReportErrorGate,
    persona: str = "team",
    run_id: str = ""
) -> None:
    """
    Central gate function - raises RuntimeError if report is invalid.
    Called BEFORE rendering to prevent bad reports from being generated.

    Checks:
    1. Critical errors in error gate
    2. GuardrailHit objects leaked into sections
    3. Null/empty/error sections
    4. Unresolved placeholders
    5. Size mismatches (if enabled)
    6. Excessive fallbacks
    """
    alert_mgr = get_alert_manager()

    # 1. Check error gate for pre-existing critical errors
    if gate.critical_errors:
        _trigger_hard_stop_alert(gate, run_id, alert_mgr)
        raise RuntimeError(f"HARD STOP: Critical errors detected - {gate.critical_errors[0]}")

    # 2. Check for GuardrailHit object leaks
    for key, value in sections.items():
        if isinstance(value, GuardrailHit):
            gate.add_guardrail_leak(key)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, GuardrailHit):
                    gate.add_guardrail_leak(f"{key}[list]")
                    break

    # 3. Check for null/empty/error sections
    critical_sections = [
        "EXECUTIVE_SUMMARY_HTML", "executive_summary",
        "ROADMAP_12M_HTML", "roadmap_12m",
        "RECOMMENDATIONS_HTML", "recommendations",
    ]
    for key in critical_sections:
        value = sections.get(key)
        if value is None or value == "":
            gate.add_section_failure(key, "Empty or null content")
        elif isinstance(value, str) and "[Error:" in value:
            gate.add_section_failure(key, "Contains error marker")

    # 4. Check all string sections for placeholders
    for key, value in sections.items():
        if isinstance(value, str) and len(value) > 10:
            check_section_for_placeholders(key, value, gate)

    # 5. Check for size mismatches (if persona is solo)
    if persona == "solo":
        for key, value in sections.items():
            if isinstance(value, str) and len(value) > 50:
                check_section_for_size_mismatch(key, value, persona, gate)

    # 6. Check fallback count
    if gate.fallback_count > HARD_STOP_MAX_FALLBACKS:
        gate.add_critical(f"Excessive fallbacks: {gate.fallback_count} > {HARD_STOP_MAX_FALLBACKS}")

    # Final check - raise if blockers found
    if gate.has_blockers():
        _trigger_hard_stop_alert(gate, run_id, alert_mgr)
        reason = gate.get_block_reason()
        raise RuntimeError(f"HARD STOP: {reason}")

    log.info("[%s] ✅ Error gate passed - report is valid for rendering", run_id)


def _trigger_hard_stop_alert(gate: ReportErrorGate, run_id: str, alert_mgr: Any) -> None:
    """Trigger monitoring alert and increment metrics for hard stop."""
    try:
        alert_mgr.create_alert(
            AlertType.MULTIPLE_FALLBACKS,  # Reusing closest alert type
            AlertSeverity.CRITICAL,
            f"HARD STOP triggered: {gate.get_block_reason()}",
            gate.to_dict(),
        )
        _metrics.increment("hard_stop.count")
        _metrics.record("hard_stop.fallbacks", gate.fallback_count)
    except Exception as e:
        log.warning("[%s] Failed to send hard stop alert: %s", run_id, e)


# --- Patch03: field label helper ---

# === KSJ helpers: Jinja rendering & placeholder fix =======================
_ksj_jinja_env = Environment(loader=BaseLoader(), autoescape=False)

def ksj_render_string(tpl_text: str, ctx: dict) -> str:
    try:
        return str(_ksj_jinja_env.from_string(tpl_text).render(**ctx))
    except Exception as e:
        return tpl_text  # be permissive in prod

def ksj_build_numeric_ctx(answers: dict, env: dict, calc: dict | None) -> dict:
    # merge numeric context for Exec Summary & Business Case
    ctx = {}
    if calc:
        ctx.update({
            "CAPEX_REALISTISCH_EUR": calc.get("CAPEX_REALISTISCH_EUR"),
            "OPEX_REALISTISCH_EUR": calc.get("OPEX_REALISTISCH_EUR"),
            "EINSPARUNG_MONAT_EUR": calc.get("EINSPARUNG_MONAT_EUR"),
            "PAYBACK_MONTHS": calc.get("PAYBACK_MONTHS"),
            "ROI_12M": calc.get("ROI_12M"),
            "BUSINESS_CASE_TABLE_HTML": calc.get("BUSINESS_CASE_TABLE_HTML"),
        })
    # quick-win hours if present, otherwise use fallback
    qw_hours = None
    for k in ("qw_hours_total", "quick_wins_total_hours", "sum_quickwin_hours"):
        if k in answers and isinstance(answers[k], (int,float)):
            qw_hours = int(answers[k])
            break
    if qw_hours is None:
        # Fallback calculation: DEFAULT_QW1_H + DEFAULT_QW2_H + FALLBACK_QW_MONTHLY_H
        qw_hours = int(env.get("DEFAULT_QW1_H", 10)) + int(env.get("DEFAULT_QW2_H", 8)) + int(env.get("FALLBACK_QW_MONTHLY_H", 18))
    ctx["qw_hours_total"] = qw_hours
    return ctx

def ksj_fix_placeholders_in_sections(sections: dict, answers: dict, scores: dict) -> dict:
    """Render any Jinja-like placeholders in section strings using numeric ctx."""
    env_defaults = {
        "DEFAULT_STUNDENSATZ_EUR": 60,
        "DEFAULT_QW1_H": 10,
        "DEFAULT_QW2_H": 8,
        "FALLBACK_QW_MONTHLY_H": 18,
    }
    calc = None

    numeric = ksj_build_numeric_ctx(answers, env_defaults, calc or {})
    # Copy numeric values to sections for template access (use direct assignment, not setdefault)
    for key in ['qw_hours_total', 'CAPEX_REALISTISCH_EUR', 'OPEX_REALISTISCH_EUR',
                'EINSPARUNG_MONAT_EUR', 'PAYBACK_MONTHS', 'ROI_12M']:
        if key in numeric and numeric[key] is not None:
            sections[key] = numeric[key]
    # also bring scores if present
    if isinstance(scores, dict):
        numeric.update({
            "score_gesamt": scores.get("overall") or scores.get("gesamt") or "",
            "score_befaehigung": scores.get("enablement") or scores.get("befaehigung") or "",
            "score_governance": scores.get("governance") or "",
            "score_sicherheit": scores.get("security") or scores.get("sicherheit") or "",
            "score_nutzen": scores.get("value") or scores.get("nutzen") or "",
        })
    # render string values
    for k,v in list(sections.items()):
        if isinstance(v, str) and "{{" in v and "}}" in v:
            sections[k] = ksj_render_string(v, numeric)
    # append extra sections if missing but available via builders
    if callable(build_benchmarks_section) and "BENCHMARKS_SECTION_HTML" not in sections:
        try:
            sections["BENCHMARKS_SECTION_HTML"] = build_benchmarks_section(scores or {})
        except Exception:
            pass
    if callable(build_starter_stacks) and "STARTER_STACKS_HTML" not in sections:
        try:
            sections["STARTER_STACKS_HTML"] = build_starter_stacks(answers or {})
        except Exception:
            pass
    if callable(build_responsible_ai_section) and "RESPONSIBLE_AI_HTML" not in sections:
        try:
            sections["RESPONSIBLE_AI_HTML"] = build_responsible_ai_section({
                "four_pillars": os.getenv("FOUR_PILLARS_PATH", "knowledge/four_pillars.html"),
                "legal_pitfalls": os.getenv("LEGAL_PITFALLS_PATH", "knowledge/legal_pitfalls.html"),
                "ten_20_70": os.getenv("TEN_20_70_PATH", "knowledge/ten_20_70.html"),
                "kmu_keypoints": os.getenv("KMU_KEYPOINTS_PATH", "knowledge/kmu_keypoints.html"),
            })
        except Exception:
            pass
    return sections
# ========================================================================
def _label_for(field_key, value):
    try:
        opts = fields.get(field_key, {}).get("options") or []
        for o in opts:
            if str(o.get("value")) == str(value):
                return o.get("label") or value
    except Exception as e:
        log.debug("Failed to get label for field %s: %s", field_key, str(e)[:100])
    return value

def _labels_for_list(field_key, values):
    if not isinstance(values, (list, tuple)):
        return _label_for(field_key, values)
    out = []
    for v in values:
        out.append(_label_for(field_key, v))
    return ", ".join([x for x in out if x])


# === STRATEGIC CONTEXT BLOCK =============================================

# G-2 FIX: v4.0 duplicates removed - using centralized keywords from services/guardrails.py
# Aliases for backward compatibility (all definitions now in services/guardrails.py v5.0)
GUARDRAIL_DETECTION_KEYWORDS = GUARDRAIL_KEYWORDS_DE  # DE keywords from guardrails.py
NEGATION_WORDS = NEGATION_WORDS_DE  # DE negation words from guardrails.py
ACTION_WORDS = ACTION_WORDS_DE  # DE action words from guardrails.py
SENSITIVE_AREAS = SENSITIVE_AREAS_DE  # DE sensitive areas from guardrails.py

# English aliases
GUARDRAIL_DETECTION_KEYWORDS_EN = GUARDRAIL_KEYWORDS_EN  # EN keywords from guardrails.py
# Note: NEGATION_WORDS_EN, ACTION_WORDS_EN, SENSITIVE_AREAS_EN already imported directly


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences using common delimiters."""
    import re
    # Replace newlines with spaces, then split on . ! ?
    text = text.replace("\n", " ")
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def _check_negation_action(sentence_lower: str, lang: str = "de") -> bool:
    """Check if sentence contains negation + action word combination."""
    if lang == "en":
        has_negation = any(neg in sentence_lower for neg in NEGATION_WORDS_EN)
        has_action = any(act in sentence_lower for act in ACTION_WORDS_EN)
    else:
        has_negation = any(neg in sentence_lower for neg in NEGATION_WORDS)
        has_action = any(act in sentence_lower for act in ACTION_WORDS)
    return has_negation and has_action


def _check_sensitive_area(sentence_lower: str, lang: str = "de") -> bool:
    """Check if sentence mentions sensitive areas."""
    if lang == "en":
        return any(area in sentence_lower for area in SENSITIVE_AREAS_EN)
    else:
        return any(area in sentence_lower for area in SENSITIVE_AREAS)


def detect_guardrails_in_freetext(answers: dict, lang: str = "de") -> tuple[bool, list[str]]:
    """
    Scannt alle Freitext-Felder nach Guardrails mit intelligenter Erkennung.

    v4.0: Erweitert um 3-stufige Erkennung:
    1. Explizite Guardrail-Keywords
    2. Negation + Aktion Kombinationen
    3. Kritische Bereiche ohne Negation

    v4.1: Language-aware detection (DE/EN)

    Args:
        answers: Dict mit den Fragebogen-Antworten
        lang: Language code ("de" or "en")

    Returns:
        Tuple (guardrails_detected: bool, detected_snippets: list[str])
    """
    # Felder, die nach Guardrails durchsucht werden sollen
    freetext_fields = [
        "strategische_ziele",
        "zeitersparnis_prioritaet",
        "hauptleistung",
        "ki_projekte",
        "geschaeftsmodell_evolution",
        "vision_3_jahre",
    ]

    # Select keywords based on language
    if lang == "en":
        guardrail_keywords = GUARDRAIL_DETECTION_KEYWORDS_EN
    else:
        guardrail_keywords = GUARDRAIL_DETECTION_KEYWORDS

    detected_snippets = []

    for field in freetext_fields:
        val = answers.get(field, "")
        if not val or val == "—":
            continue

        # Split into sentences for granular analysis
        sentences = _split_into_sentences(val)

        for sentence in sentences:
            if not sentence or len(sentence) < 10:  # Skip very short fragments
                continue

            sentence_lower = sentence.lower()

            # Check 1: Explicit guardrail keywords (language-aware)
            has_explicit_keyword = any(kw in sentence_lower for kw in guardrail_keywords)

            # Check 2: Negation + Action combination (language-aware)
            has_negation_action = _check_negation_action(sentence_lower, lang)

            # Check 3: Sensitive area mention (language-aware)
            has_sensitive_area = _check_sensitive_area(sentence_lower, lang)

            # If any check passes, add to detected snippets
            if has_explicit_keyword or has_negation_action or has_sensitive_area:
                if sentence not in detected_snippets:
                    detected_snippets.append(sentence)

    return (len(detected_snippets) > 0, detected_snippets)


def build_strategic_context_block(answers: dict, lang: str = "de") -> str:
    """
    Kombiniert alle strategischen Freitext-Felder zu einem strukturierten Kontextblock.
    Wird für spätere Prompt-Anreicherung verwendet.

    v3.1: Erweitert um automatische Guardrail-Erkennung in Freitextfeldern.
    v5.0: Nutzt services/guardrails.py mit Confidence-Scoring.

    Args:
        answers: Dict mit den normalisierten Fragebogen-Antworten
        lang: Language code ("de" or "en")

    Returns:
        Formatierter String mit allen strategischen Kontextinformationen
    """
    lines = []

    if answers.get("strategische_ziele"):
        val = answers["strategische_ziele"]
        if val and val != "—":
            lines.append(f"Strategische Prioritäten:\n{val}")

    if answers.get("zeitersparnis_prioritaet"):
        val = answers["zeitersparnis_prioritaet"]
        if val and val != "—":
            lines.append(f"Zeitfresser & Prozess-Pain-Points:\n{val}")

    if answers.get("hauptleistung"):
        val = answers["hauptleistung"]
        if val and val != "—":
            lines.append(f"Wichtigste Leistung / Hauptprodukt:\n{val}")

    if answers.get("ki_projekte"):
        val = answers["ki_projekte"]
        if val and val != "—":
            lines.append(f"Laufende oder geplante KI-Projekte:\n{val}")

    if answers.get("geschaeftsmodell_evolution"):
        val = answers["geschaeftsmodell_evolution"]
        if val and val != "—":
            lines.append(f"Idee für Geschäftsmodell-Entwicklung:\n{val}")

    if answers.get("vision_3_jahre"):
        val = answers["vision_3_jahre"]
        if val and val != "—":
            lines.append(f"Vision für die nächsten 2–3 Jahre:\n{val}")

    # === Guardrails: Explizit angegeben + Auto-Detection v5 ===
    explicit_guardrails = answers.get("ki_guardrails", "")
    has_explicit = explicit_guardrails and explicit_guardrails != "—"

    # Auto-Detection using guardrails v5 with confidence scoring
    guardrails_detected, hits = detect_guardrails_v5(answers, lang)
    # Extract sentences for backwards-compatible output (top 3 by confidence)
    detected_snippets = [hit.sentence for hit in hits[:3]]

    if has_explicit and guardrails_detected:
        # Beide vorhanden: Explizite zuerst, dann Auto-Detected
        combined = f"No-Gos & Leitplanken:\n{explicit_guardrails}"
        combined += f"\n\nNo-Gos & Leitplanken (automatisch erkannt):\n"
        combined += "• " + "\n• ".join(detected_snippets)
        lines.append(combined)
        high_conf_count = sum(1 for h in hits if h.is_high_confidence)
        log.info("🛡️ Guardrails v5: Explicit + %d auto-detected (high_conf=%d)", len(hits), high_conf_count)
    elif has_explicit:
        # Nur explizite Guardrails
        lines.append(f"No-Gos & Leitplanken:\n{explicit_guardrails}")
    elif guardrails_detected:
        # Nur auto-detected
        auto_section = "No-Gos & Leitplanken (automatisch erkannt):\n"
        auto_section += "Es wurden sensible Prioritäten erkannt:\n"
        auto_section += "• " + "\n• ".join(detected_snippets)
        lines.append(auto_section)
        high_conf_count = sum(1 for h in hits if h.is_high_confidence)
        log.info("🛡️ Guardrails v5: %d auto-detected (high_conf=%d, no explicit)", len(hits), high_conf_count)

    return "\n\n".join(lines)
# =========================================================================


# === KSJ EXEC-SUMMARY OVERRIDES (auto-insert) ============================
# (Imports already at top of file)

def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default
def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default
OPENAI_MODEL_DEFAULT = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMP_DEFAULT = _env_float("OPENAI_TEMPERATURE", 0.2)
OPENAI_MAX_TOKENS_DEFAULT = _env_int("OPENAI_MAX_TOKENS", 3000)
OPENAI_TIMEOUT_SEC = _env_int("OPENAI_TIMEOUT", 120)
EXEC_SUMMARY_MODEL = os.getenv("OPENAI_MODEL_EXEC_SUMMARY", OPENAI_MODEL_DEFAULT)
EXEC_SUMMARY_TEMP = _env_float("OPENAI_TEMP_EXEC_SUMMARY", OPENAI_TEMP_DEFAULT)
EXEC_SUMMARY_MAX_TOKENS = _env_int("OPENAI_MAX_TOKENS_EXEC_SUMMARY", OPENAI_MAX_TOKENS_DEFAULT)
GAMECHANGER_MODEL = os.getenv("OPENAI_MODEL_GAMECHANGER", OPENAI_MODEL_DEFAULT)
GAMECHANGER_TEMP = _env_float("OPENAI_TEMP_GAMECHANGER", _env_float("OPENAI_TEMPERATURE_GAMECHANGER", OPENAI_TEMP_DEFAULT))
GAMECHANGER_MAX_TOKENS = _env_int("OPENAI_MAX_TOKENS_GAMECHANGER", OPENAI_MAX_TOKENS_DEFAULT)
def _llm_params_for(section_key: str) -> Dict[str, Any]:
    """
    Liefert Modell, Temperatur und Max-Tokens für einen logischen Abschnitt.

    PLATIN+ STABILIZATION:
    - Für kritische Sections (foerderpotenzial, risks, recommendations, roadmap_12m, gamechanger)
      werden max_tokens auf 4096 erhöht und optimierte Temperature/Penalties verwendet.

    Env-Overrides (optional, überschreiben PLATIN-Defaults):
    - OPENAI_MODEL_<SECTION>
    - OPENAI_TEMP_<SECTION>
    - OPENAI_MAX_TOKENS_<SECTION>

    SECTION ist der section_key in UPPERCASE, z. B.:
    - "executive_summary" -> OPENAI_MODEL_EXECUTIVE_SUMMARY
    - "quick_wins"        -> OPENAI_MODEL_QUICK_WINS
    """
    key = (section_key or "").lower()
    suffix = key.upper()

    # PLATIN+ Konfiguration prüfen (foerderpotenzial, risks, recommendations, etc.)
    platin_config = get_platin_config(key)

    # Explizite Env-Overrides pro Section (höchste Priorität)
    model_env = os.getenv(f"OPENAI_MODEL_{suffix}")
    temp_env = os.getenv(f"OPENAI_TEMP_{suffix}")
    max_tokens_env = os.getenv(f"OPENAI_MAX_TOKENS_{suffix}")

    # Modell bestimmen
    if model_env:
        model = model_env
    elif key in {"executive_summary", "exec_summary", "summary"}:
        model = EXEC_SUMMARY_MODEL
    elif key == "gamechanger":
        model = GAMECHANGER_MODEL
    else:
        model = OPENAI_MODEL_DEFAULT

    # Temperatur bestimmen (PLATIN-Config hat Vorrang vor Default)
    if temp_env is not None:
        try:
            temperature = float(temp_env)
        except ValueError:
            temperature = OPENAI_TEMP_DEFAULT
    elif platin_config:
        temperature = platin_config.get("temperature", OPENAI_TEMP_DEFAULT)
    elif key in {"executive_summary", "exec_summary", "summary"}:
        temperature = EXEC_SUMMARY_TEMP
    elif key == "gamechanger":
        temperature = GAMECHANGER_TEMP
    else:
        temperature = OPENAI_TEMP_DEFAULT

    # Max-Tokens bestimmen (PLATIN-Config hat explizite Werte für kritische Sections)
    if max_tokens_env is not None:
        try:
            max_tokens = int(max_tokens_env)
        except ValueError:
            max_tokens = OPENAI_MAX_TOKENS_DEFAULT
    elif platin_config:
        # PLATIN+ kritische Sections: Verwende konfigurierte max_tokens (4096)
        max_tokens = platin_config.get("max_tokens", 4096)
    elif key in {"executive_summary", "exec_summary", "summary"}:
        max_tokens = EXEC_SUMMARY_MAX_TOKENS
    elif key == "gamechanger":
        max_tokens = GAMECHANGER_MAX_TOKENS
    else:
        max_tokens = OPENAI_MAX_TOKENS_DEFAULT

    return {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": OPENAI_TIMEOUT_SEC,
    }

# ========================================================================

def build_extra_sections(answers: dict, scores: dict) -> dict:
    """Compute extra sections and values for the template context."""
    env_defaults = {
        "DEFAULT_STUNDENSATZ_EUR": int(os.getenv("DEFAULT_STUNDENSATZ_EUR", "60")),
        "DEFAULT_QW1_H": int(os.getenv("DEFAULT_QW1_H", "10")),
        "DEFAULT_QW2_H": int(os.getenv("DEFAULT_QW2_H", "8")),
        "FALLBACK_QW_MONTHLY_H": int(os.getenv("FALLBACK_QW_MONTHLY_H", "18")),
    }
    extra: dict = {}
    try:
        extra["BENCHMARKS_SECTION_HTML"] = build_benchmarks_section(scores)
    except Exception as exc:
        log.warning("Benchmarks section failed: %s", exc)
    try:
        extra["STARTER_STACKS_HTML"] = build_starter_stacks(answers)
    except Exception as exc:
        log.warning("Starter stacks failed: %s", exc)
    try:
        extra["RESPONSIBLE_AI_HTML"] = build_responsible_ai_section({
            "four_pillars": os.getenv("FOUR_PILLARS_PATH", "knowledge/four_pillars.html"),
            "legal_pitfalls": os.getenv("LEGAL_PITFALLS_PATH", "knowledge/legal_pitfalls.html"),
            "ten_20_70": os.getenv("TEN_20_70_PATH", "knowledge/ten_20_70.html"),
            "kmu_keypoints": os.getenv("KMU_KEYPOINTS_PATH", "knowledge/kmu_keypoints.html"),
        })
    except Exception as exc:
        log.warning("Responsible AI section failed: %s", exc)

    # === NEW: Score Context for size-relative benchmarking (Fix #6) ===
    try:
        if callable(get_score_context):
            overall_score = scores.get("overall", 0)
            size = answers.get("unternehmensgroesse", "klein")
            score_context = get_score_context(overall_score, size)
            extra["score_context"] = score_context
            extra["score_rating"] = score_context.get("score_rating", "")
            extra["size_label"] = score_context.get("size_label", "")
            extra["avg_score_for_size"] = score_context.get("avg_score_for_size", 0)
            extra["top10_score_for_size"] = score_context.get("top10_score_for_size", 0)
            log.info("✅ Score context added: %s for %s (avg=%s, top10=%s)",
                     score_context.get("score_rating"), size,
                     score_context.get("avg_score_for_size"), score_context.get("top10_score_for_size"))
    except Exception as exc:
        log.warning("Score context failed: %s", exc)

    # === NEW: Research Provenance for transparency (Fix #8) ===
    try:
        if callable(get_research_provenance):
            provenance = get_research_provenance()
            extra["research_sources"] = provenance.get("research_sources", [])
            extra["report_date"] = provenance.get("report_date", "")
            extra["RESEARCH_PROVENANCE_HTML"] = provenance.get("provenance_html", "")
            log.info("✅ Research provenance added: %s", provenance.get("report_date"))
    except Exception as exc:
        log.warning("Research provenance failed: %s", exc)

    # === NEW: Business Case Plausibility Check (Fix #3) ===
    try:
        if callable(validate_business_case_plausibility) and extra:
            warnings = validate_business_case_plausibility(extra, answers)
            if warnings:
                log.warning("[BUSINESS-CASE] Plausibility warnings:\n%s", "\n".join(warnings))
                extra["business_case_warnings"] = warnings
    except Exception as exc:
        log.warning("Business case plausibility check failed: %s", exc)

    return extra

# Logger already initialized at top of file

OPENAI_API_KEY = settings.openai.api_key or os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = settings.openai.model or os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")  # Not in new settings structure
OPENAI_TEMPERATURE = settings.openai.temperature
OPENAI_TIMEOUT = settings.openai.timeout
# Robust: Unterstützt sowohl max_completion_tokens (neu) als auch max_tokens (alt)
try:
    OPENAI_MAX_TOKENS = getattr(settings.openai, "max_completion_tokens", None)
    if OPENAI_MAX_TOKENS is None:
        OPENAI_MAX_TOKENS = getattr(settings.openai, "max_tokens", None)
    if OPENAI_MAX_TOKENS is None:
        OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "3000"))
except Exception:
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "3000"))

ENABLE_NSFW_FILTER = (os.getenv("ENABLE_NSFW_FILTER", "1") in ("1", "true", "TRUE", "yes", "YES"))
ENABLE_REALISTIC_SCORES = (os.getenv("ENABLE_REALISTIC_SCORES", "1") in ("1", "true", "TRUE", "yes", "YES"))
ENABLE_LLM_CONTENT = (os.getenv("ENABLE_LLM_CONTENT", "1") in ("1", "true", "TRUE", "yes", "YES"))
ENABLE_REPAIR_HTML = (os.getenv("ENABLE_REPAIR_HTML", "1") in ("1", "true", "TRUE", "yes", "YES"))
USE_INTERNAL_RESEARCH = (os.getenv("RESEARCH_PROVIDER", "hybrid") != "disabled")
ENABLE_AI_ACT_SECTION = (os.getenv("ENABLE_AI_ACT_SECTION", "1") in ("1", "true", "TRUE", "yes", "YES"))
USE_PROMPT_SYSTEM = (os.getenv("USE_PROMPT_SYSTEM", "1") in ("1", "true", "TRUE", "yes", "YES"))
# Initialize PromptEnhancer (einmal beim App-Start) - NEU!
if USE_PROMPT_SYSTEM:
    try:
        _prompt_enhancer = PromptEnhancer(data_dir="data")
        log.info("✅ PromptEnhancer initialized with context system")
    except Exception as e:
        log.warning("⚠️ PromptEnhancer failed to initialize: %s", e)
        _prompt_enhancer = None
else:
    _prompt_enhancer = None
    log.info("ℹ️ PromptEnhancer disabled (USE_PROMPT_SYSTEM=0)")


AI_ACT_INFO_PATH = os.getenv("AI_ACT_INFO_PATH", "EU-AI-ACT-Infos-wichtig.txt")
AI_ACT_PHASE_LABEL = os.getenv("AI_ACT_PHASE_LABEL", "2025–2027")
GLOSSAR_PATH = os.getenv("GLOSSAR_PATH", "content/glossar-de.md")
INCLUDE_COVERAGE_BOX = os.getenv("INCLUDE_COVERAGE_BOX", "0") in ("1","true","TRUE","yes","YES")

DBG_PDF = (os.getenv("DEBUG_LOG_PDF_INFO", "1") in ("1", "true", "TRUE", "yes", "YES"))
DBG_MASK_EMAILS = (os.getenv("MASK_EMAILS", "1") in ("1", "true", "TRUE", "yes", "YES"))

# Resend Configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
SMTP_FROM = os.getenv("RESEND_FROM") or os.getenv("SMTP_FROM", "bewertung@send.ki-sicherheit.jetzt")

def _send_email_via_resend(to_email: str, subject: str, html_body: str, attachments: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, Optional[str]]:
    """Send email via Resend API with optional attachments"""
    if not resend or not RESEND_API_KEY:
        return False, "Resend not configured"
    
    try:
        resend.api_key = RESEND_API_KEY
        
        # Prepare attachments for Resend
        resend_attachments = []
        if attachments:
            import base64
            for att in attachments:
                if "content" in att and "filename" in att:
                    content_bytes = att["content"] if isinstance(att["content"], bytes) else att["content"].encode("utf-8")
                    resend_attachments.append({
                        "filename": att["filename"],
                        "content": base64.b64encode(content_bytes).decode('ascii')  # Resend expects list of bytes
                    })
        
        params: Dict[str, Any] = {
            "from": SMTP_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html_body
        }

        if resend_attachments:
            params["attachments"] = resend_attachments

        response = resend.Emails.send(params)

        # Log email ID for debugging in Resend dashboard
        email_id = response.get("id") if isinstance(response, dict) else None
        if email_id:
            log.info(f"📬 Resend Email ID: {email_id} → {_mask_email(to_email)}")
        else:
            log.warning(f"⚠️ Resend response missing email ID for {_mask_email(to_email)}")

        return True, None

    except Exception as exc:
        return False, str(exc)


# -------------------- helpers --------------------
def _ellipsize(s: str, max_len: int) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max(0, max_len - 1)].rstrip() + "…"

_LABEL_MAX = int(os.getenv("LABEL_MAX_LEN", "80"))

# -------------------- NSFW filter ----------------
NSFW_KEYWORDS = {"porn","xxx","sex","nude","naked","adult","nsfw","erotic","escort","dating","porno","nackt","fick","titten","onlyfans","torrent","crack"}
NSFW_DOMAINS = {"xvideos.com","pornhub.com","xnxx.com","redtube.com","youporn.com","onlyfans.com"}

def _is_nsfw_content(url: str, title: str, description: str) -> bool:
    if not ENABLE_NSFW_FILTER:
        return False
    url_lower = (url or "").lower()
    if any(domain in url_lower for domain in NSFW_DOMAINS):
        return True
    text = f"{title} {description}".lower()
    return any(k in text for k in NSFW_KEYWORDS)

def _filter_nsfw(research_data: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_NSFW_FILTER:
        return research_data
    out: Dict[str, Any] = {"tools": [], "funding": []}
    for t in research_data.get("tools", []):
        if not _is_nsfw_content(t.get("url", ""), t.get("title", ""), t.get("description", "")):
            out["tools"].append(t)
    for f in research_data.get("funding", []):
        if not _is_nsfw_content(f.get("url", ""), f.get("title", ""), f.get("description", "")):
            out["funding"].append(f)
    return out

# -------------------- scoring --------------------
def _map_german_to_english_keys(answers: Dict[str, Any]) -> Dict[str, Any]:
    m: Dict[str, Any] = {}
    m["ai_strategy"] = (
        "yes"
        if answers.get("roadmap_vorhanden") == "ja"
        else "in_progress"
        if answers.get("roadmap_vorhanden") == "teilweise"
        or answers.get("vision_3_jahre")
        or answers.get("ki_ziele")
        else "no"
    )
    m["ai_responsible"] = (
        "yes"
        if answers.get("governance_richtlinien") in ["ja", "alle"]
        else "shared"
        if answers.get("governance_richtlinien") == "teilweise"
        else "no"
    )
    budget_map = {
        "unter_2000": "under_10k",
        "2000_10000": "under_10k",
        "10000_50000": "10k-50k",
        "50000_100000": "50k-100k",
        "ueber_100000": "over_100k",
    }
    m["budget"] = budget_map.get(answers.get("investitionsbudget", ""), "none")
    m["goals"] = (", ".join(answers.get("ki_ziele", [])) if answers.get("ki_ziele") else answers.get("strategische_ziele", ""))
    anwendungen = answers.get("anwendungsfaelle", [])
    proj = answers.get("ki_projekte", "")
    m["use_cases"] = (", ".join(anwendungen) + (". " + proj if proj else "")) if anwendungen else proj
    m["gdpr_aware"] = "yes" if (answers.get("datenschutz") is True or answers.get("datenschutzbeauftragter") == "ja") else "no"
    if answers.get("technische_massnahmen") == "alle":
        m["data_protection"] = "comprehensive"
    elif answers.get("technische_massnahmen"):
        m["data_protection"] = "basic"
    else:
        m["data_protection"] = "none"
    m["risk_assessment"] = "yes" if answers.get("folgenabschaetzung") == "ja" else "no"
    trainings = answers.get("trainings_interessen", [])
    m["security_training"] = "regular" if trainings and len(trainings) > 2 else ("occasional" if trainings else "no")
    m["trainings_list"] = ", ".join(trainings) if trainings else ""
    u = m["use_cases"]
    val_points = 8 if u and len(u) > 50 else (4 if u else 0)
    m["_value_points_from_uses"] = val_points
    roi = answers.get("vision_prioritaet", "")
    m["roi_expected"] = "high" if roi in ["marktfuehrerschaft", "wachstum"] else ("medium" if roi else "low")
    m["measurable_goals"] = "yes" if (answers.get("strategische_ziele") or answers.get("ki_ziele")) else "no"
    m["pilot_planned"] = "yes" if answers.get("pilot_bereich") else ("in_progress" if answers.get("ki_projekte") else "no")
    kompetenz_map = {"hoch": "advanced", "mittel": "intermediate", "niedrig": "basic", "keine": "none"}
    m["ai_skills"] = kompetenz_map.get(answers.get("ki_kompetenz", ""), "none")
    m["training_budget"] = "yes" if answers.get("zeitbudget") in ["ueber_10", "5_10"] else ("planned" if answers.get("zeitbudget") else "no")
    change = answers.get("change_management", "")
    m["change_management"] = "yes" if change == "hoch" else ("planned" if change in ["mittel", "niedrig"] else "no")
    innovationsprozess = answers.get("innovationsprozess", "")
    m["innovation_culture"] = "strong" if innovationsprozess in ["mitarbeitende", "alle"] else ("moderate" if innovationsprozess else "weak")
    return m

def _calculate_realistic_score(answers: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_REALISTIC_SCORES:
        return {"scores": {"governance": 0, "security": 0, "value": 0, "enablement": 0, "overall": 0}, "details": {}, "total": 0}
    m = _map_german_to_english_keys(answers)
    gov = sec = val = ena = 0
    details: Dict[str, List[str]] = {"governance": [], "security": [], "value": [], "enablement": []}
    gov += 8 if m.get("ai_strategy") in ["yes", "in_progress"] else 0
    details["governance"].append("✅ KI-Strategie" if m.get("ai_strategy") in ["yes", "in_progress"] else "❌ Keine KI-Strategie")
    gov += 7 if m.get("ai_responsible") in ["yes", "shared"] else 0
    details["governance"].append("✅ KI-Verantwortlicher" if m.get("ai_responsible") in ["yes", "shared"] else "❌ Kein KI-Verantwortlicher")
    budget = m.get("budget", "")
    if budget in ["10k-50k", "50k-100k", "over_100k"]:
        gov += 6; details["governance"].append("✅ Ausreichendes Budget")
    elif budget == "under_10k":
        gov += 3; details["governance"].append("⚠️ Niedriges Budget")
    else:
        details["governance"].append("❌ Kein Budget")
    gov += 4 if (m.get("goals") or m.get("use_cases")) else 0
    sec += 8 if m.get("gdpr_aware") == "yes" else 0
    sec += 7 if m.get("data_protection") in ["comprehensive", "basic"] else 0
    sec += 6 if m.get("risk_assessment") == "yes" else 0
    sec += 4 if m.get("security_training") in ["regular", "occasional"] else 0
    val += m.get("_value_points_from_uses", 0)
    roi = m.get("roi_expected", "")
    val += 7 if roi in ["high", "medium"] else (3 if roi == "low" else 0)
    val += 6 if m.get("measurable_goals") == "yes" else 0
    val += 4 if m.get("pilot_planned") in ["yes", "in_progress"] else 0
    skills = m.get("ai_skills", "")
    ena += 8 if skills in ["advanced", "intermediate"] else (4 if skills == "basic" else 0)
    ena += 7 if m.get("training_budget") in ["yes", "planned"] else 0
    ena += 6 if m.get("change_management") == "yes" else 0
    culture = m.get("innovation_culture", "")
    ena += 4 if culture in ["strong", "moderate"] else 0
    scores = {
        "governance": min(gov, 25) * 4,
        "security": min(sec, 25) * 4,
        "value": min(val, 25) * 4,
        "enablement": min(ena, 25) * 4,
        "overall": round((min(gov, 25) + min(sec, 25) + min(val, 25) + min(ena, 25)) * 4 / 4),
    }
    log.info("📊 REALISTIC SCORES v5.3.0-PLATIN+++: Gov=%s Sec=%s Val=%s Ena=%s Overall=%s",
             scores["governance"], scores["security"], scores["value"], scores["enablement"], scores["overall"])
    return {"scores": scores, "details": details, "total": scores["overall"]}

# -------------------- OpenAI client ----------------
def _call_openai(
    prompt: str,
    system_prompt: str = "Du bist ein KI-Berater.",
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
    section: Optional[str] = None,  # PLATIN+ Logging: Section-Key für Diagnostik
) -> Optional[str]:
    if not OPENAI_API_KEY:
        log.error("❌ OPENAI_API_KEY not set")
        return None

    if temperature is None:
        temperature = OPENAI_TEMPERATURE
    if max_tokens is None:
        max_tokens = OPENAI_MAX_TOKENS
    if model is None:
        model = OPENAI_MODEL  # globales Default-Modell

    api_base = (OPENAI_API_BASE or "https://api.openai.com").rstrip("/")
    url = f"{api_base}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if "openai.azure.com" in api_base:
        headers["api-key"] = OPENAI_API_KEY
    else:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    try:
        # Sanitize headers for logging (remove API keys)
        safe_headers = {
            k: "***" if k.lower() in ["authorization", "api-key"] else v
            for k, v in headers.items()
        }
        log.debug("OpenAI request headers: %s", safe_headers)

        # Payload base: model, messages, temperature
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": float(temperature),
        }
        
        # GPT-5.x benötigt max_completion_tokens statt max_tokens
        if model.startswith("gpt-5"):
            payload["max_completion_tokens"] = int(max_tokens)
        else:
            payload["max_tokens"] = int(max_tokens)

        # NOTE: stop parameter removed for OpenAI models (gpt-4o-mini, gpt-4.1, etc.)
        # as it's no longer supported. Stop sequences are still used for Anthropic models
        # via the anthropic_client.py module.

        r = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=OPENAI_TIMEOUT,
        )
        r.raise_for_status()

        # Validate response structure and log finish_reason for diagnostics
        try:
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            finish_reason = data["choices"][0].get("finish_reason", "unknown")
            completion_tokens = data.get("usage", {}).get("completion_tokens", 0)
            section_label = section or "unknown"

            # PLATIN+ Diagnostik: Einheitliches Log-Format für Railway
            if finish_reason == "length":
                log.warning(
                    "⚠️ LLM section=%s finished with reason=length (hit token limit %d) – risk of truncation",
                    section_label,
                    max_tokens or OPENAI_MAX_TOKENS,
                )
            else:
                log.info(
                    "✅ LLM section=%s finished with reason=%s (tokens=%d, max=%d)",
                    section_label,
                    finish_reason,
                    completion_tokens,
                    max_tokens or OPENAI_MAX_TOKENS,
                )

            return str(content)
        except (KeyError, IndexError, TypeError) as e:
            log.error(
                "Unexpected OpenAI response structure: %s. Response: %s",
                e,
                str(data)[:500],
            )
            return None

    except requests.exceptions.RequestException as exc:
        error_msg = f"❌ OpenAI request error: {str(exc)[:200]}"
        # Bei HTTP-Fehlern: Response-Body loggen (gekürzt)
        if hasattr(exc, 'response') and exc.response is not None:
            try:
                response_text = exc.response.text[:500]
                error_msg += f" | Response: {response_text}"
            except Exception:
                pass
        log.error(error_msg)
        return None
    except Exception as exc:
        log.error("❌ OpenAI unexpected error: %s", str(exc)[:200])
        return None


def _call_llm_for_section(
    section_key: str,
    prompt: str,
    system_prompt: str = "Du bist ein KI-Berater.",
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
) -> Optional[str]:
    """
    Zentrale Stelle, um je Abschnitt zu entscheiden,
    ob OpenAI oder Anthropic benutzt wird.
    
    Args:
        section_key: Der Schlüssel des Abschnitts (z.B. "executive_summary", "risks", etc.)
        prompt: Der Prompt-Text
        system_prompt: Der System-Prompt
        temperature: Temperatur-Parameter
        max_tokens: Maximum Tokens
        model: Modell-Name
        
    Returns:
        Der generierte Text oder None bei Fehler
    """
    if should_use_anthropic(section_key):
        return call_anthropic(
            prompt=prompt,
            section=section_key,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )

    # Fallback: OpenAI wie bisher (mit section für besseres Logging)
    return _call_openai(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model,
        section=section_key,
    )


# -------------------- HTML repair ----------------
def _clean_html(s: str) -> str:
    if not s: return s
    return s.replace("```html","").replace("```","").strip()

def _needs_repair(s: str) -> bool:
    if not s: return True
    sl = s.lower()
    return ("<" not in sl) or not any(t in sl for t in ("<p","<ul","<table","<div","<h4","<ol"))

def _repair_html(section: str, s: str) -> str:
    if not ENABLE_REPAIR_HTML: return _clean_html(s)
    fixed = _call_llm_for_section(
        section_key="html_repair",
        prompt=f"""Konvertiere folgenden Text in **valides HTML** ohne Markdown‑Fences.
Erlaube nur: <p>, <ul>, <ol>, <li>, <table>, <thead>, <tbody>, <tr>, <th>, <td>, <div>, <h4>, <em>, <strong>, <br>.
Abschnitt: {section}. Antworte ausschließlich mit HTML.
---
{s}
""",
        system_prompt="Du bist ein strenger HTML‑Sanitizer. Gib nur validen HTML‑Code aus.",
        temperature=0.0, max_tokens=1200,
    )
    return _clean_html(fixed or s)


# -------------------- N4.6: Zero-Leak Policy ----------------
# Phrases that indicate assistant language "leaking" into report content
LEAK_PHRASES = [
    # German assistant language
    "wie kann ich ihnen helfen",
    "kann ich ihnen behilflich",
    "haben sie fragen",
    "wenn sie möchten",
    "kontaktieren sie uns",
    "gerne erkläre ich",
    "ich kann ihnen",
    "bei bedarf",
    "falls gewünscht",
    "klicken sie hier",
    "wählen sie",
    "bei weiteren fragen",
    "stehe ich zur verfügung",
    "zögern sie nicht",
    "melden sie sich",
    # English assistant language
    "how can i help",
    "if you have questions",
    "feel free to",
    "please let me know",
    "i can assist",
    "don't hesitate",
    # Meta language
    "im folgenden",
    "dieser abschnitt",
    "hier einfügen",
    "platzhalter",
]

# Sections eligible for 2-pass expand (per Batch 3 spec)
EXPAND_ELIGIBLE_SECTIONS = [
    "foerderpotenzial",
    "risks",
    "recommendations",
    "roadmap_12m",
    "gamechanger",
    "unternehmensprofil_markt",
]


def _detect_leak_phrases(content: str) -> List[str]:
    """
    N4.6 Zero-Leak Policy: Detect assistant language leaks in content.

    Args:
        content: HTML content to check

    Returns:
        List of detected leak phrases (empty if none found)
    """
    if not content:
        return []

    content_lower = content.lower()
    detected = []

    for phrase in LEAK_PHRASES:
        if phrase in content_lower:
            detected.append(phrase)

    return detected


def _regenerate_without_leaks(
    section_name: str,
    prompt_text: str,
    llm: Dict[str, Any],
    max_retries: int = 1,
) -> str:
    """
    N4.6 Zero-Leak Policy: Regenerate content with strict anti-leak directive.

    Args:
        section_name: Section being generated
        prompt_text: Original prompt text
        llm: LLM parameters dict
        max_retries: Max regeneration attempts

    Returns:
        Regenerated content or empty string on failure
    """
    strict_directive = """

STRIKT VERBOTEN - ASSISTENTEN-SPRACHE:
Du schreibst einen FINALEN REPORT, KEIN Gespräch.
Verwende NIEMALS:
- Fragen an den Leser
- Angebote zur Hilfe
- "Wenn Sie möchten...", "Bei Bedarf...", "Falls gewünscht..."
- "Ich kann...", "Gerne erkläre ich..."
- Interaktive Aufforderungen
"""
    enhanced_prompt = prompt_text + strict_directive

    log.info(
        "[N4.6] Regenerating %s with strict zero-leak directive...",
        section_name
    )

    result = _call_llm_for_section(
        section_key=section_name,
        prompt=enhanced_prompt,
        system_prompt="Du bist ein Senior-KI-Berater. Antworte nur mit validem HTML. KEINE Assistenten-Sprache.",
        temperature=max(0.0, llm["temperature"] - 0.1),  # Reduce temperature for stricter output
        max_tokens=llm["max_tokens"],
        model=llm["model"],
    ) or ""

    result = _clean_html(result)
    if _needs_repair(result):
        result = _repair_html(section_name, result)

    return result


# -------------------- Quick‑Wins sum ----------------
_QW_RE = re.compile(r"(?:Ersparnis\s*[:=]\s*)(\d+(?:[.,]\d{1,2})?)\s*(?:h|std\.?|stunden?)\s*(?:[/\s]*(?:pro|/)?\s*Monat)", re.IGNORECASE)
def _sum_hours_from_quick_wins(html_text: str) -> int:
    if not html_text: return 0
    text = re.sub(r"<[^>]+>", " ", html_text)
    total = 0.0; seen = set()
    for m in _QW_RE.finditer(text):
        span = m.span()
        if span in seen: continue
        seen.add(span)
        try:
            val = float(m.group(1).replace(",", "."))
            if 0 < val <= 200: total += val
        except ValueError: continue
    return int(round(total))

# -------------------- Benchmarks ----------------
def _read_json_first(*paths: str) -> Optional[dict]:
    for p in paths:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    return dict(data) if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
            log.debug("Failed to read JSON from %s: %s", p, str(e)[:100])
            continue
    return None
def _load_branch_benchmarks() -> Dict[str, Any]:
    path1 = os.getenv("BENCHMARKS_PATH", "data/benchmarks.json")
    path2 = "data/benchmarks.json"
    data = _read_json_first(path1, path2)
    return data or {}

def _estimate_size_benchmark(size_label: str) -> Dict[str, int]:
    """Estimate benchmark scores based on company size.
    
    Actual size categories from questionnaire:
    - solo: 1 (Solo-Selbstständig/Freiberuflich)
    - klein: 2-10 (Kleines Team)
    - kmu: 11-100 (KMU)
    """
    sl = (size_label or "").lower()
    
    # 1 Person (Solo)
    if "solo" in sl or "freiberuf" in sl or "selbstständig" in sl:
        return {"avg": 15, "top25": 30}
    
    # 2-10 Personen (Kleines Team)
    if "2" in sl or "klein" in sl or "team" in sl:
        return {"avg": 25, "top25": 45}
    
    # 11-100 Personen (KMU)
    if "11" in sl or "kmu" in sl or "100" in sl:
        return {"avg": 40, "top25": 60}
    
    # Fallback (should rarely happen)
    return {"avg": 30, "top25": 50}

def _build_benchmark_html(briefing: Dict[str, Any], lang: str = "de") -> str:
    """Build benchmark HTML table - TEIL 3.1.4: Language-aware."""
    benchmarks = _load_branch_benchmarks()
    branche = briefing.get("BRANCHE_LABEL") or briefing.get("branche", "")
    size_label = briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse", "")
    row_html = []
    if branche:
        b = (branche or "").lower()
        bench = benchmarks.get(b, {})
        if bench and isinstance(bench, dict):
            avg = bench.get("avg", "—")
            top25 = bench.get("top25", "—")
            source = bench.get("source", "Industry Study 2024" if lang == "en" else "Branchenstudie 2024")
            row_html.append(f"<tr><td><strong>{ui('industry', lang)}</strong>: {html.escape(branche)}</td><td>Ø {avg}% · Top‑25% {top25}%</td><td>{html.escape(source)}</td></tr>")
        else:
            row_html.append(f"<tr><td><strong>{ui('industry', lang)}</strong>: {html.escape(branche or '—')}</td><td>—</td><td>—</td></tr>")
    if size_label:
        sb = _estimate_size_benchmark(size_label)
        row_html.append(
            f"<tr><td><strong>{ui('company_size', lang)}</strong>: {html.escape(size_label)}</td>"
            f"<td>Ø {sb['avg']}% · Top‑25% {sb['top25']}%</td>"
            f"<td>{ui('estimate', lang)}</td></tr>"
        )
    table = (
        "<table class='table'>"
        f"<thead><tr><th>{ui('comparison', lang)}</th><th>{ui('value', lang)}</th><th>{ui('source', lang)}</th></tr></thead>"
        f"<tbody>{''.join(row_html)}</tbody>"
        "</table>"
        f"<p class='small muted'>{ui('size_hint_note', lang)}</p>"
    )
    return table

# -------------------- Quellenkasten & Links ----------------
_LINK_RE = re.compile(r"""<a\s+[^>]*href=['"]([^'"]+)['"][^>]*>(.*?)</a>""", re.IGNORECASE | re.DOTALL)

def _sanitize_url(url: str) -> Optional[str]:
    """
    Sanitize and validate URL to prevent XSS and SSRF attacks.

    Returns sanitized URL or None if invalid.
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()

    # Limit URL length
    if len(url) > 2000:
        log.warning("URL too long (>2000 chars), rejecting")
        return None

    try:
        parsed = urlparse(url)

        # Only allow http and https schemes
        if parsed.scheme not in ['http', 'https']:
            log.warning("Invalid URL scheme: %s", parsed.scheme[:20])
            return None

        # Block localhost and internal IPs (SSRF protection)
        hostname = parsed.hostname
        if hostname:
            hostname_lower = hostname.lower()
            # Block localhost variants
            if hostname_lower in ['localhost', '127.0.0.1', '0.0.0.0', '::1']:
                log.warning("Blocked localhost URL")
                return None
            # Block AWS metadata endpoint
            if hostname_lower.startswith('169.254.'):
                log.warning("Blocked metadata endpoint URL")
                return None
            # Block private IP ranges (simplified check)
            if hostname_lower.startswith('10.') or hostname_lower.startswith('192.168.') or hostname_lower.startswith('172.'):
                log.warning("Blocked private IP URL")
                return None

        # HTML escape the URL to prevent XSS
        return html.escape(url, quote=True)

    except Exception as e:
        log.warning("URL validation failed: %s", str(e)[:100])
        return None

def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "")

def _table_rows(html_block: str) -> List[str]:
    return re.findall(r"<tr[^>]*>(.*?)</tr>", html_block or "", flags=re.IGNORECASE | re.DOTALL)

def _tds(row_html: str) -> List[str]:
    return re.findall(r"<td[^>]*>(.*?)</td>", row_html or "", flags=re.IGNORECASE | re.DOTALL)

def _extract_links_from_tools_table(table_html: str) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    for row in _table_rows(table_html):
        cells = _tds(row)
        if not cells: continue
        title = html.unescape(_strip_tags(cells[0])).strip()
        m = _LINK_RE.search(row)
        if m:
            href = m.group(1).strip()
            label = _ellipsize(title or urlparse(href).netloc, _LABEL_MAX)
            if href: items.append((href, label))
    return items

def _extract_links_from_generic_html(block: str) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    for href, label in _LINK_RE.findall(block or ""):
        t = _strip_tags(label).strip()
        if not t or t.lower() in {"quelle","details","link","mehr","info"}:
            t = urlparse(href).netloc or href
        items.append((href.strip(), _ellipsize(html.unescape(t), _LABEL_MAX)))
    return items

def _unique_by_href(pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen = set(); out: List[Tuple[str, str]] = []
    for href, label in pairs:
        if href in seen: continue
        seen.add(href); out.append((href, label))
    return out

_OFFICIAL = {"bmwk.de","bund.de","bmi.bund.de","bmbf.de","bmwi.de","foerderdatenbank.de","europa.eu","ec.europa.eu","commission.europa.eu","berlin.de","service.berlin.de","bsi.bund.de","bafin.de"}
_MEDIA = {"heise.de","golem.de","computerwoche.de","handelsblatt.com","t3n.de","gruenderszene.de","welt.de","faz.net","zeit.de"}
_VENDOR = {"microsoft.com","azure.microsoft.com","openai.com","google.com","cloud.google.com","aws.amazon.com","meta.com","huggingface.co"}

def _domain_category(dom: str) -> int:
    d = dom.lower()
    if any(d == x or d.endswith("." + x) for x in _OFFICIAL): return 0
    if any(d == x or d.endswith("." + x) for x in _MEDIA): return 1
    if any(d == x or d.endswith("." + x) for x in _VENDOR): return 2
    return 1

def _sort_pairs(pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    def key(x: Tuple[str, str]):
        dom = urlparse(x[0]).netloc
        return (_domain_category(dom), x[1].lower())
    return sorted(pairs, key=key)

def _rewrite_table_links_with_labels(table_html: str) -> str:
    if not table_html: return table_html
    out_rows = []
    for row in _table_rows(table_html):
        cells = _tds(row)
        if not cells:
            out_rows.append(row); continue
        title = _ellipsize(html.unescape(_strip_tags(cells[0])).strip(), _LABEL_MAX)
        def repl(m):
            href = m.group(1)
            safe_href = _sanitize_url(href)
            if not safe_href:
                return html.escape(title)  # No link if URL is invalid
            return f"<a href='{safe_href}'>{html.escape(title)}</a>"
        row2 = re.sub(_LINK_RE, repl, row, count=0)
        out_rows.append(row2)
    body = "".join(f"<tr>{r}</tr>" for r in out_rows)
    if "<tbody" in table_html.lower():
        return re.sub(r"(<tbody[^>]*>).*(</tbody>)", r"\1"+body+r"\2", table_html, flags=re.IGNORECASE | re.DOTALL)
    return re.sub(r"<table[^>]*>.*</table>", lambda _: "<table>"+body+"</table>", table_html, flags=re.IGNORECASE | re.DOTALL)

def _build_sources_box_html(sections: Dict[str, str], last_updated: str) -> str:
    pairs: List[Tuple[str, str]] = []
    if sections.get("TOOLS_HTML"):
        pairs += _extract_links_from_tools_table(sections["TOOLS_HTML"])
    if sections.get("FOERDERPROGRAMME_HTML"):
        pairs += _extract_links_from_tools_table(sections["FOERDERPROGRAMME_HTML"])
    for key in ("EXECUTIVE_SUMMARY_HTML","AI_ACT_SUMMARY_HTML","BUSINESS_CASE_HTML","ROI_HTML"):
        if sections.get(key):
            pairs += _extract_links_from_generic_html(sections[key])
    pairs = _unique_by_href(pairs)
    if not pairs:
        return f"<div class='callout'><strong>Aktualisierung:</strong> Stand der Quellen: {html.escape(last_updated)}.</div>"
    pairs = _sort_pairs(pairs)
    lis = []
    for href, label in pairs:
        safe_href = _sanitize_url(href)
        if not safe_href:
            continue  # Skip invalid URLs
        try:
            dom = urlparse(href).netloc.lower()
        except Exception:
            dom = "unknown"
        label_clean = html.escape(label)
        lis.append(f"<li><a href='{safe_href}'>{label_clean}</a> <span class='small muted'>({dom})</span></li>")
    ul = "<ul>" + "".join(lis) + "</ul>"
    return ("<div class='fb-section'>"
            "<div class='fb-head'><span class='fb-step'>Quellen</span><h3 class='fb-title'>Quellen & Aktualisierung</h3></div>"
            f"<p class='small muted'>Stand der externen Quellen: {html.escape(last_updated)}.</p>{ul}"
            "</div>")

# -------------------- Kreativ-Tools ----------------
def _read_file_with_fallback(path: str) -> Optional[str]:
    """Read file content with fallback to /mnt/data directory.

    Unified file reader that replaces _read_text and _try_read.
    """
    if not path:
        return None

    # Try primary path
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except (IOError, UnicodeDecodeError) as e:
            log.debug("Failed to read file %s: %s", path, str(e)[:100])
            return None

    # Fallback to /mnt/data
    alt = os.path.join("/mnt/data", os.path.basename(path))
    if os.path.exists(alt):
        try:
            with open(alt, "r", encoding="utf-8") as f:
                return f.read()
        except (IOError, UnicodeDecodeError) as e:
            log.debug("Failed to read file %s: %s", alt, str(e)[:100])
            return None

    return None

# Backward compatibility aliases
_read_text = _read_file_with_fallback
_try_read = _read_file_with_fallback

def _parse_kreativ_tools(raw: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for line in (raw or "").splitlines():
        ln = line.strip()
        if not ln or ln.startswith("#"): continue
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) >= 2 and parts[1].startswith(("http://","https://")):
            label = parts[0]; href = parts[1]
            if len(parts) >= 3 and parts[2]: label = f"{label} – {parts[2]}"
            out.append((label, href))
            continue
        m = re.match(r"^(.*?)[\-\u2013\u2014]\s*(https?://\S+)$", ln)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
            continue
        m = re.match(r"^\[(.+?)\]\((https?://[^)]+)\)$", ln)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
            continue
        m = re.search(r"(https?://\S+)", ln)
        if m:
            href = m.group(1).strip(); label = urlparse(href).netloc
            out.append((label, href)); continue
        out.append((ln, ""))
    return out

def _build_kreativ_tools_html(path: str, report_date: str) -> str:
    raw = _read_text(path) or ""
    pairs = _parse_kreativ_tools(raw)
    if not pairs: return ""
    items = []
    for label, href in pairs:
        label_html = html.escape(_ellipsize(label, _LABEL_MAX))
        if href:
            safe_href = _sanitize_url(href)
            if safe_href:
                items.append(f"<li><a href='{safe_href}'>{label_html}</a></li>")
            else:
                items.append(f"<li>{label_html}</li>")  # No link if URL invalid
        else:
            items.append(f"<li>{label_html}</li>")
    ul = "<ul>" + "".join(items) + "</ul>"
    return ("<div class='fb-section'>"
            "<div class='fb-head'><span class='fb-step'>Kreativ</span><h3 class='fb-title'>Kreativ‑Tools (kuratierte Liste)</h3></div>"
            f"{ul}<p class='small muted'>Stand: {html.escape(report_date)} · Quelle: {html.escape(os.path.basename(path))}</p>"
            "</div>")

# -------------------- Werkbank ----------------
def _build_werkbank_html() -> str:
    def ul(items: List[str]) -> str:
        return "<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in items) + "</ul>"
    blocks = []
    blocks.append("<h3>RAG‑Stack (Open‑Source & lokal)</h3>" + ul([
        "LLM: Mistral 7B / Llama‑3.x (lokal oder gehostet)",
        "Embeddings: E5 / Instructor",
        "Vektordatenbank: FAISS / Chroma",
        "Orchestrierung: LangChain / LiteLLM",
        "Guardrails & Moderation: Pydantic‑Validatoren / Rebuff",
        "Beobachtbarkeit: OpenTelemetry Hooks (einfach)"
    ]))
    blocks.append("<h3>Azure‑only Stack (Enterprise/DSGVO)</h3>" + ul([
        "Azure OpenAI (Chat Completions / Assistants)",
        "Azure Cognitive Search (RAG)",
        "Functions + Blob Storage (Pipelines & Daten)",
        "Content Safety + Key Vault (Sicherheit)",
        "Azure Monitor/App Insights (Monitoring)"
    ]))
    blocks.append("<h3>Schneller Assistenz‑Stack (SaaS)</h3>" + ul([
        "LLM: OpenAI GPT‑4o",
        "Automatisierung: Make/Zapier",
        "Wissensablage: Notion/Confluence",
        "Kommunikation: Slack/MS Teams Bot",
        "Formulare: Tally/Typeform für Intake"
    ]))
    note = "<p class='small muted'>Hinweis: Stacks sind exemplarisch und anpassbar; Auswahl hängt von Datenschutz, Budget und IT‑Landschaft ab.</p>"
    return "<div class='fb-section'>" + "".join(blocks) + note + "</div>"

# -------------------- Score Bars (CSS-only) ----------------
def _build_score_bars_html(scores: Dict[str, Any]) -> str:
    def row(label: str, key: str) -> str:
        val = 0
        try:
            val = max(0, min(100, int(float(scores.get(key, 0)))))
        except (ValueError, TypeError) as e:
            log.debug("Failed to parse score for %s: %s", key, str(e)[:50])
            val = 0
        return (
            f"<tr><td style='padding:6px 8px;width:160px'>{html.escape(label)}</td>"
            f"<td style='padding:6px 8px;width:100%'>"
            f"<div style='height:8px;border-radius:6px;background:#eef2ff;overflow:hidden'>"
            f"<i style='display:block;height:100%;width:{val}%;background:linear-gradient(90deg,#3b82f6,#2563eb)'></i>"
            f"</div>"
            f"<div style='font-size:10px;color:#475569'>{val}/100</div>"
            f"</td></tr>"
        )
    rows = "".join([
        row("Governance", "governance"),
        row("Sicherheit", "security"),
        row("Wertschöpfung", "value"),
        row("Befähigung", "enablement"),
        row("Gesamt", "overall"),
    ])
    return f"<table style='width:100%;border-collapse:collapse'>{rows}</table>"

# -------------------- Werkbank (dynamisch nach Branche/Größe) ----------------
def _build_werkbank_html_dynamic(answers: Dict[str, Any]) -> str:
    path = os.getenv("STARTER_STACKS_PATH", "").strip()
    branche = (answers.get("BRANCHE_LABEL") or answers.get("branche") or "").strip().lower()
    size = (answers.get("UNTERNEHMENSGROESSE_LABEL") or answers.get("unternehmensgroesse") or "").strip().lower()
    # normalize size to keys used in starter_stacks.json
    if "solo" in size or "freiberuf" in size: size = "solo"
    elif "2" in size or "kleines" in size or "team" in size: size = "team"
    elif "11" in size or "kmu" in size: size = "kmu"

    def _safe_ul(items):
        return "<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in (items or [])) + "</ul>"

    if path and os.path.exists(path):
        try:
            import json as _json
            data = _json.load(open(path, "r", encoding="utf-8"))
            common = (data.get("common") or {})
            bran = (data.get(branche) or {})
            blocks = []
            if size in (common or {}):
                blocks.append("<h3>Common</h3>" + _safe_ul(common[size]))
            if size in (bran or {}):
                title = (branche.capitalize() if branche else "Branche")
                blocks.append(f"<h3>{html.escape(title)}</h3>" + _safe_ul(bran[size]))
            if blocks:
                note = "<p class='small muted'>Stacks aus Starter‑Registry · anpassbar je Datenschutz/Budget/IT‑Landschaft.</p>"
                return "<div class='fb-section'>" + "".join(blocks) + note + "</div>"
        except Exception:
            pass
    return _build_werkbank_html()

# -------------------- Feedback-Box ----------------
def _build_feedback_box(feedback_url: str, report_date: str) -> str:
    if not feedback_url:
        return ""
    safe_link = _sanitize_url(feedback_url.strip())
    if not safe_link:
        log.warning("Invalid feedback URL, skipping feedback box")
        return ""
    return (
        "<div class='fb-section'>"
        "<div class='fb-head'><span class='fb-step'>Feedback</span><h3 class='fb-title'>Ihre Meinung zählt</h3></div>"
        "<p>Was war hilfreich, was fehlt? Teilen Sie uns Ihr Feedback mit – es dauert weniger als 2 Minuten.</p>"
        f"<p><a href='{safe_link}' target='_blank' rel='noopener'>Feedback geben</a> "
        f"<span class='small muted'>· Stand: {html.escape(report_date)}</span></p>"
        "</div>"
    )

# -------------------- 🎯 NEW: Estimate hourly rate from revenue ----------------
def _estimate_hourly_rate_from_revenue(briefing: Dict[str, Any]) -> int:
    """
    Estimate a realistic hourly rate based on company size and revenue.
    This is needed because the questionnaire doesn't have a 'stundensatz_eur' field,
    but we need it for ROI calculations.
    
    Returns: Estimated hourly rate in EUR
    """
    # First check if there's an explicit hourly rate in the briefing
    explicit_rate = briefing.get("stundensatz_eur")
    if explicit_rate:
        try:
            return int(explicit_rate)
        except (ValueError, TypeError):
            pass
    
    # Get company size and revenue
    size = briefing.get("unternehmensgroesse", "").lower()
    revenue_label = briefing.get("jahresumsatz", "").lower()
    
    # Solo/Freelancer baseline
    if "solo" in size or "freiberuf" in size or "einzelunt" in size:
        return 55
    
    # Estimate based on revenue bands
    # Small companies (under 100k)
    if "unter" in revenue_label and "100" in revenue_label:
        return 50
    
    # 100k-500k range
    if any(x in revenue_label for x in ["100", "250", "500"]) and "mio" not in revenue_label:
        return 65
    
    # 500k-1M range
    if "500" in revenue_label or ("1" in revenue_label and "mio" in revenue_label):
        return 75
    
    # 1M-5M range
    if any(x in revenue_label for x in ["2", "3", "4", "5"]) and "mio" in revenue_label:
        return 85
    
    # 5M+ range
    if any(x in revenue_label for x in ["10", "20", "50"]) and "mio" in revenue_label:
        return 95
    
    # Default fallback
    try:
        return int(os.getenv("DEFAULT_STUNDENSATZ_EUR", "60"))
    except (ValueError, TypeError):
        return 60

# -------------------- 🎯 NEW: Build prompt variables ----------------
def _build_prompt_vars(briefing: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build complete variable dict for prompt interpolation.
    Extended to 60+ variables based on comprehensive analysis of:
    - Questionnaire fields (formbuilder_de_SINGLE_FULL_15_33_03.js)
    - Prompt templates (prompts/de/*.md)
    - PDF template (pdf_template.html)
    """
    now = datetime.now()
    today = now.strftime("%d.%m.%Y")
    date_30d = (now + timedelta(days=30)).strftime("%d.%m.%Y")
    report_year = now.strftime("%Y")
    
    # ===== BLOCK 1: Time & Date =====
    # Used in next_actions_de.md for dynamic deadlines
    
    # --- Patch03: derive label fields from registry ---
    try:
        # Use briefing parameter as source
        _src = briefing
        if isinstance(_src, dict):
            # Single-choice fields
            for _k, _label_key in [('branche','BRANCHE_LABEL'),
                                   ('unternehmensgroesse','UNTERNEHMENSGROESSE_LABEL'),
                                   ('bundesland','BUNDESLAND_LABEL'),
                                   ('jahresumsatz','JAHRESUMSATZ_LABEL'),
                                   ('it_infrastruktur','IT_INFRASTRUKTUR_LABEL'),
                                   ('prozesse_papierlos','PROZESSE_PAPIERLOS_LABEL'),
                                   ('automatisierungsgrad','AUTOMATISIERUNGSGRAD_LABEL'),
                                   ('interne_ki_kompetenzen','INTERNE_KI_KOMPETENZEN_LABEL'),
                                   ('roadmap_vorhanden','ROADMAP_VORHANDEN_LABEL'),
                                   ('governance_richtlinien','GOVERNANCE_RICHTLINIEN_LABEL'),
                                   ('change_management','CHANGE_MANAGEMENT_LABEL'),
                                   ('interesse_foerderung','INTERESSE_FOERDERUNG_LABEL'),
                                   ('marktposition','MARKTPOSITION_LABEL'),
                                   ('benchmark_wettbewerb','BENCHMARK_WETTBEWERB_LABEL'),
                                   ('selbststaendig','SELBSTSTAENDIG_LABEL'),
                                   ('zeitersparnis_prioritaet','ZEITERSPARNIS_PRIORITAET_LABEL')]:
                _val = _src.get(_k)
                if _val is not None and not _src.get(_label_key):
                    _src[_label_key] = _label_for(_k, _val)

            # Multi-choice fields → comma-joined labels
            for _k, _label_key in [('zielgruppen','ZIELGRUPPEN_LABELS'),
                                   ('ki_ziele','KI_ZIELE_LABELS'),
                                   ('ki_hemmnisse','KI_HEMMNISSE_LABELS'),
                                   ('anwendungsfaelle','ANWENDUNGSFAELLE_LABELS'),
                                   ('datenquellen','DATENQUELLEN_LABELS'),
                                   ('vorhandene_tools','VORHANDENE_TOOLS_LABELS'),
                                   ('regulierte_branche','REGULIERTE_BRANCHE_LABELS'),
                                   ('trainings_interessen','TRAININGS_INTERESSEN_LABELS')]:
                _vals = _src.get(_k)
                if _vals is not None and not _src.get(_label_key):
                    _src[_label_key] = _labels_for_list(_k, _vals)

    except Exception as _e:
        pass
    base_vars: Dict[str, Any] = {
        "TODAY": today,
        "heute_iso": today,
        "DATE_30D": date_30d,
        "report_date": today,
        "report_year": report_year,
    }
    
    # ===== BLOCK 2: Company Basics =====
    # Core company information needed across all prompts
    # Both uppercase and lowercase variants for compatibility

    # Map unternehmensgroesse to COMPANY_SIZE for roadmap/gamechanger prompts
    # Actual sizes from questionnaire: solo (1), klein (2-10), kmu (11-100)
    size_raw = briefing.get("unternehmensgroesse", "solo")
    size_map = {
        "solo": "solo",   # 1 (Solo-Selbstständig/Freiberuflich)
        "klein": "team",  # 2-10 (Kleines Team)
        "kmu": "kmu",     # 11-100 (KMU)
    }
    company_size = size_map.get(size_raw, "team")  # Fallback to "team" if unknown
    
    # Derive size_label (human-readable label for size)
    size_label = briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse", "")

    base_vars.update({
        "BRANCHE": briefing.get("branche", ""),
        "branche": briefing.get("branche", ""),
        "BRANCHE_LABEL": briefing.get("BRANCHE_LABEL") or briefing.get("branche", ""),
        "UNTERNEHMENSGROESSE": briefing.get("unternehmensgroesse", ""),
        "unternehmensgroesse": briefing.get("unternehmensgroesse", ""),
        "UNTERNEHMENSGROESSE_LABEL": size_label,
        "size_label": size_label,  # Consistent key for size-sensitive prompts
        "COMPANY_SIZE": company_size,  # For roadmap_90d.md and gamechanger.md
        "BUNDESLAND_LABEL": briefing.get("BUNDESLAND_LABEL") or briefing.get("bundesland", ""),
        "bundesland": briefing.get("bundesland", ""),
        "HAUPTLEISTUNG": briefing.get("hauptleistung", ""),
        "JAHRESUMSATZ_LABEL": briefing.get("JAHRESUMSATZ_LABEL", briefing.get("jahresumsatz", "")),
        "INVESTITIONSBUDGET": briefing.get("investitionsbudget", ""),  # For gamechanger.md
    })
    
    # ===== BLOCK 3: Strategy & Vision =====
    # Strategic direction and goals
    hemmnisse_raw = briefing.get("ki_hemmnisse", [])  # Fixed: was "hemmnisse", should be "ki_hemmnisse"
    if not hemmnisse_raw:
        hemmnisse_raw = briefing.get("hemmnisse", [])  # Fallback for legacy data
    
    base_vars.update({
        "VISION_PRIORITAET": briefing.get("vision_3_jahre", ""),
        "PROJEKTZIEL": ", ".join(briefing.get("ki_ziele", [])) if briefing.get("ki_ziele") else briefing.get("strategische_ziele", ""),
        "KI_KNOWHOW": briefing.get("ki_kompetenz", ""),
        "KI_HEMMNISSE": ", ".join(hemmnisse_raw) if isinstance(hemmnisse_raw, list) else hemmnisse_raw,
    })
    
    # ===== BLOCK 4: Resources =====
    # Budget and time availability
    base_vars.update({
        "INVESTITIONSBUDGET": briefing.get("investitionsbudget", ""),
        "ZEITBUDGET": briefing.get("zeitbudget", ""),
    })
    
    # ===== BLOCK 5: Data & Quality (NEW!) =====
    # Critical for data_readiness_de.md prompt
    base_vars.update({
        "DATENQUELLEN": briefing.get("datenquellen", "Nicht spezifiziert"),
        "DATENQUALITAET": briefing.get("datenqualitaet", "Nicht bewertet"),
        "LOESCHREGELN": briefing.get("loeschregeln", "Nicht dokumentiert"),
        "PROZESSE_PAPIERLOS": briefing.get("prozesse_papierlos", "Nicht angegeben"),
    })
    
    # ===== BLOCK 6: Training & Culture (NEW!) =====
    # Critical for org_change_de.md prompt
    base_vars.update({
        "TRAININGS_INTERESSEN": briefing.get("trainings_interessen", "Nicht spezifiziert"),
        "INNOVATIONSKULTUR": briefing.get("innovationskultur", "Nicht bewertet"),
    })
    
    # ===== BLOCK 7: Quick Wins & ROI (EXTENDED!) =====
    # Calculate hourly rate using our smart estimation function
    stundensatz_eur = _estimate_hourly_rate_from_revenue(briefing)
    
    # Quick Win hours from environment or defaults
    qw1_h = int(os.getenv("DEFAULT_QW1_H", "20"))
    qw2_h = int(os.getenv("DEFAULT_QW2_H", "15"))
    
    # Calculate monthly and yearly savings
    monatsersparnis_stunden = qw1_h + qw2_h
    monatsersparnis_eur = monatsersparnis_stunden * stundensatz_eur
    jahresersparnis_stunden = monatsersparnis_stunden * 12
    jahresersparnis_eur = monatsersparnis_eur * 12
    
    base_vars.update({
        "qw1_monat_stunden": qw1_h,
        "qw2_monat_stunden": qw2_h,
        "stundensatz_eur": stundensatz_eur,
        "monatsersparnis_stunden": monatsersparnis_stunden,
        "monatsersparnis_eur": monatsersparnis_eur,
        "jahresersparnis_stunden": jahresersparnis_stunden,
        "jahresersparnis_eur": jahresersparnis_eur,
    })
    
    # ===== BLOCK 8: Business Case (NEW!) =====
    # Investment estimates for business_case_de.md
    # Conservative estimates based on company size
    try:
        umsatz_label = briefing.get("jahresumsatz", "").lower()
        if "mio" in umsatz_label:
            capex_realistisch = 15000
            opex_realistisch = 3000
        elif any(x in umsatz_label for x in ["500", "1"]):
            capex_realistisch = 8000
            opex_realistisch = 2000
        else:
            capex_realistisch = 5000
            opex_realistisch = 1500
    except Exception:
        capex_realistisch = 5000
        opex_realistisch = 1500
    
    base_vars.update({
        "capex_realistisch_eur": capex_realistisch,
        "capex_konservativ_eur": int(capex_realistisch * 1.3),
        "opex_realistisch_eur": opex_realistisch,
        "opex_konservativ_eur": int(opex_realistisch * 1.2),
    })
    
    # ===== BLOCK 9: Scores (CRITICAL FIX!) =====
    # Both English AND German variants needed!
    # English: Used in code (score_security, score_value)
    # German: Used in prompts (score_sicherheit, score_nutzen)
    base_vars.update({
        # English variants (code)
        "score_governance": scores.get("governance", 0),
        "score_security": scores.get("security", 0),
        "score_value": scores.get("value", 0),
        "score_enablement": scores.get("enablement", 0),
        "score_overall": scores.get("overall", 0),
        
        # German variants (prompts)
        "score_sicherheit": scores.get("security", 0),
        "score_nutzen": scores.get("value", 0),
        "score_befaehigung": scores.get("enablement", 0),
        "score_gesamt": scores.get("overall", 0),
        
        # Special alias for PDF template
        "score_wertschoepfung": scores.get("value", 0),  # Alias for score_value in template
    })
    
    # ===== BLOCK 10: JSON Dumps =====
    # Complex data structures for advanced prompts
    base_vars.update({
        "ALL_ANSWERS_JSON": json.dumps(briefing, ensure_ascii=False, indent=2)[:2000],
        "BRIEFING_JSON": json.dumps(briefing, ensure_ascii=False, indent=2)[:2000],
        "SCORING_JSON": json.dumps(scores, ensure_ascii=False, indent=2),
        "BUSINESS_JSON": json.dumps({
            "stundensatz": stundensatz_eur,
            "monatsersparnis_h": monatsersparnis_stunden,
            "jahresersparnis_eur": jahresersparnis_eur,
            "capex": capex_realistisch,
            "opex": opex_realistisch
        }, ensure_ascii=False, indent=2),
    })
    
    # Log size context for verification
    if not base_vars.get("size_label"):
        log.warning("⚠️ size_label not recognized, using fallback. unternehmensgroesse=%s", 
                   briefing.get("unternehmensgroesse", "N/A"))
    else:
        log.debug("📊 Size context: size_label=%s, COMPANY_SIZE=%s", 
                 base_vars.get("size_label"), base_vars.get("COMPANY_SIZE"))
    
    return base_vars
# -------------------- 🎯 NEW: Better fallbacks when GPT fails ----------------
def _get_fallback_content(section_key: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    """🎯 UPDATED v5.0.0-PLATIN+: Size-aware fallback content mit PLATIN+ Wortlängen

    PLATIN+ Mindestlängen (WÖRTER, nicht Zeichen!):
    - foerderpotenzial: 900 Wörter
    - risks: 800 Wörter
    - recommendations: 800 Wörter
    - roadmap_12m: 900 Wörter

    Änderungen v5.0.0:
    - NEU: foerderpotenzial Fallback mit 900+ Wörtern
    - NEU: risks Fallback mit 800+ Wörtern
    - NEU: recommendations Fallback mit 800+ Wörtern
    - roadmap_12m: Erweitert auf 900+ Wörter
    """
    # TEIL 3.1.1: Get lang first for language-aware fallbacks
    briefing_lang = briefing.get("lang", "de") if isinstance(briefing, dict) else "de"

    # Language-aware fallbacks
    default_company = "Your Company" if briefing_lang == "en" else "Ihr Unternehmen"
    branche = briefing.get("BRANCHE_LABEL") or briefing.get("branche", default_company)
    size_label = briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse", "")
    hauptleistung = briefing.get("hauptleistung", briefing.get("HAUPTLEISTUNG", ""))

    # SPRINT G2.4: Generate short labels for redundancy reduction
    # PLATIN+++ v5.4: Use briefing's actual lang, not hardcoded "de"
    from services.prompt_enhancer import generate_short_labels
    short_labels = generate_short_labels(briefing, lang=briefing_lang)
    branch_core_label = short_labels.get("BRANCH_CORE_LABEL", branche)
    offering_label = short_labels.get("OFFERING_LABEL", "")

    # 🎯 Size-Erkennung (solo/team/kmu) wie im Briefing spezifiziert
    size_raw = (briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse") or "").lower()
    
    if "solo" in size_raw or "freiberuf" in size_raw or "1" in size_raw:
        size_group = "solo"
    elif "2" in size_raw or "team" in size_raw or "kleines" in size_raw:
        size_group = "team"
    else:
        size_group = "kmu"

    # Business Case Variablen - TEIL 3.1.1: Language-aware
    default_bundesland = "your region" if briefing_lang == "en" else "Ihrem Bundesland"
    bundesland = briefing.get("BUNDESLAND_LABEL") or briefing.get("bundesland", default_bundesland)
    # BC-Werte mit sinnvollen Defaults (werden von calc_business_case vorher gesetzt)
    capex = briefing.get("CAPEX_REALISTISCH_EUR") or 5000
    opex = briefing.get("OPEX_REALISTISCH_EUR") or 150
    einsparung = briefing.get("EINSPARUNG_MONAT_EUR") or 500
    # SPRINT G2.5: Format payback and ROI with 1 decimal place to avoid floating point issues
    payback_raw = briefing.get("PAYBACK_MONTHS") or 10
    payback = f"{float(payback_raw):.1f}" if isinstance(payback_raw, (int, float)) else payback_raw
    roi_raw = briefing.get("ROI_12M") or 60
    roi_12m = f"{float(roi_raw):.0f}" if isinstance(roi_raw, (int, float)) else roi_raw

    # ════════════════════════════════════════════════════════════════════════════
    # 🎯 PLATIN+ FALLBACK: FOERDERPOTENZIAL (900+ Wörter)
    # ════════════════════════════════════════════════════════════════════════════
    if section_key == "foerderpotenzial":
        # TEIL 3.1.4: EN fallback for funding potential
        if briefing_lang == "en":
            return f"""<section class="section funding-potential">
  <h2>Funding Potential for Your AI Project</h2>
  <p>
    Companies in the <strong>{branche}</strong> industry with size <strong>{size_label}</strong> often have good prerequisites
    for funding for projects in <strong>{hauptleistung or "AI-supported process optimization"}</strong>. The combination of
    digitization focus, AI support, and clear process improvement corresponds to the priorities of many programs at national and EU level.
  </p>
  <h3>1. Business Case Assessment Without Funding</h3>
  <p>
    The current business case shows one-time investments of approximately <strong>€{capex}</strong> and ongoing costs of
    around <strong>€{opex} per month</strong>. The expected monthly relief is approximately <strong>€{einsparung}</strong>,
    leading to an amortization period of about <strong>{payback} months</strong> and a realistic ROI of around <strong>{roi_12m}%</strong>
    in the first year. These metrics form a solid basis for evaluating funding eligibility.
  </p>
  <h3>2. How Funding Can Improve the Business Case</h3>
  <p>
    Public funding programs typically cover 30-70% of eligible investment costs, depending on company size and project scope.
    This can significantly reduce the capital commitment and accelerate the payback period. For your project, a funding rate of
    40-50% could reduce the effective initial investment by €{int(capex * 0.45)}, improving ROI to well over 100% in the first year.
  </p>
  <h3>3. EU Funding Opportunities</h3>
  <ul>
    <li><strong>Horizon Europe:</strong> EU research and innovation program with SME instruments for innovative AI projects.</li>
    <li><strong>Digital Europe Programme:</strong> Supports AI adoption and digital transformation in businesses.</li>
    <li><strong>European Innovation Council:</strong> Funding for breakthrough innovations and scale-ups.</li>
    <li><strong>National Recovery Plans:</strong> Many countries allocate funds to digitization and AI adoption as part of EU recovery funding.</li>
  </ul>
  <h3>4. Application Strategy</h3>
  <p>
    For optimal funding success, we recommend: (1) Document your AI use case with clear metrics and expected impact.
    (2) Prepare a project plan with milestones and deliverables. (3) Calculate the investment breakdown including personnel,
    software, and consulting costs. (4) Research funding programs matching your industry and company size.
  </p>
  <p class="small muted">
    {ui('note', 'en')}: Funding availability varies by region and program cycle. This overview serves as orientation –
    specific funding commitments require individual assessment. Consult with funding advisors for personalized guidance.
  </p>
</section>"""
        # Size-aware Förderhinweise
        if size_group == "solo":
            foerder_focus = "Beratungsförderung, Gründerprogramme und niedrigschwellige Digitalisierungszuschüsse"
            budget_hinweis = "Im Solo-Kontext sind Förderprogramme besonders attraktiv, da sie den Eigenanteil bei Investitionen deutlich reduzieren können"
        elif size_group == "team":
            foerder_focus = "go-digital, KMU-innovativ und regionale Digitalisierungsprogramme"
            budget_hinweis = "Für kleine Teams bieten Förderprogramme die Möglichkeit, ambitioniertere Projekte umzusetzen ohne die Liquidität zu gefährden"
        else:
            foerder_focus = "Digital Jetzt, ZIM und strukturelle KMU-Förderprogramme"
            budget_hinweis = "KMU können von umfangreichen Förderprogrammen profitieren, die sowohl Investitions- als auch Beratungskosten abdecken"

        return f"""<section class="section funding-potential">
  <h2>Förderpotenzial für Ihr KI-Projekt</h2>

  <p>
    Unternehmen in der Branche <strong>{branche}</strong> im Bundesland <strong>{bundesland}</strong> und der Größe
    <strong>{size_label}</strong> verfügen für Vorhaben im Bereich <strong>{hauptleistung or "KI-gestützte Prozessoptimierung"}</strong>
    häufig über gute Voraussetzungen für eine Förderung. Die Kombination aus Digitalisierungsfokus, KI-Unterstützung und
    klarer Prozessverbesserung entspricht den Schwerpunkten vieler Programme auf Landes- und Bundesebene. Gerade in Zeiten
    des digitalen Wandels setzen Bund, Länder und EU verstärkt auf die Förderung von KI-Projekten, die nachweislich zur
    Effizienzsteigerung und Wettbewerbsfähigkeit beitragen.
  </p>

  <h3>1. Einordnung des Business Case ohne Förderung</h3>
  <p>
    Der aktuelle Business Case zeigt einmalige Investitionen von etwa <strong>{capex}&nbsp;€</strong> sowie laufende Kosten von
    rund <strong>{opex}&nbsp;€ pro Monat</strong>. Die erwartete monatliche Entlastung liegt bei ungefähr
    <strong>{einsparung}&nbsp;€</strong>, was zu einer Amortisationsdauer von etwa <strong>{payback} Monaten</strong> und
    einem realistischen ROI von rund <strong>{roi_12m}&nbsp;%</strong> im ersten Jahr führt. Diese Kennzahlen bilden eine
    solide Grundlage für die Bewertung der Förderwürdigkeit durch öffentliche Stellen.
  </p>
  <p>
    Diese Ausgangslage ist für viele Förderstellen attraktiv: Das Projekt ist betriebswirtschaftlich plausibel, der Nutzen
    klar erkennbar und der Eigenbeitrag grundsätzlich tragfähig. Fördermittel können diese Situation zusätzlich verbessern,
    indem sie einen Teil der Investitionsbelastung abfedern. {budget_hinweis}. Die Kombination aus nachvollziehbarem
    Business Case und klarem Digitalisierungsfokus macht Ihr Vorhaben zu einem starken Kandidaten für öffentliche Förderung.
    Die Investition von {capex}&nbsp;€ amortisiert sich bei einer monatlichen Einsparung von {einsparung}&nbsp;€ nach etwa
    {payback} Monaten. Der ROI von {roi_12m}&nbsp;% zeigt, dass sich das Projekt auch ohne externe Unterstützung wirtschaftlich
    rechnet – mit Förderung wird die Rentabilität noch deutlich attraktiver. Fördergeber bewerten positiv, wenn Unternehmen
    einen substanziellen Eigenanteil einbringen und das Projekt auch ohne Förderung wirtschaftlich tragfähig erscheint.
  </p>

  <h3>2. Wie Fördermittel den Business Case verbessern können</h3>
  <p>
    Viele Programme in {bundesland} und auf Bundesebene unterstützen KI- und Digitalisierungsinitiativen, indem sie einen
    Teil der förderfähigen Investitionskosten bezuschussen. Je nach Programm, Unternehmensgröße und Projektschwerpunkt
    bewegen sich die Zuschussquoten typischerweise im Bereich von etwa <strong>30–50&nbsp;%</strong> der anerkannten Kosten.
    Für ein Investitionsvolumen von {capex}&nbsp;€ könnte das eine Entlastung von mehreren tausend Euro bedeuten.
  </p>
  <ul>
    <li><strong>Kürzere Amortisationsdauer:</strong> Durch eine Beteiligung an den Investitionskosten sinkt der Eigenanteil;
      die Amortisation kann sich von {payback} Monaten auf deutlich weniger verkürzen, ohne dass der erwartete Nutzen
      verändert wird. Bei einer angenommenen Förderquote von 40 Prozent reduziert sich der Eigenanteil erheblich.</li>
    <li><strong>Höherer effektiver ROI:</strong> Wenn ein Teil der Investitionen über Zuschüsse abgedeckt wird, steigt der
      Effektiv-Ertrag je eingesetztem Euro – der aktuelle ROI von {roi_12m}&nbsp;% kann sich bei 40% Förderung auf über
      das Doppelte erhöhen. Dies macht das Projekt noch attraktiver für interne Budgetentscheidungen.</li>
    <li><strong>Reduziertes finanzielles Risiko:</strong> Für <strong>{size_label}</strong> kann ein Zuschuss den Schritt
      in ein ambitionierteres Projekt erleichtern, ohne die Liquidität unnötig zu belasten. Die laufenden Kosten von
      {opex}&nbsp;€/Monat bleiben dabei tragbar und werden durch die monatliche Einsparung überkompensiert.</li>
    <li><strong>Mehr Spielraum für Qualität und Schulung:</strong> Einsparungen durch Förderung können genutzt werden,
      um zusätzliche Maßnahmen für Qualität, Sicherheit oder Qualifizierung vorzusehen. Dies erhöht die Nachhaltigkeit
      des Projekts und verbessert die langfristige Wirkung.</li>
    <li><strong>Bessere Planungssicherheit:</strong> Mit bewilligter Förderung lässt sich das Projektbudget verlässlicher
      planen und das Risiko bei unerwarteten Mehrkosten besser abfedern. Dies ist besonders relevant für KI-Projekte,
      bei denen Aufwände in der Pilotphase schwer vorherzusagen sind.</li>
  </ul>

  <h3>3. Passende Förderschwerpunkte für Ihr Vorhaben</h3>
  <p>
    Basierend auf der Branche <strong>{branche}</strong>, dem Schwerpunkt <strong>{hauptleistung or "KI-gestützte Prozessoptimierung"}</strong>
    und der Unternehmensgröße <strong>{size_label}</strong> kommen folgende Förderkategorien in Frage. Der Fokus liegt
    dabei auf {foerder_focus}.
  </p>
  <ul>
    <li><strong>Digitalisierungsförderung:</strong> Programme für KI-gestützte Prozessoptimierung, Automatisierung und
      digitale Werkzeuge sind besonders relevant für Ihr Vorhaben. Diese Programme fördern typischerweise sowohl
      Hardware- und Softwareinvestitionen als auch externe Beratungsleistungen und Schulungen.</li>
    <li><strong>Innovationsförderung:</strong> Zuschüsse für neuartige KI-Anwendungen, Pilotprojekte und Technologie-
      entwicklung, abgestimmt auf die Branche {branche}. Besonders interessant, wenn Ihr Projekt innovative Elemente
      enthält, die über Standardanwendungen hinausgehen.</li>
    <li><strong>Qualifizierungsförderung:</strong> Mittel für Schulungen, Weiterbildungen und den Aufbau von KI-Kompetenzen
      sind wichtig für die nachhaltige Nutzung. Viele Programme fördern explizit den Kompetenzaufbau als Teil von
      Digitalisierungsprojekten.</li>
    <li><strong>Beratungsförderung:</strong> Unterstützung für externe Expertise bei der KI-Strategieentwicklung und
      Umsetzung kann den Projekterfolg erheblich steigern. Programme wie go-digital oder regionale Beratungsförderung
      decken oft einen Großteil der Beratungskosten ab.</li>
    <li><strong>Nachhaltigkeits- und Klimaförderung:</strong> KI-Projekte, die zur Ressourceneffizienz, Energieeinsparung
      oder Reduzierung des ökologischen Fußabdrucks beitragen, können zusätzlich von spezialisierten Förderprogrammen
      profitieren. Diese Kombination aus Digitalisierung und Nachhaltigkeit wird von vielen Fördergebern besonders
      positiv bewertet und kann höhere Förderquoten ermöglichen.</li>
  </ul>
  <p>
    Die Kombination verschiedener Förderschwerpunkte kann besonders vorteilhaft sein. Prüfen Sie, ob Ihr Vorhaben
    mehrere der genannten Kategorien abdeckt, da dies die Antragserfolgschancen erhöhen kann. Fördergeber sehen gerne
    Projekte, die sowohl wirtschaftlichen Nutzen als auch gesellschaftlichen Mehrwert – etwa durch Digitalkompetenzaufbau
    oder nachhaltige Geschäftsmodelle – nachweisen können.
  </p>

  <h3>4. Nächste Schritte für die Förderprüfung</h3>
  <ol>
    <li><strong>Programmauswahl:</strong> Wählen Sie 1–2 Programme aus, die zu <strong>{branche}</strong>,
      <strong>{size_label}</strong> und <strong>{hauptleistung or "Ihrem Vorhaben"}</strong> passen. Prüfen Sie dabei
      sowohl Landes- als auch Bundesprogramme sowie mögliche EU-Förderungen.</li>
    <li><strong>Projektbeschreibung:</strong> Erstellen Sie eine kompakte Projektbeschreibung mit Zielen, Maßnahmen,
      Zeitplan, erwarteter Nutzen und groben Kosten mit Bezug auf die berechneten {capex}&nbsp;€. Eine klare
      Beschreibung der Innovationskomponente stärkt den Antrag.</li>
    <li><strong>Kumulierungsprüfung:</strong> Prüfen Sie, ob Programme aus {bundesland} mit Bundes- oder EU-Programmen
      kombiniert werden dürfen. Bei geschickter Kombination lassen sich höhere Gesamtförderquoten erreichen.</li>
    <li><strong>Beratung einholen:</strong> Halten Sie optional Rücksprache mit Förderberatungen, Kammern oder
      Finanzierungspartnern. Viele Beratungsstellen bieten kostenlose Erstgespräche zur Fördermittelprüfung an.</li>
    <li><strong>Zeitplanung:</strong> Förderanträge benötigen typischerweise 4–8 Wochen Vorlauf – berücksichtigen Sie
      dies bei der Projektplanung. Beachten Sie auch eventuelle Antragsfristen und Stichtage.</li>
    <li><strong>Dokumentation vorbereiten:</strong> Sammeln Sie vorab wichtige Unterlagen wie Handelsregisterauszug,
      aktuelle Jahresabschlüsse und eine De-minimis-Erklärung. Eine vollständige Dokumentation beschleunigt die
      Antragsbearbeitung erheblich und erhöht die Erfolgsaussichten.</li>
  </ol>

  <p class="small muted">
    Hinweis: Förderquoten, Fristen und Anforderungen können sich ändern. Vor Antragstellung sollten die offiziellen
    Richtlinien und Konditionen der jeweiligen Programme im Detail geprüft werden. Die genannten Zahlen basieren auf
    dem Business Case und dienen der Orientierung – konkrete Förderzusagen erfordern eine individuelle Prüfung.
  </p>
</section>"""

    # ════════════════════════════════════════════════════════════════════════════
    # 🎯 PLATIN+ FALLBACK: RISKS (800+ Wörter)
    # ════════════════════════════════════════════════════════════════════════════
    if section_key == "risks":
        score_gov = scores.get("governance", 50)
        score_sec = scores.get("sicherheit", 50)

        # NOTE: English fallback removed (Content Quality Pack v1)
        # English reports now use prompts/en/risks.md exclusively
        # This prevents any potential language leakage in German reports

        if size_group == "solo":
            org_risk = "Als Solo-Selbstständige:r konzentriert sich Know-how und Verantwortung auf eine Person"
            org_measure = "Dokumentation zentraler Workflows, Checklisten und bewusste Verankerung von KI-Routinen"
        elif size_group == "team":
            org_risk = "In kleinen Teams ist oft unklar, wer KI-Vorhaben priorisiert und wer für Qualität verantwortlich ist"
            org_measure = "Klare Rollenverteilung (KI-Owner), gemeinsame Standards und regelmäßige Team-Abstimmungen"
        else:
            org_risk = "In größeren Strukturen können unklare Verantwortlichkeiten und fehlende Governance zu Insellösungen führen"
            org_measure = "Governance-Framework, definierte Prozesse und bereichsübergreifende Koordination"

        # Content Quality Pack v1.1: Use ui() for localized heading
        risks_heading = ui("risks", briefing_lang)
        return f"""<section class="section risks">
  <h2>{risks_heading}</h2>

  <p>
    Der Einsatz von KI im Bereich <strong>{hauptleistung or "Ihrem Kerngeschäft"}</strong> in der Branche
    <strong>{branche}</strong> bietet erhebliche Chancen, bringt jedoch je nach Unternehmensgröße
    <strong>{size_label}</strong> unterschiedliche Risikoprofile mit sich. Der aktuelle Governance-Score von
    <strong>{score_gov}/100</strong> und der Sicherheits-Score von <strong>{score_sec}/100</strong> zeigen,
    wie weit Strukturen für Steuerung, Dokumentation und Schutzmechanismen bereits entwickelt sind.
    Die folgenden Abschnitte bündeln die wichtigsten Risikofelder und skizzieren konkrete Gegenmaßnahmen.
  </p>

  <h3>1. Strategische und organisatorische Risiken</h3>
  <ul>
    <li>
      <strong>Unklare Zielbilder und Prioritäten für KI.</strong>
      Ohne klar definierte Ziele für {hauptleistung or "Ihr Kerngeschäft"} besteht das Risiko, dass KI-Experimente
      versanden, Insellösungen entstehen oder wichtige Chancen ungenutzt bleiben. Die Gefahr ist besonders groß,
      wenn verschiedene Initiativen parallel laufen ohne gemeinsame Ausrichtung.
      <em>Gegenmaßnahme:</em> Ein knappes Zielbild mit 2–3 priorisierten Anwendungsfällen, ein einfacher
      Umsetzungsplan sowie regelmäßige Überprüfung, ob Maßnahmen zum übergeordneten Geschäftsmodell passen.
    </li>
    <li>
      <strong>Abhängigkeit von einzelnen Personen (Single-Point-of-Failure).</strong>
      {org_risk}. Fällt diese aus oder ist dauerhaft überlastet, kommen Experimente und Umsetzung ins Stocken.
      <em>Gegenmaßnahme:</em> {org_measure}. Wichtig ist die Dokumentation von Wissen, damit es nicht verloren geht.
    </li>
    <li>
      <strong>Fehlende Rollen- und Verantwortlichkeitsklarheit.</strong>
      In wachsenden Setups ist oft unklar, wer KI-Vorhaben priorisiert, wer für Qualität verantwortlich ist
      und wer Tools auswählt. Dies führt zu Verzögerungen und Doppelarbeit.
      <em>Gegenmaßnahme:</em> Eine klar benannte Rolle für KI-Verantwortung, ein schlanker Entscheidungsprozess
      für Tool-Einführung und transparente Kommunikation von Zuständigkeiten.
    </li>
    <li>
      <strong>Überlastung durch zusätzliche Aufgaben.</strong>
      Wenn KI-Einführung „on top" zum Tagesgeschäft läuft, werden neue Workflows nicht dauerhaft etabliert.
      Die initiale Lernkurve kann frustrieren und zum Abbruch führen.
      <em>Gegenmaßnahme:</em> Kleine, gut planbare Piloten mit klar begrenztem Umfang sowie bewusste
      Entlastung an anderer Stelle, damit Zeit für Experimente und Lernphasen entsteht.
    </li>
  </ul>

  <h3>2. Daten-, Sicherheits- und Compliance-Risiken</h3>
  <ul>
    <li>
      <strong>Unzureichende Kontrolle über ein- und ausgehende Daten.</strong>
      Wenn nicht geregelt ist, welche Informationen in KI-Systeme eingegeben werden dürfen, können vertrauliche
      Kundendaten, interne Dokumente oder sensible Inhalte unkontrolliert verarbeitet werden.
      <em>Gegenmaßnahme:</em> Klare Richtlinien für Datennutzung, ein kurzer Leitfaden für alle Beteiligten
      sowie technische Schutzmechanismen wie Zugriffsbeschränkungen oder getrennte Arbeitsbereiche.
    </li>
    <li>
      <strong>Lücken in Informationssicherheit und Zugriffsschutz.</strong>
      Der Sicherheits-Score von {score_sec}/100 deutet darauf hin, dass bei Passwörtern, Zugriffsrechten
      oder Backup-Konzepten noch Verbesserungspotenzial besteht.
      <em>Gegenmaßnahme:</em> Ein kompaktes Sicherheitskonzept, regelmäßige Passwort- und Rechte-Reviews
      sowie eine klare Dokumentation der eingesetzten Cloud- und KI-Dienste.
    </li>
    <li>
      <strong>Unklare Verantwortlichkeit für rechtliche Anforderungen.</strong>
      Ohne definierte Zuständigkeit besteht das Risiko, dass Vorgaben zu Datenschutz, Urheberrecht oder
      branchenspezifischer Regulierung nur punktuell beachtet werden.
      <em>Gegenmaßnahme:</em> Eine benannte Stelle, die Mindestanforderungen bündelt, praxisnahe Leitlinien
      formuliert und bei Unsicherheiten externe fachliche Beratung einholt.
    </li>
    <li>
      <strong>Fehlende Transparenz gegenüber Kund:innen und Partnern.</strong>
      Wenn unklar bleibt, an welchen Stellen KI Beiträge leistet, kann dies zu Vertrauensverlust führen.
      Der EU AI Act verlangt zudem Transparenzhinweise bei bestimmten KI-Anwendungen.
      <em>Gegenmaßnahme:</em> Kurze, verständliche Hinweise zur Nutzung von KI sowie nachvollziehbare
      Dokumentation im Hintergrund.
    </li>
  </ul>

  <h3>3. Qualitäts-, Transparenz- und Akzeptanzrisiken</h3>
  <ul>
    <li>
      <strong>Inkonsistente Ergebnisse und Qualitätsstreuung.</strong>
      Werden Prompts, Vorlagen und Workflows nicht dokumentiert, hängen Qualität und Stil stark von der
      jeweiligen Person ab. Dies erschwert reproduzierbare Ergebnisse und professionelle Standards.
      <em>Gegenmaßnahme:</em> Einheitliche Templates, kurze Leitfäden und regelmäßige Reviews von Beispielausgaben.
    </li>
    <li>
      <strong>Übervertrauen in KI-Ergebnisse (Halluzinationen).</strong>
      Wenn Texte, Analysen oder Bewertungen ungeprüft übernommen werden, können Fehler oder Halluzinationen
      direkt in Kundendokumente und Entscheidungen einfließen. Dies kann zu Reputationsschäden führen.
      <em>Gegenmaßnahme:</em> Klare Regeln für manuelle Prüfung, Vier-Augen-Prinzip bei kritischen Inhalten
      sowie einfache Checklisten für Qualitätskontrolle.
    </li>
    <li>
      <strong>Akzeptanzprobleme im Alltag.</strong>
      In Teams entsteht Widerstand, wenn der Nutzen von KI nicht nachvollziehbar ist oder Workflows als
      zu komplex empfunden werden. Skepsis kann die Einführung blockieren.
      <em>Gegenmaßnahme:</em> Verständliche Kommunikation der Ziele, kleine Pilotprojekte mit sichtbarem
      Nutzen und aktives Einholen von Feedback, um Routinen anzupassen.
    </li>
    <li>
      <strong>Unklare Nachvollziehbarkeit von Entscheidungen.</strong>
      Wenn nicht dokumentiert ist, welche Rolle KI in der Vorbereitung von Angeboten, Reports oder
      Entscheidungen spielt, wird es im Streitfall schwierig, Entscheidungswege zu rekonstruieren.
      <em>Gegenmaßnahme:</em> Eine kurze interne Dokumentation zu „Wo unterstützt KI?" senkt dieses Risiko.
    </li>
  </ul>

  <h3>4. Abhängigkeiten, Betriebs- und Lieferantenrisiken</h3>
  <ul>
    <li>
      <strong>Starke Abhängigkeit von einzelnen Tools oder Plattformen.</strong>
      Wenn zentrale Workflows ausschließlich auf einem Dienst oder Modell basieren, führen Preisänderungen,
      Ausfälle oder geänderte Nutzungsbedingungen schnell zu Unterbrechungen.
      <em>Gegenmaßnahme:</em> Einfache Fallback-Szenarien, Exportmöglichkeiten für Daten sowie Beobachtung von Alternativen.
    </li>
    <li>
      <strong>Unklare Regelungen mit Dienstleistern.</strong>
      Werden Auftragsverhältnisse, Datenverarbeitung oder Service-Level nicht explizit vereinbart, können
      Lücken in Haftung und Verfügbarkeit entstehen.
      <em>Gegenmaßnahme:</em> Klare Verträge, vereinbarte Reaktionszeiten und transparente Angaben zur Datenhaltung.
    </li>
    <li>
      <strong>Fehlende Notfall- und Wiederanlaufplanung.</strong>
      Wenn nicht vorab geklärt ist, wie bei Systemausfällen, Datenverlust oder Fehlkonfigurationen
      reagiert wird, verzögert sich der Wiederanlauf erheblich.
      <em>Gegenmaßnahme:</em> Einfache Notfallpläne, regelmäßige Backups sowie definierte Kontaktwege für kritische Vorfälle.
    </li>
    <li>
      <strong>Überkomplexe Tool-Landschaft.</strong>
      Werden zu viele spezialisierte KI-Tools parallel eingeführt, steigt der Aufwand für Pflege,
      Schulung und Koordination exponentiell.
      <em>Gegenmaßnahme:</em> Konsolidierung auf wenige Kernlösungen und eine bewusst schlanke Tool-Strategie.
    </li>
  </ul>

  <h3>5. Risiko-Matrix – Überblick über zentrale Risiken</h3>
  <p>
    Die folgende Übersicht zeigt die wichtigsten Risikofelder nach Eintrittswahrscheinlichkeit und
    Auswirkungsstärke, um die Priorisierung von Gegenmaßnahmen zu erleichtern.
  </p>
  <table class="table">
    <thead>
      <tr>
        <th>Risikobereich</th>
        <th>Typische Auswirkung</th>
        <th>Eintrittswahrscheinlichkeit</th>
        <th>Auswirkungsstärke</th>
        <th>Empfohlene Schwerpunkt-Maßnahmen</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Strategie & Organisation</td>
        <td>Verzettelung, ausbleibende Wirkung</td>
        <td>mittel</td>
        <td>hoch</td>
        <td>Klares Zielbild, priorisierte Use Cases, benannte Verantwortung</td>
      </tr>
      <tr>
        <td>Daten & Sicherheit</td>
        <td>Datenschutz-Verstöße, Vertrauensverlust</td>
        <td>mittel bis hoch</td>
        <td>hoch</td>
        <td>Leitlinie für Datennutzung, Zugriffs- und Passwortkonzept</td>
      </tr>
      <tr>
        <td>Qualität & Akzeptanz</td>
        <td>Uneinheitliche Ergebnisse, Misstrauen</td>
        <td>mittel</td>
        <td>mittel bis hoch</td>
        <td>Standards für Templates, Review-Loops, Kommunikation</td>
      </tr>
      <tr>
        <td>Abhängigkeiten & Betrieb</td>
        <td>Unterbrechungen, Mehrkosten, Lock-in</td>
        <td>niedrig bis mittel</td>
        <td>mittel</td>
        <td>Fallback-Szenarien, Tool-Konsolidierung</td>
      </tr>
      <tr>
        <td>KI-spezifisch: Halluzinationen</td>
        <td>Fehlerhafte Informationen, Reputationsschaden</td>
        <td>mittel bis hoch</td>
        <td>hoch</td>
        <td>Vier-Augen-Prinzip, Faktenprüfung</td>
      </tr>
    </tbody>
  </table>

  <p class="small muted">
    Diese Risikoanalyse zeigt die wichtigsten Handlungsfelder für KI in <strong>{hauptleistung or "Ihrem Kerngeschäft"}</strong>
    in einem Unternehmen der Größe <strong>{size_label}</strong>. Im nächsten Schritt sollten die Risiken nach
    Eintrittswahrscheinlichkeit und Auswirkung priorisiert und in eine konkrete Maßnahmenplanung überführt werden.
  </p>
</section>"""

    # ════════════════════════════════════════════════════════════════════════════
    # 🎯 PLATIN+ FALLBACK: RECOMMENDATIONS (800+ Wörter)
    # ════════════════════════════════════════════════════════════════════════════
    if section_key == "recommendations":
        # TEIL 3.1.4: EN fallback for recommendations
        if briefing_lang == "en":
            return f"""<section class="section recommendations">
  <h2>{ui('recommendations_title', 'en')}</h2>
  <p>
    For a company in the <strong>{branche}</strong> industry with size <strong>{size_label}</strong>,
    there are several immediately actionable levers to effectively deploy AI in the process <strong>{hauptleistung or "your core business"}</strong>.
    The following recommendations are prioritized, practical, and aligned with realistic resources.
  </p>
  <ol class="recommendations-list">
    <li>
      <h3>Recommendation 1: Quick Win – Implement Standard Workflow</h3>
      <p><strong>{ui('focus', 'en')}:</strong> Improve a central, recurring step in {hauptleistung or "your core business"} that frequently takes time and is suitable for AI support.</p>
      <p><strong>{ui('action', 'en')}:</strong> Introduce an AI-supported standard workflow with clear rules for inputs, quality checks, and approvals.</p>
      <p><strong>{ui('benefit_impact', 'en')}:</strong> Directly measurable relief for recurring tasks, higher consistency and more stable quality.</p>
      <p><strong>{ui('effort_budget', 'en')}:</strong> Low to medium – achievable in a few days; tool costs typically in the double to low triple-digit range per month.</p>
      <p><strong>{ui('responsible', 'en')}:</strong> Owner/Team Lead</p>
    </li>
    <li>
      <h3>Recommendation 2: Quality Assurance – AI-Supported Consistency Check</h3>
      <p><strong>{ui('focus', 'en')}:</strong> AI-supported consistency check for documents, content, or data structures tailored to industry requirements in {branche}.</p>
      <p><strong>{ui('action', 'en')}:</strong> Set up an automated review step before release including fact-checking, tone analysis, and compliance checks.</p>
      <p><strong>{ui('benefit_impact', 'en')}:</strong> Less rework, lower risk of errors, more stable quality across multiple projects.</p>
      <p><strong>{ui('effort_budget', 'en')}:</strong> Medium – 2-5 days setup; licenses dependent on user count.</p>
      <p><strong>{ui('responsible', 'en')}:</strong> Quality Management</p>
    </li>
    <li>
      <h3>Recommendation 3: Knowledge Management – Documentation & Knowledge Base</h3>
      <p><strong>{ui('focus', 'en')}:</strong> Improve documentation and knowledge management – a typical pain point that can be significantly alleviated with AI support.</p>
      <p><strong>{ui('action', 'en')}:</strong> Build an AI-supported knowledge library with templates, standards, checklists, and best practices.</p>
      <p><strong>{ui('benefit_impact', 'en')}:</strong> Faster onboarding, higher first-time hit rate, fewer follow-up questions and more consistent results.</p>
      <p><strong>{ui('effort_budget', 'en')}:</strong> Low to medium – depending on existing material; ongoing costs low.</p>
      <p><strong>{ui('responsible', 'en')}:</strong> Owner/Team Lead</p>
    </li>
    <li>
      <h3>Recommendation 4: Industry-Specific Use Case</h3>
      <p><strong>{ui('focus', 'en')}:</strong> An industry-specific use case for {branche} that promises high visibility and quick ROI.</p>
      <p><strong>{ui('action', 'en')}:</strong> Pilot a clearly defined AI use case that addresses typical industry workflows.</p>
      <p><strong>{ui('benefit_impact', 'en')}:</strong> Visible benefit immediately in daily operations, momentum for further digitization steps.</p>
      <p><strong>{ui('effort_budget', 'en')}:</strong> Variable depending on size and complexity; typically 3-10 days for a focused pilot.</p>
      <p><strong>{ui('responsible', 'en')}:</strong> Department + Management</p>
    </li>
    <li>
      <h3>Recommendation 5: Governance & Security</h3>
      <p><strong>{ui('focus', 'en')}:</strong> Establish clear guidelines and controls for AI use to minimize risks and ensure compliance.</p>
      <p><strong>{ui('action', 'en')}:</strong> Create a compact AI guideline with rules for data protection, quality checks, and approval processes.</p>
      <p><strong>{ui('benefit_impact', 'en')}:</strong> Higher legal certainty, transparent processes, strengthened trust with customers and partners. Preparation for EU AI Act.</p>
      <p><strong>{ui('effort_budget', 'en')}:</strong> Medium – policy development in 1-2 weeks.</p>
      <p><strong>{ui('responsible', 'en')}:</strong> Owner/Team Lead</p>
    </li>
  </ol>
  <h3>{ui('priorities_overview', 'en')}</h3>
  <table class="table">
    <thead><tr><th>{ui('priority', 'en')}</th><th>Recommendation</th><th>{ui('time_horizon', 'en')}</th><th>Main Benefit</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Implement standard workflow</td><td>0-3 months</td><td>Immediate relief & quality improvement</td></tr>
      <tr><td>2</td><td>AI-supported consistency check</td><td>3-6 months</td><td>Less rework & lower risk</td></tr>
      <tr><td>3</td><td>Centralize knowledge library</td><td>3-6 months</td><td>Faster onboarding & stable results</td></tr>
      <tr><td>4</td><td>Implement industry-specific pilot</td><td>6-12 months</td><td>Visible benefit & scaling momentum</td></tr>
      <tr><td>5</td><td>Governance & security guidelines</td><td>3-9 months</td><td>Legal certainty & trust</td></tr>
    </tbody>
  </table>
  <h3>{ui('summary', 'en')} and Success Factors</h3>
  <p>The successful implementation depends on several critical success factors. First, consistent follow-through is more important than perfect planning – start with a focused pilot and learn in the process. Second, define success metrics from the start to make progress measurable.</p>
  <p class="small muted">The recommendations are formulated to be immediately transferable to project planning and consistent with roadmap, business case, and risk analysis. Time frames are adapted to the {ui('company_size', 'en')} <strong>{size_label}</strong>.</p>
</section>"""
        if size_group == "solo":
            verantwortlich_1 = "Inhaber:in"
            verantwortlich_2 = "Inhaber:in"
            zeitrahmen_1 = "0–3 Monate"
            zeitrahmen_2 = "3–6 Monate"
            aufwand_1 = "Niedrig – realisierbar in wenigen Tagen"
            aufwand_5 = "Niedrig – persönliche Checkliste in 1-2 Tagen"
        elif size_group == "team":
            verantwortlich_1 = "Teamlead oder KI-Owner"
            verantwortlich_2 = "Qualitätsverantwortliche"
            zeitrahmen_1 = "0–6 Monate"
            zeitrahmen_2 = "3–9 Monate"
            aufwand_1 = "Mittel – 3-5 Tage Setup im Team"
            aufwand_5 = "Mittel – Team-Workshop + Dokumentation in 3-5 Tagen"
        else:
            verantwortlich_1 = "Fachbereich + verantwortliche Leitung"
            verantwortlich_2 = "Qualitätsmanagement + Fachbereich"
            zeitrahmen_1 = "0–6 Monate"
            zeitrahmen_2 = "6–9 Monate"
            aufwand_1 = "Mittel bis hoch – strukturiertes Setup mit Abstimmung"
            aufwand_5 = "Mittel bis hoch – Policy-Entwicklung in 2-4 Wochen"

        return f"""<section class="section recommendations">
  <h2>Handlungsempfehlungen – Ihre nächsten Schritte mit KI</h2>

  <p>
    Für ein Unternehmen in der Branche <strong>{branche}</strong> mit der Größe <strong>{size_label}</strong>
    ergeben sich mehrere unmittelbar realisierbare Hebel, um KI im Prozess <strong>{hauptleistung or "Ihrem Kerngeschäft"}</strong>
    wirksam einzusetzen. Die folgenden Empfehlungen sind priorisiert, praxisnah und auf realistische Ressourcen abgestimmt.
    Jede Empfehlung enthält konkrete Maßnahmen, erwarteten Nutzen, Aufwandsschätzung und Förderhinweise.
  </p>
  <p>
    Die Empfehlungen bauen aufeinander auf und sind so strukturiert, dass Sie mit einem Quick Win starten können und
    sukzessive komplexere Anwendungen erschließen. Beginnen Sie mit Empfehlung 1, um schnelle Erfolgserlebnisse zu
    generieren, und arbeiten Sie sich dann durch die weiteren Stufen. Parallelisieren Sie, wo Ressourcen es erlauben,
    aber verlieren Sie nicht den Fokus auf messbare Ergebnisse bei jedem Schritt. So schaffen Sie eine solide Basis
    für nachhaltigen Erfolg mit KI-gestützten Prozessen.
  </p>

  <ol class="recommendations-list">
    <li>
      <h3>Empfehlung 1: Quick Win – Standard-Workflow einführen</h3>
      <p><strong>Schwerpunkt:</strong> Verbesserung eines zentralen, wiederkehrenden Schritts in
        {hauptleistung or "Ihrem Kerngeschäft"}, der häufig Zeit bindet und sich für KI-Unterstützung eignet.</p>
      <p><strong>Maßnahme:</strong> Einführung eines KI-gestützten Standard-Workflows mit klaren Regeln für
        Eingaben, Qualitätsprüfung und Freigabe. Dokumentation der Prompts und Best Practices, damit die
        Ergebnisse reproduzierbar und konsistent sind.</p>
      <p><strong>Nutzen &amp; Wirkung:</strong> Direkt messbare Entlastung bei wiederkehrenden Aufgaben,
        höhere Konsistenz und stabilere Qualität. Die Zeitersparnis kann 10-25% im Zielbereich betragen.</p>
      <p><strong>Aufwand &amp; Budget:</strong> {aufwand_1}; Toolkosten typischerweise im zweistelligen
        bis niedrigen dreistelligen Bereich pro Monat.</p>
      <p><strong>Verantwortlich:</strong> {verantwortlich_1}</p>
      <p><strong>Förderchance:</strong> Je nach Bundesland {bundesland} bestehen Zuschussprogramme für
        digitale Prozessoptimierung. Prüfen Sie go-digital oder regionale Digitalisierungsförderung.</p>
    </li>

    <li>
      <h3>Empfehlung 2: Qualitätssicherung – KI-gestützte Konsistenzprüfung</h3>
      <p><strong>Schwerpunkt:</strong> KI-gestützte Konsistenzprüfung für Dokumente, Inhalte oder
        Datenstrukturen, abgestimmt auf branchentypische Anforderungen in {branche}.</p>
      <p><strong>Maßnahme:</strong> Einrichten eines automatisierten Review-Schritts vor der Freigabe.
        Dies kann Faktencheck, Tonalitätsprüfung, Markenrichtlinien oder Compliance-Checks umfassen.</p>
      <p><strong>Nutzen &amp; Wirkung:</strong> Weniger Nachbearbeitung, geringeres Risiko von Fehlern,
        stabilere Qualität über mehrere Aufträge hinweg. Reduziert Korrekturschleifen erheblich.</p>
      <p><strong>Aufwand &amp; Budget:</strong> Mittel – 2-5 Tage Setup; Lizenzen abhängig von Nutzerzahl.
        Oft in bestehende KI-Tools integrierbar.</p>
      <p><strong>Verantwortlich:</strong> {verantwortlich_2}</p>
      <p><strong>Förderchance:</strong> Programme für Qualitäts- und Effizienzsteigerungen in mehreren
        Bundesländern verfügbar. Besonders relevant bei Compliance-Bezug.</p>
    </li>

    <li>
      <h3>Empfehlung 3: Wissensmanagement – Dokumentation &amp; Wissensbasis</h3>
      <p><strong>Schwerpunkt:</strong> Dokumentation und Wissensmanagement verbessern – ein typisches
        Pain Point, das sich durch KI-Unterstützung deutlich entschärfen lässt.</p>
      <p><strong>Maßnahme:</strong> Aufbau einer KI-gestützten Wissensbibliothek mit Vorlagen, Standards,
        Checklisten und Best Practices. Zentrale Ablage für Prompts, Beispiele und Dokumentation.</p>
      <p><strong>Nutzen &amp; Wirkung:</strong> Schnellere Einarbeitung, höhere Ersttrefferquote, weniger
        Rückfragen und konsistentere Ergebnisse im Tagesgeschäft. Wissen geht nicht verloren.</p>
      <p><strong>Aufwand &amp; Budget:</strong> Niedrig bis mittel – abhängig vom vorhandenen Material;
        laufende Kosten gering. Initial 2-3 Tage für Strukturierung.</p>
      <p><strong>Verantwortlich:</strong> {verantwortlich_1}</p>
      <p><strong>Förderchance:</strong> Wissens- und Prozessdigitalisierung ist in vielen Programmen
        förderfähig. Prüfung für {bundesland} empfohlen.</p>
    </li>

    <li>
      <h3>Empfehlung 4: Branchenspezifischer Use Case</h3>
      <p><strong>Schwerpunkt:</strong> Ein branchenspezifischer Use Case für {branche}, der hohe
        Sichtbarkeit und schnellen ROI verspricht.</p>
      <p><strong>Maßnahme:</strong> Pilotierung eines klar abgegrenzten KI-Use-Cases, der typische
        Workflows der Branche adressiert. Fokus auf messbaren Nutzen und Lerneffekte.</p>
      <p><strong>Nutzen &amp; Wirkung:</strong> Sichtbarer Nutzen unmittelbar im Alltag, Momentum für
        weitere Digitalisierungsschritte. Erfolgsgeschichte für interne Kommunikation.</p>
      <p><strong>Aufwand &amp; Budget:</strong> Variable je nach Größe und Komplexität; typischerweise
        3-10 Tage für einen fokussierten Pilot.</p>
      <p><strong>Verantwortlich:</strong> {verantwortlich_1}</p>
      <p><strong>Förderchance:</strong> Pilot-Use-Cases mit klarer Zielsetzung werden von vielen
        Förderprogrammen priorisiert. Dokumentieren Sie den Pilot sorgfältig, um die Ergebnisse für
        weitere Förderanträge und interne Entscheidungsvorlagen nutzen zu können.</p>
    </li>

    <li>
      <h3>Empfehlung 5: Governance &amp; Sicherheit</h3>
      <p><strong>Schwerpunkt:</strong> Klare Richtlinien und Kontrollen für den KI-Einsatz etablieren,
        um Risiken zu minimieren und Compliance sicherzustellen.</p>
      <p><strong>Maßnahme:</strong> Erstellung eines kompakten KI-Leitfadens mit Regeln zu Datenschutz,
        Qualitätsprüfung und Freigabeprozessen. Definition von Verantwortlichkeiten und Eskalationswegen.</p>
      <p><strong>Nutzen &amp; Wirkung:</strong> Höhere Rechtssicherheit, transparente Prozesse und
        gestärktes Vertrauen bei Kund:innen und Partnern. Vorbereitung auf EU AI Act.</p>
      <p><strong>Aufwand &amp; Budget:</strong> {aufwand_5}</p>
      <p><strong>Verantwortlich:</strong> {verantwortlich_1}</p>
      <p><strong>Förderchance:</strong> Beratungsförderung für Datenschutz und IT-Sicherheit in
        {bundesland} prüfen. Auch KMU-Programme decken oft Governance ab.</p>
    </li>
  </ol>

  <h3>Prioritäten-Überblick</h3>
  <table class="table">
    <thead>
      <tr>
        <th>Priorität</th>
        <th>Empfehlung</th>
        <th>Zeitrahmen</th>
        <th>Hauptnutzen</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>1</td>
        <td>Standard-Workflow einführen</td>
        <td>{zeitrahmen_1}</td>
        <td>Sofortige Entlastung & Qualitätssteigerung</td>
      </tr>
      <tr>
        <td>2</td>
        <td>KI-gestützte Konsistenzprüfung</td>
        <td>{zeitrahmen_2}</td>
        <td>Weniger Nacharbeit & geringeres Risiko</td>
      </tr>
      <tr>
        <td>3</td>
        <td>Wissensbibliothek zentralisieren</td>
        <td>{zeitrahmen_2}</td>
        <td>Schnellere Einarbeitung & stabile Ergebnisse</td>
      </tr>
      <tr>
        <td>4</td>
        <td>Branchenspezifischen Pilot umsetzen</td>
        <td>6–12 Monate</td>
        <td>Sichtbarer Nutzen & Skalierungsmomentum</td>
      </tr>
      <tr>
        <td>5</td>
        <td>Governance & Sicherheitsrichtlinien</td>
        <td>{zeitrahmen_2}</td>
        <td>Rechtssicherheit & Vertrauen</td>
      </tr>
    </tbody>
  </table>

  <h3>Zusammenfassung und Erfolgsfaktoren</h3>
  <p>
    Die erfolgreiche Umsetzung dieser Empfehlungen hängt von mehreren kritischen Erfolgsfaktoren ab. Erstens ist
    konsequentes Dranbleiben wichtiger als perfekte Planung – starten Sie lieber mit einem fokussierten Pilot und
    lernen Sie im Prozess. Zweitens sollten Sie von Anfang an Erfolgskennzahlen definieren, um den Fortschritt
    messbar zu machen. Drittens empfiehlt es sich, regelmäßige Retrospektiven einzuplanen, um Learnings festzuhalten
    und Kurskorrekturen vorzunehmen.
  </p>
  <p>
    Achten Sie darauf, nicht zu viele Initiativen gleichzeitig zu starten. Besser ein Use Case sauber umgesetzt als
    drei halbfertige Experimente. Die Kombination aus schnellen Erfolgen (Empfehlung 1-2) und strukturierter
    Absicherung (Empfehlung 5) schafft sowohl Momentum als auch Stabilität für Ihre KI-Transformation.
  </p>
  <p>
    Dokumentieren Sie Ihre Erfahrungen von Anfang an: Welche Prompts funktionieren? Wo entstehen Fehler?
    Welche Qualitätsprüfungen haben sich bewährt? Diese Erkenntnisse sind wertvoll für die Skalierung auf weitere
    Anwendungsfälle und für das Onboarding zukünftiger Nutzer:innen der KI-Werkzeuge.
  </p>

  <p class="small muted">
    Die Empfehlungen sind so formuliert, dass sie unmittelbar in die Projektplanung übernommen werden können
    und konsistent mit Roadmap, Business Case und Risikoanalyse wirken. Die Zeitrahmen sind an die
    Unternehmensgröße <strong>{size_label}</strong> angepasst.
  </p>
</section>"""

    # 🎯 SIZE-AWARE ROADMAP FALLBACKS (inline HTML, 1000+ Zeichen)
    if section_key in ("roadmap", "roadmap_90d"):
        # TEIL 3.1.4: EN fallback for roadmap
        if briefing_lang == "en":
            phase3_text_en = ""
            if size_group == "team":
                phase3_text_en = " and share with 1-2 colleagues"
            elif size_group == "kmu":
                phase3_text_en = " and roll out aligned with departments"
            return f"""<div class="roadmap">
  <h4>Phase 1: Test & Preparation (0-30 days)</h4>
  <ul>
    <li>Define and document 2-3 most important AI deployment points in the {hauptleistung or "core business"} process.</li>
    <li>Select toolset, conduct initial tests, and log experiences.</li>
    <li>Create and communicate brief guide for inputs, quality criteria, and secure workflows.</li>
    <li>Collect initial examples and store in structured form (start prompt library).</li>
  </ul>
  <h4>Phase 2: Piloting (31-60 days)</h4>
  <ul>
    <li>Test a pilot workflow in daily operations, systematically collect feedback and document learnings.</li>
    <li>Schedule weekly mini-reviews to identify adjustment needs early.</li>
    <li>Document templates, examples, and best practices and prepare for repeated use.</li>
    <li>Define quality metrics (time, error rate, consistency) and conduct initial measurements.</li>
  </ul>
  <h4>Phase 3: Consolidation (61-90 days)</h4>
  <ul>
    <li>Establish proven workflows{phase3_text_en} and integrate into regular work routine.</li>
    <li>Define simple AI guidelines (data handling, approval processes, quality assurance).</li>
    <li>Prioritize next use cases, prepare {ui('roadmap', 'en')} 2.0, and plan resources.</li>
    <li>Conduct initial impact measurement: document time savings, quality improvement, risk reduction.</li>
  </ul>
</div>"""
        # Bedingter Text für Phase 3 basierend auf size_group
        phase3_text = ""
        if size_group == "team":
            phase3_text = " und an 1–2 Kolleg:innen weitergeben"
        elif size_group == "kmu":
            phase3_text = " und abgestimmt mit Fachbereichen ausrollen"

        return f"""<div class="roadmap">
  <h4>Phase 1: Test &amp; Vorbereitung (0–30 Tage)</h4>
  <ul>
    <li>2–3 wichtigste KI-Einsatzstellen im Prozess {hauptleistung or "Kerngeschäft"} festlegen und dokumentieren.</li>
    <li>Werkzeug-Set auswählen, erste Tests durchführen und Erfahrungen protokollieren.</li>
    <li>Kurzleitfaden für Eingaben, Qualitätskriterien und sichere Workflows erstellen und kommunizieren.</li>
    <li>Erste Beispiele sammeln und in strukturierter Form ablegen (Prompt-Bibliothek starten).</li>
  </ul>

  <h4>Phase 2: Pilotierung (31–60 Tage)</h4>
  <ul>
    <li>Einen Pilotworkflow im Alltag testen, Feedback systematisch einholen und Learnings dokumentieren.</li>
    <li>Wöchentliche Mini-Reviews einplanen, um Anpassungsbedarf frühzeitig zu erkennen.</li>
    <li>Vorlagen, Beispiele und Best Practices dokumentieren und für wiederholte Nutzung aufbereiten.</li>
    <li>Qualitätsmetriken definieren (Zeit, Fehlerquote, Konsistenz) und erste Messungen durchführen.</li>
  </ul>

  <h4>Phase 3: Verstetigung (61–90 Tage)</h4>
  <ul>
    <li>Bewährte Abläufe verstetigen{phase3_text} und in den regulären Arbeitsalltag integrieren.</li>
    <li>Einfache KI-Leitlinien definieren (Datenhandling, Freigabeprozesse, Qualitätssicherung).</li>
    <li>Nächste Use Cases priorisieren, Roadmap 2.0 vorbereiten und Ressourcen planen.</li>
    <li>Erste Wirkungsmessung durchführen: Zeitersparnis, Qualitätsverbesserung, Risikominderung dokumentieren.</li>
  </ul>
</div>"""
    
    # ════════════════════════════════════════════════════════════════════════════
    # 🎯 PLATIN+ FALLBACK: ROADMAP_12M (900+ Wörter)
    # ════════════════════════════════════════════════════════════════════════════
    if section_key == "roadmap_12m":
        # Size-aware Rollen und Governance-Aspekte
        if size_group == "solo":
            verantwortlich_1 = "Sie als Inhaber:in"
            verantwortlich_2 = "Sie persönlich"
            governance_1 = "Erstellen Sie eine persönliche Checkliste für KI-Output-Prüfung und dokumentieren Sie grundlegende Datenschutz-Regeln für Ihre Arbeit."
            governance_2 = "Führen Sie monatliche Selbst-Audits durch, dokumentieren Sie alle KI-gestützten Prozesse und halten Sie Best Practices schriftlich fest."
            governance_3 = "Etablieren Sie einen jährlichen Sicherheits-Check, entwickeln Sie eine Backup-Strategie für KI-generierte Inhalte und definieren Sie einen Notfallplan für Tool-Ausfälle."
            governance_4 = "Führen Sie ein Jahres-Audit durch, dokumentieren Sie Ihren Compliance-Status und bereiten Sie Ihre Learnings für die Roadmap 2.0 auf."
            skalierung = "Übertragen Sie erfolgreich erprobte Workflows auf weitere eigene Aufgabenbereiche und identifizieren Sie neue Automatisierungspotenziale in Ihrem Geschäftsmodell."
            team_aspekt = "Als Solo-Selbstständige:r liegt der Fokus auf persönlicher Effizienzsteigerung und der Entwicklung Ihrer eigenen KI-Kompetenz."
        elif size_group == "team":
            verantwortlich_1 = "Teamlead oder KI-Owner"
            verantwortlich_2 = "KI-Koordinator und beteiligte Teammitglieder"
            governance_1 = "Vereinbaren Sie Team-Regeln für die KI-Nutzung und definieren Sie einen Review-Prozess für kritische Outputs."
            governance_2 = "Etablieren Sie Quartals-Reviews mit dem gesamten Team, definieren Sie einen Incident-Prozess für KI-Fehler und erstellen Sie Schulungsmaterial."
            governance_3 = "Führen Sie halbjährliche Governance-Reviews durch, aktualisieren Sie das Risiko-Register und planen Sie Schulungs-Refresher für alle Teammitglieder."
            governance_4 = "Führen Sie eine Team-Retrospektive zur Governance durch, aktualisieren Sie Ihre Richtlinien und dokumentieren Sie Lessons Learned für das gesamte Team."
            skalierung = "Rollen Sie bewährte Workflows auf weitere Teammitglieder und Aufgabenbereiche aus und klären Sie Zuständigkeiten und Verantwortlichkeiten im Team."
            team_aspekt = "Im Team-Kontext steht die gemeinsame Entwicklung von Standards und der kontinuierliche Wissensaustausch im Vordergrund."
        else:  # kmu
            verantwortlich_1 = "Fachbereichsleitung in Abstimmung mit IT und Datenschutz"
            verantwortlich_2 = "Prozessverantwortliche und QS-Beauftragte"
            governance_1 = "Erstellen Sie einen Entwurf der KI-Richtlinie und führen Sie eine Datenschutz-Folgenabschätzung für die Pilotprojekte durch."
            governance_2 = "Richten Sie ein Governance-Board ein, etablieren Sie einen Audit-Trail für kritische Entscheidungen und formalisieren Sie Compliance-Checks."
            governance_3 = "Finalisieren Sie die KI-Richtlinie und kommunizieren Sie diese unternehmensweit, bereiten Sie ein externes Audit vor und formalisieren Sie das Risiko-Management."
            governance_4 = "Erstellen Sie einen Management-Report zur KI-Governance, evaluieren Sie Compliance-Zertifizierungen und führen Sie eine strategische Risiko-Bewertung für Jahr 2 durch."
            skalierung = "Pilotieren Sie erfolgreiche Anwendungen in weiteren Fachbereichen, identifizieren Sie Synergien und entwickeln Sie skalierbare Best Practices."
            team_aspekt = "Als KMU ermöglicht Ihre Organisationsstruktur die systematische Koordination verschiedener Fachbereiche und die Etablierung verbindlicher Standards."

        return f"""<section class="section roadmap-12m">
  <h2>Strategische 12-Monats-Roadmap</h2>

  <p>
    Diese Roadmap zeigt, wie ein Unternehmen der Größe <strong>{size_label}</strong> in der Branche
    <strong>{branche}</strong> innerhalb eines Jahres KI-gestützte Arbeitsweisen im Bereich
    <strong>{hauptleistung or "KI-gestützte Prozessoptimierung"}</strong> nachhaltig etabliert und ausbaut.
    Sie baut auf den Erfahrungen der ersten 90 Tage auf und verbindet schnelle operative Erfolge mit
    langfristiger strategischer Entwicklung. {team_aspekt}
  </p>

  <h3>Monate 1–3: Fundament und Pilot-Setup</h3>

  <p>
    Die ersten drei Monate dienen der Schaffung einer soliden Grundlage für die KI-Nutzung. Das Ziel
    ist es, realistische Erwartungen zu definieren, erste Quick Wins zu realisieren und eine
    strukturierte Basis für die weitere Entwicklung zu etablieren. In dieser Phase geht es darum,
    das Potenzial von KI für <strong>{hauptleistung or "Ihre Kernprozesse"}</strong> konkret zu
    erfassen und erste messbare Erfolge zu erzielen.
  </p>

  <h4>Priorisierung und Use-Case-Definition</h4>
  <p>
    Beginnen Sie mit der Definition von 3 bis 5 priorisierten Use Cases, die ein klares Wirkungspotenzial
    für Ihre tägliche Arbeit haben. Analysieren Sie, welche wiederkehrenden Aufgaben sich besonders
    für KI-Unterstützung eignen und wo der größte Hebel für Effizienzgewinne liegt. Dokumentieren Sie
    Ihre Auswahlkriterien und die erwarteten Ergebnisse, um später den Erfolg messen zu können.
  </p>

  <h4>Aufbau der Wissensbasis</h4>
  <p>
    Parallel bauen Sie eine strukturierte Prompt-Bibliothek mit 10 bis 15 dokumentierten Beispielen
    auf, die auf die spezifischen Anforderungen der Branche <strong>{branche}</strong> abgestimmt sind.
    Sammeln Sie Best Practices und legen Sie klare Qualitätskriterien fest. Diese Dokumentation bildet
    das Fundament für konsistente Ergebnisse und erleichtert die spätere Skalierung.
  </p>

  <h4>Governance-Grundlagen</h4>
  <p>
    {governance_1} Verantwortlich für diese Phase ist {verantwortlich_1}. Als messbare KPIs für die
    ersten drei Monate gelten: 2 bis 3 Quick Wins sind produktiv im Einsatz, eine erste Zeitersparnis
    von mindestens 10 Prozent ist nachweisbar dokumentiert, und die grundlegenden Qualitätskriterien
    sind definiert und kommuniziert.
  </p>

  <h3>Monate 4–6: Pilotierung und Qualitätsstandards</h3>

  <p>
    In der zweiten Phase geht es darum, KI-gestützte Prozesse im Arbeitsalltag zu verankern und
    stabile Workflows zu etablieren. Das Ziel ist die Verstetigung der ersten Erfolge und der Aufbau
    eines systematischen Monitoring-Systems. Die Erfahrungen aus den Quick Wins fließen in die
    Entwicklung robuster Standard-Workflows ein.
  </p>

  <h4>Workflow-Integration und Prozessstabilität</h4>
  <p>
    Etablieren Sie stabile Workflows für die wichtigsten Use Cases mit einem klaren Ablauf: Input,
    KI-Verarbeitung, Review und Freigabe. Erweitern Sie die Prompt-Bibliothek auf 25 bis 30
    praxiserprobte Beispiele und dokumentieren Sie systematisch, welche Ansätze funktionieren und
    welche Anpassungen erforderlich sind. Die Integration in bestehende Arbeitsprozesse sollte
    reibungslos und ohne unnötige Medienbrüche erfolgen.
  </p>

  <h4>Monitoring und kontinuierliche Verbesserung</h4>
  <p>
    Bauen Sie ein kontinuierliches Monitoring auf, das Zeitersparnis, Qualität, Fehlerquoten und
    Konsistenz systematisch erfasst. Erstellen Sie Schulungs- und Onboarding-Materialien für neue
    Use Cases und etablieren Sie regelmäßige Review-Formate, um Learnings zeitnah zu erfassen.
  </p>

  <h4>Governance und Qualitätssicherung</h4>
  <p>
    {governance_2} Verantwortlich für diese Phase ist {verantwortlich_2}. Die KPIs für Monat 4 bis 6
    umfassen: stabile Workflows sind produktiv im Einsatz, das Monitoring-System ist etabliert, und
    eine messbare Qualitätsverbesserung von mindestens 20 Prozent Zeitersparnis ist dokumentiert.
  </p>

  <h3>Monate 7–12: Ausbau, Skalierung und Governance</h3>

  <p>
    Die dritte Phase fokussiert auf die Multiplikation erfolgreicher Workflows und die Erschließung
    neuer Anwendungsbereiche. Das Ziel ist es, den nachweisbaren ROI zu erreichen und eine tragfähige
    Governance-Struktur zu etablieren, die langfristige Stabilität und Compliance gewährleistet.
    {skalierung}
  </p>

  <h4>Systematische Skalierung</h4>
  <p>
    Bauen Sie auf den Erfolgen der ersten sechs Monate auf und skalieren Sie auf 5 bis 8 produktive
    Use Cases mit nachweisbarem ROI. Identifizieren Sie Synergien zwischen verschiedenen
    Anwendungsbereichen und entwickeln Sie systematische Erfolgsmessung mit Dashboards, KPIs und
    Trendanalysen. Die Skalierung sollte kontrolliert erfolgen, um die Qualität zu gewährleisten.
    Nutzen Sie die gewonnenen Erkenntnisse aus den ersten sechs Monaten, um die Einführung neuer
    Use Cases zu beschleunigen und typische Fehler zu vermeiden. Eine schrittweise Erweiterung
    minimiert Risiken und ermöglicht kontinuierliches Lernen.
  </p>

  <h4>Governance-Framework finalisieren</h4>
  <p>
    {governance_3} Entwickeln Sie klare Leitlinien für Datenhandling, Qualitätssicherung und
    Freigabeprozesse. Definieren Sie eindeutige Verantwortlichkeiten und Eskalationswege. Die
    Governance-Strukturen sollten so gestaltet sein, dass sie den Anforderungen des EU AI Act
    entsprechen und eine externe Prüfung bestehen können. Dokumentieren Sie alle Prozesse und
    Entscheidungen nachvollziehbar, um bei Bedarf Rechenschaft ablegen zu können.
  </p>

  <h4>Erfolgsmessung und ROI-Nachweis</h4>
  <p>
    Verantwortlich für diese Phase ist {verantwortlich_1}. Als KPIs gelten: 5 bis 8 Use Cases sind
    produktiv im Einsatz, der ROI erreicht mindestens 30 Prozent des ursprünglichen Business Case,
    und die Governance-Strukturen sind etabliert und dokumentiert. Bereiten Sie die Datenbasis für
    das Management-Reporting vor.
  </p>

  <h3>Abschluss und Verstetigung: 12-Monats-Bilanz</h3>

  <p>
    Die abschließende Phase dient der Konsolidierung aller Learnings und der Vorbereitung der
    strategischen Weiterentwicklung für Jahr 2. Das Ziel ist ein umfassender Jahresrückblick, der
    sowohl Erfolge als auch Verbesserungspotenziale identifiziert und eine klare Roadmap 2.0
    für das kommende Jahr definiert.
  </p>

  <h4>Systematische Auswertung</h4>
  <p>
    Führen Sie eine systematische Auswertung aller Use Cases durch: Analysieren Sie Wirkung,
    Effizienz, Risiken und Optimierungspotenziale. Dokumentieren Sie detailliert, welche Ansätze
    besonders erfolgreich waren und welche Anpassungen für die Zukunft sinnvoll sind. Diese
    Erkenntnisse bilden die Grundlage für die strategische Planung des kommenden Jahres.
  </p>

  <h4>Strategische Planung für Jahr 2</h4>
  <p>
    Definieren Sie die strategische Roadmap 2.0 für das zweite Jahr: Priorisieren Sie die nächsten
    Use Cases, sichern Sie das Budget und treffen Sie strategische Entscheidungen über
    Ausbaustufen, Integration und Automatisierung. Berücksichtigen Sie dabei die Erkenntnisse aus
    dem ersten Jahr und die sich entwickelnden Möglichkeiten der KI-Technologie. Beziehen Sie
    aktuelle Marktentwicklungen und technologische Trends in Ihre Planung ein, um auch im zweiten
    Jahr wettbewerbsfähig zu bleiben und neue Chancen frühzeitig zu erkennen.
  </p>

  <h4>Governance-Abschluss und Compliance</h4>
  <p>
    {governance_4} Verantwortlich für den Jahresabschluss ist {verantwortlich_1}. Die finalen KPIs
    umfassen: ein vollständiger Jahresreview ist dokumentiert, die Roadmap 2.0 ist priorisiert und
    freigegeben, das Budget für Jahr 2 ist gesichert, und der ursprünglich geplante ROI ist erreicht
    oder übertroffen.
  </p>

  <p class="small muted">
    Diese 12-Monats-Roadmap schafft die Grundlage für eine nachhaltige, strategisch verankerte
    KI-Nutzung in <strong>{hauptleistung or "Ihrem Kerngeschäft"}</strong>. Sie verbindet schnelle
    operative Erfolge mit langfristiger strategischer Entwicklung und bereitet die Skalierung
    für Jahr 2 systematisch vor.
  </p>
</section>"""

    # 🎯 SIZE-AWARE ORG_CHANGE FALLBACK
    if section_key == "org_change":
        # Vollwertiger, size-aware Fallback für Org Change (900+ Zeichen)
        if size_group == "solo":
            return f"""<div class="org-change-content">
  <p><strong>Veränderungsfähigkeit &amp; Lernen als Solo-Berater:in in der KI-Beratung</strong></p>

  <p>
    Als Solo-Berater:in in <strong>{branche}</strong> ist Ihre Fähigkeit, Veränderungen bei Kund:innen
    zu begleiten und gleichzeitig selbst kontinuierlich zu lernen, ein entscheidender Erfolgsfaktor.
    Der Einsatz von KI-Tools verändert nicht nur Ihre eigenen Arbeitsprozesse, sondern auch die
    Erwartungen und Anforderungen Ihrer Kund:innen. Eine strukturierte Herangehensweise hilft,
    diese Transformation erfolgreich zu gestalten.
  </p>

  <h4>Kommunikation &amp; Erwartungsmanagement</h4>
  <p>
    Klare Kommunikation ist die Basis jeder erfolgreichen Veränderung. Bereits im Kick-off-Gespräch
    sollten Sie ein realistisches Zielbild entwickeln: Was kann KI in Ihrem Beratungskontext leisten,
    wo liegen die Grenzen? Sprechen Sie offen über mögliche Risiken – von Datenschutz bis zu
    Qualitätssicherung – und definieren Sie gemeinsam mit Ihren Kund:innen messbare Erfolgskriterien.
    Diese Transparenz schafft Vertrauen und verhindert unrealistische Erwartungen.
  </p>

  <h4>Pilotprojekte &amp; Feedback-Schleifen</h4>
  <p>
    Starten Sie mit einem kleinen, klar abgegrenzten Vorhaben – etwa der KI-gestützten Erstellung
    von Konzeptentwürfen oder der Automatisierung von Recherche-Prozessen. Dokumentieren Sie
    systematisch, was funktioniert und was nicht. Planen Sie wöchentliche oder zweiwöchentliche
    Mini-Reviews ein, um Learnings zeitnah zu erfassen und den Ansatz kontinuierlich anzupassen.
    Diese iterative Vorgehensweise ermöglicht schnelle Korrekturen ohne großen Aufwand.
  </p>

  <h4>Dokumentation &amp; Routinen etablieren</h4>
  <p>
    Halten Sie erfolgreiche Workflows in Form von Checklisten, Prompt-Vorlagen und einfachen
    Regeln fest. Diese Dokumentation ist Ihr persönliches Wissensmanagement-System und hilft,
    bewährte Praktiken zu verstetigen. Definieren Sie klare, einfache Routinen für wiederkehrende
    Aufgaben – ohne unnötige Bürokratie. Das spart Zeit und erhöht die Konsistenz Ihrer Beratungsleistung.
  </p>

  <h4>Umgang mit Widerständen &amp; Ängsten</h4>
  <p>
    Veränderung erzeugt oft Unsicherheit – bei Ihnen selbst und bei Ihren Kund:innen. Nehmen Sie
    Ängste ernst: Bedenken bezüglich Datenschutz, Angst vor Überlastung oder Skepsis gegenüber
    neuen Technologien sind legitim. Bieten Sie praktische Hilfen an: klare Leitlinien, einfache
    Einstiegsszenarien und konkrete Erfolgsbeispiele. Zeigen Sie, dass KI Sie unterstützt und
    nicht ersetzt – und dass der Lernprozess schrittweise und beherrschbar ist.
  </p>

  <p class="small muted">
    Der Fokus liegt auf einer schlanken, realistischen Umsetzung, die zu einem Solo-Unternehmen
    passt: kurze Wege, klare persönliche Routinen und möglichst wenig organisatorischer Overhead.
    Ihre Agilität als Solo-Selbstständige:r ist dabei ein Vorteil – nutzen Sie ihn bewusst.
  </p>
</div>"""
        elif size_group == "team":
            return f"""<div class="org-change-content">
  <p><strong>Veränderungsfähigkeit &amp; Lernen im Team-Kontext</strong></p>

  <p>
    In einem kleinen Team (2–10 Personen) in <strong>{branche}</strong> ist es entscheidend,
    Veränderungen gemeinsam zu gestalten und dabei alle Teammitglieder mitzunehmen. Der Einsatz
    von KI-Tools bietet Chancen für effizientere Workflows, erfordert aber auch klare Abstimmung
    und gemeinsame Lernprozesse.
  </p>

  <h4>Kommunikation &amp; Erwartungsmanagement im Team</h4>
  <p>
    Organisieren Sie einen gemeinsamen Kick-off, bei dem alle Beteiligten ein realistisches
    Zielbild entwickeln. Klären Sie Rollen (z.B. KI-Owner, Teamlead) und definieren Sie
    messbare Ziele. Sprechen Sie offen über Risiken und Bedenken – nur so entsteht Vertrauen
    und Akzeptanz für neue Arbeitsweisen.
  </p>

  <h4>Pilotprojekte &amp; Team-Feedback</h4>
  <p>
    Starten Sie mit einem überschaubaren Pilotvorhaben, bei dem 2–3 Teammitglieder eng zusammenarbeiten.
    Richten Sie regelmäßige Feedback-Runden ein (z.B. wöchentliche Retrospektiven), um Learnings
    schnell zu teilen und Anpassungen vorzunehmen. Dokumentieren Sie Erfolge und Herausforderungen
    gemeinsam, sodass alle vom Wissen der anderen profitieren.
  </p>

  <h4>Gemeinsame Standards &amp; Workflows</h4>
  <p>
    Entwickeln Sie zusammen Checklisten, Prompt-Vorlagen und Qualitätskriterien, die für alle
    im Team gelten. Klare, abgestimmte Prozesse vermeiden Missverständnisse und sorgen für
    konsistente Ergebnisse. Halten Sie diese Standards schlank und praxisnah – Überregulierung
    bremst den Fortschritt.
  </p>

  <h4>Umgang mit unterschiedlichen Lerntempi</h4>
  <p>
    Nicht alle Teammitglieder haben denselben Zugang zu neuen Technologien. Bieten Sie
    niedrigschwellige Einstiegshilfen an, teilen Sie Erfolgsbeispiele und schaffen Sie Raum
    für Fragen. Peer-Learning und gegenseitige Unterstützung sind in kleinen Teams besonders
    wertvoll – nutzen Sie diese Dynamik aktiv.
  </p>

  <p class="small muted">
    Der Fokus liegt auf gemeinsamer Verantwortung, klarer Rollenverteilung und agilen Lernzyklen.
    Ihre Größe ist ein Vorteil: kurze Abstimmungswege, schnelle Entscheidungen und direkter Austausch.
  </p>
</div>"""
        else:  # kmu
            return f"""<div class="org-change-content">
  <p><strong>Veränderungsfähigkeit &amp; Lernen in KMU-Strukturen</strong></p>

  <p>
    In einem KMU (11–100 Mitarbeitende) in <strong>{branche}</strong> erfordert die Einführung
    von KI-Tools eine strukturierte Change-Management-Strategie. Verschiedene Fachbereiche,
    unterschiedliche Interessen und formale Governance-Anforderungen müssen koordiniert werden,
    um nachhaltige Veränderungen zu erreichen.
  </p>

  <h4>Stakeholder-Kommunikation &amp; Erwartungsmanagement</h4>
  <p>
    Binden Sie von Anfang an relevante Stakeholder ein: Management, Fachbereichsleitung,
    IT und Datenschutz. Entwickeln Sie ein gemeinsames Zielbild, klären Sie Verantwortlichkeiten
    und definieren Sie messbare KPIs. Transparente Kommunikation über Chancen, Risiken und
    Ressourcenbedarf schafft Akzeptanz und verhindert spätere Konflikte.
  </p>

  <h4>Pilotprojekte mit Fachbereichseinbindung</h4>
  <p>
    Starten Sie mit einem klar abgegrenzten Pilotprojekt in einem oder zwei Fachbereichen.
    Definieren Sie Pilotflächen, benennen Sie verantwortliche Personen und etablieren Sie
    regelmäßige Review-Formate (z.B. monatliche Steering-Meetings). Dokumentieren Sie Erfolge
    und Learnings systematisch, um daraus skalierbare Best Practices abzuleiten.
  </p>

  <h4>Bereichsübergreifende Standards &amp; Governance</h4>
  <p>
    Entwickeln Sie einheitliche Leitlinien für Datenhandling, Qualitätssicherung und Freigabeprozesse.
    Klären Sie, wer für welche Entscheidungen verantwortlich ist (z.B. Datenschutzbeauftragte,
    IT-Leitung, Prozessverantwortliche in Fachbereichen). Dokumentieren Sie diese Standards klar
    und kommunizieren Sie sie aktiv – nur so entsteht organisationsweite Verbindlichkeit.
  </p>

  <h4>Change-Kommunikation &amp; Widerstandsmanagement</h4>
  <p>
    Veränderungen stoßen oft auf Skepsis oder Widerstand. Kommunizieren Sie frühzeitig und
    regelmäßig über Fortschritte, Erfolge und Herausforderungen. Bieten Sie Schulungen und
    niedrigschwellige Einstiegsformate an (z.B. Lunch &amp; Learn, Mini-Workshops). Nehmen
    Sie Bedenken ernst und zeigen Sie konkrete Nutzenbeispiele aus der eigenen Organisation –
    das erhöht Akzeptanz und Motivation nachhaltig.
  </p>

  <p class="small muted">
    Der Fokus liegt auf strukturierter Koordination, klaren Verantwortlichkeiten und skalierbaren
    Prozessen. Ihre Organisationsgröße erfordert formale Governance, bietet aber auch die
    Möglichkeit, bereichsübergreifende Synergien systematisch zu nutzen.
  </p>
</div>"""

    # 🎯 SIZE-AWARE NEXT ACTIONS
    if section_key == "next_actions":
        if size_group == "solo":
            # Solo: Persönliche Tasks ohne Rollen
            return f"""<ol>
<li><strong>Persönliche Priorisierung</strong> — Top-3 KI-Einsatzbereiche für {hauptleistung or "Ihr Kerngeschäft"} definieren<br>
⏱ 1 Tag · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=7)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 3 priorisierte Use Cases dokumentiert und bewertet</li>

<li><strong>Tool-Evaluation</strong> — 2–3 KI-Tools testen (inkl. DSGVO-Check)<br>
⏱ 2 Tage · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=14)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 1 Tool ausgewählt mit klarer Begründung</li>

<li><strong>Erste Workflows aufsetzen</strong> — Kurzleitfaden für Eingaben und Qualitätskriterien erstellen<br>
⏱ 1 Tag · 🎯 mittel · 📆 {(datetime.now() + timedelta(days=21)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> Leitfaden dokumentiert, erste Tests durchgeführt</li>

<li><strong>Quick Win pilotieren</strong> — Ersten Use Case im Alltag testen und Wirkung messen<br>
⏱ 3 Tage · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=28)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> Erstes messbares Ergebnis (Zeitersparnis, Qualität) dokumentiert</li>
</ol>"""
        elif size_group == "team":
            # Team: Team-bezogene Tasks
            return f"""<ol>
<li><strong>KI-Owner / Teamlead</strong> — Team-Kick-off organisieren und Top-3 Use Cases priorisieren<br>
⏱ 2 Tage · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=14)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 3–5 priorisierte Use Cases dokumentiert und im Team abgestimmt</li>

<li><strong>IT-Verantwortliche:r</strong> — Tool-Evaluierung durchführen (inkl. DSGVO-Check und Security-Review)<br>
⏱ 3 Tage · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=21)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 3 Tools evaluiert, 1 konkrete Empfehlung mit Begründung</li>

<li><strong>Team-Koordinator:in</strong> — Qualitätskriterien definieren und erste Workflows dokumentieren<br>
⏱ 2 Tage · 🎯 mittel · 📆 {(datetime.now() + timedelta(days=21)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> Workflow-Dokumentation erstellt, im Team geteilt</li>

<li><strong>Projektleitung</strong> — Pilot-Phase planen und Erwartungen definieren<br>
⏱ 1 Tag · 🎯 mittel · 📆 {(datetime.now() + timedelta(days=28)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 3–5 konkrete Testszenarien dokumentiert</li>
</ol>"""
        else:  # kmu
            # KMU: Erweiterte Rollenstruktur
            return f"""<ol>
<li><strong>Bereichsleitung / Prozessverantwortliche:r</strong> — Stakeholder-Kick-off organisieren und Top-3 Use Cases priorisieren<br>
⏱ 2 Tage · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=14)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 3–5 priorisierte Use Cases dokumentiert und abgestimmt</li>

<li><strong>IT-Verantwortliche:r</strong> — Tool-Evaluierung durchführen (inkl. DSGVO-Check und Security-Review)<br>
⏱ 3 Tage · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=21)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 3 Tools evaluiert, 1 konkrete Empfehlung mit Begründung</li>

<li><strong>Datenschutz-Verantwortliche:r</strong> — Datenschutz-Konzept für KI-Einsatz erstellen<br>
⏱ 2 Tage · 🎯 hoch · 📆 {(datetime.now() + timedelta(days=21)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> DSGVO-Checkliste vollständig abgearbeitet</li>

<li><strong>Projektleitung</strong> — Pilot-Phase planen und Erwartungen definieren<br>
⏱ 1 Tag · 🎯 mittel · 📆 {(datetime.now() + timedelta(days=28)).strftime('%d.%m.%Y')}<br>
<em>KPI:</em> 3–5 konkrete Testszenarien dokumentiert</li>
</ol>"""
    
    # 🎯 STATIC SECTIONS: Business ROI / Costs (verwenden Business-Case-Daten aus briefing)
    if section_key in ("business_roi", "business_costs"):
        capex = briefing.get("CAPEX_REALISTISCH_EUR", "—")
        opex = briefing.get("OPEX_REALISTISCH_EUR", "—")
        einsparung = briefing.get("EINSPARUNG_MONAT_EUR", "—")
        payback = briefing.get("PAYBACK_MONTHS", "—")
        # SPRINT G2.5: Format ROI with 1 decimal place to avoid floating point issues
        roi_raw = briefing.get("ROI_12M", "—")
        roi_12m = f"{float(roi_raw):.1f}" if isinstance(roi_raw, (int, float)) else roi_raw

        return f"""<div class="business-case-summary">
  <h3>Business Case Übersicht</h3>
  <table class="table">
    <tr>
      <td><strong>Einführungskosten (CAPEX)</strong></td>
      <td class="text-right">{capex} €</td>
    </tr>
    <tr>
      <td><strong>Laufende Kosten (OPEX)</strong></td>
      <td class="text-right">{opex} €/Monat</td>
    </tr>
    <tr>
      <td><strong>Erwartete Einsparung</strong></td>
      <td class="text-right">{einsparung} €/Monat</td>
    </tr>
    <tr>
      <td><strong>Amortisation</strong></td>
      <td class="text-right">{payback} Monate</td>
    </tr>
    <tr>
      <td><strong>ROI nach 12 Monaten</strong></td>
      <td class="text-right">{roi_12m} %</td>
    </tr>
  </table>
  <p class="small muted">Detaillierte Berechnungen finden Sie im Business-Case-Abschnitt.</p>
</div>"""

    # 🎯 AI ACT SUMMARY: Statische Zusammenfassung (keine LLM-Variabilität)
    if section_key == "ai_act_summary":
        return f"""<div class="ai-act-summary">
  <h3>EU AI Act – Kernpunkte für {size_label}</h3>
  <p>
    Der EU AI Act klassifiziert KI-Systeme nach Risikostufen und legt entsprechende
    Anforderungen fest. Für die meisten betrieblichen KI-Anwendungen ({branche}) gelten
    moderate Transparenz- und Dokumentationspflichten.
  </p>
  <h4>Risikoeinstufung</h4>
  <ul>
    <li><strong>Minimales Risiko:</strong> Standardanwendungen wie Textgenerierung, Übersetzung,
        Datenanalyse – geringe Regulierung, Transparenzhinweise empfohlen.</li>
    <li><strong>Begrenztes Risiko:</strong> Chatbots, personalisierte Empfehlungen –
        Informationspflicht gegenüber Nutzern erforderlich.</li>
    <li><strong>Hohes Risiko:</strong> Recruiting, Kreditvergabe, kritische Infrastruktur –
        umfassende Dokumentation, Risikoanalyse, menschliche Aufsicht verpflichtend.</li>
  </ul>
  <h4>Praktische Implikationen</h4>
  <p>
    Für {size_label} bedeutet dies: Bei Standardanwendungen (Content, Analyse, Automatisierung)
    sind primär transparente Nutzungshinweise und DSGVO-konforme Datenverarbeitung relevant.
    Hochrisiko-Anwendungen erfordern zusätzliche Governance-Prozesse.
  </p>
  <p class="small muted">
    Stand: Q1 2025. Detaillierte Anforderungen entwickeln sich weiter – bei kritischen
    Anwendungen rechtliche Beratung empfohlen.
  </p>
</div>"""

    # ════════════════════════════════════════════════════════════════════════════
    # 🎯 PLATIN+ FALLBACK: UNTERNEHMENSPROFIL_MARKT (500+ Wörter)
    # ════════════════════════════════════════════════════════════════════════════
    if section_key == "unternehmensprofil_markt":
        if size_group == "solo":
            markt_position = "Als Solo-Selbstständige:r agieren Sie flexibel und können schnell auf Marktveränderungen reagieren"
            wettbewerb = "Ihre Wettbewerber sind oft größere Agenturen oder spezialisierte Einzelberater:innen"
            ki_chance = "KI kann Ihnen helfen, Leistungen anzubieten, die sonst nur größeren Anbietern möglich wären"
            differenzierung = "Ihre persönliche Expertise kombiniert mit KI-Unterstützung schafft ein einzigartiges Leistungsprofil"
        elif size_group == "team":
            markt_position = "Als kleines Team vereinen Sie Agilität mit gebündelter Fachkompetenz"
            wettbewerb = "Ihre Wettbewerber reichen von Solo-Selbstständigen bis zu etablierten Mittelständlern"
            ki_chance = "KI ermöglicht Ihrem Team, effizienter zu arbeiten und gleichzeitig die Qualität zu steigern"
            differenzierung = "Die Kombination aus Teamkompetenz und KI-gestützten Prozessen hebt Sie von Wettbewerbern ab"
        else:  # kmu
            markt_position = "Als KMU verfügen Sie über etablierte Strukturen und können systematisch skalieren"
            wettbewerb = "Ihre Wettbewerber sind sowohl agile kleinere Anbieter als auch große Konzerne"
            ki_chance = "KI unterstützt Sie dabei, Prozesse zu standardisieren und gleichzeitig individuell auf Kundenbedürfnisse einzugehen"
            differenzierung = "Die strukturierte Integration von KI in Ihre Fachbereiche schafft nachhaltige Wettbewerbsvorteile"

        return f"""<section class="section unternehmensprofil-markt">
  <h2>Unternehmensprofil und Marktumfeld</h2>

  <h3>Ihr Unternehmen im Überblick</h3>
  <p>
    Als Unternehmen der Größe <strong>{size_label}</strong> in der Branche <strong>{branche}</strong>
    haben Sie sich auf <strong>{hauptleistung or "spezialisierte Dienstleistungen"}</strong> fokussiert.
    Diese Positionierung bringt spezifische Chancen und Herausforderungen mit sich, die bei der
    Einführung von KI-Technologien berücksichtigt werden sollten. {markt_position}. Ihre Kernkompetenz
    liegt in der Verbindung von Branchenwissen mit praxisnaher Umsetzungsstärke. Das tiefe Verständnis
    für branchenspezifische Anforderungen und Kundenerwartungen bildet eine solide Grundlage für die
    erfolgreiche Integration von KI-Technologien in Ihre Geschäftsprozesse.
  </p>
  <p>
    Die Kombination aus Branchenexpertise und technologischer Offenheit ist ein entscheidender
    Erfolgsfaktor. Unternehmen, die beide Dimensionen vereinen, können KI nicht nur als
    Effizienzwerkzeug nutzen, sondern auch als strategischen Hebel zur Weiterentwicklung ihres
    Geschäftsmodells. Die folgenden Abschnitte analysieren Ihr Marktumfeld und die sich daraus
    ergebenden Chancen für den KI-Einsatz.
  </p>

  <h3>Marktumfeld und Wettbewerbssituation</h3>
  <p>
    Die Branche <strong>{branche}</strong> durchläuft aktuell einen tiefgreifenden digitalen Wandel.
    Kund:innen erwarten zunehmend schnellere Reaktionszeiten, höhere Qualität und individuellere
    Lösungen. {wettbewerb}. Der Markt zeigt einen klaren Trend zur Integration von KI-Technologien
    in Kernprozesse – Unternehmen, die diesen Wandel aktiv gestalten, können sich entscheidende
    Vorteile sichern. Die Geschwindigkeit des technologischen Wandels erfordert kontinuierliche
    Anpassungsfähigkeit und die Bereitschaft, etablierte Prozesse kritisch zu hinterfragen.
  </p>
  <p>
    Die Digitalisierung hat die Markteintrittsbarrieren in vielen Bereichen gesenkt, gleichzeitig
    aber auch die Anforderungen an Qualität und Geschwindigkeit erhöht. In diesem dynamischen
    Umfeld ist die strategische Nutzung von KI ein wesentlicher Hebel für nachhaltigen Erfolg.
    Unternehmen, die KI frühzeitig und durchdacht einsetzen, können Effizienzgewinne realisieren
    und gleichzeitig ihre Dienstleistungsqualität verbessern. Die Wettbewerbslandschaft verändert
    sich kontinuierlich, und Anbieter, die innovative Technologien schnell adaptieren, können
    Marktanteile gewinnen.
  </p>

  <h3>KI-Chancen für Ihr Geschäftsmodell</h3>
  <p>
    {ki_chance}. Im Bereich <strong>{hauptleistung or "Ihrer Kernleistung"}</strong> ergeben sich
    konkrete Einsatzmöglichkeiten: von der Automatisierung wiederkehrender Aufgaben über die
    Verbesserung der Qualitätssicherung bis hin zur Entwicklung neuer Angebote. Die wichtigsten
    Potenziale liegen typischerweise in drei Bereichen:
  </p>
  <ul>
    <li><strong>Effizienzsteigerung:</strong> Automatisierung von Routineaufgaben, schnellere
        Recherche und Dokumentation, optimierte Workflows in Kernprozessen. Diese Verbesserungen
        setzen Kapazitäten frei, die für wertschöpfende Tätigkeiten genutzt werden können.</li>
    <li><strong>Qualitätsverbesserung:</strong> Konsistenzprüfung, systematische Reviews,
        datengestützte Entscheidungsvorbereitung und standardisierte Qualitätskontrollen. KI
        kann hier als zweite Prüfinstanz dienen und die Fehlerquote deutlich reduzieren.</li>
    <li><strong>Innovationspotenzial:</strong> Neue Dienstleistungsangebote, erweiterte
        Beratungskapazitäten und verbesserte Kundenerlebnisse durch KI-gestützte Services.
        Innovative KI-Anwendungen können auch neue Zielgruppen erschließen.</li>
  </ul>
  <p>
    Die Realisierung dieser Potenziale erfordert einen strukturierten Ansatz, der sowohl
    technische als auch organisatorische Aspekte berücksichtigt. Erfolgreiche KI-Implementierungen
    beginnen typischerweise mit klar definierten Use Cases, die schnell messbare Ergebnisse liefern.
  </p>

  <h3>Differenzierungsstrategie</h3>
  <p>
    {differenzierung}. Die Branche {branche} bietet spezifische Ansatzpunkte: branchentypische
    Pain Points können durch gezielte KI-Lösungen adressiert werden, typische Workflows lassen
    sich optimieren und die Erwartungen Ihrer Zielgruppe können besser erfüllt werden. Eine klare
    Positionierung als technologisch fortschrittlicher Anbieter kann ein wichtiges Differenzierungsmerkmal
    im Wettbewerb darstellen.
  </p>
  <p>
    Ein strukturierter Ansatz zur KI-Einführung – beginnend mit Quick Wins und aufbauend zu
    komplexeren Anwendungen – ermöglicht es Ihnen, Risiken zu minimieren und gleichzeitig
    kontinuierlich Mehrwert zu schaffen. Die 90-Tage-Roadmap und die 12-Monats-Strategie in
    diesem Bericht zeigen konkrete Schritte für diese Entwicklung auf. Dabei ist es wichtig,
    die eigene Differenzierungsstrategie kontinuierlich zu überprüfen und an Marktveränderungen
    anzupassen.
  </p>

  <h3>Standortfaktoren und regionale Chancen</h3>
  <p>
    Als Unternehmen mit Sitz in <strong>{bundesland}</strong> können Sie von regionalen
    Förderprogrammen und Netzwerken profitieren. Viele Bundesländer bieten spezifische
    Digitalisierungs- und Innovationsförderungen, die für KI-Projekte nutzbar sind.
    Der Förderkapitel in diesem Bericht enthält detaillierte Hinweise zu passenden Programmen.
    Regionale Wirtschaftsförderungen, IHK-Netzwerke und Technologiezentren können wertvolle
    Ressourcen für den Einstieg in KI-Technologien sein. Auch der Austausch mit anderen
    Unternehmen der Region, die bereits KI einsetzen, kann wichtige Erfahrungswerte liefern.
  </p>

  <p class="small muted">
    Diese Analyse basiert auf den Angaben aus Ihrem Briefing und allgemeinen Branchentrends.
    Für eine vertiefte Markt- und Wettbewerbsanalyse empfiehlt sich eine spezialisierte Beratung.
  </p>
</section>"""

    # ════════════════════════════════════════════════════════════════════════════
    # 🎯 PLATIN+ FALLBACK: GAMECHANGER (700+ Wörter)
    # ════════════════════════════════════════════════════════════════════════════
    if section_key == "gamechanger":
        if size_group == "solo":
            gc_voraussetzung_1 = "Als Solo-Selbstständige:r können Sie diese Standardisierung eigenverantwortlich umsetzen"
            gc_voraussetzung_2 = "Die persönliche Sortierung und Pflege Ihrer Wissensbasis liegt in Ihrer Hand"
            gc_voraussetzung_3 = "Entwickeln Sie persönliche Routinen für die Qualitätsprüfung vor jeder Kundenabgabe"
            gc_team_aspekt = "Ihre Agilität als Einzelperson ermöglicht schnelle Experimente und direkte Umsetzung"
        elif size_group == "team":
            gc_voraussetzung_1 = "Im Team definieren Sie klare Rollen für die Pflege von Vorlagen und Automatisierungen"
            gc_voraussetzung_2 = "Die gemeinsame Abstimmung im Team sichert konsistente Qualität und Wissenstransfer"
            gc_voraussetzung_3 = "Etablieren Sie Review-Rollen innerhalb des Teams für gegenseitige Qualitätssicherung"
            gc_team_aspekt = "Ihr Team kann Aufgaben aufteilen und voneinander lernen – nutzen Sie diese Dynamik"
        else:  # kmu
            gc_voraussetzung_1 = "In Ihrer Organisation koordinieren Sie die Standardisierung über Fachbereiche hinweg"
            gc_voraussetzung_2 = "Die bereichsübergreifende Koordination erfordert klare Verantwortlichkeiten und Governance"
            gc_voraussetzung_3 = "Binden Sie Qualitätssicherung und Fachbereiche in die KI-gestützte Prüfung ein"
            gc_team_aspekt = "Ihre Organisationsstruktur ermöglicht systematische Skalierung erfolgreicher Piloten"

        return f"""<section class="section gamechanger">
  <h2>KI als Gamechanger für Ihr Geschäftsmodell</h2>

  <p>
    Für ein Unternehmen in der Branche <strong>{branche}</strong> mit der Größe
    <strong>{size_label}</strong> und dem Schwerpunkt <strong>{hauptleistung or "KI-gestützte Prozessoptimierung"}</strong>
    ergeben sich mehrere KI-Szenarien, die die Wertschöpfung in den kommenden Jahren spürbar verändern können.
    Die folgenden Vorschläge zeigen konkrete Ansatzpunkte, wie KI nicht nur einzelne Aufgaben beschleunigt,
    sondern grundlegende Veränderungen im Geschäftsmodell ermöglicht. {gc_team_aspekt}.
  </p>
  <p>
    Ein Gamechanger unterscheidet sich von einfachen Optimierungen dadurch, dass er das Potenzial hat,
    die Art und Weise, wie Sie arbeiten und Wert für Ihre Kund:innen schaffen, grundlegend zu verändern.
    Die folgenden drei Szenarien sind so gewählt, dass sie aufeinander aufbauen und schrittweise
    realisiert werden können – beginnend mit schnellen Erfolgen bis hin zu strategischen Transformationen.
  </p>

  <h3>Gamechanger 1: KI-gestützte Standardisierung und Automatisierung zentraler Kernprozesse</h3>

  <h4>Kernidee</h4>
  <p>
    Wiederkehrende Aufgaben in <strong>{hauptleistung or "Ihrem Kerngeschäft"}</strong> werden über
    KI-gestützte Vorlagen, Automatisierungen und strukturierte Entscheidungswege so standardisiert,
    dass Qualität und Geschwindigkeit deutlich steigen. Statt jede Aufgabe von Grund auf neu zu bearbeiten,
    nutzen Sie intelligente Vorlagen, die sich an den jeweiligen Kontext anpassen. Dies reduziert nicht nur
    den Zeitaufwand, sondern erhöht auch die Konsistenz Ihrer Ergebnisse erheblich.
  </p>

  <h4>Betroffene Wertschöpfung</h4>
  <p>
    Die Standardisierung wirkt sich auf mehrere Bereiche Ihrer Wertschöpfungskette aus: Erstellung von
    Dokumenten und Analysen, interne Abstimmungsprozesse, Kundendokumentation und Qualitätssicherung.
    In der Branche <strong>{branche}</strong> sind besonders Angebotserstellung, Projektdokumentation
    und wiederkehrende Berichte von dieser Automatisierung betroffen.
  </p>

  <h4>Erwarteter Nutzen</h4>
  <p>
    Weniger manuelle Routinearbeit, stabilere Ergebnisse und eine konsistente Kundenerfahrung – unabhängig
    von Tagesform oder Auslastung. Die Zeitersparnis kann je nach Prozess 20-40% betragen. Gleichzeitig
    sinkt die Fehlerquote, da standardisierte Abläufe weniger Raum für Flüchtigkeitsfehler lassen.
    Die gewonnene Zeit kann für wertschöpfende Tätigkeiten genutzt werden.
  </p>

  <h4>Voraussetzungen</h4>
  <p>
    Für die erfolgreiche Umsetzung benötigen Sie 5-10 typische Beispiele aus Ihrem Arbeitsalltag,
    definierte Qualitätskriterien und klare Regeln für Eingaben und Ausgaben. {gc_voraussetzung_1}.
    Beginnen Sie mit einem klar abgegrenzten Prozess, bevor Sie die Standardisierung ausweiten.
  </p>

  <h4>Erster Schritt in den nächsten 90 Tagen</h4>
  <p>
    Wählen Sie einen priorisierten Teilprozess aus und stabilisieren Sie ihn mit KI-Vorlagen und
    Review-Schritten als Mini-Pilot. Dokumentieren Sie die Ergebnisse und sammeln Sie Feedback,
    um den Prozess kontinuierlich zu verbessern.
  </p>

  <h3>Gamechanger 2: Aufbau eines KI-gestützten Wissenspools für Entscheidungen und Angebotserstellung</h3>

  <h4>Kernidee</h4>
  <p>
    Zentrale Informationen, Beispiele, Best Practices und interne Expertise werden KI-unterstützt
    gebündelt, sodass Recherchen, Angebotsprozesse oder Analysen deutlich schneller und konsistenter
    erfolgen. Statt Wissen in verschiedenen Dokumenten, E-Mails und Köpfen verstreut zu haben,
    schaffen Sie eine intelligente Wissensbasis, die auf Anfrage relevante Informationen liefert.
  </p>

  <h4>Betroffene Wertschöpfung</h4>
  <p>
    Dieser Gamechanger wirkt sich auf Angebotsentwicklung, strategische Planung, interne Abstimmungen
    und den Wissenstransfer aus. In der Branche <strong>{branche}</strong> profitieren besonders
    Kundenberatung, Projektakquise und die Entwicklung neuer Dienstleistungsangebote von einer
    strukturierten Wissensbasis.
  </p>

  <h4>Erwarteter Nutzen</h4>
  <p>
    Weniger Suchaufwand, deutliche Zeitersparnis bei der Angebotserstellung, bessere Entscheidungsqualität
    durch schnellen Zugriff auf relevante Erfahrungen und ein höherer Wiedererkennungswert für Kund:innen.
    Die Qualität Ihrer Arbeit steigt, weil Sie systematisch auf bewährte Ansätze zurückgreifen können,
    statt jedes Mal bei Null zu beginnen.
  </p>

  <h4>Voraussetzungen</h4>
  <p>
    Sie benötigen strukturierte Beispiele und interne Inhalte als Ausgangsbasis sowie kurze Regeln
    für Qualität und regelmäßige Aktualisierung. {gc_voraussetzung_2}. Die Wissensbasis sollte
    einfach zu pflegen sein, damit sie langfristig aktuell bleibt.
  </p>

  <h4>Erster Schritt in den nächsten 90 Tagen</h4>
  <p>
    Bündeln Sie 10-15 reale Inhalte (Angebote, Konzepte, Best Practices), erzeugen Sie erste
    KI-gestützte Zusammenfassungen und integrieren Sie diese als Wissensbasis in den Arbeitsalltag.
    Testen Sie die Nutzung bei konkreten Anfragen und optimieren Sie die Struktur basierend auf
    dem praktischen Nutzen.
  </p>

  <h3>Gamechanger 3: KI-basierte Qualitätssicherung und konsistente Kundenergebnisse</h3>

  <h4>Kernidee</h4>
  <p>
    Qualität, Präzision und Konsistenz werden über KI-gestützte Prüfmechanismen verbessert, die
    branchenspezifische Anforderungen berücksichtigen – etwa Tonalität, Struktur, Vollständigkeit,
    Risiken und sensible Inhalte. Die KI fungiert als zweite Prüfinstanz, die systematisch nach
    typischen Fehlern und Verbesserungsmöglichkeiten sucht.
  </p>

  <h4>Betroffene Wertschöpfung</h4>
  <p>
    Dieser Gamechanger wirkt sich auf Kundenkommunikation, inhaltliche Produktion, interne Reviews
    und den finalen Output aus. In der Branche <strong>{branche}</strong> ist konsistente Qualität
    besonders wichtig für Kundenvertrauen, Reputation und langfristige Geschäftsbeziehungen.
  </p>

  <h4>Erwarteter Nutzen</h4>
  <p>
    Weniger Fehler, weniger Korrekturschleifen und eine deutlich höhere Ersttrefferquote – besonders
    relevant bei Zeitdruck oder hoher Auslastung. Die Qualitätssicherung wird systematisiert und
    skaliert mit dem Arbeitsvolumen, ohne dass der Aufwand proportional steigt. Kundenreklamationen
    sinken und die Kundenzufriedenheit steigt messbar.
  </p>

  <h4>Voraussetzungen</h4>
  <p>
    Definieren Sie 5-7 klare Prüfkriterien, entwickeln Sie einheitliche Vorlagen und legen Sie eine
    Eskalationslogik für kritische Fälle fest. {gc_voraussetzung_3}. Die Prüfkriterien sollten
    branchenspezifisch und auf Ihre typischen Kundenanforderungen abgestimmt sein.
  </p>

  <h4>Erster Schritt in den nächsten 90 Tagen</h4>
  <p>
    Führen Sie eine KI-gestützte Mini-Checkliste ein und wenden Sie diese bei jedem Output an,
    bevor Ergebnisse intern oder extern genutzt werden. Sammeln Sie systematisch Feedback zu
    den gefundenen Verbesserungen und passen Sie die Checkliste kontinuierlich an.
  </p>

  <h3>Was diese Gamechanger gemeinsam haben</h3>
  <ul>
    <li>Sie bauen auf bestehenden Stärken von <strong>{hauptleistung or "Ihrem Kerngeschäft"}</strong>
        auf und verstärken diese gezielt mit KI-Unterstützung.</li>
    <li>Sie berücksichtigen die Ressourcen und Entscheidungswege eines <strong>{size_label}</strong>-Unternehmens
        und sind realistisch umsetzbar.</li>
    <li>Sie lassen sich mit überschaubarem Risiko pilotieren und bei Erfolg schrittweise skalieren.</li>
    <li>Sie erzeugen messbare Ergebnisse, die den ROI der KI-Investition nachweisbar machen.</li>
    <li>Sie sind miteinander verzahnt und verstärken sich gegenseitig bei paralleler Umsetzung.</li>
  </ul>

  <h3>Strategische Einordnung</h3>
  <p>
    Die drei Gamechanger bilden zusammen eine Transformationsstrategie: Gamechanger 1 schafft die
    operative Grundlage durch Standardisierung, Gamechanger 2 baut das Wissenskapital auf und
    Gamechanger 3 sichert die Qualität ab. Diese Kombination ermöglicht es Ihrem Unternehmen,
    von ersten KI-Schritten hin zu nachhaltiger, skalierbarer Wertschöpfung zu kommen.
  </p>
  <p>
    Die Umsetzung sollte priorisiert erfolgen: Beginnen Sie mit dem Gamechanger, der den größten
    unmittelbaren Nutzen für Ihr Tagesgeschäft verspricht. Typischerweise ist dies Gamechanger 1
    oder 3, da beide schnelle Ergebnisse liefern. Gamechanger 2 entfaltet seinen vollen Nutzen
    oft erst nach einigen Monaten, legt aber das Fundament für langfristige Wettbewerbsvorteile.
  </p>

  <p class="small muted">
    Die Gamechanger dienen als strategische Leitplanken und unterstützen Ihr Unternehmen dabei,
    von ersten KI-Schritten hin zu nachhaltiger, skalierbarer Wertschöpfung zu kommen. Die
    konkreten Maßnahmen sollten auf Basis der 90-Tage-Roadmap und der 12-Monats-Strategie
    weiter detailliert werden.
  </p>
</section>"""

    # SPRINT G2.5: Helper for formatting ROI/Payback values
    def _fmt_num(val, decimals=1):
        if val is None or val == "—":
            return "—"
        try:
            return f"{float(val):.{decimals}f}"
        except (ValueError, TypeError):
            return str(val)

    _payback_fmt = _fmt_num(briefing.get("PAYBACK_MONTHS"), 1)
    _roi_fmt = _fmt_num(briefing.get("ROI_12M"), 0)

    # Statische Fallbacks (Quick Wins UNVERÄNDERT)
    fallbacks = {
        "quick_wins": f"""<ul>
<li><strong>E-Mail-Entwürfe automatisieren:</strong> Automatische Vorschläge für Standard-Antworten und Textbausteine. <em>Ersparnis: 20 h/Monat</em></li>
<li><strong>Meeting-Protokolle mit KI:</strong> Automatische Transkription und Zusammenfassung von Besprechungen. <em>Ersparnis: 15 h/Monat</em></li>
<li><strong>Dokumenten-Recherche beschleunigen:</strong> Semantische Suche in Ihrer Wissensdatenbank statt manuelles Durchsuchen. <em>Ersparnis: 12 h/Monat</em></li>
<li><strong>Social Media Posts generieren:</strong> KI-gestützte Content-Vorschläge für LinkedIn, Instagram und andere Kanäle. <em>Ersparnis: 8 h/Monat</em></li>
</ul>
<p class="small muted">Angepasst an {branche} · {size_label}</p>""",
        "business_case": f"""<div class="business-case-fallback">
  <h3>Investition und erwarteter Nutzen</h3>
  <p>
    Der Einsatz von KI in der Branche <strong>{branche}</strong> erfordert eine realistische
    Einschätzung der Aufwände und des erwarteten Nutzens. Die Investition umfasst sowohl
    einmalige Einführungskosten (CAPEX) als auch laufende Betriebskosten (OPEX).
  </p>
  <table class="table">
    <tr>
      <td><strong>Einführungskosten (CAPEX)</strong></td>
      <td class="text-right">{briefing.get("CAPEX_REALISTISCH_EUR", "—")} €</td>
    </tr>
    <tr>
      <td><strong>Laufende Kosten (OPEX)</strong></td>
      <td class="text-right">{briefing.get("OPEX_REALISTISCH_EUR", "—")} €/Monat</td>
    </tr>
    <tr>
      <td><strong>Erwartete Einsparung</strong></td>
      <td class="text-right">{briefing.get("EINSPARUNG_MONAT_EUR", "—")} €/Monat</td>
    </tr>
    <tr>
      <td><strong>Amortisation</strong></td>
      <td class="text-right">{_payback_fmt} Monate</td>
    </tr>
    <tr>
      <td><strong>ROI nach 12 Monaten</strong></td>
      <td class="text-right">{_roi_fmt} %</td>
    </tr>
  </table>
  <p>
    Die Amortisationszeit gibt an, nach wie vielen Monaten sich die Anfangsinvestition
    durch die laufenden Einsparungen rechnet. Der Return on Investment (ROI) zeigt die
    Gesamtrendite nach einem Jahr in Relation zur Investition.
  </p>
</div>""",
        "gamechanger": f"""<div class="gamechanger-fallback">
  <h3>KI als strategischer Hebel</h3>
  <p>
    Für ein Unternehmen in der Branche <strong>{branche}</strong> ({size_label})
    eröffnet der Einsatz von KI mehrere strategische Handlungsfelder, die die
    Wettbewerbsfähigkeit nachhaltig stärken können:
  </p>
  <ol>
    <li>
      <strong>Prozessautomatisierung und Effizienzsteigerung:</strong>
      Wiederholbare Aufgaben können durch KI-gestützte Workflows beschleunigt werden.
      Dies reduziert manuelle Arbeitszeit und ermöglicht den Fokus auf wertschöpfende Tätigkeiten.
    </li>
    <li>
      <strong>Datengetriebene Entscheidungsfindung:</strong>
      KI-Analysewerkzeuge helfen dabei, Muster in Geschäftsdaten zu erkennen und
      fundierte strategische Entscheidungen zu treffen. Dies umfasst Kundensegmentierung,
      Nachfrageprognosen und Marktanalysen.
    </li>
    <li>
      <strong>Qualitätssteigerung und Personalisierung:</strong>
      Durch den Einsatz von KI können Produkte und Dienstleistungen besser auf individuelle
      Kundenbedürfnisse zugeschnitten werden. Dies erhöht die Kundenzufriedenheit und
      langfristige Kundenbindung.
    </li>
  </ol>
  <p class="small muted">
    Die konkreten Umsetzungsschritte hängen von den spezifischen Geschäftsprozessen,
    vorhandenen Daten und strategischen Prioritäten ab.
  </p>
</div>""",
        # SPRINT G2.3/G2.4: Fallback für tools_empfehlungen (size-aware + short labels)
        # SPRINT G6: Erweitert auf ~150+ Wörter, size-aware Struktur
        "tools_empfehlungen": f"""<div class="tools-empfehlungen-fallback">
  <h3>Empfohlener KI-Stack für {branche}</h3>
  <p class="context-label"><em>{branch_core_label}</em></p>

  <h4>1. Fundament & Basis</h4>
  <ul>
    <li><strong>KI-Assistent:</strong> Texterstellung, E-Mail-Entwürfe, Content-Generierung – Einstieg ab 20 €/Monat.</li>
    <li><strong>Wissensspeicher:</strong> Zentrale Ablage für Templates, Prompts und Best Practices.</li>
    <li><strong>Aufgabenverwaltung:</strong> Planung und Koordination von KI-gestützten Workflows.</li>
  </ul>

  <h4>2. Kernprozess-Tools für {offering_label or hauptleistung or branche}</h4>
  <ul>
    <li><strong>Formular-Tool:</strong> Strukturierte Erfassung von Kundendaten und Feedback.</li>
    <li><strong>Auswertungs-Tool:</strong> KI-gestützte Analyse und Report-Erstellung.</li>
    <li><strong>Automatisierung:</strong> Make.com oder Zapier für wiederkehrende Abläufe (ab 9 €/Monat).</li>
  </ul>

  {"" if size_group == "solo" else '''<h4>3. Governance & Qualität</h4>
  <ul>
    <li><strong>Richtlinien:</strong> Kurze, schriftliche Regeln für den KI-Einsatz.</li>
    <li><strong>Dokumentation:</strong> Übersicht welche Tools wofür eingesetzt werden.</li>
    <li><strong>Qualitätskontrolle:</strong> Review-Prozesse für wichtige KI-Ergebnisse.</li>
  </ul>'''}

  <p>
    Für <strong>{size_label}</strong> empfiehlt sich ein schrittweiser Ausbau: Erst Fundament,
    dann Kernprozess-Tools, schließlich Governance. Details zur Einführung → siehe Roadmap.
  </p>
</div>""",
        # SPRINT G2.3/G2.4: Fallback für strategie_governance (size-aware + short labels)
        "strategie_governance": f"""<div class="strategie-governance-fallback">
  <h3>KI-Strategie und Governance</h3>
  <p class="context-label"><em>{branch_core_label}</em></p>
  <p>
    Eine erfolgreiche KI-Einführung erfordert klare Verantwortlichkeiten und Richtlinien:
  </p>
  <ul>
    <li><strong>Datenschutz:</strong> Keine sensiblen Kundendaten in öffentliche KI-Tools eingeben.</li>
    <li><strong>Qualitätskontrolle:</strong> KI-generierte Inhalte vor Veröffentlichung prüfen.</li>
    <li><strong>Dokumentation:</strong> Welche Tools werden wofür eingesetzt? Wer ist verantwortlich?</li>
    <li><strong>Schulung:</strong> Grundlegendes KI-Wissen für alle Beteiligten sicherstellen.</li>
  </ul>
  <p>
    Für <strong>{size_label}</strong> gilt: Starten Sie pragmatisch mit einem Pilotprojekt
    und dokumentieren Sie Erfolge und Learnings.
  </p>
</div>""",
    }

    # SPRINT G2.3/G2.4: Default-Fallback – Meta-Text-frei, mit Kurzlabels
    result = fallbacks.get(
        section_key,
        f"""<div class="section-content">
  <p class="context-label"><em>{branch_core_label}</em></p>
  <p>KI-Einsatz für <strong>{size_label or "Ihr Unternehmen"}</strong> bietet Potenziale in Prozessautomatisierung, Dokumentenverarbeitung und Entscheidungsunterstützung.</p>
  <p>Konkrete Empfehlungen richten sich nach Ihren individuellen Prioritäten und vorhandenen Ressourcen.</p>
</div>"""
    )

    # PE-4 FIX: Apply governance simplification to fallback content
    # Solo users should not see team/department terminology
    from services.report_validator import filter_size_inappropriate_content
    return filter_size_inappropriate_content(result, size_label)

# -------------------- 🎯 NEW: Use prompt system instead of hardcoded prompts ----------------
# 🎯 STATIC SECTIONS – diese nutzen IMMER Fallback, kein GPT-Call
# Grund: Hohe Konsistenz, keine LLM-Variabilität, schneller
STATIC_SECTIONS = {
    "business_roi",
    "business_costs",
    "ai_act_summary",
}

def _generate_content_section(section_name: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    """🎯 UPDATED: Uses prompt_loader system mit Variable-Interpolation und Förder-Kontext."""
    # Get error gate from thread-local storage (set by parent analyze_briefing)
    error_gate = get_error_gate()

    if not ENABLE_LLM_CONTENT:
        return f"<p><em>[{section_name} – LLM disabled]</em></p>"

    # 🎯 STATIC SECTIONS: Direkt Fallback nutzen, kein GPT-Call
    if section_name in STATIC_SECTIONS:
        log.info("📌 Using static fallback for %s (no GPT call)", section_name)
        return _get_fallback_content(section_name, briefing, scores)

    # Map section names to prompt files (without _de suffix for load_prompt)
    prompt_map = {
        # Core sections
        "executive_summary": "executive_summary",
        "quick_wins": "quick_wins",
        "roadmap": "roadmap_90d",  # 90-Tage-Roadmap
        "roadmap_12m": "roadmap_12m",
        "business_roi": "costs_overview",
        "business_costs": "costs_overview",
        "business_case": "business_case",
        "data_readiness": "data_readiness",
        "org_change": "org_change",
        "risks": "risks",
        "gamechanger": "gamechanger",
        "recommendations": "recommendations",
        "reifegrad_sowhat": "executive_summary",  # fallback auf Exec-Summary-Prompt
        # Aktivierte Zusatz-Prompts
        "ai_act_summary": "ai_act_summary",
        "strategie_governance": "strategie_governance",
        "wettbewerb_benchmark": "wettbewerb_benchmark",
        "technologie_prozesse": "technologie_prozesse",
        "unternehmensprofil_markt": "unternehmensprofil_markt",
        "tools_empfehlungen": "tools_empfehlungen",
        "foerderpotenzial": "foerderpotenzial",
        "transparency_box": "transparency_box",
        "ki_aktivitaeten_ziele": "ki_aktivitaeten_ziele",
        # Neue Sektionen (Sprint 2025)
        "monetarisierung": "monetarisierung",
        "ki_skillplan": "ki_skillplan",
        "templates_start": "templates_start",
        # Neue Sektionen (Sprint 2025 - Phase 2)
        "roi_tracking": "roi_tracking",
        "ai_policy_mini": "ai_policy_mini",
        "kickoff_vorlage": "kickoff_vorlage",
        "prompt_framework": "prompt_framework",
    }
    
    prompt_key = prompt_map.get(section_name)

    # =========================================================================
    # Sprint G1.2 FIX: LLM-Parameter IMMER VOR dem try-Block definieren
    # Verhindert "cannot access local variable 'llm'" Fehler im Legacy-Fallback
    # =========================================================================
    llm = _llm_params_for(section_name)

    # Prompt-System verwenden, wenn aktiv und Prompt vorhanden
    if USE_PROMPT_SYSTEM and prompt_key and _prompt_enhancer:
        try:
            # TEIL 3.1.4.8/3.1.4.9/3.1.4.11: Locale normalization for prompt routing
            # Note: Authoritative lang is set upstream from br.lang (3.1.4.9)
            # This block is a safety net ensuring consistent lang/LANG/sprache fields
            if isinstance(briefing, dict):
                lang_raw = (
                    briefing.get("lang")
                    or briefing.get("LANG")
                    or briefing.get("sprache")
                    or "de"
                )
                lang_norm = str(lang_raw).lower().strip()
                prompt_lang = "en" if lang_norm.startswith("en") else "de"

                briefing["lang"] = prompt_lang
                briefing["LANG"] = prompt_lang
                briefing["sprache"] = prompt_lang

                # 3.1.4.11: Debug trace for locale normalization
                log.debug("[locale] section=%s lang_raw=%s → prompt_lang=%s", section_name, lang_raw, prompt_lang)

            # 1. Prompt mit Kontext (Branche/Größe) anreichern
            enhanced_prompt = _prompt_enhancer.enhance_prompt(prompt_key, briefing)
            
            # 2. Variablen für Interpolation bauen
            vars_dict = _build_prompt_vars(briefing, scores)
            
            # 3. Interpolation
            from services.prompt_loader import _interpolate
            prompt_text = _interpolate(enhanced_prompt, vars_dict)

            # 3b. Spezieller Förder-Kontext aus foerderprogramme.md
            # v4.15.0: Skip for English reports (Germany-specific funding)
            briefing_lang = briefing.get("lang", "de") if isinstance(briefing, dict) else "de"
            if section_name == "foerderpotenzial" and briefing_lang != "en":
                try:
                    foerder_prog_text = load_prompt("foerderprogramme", lang=briefing_lang, vars_dict=vars_dict)
                except Exception:
                    foerder_prog_text = None
                if foerder_prog_text:
                    prompt_text = (
                        f"{prompt_text}\n\n"
                        "-----\n\n"
                        "Zusätzlicher Kontext aus der Förder-Übersicht (foerderprogramme.md):\n"
                        "Nutze diese Informationen, um die Förderlogik für dieses Unternehmen "
                        "(Bund/Land/KMU) plausibel und aktuell einzuordnen. Fasse und priorisiere – "
                        "NICHT einfach 1:1 als Liste kopieren.\n\n"
                        f"{foerder_prog_text}"
                    )
            
            if not isinstance(prompt_text, str):
                log.warning(
                    "⚠️ Enhanced prompt %s returned non-string: %s, falling back",
                    prompt_key,
                    type(prompt_text),
                )
                raise ValueError("Non-string prompt")
            
            log.info("✅ Using enhanced prompt for %s (with context)", section_name)

            # 4. LLM-Aufruf mit bereits definierten Parametern (llm defined before try block)
            result = _call_llm_for_section(
                section_key=section_name,
                prompt=prompt_text,
                system_prompt="Du bist ein Senior-KI-Berater. Antworte nur mit validem HTML.",
                temperature=llm["temperature"],
                max_tokens=llm["max_tokens"],
                model=llm["model"],
            ) or ""

            
            result = _clean_html(result)
            if _needs_repair(result):
                result = _repair_html(section_name, result)
            
            # 🎯 PLATZHALTER-FIX: Entferne Developer-Wörter die GPT manchmal ausgibt
            if result:
                developer_words = ["Platzhalter", "TODO", "Beispieltext", "Content wird erstellt", "XXX"]
                for word in developer_words:
                    result = result.replace(word, "")

            # =========================================================================
            # N4.6 Zero-Leak Policy: Detect and regenerate if leaks found
            # =========================================================================
            detected_leaks = _detect_leak_phrases(result)
            if detected_leaks:
                log.warning(
                    "[N4.6] 🚨 Leak phrases detected in %s: %s – regenerating with strict mode",
                    section_name,
                    detected_leaks[:3],  # Log first 3 for brevity
                )
                # Try regeneration with strict anti-leak directive
                regenerated = _regenerate_without_leaks(section_name, prompt_text, llm)

                # Check if regenerated content is still leaky
                regenerated_leaks = _detect_leak_phrases(regenerated)
                if not regenerated_leaks and regenerated:
                    log.info("[N4.6] ✅ Regeneration successful – no leaks in %s", section_name)
                    result = regenerated
                else:
                    # PLATIN+++ v5.4: If still leaky, use PLATIN fallback instead of stripping
                    # Rationale: Stripped content is often broken/incoherent - full fallback is better
                    log.warning(
                        "[N4.6] ⚠️ Regeneration still has leaks in %s – using PLATIN fallback (not stripping)",
                        section_name
                    )
                    fallback_content = _get_fallback_content(section_name, briefing, scores)
                    if fallback_content:
                        log.info("[N4.6] ✅ PLATIN fallback used for %s", section_name)
                        result = fallback_content
                    else:
                        # Last resort: strip only if no fallback available
                        log.warning("[N4.6] No fallback for %s, stripping leaks as last resort", section_name)
                        for leak in detected_leaks:
                            import re as _re_leak
                            pattern = _re_leak.compile(
                                r'[^.!?]*' + _re_leak.escape(leak) + r'[^.!?]*[.!?]',
                                _re_leak.IGNORECASE
                            )
                            result = pattern.sub('', result)

            # PLATIN+ Minimalumfang prüfen (dynamisch nach Section-Typ)
            # WICHTIG: Werte sind jetzt in WÖRTERN, nicht Zeichen!
            # Für kritische Sections höhere Schwelle, damit size-aware Fallbacks greifen
            # HINWEIS: Prompt fordert 900+ Wörter für roadmap_12m, aber wir prüfen
            # konservativ auf 800 Wörter – so verschwinden False Negatives bei Zähldifferenzen.
            platin_min_words = {
                "roadmap": 100,               # ~600 Zeichen
                "roadmap_90d": 100,           # ~600 Zeichen
                "roadmap_12m": 800,           # PLATIN+: Prompt fordert 900, prüfen auf 800 (Sicherheitsmarge)
                "foerderpotenzial": 900,      # PLATIN+: 900 Wörter
                "org_change": 100,            # ~600 Zeichen
                "strategie_governance": 120,  # ~700 Zeichen
                "risks": 800,                 # PLATIN+: 800 Wörter
                "recommendations": 800,       # PLATIN+: 800 Wörter
                "gamechanger": 700,           # PLATIN+: 700 Wörter
                "unternehmensprofil_markt": 600,  # N4.6: Added for 2-pass expand
            }
            min_words = platin_min_words.get(section_name, 10)

            # Wörter zählen statt Zeichen (PLATIN+ Standard)
            import re as _re
            text_only = _re.sub(r"<[^>]+>", "", result or "").strip()
            word_count = len(text_only.split()) if text_only else 0

            # =========================================================================
            # N4.6 2-Pass Expand: If content too short but section is expandable
            # =========================================================================
            if result and word_count < min_words and section_name in EXPAND_ELIGIBLE_SECTIONS:
                log.info(
                    "[N4.6] 📏 Content for %s too short (%d/%d words) – attempting 2-pass expand",
                    section_name,
                    word_count,
                    min_words,
                )
                expand_prompt = f"""
Der folgende Inhalt ist zu kurz und muss erweitert werden.
Ziel-Wortanzahl: mindestens {min_words} Wörter (aktuell: {word_count}).

REGELN FÜR ERWEITERUNG:
- Behalte ALLE bestehenden Informationen und Strukturen
- Füge MEHR Details, Beispiele und Erklärungen hinzu
- Vertiefe jeden Punkt mit konkreten Maßnahmen
- Verwende die gleiche HTML-Struktur
- KEINE Assistenten-Sprache, KEINE Fragen an den Leser

Bestehender Inhalt zum Erweitern:
{result}

Gib den erweiterten HTML-Inhalt aus (mindestens {min_words} Wörter):
"""
                expanded = _call_llm_for_section(
                    section_key=f"{section_name}_expand",
                    prompt=expand_prompt,
                    system_prompt="Du bist ein Senior-KI-Berater. Erweitere den Inhalt mit mehr Details. Nur valides HTML.",
                    temperature=llm["temperature"],
                    max_tokens=llm["max_tokens"] + 500,  # Allow more tokens for expansion
                    model=llm["model"],
                ) or ""

                expanded = _clean_html(expanded)
                if _needs_repair(expanded):
                    expanded = _repair_html(section_name, expanded)

                # Check if expansion was successful
                expanded_text = _re.sub(r"<[^>]+>", "", expanded or "").strip()
                expanded_word_count = len(expanded_text.split()) if expanded_text else 0

                if expanded_word_count >= min_words:
                    log.info(
                        "[N4.6] ✅ 2-pass expand successful for %s: %d -> %d words",
                        section_name,
                        word_count,
                        expanded_word_count,
                    )
                    result = expanded
                    word_count = expanded_word_count
                else:
                    log.warning(
                        "[N4.6] ⚠️ 2-pass expand insufficient for %s: %d words (need %d)",
                        section_name,
                        expanded_word_count,
                        min_words,
                    )

            if not result or word_count < min_words:
                log.info(
                    "ℹ️ LLM content for %s too short (%d words < %d min) – using PLATIN fallback.",
                    section_name,
                    word_count,
                    min_words,
                )
                # Track fallback usage in error gate
                if error_gate:
                    error_gate.increment_fallback()
                return _get_fallback_content(section_name, briefing, scores)

            return result

        except FileNotFoundError as e:
            log.warning(
                "⚠️ Prompt file not found for %s: %s - using legacy", prompt_key, e
            )
            # Track prompt failure in error gate
            if error_gate:
                error_gate.add_prompt_failure(str(prompt_key), f"File not found: {e}")
        except Exception as e:
            log.error(
                "❌ Error loading/using prompt for %s: %s - using legacy", section_name, e
            )
            # Track general prompt failure
            if error_gate:
                error_gate.add_prompt_failure(section_name, str(e))
    
    # ---------------- Fallback: Legacy-hardcoded Prompts ----------------
    branche = briefing.get("branche", "Unternehmen")
    hauptleistung = briefing.get("hauptleistung", "")
    unternehmensgroesse = briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse") or ""
    bundesland = briefing.get("BUNDESLAND_LABEL") or briefing.get("bundesland") or ""
    ki_ziele = briefing.get("ki_ziele", [])
    ki_projekte = briefing.get("ki_projekte", "")
    vision = briefing.get("vision_3_jahre", "")
    trainings_liste = briefing.get("trainings_interessen", [])
    overall = scores.get("overall", 0)
    governance = scores.get("governance", 0)
    security = scores.get("security", 0)
    value = scores.get("value", 0)
    enablement = scores.get("enablement", 0)
    context = (
        f"Branche: {branche}; Größe: {unternehmensgroesse}; Bundesland: {bundesland}; "
        f"Hauptleistung/-produkt: {hauptleistung}."
    )
    tone = "Sprache: neutral, dritte Person; keine Wir/Ich-Formulierungen."
    only_html = "Antworte ausschließlich mit validem HTML (ohne Markdown-Fences)."
    prompts = {
        "executive_summary": f"""Erstelle eine prägnante Executive Summary. {context}
KI-Ziele: {', '.join(ki_ziele) if ki_ziele else 'nicht definiert'} • Vision: {vision}
KI-Reifegrad: Gesamt {overall}/100 • Governance {governance}/100 • Sicherheit {security}/100 • Nutzen {value}/100 • Befähigung {enablement}/100
{tone} {only_html} Verwende nur <p>-Absätze.""",
        "quick_wins": f"""Liste 4–6 **konkrete Quick Wins** (0–90 Tage) für {context}
Jeder Quick Win: Titel, 1–2 Sätze Nutzen, realistische **Ersparnis: … h/Monat**.
Bezug: Hauptleistung {hauptleistung}; Projekte: {ki_projekte or 'keine'}; Trainingsinteressen: {', '.join(trainings_liste) if trainings_liste else '—'}.
{tone} {only_html} Liefere exakt eine <ul>-Liste mit <li>-Einträgen im Format:
<li><strong>Titel:</strong> Beschreibung. <em>Ersparnis: 5 h/Monat</em></li>""",
        "roadmap": f"""Erstelle eine **90-Tage-Roadmap** (0–30 Test; 31–60 Pilot; 61–90 Rollout) mit Bezug auf {context}
{tone} {only_html} Pro Phase 3–5 Meilensteine. Format: <h4>Phase …</h4> + <ul>…</ul>.""",
        "roadmap_12m": f"""Erstelle eine **12-Monats-Roadmap** in 3 Phasen (0–3/3–6/6–12) für {context}.
{tone} {only_html} Format: <div class="roadmap"><div class="roadmap-phase">…</div></div>. """,
        "business_roi": f"""Erstelle eine **ROI & Payback**-Tabelle (Jahr 1) für {context}. {tone} {only_html}
Format: <table> mit 2 Spalten (Kennzahl, Wert).""",
        "business_costs": f"""Erstelle eine **Kostenübersicht Jahr 1** für {context}. {tone} {only_html}
Format: <table> mit 2 Spalten (Position, Betrag).""",
        "recommendations": f"""Formuliere 5–7 **Handlungsempfehlungen** mit Priorität [H/M/N] und Zeitrahmen (30/60/90). Kontext: {context}
{tone} {only_html} Format: <ol><li><strong>[H]</strong> Maßnahme — <em>60 Tage</em></li></ol>.""",
        "risks": f"""Erstelle eine **Risikomatrix** (5–7 Risiken) für {context} + EU-AI-Act Pflichtenliste.
{tone} {only_html} Format: <table> mit <thead>/<tbody>. """,
        "gamechanger": f"""Skizziere einen **Gamechanger-Use Case** für {context}. (Idee: 3–4 Sätze; 3 Vorteile; 3 Schritte)
{tone} {only_html} Verwende <h4>, <p>, <ul>. """,
        "data_readiness": f"""Erstelle eine kompakte **Dateninventar & -Qualität**-Übersicht für {context}.
{tone} {only_html} Format: <div class="data-readiness"><h4>…</h4><ul>…</ul></div>. """,
        "org_change": f"""Beschreibe **Organisation & Change** (Governance-Rollen, Skill-Programm, Kommunikation) für {context}.
{tone} {only_html} Format: <div class="org-change">…</div>. """,
        "business_case": f"""Erstelle einen kompakten **Business Case (detailliert)** für {context} – Annahmen, Nutzen (J1), Kosten (CapEx/OpEx), Payback, ROI, Sensitivität.
{tone} {only_html} Format: <div class="business-case"> … </div>. """,
        "reifegrad_sowhat": f"""Erkläre kurz: **Was heißt der Reifegrad konkret?** Kontext: {context}
Gesamt {overall}/100 • Governance {governance}/100 • Sicherheit {security}/100 • Nutzen {value}/100 • Befähigung {enablement}/100.
{tone} {only_html} Gib 4–6 Bullet-Points (<ul>) aus.""",
    }
    
    out = _call_llm_for_section(
        section_key=section_name,
        prompt=prompts.get(section_name, ""),
        system_prompt="Du bist ein Senior-KI-Berater. Antworte nur mit validem HTML.",
        temperature=llm["temperature"],
        max_tokens=llm["max_tokens"],
        model=llm["model"],
    ) or ""
    out = _clean_html(out)
    if _needs_repair(out):
        out = _repair_html(section_name, out)
    
    # 🎯 PLATZHALTER-FIX: Entferne Developer-Wörter die GPT manchmal ausgibt
    if out:
        developer_words = ["Platzhalter", "TODO", "Beispieltext", "Content wird erstellt", "XXX"]
        for word in developer_words:
            out = out.replace(word, "")
    
    # Fallback wenn GPT wirklich gar nichts bringt
    if not out or len(out.strip()) < 50:
        # Track fallback usage in error gate
        if error_gate:
            error_gate.increment_fallback()
        return _get_fallback_content(section_name, briefing, scores)

    return out


def _one_liner(title: str, section_html: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    base = f'Erzeuge einen prägnanten One‑liner unter der H2‑Überschrift "{title}". Formel: "Kernaussage; Konsequenz → nächster Schritt". Nur 1 Zeile.'
    text = _call_llm_for_section(
        section_key="one_liner",
        prompt=base + "\n---\n" + re.sub(r"<[^>]+>", " ", section_html)[:1800],
        system_prompt="Du formulierst prägnante One‑liner auf Deutsch.",
        temperature=0.1,
        max_tokens=80
    )
    return (text or "").strip()

def _split_li_list_to_columns(html_list: str) -> Tuple[str, str]:
    if not html_list: return "<ul></ul>", "<ul></ul>"
    items = re.findall(r"<li[\s>].*?</li>", html_list, flags=re.DOTALL | re.IGNORECASE)
    if not items:
        lines = [ln.strip() for ln in re.split(r"<br\s*/?>|\n", html_list) if ln.strip()]
        items = [f"<li>{ln}</li>" for ln in lines]
    mid = (len(items) + 1) // 2
    return "<ul>" + "".join(items[:mid]) + "</ul>", "<ul>" + "".join(items[mid:]) + "</ul>"

# -------------------- AI Act ----------------
# _try_read is now an alias for _read_file_with_fallback (defined above)

def _md_to_simple_html(md: str) -> str:
    if not md: return ""
    out: List[str] = []; in_ul = False
    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            if in_ul: out.append("</ul>"); in_ul = False
            continue
        if line.startswith("!["):
            continue
        if re.match(r"^\[\d+\]:\s*https?://", line):
            continue
        if line.startswith("#### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h4>{html.escape(line[5:].strip())}</h4>")
            continue
        if line.startswith("### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h3>{html.escape(line[4:].strip())}</h3>"); continue
        if line.startswith(("* ", "- ")):
            if not in_ul: in_ul = True; out.append("<ul>")
            out.append(f"<li>{html.escape(line[2:].strip())}</li>"); continue
        if in_ul: out.append("</ul>"); in_ul = False
        out.append(f"<p>{html.escape(line)}</p>")
    if in_ul: out.append("</ul>")
    return "\n".join(out)

def _build_ai_act_blocks() -> Dict[str, str]:
    if not ENABLE_AI_ACT_SECTION: return {}
    text = _try_read(AI_ACT_INFO_PATH) or ""
    html_block = _md_to_simple_html(text) if text else ("<h3>Wesentliche Eckdaten</h3>"
        "<ul><li>Gestaffelte Anwendung ab 2025; Kernpflichten 2025–2027.</li>"
        "<li>Frühzeitige Vorbereitung: Risiko- & Governance-Prozesse, Dokumentation, Monitoring.</li></ul>")
    cta = ('<div class="callout">'
           "<strong>Auf Wunsch:</strong> Tabellarische Übersicht der Termine/Fristen – Phase "
           f"<strong>{html.escape(AI_ACT_PHASE_LABEL)}</strong> – inkl. Verantwortlichkeiten und Checkpoints."
           "</div>")
    packages = ('<table class="table">'
                "<thead><tr><th>Paket</th><th>Umfang</th><th>Ergebnisse</th></tr></thead><tbody>"
                "<tr><td><strong>Lite: Tabellen‑Kit</strong></td>"
                "<td>Termin-/Fristen‑Tabelle (2025–2027) + 10–15 Checkpoints.</td>"
                "<td>PDF/CSV, kurze Einordnung pro Zeile.</td></tr>"
                "<tr><td><strong>Pro: Compliance‑Kit</strong></td>"
                "<td>Lite + Vorlagen (Risikomanagement, Logging, Monitoring) + 60‑Tage‑Plan.</td>"
                "<td>Dokupaket, editierbar.</td></tr>"
                "<tr><td><strong>Max: Audit‑Ready</strong></td>"
                "<td>Pro + Abgleich mit Prozessen, Nachweis‑Mapping, Q&A.</td>"
                "<td>Audit‑Map + Meilensteine.</td></tr>"
                "</tbody></table>")
    return {"AI_ACT_SUMMARY_HTML": html_block, "AI_ACT_TABLE_OFFER_HTML": cta, "AI_ACT_ADDON_PACKAGES_HTML": packages, "ai_act_phase_label": AI_ACT_PHASE_LABEL}

# -------------------- Mail & helpers ----------------
def _mask_email(addr: Optional[str]) -> str:
    if not addr or not DBG_MASK_EMAILS: return addr or ""
    try:
        name, domain = addr.split("@", 1)
        return f"{name[:3]}***@{domain}" if len(name) > 3 else f"{name}***@{domain}"
    except Exception:
        return "***"

def _admin_recipients() -> List[str]:
    emails: List[str] = []
    for raw in (os.getenv("ADMIN_EMAILS", ""),
                os.getenv("REPORT_ADMIN_EMAIL", ""),
                os.getenv("ADMIN_NOTIFY_EMAIL", "")):
        if raw: emails.extend([e.strip() for e in raw.split(",") if e.strip()])
    return list(dict.fromkeys(emails))

def _determine_user_email(db: Session, briefing: Briefing, override: Optional[str]) -> Optional[str]:
    if override: return override
    if getattr(briefing, "user_id", None):
        u = db.get(User, briefing.user_id)
        if u and getattr(u, "email", None):
            email = getattr(u, "email", None)
            return str(email) if email else None
    answers = getattr(briefing, "answers", None) or {}
    email_value = answers.get("email") or answers.get("kontakt_email")
    return str(email_value) if email_value else None

def _version_major_minor(v: str) -> str:
    m = re.match(r"^\s*(\d+)\.(\d+)", v or ""); return f"{m.group(1)}.{m.group(2)}" if m else "1.0"

def _build_watermark_text(report_id: str, version_mm: str) -> str:
    return f"Trusted KI‑Check · Report‑ID: {report_id} · v{version_mm}"

def _derive_kundencode(answers: Dict[str, Any], user_email: str) -> str:
    raw = ""
    if user_email and "@" in user_email:
        raw = user_email.split("@", 1)[-1].split(".")[0]
    code = re.sub(r"[^A-Za-z0-9]", "", (raw or "KND").upper())
    return code[:3] or "KND"

def _theme_vars_for_branch(branch_label: str) -> str:
    b = (branch_label or "").lower()
    brand, weak, accent = "#2563eb", "#dbeafe", "#1e3a5f"
    if "it" in b or "software" in b:
        brand, weak, accent = "#1d4ed8", "#c7d2fe", "#16327a"
    elif "marketing" in b or "werbung" in b:
        brand, weak, accent = "#0ea5e9", "#bae6fd", "#0c4a6e"
    elif "industrie" in b or "produktion" in b:
        brand, weak, accent = "#1e40af", "#c7d2fe", "#112a63"
    elif "verwaltung" in b:
        brand, weak, accent = "#1e3a8a", "#c7d2fe", "#0f2c5a"
    return f"<style>:root{{--c-brand:{brand};--c-brand-weak:{weak};--c-accent:{accent};}}</style>"

def _build_freetext_snippets_html(ans: Dict[str, Any]) -> str:
    keys = [
        ("hauptleistung", "Hauptleistung/Produkt"),
        ("ki_projekte", "Laufende/geplante KI‑Projekte"),
        ("zeitersparnis_prioritaet", "Zeitersparnis‑Priorität"),
        ("geschaeftsmodell_evolution", "Geschäftsmodell‑Idee"),
        ("vision_3_jahre", "Vision 3 Jahre"),
        ("strategische_ziele", "Strategische Ziele"),
    ]
    items: list[str] = []
    for k, label in keys:
        val = (ans.get(k) or "").strip()
        if val:
            items.append(f"<li><strong>{html.escape(label)}:</strong> {html.escape(val)}</li>")
    if not items:
        return ""
    title = "Ihre Freitext‑Eingaben (Kurzüberblick)"
    return (
        "<section class='fb-section'>"
        "<div class='fb-head'><span class='fb-step'>F</span>"
        f"<h3 class='fb-title'>{html.escape(title)}</h3></div>"
        "<ul>" + "".join(items) + "</ul>"
        "</section>"
    )
# -------------------- 🎯 UPDATED: Main composer with prompt system ----------------
def _generate_content_sections(briefing: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    """Generate all content sections - using PARALLEL execution.
    
    Zusätzlich werden logische Section-Keys (executive_summary, quick_wins, roadmap_90d, ...)
    für Validator & interne Checks gesetzt.
    """
    sections: Dict[str, Any] = {}

    # Alle GPT-Sektionen, die parallel erzeugt werden
    parallel_sections = [
        ("executive_summary", "EXECUTIVE_SUMMARY_HTML"),
        ("executive_decision", "EXECUTIVE_DECISION_HTML"),  # Step 1/3: Executive Decision Block
        ("ki_stack_summary", "KI_STACK_SUMMARY_HTML"),  # G20: KI-Stack Summary Card
        ("quick_wins", "_QUICK_WINS_RAW"),  # wird später aufbereitet
        ("roadmap", "PILOT_PLAN_HTML"),
        ("roadmap_12m", "ROADMAP_12M_HTML"),
        ("business_roi", "ROI_HTML"),
        ("business_costs", "COSTS_OVERVIEW_HTML"),
        ("business_case", "BUSINESS_CASE_HTML"),
        ("data_readiness", "DATA_READINESS_HTML"),
        ("org_change", "ORG_CHANGE_HTML"),
        ("risks", "RISKS_HTML"),
        ("gamechanger", "GAMECHANGER_HTML"),
        ("recommendations", "RECOMMENDATIONS_HTML"),
        ("reifegrad_sowhat", "REIFEGRAD_SOWHAT_HTML"),
        ("ai_act_summary", "AI_ACT_SUMMARY_HTML"),
        ("strategie_governance", "STRATEGIE_GOVERNANCE_HTML"),
        ("wettbewerb_benchmark", "WETTBEWERB_BENCHMARK_HTML"),
        ("technologie_prozesse", "TECHNOLOGIE_PROZESSE_HTML"),
        ("unternehmensprofil_markt", "UNTERNEHMENSPROFIL_MARKT_HTML"),
        ("tools_empfehlungen", "TOOLS_EMPFEHLUNGEN_HTML"),
        ("foerderpotenzial", "FOERDERPOTENZIAL_HTML"),
        ("transparency_box", "TRANSPARENCY_BOX_HTML"),
        ("ki_aktivitaeten_ziele", "KI_AKTIVITAETEN_ZIELE_HTML"),
        # Neue Sektionen (Sprint 2025)
        ("monetarisierung", "MONETARISIERUNG_HTML"),
        ("ki_skillplan", "KI_SKILLPLAN_HTML"),
        ("templates_start", "TEMPLATES_START_HTML"),
        # Neue Sektionen (Sprint 2025 - Phase 2)
        ("roi_tracking", "ROI_TRACKING_HTML"),
        ("ai_policy_mini", "AI_POLICY_MINI_HTML"),
        ("kickoff_vorlage", "KICKOFF_VORLAGE_HTML"),
        ("prompt_framework", "PROMPT_FRAMEWORK_HTML"),
        # G24: Branch Deep-Dive Addon
        ("branch_deep_dive", "BRANCH_DEEP_DIVE_HTML"),
    ]

    max_workers = int(os.getenv("GPT_PARALLEL_WORKERS", "10"))

    log.info(
        "🚀 Generating %d sections in PARALLEL (max_workers=%d)...",
        len(parallel_sections),
        max_workers,
    )
    start_time = datetime.now()

    # GPT-Aufrufe parallel ausführen
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_section = {
            executor.submit(
                _generate_content_section, section_name, briefing, scores
            ): (section_name, key)
            for section_name, key in parallel_sections
        }

        for future in as_completed(future_to_section):
            section_name, key = future_to_section[future]
            try:
                result = future.result()
                # HTML-Variante für Renderer/Template
                sections[key] = result
                # Logischer Key für Validator / interne Checks
                sections[section_name] = result
            except Exception as exc:
                log.error("❌ Section %s failed: %s", section_name, exc)
                err_html = f"<p><em>[{section_name} – Error: {exc}]</em></p>"
                sections[key] = err_html
                sections[section_name] = err_html

    elapsed = (datetime.now() - start_time).total_seconds()
    log.info(
        "✅ Parallel generation completed in %.1fs (vs ~%ds sequential)",
        elapsed,
        len(parallel_sections) * 15,
    )

    # Executive Summary Placeholder-Fix
    sections["EXECUTIVE_SUMMARY_HTML"] = _fix_exec_placeholders(
        sections.get("EXECUTIVE_SUMMARY_HTML", ""),
        scores,
        sections,
        sections.get("report_date", ""),
    )
    sections["executive_summary"] = sections["EXECUTIVE_SUMMARY_HTML"]

    # Quick Wins: reparieren, splitten, Aliase setzen
    qw_html = sections.pop("_QUICK_WINS_RAW", "")
    if _needs_repair(qw_html):
        qw_html = _repair_html("quick_wins", qw_html)

    left, right = _split_li_list_to_columns(qw_html)
    sections["QUICK_WINS_HTML_LEFT"] = left
    sections["QUICK_WINS_HTML_RIGHT"] = right
    sections["QUICK_WINS_HTML"] = (
        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:16px'>"
        + left
        + right
        + "</div>"
    )
    # logischer Inhalt (Validator)
    sections["quick_wins"] = qw_html

    # Stunden aus Quick Wins extrahieren
    total_h = 0
    try:
        total_h = _sum_hours_from_quick_wins(qw_html)
    except Exception:
        total_h = 0

    if total_h <= 0:
        try:
            fb = int(os.getenv("FALLBACK_QW_MONTHLY_H", "0"))
        except Exception:
            fb = 0
        if fb <= 0:
            try:
                fb = int(os.getenv("DEFAULT_QW1_H", "20")) + int(
                    os.getenv("DEFAULT_QW2_H", "15")
                )
            except Exception:
                fb = 35
        total_h = max(0, fb)

    rate = int(
        briefing.get("stundensatz_eur") or os.getenv("DEFAULT_STUNDENSATZ_EUR", "60") or 60
    )
    if total_h > 0:
        sections.update(
            {
                "monatsersparnis_stunden": total_h,
                "monatsersparnis_eur": total_h * rate,
                "jahresersparnis_stunden": total_h * 12,
                "jahresersparnis_eur": total_h * rate * 12,
                "stundensatz_eur": rate,
                "REALITY_NOTE_QW": (
                    "Praxis-Hinweis: Diese Quick-Wins sparen ~"
                    f"{max(1, int(round(total_h * 0.7)))}–{int(round(total_h * 1.2))} h/Monat "
                    "(konservativ geschätzt)."
                ),
            }
        )

    # Statische Sensitivitäts-Tabelle
    sections["BUSINESS_SENSITIVITY_HTML"] = (
        '<table class="table"><thead><tr><th>Adoption</th><th>Kommentar</th></tr></thead>'
        "<tbody><tr><td>100%</td><td>Planmäßige Wirkung der Maßnahmen.</td></tr>"
        "<tr><td>80%</td><td>Leichte Abweichungen – Payback +2–3 Monate.</td></tr>"
        "<tr><td>60%</td><td>Konservativ – nur Kernmaßnahmen; Payback länger.</td></tr></tbody></table>"
    )

    # NEXT ACTIONS – Prompt-System oder Legacy
    # PLATIN+++ v5.4: Use briefing's actual lang
    briefing_lang_for_actions = briefing.get("lang", "de") if isinstance(briefing, dict) else "de"
    if USE_PROMPT_SYSTEM:
        try:
            vars_dict = _build_prompt_vars(briefing, scores)
            prompt_text = load_prompt("next_actions", lang=briefing_lang_for_actions, vars_dict=vars_dict)
            params = _llm_params_for("next_actions")
            # PLATIN+++ v5.4: Language-aware system prompt
            sys_prompt = "Du bist PMO-Lead. Antworte nur mit HTML." if briefing_lang_for_actions == "de" else "You are a PMO lead. Reply only with HTML."
            nxt = _call_llm_for_section(
                section_key="next_actions",
                prompt=prompt_text,
                system_prompt=sys_prompt,
                temperature=params["temperature"],
                max_tokens=min(params["max_tokens"], 600),
                model=params["model"],
            ) or ""
            sections["NEXT_ACTIONS_HTML"] = (
                _clean_html(nxt)
                if nxt
                else _get_fallback_content("next_actions", briefing, scores)
            )
        except Exception as e:
            log.warning(
                "⚠️ Next actions prompt system failed: %s, using fallback", e
            )
            sections["NEXT_ACTIONS_HTML"] = _get_fallback_content(
                "next_actions", briefing, scores
            )
    else:
        now = datetime.now()
        params = _llm_params_for("next_actions")
        nxt = _call_llm_for_section(
            section_key="next_actions",
            prompt=f"""Erstelle 3–7 **Next Actions (30 Tage)** in <ol>. ...""",
            system_prompt="Du bist PMO-Lead. Antworte nur mit HTML.",
            temperature=params["temperature"],
            max_tokens=min(params["max_tokens"], 600),
            model=params["model"],
        ) or ""
        sections["NEXT_ACTIONS_HTML"] = (
            _clean_html(nxt)
            if nxt
            else _get_fallback_content("next_actions", briefing, scores)
        )

    # One-Liner-LEADs (parallel)
    one_liner_tasks = [
        ("LEAD_EXEC", "Executive Summary", sections["EXECUTIVE_SUMMARY_HTML"]),
        ("LEAD_KPI", "KPI-Dashboard & Monitoring", ""),
        ("LEAD_QW", "Quick Wins (0–90 Tage)", qw_html),
        (
            "LEAD_ROADMAP_90",
            "Roadmap (90 Tage – Test → Pilot → Rollout)",
            sections["PILOT_PLAN_HTML"],
        ),
        (
            "LEAD_ROADMAP_12",
            "Roadmap (12 Monate)",
            sections["ROADMAP_12M_HTML"],
        ),
        (
            "LEAD_BUSINESS",
            "Business Case & Kostenübersicht",
            sections["ROI_HTML"],
        ),
        (
            "LEAD_BUSINESS_DETAIL",
            "Business Case (detailliert)",
            sections["BUSINESS_CASE_HTML"],
        ),
        (
            "LEAD_TOOLS",
            "Empfohlene Tools (Pro & Open-Source)",
            sections.get("TOOLS_HTML", ""),
        ),
        (
            "LEAD_DATA",
            "Dateninventar & -Qualität",
            sections["DATA_READINESS_HTML"],
        ),
        ("LEAD_ORG", "Organisation & Change", sections["ORG_CHANGE_HTML"]),
        ("LEAD_RISKS", "Risiko-Assessment & Compliance", sections["RISKS_HTML"]),
        ("LEAD_GC", "Gamechanger-Use Case", sections["GAMECHANGER_HTML"]),
        (
            "LEAD_FUNDING",
            "Aktuelle Förderprogramme & Quellen",
            sections.get("FOERDERPROGRAMME_HTML", ""),
        ),
        (
            "LEAD_NEXT_ACTIONS",
            "Nächste Schritte (30 Tage)",
            sections["NEXT_ACTIONS_HTML"],
        ),
        (
            "LEAD_AI_ACT",
            "EU AI Act – Zusammenfassung & Compliance",
            sections["AI_ACT_SUMMARY_HTML"],
        ),
        (
            "LEAD_STRATEGIE",
            "Strategie & Governance",
            sections["STRATEGIE_GOVERNANCE_HTML"],
        ),
        (
            "LEAD_WETTBEWERB",
            "Wettbewerb & Benchmarking",
            sections["WETTBEWERB_BENCHMARK_HTML"],
        ),
        (
            "LEAD_TECH",
            "Technologie & Prozesse",
            sections["TECHNOLOGIE_PROZESSE_HTML"],
        ),
        (
            "LEAD_UNTERNEHMEN",
            "Unternehmensprofil & Markt",
            sections["UNTERNEHMENSPROFIL_MARKT_HTML"],
        ),
        (
            "LEAD_TOOLS_EMPF",
            "Tool-Empfehlungen & Einführungsreihenfolge",
            sections["TOOLS_EMPFEHLUNGEN_HTML"],
        ),
        ("LEAD_FOERDER", "Förderpotenzial", sections["FOERDERPOTENZIAL_HTML"]),
        (
            "LEAD_TRANSPARENCY",
            "Transparenz & Methodik",
            sections["TRANSPARENCY_BOX_HTML"],
        ),
        (
            "LEAD_KI_AKTIVITAETEN",
            "KI-Aktivitäten & Ziele",
            sections["KI_AKTIVITAETEN_ZIELE_HTML"],
        ),
    ]

    log.info("🚀 Generating %d one-liners in PARALLEL...", len(one_liner_tasks))
    oneliner_start = datetime.now()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_key = {
            executor.submit(_one_liner, title, html_content, briefing, scores): key
            for key, title, html_content in one_liner_tasks
        }
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                sections[key] = future.result()
            except Exception as exc:
                log.warning("One-liner %s failed: %s", key, exc)
                sections[key] = ""

    oneliner_elapsed = (datetime.now() - oneliner_start).total_seconds()
    log.info(
        "✅ One-liners completed in %.1fs (vs ~%ds sequential)",
        oneliner_elapsed,
        len(one_liner_tasks) * 3,
    )

    # Benchmark-HTML & KPI-Kontext
    # TEIL 3.1.4: Pass lang for locale-aware benchmark table
    benchmark_lang = briefing.get("lang", "de") if isinstance(briefing, dict) else "de"
    sections["BENCHMARK_HTML"] = _build_benchmark_html(briefing, lang=benchmark_lang)

    score_overall = scores.get("overall", 0)
    benchmark_avg = briefing.get("benchmark_avg", 35)
    benchmark_top = briefing.get("benchmark_top", 55)
    # TEIL 3.1.4: Language-aware interpretation
    if benchmark_lang == "en":
        if score_overall >= 70:
            interpretation = "Very good – above average"
        elif score_overall >= 50:
            interpretation = "Solid – in the upper middle field"
        else:
            interpretation = "Room for improvement – considerable potential"
        kpi_context = f"""<div class="kpi-context">
<p><strong>Interpretation:</strong> {interpretation}</p>
<p><strong>Benchmark:</strong> Average {benchmark_avg}/100 · Top quartile {benchmark_top}/100</p>
</div>"""
    else:
        if score_overall >= 70:
            interpretation = "Sehr gut – überdurchschnittlich"
        elif score_overall >= 50:
            interpretation = "Solide – im guten Mittelfeld"
        else:
            interpretation = "Ausbaufähig – erhebliches Potenzial vorhanden"
        kpi_context = f"""<div class="kpi-context">
<p><strong>Interpretation:</strong> {interpretation}</p>
<p><strong>Benchmark:</strong> Durchschnitt {benchmark_avg}/100 · Top-Quartil {benchmark_top}/100</p>
</div>"""
    sections["KPI_CONTEXT_HTML"] = kpi_context

    try:
        _s = scores
        # TEIL 3.1.4: Language-aware KPI labels
        if benchmark_lang == "en":
            kpi_rows = (
                "<tr><td>Governance</td><td>" + str(_s.get("governance", 0)) + "</td></tr>"
                "<tr><td>Security</td><td>" + str(_s.get("security", 0)) + "</td></tr>"
                "<tr><td>Value Creation</td><td>" + str(_s.get("value", 0)) + "</td></tr>"
                "<tr><td>Enablement</td><td>" + str(_s.get("enablement", 0)) + "</td></tr>"
                "<tr><td><strong>Overall</strong></td><td><strong>" + str(_s.get("overall", 0)) + "</strong></td></tr>"
            )
            sections["KPI_SCORES_HTML"] = (
                "<table class='table'><thead><tr><th>Dimension</th><th>Score (0–100)</th></tr></thead><tbody>"
                + kpi_rows
                + "</tbody></table>"
            )
        else:
            kpi_rows = (
                "<tr><td>Governance</td><td>" + str(_s.get("governance", 0)) + "</td></tr>"
                "<tr><td>Sicherheit</td><td>" + str(_s.get("security", 0)) + "</td></tr>"
                "<tr><td>Wertschöpfung</td><td>" + str(_s.get("value", 0)) + "</td></tr>"
                "<tr><td>Befähigung</td><td>" + str(_s.get("enablement", 0)) + "</td></tr>"
                "<tr><td><strong>Gesamt</strong></td><td><strong>" + str(_s.get("overall", 0)) + "</strong></td></tr>"
            )
            sections["KPI_SCORES_HTML"] = (
                "<table class='table'><thead><tr><th>Dimension</th><th>Score (0–100)</th></tr></thead><tbody>"
                + kpi_rows
                + "</tbody></table>"
                + sections.get("BENCHMARK_HTML", "")
                + sections.get("KPI_CONTEXT_HTML", "")
            )
    except Exception:
        sections.setdefault("KPI_SCORES_HTML", sections.get("KPI_CONTEXT_HTML", ""))

    # ZIM & Kreativ-Aliase
    sections["ZIM_ALERT_HTML"] = os.getenv("ZIM_ALERT_HTML", "")
    sections["ZIM_WORKFLOW_HTML"] = os.getenv("ZIM_WORKFLOW_HTML", "")
    sections.setdefault("KREATIV_TOOLS_HTML", "")
    sections["LEAD_ZIM_ALERT"] = "Wichtige Änderung ab 2025"
    sections["LEAD_ZIM_WORKFLOW"] = "Schritt-für-Schritt-Anleitung zur volldigitalen Antragstellung"
    sections["LEAD_CREATIV"] = "Kuratierte Tools für kreative Branchen"
    sections.setdefault(
        "LEAD_ROADMAP",
        _one_liner("Roadmap", sections.get("PILOT_PLAN_HTML", ""), briefing, scores),
    )

    # 🎯 WICHTIG: Logische Aliase für Validator & Template

    # 90-Tage-Roadmap (Validator + Template) - KONSISTENTES MAPPING
    sections["roadmap_90d"] = sections.get("PILOT_PLAN_HTML", "")
    sections["ROADMAP_HTML"] = sections.get("PILOT_PLAN_HTML", "")
    sections["ROADMAP_90D_HTML"] = sections.get("PILOT_PLAN_HTML", "")

    # 12-Monats-Roadmap
    sections["roadmap_12m"] = sections.get("ROADMAP_12M_HTML", "")

    # Business Case / Governance / Org / Tools / Förderpotenzial
    # Sprint G6.4: Inject pre-calculated Business Case Table into BUSINESS_CASE_HTML
    bc_table = briefing.get("BUSINESS_CASE_TABLE_HTML", "")
    bc_html = sections.get("BUSINESS_CASE_HTML", "")
    if bc_table and bc_html:
        # Append the calculated table to the business case section
        # Insert before closing </section> tag if present, otherwise append
        if "</section>" in bc_html:
            bc_html = bc_html.replace("</section>", f"\n{bc_table}\n</section>", 1)
        else:
            bc_html = f"{bc_html}\n{bc_table}"
        sections["BUSINESS_CASE_HTML"] = bc_html
        log.debug("💰 Business Case Table injected into BUSINESS_CASE_HTML")
    # Also store table separately for direct template access
    sections["BUSINESS_CASE_TABLE_HTML"] = bc_table
    sections["business_case"] = sections.get("BUSINESS_CASE_HTML", "")
    sections["strategie_governance"] = sections.get("STRATEGIE_GOVERNANCE_HTML", "")
    sections["org_change"] = sections.get("ORG_CHANGE_HTML", "")
    sections["tools_empfehlungen"] = sections.get("TOOLS_EMPFEHLUNGEN_HTML", "")
    sections["foerderpotenzial"] = sections.get("FOERDERPOTENZIAL_HTML", "")
    sections["risks"] = sections.get("RISKS_HTML", "")
    sections["gamechanger"] = sections.get("GAMECHANGER_HTML", "")
    sections["recommendations"] = sections.get("RECOMMENDATIONS_HTML", "")
    # Sprint N3.3: Apply Exec Summary Hard-Clean to remove H1/H2 and label text
    from services.html_sanitizer import clean_exec_summary_html
    exec_summary_cleaned = clean_exec_summary_html(sections.get("EXECUTIVE_SUMMARY_HTML", ""))
    sections["EXECUTIVE_SUMMARY_HTML"] = exec_summary_cleaned
    sections["EXEC_SUMMARY_HTML"] = exec_summary_cleaned
    sections["executive_summary"] = exec_summary_cleaned

    # ==========================================================================
    # Sprint G7/G8: AI Act Compliance Sections with Cross-Integration
    # ==========================================================================
    try:
        # Determine report language from briefing (Multilingual v1: normalize)
        report_lang = normalize_lang(briefing.get("lang"), default="de")

        # G8.6: Use optimized version with caching
        ai_act_data = build_ai_act_sections_optimized(briefing, lang=report_lang)

        # Add AI Act variables to sections
        sections.update(ai_act_data)

        # Generate HTML for alerts and gaps (convert lists to HTML)
        alerts_list = ai_act_data.get("AI_ACT_NONCOMPLIANCE_ALERTS", [])
        if alerts_list:
            alerts_html = "<ul class='alert-list'>\n"
            for alert in alerts_list:
                alerts_html += f"  <li class='alert-item'>{alert}</li>\n"
            alerts_html += "</ul>"
            sections["AI_ACT_NONCOMPLIANCE_ALERTS_HTML"] = alerts_html

        gaps_list = ai_act_data.get("AI_ACT_DATA_GAPS", [])
        if gaps_list:
            gaps_html = "<ul class='gaps-list'>\n"
            for gap in gaps_list:
                gaps_html += f"  <li class='gap-item'>{gap}</li>\n"
            gaps_html += "</ul>"
            sections["AI_ACT_DATA_GAPS_HTML"] = gaps_html

        # G8.2: Harmonize AI Act content across all sections
        sections = ai_act_harmonize(sections, briefing)

        # =======================================================================
        # G8.1: Apply AI Act Business Case Modifiers
        # =======================================================================
        risk_level = sections.get("AI_ACT_RISK_LEVEL", "minimal")
        ai_act_bc_modifiers = {
            "CAPEX_MODIFIER": sections.get("CAPEX_MODIFIER", 1.0),
            "OPEX_MODIFIER": sections.get("OPEX_MODIFIER", 1.0),
        }

        # Only apply if modifiers exist and are non-default
        if (callable(apply_ai_act_modifiers_to_business_case) and
            (ai_act_bc_modifiers["CAPEX_MODIFIER"] != 1.0 or
             ai_act_bc_modifiers["OPEX_MODIFIER"] != 1.0)):

            # Build current business case dict from sections
            current_bc = {
                "CAPEX_REALISTISCH_EUR": sections.get("CAPEX_REALISTISCH_EUR", 0),
                "OPEX_REALISTISCH_EUR": sections.get("OPEX_REALISTISCH_EUR", 0),
                "EINSPARUNG_MONAT_EUR": sections.get("EINSPARUNG_MONAT_EUR", 0),
                "PAYBACK_MONTHS": sections.get("PAYBACK_MONTHS", 0),
                "ROI_12M": sections.get("ROI_12M", 0),
                "BUSINESS_CASE_TABLE_HTML": sections.get("BUSINESS_CASE_TABLE_HTML", ""),
            }

            # Apply AI Act modifiers
            adjusted_bc = apply_ai_act_modifiers_to_business_case(
                current_bc,
                ai_act_bc_modifiers,
                risk_level
            )

            # Update sections with adjusted values
            sections.update(adjusted_bc)

            # G9.1: Track BC modification metrics
            if callable(track_bc_modification):
                track_bc_modification(
                    sections=sections,
                    original_bc=current_bc,
                    adjusted_bc=adjusted_bc,
                    risk_level=risk_level,
                    modifiers=ai_act_bc_modifiers
                )

            # Validate the adjusted business case
            if callable(validate_business_case_with_ai_act):
                bc_warnings = validate_business_case_with_ai_act(adjusted_bc, risk_level)
                if bc_warnings:
                    log.warning("⚠️ AI Act BC validation: %s", bc_warnings)

            log.info("✅ AI Act BC modifiers applied: CAPEX ×%.2f, OPEX ×%.2f for %s",
                     ai_act_bc_modifiers["CAPEX_MODIFIER"],
                     ai_act_bc_modifiers["OPEX_MODIFIER"],
                     risk_level)
        else:
            log.debug("ℹ️ AI Act BC modifiers not applied (defaults or function unavailable)")

        # G8.3: Validate persona compliance
        size = briefing.get("unternehmensgroesse", "")
        persona_violations = validate_ai_act_persona_compliance(sections, size)
        if persona_violations:
            log.warning("⚠️ AI Act persona violations: %s", persona_violations[:3])

        # Validate AI Act sections
        validation_errors = validate_ai_act_sections(ai_act_data)
        if validation_errors:
            log.warning("⚠️ AI Act validation issues: %s", validation_errors)
        else:
            log.info("✅ AI Act sections validated & harmonized successfully")

    except Exception as e:
        log.error("❌ AI Act section generation failed: %s", e)
        # Set fallback values
        sections["AI_ACT_RISK_LEVEL"] = "limited"
        sections["AI_ACT_RISK_REASONING"] = (
            "Die Risikoeinstufung konnte nicht automatisch ermittelt werden. "
            "Bitte prüfen Sie die AI Act Anforderungen manuell basierend auf Ihrer Branche und Ihren Anwendungsfällen."
        )
        sections["AI_ACT_DUTY_MATRIX_HTML"] = ""
        sections["AI_ACT_NONCOMPLIANCE_ALERTS"] = []
        sections["AI_ACT_NONCOMPLIANCE_ALERTS_HTML"] = ""
        sections["AI_ACT_DATA_GAPS"] = []
        sections["AI_ACT_DATA_GAPS_HTML"] = ""
        sections["AI_ACT_RECOMMENDED_NEXT_STEPS_HTML"] = ""
        sections["AI_ACT_RELATED_USECASES_HTML"] = ""
        sections["AI_ACT_CONSISTENCY_WARNINGS"] = []

    return sections


# -------------------- pipeline (kept from original with minor logging updates) ----------------
def analyze_briefing(db: Session, briefing_id: int, run_id: str) -> tuple[int, str, Dict[str, Any]]:
    """Analyze briefing and generate AI report."""
    # === HARD STOP ARCHITECTURE: Initialize error gate ===
    error_gate = ReportErrorGate(run_id=run_id)
    set_error_gate(error_gate)  # Make available to worker threads

    # Validate briefing_id
    if not isinstance(briefing_id, int):
        raise ValueError(f"briefing_id must be an integer, got {type(briefing_id)}")
    if briefing_id <= 0:
        raise ValueError(f"briefing_id must be positive, got {briefing_id}")

    br = db.get(Briefing, briefing_id)
    if not br: raise ValueError("Briefing not found")
    raw_answers: Dict[str, Any] = getattr(br, "answers", {}) or {}

    # Double-check encoding (safety net for old DB data)
    log.info("[%s] [ENCODING-FIX] Double-check on briefing %s", run_id, briefing_id)
    raw_answers = clean_briefing_data(raw_answers)  # type: ignore[assignment]

    answers = (lambda x: x)(raw_answers)
    try:
        from services.answers_normalizer import normalize_answers
        answers = normalize_answers(raw_answers)
    except Exception:
        pass

    # === STRATEGIC CONTEXT BLOCK erzeugen (für spätere Prompt-Anreicherung) ===
    # Multilingual v1: normalize language from br.lang
    report_lang = normalize_lang(getattr(br, "lang", "de"), default="de")
    strategic_context = build_strategic_context_block(answers, lang=report_lang)
    answers["strategic_context_block"] = strategic_context

    # === 3.1.4.9: AUTHORITATIVE LANGUAGE from br.lang ===
    # Set lang/LANG/sprache BEFORE content generation so prompt routing is correct
    # This is the single source of truth - briefing dict alone must NOT decide
    answers["lang"] = report_lang
    answers["LANG"] = report_lang
    answers["sprache"] = report_lang
    log.info("[%s] 🌐 Authoritative language set from br.lang: %s", run_id, report_lang)

    if strategic_context:
        log.info("[%s] 📋 Strategic context block generated (%d chars)", run_id, len(strategic_context))
    else:
        log.info("[%s] 📋 Strategic context block is empty (no strategic fields provided)", run_id)

    # === GUARDRAILS v5: Store hits for future prompt access (Phase 2) ===
    # Risiko/Compliance-Prompts können GUARDRAILS_HITS nutzen (vorbereitet)
    _, guardrail_hits = detect_guardrails_v5(answers, report_lang)
    # =========================================================================
    # Sprint G1.1 FIX: Speichere SERIALISIERTE Version der GuardrailHits
    # Verhindert "Object of type GuardrailHit is not JSON serializable" Fehler
    # bei json.dumps(briefing) in _build_prompt_vars()
    # =========================================================================
    answers["_guardrail_hits_text"] = guardrails_to_text(guardrail_hits)  # Text für Prompts
    answers["_guardrail_hits_count"] = len(guardrail_hits)  # Anzahl für Logik
    answers["_has_guardrails"] = len(guardrail_hits) > 0  # Boolean Flag

    log.info("[%s] 📊 Calculating realistic scores (v5.3.0-PLATIN+++)...", run_id)
    score_wrap = _calculate_realistic_score(answers)
    scores = score_wrap["scores"]

    # === Business Case FRÜHZEITIG berechnen (vor Content-Generierung!) ===
    # Damit sind BC-Werte (CAPEX, OPEX, ROI, etc.) für alle Fallbacks verfügbar
    if calc_business_case:
        bc = calc_business_case(answers, dict(os.environ))
        # BC-Werte zu answers hinzufügen, damit Fallbacks sie nutzen können
        answers["CAPEX_REALISTISCH_EUR"] = bc.get("CAPEX_REALISTISCH_EUR", 0)
        answers["OPEX_REALISTISCH_EUR"] = bc.get("OPEX_REALISTISCH_EUR", 0)
        answers["EINSPARUNG_MONAT_EUR"] = bc.get("EINSPARUNG_MONAT_EUR", 0)
        answers["PAYBACK_MONTHS"] = bc.get("PAYBACK_MONTHS", 0)
        answers["ROI_12M"] = bc.get("ROI_12M", 0)
        answers["BUSINESS_CASE_TABLE_HTML"] = bc.get("BUSINESS_CASE_TABLE_HTML", "")
        log.info("[%s] 💰 Business Case pre-calculated: CAPEX=%s, OPEX=%s, Payback=%sm, ROI=%s%%",
                 run_id,
                 bc.get("CAPEX_REALISTISCH_EUR", "N/A"),
                 bc.get("OPEX_REALISTISCH_EUR", "N/A"),
                 bc.get("PAYBACK_MONTHS", "N/A"),
                 bc.get("ROI_12M", "N/A"))

    log.info("[%s] 🎨 Generating content sections with %s...", run_id, "PROMPT SYSTEM" if USE_PROMPT_SYSTEM else "legacy prompts")
    sections = _generate_content_sections(briefing=answers, scores=scores)
    
    now = datetime.now()
    # Core metadata + Language
    sections["LANG"] = getattr(br, "lang", "de")
    sections["report_date"] = now.strftime("%d.%m.%Y")
    sections["report_year"] = now.strftime("%Y")
    sections["transparency_text"] = os.getenv("TRANSPARENCY_TEXT", "")
    sections["user_email"] = answers.get("email") or answers.get("kontakt_email") or ""
    sections["ki_kompetenz"] = answers.get("ki_kompetenz") or answers.get("ki_knowhow", "")

    # Scores
    sections["score_governance"] = scores.get("governance", 0)
    sections["score_sicherheit"] = scores.get("security", 0)
    sections["score_nutzen"] = scores.get("value", 0)
    sections["score_wertschoepfung"] = scores.get("value", 0)
    sections["score_befaehigung"] = scores.get("enablement", 0)
    sections["score_gesamt"] = scores.get("overall", 0)

    # ==========================================================================
    # Badges: Derived from scores for QA-Gate compliance
    # badge_security: Based on security score (score_sicherheit)
    # badge_compliance: Based on governance score (score_governance)
    # badge_efficiency: Based on value/efficiency score (score_nutzen)
    # ==========================================================================
    sec_score = scores.get("security", 0)
    gov_score = scores.get("governance", 0)
    val_score = scores.get("value", 0)

    # Badge status: "green" if score >= 60, "yellow" if >= 30, "red" otherwise
    def _badge_status(score: float) -> str:
        if score >= 60:
            return "green"
        elif score >= 30:
            return "yellow"
        return "red"

    sections["badge_security"] = _badge_status(sec_score)
    sections["badge_compliance"] = _badge_status(gov_score)
    sections["badge_efficiency"] = _badge_status(val_score)

    log.debug("[%s] Badges set: security=%s, compliance=%s, efficiency=%s",
              run_id, sections["badge_security"], sections["badge_compliance"], sections["badge_efficiency"])

    # Copy all label variables from answers to sections using loops
    # Single-choice labels with fallback
    label_with_fallback = [
        ("BRANCHE_LABEL", "branche"),
        ("BUNDESLAND_LABEL", "bundesland"),
        ("UNTERNEHMENSGROESSE_LABEL", "unternehmensgroesse"),
        ("JAHRESUMSATZ_LABEL", "jahresumsatz"),
    ]
    for label_key, fallback_key in label_with_fallback:
        sections[label_key] = answers.get(label_key, "") or answers.get(fallback_key, "")

    # Direct copy labels (single-choice and multi-choice)
    direct_copy_keys = [
        "HAUPTLEISTUNG", "IT_INFRASTRUKTUR_LABEL", "PROZESSE_PAPIERLOS_LABEL",
        "AUTOMATISIERUNGSGRAD_LABEL", "ROADMAP_VORHANDEN_LABEL", "GOVERNANCE_RICHTLINIEN_LABEL",
        "CHANGE_MANAGEMENT_LABEL", "MELDEWEGE_LABEL", "DATENSCHUTZ_LABEL",
        "LOESCHREGELN_LABEL", "DATENSCHUTZBEAUFTRAGTER_LABEL", "FOLGENABSCHAETZUNG_LABEL",
        "INTERNE_KI_KOMPETENZEN_LABEL", "STRATEGISCHE_ZIELE", "GESCHAEFTSMODELL_EVOLUTION",
        "ZEITERSPARNIS_PRIORITAET", "KI_PROJEKTE", "VISION_3_JAHRE", "KI_GUARDRAILS",
        "MITARBEITER_LABEL", "UMSATZ_LABEL", "SELBSTSTAENDIG_LABEL",
        "ZIELGRUPPEN_LABELS", "MARKTPOSITION_LABEL", "BENCHMARK_WETTBEWERB_LABEL",
        "INTERESSE_FOERDERUNG_LABEL",
        # Multi-choice labels
        "KI_ZIELE_LABELS", "KI_HEMMNISSE_LABELS", "ANWENDUNGSFAELLE_LABELS",
        "DATENQUELLEN_LABELS", "VORHANDENE_TOOLS_LABELS", "REGULIERTE_BRANCHE_LABELS",
        "TRAININGS_INTERESSEN_LABELS",
        # Strategic context block
        "strategic_context_block",
    ]
    for key in direct_copy_keys:
        sections[key] = answers.get(key, "")

    # === STRATEGIC CONTEXT FIELDS (lowercase for template compatibility) ===
    # These are the user's freetext strategic inputs, mapped to lowercase template keys
    strategic_field_mappings = [
        ("strategische_ziele", "strategische_ziele"),
        ("zeitersparnis_prioritaet", "zeitersparnis_prioritaet"),
        ("hauptleistung", "hauptleistung"),
        ("ki_projekte", "ki_projekte"),
        ("geschaeftsmodell_evolution", "geschaeftsmodell_evolution"),
        ("vision_3_jahre", "vision_3_jahre"),
        ("ki_guardrails", "ki_guardrails"),
        ("strategic_context_block", "strategic_context_block"),
    ]
    for answer_key, template_key in strategic_field_mappings:
        val = answers.get(answer_key, "")
        # Skip placeholder values
        if val and val != "—":
            sections[template_key] = val
        else:
            sections[template_key] = ""

    # === GUARDRAILS_HITS for future Risk/Compliance prompts (v5.0 preparation) ===
    # Sprint G1.1: Nutze bereits serialisierte Version (kein guardrails_to_text mehr nötig)
    sections["GUARDRAILS_HITS"] = answers.get("_guardrail_hits_text", "")

    log.info("[%s] Copied %d label variables to sections", run_id, len(direct_copy_keys) + len(label_with_fallback))
# === END LABELS FIX ===

    version_full = os.getenv("VERSION", "1.0.0")
    version_mm_match = re.match(r"^\s*(\d+)\.(\d+)", version_full or "")
    version_mm = f"{version_mm_match.group(1)}.{version_mm_match.group(2)}" if version_mm_match else "1.0"
    kundencode = _derive_kundencode(answers, sections["user_email"])
    report_id = f"R-{now.strftime('%Y%m%d')}-{kundencode}"
    sections["kundencode"] = kundencode
    sections["report_id"] = report_id
    sections["report_version"] = version_mm
    sections["WATERMARK_TEXT"] = _build_watermark_text(report_id, version_mm)
    
    # Build stamp & Feedback box
    sections["BUILD_STAMP"] = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · {report_id} · v{version_mm}"
    if sections.get("FEEDBACK_URL"):
        fb_html = _build_feedback_box(sections["FEEDBACK_URL"], sections["report_date"])
        if fb_html:
            sections["FEEDBACK_BOX_HTML"] = fb_html

    sections["CHANGELOG_SHORT"] = os.getenv("CHANGELOG_SHORT", "—")
    sections["AUDITOR_INITIALS"] = os.getenv("AUDITOR_INITIALS", "KSJ")

    # G23: KPI Visualisation Layer
    try:
        from utils.kpi_visuals import generate_kpi_visuals
        kpi_data = {
            "roi": answers.get("ROI_12M") or sections.get("ROI_12M") or 0,
            "payback_months": answers.get("PAYBACK_MONTHS") or sections.get("PAYBACK_MONTHS") or 0,
            "time_savings_eur": answers.get("EINSPARUNG_MONAT_EUR") or sections.get("EINSPARUNG_MONAT_EUR") or 0,
        }
        # Add industry benchmark if available from branch profile
        if answers.get("branch_avg_roi"):
            kpi_data["industry_roi"] = answers.get("branch_avg_roi")
        kpi_visuals = generate_kpi_visuals(kpi_data, lang=sections.get("LANG", "de"))
        sections["KPI_VISUALS_HTML"] = kpi_visuals.get("html", "")
        sections["KPI_HTML"] = kpi_visuals.get("bar_html", "")
        log.debug("[%s] 📊 G23 KPI visuals generated", run_id)
    except ImportError:
        log.debug("[%s] G23 kpi_visuals not available - skipping", run_id)
        sections.setdefault("KPI_HTML", "")
        sections.setdefault("KPI_VISUALS_HTML", "")
    except Exception as exc:
        log.warning("[%s] ⚠️ G23 KPI visuals generation failed: %s", run_id, exc)
        sections.setdefault("KPI_HTML", "")
        sections.setdefault("KPI_VISUALS_HTML", "")

    sections.setdefault("FEEDBACK_BOX_HTML","Feedback willkommen – was war hilfreich, was fehlt?")
    sections.setdefault("DATA_COVERAGE_HTML","")
    sections.setdefault("FREITEXT_SNIPPETS_HTML","")
    sections.setdefault("KREATIV_SPECIAL_HTML","")
    sections.setdefault("LEISTUNG_NACHWEIS_HTML","")
    sections.setdefault("GLOSSAR_HTML","")

    # Kreativ Tools
    kreat_path = os.getenv("KREATIV_TOOLS_PATH", "").strip()
    if kreat_path:
        kreat_html = _build_kreativ_tools_html(kreat_path, sections["report_date"])
        if kreat_html:
            sections["KREATIV_TOOLS_HTML"] = kreat_html
            sections["KREATIV_SPECIAL_HTML"] = kreat_html
    
    # Research integration
    research_last_updated = ""
    try:
        from services.research_pipeline import run_research
        if USE_INTERNAL_RESEARCH and run_research:
            log.info("[%s] 🔬 Running internal research...", run_id)
            research_blocks = run_research(answers)
            if isinstance(research_blocks, dict):
                for k, v in research_blocks.items():
                    if isinstance(v, str): 
                        sections[k] = v
                research_last_updated = str(research_blocks.get("last_updated") or "")
    except Exception as exc:
        log.warning("[%s] ⚠️ Internal research failed: %s", run_id, exc)
    
    sections["research_last_updated"] = research_last_updated or sections["report_date"]
    
    # Alias für Templates, die {{ LAST_UPDATED }} verwenden
    sections.setdefault("LAST_UPDATED", sections["research_last_updated"])
    # Map research results
    if "TOOLS_TABLE_HTML" in sections: 
        sections["TOOLS_HTML"] = sections.pop("TOOLS_TABLE_HTML", "")
    if "FUNDING_TABLE_HTML" in sections: 
        sections["FOERDERPROGRAMME_HTML"] = sections.pop("FUNDING_TABLE_HTML", "")
    
    # Rewrite table link labels
    if sections.get("TOOLS_HTML"): 
        sections["TOOLS_HTML"] = _rewrite_table_links_with_labels(sections["TOOLS_HTML"])
    if sections.get("FOERDERPROGRAMME_HTML"):
        sections["FOERDERPROGRAMME_HTML"] = _rewrite_table_links_with_labels(sections["FOERDERPROGRAMME_HTML"])

    # 🎯 KERN-FÖRDERMATRIX 2025/2026: Statischer, size-aware Kern immer einfügen
    # v4.16.0: Enable funding for EN reports when country is DE/Germany
    # v4.17.0: Phase 2 - Enable EU core funding for EN reports with non-German countries
    # Multilingual v1: normalize language from sections
    report_lang = normalize_lang(sections.get("LANG"), default="de")
    report_country = (answers.get("country") or "").upper()

    # Check if this is an EN report for Germany (enable DE funding)
    is_en_germany = (
        report_lang == "en" and
        report_country in ("DE", "GERMANY", "DEUTSCHLAND", "")  # Empty = default to DE
    )

    if report_lang == "en" and is_en_germany:
        # Phase 1: EN report for Germany - Enable German funding with dedicated EN service
        log.info("[%s] 🌐 Enabling German funding for English report", run_id)
        from services.funding_service_en import get_funding_for_germany_en, render_funding_html_en
        try:
            funding_result = get_funding_for_germany_en(answers)
            if funding_result.has_programmes:
                funding_html = render_funding_html_en(funding_result, limit=5)
                sections["FOERDERPROGRAMME_HTML"] = (
                    f"<h3>German Funding Programs for Your Profile (2025/2026)</h3>\n"
                    f"{funding_html}"
                )
                sections["FOERDERPOTENZIAL_HTML"] = ""  # Potential section handled by prompt
                sections["FUNDING_HTML"] = funding_html
                sections["FUNDING_PROGRAMMES"] = funding_result.programmes  # For Jinja2 template
                sections["FUNDING_SCOPE"] = "DE"  # For template title logic
                log.info("[%s] ✅ EN funding (DE): %d programmes loaded", run_id, funding_result.programme_count)
            else:
                log.info("[%s] ⚠️ EN funding (DE): No matching programmes found", run_id)
                sections["FOERDERPROGRAMME_HTML"] = ""
                sections["FOERDERPOTENZIAL_HTML"] = ""
                sections["FUNDING_HTML"] = ""
                sections["FUNDING_PROGRAMMES"] = []
                sections["FUNDING_SCOPE"] = ""
        except Exception as e:
            log.warning("[%s] ⚠️ EN funding service error: %s", run_id, e)
            sections["FOERDERPROGRAMME_HTML"] = ""
            sections["FOERDERPOTENZIAL_HTML"] = ""
            sections["FUNDING_HTML"] = ""
            sections["FUNDING_PROGRAMMES"] = []
            sections["FUNDING_SCOPE"] = ""
    elif report_lang == "en":
        # Phase 2: EN report for non-German country - Enable EU core funding
        log.info("[%s] 🌐 Enabling EU core funding for English report (country=%s)", run_id, report_country)
        from services.funding_service_en import get_funding_eu_core_en, render_funding_eu_core_html_en
        try:
            eu_result = get_funding_eu_core_en(answers)
            if eu_result.has_programmes:
                funding_html = render_funding_eu_core_html_en(eu_result, limit=4)
                sections["FOERDERPROGRAMME_HTML"] = funding_html
                sections["FOERDERPOTENZIAL_HTML"] = ""
                sections["FUNDING_HTML"] = funding_html
                sections["FUNDING_PROGRAMMES_EU_CORE"] = eu_result.programmes  # For Jinja2 template
                sections["FUNDING_SCOPE"] = "EU_CORE"  # For template title logic
                log.info("[%s] ✅ EN funding (EU): %d programmes loaded", run_id, eu_result.programme_count)
            else:
                log.info("[%s] ⚠️ EN funding (EU): No matching programmes found", run_id)
                sections["FOERDERPROGRAMME_HTML"] = ""
                sections["FOERDERPOTENZIAL_HTML"] = ""
                sections["FUNDING_HTML"] = ""
                sections["FUNDING_PROGRAMMES_EU_CORE"] = []
                sections["FUNDING_SCOPE"] = ""
        except Exception as e:
            log.warning("[%s] ⚠️ EU core funding service error: %s", run_id, e)
            sections["FOERDERPROGRAMME_HTML"] = ""
            sections["FOERDERPOTENZIAL_HTML"] = ""
            sections["FUNDING_HTML"] = ""
            sections["FUNDING_PROGRAMMES_EU_CORE"] = []
            sections["FUNDING_SCOPE"] = ""
    else:
        from services.extra_sections import build_core_funding_table_html
        core_funding_html = build_core_funding_table_html(sections)

        if sections.get("FOERDERPROGRAMME_HTML"):
            # Kern-Matrix + Research-Ergebnisse kombinieren
            sections["FOERDERPROGRAMME_HTML"] = (
                f"<h3>Kernprogramme für Ihr Profil (2025/2026)</h3>\n"
                f"{core_funding_html}\n\n"
                f"<h3 style='margin-top: 16pt;'>Aktuell recherchierte Programme</h3>\n"
                f"{sections['FOERDERPROGRAMME_HTML']}"
            )
        else:
            # Nur Kern-Matrix (kein Research)
            sections["FOERDERPROGRAMME_HTML"] = core_funding_html

    sections["SOURCES_BOX_HTML"] = _build_sources_box_html(sections, sections["research_last_updated"])

    # Freitext snippets
    sections['FREITEXT_SNIPPETS_HTML'] = _build_freetext_snippets_html(answers)
    
    # Glossar
    gloss_raw = _try_read(GLOSSAR_PATH) or ""
    if gloss_raw:
        if GLOSSAR_PATH.lower().endswith(".md"):
            sections["GLOSSAR_HTML"] = _md_to_simple_html(gloss_raw)
        else:
            sections["GLOSSAR_HTML"] = gloss_raw
        # Replace {LAST_UPDATED} placeholder in glossar
        if "{LAST_UPDATED}" in sections["GLOSSAR_HTML"]:
            last_updated = sections.get("research_last_updated") or sections.get("report_date", "")
            sections["GLOSSAR_HTML"] = sections["GLOSSAR_HTML"].replace("{LAST_UPDATED}", last_updated)

    # Coverage guard
    try:
        cov = analyze_coverage(answers)
        log.info("[%s] 📈 Coverage: %s%% (present=%s, missing=%s)", run_id, cov.get("coverage_pct"), len(cov.get("present",[])), len(cov.get("missing",[])))
        if INCLUDE_COVERAGE_BOX:
            sections["LEISTUNG_NACHWEIS_HTML"] = (sections.get("LEISTUNG_NACHWEIS_HTML","") + build_html_report(cov))
    except Exception as _exc:
        log.warning("[%s] ⚠️ Coverage-guard warning: %s", run_id, _exc)

    # Logos & branding
    sections["LOGO_PRIMARY_SRC"] = os.getenv("LOGO_PRIMARY_SRC", "")
    sections["FOOTER_LEFT_LOGO_SRC"] = os.getenv("FOOTER_LEFT_LOGO_SRC", "")
    sections["FOOTER_MID_LOGO_SRC"] = os.getenv("FOOTER_MID_LOGO_SRC", "")
    sections["FOOTER_RIGHT_LOGO_SRC"] = os.getenv("FOOTER_RIGHT_LOGO_SRC", "")
    sections["FEEDBACK_URL"] = (os.getenv("FEEDBACK_URL") or os.getenv("FEEDBACK_REDIRECT_BASE") or "").strip()
    sections["FOOTER_BRANDS_HTML"] = os.getenv("FOOTER_BRANDS_HTML", "")
    sections["OWNER_NAME"] = os.getenv("OWNER_NAME", "KI‑Sicherheit.jetzt")
    sections["CONTACT_EMAIL"] = os.getenv("CONTACT_EMAIL", "info@example.com")
    sections["THEME_CSS_VARS"] = _theme_vars_for_branch(sections.get("BRANCHE_LABEL") or sections.get("branche", ""))
    
    # BUILD_ID - timestamp for report generation tracking
    sections["BUILD_ID"] = f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}"
    
    # Werkbank
    sections["WERKBANK_HTML"] = _build_werkbank_html_dynamic(answers)
    
    # AI Act blocks
    ai_act_blocks = _build_ai_act_blocks()
    sections.update(ai_act_blocks)
    # News/Änderungen box (AI Act phase + research timestamp)
    sections["NEWS_BOX_HTML"] = (
        "<div class='callout'><strong>EU AI Act – Phase:</strong> "
        + html.escape(sections.get("ai_act_phase_label","2025–2027"))
        + " · <strong>Quellenstand:</strong> "
        + html.escape(sections.get("research_last_updated", sections.get("report_date","")))
        + "</div>"
    )

    # Aliases for PDF template variables
    if sections.get("FOERDERPROGRAMME_HTML"):
        sections["FUNDING_HTML"] = sections["FOERDERPROGRAMME_HTML"]

    # =========================================================================
    # SPRINT B2.2: Tools × Funding Alignment & Starter Kits
    # =========================================================================
    try:
        from services.tools_funding_alignment import inject_alignment_into_sections
        sections = inject_alignment_into_sections(sections, answers, lang=report_lang)
    except ImportError:
        log.debug("[%s] B2.2 tools_funding_alignment not available", run_id)
    except Exception as e:
        log.warning("[%s] ⚠️ Tools-Funding alignment failed: %s", run_id, e)
        sections.setdefault("TOOLS_FUNDING_ALIGNMENT_HTML", "")
        sections.setdefault("TOOLS_FUNDING_ALIGNMENT_COMPACT_HTML", "")

    try:
        from services.tools_starter_kits import inject_starter_kit_into_sections
        sections = inject_starter_kit_into_sections(sections, answers, lang=report_lang)
    except ImportError:
        log.debug("[%s] B2.2 tools_starter_kits not available", run_id)
    except Exception as e:
        log.warning("[%s] ⚠️ Starter-Kit generation failed: %s", run_id, e)
        sections.setdefault("STARTER_KIT_HTML", "")
        sections.setdefault("STARTER_KIT_COMPACT_HTML", "")

    # =========================================================================
    # SPRINT G19: Branchenintelligenz & Marktlogik 2.0
    # =========================================================================
    try:
        from services.branch_profile_engine import get_branch_profile_html_sections
        branch_sections = get_branch_profile_html_sections(answers, lang=report_lang)
        sections.update(branch_sections)
        log.info("[%s] ✅ G19 Branch Profile injected", run_id)
    except ImportError:
        log.debug("[%s] G19 branch_profile_engine not available", run_id)
    except Exception as e:
        log.warning("[%s] ⚠️ G19 Branch Profile generation failed: %s", run_id, e)
        sections.setdefault("BRANCH_PROFILE_HTML", "")
        sections.setdefault("BRANCH_OPPORTUNITIES_HTML", "")
        sections.setdefault("BRANCH_RISKS_HTML", "")

    try:
        from services.funding_recommender import inject_funding_branch_alignment_into_sections
        sections = inject_funding_branch_alignment_into_sections(sections, answers, lang=report_lang)
        log.info("[%s] ✅ G19 Funding Branch Alignment injected", run_id)
    except ImportError:
        log.debug("[%s] G19 funding_branch_alignment not available", run_id)
    except Exception as e:
        log.warning("[%s] ⚠️ G19 Funding Branch Alignment failed: %s", run_id, e)
        sections.setdefault("FUNDING_BRANCH_ALIGNMENT_HTML", "")

    try:
        from services.tools_analytics import inject_tools_branch_alignment_into_sections
        sections = inject_tools_branch_alignment_into_sections(sections, answers, lang=report_lang)
        log.info("[%s] ✅ G19 Tools Branch Alignment injected", run_id)
    except ImportError:
        log.debug("[%s] G19 tools_branch_alignment not available", run_id)
    except Exception as e:
        log.warning("[%s] ⚠️ G19 Tools Branch Alignment failed: %s", run_id, e)
        sections.setdefault("TOOLS_BRANCH_ALIGNMENT_HTML", "")

    # =========================================================================
    # SPRINT G29: Risk Engine 2.0 – Konsolidierte Risikoanalyse
    # =========================================================================
    try:
        from services.risk_engine_v2 import generate_risk_report, risk_report_to_html

        risk_report = generate_risk_report(
            context=None,
            sections=sections,
            tools_data=sections.get("_tools_data"),  # Pass tools data if available
            funding_data=sections.get("_funding_data"),  # Pass funding data if available
            briefing=answers,
            llm_response=None,  # No LLM call for now, uses extraction
        )

        sections["RISK_ENGINE_HTML"] = risk_report_to_html(risk_report, lang=report_lang)
        sections["_risk_report"] = risk_report  # Store for Strategy Engine usage

        # Extract key values for template usage
        sections["RISK_CONSOLIDATED_SCORE"] = risk_report.consolidated_score
        sections["RISK_CONSOLIDATED_GRADE"] = risk_report.consolidated_grade
        sections["RISK_AI_ACT_CLASS"] = risk_report.ai_act_class
        sections["RISK_DSGVO_LEVEL"] = risk_report.dsgvo_risk_level
        sections["RISK_VENDOR_SCORE"] = risk_report.vendor_risk_score

        log.info("[%s] ✅ G29 Risk Engine 2.0 generated: score=%.1f, grade=%s, ai_act=%s",
                 run_id, risk_report.consolidated_score, risk_report.consolidated_grade,
                 risk_report.ai_act_class)
    except ImportError:
        log.debug("[%s] G29 risk_engine_v2 not available", run_id)
        sections.setdefault("RISK_ENGINE_HTML", "")
    except Exception as e:
        log.warning("[%s] ⚠️ G29 Risk Engine 2.0 failed: %s", run_id, e)
        sections.setdefault("RISK_ENGINE_HTML", "")

    # =========================================================================
    # SPRINT G33: Risk Engine 3.0 – DPIA & AI Act Conformity Mapping
    # =========================================================================
    try:
        from services.risk_engine_v3 import generate_risk_report_v3, risk_report_v3_to_html

        risk_report_v3 = generate_risk_report_v3(
            context=None,
            sections=sections,
            tools_data=sections.get("_tools_data"),
            funding_data=sections.get("_funding_data"),
            strategy_data=sections.get("_strategy_plan"),
            base_risk_report=sections.get("_risk_report"),
            briefing=answers,
            llm_response=None,
        )

        sections["RISK_ENGINE_V3_HTML"] = risk_report_v3_to_html(risk_report_v3, lang=report_lang)
        sections["_risk_report_v3"] = risk_report_v3

        # Extract key values for template usage
        sections["DPIA_REQUIRED"] = risk_report_v3.dpia_required
        sections["DPIA_REASON"] = risk_report_v3.dpia_reason
        sections["AI_ACT_CONFORMITY_SCORE"] = risk_report_v3.ai_act_conformity.conformity_score
        sections["RESIDUAL_RISK_SCORE"] = risk_report_v3.residual_risk_score
        sections["RESIDUAL_RISK_GRADE"] = risk_report_v3.residual_risk_grade
        sections["COMPLIANCE_STATUS"] = risk_report_v3.compliance_status

        log.info("[%s] ✅ G33 Risk Engine V3 generated: DPIA=%s, Conformity=%.0f%%, Residual=%s (%s)",
                 run_id,
                 "Required" if risk_report_v3.dpia_required else "Not Required",
                 risk_report_v3.ai_act_conformity.conformity_score * 100,
                 risk_report_v3.residual_risk_grade,
                 risk_report_v3.compliance_status)
    except ImportError:
        log.debug("[%s] G33 risk_engine_v3 not available", run_id)
        sections.setdefault("RISK_ENGINE_V3_HTML", "")
    except Exception as e:
        log.warning("[%s] ⚠️ G33 Risk Engine V3 failed: %s", run_id, e)
        sections.setdefault("RISK_ENGINE_V3_HTML", "")

    # =========================================================================
    # SPRINT G35: Vendor Audit Engine – KI-TUV for Tools & Models
    # =========================================================================
    try:
        from services.vendor_audit_engine import (
            generate_vendor_audit_report,
            vendor_audit_report_to_html,
        )

        vendor_audit_report = generate_vendor_audit_report(
            context=None,
            tools_data=sections.get("_tools_data"),
            risk_report_v2=sections.get("_risk_report"),
            risk_report_v3=sections.get("_risk_report_v3"),
            briefing=answers,
            llm_response=None,
        )

        sections["VENDOR_AUDIT_HTML"] = vendor_audit_report_to_html(vendor_audit_report, lang=report_lang)
        sections["_vendor_audit_report"] = vendor_audit_report

        # Extract key values for template usage
        sections["VENDOR_AUDIT_TOTAL"] = vendor_audit_report.total_vendors
        sections["VENDOR_AUDIT_GREEN"] = vendor_audit_report.green_count
        sections["VENDOR_AUDIT_YELLOW"] = vendor_audit_report.yellow_count
        sections["VENDOR_AUDIT_RED"] = vendor_audit_report.red_count
        sections["VENDOR_AUDIT_COMPLIANCE_SCORE"] = vendor_audit_report.compliance_score
        sections["VENDOR_AUDIT_STATUS"] = vendor_audit_report.overall_audit_status

        log.info("[%s] ✅ G35 Vendor Audit generated: %d vendors, %d green, %d yellow, %d red",
                 run_id,
                 vendor_audit_report.total_vendors,
                 vendor_audit_report.green_count,
                 vendor_audit_report.yellow_count,
                 vendor_audit_report.red_count)
    except ImportError:
        log.debug("[%s] G35 vendor_audit_engine not available", run_id)
        sections.setdefault("VENDOR_AUDIT_HTML", "")
    except Exception as e:
        log.warning("[%s] ⚠️ G35 Vendor Audit Engine failed: %s", run_id, e)
        sections.setdefault("VENDOR_AUDIT_HTML", "")

    # =========================================================================
    # SPRINT G36: Automation Roadmap Engine – Prozessanalyse & Transformationspfade
    # =========================================================================
    try:
        from services.automation_roadmap_engine import (
            generate_automation_roadmap,
            automation_roadmap_to_html,
        )

        automation_roadmap_report = generate_automation_roadmap(
            context=None,
            sections=sections,
            tools_data=sections.get("_tools_data"),
            funding_data=sections.get("_funding_data"),
            risk_report_v3=sections.get("_risk_report_v3"),
            business_case=sections.get("_bc_report"),
            strategy_plan=sections.get("_strategy_plan"),
            vendor_audit_report=sections.get("_vendor_audit_report"),
            briefing=answers,
            llm_response=None,
        )

        sections["AUTOMATION_ROADMAP_HTML"] = automation_roadmap_to_html(
            automation_roadmap_report,
            lang=report_lang
        )
        sections["_automation_roadmap_report"] = automation_roadmap_report

        # Extract key values for template usage
        sections["AUTO_TOTAL_PROCESSES"] = automation_roadmap_report.total_processes
        sections["AUTO_QUICK_WINS"] = automation_roadmap_report.quick_win_count
        sections["AUTO_AVG_POTENTIAL"] = automation_roadmap_report.avg_automation_potential
        sections["AUTO_PHASE_1_COUNT"] = len(automation_roadmap_report.phase_1_processes)
        sections["AUTO_PHASE_2_COUNT"] = len(automation_roadmap_report.phase_2_processes)
        sections["AUTO_PHASE_3_COUNT"] = len(automation_roadmap_report.phase_3_processes)
        sections["AUTO_TOTAL_PATHS"] = automation_roadmap_report.total_paths

        log.info("[%s] ✅ G36 Automation Roadmap generated: %d processes, %d paths, %d quick wins, avg potential=%.0f%%",
                 run_id,
                 automation_roadmap_report.total_processes,
                 automation_roadmap_report.total_paths,
                 automation_roadmap_report.quick_win_count,
                 automation_roadmap_report.avg_automation_potential * 100)
    except ImportError:
        log.debug("[%s] G36 automation_roadmap_engine not available", run_id)
        sections.setdefault("AUTOMATION_ROADMAP_HTML", "")
    except Exception as e:
        log.warning("[%s] ⚠️ G36 Automation Roadmap Engine failed: %s", run_id, e)
        sections.setdefault("AUTOMATION_ROADMAP_HTML", "")

    # =========================================================================
    # SPRINT G30: Business Case Engine 2.0 – ROI-Simulation & Szenarien
    # =========================================================================
    try:
        from services.business_case_engine_v2 import (
            generate_business_case_report,
            business_case_report_to_html,
        )

        bc_report = generate_business_case_report(
            context=None,
            sections=sections,
            tools_data=sections.get("_tools_data"),  # Pass tools data if available
            funding_data=sections.get("_funding_data"),  # Pass funding data if available
            briefing=answers,
            llm_response=None,  # Uses extraction-based calculation
        )

        sections["BUSINESS_CASE_ENGINE_HTML"] = business_case_report_to_html(bc_report, lang=report_lang)
        sections["_bc_report"] = bc_report  # Store for consistency checks

        # Extract key values for template usage
        realistic = bc_report.realistic_scenario
        if realistic:
            sections["BC_ROI_REALISTIC"] = realistic.roi_12m
            sections["BC_PAYBACK_REALISTIC"] = realistic.payback_months
            sections["BC_MONTHLY_SAVINGS_REALISTIC"] = realistic.monthly_savings
            sections["BC_INVESTMENT_TOTAL"] = bc_report.investment_total
            sections["BC_FUNDING_EFFECT"] = bc_report.funding_effect

        log.info("[%s] ✅ G30 Business Case Engine 2.0 generated: investment=%.0f€, ROI=%.1f%%, payback=%.1f months",
                 run_id, bc_report.investment_total,
                 realistic.roi_12m if realistic else 0,
                 realistic.payback_months if realistic else 0)
    except ImportError:
        log.debug("[%s] G30 business_case_engine_v2 not available", run_id)
        sections.setdefault("BUSINESS_CASE_ENGINE_HTML", "")
    except Exception as e:
        log.warning("[%s] ⚠️ G30 Business Case Engine 2.0 failed: %s", run_id, e)
        sections.setdefault("BUSINESS_CASE_ENGINE_HTML", "")

    # =========================================================================
    # SPRINT G32: Recommendations Engine – Meta-Empfehlungsschicht
    # =========================================================================
    try:
        from services.recommendations_engine import (
            generate_recommendations_report,
            recommendations_report_to_html,
        )

        reco_report = generate_recommendations_report(
            context=None,
            sections=sections,
            tools_data=sections.get("_tools_data"),
            funding_data=sections.get("_funding_data"),
            risk_report=sections.get("_risk_report"),
            strategy_plan=sections.get("_strategy_plan"),
            business_case=sections.get("_bc_report"),
            briefing=answers,
            llm_response=None,  # Will use extraction-based generation
        )

        sections["RECOMMENDATIONS_ENGINE_HTML"] = recommendations_report_to_html(reco_report, lang=report_lang)
        sections["_reco_report"] = reco_report  # Store for consistency checks

        # Extract key values for template usage
        sections["RECO_COUNT"] = len(reco_report.recommendations)
        sections["RECO_TOP_3_IDS"] = reco_report.top_3_ids
        sections["RECO_SUMMARY"] = reco_report.summary

        log.info("[%s] ✅ G32 Recommendations Engine generated: %d recommendations, top_3=%s",
                 run_id, len(reco_report.recommendations), reco_report.top_3_ids[:3])
    except ImportError:
        log.debug("[%s] G32 recommendations_engine not available", run_id)
        sections.setdefault("RECOMMENDATIONS_ENGINE_HTML", "")
    except Exception as e:
        log.warning("[%s] ⚠️ G32 Recommendations Engine failed: %s", run_id, e)
        sections.setdefault("RECOMMENDATIONS_ENGINE_HTML", "")

    # =========================================================================
    # SPRINT G34: Business Case Simulation – Monte Carlo ROI & Payback Analysis
    # =========================================================================
    try:
        from services.business_case_simulation import (
            generate_business_case_simulation,
            business_case_simulation_to_html,
        )

        bc_simulation = generate_business_case_simulation(
            context=None,
            business_case=sections.get("_bc_report"),
            risk_report_v3=sections.get("_risk_report_v3"),
            auto_report=sections.get("_automation_roadmap_report"),
            briefing=answers,
            llm_response=None,
        )

        sections["BUSINESS_CASE_SIM_HTML"] = business_case_simulation_to_html(bc_simulation, lang=report_lang)
        sections["_business_case_simulation_report"] = bc_simulation

        # Extract key values for template usage
        if bc_simulation.distribution:
            sections["ROI_P50"] = bc_simulation.distribution.roi_p50
            sections["ROI_P80"] = bc_simulation.distribution.roi_p80
            sections["ROI_P90"] = bc_simulation.distribution.roi_p90
            sections["PAYBACK_P50"] = bc_simulation.distribution.payback_p50

        log.info("[%s] ✅ G34 Business Case Simulation generated: P50 ROI=%.1f%%, P80 ROI=%.1f%%",
                 run_id,
                 bc_simulation.distribution.roi_p50 if bc_simulation.distribution else 0,
                 bc_simulation.distribution.roi_p80 if bc_simulation.distribution else 0)
    except ImportError:
        log.debug("[%s] G34 business_case_simulation not available", run_id)
        sections.setdefault("BUSINESS_CASE_SIM_HTML", "")
    except Exception as e:
        log.warning("[%s] ⚠️ G34 Business Case Simulation failed: %s", run_id, e)
        sections.setdefault("BUSINESS_CASE_SIM_HTML", "")

    # =========================================================================
    # SPRINT G37: Benchmark Engine – Branchenvergleich & Wettbewerbsposition
    # =========================================================================
    try:
        from services.benchmark_engine import (
            generate_benchmark_report,
            benchmark_report_to_html,
        )

        benchmark_report = generate_benchmark_report(
            context=None,
            sections=sections,
            kpi_data=sections.get("_business_case_simulation_report"),
            tools_data=sections.get("_tools_data"),
            funding_data=sections.get("_funding_data"),
            risk_report_v3=sections.get("_risk_report_v3"),
            auto_report=sections.get("_automation_roadmap_report"),
            strategy_plan=sections.get("_strategy_plan"),
            business_case=sections.get("_bc_report"),
            briefing=answers,
            llm_response=None,
            lang=report_lang,
        )

        sections["BENCHMARK_ENGINE_HTML"] = benchmark_report_to_html(benchmark_report, lang=report_lang)
        sections["_benchmark_report"] = benchmark_report

        # Extract key values for template usage
        sections["BENCHMARK_MATURITY_SCORE"] = benchmark_report.maturity_score
        sections["BENCHMARK_GRADE"] = benchmark_report.competitiveness_grade
        sections["BENCHMARK_ABOVE_MEDIAN"] = benchmark_report.above_median_count

        log.info("[%s] ✅ G37 Benchmark Engine generated: maturity=%.0f%%, grade=%s, above_median=%d/%d",
                 run_id,
                 benchmark_report.maturity_score,
                 benchmark_report.competitiveness_grade,
                 benchmark_report.above_median_count,
                 len(benchmark_report.positions))
    except ImportError:
        log.debug("[%s] G37 benchmark_engine not available", run_id)
        sections.setdefault("BENCHMARK_ENGINE_HTML", "")
    except Exception as e:
        log.warning("[%s] ⚠️ G37 Benchmark Engine failed: %s", run_id, e)
        sections.setdefault("BENCHMARK_ENGINE_HTML", "")

    log.info("[%s] 🎨 Rendering final HTML...", run_id)
    # --- Sanitize dynamic sections to prevent HTML leaks (z. B. eingebettetes <html> im Pilot-Plan) ---
    # 3.1.4.16: Pass lang for EN locale sanitization (lastline guardrail)
    try:
        if os.getenv("ENABLE_REPAIR_HTML", "1") in ("1","true","TRUE","yes","YES"):
            _pre_sanitize_count = sum(1 for _k,_v in sections.items() if isinstance(_v, str))
            sections = sanitize_sections_dict(sections, truthy_env=True, lang=report_lang)
            log.info("[%s] 🧼 HTML sanitized for %s string sections (lang=%s)", run_id, _pre_sanitize_count, report_lang)
    except Exception as _exc:
        log.warning("[%s] ⚠️ Sanitizer skipped: %s", run_id, _exc)

    # === Business Case Sensitivity-Werte berechnen (BC wurde bereits oben berechnet) ===
    # BC-Werte wurden früher in answers eingefügt (vor _generate_content_sections)
    if answers.get("CAPEX_REALISTISCH_EUR") is not None:
        sections["business_case_table_html"] = answers.get("BUSINESS_CASE_TABLE_HTML", "")
        # BC-Werte von answers nach sections kopieren
        for bc_key in ["CAPEX_REALISTISCH_EUR", "OPEX_REALISTISCH_EUR", "EINSPARUNG_MONAT_EUR", "PAYBACK_MONTHS", "ROI_12M"]:
            sections[bc_key] = answers.get(bc_key, 0)

        # Pre-calculate sensitivity values for Jinja2 template
        # These are used in template expressions like {{ ROI_12M * 0.8 }}
        try:
            capex = float(answers.get('CAPEX_REALISTISCH_EUR', 6000))
            opex = float(answers.get('OPEX_REALISTISCH_EUR', 120))
            einsparung = float(answers.get('EINSPARUNG_MONAT_EUR', 4500))
            roi_12m = float(answers.get('ROI_12M', 0))  # ROI_12M ist bereits ein Prozentwert (z.B. 200.0 für 200%)

            # Ensure numeric values are available for Jinja2 calculations
            sections['CAPEX_REALISTISCH_EUR'] = capex
            sections['OPEX_REALISTISCH_EUR'] = opex
            sections['EINSPARUNG_MONAT_EUR'] = einsparung
            sections['ROI_12M'] = roi_12m  # Prozentwert (z.B. 200.0)
            sections['ROI_12M_RATE'] = roi_12m / 100.0  # Als Faktor (z.B. 2.0 für 200%)

            # Sensitivity calculations (pessimistic 80%, optimistic 120%)
            # ROI_12M ist bereits in %, daher KEINE zusätzliche *100 Multiplikation
            sections['ROI_12M_LOW'] = round(roi_12m * 0.8, 1)  # in %
            sections['ROI_12M_HIGH'] = round(roi_12m * 1.2, 1)  # in %
            sections['EINSPARUNG_MONAT_EUR_LOW'] = round(einsparung * 0.8)
            sections['EINSPARUNG_MONAT_EUR_HIGH'] = round(einsparung * 1.2)
            sections['OPEX_REALISTISCH_EUR_LOW'] = round(opex * 0.8)
            sections['OPEX_REALISTISCH_EUR_HIGH'] = round(opex * 1.2)

            # Payback calculations for different scenarios
            einsparung_low = einsparung * 0.8 - opex
            einsparung_high = einsparung * 1.2 - opex
            sections['PAYBACK_MONTHS_PESSIMISTIC'] = round(capex / einsparung_low, 1) if einsparung_low > 0 else 99
            sections['PAYBACK_MONTHS_OPTIMISTIC'] = round(capex / einsparung_high, 1) if einsparung_high > 0 else 0
            
            # Logging: Business-Case-Details mit ROI-Werten
            log.info("[%s] 📊 ROI Details: ROI_12M=%.1f%% (Rate=%.2f, Low=%.1f%%, High=%.1f%%)",
                     run_id, roi_12m, sections['ROI_12M_RATE'], 
                     sections['ROI_12M_LOW'], sections['ROI_12M_HIGH'])
            log.info("[%s] 📊 Payback: Realistisch=%.1f Monate, Pessimistisch=%.1f, Optimistisch=%.1f",
                     run_id, float(answers.get('PAYBACK_MONTHS', 0)),
                     sections['PAYBACK_MONTHS_PESSIMISTIC'], sections['PAYBACK_MONTHS_OPTIMISTIC'])
        except (ValueError, ZeroDivisionError) as e:
            log.warning("[%s] ⚠️ Sensitivity calculation failed: %s", run_id, e)

        # FIX: Apply calculated values to HTML sections
        # Include both UPPERCASE (template keys) and lowercase (logical keys)
        sections_to_fix = [
            'BUSINESS_CASE_HTML',
            'business_case',
            'LEAD_BUSINESS_DETAIL',
            'EXECUTIVE_SUMMARY_HTML',
            'executive_summary',
            'QUICK_WINS_HTML',
            'quick_wins',
            'PILOT_PLAN_HTML',
            'ORG_CHANGE_HTML',
            'org_change',
            'ROADMAP_12M_HTML',
            'roadmap_12m',
            'GAMECHANGER_HTML',
            'gamechanger',
            'REIFEGRAD_SOWHAT_HTML',
            'reifegrad_sowhat',
            'RECOMMENDATIONS_HTML',
            'recommendations',
            'BUSINESS_ROI_HTML',
            'business_roi',
            'BUSINESS_COSTS_HTML',
            'business_costs',
            'FOERDERPOTENZIAL_HTML',  # Business-Case-Variablen im Förderkapitel
            'foerderpotenzial',       # Kleingeschriebene Variante
            'RESPONSIBLE_AI_HTML',     # Falls Business-Case-Variablen vorhanden
            'responsible_ai',
            'TOOLS_EMPFEHLUNGEN_HTML', # Tools-Empfehlungen können BC-Kosten referenzieren
            'tools_empfehlungen',
            'DATA_READINESS_HTML',     # Data Readiness kann BC-Investitionen referenzieren
            'data_readiness',
        ]

        # Get qw_hours_total from sections or calculate fallback
        qw_hours = sections.get('qw_hours_total', 36)

        replacements = {
            # Single-brace patterns (GPT sometimes generates these)
            '{CAPEX_REALISTISCH_EUR}': str(int(bc.get('CAPEX_REALISTISCH_EUR', 6000))),
            '{OPEX_REALISTISCH_EUR}': str(int(bc.get('OPEX_REALISTISCH_EUR', 120))),
            '{EINSPARUNG_MONAT_EUR}': str(int(bc.get('EINSPARUNG_MONAT_EUR', 4500))),
            '{PAYBACK_MONTHS}': str(round(bc.get('PAYBACK_MONTHS', 2.9), 1)),
            '{ROI_12M}': f"{bc.get('ROI_12M', 0):.1f}",  # ROI_12M ist bereits in % (z.B. 200.0)
            '{ROI_12M_EUR}': str(int(bc.get('ROI_12M_EUR', 0))),
            '{ROI_12M_LOW}': f"{sections.get('ROI_12M_LOW', 0):.1f}",
            '{ROI_12M_HIGH}': f"{sections.get('ROI_12M_HIGH', 0):.1f}",
            '{EINSPARUNG_MONAT_EUR_LOW}': str(int(sections.get('EINSPARUNG_MONAT_EUR_LOW', 0))),
            '{EINSPARUNG_MONAT_EUR_HIGH}': str(int(sections.get('EINSPARUNG_MONAT_EUR_HIGH', 0))),
            '{OPEX_REALISTISCH_EUR_LOW}': str(int(sections.get('OPEX_REALISTISCH_EUR_LOW', 0))),
            '{OPEX_REALISTISCH_EUR_HIGH}': str(int(sections.get('OPEX_REALISTISCH_EUR_HIGH', 0))),
            '{PAYBACK_MONTHS_PESSIMISTIC}': str(round(sections.get('PAYBACK_MONTHS_PESSIMISTIC', 0), 1)),
            '{PAYBACK_MONTHS_OPTIMISTIC}': str(round(sections.get('PAYBACK_MONTHS_OPTIMISTIC', 0), 1)),
            '{COMPANY_SIZE}': answers.get('unternehmensgroesse', 'solo'),
            '{qw_hours_total}': str(qw_hours),
            # Double-brace patterns (Jinja2-style that GPT may use)
            '{{CAPEX_REALISTISCH_EUR}}': str(int(bc.get('CAPEX_REALISTISCH_EUR', 6000))),
            '{{OPEX_REALISTISCH_EUR}}': str(int(bc.get('OPEX_REALISTISCH_EUR', 120))),
            '{{EINSPARUNG_MONAT_EUR}}': str(int(bc.get('EINSPARUNG_MONAT_EUR', 4500))),
            '{{PAYBACK_MONTHS}}': str(round(bc.get('PAYBACK_MONTHS', 2.9), 1)),
            '{{ROI_12M}}': f"{bc.get('ROI_12M', 0):.1f}",  # ROI_12M ist bereits in % (z.B. 200.0)
            '{{ROI_12M_LOW}}': f"{sections.get('ROI_12M_LOW', 0):.1f}",
            '{{ROI_12M_HIGH}}': f"{sections.get('ROI_12M_HIGH', 0):.1f}",
            '{{EINSPARUNG_MONAT_EUR_LOW}}': str(int(sections.get('EINSPARUNG_MONAT_EUR_LOW', 0))),
            '{{EINSPARUNG_MONAT_EUR_HIGH}}': str(int(sections.get('EINSPARUNG_MONAT_EUR_HIGH', 0))),
            '{{OPEX_REALISTISCH_EUR_LOW}}': str(int(sections.get('OPEX_REALISTISCH_EUR_LOW', 0))),
            '{{OPEX_REALISTISCH_EUR_HIGH}}': str(int(sections.get('OPEX_REALISTISCH_EUR_HIGH', 0))),
            '{{PAYBACK_MONTHS_PESSIMISTIC}}': str(round(sections.get('PAYBACK_MONTHS_PESSIMISTIC', 0), 1)),
            '{{PAYBACK_MONTHS_OPTIMISTIC}}': str(round(sections.get('PAYBACK_MONTHS_OPTIMISTIC', 0), 1)),
            '{{qw_hours_total}}': str(qw_hours),
            '{{ qw_hours_total }}': str(qw_hours),
        }

        replaced_count = 0
        replaced_sections = []
        for section_key in sections_to_fix:
            if section_key in sections and isinstance(sections[section_key], str):
                original = sections[section_key]
                for old_val, new_val in replacements.items():
                    sections[section_key] = sections[section_key].replace(old_val, new_val)
                if original != sections[section_key]:
                    replaced_count += 1
                    replaced_sections.append(section_key)

        if replaced_count > 0:
            log.info("[%s] 🔧 Business Case variables replaced in %s sections: %s", 
                     run_id, replaced_count, ", ".join(replaced_sections[:8]))
        else:
            log.warning("[%s] ⚠️ No Business Case replacements made - check if sections contain placeholders", run_id)

        sections.update(build_extra_sections(answers, scores))

    # Jinja‑ähnliche Platzhalter (z. B. {{ ROI_12M * 1.2 }}) in Sections auswerten
    try:
        sections = ksj_fix_placeholders_in_sections(sections, answers, scores)
    except Exception as _exc:
        log.warning("[%s] ⚠️ ksj_fix_placeholders_in_sections failed: %s", run_id, _exc)

    # === Placeholder-Fix (jetzt mit Business Case Variablen verfügbar!) ===
    try:
        placeholder_fix_count = 0
        for key, value in sections.items():
            if isinstance(value, str) and ("{" in value):
                fixed_value = _fix_exec_placeholders(value, scores, sections, sections.get("report_date", ""))
                if fixed_value != value:
                    sections[key] = fixed_value
                    placeholder_fix_count += 1
        if placeholder_fix_count > 0:
            log.info("[%s] 🔧 Fixed placeholders in %s sections", run_id, placeholder_fix_count)
    except Exception as _exc:
        log.warning("[%s] ⚠️ Placeholder fix failed: %s", run_id, _exc)

    # === CONTENT FILTER - Apply size-appropriate replacements ===
    from services.report_validator import (
        validate_report,
        filter_all_sections,
        # SPRINT N2: Import healing functions
        validate_and_heal,
        heal_placeholder_sections,
)


    log.info(f"[{run_id}] 🔍 Applying size-inappropriate content filter...")
    sections = filter_all_sections(sections, answers)

    # === SPRINT N2: VALIDATE AND HEAL - Wolf 2025-12 ===
    # New flow: validate_and_heal() replaces leaked content BEFORE rendering
    log.info(f"[{run_id}] 🔍 Running report validation with N2 healing...")
    is_valid, validation_errors, healed_count = validate_and_heal(sections, answers)

    if healed_count > 0:
        log.info(f"[{run_id}] 🔧 N2-Healing: Fixed {healed_count} sections")

    if not is_valid:
        log.warning(f"[{run_id}] ⚠️ Report has validation errors (see above) - continuing anyway")
        # TODO: Later enable Quality Gate:
        # raise ValueError("Report validation failed - fix errors first!")
    else:
        log.info(f"[{run_id}] ✅ Report validation passed - PLATIN++")
    # === END VALIDATION ===

    # === G22: CROSS-SECTION CONSISTENCY CHECK ===
    try:
        from services.consistency_engine import check_consistency, ConsistencyReport
        log.info(f"[{run_id}] 🔗 Running G22 cross-section consistency check...")
        consistency_report = check_consistency(sections, answers, language=sections.get("LANG", "de"))

        # Store report in sections for debugging/transparency
        sections["_CONSISTENCY_REPORT"] = consistency_report.to_dict()
        sections["_CONSISTENCY_GRADE"] = consistency_report.grade
        sections["_CONSISTENCY_SCORE"] = consistency_report.score

        if consistency_report.status == "FAIL":
            log.warning(f"[{run_id}] ⚠️ G22 Consistency: FAIL (Grade {consistency_report.grade}, Score {consistency_report.score:.1f})")
            for issue in consistency_report.issues:
                if issue.severity == "ERROR":
                    log.warning(f"[{run_id}]   [{issue.rule_id}] {issue.message}")
        elif consistency_report.status == "WARN":
            log.info(f"[{run_id}] ⚡ G22 Consistency: WARN (Grade {consistency_report.grade}, Score {consistency_report.score:.1f})")
        else:
            log.info(f"[{run_id}] ✅ G22 Consistency: PASS (Grade {consistency_report.grade}, Score {consistency_report.score:.1f})")
    except ImportError:
        log.debug(f"[{run_id}] G22 consistency_engine not available - skipping")
    except Exception as exc:
        log.warning(f"[{run_id}] ⚠️ G22 consistency check failed: {exc}")
    # === END G22 CONSISTENCY CHECK ===

    # Benchmarks / Starter-Stacks / Responsible AI
    if build_benchmarks_section:
        sections["benchmarks_html"] = build_benchmarks_section(scores)
        sections["BENCHMARKS_HTML"] = sections["benchmarks_html"]  # Uppercase alias für Kompatibilität

    if build_starter_stacks:
        sections["starter_stacks_html"] = build_starter_stacks(answers)
        sections["STARTER_STACKS_HTML"] = sections["starter_stacks_html"]  # Uppercase alias für Kompatibilität

    if build_responsible_ai_section:
        sections["responsible_ai_html"] = build_responsible_ai_section({
            "four_pillars": "knowledge/four_pillars.html",
            "legal_pitfalls": "knowledge/legal_pitfalls.html",
            "ten_20_70": "knowledge/ten_20_70.html",
            "kmu_keypoints": "knowledge/kmu_keypoints.html"
        })
        sections["RESPONSIBLE_AI_HTML"] = sections["responsible_ai_html"]  # Uppercase alias für Kompatibilität

    # Sprint N3.1: Apply content filter AGAIN to catch RESPONSIBLE_AI_HTML and other late additions
    log.info(f"[{run_id}] 🔍 Re-applying size-inappropriate content filter for late sections...")
    sections = filter_all_sections(sections, answers)

    # === SPRINT N2: Final placeholder healing before hard stop ===
    log.info(f"[{run_id}] 🔧 N2: Final placeholder healing pass...")
    final_healed = heal_placeholder_sections(sections)
    if final_healed > 0:
        log.info(f"[{run_id}] 🔧 N2: Healed {final_healed} empty sections in final pass")

    # === SPRINT N4.3: Governance Layer 2.0 / Enterprise Safety Layer ===
    if N43_GOVERNANCE_AVAILABLE and process_n43_governance:
        try:
            # Derive branch and size for N4.3
            branch_raw = (answers.get("branche", "") or "consulting").lower()
            size_raw = (answers.get("unternehmensgroesse", "") or "").lower()

            if "solo" in size_raw or "freiberuf" in size_raw:
                n43_size = "solo"
            elif "kmu" in size_raw or "11" in size_raw:
                n43_size = "kmu"
            elif "enterprise" in size_raw or "konzern" in size_raw or "251" in size_raw:
                n43_size = "enterprise"
            else:
                n43_size = "team"

            target_lang = getattr(br, "lang", "de") or "de"

            log.info(f"[{run_id}] 🛡️ N4.3: Starting Governance Layer 2.0 processing...")
            sections, n43_report = process_n43_governance(
                sections=sections,
                briefing=answers,
                branch=branch_raw,
                size=n43_size,
                target_language=target_lang,
            )

            if n43_report.dod_passed:
                log.info(f"[{run_id}] ✅ N4.3: DoD PASSED - score={n43_report.governance_score}, healed={n43_report.total_healed}")
            else:
                log.warning(f"[{run_id}] ⚠️ N4.3: DoD FAILED - conflicts={n43_report.governance_conflicts}, issues={len(n43_report.issues)}")

            # Store N4.3 metrics in sections for template access
            sections["N43_GOVERNANCE_SCORE"] = n43_report.governance_score
            sections["N43_RISK_CLASS"] = n43_report.risk_class
            sections["N43_MATURITY_LEVEL"] = n43_report.maturity_level
            sections["N43_DOD_PASSED"] = n43_report.dod_passed

        except Exception as e:
            log.error(f"[{run_id}] ❌ N4.3: Governance processing failed: {e}")
            sections["_n43_error"] = str(e)

    # === HARD STOP GATE: Validate report BEFORE rendering ===
    # Derive persona from unternehmensgroesse
    size_raw = (answers.get("unternehmensgroesse", "") or "").lower()
    if "solo" in size_raw or "freiberuf" in size_raw or "einzelunt" in size_raw:
        persona = "solo"
    elif "kmu" in size_raw or "11" in size_raw:
        persona = "kmu"
    else:
        persona = "team"

    # Execute hard stop validation
    hard_stop_if_invalid(sections, error_gate, persona=persona, run_id=run_id)

    # === SPRINT FIX: Store sections in meta for Golden Gate summary ===
    # Filter sections to only include JSON-serializable string values (HTML sections)
    # This enables /api/report/summary to validate sections_present
    serializable_sections: Dict[str, Any] = {}
    for k, v in sections.items():
        # Skip internal/debug keys and non-string values
        if k.startswith("_"):
            continue
        if isinstance(v, str) and len(v) < 500000:  # Limit size per section
            serializable_sections[k] = v
        elif isinstance(v, (int, float, bool)):
            serializable_sections[k] = v
        # Skip complex objects (GuardrailHit, dicts, etc.) to keep meta clean

    log.info(f"[{run_id}] 📦 Storing {len(serializable_sections)} sections in meta for Golden Gate")

    result = render(
        br,
        run_id=run_id,
        generated_sections=sections,
        use_fetchers=True,
        scores=scores,
        meta={
            "scores": scores,
            "score_details": score_wrap.get("details", {}),
            "research_last_updated": sections["research_last_updated"],
            "sections": serializable_sections,  # Store sections for summary gate
        }
    )

    # === G17.3: Extract Fine-Tuning Signals ===
    if FT_SIGNAL_EXTRACTION_ENABLED and extract_llm_signals and accumulate_signals:
        try:
            # Prepare report sections for signal extraction
            ft_report_sections = {
                **sections,
                **answers,
                "LANG": getattr(br, "lang", "de"),
                "_segment_key": f"{persona}_{answers.get('branche', 'other')}".lower(),
                "unternehmensgroesse": answers.get("unternehmensgroesse", ""),
                "branche": answers.get("branche", ""),
            }

            # Get validation result if available
            validation_result = None
            if error_gate:
                validation_result = {
                    "warnings": error_gate.warnings,
                    "fallback_count": error_gate.fallback_count,
                    "sections_failed": error_gate.sections_failed,
                }

            # Get predictive output if available
            predictive_output = sections.get("_predictive_output")

            # Get segment stats if available
            segment_stats = None
            try:
                from services.feedback_analyzer import get_segment_for_report
                segment_stats = get_segment_for_report(ft_report_sections)
            except Exception:
                pass

            # Extract signals with full context
            ft_signals = extract_llm_signals(
                report_sections=ft_report_sections,
                validation_result=validation_result,
                predictive_output=predictive_output,
                segment_stats=segment_stats,
            )

            if ft_signals:
                # Accumulate to daily queue file
                accumulated_count = accumulate_signals(ft_signals)
                log.info("[%s] 📊 Extracted %d FT signals, accumulated %d", run_id, len(ft_signals), accumulated_count)

                # Optionally build dataset on each report
                if FT_BUILD_DATASET_ON_REPORT and build_training_dataset:
                    build_training_dataset()

                # === G17.4: Auto-Prompt-Rewrite Engine ===
                try:
                    from services.prompt_rewrite_engine import (
                        PROMPT_REWRITE_ENGINE_ENABLED,
                        detect_prompt_weaknesses,
                        generate_prompt_rewrite_suggestions,
                        store_suggestions,
                    )

                    if PROMPT_REWRITE_ENGINE_ENABLED:
                        # Get prompt text for the current section (simplified - uses section data)
                        prompt_context = ft_report_sections.get("_prompt_context", "")

                        # Detect weaknesses based on signals
                        validation_warnings_raw = validation_result.get("warnings", []) if validation_result else []
                        validation_warnings_list: List[Dict[str, Any]] = validation_warnings_raw if isinstance(validation_warnings_raw, list) else []
                        issues = detect_prompt_weaknesses(
                            prompt_text=prompt_context,
                            aggregated_signals=ft_signals,
                            segment_stats=segment_stats,
                            validation_warnings=validation_warnings_list,
                        )

                        # Generate rewrite suggestions
                        if issues.get("issues"):
                            suggestions = generate_prompt_rewrite_suggestions(
                                issues=issues.get("issues", []),
                                aggregated_signals=ft_signals,
                                segment_stats=segment_stats,
                                predictive_output=predictive_output,
                            )

                            if suggestions:
                                store_suggestions(suggestions)
                                log.info("[%s] 📝 Generated %d prompt rewrite suggestions", run_id, len(suggestions))
                except ImportError:
                    pass  # G17.4 not available
                except Exception as rewrite_exc:
                    log.warning("[%s] ⚠️ Prompt rewrite engine failed: %s", run_id, rewrite_exc)

        except Exception as ft_exc:
            log.warning("[%s] ⚠️ FT signal extraction failed: %s", run_id, ft_exc)

    an = Analysis(
        user_id=br.user_id, 
        briefing_id=briefing_id, 
        html=result["html"], 
        meta=result.get("meta", {}), 
        created_at=datetime.now(timezone.utc)
    )
    db.add(an)
    db.commit()
    db.refresh(an)
    
    log.info("[%s] ✅ Analysis created (v5.3.0-PLATIN+++): id=%s", run_id, an.id)
    return an.id, result["html"], result.get("meta", {})

# -------------------- briefing summary for admin ----------------
def _build_briefing_summary_html(br: Briefing, rep: Report, user_email: str) -> str:
    """Build HTML summary of briefing for admin email"""
    answers = getattr(br, "answers", {}) or {}

    # Key metrics
    metrics = f"""
    <div style="background:#f8f9fa;padding:16px;border-radius:8px;margin:16px 0">
        <h3 style="margin:0 0 12px 0;color:#111827">📊 Briefing-Übersicht</h3>
        <table style="width:100%;border-collapse:collapse">
            <tr><td><b>Briefing ID:</b></td><td>{br.id}</td></tr>
            <tr><td><b>Analysis ID:</b></td><td>{getattr(rep, 'analysis_id', 'N/A')}</td></tr>
            <tr><td><b>User:</b></td><td>{user_email}</td></tr>
            <tr><td><b>Erstellt:</b></td><td>{getattr(br, 'created_at', 'N/A')}</td></tr>
            <tr><td><b>Sprache:</b></td><td>{getattr(br, 'lang', 'de')}</td></tr>
        </table>
    </div>
    """

    # Scores
    scores_html = f"""
    <div style="background:#eff6ff;padding:16px;border-radius:8px;margin:16px 0">
        <h3 style="margin:0 0 12px 0;color:#1e40af">🎯 Scores</h3>
        <table style="width:100%;border-collapse:collapse">
            <tr><td><b>Gesamt:</b></td><td>{getattr(rep, 'score_overall', 0)}/100</td></tr>
            <tr><td><b>Governance:</b></td><td>{getattr(rep, 'score_governance', 0)}/100</td></tr>
            <tr><td><b>Sicherheit:</b></td><td>{getattr(rep, 'score_security', 0)}/100</td></tr>
            <tr><td><b>Wertschöpfung:</b></td><td>{getattr(rep, 'score_value', 0)}/100</td></tr>
            <tr><td><b>Befähigung:</b></td><td>{getattr(rep, 'score_enablement', 0)}/100</td></tr>
        </table>
    </div>
    """

    # Key answers (top 10 most important)
    key_fields = {
        "branche": "Branche",
        "unternehmensgroesse": "Unternehmensgröße",
        "bundesland": "Bundesland",
        "hauptleistung": "Hauptleistung",
        "ai_experience": "KI-Erfahrung",
        "ai_budget": "KI-Budget",
        "data_quality": "Datenqualität",
        "gdpr_aware": "DSGVO-Bewusstsein",
        "ai_goals": "KI-Ziele",
        "biggest_challenge": "Größte Herausforderung",
    }

    answers_rows = []
    for key, label in key_fields.items():
        value = answers.get(key, "—")
        if value and value != "—":
            # Truncate long values
            if isinstance(value, str) and len(value) > 80:
                value = value[:77] + "..."
            answers_rows.append(f"<tr><td><b>{label}:</b></td><td>{html.escape(str(value))}</td></tr>")

    answers_html = f"""
    <div style="background:#fef3c7;padding:16px;border-radius:8px;margin:16px 0">
        <h3 style="margin:0 0 12px 0;color:#92400e">📝 Wichtige Antworten</h3>
        <table style="width:100%;border-collapse:collapse">
            {''.join(answers_rows)}
        </table>
        <p style="margin:8px 0 0 0;font-size:12px;color:#78716c">
            <i>Vollständige Antworten siehe JSON-Attachment</i>
        </p>
    </div>
    """

    return metrics + scores_html + answers_html

# -------------------- runner (kept from original) ----------------
def _fetch_pdf_if_needed(pdf_url: Optional[str], pdf_bytes: Optional[bytes]) -> Optional[bytes]:
    if pdf_bytes: return pdf_bytes
    if not pdf_url: return None

    # SECURITY: Validate URL to prevent SSRF attacks
    if not _sanitize_url(pdf_url):
        log.error("Invalid or unsafe PDF URL, rejecting: %s", pdf_url[:100])
        return None

    try:
        r = requests.get(pdf_url, timeout=30)
        if r.ok:
            return bytes(r.content)
    except Exception as e:
        log.warning("Failed to fetch PDF from URL: %s", str(e)[:100])
        return None
    return None

def _send_emails(db: Session, rep: Report, br: Briefing, pdf_url: Optional[str], pdf_bytes: Optional[bytes], run_id: str) -> None:
    """Send emails via Resend API"""
    # Global Email Kill-Switch
    if os.getenv("DISABLE_EMAILS", "").lower() in ("1", "true", "yes", "on"):
        log.info("[%s] 📧 Emails disabled via DISABLE_EMAILS=1. Skipping user/admin email send.", run_id)
        return

    best_pdf = _fetch_pdf_if_needed(pdf_url, pdf_bytes)
    attachments_admin: List[Dict[str, Any]] = []
    if best_pdf:
        attachments_admin.append({
            "filename": f"KI-Status-Report-{getattr(rep, 'id', None)}.pdf", 
            "content": best_pdf, 
            "mimetype": "application/pdf"
        })
    try:
        # Build comprehensive briefing data with metadata for admin review
        user_email = _determine_user_email(db, br, getattr(rep, "user_email", None)) or "unknown"

        briefing_data = {
            "briefing_id": br.id,
            "analysis_id": getattr(rep, "analysis_id", None),
            "user_email": user_email,
            "created_at": str(getattr(br, "created_at", "")),
            "lang": getattr(br, "lang", "de"),
            "scores": {
                "overall": getattr(rep, "score_overall", 0),
                "governance": getattr(rep, "score_governance", 0),
                "security": getattr(rep, "score_security", 0),
                "value": getattr(rep, "score_value", 0),
                "enablement": getattr(rep, "score_enablement", 0),
            },
            "answers": getattr(br, "answers", {}) or {},
        }

        bjson = json.dumps(briefing_data, ensure_ascii=False, indent=2).encode("utf-8")
        attachments_admin.append({
            "filename": f"briefing-{br.id}-full.json",
            "content": bjson,
            "mimetype": "application/json"
        })
        log.info("[%s] 📎 Added briefing JSON attachment for admin (%d bytes)", run_id, len(bjson))
    except Exception as e:
        log.warning("[%s] ⚠️ Could not create briefing JSON attachment: %s", run_id, str(e))
    
    # Send to user
    try:
        user_email = None
        try: 
            user_email = _determine_user_email(db, br, getattr(rep, "user_email", None))
        except Exception: 
            user_email = None
        
        if user_email:
            user_attachments = [] if pdf_url else attachments_admin[:1]
            ok, err = _send_email_via_resend(
                user_email, 
                "Ihr KI‑Status‑Report ist fertig", 
                render_report_ready_email(recipient="user", pdf_url=pdf_url),
                attachments=user_attachments
            )
            if ok: 
                log.info("[%s] 📧 Mail sent to user %s via Resend", run_id, _mask_email(user_email))
            else: 
                log.warning("[%s] ⚠️ MAIL_USER failed: %s", run_id, err)
    except Exception as exc:
        log.warning("[%s] ⚠️ MAIL_USER failed: %s", run_id, exc)
    
    # Send to admins
    try:
        if os.getenv("ENABLE_ADMIN_NOTIFY", "1") in ("1","true","TRUE","yes","YES"):
            # Generate briefing summary HTML for admin emails
            briefing_summary_html = None
            try:
                briefing_summary_html = _build_briefing_summary_html(br, rep, user_email or "unknown")
                log.info("[%s] 📋 Generated briefing summary HTML for admin email", run_id)
            except Exception as e:
                log.warning("[%s] ⚠️ Could not generate briefing summary HTML: %s", run_id, str(e))

            for addr in _admin_recipients():
                ok, err = _send_email_via_resend(
                    addr,
                    f"Neuer KI‑Status‑Report – Analysis #{rep.analysis_id} / Briefing #{rep.briefing_id}",
                    render_report_ready_email(
                        recipient="admin",
                        pdf_url=pdf_url,
                        briefing_summary_html=briefing_summary_html
                    ),
                    attachments=attachments_admin
                )
                if ok:
                    log.info("[%s] 📧 Admin notify sent to %s via Resend", run_id, _mask_email(addr))
                else:
                    log.warning("[%s] ⚠️ MAIL_ADMIN failed for %s: %s", run_id, _mask_email(addr), err)
    except Exception as exc:
        log.warning("[%s] ⚠️ MAIL_ADMIN block failed: %s", run_id, exc)

def run_analysis_for_briefing(briefing_id: int, email: Optional[str] = None) -> None:
    """Public API: Start analysis for a briefing (called from routes/briefings.py)"""
    run_async(briefing_id, email)


def run_briefing_pipeline(db: Session, briefing_id: int, email: Optional[str] = None, run_id: Optional[str] = None) -> None:
    """
    Execute the full briefing analysis pipeline (LLM + PDF + Email).

    Called by the worker process. Expects an external DB session and handles
    all processing without managing session lifecycle.

    Args:
        db: SQLAlchemy session (managed by caller/worker)
        briefing_id: ID of the briefing to process
        email: Optional user email for notifications
        run_id: Optional run ID for logging (generated if not provided)

    Raises:
        ValueError: If briefing not found or PDF generation fails
        Exception: Any error during analysis/PDF/email
    """
    if not run_id:
        run_id = f"worker-{uuid.uuid4().hex[:8]}"

    rep: Optional[Report] = None
    try:
        log.info("[%s] 🚀 Starting analysis v5.3.0-PLATIN+++ for briefing_id=%s (worker mode)", run_id, briefing_id)

        # Core analysis pipeline
        an_id, html, meta = analyze_briefing(db, briefing_id, run_id=run_id)

        br = db.get(Briefing, briefing_id)
        if not br:
            raise ValueError(f"Briefing {briefing_id} not found after analysis")

        # Create Report record
        rep = Report(
            user_id=br.user_id if br else None,
            briefing_id=briefing_id,
            analysis_id=an_id,
            created_at=datetime.now(timezone.utc)
        )
        if hasattr(rep, "user_email"):
            rep.user_email = (email or "")
        if hasattr(rep, "task_id"):
            rep.task_id = f"worker-{uuid.uuid4()}"
        if hasattr(rep, "status"):
            rep.status = "pending"
        db.add(rep)
        db.commit()
        db.refresh(rep)

        # PDF generation with footer
        if DBG_PDF:
            log.debug("[%s] 📄 pdf_render start", run_id)

        # Build PDF options with footer template (page numbers + report metadata)
        footer_template = build_footer_template(
            report_id=meta.get("report_id", ""),
            report_date=meta.get("report_date", "")
        )
        pdf_options = {
            "format": "A4",
            "printBackground": True,
            "displayHeaderFooter": True,
            "headerTemplate": "<div></div>",
            "footerTemplate": footer_template,
            "margin": {"top": "12mm", "right": "12mm", "bottom": "20mm", "left": "12mm"}
        }

        pdf_info = render_pdf_from_html(
            html,
            meta={"analysis_id": an_id, "briefing_id": briefing_id, "run_id": run_id},
            pdf_options=pdf_options
        )
        pdf_url = pdf_info.get("pdf_url")
        pdf_bytes = pdf_info.get("pdf_bytes")
        pdf_error = pdf_info.get("error")
        if DBG_PDF:
            log.debug("[%s] 📄 pdf_render done url=%s bytes=%s error=%s", run_id, bool(pdf_url), len(pdf_bytes or b""), pdf_error)

        if not pdf_url and not pdf_bytes:
            error_msg = f"PDF failed: {pdf_error or 'no output'}"
            log.error("[%s] ❌ %s", run_id, error_msg)
            if hasattr(rep, "status"):
                rep.status = "failed"
            if hasattr(rep, "email_error_user"):
                rep.email_error_user = error_msg
            if hasattr(rep, "updated_at"):
                rep.updated_at = datetime.now(timezone.utc)
            db.add(rep)
            db.commit()
            raise ValueError(error_msg)

        # Update Report with PDF info
        if hasattr(rep, "pdf_url"):
            rep.pdf_url = pdf_url
        if hasattr(rep, "pdf_bytes_len") and pdf_bytes:
            rep.pdf_bytes_len = len(pdf_bytes)
        if hasattr(rep, "status"):
            rep.status = "done"
        if hasattr(rep, "updated_at"):
            rep.updated_at = datetime.now(timezone.utc)
        db.add(rep)
        db.commit()
        db.refresh(rep)

        # Send notification emails
        _send_emails(db, rep, br, pdf_url, pdf_bytes, run_id)

        log.info("[%s] ✅ Pipeline complete for briefing_id=%s", run_id, briefing_id)

    except Exception as exc:
        log.error("[%s] ❌ Pipeline failed: %s", run_id, exc, exc_info=True)
        if rep and hasattr(rep, "status"):
            rep.status = "failed"
            if hasattr(rep, "email_error_user"):
                rep.email_error_user = str(exc)
            if hasattr(rep, "updated_at"):
                rep.updated_at = datetime.now(timezone.utc)
            db.add(rep)
            db.commit()
        raise


def run_async(briefing_id: int, email: Optional[str] = None) -> None:
    run_id = f"run-{uuid.uuid4().hex[:8]}"

    db = core_db.SessionLocal()
    rep: Optional[Report] = None
    try:
        log.info("[%s] 🚀 Starting analysis v5.3.0-PLATIN+++ for briefing_id=%s", run_id, briefing_id)
        an_id, html, meta = analyze_briefing(db, briefing_id, run_id=run_id)
        br = db.get(Briefing, briefing_id)
        rep = Report(
            user_id=br.user_id if br else None, 
            briefing_id=briefing_id, 
            analysis_id=an_id, 
            created_at=datetime.now(timezone.utc)
        )
        if hasattr(rep, "user_email"): 
            rep.user_email = (email or "")
        if hasattr(rep, "task_id"): 
            rep.task_id = f"local-{uuid.uuid4()}"
        if hasattr(rep, "status"): 
            rep.status = "pending"
        db.add(rep)
        db.commit()
        db.refresh(rep)
        
        # PDF generation with footer
        if DBG_PDF:
            log.debug("[%s] 📄 pdf_render start", run_id)

        # Build PDF options with footer template (page numbers + report metadata)
        footer_template = build_footer_template(
            report_id=meta.get("report_id", ""),
            report_date=meta.get("report_date", "")
        )
        pdf_options = {
            "format": "A4",
            "printBackground": True,
            "displayHeaderFooter": True,
            "headerTemplate": "<div></div>",
            "footerTemplate": footer_template,
            "margin": {"top": "12mm", "right": "12mm", "bottom": "20mm", "left": "12mm"}
        }

        pdf_info = render_pdf_from_html(
            html,
            meta={"analysis_id": an_id, "briefing_id": briefing_id, "run_id": run_id},
            pdf_options=pdf_options
        )
        pdf_url = pdf_info.get("pdf_url")
        pdf_bytes = pdf_info.get("pdf_bytes")
        pdf_error = pdf_info.get("error")
        if DBG_PDF:
            log.debug("[%s] 📄 pdf_render done url=%s bytes=%s error=%s", run_id, bool(pdf_url), len(pdf_bytes or b""), pdf_error)
        
        if not pdf_url and not pdf_bytes:
            error_msg = f"PDF failed: {pdf_error or 'no output'}"
            log.error("[%s] ❌ %s", run_id, error_msg)
            if hasattr(rep, "status"): 
                rep.status = "failed"
            if hasattr(rep, "email_error_user"): 
                rep.email_error_user = error_msg
            if hasattr(rep, "updated_at"): 
                rep.updated_at = datetime.now(timezone.utc)
            db.add(rep)
            db.commit()
            raise ValueError(error_msg)
        
        if hasattr(rep, "pdf_url"): 
            rep.pdf_url = pdf_url
        if hasattr(rep, "pdf_bytes_len") and pdf_bytes: 
            rep.pdf_bytes_len = len(pdf_bytes)
        if hasattr(rep, "status"): 
            rep.status = "done"
        if hasattr(rep, "updated_at"): 
            rep.updated_at = datetime.now(timezone.utc)
        db.add(rep)
        db.commit()
        db.refresh(rep)
        
        _send_emails(db, rep, br, pdf_url, pdf_bytes, run_id)
        
    except Exception as exc:
        log.error("[%s] ❌ Analysis failed: %s", run_id, exc, exc_info=True)
        if rep and hasattr(rep, "status"):
            rep.status = "failed"
            if hasattr(rep, "email_error_user"): 
                rep.email_error_user = str(exc)
            if hasattr(rep, "updated_at"): 
                rep.updated_at = datetime.now(timezone.utc)
            db.add(rep)
            db.commit()
        raise
    finally:
        db.close()

def _section_temperature(section_name: str) -> float:
    """Per‑Sektion‑Temperatur. Default = OPENAI_TEMPERATURE; Gamechanger 0.35–0.45."""
    try:
        if section_name == "gamechanger":
            # env overrides allowed
            return float(os.getenv("TEMP_GAMECHANGER", os.getenv("OPENAI_TEMPERATURE_GAMECHANGER", "0.4")))
    except Exception:
        pass
    try:
        return float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    except Exception:
        return 0.2


def _fix_exec_placeholders(html_block: str, scores: Dict[str, Any], sections: Dict[str, Any], report_date: str) -> str:
    """Ersetzt eventuell mit-ausgegebenen Prompt-Platzhalter in der Executive Summary (Robustheits-Fix).

    FIX: Ersetzt BEIDE Varianten - mit doppelten {{}} UND einfachen {} geschweiften Klammern,
    da GPT manchmal einfache Klammern zurückgibt.

    Args:
        html_block: HTML-String zum Fixen
        scores: Score-Dictionary
        sections: Sections-Dictionary mit allen verfügbaren Werten
        report_date: Berichtsdatum
    """
    if not html_block:
        return html_block

    # Mapping: Platzhalter -> Wert (aus sections oder scores)
    replacements = {
        "heute_iso": report_date,
        "report_date": report_date,
        "score_gov": str(scores.get("governance", 0)),
        "score_sec": str(scores.get("security", 0)),
        "score_val": str(scores.get("value", 0)),
        "score_enable": str(scores.get("enablement", 0)),
        "score_gesamt": str(scores.get("overall", 0)),
        "score_governance": str(scores.get("governance", 0)),
        "score_sicherheit": str(scores.get("security", 0)),
        "score_nutzen": str(scores.get("value", 0)),
        "score_befaehigung": str(scores.get("enablement", 0)),
        "BRANCHE_LABEL": sections.get("BRANCHE_LABEL", ""),
        "UNTERNEHMENSGROESSE_LABEL": sections.get("UNTERNEHMENSGROESSE_LABEL", ""),
        "BUNDESLAND_LABEL": sections.get("BUNDESLAND_LABEL", ""),
        "HAUPTLEISTUNG": sections.get("HAUPTLEISTUNG", ""),
        "report_year": sections.get("report_year", ""),
        "report_month": sections.get("report_month", ""),
        "kundencode": sections.get("kundencode", ""),
        "report_id": sections.get("report_id", ""),
        "KI_PROJEKTE": sections.get("ki_projekte", ""),
        "IT_INFRASTRUKTUR_LABEL": sections.get("IT_INFRASTRUKTUR_LABEL", ""),
        "PROZESSE_PAPIERLOS_LABEL": sections.get("PROZESSE_PAPIERLOS_LABEL", ""),
        "AUTOMATISIERUNGSGRAD_LABEL": sections.get("AUTOMATISIERUNGSGRAD_LABEL", ""),
        "ZEITERSPARNIS_PRIORITAET_LABEL": sections.get("ZEITERSPARNIS_PRIORITAET_LABEL", ""),
        "GESCHAEFTSMODELL_EVOLUTION": sections.get("GESCHAEFTSMODELL_EVOLUTION", ""),
        "research_last_updated": sections.get("research_last_updated", ""),
        "STRATEGISCHE_ZIELE": sections.get("STRATEGISCHE_ZIELE", ""),
        "ROADMAP_VORHANDEN_LABEL": sections.get("ROADMAP_VORHANDEN_LABEL", ""),
        "GOVERNANCE_RICHTLINIEN_LABEL": sections.get("GOVERNANCE_RICHTLINIEN_LABEL", ""),
        "CHANGE_MANAGEMENT_LABEL": sections.get("CHANGE_MANAGEMENT_LABEL", ""),
        # Business Case variables (ROI_12M ist bereits in %, KEINE zusätzliche *100 Multiplikation!)
        "CAPEX_REALISTISCH_EUR": str(int(sections.get("CAPEX_REALISTISCH_EUR", 6000) or 6000)),
        "OPEX_REALISTISCH_EUR": str(int(sections.get("OPEX_REALISTISCH_EUR", 120) or 120)),
        "EINSPARUNG_MONAT_EUR": str(int(sections.get("EINSPARUNG_MONAT_EUR", 4500) or 4500)),
        "PAYBACK_MONTHS": str(round(float(sections.get("PAYBACK_MONTHS", 2.9) or 2.9), 1)),
        "ROI_12M": f"{float(sections.get('ROI_12M', 0) or 0):.1f}",  # Bereits in % (z.B. 200.0)
        "ROI_12M_LOW": f"{float(sections.get('ROI_12M_LOW', 0) or 0):.1f}",
        "ROI_12M_HIGH": f"{float(sections.get('ROI_12M_HIGH', 0) or 0):.1f}",
        "EINSPARUNG_MONAT_EUR_LOW": str(int(sections.get("EINSPARUNG_MONAT_EUR_LOW", 0) or 0)),
        "EINSPARUNG_MONAT_EUR_HIGH": str(int(sections.get("EINSPARUNG_MONAT_EUR_HIGH", 0) or 0)),
        "OPEX_REALISTISCH_EUR_LOW": str(int(sections.get("OPEX_REALISTISCH_EUR_LOW", 0) or 0)),
        "OPEX_REALISTISCH_EUR_HIGH": str(int(sections.get("OPEX_REALISTISCH_EUR_HIGH", 0) or 0)),
        "PAYBACK_MONTHS_PESSIMISTIC": str(round(float(sections.get("PAYBACK_MONTHS_PESSIMISTIC", 0) or 0), 1)),
        "PAYBACK_MONTHS_OPTIMISTIC": str(round(float(sections.get("PAYBACK_MONTHS_OPTIMISTIC", 0) or 0), 1)),
        "qw_hours_total": str(sections.get("qw_hours_total", 36)),
    }

    fixed = html_block
    for placeholder, value in replacements.items():
        # Ersetze BEIDE Varianten: {{placeholder}} UND {placeholder}
        fixed = fixed.replace(f"{{{{{placeholder}}}}}", str(value))  # Doppelte {{}}
        fixed = fixed.replace(f"{{{placeholder}}}", str(value))       # Einfache {}

    # Entferne fälschlich von GPT kopierte Template-Platzhalter (sollten nie im Output sein!)
    template_placeholders = [
        "TOOLS_TABLE_HTML", "FUNDING_TABLE_HTML", "NEWS_BOX_HTML",
        "TOOLS_HTML", "FUNDING_HTML", "FOERDERPROGRAMME_HTML"
    ]
    for tpl in template_placeholders:
        fixed = fixed.replace(f"{{{{{tpl}}}}}", "")  # Doppelte {{}}
        fixed = fixed.replace(f"{{{tpl}}}", "")       # Einfache {}

    return fixed