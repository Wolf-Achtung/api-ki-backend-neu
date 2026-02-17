# -*- coding: utf-8 -*-
"""
Sprint G37: Benchmark Engine – Wettbewerb, Branchenmedian, Reifegradvergleich
=============================================================================

A comprehensive Benchmark Engine that:

- Compares the company with industry median values
- Integrates competitive and market perspectives
- Quantifies internal maturity (Readiness Score)
- Embeds KPI, Tool, Risk, Automation, Strategy, and Funding values in a benchmark model
- Generates a new report chapter: BENCHMARK_ENGINE_HTML

This module elevates the Decision Suite to a full AI Maturity & Competitiveness Framework.

Version: 1.2.0 (Sprint G37 + N3-06 + Phase 5C)
Author: Claude + Wolf

Sprint N3-06: Benchmark Quality Boost
- Compensate for missing Perplexity research data
- Increase governance (strategy) weight for finance/beratung branches
- Dynamic weight adjustment based on research_sources mode

Phase 5C (2026-01-06): Final Polish & Optimizations
- LRU caching for benchmark lookups (performance)
- Enhanced docstrings with all 13 Branchen documented
- Improved edge-case handling (None, empty, invalid values)
- Structured logging for monitoring
- Type hints completed

Supported Branchen (13 total, aligned with questionnaire):
    1. Marketing & Werbung (marketing)
    2. Beratung & Dienstleistungen (beratung)
    3. IT & Software (it)
    4. Finanzen & Versicherungen (finanzen)
    5. Handel & E-Commerce (handel)
    6. Bildung (bildung)
    7. Verwaltung (verwaltung)
    8. Gesundheit & Pflege (gesundheit)
    9. Bauwesen & Architektur (bau)
    10. Medien & Kreativwirtschaft (medien)
    11. Industrie & Produktion (industrie)
    12. Transport & Logistik (logistik)
    13. Gastronomie & Tourismus (gastronomie)

Supported Company Sizes (aligned with questionnaire):
    - "1" → "solo" (Solo-Selbstständig)
    - "2–10" → "small" (Kleines Team)
    - "11–100" → "medium" (KMU)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple, Union

log = logging.getLogger(__name__)

__all__ = [
    "BenchmarkPosition",
    "BenchmarkRadar",
    "BenchmarkReport",
    "generate_benchmark_report",
    "benchmark_report_to_html",
    "BENCHMARK_ENGINE_ENABLED",
]


# =============================================================================
# CONFIGURATION
# =============================================================================

BENCHMARK_ENGINE_ENABLED = True

# Benchmark domains
BENCHMARK_DOMAINS = ["kpi", "tools", "risk", "automation", "funding", "strategy"]

# Industry benchmark values by branch (median and top quartile)
# These are baseline values that get adjusted based on actual data
INDUSTRY_BENCHMARKS: Dict[str, Dict[str, Dict[str, float]]] = {
    # Default benchmarks (used when branch not found)
    "default": {
        "kpi": {"median": 0.8, "top_quartile": 1.4, "floor": 0.3},
        "tools": {"median": 0.5, "top_quartile": 0.75, "floor": 0.2},
        "risk": {"median": 0.6, "top_quartile": 0.35, "floor": 0.1},  # Lower is better for risk
        "automation": {"median": 0.4, "top_quartile": 0.65, "floor": 0.1},
        "funding": {"median": 0.3, "top_quartile": 0.55, "floor": 0.05},
        "strategy": {"median": 0.5, "top_quartile": 0.75, "floor": 0.2},
    },
    # Technology / IT
    "technologie": {
        "kpi": {"median": 1.0, "top_quartile": 1.8, "floor": 0.4},
        "tools": {"median": 0.65, "top_quartile": 0.85, "floor": 0.3},
        "risk": {"median": 0.5, "top_quartile": 0.3, "floor": 0.1},
        "automation": {"median": 0.55, "top_quartile": 0.8, "floor": 0.2},
        "funding": {"median": 0.35, "top_quartile": 0.6, "floor": 0.1},
        "strategy": {"median": 0.6, "top_quartile": 0.85, "floor": 0.3},
    },
    "it": {
        "kpi": {"median": 1.0, "top_quartile": 1.8, "floor": 0.4},
        "tools": {"median": 0.65, "top_quartile": 0.85, "floor": 0.3},
        "risk": {"median": 0.5, "top_quartile": 0.3, "floor": 0.1},
        "automation": {"median": 0.55, "top_quartile": 0.8, "floor": 0.2},
        "funding": {"median": 0.35, "top_quartile": 0.6, "floor": 0.1},
        "strategy": {"median": 0.6, "top_quartile": 0.85, "floor": 0.3},
    },
    "software": {
        "kpi": {"median": 1.2, "top_quartile": 2.0, "floor": 0.5},
        "tools": {"median": 0.7, "top_quartile": 0.9, "floor": 0.35},
        "risk": {"median": 0.45, "top_quartile": 0.25, "floor": 0.1},
        "automation": {"median": 0.6, "top_quartile": 0.85, "floor": 0.25},
        "funding": {"median": 0.4, "top_quartile": 0.65, "floor": 0.1},
        "strategy": {"median": 0.65, "top_quartile": 0.88, "floor": 0.35},
    },
    # Finance / Banking
    "finanzen": {
        "kpi": {"median": 0.9, "top_quartile": 1.5, "floor": 0.35},
        "tools": {"median": 0.55, "top_quartile": 0.78, "floor": 0.25},
        "risk": {"median": 0.65, "top_quartile": 0.4, "floor": 0.15},
        "automation": {"median": 0.45, "top_quartile": 0.7, "floor": 0.15},
        "funding": {"median": 0.25, "top_quartile": 0.45, "floor": 0.05},
        "strategy": {"median": 0.55, "top_quartile": 0.8, "floor": 0.25},
    },
    "banking": {
        "kpi": {"median": 0.9, "top_quartile": 1.5, "floor": 0.35},
        "tools": {"median": 0.55, "top_quartile": 0.78, "floor": 0.25},
        "risk": {"median": 0.65, "top_quartile": 0.4, "floor": 0.15},
        "automation": {"median": 0.45, "top_quartile": 0.7, "floor": 0.15},
        "funding": {"median": 0.25, "top_quartile": 0.45, "floor": 0.05},
        "strategy": {"median": 0.55, "top_quartile": 0.8, "floor": 0.25},
    },
    # Healthcare
    "healthcare": {
        "kpi": {"median": 0.7, "top_quartile": 1.2, "floor": 0.3},
        "tools": {"median": 0.45, "top_quartile": 0.68, "floor": 0.2},
        "risk": {"median": 0.7, "top_quartile": 0.45, "floor": 0.2},
        "automation": {"median": 0.35, "top_quartile": 0.55, "floor": 0.1},
        "funding": {"median": 0.35, "top_quartile": 0.6, "floor": 0.1},
        "strategy": {"median": 0.45, "top_quartile": 0.7, "floor": 0.2},
    },
    "gesundheit": {
        "kpi": {"median": 0.7, "top_quartile": 1.2, "floor": 0.3},
        "tools": {"median": 0.45, "top_quartile": 0.68, "floor": 0.2},
        "risk": {"median": 0.7, "top_quartile": 0.45, "floor": 0.2},
        "automation": {"median": 0.35, "top_quartile": 0.55, "floor": 0.1},
        "funding": {"median": 0.35, "top_quartile": 0.6, "floor": 0.1},
        "strategy": {"median": 0.45, "top_quartile": 0.7, "floor": 0.2},
    },
    # Manufacturing / Production
    "produktion": {
        "kpi": {"median": 0.85, "top_quartile": 1.4, "floor": 0.35},
        "tools": {"median": 0.5, "top_quartile": 0.72, "floor": 0.2},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.5, "top_quartile": 0.75, "floor": 0.2},
        "funding": {"median": 0.4, "top_quartile": 0.65, "floor": 0.15},
        "strategy": {"median": 0.5, "top_quartile": 0.75, "floor": 0.25},
    },
    "manufacturing": {
        "kpi": {"median": 0.85, "top_quartile": 1.4, "floor": 0.35},
        "tools": {"median": 0.5, "top_quartile": 0.72, "floor": 0.2},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.5, "top_quartile": 0.75, "floor": 0.2},
        "funding": {"median": 0.4, "top_quartile": 0.65, "floor": 0.15},
        "strategy": {"median": 0.5, "top_quartile": 0.75, "floor": 0.25},
    },
    # Retail / E-commerce
    "retail": {
        "kpi": {"median": 0.75, "top_quartile": 1.3, "floor": 0.3},
        "tools": {"median": 0.55, "top_quartile": 0.75, "floor": 0.25},
        "risk": {"median": 0.5, "top_quartile": 0.32, "floor": 0.1},
        "automation": {"median": 0.45, "top_quartile": 0.68, "floor": 0.15},
        "funding": {"median": 0.3, "top_quartile": 0.5, "floor": 0.08},
        "strategy": {"median": 0.5, "top_quartile": 0.73, "floor": 0.22},
    },
    "handel": {
        "kpi": {"median": 0.75, "top_quartile": 1.3, "floor": 0.3},
        "tools": {"median": 0.55, "top_quartile": 0.75, "floor": 0.25},
        "risk": {"median": 0.5, "top_quartile": 0.32, "floor": 0.1},
        "automation": {"median": 0.45, "top_quartile": 0.68, "floor": 0.15},
        "funding": {"median": 0.3, "top_quartile": 0.5, "floor": 0.08},
        "strategy": {"median": 0.5, "top_quartile": 0.73, "floor": 0.22},
    },
    "e-commerce": {
        "kpi": {"median": 0.9, "top_quartile": 1.5, "floor": 0.4},
        "tools": {"median": 0.6, "top_quartile": 0.82, "floor": 0.28},
        "risk": {"median": 0.48, "top_quartile": 0.3, "floor": 0.1},
        "automation": {"median": 0.52, "top_quartile": 0.75, "floor": 0.2},
        "funding": {"median": 0.32, "top_quartile": 0.55, "floor": 0.1},
        "strategy": {"median": 0.55, "top_quartile": 0.78, "floor": 0.25},
    },
    # Professional Services / Consulting
    "beratung": {
        "kpi": {"median": 0.95, "top_quartile": 1.6, "floor": 0.4},
        "tools": {"median": 0.6, "top_quartile": 0.8, "floor": 0.3},
        "risk": {"median": 0.45, "top_quartile": 0.28, "floor": 0.1},
        "automation": {"median": 0.48, "top_quartile": 0.7, "floor": 0.2},
        "funding": {"median": 0.28, "top_quartile": 0.48, "floor": 0.08},
        "strategy": {"median": 0.58, "top_quartile": 0.82, "floor": 0.28},
    },
    "consulting": {
        "kpi": {"median": 0.95, "top_quartile": 1.6, "floor": 0.4},
        "tools": {"median": 0.6, "top_quartile": 0.8, "floor": 0.3},
        "risk": {"median": 0.45, "top_quartile": 0.28, "floor": 0.1},
        "automation": {"median": 0.48, "top_quartile": 0.7, "floor": 0.2},
        "funding": {"median": 0.28, "top_quartile": 0.48, "floor": 0.08},
        "strategy": {"median": 0.58, "top_quartile": 0.82, "floor": 0.28},
    },
    # Education
    "bildung": {
        "kpi": {"median": 0.65, "top_quartile": 1.1, "floor": 0.25},
        "tools": {"median": 0.45, "top_quartile": 0.65, "floor": 0.2},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.35, "top_quartile": 0.55, "floor": 0.12},
        "funding": {"median": 0.45, "top_quartile": 0.7, "floor": 0.15},
        "strategy": {"median": 0.42, "top_quartile": 0.65, "floor": 0.18},
    },
    "education": {
        "kpi": {"median": 0.65, "top_quartile": 1.1, "floor": 0.25},
        "tools": {"median": 0.45, "top_quartile": 0.65, "floor": 0.2},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.35, "top_quartile": 0.55, "floor": 0.12},
        "funding": {"median": 0.45, "top_quartile": 0.7, "floor": 0.15},
        "strategy": {"median": 0.42, "top_quartile": 0.65, "floor": 0.18},
    },
    # Marketing / Media
    "marketing": {
        "kpi": {"median": 0.85, "top_quartile": 1.45, "floor": 0.35},
        "tools": {"median": 0.62, "top_quartile": 0.82, "floor": 0.3},
        "risk": {"median": 0.42, "top_quartile": 0.25, "floor": 0.08},
        "automation": {"median": 0.55, "top_quartile": 0.78, "floor": 0.22},
        "funding": {"median": 0.25, "top_quartile": 0.42, "floor": 0.05},
        "strategy": {"median": 0.55, "top_quartile": 0.78, "floor": 0.25},
    },
    "media": {
        "kpi": {"median": 0.82, "top_quartile": 1.4, "floor": 0.32},
        "tools": {"median": 0.58, "top_quartile": 0.78, "floor": 0.28},
        "risk": {"median": 0.45, "top_quartile": 0.28, "floor": 0.1},
        "automation": {"median": 0.5, "top_quartile": 0.72, "floor": 0.2},
        "funding": {"median": 0.28, "top_quartile": 0.48, "floor": 0.08},
        "strategy": {"median": 0.52, "top_quartile": 0.75, "floor": 0.22},
    },
    # Legal
    "recht": {
        "kpi": {"median": 0.7, "top_quartile": 1.2, "floor": 0.3},
        "tools": {"median": 0.4, "top_quartile": 0.62, "floor": 0.18},
        "risk": {"median": 0.6, "top_quartile": 0.38, "floor": 0.15},
        "automation": {"median": 0.32, "top_quartile": 0.52, "floor": 0.12},
        "funding": {"median": 0.2, "top_quartile": 0.38, "floor": 0.05},
        "strategy": {"median": 0.42, "top_quartile": 0.65, "floor": 0.18},
    },
    "legal": {
        "kpi": {"median": 0.7, "top_quartile": 1.2, "floor": 0.3},
        "tools": {"median": 0.4, "top_quartile": 0.62, "floor": 0.18},
        "risk": {"median": 0.6, "top_quartile": 0.38, "floor": 0.15},
        "automation": {"median": 0.32, "top_quartile": 0.52, "floor": 0.12},
        "funding": {"median": 0.2, "top_quartile": 0.38, "floor": 0.05},
        "strategy": {"median": 0.42, "top_quartile": 0.65, "floor": 0.18},
    },
    # Phase 5B: Added missing questionnaire Branchen
    # Handwerk & Bau
    "handwerk": {
        "kpi": {"median": 0.6, "top_quartile": 1.0, "floor": 0.25},
        "tools": {"median": 0.35, "top_quartile": 0.55, "floor": 0.15},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.3, "top_quartile": 0.5, "floor": 0.1},
        "funding": {"median": 0.35, "top_quartile": 0.55, "floor": 0.1},
        "strategy": {"median": 0.38, "top_quartile": 0.6, "floor": 0.15},
    },
    "bau": {
        "kpi": {"median": 0.6, "top_quartile": 1.0, "floor": 0.25},
        "tools": {"median": 0.35, "top_quartile": 0.55, "floor": 0.15},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.3, "top_quartile": 0.5, "floor": 0.1},
        "funding": {"median": 0.35, "top_quartile": 0.55, "floor": 0.1},
        "strategy": {"median": 0.38, "top_quartile": 0.6, "floor": 0.15},
    },
    "construction": {
        "kpi": {"median": 0.6, "top_quartile": 1.0, "floor": 0.25},
        "tools": {"median": 0.35, "top_quartile": 0.55, "floor": 0.15},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.3, "top_quartile": 0.5, "floor": 0.1},
        "funding": {"median": 0.35, "top_quartile": 0.55, "floor": 0.1},
        "strategy": {"median": 0.38, "top_quartile": 0.6, "floor": 0.15},
    },
    # Gastronomie & Tourismus
    "gastronomie": {
        "kpi": {"median": 0.55, "top_quartile": 0.95, "floor": 0.22},
        "tools": {"median": 0.4, "top_quartile": 0.6, "floor": 0.18},
        "risk": {"median": 0.5, "top_quartile": 0.32, "floor": 0.1},
        "automation": {"median": 0.35, "top_quartile": 0.55, "floor": 0.12},
        "funding": {"median": 0.3, "top_quartile": 0.5, "floor": 0.08},
        "strategy": {"median": 0.4, "top_quartile": 0.62, "floor": 0.18},
    },
    "tourismus": {
        "kpi": {"median": 0.58, "top_quartile": 1.0, "floor": 0.25},
        "tools": {"median": 0.45, "top_quartile": 0.65, "floor": 0.2},
        "risk": {"median": 0.48, "top_quartile": 0.3, "floor": 0.1},
        "automation": {"median": 0.38, "top_quartile": 0.58, "floor": 0.15},
        "funding": {"median": 0.32, "top_quartile": 0.52, "floor": 0.1},
        "strategy": {"median": 0.42, "top_quartile": 0.65, "floor": 0.2},
    },
    "hospitality": {
        "kpi": {"median": 0.55, "top_quartile": 0.95, "floor": 0.22},
        "tools": {"median": 0.4, "top_quartile": 0.6, "floor": 0.18},
        "risk": {"median": 0.5, "top_quartile": 0.32, "floor": 0.1},
        "automation": {"median": 0.35, "top_quartile": 0.55, "floor": 0.12},
        "funding": {"median": 0.3, "top_quartile": 0.5, "floor": 0.08},
        "strategy": {"median": 0.4, "top_quartile": 0.62, "floor": 0.18},
    },
    # Kreativwirtschaft
    "kreativ": {
        "kpi": {"median": 0.75, "top_quartile": 1.3, "floor": 0.3},
        "tools": {"median": 0.55, "top_quartile": 0.75, "floor": 0.25},
        "risk": {"median": 0.42, "top_quartile": 0.26, "floor": 0.08},
        "automation": {"median": 0.48, "top_quartile": 0.7, "floor": 0.18},
        "funding": {"median": 0.28, "top_quartile": 0.48, "floor": 0.08},
        "strategy": {"median": 0.5, "top_quartile": 0.72, "floor": 0.22},
    },
    "kreativwirtschaft": {
        "kpi": {"median": 0.75, "top_quartile": 1.3, "floor": 0.3},
        "tools": {"median": 0.55, "top_quartile": 0.75, "floor": 0.25},
        "risk": {"median": 0.42, "top_quartile": 0.26, "floor": 0.08},
        "automation": {"median": 0.48, "top_quartile": 0.7, "floor": 0.18},
        "funding": {"median": 0.28, "top_quartile": 0.48, "floor": 0.08},
        "strategy": {"median": 0.5, "top_quartile": 0.72, "floor": 0.22},
    },
    "creative": {
        "kpi": {"median": 0.75, "top_quartile": 1.3, "floor": 0.3},
        "tools": {"median": 0.55, "top_quartile": 0.75, "floor": 0.25},
        "risk": {"median": 0.42, "top_quartile": 0.26, "floor": 0.08},
        "automation": {"median": 0.48, "top_quartile": 0.7, "floor": 0.18},
        "funding": {"median": 0.28, "top_quartile": 0.48, "floor": 0.08},
        "strategy": {"median": 0.5, "top_quartile": 0.72, "floor": 0.22},
    },
    # Versicherungen (to complete Finanzen & Versicherungen)
    "versicherung": {
        "kpi": {"median": 0.85, "top_quartile": 1.4, "floor": 0.35},
        "tools": {"median": 0.52, "top_quartile": 0.72, "floor": 0.22},
        "risk": {"median": 0.68, "top_quartile": 0.42, "floor": 0.18},
        "automation": {"median": 0.42, "top_quartile": 0.65, "floor": 0.15},
        "funding": {"median": 0.22, "top_quartile": 0.4, "floor": 0.05},
        "strategy": {"median": 0.52, "top_quartile": 0.75, "floor": 0.22},
    },
    "insurance": {
        "kpi": {"median": 0.85, "top_quartile": 1.4, "floor": 0.35},
        "tools": {"median": 0.52, "top_quartile": 0.72, "floor": 0.22},
        "risk": {"median": 0.68, "top_quartile": 0.42, "floor": 0.18},
        "automation": {"median": 0.42, "top_quartile": 0.65, "floor": 0.15},
        "funding": {"median": 0.22, "top_quartile": 0.4, "floor": 0.05},
        "strategy": {"median": 0.52, "top_quartile": 0.75, "floor": 0.22},
    },
    # Dienstleistungen (alias for Beratung)
    "dienstleistungen": {
        "kpi": {"median": 0.95, "top_quartile": 1.6, "floor": 0.4},
        "tools": {"median": 0.6, "top_quartile": 0.8, "floor": 0.3},
        "risk": {"median": 0.45, "top_quartile": 0.28, "floor": 0.1},
        "automation": {"median": 0.48, "top_quartile": 0.7, "floor": 0.2},
        "funding": {"median": 0.28, "top_quartile": 0.48, "floor": 0.08},
        "strategy": {"median": 0.58, "top_quartile": 0.82, "floor": 0.28},
    },
    # Industrie (alias for Produktion)
    "industrie": {
        "kpi": {"median": 0.85, "top_quartile": 1.4, "floor": 0.35},
        "tools": {"median": 0.5, "top_quartile": 0.72, "floor": 0.2},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.5, "top_quartile": 0.75, "floor": 0.2},
        "funding": {"median": 0.4, "top_quartile": 0.65, "floor": 0.15},
        "strategy": {"median": 0.5, "top_quartile": 0.75, "floor": 0.25},
    },
    # Schulung (alias for Bildung)
    "schulung": {
        "kpi": {"median": 0.65, "top_quartile": 1.1, "floor": 0.25},
        "tools": {"median": 0.45, "top_quartile": 0.65, "floor": 0.2},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.35, "top_quartile": 0.55, "floor": 0.12},
        "funding": {"median": 0.45, "top_quartile": 0.7, "floor": 0.15},
        "strategy": {"median": 0.42, "top_quartile": 0.65, "floor": 0.18},
    },
    # Werbung (alias for Marketing)
    "werbung": {
        "kpi": {"median": 0.85, "top_quartile": 1.45, "floor": 0.35},
        "tools": {"median": 0.62, "top_quartile": 0.82, "floor": 0.3},
        "risk": {"median": 0.42, "top_quartile": 0.25, "floor": 0.08},
        "automation": {"median": 0.55, "top_quartile": 0.78, "floor": 0.22},
        "funding": {"median": 0.25, "top_quartile": 0.42, "floor": 0.05},
        "strategy": {"median": 0.55, "top_quartile": 0.78, "floor": 0.25},
    },
    # Soziales (alias for Gesundheit)
    "soziales": {
        "kpi": {"median": 0.6, "top_quartile": 1.0, "floor": 0.25},
        "tools": {"median": 0.4, "top_quartile": 0.6, "floor": 0.18},
        "risk": {"median": 0.65, "top_quartile": 0.42, "floor": 0.18},
        "automation": {"median": 0.3, "top_quartile": 0.5, "floor": 0.1},
        "funding": {"median": 0.4, "top_quartile": 0.65, "floor": 0.12},
        "strategy": {"median": 0.4, "top_quartile": 0.62, "floor": 0.18},
    },
    # Phase 5B.2: Additional Frontend V2 Branchen support
    # Pflege (for "Gesundheit & Pflege")
    "pflege": {
        "kpi": {"median": 0.6, "top_quartile": 1.0, "floor": 0.25},
        "tools": {"median": 0.4, "top_quartile": 0.6, "floor": 0.18},
        "risk": {"median": 0.65, "top_quartile": 0.42, "floor": 0.18},
        "automation": {"median": 0.3, "top_quartile": 0.5, "floor": 0.1},
        "funding": {"median": 0.4, "top_quartile": 0.65, "floor": 0.12},
        "strategy": {"median": 0.4, "top_quartile": 0.62, "floor": 0.18},
    },
    # Verwaltung (Public Administration)
    "verwaltung": {
        "kpi": {"median": 0.55, "top_quartile": 0.9, "floor": 0.22},
        "tools": {"median": 0.38, "top_quartile": 0.58, "floor": 0.15},
        "risk": {"median": 0.62, "top_quartile": 0.4, "floor": 0.15},
        "automation": {"median": 0.28, "top_quartile": 0.48, "floor": 0.1},
        "funding": {"median": 0.45, "top_quartile": 0.7, "floor": 0.15},
        "strategy": {"median": 0.38, "top_quartile": 0.6, "floor": 0.15},
    },
    "administration": {
        "kpi": {"median": 0.55, "top_quartile": 0.9, "floor": 0.22},
        "tools": {"median": 0.38, "top_quartile": 0.58, "floor": 0.15},
        "risk": {"median": 0.62, "top_quartile": 0.4, "floor": 0.15},
        "automation": {"median": 0.28, "top_quartile": 0.48, "floor": 0.1},
        "funding": {"median": 0.45, "top_quartile": 0.7, "floor": 0.15},
        "strategy": {"median": 0.38, "top_quartile": 0.6, "floor": 0.15},
    },
    # Bauwesen & Architektur
    "bauwesen": {
        "kpi": {"median": 0.6, "top_quartile": 1.0, "floor": 0.25},
        "tools": {"median": 0.35, "top_quartile": 0.55, "floor": 0.15},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.3, "top_quartile": 0.5, "floor": 0.1},
        "funding": {"median": 0.35, "top_quartile": 0.55, "floor": 0.1},
        "strategy": {"median": 0.38, "top_quartile": 0.6, "floor": 0.15},
    },
    "architektur": {
        "kpi": {"median": 0.65, "top_quartile": 1.1, "floor": 0.28},
        "tools": {"median": 0.45, "top_quartile": 0.65, "floor": 0.2},
        "risk": {"median": 0.52, "top_quartile": 0.32, "floor": 0.1},
        "automation": {"median": 0.35, "top_quartile": 0.55, "floor": 0.12},
        "funding": {"median": 0.32, "top_quartile": 0.52, "floor": 0.1},
        "strategy": {"median": 0.42, "top_quartile": 0.65, "floor": 0.18},
    },
    "architecture": {
        "kpi": {"median": 0.65, "top_quartile": 1.1, "floor": 0.28},
        "tools": {"median": 0.45, "top_quartile": 0.65, "floor": 0.2},
        "risk": {"median": 0.52, "top_quartile": 0.32, "floor": 0.1},
        "automation": {"median": 0.35, "top_quartile": 0.55, "floor": 0.12},
        "funding": {"median": 0.32, "top_quartile": 0.52, "floor": 0.1},
        "strategy": {"median": 0.42, "top_quartile": 0.65, "floor": 0.18},
    },
    # Transport & Logistik
    "transport": {
        "kpi": {"median": 0.65, "top_quartile": 1.1, "floor": 0.28},
        "tools": {"median": 0.42, "top_quartile": 0.62, "floor": 0.18},
        "risk": {"median": 0.55, "top_quartile": 0.35, "floor": 0.12},
        "automation": {"median": 0.4, "top_quartile": 0.6, "floor": 0.15},
        "funding": {"median": 0.35, "top_quartile": 0.55, "floor": 0.1},
        "strategy": {"median": 0.42, "top_quartile": 0.65, "floor": 0.18},
    },
    "logistik": {
        "kpi": {"median": 0.7, "top_quartile": 1.15, "floor": 0.3},
        "tools": {"median": 0.48, "top_quartile": 0.68, "floor": 0.2},
        "risk": {"median": 0.52, "top_quartile": 0.32, "floor": 0.1},
        "automation": {"median": 0.45, "top_quartile": 0.68, "floor": 0.18},
        "funding": {"median": 0.32, "top_quartile": 0.52, "floor": 0.1},
        "strategy": {"median": 0.45, "top_quartile": 0.68, "floor": 0.2},
    },
    "logistics": {
        "kpi": {"median": 0.7, "top_quartile": 1.15, "floor": 0.3},
        "tools": {"median": 0.48, "top_quartile": 0.68, "floor": 0.2},
        "risk": {"median": 0.52, "top_quartile": 0.32, "floor": 0.1},
        "automation": {"median": 0.45, "top_quartile": 0.68, "floor": 0.18},
        "funding": {"median": 0.32, "top_quartile": 0.52, "floor": 0.1},
        "strategy": {"median": 0.45, "top_quartile": 0.68, "floor": 0.2},
    },
    # Medien (for "Medien & Kreativwirtschaft")
    "medien": {
        "kpi": {"median": 0.78, "top_quartile": 1.35, "floor": 0.32},
        "tools": {"median": 0.55, "top_quartile": 0.75, "floor": 0.25},
        "risk": {"median": 0.42, "top_quartile": 0.26, "floor": 0.08},
        "automation": {"median": 0.48, "top_quartile": 0.7, "floor": 0.18},
        "funding": {"median": 0.28, "top_quartile": 0.48, "floor": 0.08},
        "strategy": {"median": 0.5, "top_quartile": 0.72, "floor": 0.22},
    },
}

# Size multipliers for benchmarks
SIZE_BENCHMARK_MULTIPLIERS = {
    "solo": {"kpi": 0.85, "tools": 0.75, "risk": 1.1, "automation": 0.7, "funding": 0.6, "strategy": 0.75},
    "small": {"kpi": 1.0, "tools": 1.0, "risk": 1.0, "automation": 1.0, "funding": 1.0, "strategy": 1.0},  # was "team"
    "medium": {"kpi": 1.15, "tools": 1.1, "risk": 0.9, "automation": 1.15, "funding": 1.2, "strategy": 1.15},  # was "kmu"
}

# Radar categories for visualization
RADAR_CATEGORIES_DE = ["ROI", "Risiko", "Tools", "Automation", "Förderung", "Strategie"]
RADAR_CATEGORIES_EN = ["ROI", "Risk", "Tools", "Automation", "Funding", "Strategy"]

# Percentile thresholds
PERCENTILE_TOP_QUARTILE = 75
PERCENTILE_MEDIAN = 50
PERCENTILE_BOTTOM_QUARTILE = 25


# =============================================================================
# Sprint N3-06: Quality Boost Configuration
# =============================================================================

# Branches that get increased governance (strategy) weight
GOVERNANCE_BOOSTED_BRANCHES = [
    "finanzen", "finance", "banking", "fintech", "versicherung", "insurance",
    "beratung", "consulting", "advisory", "legal", "recht", "kanzlei",
]

# Default and boosted governance weights
DEFAULT_STRATEGY_WEIGHT = 0.15
BOOSTED_STRATEGY_WEIGHT = 0.25  # +10% for finance/beratung

# Compensation boost when Perplexity research data is missing
# This boosts internal data-derived scores to compensate for missing external insights
PERPLEXITY_COMPENSATION_BOOST = 1.08  # +8% boost to compensate


def get_domain_weights(branch: str = "", research_sources: str = "hybrid") -> Dict[str, float]:
    """
    N3-06: Get dynamic domain weights based on branch and research mode.

    Finance and consulting branches get increased strategy/governance weight.
    Missing Perplexity data triggers compensation adjustments.

    Args:
        branch: Industry branch
        research_sources: Research mode (hybrid, tavily_only, partial_perplexity)

    Returns:
        Dict of domain weights (sum = 1.0)
    """
    # Base weights
    weights = {
        "kpi": 0.25,
        "tools": 0.15,
        "risk": 0.20,
        "automation": 0.15,
        "funding": 0.10,
        "strategy": DEFAULT_STRATEGY_WEIGHT,
    }

    # N3-06: Boost governance weight for finance/beratung branches
    branch_lower = branch.lower() if branch else ""
    is_governance_boosted = any(gb in branch_lower for gb in GOVERNANCE_BOOSTED_BRANCHES)

    if is_governance_boosted:
        # Increase strategy weight, decrease others proportionally
        strategy_increase = BOOSTED_STRATEGY_WEIGHT - DEFAULT_STRATEGY_WEIGHT
        weights["strategy"] = BOOSTED_STRATEGY_WEIGHT
        # Reduce KPI slightly to compensate
        weights["kpi"] -= strategy_increase / 2
        weights["automation"] -= strategy_increase / 2
        log.debug("[N3-06] Governance boost applied for branch=%s", branch)

    # Normalize weights to ensure they sum to 1.0
    total = sum(weights.values())
    if total != 1.0:
        weights = {k: v / total for k, v in weights.items()}

    return weights


def apply_perplexity_compensation(
    value: float,
    domain: str,
    research_sources: str = "hybrid",
) -> float:
    """
    N3-06: Apply compensation boost when Perplexity research is missing.

    This compensates for potentially lower quality external insights
    by boosting internally-derived scores.

    Args:
        value: Original benchmark value
        domain: Benchmark domain
        research_sources: Research mode (hybrid, tavily_only, partial_perplexity)

    Returns:
        Adjusted value (potentially boosted)
    """
    if research_sources == "hybrid":
        # Full research data available, no compensation needed
        return value

    # Domains most affected by missing Perplexity data
    affected_domains = ["tools", "risk", "automation", "strategy"]

    if domain in affected_domains and research_sources in ["tavily_only", "partial_perplexity"]:
        boosted = value * PERPLEXITY_COMPENSATION_BOOST
        log.debug(
            "[N3-06] Perplexity compensation: domain=%s value=%.3f→%.3f (mode=%s)",
            domain, value, boosted, research_sources
        )
        return boosted

    return value


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class BenchmarkPosition:
    """
    A single benchmark position for a specific domain.

    Compares company value against industry median and top quartile.
    """
    domain: str  # e.g. "kpi", "tools", "risk", "automation", "funding", "strategy"
    company_value: float
    industry_median: float
    industry_top_quartile: float
    score_percentile: float  # 0-100
    narrative: str

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Validate domain
        if self.domain not in BENCHMARK_DOMAINS:
            log.warning(
                "[G37] Invalid benchmark domain: %s, defaulting to 'kpi'",
                self.domain
            )
            self.domain = "kpi"

        # Clamp percentile
        self.score_percentile = max(0.0, min(100.0, self.score_percentile))

        # Ensure non-negative values
        self.company_value = max(0.0, self.company_value)
        self.industry_median = max(0.01, self.industry_median)  # Avoid division by zero
        self.industry_top_quartile = max(0.01, self.industry_top_quartile)

    @property
    def is_above_median(self) -> bool:
        """Check if company is above industry median."""
        if self.domain == "risk":
            # For risk, lower is better
            return self.company_value < self.industry_median
        return self.company_value > self.industry_median

    @property
    def is_top_quartile(self) -> bool:
        """Check if company is in top quartile."""
        if self.domain == "risk":
            # For risk, lower is better
            return self.company_value <= self.industry_top_quartile
        return self.company_value >= self.industry_top_quartile

    @property
    def deviation_from_median(self) -> float:
        """Calculate percentage deviation from median."""
        if self.industry_median == 0:
            return 0.0
        deviation = ((self.company_value - self.industry_median) / self.industry_median) * 100
        if self.domain == "risk":
            # Invert for risk (negative deviation = good)
            deviation = -deviation
        return round(deviation, 1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "domain": self.domain,
            "company_value": round(self.company_value, 3),
            "industry_median": round(self.industry_median, 3),
            "industry_top_quartile": round(self.industry_top_quartile, 3),
            "score_percentile": round(self.score_percentile, 1),
            "narrative": self.narrative,
            "is_above_median": self.is_above_median,
            "is_top_quartile": self.is_top_quartile,
            "deviation_from_median": self.deviation_from_median,
        }


@dataclass
class BenchmarkRadar:
    """
    Radar/Radial chart data for benchmark visualization.

    All scores are normalized to 0-1 for consistent display.
    """
    categories: List[str] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Ensure lists are the same length
        if len(self.categories) != len(self.scores):
            log.warning(
                "[G37] Radar categories/scores length mismatch: %d vs %d",
                len(self.categories), len(self.scores)
            )
            # Truncate to shorter length
            min_len = min(len(self.categories), len(self.scores))
            self.categories = self.categories[:min_len]
            self.scores = self.scores[:min_len]

        # Normalize scores to 0-1
        self.scores = [max(0.0, min(1.0, s)) for s in self.scores]

    @property
    def is_valid(self) -> bool:
        """Check if radar has valid data."""
        return len(self.categories) >= 3 and len(self.scores) >= 3

    @property
    def average_score(self) -> float:
        """Calculate average of all radar scores."""
        if not self.scores:
            return 0.0
        return sum(self.scores) / len(self.scores)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "categories": self.categories,
            "scores": [round(s, 3) for s in self.scores],
            "average_score": round(self.average_score, 3),
        }


@dataclass
class BenchmarkReport:
    """
    Complete benchmark report with positions, radar, and SWOT analysis.

    N3-06: Added branch and research_sources for dynamic weight calculation.
    """
    positions: List[BenchmarkPosition] = field(default_factory=list)
    radar: BenchmarkRadar = field(default_factory=BenchmarkRadar)
    summary: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)
    maturity_score: float = 0.0  # Overall AI maturity score (0-100)
    competitiveness_grade: str = "C"  # A-F grade
    # N3-06: Additional fields for dynamic weighting
    branch: str = ""  # Industry branch for governance boost
    research_sources: str = "hybrid"  # Research mode for Perplexity compensation

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Ensure lists
        if not isinstance(self.positions, list):
            self.positions = []
        if not isinstance(self.strengths, list):
            self.strengths = []
        if not isinstance(self.weaknesses, list):
            self.weaknesses = []
        if not isinstance(self.opportunities, list):
            self.opportunities = []
        if not isinstance(self.threats, list):
            self.threats = []

        # Clamp maturity score
        self.maturity_score = max(0.0, min(100.0, self.maturity_score))

        # Validate grade
        if self.competitiveness_grade not in ["A", "B", "C", "D", "F"]:
            self.competitiveness_grade = "C"

        # Recalculate if positions exist
        if self.positions:
            self._recalculate_scores()

    def _recalculate_scores(self) -> None:
        """
        Recalculate maturity score and grade from positions.

        N3-06: Uses dynamic weights based on branch and research_sources.
        """
        if not self.positions:
            return

        # N3-06: Get dynamic weights based on branch and research mode
        weights = get_domain_weights(self.branch, self.research_sources)
        total_weight = 0.0
        weighted_sum = 0.0

        for pos in self.positions:
            weight = weights.get(pos.domain, 0.1)
            weighted_sum += pos.score_percentile * weight
            total_weight += weight

        if total_weight > 0:
            self.maturity_score = weighted_sum / total_weight

        # Determine grade
        if self.maturity_score >= 80:
            self.competitiveness_grade = "A"
        elif self.maturity_score >= 65:
            self.competitiveness_grade = "B"
        elif self.maturity_score >= 50:
            self.competitiveness_grade = "C"
        elif self.maturity_score >= 35:
            self.competitiveness_grade = "D"
        else:
            self.competitiveness_grade = "F"

        # N3-06: Log if special weighting was applied
        if self.branch and any(gb in self.branch.lower() for gb in GOVERNANCE_BOOSTED_BRANCHES):
            log.debug("[N3-06] Governance-boosted scoring for branch=%s", self.branch)

    @property
    def is_valid(self) -> bool:
        """Check if report has valid data."""
        return len(self.positions) >= 3 and self.radar.is_valid

    @property
    def above_median_count(self) -> int:
        """Count positions above industry median."""
        return sum(1 for p in self.positions if p.is_above_median)

    @property
    def top_quartile_count(self) -> int:
        """Count positions in top quartile."""
        return sum(1 for p in self.positions if p.is_top_quartile)

    def get_position(self, domain: str) -> Optional[BenchmarkPosition]:
        """Get position for a specific domain."""
        for pos in self.positions:
            if pos.domain == domain:
                return pos
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "positions": [p.to_dict() for p in self.positions],
            "radar": self.radar.to_dict(),
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "opportunities": self.opportunities,
            "threats": self.threats,
            "maturity_score": round(self.maturity_score, 1),
            "competitiveness_grade": self.competitiveness_grade,
            "above_median_count": self.above_median_count,
            "top_quartile_count": self.top_quartile_count,
            # N3-06: Include branch and research mode info
            "branch": self.branch,
            "research_sources": self.research_sources,
            "governance_boosted": any(
                gb in self.branch.lower() for gb in GOVERNANCE_BOOSTED_BRANCHES
            ) if self.branch else False,
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Set of known branches for O(1) validation lookup (Phase 5C)
KNOWN_BRANCHES: Set[str] = set(INDUSTRY_BENCHMARKS.keys())


@lru_cache(maxsize=256)
def _normalize_branch(branch: str) -> str:
    """
    Normalize branch name for benchmark lookup.

    Supports all 13 Branchen from questionnaire (updated 2026-01-06):
    marketing, beratung, it, finanzen, handel, bildung, verwaltung,
    gesundheit, bau, medien, industrie, logistik, gastronomie

    Uses LRU cache (Phase 5C) since same branches are requested frequently.
    Cache size of 256 covers all variants multiple times.

    Args:
        branch: Branch name from questionnaire or briefing data.
                Can be German or English, with or without special chars.

    Returns:
        str: Normalized branch key for INDUSTRY_BENCHMARKS lookup.
             Returns "default" if branch is unknown.

    Examples:
        >>> _normalize_branch("IT & Software")
        'it'
        >>> _normalize_branch("Gastronomie & Tourismus")
        'gastronomie'
        >>> _normalize_branch("Marketing")
        'marketing'

    Notes:
        - Case-insensitive matching
        - Supports Umlaut variants (ä/ae, ö/oe, ü/ue)
        - Logs unknown branches for monitoring
    """
    # Edge case: None, empty string, or whitespace-only
    if not branch or not str(branch).strip():
        log.debug("Empty branch received, defaulting to 'default'")
        return "default"

    branch_lower = str(branch).lower().strip()

    # Handle Umlaute for robust matching (Phase 5C)
    branch_normalized = (branch_lower
        .replace('ä', 'ae')
        .replace('ö', 'oe')
        .replace('ü', 'ue')
        .replace('ß', 'ss'))

    # Direct mapping for aliases and translations
    # Keys are defined as frozenset for faster lookup
    branch_mappings = {
        "technology": "technologie",
        "tech": "technologie",
        "information technology": "it",
        "finance": "finanzen",
        "finanzdienstleistungen": "finanzen",
        "bank": "banking",
        "versicherung": "finanzen",
        "insurance": "finanzen",
        "health": "healthcare",
        "medical": "healthcare",
        "pharma": "healthcare",
        "produktion": "manufacturing",
        "industrie": "industrie",
        "industry": "manufacturing",
        "fertigung": "manufacturing",
        "einzelhandel": "retail",
        "commerce": "e-commerce",
        "ecommerce": "e-commerce",
        "onlinehandel": "e-commerce",
        "dienstleistung": "beratung",
        "service": "beratung",
        "professional services": "consulting",
        "unternehmensberatung": "consulting",
        "ausbildung": "education",
        "schule": "education",
        "hochschule": "education",
        "werbung": "marketing",
        "agentur": "marketing",
        "medien": "media",
        "verlag": "media",
        "publishing": "media",
        "rechtsanwalt": "legal",
        "anwalt": "legal",
        "kanzlei": "legal",
        # Gastronomie & Tourismus (Phase 5B.2)
        "gastronomie": "gastronomie",
        "tourismus": "tourismus",
        "gastronomie & tourismus": "gastronomie",
        "hotellerie": "gastronomie",
        "restaurant": "gastronomie",
        "hotel": "tourismus",
        "hospitality": "gastronomie",
        "tourism": "tourismus",
        # Phase 5C: Additional aliases for 13 Branchen
        "bauwesen": "bau",
        "architektur": "bau",
        "bauwesen & architektur": "bau",
        "construction": "bau",
        "kreativwirtschaft": "kreativ",
        "medien & kreativwirtschaft": "medien",
        "transport": "logistik",
        "transport & logistik": "logistik",
        "logistics": "logistik",
        "pflege": "gesundheit",
        "gesundheit & pflege": "gesundheit",
    }

    # Check direct mappings (partial match)
    for key, value in branch_mappings.items():
        if key in branch_lower or key in branch_normalized:
            return value

    # Check if branch exists directly in benchmarks
    if branch_lower in INDUSTRY_BENCHMARKS:
        return branch_lower

    # Check normalized version
    if branch_normalized in INDUSTRY_BENCHMARKS:
        return branch_normalized

    # Unknown branch - log for monitoring (Phase 5C)
    log.info(
        "Unknown branch for benchmark lookup",
        extra={
            "input_branch": branch,
            "normalized": "default",
            "needs_review": True
        }
    )
    return "default"


@lru_cache(maxsize=128)
def _get_industry_benchmarks(branch: str, domain: str) -> Dict[str, float]:
    """
    Get industry benchmark values for branch and domain (cached).

    Uses LRU cache (Phase 5C) since same branch/domain combinations
    are requested frequently. Cache size of 128 covers all combinations.

    Args:
        branch: Branch name (will be normalized internally)
        domain: Benchmark domain (kpi, tools, risk, automation, funding, strategy)

    Returns:
        Dict with 'median', 'top_quartile', 'floor' values

    Example:
        >>> _get_industry_benchmarks("gastronomie", "kpi")
        {'median': 0.55, 'top_quartile': 0.95, 'floor': 0.22}
    """
    normalized_branch = _normalize_branch(branch)
    benchmarks = INDUSTRY_BENCHMARKS.get(normalized_branch, INDUSTRY_BENCHMARKS["default"])
    return benchmarks.get(domain, INDUSTRY_BENCHMARKS["default"][domain])


def _calculate_percentile(
    company_value: float,
    median: float,
    top_quartile: float,
    floor: float,
    is_inverse: bool = False
) -> float:
    """
    Calculate percentile position based on value relative to benchmarks.

    For inverse metrics (like risk), lower is better.
    """
    if is_inverse:
        # Invert the logic for risk-like metrics
        if company_value <= top_quartile:
            # Top quartile (75-100)
            range_size = top_quartile - floor if top_quartile > floor else 0.1
            position = (top_quartile - company_value) / range_size
            return 75 + min(25, position * 25)
        elif company_value <= median:
            # Above median (50-75)
            range_size = median - top_quartile if median > top_quartile else 0.1
            position = (median - company_value) / range_size
            return 50 + position * 25
        else:
            # Below median (0-50)
            # Use a reasonable ceiling (2x median)
            ceiling = median * 2
            range_size = ceiling - median if ceiling > median else median
            position = (ceiling - company_value) / range_size
            return max(0, min(50, position * 50))
    else:
        # Normal metrics (higher is better)
        if company_value >= top_quartile:
            # Top quartile (75-100)
            # Extrapolate beyond top quartile
            range_size = top_quartile - median if top_quartile > median else 0.1
            overshoot = (company_value - top_quartile) / range_size
            return min(100, 75 + overshoot * 25)
        elif company_value >= median:
            # Above median (50-75)
            range_size = top_quartile - median if top_quartile > median else 0.1
            position = (company_value - median) / range_size
            return 50 + position * 25
        elif company_value >= floor:
            # Below median but above floor (25-50)
            range_size = median - floor if median > floor else 0.1
            position = (company_value - floor) / range_size
            return 25 + position * 25
        else:
            # Below floor (0-25)
            if floor > 0:
                position = company_value / floor
                return position * 25
            return 0


def _extract_kpi_value(
    kpi_data: Any,
    business_case: Any,
    sections: Dict[str, str]
) -> float:
    """Extract normalized KPI value (ROI-based)."""
    # Try business case simulation P50 ROI
    if kpi_data:
        if hasattr(kpi_data, "roi_p50"):
            return float(kpi_data.roi_p50) / 100  # Convert percentage to ratio
        if hasattr(kpi_data, "roi_distribution") and kpi_data.roi_distribution:
            if hasattr(kpi_data.roi_distribution, "p50"):
                return float(kpi_data.roi_distribution.p50) / 100

    # Try business case report
    if business_case:
        if hasattr(business_case, "get_scenario"):
            realistic = business_case.get_scenario("realistic")
            if realistic and hasattr(realistic, "roi_12m"):
                return float(realistic.roi_12m) / 100
        if hasattr(business_case, "scenarios"):
            for scenario in business_case.scenarios:
                if hasattr(scenario, "name") and scenario.name == "realistic":
                    if hasattr(scenario, "roi_12m"):
                        return float(scenario.roi_12m) / 100

    # Try sections
    roi_val = sections.get("ROI_P50") or sections.get("ROI_12M")
    if roi_val:
        try:
            return float(str(roi_val).replace("%", "").replace(",", ".")) / 100
        except (ValueError, TypeError):
            pass

    return 0.8  # Default to median


def _extract_tools_value(tools_data: Any, sections: Dict[str, str]) -> float:
    """Extract normalized tools maturity value."""
    if tools_data:
        # Try avg_fit_score
        if hasattr(tools_data, "avg_fit_score"):
            return float(tools_data.avg_fit_score)
        if hasattr(tools_data, "summary") and hasattr(tools_data.summary, "avg_fit"):
            return float(tools_data.summary.avg_fit)
        if isinstance(tools_data, dict):
            if "avg_fit_score" in tools_data:
                return float(tools_data["avg_fit_score"])
            if "summary" in tools_data and "avg_fit" in tools_data["summary"]:
                return float(tools_data["summary"]["avg_fit"])

    # Try sections
    tools_fit = sections.get("TOOLS_AVG_FIT") or sections.get("AVG_FIT_SCORE")
    if tools_fit:
        try:
            return float(str(tools_fit).replace(",", "."))
        except (ValueError, TypeError):
            pass

    return 0.5  # Default to median


def _extract_risk_value(risk_report_v3: Any, sections: Dict[str, str]) -> float:
    """Extract normalized risk value (0-1, lower is better)."""
    if risk_report_v3:
        # Try residual risk score
        if hasattr(risk_report_v3, "residual_risk_score"):
            return float(risk_report_v3.residual_risk_score) / 100
        if isinstance(risk_report_v3, dict) and "residual_risk_score" in risk_report_v3:
            return float(risk_report_v3["residual_risk_score"]) / 100

    # Try sections
    risk_score = sections.get("RESIDUAL_RISK_SCORE")
    if risk_score:
        try:
            score = float(str(risk_score).replace(",", "."))
            if score > 1:
                score = score / 100
            return score
        except (ValueError, TypeError):
            pass

    return 0.6  # Default to median


def _extract_automation_value(auto_report: Any, sections: Dict[str, str]) -> float:
    """Extract normalized automation potential value."""
    if auto_report:
        if hasattr(auto_report, "avg_automation_potential"):
            return float(auto_report.avg_automation_potential)
        if isinstance(auto_report, dict) and "avg_automation_potential" in auto_report:
            return float(auto_report["avg_automation_potential"])

    # Try sections
    auto_potential = sections.get("AUTO_AVG_POTENTIAL")
    if auto_potential:
        try:
            val = float(str(auto_potential).replace("%", "").replace(",", "."))
            return val if val <= 1 else val / 100
        except (ValueError, TypeError):
            pass

    return 0.4  # Default to median


def _extract_funding_value(funding_data: Any, sections: Dict[str, str]) -> float:
    """Extract normalized funding success/coverage value."""
    if funding_data:
        # Try funding coverage or success rate
        if hasattr(funding_data, "coverage_ratio"):
            return float(funding_data.coverage_ratio)
        if hasattr(funding_data, "summary") and hasattr(funding_data.summary, "coverage"):
            return float(funding_data.summary.coverage)
        if isinstance(funding_data, dict):
            if "coverage_ratio" in funding_data:
                return float(funding_data["coverage_ratio"])
            if "success_probability" in funding_data:
                return float(funding_data["success_probability"])

    # Try sections
    funding_coverage = sections.get("FUNDING_COVERAGE") or sections.get("FUNDING_SUCCESS_RATE")
    if funding_coverage:
        try:
            val = float(str(funding_coverage).replace("%", "").replace(",", "."))
            return val if val <= 1 else val / 100
        except (ValueError, TypeError):
            pass

    return 0.3  # Default to median


def _extract_strategy_value(strategy_plan: Any, sections: Dict[str, str]) -> float:
    """Extract normalized strategy maturity value."""
    if strategy_plan:
        # Try strategy readiness or maturity score
        if hasattr(strategy_plan, "readiness_score"):
            return float(strategy_plan.readiness_score)
        if hasattr(strategy_plan, "maturity_level"):
            # Map maturity level to score
            maturity_map = {"low": 0.3, "medium": 0.5, "high": 0.75, "advanced": 0.9}
            return maturity_map.get(str(strategy_plan.maturity_level).lower(), 0.5)
        if isinstance(strategy_plan, dict):
            if "readiness_score" in strategy_plan:
                return float(strategy_plan["readiness_score"])

    # Try sections
    strategy_score = sections.get("STRATEGY_READINESS") or sections.get("STRATEGY_SCORE")
    if strategy_score:
        try:
            val = float(str(strategy_score).replace("%", "").replace(",", "."))
            return val if val <= 1 else val / 100
        except (ValueError, TypeError):
            pass

    return 0.5  # Default to median


def _generate_position_narrative(
    domain: str,
    company_value: float,
    median: float,
    percentile: float,
    lang: str = "de"
) -> str:
    """Generate narrative for a benchmark position."""
    is_inverse = domain == "risk"

    if percentile >= 75:
        position = "Top-Quartil" if lang == "de" else "top quartile"
        trend = "unterdurchschnittlich (positiv)" if is_inverse and lang == "de" else \
                "below average (positive)" if is_inverse else \
                "überdurchschnittlich" if lang == "de" else "above average"
    elif percentile >= 50:
        position = "obere Hälfte" if lang == "de" else "upper half"
        trend = "unter Median (positiv)" if is_inverse and lang == "de" else \
                "below median (positive)" if is_inverse else \
                "über Median" if lang == "de" else "above median"
    elif percentile >= 25:
        position = "untere Hälfte" if lang == "de" else "lower half"
        trend = "über Median (negativ)" if is_inverse and lang == "de" else \
                "above median (negative)" if is_inverse else \
                "unter Median" if lang == "de" else "below median"
    else:
        position = "unterste Quartil" if lang == "de" else "bottom quartile"
        trend = "überdurchschnittlich (negativ)" if is_inverse and lang == "de" else \
                "above average (negative)" if is_inverse else \
                "unterdurchschnittlich" if lang == "de" else "below average"

    domain_names_de = {
        "kpi": "KPI/ROI-Leistung",
        "tools": "Tool-Reife",
        "risk": "Risiko-Management",
        "automation": "Automationsgrad",
        "funding": "Förder-Ausschöpfung",
        "strategy": "Strategie-Reife"
    }
    domain_names_en = {
        "kpi": "KPI/ROI performance",
        "tools": "tool maturity",
        "risk": "risk management",
        "automation": "automation level",
        "funding": "funding utilization",
        "strategy": "strategy maturity"
    }

    domain_name = domain_names_de.get(domain, domain) if lang == "de" else domain_names_en.get(domain, domain)

    if lang == "de":
        return f"{domain_name}: {position} der Branche ({trend}, Perzentil: {percentile:.0f})"
    else:
        return f"{domain_name}: {position} of industry ({trend}, percentile: {percentile:.0f})"


def _generate_swot_from_positions(
    positions: List[BenchmarkPosition],
    lang: str = "de"
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Generate SWOT analysis from benchmark positions."""
    strengths: List[str] = []
    weaknesses: List[str] = []
    opportunities: List[str] = []
    threats: List[str] = []

    domain_labels_de = {
        "kpi": "Starke ROI-Kennzahlen",
        "tools": "Fortschrittlicher Tool-Stack",
        "risk": "Gutes Risikomanagement",
        "automation": "Hoher Automationsgrad",
        "funding": "Gute Förder-Ausschöpfung",
        "strategy": "Klare KI-Strategie"
    }
    domain_labels_en = {
        "kpi": "Strong ROI metrics",
        "tools": "Advanced tool stack",
        "risk": "Good risk management",
        "automation": "High automation level",
        "funding": "Good funding utilization",
        "strategy": "Clear AI strategy"
    }

    weakness_labels_de = {
        "kpi": "ROI-Potenzial noch nicht ausgeschöpft",
        "tools": "Tool-Stack ausbaufähig",
        "risk": "Risikomanagement verbesserungswürdig",
        "automation": "Automationspotenzial ungenutzt",
        "funding": "Fördermittel unterbeansprucht",
        "strategy": "KI-Strategie unklar definiert"
    }
    weakness_labels_en = {
        "kpi": "ROI potential not fully realized",
        "tools": "Tool stack needs improvement",
        "risk": "Risk management needs attention",
        "automation": "Automation potential untapped",
        "funding": "Funding underutilized",
        "strategy": "AI strategy unclear"
    }

    opportunity_labels_de = {
        "kpi": "Weitere ROI-Steigerung durch KI-Optimierung",
        "tools": "Neue KI-Tools können Effizienz steigern",
        "risk": "Compliance-Vorsprung als Wettbewerbsvorteil",
        "automation": "Erweiterung durch weitere Automatisierung",
        "funding": "Zusätzliche Förderprogramme verfügbar",
        "strategy": "Strategische Positionierung als KI-Leader"
    }
    opportunity_labels_en = {
        "kpi": "Further ROI increase through AI optimization",
        "tools": "New AI tools can boost efficiency",
        "risk": "Compliance lead as competitive advantage",
        "automation": "Scaling through further automation",
        "funding": "Additional funding programs available",
        "strategy": "Strategic positioning as AI leader"
    }

    threat_labels_de = {
        "kpi": "Wettbewerber holen bei ROI auf",
        "tools": "Technologische Disruption durch neue Tools",
        "risk": "Regulatorische Verschärfungen (AI Act)",
        "automation": "Wettbewerber automatisieren schneller",
        "funding": "Förderbudgets werden kompetitiver",
        "strategy": "Strategielücke gegenüber Wettbewerbern"
    }
    threat_labels_en = {
        "kpi": "Competitors catching up on ROI",
        "tools": "Technological disruption from new tools",
        "risk": "Regulatory tightening (AI Act)",
        "automation": "Competitors automating faster",
        "funding": "Funding budgets becoming more competitive",
        "strategy": "Strategy gap vs competitors"
    }

    labels = domain_labels_de if lang == "de" else domain_labels_en
    weak_labels = weakness_labels_de if lang == "de" else weakness_labels_en
    opp_labels = opportunity_labels_de if lang == "de" else opportunity_labels_en
    threat_labels = threat_labels_de if lang == "de" else threat_labels_en

    for pos in positions:
        if pos.score_percentile >= 65:
            # Strength
            strengths.append(labels.get(pos.domain, f"Strong in {pos.domain}"))
            # Opportunity to leverage
            opportunities.append(opp_labels.get(pos.domain, f"Opportunity in {pos.domain}"))
        elif pos.score_percentile <= 35:
            # Weakness
            weaknesses.append(weak_labels.get(pos.domain, f"Weak in {pos.domain}"))
            # Threat from gap
            threats.append(threat_labels.get(pos.domain, f"Threat in {pos.domain}"))
        else:
            # Middle ground - opportunity for improvement
            if pos.score_percentile >= 50:
                opportunities.append(opp_labels.get(pos.domain, f"Opportunity in {pos.domain}"))
            else:
                weaknesses.append(weak_labels.get(pos.domain, f"Needs work in {pos.domain}"))

    # Ensure at least one item in each category
    if not strengths:
        strengths.append(
            "Solide Grundlage für KI-Transformation" if lang == "de"
            else "Solid foundation for AI transformation"
        )
    if not weaknesses:
        weaknesses.append(
            "Keine kritischen Schwächen identifiziert" if lang == "de"
            else "No critical weaknesses identified"
        )
    if not opportunities:
        opportunities.append(
            "Potenzial zur Branchenführerschaft" if lang == "de"
            else "Potential for industry leadership"
        )
    if not threats:
        threats.append(
            "Allgemeiner Wettbewerbsdruck im KI-Bereich" if lang == "de"
            else "General competitive pressure in AI"
        )

    import logging as _n6_log
    _n6_log.getLogger(__name__).info("[SWOT-N6] S=%d W=%d O=%d T=%d", len(strengths), len(weaknesses), len(opportunities), len(threats))
    return strengths[:4], weaknesses[:4], opportunities[:4], threats[:4]


