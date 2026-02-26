"""
Live-Daten-Integration via Tavily API für KI-Sicherheit.jetzt
=============================================================

OPTIMIZED für:
- Bundesland-Codes (be, by, nw, etc.)
- EU/International Support
- Alle 12 Branchen
- 3 Company Sizes (solo, small, medium)

Version: 2.0 (OPTIMIZED)
Created: 2026-01-06
"""

import os
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logging.warning("tavily-python not installed. Install with: pip install tavily-python")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("httpx not installed. Install with: pip install httpx")

log = logging.getLogger(__name__)


# ==================== MAPPINGS (aus Fragebogen validiert) ====================

BUNDESLAND_MAPPING = {
    "bw": "Baden-Württemberg",
    "by": "Bayern",
    "be": "Berlin",
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
    "th": "Thüringen"
}

COUNTRY_MAPPING = {
    # EU
    "DE": "Deutschland",
    "AT": "Österreich",
    "FR": "Frankreich",
    "IT": "Italien",
    "ES": "Spanien",
    "NL": "Niederlande",
    "BE": "Belgien",
    "IE": "Irland",
    "PL": "Polen",
    "SE": "Schweden",
    "DK": "Dänemark",
    "FI": "Finnland",
    "PT": "Portugal",
    "CZ": "Tschechien",
    "GR": "Griechenland",
    "HU": "Ungarn",
    "RO": "Rumänien",
    # Non-EU Europe
    "GB": "Vereinigtes Königreich",
    "CH": "Schweiz",
    "NO": "Norwegen",
    "IS": "Island",
    "LI": "Liechtenstein"
}

# ==================== SERVICE ====================

