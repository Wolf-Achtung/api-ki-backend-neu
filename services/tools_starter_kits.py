# -*- coding: utf-8 -*-
"""
Sprint B2.2: Starter-Kit Generator

Generates curated starter kits per segment (size × branch × maturity).
Each starter kit contains:
- Recommended tools for getting started
- Matching funding programs
- Quick-start checklist
- Estimated timeline

Version: 1.0.0 (Sprint B2.2)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from ._normalize import _briefing_to_dict

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

STARTER_KITS_ENABLED = os.environ.get("STARTER_KITS_ENABLED", "1") == "1"
STARTER_KIT_MAX_TOOLS = int(os.environ.get("STARTER_KIT_MAX_TOOLS", "5"))
STARTER_KIT_MAX_FUNDING = int(os.environ.get("STARTER_KIT_MAX_FUNDING", "3"))


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class StarterKitTool:
    """A tool in a starter kit."""
    name: str
    category: str
    purpose: str
    priority: int  # 1 = essential, 2 = recommended, 3 = optional
    estimated_setup_days: int = 1
    funding_eligible: bool = False


@dataclass
class StarterKitFunding:
    """A funding program in a starter kit."""
    program_id: str
    name: str
    provider: str
    max_amount: str
    fit_reason: str
    application_complexity: str = "medium"


@dataclass
class StarterKitChecklist:
    """Checklist item for starter kit."""
    step: int
    title: str
    description: str
    category: str  # setup, governance, funding, training
    estimated_hours: float = 2.0


@dataclass
class StarterKit:
    """Complete starter kit for a segment."""
    kit_id: str
    kit_name: str
    segment_label: str  # e.g., "Solo/Beratung/Einsteiger"
    tools: List[StarterKitTool] = field(default_factory=list)
    funding: List[StarterKitFunding] = field(default_factory=list)
    checklist: List[StarterKitChecklist] = field(default_factory=list)
    estimated_total_days: int = 30
    estimated_investment: str = ""
    potential_funding: str = ""
    quick_win_count: int = 3
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kit_id": self.kit_id,
            "kit_name": self.kit_name,
            "segment_label": self.segment_label,
            "tools": [asdict(t) for t in self.tools],
            "funding": [asdict(f) for f in self.funding],
            "checklist": [asdict(c) for c in self.checklist],
            "estimated_total_days": self.estimated_total_days,
            "estimated_investment": self.estimated_investment,
            "potential_funding": self.potential_funding,
            "quick_win_count": self.quick_win_count,
            "description": self.description,
            "created_at": self.created_at,
        }


# =============================================================================
# STARTER KIT TEMPLATES
# =============================================================================

# Base tool configurations per size
TOOL_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "solo": [
        {
            "name": "KI-Assistent",
            "category": "KI-API",
            "purpose": "Alltägliche Textarbeit, Entwürfe, Recherche",
            "priority": 1,
            "estimated_setup_days": 1,
            "funding_eligible": True,
        },
        {
            "name": "Workflow-Automation",
            "category": "Workflow-Automation",
            "purpose": "Automatisierung wiederkehrender Aufgaben",
            "priority": 1,
            "estimated_setup_days": 3,
            "funding_eligible": True,
        },
        {
            "name": "Formular-Tool",
            "category": "Fragebogen / Intake",
            "purpose": "Strukturierte Datenerfassung von Kunden",
            "priority": 2,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
        {
            "name": "Wissens-Datenbank",
            "category": "Wissensmanagement / Docs",
            "purpose": "Zentrale Ablage für Templates und Wissen",
            "priority": 2,
            "estimated_setup_days": 2,
            "funding_eligible": False,
        },
    ],
    "team": [
        {
            "name": "Team-KI-Plattform",
            "category": "KI-API",
            "purpose": "Gemeinsame KI-Nutzung im Team",
            "priority": 1,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
        {
            "name": "Kollaborations-Tool",
            "category": "Team-Kommunikation",
            "purpose": "Interne Kommunikation und Abstimmung",
            "priority": 1,
            "estimated_setup_days": 1,
            "funding_eligible": True,
        },
        {
            "name": "Projekt-/Aufgaben-Management",
            "category": "Wissensmanagement / Docs",
            "purpose": "Aufgabenverteilung und Fortschrittsverfolgung",
            "priority": 1,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
        {
            "name": "Workflow-Automation",
            "category": "Workflow-Automation",
            "purpose": "Prozessautomatisierung für Teamabläufe",
            "priority": 2,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "CRM-System",
            "category": "CRM / Sales",
            "purpose": "Kundenverwaltung und Vertrieb",
            "priority": 2,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
    ],
    # PLATIN+++ FIX 4.2: KMU-appropriate tools (not Enterprise-grade)
    "kmu": [
        {
            "name": "KI-Assistenz-Plattform (KMU)",
            "category": "KI-API",
            "purpose": "Unternehmensweite KI-Integration für 11-100 Mitarbeiter",
            "priority": 1,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "Datenqualitäts-Tool",
            "category": "Data Quality",
            "purpose": "Sicherung der Datenqualität für KI",
            "priority": 1,
            "estimated_setup_days": 7,
            "funding_eligible": True,
        },
        {
            "name": "Workflow-Automatisierung",
            "category": "Automation",
            "purpose": "Automatisierung wiederkehrender Geschäftsprozesse",
            "priority": 1,
            "estimated_setup_days": 7,
            "funding_eligible": True,
        },
        {
            "name": "BI/Reporting-System",
            "category": "Monitoring / Observability",
            "purpose": "Monitoring und Analytics",
            "priority": 2,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "KI-Governance-Checkliste",
            "category": "Governance",
            "purpose": "AI Act Compliance und interne Richtlinien",
            "priority": 2,
            "estimated_setup_days": 3,
            "funding_eligible": True,
        },
    ],
}

# Funding templates per size
# Fix-Batch B3: Removed regional funding programs (NRW, BW) that caused false positives
# Only universal BMWK/federal programs are included here.
# Regional programs should be handled by funding_engine_v2 with bundesland filter.
FUNDING_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    # PLATIN+++ FIX 4.1: Removed go-digital (ended Dec 2024) and Digital Jetzt (ended Dec 2023)
    "solo": [
        {
            "program_id": "unternehmensberater_foerderung",
            "name": "Förderung unternehmerischen Know-hows",
            "provider": "BAFA",
            "max_amount": "4.000 €",
            "fit_reason": "Beratungsförderung für Gründer und Selbstständige (bundesweit)",
            "application_complexity": "low",
        },
        {
            "program_id": "eic_accelerator_small",
            "name": "EIC Accelerator (Kleinformat)",
            "provider": "EU",
            "max_amount": "2.500 €",
            "fit_reason": "EU-Innovationsförderung für Solo-Selbstständige",
            "application_complexity": "medium",
        },
    ],
    "team": [
        {
            "program_id": "unternehmensberater_foerderung",
            "name": "Förderung unternehmerischen Know-hows",
            "provider": "BAFA",
            "max_amount": "4.000 €",
            "fit_reason": "Beratungsförderung für kleine Teams (bundesweit)",
            "application_complexity": "low",
        },
        {
            "program_id": "kfw_digitalisierung",
            "name": "KfW-Digitalisierungskredit",
            "provider": "KfW",
            "max_amount": "25.000 €",
            "fit_reason": "Günstige Finanzierung für Digitalisierungsvorhaben",
            "application_complexity": "medium",
        },
    ],
    "kmu": [
        {
            "program_id": "zim",
            "name": "ZIM",
            "provider": "BMWK",
            "max_amount": "380.000 €",
            "fit_reason": "Für größere KI-Innovationsprojekte",
            "application_complexity": "high",
        },
        {
            "program_id": "ai_act_compliance",
            "name": "AI Act Compliance Support",
            "provider": "BMWK",
            "max_amount": "30.000 €",
            "fit_reason": "Beratungsförderung für AI Act Compliance",
            "application_complexity": "medium",
        },
    ],
}

# Checklist templates per size
CHECKLIST_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "solo": [
        {
            "step": 1,
            "title": "KI-Assistent einrichten",
            "description": "Registrierung und erste Testläufe mit einem KI-Assistenten",
            "category": "setup",
            "estimated_hours": 2,
        },
        {
            "step": 2,
            "title": "Erste Automatisierung erstellen",
            "description": "Einen wiederkehrenden Prozess automatisieren (z.B. E-Mail → Task)",
            "category": "setup",
            "estimated_hours": 4,
        },
        {
            "step": 3,
            "title": "Persönliche KI-Richtlinie festlegen",
            "description": "Dokumentieren, welche Daten in KI eingegeben werden dürfen",
            "category": "governance",
            "estimated_hours": 2,
        },
        {
            "step": 4,
            "title": "Förderprogramm prüfen",
            "description": "Passende Förderung identifizieren und Antragsinformationen sammeln",
            "category": "funding",
            "estimated_hours": 3,
        },
        {
            "step": 5,
            "title": "Erste Quick Wins dokumentieren",
            "description": "Zeitersparnis und Qualitätsverbesserungen nach 2 Wochen notieren",
            "category": "training",
            "estimated_hours": 1,
        },
    ],
    "team": [
        {
            "step": 1,
            "title": "Team-Workspace einrichten",
            "description": "Gemeinsamen Workspace und Kommunikationskanal aufsetzen",
            "category": "setup",
            "estimated_hours": 3,
        },
        {
            "step": 2,
            "title": "KI-Zugang für Team bereitstellen",
            "description": "Team-Accounts für KI-Plattform anlegen und Berechtigungen vergeben",
            "category": "setup",
            "estimated_hours": 2,
        },
        {
            "step": 3,
            "title": "Team-Guidelines definieren",
            "description": "Gemeinsame Regeln für KI-Nutzung im Team festlegen",
            "category": "governance",
            "estimated_hours": 4,
        },
        {
            "step": 4,
            "title": "Erste Team-Automatisierung",
            "description": "Einen Team-übergreifenden Workflow automatisieren",
            "category": "setup",
            "estimated_hours": 6,
        },
        {
            "step": 5,
            "title": "Förderantrag vorbereiten",
            "description": "Unterlagen für go-digital oder regionale Programme zusammenstellen",
            "category": "funding",
            "estimated_hours": 8,
        },
        {
            "step": 6,
            "title": "Kurzes Team-Training",
            "description": "30-minütiges Onboarding für alle Team-Mitglieder",
            "category": "training",
            "estimated_hours": 2,
        },
    ],
    "kmu": [
        {
            "step": 1,
            "title": "KI-Strategie skizzieren",
            "description": "Grobe KI-Roadmap mit Prioritäten für die nächsten 12 Monate",
            "category": "governance",
            "estimated_hours": 8,
        },
        {
            "step": 2,
            "title": "Datenlandschaft analysieren",
            "description": "Bestandsaufnahme vorhandener Datenquellen und -qualität",
            "category": "setup",
            "estimated_hours": 16,
        },
        {
            "step": 3,
            "title": "Pilotprojekt definieren",
            "description": "Konkretes KI-Pilotprojekt mit messbaren Zielen festlegen",
            "category": "setup",
            "estimated_hours": 8,
        },
        {
            "step": 4,
            "title": "Governance-Framework etablieren",
            "description": "KI-Richtlinien, Rollen und Verantwortlichkeiten dokumentieren",
            "category": "governance",
            "estimated_hours": 12,
        },
        {
            "step": 5,
            "title": "AI Act Compliance prüfen",
            "description": "Risikoeinstufung und Compliance-Anforderungen klären",
            "category": "governance",
            "estimated_hours": 8,
        },
        {
            "step": 6,
            "title": "ZIM-Antrag vorbereiten",
            "description": "Innovationsprojekt für ZIM-Förderung strukturieren",
            "category": "funding",
            "estimated_hours": 24,
        },
        {
            "step": 7,
            "title": "Schulungskonzept erstellen",
            "description": "Rollenspezifische Trainings für Fachbereiche planen",
            "category": "training",
            "estimated_hours": 8,
        },
    ],
}

# =============================================================================
# KIS-1132: EXPERT TOOL TEMPLATES (overrides for expert users)
# =============================================================================

TOOL_TEMPLATES_EXPERT: Dict[str, List[Dict[str, Any]]] = {
    "solo": [
        {
            "name": "LLM-API-Zugang (Anthropic/OpenAI)",
            "category": "KI-API",
            "purpose": "Direkte API-Integration für eigene Pipelines",
            "priority": 1,
            "estimated_setup_days": 1,
            "funding_eligible": True,
        },
        {
            "name": "LLM-Monitoring (Langfuse)",
            "category": "Monitoring / Observability",
            "purpose": "Prompt-Tracking, Cost-Monitoring, Evaluierung",
            "priority": 1,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
        {
            "name": "Prompt-Versionierung (Git/Langfuse)",
            "category": "DevOps",
            "purpose": "Versionskontrolle und A/B-Testing für Prompts",
            "priority": 1,
            "estimated_setup_days": 1,
            "funding_eligible": False,
        },
        {
            "name": "Evaluierungs-Framework (Promptfoo)",
            "category": "Qualitätssicherung",
            "purpose": "Automatisierte Qualitätsprüfung von LLM-Outputs",
            "priority": 2,
            "estimated_setup_days": 3,
            "funding_eligible": True,
        },
    ],
    "team": [
        {
            "name": "LLM-Gateway (LiteLLM/Portkey)",
            "category": "KI-API",
            "purpose": "Zentrales API-Management, Multi-Provider-Routing",
            "priority": 1,
            "estimated_setup_days": 3,
            "funding_eligible": True,
        },
        {
            "name": "LLM-Observability (Langfuse/Helicone)",
            "category": "Monitoring / Observability",
            "purpose": "Team-weites Monitoring, Cost-Tracking, Evaluierung",
            "priority": 1,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
        {
            "name": "KI-Governance-Framework",
            "category": "Governance",
            "purpose": "AI Act Compliance, Richtlinien, Dokumentation",
            "priority": 1,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "CI/CD für Prompts",
            "category": "DevOps",
            "purpose": "Automatisierte Tests und Deployment für Prompt-Änderungen",
            "priority": 2,
            "estimated_setup_days": 3,
            "funding_eligible": False,
        },
    ],
    "kmu": [
        {
            "name": "LLM-Operations-Plattform",
            "category": "KI-API",
            "purpose": "Enterprise-weites LLM-Management mit Governance",
            "priority": 1,
            "estimated_setup_days": 7,
            "funding_eligible": True,
        },
        {
            "name": "Monitoring & Evaluierung",
            "category": "Monitoring / Observability",
            "purpose": "Produktionsreife Observability für alle LLM-Aufrufe",
            "priority": 1,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "KI-Governance & Compliance",
            "category": "Governance",
            "purpose": "AI Act Compliance, Risikomanagement, Audit-Trail",
            "priority": 1,
            "estimated_setup_days": 7,
            "funding_eligible": True,
        },
        {
            "name": "Evaluierungs-Pipeline",
            "category": "Qualitätssicherung",
            "purpose": "Automatisierte Quality Gates und Regression Testing",
            "priority": 1,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "Cost-Management & Budgetierung",
            "category": "FinOps",
            "purpose": "Budget-Alerts, Cost-per-Output-Tracking, Optimierung",
            "priority": 2,
            "estimated_setup_days": 3,
            "funding_eligible": False,
        },
    ],
}

KIT_DESCRIPTIONS_EXPERT: Dict[str, str] = {
    "solo": (
        "Operations-Kit für KI-Profis: Monitoring, Prompt-Versionierung und "
        "Evaluierung für Ihre bestehenden LLM-Pipelines. Fokus auf Qualität, "
        "Kosten und Compliance – nicht auf Grundlagen."
    ),
    "team": (
        "Team-Operations-Kit: Zentrales API-Management, Team-weites Monitoring "
        "und Governance-Framework für produktive LLM-Nutzung. "
        "Integration: 1-2 Wochen."
    ),
    "kmu": (
        "Enterprise-LLM-Operations: Skalierbare Infrastruktur mit Monitoring, "
        "Governance und automatisierten Quality Gates für unternehmensweite "
        "KI-Nutzung. Integration: 2-4 Wochen."
    ),
}

# Size-specific kit descriptions
KIT_DESCRIPTIONS: Dict[str, str] = {
    "solo": (
        "Kompakter Einstieg für Einzelunternehmer: Mit diesem Starter-Kit "
        "automatisieren Sie erste Aufgaben, nutzen KI für Textarbeit und "
        "sichern sich passende Fördermittel – alles mit überschaubarem Aufwand."
    ),
    "team": (
        "Team-KI-Stack für effektive Zusammenarbeit: Dieses Kit ermöglicht "
        "gemeinsame KI-Nutzung, automatisierte Workflows und strukturierte "
        "Kommunikation – plus Zugang zu attraktiven Förderprogrammen."
    ),
    # PLATIN+++ FIX 4.2: KMU-appropriate description (not Enterprise)
    "kmu": (
        "Wachstums-Kit für KMU: Strukturiertes Paket für Unternehmen mit 11-100 "
        "Mitarbeitern – mit Fokus auf Datenqualität, Prozessautomatisierung und "
        "schrittweise KI-Integration inklusive passender Förderprogramme."
    ),
}


# =============================================================================
# GENERATOR
# =============================================================================

def generate_starter_kit(
    profile_context: Dict[str, Any],
    lang: str = "de",
) -> StarterKit:
    """
    Generate a starter kit for a profile.

    Args:
        profile_context: Profile data (briefing or sections)
        lang: Language code

    Returns:
        StarterKit object
    """
    if not STARTER_KITS_ENABLED:
        return StarterKit(
            kit_id="disabled",
            kit_name="Starter-Kit deaktiviert",
            segment_label="N/A",
        )

    ctx = _briefing_to_dict(profile_context)

    # Extract segment
    size_label = _normalize_size(ctx.get("unternehmensgroesse") or ctx.get("groesse") or "team")
    branch_group = (ctx.get("branche") or ctx.get("branche_label") or "Allgemein").capitalize()
    maturity = int(ctx.get("maturity_level", 2) or 2)

    # KIS-1132: Use expertise_level if available (injected by gpt_analyze.py)
    expertise_level = str(ctx.get("expertise_level", "") or "").lower()

    maturity_label = "Einsteiger" if maturity <= 2 else "Fortgeschritten" if maturity <= 3 else "Erfahren"
    # KIS-1132: Override maturity label with expertise label if available
    if expertise_level == "expert":
        maturity_label = "KI-Experte"
    elif expertise_level == "intermediate":
        maturity_label = "KI-Anwender"
    segment_label = f"{size_label.upper()}/{branch_group}/{maturity_label}"

    kit_id = f"{size_label}_{branch_group.lower()[:4]}_{maturity}"
    kit_name = _generate_kit_name(size_label, branch_group, lang, expertise_level=expertise_level)

    # KIS-1132: Get templates based on expertise level
    if expertise_level == "expert":
        tool_templates = TOOL_TEMPLATES_EXPERT.get(size_label, TOOL_TEMPLATES_EXPERT["solo"])
    else:
        tool_templates = TOOL_TEMPLATES.get(size_label, TOOL_TEMPLATES["team"])
    funding_templates = FUNDING_TEMPLATES.get(size_label, FUNDING_TEMPLATES["team"])
    checklist_templates = CHECKLIST_TEMPLATES.get(size_label, CHECKLIST_TEMPLATES["team"])

    # Build tools list
    tools = [
        StarterKitTool(**t)
        for t in tool_templates[:STARTER_KIT_MAX_TOOLS]
    ]

    # Build funding list
    funding = [
        StarterKitFunding(**f)
        for f in funding_templates[:STARTER_KIT_MAX_FUNDING]
    ]

    # Build checklist
    checklist = [
        StarterKitChecklist(**c)
        for c in checklist_templates
    ]

    # Calculate estimates
    total_setup_days = sum(t.estimated_setup_days for t in tools)
    total_checklist_hours = sum(c.estimated_hours for c in checklist)
    estimated_total_days = total_setup_days + int(total_checklist_hours / 8)

    # Estimate investment
    estimated_investment = _estimate_investment(size_label)

    # Calculate potential funding
    potential_funding = _calculate_potential_funding(funding)

    # Quick win count
    quick_win_count = min(3, len([t for t in tools if t.priority == 1]))

    return StarterKit(
        kit_id=kit_id,
        kit_name=kit_name,
        segment_label=segment_label,
        tools=tools,
        funding=funding,
        checklist=checklist,
        estimated_total_days=estimated_total_days,
        estimated_investment=estimated_investment,
        potential_funding=potential_funding,
        quick_win_count=quick_win_count,
        description=(KIT_DESCRIPTIONS_EXPERT if expertise_level == "expert" else KIT_DESCRIPTIONS).get(size_label, ""),
    )


def _normalize_size(size_raw: str) -> str:
    """Normalize company size to solo/team/kmu."""
    size_lower = size_raw.lower()
    if "solo" in size_lower or "1" in size_lower or "freiberuf" in size_lower:
        return "solo"
    elif "team" in size_lower or "klein" in size_lower or "2-10" in size_lower:
        return "team"
    return "kmu"


def _generate_kit_name(size_label: str, branch: str, lang: str, expertise_level: str = "") -> str:
    """Generate human-readable kit name."""
    # KIS-1132: Expertise-aware kit names
    if expertise_level == "expert":
        size_names = {
            "solo": "KI-Operations",
            "team": "Team-LLM-Ops",
            "kmu": "Enterprise-LLM-Ops",
        }
    else:
        size_names = {
            "solo": "Solo-Starter",
            "team": "Team-Boost",
            "kmu": "KMU-Enterprise",
        }
    base_name = size_names.get(size_label, "Starter")
    return f"{base_name} Kit für {branch}"


def _estimate_investment(size_label: str) -> str:
    """Estimate typical investment range."""
    ranges = {
        "solo": "500–2.000 €/Jahr",
        "team": "2.000–10.000 €/Jahr",
        "kmu": "10.000–50.000 €/Jahr",
    }
    return ranges.get(size_label, "variabel")


def _calculate_potential_funding(funding: List[StarterKitFunding]) -> str:
    """Calculate total potential funding from programs."""
    total = 0
    for f in funding:
        try:
            amount_str = f.max_amount.replace(".", "").replace("€", "").replace("EUR", "").strip()
            amount_str = amount_str.split()[0] if amount_str else "0"
            total += int(amount_str) if amount_str.isdigit() else 0
        except (ValueError, IndexError):
            pass

    if total >= 100_000:
        return f"bis zu {total:,.0f} €".replace(",", ".")
    elif total > 0:
        return f"bis zu {total:,.0f} €".replace(",", ".")
    return ""


# =============================================================================
# HTML OUTPUT
# =============================================================================

def generate_starter_kit_html(kit: StarterKit, lang: str = "de") -> str:
    """
    Generate HTML output for a starter kit.

    Args:
        kit: StarterKit object
        lang: Language code

    Returns:
        HTML string
    """
    if lang == "en":
        title = "Your AI Starter Kit"
        tools_label = "Recommended Tools"
        funding_label = "Funding Programs"
        checklist_label = "Quick-Start Checklist"
        summary_label = "Summary"
    else:
        title = "Ihr KI-Starter-Kit"
        tools_label = "Empfohlene Tools"
        funding_label = "Förderprogramme"
        checklist_label = "Quick-Start-Checkliste"
        summary_label = "Zusammenfassung"

    # Tools section
    tools_html = ""
    for t in kit.tools:
        priority_badge = {
            1: '<span style="color:#22c55e;font-size:9px;font-weight:600;">ESSENTIAL</span>',
            2: '<span style="color:#f59e0b;font-size:9px;font-weight:600;">EMPFOHLEN</span>',
            3: '<span style="color:#6b7280;font-size:9px;font-weight:600;">OPTIONAL</span>',
        }.get(t.priority, "")

        tools_html += f"""
        <div class="tool-card" style="padding:10px;background:#f9fafb;border-radius:6px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <strong style="font-size:12px;color:#1f2937;">{t.name}</strong>
                {priority_badge}
            </div>
            <p style="margin:4px 0 0 0;font-size:11px;color:#6b7280;">{t.purpose}</p>
            <div style="margin-top:4px;font-size:10px;color:#9ca3af;">
                Setup: ~{t.estimated_setup_days} Tag(e) | {t.category}
            </div>
        </div>
        """

    # Funding section
    funding_html = ""
    for f in kit.funding:
        complexity_color = {"low": "#22c55e", "medium": "#f59e0b", "high": "#ef4444"}.get(
            f.application_complexity, "#6b7280"
        )
        funding_html += f"""
        <div style="padding:10px;background:#f0f7ff;border-radius:6px;margin-bottom:8px;border-left:3px solid #3b82f6;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <strong style="font-size:12px;color:#1f2937;">{f.name}</strong>
                <span style="font-size:11px;font-weight:600;color:#3b82f6;">{f.max_amount}</span>
            </div>
            <p style="margin:4px 0 0 0;font-size:11px;color:#495057;">{f.fit_reason}</p>
            <div style="margin-top:4px;font-size:10px;color:#9ca3af;">
                {f.provider} | Komplexität: <span style="color:{complexity_color};">{f.application_complexity}</span>
            </div>
        </div>
        """

    # Checklist section
    checklist_html = ""
    for c in kit.checklist:
        category_icons = {
            "setup": "🔧",
            "governance": "📋",
            "funding": "💰",
            "training": "📚",
        }
        icon = category_icons.get(c.category, "✓")
        checklist_html += f"""
        <div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:8px;">
            <span style="font-size:14px;">{icon}</span>
            <div>
                <strong style="font-size:11px;color:#1f2937;">Schritt {c.step}: {c.title}</strong>
                <p style="margin:2px 0 0 0;font-size:10px;color:#6b7280;">{c.description}</p>
            </div>
        </div>
        """

    html = f"""
    <div class="starter-kit" style="margin:24px 0;padding:24px;background:linear-gradient(135deg,#ecfdf5,#f0f9ff);border-radius:16px;border:1px solid #a7f3d0;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <div>
                <h3 style="margin:0;font-size:18px;color:#065f46;display:flex;align-items:center;gap:8px;">
                    <span>🚀</span> {title}
                    <span style="font-size:9px;padding:2px 6px;background:#059669;color:#fff;border-radius:4px;">B2.2</span>
                </h3>
                <p style="margin:4px 0 0 0;font-size:12px;color:#6b7280;">{kit.kit_name} – {kit.segment_label}</p>
            </div>
            <div style="text-align:right;">
                <div style="font-size:20px;font-weight:700;color:#059669;">{kit.estimated_total_days} Tage</div>
                <div style="font-size:10px;color:#6b7280;">Geschätzte Einführungszeit</div>
            </div>
        </div>

        {f'<p style="margin:0 0 16px 0;font-size:12px;color:#374151;line-height:1.5;">{kit.description}</p>' if kit.description else ''}

        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;">
            <!-- Tools Column -->
            <div style="background:#fff;padding:16px;border-radius:12px;">
                <h4 style="margin:0 0 12px 0;font-size:13px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:8px;">
                    🛠️ {tools_label}
                </h4>
                {tools_html}
            </div>

            <!-- Funding Column -->
            <div style="background:#fff;padding:16px;border-radius:12px;">
                <h4 style="margin:0 0 12px 0;font-size:13px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:8px;">
                    💰 {funding_label}
                </h4>
                {funding_html}
                {f'<div style="margin-top:12px;padding:8px;background:#dcfce7;border-radius:6px;text-align:center;"><strong style="color:#166534;font-size:12px;">Förderpotenzial: {kit.potential_funding}</strong></div>' if kit.potential_funding else ''}
            </div>
        </div>

        <!-- Checklist -->
        <div style="margin-top:16px;background:#fff;padding:16px;border-radius:12px;">
            <h4 style="margin:0 0 12px 0;font-size:13px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:8px;">
                ✅ {checklist_label}
            </h4>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:8px;">
                {checklist_html}
            </div>
        </div>

        <!-- Summary -->
        <div style="margin-top:16px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
            <div style="background:#fff;padding:12px;border-radius:8px;text-align:center;">
                <div style="font-size:20px;font-weight:700;color:#059669;">{len(kit.tools)}</div>
                <div style="font-size:10px;color:#6b7280;">Tools im Kit</div>
            </div>
            <div style="background:#fff;padding:12px;border-radius:8px;text-align:center;">
                <div style="font-size:20px;font-weight:700;color:#3b82f6;">{len(kit.funding)}</div>
                <div style="font-size:10px;color:#6b7280;">Förderprogramme</div>
            </div>
            <div style="background:#fff;padding:12px;border-radius:8px;text-align:center;">
                <div style="font-size:20px;font-weight:700;color:#f59e0b;">{kit.quick_win_count}</div>
                <div style="font-size:10px;color:#6b7280;">Quick Wins</div>
            </div>
        </div>

        <p style="margin:16px 0 0 0;font-size:10px;color:#9ca3af;text-align:center;">
            Geschätzte Investition: {kit.estimated_investment} | {summary_label}: {kit.segment_label}
        </p>
    </div>
    """

    return html


def generate_starter_kit_compact_html(kit: StarterKit, lang: str = "de") -> str:
    """
    Generate compact starter kit summary.

    Args:
        kit: StarterKit object
        lang: Language code

    Returns:
        Compact HTML string
    """
    title = "Starter-Kit" if lang == "de" else "Starter Kit"

    tools_list = ", ".join(t.name for t in kit.tools[:3])
    funding_list = ", ".join(f.name for f in kit.funding[:2])

    return f"""
    <div class="starter-kit-compact" style="margin:16px 0;padding:16px;background:#ecfdf5;border-radius:8px;border:1px solid #a7f3d0;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <strong style="font-size:13px;color:#065f46;">🚀 {title}: {kit.kit_name}</strong>
                <p style="margin:4px 0 0 0;font-size:11px;color:#6b7280;">
                    {len(kit.tools)} Tools | {len(kit.funding)} Förderprogramme | ~{kit.estimated_total_days} Tage
                </p>
            </div>
            {f'<div style="font-size:12px;font-weight:600;color:#059669;">{kit.potential_funding}</div>' if kit.potential_funding else ''}
        </div>
        <div style="margin-top:8px;font-size:10px;color:#495057;">
            <strong>Tools:</strong> {tools_list}<br>
            <strong>Förderung:</strong> {funding_list}
        </div>
    </div>
    """


# =============================================================================
# INTEGRATION
# =============================================================================

def inject_starter_kit_into_sections(
    sections: Dict[str, Any],
    briefing: Optional[Dict[str, Any]] = None,
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Inject starter kit HTML into report sections.

    Args:
        sections: Report sections dict
        briefing: Optional briefing data
        lang: Language code

    Returns:
        Updated sections with STARTER_KIT_HTML
    """
    if not STARTER_KITS_ENABLED:
        sections["STARTER_KIT_HTML"] = ""
        sections["STARTER_KIT_COMPACT_HTML"] = ""
        return sections

    try:
        profile_context = dict(sections)
        if briefing:
            profile_context.update(briefing)

        kit = generate_starter_kit(profile_context, lang)

        # FIX: If the main FOERDERPROGRAMME section exists (with regional programs),
        # replace the starter kit's generic federal funding with a cross-reference
        # to avoid inconsistency (e.g. ZIM 380k vs NRW-specific MID program).
        foerder_main = sections.get("FOERDERPROGRAMME_HTML", "")
        if foerder_main and len(foerder_main) > 100:
            kit.funding = [
                StarterKitFunding(
                    program_id="crossref_foerderprogramme",
                    name="\u2192 siehe Kapitel F\u00f6rdermittel",
                    provider="",
                    max_amount="",
                    fit_reason="Detaillierte F\u00f6rderprogramme (inkl. regionaler Programme) finden Sie im Hauptkapitel F\u00f6rdermittel & Finanzierung.",
                    application_complexity="low",
                ),
            ]
            kit.potential_funding = ""

        sections["STARTER_KIT_HTML"] = generate_starter_kit_html(kit, lang)
        sections["STARTER_KIT_COMPACT_HTML"] = generate_starter_kit_compact_html(kit, lang)

        log.info(f"✅ [B2.2] Generated starter kit: {kit.kit_name}")

    except Exception as e:
        log.error(f"[B2.2] Failed to generate starter kit: {e}")
        sections["STARTER_KIT_HTML"] = ""
        sections["STARTER_KIT_COMPACT_HTML"] = ""

    return sections


def get_starter_kit_api_response(
    briefing: Dict[str, Any],
    lang: str = "de",
) -> Dict[str, Any]:
    """
    Generate API response with starter kit.

    Args:
        briefing: Briefing data
        lang: Language code

    Returns:
        API response dict
    """
    if not STARTER_KITS_ENABLED:
        return {
            "enabled": False,
            "kit": None,
            "message": "Starter kits disabled",
        }

    try:
        kit = generate_starter_kit(briefing, lang)

        return {
            "enabled": True,
            "kit": kit.to_dict(),
            "html": generate_starter_kit_html(kit, lang),
            "compact_html": generate_starter_kit_compact_html(kit, lang),
        }

    except Exception as e:
        log.error(f"[B2.2] API starter kit error: {e}")
        return {
            "enabled": True,
            "kit": None,
            "error": str(e),
        }


# =============================================================================
# MODULE INIT
# =============================================================================

log.info(
    "[B2.2] Starter-Kit Generator loaded - enabled=%s, max_tools=%d",
    STARTER_KITS_ENABLED,
    STARTER_KIT_MAX_TOOLS,
)
