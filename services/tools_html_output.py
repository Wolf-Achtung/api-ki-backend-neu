# -*- coding: utf-8 -*-
"""
Sprint B2-F: Tools HTML Report Output
=====================================

Provides HTML template variables for tools section in reports.

Variables:
- TOOLS_CONFIDENCE_TABLE_HTML
- TOOLS_TREND_CHART_HTML
- TOOLS_INSIGHT_CARDS_HTML
- TOOLS_PREDICTED_VALUE_HTML
- TOOLS_SEGMENT_STABILITY_HTML

Version: 1.0.0 (Sprint B2)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

log = logging.getLogger(__name__)

# Configuration
TOOLS_ENGINE_ENABLED = os.environ.get("TOOLS_ENGINE_ENABLED", "1") == "1"
TOOLS_CONFIDENCE_SHOW_BADGES = os.environ.get("TOOLS_CONFIDENCE_SHOW_BADGES", "1") == "1"
TOOLS_PREDICTIVE_ENABLED = os.environ.get("TOOLS_PREDICTIVE_ENABLED", "1") == "1"


def get_tools_html_sections(briefing: Dict[str, Any]) -> Dict[str, str]:
    """
    Get all tools-related HTML sections for report template.

    This is the main entry point for the report pipeline.

    Args:
        briefing: Briefing data with company context

    Returns:
        Dict with HTML template variable names and values
    """
    if not TOOLS_ENGINE_ENABLED:
        return {
            "TOOLS_CONFIDENCE_TABLE_HTML": "",
            "TOOLS_TREND_CHART_HTML": "",
            "TOOLS_INSIGHT_CARDS_HTML": "",
            "TOOLS_PREDICTED_VALUE_HTML": "",
            "TOOLS_SEGMENT_STABILITY_HTML": "",
        }

    try:
        from services.tools_recommender import generate_all_html_sections
        return generate_all_html_sections(briefing)
    except ImportError as e:
        log.warning(f"Could not import tools_recommender: {e}")
        return _get_fallback_sections()
    except Exception as e:
        log.error(f"Error generating tools HTML: {e}")
        return _get_fallback_sections()


def _get_fallback_sections() -> Dict[str, str]:
    """Get fallback empty sections when tools engine is unavailable."""
    return {
        "TOOLS_TABLE_HTML": "",
        "TOOLS_CONFIDENCE_TABLE_HTML": "",
        "TOOLS_TREND_CHART_HTML": "",
        "TOOLS_INSIGHT_CARDS_HTML": "",
        "TOOLS_PREDICTED_VALUE_HTML": "",
        "TOOLS_SEGMENT_STABILITY_HTML": "",
    }


# =============================================================================
# SAMPLE INSIGHT CARDS (for documentation/testing)
# =============================================================================

SAMPLE_INSIGHT_CARDS = [
    {
        "type": "high_adoption",
        "title": "Hohe Adoption in Ihrem Segment",
        "description": "3 Tools werden haeufig in aehnlichen Unternehmen eingesetzt.",
        "tools": ["Notion", "Make (Integromat)", "Slack"],
        "icon": "chart-line-up"
    },
    {
        "type": "emerging",
        "title": "Aufstrebende Tools fuer IT",
        "description": "2 Tools zeigen einen positiven Trend.",
        "tools": ["Claude API", "Great Expectations"],
        "icon": "rocket"
    },
    {
        "type": "governance",
        "title": "Starke Governance-Ausrichtung",
        "description": "4 Tools unterstuetzen Ihre Compliance-Anforderungen.",
        "tools": ["MLflow", "DataDog", "Grafana"],
        "icon": "shield-check"
    },
    {
        "type": "persona_fit",
        "title": "Fokus auf Data Quality + Governance fuer KMU",
        "description": "Empfohlene Kategorien: Data Quality, ML Lifecycle, Monitoring",
        "tools": [],
        "icon": "user-check"
    },
    {
        "type": "cost_efficiency",
        "title": "Kosteneffiziente Optionen",
        "description": "5 Tools bieten kostenlose Einstiegsoptionen.",
        "tools": ["Notion", "Make", "MLflow"],
        "icon": "wallet"
    }
]


def get_sample_insight_cards_html() -> str:
    """
    Generate HTML for sample insight cards.

    Returns:
        HTML string with 3-5 sample cards
    """
    try:
        from services.tools_recommender import generate_insight_cards_html
        return generate_insight_cards_html(SAMPLE_INSIGHT_CARDS[:5])
    except ImportError:
        return _generate_basic_insight_cards(SAMPLE_INSIGHT_CARDS[:5])


def _generate_basic_insight_cards(insights: List[Dict[str, Any]]) -> str:
    """Generate basic HTML for insight cards without full module."""
    if not insights:
        return ""

    cards = []
    colors = {
        "high_adoption": "#22c55e",
        "emerging": "#8b5cf6",
        "governance": "#3b82f6",
        "persona_fit": "#f59e0b",
        "cost_efficiency": "#10b981"
    }

    for ins in insights:
        ins_type = ins.get("type", "default")
        color = colors.get(ins_type, "#6b7280")

        tools_html = ""
        if ins.get("tools"):
            tools_html = f"""
            <div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px;">
                {"".join(f'<span style="background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{t}</span>' for t in ins["tools"][:3])}
            </div>
            """

        cards.append(f"""
        <div style="
            background: {color}08;
            border: 1px solid {color}20;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
        ">
            <h5 style="margin: 0 0 6px 0; font-size: 13px; color: {color};">{ins.get("title", "")}</h5>
            <p style="margin: 0; font-size: 11px; color: #6b7280;">{ins.get("description", "")}</p>
            {tools_html}
        </div>
        """)

    return f"""
    <div class="tools-insight-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; margin: 16px 0;">
        {"".join(cards)}
    </div>
    """


# =============================================================================
# SAMPLE JSON OUTPUT
# =============================================================================

def get_sample_tool_stats_json() -> Dict[str, Any]:
    """
    Get sample tool statistics JSON for documentation.

    Returns:
        Dict with sample tool statistics
    """
    return {
        "snapshot_id": "tools_snap_20241209_120000",
        "timestamp": "2024-12-09T12:00:00.000Z",
        "total_reports_analyzed": 150,
        "total_tools_tracked": 12,
        "segment_analyses": [
            {
                "segment_id": "size_solo",
                "segment_type": "size_label",
                "segment_value": "solo",
                "tool_count": 8,
                "report_count": 45,
                "stability": "strong",
                "sample_size": 45,
                "mean_tools_per_report": 5.2,
                "top_tools": ["Make (Integromat)", "Notion", "ChatGPT", "Canva", "Tally.so"]
            },
            {
                "segment_id": "size_team",
                "segment_type": "size_label",
                "segment_value": "team",
                "tool_count": 10,
                "report_count": 55,
                "stability": "strong",
                "sample_size": 55,
                "mean_tools_per_report": 6.8,
                "top_tools": ["Slack", "Notion", "Jira", "HubSpot", "Figma"]
            },
            {
                "segment_id": "size_kmu",
                "segment_type": "size_label",
                "segment_value": "kmu",
                "tool_count": 12,
                "report_count": 50,
                "stability": "medium",
                "sample_size": 50,
                "mean_tools_per_report": 8.5,
                "top_tools": ["HubSpot", "DataDog", "Great Expectations", "Salesforce", "Power BI"]
            }
        ],
        "tool_stats": [
            {
                "tool_name": "Make (Integromat)",
                "usage_count": 95,
                "confidence": 0.82,
                "confidence_level": "high",
                "segment_stability": "strong",
                "ai_act_alignment": 0.65,
                "persona_fit_score": 0.90,
                "recommended_rank": 1
            },
            {
                "tool_name": "Notion",
                "usage_count": 88,
                "confidence": 0.78,
                "confidence_level": "high",
                "segment_stability": "strong",
                "ai_act_alignment": 0.60,
                "persona_fit_score": 0.85,
                "recommended_rank": 2
            },
            {
                "tool_name": "DataDog",
                "usage_count": 42,
                "confidence": 0.72,
                "confidence_level": "high",
                "segment_stability": "medium",
                "ai_act_alignment": 0.95,
                "persona_fit_score": 0.70,
                "recommended_rank": 3
            }
        ],
        "confidence_distribution": {
            "high": 5,
            "medium": 5,
            "low": 2
        },
        "stability_distribution": {
            "strong": 6,
            "medium": 4,
            "weak": 2
        }
    }


# =============================================================================
# VALIDATION ANALYSIS SAMPLE
# =============================================================================

def get_sample_validation_analysis() -> Dict[str, Any]:
    """
    Get sample validation analysis for tools section.

    Returns:
        Dict with validation analysis results
    """
    return {
        "validation_timestamp": "2024-12-09T12:00:00.000Z",
        "tools_section_validated": True,
        "issues_found": [
            {
                "severity": "INFO",
                "category": "TOOLS_SEGMENT_WEAKNESS",
                "message": "Segment 'solo' hat moderate Datenbasis",
                "details": "Sample-Size: 45 Reports. Empfehlung: Weitere Daten sammeln."
            }
        ],
        "confidence_check": {
            "all_tools_have_confidence": True,
            "low_confidence_tools_count": 0,
            "average_confidence": 0.68
        },
        "ai_act_alignment_check": {
            "risk_level": "limited",
            "misaligned_tools_count": 0,
            "governance_tools_present": True
        },
        "persona_fit_check": {
            "persona": "team",
            "inappropriate_tools_count": 0,
            "fit_score_average": 0.85
        },
        "overpopulation_check": {
            "tool_count": 10,
            "limit": 14,
            "is_overpopulated": False
        },
        "overall_status": "PASS",
        "recommendations": [
            "Alle Tools haben Konfidenz-Metadaten - gut!",
            "Governance-Tools fuer 'limited' Risk-Level vorhanden",
            "Tool-Anzahl im akzeptablen Bereich"
        ]
    }


# =============================================================================
# GOLD PROFILE VALIDATION
# =============================================================================

GOLD_PROFILES = [
    {
        "name": "Solo Consultant - IT Beratung",
        "briefing": {
            "unternehmensgroesse": "Solo-Selbststaendige/r (1)",
            "branche": "IT & Softwareentwicklung",
            "ai_act_risk_level": "minimal"
        },
        "expected": {
            "min_tools": 5,
            "max_tools": 8,
            "required_categories": ["Workflow-Automation", "KI-API"],
            "forbidden_tools": ["Collibra", "SAP MDM", "ServiceNow"]
        }
    },
    {
        "name": "Team Agentur - Marketing",
        "briefing": {
            "unternehmensgroesse": "Kleines Team (2-10)",
            "branche": "Marketing & Kommunikation",
            "ai_act_risk_level": "limited"
        },
        "expected": {
            "min_tools": 6,
            "max_tools": 10,
            "required_categories": ["Team-Kommunikation", "CRM"],
            "forbidden_tools": ["SAP MDM", "IBM DataStage"]
        }
    },
    {
        "name": "KMU Manufacturing - High Risk",
        "briefing": {
            "unternehmensgroesse": "KMU (11-250)",
            "branche": "Produktion & Fertigung",
            "ai_act_risk_level": "high-risk"
        },
        "expected": {
            "min_tools": 8,
            "max_tools": 12,
            "required_categories": ["Monitoring", "Data Quality", "ML Lifecycle"],
            "forbidden_tools": []
        }
    }
]


def validate_gold_profiles() -> List[Dict[str, Any]]:
    """
    Run validation on gold profiles.

    Returns:
        List of validation results per profile
    """
    results = []

    try:
        from services.tools_recommender import recommend_tools
    except ImportError:
        return [{"error": "tools_recommender not available"}]

    for profile in GOLD_PROFILES:
        briefing = profile["briefing"]
        expected = profile["expected"]

        # Get recommendations
        tools = recommend_tools(briefing)
        tool_names = [t.get("name", "") for t in tools]
        tool_cats = [t.get("category", "") for t in tools]

        # Validate
        validation = {
            "profile_name": profile["name"],
            "passed": True,
            "checks": []
        }

        # Check tool count
        if len(tools) < expected["min_tools"]:
            validation["passed"] = False
            validation["checks"].append({
                "check": "min_tools",
                "passed": False,
                "message": f"Too few tools: {len(tools)} < {expected['min_tools']}"
            })
        elif len(tools) > expected["max_tools"]:
            validation["passed"] = False
            validation["checks"].append({
                "check": "max_tools",
                "passed": False,
                "message": f"Too many tools: {len(tools)} > {expected['max_tools']}"
            })
        else:
            validation["checks"].append({
                "check": "tool_count",
                "passed": True,
                "message": f"Tool count OK: {len(tools)}"
            })

        # Check required categories
        for req_cat in expected["required_categories"]:
            found = any(req_cat.lower() in cat.lower() for cat in tool_cats)
            if not found:
                validation["passed"] = False
                validation["checks"].append({
                    "check": "required_category",
                    "passed": False,
                    "message": f"Missing required category: {req_cat}"
                })

        # Check forbidden tools
        for forbidden in expected["forbidden_tools"]:
            if any(forbidden.lower() in name.lower() for name in tool_names):
                validation["passed"] = False
                validation["checks"].append({
                    "check": "forbidden_tool",
                    "passed": False,
                    "message": f"Found forbidden tool: {forbidden}"
                })

        results.append(validation)

    return results
