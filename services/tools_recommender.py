# -*- coding: utf-8 -*-
"""
Sprint B2-B: Tools Recommendation Engine 2.0
=============================================

Enhanced tools recommendation with:
- Real-World Weighted Recommendation
- Predictive Trend Engine
- Smart Defaults Integration
- Adoption Cards (HTML)

Based on Premium-Funding patterns from Sprint B1.

Version: 2.0.0 (Sprint B2)
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ._normalize import _briefing_to_dict
# KIS-1292 (Stufe 4): Sparten-Feld in den Werkzeugdaten
from .medien_sparte import passt_zur_sparte as _passt_zur_sparte, slug as _sparte_slug

# Import analytics layer
try:
    from services.tools_analytics import (
        TOOLS_ENGINE_ENABLED,
        TOOLS_CONFIDENCE_MIN,
        TOOLS_MAX_RECOMMENDATIONS,
        TOOLS_MIN_SAMPLE_SIZE,
        ToolSegmentStats,
        get_tool_stats,
        get_top_tools,
        get_segment_analysis,
        get_co_occurring_tools,
        calculate_ai_act_alignment,
        calculate_persona_fit,
        calculate_tool_confidence,
    )
    _HAS_ANALYTICS = True
except ImportError:
    _HAS_ANALYTICS = False
    TOOLS_ENGINE_ENABLED = True
    TOOLS_CONFIDENCE_MIN = 0.35
    TOOLS_MAX_RECOMMENDATIONS = 12
    TOOLS_MIN_SAMPLE_SIZE = 5

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION (ENV)
# =============================================================================

TOOLS_CONFIDENCE_SHOW_BADGES = os.environ.get("TOOLS_CONFIDENCE_SHOW_BADGES", "1") == "1"
TOOLS_PREDICTIVE_ENABLED = os.environ.get("TOOLS_PREDICTIVE_ENABLED", "1") == "1"
TOOLS_PREDICTIVE_TREND_WINDOW = int(os.environ.get("TOOLS_PREDICTIVE_TREND_WINDOW", "30"))
TOOLS_TREND_WEIGHT = float(os.environ.get("TOOLS_TREND_WEIGHT", "0.3"))
TOOLS_GENERIC_FALLBACK_ENABLED = os.environ.get("TOOLS_GENERIC_FALLBACK_ENABLED", "1") == "1"
TOOLS_SMART_DEFAULTS_ENABLED = os.environ.get("TOOLS_SMART_DEFAULTS_ENABLED", "1") == "1"
DASHBOARD_TOOLS_ENABLED = os.environ.get("DASHBOARD_TOOLS_ENABLED", "1") == "1"

# Storage for trend data
TOOLS_TREND_STORAGE_PATH = os.environ.get(
    "TOOLS_TREND_STORAGE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "storage", "tools_trends")
)

# =============================================================================
# CURATED SEED DATA
# =============================================================================

# Notfall-Ausweichliste: greift nur, wenn data/tools_seed.json fehlt oder
# nicht lesbar ist. Der Tool-Radar prueft sie NICHT — er kennt nur die
# Seed-Datei. Damit sie nicht unbemerkt veraltet, haelt
# tests/test_kis1278_zweite_toolliste.py fest: Wo beide Listen dasselbe
# Werkzeug fuehren, muessen url und trust_url uebereinstimmen.
DEFAULT_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "Tally.so",
        "url": "https://tally.so",
        "trust_url": "https://tally.so/help/privacy-policy",
        "category": "Fragebogen / Intake",
        "price": "0-29 EUR/Monat",
        "gdpr": "EU/US (DPA)",
        "host": "EU/US",
        "best_for_size": ["solo", "team", "kmu"],
        "best_for_industries": ["beratung", "dienstleistungen", "marketing"],
    },
    {
        "name": "Make (Integromat)",
        "url": "https://www.make.com",
        "trust_url": "https://www.make.com/en/privacy-notice",
        "category": "Workflow-Automation",
        "price": "Free + Plans",
        "gdpr": "EU/US (DPA)",
        "host": "EU/US",
        "best_for_size": ["solo", "team", "kmu"],
        "best_for_industries": ["alle"],
    },
    {
        "name": "Notion",
        "url": "https://www.notion.so",
        "trust_url": "https://www.notion.so/help/privacy",
        "category": "Wissensmanagement / Docs",
        "price": "0-8 EUR/User",
        "gdpr": "US (DPA, SOC2)",
        "host": "US/EU",
        "best_for_size": ["team", "kmu"],
        "best_for_industries": ["alle"],
    },
    {
        "name": "Perplexity",
        "url": "https://www.perplexity.ai",
        "trust_url": "https://www.perplexity.ai/privacy",
        "category": "Antwort-/Recherche-API",
        "price": "Usage/Pro",
        "gdpr": "US (Vendor-Assessment)",
        "host": "US",
        "best_for_size": ["solo", "kmu"],
        "best_for_industries": ["beratung", "dienstleistungen", "marketing", "it"],
    },
    {
        "name": "Tavily",
        "url": "https://www.tavily.com",
        "trust_url": "https://www.tavily.com/privacy",
        "category": "Web-Recherche (API)",
        "price": "Usage",
        "gdpr": "US (Vendor-Assessment)",
        "host": "US",
        "best_for_size": ["solo", "team", "kmu"],
        "best_for_industries": ["alle"],
    },
    {
        "name": "Claude API",
        "url": "https://www.anthropic.com",
        "trust_url": "https://www.anthropic.com/privacy",
        "category": "KI-API",
        "price": "Usage-basiert",
        "gdpr": "US (DPA)",
        "host": "US",
        "best_for_size": ["solo", "team", "kmu"],
        "best_for_industries": ["alle"],
    },
    {
        "name": "Mistral AI",
        "url": "https://mistral.ai",
        "trust_url": "https://legal.mistral.ai/terms/privacy-policy",
        "category": "KI-API (EU)",
        "price": "Usage-basiert",
        "gdpr": "EU-Anbieter",
        "host": "EU",
        "best_for_size": ["solo", "team", "kmu"],
        "best_for_industries": ["alle"],
    },
    {
        "name": "Slack",
        "url": "https://slack.com",
        "trust_url": "https://slack.com/trust/privacy",
        "category": "Team-Kommunikation",
        "price": "Free + Plans",
        "gdpr": "EU (DPA)",
        "host": "EU/US",
        "best_for_size": ["team", "kmu"],
        "best_for_industries": ["alle"],
    },
    {
        "name": "HubSpot",
        "url": "https://www.hubspot.de",
        "trust_url": "https://legal.hubspot.com/privacy-policy",
        "category": "CRM / Sales",
        "price": "Free / ab 18 EUR/Monat",
        "gdpr": "AVV verfügbar",
        "host": "EU/US",
        "best_for_size": ["team", "kmu"],
        "best_for_industries": ["beratung", "dienstleistungen", "handel"],
    },
    {
        "name": "DataDog",
        "url": "https://www.datadoghq.com",
        "trust_url": "https://www.datadoghq.com/legal/privacy/",
        "category": "Monitoring / Observability",
        "price": "ab 15 USD/Host",
        "gdpr": "EU (DPA)",
        "host": "EU/US",
        "best_for_size": ["kmu"],
        "best_for_industries": ["it", "dienstleistungen"],
    },
    {
        "name": "Great Expectations",
        "url": "https://greatexpectations.io",
        "trust_url": "https://greatexpectations.io/privacy",
        "category": "Data Quality",
        "price": "Open Source + Enterprise",
        "gdpr": "Self-hosted möglich",
        "host": "Self/Cloud",
        "best_for_size": ["kmu"],
        "best_for_industries": ["it", "dienstleistungen", "handel"],
    },
    {
        "name": "MLflow",
        "url": "https://mlflow.org",
        "trust_url": "https://mlflow.org/docs/latest/index.html",
        "category": "ML Lifecycle / Governance",
        "price": "Open Source",
        "gdpr": "Self-hosted",
        "host": "Self",
        "best_for_size": ["kmu"],
        "best_for_industries": ["it", "manufacturing"],
    },
]


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ToolTrend:
    """Predictive trend data for a tool."""
    tool_name: str
    trend_30d: float = 0.0  # -1.0 to +1.0
    trend_60d: float = 0.0
    trend_90d: float = 0.0
    sample_count_30d: int = 0
    sample_count_60d: int = 0
    sample_count_90d: int = 0
    trend_direction: str = "stable"  # rising, stable, declining
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ToolRecommendation:
    """Single tool recommendation with metadata."""
    tool_name: str
    url: str
    trust_url: str
    category: str
    price: str
    gdpr: str
    host: str
    final_score: float = 0.0
    confidence: float = 0.0
    confidence_level: str = "medium"
    segment_stability: str = "medium"
    ai_act_alignment: float = 0.0
    persona_fit: float = 0.0
    trend: float = 0.0
    trend_direction: str = "stable"
    tuning_factor: float = 1.0
    rank: int = 0


@dataclass
class ToolsRecommendationResult:
    """Complete recommendation result."""
    recommendations: List[ToolRecommendation] = field(default_factory=list)
    segment_context: Dict[str, str] = field(default_factory=dict)
    segment_stability: str = "medium"
    fallback_used: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    insights: List[Dict[str, Any]] = field(default_factory=list)


# =============================================================================
# SMART DEFAULTS
# =============================================================================

SMART_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "solo": {
        "focus": "automation",
        "priorities": ["workflow_automation", "ai_assistants", "productivity"],
        "max_tools": 8,
        "description": "Fokus auf Automatisierungs-Tools für Einzelunternehmer",
        "recommended_categories": [
            "Workflow-Automation",
            "KI-API",
            "Antwort-/Recherche-API",
            "Fragebogen / Intake"
        ]
    },
    "team": {
        "focus": "collaboration",
        "priorities": ["collaboration", "documentation", "project_management"],
        "max_tools": 10,
        "description": "Fokus auf Kollaboration + Dokumentation für Teams",
        "recommended_categories": [
            "Team-Kommunikation",
            "Wissensmanagement / Docs",
            "CRM / Sales",
            "Workflow-Automation"
        ]
    },
    "kmu": {
        "focus": "governance",
        "priorities": ["data_quality", "governance", "analytics", "security"],
        "max_tools": 12,
        "description": "Fokus auf Data Quality + Governance für KMU",
        "recommended_categories": [
            "Data Quality",
            "ML Lifecycle / Governance",
            "Monitoring / Observability",
            "CRM / Sales"
        ]
    }
}


# =============================================================================
# SEED DATA LOADER
# =============================================================================

def _load_seed() -> List[Dict[str, Any]]:
    """Load tools from seed file or default.

    KIS-1278: Der Pfad war relativ und hing damit am
    Arbeitsverzeichnis des Prozesses. Steht das woanders,
    findet der Code die Datei nicht, faellt still auf DEFAULT_TOOLS
    zurueck — 12 statt 23 Tools, mit Preisen und Trust-URLs, die niemand
    pflegt und die der Tool-Radar nicht prueft. Kein Fehler im Log, nur
    ein schlechterer Report.
    """
    seed_file = Path(__file__).resolve().parent.parent / "data" / "tools_seed.json"
    if seed_file.exists():
        try:
            data = json.loads(seed_file.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else DEFAULT_TOOLS
        except Exception:
            pass
    return DEFAULT_TOOLS


# =============================================================================
# TREND ENGINE
# =============================================================================

_tool_trends: Dict[str, ToolTrend] = {}


def _load_trends() -> Dict[str, ToolTrend]:
    """Load trend data from storage."""
    global _tool_trends

    if _tool_trends:
        return _tool_trends

    trend_file = Path(TOOLS_TREND_STORAGE_PATH) / "tool_trends.json"
    if trend_file.exists():
        try:
            with open(trend_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for name, trend_data in data.items():
                    _tool_trends[name] = ToolTrend(**trend_data)
        except Exception as e:
            log.error(f"Error loading tool trends: {e}")

    return _tool_trends


def _save_trends(trends: Dict[str, ToolTrend]) -> bool:
    """Save trend data to storage."""
    try:
        Path(TOOLS_TREND_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
        trend_file = Path(TOOLS_TREND_STORAGE_PATH) / "tool_trends.json"

        data = {name: asdict(trend) for name, trend in trends.items()}
        with open(trend_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        log.error(f"Error saving tool trends: {e}")
        return False


def get_tool_trend(tool_name: str) -> ToolTrend:
    """
    Get trend data for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        ToolTrend with trend data
    """
    trends = _load_trends()
    return trends.get(tool_name, ToolTrend(tool_name=tool_name))


def calculate_predictive_trend(
    tool_name: str,
    recent_count: int,
    historical_count: int,
    window_days: int = TOOLS_PREDICTIVE_TREND_WINDOW
) -> float:
    """
    Calculate predictive trend score for a tool.

    Args:
        tool_name: Name of the tool
        recent_count: Recent usage count
        historical_count: Historical usage count
        window_days: Trend window in days

    Returns:
        Trend score from -1.0 (declining) to +1.0 (rising)
    """
    if not TOOLS_PREDICTIVE_ENABLED:
        return 0.0

    if historical_count == 0:
        if recent_count > 0:
            return 0.5  # New tool, slight positive
        return 0.0

    # Calculate change rate
    change_rate = (recent_count - historical_count) / max(historical_count, 1)

    # Normalize to -1 to +1 range
    trend = max(-1.0, min(1.0, change_rate))

    return round(trend, 3)


def update_tool_trend(
    tool_name: str,
    usage_count_30d: int,
    usage_count_60d: int,
    usage_count_90d: int
) -> ToolTrend:
    """
    Update trend data for a tool.

    Args:
        tool_name: Name of the tool
        usage_count_30d: Usage in last 30 days
        usage_count_60d: Usage in last 60 days
        usage_count_90d: Usage in last 90 days

    Returns:
        Updated ToolTrend
    """
    trends = _load_trends()

    # Calculate trends
    trend_30d = calculate_predictive_trend(
        tool_name,
        usage_count_30d,
        (usage_count_60d - usage_count_30d) if usage_count_60d > usage_count_30d else usage_count_30d // 2
    )
    trend_60d = calculate_predictive_trend(
        tool_name,
        usage_count_60d,
        (usage_count_90d - usage_count_60d) if usage_count_90d > usage_count_60d else usage_count_60d // 2
    )
    trend_90d = calculate_predictive_trend(
        tool_name,
        usage_count_90d,
        usage_count_90d  # Use same as baseline for 90d
    )

    # Determine direction
    avg_trend = (trend_30d * 0.5 + trend_60d * 0.3 + trend_90d * 0.2)
    if avg_trend > 0.15:
        direction = "rising"
    elif avg_trend < -0.15:
        direction = "declining"
    else:
        direction = "stable"

    trend = ToolTrend(
        tool_name=tool_name,
        trend_30d=trend_30d,
        trend_60d=trend_60d,
        trend_90d=trend_90d,
        sample_count_30d=usage_count_30d,
        sample_count_60d=usage_count_60d,
        sample_count_90d=usage_count_90d,
        trend_direction=direction,
        last_updated=datetime.utcnow().isoformat()
    )

    trends[tool_name] = trend
    _save_trends(trends)

    return trend


# =============================================================================
# REAL-WORLD WEIGHTED RECOMMENDATION
# =============================================================================

def calculate_final_score(
    confidence: float,
    predictive_trend: float,
    segment_weight: float,
    tuning_factor: float = 1.0
) -> float:
    """
    Calculate final recommendation score.

    Formula: final_score = confidence x predictive_trend x segment_weight x tuning_factor

    Args:
        confidence: Base confidence score (0-1)
        predictive_trend: Trend score (-1 to +1)
        segment_weight: Segment-specific weight (0-1)
        tuning_factor: Auto-tuning adjustment factor (typically 0.8-1.2)

    Returns:
        Final score (0-1)
    """
    # Normalize trend to positive multiplier (0.7 - 1.3)
    trend_multiplier = 1.0 + (predictive_trend * TOOLS_TREND_WEIGHT)

    score = confidence * trend_multiplier * segment_weight * tuning_factor

    return max(0.0, min(1.0, score))


def get_segment_weight(
    tool: Dict[str, Any],
    size_label: str,
    branch_group: str,
    ai_act_risk: str,
    sparte: str = "",
) -> float:
    """
    Calculate segment-specific weight for a tool.

    Args:
        tool: Tool data dict
        size_label: Company size
        branch_group: Industry branch
        ai_act_risk: AI Act risk level

    Returns:
        Segment weight (0-1)
    """
    weight = 0.5  # Base weight

    # Size match
    best_sizes = [s.lower() for s in tool.get("best_for_size", [])]
    if size_label.lower() in best_sizes or "alle" in best_sizes:
        weight += 0.2

    # Industry match
    best_industries = [i.lower() for i in tool.get("best_for_industries", [])]
    if branch_group.lower() in best_industries or "alle" in best_industries:
        weight += 0.15

    # KIS-1292: Sparten-Treffer (nur Eintraege mit ``sparten``-Feld)
    if _passt_zur_sparte(tool, sparte):
        weight += 0.15

    # Smart defaults match
    if TOOLS_SMART_DEFAULTS_ENABLED:
        smart_config: Dict[str, Any] = SMART_DEFAULTS.get(size_label.lower(), {})
        rec_cats: List[str] = smart_config.get("recommended_categories", [])
        recommended_cats = [c.lower() for c in rec_cats]
        tool_cat = (tool.get("category", "") or "").lower()

        if any(cat in tool_cat for cat in recommended_cats):
            weight += 0.15

    return min(1.0, weight)


# =============================================================================
# KIS-1142 Punkt 6 Variante B: Budget-aware tool filter
# =============================================================================

# investitionsbudget enum → max monthly entry-level cost (€/month) per tool.
# None = no cap (don't filter). "ueber_50000" and "unklar" also bypass the
# filter — never penalise enterprise buyers or users with missing data.
_BUDGET_BAND_MAX_MONTHLY: Dict[str, Optional[int]] = {
    "unter_2000":     30,
    "2000_10000":    100,
    "10000_50000":   500,
    "ueber_50000":  None,
    "unklar":       None,
}


def _parse_price_min_monthly(price: str) -> Optional[int]:
    """Extract the minimum monthly €-amount a user would pay for the tool.

    Returns None when the price string is usage-based or otherwise
    unparseable — callers should treat None as "unknown, keep the tool"
    rather than "free, keep the tool".

    Examples:
        '0–29 €/Monat'         → 0
        '0–10 €/Monat'         → 0
        'Free / ab 18 €/Monat' → 0   (free tier available)
        'Kostenlos'            → 0
        'ab 9 €/Monat'         → 9
        'ab ~5 € (Nutzung)'    → 5
        'Usage-basiert'        → None
        'Usage'                → None
    """
    if not price:
        return None
    s = price.strip().lower()
    if "kostenlos" in s or s.startswith("free"):
        # "Free / ab 18 …" → users can start at €0.
        return 0
    if s.startswith("usage") or "usage" in s and "€" not in s:
        return None
    # Ranges like "0–29 €/Monat" or "0-10 €/Monat" — take the low end.
    range_match = re.match(r"\s*(\d+)\s*[–-]\s*(\d+)", s)
    if range_match:
        try:
            return int(range_match.group(1))
        except ValueError:
            pass
    # Open-ended like "ab 9 €" or "ab ~5 €".
    ab_match = re.search(r"ab\s*~?\s*(\d+)", s)
    if ab_match:
        try:
            return int(ab_match.group(1))
        except ValueError:
            pass
    # Last resort: first integer anywhere in the string.
    num_match = re.search(r"(\d+)", s)
    if num_match:
        try:
            return int(num_match.group(1))
        except ValueError:
            pass
    return None


def _fits_budget(tool: Dict[str, Any], budget_band: str) -> bool:
    """True if the tool's minimum monthly entry cost fits the budget band.

    Tools with unparseable ("Usage-basiert") prices are always kept — we'd
    rather show an unknown-cost tool than drop a potentially critical
    recommendation because of a price-string edge case.
    """
    cap = _BUDGET_BAND_MAX_MONTHLY.get(budget_band)
    if cap is None:
        return True
    price = tool.get("price", "")
    min_monthly = _parse_price_min_monthly(str(price))
    if min_monthly is None:
        return True
    return min_monthly <= cap


# =============================================================================
# MAIN RECOMMENDATION ENGINE
# =============================================================================

def recommend_tools(
    briefing: Dict[str, Any] | Any,
    include_confidence: bool = True,
    include_trends: bool = True,
    max_tools: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate tool recommendations for a briefing.

    Enhanced version with:
    - Real-world confidence scores
    - Predictive trends
    - Smart defaults per persona
    - Segment weighting

    Args:
        briefing: Briefing data
        include_confidence: Include confidence metadata
        include_trends: Include trend data
        max_tools: Override max tools limit

    Returns:
        List of recommended tools with metadata
    """
    tools = _load_seed()
    b = _briefing_to_dict(briefing)

    # Extract context
    branche = (b.get("branche") or b.get("branche_label") or "").lower()
    groesse = (b.get("unternehmensgroesse") or b.get("groesse") or "").lower()
    hauptleistung = (b.get("hauptleistung") or "").lower()
    ai_act_risk = (b.get("ai_act_risk_level") or b.get("risk_level") or "minimal").lower()
    # KIS-1292 (Stufe 4): Sparte als Slug — ein Tonstudio bekam bisher
    # dieselbe Liste wie ein Games-Studio, weil nur ``branche`` zaehlte.
    sparte = _sparte_slug(b.get("medien_sparte"))

    # KIS-1142 Punkt 6 Variante B: budget-aware pre-filter.
    # Drops tools whose minimum monthly entry cost exceeds what the user's
    # budget band can reasonably absorb per tool. Applied before scoring so
    # segment weighting doesn't silently rank an unaffordable tool to the top.
    # KIS-1304: Fragebogen 2 (s1_budget) hat Vorrang — dieselbe Regel wie
    # Budget-Gate und Spannungs-Box. Lauf KIS1276: FB1 sagte 2.000–10.000 €,
    # FB2 10.000–50.000 €; der Filter nahm FB1 und warf Amberscript, Descript
    # und Runway hinaus. Übrig blieben Canva, LanguageTool und Duden — für
    # ein VFX-Studio. Werkzeuge der eigenen Sparte fallen nie am Budget:
    # sie erscheinen mit Preis, und der Kunde entscheidet.
    _sa = b.get("_strategy_answers") if isinstance(b.get("_strategy_answers"), dict) else {}
    _budget_band = (str((_sa or {}).get("s1_budget") or "") or str(b.get("investitionsbudget") or "")).strip().lower()
    if _budget_band and _BUDGET_BAND_MAX_MONTHLY.get(_budget_band) is not None:
        _before = len(tools)
        tools = [t for t in tools
                 if _fits_budget(t, _budget_band) or _passt_zur_sparte(t, sparte)]
        if _before != len(tools):
            log.info(
                "[tools_recommender] budget filter (%s): %d → %d tools",
                _budget_band, _before, len(tools),
            )

    # Normalize size
    if "solo" in groesse or "1" in groesse or "freiberuf" in groesse:
        size_label = "solo"
    elif "team" in groesse or "klein" in groesse or "2-10" in groesse:
        size_label = "team"
    else:
        size_label = "kmu"

    # Get smart defaults
    smart_config = SMART_DEFAULTS.get(size_label, SMART_DEFAULTS["kmu"])
    tools_limit: int = max_tools or int(smart_config.get("max_tools", TOOLS_MAX_RECOMMENDATIONS))

    ranked: List[Dict[str, Any]] = []

    for t in tools:
        # Base scoring (legacy compatibility)
        score = 0
        industries = [x.lower() for x in t.get("best_for_industries", [])]
        sizes = [x.lower() for x in t.get("best_for_size", [])]
        cat = (t.get("category", "") or "").lower()

        if not branche or any(branche.startswith(bi) or bi == "alle" for bi in industries):
            score += 2
        if not groesse or (size_label in sizes or "alle" in sizes):
            score += 2
        # KIS-1292: Werkzeuge, die ihre Sparte nennen, steigen bei Treffer
        # auf — ohne Treffer bleibt der Wert, nichts faellt heraus.
        if _passt_zur_sparte(t, sparte):
            score += 2

        if "fragebogen" in cat or "intake" in cat or "automation" in cat:
            score += 1

        if hauptleistung:
            if any(token in hauptleistung for token in ["fragebogen", "questionnaire", "assessment"]):
                if "fragebogen" in cat or "intake" in cat:
                    score += 2
            if any(token in hauptleistung for token in ["auswertung", "analyse", "report"]):
                if "analytics" in cat or "dashboard" in cat or "wissensmanagement" in cat:
                    score += 1

        # Enhanced scoring with analytics
        confidence = 0.5
        confidence_level = "medium"
        segment_stability = "medium"
        ai_alignment = 0.5
        persona_fit = 0.5
        trend = 0.0
        trend_direction = "stable"

        if _HAS_ANALYTICS and TOOLS_ENGINE_ENABLED:
            # Get analytics data
            tool_stats = get_tool_stats(t["name"], size_label)
            if tool_stats:
                confidence = tool_stats.confidence
                confidence_level = tool_stats.confidence_level
                segment_stability = tool_stats.segment_stability
                ai_alignment = tool_stats.ai_act_alignment
                persona_fit = tool_stats.persona_fit_score
            else:
                # Calculate on-the-fly
                ai_alignment = calculate_ai_act_alignment(t["name"], ai_act_risk)
                persona_fit = calculate_persona_fit(t["name"], size_label)
                confidence, confidence_level = calculate_tool_confidence(
                    usage_count=score,
                    segment_stability="medium",
                    ai_act_alignment=ai_alignment,
                    persona_fit=persona_fit,
                    sample_size=TOOLS_MIN_SAMPLE_SIZE
                )

        # Get trend data
        if include_trends and TOOLS_PREDICTIVE_ENABLED:
            tool_trend = get_tool_trend(t["name"])
            trend = tool_trend.trend_30d
            trend_direction = tool_trend.trend_direction

        # Calculate segment weight
        segment_weight = get_segment_weight(t, size_label, branche, ai_act_risk, sparte=sparte)

        # Calculate final score
        final_score = calculate_final_score(
            confidence=confidence,
            predictive_trend=trend,
            segment_weight=segment_weight,
            tuning_factor=1.0
        )

        # Build tool result
        tool_result = dict(t)
        tool_result["_score"] = score  # Legacy score
        tool_result["_final_score"] = round(final_score, 3)

        if include_confidence:
            tool_result["_confidence"] = round(confidence, 3)
            tool_result["_confidence_level"] = confidence_level
            tool_result["_segment_stability"] = segment_stability
            tool_result["_ai_act_alignment"] = round(ai_alignment, 3)
            tool_result["_persona_fit"] = round(persona_fit, 3)

        if include_trends:
            tool_result["_trend"] = round(trend, 3)
            tool_result["_trend_direction"] = trend_direction

        ranked.append(tool_result)

    # Sort by final score (or legacy score if no analytics)
    if _HAS_ANALYTICS and TOOLS_ENGINE_ENABLED:
        ranked.sort(key=lambda x: x.get("_final_score", 0), reverse=True)
    else:
        ranked.sort(key=lambda x: x.get("_score", 0), reverse=True)

    # Apply segment-specific limit
    return ranked[:tools_limit]