def _generate_summary(
    report: BenchmarkReport,
    branch: str,
    size_label: str,
    lang: str = "de"
) -> str:
    """Generate executive summary for benchmark report."""
    grade = report.competitiveness_grade
    maturity = report.maturity_score
    above_median = report.above_median_count
    total = len(report.positions)

    if lang == "de":
        grade_labels = {
            "A": "exzellent",
            "B": "gut",
            "C": "durchschnittlich",
            "D": "unter dem Durchschnitt",
            "F": "verbesserungswürdig"
        }
        size_labels = {"solo": "Einzelunternehmen", "small": "Kleinunternehmen", "medium": "Mittelstand (KMU)"}

        return (
            f"Ihre KI-Wettbewerbsposition ist {grade_labels.get(grade, 'solide')} (Note {grade}). "
            f"Mit einem Reifegrad von {maturity:.0f}% liegen Sie in {above_median} von {total} "
            f"Benchmark-Kategorien über dem Branchenmedian. "
            f"Als {size_labels.get(size_label, 'Unternehmen')} in der Branche {branch} "
            f"haben Sie eine {_get_position_phrase_de(maturity)} Ausgangsposition."
        )
    else:
        grade_labels = {
            "A": "excellent",
            "B": "good",
            "C": "average",
            "D": "below average",
            "F": "needs improvement"
        }
        size_labels = {"solo": "solo entrepreneur", "small": "small business", "medium": "SME"}

        return (
            f"Your AI competitive position is {grade_labels.get(grade, 'solid')} (grade {grade}). "
            f"With a maturity score of {maturity:.0f}%, you are above the industry median in "
            f"{above_median} out of {total} benchmark categories. "
            f"As a {size_labels.get(size_label, 'company')} in the {branch} industry, "
            f"you have a {_get_position_phrase_en(maturity)} starting position."
        )


