# -*- coding: utf-8 -*-
"""
Sprint B2.2: Tools × Funding Alignment Engine

Matching engine that aligns tool recommendations with funding programs
to generate combined recommendations and starter kits.

Features:
- Heuristic-based matching between tools and funding programs
- Profile-aware alignment scoring
- Cross-reference opportunities (tools that match funding requirements)
- Starter kit generation per segment

Version: 1.0.0 (Sprint B2.2)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ._normalize import _briefing_to_dict

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

TOOLS_FUNDING_ALIGNMENT_ENABLED = os.environ.get(
    "TOOLS_FUNDING_ALIGNMENT_ENABLED", "1"
) == "1"

ALIGNMENT_MIN_SCORE = float(os.environ.get("ALIGNMENT_MIN_SCORE", "0.35"))
ALIGNMENT_MAX_RECOMMENDATIONS = int(os.environ.get("ALIGNMENT_MAX_RECOMMENDATIONS", "8"))

# Weights for alignment scoring
ALIGNMENT_WEIGHT_CATEGORY = float(os.environ.get("ALIGNMENT_WEIGHT_CATEGORY", "0.30"))
ALIGNMENT_WEIGHT_SIZE = float(os.environ.get("ALIGNMENT_WEIGHT_SIZE", "0.25"))
ALIGNMENT_WEIGHT_BRANCH = float(os.environ.get("ALIGNMENT_WEIGHT_BRANCH", "0.20"))
ALIGNMENT_WEIGHT_KI_RELEVANCE = float(os.environ.get("ALIGNMENT_WEIGHT_KI_RELEVANCE", "0.15"))
ALIGNMENT_WEIGHT_COMPLEXITY = float(os.environ.get("ALIGNMENT_WEIGHT_COMPLEXITY", "0.10"))


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ToolFundingMatch:
    """A single tool-funding match with scoring."""
    tool_name: str
    tool_category: str
    funding_program_id: str
    funding_program_name: str
    alignment_score: float  # 0.0 - 1.0
    match_reasons: List[str] = field(default_factory=list)
    tool_confidence: float = 0.5
    funding_relevance: float = 0.5
    combined_score: float = 0.0
    alignment_type: str = "direct"  # direct, complementary, prerequisite

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AlignmentResult:
    """Complete alignment result for a profile."""
    matches: List[ToolFundingMatch] = field(default_factory=list)
    segment_context: Dict[str, str] = field(default_factory=dict)
    recommended_starter_tools: List[str] = field(default_factory=list)
    recommended_funding_programs: List[str] = field(default_factory=list)
    total_potential_funding: str = ""
    alignment_summary: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matches": [m.to_dict() for m in self.matches],
            "segment_context": self.segment_context,
            "recommended_starter_tools": self.recommended_starter_tools,
            "recommended_funding_programs": self.recommended_funding_programs,
            "total_potential_funding": self.total_potential_funding,
            "alignment_summary": self.alignment_summary,
            "timestamp": self.timestamp,
        }


# =============================================================================
# CATEGORY MAPPINGS
# =============================================================================

# Mapping of tool categories to funding-eligible areas
TOOL_CATEGORY_TO_FUNDING_AREA: Dict[str, List[str]] = {
    "workflow-automation": ["digitalisierung", "prozessoptimierung", "ki_integration"],
    "ki-api": ["ki_integration", "digitalisierung", "innovation"],
    "ki-api (eu)": ["ki_integration", "digitalisierung", "innovation", "eu_konform"],
    "antwort-/recherche-api": ["ki_integration", "wissensmanagement"],
    "fragebogen / intake": ["digitalisierung", "prozessoptimierung"],
    "wissensmanagement / docs": ["digitalisierung", "wissensmanagement"],
    "team-kommunikation": ["digitalisierung", "kollaboration"],
    "crm / sales": ["digitalisierung", "vertrieb", "kundenbindung"],
    "monitoring / observability": ["it_sicherheit", "governance"],
    "data quality": ["datenmanagement", "governance", "ki_integration"],
    "ml lifecycle / governance": ["ki_integration", "governance", "innovation"],
    "web-recherche (api)": ["ki_integration", "wissensmanagement"],
}

# Funding program focus areas
FUNDING_FOCUS_AREAS: Dict[str, List[str]] = {
    "go_digital": ["digitalisierung", "it_sicherheit", "prozessoptimierung"],
    "digital_jetzt": ["digitalisierung", "ki_integration", "qualifizierung"],
    "zim": ["innovation", "forschung", "ki_integration"],
    "exist": ["innovation", "technologie", "startup"],
    "kfw_digitalisierung": ["digitalisierung", "investition"],
    "horizon_europe": ["innovation", "ki_integration", "forschung", "eu_konform"],
    "invest_bw": ["innovation", "digitalisierung", "regional"],
    "bavarian_ai": ["ki_integration", "innovation", "regional"],
    "nrw_digital": ["digitalisierung", "ki_integration", "regional"],
    "ai_act_compliance": ["governance", "compliance", "ki_integration"],
}

# Size compatibility matrix
SIZE_COMPATIBILITY: Dict[str, Dict[str, float]] = {
    "solo": {"go_digital": 0.9, "nrw_digital": 0.8, "exist": 0.7, "digital_jetzt": 0.3},
    "team": {"go_digital": 0.8, "digital_jetzt": 0.9, "nrw_digital": 0.8, "invest_bw": 0.7, "bavarian_ai": 0.7},
    "kmu": {"digital_jetzt": 0.8, "zim": 0.9, "horizon_europe": 0.7, "kfw_digitalisierung": 0.8, "ai_act_compliance": 0.8},
}


# =============================================================================
# MATCHING ENGINE
# =============================================================================

def match_tool_to_funding(
    program: Dict[str, Any],
    tool: Dict[str, Any],
    size_label: str = "team",
    branch_group: str = "",
) -> ToolFundingMatch:
    """
    Calculate alignment score between a tool and a funding program.

    Heuristic-based matching using:
    - Category overlap (tool category vs funding focus areas)
    - Size compatibility
    - Branch relevance
    - KI relevance alignment
    - Complexity matching

    Args:
        program: Funding program dict
        tool: Tool recommendation dict
        size_label: Company size (solo/team/kmu)
        branch_group: Industry branch

    Returns:
        ToolFundingMatch with alignment score and reasons
    """
    program_id = program.get("id", "unknown")
    program_name = program.get("name", program_id)
    tool_name = tool.get("name", "Unknown Tool")
    tool_category = (tool.get("category", "") or "").lower()

    match_reasons: List[str] = []
    scores: Dict[str, float] = {
        "category": 0.0,
        "size": 0.0,
        "branch": 0.0,
        "ki_relevance": 0.0,
        "complexity": 0.0,
    }

    # 1. Category Match (30%)
    funding_areas = FUNDING_FOCUS_AREAS.get(program_id, [])
    tool_areas = TOOL_CATEGORY_TO_FUNDING_AREA.get(tool_category, [])

    overlap = set(funding_areas) & set(tool_areas)
    if overlap:
        scores["category"] = min(1.0, len(overlap) / 2)
        match_reasons.append(f"Gemeinsame Bereiche: {', '.join(list(overlap)[:2])}")

    # 2. Size Compatibility (25%)
    size_compat = SIZE_COMPATIBILITY.get(size_label, {})
    scores["size"] = size_compat.get(program_id, 0.5)

    tool_sizes = [s.lower() for s in tool.get("best_for_size", [])]
    if size_label in tool_sizes or "alle" in tool_sizes:
        scores["size"] = min(1.0, scores["size"] + 0.2)
        match_reasons.append(f"Passend für {size_label.upper()}")

    # 3. Branch Relevance (20%)
    program_branches = program.get("branches", ["all"])
    tool_branches = [b.lower() for b in tool.get("best_for_industries", [])]

    if "all" in program_branches or "all" in tool_branches:
        scores["branch"] = 0.7
    elif branch_group:
        branch_lower = branch_group.lower()
        if branch_lower in program_branches or any(b in branch_lower for b in program_branches):
            scores["branch"] = 0.9
            match_reasons.append(f"Branchenpassung: {branch_group}")
        elif branch_lower in tool_branches:
            scores["branch"] = 0.6
    else:
        scores["branch"] = 0.5

    # 4. KI Relevance (15%)
    program_ki = program.get("ki_relevance", "medium")
    # Tools with KI in category get higher KI relevance
    if "ki" in tool_category or "ml" in tool_category or "ai" in tool_category:
        tool_ki = "high"
    else:
        tool_ki = "medium"

    ki_scores = {"high": 1.0, "medium": 0.6, "low": 0.3}
    program_ki_score = ki_scores.get(program_ki, 0.5)
    tool_ki_score = ki_scores.get(tool_ki, 0.5)

    scores["ki_relevance"] = (program_ki_score + tool_ki_score) / 2
    if program_ki == "high" and tool_ki == "high":
        match_reasons.append("Hohe KI-Relevanz")

    # 5. Complexity Matching (10%)
    program_complexity = program.get("complexity", "medium")
    complexity_scores = {"low": 0.9, "medium": 0.7, "high": 0.5}
    scores["complexity"] = complexity_scores.get(program_complexity, 0.6)

    # Calculate weighted alignment score
    alignment_score = (
        scores["category"] * ALIGNMENT_WEIGHT_CATEGORY +
        scores["size"] * ALIGNMENT_WEIGHT_SIZE +
        scores["branch"] * ALIGNMENT_WEIGHT_BRANCH +
        scores["ki_relevance"] * ALIGNMENT_WEIGHT_KI_RELEVANCE +
        scores["complexity"] * ALIGNMENT_WEIGHT_COMPLEXITY
    )

    # Get tool confidence if available
    tool_confidence = tool.get("_confidence", 0.5)
    funding_relevance = program.get("relevance_score", 0.5) if "relevance_score" in program else 0.5

    # Combined score = alignment × tool_confidence × funding_relevance
    combined_score = alignment_score * (0.5 + tool_confidence * 0.25 + funding_relevance * 0.25)

    # Determine alignment type
    if scores["category"] >= 0.6 and scores["ki_relevance"] >= 0.7:
        alignment_type = "direct"
    elif scores["category"] >= 0.4:
        alignment_type = "complementary"
    else:
        alignment_type = "prerequisite"

    return ToolFundingMatch(
        tool_name=tool_name,
        tool_category=tool.get("category", ""),
        funding_program_id=program_id,
        funding_program_name=program_name,
        alignment_score=round(alignment_score, 3),
        match_reasons=match_reasons,
        tool_confidence=round(tool_confidence, 3),
        funding_relevance=round(funding_relevance, 3),
        combined_score=round(combined_score, 3),
        alignment_type=alignment_type,
    )


def calculate_alignment_for_profile(
    profile_context: Dict[str, Any],
    tools: Optional[List[Dict[str, Any]]] = None,
    funding_programs: Optional[List[Dict[str, Any]]] = None,
) -> AlignmentResult:
    """
    Generate Tools × Funding alignment scores for a profile.

    Args:
        profile_context: Profile data (briefing, sections, or combined)
        tools: Optional list of tool recommendations
        funding_programs: Optional list of funding programs

    Returns:
        AlignmentResult with all matches and recommendations
    """
    if not TOOLS_FUNDING_ALIGNMENT_ENABLED:
        log.debug("[B2.2] Tools-Funding alignment disabled")
        return AlignmentResult()

    # Normalize profile context
    ctx = _briefing_to_dict(profile_context)

    # Extract segment info
    size_label = _normalize_size(ctx.get("unternehmensgroesse") or ctx.get("groesse") or "team")
    branch_group = (ctx.get("branche") or ctx.get("branche_label") or "").lower()
    region = ctx.get("bundesland") or ctx.get("region") or "DE"
    ai_act_risk = ctx.get("ai_act_risk_level") or "minimal"

    # Get tools if not provided
    if tools is None:
        try:
            from services.tools_recommender import recommend_tools
            tools = recommend_tools(ctx, include_confidence=True, include_trends=True)
        except Exception as e:
            log.warning(f"[B2.2] Could not load tools: {e}")
            tools = []

    # Get funding programs if not provided
    if funding_programs is None:
        try:
            from services.funding_recommender import load_funding_programs
            funding_programs = load_funding_programs()
        except Exception as e:
            log.warning(f"[B2.2] Could not load funding programs: {e}")
            funding_programs = []

    # Generate all matches
    matches: List[ToolFundingMatch] = []

    for tool in tools:
        for program in funding_programs:
            match = match_tool_to_funding(
                program=program,
                tool=tool,
                size_label=size_label,
                branch_group=branch_group,
            )

            # Filter by minimum score
            if match.alignment_score >= ALIGNMENT_MIN_SCORE:
                matches.append(match)

    # Sort by combined score
    matches.sort(key=lambda m: m.combined_score, reverse=True)

    # Limit results
    matches = matches[:ALIGNMENT_MAX_RECOMMENDATIONS * 3]

    # Extract top recommendations
    seen_tools: set = set()
    seen_programs: set = set()
    recommended_tools: List[str] = []
    recommended_programs: List[str] = []

    for m in matches:
        if m.tool_name not in seen_tools and len(recommended_tools) < 5:
            recommended_tools.append(m.tool_name)
            seen_tools.add(m.tool_name)
        if m.funding_program_id not in seen_programs and len(recommended_programs) < 3:
            recommended_programs.append(m.funding_program_name)
            seen_programs.add(m.funding_program_id)

    # Calculate total potential funding
    total_funding = _estimate_total_funding(
        [m.funding_program_id for m in matches[:5]],
        funding_programs
    )

    # Generate summary
    alignment_summary = _generate_alignment_summary(
        len(matches),
        recommended_tools,
        recommended_programs,
        size_label,
    )

    return AlignmentResult(
        matches=matches[:ALIGNMENT_MAX_RECOMMENDATIONS],
        segment_context={
            "size_label": size_label,
            "branch_group": branch_group,
            "region": region,
            "ai_act_risk": ai_act_risk,
        },
        recommended_starter_tools=recommended_tools,
        recommended_funding_programs=recommended_programs,
        total_potential_funding=total_funding,
        alignment_summary=alignment_summary,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _normalize_size(size_raw: str) -> str:
    """Normalize company size to solo/team/kmu."""
    size_lower = size_raw.lower()
    if "solo" in size_lower or "1" in size_lower or "freiberuf" in size_lower:
        return "solo"
    elif "team" in size_lower or "klein" in size_lower or "2-10" in size_lower:
        return "team"
    return "kmu"


def _estimate_total_funding(
    program_ids: List[str],
    programs: List[Dict[str, Any]]
) -> str:
    """Estimate total potential funding amount."""
    total = 0
    for program in programs:
        if program.get("id") in program_ids:
            max_amount = program.get("max_funding", "")
            # Extract numeric value
            try:
                # Handle formats like "16.500 €", "50.000 €", "2.500.000 €"
                amount_str = max_amount.replace(".", "").replace("€", "").replace("EUR", "").strip()
                amount_str = amount_str.split()[0] if amount_str else "0"
                total += int(amount_str) if amount_str.isdigit() else 0
            except (ValueError, IndexError):
                pass

    if total >= 1_000_000:
        return f"bis zu {total / 1_000_000:.1f} Mio. €"
    elif total >= 1_000:
        return f"bis zu {total:,.0f} €".replace(",", ".")
    return ""


def _generate_alignment_summary(
    match_count: int,
    recommended_tools: List[str],
    recommended_programs: List[str],
    size_label: str,
) -> str:
    """Generate human-readable alignment summary."""
    if not match_count:
        return "Keine passenden Tool-Förder-Kombinationen gefunden."

    size_labels = {
        "solo": "Einzelunternehmer",
        "team": "kleine Teams",
        "kmu": "KMU",
    }
    size_text = size_labels.get(size_label, size_label)

    tool_text = ", ".join(recommended_tools[:3]) if recommended_tools else "keine Tools"
    program_text = ", ".join(recommended_programs[:2]) if recommended_programs else "keine Programme"

    return (
        f"{match_count} Tool-Förder-Kombinationen für {size_text} identifiziert. "
        f"Empfohlene Tools: {tool_text}. "
        f"Passende Förderprogramme: {program_text}."
    )


# =============================================================================
# HTML OUTPUT
# =============================================================================

def generate_alignment_html(result: AlignmentResult, lang: str = "de") -> str:
    """
    Generate HTML output for tool-funding alignment.

    Args:
        result: AlignmentResult object
        lang: Language code (de/en)

    Returns:
        HTML string
    """
    if not result.matches:
        return ""

    if lang == "en":
        title = "Tool &amp; Funding Alignment"
        subtitle = "Recommended tool-funding combinations for your profile"
        headers = ["Tool", "Funding Program", "Match", "Reasons"]
        summary_label = "Summary"
    else:
        title = "Tool- &amp; Förder-Alignment"
        subtitle = "Empfohlene Tool-Förder-Kombinationen für Ihr Profil"
        headers = ["Tool", "Förderprogramm", "Match", "Gründe"]
        summary_label = "Zusammenfassung"

    # Score colors
    def score_color(score: float) -> str:
        if score >= 0.7:
            return "#22c55e"
        elif score >= 0.5:
            return "#f59e0b"
        return "#6b7280"

    rows_html = ""
    for m in result.matches[:6]:
        color = score_color(m.alignment_score)
        reasons_html = "<br>".join(m.match_reasons[:2]) if m.match_reasons else "-"

        rows_html += f"""
        <tr>
            <td style="padding:10px;font-size:12px;">
                <strong>{m.tool_name}</strong>
                <br><span style="font-size:10px;color:#6b7280;">{m.tool_category}</span>
            </td>
            <td style="padding:10px;font-size:12px;">{m.funding_program_name}</td>
            <td style="padding:10px;text-align:center;">
                <span style="display:inline-block;padding:4px 8px;background:{color}20;color:{color};border-radius:4px;font-weight:600;">
                    {int(m.alignment_score * 100)}%
                </span>
            </td>
            <td style="padding:10px;font-size:11px;color:#495057;">{reasons_html}</td>
        </tr>
        """

    html = f"""
    <div class="tools-funding-alignment" style="margin:24px 0;padding:20px;background:linear-gradient(135deg,#f0f7ff,#f5f0ff);border-radius:12px;border:1px solid #c7d2fe;">
        <h3 style="margin:0 0 8px 0;font-size:16px;color:#4338ca;display:flex;align-items:center;gap:8px;">
            <span>🔗</span> {title}
            <span style="font-size:9px;padding:2px 6px;background:#4338ca;color:#fff;border-radius:4px;">B2.2</span>
        </h3>
        <p style="margin:0 0 16px 0;font-size:12px;color:#6b7280;">{subtitle}</p>

        <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;">
            <thead>
                <tr style="background:#e0e7ff;">
                    <th style="padding:10px;font-size:11px;text-align:left;">{headers[0]}</th>
                    <th style="padding:10px;font-size:11px;text-align:left;">{headers[1]}</th>
                    <th style="padding:10px;font-size:11px;text-align:center;">{headers[2]}</th>
                    <th style="padding:10px;font-size:11px;text-align:left;">{headers[3]}</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        {f'''
        <div style="margin-top:16px;padding:12px;background:#fff;border-radius:8px;border-left:3px solid #4338ca;">
            <strong style="font-size:11px;color:#4338ca;">{summary_label}:</strong>
            <p style="margin:4px 0 0 0;font-size:11px;color:#495057;">{result.alignment_summary}</p>
            {f'<p style="margin:8px 0 0 0;font-size:12px;color:#22c55e;font-weight:600;">💰 Förderpotenzial: {result.total_potential_funding}</p>' if result.total_potential_funding else ''}
        </div>
        ''' if result.alignment_summary else ''}
    </div>
    """

    return html


def generate_alignment_compact_html(result: AlignmentResult, lang: str = "de") -> str:
    """
    Generate compact HTML output for inline display.

    Args:
        result: AlignmentResult object
        lang: Language code

    Returns:
        Compact HTML string
    """
    if not result.matches:
        return ""

    title = "Top Tool-Förder-Matches" if lang == "de" else "Top Tool-Funding Matches"

    cards_html = ""
    for m in result.matches[:3]:
        score_pct = int(m.alignment_score * 100)
        cards_html += f"""
        <div style="flex:1;min-width:200px;padding:12px;background:#fff;border-radius:8px;border:1px solid #e5e7eb;">
            <div style="font-size:12px;font-weight:600;color:#1f2937;">{m.tool_name}</div>
            <div style="font-size:10px;color:#6b7280;margin:4px 0;">+ {m.funding_program_name}</div>
            <div style="font-size:11px;color:#4338ca;font-weight:600;">{score_pct}% Match</div>
        </div>
        """

    return f"""
    <div class="alignment-compact" style="margin:16px 0;">
        <div style="font-size:12px;font-weight:600;color:#374151;margin-bottom:8px;">{title}</div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
            {cards_html}
        </div>
    </div>
    """


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def inject_alignment_into_sections(
    sections: Dict[str, Any],
    briefing: Optional[Dict[str, Any]] = None,
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Inject tool-funding alignment HTML into report sections.

    Args:
        sections: Report sections dict
        briefing: Optional briefing data
        lang: Language code

    Returns:
        Updated sections with TOOLS_FUNDING_ALIGNMENT_HTML
    """
    if not TOOLS_FUNDING_ALIGNMENT_ENABLED:
        sections["TOOLS_FUNDING_ALIGNMENT_HTML"] = ""
        return sections

    try:
        # Use sections as profile context, merge with briefing if available
        profile_context = dict(sections)
        if briefing:
            profile_context.update(briefing)

        result = calculate_alignment_for_profile(profile_context)
        sections["TOOLS_FUNDING_ALIGNMENT_HTML"] = generate_alignment_html(result, lang)
        sections["TOOLS_FUNDING_ALIGNMENT_COMPACT_HTML"] = generate_alignment_compact_html(result, lang)

        if result.matches:
            log.info(f"✅ [B2.2] Injected {len(result.matches)} tool-funding alignments")
        else:
            log.debug("[B2.2] No tool-funding alignments generated")

    except Exception as e:
        log.error(f"[B2.2] Failed to generate alignment: {e}")
        sections["TOOLS_FUNDING_ALIGNMENT_HTML"] = ""
        sections["TOOLS_FUNDING_ALIGNMENT_COMPACT_HTML"] = ""

    return sections


