# -*- coding: utf-8 -*-
"""
services/research_policy.py
===========================
Gold-Standard Research-Policy für aktuelle Tools, News und Förderprogramme
über Tavily & Perplexity. Fokus: belastbare Primärquellen, Aktualität, Compliance.

Integration:
    from services.research_pipeline import run_research
    data = run_research(briefing_dict)
    # Mergen in Template-Kontext:
    context.update(data)  # liefert u.a. TOOLS_HTML, FOERDERPROGRAMME_HTML, QUELLEN_HTML, last_updated

Konfiguration via ENV:
    TAVILY_API_KEY
    PERPLEXITY_API_KEY
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict

# -- Bundesland-Codes → Volltext (für Förder-Suche) ---------------------------
BUNDESLAND_MAP = {
    "be": "Berlin",
    "by": "Bayern",
    "bw": "Baden-Württemberg",
    "bb": "Brandenburg",
    "hb": "Bremen",
    "hh": "Hamburg",
    "he": "Hessen",
    "mv": "Mecklenburg-Vorpommern",
    "ni": "Niedersachsen",
    "nw": "Nordrhein-Westfalen",
    "rp": "Rheinland-Pfalz",
    "sl": "Saarland",
    "sn": "Sachsen",
    "st": "Sachsen-Anhalt",
    "sh": "Schleswig-Holstein",
    "th": "Thüringen",
}

PRIMARY_FUNDING_DOMAINS = [
    # Bund / EU / Länder
    "bmwk.de", "bmbf.de", "bundesanzeiger.de", "foerderdatenbank.de",
    "ec.europa.eu", "europa.eu", "funding-and-tenders.ec.europa.eu",
    "dip.bundestag.de",
    # Landesförderbanken / -ministerien (Auszug)
    "ibb.de", "investitionsbank-berlin.de", "nrwbank.de", "l-bank.de", "ifb.hamburg",
    "saarland.de", "bayern.de", "stmwi.bayern.de", "stmwk.bayern.de",
]

PRIMARY_TOOL_DOMAINS_HINT = [
    # Hersteller/Docs/Trust-Centers – Beispiele
    "openai.com", "microsoft.com", "azure.microsoft.com", "aws.amazon.com",
    "google.com", "deepmind.google", "anthropic.com",
    "atlassian.com", "notion.so", "zapier.com", "make.com",
    "huggingface.co", "ollama.com", "langchain.com", "deepset.ai",
]

GLOBAL_EXCLUDE_DOMAINS = [
    # SEO/Agentur/Video/Foren (für Report ungeeignet)
    "youtube.com", "tiktok.com", "instagram.com", "facebook.com", "reddit.com",
    "medium.com", "substack.com", "notion.site", "gumroad.com",
    "udemy.com", "coursera.org", "kdnuggets.com", "towardsdatascience.com",
    "stackoverflow.com", "github.com",  # i.d.R. kein Primärartikel
]

@dataclass
class ResearchPolicy:
    # Recency-Fenster: 7–60 Tage (Default)
    min_days: int = 7
    max_days: int = 60

    # Limits
    max_results_tools: int = 10
    max_results_funding: int = 10
    max_results_sources: int = 12

    # Domain-Regeln
    include_funding: List[str] = field(default_factory=lambda: list(PRIMARY_FUNDING_DOMAINS))
    include_tools_hint: List[str] = field(default_factory=lambda: list(PRIMARY_TOOL_DOMAINS_HINT))
    exclude_global: List[str] = field(default_factory=lambda: list(GLOBAL_EXCLUDE_DOMAINS))

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
        f"site:bmwk.de ODER site:foerderdatenbank.de künstliche Intelligenz Zuschuss Antrag Frist",
        f"site:ec.europa.eu ODER site:funding-and-tenders.ec.europa.eu AI grant call deadline",
    ]
    if bundesland:
        funding_q.append(f'site:{bundesland.lower()}.de ODER site:{bundesland.lower()}.* Förderprogramm KI Frist')

    # Tools – kuratiert (de + en, aber primär deutsch)
    tools_q = [
        f"KI Tools {branche} DSGVO hosting EU Preis",
        f"DSGVO Trust Center KI Tool Preis EU Hosting",
        f"Open-Source KI {branche} on-premise",
    ]

    # EU AI Act / Compliance – aktuelle News & Guidance
    ai_act_q = [
        "site:europa.eu ODER site:ec.europa.eu AI Act guidance transparency obligations",
        "site:bmwk.de AI Act Umsetzung Unternehmen Leitfaden",
    ]

    return {"funding": funding_q, "tools": tools_q, "ai_act": ai_act_q}