def recommend_tools_v2(
    briefing: Dict[str, Any] | Any
) -> ToolsRecommendationResult:
    """
    Generate tool recommendations with full result object.

    Args:
        briefing: Briefing data

    Returns:
        ToolsRecommendationResult with recommendations and metadata
    """
    b = _briefing_to_dict(briefing)

    # Get recommendations
    tools = recommend_tools(briefing, include_confidence=True, include_trends=True)

    # Extract context
    groesse = (b.get("unternehmensgroesse") or b.get("groesse") or "").lower()
    branche = (b.get("branche") or b.get("branche_label") or "").lower()
    ai_act_risk = (b.get("ai_act_risk_level") or "minimal").lower()

    # Normalize size
    if "solo" in groesse or "1" in groesse:
        size_label = "solo"
    elif "team" in groesse or "klein" in groesse:
        size_label = "team"
    else:
        size_label = "kmu"

    # Build recommendations
    recommendations: List[ToolRecommendation] = []
    for i, t in enumerate(tools):
        rec = ToolRecommendation(
            tool_name=t.get("name", ""),
            url=t.get("url", ""),
            trust_url=t.get("trust_url", ""),
            category=t.get("category", ""),
            price=t.get("price", ""),
            gdpr=t.get("gdpr", ""),
            host=t.get("host", ""),
            final_score=t.get("_final_score", 0),
            confidence=t.get("_confidence", 0),
            confidence_level=t.get("_confidence_level", "medium"),
            segment_stability=t.get("_segment_stability", "medium"),
            ai_act_alignment=t.get("_ai_act_alignment", 0),
            persona_fit=t.get("_persona_fit", 0),
            trend=t.get("_trend", 0),
            trend_direction=t.get("_trend_direction", "stable"),
            rank=i + 1
        )
        recommendations.append(rec)

    # Determine overall segment stability
    stabilities = [r.segment_stability for r in recommendations if r.segment_stability]
    if stabilities:
        stability_counts = {s: stabilities.count(s) for s in set(stabilities)}
        overall_stability = max(stability_counts, key=stability_counts.get)
    else:
        overall_stability = "medium"

    # Check if fallback was used
    fallback_used = not _HAS_ANALYTICS or not TOOLS_ENGINE_ENABLED

    # Generate insights
    insights = generate_insights(recommendations, size_label, branche, ai_act_risk)

    return ToolsRecommendationResult(
        recommendations=recommendations,
        segment_context={
            "size_label": size_label,
            "branch_group": branche,
            "ai_act_risk": ai_act_risk
        },
        segment_stability=overall_stability,
        fallback_used=fallback_used,
        insights=insights
    )