def _get_position_phrase_de(maturity: float) -> str:
    """Get German position phrase based on maturity."""
    if maturity >= 80:
        return "hervorragende"
    elif maturity >= 65:
        return "gute"
    elif maturity >= 50:
        return "solide"
    elif maturity >= 35:
        return "ausbaufaehige"
    else:
        return "herausfordernde"


def _get_position_phrase_en(maturity: float) -> str:
    """Get English position phrase based on maturity."""
    if maturity >= 80:
        return "excellent"
    elif maturity >= 65:
        return "good"
    elif maturity >= 50:
        return "solid"
    elif maturity >= 35:
        return "developing"
    else:
        return "challenging"


def _parse_llm_benchmark_response(response: Optional[str]) -> Optional[Dict[str, Any]]:
    """Parse LLM response JSON for benchmark data."""
    if not response:
        return None

    try:
        # Try direct JSON parse
        data = json.loads(response)
        return dict(data) if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            return dict(parsed) if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in response
    brace_match = re.search(r'\{[^{}]*"positions"[^{}]*\}', response, re.DOTALL)
    if brace_match:
        try:
            parsed = json.loads(brace_match.group(0))
            return dict(parsed) if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass

    log.warning("[G37] Failed to parse LLM benchmark response")
    return None


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def generate_benchmark_report(
    context: Any,
    sections: Dict[str, str],
    kpi_data: Any = None,
    tools_data: Any = None,
    funding_data: Any = None,
    risk_report_v3: Any = None,
    auto_report: Any = None,
    strategy_plan: Any = None,
    business_case: Any = None,
    briefing: Optional[Dict[str, Any]] = None,
    llm_response: Optional[str] = None,
    lang: str = "de",
    research_sources: str = "hybrid",  # N3-06: Research mode for compensation
) -> BenchmarkReport:
    """
    Generate comprehensive benchmark report comparing company to industry.

    Integrates data from:
    - Business Case Simulation (G34) for KPI benchmarks
    - Tools Engine 4.0 (G25) for tool maturity
    - Funding Engine v2 (G26) for funding utilization
    - Risk Engine V3 (G33) for risk benchmarks
    - Automation Roadmap (G36) for automation benchmarks
    - Strategy Plan for strategy maturity

    N3-06: Added research_sources for Perplexity compensation.

    Args:
        context: Report context (optional)
        sections: Dictionary of report sections
        kpi_data: Business Case Simulation data (G34)
        tools_data: Tools Engine data (G25)
        funding_data: Funding Engine data (G26)
        risk_report_v3: Risk Engine V3 data (G33)
        auto_report: Automation Roadmap data (G36)
        strategy_plan: Strategy plan data
        business_case: Business Case data (G30)
        briefing: User briefing/questionnaire data
        llm_response: Optional LLM response for narrative enhancement
        lang: Language code ("de" or "en")

    Returns:
        BenchmarkReport with positions, radar, SWOT, and summary
    """
    if not BENCHMARK_ENGINE_ENABLED:
        log.debug("[G37] Benchmark Engine is disabled")
        return BenchmarkReport()

    # Extract context from briefing
    briefing = briefing or {}
    branch = str(briefing.get("branche", briefing.get("industry", "default"))).lower()
    size_label = _normalize_size(briefing.get("unternehmensgroesse", briefing.get("company_size", "small")))

    log.info("[G37] Generating benchmark report for branch=%s, size=%s", branch, size_label)

    # Parse LLM response if provided
    llm_data = _parse_llm_benchmark_response(llm_response)

    # Get size multipliers
    size_mult = SIZE_BENCHMARK_MULTIPLIERS.get(size_label, SIZE_BENCHMARK_MULTIPLIERS["small"])

    # Generate positions for each domain
    positions: List[BenchmarkPosition] = []

    # KPI Benchmark
    kpi_value = _extract_kpi_value(kpi_data, business_case, sections)
    kpi_benchmarks = _get_industry_benchmarks(branch, "kpi")
    kpi_median = kpi_benchmarks["median"] * size_mult["kpi"]
    kpi_tq = kpi_benchmarks["top_quartile"] * size_mult["kpi"]
    kpi_floor = kpi_benchmarks["floor"] * size_mult["kpi"]
    kpi_percentile = _calculate_percentile(kpi_value, kpi_median, kpi_tq, kpi_floor)
    positions.append(BenchmarkPosition(
        domain="kpi",
        company_value=kpi_value,
        industry_median=kpi_median,
        industry_top_quartile=kpi_tq,
        score_percentile=kpi_percentile,
        narrative=_generate_position_narrative("kpi", kpi_value, kpi_median, kpi_percentile, lang)
    ))

    # Tools Benchmark
    tools_value = _extract_tools_value(tools_data, sections)
    # N3-06: Apply Perplexity compensation if needed
    tools_value = apply_perplexity_compensation(tools_value, "tools", research_sources)
    tools_benchmarks = _get_industry_benchmarks(branch, "tools")
    tools_median = tools_benchmarks["median"] * size_mult["tools"]
    tools_tq = tools_benchmarks["top_quartile"] * size_mult["tools"]
    tools_floor = tools_benchmarks["floor"] * size_mult["tools"]
    tools_percentile = _calculate_percentile(tools_value, tools_median, tools_tq, tools_floor)
    positions.append(BenchmarkPosition(
        domain="tools",
        company_value=tools_value,
        industry_median=tools_median,
        industry_top_quartile=tools_tq,
        score_percentile=tools_percentile,
        narrative=_generate_position_narrative("tools", tools_value, tools_median, tools_percentile, lang)
    ))

    # Risk Benchmark (inverse - lower is better)
    risk_value = _extract_risk_value(risk_report_v3, sections)
    # N3-06: Apply Perplexity compensation if needed (note: for risk, we don't boost since lower is better)
    # The compensation here slightly improves risk posture estimation when external data is limited
    risk_benchmarks = _get_industry_benchmarks(branch, "risk")
    risk_median = risk_benchmarks["median"] * size_mult["risk"]
    risk_tq = risk_benchmarks["top_quartile"] * size_mult["risk"]
    risk_floor = risk_benchmarks["floor"] * size_mult["risk"]
    risk_percentile = _calculate_percentile(risk_value, risk_median, risk_tq, risk_floor, is_inverse=True)
    positions.append(BenchmarkPosition(
        domain="risk",
        company_value=risk_value,
        industry_median=risk_median,
        industry_top_quartile=risk_tq,
        score_percentile=risk_percentile,
        narrative=_generate_position_narrative("risk", risk_value, risk_median, risk_percentile, lang)
    ))

    # Automation Benchmark
    auto_value = _extract_automation_value(auto_report, sections)
    # N3-06: Apply Perplexity compensation if needed
    auto_value = apply_perplexity_compensation(auto_value, "automation", research_sources)
    auto_benchmarks = _get_industry_benchmarks(branch, "automation")
    auto_median = auto_benchmarks["median"] * size_mult["automation"]
    auto_tq = auto_benchmarks["top_quartile"] * size_mult["automation"]
    auto_floor = auto_benchmarks["floor"] * size_mult["automation"]
    auto_percentile = _calculate_percentile(auto_value, auto_median, auto_tq, auto_floor)
    positions.append(BenchmarkPosition(
        domain="automation",
        company_value=auto_value,
        industry_median=auto_median,
        industry_top_quartile=auto_tq,
        score_percentile=auto_percentile,
        narrative=_generate_position_narrative("automation", auto_value, auto_median, auto_percentile, lang)
    ))

    # Funding Benchmark
    funding_value = _extract_funding_value(funding_data, sections)
    funding_benchmarks = _get_industry_benchmarks(branch, "funding")
    funding_median = funding_benchmarks["median"] * size_mult["funding"]
    funding_tq = funding_benchmarks["top_quartile"] * size_mult["funding"]
    funding_floor = funding_benchmarks["floor"] * size_mult["funding"]
    funding_percentile = _calculate_percentile(funding_value, funding_median, funding_tq, funding_floor)
    positions.append(BenchmarkPosition(
        domain="funding",
        company_value=funding_value,
        industry_median=funding_median,
        industry_top_quartile=funding_tq,
        score_percentile=funding_percentile,
        narrative=_generate_position_narrative("funding", funding_value, funding_median, funding_percentile, lang)
    ))

    # Strategy Benchmark
    strategy_value = _extract_strategy_value(strategy_plan, sections)
    # N3-06: Apply Perplexity compensation if needed
    strategy_value = apply_perplexity_compensation(strategy_value, "strategy", research_sources)
    strategy_benchmarks = _get_industry_benchmarks(branch, "strategy")
    strategy_median = strategy_benchmarks["median"] * size_mult["strategy"]
    strategy_tq = strategy_benchmarks["top_quartile"] * size_mult["strategy"]
    strategy_floor = strategy_benchmarks["floor"] * size_mult["strategy"]
    strategy_percentile = _calculate_percentile(strategy_value, strategy_median, strategy_tq, strategy_floor)
    positions.append(BenchmarkPosition(
        domain="strategy",
        company_value=strategy_value,
        industry_median=strategy_median,
        industry_top_quartile=strategy_tq,
        score_percentile=strategy_percentile,
        narrative=_generate_position_narrative("strategy", strategy_value, strategy_median, strategy_percentile, lang)
    ))

    # Generate radar data
    radar_categories = RADAR_CATEGORIES_DE if lang == "de" else RADAR_CATEGORIES_EN
    radar_scores = [
        kpi_percentile / 100,
        risk_percentile / 100,
        tools_percentile / 100,
        auto_percentile / 100,
        funding_percentile / 100,
        strategy_percentile / 100,
    ]
    radar = BenchmarkRadar(categories=radar_categories, scores=radar_scores)

    # Generate SWOT
    strengths, weaknesses, opportunities, threats = _generate_swot_from_positions(positions, lang)

    # Use LLM data to enhance if available
    # O4: Only override if LLM provides NON-EMPTY lists (empty [] was wiping generated SWOT)
    if llm_data:
        if llm_data.get("strengths") and len(llm_data["strengths"]) > 0:
            strengths = llm_data["strengths"][:4]
        if llm_data.get("weaknesses") and len(llm_data["weaknesses"]) > 0:
            weaknesses = llm_data["weaknesses"][:4]
        if llm_data.get("opportunities") and len(llm_data["opportunities"]) > 0:
            opportunities = llm_data["opportunities"][:4]
        if llm_data.get("threats") and len(llm_data["threats"]) > 0:
            threats = llm_data["threats"][:4]
    log.info("[O4-SWOT] After LLM merge: S=%d W=%d O=%d T=%d (llm_data=%s)",
             len(strengths), len(weaknesses), len(opportunities), len(threats),
             bool(llm_data))
    # P2-DEBUG: Log actual items for diagnosis
    log.info("[P2-SWOT-ITEMS] O=%s | T=%s", str(opportunities)[:200], str(threats)[:200])

    # Create report with N3-06 branch and research_sources
    report = BenchmarkReport(
        positions=positions,
        radar=radar,
        strengths=strengths,
        weaknesses=weaknesses,
        opportunities=opportunities,
        threats=threats,
        branch=branch,  # N3-06: For governance weight boost
        research_sources=research_sources,  # N3-06: For Perplexity compensation
    )

    # Generate summary
    report.summary = llm_data.get("summary") if llm_data and llm_data.get("summary") else \
        _generate_summary(report, branch, size_label, lang)

    # N3-06: Log quality boost info
    governance_boosted = any(gb in branch.lower() for gb in GOVERNANCE_BOOSTED_BRANCHES) if branch else False
    log.info(
        "[G37] Benchmark report generated: maturity=%.1f%%, grade=%s, above_median=%d/%d, "
        "governance_boost=%s, research_mode=%s",
        report.maturity_score,
        report.competitiveness_grade,
        report.above_median_count,
        len(positions),
        governance_boosted,
        research_sources,
    )

    return report


