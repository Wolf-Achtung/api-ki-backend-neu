"""
Funding Service EN - English funding recommendations for EN reports.

This module provides English-language funding program recommendations:
- Phase 1: German programmes for users with companies based in Germany (lang="en", country="DE")
- Phase 2: EU core programmes for users in other EU countries (lang="en", country != "DE")

Version: 2.0.0 - Refactored to use unified types and renderer
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import unified types and renderer
from services.funding_types import (
    FundingProgramView,
    FundingRenderContext,
    FundingScope,
)
from services.funding_renderer import render_funding_html

logger = logging.getLogger(__name__)


@dataclass
class FundingResult:
    """Result of funding program matching for EN reports (Germany)."""

    programmes: List[Dict[str, Any]] = field(default_factory=list)
    country: str = "DE"
    language: str = "en"
    error: Optional[str] = None

    @property
    def has_programmes(self) -> bool:
        """Check if any programmes were found."""
        return len(self.programmes) > 0

    @property
    def programme_count(self) -> int:
        """Return number of matched programmes."""
        return len(self.programmes)


@dataclass
class FundingResultEUCore:
    """Result of EU core funding program matching for EN reports (non-German countries)."""

    programmes: List[Dict[str, Any]] = field(default_factory=list)
    country: str = "EU"
    language: str = "en"
    error: Optional[str] = None

    @property
    def has_programmes(self) -> bool:
        """Check if any programmes were found."""
        return len(self.programmes) > 0

    @property
    def programme_count(self) -> int:
        """Return number of matched programmes."""
        return len(self.programmes)


def _load_funding_data() -> Dict[str, Any]:
    """Load funding_de_en.json data file."""
    funding_file = Path(__file__).parent.parent / "data" / "funding" / "funding_de_en.json"

    if not funding_file.exists():
        logger.warning(f"Funding data file not found: {funding_file}")
        return {"programmes": []}

    try:
        with open(funding_file, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing funding data: {e}")
        return {"programmes": []}
    except Exception as e:
        logger.error(f"Error loading funding data: {e}")
        return {"programmes": []}


def _normalize_company_size(answers: Dict[str, Any]) -> str:
    """
    Normalize company size from answers to matching key.

    Returns: 'solo', 'team', or 'kmu'
    """
    size_raw = answers.get("unternehmensgroesse", "")
    if not size_raw:
        size_raw = answers.get("company_size", "")

    size = str(size_raw).lower().strip()

    # Primary: use canonical normalizer for robust range/dash handling
    try:
        from services.company_size_normalizer import get_segment
        segment = get_segment(size)
        if segment in ("solo", "team", "kmu"):
            return segment
    except Exception:
        pass

    # Fallback: exact match for common values
    if size in ("solo", "solo-selbständig", "freelancer", "einzelunternehmer"):
        return "solo"
    elif size in ("team", "klein", "small", "2-10", "kleines team"):
        return "team"
    elif size in ("kmu", "sme", "mittel", "medium", "11-50", "51-250", "mittelstand"):
        return "kmu"

    # Default fallback based on employee count if available
    employees = answers.get("mitarbeiter", answers.get("employees", 0))
    try:
        emp_count = int(employees) if employees else 0
    except (ValueError, TypeError):
        emp_count = 0

    if emp_count <= 1:
        return "solo"
    elif emp_count <= 10:
        return "team"
    else:
        return "kmu"


def _match_programmes(
    programmes: List[Dict[str, Any]],
    company_size: str,
    bundesland: Optional[str] = None,
    budget: Optional[float] = None,
    branch: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter and sort programmes based on company profile.

    Args:
        programmes: List of funding programmes from JSON
        company_size: Normalized company size ('solo', 'team', 'kmu')
        bundesland: Optional German state code (e.g., 'BY', 'BE', 'BW')
        budget: Optional project budget for filtering by max_amount

    Returns:
        Sorted list of matching programmes
    """
    matched: List[Dict[str, Any]] = []

    for prog in programmes:
        # Check if programme is suitable for company size
        suitable_for = prog.get("suitable_for", [])
        if company_size not in suitable_for:
            continue

        # Optional branch filter (Phase 1 media vertical): programmes with a
        # "branchen" list only appear for matching branches; programmes
        # without the field stay visible for everyone (fail-open).
        prog_branchen = prog.get("branchen")
        if prog_branchen and branch and branch.lower() not in [
            str(b).lower() for b in prog_branchen
        ]:
            continue

        # Check region match (DE = nationwide, or specific state)
        prog_region = prog.get("region", "DE")
        if prog_region != "DE" and bundesland:
            if prog_region != bundesland:
                continue

        # Optional: filter by budget if max_amount is set
        if budget is not None and prog.get("max_amount", 0) > 0:
            if budget > prog["max_amount"] * 2:  # Allow some flexibility
                continue

        matched.append(prog)

    # Sort by priority (lower = higher priority) and AI relevance
    def sort_key(p: Dict[str, Any]) -> tuple:
        priority = p.get("priority", 99)
        relevance_order = {"high": 0, "medium": 1, "low": 2}
        relevance = relevance_order.get(p.get("relevance_ki", "low"), 2)
        return (priority, relevance)

    matched.sort(key=sort_key)

    return matched


