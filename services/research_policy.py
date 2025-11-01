# -*- coding: utf-8 -*-
"""
services/research_policy.py
===========================
Research-Policy: Domain-Whitelists, Query-Generierung, Config.

Usage:
    from services.research_policy import ResearchPolicy, DEFAULT_POLICY, queries_for_briefing
    
    # Get queries for briefing
    queries = queries_for_briefing(briefing_answers)
    # -> {"tools": [...], "funding": [...], "ai_act": [...]}
    
    # Use policy for filtering
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


# ============================================================================
# DOMAIN WHITELISTS & BLACKLISTS
# ============================================================================

# Funding-spezifische Domains (Deutschland + EU)
FUNDING_DOMAINS = [
    # Bund
    "bmwk.de", "bmbf.de", "foerderdatenbank.de", "bafa.de",
    "digitale-dienste.eu", "bundesregierung.de",
    # EU
    "ec.europa.eu", "europe.eu", "digital-strategy.ec.europa.eu",
    "eismea.ec.europa.eu", "cordis.europa.eu",
    # Länder
    "bayern.de", "stmwi.bayern.de", "nrw.de", "mkw.nrw",
    "berlin.de", "hamburg.de", "sachsen.de", "bw.de",
    # Förderbanken
    "kfw.de", "nbank.de", "lbank.de", "saarland.de",
]

# Tools/Tech Domains (vertrauenswürdige Quellen)
TOOLS_DOMAINS = [
    # Hersteller
    "openai.com", "anthropic.com", "google.com", "microsoft.com",
    # Tech-News (DE/EU)
    "heise.de", "ct.de", "t3n.de", "golem.de", "computerwoche.de",
    # Developer
    "github.com", "gitlab.com", "huggingface.co",
    # Reviews/Vergleiche
    "g2.com", "capterra.com", "trustpilot.com",
]

# Global Exclude (Spam/Low-Quality)
EXCLUDE_DOMAINS = [
    # Social Media (nicht-primär)
    "youtube.com", "youtu.be", "facebook.com", "instagram.com",
    "pinterest.com", "tiktok.com", "linkedin.com",
    # Affiliate/Marketing
    "medium.com", "slideshare.net", "kiberatung.de",
    # Low-Quality
    "everlast.ai", "spam.com", "click-here.com",
]


# ============================================================================
# RESEARCH POLICY
# ============================================================================

@dataclass
class ResearchPolicy:
    """
    Research-Policy: Konfiguration für Recherche-Verhalten.
    
    Attributes:
        include_funding: Whitelist für Förderprogramme
        include_tools_hint: Whitelist für Tools
        exclude_global: Global Blacklist
        max_results_tools: Max. Ergebnisse für Tools
        max_results_funding: Max. Ergebnisse für Funding
        max_results_sources: Max. Ergebnisse für Sources
        default_days: Default Zeitfenster in Tagen
    """
    include_funding: List[str] = field(default_factory=lambda: FUNDING_DOMAINS.copy())
    include_tools_hint: List[str] = field(default_factory=lambda: TOOLS_DOMAINS.copy())
    exclude_global: List[str] = field(default_factory=lambda: EXCLUDE_DOMAINS.copy())
    
    max_results_tools: int = 10
    max_results_funding: int = 10
    max_results_sources: int = 8
    
    default_days: int = 30
    
    def is_allowed_domain(self, url: str) -> bool:
        """Prüft ob Domain erlaubt ist."""
        url_lower = url.lower()
        
        # Check Blacklist
        if any(bad in url_lower for bad in self.exclude_global):
            return False
        
        # Check Whitelists
        if any(good in url_lower for good in self.include_funding):
            return True
        if any(good in url_lower for good in self.include_tools_hint):
            return True
        
        # Default: erlaubt wenn .de oder .eu
        if url_lower.endswith('.de') or url_lower.endswith('.eu'):
            return True
        
        return False


# Global Default Policy
DEFAULT_POLICY = ResearchPolicy()


# ============================================================================
# QUERY GENERATION
# ============================================================================

def queries_for_briefing(briefing: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Generiert Search-Queries basierend auf Briefing-Antworten.
    
    Args:
        briefing: Briefing-Antworten Dict mit keys wie:
            - branche (str)
            - bundesland (str)
            - ki_ziele (list)
            - hauptleistung (str)
            
    Returns:
        Dict mit Query-Listen:
        {
            "tools": ["query1", "query2", ...],
            "funding": ["query1", "query2", ...],
            "ai_act": ["query1", "query2", ...]
        }
    """
    branche = (briefing.get('branche') or 'Unternehmen').strip()
    bundesland = (briefing.get('bundesland') or 'Deutschland').strip()
    hauptleistung = (briefing.get('hauptleistung') or '').strip()
    ki_ziele = briefing.get('ki_ziele', [])
    
    # Bundesland-Mapping (Abkürzung -> Vollname)
    bundesland_map = {
        "BE": "Berlin", "BY": "Bayern", "BW": "Baden-Württemberg",
        "NW": "Nordrhein-Westfalen", "HE": "Hessen", "HH": "Hamburg",
        "HB": "Bremen", "RP": "Rheinland-Pfalz", "SL": "Saarland",
        "SN": "Sachsen", "ST": "Sachsen-Anhalt", "TH": "Thüringen",
        "MV": "Mecklenburg-Vorpommern", "NI": "Niedersachsen",
        "SH": "Schleswig-Holstein"
    }
    bundesland = bundesland_map.get(bundesland.upper(), bundesland)
    
    queries: Dict[str, List[str]] = {
        "tools": [],
        "funding": [],
        "ai_act": []
    }
    
    # ========== TOOLS QUERIES ==========
    queries["tools"].append(f"KI Tools {branche} Deutschland EU DSGVO")
    queries["tools"].append(f"generative AI {branche} SaaS Open Source")
    
    if hauptleistung:
        queries["tools"].append(f"KI Software {hauptleistung} Automation")
    
    if ki_ziele:
        # Nutze erstes Ziel für spezifischere Query
        ziel = ki_ziele[0] if isinstance(ki_ziele, list) else str(ki_ziele)
        queries["tools"].append(f"KI {ziel} {branche} Best Practices")
    
    # ========== FUNDING QUERIES ==========
    queries["funding"].append(f"Förderprogramme KI {bundesland} KMU")
    queries["funding"].append(f"Digitalisierung Förderung {branche} {bundesland}")
    queries["funding"].append(f"BAFA KfW Förderung Künstliche Intelligenz {bundesland}")
    
    if branche.lower() not in ['unternehmen', 'firma']:
        queries["funding"].append(f"Branchenprogramm {branche} Digitalisierung Förderung")
    
    # ========== AI ACT / SOURCES QUERIES ==========
    queries["ai_act"].append("EU AI Act Deutschland KMU Leitfaden")
    queries["ai_act"].append("KI Verordnung Compliance Deutschland 2024")
    queries["ai_act"].append("DSGVO KI Datenschutz Best Practices Deutschland")
    
    log.debug("Generated queries: tools=%d, funding=%d, ai_act=%d", 
             len(queries["tools"]), len(queries["funding"]), len(queries["ai_act"]))
    
    return queries


