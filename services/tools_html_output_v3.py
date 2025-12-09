# -*- coding: utf-8 -*-
"""
Sprint B3-G: Tools HTML Output Module v3

Unified HTML output generation for all Tools Engine 3.0 components.
Combines outputs from:
- tools_stack_builder.py (Adaptive Stacks)
- tools_workflow_engine.py (Workflow Cards)
- tools_governance.py (Governance Analysis)
- tools_fit_engine.py (Fit Scores)

Produces consistent, styled HTML for report injection.

Version: 3.0.0 (Sprint B3)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

log = logging.getLogger(__name__)


# =============================================================================
# OUTPUT DATA CLASSES
# =============================================================================

@dataclass
class ToolsHtmlOutput:
    """Complete HTML output for tools section."""
    # Main sections
    tools_stack_html: str
    tools_workflow_html: str
    tools_governance_html: str
    tools_quick_wins_html: str

    # Individual tool cards
    tool_cards_html: str

    # Summary sections
    tools_summary_html: str
    tools_roadmap_html: str

    # Metadata
    total_tools: int
    quick_win_count: int
    workflow_count: int
    governance_score: float


# =============================================================================
# HTML TEMPLATES
# =============================================================================

CSS_STYLES = """
<style>
/* Tools Engine 3.0 Styles */
.tools-section {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
}

.tools-header {
    border-bottom: 2px solid #2563eb;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
    color: #1e40af;
}

/* Tool Cards */
.tool-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.tool-card:hover {
    border-color: #2563eb;
    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.1);
}

.tool-card h4 {
    margin: 0 0 0.5rem 0;
    color: #1e40af;
}