def get_funding_for_germany_en(answers: Dict[str, Any]) -> FundingResult:
    """
    Get funding recommendations for Germany-based companies (EN language).

    This function:
    1. Loads funding_de_en.json
    2. Matches programmes based on company size, region, budget
    3. Returns FundingResult with EN-language strings

    Args:
        answers: Dictionary containing user answers with keys like:
            - unternehmensgroesse / company_size
            - bundesland / state
            - mitarbeiter / employees
            - budget (optional)

    Returns:
        FundingResult with matched programmes and metadata
    """
    try:
        # Load funding data
        data = _load_funding_data()
        programmes = data.get("programmes", [])

        if not programmes:
            logger.warning("No funding programmes found in data file")
            return FundingResult(
                programmes=[],
                country="DE",
                language="en",
                error="No funding programmes available",
            )

        # Extract matching criteria from answers
        company_size = _normalize_company_size(answers)
        bundesland = answers.get("bundesland", answers.get("state", ""))
        if bundesland:
            # Phase 5B: Normalize to lowercase 2-letter code (questionnaire sends lowercase)
            bundesland = str(bundesland).lower()[:2]

        budget_raw = answers.get("budget", answers.get("investitionsvolumen", 0))
        try:
            budget = float(budget_raw) if budget_raw else None
        except (ValueError, TypeError):
            budget = None

        # Match programmes
        matched = _match_programmes(
            programmes=programmes,
            company_size=company_size,
            bundesland=bundesland if bundesland else None,
            budget=budget,
            branch=str(answers.get("branche", "") or "").strip() or None,
        )

        logger.info(
            f"Funding match: size={company_size}, region={bundesland or 'DE'}, "
            f"found={len(matched)} programmes"
        )

        return FundingResult(
            programmes=matched,
            country="DE",
            language="en",
            error=None,
        )

    except Exception as e:
        logger.error(f"Error in get_funding_for_germany_en: {e}")
        return FundingResult(
            programmes=[],
            country="DE",
            language="en",
            error=str(e),
        )


def render_funding_html_en(result: FundingResult, limit: int = 5) -> str:
    """
    Render funding programmes as HTML for EN reports.

    Uses the unified funding renderer for consistent output.

    Args:
        result: FundingResult from get_funding_for_germany_en()
        limit: Maximum number of programmes to render

    Returns:
        HTML string for embedding in report
    """
    if not result.has_programmes:
        return ""

    # Convert programme dicts to FundingProgramView objects
    programmes = result.programmes[:limit]
    views: List[FundingProgramView] = [
        FundingProgramView(
            id=prog.get("id", "unknown"),
            name=prog.get("name_en", prog.get("name_de", "Unknown Programme")),
            summary=prog.get("summary_en", prog.get("focus_en", "")),
            funding_type=prog.get("funding_type_en", "Grant"),
            funding_rate=prog.get("funding_rate_en", ""),
            max_amount=prog.get("max_amount_en", ""),
            scope_label=prog.get("region_en", "Germany"),
            region=prog.get("region_en"),
            url=prog.get("url", ""),
        )
        for prog in programmes
    ]

    # Create render context and use unified renderer
    context = FundingRenderContext(
        scope="DE_EN",
        programmes=views,
        lang="en",
        country="DE",
        show_disclaimer=False,
    )

    return render_funding_html(context)


# =============================================================================
# Phase 2: EU Core Funding (for non-German EN reports)
# =============================================================================