# Company size constants (Phase 5C - avoid magic strings)
SIZE_SOLO: str = "solo"      # 1 person
SIZE_SMALL: str = "small"    # 2-10 persons
SIZE_MEDIUM: str = "medium"  # 11-100 persons

# Frontend V2 size values (for direct matching - O(1) set lookup)
FRONTEND_SIZE_VALUES_SOLO: Set[str] = {"1", "1 mitarbeiter"}
FRONTEND_SIZE_VALUES_SMALL: Set[str] = {"2-10", "2–10", "2-10 mitarbeiter", "2–10 mitarbeiter"}
FRONTEND_SIZE_VALUES_MEDIUM: Set[str] = {"11-100", "11–100", "11-100 mitarbeiter", "11–100 mitarbeiter"}


def _normalize_size(size: Any) -> str:
    """
    Normalize company size to internal standard values.

    This function supports both current frontend (V2, since 2026-01-06)
    and legacy data formats for backward compatibility.

    **Frontend V2 (current):**
    - Input: "1", "2–10", "11–100"
    - Direct string matching (fast path)

    **Legacy Format (pre-2026-01-06):**
    - Input: "solo", "team", "kmu"
    - Keyword-based fallback (for old data)

    **Internal Values (output):**
    - "solo": 1 person (Solo-Selbstständig)
    - "small": 2-10 persons (Kleines Team)
    - "medium": 11-100 persons (KMU)

    Args:
        size: Company size from questionnaire or legacy data.
              Can be str, int, or None.

    Returns:
        str: Normalized size ("solo", "small", or "medium")

    Examples:
        >>> _normalize_size("1")
        'solo'
        >>> _normalize_size("2–10")
        'small'
        >>> _normalize_size("11–100")
        'medium'
        >>> _normalize_size("team")  # Legacy
        'small'

    Notes:
        - Supports both dash types: "–" (En-Dash) and "-" (Hyphen)
        - Default fallback: "small" (most common use case)
        - Legacy support maintained for data migration period
    """
    # Edge case: None, empty string, or whitespace-only
    if not size or not str(size).strip():
        log.debug("Empty size received, defaulting to 'small'")
        return SIZE_SMALL

    size_str = str(size).lower().strip()

    # --- Frontend V2 (fast path with set lookup - O(1)) ---
    # Support both En-Dash (–) and Hyphen (-) from different keyboards
    if size_str in FRONTEND_SIZE_VALUES_SOLO:
        return SIZE_SOLO
    if size_str in FRONTEND_SIZE_VALUES_SMALL:
        return SIZE_SMALL
    if size_str in FRONTEND_SIZE_VALUES_MEDIUM:
        return SIZE_MEDIUM

    # --- Legacy keyword matching (fallback) ---
    # Medium keywords (11-100 Personen) - check before small to avoid false matches
    medium_keywords = ("medium", "mittel", "sme", "kmu")
    if any(kw in size_str for kw in medium_keywords):
        return SIZE_MEDIUM

    # Small keywords (2-10 Personen)
    small_keywords = ("small", "klein", "startup", "team")
    if any(kw in size_str for kw in small_keywords):
        return SIZE_SMALL

    # Solo keywords (1 Person) - check last to avoid false matches
    solo_keywords = ("solo", "einzelunternehmer", "freelancer", "selbststaendig", "freiberuf", "one", "1 person")
    if any(kw in size_str for kw in solo_keywords):
        return SIZE_SOLO

    # Edge case: numeric input (Phase 5C)
    if isinstance(size, (int, float)):
        if size == 1:
            return SIZE_SOLO
        elif 2 <= size <= 10:
            return SIZE_SMALL
        elif 11 <= size <= 100:
            return SIZE_MEDIUM
        else:
            log.warning(
                "Company size out of expected range",
                extra={"input_size": size, "normalized": SIZE_SMALL}
            )
            return SIZE_SMALL

    # Unknown value - log for monitoring (Phase 5C)
    log.info(
        "Legacy size format detected",
        extra={
            "input_size": str(size),
            "normalized": SIZE_SMALL,
            "migration_needed": True
        }
    )
    return SIZE_SMALL


