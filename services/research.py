# -*- coding: utf-8 -*-
"""
Research Service mit Tavily Integration
Optimiert für KI-Sicherheit.jetzt Report-System
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


def search_funding_and_tools(branch: str, state: str = None) -> dict:
    """
    Recherchiert aktuelle KI-Tools und Förderprogramme für Branche/Region.
    
    Args:
        branch: Branche (z.B. 'beratung', 'handel', 'produktion')
        state: Bundesland-Kürzel (z.B. 'be', 'by', 'nw')
    
    Returns:
        Dict mit tools, foerderungen, und metadata
    """
    try:
        # Prüfe ob Tavily verfügbar ist
        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            logger.warning("TAVILY_API_KEY not found - returning empty results")
            return _empty_research_result()
        
        # Import Tavily (lazy import)
        try:
            from tavily import TavilyClient
        except ImportError:
            logger.error("tavily-python not installed - run: pip install tavily-python")
            return _empty_research_result()
        
        # Initialisiere Client
        client = TavilyClient(api_key=api_key)
        logger.info(f"[RESEARCH] Starting Tavily search for branch={branch}, state={state}")
        
        # Suche 1: KI-Tools für die Branche
        tools_query = f"beste KI Tools für {branch} Deutschland 2025"
        logger.info(f"[TAVILY] Query 1: {tools_query}")
        
        tools_results = client.search(
            query=tools_query,
            search_depth="advanced",
            max_results=5,
            include_domains=["heise.de", "t3n.de", "computerwoche.de", "it-zoom.de"]
        )
        
        # Suche 2: Förderprogramme
        if state:
            funding_query = f"KI Förderung Digitalisierung {state} Deutschland 2025"
        else:
            funding_query = "KI Förderung Digitalisierung Deutschland Bundesweit 2025"
        
        logger.info(f"[TAVILY] Query 2: {funding_query}")
        
        funding_results = client.search(
            query=funding_query,
            search_depth="advanced",
            max_results=5,
            include_domains=["foerderdatenbank.de", "bmwk.de", "digitalagentur.de"]
        )
        
        # Extrahiere und strukturiere Ergebnisse
        tools = _extract_tools_from_results(tools_results.get('results', []))
        foerderungen = _extract_funding_from_results(funding_results.get('results', []))
        
        logger.info(f"[RESEARCH] Found {len(tools)} tools and {len(foerderungen)} funding programs")
        
        return {
            "tools": tools,
            "foerderungen": foerderungen,
            "metadata": {
                "searched_at": datetime.now().isoformat(),
                "branch": branch,
                "state": state,
                "queries": [tools_query, funding_query],
                "source": "tavily"
            }
        }
        
    except Exception as e:
        logger.error(f"[RESEARCH] Error in search_funding_and_tools: {e}", exc_info=True)
        return _empty_research_result()


def _extract_tools_from_results(results: List[dict]) -> List[dict]:
    """Extrahiert Tool-Informationen aus Tavily-Ergebnissen."""
    tools = []
    
    for result in results[:5]:  # Max 5 Tools
        tool = {
            "name": _extract_tool_name(result.get('title', '')),
            "description": result.get('content', '')[:200],  # Max 200 chars
            "url": result.get('url', ''),
            "category": _categorize_tool(result.get('content', '')),
            "relevance_score": result.get('score', 0.0)
        }
        
        # Nur hinzufügen wenn URL vorhanden
        if tool['url']:
            tools.append(tool)
    
    return tools


def _extract_funding_from_results(results: List[dict]) -> List[dict]:
    """Extrahiert Förderprogramm-Informationen aus Tavily-Ergebnissen."""
    foerderungen = []
    
    for result in results[:5]:  # Max 5 Programme
        program = {
            "name": result.get('title', ''),
            "description": result.get('content', '')[:300],  # Max 300 chars
            "url": result.get('url', ''),
            "provider": _extract_provider(result.get('url', '')),
            "relevance_score": result.get('score', 0.0)
        }
        
        # Nur hinzufügen wenn URL vorhanden
        if program['url']:
            foerderungen.append(program)
    
    return foerderungen


def _extract_tool_name(title: str) -> str:
    """Extrahiert Tool-Namen aus Artikel-Titel."""
    # Entferne gängige Präfixe/Suffixe
    for prefix in ['Die besten', 'Top', 'Review:', 'Test:']:
        if title.startswith(prefix):
            title = title[len(prefix):].strip()
    
    # Nimm ersten Teil vor Trennzeichen
    for separator in [' - ', ' | ', ': ']:
        if separator in title:
            title = title.split(separator)[0].strip()
            break
    
    return title[:100]  # Max 100 chars


def _categorize_tool(content: str) -> str:
    """Kategorisiert Tool basierend auf Inhalt."""
    content_lower = content.lower()
    
    if any(keyword in content_lower for keyword in ['chatbot', 'chat', 'konversation']):
        return 'Kundenservice'
    elif any(keyword in content_lower for keyword in ['text', 'schreiben', 'content']):
        return 'Content-Erstellung'
    elif any(keyword in content_lower for keyword in ['analyse', 'daten', 'insights']):
        return 'Datenanalyse'
    elif any(keyword in content_lower for keyword in ['automation', 'prozess', 'workflow']):
        return 'Prozessautomatisierung'
    else:
        return 'Sonstiges'


def _extract_provider(url: str) -> str:
    """Extrahiert Anbieter aus URL."""
    if 'foerderdatenbank.de' in url:
        return 'Bund'
    elif 'bmwk.de' in url:
        return 'BMWK'
    elif any(state in url for state in ['.bayern.de', '.nrw.de', '.berlin.de']):
        return 'Land'
    else:
        return 'Extern'


def _empty_research_result() -> dict:
    """Gibt leere Struktur zurück wenn Recherche fehlschlägt."""
    return {
        "tools": [],
        "foerderungen": [],
        "metadata": {
            "searched_at": datetime.now().isoformat(),
            "error": "No API key or search failed",
            "source": "none"
        }
    }


# Fallback-Funktion für Offline-Testing
def get_mock_research_data(branch: str, state: str = None) -> dict:
    """Mock-Daten für Testing ohne API-Key."""
    return {
        "tools": [
            {
                "name": "ChatGPT Enterprise",
                "description": "Professionelle KI-Lösung für Unternehmen mit erweiterten Sicherheits- und Compliance-Features",
                "url": "https://openai.com/enterprise",
                "category": "Kundenservice",
                "relevance_score": 0.95
            },
            {
                "name": "Jasper.ai",
                "description": "KI-gestützte Content-Erstellung für Marketing und Kommunikation",
                "url": "https://jasper.ai",
                "category": "Content-Erstellung",
                "relevance_score": 0.88
            }
        ],
        "foerderungen": [
            {
                "name": "Digital Jetzt",
                "description": "Bundesförderung für Digitalisierung in KMU - bis zu 50.000 Euro Zuschuss",
                "url": "https://www.bmwk.de/digital-jetzt",
                "provider": "BMWK",
                "relevance_score": 0.92
            }
        ],
        "metadata": {
            "searched_at": datetime.now().isoformat(),
            "branch": branch,
            "state": state,
            "source": "mock"
        }
    }