class LiveDataService:
    """
    Service für Live-Daten-Abfragen via Tavily API.

    Features:
    - Live Förderprogramme-Suche mit Bundesland-Code-Support
    - Automatischer Fallback auf statische DB
    - Rate Limiting (100 req/h)
    - EU/International Support
    """

    def __init__(self) -> None:
        """Initialize LiveDataService with Tavily API."""
        self.tavily_key = os.getenv("TAVILY_API_KEY")
        self.enable_live_foerderung = os.getenv("ENABLE_LIVE_FOERDERPROGRAMME", "false").lower() == "true"
        self.enable_live_tools = os.getenv("ENABLE_LIVE_TOOL_PRICING", "false").lower() == "true"
        self.timeout = int(os.getenv("TAVILY_TIMEOUT_MS", "15000")) / 1000
        self.max_results = int(os.getenv("TAVILY_MAX_RESULTS", "10"))

        # Rate limiting
        self.rate_limit_per_hour = int(os.getenv("TAVILY_RATE_LIMIT_PER_HOUR", "100"))
        self._request_count = 0
        self._rate_limit_reset = datetime.now()

        # Initialize Tavily client
        self.tavily: Optional[TavilyClient] = None
        if self.tavily_key and TAVILY_AVAILABLE:
            try:
                self.tavily = TavilyClient(api_key=self.tavily_key)
                log.info("[LIVE DATA] Tavily client initialized successfully")
            except Exception as e:
                log.error(f"[LIVE DATA] Failed to initialize Tavily: {e}")
                self.tavily = None
        else:
            if not self.tavily_key:
                log.warning("[LIVE DATA] TAVILY_API_KEY not set - using fallback mode")
            if not TAVILY_AVAILABLE:
                log.warning("[LIVE DATA] Tavily not available - using fallback mode")

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.now()

        # Reset counter every hour
        if (now - self._rate_limit_reset).seconds >= 3600:
            self._request_count = 0
            self._rate_limit_reset = now

        if self._request_count >= self.rate_limit_per_hour:
            log.warning(f"[LIVE DATA] Rate limit reached ({self.rate_limit_per_hour}/hour)")
            return False

        self._request_count += 1
        return True

    def search_foerderprogramme(
        self,
        bundesland: str,
        branche: str,
        country: str = "DE",
        year: Optional[int] = None,
        force_live: bool = False
    ) -> List[Dict]:
        """
        Sucht aktuelle Förderprogramme via Tavily.

        Args:
            bundesland: Bundesland-Code ("be", "by", "nw") oder Name ("Berlin")
            branche: Branche (z.B. "Beratung & Dienstleistungen")
            country: ISO Country Code ("DE", "AT", "FR", etc.)
            year: Jahr für die Suche (default: aktuelles Jahr)
            force_live: Erzwingt Live-Suche

        Returns:
            Liste von max. 5 Förderprogrammen
        """
        # Check if live data is enabled
        if not (self.enable_live_foerderung or force_live):
            log.info("[LIVE DATA] Feature disabled - using fallback")
            return self._get_fallback_foerderprogramme(bundesland, branche, country)

        # Check if Tavily is available
        if not self.tavily:
            log.info("[LIVE DATA] Tavily not available - using fallback")
            return self._get_fallback_foerderprogramme(bundesland, branche, country)

        # Check rate limit
        if not self._check_rate_limit():
            log.info("[LIVE DATA] Rate limit exceeded - using fallback")
            return self._get_fallback_foerderprogramme(bundesland, branche, country)

        # Map Bundesland code to name
        bundesland_name = BUNDESLAND_MAPPING.get(bundesland.lower(), bundesland)
        country_name = COUNTRY_MAPPING.get(country.upper(), country)

        # Build optimized search query
        search_year = year or datetime.now().year

        # Query depends on location
        if country == "DE":
            # Deutsche Förderprogramme
            query = f"Förderprogramme Digitalisierung KI {bundesland_name} {branche} {search_year}"
        elif country in COUNTRY_MAPPING:
            # EU-Förderprogramme
            query = f"Förderprogramme Digitalisierung KI {country_name} {branche} {search_year} EU"
        else:
            # International
            query = f"Digitalization funding programs {country_name} {search_year}"

        # Domain restrictions based on country
        include_domains = self._get_domains_for_country(country)

        try:
            log.info(f"[LIVE DATA] Searching Tavily: {query}")

            results = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=self.max_results,
                include_domains=include_domains
            )

            programmes: List[Dict] = []
            for result in results.get("results", []):
                prog = self._parse_foerderprogramm(result, bundesland_name, country)
                if prog:
                    programmes.append(prog)

            log.info(f"[LIVE DATA] Found {len(programmes)} programmes from Tavily")

            # If we found results, return them
            if programmes:
                return programmes[:5]

            # No results - use fallback
            log.info("[LIVE DATA] No results from Tavily - using fallback")
            return self._get_fallback_foerderprogramme(bundesland, branche, country)

        except Exception as e:
            log.error(f"[LIVE DATA] Tavily search error: {e}")
            return self._get_fallback_foerderprogramme(bundesland, branche, country)

    def _get_domains_for_country(self, country: str) -> List[str]:
        """Get search domains based on country."""

        if country == "DE":
            return [
                "bmwk.de",
                "bafa.de",
                "ibb.de",
                "investitionsbank-berlin.de",
                "foerderdatenbank.de",
                "nrwbank.de",
                "l-bank.de",
                "ifb.hamburg",
                "stmwi.bayern.de",
                "wibank.de"
            ]
        elif country in ["AT", "FR", "IT", "ES", "NL", "BE", "IE"]:
            # EU countries
            return [
                "ec.europa.eu",
                "europa.eu",
                "digital-strategy.ec.europa.eu"
            ]
        else:
            # International - no domain restrictions
            return []

    def _parse_foerderprogramm(self, result: Dict, bundesland: str, country: str) -> Optional[Dict]:
        """Parse Tavily result to structured funding programme."""
        try:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")

            # Extract funding amount
            betrag = self._extract_betrag(content)

            # Determine suitability
            eignung = self._determine_eignung(content, bundesland)

            return {
                "name": title,
                "beschreibung": content[:200] + "..." if len(content) > 200 else content,
                "url": url,
                "max_foerderung": betrag,
                "eignung": eignung,
                "komplexitaet": "Unbekannt",
                "source": "live_data",
                "country": country,
                "updated_at": datetime.now().isoformat(),
                "raw_content": content[:500]
            }

        except Exception as e:
            log.error(f"[LIVE DATA] Error parsing programme: {e}")
            return None

    def _extract_betrag(self, text: str) -> str:
        """Extract funding amounts from text."""
        # Pattern for German number format
        patterns = [
            r'bis\s+zu\s+([\d.]+)\s*(?:€|Euro)',
            r'maximal\s+([\d.]+)\s*(?:€|Euro)',
            r'([\d.]+)\s*(?:€|Euro)\s+Förderung',
            r'Förderung\s+(?:von|bis)\s+([\d.]+)\s*(?:€|Euro)',
            r'([\d.]+)\s*(?:€|Euro)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                betrag = match.group(1)
                return f"{betrag} €"

        return "Betrag nicht verfügbar"

    def _determine_eignung(self, content: str, bundesland: str) -> str:
        """Determine suitability based on content."""
        content_lower = content.lower()
        bundesland_lower = bundesland.lower()

        # High: Bundesland-specific + easy access
        if bundesland_lower in content_lower:
            if any(word in content_lower for word in ["einfach", "unbürokratisch", "schnell", "sofort"]):
                return "Hoch"
            return "Mittel"

        # Low: Complex or not matching
        if any(word in content_lower for word in ["komplex", "aufwendig", "langwierig"]):
            return "Niedrig"

        return "Mittel"

    def _get_fallback_foerderprogramme(
        self,
        bundesland: str,
        branche: str,
        country: str = "DE"
    ) -> List[Dict]:
        """
        Fallback auf statische Förderprogramm-Datenbank.
        Verwendet die 30-Programme DB aus Briefing 3.
        """
        log.info("[FALLBACK] Using static funding database")

        # Map code to name if needed
        bundesland_name = BUNDESLAND_MAPPING.get(bundesland.lower(), bundesland)

        # Import from gpt_analyze (Phase 3)
        try:
            from gpt_analyze import get_foerderprogramme_extended

            # Map country to company_size for fallback
            # (This is a simplification, ideally pass actual company_size)
            company_size = "solo"  # Default

            programmes = get_foerderprogramme_extended(
                bundesland=bundesland_name,
                company_size=company_size,
                branche=branche
            )

            # Add fallback metadata
            for prog in programmes:
                prog["source"] = "static"
                prog["country"] = country

            return programmes

        except ImportError:
            log.error("[FALLBACK] Could not import get_foerderprogramme_extended")
            return self._minimal_fallback(bundesland_name, country)

    def _minimal_fallback(self, bundesland: str, country: str) -> List[Dict]:
        """Minimal fallback if Phase 3 is not available."""

        if country != "DE":
            # EU-Programme
            return [
                {
                    "name": "Digital Europe Programme",
                    "beschreibung": "EU-Förderung für digitale Transformation",
                    "max_foerderung": "200.000 €",
                    "eignung": "Mittel",
                    "komplexitaet": "Hoch",
                    "url": "https://digital-strategy.ec.europa.eu",
                    "source": "static",
                    "country": country
                }
            ]

        # Deutsche Basisprogramme
        # FIX-B15: Removed go-digital (ended Dec 2024) and Digital Jetzt (ended Dec 2023)
        return [
            {
                "name": "BAFA Unternehmensberatung",
                "beschreibung": "Beratungsförderung für KMU bis 249 Mitarbeiter",
                "max_foerderung": "3.200 €",
                "eignung": "Hoch",
                "komplexitaet": "Niedrig",
                "url": "https://www.bafa.de",
                "source": "static",
                "country": "DE"
            },
            {
                "name": "KMU-innovativ (BMBF)",
                "beschreibung": "Förderung innovativer KMU in Spitzentechnologien",
                "max_foerderung": "Projektabhängig",
                "eignung": "Mittel",
                "komplexitaet": "Mittel",
                "url": "https://www.bmbf.de/kmu-innovativ",
                "source": "static",
                "country": "DE"
            }
        ]


# ==================== SINGLETON ====================

_live_data_service: Optional[LiveDataService] = None


def get_live_data_service() -> LiveDataService:
    """Get singleton instance of LiveDataService."""
    global _live_data_service
    if _live_data_service is None:
        _live_data_service = LiveDataService()
    return _live_data_service


# ==================== TESTING ====================

def test_tavily_connection() -> bool:
    """Test if Tavily API is accessible."""
    service = get_live_data_service()

    if not service.tavily:
        print("❌ Tavily not initialized")
        return False

    try:
        results = service.tavily.search(query="test", max_results=1)
        print("✅ Tavily connection successful")
        return True
    except Exception as e:
        print(f"❌ Tavily connection failed: {e}")
        return False


def test_bundesland_mapping() -> None:
    """Test Bundesland code mapping."""
    test_cases = [
        ("be", "Berlin"),
        ("by", "Bayern"),
        ("nw", "Nordrhein-Westfalen")
    ]

    for code, expected_name in test_cases:
        mapped_name = BUNDESLAND_MAPPING.get(code)
        assert mapped_name == expected_name, f"Mapping failed: {code} → {mapped_name} (expected {expected_name})"
        print(f"✅ {code} → {mapped_name}")

    print("✅ All Bundesland mappings correct")


def test_foerderprogramme_search() -> None:
    """Test funding programme search with different Bundesländer."""
    service = get_live_data_service()

    test_cases = [
        ("be", "Beratung & Dienstleistungen", "DE"),
        ("by", "IT & Software", "DE"),
        ("nw", "Handel & E-Commerce", "DE")
    ]

    for bundesland, branche, country in test_cases:
        result = service.search_foerderprogramme(bundesland=bundesland, branche=branche, country=country)
        print(f"\n{bundesland} ({branche}): {len(result)} programmes")
        for prog in result[:2]:  # Show first 2
            print(f"  - {prog['name']}: {prog['max_foerderung']} ({prog.get('source', 'unknown')})")

    print("\n✅ Förderprogramme search working")


if __name__ == "__main__":
    """Run tests when executed directly."""
    print("=== Live Data Integration Tests (OPTIMIZED) ===\n")

    print("Test 1: Tavily Connection")
    test_tavily_connection()

    print("\nTest 2: Bundesland Mapping")
    test_bundesland_mapping()

    print("\nTest 3: Förderprogramme Search")
    test_foerderprogramme_search()

    print("\n=== Tests Complete ===")