# =============================================================================
# INSIGHTS GENERATION
# =============================================================================

def generate_insights(
    recommendations: List[ToolRecommendation],
    size_label: str,
    branch_group: str,
    ai_act_risk: str
) -> List[Dict[str, Any]]:
    """
    Generate insight cards based on recommendations.

    Args:
        recommendations: List of tool recommendations
        size_label: Company size
        branch_group: Industry branch
        ai_act_risk: AI Act risk level

    Returns:
        List of insight dicts
    """
    insights: List[Dict[str, Any]] = []

    # High adoption insight
    high_conf_tools = [r for r in recommendations if r.confidence_level == "high"]
    if high_conf_tools:
        insights.append({
            "type": "high_adoption",
            "title": "Hohe Adoption in Ihrem Segment",
            "description": f"{len(high_conf_tools)} Tools werden häufig in ähnlichen Unternehmen eingesetzt.",
            "tools": [t.tool_name for t in high_conf_tools[:3]],
            "icon": "chart-line-up"
        })

    # Emerging tools insight
    rising_tools = [r for r in recommendations if r.trend_direction == "rising"]
    if rising_tools:
        insights.append({
            "type": "emerging",
            "title": f"Aufstrebende Tools für {branch_group.capitalize() or 'Ihre Branche'}",
            "description": f"{len(rising_tools)} Tools zeigen einen positiven Trend.",
            "tools": [t.tool_name for t in rising_tools[:3]],
            "icon": "rocket"
        })

    # Governance alignment insight
    if ai_act_risk in ("high-risk", "high", "limited"):
        governance_tools = [r for r in recommendations if r.ai_act_alignment >= 0.7]
        if governance_tools:
            insights.append({
                "type": "governance",
                "title": "Starke Governance-Ausrichtung",
                "description": f"{len(governance_tools)} Tools unterstützen Ihre Compliance-Anforderungen.",
                "tools": [t.tool_name for t in governance_tools[:3]],
                "icon": "shield-check"
            })

    # Persona fit insight
    smart_config: Dict[str, Any] = SMART_DEFAULTS.get(size_label, {})
    if smart_config:
        rec_cats_list: List[str] = smart_config.get("recommended_categories", [])
        insights.append({
            "type": "persona_fit",
            "title": str(smart_config.get("description", "Passende Tools")),
            "description": f"Empfohlene Kategorien: {', '.join(rec_cats_list[:3])}",
            "tools": [],
            "icon": "user-check"
        })

    return insights[:5]  # Max 5 insights


