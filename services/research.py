"""
GOLD STANDARD+ FIX 1.1: Web-Search Content-Filter
================================================

Dieses File enthält die erweiterte research.py mit:
- NSFW/Pornografie-Filter
- Spam-Domain-Blocking
- Content-Validation
- Besseres Logging

INTEGRATION: Ersetze deine bestehende services/research.py mit diesem Code
"""

import logging
from typing import List, Dict, Optional, Any
import os
from tavily import TavilyClient

logger = logging.getLogger(__name__)

# ============================================================================
# NSFW-FILTER CONFIGURATION
# ============================================================================

# NSFW-Keywords (Deutsch + Englisch + Hindi/andere Sprachen)
NSFW_KEYWORDS = [
    # Englisch
    'porn', 'sex', 'xxx', 'adult', 'nude', 'naked', 'erotic', '18+', 'nsfw',
    'fetish', 'escort', 'dating', 'hookup', 'singles', 'webcam', 'camgirl',
    'strip', 'massage', 'brothel', 'prostitute', 'pornstar', 'milf',
    
    # Hindi/andere
    'chudai', 'sexy', 'bf video', 'desi sex', 'bhabhi',
    
    # Deutsch
    'porno', 'sexfilm', 'erotik', 'bordell', 'huren', 'nutten',
]

# Spam/Adult-Domains
SPAM_DOMAINS = [
    # Bekannte Pornoseiten
    'xvideos', 'pornhub', 'xhamster', 'youporn', 'redtube', 'tube8',
    'beeg', 'spankbang', 'eporner', 'txxx', 'xnxx', 'porn.com',
    
    # Dating/Escort-Seiten
    'tinder', 'bumble', 'escort', 'callgirl', 'dating',
    
    # Spam-Domains
    'click-here', 'download-now', 'free-download', 'torrent',
]


def _is_safe_content(result: dict) -> bool:
    """
    Prüft ob Suchergebnis sicher ist (kein NSFW/Spam).
    
    Args:
        result: Dict mit 'title', 'content', 'url' keys
    
    Returns:
        True wenn sicher, False wenn gefiltert werden soll
    """
    # Prüfe Title
    title = (result.get('title', '') or '').lower()
    for keyword in NSFW_KEYWORDS:
        if keyword in title:
            logger.warning(f"[FILTER] ❌ Blocked NSFW title: {title[:80]}...")
            return False
    
    # Prüfe Content
    content = (result.get('content', '') or '').lower()
    for keyword in NSFW_KEYWORDS:
        if keyword in content:
            logger.warning(f"[FILTER] ❌ Blocked NSFW content: {content[:80]}...")
            return False
    
    # Prüfe URL
    url = (result.get('url', '') or '').lower()
    for domain in SPAM_DOMAINS:
        if domain in url:
            logger.warning(f"[FILTER] ❌ Blocked spam domain: {url}")
            return False
    
    logger.debug(f"[FILTER] ✅ Safe content: {title[:50]}")
    return True


# ============================================================================
# TOOL EXTRACTION
# ============================================================================

def _extract_tool_name(title: str) -> str:
    """Extrahiert Tool-Name aus Title."""
    # Entferne häufige Präfixe/Suffixe
    name = title.replace(' - Test', '').replace(' Review', '').strip()
    
    # Kürze auf ersten Teil vor Pipe/Dash
    if '|' in name:
        name = name.split('|')[0].strip()
    if ' - ' in name and len(name.split(' - ')) > 1:
        name = name.split(' - ')[0].strip()
    
    return name[:100]  # Max 100 chars


def _categorize_tool(content: str) -> str:
    """Kategorisiert Tool basierend auf Content."""
    content_lower = content.lower()
    
    categories = {
        'Textgenerierung': ['text', 'schreiben', 'content', 'copywriting', 'artikel'],
        'Bildgenerierung': ['bild', 'image', 'foto', 'grafik', 'design', 'midjourney', 'dalle'],
        'Datenanalyse': ['daten', 'analytics', 'analyse', 'data', 'statistik'],
        'Automatisierung': ['automation', 'workflow', 'zapier', 'make.com', 'n8n'],
        'Kundenservice': ['customer', 'support', 'chatbot', 'chat', 'kunde'],
        'Marketing': ['marketing', 'social media', 'ads', 'kampagne', 'seo'],
        'Entwicklung': ['code', 'programming', 'entwicklung', 'github', 'api'],
    }
    
    for category, keywords in categories.items():
        if any(kw in content_lower for kw in keywords):
            return category
    
    return 'Sonstiges'