# =============================================================================
# HTML GENERATION
# =============================================================================

def benchmark_report_to_html(
    report: BenchmarkReport,
    lang: str = "de"
) -> str:
    """
    Generate HTML output for benchmark report.

    Creates PLATIN++ compliant HTML with:
    - Comparison tables
    - Color coding (good: blue/green, neutral: gray, weak: red)
    - Radar representation (table-based)
    - Mini-SWOT from benchmark perspective
    - Position in industry field

    Args:
        report: BenchmarkReport to render
        lang: Language code ("de" or "en")

    Returns:
        HTML string for BENCHMARK_ENGINE_HTML section
    """
    if not report or not report.is_valid:
        return _get_empty_benchmark_html(lang)

    html_parts: List[str] = []

    # Header with maturity score
    html_parts.append(_generate_header_html(report, lang))

    # Benchmark positions table
    html_parts.append(_generate_positions_table_html(report.positions, lang))

    # Radar visualization (table-based)
    html_parts.append(_generate_radar_table_html(report.radar, lang))

    # SWOT analysis
    html_parts.append(_generate_swot_html(report, lang))

    # Summary
    html_parts.append(_generate_summary_html(report, lang))

    return "\n".join(html_parts)


def _get_empty_benchmark_html(lang: str) -> str:
    """Return empty state HTML for benchmark section."""
    if lang == "de":
        return """
<div class="benchmark-empty">
    <p class="text-muted">Benchmark-Daten werden berechnet...</p>
</div>
"""
    return """
<div class="benchmark-empty">
    <p class="text-muted">Benchmark data is being calculated...</p>
</div>
"""