# =============================================================================
# HTML OUTPUT
# =============================================================================

def _link(label: str, url: str | None) -> str:
    """Create HTML link."""
    if not url:
        return ""
    return f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'


def _confidence_badge(level: str) -> str:
    """Generate confidence badge HTML."""
    if not TOOLS_CONFIDENCE_SHOW_BADGES:
        return ""

    colors = {
        "high": "#22c55e",
        "medium": "#f59e0b",
        "low": "#ef4444"
    }
    labels = {
        "high": "Hohe Konfidenz",
        "medium": "Mittlere Konfidenz",
        "low": "Niedrige Konfidenz"
    }

    color = colors.get(level, colors["medium"])
    label = labels.get(level, labels["medium"])

    return f'''<span class="confidence-badge" style="
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;
        background-color: {color}20;
        color: {color};
        margin-left: 8px;
    ">{label}</span>'''


def _trend_indicator(direction: str, value: float) -> str:
    """Generate trend indicator HTML."""
    if not TOOLS_PREDICTIVE_ENABLED:
        return ""

    icons = {
        "rising": "trending_up",
        "stable": "trending_flat",
        "declining": "trending_down"
    }
    colors = {
        "rising": "#22c55e",
        "stable": "#6b7280",
        "declining": "#ef4444"
    }

    icon = icons.get(direction, icons["stable"])
    color = colors.get(direction, colors["stable"])

    return f'''<span class="trend-indicator" style="
        color: {color};
        font-size: 12px;
        margin-left: 4px;
    " title="Trend: {direction}">
        <span style="vertical-align: middle;">{"+" if value > 0 else ""}{int(value * 100)}%</span>
    </span>'''