.tool-card .tool-category {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.tool-card .tool-fit {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 600;
}

.tool-fit-excellent { background: #dcfce7; color: #166534; }
.tool-fit-good { background: #dbeafe; color: #1e40af; }
.tool-fit-moderate { background: #fef3c7; color: #92400e; }
.tool-fit-low { background: #fee2e2; color: #991b1b; }

/* Badges */
.badge {
    display: inline-block;
    padding: 0.125rem 0.5rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 0.25rem;
}

.badge-quickwin { background: #dcfce7; color: #166534; }
.badge-roi { background: #dbeafe; color: #1e40af; }
.badge-effort-low { background: #dcfce7; color: #166534; }
.badge-effort-medium { background: #fef3c7; color: #92400e; }
.badge-effort-high { background: #fee2e2; color: #991b1b; }

/* Workflow Cards */
.workflow-card {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
}

.workflow-card h4 {
    margin: 0;
    color: #0f172a;
}

.workflow-badges {
    margin-top: 0.5rem;
}

.workflow-tools, .workflow-benefits {
    margin-top: 1rem;
}

.workflow-tools ul, .workflow-benefits ul {
    margin: 0.5rem 0;
    padding-left: 1.5rem;
}

.workflow-steps {
    margin-top: 1rem;
    background: white;
    border-radius: 8px;
    padding: 0.75rem;
}

.workflow-steps summary {
    cursor: pointer;
    font-weight: 500;
}

.workflow-meta {
    margin-top: 1rem;
    font-size: 0.875rem;
    color: #64748b;
}

/* Governance */
.governance-scores {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.score-card {
    flex: 1;
    text-align: center;
    padding: 1rem;
    border-radius: 8px;
    background: #f8fafc;
}

.score-card .score-value {
    display: block;
    font-size: 2rem;
    font-weight: 700;
}

.score-card .score-label {
    display: block;
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
}

.score-excellent { background: #dcfce7; }
.score-excellent .score-value { color: #166534; }

.score-good { background: #dbeafe; }
.score-good .score-value { color: #1e40af; }

.score-warning { background: #fef3c7; }
.score-warning .score-value { color: #92400e; }

.score-critical { background: #fee2e2; }
.score-critical .score-value { color: #991b1b; }

/* Risk List */
.risk-list li {
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    border-radius: 4px;
}

.risk-low { background: #f0fdf4; border-left: 3px solid #22c55e; }
.risk-medium { background: #fefce8; border-left: 3px solid #eab308; }
.risk-high { background: #fef2f2; border-left: 3px solid #ef4444; }
.risk-critical { background: #fef2f2; border-left: 3px solid #dc2626; }

/* Tool Stack */
.tool-stack {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
}

.stack-category {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
}

.stack-category h5 {
    margin: 0 0 0.75rem 0;
    color: #475569;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 0.5rem;
}

/* Quick Wins */
.quick-wins-section {
    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.quick-wins-section h3 {
    color: #065f46;
    margin-top: 0;
}

/* Roadmap */
.roadmap-timeline {
    position: relative;
    padding-left: 2rem;
}

.roadmap-timeline::before {
    content: '';
    position: absolute;
    left: 0.5rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #e2e8f0;
}

.roadmap-item {
    position: relative;
    padding-bottom: 1.5rem;
}

.roadmap-item::before {
    content: '';
    position: absolute;
    left: -1.75rem;
    top: 0.25rem;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #2563eb;
    border: 2px solid white;
}

.roadmap-phase {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Summary Stats */
.tools-stats {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.stat-item {
    text-align: center;
    padding: 1rem 1.5rem;
    background: #f8fafc;
    border-radius: 8px;
    min-width: 120px;
}

.stat-value {
    display: block;
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e40af;
}

.stat-label {
    display: block;
    font-size: 0.75rem;
    color: #64748b;
}

/* Integration Hints */
.integration-hints {
    background: #eff6ff;
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
}

.integration-hints h5 {
    margin: 0 0 0.5rem 0;
    color: #1e40af;
}

.integration-hints ul {
    margin: 0;
    padding-left: 1.25rem;
}
</style>
"""


# =============================================================================
# TOOL CARD GENERATION
# =============================================================================

def generate_tool_card_html(
    tool: Dict[str, Any],
    language: str = "de",
) -> str:
    """
    Generate HTML for a single tool card.

    Args:
        tool: Tool data dictionary
        language: Output language (de/en)

    Returns:
        HTML string for tool card
    """
    is_de = language.lower() == "de"

    name = tool.get("name", "Unknown Tool")
    category = tool.get("category", "general")
    description = tool.get("description_de" if is_de else "description_en", tool.get("description", ""))
    fit_score = tool.get("fit_score", 0)
    monthly_cost = tool.get("monthly_cost", 0)
    setup_hours = tool.get("setup_hours", 0)

    # Determine fit class
    if fit_score >= 80:
        fit_class = "tool-fit-excellent"
        fit_label = "Exzellent" if is_de else "Excellent"
    elif fit_score >= 60:
        fit_class = "tool-fit-good"
        fit_label = "Gut" if is_de else "Good"
    elif fit_score >= 40:
        fit_class = "tool-fit-moderate"
        fit_label = "Moderat" if is_de else "Moderate"
    else:
        fit_class = "tool-fit-low"
        fit_label = "Niedrig" if is_de else "Low"

    # Labels
    cost_label = "Kosten" if is_de else "Cost"
    setup_label = "Setup" if is_de else "Setup"
    month_label = "Monat" if is_de else "month"
    hours_label = "Stunden" if is_de else "hours"

    return f'''
    <div class="tool-card" data-category="{category}">
        <div class="tool-category">{category}</div>
        <h4>{name}</h4>
        <p>{description}</p>
        <div class="tool-meta">
            <span class="tool-fit {fit_class}">{fit_label} ({fit_score:.0f}%)</span>
            <span class="tool-cost">{cost_label}: €{monthly_cost:.2f}/{month_label}</span>
            <span class="tool-setup">{setup_label}: {setup_hours} {hours_label}</span>
        </div>
    </div>
    '''


def generate_tool_cards_html(
    tools: List[Dict[str, Any]],
    language: str = "de",
) -> str:
    """
    Generate HTML for multiple tool cards.

    Args:
        tools: List of tool data dictionaries
        language: Output language (de/en)

    Returns:
        HTML string for all tool cards
    """
    if not tools:
        return ""

    cards = [generate_tool_card_html(tool, language) for tool in tools]
    return f'<div class="tool-cards">{" ".join(cards)}</div>'


# =============================================================================
# SUMMARY GENERATION
# =============================================================================

def generate_tools_summary_html(
    total_tools: int,
    quick_wins: int,
    workflows: int,
    governance_score: float,
    estimated_monthly_cost: float,
    estimated_setup_hours: int,
    language: str = "de",
) -> str:
    """
    Generate HTML for tools summary section.

    Args:
        total_tools: Total number of recommended tools
        quick_wins: Number of quick win opportunities
        workflows: Number of workflow recommendations
        governance_score: Overall governance score
        estimated_monthly_cost: Estimated monthly cost
        estimated_setup_hours: Estimated setup hours
        language: Output language (de/en)

    Returns:
        HTML string for summary
    """
    is_de = language.lower() == "de"

    # Labels
    tools_label = "Tools" if is_de else "Tools"
    quick_wins_label = "Quick Wins" if is_de else "Quick Wins"
    workflows_label = "Workflows" if is_de else "Workflows"
    governance_label = "Governance" if is_de else "Governance"
    cost_label = "Monatliche Kosten" if is_de else "Monthly Cost"
    setup_label = "Setup-Zeit" if is_de else "Setup Time"
    hours_label = "Stunden" if is_de else "hours"

    return f'''
    <div class="tools-summary">
        <div class="tools-stats">
            <div class="stat-item">
                <span class="stat-value">{total_tools}</span>
                <span class="stat-label">{tools_label}</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{quick_wins}</span>
                <span class="stat-label">{quick_wins_label}</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{workflows}</span>
                <span class="stat-label">{workflows_label}</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{governance_score:.0f}%</span>
                <span class="stat-label">{governance_label}</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">€{estimated_monthly_cost:.0f}</span>
                <span class="stat-label">{cost_label}</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{estimated_setup_hours}</span>
                <span class="stat-label">{setup_label} ({hours_label})</span>
            </div>
        </div>
    </div>
    '''


# =============================================================================
# ROADMAP GENERATION
# =============================================================================

def generate_roadmap_html(
    roadmap_phases: List[Dict[str, Any]],
    language: str = "de",
) -> str:
    """
    Generate HTML for implementation roadmap.

    Args:
        roadmap_phases: List of roadmap phase dictionaries
        language: Output language (de/en)

    Returns:
        HTML string for roadmap
    """
    is_de = language.lower() == "de"

    if not roadmap_phases:
        # Generate default roadmap
        roadmap_phases = [
            {
                "phase": "Phase 1",
                "title": "Quick Wins implementieren" if is_de else "Implement Quick Wins",
                "timeframe": "Woche 1-2" if is_de else "Week 1-2",
                "items": [
                    "KI-Assistenz einrichten" if is_de else "Set up AI assistance",
                    "Dokumentation automatisieren" if is_de else "Automate documentation",
                    "Social Media Tools aktivieren" if is_de else "Activate social media tools",
                ],
            },
            {
                "phase": "Phase 2",
                "title": "Kernprozesse digitalisieren" if is_de else "Digitize core processes",
                "timeframe": "Woche 3-6" if is_de else "Week 3-6",
                "items": [
                    "CRM-System einführen" if is_de else "Implement CRM system",
                    "Projektmanagement-Tools integrieren" if is_de else "Integrate project management tools",
                    "Reporting-Automatisierung" if is_de else "Reporting automation",
                ],
            },
            {
                "phase": "Phase 3",
                "title": "Optimierung & Skalierung" if is_de else "Optimization & Scaling",
                "timeframe": "Woche 7-12" if is_de else "Week 7-12",
                "items": [
                    "Workflow-Automationen verfeinern" if is_de else "Refine workflow automations",
                    "Integrationen optimieren" if is_de else "Optimize integrations",
                    "KI-gestützte Analysen ausbauen" if is_de else "Expand AI-powered analytics",
                ],
            },
        ]

    header = "Implementierungs-Roadmap" if is_de else "Implementation Roadmap"

    html_parts = [
        f'<div class="tools-roadmap">',
        f'<h3 class="tools-header">{header}</h3>',
        f'<div class="roadmap-timeline">',
    ]

    for phase in roadmap_phases:
        html_parts.append(f'''
        <div class="roadmap-item">
            <div class="roadmap-phase">{phase.get("phase", "")} ({phase.get("timeframe", "")})</div>
            <h4>{phase.get("title", "")}</h4>
            <ul>
        ''')
        for item in phase.get("items", []):
            html_parts.append(f'<li>{item}</li>')
        html_parts.append('</ul></div>')

    html_parts.append('</div></div>')

    return "\n".join(html_parts)


# =============================================================================
# STACK HTML GENERATION
# =============================================================================

def generate_stack_html(
    stack_data: Dict[str, Any],
    language: str = "de",
) -> str:
    """
    Generate HTML for adaptive tool stack.

    Args:
        stack_data: Stack data from tools_stack_builder
        language: Output language (de/en)

    Returns:
        HTML string for stack
    """
    is_de = language.lower() == "de"

    header = "Empfohlene Tool-Stack" if is_de else "Recommended Tool Stack"
    integration_header = "Integrationshinweise" if is_de else "Integration Hints"

    html_parts = [
        f'<div class="tools-stack-section">',
        f'<h3 class="tools-header">{header}</h3>',
        f'<div class="tool-stack">',
    ]

    # Group tools by category
    categories = stack_data.get("categories", {})
    if not categories:
        # Fallback: group from tools list
        tools = stack_data.get("tools", [])
        categories = {}
        for tool in tools:
            cat = tool.get("category", "general")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool)

    # Category labels
    category_labels = {
        "communication": ("Kommunikation", "Communication"),
        "project_management": ("Projektmanagement", "Project Management"),
        "crm": ("CRM", "CRM"),
        "analytics": ("Analytics", "Analytics"),
        "finance": ("Finanzen", "Finance"),
        "hr": ("Personal", "HR"),
        "marketing": ("Marketing", "Marketing"),
        "ai_automation": ("KI & Automation", "AI & Automation"),
        "security": ("Sicherheit", "Security"),
        "general": ("Allgemein", "General"),
    }

    for cat_key, tools in categories.items():
        cat_label = category_labels.get(cat_key, (cat_key.title(), cat_key.title()))[0 if is_de else 1]

        html_parts.append(f'''
        <div class="stack-category" data-category="{cat_key}">
            <h5>{cat_label}</h5>
            <ul>
        ''')

        for tool in tools:
            name = tool.get("name", "Unknown")
            fit = tool.get("fit_score", 0)
            html_parts.append(f'<li><strong>{name}</strong> ({fit:.0f}%)</li>')

        html_parts.append('</ul></div>')

    html_parts.append('</div>')

    # Integration hints
    hints = stack_data.get("integration_hints", [])
    if hints:
        html_parts.append(f'''
        <div class="integration-hints">
            <h5>{integration_header}</h5>
            <ul>
        ''')
        for hint in hints:
            html_parts.append(f'<li>{hint}</li>')
        html_parts.append('</ul></div>')

    html_parts.append('</div>')

    return "\n".join(html_parts)


# =============================================================================
# MAIN OUTPUT GENERATION
# =============================================================================

def generate_tools_html_output(
    briefing: Dict[str, Any],
    language: str = "de",
    include_styles: bool = True,
) -> ToolsHtmlOutput:
    """
    Generate complete HTML output for tools section.

    Args:
        briefing: Company briefing dictionary
        language: Output language (de/en)
        include_styles: Whether to include CSS styles

    Returns:
        ToolsHtmlOutput with all HTML sections
    """
    branch = briefing.get("branche", "beratung")
    size = briefing.get("unternehmensgroesse", "team")
    usecases = briefing.get("usecases", [])

    if isinstance(usecases, str):
        usecases = [u.strip() for u in usecases.split(",") if u.strip()]

    # Map frontend branch if needed
    try:
        from services.branch_mapping import map_frontend_branch_to_engine
        branch = map_frontend_branch_to_engine(branch)
    except ImportError:
        pass

    # Initialize output sections
    tools_stack_html = ""
    tools_workflow_html = ""
    tools_governance_html = ""
    tools_quick_wins_html = ""
    tool_cards_html = ""
    tools_summary_html = ""
    tools_roadmap_html = ""

    # Track statistics
    total_tools = 0
    quick_win_count = 0
    workflow_count = 0
    governance_score = 0.0
    estimated_monthly_cost = 0.0
    estimated_setup_hours = 0

    # Try to generate stack HTML
    try:
        from services.tools_stack_builder import generate_adaptive_stack

        stack = generate_adaptive_stack(
            branch=branch,
            size=size,
            usecases=usecases,
            risk_level="medium",
            funding_focus=[],
            top_k=15,
        )

        # Convert to dict for HTML generation
        stack_dict = {
            "tools": [
                {
                    "name": t.tool_name,
                    "category": t.category,
                    "fit_score": t.fit_score,
                }
                for t in stack.tools
            ],
            "integration_hints": stack.integration_hints,
        }

        tools_stack_html = generate_stack_html(stack_dict, language)
        total_tools = len(stack.tools)
        # estimated_monthly_cost is not in dataclass, calculate from tools
        estimated_monthly_cost = 0.0  # Would need tool cost data
        estimated_setup_hours = stack.estimated_setup_days * 8  # Convert days to hours

    except ImportError as e:
        log.warning("[B3-G] Stack builder not available: %s", e)
    except Exception as e:
        log.warning("[B3-G] Error generating stack HTML: %s", e)

    # Try to generate workflow HTML
    try:
        from services.tools_workflow_engine import get_workflow_html_sections

        workflow_sections = get_workflow_html_sections(briefing, language)
        tools_workflow_html = workflow_sections.get("TOOLS_WORKFLOW_HTML", "")
        tools_quick_wins_html = workflow_sections.get("TOOLS_QUICK_WINS_HTML", "")

        # Count workflows and quick wins
        workflow_count = tools_workflow_html.count('class="workflow-card"')
        quick_win_count = tools_quick_wins_html.count('class="workflow-card"')

    except ImportError as e:
        log.warning("[B3-G] Workflow engine not available: %s", e)
    except Exception as e:
        log.warning("[B3-G] Error generating workflow HTML: %s", e)

    # Try to generate governance HTML
    try:
        from services.tools_governance import get_governance_html_sections, analyze_governance

        # Get tool IDs from stack if available
        tool_ids = []
        try:
            from services.tools_stack_builder import generate_adaptive_stack
            stack = generate_adaptive_stack(branch, size, usecases, "medium", [], 15)
            tool_ids = [t.tool_id for t in stack.tools]
        except Exception:
            pass

        if tool_ids:
            gov_sections = get_governance_html_sections(tool_ids, briefing, language)
            tools_governance_html = gov_sections.get("TOOLS_GOVERNANCE_HTML", "")

            # Get governance score
            analysis = analyze_governance(tool_ids, branch, size)
            governance_score = analysis.overall_score

    except ImportError as e:
        log.warning("[B3-G] Governance module not available: %s", e)
    except Exception as e:
        log.warning("[B3-G] Error generating governance HTML: %s", e)

    # Generate summary
    tools_summary_html = generate_tools_summary_html(
        total_tools=total_tools,
        quick_wins=quick_win_count,
        workflows=workflow_count,
        governance_score=governance_score,
        estimated_monthly_cost=estimated_monthly_cost,
        estimated_setup_hours=estimated_setup_hours,
        language=language,
    )

    # Generate roadmap
    tools_roadmap_html = generate_roadmap_html([], language)

    # Prepend CSS if requested
    if include_styles:
        tools_stack_html = CSS_STYLES + tools_stack_html

    return ToolsHtmlOutput(
        tools_stack_html=tools_stack_html,
        tools_workflow_html=tools_workflow_html,
        tools_governance_html=tools_governance_html,
        tools_quick_wins_html=tools_quick_wins_html,
        tool_cards_html=tool_cards_html,
        tools_summary_html=tools_summary_html,
        tools_roadmap_html=tools_roadmap_html,
        total_tools=total_tools,
        quick_win_count=quick_win_count,
        workflow_count=workflow_count,
        governance_score=governance_score,
    )


def get_all_tools_html_sections(
    briefing: Dict[str, Any],
    language: str = "de",
) -> Dict[str, str]:
    """
    Get all HTML sections as a dictionary for template injection.

    Args:
        briefing: Company briefing dictionary
        language: Output language (de/en)

    Returns:
        Dictionary mapping section names to HTML content
    """
    output = generate_tools_html_output(briefing, language)

    return {
        "TOOLS_STACK_HTML": output.tools_stack_html,
        "TOOLS_WORKFLOW_HTML": output.tools_workflow_html,
        "TOOLS_GOVERNANCE_HTML": output.tools_governance_html,
        "TOOLS_QUICK_WINS_HTML": output.tools_quick_wins_html,
        "TOOLS_CARDS_HTML": output.tool_cards_html,
        "TOOLS_SUMMARY_HTML": output.tools_summary_html,
        "TOOLS_ROADMAP_HTML": output.tools_roadmap_html,
    }


# =============================================================================
# CSS INJECTION HELPER
# =============================================================================

def get_tools_css() -> str:
    """
    Get CSS styles for tools sections.

    Returns:
        CSS string without <style> tags
    """
    # Strip the <style> tags
    css = CSS_STYLES.replace("<style>", "").replace("</style>", "").strip()
    return css


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[B3-G] HTML Output Module v3 loaded")
