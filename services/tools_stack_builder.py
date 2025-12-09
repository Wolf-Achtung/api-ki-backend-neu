# -*- coding: utf-8 -*-
"""
Sprint B3-C: Adaptive Tool Stack Builder

Builds personalized AI tool stacks based on profile.

Features:
- Branch-specific stack definitions
- Adaptive selection based on size, risk, funding
- Category-balanced recommendations
- Setup hints and integration guides

Version: 1.0.0 (Sprint B3)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

TOOLS_STACK_ENABLED = os.getenv("TOOLS_STACK_ENABLED", "1").lower() in ("1", "true", "yes")
TOOLS_STACK_SIZE = int(os.getenv("TOOLS_STACK_SIZE", "12"))
TOOLS_STACK_MIN_CATEGORIES = int(os.getenv("TOOLS_STACK_MIN_CATEGORIES", "4"))

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class StackCategory:
    """A category within a tool stack."""
    name: str
    description: str
    tools: List[str] = field(default_factory=list)
    priority: int = 1  # 1=high, 2=medium, 3=optional
    icon: str = "🔧"


@dataclass
class ToolStackItem:
    """A single tool in the stack."""
    tool_name: str
    tool_id: str
    category: str
    fit_score: float
    fit_level: str
    description: str
    setup_hint: str
    is_primary: bool = False  # Primary tool for category


@dataclass
class AdaptiveToolStack:
    """Complete adaptive tool stack for a profile."""
    branch: str
    size: str
    stack_name: str
    stack_description: str
    categories: List[StackCategory] = field(default_factory=list)
    tools: List[ToolStackItem] = field(default_factory=list)
    total_tools: int = 0
    integration_hints: List[str] = field(default_factory=list)
    estimated_setup_days: int = 0

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["categories"] = [asdict(c) for c in self.categories]
        result["tools"] = [asdict(t) for t in self.tools]
        return result


# =============================================================================
# BRANCH STACK DEFINITIONS
# =============================================================================

# Stack definitions per branch - categories and recommended tools
BRANCH_STACK_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "beratung": {
        "stack_name": "Consulting Intelligence Stack",
        "stack_description": "KI-Tools für effiziente Beratung und Wissensvermittlung",
        "categories": [
            {
                "name": "Research & Analysis",
                "description": "Marktforschung und Wettbewerbsanalyse",
                "tools": ["Perplexity AI", "Claude", "ChatGPT", "Consensus"],
                "priority": 1,
                "icon": "🔍",
            },
            {
                "name": "Content & Reports",
                "description": "Berichte, Präsentationen, Dokumente",
                "tools": ["ChatGPT", "Claude", "Gamma", "Beautiful.ai", "Notion AI"],
                "priority": 1,
                "icon": "📄",
            },
            {
                "name": "Meeting & Collaboration",
                "description": "Meetings dokumentieren und zusammenarbeiten",
                "tools": ["Fireflies.ai", "Otter.ai", "Loom", "Miro"],
                "priority": 2,
                "icon": "🤝",
            },
            {
                "name": "Automation",
                "description": "Prozesse automatisieren",
                "tools": ["Make (Integromat)", "Zapier", "n8n"],
                "priority": 2,
                "icon": "⚡",
            },
        ],
    },
    "it": {
        "stack_name": "Developer Productivity Stack",
        "stack_description": "KI-Tools für moderne Softwareentwicklung",
        "categories": [
            {
                "name": "Code Generation",
                "description": "KI-gestützte Programmierung",
                "tools": ["GitHub Copilot", "Cursor", "Claude", "ChatGPT", "Tabnine"],
                "priority": 1,
                "icon": "💻",
            },
            {
                "name": "DevOps & Quality",
                "description": "CI/CD, Testing, Qualität",
                "tools": ["Snyk", "Great Expectations", "MLflow"],
                "priority": 1,
                "icon": "🔧",
            },
            {
                "name": "Documentation",
                "description": "Technische Dokumentation",
                "tools": ["Notion AI", "ChatGPT", "Gamma"],
                "priority": 2,
                "icon": "📚",
            },
            {
                "name": "Project Management",
                "description": "Aufgaben und Sprints verwalten",
                "tools": ["ClickUp", "Asana", "Monday.com"],
                "priority": 2,
                "icon": "📋",
            },
        ],
    },
    "handel": {
        "stack_name": "E-Commerce Intelligence Stack",
        "stack_description": "KI-Tools für Handel und Kundenservice",
        "categories": [
            {
                "name": "Customer Service",
                "description": "Kundenbetreuung automatisieren",
                "tools": ["Intercom", "Zendesk", "Freshdesk", "Drift"],
                "priority": 1,
                "icon": "💬",
            },
            {
                "name": "Marketing & Content",
                "description": "Marketing-Inhalte erstellen",
                "tools": ["Jasper", "Copy.ai", "Canva", "Buffer"],
                "priority": 1,
                "icon": "📣",
            },
            {
                "name": "Analytics",
                "description": "Daten analysieren und verstehen",
                "tools": ["Power BI", "Obviously AI", "MonkeyLearn"],
                "priority": 2,
                "icon": "📊",
            },
            {
                "name": "CRM & Sales",
                "description": "Kundenbeziehungen verwalten",
                "tools": ["HubSpot", "Apollo.io", "Mailchimp"],
                "priority": 2,
                "icon": "🎯",
            },
        ],
    },
    "finanzen": {
        "stack_name": "Financial Intelligence Stack",
        "stack_description": "KI-Tools für Finanzdienstleister",
        "categories": [
            {
                "name": "Risk Analytics",
                "description": "Risikobewertung und Analyse",
                "tools": ["Obviously AI", "Power BI", "Tableau"],
                "priority": 1,
                "icon": "📈",
            },
            {
                "name": "Compliance & Governance",
                "description": "Regulatorische Anforderungen erfüllen",
                "tools": ["OneTrust", "ContractPodAi", "Harvey"],
                "priority": 1,
                "icon": "🔒",
            },
            {
                "name": "Reporting",
                "description": "Berichte automatisieren",
                "tools": ["Power BI", "ChatGPT", "Claude"],
                "priority": 2,
                "icon": "📑",
            },
            {
                "name": "Customer Communication",
                "description": "Kundenkommunikation",
                "tools": ["HubSpot", "Intercom", "Grammarly"],
                "priority": 2,
                "icon": "✉️",
            },
        ],
    },
    "gesundheit": {
        "stack_name": "Healthcare Intelligence Stack",
        "stack_description": "KI-Tools für Gesundheitswesen",
        "categories": [
            {
                "name": "Documentation",
                "description": "Medizinische Dokumentation",
                "tools": ["Nuance DAX", "Otter.ai", "ChatGPT"],
                "priority": 1,
                "icon": "📋",
            },
            {
                "name": "Compliance & Privacy",
                "description": "DSGVO und Datenschutz",
                "tools": ["OneTrust", "Snyk"],
                "priority": 1,
                "icon": "🔐",
            },
            {
                "name": "Research",
                "description": "Medizinische Recherche",
                "tools": ["Consensus", "Elicit", "Perplexity AI"],
                "priority": 2,
                "icon": "🔬",
            },
            {
                "name": "Communication",
                "description": "Patientenkommunikation",
                "tools": ["Intercom", "Typeform", "Loom"],
                "priority": 2,
                "icon": "💬",
            },
        ],
    },
    "industrie": {
        "stack_name": "Industry 4.0 Stack",
        "stack_description": "KI-Tools für Produktion und Fertigung",
        "categories": [
            {
                "name": "Process Automation",
                "description": "Produktionsprozesse automatisieren",
                "tools": ["Make (Integromat)", "Power Automate", "n8n"],
                "priority": 1,
                "icon": "🏭",
            },
            {
                "name": "Data & Analytics",
                "description": "Produktionsdaten analysieren",
                "tools": ["Power BI", "Tableau", "Obviously AI"],
                "priority": 1,
                "icon": "📊",
            },
            {
                "name": "Quality Management",
                "description": "Qualitätskontrolle",
                "tools": ["Great Expectations", "MLflow"],
                "priority": 2,
                "icon": "✅",
            },
            {
                "name": "Documentation",
                "description": "Technische Dokumentation",
                "tools": ["Notion AI", "ChatGPT", "Loom"],
                "priority": 2,
                "icon": "📚",
            },
        ],
    },
    "bildung": {
        "stack_name": "EdTech Intelligence Stack",
        "stack_description": "KI-Tools für Bildung und Training",
        "categories": [
            {
                "name": "Content Creation",
                "description": "Lerninhalte erstellen",
                "tools": ["ChatGPT", "Claude", "Canva", "Gamma"],
                "priority": 1,
                "icon": "📝",
            },
            {
                "name": "Video & Presentation",
                "description": "Videos und Präsentationen",
                "tools": ["Loom", "Synthesia", "Beautiful.ai", "Descript"],
                "priority": 1,
                "icon": "🎬",
            },
            {
                "name": "Assessment",
                "description": "Tests und Umfragen",
                "tools": ["Typeform", "Tally", "Google Forms"],
                "priority": 2,
                "icon": "📋",
            },
            {
                "name": "Collaboration",
                "description": "Zusammenarbeit",
                "tools": ["Notion AI", "Miro", "ClickUp"],
                "priority": 2,
                "icon": "🤝",
            },
        ],
    },
    "marketing": {
        "stack_name": "Marketing Intelligence Stack",
        "stack_description": "KI-Tools für Marketing und Werbung",
        "categories": [
            {
                "name": "Content Generation",
                "description": "Marketing-Inhalte erstellen",
                "tools": ["Jasper", "Copy.ai", "ChatGPT", "Claude"],
                "priority": 1,
                "icon": "✍️",
            },
            {
                "name": "Design & Visual",
                "description": "Visuelle Inhalte",
                "tools": ["Canva", "Midjourney", "DALL-E", "Figma"],
                "priority": 1,
                "icon": "🎨",
            },
            {
                "name": "Social Media",
                "description": "Social Media Management",
                "tools": ["Buffer", "Hootsuite", "Sprout Social"],
                "priority": 2,
                "icon": "📱",
            },
            {
                "name": "SEO & Analytics",
                "description": "SEO und Analyse",
                "tools": ["Semrush", "Ahrefs", "Clearscope"],
                "priority": 2,
                "icon": "📈",
            },
        ],
    },
    "bauwesen_architektur": {
        "stack_name": "Construction Intelligence Stack",
        "stack_description": "KI-Tools für Bau und Architektur",
        "categories": [
            {
                "name": "Project Management",
                "description": "Bauprojekte verwalten",
                "tools": ["Procore", "PlanRadar", "ClickUp"],
                "priority": 1,
                "icon": "🏗️",
            },
            {
                "name": "Documentation",
                "description": "Baudokumentation",
                "tools": ["ChatGPT", "Notion AI", "Fireflies.ai"],
                "priority": 1,
                "icon": "📋",
            },
            {
                "name": "BIM & Design",
                "description": "BIM und Planung",
                "tools": ["BIM 360", "Figma", "Canva"],
                "priority": 2,
                "icon": "📐",
            },
            {
                "name": "Communication",
                "description": "Teamkommunikation",
                "tools": ["Loom", "Slack", "Microsoft Teams"],
                "priority": 2,
                "icon": "💬",
            },
        ],
    },
    "verwaltung": {
        "stack_name": "GovTech Intelligence Stack",
        "stack_description": "KI-Tools für öffentliche Verwaltung",
        "categories": [
            {
                "name": "Citizen Services",
                "description": "Bürgerservices",
                "tools": ["Intercom", "Zendesk", "Typeform"],
                "priority": 1,
                "icon": "👥",
            },
            {
                "name": "Document Processing",
                "description": "Dokumentenverarbeitung",
                "tools": ["ChatGPT", "Claude", "Notion AI"],
                "priority": 1,
                "icon": "📄",
            },
            {
                "name": "Compliance & Privacy",
                "description": "Datenschutz und Compliance",
                "tools": ["OneTrust", "Snyk"],
                "priority": 1,
                "icon": "🔒",
            },
            {
                "name": "Process Automation",
                "description": "Prozessautomatisierung",
                "tools": ["Power Automate", "Make (Integromat)", "n8n"],
                "priority": 2,
                "icon": "⚡",
            },
        ],
    },
    "transport_logistik": {
        "stack_name": "Logistics Intelligence Stack",
        "stack_description": "KI-Tools für Transport und Logistik",
        "categories": [
            {
                "name": "Route Optimization",
                "description": "Routenplanung",
                "tools": ["Route4Me", "Project44"],
                "priority": 1,
                "icon": "🗺️",
            },
            {
                "name": "Supply Chain",
                "description": "Lieferkettenmanagement",
                "tools": ["Project44", "Flexport"],
                "priority": 1,
                "icon": "📦",
            },
            {
                "name": "Analytics",
                "description": "Logistik-Analytics",
                "tools": ["Power BI", "Tableau", "Obviously AI"],
                "priority": 2,
                "icon": "📊",
            },
            {
                "name": "Communication",
                "description": "Teamkommunikation",
                "tools": ["Slack", "Loom", "Fireflies.ai"],
                "priority": 2,
                "icon": "💬",
            },
        ],
    },
}

# Default stack for unknown branches
DEFAULT_STACK_DEFINITION: Dict[str, Any] = {
    "stack_name": "Universal AI Stack",
    "stack_description": "Vielseitige KI-Tools für jede Branche",
    "categories": [
        {
            "name": "Content & Writing",
            "description": "Texte und Inhalte erstellen",
            "tools": ["ChatGPT", "Claude", "Jasper"],
            "priority": 1,
            "icon": "✍️",
        },
        {
            "name": "Automation",
            "description": "Prozesse automatisieren",
            "tools": ["Make (Integromat)", "Zapier", "n8n"],
            "priority": 1,
            "icon": "⚡",
        },
        {
            "name": "Analytics",
            "description": "Daten analysieren",
            "tools": ["Power BI", "Obviously AI"],
            "priority": 2,
            "icon": "📊",
        },
        {
            "name": "Collaboration",
            "description": "Zusammenarbeiten",
            "tools": ["Notion AI", "ClickUp", "Loom"],
            "priority": 2,
            "icon": "🤝",
        },
    ],
}


# =============================================================================
# SIZE ADJUSTMENTS
# =============================================================================

SIZE_STACK_ADJUSTMENTS: Dict[str, Dict[str, Any]] = {
    "solo": {
        "max_tools": 8,
        "max_categories": 4,
        "prefer_freemium": True,
        "exclude_enterprise": True,
        "setup_multiplier": 0.5,
    },
    "team": {
        "max_tools": 12,
        "max_categories": 5,
        "prefer_freemium": False,
        "exclude_enterprise": False,
        "setup_multiplier": 1.0,
    },
    "kmu": {
        "max_tools": 15,
        "max_categories": 6,
        "prefer_freemium": False,
        "exclude_enterprise": False,
        "setup_multiplier": 1.5,
    },
}


# =============================================================================
# STACK BUILDER FUNCTIONS
# =============================================================================

def _get_stack_definition(branch: str) -> Dict[str, Any]:
    """Get stack definition for branch."""
    return BRANCH_STACK_DEFINITIONS.get(branch, DEFAULT_STACK_DEFINITION)


def _get_size_adjustments(size: str) -> Dict[str, Any]:
    """Get size-specific adjustments."""
    return SIZE_STACK_ADJUSTMENTS.get(size, SIZE_STACK_ADJUSTMENTS["team"])


def _filter_tools_for_size(
    tools: List[str],
    size: str,
    max_per_category: int = 3,
) -> List[str]:
    """Filter and limit tools based on size constraints."""
    from services.tools_embedding_engine import get_tool_by_name

    adjustments = _get_size_adjustments(size)
    filtered = []

    for tool_name in tools:
        if len(filtered) >= max_per_category:
            break

        tool = get_tool_by_name(tool_name)
        if not tool:
            continue

        # Check enterprise exclusion
        if adjustments.get("exclude_enterprise"):
            categories = tool.get("categories", [])
            if "enterprise" in categories:
                continue

        # Prefer freemium for solo
        pricing = tool.get("pricing", "")
        if adjustments.get("prefer_freemium") and pricing == "paid":
            # Still include but lower priority
            if len(filtered) < max_per_category - 1:
                filtered.append(tool_name)
        else:
            filtered.append(tool_name)

    return filtered[:max_per_category]


def _calculate_setup_days(
    tools: List[ToolStackItem],
    size: str,
) -> int:
    """Estimate setup days for the stack."""
    from services.tools_embedding_engine import get_tool_by_name

    adjustments = _get_size_adjustments(size)
    multiplier = adjustments.get("setup_multiplier", 1.0)

    total_days = 0
    for tool_item in tools:
        tool = get_tool_by_name(tool_item.tool_name)
        if tool:
            complexity = tool.get("complexity", "medium")
            if complexity == "low":
                total_days += 0.5
            elif complexity == "medium":
                total_days += 1.5
            else:
                total_days += 3

    return max(1, int(total_days * multiplier))


def _generate_integration_hints(
    tools: List[ToolStackItem],
    branch: str,
    size: str,
) -> List[str]:
    """Generate integration hints for the stack."""
    hints = []

    # Count automations
    automation_tools = [t for t in tools if "automation" in t.category.lower()]
    if automation_tools:
        hints.append(f"💡 Verbinden Sie {automation_tools[0].tool_name} als zentrale Automatisierungsplattform")

    # Size-specific hints
    if size == "solo":
        hints.append("🎯 Starten Sie mit 2-3 Core-Tools und erweitern Sie bei Bedarf")
        hints.append("💰 Nutzen Sie kostenlose Tiers für den Einstieg")
    elif size == "team":
        hints.append("👥 Richten Sie Team-Workspaces für alle Tools ein")
        hints.append("📋 Definieren Sie klare Zuständigkeiten pro Tool")
    else:  # kmu
        hints.append("🔄 Planen Sie eine schrittweise Einführung über 2-3 Monate")
        hints.append("📊 Messen Sie ROI pro Tool nach 30 Tagen")

    # Branch-specific hints
    branch_hints = {
        "beratung": "📝 Integrieren Sie Meeting-Tools mit Dokumentation für nahtlose Protokolle",
        "it": "🔧 Verbinden Sie Copilot mit Ihrem bestehenden IDE-Setup",
        "handel": "🛒 Verknüpfen Sie CRM mit Customer Service für 360°-Kundensicht",
        "finanzen": "🔒 Priorisieren Sie Compliance-Tools vor der Einführung",
        "verwaltung": "📋 Starten Sie mit DSGVO-konformen Tools für Bürgerdaten",
    }
    if branch in branch_hints:
        hints.append(branch_hints[branch])

    return hints


def generate_adaptive_stack(
    branch: str,
    size: str,
    usecases: List[str] = None,
    risk_level: str = "limited",
    funding_focus: List[str] = None,
    top_k: int = None,
) -> AdaptiveToolStack:
    """
    Generate adaptive tool stack for a profile.

    Args:
        branch: Industry branch
        size: Company size (solo/team/kmu)
        usecases: Use case descriptions
        risk_level: AI-Act risk level
        funding_focus: Funding focus areas
        top_k: Override max tools

    Returns:
        AdaptiveToolStack with categorized tools
    """
    from services.tools_fit_engine import calculate_tool_fit_score
    from services.tools_embedding_engine import get_tool_by_name

    # Get definitions
    stack_def = _get_stack_definition(branch)
    adjustments = _get_size_adjustments(size)

    max_tools = top_k or adjustments.get("max_tools", TOOLS_STACK_SIZE)
    max_categories = adjustments.get("max_categories", 5)

    # Build categories
    categories = []
    all_tools: List[ToolStackItem] = []
    tools_added = set()

    for cat_def in stack_def.get("categories", [])[:max_categories]:
        cat_tools = _filter_tools_for_size(
            cat_def.get("tools", []),
            size,
            max_per_category=3,
        )

        category = StackCategory(
            name=cat_def.get("name", ""),
            description=cat_def.get("description", ""),
            tools=cat_tools,
            priority=cat_def.get("priority", 2),
            icon=cat_def.get("icon", "🔧"),
        )
        categories.append(category)

        # Add tool items
        is_first = True
        for tool_name in cat_tools:
            if tool_name in tools_added:
                continue
            if len(all_tools) >= max_tools:
                break

            tool = get_tool_by_name(tool_name)
            if not tool:
                continue

            # Calculate fit score
            fit_score = calculate_tool_fit_score(
                tool=tool,
                branch=branch,
                size=size,
                usecases=usecases or [],
                risk_level=risk_level,
                funding_focus=funding_focus,
            )

            tool_item = ToolStackItem(
                tool_name=tool_name,
                tool_id=tool.get("id", ""),
                category=category.name,
                fit_score=fit_score.total_score,
                fit_level=fit_score.fit_level,
                description=tool.get("description", ""),
                setup_hint=fit_score.setup_hint,
                is_primary=is_first,
            )

            all_tools.append(tool_item)
            tools_added.add(tool_name)
            is_first = False

    # Sort tools by fit score
    all_tools.sort(key=lambda x: x.fit_score, reverse=True)

    # Generate hints
    integration_hints = _generate_integration_hints(all_tools, branch, size)

    # Calculate setup time
    setup_days = _calculate_setup_days(all_tools, size)

    return AdaptiveToolStack(
        branch=branch,
        size=size,
        stack_name=stack_def.get("stack_name", "AI Tool Stack"),
        stack_description=stack_def.get("stack_description", ""),
        categories=categories,
        tools=all_tools,
        total_tools=len(all_tools),
        integration_hints=integration_hints,
        estimated_setup_days=setup_days,
    )


def get_stack_summary(stack: AdaptiveToolStack) -> Dict[str, Any]:
    """Get summary statistics for a stack."""
    high_fit = sum(1 for t in stack.tools if t.fit_level == "high")
    medium_fit = sum(1 for t in stack.tools if t.fit_level == "medium")

    return {
        "stack_name": stack.stack_name,
        "total_tools": stack.total_tools,
        "categories": len(stack.categories),
        "high_fit_tools": high_fit,
        "medium_fit_tools": medium_fit,
        "setup_days": stack.estimated_setup_days,
        "primary_tools": [t.tool_name for t in stack.tools if t.is_primary],
    }


def compare_stacks(
    stack1: AdaptiveToolStack,
    stack2: AdaptiveToolStack,
) -> Dict[str, Any]:
    """Compare two tool stacks."""
    tools1 = set(t.tool_name for t in stack1.tools)
    tools2 = set(t.tool_name for t in stack2.tools)

    return {
        "common_tools": list(tools1 & tools2),
        "only_in_first": list(tools1 - tools2),
        "only_in_second": list(tools2 - tools1),
        "overlap_percentage": len(tools1 & tools2) / max(len(tools1 | tools2), 1) * 100,
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[B3] Tool Stack Builder loaded - %d branch definitions, stack_size=%d",
    len(BRANCH_STACK_DEFINITIONS),
    TOOLS_STACK_SIZE,
)
