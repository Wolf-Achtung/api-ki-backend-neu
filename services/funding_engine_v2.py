# -*- coding: utf-8 -*-
"""
Sprint G26: Funding Engine V2 - Multi-Year Funding Matrix 2025/2026/2027

Enhanced funding programme evaluation with:
- Multi-year horizon (2025, 2026, 2027)
- Year-factor scoring for temporal relevance
- Level-based classification (EU, Federal, State, Regional)
- Category-based matching (Digitalisierung, KI, Innovation, etc.)
- Size-fit scores for solo/team/KMU
- Risk and deadline tracking

Version: 2.0.0 (Sprint G26)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

FundingLevel = Literal["eu", "federal", "state", "regional", "private"]
FundingCategory = Literal[
    "digitalisierung", "ki", "innovation", "forschung",
    "nachhaltigkeit", "gruendung", "export", "allgemein", "medien"
]
FundingYear = Literal[2025, 2026, 2027]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FundingProgramme:
    """
    Multi-dimensional representation of a funding programme.

    G26: Extended dataclass for multi-year funding matrix with
    comprehensive evaluation dimensions.
    """
    # Core identification
    name: str
    year: int  # Primary year (2025, 2026, 2027)
    level: FundingLevel  # eu, federal, state, regional, private
    country: str  # ISO country code (DE, AT, EU, etc.)
    category: FundingCategory  # Primary category

    # Funding details
    funding_rate: str  # e.g., "50%", "30-50%", "bis 70%"
    max_amount: str  # e.g., "50.000 €", "2,5 Mio. €"
    max_amount_numeric: float = 0.0  # Numeric for sorting

    # Scoring
    match_score: float = 0.0  # 0.0-1.0 overall match
    branch_relevance: float = 0.0  # 0.0-1.0 branch fit
    year_factor: float = 1.0  # Year-based weighting

    # Size fit scores (0.0-1.0)
    fit_solo: float = 0.5
    fit_team: float = 0.5
    fit_kmu: float = 0.5

    # Requirements and constraints
    requirements: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)

    # Temporal info
    deadline: Optional[str] = None  # e.g., "Q2 2025", "31.12.2025"
    deadline_urgency: str = "normal"  # urgent, normal, flexible

    # Additional info
    notes: str = ""
    provider: str = ""
    url: Optional[str] = None

    # Multi-year availability
    years_available: List[int] = field(default_factory=lambda: [2025])

    # AI Act relevance
    ai_act_relevant: bool = False
    ki_relevance: str = "medium"  # high, medium, low

    # Compliance info
    eu_compliant: bool = True
    dsgvo_relevant: bool = False

    def __post_init__(self) -> None:
        """Post-initialization validation and normalization."""
        # Normalize level
        if self.level not in ("eu", "federal", "state", "regional", "private"):
            self.level = "federal"

        # Ensure years_available includes primary year
        if self.year not in self.years_available:
            self.years_available = [self.year] + self.years_available

        # Parse max_amount_numeric from max_amount string
        if not self.max_amount_numeric and self.max_amount:
            self.max_amount_numeric = _parse_amount(self.max_amount)

    def get_size_fit(self, size: str) -> float:
        """Get fit score for company size."""
        size_lower = size.lower() if size else "team"
        if "solo" in size_lower or "1" == size_lower:
            return self.fit_solo
        elif "kmu" in size_lower or "sme" in size_lower or "mittel" in size_lower:
            return self.fit_kmu
        return self.fit_team

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "year": self.year,
            "level": self.level,
            "country": self.country,
            "category": self.category,
            "funding_rate": self.funding_rate,
            "max_amount": self.max_amount,
            "max_amount_numeric": self.max_amount_numeric,
            "match_score": round(self.match_score, 2),
            "branch_relevance": round(self.branch_relevance, 2),
            "year_factor": round(self.year_factor, 2),
            "fit_solo": round(self.fit_solo, 2),
            "fit_team": round(self.fit_team, 2),
            "fit_kmu": round(self.fit_kmu, 2),
            "requirements": self.requirements,
            "risks": self.risks,
            "deadline": self.deadline,
            "deadline_urgency": self.deadline_urgency,
            "notes": self.notes,
            "provider": self.provider,
            "url": self.url,
            "years_available": self.years_available,
            "ai_act_relevant": self.ai_act_relevant,
            "ki_relevance": self.ki_relevance,
        }


@dataclass
class FundingEvaluationResult:
    """Result of funding programme evaluation."""
    programmes: List[FundingProgramme]
    total_evaluated: int
    filtered_count: int
    year_distribution: Dict[int, int]
    level_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    evaluation_context: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_programmes(self) -> bool:
        return len(self.programmes) > 0

    @property
    def top_3(self) -> List[FundingProgramme]:
        return self.programmes[:3]


# =============================================================================
# CORE FUNDING DATABASE (2025-2027)
# =============================================================================

FUNDING_PROGRAMMES_2025_2027: List[Dict[str, Any]] = [
    # EU-Level Programmes
    {
        "name": "Horizon Europe - EIC Accelerator",
        "year": 2025,
        "level": "eu",
        "country": "EU",
        "category": "innovation",
        "funding_rate": "70%",
        "max_amount": "2,5 Mio. €",
        "max_amount_numeric": 2500000,
        "provider": "EU Commission",
        "fit_solo": 0.3,
        "fit_team": 0.6,
        "fit_kmu": 0.9,
        "ki_relevance": "high",
        "deadline": "Q2 2025",
        "years_available": [2025, 2026, 2027],
        "requirements": ["SME status", "Innovative breakthrough technology", "Scale-up potential"],
        "risks": ["High competition", "Long evaluation process"],
    },
    {
        "name": "Digital Europe Programme (DIGITAL)",
        "year": 2025,
        "level": "eu",
        "country": "EU",
        "category": "digitalisierung",
        "funding_rate": "50-75%",
        "max_amount": "500.000 €",
        "max_amount_numeric": 500000,
        "provider": "EU Commission",
        "fit_solo": 0.4,
        "fit_team": 0.7,
        "fit_kmu": 0.8,
        "ki_relevance": "high",
        "deadline": "Rolling 2025",
        "years_available": [2025, 2026],
        "requirements": ["EU company", "Digital transformation focus"],
        "risks": ["Complex application"],
    },
    {
        "name": "Connecting Europe Facility (CEF) Digital",
        "year": 2025,
        "level": "eu",
        "country": "EU",
        "category": "digitalisierung",
        "funding_rate": "75%",
        "max_amount": "1 Mio. €",
        "max_amount_numeric": 1000000,
        "provider": "EU Commission",
        "fit_solo": 0.2,
        "fit_team": 0.5,
        "fit_kmu": 0.7,
        "ki_relevance": "medium",
        "deadline": "Q3 2025",
        "years_available": [2025, 2026, 2027],
        "requirements": ["Digital infrastructure project", "Cross-border element"],
        "risks": ["Long approval process"],
    },

    # Federal-Level Programmes (Germany)
    {
        "name": "go-digital",
        "year": 2025,
        "level": "federal",
        "country": "DE",
        "category": "digitalisierung",
        "funding_rate": "50%",
        "max_amount": "16.500 €",
        "max_amount_numeric": 16500,
        "provider": "BMWK",
        # KIS-1286 (Freshness-Check 2026-08): Programm zum 31.12.2024
        # ausgelaufen — fit-Werte auf 0, damit es nie mehr empfohlen wird
        # (Eintrag bleibt als Historie; b25_enforcer blacklistet den Namen
        # textseitig bereits).
        "fit_solo": 0.0,
        "fit_team": 0.0,
        "fit_kmu": 0.0,
        "ki_relevance": "high",
        "deadline": "Eingestellt (31.12.2024)",
        "deadline_urgency": "expired",
        "years_available": [2025],
        "requirements": ["< 100 Mitarbeiter", "< 20 Mio. € Jahresumsatz"],
        "risks": ["Programm eingestellt"],
        "notes": "EINGESTELLT: Richtlinie zum 31.12.2024 ausgelaufen, keine Anträge mehr möglich. Nachfolge-Angebote: kostenfreie Mittelstand-Digital Zentren, KfW ERP-Förderkredit Digitalisierung, Digitalbonus-Programme der Länder.",
        "last_verified": "2026-08-05",
    },
    {
        "name": "ZIM - Zentrales Innovationsprogramm Mittelstand",
        "year": 2025,
        "level": "federal",
        "country": "DE",
        "category": "innovation",
        "funding_rate": "25-60%",
        "max_amount": "550.000 €",
        "max_amount_numeric": 550000,
        "provider": "BMWE",
        # KIS-1286 (Freshness-Check 2026-08): befristeter Antragsstopp seit
        # 07.07.2026 (Haushaltsmittel erschöpft), Wiederaufnahme angestrebt
        # Anfang 2027 — fit-Werte reduziert, damit ZIM nicht als sofort
        # verfügbare Empfehlung erscheint.
        "fit_solo": 0.1,
        "fit_team": 0.3,
        "fit_kmu": 0.5,
        "ki_relevance": "high",
        "deadline": "Antragsstopp seit 07.07.2026 — Wiederaufnahme voraussichtlich Anfang 2027",
        "deadline_urgency": "paused",
        "years_available": [2025, 2026, 2027],
        "requirements": ["KMU-Status", "Innovatives F&E-Projekt"],
        "risks": ["Befristeter Antragsstopp (Bundesmittel 2026 erschöpft)", "Komplexe Antragsstellung"],
        "notes": "⚠️ Befristeter Antragsstopp seit 07.07.2026 für alle Projektformen; Wiederaufnahme abhängig vom Bundeshaushalt 2027.",
        "last_verified": "2026-08-05",
    },
    {
        "name": "EXIST-Gründerstipendium",
        "year": 2025,
        "level": "federal",
        "country": "DE",
        "category": "gruendung",
        "funding_rate": "100%",
        "max_amount": "150.000 €",
        "max_amount_numeric": 150000,
        "provider": "BMWK",
        "fit_solo": 0.9,
        "fit_team": 0.8,
        "fit_kmu": 0.2,
        "ki_relevance": "high",
        "deadline": "Fortlaufend",
        "years_available": [2025, 2026, 2027],
        "requirements": ["Technologiebasierte Gründung", "Hochschulanbindung"],
        "risks": ["Strenge Kriterien"],
    },
    {
        "name": "KfW-Digitalisierungskredit",
        "year": 2025,
        "level": "federal",
        "country": "DE",
        "category": "digitalisierung",
        "funding_rate": "Kredit (1-3%)",
        "max_amount": "25 Mio. €",
        "max_amount_numeric": 25000000,
        "provider": "KfW",
        "fit_solo": 0.6,
        "fit_team": 0.8,
        "fit_kmu": 0.9,
        "ki_relevance": "medium",
        "deadline": "Fortlaufend",
        "deadline_urgency": "flexible",
        "years_available": [2025, 2026, 2027],
        "requirements": ["Digitalisierungsinvestition"],
        "risks": ["Rückzahlungspflicht"],
    },
    {
        "name": "AI Act Compliance Support",
        "year": 2025,
        "level": "federal",
        "country": "DE",
        "category": "ki",
        "funding_rate": "50%",
        "max_amount": "30.000 €",
        "max_amount_numeric": 30000,
        "provider": "BMWK",
        "fit_solo": 0.7,
        "fit_team": 0.85,
        "fit_kmu": 0.9,
        "ki_relevance": "high",
        "ai_act_relevant": True,
        "deadline": "2025-2027",
        "years_available": [2025, 2026, 2027],
        "requirements": ["KI-Einsatz geplant oder aktiv", "AI Act Relevanz"],
        "risks": ["Noch nicht final bestätigt"],
    },

    # State-Level Programmes
    {
        "name": "Bayerisches KI-Förderprogramm",
        "year": 2025,
        "level": "state",
        "country": "DE",
        "category": "ki",
        "funding_rate": "50%",
        "max_amount": "200.000 €",
        "max_amount_numeric": 200000,
        "provider": "StMWi Bayern",
        "fit_solo": 0.6,
        "fit_team": 0.85,
        "fit_kmu": 0.9,
        "ki_relevance": "high",
        "deadline": "Q4 2025",
        "years_available": [2025, 2026],
        "requirements": ["Firmensitz Bayern", "KI-Projekt"],
        "risks": ["Regionale Beschränkung"],
        "notes": "Region: BY",
    },
    {
        "name": "Invest BW - Innovationsförderung",
        "year": 2025,
        "level": "state",
        "country": "DE",
        "category": "innovation",
        "funding_rate": "20-40%",
        "max_amount": "100.000 €",
        "max_amount_numeric": 100000,
        "provider": "L-Bank BW",
        "fit_solo": 0.5,
        "fit_team": 0.8,
        "fit_kmu": 0.85,
        "ki_relevance": "medium",
        "deadline": "Fortlaufend",
        "years_available": [2025, 2026],
        "requirements": ["Firmensitz Baden-Württemberg"],
        "risks": ["Regionale Beschränkung"],
        "notes": "Region: BW",
    },
    {
        "name": "NRW Digitalförderung",
        "year": 2025,
        "level": "state",
        "country": "DE",
        "category": "digitalisierung",
        "funding_rate": "30-50%",
        "max_amount": "75.000 €",
        "max_amount_numeric": 75000,
        "provider": "MWIDE NRW",
        "fit_solo": 0.8,
        "fit_team": 0.85,
        "fit_kmu": 0.8,
        "ki_relevance": "high",
        "deadline": "2025",
        "years_available": [2025],
        "requirements": ["Firmensitz NRW"],
        "risks": ["Budget oft schnell erschöpft"],
        "notes": "Region: NW",
    },
    {
        "name": "Digitalbonus Berlin",
        "year": 2025,
        "level": "state",
        "country": "DE",
        "category": "digitalisierung",
        "funding_rate": "50%",
        "max_amount": "17.000 €",
        "max_amount_numeric": 17000,
        "provider": "IBB Berlin",
        "fit_solo": 0.9,
        "fit_team": 0.85,
        "fit_kmu": 0.6,
        "ki_relevance": "medium",
        "deadline": "Fortlaufend",
        "years_available": [2025, 2026],
        "requirements": ["Firmensitz Berlin", "< 250 Mitarbeiter"],
        "risks": ["Begrenzte Mittel"],
        "notes": "Region: BE",
    },
    {
        "name": "Digitalbonus Bayern",
        "year": 2025,
        "level": "state",
        "country": "DE",
        "category": "digitalisierung",
        "funding_rate": "bis 50%",
        "max_amount": "50.000 €",
        "max_amount_numeric": 50000,
        "provider": "StMWi Bayern",
        "fit_solo": 0.9,
        "fit_team": 0.9,
        "fit_kmu": 0.85,
        "ki_relevance": "high",
        "deadline": "Fortlaufend",
        "years_available": [2025, 2026],
        "requirements": ["Firmensitz Bayern", "< 250 Mitarbeiter"],
        "risks": ["Fördermittel begrenzt — schnell beantragen"],
        "notes": "Region: BY",
    },
    {
        "name": "Hessen Digital",
        "year": 2025,
        "level": "state",
        "country": "DE",
        "category": "digitalisierung",
        "funding_rate": "40%",
        "max_amount": "50.000 €",
        "max_amount_numeric": 50000,
        "provider": "WIBank Hessen",
        "fit_solo": 0.7,
        "fit_team": 0.8,
        "fit_kmu": 0.75,
        "ki_relevance": "medium",
        "deadline": "2025",
        "years_available": [2025],
        "requirements": ["Firmensitz Hessen"],
        "risks": ["Budgetabhängig"],
        "notes": "Region: HE",
    },

    # 2026 Forward-Looking Programmes
    {
        "name": "AI Made in Germany 2026",
        "year": 2026,
        "level": "federal",
        "country": "DE",
        "category": "ki",
        "funding_rate": "60%",
        "max_amount": "500.000 €",
        "max_amount_numeric": 500000,
        "provider": "BMBF",
        "fit_solo": 0.4,
        "fit_team": 0.75,
        "fit_kmu": 0.9,
        "ki_relevance": "high",
        "deadline": "Q1 2026",
        "deadline_urgency": "normal",
        "years_available": [2026, 2027],
        "requirements": ["Innovative KI-Anwendung", "Made in Germany Fokus"],
        "risks": ["Noch nicht final verabschiedet"],
        "notes": "Geplantes Programm - Details können sich ändern",
    },
    {
        "name": "EU AI Excellence Hub",
        "year": 2026,
        "level": "eu",
        "country": "EU",
        "category": "ki",
        "funding_rate": "75%",
        "max_amount": "1 Mio. €",
        "max_amount_numeric": 1000000,
        "provider": "EU Commission",
        "fit_solo": 0.3,
        "fit_team": 0.6,
        "fit_kmu": 0.85,
        "ki_relevance": "high",
        "deadline": "Q2 2026",
        "years_available": [2026, 2027],
        "requirements": ["EU-Konsortium", "KI-Exzellenz nachweisen"],
        "risks": ["Komplexe Konsortialbildung"],
    },
    {
        "name": "Green AI Initiative 2026",
        "year": 2026,
        "level": "eu",
        "country": "EU",
        "category": "nachhaltigkeit",
        "funding_rate": "70%",
        "max_amount": "750.000 €",
        "max_amount_numeric": 750000,
        "provider": "EU Commission",
        "fit_solo": 0.3,
        "fit_team": 0.65,
        "fit_kmu": 0.8,
        "ki_relevance": "high",
        "deadline": "Q3 2026",
        "years_available": [2026, 2027],
        "requirements": ["Nachhaltige KI-Anwendung", "CO2-Reduktion Nachweis"],
        "risks": ["Strenge Nachhaltigkeitskriterien"],
    },

    # 2027 Future Programmes
    {
        "name": "Industrie 5.0 Förderung",
        "year": 2027,
        "level": "federal",
        "country": "DE",
        "category": "innovation",
        "funding_rate": "50%",
        "max_amount": "400.000 €",
        "max_amount_numeric": 400000,
        "provider": "BMWK",
        "fit_solo": 0.3,
        "fit_team": 0.6,
        "fit_kmu": 0.85,
        "ki_relevance": "high",
        "deadline": "2027",
        "years_available": [2027],
        "requirements": ["Industrie 5.0 Konzept", "Mensch-Maschine-Kollaboration"],
        "risks": ["Programm noch in Planung"],
    },
    {
        "name": "Horizon Europe AI Mission 2027",
        "year": 2027,
        "level": "eu",
        "country": "EU",
        "category": "ki",
        "funding_rate": "70%",
        "max_amount": "3 Mio. €",
        "max_amount_numeric": 3000000,
        "provider": "EU Commission",
        "fit_solo": 0.2,
        "fit_team": 0.5,
        "fit_kmu": 0.9,
        "ki_relevance": "high",
        "deadline": "Q1 2027",
        "years_available": [2027],
        "requirements": ["Breakthrough AI research", "EU consortium"],
        "risks": ["Very competitive"],
    },

    # Phase 1 Medien-Vertikale: Film-/Medien-/Games-Förderung
    {
        "name": "DFFF - Deutscher Filmförderfonds",
        "year": 2025,
        "level": "federal",
        "country": "DE",
        "category": "medien",
        "funding_rate": "30%",
        "max_amount": "DFFF I bis 5 Mio. €, DFFF II bis 25 Mio. €",
        "max_amount_numeric": 5000000,
        "provider": "BKM / FFA",
        "fit_solo": 0.2,
        "fit_team": 0.8,
        "fit_kmu": 0.9,
        "ki_relevance": "medium",
        "deadline": "laufend",
        "years_available": [2025, 2026, 2027],
        "requirements": ["Kinofilmproduktion", "Deutsche Herstellungskosten", "Kulturtest"],
        "risks": ["Abrechnung/Nachweis aufwendig"],
    },
    {
        "name": "German Motion Picture Fund (GMPF)",
        "year": 2025,
        "level": "federal",
        "country": "DE",
        "category": "medien",
        "funding_rate": "30%",
        "max_amount": "Serien bis 20 Mio. €/Staffel",
        "max_amount_numeric": 20000000,
        "provider": "BKM / FFA",
        "fit_solo": 0.1,
        "fit_team": 0.7,
        "fit_kmu": 0.9,
        "ki_relevance": "medium",
        "deadline": "laufend",
        "years_available": [2025, 2026, 2027],
        "requirements": ["High-End-Serie oder Film", "VFX-/Postproduktionsanteil in DE"],
        "risks": ["Mindestbudgets beachten"],
    },
    {
        "name": "Medienboard Berlin-Brandenburg - New Media",
        "year": 2025,
        "level": "state",
        "country": "DE",
        "category": "medien",
        "funding_rate": "projektabhängig",
        "max_amount": "projektabhängig",
        "max_amount_numeric": 1500000,
        "provider": "Medienboard Berlin-Brandenburg",
        "fit_solo": 0.6,
        "fit_team": 0.9,
        "fit_kmu": 0.8,
        "ki_relevance": "high",
        "deadline": "mehrere Einreichtermine/Jahr",
        "years_available": [2025, 2026, 2027],
        "requirements": ["Regionaleffekt Berlin/Brandenburg", "Innovatives audiovisuelles Format"],
        "risks": ["Regionalbindung der Ausgaben"],
    },
    {
        "name": "Games-Förderung des Bundes",
        "year": 2025,
        "level": "federal",
        "country": "DE",
        "category": "medien",
        "funding_rate": "bis 45% (KMU) / 50% (Start-ups)",
        "max_amount": "bis 8 Mio. € (min. 300.000 €)",
        "max_amount_numeric": 8000000,
        "provider": "BMFTR (DLR Projektträger)",
        "fit_solo": 0.3,
        "fit_team": 0.8,
        "fit_kmu": 0.9,
        "ki_relevance": "medium",
        "deadline": "abhängig von Förderrunden",
        "years_available": [2025, 2026, 2027],
        "requirements": ["Games-Entwicklung in DE", "Kulturtest", "USK-Kennzeichnung"],
        "risks": ["Budget 2026: 125 Mio. € — Mitte 2026 gute Antragschancen"],
    },
    {
        "name": "Creative Europe MEDIA",
        "year": 2025,
        "level": "eu",
        "country": "EU",
        "category": "medien",
        "funding_rate": "Ko-Finanzierung",
        "max_amount": "projektabhängig",
        "max_amount_numeric": 1000000,
        "provider": "EU Commission",
        "fit_solo": 0.3,
        "fit_team": 0.7,
        "fit_kmu": 0.8,
        "ki_relevance": "medium",
        "deadline": "Calls laufend",
        "years_available": [2025, 2026, 2027],
        "requirements": ["Audiovisueller Sektor", "EU-Dimension"],
        "risks": ["Antragsaufwand, Wettbewerb"],
    },
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _parse_amount(amount_str: str) -> float:
    """Parse amount string to numeric value."""
    if not amount_str:
        return 0.0

    amount_lower = amount_str.lower().replace(" ", "").replace(".", "").replace(",", ".")

    # Handle "Mio" (millions)
    if "mio" in amount_lower:
        match = re.search(r'([\d.,]+)', amount_lower)
        if match:
            try:
                return float(match.group(1).replace(",", ".")) * 1_000_000
            except ValueError:
                pass

    # Handle regular amounts
    match = re.search(r'([\d.,]+)', amount_lower)
    if match:
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            pass

    return 0.0


def _calculate_year_factor(programme_year: int, target_year: int = 2025) -> float:
    """
    Calculate year-based weighting factor.

    Programmes closer to target_year get higher weight.
    2025 = 1.0, 2026 = 0.85, 2027 = 0.7
    """
    year_diff = abs(programme_year - target_year)

    if year_diff == 0:
        return 1.0
    elif year_diff == 1:
        return 0.85
    elif year_diff == 2:
        return 0.7
    else:
        return 0.5


def _calculate_branch_relevance(category: str, branch: str) -> float:
    """Calculate relevance between funding category and business branch."""
    if not branch:
        return 0.5

    branch_lower = branch.lower()

    # Branch-category alignment matrix
    alignments: Dict[str, Dict[str, float]] = {
        "digitalisierung": {
            "it": 0.95, "software": 0.95, "tech": 0.9,
            "beratung": 0.85, "handel": 0.8, "marketing": 0.8,
            "finanzen": 0.75, "industrie": 0.7, "gesundheit": 0.7,
            "medien": 0.75, "kreativ": 0.75,
        },
        "ki": {
            "it": 0.95, "software": 0.95, "tech": 0.95,
            "beratung": 0.8, "finanzen": 0.85, "gesundheit": 0.85,
            "industrie": 0.8, "handel": 0.75,
            "medien": 0.8, "kreativ": 0.8,
        },
        "innovation": {
            "it": 0.9, "tech": 0.9, "industrie": 0.85,
            "gesundheit": 0.8, "beratung": 0.7,
            "medien": 0.75,
        },
        # Phase 1 Medien-Vertikale: Film-/Medien-/Games-Förderung
        "medien": {
            "medien": 0.95, "kreativ": 0.95, "film": 0.95,
            "marketing": 0.6, "it": 0.4,
        },
        "forschung": {
            "it": 0.85, "tech": 0.9, "gesundheit": 0.9,
            "industrie": 0.8,
        },
        "nachhaltigkeit": {
            "industrie": 0.9, "energie": 0.95, "bau": 0.85,
            "handel": 0.7, "logistik": 0.8,
        },
        "gruendung": {
            "it": 0.9, "tech": 0.95, "beratung": 0.8,
        },
    }

    category_alignments = alignments.get(category, {})

    for key, score in category_alignments.items():
        if key in branch_lower:
            return score

    return 0.5  # Default moderate relevance


def _calculate_size_match_score(programme: Dict[str, Any], size: str) -> float:
    """Calculate size match score."""
    size_lower = size.lower() if size else "team"

    if "solo" in size_lower or size_lower == "1":
        return float(programme.get("fit_solo", 0.5))
    elif "kmu" in size_lower or "sme" in size_lower or "mittel" in size_lower:
        return float(programme.get("fit_kmu", 0.5))
    else:
        return float(programme.get("fit_team", 0.5))


def _check_region_match(programme: Dict[str, Any], region: str) -> bool:
    """Check if programme is available in region."""
    notes = programme.get("notes", "").lower()
    country = programme.get("country", "DE")

    # EU programmes available everywhere
    if country == "EU":
        return True

    # Federal programmes available in all of Germany
    if programme.get("level") == "federal" and country == "DE":
        return True

    # State programmes need region match
    if programme.get("level") == "state" and notes:
        region_upper = region.upper() if region else ""
        if f"region: {region_upper.lower()}" in notes:
            return True
        # No specific region in notes = available for all
        if "region:" not in notes:
            return True
        return False

    return True


# =============================================================================
# CORE EVALUATION FUNCTIONS
# =============================================================================

def evaluate_funding_v2(
    branch: str = "",
    size: str = "team",
    region: str = "DE",
    country: str = "DE",
    maturity: int = 2,
    ai_goals: Optional[List[str]] = None,
    target_year: int = 2025,
    include_future: bool = True,
    ai_act_risk: str = "minimal",
    max_budget: Optional[float] = None,
    lang: str = "de",
) -> FundingEvaluationResult:
    """
    Evaluate funding programmes for a company profile.

    G26: Multi-year funding evaluation with comprehensive scoring.

    Args:
        branch: Industry/branch (e.g., "beratung", "it", "handel")
        size: Company size (solo, team, kmu)
        region: Region code (e.g., "BY", "NW", "BE")
        country: Country code (e.g., "DE", "AT")
        maturity: Digital maturity level (1-5)
        ai_goals: List of AI goals
        target_year: Primary year focus (2025, 2026, 2027)
        include_future: Include 2026/2027 programmes
        ai_act_risk: AI Act risk level
        max_budget: Maximum budget filter
        lang: Language code

    Returns:
        FundingEvaluationResult with ranked programmes
    """
    log.info(
        "[G26] Evaluating funding: branch=%s, size=%s, region=%s, year=%d",
        branch, size, region, target_year
    )

    programmes: List[FundingProgramme] = []
    year_dist: Dict[int, int] = {2025: 0, 2026: 0, 2027: 0}
    level_dist: Dict[str, int] = {}
    category_dist: Dict[str, int] = {}

    for prog_data in FUNDING_PROGRAMMES_2025_2027:
        prog_year = prog_data.get("year", 2025)

        # Filter by year
        if not include_future and prog_year > target_year:
            continue

        # Filter by region
        if not _check_region_match(prog_data, region):
            continue

        # Filter by max budget
        if max_budget and prog_data.get("max_amount_numeric", 0) > max_budget:
            continue

        # Calculate scores
        year_factor = _calculate_year_factor(prog_year, target_year)
        branch_relevance = _calculate_branch_relevance(
            prog_data.get("category", "allgemein"), branch
        )
        size_fit = _calculate_size_match_score(prog_data, size)

        # Base match score
        base_score = (
            size_fit * 0.35 +
            branch_relevance * 0.30 +
            year_factor * 0.20 +
            (0.15 if prog_data.get("ki_relevance") == "high" else 0.08)
        )

        # AI Act bonus
        if ai_act_risk in ("high-risk", "limited") and prog_data.get("ai_act_relevant"):
            base_score *= 1.15

        # Maturity adjustment
        if maturity >= 3 and prog_data.get("level") in ("eu", "federal"):
            base_score *= 1.1
        elif maturity <= 2 and prog_data.get("level") == "state":
            base_score *= 1.1

        match_score = min(1.0, base_score)

        # Create FundingProgramme
        programme = FundingProgramme(
            name=prog_data.get("name", ""),
            year=prog_year,
            level=prog_data.get("level", "federal"),
            country=prog_data.get("country", "DE"),
            category=prog_data.get("category", "allgemein"),
            funding_rate=prog_data.get("funding_rate", ""),
            max_amount=prog_data.get("max_amount", ""),
            max_amount_numeric=prog_data.get("max_amount_numeric", 0),
            match_score=match_score,
            branch_relevance=branch_relevance,
            year_factor=year_factor,
            fit_solo=prog_data.get("fit_solo", 0.5),
            fit_team=prog_data.get("fit_team", 0.5),
            fit_kmu=prog_data.get("fit_kmu", 0.5),
            requirements=prog_data.get("requirements", []),
            risks=prog_data.get("risks", []),
            deadline=prog_data.get("deadline"),
            deadline_urgency=prog_data.get("deadline_urgency", "normal"),
            notes=prog_data.get("notes", ""),
            provider=prog_data.get("provider", ""),
            url=prog_data.get("url"),
            years_available=prog_data.get("years_available", [prog_year]),
            ai_act_relevant=prog_data.get("ai_act_relevant", False),
            ki_relevance=prog_data.get("ki_relevance", "medium"),
        )

        programmes.append(programme)

        # Update distributions
        year_dist[prog_year] = year_dist.get(prog_year, 0) + 1
        level_dist[programme.level] = level_dist.get(programme.level, 0) + 1
        category_dist[programme.category] = category_dist.get(programme.category, 0) + 1

    # Sort by match_score
    programmes.sort(key=lambda p: p.match_score, reverse=True)

    log.info("[G26] Evaluated %d programmes, top match: %.2f",
             len(programmes), programmes[0].match_score if programmes else 0)

    return FundingEvaluationResult(
        programmes=programmes,
        total_evaluated=len(FUNDING_PROGRAMMES_2025_2027),
        filtered_count=len(programmes),
        year_distribution=year_dist,
        level_distribution=level_dist,
        category_distribution=category_dist,
        evaluation_context={
            "branch": branch,
            "size": size,
            "region": region,
            "target_year": target_year,
        }
    )


def rank_funding(
    programmes: List[FundingProgramme],
    context: Optional[Dict[str, Any]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> List[FundingProgramme]:
    """
    Re-rank funding programmes with custom weights.

    G26: Advanced ranking with configurable weighting factors.

    Args:
        programmes: List of programmes to rank
        context: Optional context for ranking adjustments
        weights: Custom weights for scoring factors

    Returns:
        Re-ranked list of programmes
    """
    if not programmes:
        return []

    # Default weights
    default_weights = {
        "match_score": 0.40,
        "year_factor": 0.25,
        "size_fit": 0.20,
        "max_amount": 0.15,
    }

    w = weights or default_weights
    context = context or {}

    size = context.get("size", "team")

    for prog in programmes:
        # Get size-specific fit
        size_fit = prog.get_size_fit(size)

        # Normalize max_amount (log scale)
        amount_score = min(1.0, prog.max_amount_numeric / 1_000_000) if prog.max_amount_numeric > 0 else 0.3

        # Calculate weighted score
        weighted_score = (
            prog.match_score * w.get("match_score", 0.4) +
            prog.year_factor * w.get("year_factor", 0.25) +
            size_fit * w.get("size_fit", 0.2) +
            amount_score * w.get("max_amount", 0.15)
        )

        # Deadline urgency boost
        if prog.deadline_urgency == "urgent":
            weighted_score *= 1.1

        prog.match_score = min(1.0, weighted_score)

    # Re-sort
    programmes.sort(key=lambda p: p.match_score, reverse=True)

    return programmes


def get_funding_by_year(
    programmes: List[FundingProgramme],
    year: int,
) -> List[FundingProgramme]:
    """Filter programmes by specific year."""
    return [p for p in programmes if p.year == year or year in p.years_available]


def get_funding_by_level(
    programmes: List[FundingProgramme],
    level: FundingLevel,
) -> List[FundingProgramme]:
    """Filter programmes by funding level."""
    return [p for p in programmes if p.level == level]


def get_funding_by_category(
    programmes: List[FundingProgramme],
    category: FundingCategory,
) -> List[FundingProgramme]:
    """Filter programmes by category."""
    return [p for p in programmes if p.category == category]


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_funding_matrix_html(
    result: FundingEvaluationResult,
    lang: str = "de",
    max_programmes: int = 8,
) -> str:
    """
    Generate FUNDING_MATRIX_2025_HTML section.

    G26: Multi-year funding matrix with year badges.

    Args:
        result: Evaluation result with programmes
        lang: Language code
        max_programmes: Maximum programmes to display

    Returns:
        HTML string for PDF template
    """
    if not result.has_programmes:
        if lang == "en":
            return '<p class="muted small">No funding programmes match your profile.</p>'
        return '<p class="muted small">Keine passenden Förderprogramme für Ihr Profil.</p>'

    programmes = result.programmes[:max_programmes]

    # Labels
    if lang == "en":
        title = "Funding Matrix 2025-2027"
        headers = ["Programme", "Year", "Level", "Funding", "Max. Amount", "Match"]
        level_labels = {
            "eu": "EU", "federal": "Federal", "state": "State", "regional": "Regional"
        }
        year_note = "Year badges indicate primary availability. Some programmes span multiple years."
    else:
        title = "Fördermatrix 2025-2027"
        headers = ["Programm", "Jahr", "Ebene", "Quote", "Max. Betrag", "Match"]
        level_labels = {
            "eu": "EU", "federal": "Bund", "state": "Land", "regional": "Regional"
        }
        year_note = "Jahr-Badges zeigen primäre Verfügbarkeit. Einige Programme laufen mehrjährig."

    html_parts = [f'''
    <div class="funding-matrix-v2" style="margin-top:20px;">
        <h3 style="margin:0 0 12px 0;font-size:15px;color:#1e40af;display:flex;align-items:center;gap:10px;">
            <span style="font-size:18px;">💰</span> {title}
            <span style="font-size:9px;padding:2px 8px;background:#3b82f6;color:#fff;border-radius:4px;">G26</span>
        </h3>

        <table class="funding-table table-modern" style="width:100%;border-collapse:collapse;font-size:11px;">
            <thead>
                <tr style="background:#f1f5f9;">
                    <th style="padding:8px;text-align:left;font-weight:600;">{headers[0]}</th>
                    <th style="padding:8px;text-align:center;font-weight:600;">{headers[1]}</th>
                    <th style="padding:8px;text-align:center;font-weight:600;">{headers[2]}</th>
                    <th style="padding:8px;text-align:center;font-weight:600;">{headers[3]}</th>
                    <th style="padding:8px;text-align:center;font-weight:600;">{headers[4]}</th>
                    <th style="padding:8px;text-align:center;font-weight:600;">{headers[5]}</th>
                </tr>
            </thead>
            <tbody>
    ''']

    for prog in programmes:
        match_pct = int(prog.match_score * 100)
        match_color = "#22c55e" if match_pct >= 70 else "#f59e0b" if match_pct >= 50 else "#6b7280"

        # Year badge color
        year_colors = {2025: "#3b82f6", 2026: "#8b5cf6", 2027: "#ec4899"}
        year_color = year_colors.get(prog.year, "#6b7280")

        # Level badge
        level_label = level_labels.get(prog.level, prog.level)
        level_colors = {
            "eu": "#0ea5e9", "federal": "#22c55e", "state": "#f59e0b", "regional": "#6b7280"
        }
        level_color = level_colors.get(prog.level, "#6b7280")

        # KI relevance indicator
        ki_indicator = ""
        if prog.ki_relevance == "high":
            ki_indicator = '<span style="font-size:10px;margin-left:4px;">🤖</span>'

        html_parts.append(f'''
            <tr style="border-bottom:1px solid #e2e8f0;">
                <td style="padding:10px;">
                    <div style="font-weight:600;color:#1e293b;">{prog.name}{ki_indicator}</div>
                    <div style="font-size:10px;color:#64748b;margin-top:2px;">{prog.provider}</div>
                </td>
                <td style="padding:10px;text-align:center;">
                    <span class="year-badge year-{prog.year}" style="padding:2px 8px;background:{year_color};color:#fff;border-radius:4px;font-weight:600;font-size:10px;">{prog.year}</span>
                </td>
                <td style="padding:10px;text-align:center;">
                    <span class="level-badge level-{prog.level}" style="padding:2px 6px;background:{level_color}20;color:{level_color};border-radius:3px;font-size:10px;">{level_label}</span>
                </td>
                <td style="padding:10px;text-align:center;font-weight:500;">{prog.funding_rate}</td>
                <td style="padding:10px;text-align:center;">{prog.max_amount}</td>
                <td style="padding:10px;text-align:center;">
                    <span style="font-weight:700;color:{match_color};">{match_pct}%</span>
                </td>
            </tr>
        ''')

    html_parts.append(f'''
            </tbody>
        </table>
        <p style="margin:10px 0 0 0;font-size:9px;color:#94a3b8;font-style:italic;">{year_note}</p>
    </div>
    ''')

    return '\n'.join(html_parts)


def generate_funding_timeline_html(
    result: FundingEvaluationResult,
    lang: str = "de",
) -> str:
    """
    Generate FUNDING_TIMELINE_HTML section.

    G26: Visual timeline of funding opportunities across years.
    """
    if not result.has_programmes:
        return ""

    # Group by year
    by_year: Dict[int, List[FundingProgramme]] = {2025: [], 2026: [], 2027: []}
    for prog in result.programmes:
        if prog.year in by_year:
            by_year[prog.year].append(prog)

    if lang == "en":
        title = "Funding Timeline 2025-2027"
        now_label = "Current"
        future_label = "Upcoming"
    else:
        title = "Förder-Timeline 2025-2027"
        now_label = "Aktuell"
        future_label = "Kommend"

    html_parts = [f'''
    <div class="funding-timeline" style="margin-top:16px;padding:16px;background:#f8fafc;border-radius:8px;">
        <h4 style="margin:0 0 12px 0;font-size:13px;color:#475569;">{title}</h4>
        <div style="display:flex;gap:16px;">
    ''']

    year_colors = {2025: "#3b82f6", 2026: "#8b5cf6", 2027: "#ec4899"}

    for year in [2025, 2026, 2027]:
        progs = by_year.get(year, [])[:3]
        count = len(by_year.get(year, []))
        color = year_colors.get(year, "#6b7280")
        label = now_label if year == 2025 else future_label

        html_parts.append(f'''
            <div style="flex:1;padding:12px;background:#fff;border-radius:6px;border-top:3px solid {color};">
                <div style="font-size:16px;font-weight:700;color:{color};">{year}</div>
                <div style="font-size:10px;color:#94a3b8;margin-bottom:8px;">{label} • {count} Programme</div>
        ''')

        for prog in progs:
            html_parts.append(f'''
                <div style="font-size:10px;color:#475569;padding:4px 0;border-bottom:1px solid #f1f5f9;">
                    {prog.name}
                </div>
            ''')

        html_parts.append('</div>')

    html_parts.append('</div></div>')

    return '\n'.join(html_parts)


def inject_funding_v2_into_sections(
    sections: Dict[str, Any],
    briefing: Dict[str, Any],
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Inject G26 funding sections into report sections.

    Args:
        sections: Report sections dictionary
        briefing: Briefing dictionary
        lang: Language code

    Returns:
        Updated sections with FUNDING_MATRIX_2025_HTML and FUNDING_TIMELINE_HTML
    """
    try:
        # Extract context from briefing
        branch = briefing.get("branche") or briefing.get("BRANCH_LABEL") or ""
        size = briefing.get("unternehmensgroesse") or briefing.get("SIZE_LABEL") or "team"
        region = briefing.get("bundesland") or "DE"
        maturity = sections.get("MATURITY_LEVEL", 2)
        ai_act_risk = sections.get("AI_ACT_RISK_LEVEL", "minimal")

        # Evaluate funding
        result = evaluate_funding_v2(
            branch=branch,
            size=size,
            region=region,
            maturity=int(maturity) if maturity else 2,
            target_year=2025,
            include_future=True,
            ai_act_risk=ai_act_risk,
            lang=lang,
        )

        # Generate HTML
        sections["FUNDING_MATRIX_2025_HTML"] = generate_funding_matrix_html(result, lang)
        sections["FUNDING_TIMELINE_HTML"] = generate_funding_timeline_html(result, lang)

        # Add metadata
        sections["FUNDING_V2_PROGRAMMES_COUNT"] = result.filtered_count
        sections["FUNDING_V2_TOP_MATCH"] = round(result.programmes[0].match_score, 2) if result.programmes else 0

        log.info("✅ [G26] Injected funding matrix: %d programmes, top=%s%%",
                 result.filtered_count,
                 int(result.programmes[0].match_score * 100) if result.programmes else 0)

    except Exception as e:
        log.error("[G26] Failed to inject funding sections: %s", e)
        sections["FUNDING_MATRIX_2025_HTML"] = ""
        sections["FUNDING_TIMELINE_HTML"] = ""

    return sections


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G26] Funding Engine V2 loaded - %d programmes available (2025-2027)",
         len(FUNDING_PROGRAMMES_2025_2027))