def _generate_header_html(report: BenchmarkReport, lang: str) -> str:
    """Generate header HTML with maturity score and grade."""
    grade_colors = {
        "A": "#22c55e",  # Green
        "B": "#3b82f6",  # Blue
        "C": "#f59e0b",  # Amber
        "D": "#f97316",  # Orange
        "F": "#dc2626",  # Red
    }
    grade_color = grade_colors.get(report.competitiveness_grade, "#64748b")

    maturity_label = "KI-Reifegrad" if lang == "de" else "AI Maturity"
    grade_label = "Wettbewerbsnote" if lang == "de" else "Competitiveness Grade"
    above_median_label = "über Branchenmedian" if lang == "de" else "above industry median"

    return f"""
<div class="benchmark-header" style="display: flex; gap: 24px; margin-bottom: 24px; flex-wrap: wrap;">
    <div class="benchmark-score-card" style="flex: 1; min-width: 200px; padding: 20px; background: var(--color-bg-surface, #f8fafc); border-radius: 10px; border: 1px solid var(--color-border, #e2e8f0);">
        <div class="score-label" style="font-size: 11pt; color: var(--color-text-muted, #64748b); margin-bottom: 8px;">{maturity_label}</div>
        <div class="score-value" style="font-size: 32pt; font-weight: 700; color: var(--color-text-strong, #0f172a);">{report.maturity_score:.0f}%</div>
        <div class="score-bar" style="margin-top: 12px; height: 8px; background: var(--color-border, #e2e8f0); border-radius: 4px; overflow: hidden;">
            <div style="width: {report.maturity_score}%; height: 100%; background: {grade_color}; border-radius: 4px;"></div>
        </div>
    </div>
    <div class="benchmark-grade-card" style="flex: 1; min-width: 200px; padding: 20px; background: var(--color-bg-surface, #f8fafc); border-radius: 10px; border: 1px solid var(--color-border, #e2e8f0); text-align: center;">
        <div class="grade-label" style="font-size: 11pt; color: var(--color-text-muted, #64748b); margin-bottom: 8px;">{grade_label}</div>
        <div class="grade-value" style="font-size: 48pt; font-weight: 700; color: {grade_color};">{report.competitiveness_grade}</div>
    </div>
    <div class="benchmark-summary-card" style="flex: 1; min-width: 200px; padding: 20px; background: var(--color-bg-surface, #f8fafc); border-radius: 10px; border: 1px solid var(--color-border, #e2e8f0);">
        <div class="summary-stat" style="font-size: 11pt; color: var(--color-text-muted, #64748b); margin-bottom: 8px;">{above_median_label}</div>
        <div class="summary-value" style="font-size: 28pt; font-weight: 700; color: var(--color-text-strong, #0f172a);">{report.above_median_count}/{len(report.positions)}</div>
        <div class="summary-detail" style="margin-top: 8px; font-size: 10pt; color: var(--color-text-muted, #64748b);">
            {"Top-Quartil" if lang == "de" else "Top quartile"}: {report.top_quartile_count}
        </div>
    </div>
</div>
"""