def to_html(tools: List[Dict[str, Any]]) -> str:
    """
    Convert tool recommendations to HTML table.

    Args:
        tools: List of tool dicts

    Returns:
        HTML string
    """
    if not tools:
        return "<p class='muted'>Keine passenden Tools gefunden.</p>"

    rows: List[str] = []
    rows.append(
        """<table class="table table-modern tools-table">
<thead><tr>
<th>Tool/Produkt</th>
<th>Kategorie</th>
<th>Preis</th>
<th>DSGVO/Host</th>
<th>Links</th>
</tr></thead><tbody>"""
    )

    for t in tools:
        links: List[str] = []
        if t.get("url"):
            links.append(_link("Quelle", t["url"]))
        if t.get("trust_url"):
            links.append(_link("Trust&nbsp;Center", t["trust_url"]))
        link_html = " &middot; ".join(links) if links else "-"

        # Add confidence badge
        conf_badge = ""
        if "_confidence_level" in t:
            conf_badge = _confidence_badge(t["_confidence_level"])

        # Add trend indicator
        trend_ind = ""
        if "_trend" in t and "_trend_direction" in t:
            trend_ind = _trend_indicator(t["_trend_direction"], t["_trend"])

        name_html = f"<strong>{t.get('name', '')}</strong>{conf_badge}{trend_ind}"

        rows.append(
            f"""<tr>
<td>{name_html}</td>
<td>{t.get('category', '')}</td>
<td>{t.get('price', '')}</td>
<td>{t.get('gdpr', '')} - {t.get('host', '')}</td>
<td>{link_html}</td>
</tr>"""
        )

    rows.append("</tbody></table>")
    return "\n".join(rows)