def _extract_tools_from_results(results: List[dict]) -> List[dict]:
    """
    Extrahiert Tool-Informationen aus Tavily-Ergebnissen.
    
    WICHTIG: Wendet NSFW-Filter an!
    """
    tools = []
    filtered_count = 0
    
    # Hole mehr Ergebnisse als benötigt (wegen Filterung)
    for result in results[:15]:
        # ⚠️ CRITICAL: Content-Filter anwenden
        if not _is_safe_content(result):
            filtered_count += 1
            continue
        
        tool = {
            "name": _extract_tool_name(result.get('title', 'Unbekanntes Tool')),
            "description": (result.get('content', '') or '')[:300],  # Max 300 chars
            "url": result.get('url', ''),
            "category": _categorize_tool(result.get('content', '')),
            "relevance_score": result.get('score', 0.5)
        }
        
        # Nur Tools mit URL aufnehmen
        if tool['url'] and len(tool['description']) > 20:
            tools.append(tool)
        
        # Stoppe bei 5 validen Tools
        if len(tools) >= 5:
            break
    
    logger.info(f"[TOOLS] ✅ Extracted {len(tools)} tools, filtered {filtered_count} NSFW/spam")
    return tools


# ============================================================================
# FUNDING EXTRACTION
# ============================================================================

def _extract_provider(url: str) -> str:
    """Extrahiert Förder-Provider aus URL."""
    url_lower = url.lower()
    
    providers = {
        'BAFA': 'bafa',
        'KfW': 'kfw',
        'BMWi': ['bmwi', 'bmwk'],
        'Bundesregierung': 'bundesregierung',
        'Förderbank': 'foerderbank',
        'IHK': 'ihk',
        'Land': 'land',
    }
    
    for provider, keywords in providers.items():
        if isinstance(keywords, str):
            keywords = [keywords]
        if any(kw in url_lower for kw in keywords):
            return provider
    
    return 'Sonstige'


def _extract_funding_from_results(results: List[dict]) -> List[dict]:
    """
    Extrahiert Förderprogramm-Informationen aus Tavily-Ergebnissen.
    
    WICHTIG: Wendet NSFW-Filter an!
    """
    foerderungen = []
    filtered_count = 0
    
    # Hole mehr Ergebnisse als benötigt (wegen Filterung)
    for result in results[:15]:
        # ⚠️ CRITICAL: Content-Filter anwenden
        if not _is_safe_content(result):
            filtered_count += 1
            continue
        
        program = {
            "name": (result.get('title', '') or '')[:200],
            "description": (result.get('content', '') or '')[:400],  # Max 400 chars
            "url": result.get('url', ''),
            "provider": _extract_provider(result.get('url', '')),
            "relevance_score": result.get('score', 0.5)
        }
        
        # Nur Programme mit URL und sinnvoller Description
        if program['url'] and len(program['description']) > 30:
            foerderungen.append(program)
        
        # Stoppe bei 5 validen Programmen
        if len(foerderungen) >= 5:
            break
    
    logger.info(f"[FUNDING] ✅ Extracted {len(foerderungen)} programs, filtered {filtered_count} NSFW/spam")
    return foerderungen


# ============================================================================
# MAIN SEARCH FUNCTION
# ============================================================================