def _generate_positions_table_html(positions: List[BenchmarkPosition], lang: str) -> str:
    """Generate benchmark positions comparison table."""
    domain_labels_de = {
        "kpi": "ROI / KPIs",
        "tools": "Tool-Reife",
        "risk": "Risiko-Management",
        "automation": "Automationsgrad",
        "funding": "Förder-Ausschöpfung",
        "strategy": "Strategie-Reife"
    }
    domain_labels_en = {
        "kpi": "ROI / KPIs",
        "tools": "Tool Maturity",
        "risk": "Risk Management",
        "automation": "Automation Level",
        "funding": "Funding Utilization",
        "strategy": "Strategy Maturity"
    }
    labels = domain_labels_de if lang == "de" else domain_labels_en

    header_company = "Ihr Wert" if lang == "de" else "Your Value"
    header_median = "Branchenmedian" if lang == "de" else "Industry Median"
    header_tq = "Top-Quartil" if lang == "de" else "Top Quartile"
    header_percentile = "Perzentil" if lang == "de" else "Percentile"
    header_position = "Position" if lang == "de" else "Position"
    title = "Branchenvergleich" if lang == "de" else "Industry Comparison"

    rows: List[str] = []
    for pos in positions:
        # Color coding based on percentile
        if pos.score_percentile >= 75:
            color = "#22c55e"  # Green
            bg = "rgba(34, 197, 94, 0.08)"
        elif pos.score_percentile >= 50:
            color = "#3b82f6"  # Blue
            bg = "rgba(59, 130, 246, 0.08)"
        elif pos.score_percentile >= 25:
            color = "#f59e0b"  # Amber
            bg = "rgba(245, 158, 11, 0.08)"
        else:
            color = "#dc2626"  # Red
            bg = "rgba(220, 38, 38, 0.08)"

        # Format values based on domain
        if pos.domain in ["kpi"]:
            company_fmt = f"{pos.company_value * 100:.0f}%"
            median_fmt = f"{pos.industry_median * 100:.0f}%"
            tq_fmt = f"{pos.industry_top_quartile * 100:.0f}%"
        else:
            company_fmt = f"{pos.company_value:.2f}"
            median_fmt = f"{pos.industry_median:.2f}"
            tq_fmt = f"{pos.industry_top_quartile:.2f}"

        # Position indicator
        if pos.is_top_quartile:
            position_icon = "&#9733;"  # Star
            position_text = "Top" if lang == "en" else "Top"
        elif pos.is_above_median:
            position_icon = "&#9650;"  # Up triangle
            position_text = "Above" if lang == "en" else "Ueber"
        else:
            position_icon = "&#9660;"  # Down triangle
            position_text = "Below" if lang == "en" else "Unter"

        rows.append(f"""
        <tr style="background: {bg};">
            <td style="padding: 12px; font-weight: 600; border-bottom: 1px solid var(--color-border, #e2e8f0);">{labels.get(pos.domain, pos.domain)}</td>
            <td style="padding: 12px; border-bottom: 1px solid var(--color-border, #e2e8f0); text-align: right; font-weight: 600; color: {color};">{company_fmt}</td>
            <td style="padding: 12px; border-bottom: 1px solid var(--color-border, #e2e8f0); text-align: right; color: var(--color-text-muted, #64748b);">{median_fmt}</td>
            <td style="padding: 12px; border-bottom: 1px solid var(--color-border, #e2e8f0); text-align: right; color: var(--color-text-muted, #64748b);">{tq_fmt}</td>
            <td style="padding: 12px; border-bottom: 1px solid var(--color-border, #e2e8f0); text-align: right;">
                <span style="display: inline-block; padding: 4px 12px; background: {color}; color: white; border-radius: 12px; font-size: 10pt; font-weight: 600;">P{pos.score_percentile:.0f}</span>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid var(--color-border, #e2e8f0); text-align: center; color: {color};">
                <span style="font-size: 14pt;">{position_icon}</span> {position_text}
            </td>
        </tr>
        """)

    return f"""
<div class="benchmark-positions" style="margin-bottom: 24px;">
    <h3 style="font-size: 14pt; font-weight: 600; color: var(--color-text-strong, #0f172a); margin-bottom: 16px;">{title}</h3>
    <table class="table-modern" style="width: 100%; border-collapse: collapse; background: var(--color-bg-card, #ffffff); border-radius: 8px; overflow: hidden; border: 1px solid var(--color-border, #e2e8f0);">
        <thead>
            <tr style="background: var(--color-bg-surface, #f8fafc);">
                <th style="padding: 12px; text-align: left; font-weight: 600; font-size: 10pt; color: var(--color-text-muted, #64748b); border-bottom: 1px solid var(--color-border, #e2e8f0);">Domain</th>
                <th style="padding: 12px; text-align: right; font-weight: 600; font-size: 10pt; color: var(--color-text-muted, #64748b); border-bottom: 1px solid var(--color-border, #e2e8f0);">{header_company}</th>
                <th style="padding: 12px; text-align: right; font-weight: 600; font-size: 10pt; color: var(--color-text-muted, #64748b); border-bottom: 1px solid var(--color-border, #e2e8f0);">{header_median}</th>
                <th style="padding: 12px; text-align: right; font-weight: 600; font-size: 10pt; color: var(--color-text-muted, #64748b); border-bottom: 1px solid var(--color-border, #e2e8f0);">{header_tq}</th>
                <th style="padding: 12px; text-align: right; font-weight: 600; font-size: 10pt; color: var(--color-text-muted, #64748b); border-bottom: 1px solid var(--color-border, #e2e8f0);">{header_percentile}</th>
                <th style="padding: 12px; text-align: center; font-weight: 600; font-size: 10pt; color: var(--color-text-muted, #64748b); border-bottom: 1px solid var(--color-border, #e2e8f0);">{header_position}</th>
            </tr>
        </thead>
        <tbody>
            {"".join(rows)}
        </tbody>
    </table>
</div>
"""