# =============================================================================
# INSIGHT CARDS HTML
# =============================================================================

TOOLS_INSIGHT_CARDS_HTML_TEMPLATE = """
<div class="tools-insight-cards" style="
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin: 24px 0;
">
{cards}
</div>
"""

INSIGHT_CARD_TEMPLATE = """
<div class="insight-card insight-{type}" style="
    background: linear-gradient(135deg, {bg_color}10, {bg_color}05);
    border: 1px solid {bg_color}30;
    border-radius: 12px;
    padding: 16px;
    transition: transform 0.2s;
">
    <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <span style="
            width: 32px;
            height: 32px;
            background: {bg_color}20;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
        ">
            <span style="color: {bg_color}; font-size: 16px;">{icon}</span>
        </span>
        <h4 style="margin: 0; font-size: 14px; font-weight: 600; color: #1f2937;">{title}</h4>
    </div>
    <p style="margin: 0 0 12px 0; font-size: 13px; color: #6b7280; line-height: 1.5;">
        {description}
    </p>
    {tools_html}
</div>
"""

INSIGHT_ICONS = {
    "high_adoption": "&#x1F4C8;",  # Chart
    "emerging": "&#x1F680;",  # Rocket
    "governance": "&#x1F6E1;",  # Shield
    "persona_fit": "&#x2705;",  # Check
    "default": "&#x1F4A1;"  # Lightbulb
}