def search_funding_and_tools(
    branche: str,
    bundesland: Optional[str] = None,
    run_id: Optional[str] = "unknown"
) -> Dict[str, Any]:
    """
    Sucht nach Förderprogrammen und KI-Tools für ein Unternehmen.
    
    Args:
        branche: Branche des Unternehmens (z.B. "Maschinenbau", "E-Commerce")
        bundesland: Bundesland (z.B. "Bayern", "NRW") - Optional
        run_id: Run-ID für Logging
    
    Returns:
        Dict mit 'funding' und 'tools' Listen
    """
    logger.info(f"[{run_id}] 🔍 Starting research for: {branche} in {bundesland or 'Deutschland'}")
    
    # Tavily-Client initialisieren
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error(f"[{run_id}] ❌ TAVILY_API_KEY nicht gesetzt!")
        return {"funding": [], "tools": []}
    
    client = TavilyClient(api_key=api_key)
    
    result = {
        "funding": [],
        "tools": []
    }
    
    # ============================================================================
    # SEARCH 1: Förderprogramme
    # ============================================================================
    try:
        # Query für Förderprogramme
        funding_query = f"KI Digitalisierung Förderprogramme {branche}"
        if bundesland:
            funding_query += f" {bundesland}"
        
        logger.info(f"[{run_id}] 🔍 Funding query: {funding_query}")
        
        funding_response = client.search(
            query=funding_query,
            search_depth="advanced",
            max_results=15,  # Mehr holen wegen Filterung
            include_domains=[
                "bafa.de", "kfw.de", "bmwk.de", "foerderdatenbank.de",
                "ihk.de", "handwerkskammer.de"
            ]
        )
        
        funding_results = funding_response.get("results", [])
        logger.info(f"[{run_id}] 📊 Got {len(funding_results)} raw funding results")
        
        # Extrahiere + Filtere
        result["funding"] = _extract_funding_from_results(funding_results)
        
    except Exception as e:
        logger.exception(f"[{run_id}] ❌ Funding search failed: {e}")
    
    # ============================================================================
    # SEARCH 2: KI-Tools
    # ============================================================================
    try:
        # Query für KI-Tools
        tools_query = f"beste KI Tools Software {branche} Deutschland 2024"
        
        logger.info(f"[{run_id}] 🔍 Tools query: {tools_query}")
        
        tools_response = client.search(
            query=tools_query,
            search_depth="advanced",
            max_results=15,  # Mehr holen wegen Filterung
            # Keine Domain-Einschränkung, aber Filter wird angewendet
        )
        
        tools_results = tools_response.get("results", [])
        logger.info(f"[{run_id}] 📊 Got {len(tools_results)} raw tool results")
        
        # Extrahiere + Filtere
        result["tools"] = _extract_tools_from_results(tools_results)
        
    except Exception as e:
        logger.exception(f"[{run_id}] ❌ Tools search failed: {e}")
    
    # ============================================================================
    # FINAL SUMMARY
    # ============================================================================
    logger.info(
        f"[{run_id}] ✅ Research completed: "
        f"{len(result['funding'])} funding programs, "
        f"{len(result['tools'])} tools"
    )
    
    return result


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test NSFW-Filter
    print("\n=== TESTING NSFW FILTER ===\n")
    
    test_cases = [
        {
            'title': 'Die besten KI Tools für Marketing 2024',
            'url': 'https://heise.de/ki-tools',
            'content': 'Eine Übersicht über KI-gestützte Marketing-Tools...',
        },
        {
            'title': 'Hindi Chudai Video XXX Adult Content',
            'url': 'https://xvideos.com/something',
            'content': 'Adult content porn sex xxx...',
        },
        {
            'title': 'ChatGPT Tutorial für Anfänger',
            'url': 'https://openai.com/blog/chatgpt',
            'content': 'So nutzen Sie ChatGPT effektiv für Ihr Business...',
        },
        {
            'title': 'Sexy Singles in Your Area - Dating',
            'url': 'https://dating-spam.com',
            'content': 'Meet hot singles now! Click here for hookup...',
        },
    ]
    
    for i, case in enumerate(test_cases, 1):
        is_safe = _is_safe_content(case)
        status = "✅ SAFE" if is_safe else "❌ BLOCKED"
        print(f"{i}. {status}: {case['title'][:60]}")
    
    print("\n=== TEST COMPLETED ===\n")