def get_alignment_api_response(
    briefing: Dict[str, Any],
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Generate API response with tool-funding alignment.

    Args:
        briefing: Briefing data
        lang: Language code

    Returns:
        API response dict
    """
    if not TOOLS_FUNDING_ALIGNMENT_ENABLED:
        return {
            "enabled": False,
            "matches": [],
            "message": "Tool-Funding alignment is disabled",
        }

    try:
        result = calculate_alignment_for_profile(briefing)

        return {
            "enabled": True,
            "matches": [m.to_dict() for m in result.matches],
            "segment_context": result.segment_context,
            "recommended_starter_tools": result.recommended_starter_tools,
            "recommended_funding_programs": result.recommended_funding_programs,
            "total_potential_funding": result.total_potential_funding,
            "alignment_summary": result.alignment_summary,
            "html": generate_alignment_html(result, lang),
            "compact_html": generate_alignment_compact_html(result, lang),
            "timestamp": result.timestamp,
        }

    except Exception as e:
        log.error(f"[B2.2] API alignment error: {e}")
        return {
            "enabled": True,
            "matches": [],
            "error": str(e),
        }


# =============================================================================
# MODULE INIT
# =============================================================================

log.info(
    "[B2.2] Tools-Funding Alignment Engine loaded - enabled=%s, min_score=%.2f",
    TOOLS_FUNDING_ALIGNMENT_ENABLED,
    ALIGNMENT_MIN_SCORE,
)
