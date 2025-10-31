# -*- coding: utf-8 -*-
"""
services/research_policy.py
===========================
Gold-Standard Research-Policy (extended whitelist, dynamic windows).

ENV (optional):
    RESEARCH_DAYS_DEFAULT=30
    RESEARCH_DAYS_MIN=7
    RESEARCH_DAYS_MAX=60
    TOOLS_DAYS=30
    FUNDING_DAYS=30
    RESEARCH_INCLUDE_FUNDING="domain1,domain2,..."
    RESEARCH_INCLUDE_TOOLS="domain1,domain2,..."
    RESEARCH_EXCLUDE="domain1,domain2,..."
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List, Dict

# -- Bundesland-Codes → Volltext (für Förder-Suche) ---------------------------
BUNDESLAND_MAP = {
    "be": "Berlin", "by": "Bayern", "bw": "Baden-Württemberg", "bb": "Brandenburg",
    "hb": "Bremen", "hh": "Hamburg", "he": "Hessen", "mv": "Mecklenburg-Vorpommern",
    "ni": "Niedersachsen", "nw": "Nordrhein-Westfalen", "rp": "Rheinland-Pfalz",
    "sl": "Saarland", "sn": "Sachsen", "st": "Sachsen-Anhalt", "sh": "Schleswig-Holstein",
    "th": "Thüringen",
}

# --- Whitelists --------------------------------------------------------------
PRIMARY_FUNDING_DOMAINS = [
    # Bund / EU
    "bmwk.de", "bmbf.de", "bmuv.de", "bundesanzeiger.de", "foerderdatenbank.de",
    "ec.europa.eu", "europa.eu", "funding-and-tenders.ec.europa.eu",
    "eacea.ec.europa.eu", "eitdigital.europa.eu",
    # Parl./Gesetzbl.
    "dip.bundestag.de", "bgbl.de",
    # Länder/Banken (erweitert)
    "ibb.de", "investitionsbank-berlin.de", "nrwbank.de", "l-bank.de", "ifb.hamburg",
    "lfi.saarland.de", "saarland.de", "sachsen.de", "bayern.de", "stmwi.bayern.de",
    "stmwk.bayern.de", "berlin.de", "wirtschaft.nrw", "mw.de", "mkw.nrw",
]
PRIMARY_TOOL_DOMAINS_HINT = [
    # Hersteller/Docs/Trust Center
    "openai.com", "microsoft.com", "azure.microsoft.com", "aws.amazon.com",
    "google.com", "deepmind.google", "cloud.google.com", "anthropic.com",
    "notion.so", "atlassian.com", "zapier.com", "make.com", "airtable.com",
    "slack.com", "monday.com", "asana.com", "hubspot.com",
    "huggingface.co", "ollama.com", "langchain.com", "deepset.ai", "haystack.deepset.ai",
    "gitlab.com", "snyk.io", "datadog.com",
]
GLOBAL_EXCLUDE_DOMAINS = [
    # SEO/Video/Agentur/Foren
    "youtube.com", "tiktok.com", "instagram.com", "facebook.com", "reddit.com",
    "medium.com", "substack.com", "notion.site", "gumroad.com", "kdnuggets.com",
    "towardsdatascience.com", "udemy.com", "coursera.org",
    "stackoverflow.com", "github.com",
]

def _env_list(name: str, default_list: List[str]) -> List[str]:
    raw = os.getenv(name, "")
    if not raw:
        return list(default_list)
    return [x.strip() for x in raw.split(",") if x.strip()]

@dataclass
class ResearchPolicy:
    # Recency-Fenster
    min_days: int = int(os.getenv("RESEARCH_DAYS_MIN", "7"))
    max_days: int = int(os.getenv("RESEARCH_DAYS_MAX", "60"))
    default_days: int = int(os.getenv("RESEARCH_DAYS_DEFAULT", os.getenv("TOOLS_DAYS", "30")))

    # Limits
    max_results_tools: int = 10
    max_results_funding: int = 10
    max_results_sources: int = 12

    # Domain-Regeln
    include_funding: List[str] = field(default_factory=lambda: _env_list("RESEARCH_INCLUDE_FUNDING", PRIMARY_FUNDING_DOMAINS))
    include_tools_hint: List[str] = field(default_factory=lambda: _env_list("RESEARCH_INCLUDE_TOOLS", PRIMARY_TOOL_DOMAINS_HINT))
    exclude_global: List[str] = field(default_factory=lambda: _env_list("RESEARCH_EXCLUDE", GLOBAL_EXCLUDE_DOMAINS))

    # Qualität
    require_primary_sources: bool = True
    disallow_video: bool = True
    deduplicate_by_url: bool = True

    # Sprache/Region
    language: str = "de"
    country: str = "DE"


DEFAULT_POLICY = ResearchPolicy()


def queries_for_briefing(briefing: Dict) -> Dict[str, List[str]]:
    """Erzeugt suchspezifische Queries für Funding/Tools/Act-News auf Basis des Briefings."""
    branche = (briefing or {}).get("branche", "") or ""
    bundesland_code = (briefing or {}).get("bundesland", "") or ""
    bundesland = BUNDESLAND_MAP.get(bundesland_code.lower(), bundesland_code)

    # Funding – fokussiere auf Primärquellen und Bundesland
    funding_q = [
        "site:bmwk.de ODER site:foerderdatenbank.de künstliche Intelligenz Zuschuss Antrag Frist",
        "site:ec.europa.eu ODER site:funding-and-tenders.ec.europa.eu AI grant call deadline",
    ]
    if bundesland:
        host = bundesland.lower()
        funding_q.append(f"site:{host}.de ODER site:{host}.* Förderprogramm KI Frist")
        funding_q.append(f"site:investitionsbank-{host}.de ODER site:ib{host}.de KI Förderung Frist")

    # Tools – kuratiert (de + en, aber primär deutsch)
    tools_q = [
        f"KI Tools {branche} DSGVO hosting EU Preis",
        "DSGVO Trust Center KI Tool Preis EU Hosting",
        f"Open-Source KI {branche} on-premise GDPR",
    ]

    # EU AI Act / Compliance – aktuelle News & Guidance
    ai_act_q = [
        "site:europa.eu ODER site:ec.europa.eu AI Act guidance transparency obligations",
        "site:bmwk.de AI Act Umsetzung Unternehmen Leitfaden",
    ]

    return {"funding": funding_q, "tools": tools_q, "ai_act": ai_act_q}