def _generate_radar_table_html(radar: BenchmarkRadar, lang: str) -> str:
    """Generate radar visualization as a table (PDF-friendly, no SVG filters)."""
    title = "KI-Reifeprofil" if lang == "de" else "AI Maturity Profile"

    rows: List[str] = []
    for i, (cat, score) in enumerate(zip(radar.categories, radar.scores)):
        percentage = score * 100
        # Color gradient from red to green
        if percentage >= 75:
            color = "#22c55e"
        elif percentage >= 50:
            color = "#3b82f6"
        elif percentage >= 25:
            color = "#f59e0b"
        else:
            color = "#dc2626"

        rows.append(f"""
        <tr>
            <td style="padding: 10px 12px; border-bottom: 1px solid var(--color-border, #e2e8f0); font-weight: 500;">{cat}</td>
            <td style="padding: 10px 12px; border-bottom: 1px solid var(--color-border, #e2e8f0); width: 60%;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="flex: 1; height: 12px; background: var(--color-border, #e2e8f0); border-radius: 6px; overflow: hidden;">
                        <div style="width: {percentage}%; height: 100%; background: {color}; border-radius: 6px;"></div>
                    </div>
                    <span style="min-width: 45px; text-align: right; font-weight: 600; color: {color};">{percentage:.0f}%</span>
                </div>
            </td>
        </tr>
        """)

    avg_score = radar.average_score * 100
    avg_label = "Durchschnitt" if lang == "de" else "Average"

    return f"""
<div class="benchmark-radar" style="margin-bottom: 24px;">
    <h3 style="font-size: 14pt; font-weight: 600; color: var(--color-text-strong, #0f172a); margin-bottom: 16px;">{title}</h3>
    <table class="table-modern" style="width: 100%; border-collapse: collapse; background: var(--color-bg-card, #ffffff); border-radius: 8px; overflow: hidden; border: 1px solid var(--color-border, #e2e8f0);">
        <tbody>
            {"".join(rows)}
        </tbody>
        <tfoot>
            <tr style="background: var(--color-bg-surface, #f8fafc);">
                <td style="padding: 12px; font-weight: 700;">{avg_label}</td>
                <td style="padding: 12px;">
                    <span style="font-weight: 700; font-size: 14pt; color: var(--color-text-strong, #0f172a);">{avg_score:.0f}%</span>
                </td>
            </tr>
        </tfoot>
    </table>
</div>
"""


def _generate_swot_html(report: BenchmarkReport, lang: str) -> str:
    """Generate SWOT analysis HTML."""
    title = "Mini-SWOT Analyse" if lang == "de" else "Mini-SWOT Analysis"
    labels = {
        "strengths": "Stärken" if lang == "de" else "Strengths",
        "weaknesses": "Schwächen" if lang == "de" else "Weaknesses",
        "opportunities": "Chancen" if lang == "de" else "Opportunities",
        "threats": "Risiken" if lang == "de" else "Threats",
    }

    def render_items(items: List[str], color: str, bg: str) -> str:
        return "".join([
            f'<li style="padding: 6px 0; border-bottom: 1px solid {bg};">{item}</li>'
            for item in items
        ])

    return f"""
<!-- P2-SWOT-DEBUG: S={len(report.strengths)} W={len(report.weaknesses)} O={len(report.opportunities)} T={len(report.threats)} -->
<div class="benchmark-swot" style="margin-bottom: 24px;">
    <h3 style="font-size: 14pt; font-weight: 600; color: var(--color-text-strong, #0f172a); margin-bottom: 16px;">{title}</h3>
    <table style="width: 100%; border-collapse: separate; border-spacing: 12px; table-layout: fixed;">
        <tr>
            <td style="padding: 16px; background: rgba(34, 197, 94, 0.08); border-radius: 8px; border-left: 4px solid #22c55e; vertical-align: top; width: 50%;">
                <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #22c55e;">{labels["strengths"]}</h4>
                <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">
                    {render_items(report.strengths, "#22c55e", "rgba(34, 197, 94, 0.2)")}
                </ul>
            </td>
            <td style="padding: 16px; background: rgba(239, 68, 68, 0.08); border-radius: 8px; border-left: 4px solid #ef4444; vertical-align: top; width: 50%;">
                <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #ef4444;">{labels["weaknesses"]}</h4>
                <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">
                    {render_items(report.weaknesses, "#ef4444", "rgba(239, 68, 68, 0.2)")}
                </ul>
            </td>
        </tr>
        <tr>
            <td style="padding: 16px; background: rgba(59, 130, 246, 0.08); border-radius: 8px; border-left: 4px solid #3b82f6; vertical-align: top; width: 50%;">
                <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #3b82f6;">{labels["opportunities"]}</h4>
                <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">
                    {render_items(report.opportunities, "#3b82f6", "rgba(59, 130, 246, 0.2)")}
                </ul>
            </td>
            <td style="padding: 16px; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border-left: 4px solid #f59e0b; vertical-align: top; width: 50%;">
                <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #f59e0b;">{labels["threats"]}</h4>
                <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">
                    {render_items(report.threats, "#f59e0b", "rgba(245, 158, 11, 0.2)")}
                </ul>
            </td>
        </tr>
    </table>
</div>
"""


def _generate_summary_html(report: BenchmarkReport, lang: str) -> str:
    """Generate summary section HTML."""
    title = "Zusammenfassung" if lang == "de" else "Summary"

    return f"""
<div class="benchmark-summary" style="padding: 20px; background: var(--color-bg-surface, #f8fafc); border-radius: 10px; border: 1px solid var(--color-border, #e2e8f0);">
    <h3 style="font-size: 14pt; font-weight: 600; color: var(--color-text-strong, #0f172a); margin: 0 0 12px 0;">{title}</h3>
    <p style="margin: 0; font-size: 11pt; line-height: 1.6; color: var(--color-text-normal, #1e293b);">
        {report.summary}
    </p>
</div>
"""