def _load_eu_core_funding_data() -> Dict[str, Any]:
    """Load funding_eu_core_en.json data file."""
    funding_file = Path(__file__).parent.parent / "data" / "funding" / "funding_eu_core_en.json"

    if not funding_file.exists():
        logger.warning(f"EU core funding data file not found: {funding_file}")
        return {"programmes": []}

    try:
        with open(funding_file, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing EU core funding data: {e}")
        return {"programmes": []}
    except Exception as e:
        logger.error(f"Error loading EU core funding data: {e}")
        return {"programmes": []}


def _normalize_target_group(answers: Dict[str, Any]) -> str:
    """
    Normalize company profile to EU target group category.

    Returns: 'startup', 'sme', 'large', 'research', or 'public'
    """
    company_size = _normalize_company_size(answers)

    # Check for research/academic indicators
    branche = str(answers.get("branche", answers.get("industry", ""))).lower()
    if any(kw in branche for kw in ("research", "university", "forschung", "hochschule", "academic")):
        return "research"

    # Check for public sector
    if any(kw in branche for kw in ("public", "government", "öffentlich", "behörde", "verwaltung")):
        return "public"

    # Map company size to EU target groups
    if company_size == "solo":
        return "startup"
    elif company_size == "team":
        return "sme"  # Small teams typically qualify as SME
    else:
        # Check employee count for large enterprise threshold
        employees = answers.get("mitarbeiter", answers.get("employees", 0))
        try:
            emp_count = int(employees) if employees else 0
        except (ValueError, TypeError):
            emp_count = 0

        if emp_count > 250:
            return "large"
        return "sme"


def _match_eu_core_programmes(
    programmes: List[Dict[str, Any]],
    target_group: str,
    ai_focus: bool = True,
) -> List[Dict[str, Any]]:
    """
    Filter and sort EU core programmes based on profile.

    Args:
        programmes: List of EU funding programmes from JSON
        target_group: Normalized target group ('startup', 'sme', 'large', 'research', 'public')
        ai_focus: Whether to prioritize AI-relevant programmes

    Returns:
        Sorted list of matching programmes
    """
    matched: List[Dict[str, Any]] = []

    # Map our target groups to JSON target_groups_en values
    target_map = {
        "startup": ["Startups", "Deep-tech startups", "Scale-ups", "High-growth SMEs", "SMEs", "Innovative SMEs"],
        "sme": ["SMEs", "Innovative SMEs", "Startups", "Scale-ups", "High-growth SMEs", "Mid-caps"],
        "large": ["Large enterprises", "Mid-caps", "SMEs"],
        "research": ["Research organisations", "Universities", "Research partners"],
        "public": ["Public sector", "Public authorities"],
    }

    allowed_targets = target_map.get(target_group, ["SMEs"])

    for prog in programmes:
        prog_targets = prog.get("target_groups_en", [])

        # Check if any of our allowed targets match the programme's target groups
        if not any(t in prog_targets for t in allowed_targets):
            continue

        matched.append(prog)

    # Sort by priority and AI relevance
    def sort_key(p: Dict[str, Any]) -> tuple:
        priority = p.get("priority", 99)
        relevance_order = {"Very high": 0, "High": 1, "Medium-High": 2, "Medium": 3, "Low": 4}
        relevance = relevance_order.get(p.get("ai_relevance_en", "Medium"), 3)

        # Boost AI-relevant programmes if ai_focus is True
        if ai_focus and relevance <= 1:
            priority -= 1

        return (priority, relevance)

    matched.sort(key=sort_key)

    return matched


def get_funding_eu_core_en(answers: Dict[str, Any]) -> FundingResultEUCore:
    """
    Get EU core funding recommendations for non-German EN reports.

    This function:
    1. Loads funding_eu_core_en.json
    2. Matches programmes based on company type and AI relevance
    3. Returns FundingResultEUCore with EN-language strings

    Args:
        answers: Dictionary containing user answers with keys like:
            - unternehmensgroesse / company_size
            - branche / industry
            - mitarbeiter / employees
            - country

    Returns:
        FundingResultEUCore with matched programmes and metadata
    """
    try:
        # Get country from answers
        country = str(answers.get("country", "EU")).upper()

        # Load EU core funding data
        data = _load_eu_core_funding_data()
        programmes = data.get("programmes", [])

        if not programmes:
            logger.warning("No EU core funding programmes found in data file")
            return FundingResultEUCore(
                programmes=[],
                country=country,
                language="en",
                error="No EU funding programmes available",
            )

        # Determine target group
        target_group = _normalize_target_group(answers)

        # Check if project has AI focus (default True for this service)
        ai_focus = True

        # Match programmes
        matched = _match_eu_core_programmes(
            programmes=programmes,
            target_group=target_group,
            ai_focus=ai_focus,
        )

        logger.info(
            f"EU Core funding match: target={target_group}, country={country}, "
            f"found={len(matched)} programmes"
        )

        return FundingResultEUCore(
            programmes=matched,
            country=country,
            language="en",
            error=None,
        )

    except Exception as e:
        logger.error(f"Error in get_funding_eu_core_en: {e}")
        return FundingResultEUCore(
            programmes=[],
            country=str(answers.get("country", "EU")).upper(),
            language="en",
            error=str(e),
        )


def render_funding_eu_core_html_en(result: FundingResultEUCore, limit: int = 4) -> str:
    """
    Render EU core funding programmes as HTML for EN reports.

    Uses the unified funding renderer for consistent output.

    Args:
        result: FundingResultEUCore from get_funding_eu_core_en()
        limit: Maximum number of programmes to render (default 4)

    Returns:
        HTML string for embedding in report
    """
    if not result.has_programmes:
        return ""

    # Convert programme dicts to FundingProgramView objects
    programmes = result.programmes[:limit]
    views: List[FundingProgramView] = [
        FundingProgramView(
            id=prog.get("id", "unknown"),
            name=prog.get("name_en", "Unknown Programme"),
            summary=prog.get("summary_en", ""),
            funding_type=prog.get("funding_type_en", ""),
            funding_rate=prog.get("funding_rate_en", ""),
            max_amount=prog.get("max_amount_en", ""),
            scope_label="EU-wide",
            target_groups=prog.get("target_groups_en", []),
            ai_relevance=prog.get("ai_relevance_en", ""),
            notes=prog.get("notes_en", ""),
        )
        for prog in programmes
    ]

    # Create render context and use unified renderer
    context = FundingRenderContext(
        scope="EU_CORE",
        programmes=views,
        lang="en",
        country=result.country,
        show_disclaimer=True,  # EU-Core always shows disclaimer
    )

    return render_funding_html(context)