# ============================================================================
# ENVIRONMENT-BASED CONFIG
# ============================================================================

def load_policy_from_env() -> ResearchPolicy:
    """
    Lädt ResearchPolicy aus Environment Variables.
    
    ENV Variables:
        RESEARCH_INCLUDE_FUNDING: Comma-separated domains
        RESEARCH_INCLUDE_TOOLS: Comma-separated domains
        RESEARCH_EXCLUDE: Comma-separated domains
        RESEARCH_MAX_RESULTS_TOOLS: int
        RESEARCH_MAX_RESULTS_FUNDING: int
        RESEARCH_MAX_RESULTS_SOURCES: int
        RESEARCH_DEFAULT_DAYS: int (7, 30, 60)
    """
    policy = ResearchPolicy()
    
    # Include Funding
    if os.getenv("RESEARCH_INCLUDE_FUNDING"):
        custom = [d.strip() for d in os.getenv("RESEARCH_INCLUDE_FUNDING", "").split(",") if d.strip()]
        policy.include_funding.extend(custom)
    
    # Include Tools
    if os.getenv("RESEARCH_INCLUDE_TOOLS"):
        custom = [d.strip() for d in os.getenv("RESEARCH_INCLUDE_TOOLS", "").split(",") if d.strip()]
        policy.include_tools_hint.extend(custom)
    
    # Exclude
    if os.getenv("RESEARCH_EXCLUDE"):
        custom = [d.strip() for d in os.getenv("RESEARCH_EXCLUDE", "").split(",") if d.strip()]
        policy.exclude_global.extend(custom)
    
    # Max Results
    if os.getenv("RESEARCH_MAX_RESULTS_TOOLS"):
        try:
            policy.max_results_tools = int(os.getenv("RESEARCH_MAX_RESULTS_TOOLS"))
        except ValueError:
            pass
    
    if os.getenv("RESEARCH_MAX_RESULTS_FUNDING"):
        try:
            policy.max_results_funding = int(os.getenv("RESEARCH_MAX_RESULTS_FUNDING"))
        except ValueError:
            pass
    
    if os.getenv("RESEARCH_MAX_RESULTS_SOURCES"):
        try:
            policy.max_results_sources = int(os.getenv("RESEARCH_MAX_RESULTS_SOURCES"))
        except ValueError:
            pass
    
    # Default Days
    if os.getenv("RESEARCH_DEFAULT_DAYS"):
        try:
            days = int(os.getenv("RESEARCH_DEFAULT_DAYS"))
            if days in (7, 30, 60):
                policy.default_days = days
        except ValueError:
            pass
    
    return policy
