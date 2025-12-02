"""
Funding Service EN - English funding recommendations for Germany-based companies.

This module provides English-language funding program recommendations
for users with companies based in Germany (lang="en", country="DE").
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class FundingResult:
    """Result of funding program matching for EN reports."""

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

    # Map common values to our categories
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
            bundesland = str(bundesland).upper()[:2]  # Normalize to 2-letter code

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

    Args:
        result: FundingResult from get_funding_for_germany_en()
        limit: Maximum number of programmes to render

    Returns:
        HTML string for embedding in report
    """
    if not result.has_programmes:
        return ""

    programmes = result.programmes[:limit]
    html_parts: List[str] = ['<div class="funding-programmes">']

    for prog in programmes:
        name = prog.get("name_en", prog.get("name_de", "Unknown Programme"))
        summary = prog.get("summary_en", prog.get("focus_en", ""))
        funding_type = prog.get("funding_type_en", "Grant")
        funding_rate = prog.get("funding_rate_en", "")
        max_amount = prog.get("max_amount_en", "")
        region = prog.get("region_en", "Germany")
        url = prog.get("url", "")

        html_parts.append('<div class="funding-programme">')
        html_parts.append(f'  <h4>{name}</h4>')

        if summary:
            html_parts.append(f'  <p class="summary">{summary}</p>')

        html_parts.append('  <ul class="details">')
        if funding_type:
            html_parts.append(f"    <li><strong>Type:</strong> {funding_type}</li>")
        if funding_rate:
            html_parts.append(f"    <li><strong>Funding Rate:</strong> {funding_rate}</li>")
        if max_amount:
            html_parts.append(f"    <li><strong>Maximum Amount:</strong> {max_amount}</li>")
        if region:
            html_parts.append(f"    <li><strong>Region:</strong> {region}</li>")
        html_parts.append("  </ul>")

        if url:
            html_parts.append(
                f'  <p class="url"><a href="{url}" target="_blank">More information</a></p>'
            )

        html_parts.append("</div>")

    html_parts.append("</div>")

    return "\n".join(html_parts)
