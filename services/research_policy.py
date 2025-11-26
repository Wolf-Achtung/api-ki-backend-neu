# -*- coding: utf-8 -*-
"""
services/research_policy.py
===========================
Research-Policy: Domain-Whitelists, Query-Generierung, Config.

Usage:
    from services.research_policy import ResearchPolicy, DEFAULT_POLICY, queries_for_briefing

    queries = queries_for_briefing(briefing_answers)
    # -> {"tools": [...], "funding": [...], "ai_act": [...]}

    policy = DEFAULT_POLICY
    if policy.is_allowed_domain("heise.de"):
        ...

"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

TOOLS_DOMAINS_DEFAULT = [
    "github.com",
    "huggingface.co",
    "openai.com",
    "anthropic.com",
    "google.com",
    "microsoft.com",
]

FUNDING_DOMAINS_DEFAULT = [
    "bmwk.de",
    "kfw.de",
    "bafa.de",
    "ibb.de",
    "nrwbank.de",
]

EXCLUDE_DOMAINS_DEFAULT = [
    "facebook.com",
    "instagram.com",
    "tiktok.com",
]

DEFAULT_DAYS = 30


@dataclass
class ResearchPolicy:
    include_funding: List[str] = field(default_factory=lambda: FUNDING_DOMAINS_DEFAULT[:])
    include_tools: List[str] = field(default_factory=lambda: TOOLS_DOMAINS_DEFAULT[:])
    exclude: List[str] = field(default_factory=lambda: EXCLUDE_DOMAINS_DEFAULT[:])
    max_results_tools: int = 8
    max_results_funding: int = 8
    max_results_sources: int = 7
    default_days: int = DEFAULT_DAYS

    def is_allowed_domain(self, domain: str) -> bool:
        domain = (domain or "").lower()
        if not domain:
            return False
        if any(bad in domain for bad in self.exclude):
            return False
        return True


DEFAULT_POLICY = ResearchPolicy()


def queries_for_briefing(briefing: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Generiert Search-Queries für Tools, Förderprogramme und AI Act.

    Args:
        briefing: Normalisierte Briefing-Antworten

    Returns:
        Dict mit Query-Listen:
        {
            "tools": ["query1", "query2", ...],
            "funding": ["query1", "query2", ...],
            "ai_act": ["query1", "query2", ...]
        }
    """
    branche = (briefing.get("branche") or "Unternehmen").strip()
    bundesland = (briefing.get("bundesland") or "Deutschland").strip()
    hauptleistung = (briefing.get("hauptleistung") or "").strip()
    ki_ziele = briefing.get("ki_ziele", [])
    groesse = (briefing.get("unternehmensgroesse") or "").strip().lower()

    bundesland_map = {
        "BE": "Berlin",
        "BY": "Bayern",
        "BW": "Baden-Württemberg",
        "NW": "Nordrhein-Westfalen",
        "HE": "Hessen",
        "HH": "Hamburg",
        "HB": "Bremen",
        "RP": "Rheinland-Pfalz",
        "SL": "Saarland",
        "SN": "Sachsen",
        "ST": "Sachsen-Anhalt",
        "TH": "Thüringen",
        "MV": "Mecklenburg-Vorpommern",
        "NI": "Niedersachsen",
        "SH": "Schleswig-Holstein",
    }
    bundesland = bundesland_map.get(bundesland.upper(), bundesland)

    if groesse == "solo":
        size_label = "Solo-Selbstständige"
    elif groesse.startswith("team"):
        size_label = "kleine Unternehmen"
    elif groesse == "kmu":
        size_label = "KMU"
    else:
        size_label = "KMU"

    queries: Dict[str, List[str]] = {
        "tools": [],
        "funding": [],
        "ai_act": [],
    }

    # TOOLS QUERIES
    queries["tools"].append(f"KI Tools {branche} Deutschland EU DSGVO")
    queries["tools"].append(f"generative AI {branche} SaaS Open Source")

    if hauptleistung:
        queries["tools"].append(f"KI Software {hauptleistung} Automation")
        queries["tools"].append(f"Workflow Automatisierung {hauptleistung} KI Software")

    if ki_ziele:
        ziel = ki_ziele[0] if isinstance(ki_ziele, list) else str(ki_ziele)
        queries["tools"].append(f"KI {ziel} {branche} Best Practices")

    # FUNDING QUERIES
    queries["funding"].append(f"Förderprogramme KI {bundesland} {size_label}")
    queries["funding"].append(
        f"Digitalisierung Förderung {branche} {bundesland}"
    )
    queries["funding"].append(
        f"BAFA KfW Förderung Künstliche Intelligenz {bundesland}"
    )

    if branche.lower() not in ["unternehmen", "firma"]:
        queries["funding"].append(
            f"Branchenprogramm {branche} Digitalisierung Förderung"
        )

    # AI ACT / SOURCES QUERIES
    queries["ai_act"].append("EU AI Act Deutschland KMU Leitfaden")
    queries["ai_act"].append("KI Verordnung Compliance Deutschland 2024")
    queries["ai_act"].append("DSGVO KI Datenschutz Best Practices Deutschland")

    log.debug(
        "Generated queries: tools=%d, funding=%d, ai_act=%d",
        len(queries["tools"]),
        len(queries["funding"]),
        len(queries["ai_act"]),
    )

    return queries


def load_policy_from_env() -> ResearchPolicy:
    policy = ResearchPolicy()

    inc_funding = os.getenv("RESEARCH_INCLUDE_FUNDING")
    if inc_funding:
        policy.include_funding = [x.strip() for x in inc_funding.split(",") if x.strip()]

    inc_tools = os.getenv("RESEARCH_INCLUDE_TOOLS")
    if inc_tools:
        policy.include_tools = [x.strip() for x in inc_tools.split(",") if x.strip()]

    exc = os.getenv("RESEARCH_EXCLUDE")
    if exc:
        policy.exclude = [x.strip() for x in exc.split(",") if x.strip()]

    for name, attr in [
        ("RESEARCH_MAX_RESULTS_TOOLS", "max_results_tools"),
        ("RESEARCH_MAX_RESULTS_FUNDING", "max_results_funding"),
        ("RESEARCH_MAX_RESULTS_SOURCES", "max_results_sources"),
        ("RESEARCH_DEFAULT_DAYS", "default_days"),
    ]:
        val = os.getenv(name)
        if val:
            try:
                setattr(policy, attr, int(val))
            except Exception:
                log.warning("Invalid value for %s: %r", name, val)

    return policy