INSIGHT_COLORS = {
    "high_adoption": "#22c55e",
    "emerging": "#8b5cf6",
    "governance": "#3b82f6",
    "persona_fit": "#f59e0b",
    "default": "#6b7280"
}


def generate_insight_cards_html(insights: List[Dict[str, Any]]) -> str:
    """
    Generate HTML for insight cards.

    Args:
        insights: List of insight dicts

    Returns:
        HTML string
    """
    if not insights:
        return ""

    cards_html = []
    for insight in insights:
        insight_type = insight.get("type", "default")
        icon = INSIGHT_ICONS.get(insight_type, INSIGHT_ICONS["default"])
        color = INSIGHT_COLORS.get(insight_type, INSIGHT_COLORS["default"])

        # Tools list
        tools = insight.get("tools", [])
        if tools:
            tools_html = f'''
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                {"".join(f'<span style="background: #f3f4f6; padding: 4px 8px; border-radius: 4px; font-size: 11px;">{t}</span>' for t in tools[:3])}
            </div>
            '''
        else:
            tools_html = ""

        card = INSIGHT_CARD_TEMPLATE.format(
            type=insight_type,
            bg_color=color,
            icon=icon,
            title=insight.get("title", ""),
            description=insight.get("description", ""),
            tools_html=tools_html
        )
        cards_html.append(card)

    return TOOLS_INSIGHT_CARDS_HTML_TEMPLATE.format(cards="\n".join(cards_html))


# =============================================================================
# CONFIDENCE TABLE HTML
# =============================================================================

def generate_confidence_table_html(tools: List[Dict[str, Any]]) -> str:
    """
    Generate HTML confidence table for tools.

    Args:
        tools: List of tool dicts with confidence data

    Returns:
        HTML string
    """
    if not tools:
        return ""

    rows = []
    for t in tools:
        conf = t.get("_confidence", 0)
        conf_level = t.get("_confidence_level", "medium")
        stability = t.get("_segment_stability", "medium")
        ai_align = t.get("_ai_act_alignment", 0)
        persona = t.get("_persona_fit", 0)

        conf_color = {"high": "#22c55e", "medium": "#f59e0b", "low": "#ef4444"}.get(conf_level, "#6b7280")

        rows.append(f"""
        <tr>
            <td><strong>{t.get('name', '')}</strong></td>
            <td style="text-align: center;">
                <span style="color: {conf_color}; font-weight: 600;">{conf:.0%}</span>
            </td>
            <td style="text-align: center;">{stability.capitalize()}</td>
            <td style="text-align: center;">{ai_align:.0%}</td>
            <td style="text-align: center;">{persona:.0%}</td>
        </tr>
        """)

    return f"""
    <table class="table table-modern confidence-table" style="margin-top: 24px;">
        <thead>
            <tr>
                <th>Tool</th>
                <th style="text-align: center;">Konfidenz</th>
                <th style="text-align: center;">Stabilität</th>
                <th style="text-align: center;">AI Act</th>
                <th style="text-align: center;">Persona</th>
            </tr>
        </thead>
        <tbody>
            {"".join(rows)}
        </tbody>
    </table>
    """


# =============================================================================
# TREND CHART HTML
# =============================================================================

def generate_trend_chart_html(tools: List[Dict[str, Any]]) -> str:
    """
    Generate HTML trend visualization for tools.

    Args:
        tools: List of tool dicts with trend data

    Returns:
        HTML string
    """
    if not tools or not TOOLS_PREDICTIVE_ENABLED:
        return ""

    # Filter tools with significant trends
    trending = [t for t in tools if abs(t.get("_trend", 0)) > 0.05][:8]

    if not trending:
        return ""

    bars = []
    for t in trending:
        trend = t.get("_trend", 0)
        direction = t.get("_trend_direction", "stable")

        # Bar width (max 100px)
        width = abs(trend) * 100

        color = {"rising": "#22c55e", "stable": "#6b7280", "declining": "#ef4444"}.get(direction, "#6b7280")

        bars.append(f"""
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="width: 120px; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {t.get('name', '')}
            </span>
            <div style="flex: 1; display: flex; align-items: center; margin-left: 12px;">
                <div style="
                    width: {width}px;
                    height: 20px;
                    background: {color}20;
                    border-left: 3px solid {color};
                    border-radius: 0 4px 4px 0;
                    display: flex;
                    align-items: center;
                    padding-left: 8px;
                ">
                    <span style="font-size: 11px; color: {color}; font-weight: 500;">
                        {"+" if trend > 0 else ""}{trend:.0%}
                    </span>
                </div>
            </div>
        </div>
        """)

    return f"""
    <div class="tools-trend-chart" style="margin: 24px 0;">
        <h4 style="font-size: 14px; margin-bottom: 16px; color: #374151;">Tool-Trends (30 Tage)</h4>
        {"".join(bars)}
    </div>
    """


# =============================================================================
# SEGMENT STABILITY HTML
# =============================================================================

def generate_segment_stability_html(stability: str, context: Dict[str, str]) -> str:
    """
    Generate HTML segment stability indicator.

    Args:
        stability: Overall stability (strong/medium/weak)
        context: Segment context dict

    Returns:
        HTML string
    """
    colors = {
        "strong": "#22c55e",
        "medium": "#f59e0b",
        "weak": "#ef4444"
    }
    labels = {
        "strong": "Stabile Datenbasis",
        "medium": "Moderate Datenbasis",
        "weak": "Begrenzte Datenbasis"
    }
    descriptions = {
        "strong": "Empfehlungen basieren auf einer großen Anzahl ähnlicher Profile.",
        "medium": "Empfehlungen basieren auf einer moderaten Datenbasis.",
        "weak": "Empfehlungen basieren auf begrenzten Daten. Generische Fallbacks können enthalten sein."
    }

    color = colors.get(stability, colors["medium"])
    label = labels.get(stability, labels["medium"])
    desc = descriptions.get(stability, descriptions["medium"])

    size_label = context.get("size_label", "kmu")
    branch = context.get("branch_group", "")

    return f"""
    <div class="segment-stability-box" style="
        background: {color}10;
        border: 1px solid {color}30;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 16px 0;
        display: flex;
        align-items: center;
    ">
        <div style="
            width: 8px;
            height: 8px;
            background: {color};
            border-radius: 50%;
            margin-right: 12px;
        "></div>
        <div>
            <strong style="color: {color}; font-size: 13px;">{label}</strong>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: #6b7280;">
                {desc}
                <br><small>Segment: {size_label.upper()} | {branch.capitalize() if branch else 'Alle Branchen'}</small>
            </p>
        </div>
    </div>
    """


# =============================================================================
# PREDICTED VALUE HTML
# =============================================================================

def generate_predicted_value_html(recommendations: List[ToolRecommendation]) -> str:
    """
    Generate HTML showing predicted value/impact.

    Args:
        recommendations: List of recommendations

    Returns:
        HTML string
    """
    if not recommendations:
        return ""

    # Calculate aggregate metrics
    avg_confidence = sum(r.confidence for r in recommendations) / len(recommendations)
    high_conf_count = sum(1 for r in recommendations if r.confidence_level == "high")
    rising_count = sum(1 for r in recommendations if r.trend_direction == "rising")

    return f"""
    <div class="predicted-value-box" style="
        background: linear-gradient(135deg, #3b82f610, #8b5cf610);
        border: 1px solid #3b82f630;
        border-radius: 12px;
        padding: 20px;
        margin: 24px 0;
    ">
        <h4 style="margin: 0 0 16px 0; font-size: 14px; color: #1f2937;">
            Prognostizierter Mehrwert
        </h4>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
            <div style="text-align: center;">
                <div style="font-size: 24px; font-weight: 700; color: #3b82f6;">
                    {avg_confidence:.0%}
                </div>
                <div style="font-size: 11px; color: #6b7280;">
                    Durchschn. Konfidenz
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 24px; font-weight: 700; color: #22c55e;">
                    {high_conf_count}
                </div>
                <div style="font-size: 11px; color: #6b7280;">
                    High-Confidence Tools
                </div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 24px; font-weight: 700; color: #8b5cf6;">
                    {rising_count}
                </div>
                <div style="font-size: 11px; color: #6b7280;">
                    Trending Tools
                </div>
            </div>
        </div>
    </div>
    """


# =============================================================================
# COMBINED HTML GENERATION
# =============================================================================

def generate_all_html_sections(
    briefing: Dict[str, Any] | Any
) -> Dict[str, str]:
    """
    Generate all HTML sections for tools recommendations.

    Args:
        briefing: Briefing data

    Returns:
        Dict with HTML section keys and values
    """
    result = recommend_tools_v2(briefing)

    # Convert recommendations to dict format for existing functions
    tools_dicts = []
    for rec in result.recommendations:
        tool_dict = {
            "name": rec.tool_name,
            "url": rec.url,
            "trust_url": rec.trust_url,
            "category": rec.category,
            "price": rec.price,
            "gdpr": rec.gdpr,
            "host": rec.host,
            "_confidence": rec.confidence,
            "_confidence_level": rec.confidence_level,
            "_segment_stability": rec.segment_stability,
            "_ai_act_alignment": rec.ai_act_alignment,
            "_persona_fit": rec.persona_fit,
            "_trend": rec.trend,
            "_trend_direction": rec.trend_direction,
        }
        tools_dicts.append(tool_dict)

    return {
        "TOOLS_TABLE_HTML": to_html(tools_dicts),
        "TOOLS_CONFIDENCE_TABLE_HTML": generate_confidence_table_html(tools_dicts),
        "TOOLS_TREND_CHART_HTML": generate_trend_chart_html(tools_dicts),
        "TOOLS_INSIGHT_CARDS_HTML": generate_insight_cards_html(result.insights),
        "TOOLS_PREDICTED_VALUE_HTML": generate_predicted_value_html(result.recommendations),
        "TOOLS_SEGMENT_STABILITY_HTML": generate_segment_stability_html(
            result.segment_stability,
            result.segment_context
        ),
    }
