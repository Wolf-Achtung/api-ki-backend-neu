# -*- coding: utf-8 -*-
"""
Sprint B3-D: Tools Workflow Engine

Maps tools to business processes and generates workflow cards
with Quick Wins and implementation roadmaps.

Each workflow card contains:
- Workflow name and description
- 3 recommended tools
- Setup steps with effort estimates
- Risk/effort assessment
- Expected benefits

Version: 3.0.0 (Sprint B3)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

log = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

class WorkflowCategory(str, Enum):
    """Categories for workflow classification."""
    AUTOMATION = "automation"
    ANALYTICS = "analytics"
    COLLABORATION = "collaboration"
    CUSTOMER = "customer"
    CONTENT = "content"
    SECURITY = "security"
    OPERATIONS = "operations"


class EffortLevel(str, Enum):
    """Effort levels for implementation."""
    LOW = "low"  # < 1 week
    MEDIUM = "medium"  # 1-4 weeks
    HIGH = "high"  # > 4 weeks


class RiskLevel(str, Enum):
    """Risk levels for workflow implementation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class SetupStep:
    """A single setup step in a workflow."""
    order: int
    title: str
    description: str
    effort_hours: int
    dependencies: List[str] = field(default_factory=list)


@dataclass
class WorkflowTool:
    """A tool recommendation within a workflow."""
    tool_id: str
    name: str
    role: str  # e.g., "primary", "integration", "reporting"
    setup_time_hours: int
    monthly_cost_eur: float


@dataclass
class WorkflowCard:
    """Complete workflow card with tools and implementation details."""
    id: str
    name: str
    name_en: str
    description: str
    description_en: str
    category: WorkflowCategory
    tools: List[WorkflowTool]
    setup_steps: List[SetupStep]
    effort_level: EffortLevel
    risk_level: RiskLevel
    expected_benefits: List[str]
    expected_benefits_en: List[str]
    time_to_value_weeks: int
    roi_estimate_percent: int
    quick_win: bool = False
    suitable_branches: List[str] = field(default_factory=list)
    suitable_sizes: List[str] = field(default_factory=list)


@dataclass
class WorkflowRecommendation:
    """A workflow recommendation with context."""
    workflow: WorkflowCard
    relevance_score: float
    reason: str
    reason_en: str
    priority: int  # 1=highest


# =============================================================================
# WORKFLOW TEMPLATES DATABASE
# =============================================================================

WORKFLOW_TEMPLATES: Dict[str, Dict] = {
    # ==== AUTOMATION WORKFLOWS ====
    "doc_automation": {
        "name": "Dokumentationsautomation",
        "name_en": "Documentation Automation",
        "description": "Automatisierte Erstellung und Verwaltung von Dokumentation mit KI-Unterstützung",
        "description_en": "Automated creation and management of documentation with AI support",
        "category": WorkflowCategory.AUTOMATION,
        "tool_ids": ["notion", "confluence", "chatgpt"],
        "tool_roles": {
            "notion": "primary",
            "confluence": "alternative",
            "chatgpt": "assistant",
        },
        "setup_steps": [
            {"order": 1, "title": "Template-Struktur erstellen", "title_en": "Create template structure", "effort_hours": 4},
            {"order": 2, "title": "KI-Prompts konfigurieren", "title_en": "Configure AI prompts", "effort_hours": 2},
            {"order": 3, "title": "Automatisierung einrichten", "title_en": "Set up automation", "effort_hours": 4},
        ],
        "effort_level": EffortLevel.LOW,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "60% Zeitersparnis bei Dokumentation",
            "Konsistente Qualität",
            "Bessere Auffindbarkeit",
        ],
        "benefits_en": [
            "60% time savings on documentation",
            "Consistent quality",
            "Better discoverability",
        ],
        "time_to_value_weeks": 2,
        "roi_estimate_percent": 150,
        "quick_win": True,
        "suitable_branches": ["beratung", "it", "marketing", "bildung", "verwaltung"],
        "suitable_sizes": ["solo", "team", "kmu"],
    },
    "reporting_automation": {
        "name": "Reporting-Automation",
        "name_en": "Reporting Automation",
        "description": "Automatische Erstellung von Reports und Dashboards aus Unternehmensdaten",
        "description_en": "Automatic creation of reports and dashboards from business data",
        "category": WorkflowCategory.ANALYTICS,
        "tool_ids": ["power_bi", "tableau", "google_data_studio"],
        "tool_roles": {
            "power_bi": "primary",
            "tableau": "alternative",
            "google_data_studio": "budget",
        },
        "setup_steps": [
            {"order": 1, "title": "Datenquellen anbinden", "title_en": "Connect data sources", "effort_hours": 8},
            {"order": 2, "title": "Dashboard-Templates erstellen", "title_en": "Create dashboard templates", "effort_hours": 12},
            {"order": 3, "title": "Automatische Aktualisierung", "title_en": "Set up auto-refresh", "effort_hours": 4},
        ],
        "effort_level": EffortLevel.MEDIUM,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "80% schnellere Report-Erstellung",
            "Echtzeit-Einblicke",
            "Datengetriebene Entscheidungen",
        ],
        "benefits_en": [
            "80% faster report creation",
            "Real-time insights",
            "Data-driven decisions",
        ],
        "time_to_value_weeks": 4,
        "roi_estimate_percent": 200,
        "quick_win": False,
        "suitable_branches": ["finanzen", "handel", "industrie", "marketing"],
        "suitable_sizes": ["team", "kmu"],
    },
    "email_automation": {
        "name": "E-Mail-Marketing-Automation",
        "name_en": "Email Marketing Automation",
        "description": "Automatisierte E-Mail-Kampagnen mit personalisierten Inhalten",
        "description_en": "Automated email campaigns with personalized content",
        "category": WorkflowCategory.CUSTOMER,
        "tool_ids": ["mailchimp", "hubspot", "activecampaign"],
        "tool_roles": {
            "mailchimp": "budget",
            "hubspot": "primary",
            "activecampaign": "advanced",
        },
        "setup_steps": [
            {"order": 1, "title": "Kontaktlisten importieren", "title_en": "Import contact lists", "effort_hours": 4},
            {"order": 2, "title": "E-Mail-Templates erstellen", "title_en": "Create email templates", "effort_hours": 8},
            {"order": 3, "title": "Automations-Flows einrichten", "title_en": "Set up automation flows", "effort_hours": 6},
        ],
        "effort_level": EffortLevel.MEDIUM,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "3x mehr Conversions",
            "Personalisierte Kundenansprache",
            "Zeitersparnis im Marketing",
        ],
        "benefits_en": [
            "3x more conversions",
            "Personalized customer outreach",
            "Time savings in marketing",
        ],
        "time_to_value_weeks": 3,
        "roi_estimate_percent": 300,
        "quick_win": True,
        "suitable_branches": ["marketing", "handel", "beratung"],
        "suitable_sizes": ["team", "kmu"],
    },
    "customer_support_ai": {
        "name": "KI-Kundenservice",
        "name_en": "AI Customer Service",
        "description": "24/7 Kundenservice mit KI-Chatbots und automatischer Ticket-Klassifizierung",
        "description_en": "24/7 customer service with AI chatbots and automatic ticket classification",
        "category": WorkflowCategory.CUSTOMER,
        "tool_ids": ["zendesk", "intercom", "chatgpt"],
        "tool_roles": {
            "zendesk": "primary",
            "intercom": "alternative",
            "chatgpt": "assistant",
        },
        "setup_steps": [
            {"order": 1, "title": "Knowledge Base aufbauen", "title_en": "Build knowledge base", "effort_hours": 16},
            {"order": 2, "title": "Chatbot trainieren", "title_en": "Train chatbot", "effort_hours": 8},
            {"order": 3, "title": "Integration testen", "title_en": "Test integration", "effort_hours": 4},
        ],
        "effort_level": EffortLevel.MEDIUM,
        "risk_level": RiskLevel.MEDIUM,
        "benefits": [
            "70% Anfragen automatisch beantwortet",
            "24/7 Verfügbarkeit",
            "Kürzere Reaktionszeiten",
        ],
        "benefits_en": [
            "70% queries answered automatically",
            "24/7 availability",
            "Shorter response times",
        ],
        "time_to_value_weeks": 6,
        "roi_estimate_percent": 250,
        "quick_win": False,
        "suitable_branches": ["handel", "beratung", "it", "gesundheit"],
        "suitable_sizes": ["team", "kmu"],
    },
    "content_creation": {
        "name": "KI-Content-Erstellung",
        "name_en": "AI Content Creation",
        "description": "Automatisierte Erstellung von Marketing-Content mit KI-Tools",
        "description_en": "Automated creation of marketing content with AI tools",
        "category": WorkflowCategory.CONTENT,
        "tool_ids": ["chatgpt", "jasper", "canva"],
        "tool_roles": {
            "chatgpt": "primary",
            "jasper": "alternative",
            "canva": "design",
        },
        "setup_steps": [
            {"order": 1, "title": "Brand Guidelines definieren", "title_en": "Define brand guidelines", "effort_hours": 4},
            {"order": 2, "title": "Content-Templates erstellen", "title_en": "Create content templates", "effort_hours": 6},
            {"order": 3, "title": "Review-Prozess einrichten", "title_en": "Set up review process", "effort_hours": 2},
        ],
        "effort_level": EffortLevel.LOW,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "5x mehr Content-Output",
            "Konsistente Markenkommunikation",
            "Schnellere Time-to-Market",
        ],
        "benefits_en": [
            "5x more content output",
            "Consistent brand communication",
            "Faster time-to-market",
        ],
        "time_to_value_weeks": 1,
        "roi_estimate_percent": 400,
        "quick_win": True,
        "suitable_branches": ["marketing", "handel", "beratung", "bildung"],
        "suitable_sizes": ["solo", "team", "kmu"],
    },
    "project_management": {
        "name": "Digitales Projektmanagement",
        "name_en": "Digital Project Management",
        "description": "Zentralisierte Projektverwaltung mit Automatisierungen und Reportings",
        "description_en": "Centralized project management with automations and reporting",
        "category": WorkflowCategory.COLLABORATION,
        "tool_ids": ["asana", "monday", "jira"],
        "tool_roles": {
            "asana": "primary",
            "monday": "alternative",
            "jira": "technical",
        },
        "setup_steps": [
            {"order": 1, "title": "Projektstruktur definieren", "title_en": "Define project structure", "effort_hours": 6},
            {"order": 2, "title": "Workflows automatisieren", "title_en": "Automate workflows", "effort_hours": 8},
            {"order": 3, "title": "Team onboarden", "title_en": "Onboard team", "effort_hours": 4},
        ],
        "effort_level": EffortLevel.MEDIUM,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "30% höhere Produktivität",
            "Bessere Transparenz",
            "Reduzierte Meeting-Zeit",
        ],
        "benefits_en": [
            "30% higher productivity",
            "Better transparency",
            "Reduced meeting time",
        ],
        "time_to_value_weeks": 3,
        "roi_estimate_percent": 180,
        "quick_win": False,
        "suitable_branches": ["beratung", "it", "marketing", "bauwesen_architektur"],
        "suitable_sizes": ["team", "kmu"],
    },
    "financial_automation": {
        "name": "Finanzprozess-Automation",
        "name_en": "Financial Process Automation",
        "description": "Automatisierte Buchhaltung, Rechnungsstellung und Finanzreporting",
        "description_en": "Automated accounting, invoicing, and financial reporting",
        "category": WorkflowCategory.OPERATIONS,
        "tool_ids": ["datev", "lexoffice", "sevdesk"],
        "tool_roles": {
            "datev": "enterprise",
            "lexoffice": "primary",
            "sevdesk": "budget",
        },
        "setup_steps": [
            {"order": 1, "title": "Kontenplan einrichten", "title_en": "Set up chart of accounts", "effort_hours": 8},
            {"order": 2, "title": "Banking-Anbindung", "title_en": "Connect banking", "effort_hours": 4},
            {"order": 3, "title": "Automatische Buchungen", "title_en": "Set up auto-bookings", "effort_hours": 6},
        ],
        "effort_level": EffortLevel.MEDIUM,
        "risk_level": RiskLevel.MEDIUM,
        "benefits": [
            "90% weniger manuelle Buchungen",
            "Echtzeit-Finanzübersicht",
            "Fehlerreduzierung",
        ],
        "benefits_en": [
            "90% fewer manual bookings",
            "Real-time financial overview",
            "Error reduction",
        ],
        "time_to_value_weeks": 4,
        "roi_estimate_percent": 200,
        "quick_win": False,
        "suitable_branches": ["beratung", "handel", "finanzen", "industrie"],
        "suitable_sizes": ["solo", "team", "kmu"],
    },
    "crm_automation": {
        "name": "CRM-Automation",
        "name_en": "CRM Automation",
        "description": "Automatisierte Kundenverwaltung und Sales-Pipeline",
        "description_en": "Automated customer management and sales pipeline",
        "category": WorkflowCategory.CUSTOMER,
        "tool_ids": ["salesforce", "hubspot", "pipedrive"],
        "tool_roles": {
            "salesforce": "enterprise",
            "hubspot": "primary",
            "pipedrive": "budget",
        },
        "setup_steps": [
            {"order": 1, "title": "Kontakte migrieren", "title_en": "Migrate contacts", "effort_hours": 8},
            {"order": 2, "title": "Sales-Pipeline konfigurieren", "title_en": "Configure sales pipeline", "effort_hours": 6},
            {"order": 3, "title": "Automations einrichten", "title_en": "Set up automations", "effort_hours": 8},
        ],
        "effort_level": EffortLevel.MEDIUM,
        "risk_level": RiskLevel.MEDIUM,
        "benefits": [
            "40% mehr Abschlüsse",
            "Keine verlorenen Leads",
            "Bessere Kundenbeziehungen",
        ],
        "benefits_en": [
            "40% more closed deals",
            "No lost leads",
            "Better customer relationships",
        ],
        "time_to_value_weeks": 4,
        "roi_estimate_percent": 350,
        "quick_win": False,
        "suitable_branches": ["beratung", "handel", "marketing", "it"],
        "suitable_sizes": ["team", "kmu"],
    },
    "security_monitoring": {
        "name": "Security-Monitoring",
        "name_en": "Security Monitoring",
        "description": "Automatische Überwachung von IT-Sicherheit und Compliance",
        "description_en": "Automatic monitoring of IT security and compliance",
        "category": WorkflowCategory.SECURITY,
        "tool_ids": ["1password", "crowdstrike", "sentinelone"],
        "tool_roles": {
            "1password": "access",
            "crowdstrike": "primary",
            "sentinelone": "alternative",
        },
        "setup_steps": [
            {"order": 1, "title": "Security-Audit durchführen", "title_en": "Conduct security audit", "effort_hours": 16},
            {"order": 2, "title": "Tools implementieren", "title_en": "Implement tools", "effort_hours": 8},
            {"order": 3, "title": "Monitoring einrichten", "title_en": "Set up monitoring", "effort_hours": 6},
        ],
        "effort_level": EffortLevel.HIGH,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "99% Bedrohungserkennung",
            "DSGVO-Compliance",
            "Reduziertes Cyber-Risiko",
        ],
        "benefits_en": [
            "99% threat detection",
            "GDPR compliance",
            "Reduced cyber risk",
        ],
        "time_to_value_weeks": 6,
        "roi_estimate_percent": 500,
        "quick_win": False,
        "suitable_branches": ["finanzen", "gesundheit", "verwaltung", "it"],
        "suitable_sizes": ["team", "kmu"],
    },
    "inventory_management": {
        "name": "Bestandsmanagement",
        "name_en": "Inventory Management",
        "description": "Automatisierte Lagerverwaltung mit Echtzeit-Tracking",
        "description_en": "Automated warehouse management with real-time tracking",
        "category": WorkflowCategory.OPERATIONS,
        "tool_ids": ["sap_business_one", "sage", "weclapp"],
        "tool_roles": {
            "sap_business_one": "enterprise",
            "sage": "primary",
            "weclapp": "budget",
        },
        "setup_steps": [
            {"order": 1, "title": "Artikelstamm importieren", "title_en": "Import item master data", "effort_hours": 12},
            {"order": 2, "title": "Lagerorte definieren", "title_en": "Define storage locations", "effort_hours": 6},
            {"order": 3, "title": "Bestandsführung aktivieren", "title_en": "Activate inventory tracking", "effort_hours": 8},
        ],
        "effort_level": EffortLevel.HIGH,
        "risk_level": RiskLevel.MEDIUM,
        "benefits": [
            "50% weniger Fehlbestände",
            "Optimierte Lagerkosten",
            "Automatische Nachbestellung",
        ],
        "benefits_en": [
            "50% fewer stockouts",
            "Optimized storage costs",
            "Automatic reordering",
        ],
        "time_to_value_weeks": 8,
        "roi_estimate_percent": 180,
        "quick_win": False,
        "suitable_branches": ["handel", "industrie", "transport_logistik"],
        "suitable_sizes": ["team", "kmu"],
    },
    "hr_automation": {
        "name": "HR-Prozess-Automation",
        "name_en": "HR Process Automation",
        "description": "Digitalisierte Personalverwaltung mit Self-Service-Portal",
        "description_en": "Digitalized HR management with self-service portal",
        "category": WorkflowCategory.OPERATIONS,
        "tool_ids": ["personio", "sage_hr", "bamboohr"],
        "tool_roles": {
            "personio": "primary",
            "sage_hr": "alternative",
            "bamboohr": "international",
        },
        "setup_steps": [
            {"order": 1, "title": "Mitarbeiterdaten migrieren", "title_en": "Migrate employee data", "effort_hours": 12},
            {"order": 2, "title": "Workflows konfigurieren", "title_en": "Configure workflows", "effort_hours": 8},
            {"order": 3, "title": "Self-Service aktivieren", "title_en": "Enable self-service", "effort_hours": 4},
        ],
        "effort_level": EffortLevel.MEDIUM,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "60% weniger HR-Admin",
            "Bessere Mitarbeiter-Experience",
            "Compliance-Sicherheit",
        ],
        "benefits_en": [
            "60% less HR admin work",
            "Better employee experience",
            "Compliance security",
        ],
        "time_to_value_weeks": 6,
        "roi_estimate_percent": 150,
        "quick_win": False,
        "suitable_branches": ["beratung", "it", "industrie", "verwaltung"],
        "suitable_sizes": ["team", "kmu"],
    },
    "social_media_automation": {
        "name": "Social-Media-Automation",
        "name_en": "Social Media Automation",
        "description": "Geplante Veröffentlichungen und Analytics über alle Kanäle",
        "description_en": "Scheduled publishing and analytics across all channels",
        "category": WorkflowCategory.CONTENT,
        "tool_ids": ["hootsuite", "buffer", "sprout_social"],
        "tool_roles": {
            "hootsuite": "enterprise",
            "buffer": "budget",
            "sprout_social": "primary",
        },
        "setup_steps": [
            {"order": 1, "title": "Social-Accounts verbinden", "title_en": "Connect social accounts", "effort_hours": 2},
            {"order": 2, "title": "Content-Kalender erstellen", "title_en": "Create content calendar", "effort_hours": 4},
            {"order": 3, "title": "Analytics einrichten", "title_en": "Set up analytics", "effort_hours": 2},
        ],
        "effort_level": EffortLevel.LOW,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "Konstante Social-Präsenz",
            "4x mehr Engagement",
            "Zeit für Strategie",
        ],
        "benefits_en": [
            "Consistent social presence",
            "4x more engagement",
            "Time for strategy",
        ],
        "time_to_value_weeks": 1,
        "roi_estimate_percent": 200,
        "quick_win": True,
        "suitable_branches": ["marketing", "handel", "beratung", "bildung"],
        "suitable_sizes": ["solo", "team", "kmu"],
    },
    "process_digitalization": {
        "name": "Prozessdigitalisierung",
        "name_en": "Process Digitalization",
        "description": "Digitalisierung von Papierprozessen mit elektronischen Formularen",
        "description_en": "Digitalization of paper processes with electronic forms",
        "category": WorkflowCategory.AUTOMATION,
        "tool_ids": ["typeform", "jotform", "microsoft_forms"],
        "tool_roles": {
            "typeform": "primary",
            "jotform": "alternative",
            "microsoft_forms": "budget",
        },
        "setup_steps": [
            {"order": 1, "title": "Prozesse analysieren", "title_en": "Analyze processes", "effort_hours": 8},
            {"order": 2, "title": "Formulare erstellen", "title_en": "Create forms", "effort_hours": 6},
            {"order": 3, "title": "Workflows automatisieren", "title_en": "Automate workflows", "effort_hours": 4},
        ],
        "effort_level": EffortLevel.LOW,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "Papierlose Prozesse",
            "80% schnellere Bearbeitung",
            "Automatische Datenspeicherung",
        ],
        "benefits_en": [
            "Paperless processes",
            "80% faster processing",
            "Automatic data storage",
        ],
        "time_to_value_weeks": 2,
        "roi_estimate_percent": 250,
        "quick_win": True,
        "suitable_branches": ["verwaltung", "bauwesen_architektur", "gesundheit", "bildung"],
        "suitable_sizes": ["solo", "team", "kmu"],
    },
    "fleet_management": {
        "name": "Flottenmanagement",
        "name_en": "Fleet Management",
        "description": "GPS-Tracking und Routenoptimierung für Fahrzeugflotten",
        "description_en": "GPS tracking and route optimization for vehicle fleets",
        "category": WorkflowCategory.OPERATIONS,
        "tool_ids": ["vimcar", "fleetio", "samsara"],
        "tool_roles": {
            "vimcar": "primary",
            "fleetio": "alternative",
            "samsara": "enterprise",
        },
        "setup_steps": [
            {"order": 1, "title": "Hardware installieren", "title_en": "Install hardware", "effort_hours": 8},
            {"order": 2, "title": "Fahrzeuge einrichten", "title_en": "Set up vehicles", "effort_hours": 4},
            {"order": 3, "title": "Routen optimieren", "title_en": "Optimize routes", "effort_hours": 6},
        ],
        "effort_level": EffortLevel.MEDIUM,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "20% weniger Kraftstoffkosten",
            "Echtzeit-Fahrzeugortung",
            "Optimierte Touren",
        ],
        "benefits_en": [
            "20% lower fuel costs",
            "Real-time vehicle tracking",
            "Optimized tours",
        ],
        "time_to_value_weeks": 4,
        "roi_estimate_percent": 180,
        "quick_win": False,
        "suitable_branches": ["transport_logistik", "bauwesen_architektur", "handel"],
        "suitable_sizes": ["team", "kmu"],
    },
    "quality_management": {
        "name": "Qualitätsmanagement",
        "name_en": "Quality Management",
        "description": "Digitale Qualitätskontrolle mit Checklisten und Audits",
        "description_en": "Digital quality control with checklists and audits",
        "category": WorkflowCategory.OPERATIONS,
        "tool_ids": ["iauditor", "lumiform", "qms"],
        "tool_roles": {
            "iauditor": "primary",
            "lumiform": "alternative",
            "qms": "enterprise",
        },
        "setup_steps": [
            {"order": 1, "title": "Checklisten erstellen", "title_en": "Create checklists", "effort_hours": 8},
            {"order": 2, "title": "Inspektionsrouten definieren", "title_en": "Define inspection routes", "effort_hours": 4},
            {"order": 3, "title": "Reporting einrichten", "title_en": "Set up reporting", "effort_hours": 4},
        ],
        "effort_level": EffortLevel.MEDIUM,
        "risk_level": RiskLevel.LOW,
        "benefits": [
            "50% weniger Qualitätsmängel",
            "Lückenlose Dokumentation",
            "Schnellere Audits",
        ],
        "benefits_en": [
            "50% fewer quality issues",
            "Complete documentation",
            "Faster audits",
        ],
        "time_to_value_weeks": 4,
        "roi_estimate_percent": 200,
        "quick_win": False,
        "suitable_branches": ["industrie", "bauwesen_architektur", "gesundheit", "transport_logistik"],
        "suitable_sizes": ["team", "kmu"],
    },
}


# =============================================================================
# TOOL METADATA FOR WORKFLOWS
# =============================================================================

TOOL_WORKFLOW_DATA: Dict[str, Dict] = {
    # Documentation & Collaboration
    "notion": {"name": "Notion", "setup_hours": 2, "monthly_cost": 8},
    "confluence": {"name": "Confluence", "setup_hours": 4, "monthly_cost": 5.75},
    # Analytics
    "power_bi": {"name": "Power BI", "setup_hours": 8, "monthly_cost": 9.40},
    "tableau": {"name": "Tableau", "setup_hours": 12, "monthly_cost": 70},
    "google_data_studio": {"name": "Looker Studio", "setup_hours": 4, "monthly_cost": 0},
    # Email Marketing
    "mailchimp": {"name": "Mailchimp", "setup_hours": 4, "monthly_cost": 13},
    "hubspot": {"name": "HubSpot", "setup_hours": 8, "monthly_cost": 45},
    "activecampaign": {"name": "ActiveCampaign", "setup_hours": 6, "monthly_cost": 29},
    # Customer Service
    "zendesk": {"name": "Zendesk", "setup_hours": 8, "monthly_cost": 49},
    "intercom": {"name": "Intercom", "setup_hours": 6, "monthly_cost": 74},
    # AI Tools
    "chatgpt": {"name": "ChatGPT", "setup_hours": 1, "monthly_cost": 20},
    "jasper": {"name": "Jasper", "setup_hours": 2, "monthly_cost": 49},
    "canva": {"name": "Canva", "setup_hours": 1, "monthly_cost": 12.99},
    # Project Management
    "asana": {"name": "Asana", "setup_hours": 4, "monthly_cost": 10.99},
    "monday": {"name": "Monday.com", "setup_hours": 4, "monthly_cost": 9},
    "jira": {"name": "Jira", "setup_hours": 6, "monthly_cost": 7.75},
    # Finance
    "datev": {"name": "DATEV", "setup_hours": 16, "monthly_cost": 50},
    "lexoffice": {"name": "lexoffice", "setup_hours": 4, "monthly_cost": 7.90},
    "sevdesk": {"name": "sevDesk", "setup_hours": 3, "monthly_cost": 8.90},
    # CRM
    "salesforce": {"name": "Salesforce", "setup_hours": 20, "monthly_cost": 75},
    "pipedrive": {"name": "Pipedrive", "setup_hours": 4, "monthly_cost": 14.90},
    # Security
    "1password": {"name": "1Password", "setup_hours": 2, "monthly_cost": 7.99},
    "crowdstrike": {"name": "CrowdStrike", "setup_hours": 8, "monthly_cost": 8.99},
    "sentinelone": {"name": "SentinelOne", "setup_hours": 8, "monthly_cost": 7},
    # ERP
    "sap_business_one": {"name": "SAP Business One", "setup_hours": 80, "monthly_cost": 150},
    "sage": {"name": "Sage", "setup_hours": 20, "monthly_cost": 50},
    "weclapp": {"name": "weclapp", "setup_hours": 12, "monthly_cost": 39},
    # HR
    "personio": {"name": "Personio", "setup_hours": 16, "monthly_cost": 99},
    "sage_hr": {"name": "Sage HR", "setup_hours": 8, "monthly_cost": 5.50},
    "bamboohr": {"name": "BambooHR", "setup_hours": 12, "monthly_cost": 8},
    # Social Media
    "hootsuite": {"name": "Hootsuite", "setup_hours": 2, "monthly_cost": 99},
    "buffer": {"name": "Buffer", "setup_hours": 1, "monthly_cost": 6},
    "sprout_social": {"name": "Sprout Social", "setup_hours": 3, "monthly_cost": 249},
    # Forms
    "typeform": {"name": "Typeform", "setup_hours": 2, "monthly_cost": 25},
    "jotform": {"name": "JotForm", "setup_hours": 2, "monthly_cost": 34},
    "microsoft_forms": {"name": "Microsoft Forms", "setup_hours": 1, "monthly_cost": 0},
    # Fleet
    "vimcar": {"name": "Vimcar", "setup_hours": 4, "monthly_cost": 7.90},
    "fleetio": {"name": "Fleetio", "setup_hours": 6, "monthly_cost": 5},
    "samsara": {"name": "Samsara", "setup_hours": 8, "monthly_cost": 25},
    # Quality
    "iauditor": {"name": "SafetyCulture", "setup_hours": 4, "monthly_cost": 24},
    "lumiform": {"name": "Lumiform", "setup_hours": 3, "monthly_cost": 16},
    "qms": {"name": "QMS Software", "setup_hours": 16, "monthly_cost": 50},
}


# =============================================================================
# WORKFLOW BUILDER FUNCTIONS
# =============================================================================

def _build_workflow_card(workflow_id: str, template: Dict) -> WorkflowCard:
    """Build a WorkflowCard from a template."""
    tools = []
    for tool_id in template.get("tool_ids", []):
        tool_data = TOOL_WORKFLOW_DATA.get(tool_id, {})
        role = template.get("tool_roles", {}).get(tool_id, "primary")
        tools.append(WorkflowTool(
            tool_id=tool_id,
            name=tool_data.get("name", tool_id),
            role=role,
            setup_time_hours=tool_data.get("setup_hours", 4),
            monthly_cost_eur=tool_data.get("monthly_cost", 0),
        ))

    setup_steps = []
    for step in template.get("setup_steps", []):
        setup_steps.append(SetupStep(
            order=step["order"],
            title=step["title"],
            description=step.get("title_en", step["title"]),
            effort_hours=step["effort_hours"],
        ))

    return WorkflowCard(
        id=workflow_id,
        name=template["name"],
        name_en=template["name_en"],
        description=template["description"],
        description_en=template["description_en"],
        category=template["category"],
        tools=tools,
        setup_steps=setup_steps,
        effort_level=template["effort_level"],
        risk_level=template["risk_level"],
        expected_benefits=template["benefits"],
        expected_benefits_en=template["benefits_en"],
        time_to_value_weeks=template["time_to_value_weeks"],
        roi_estimate_percent=template["roi_estimate_percent"],
        quick_win=template.get("quick_win", False),
        suitable_branches=template.get("suitable_branches", []),
        suitable_sizes=template.get("suitable_sizes", []),
    )


def get_workflow_card(workflow_id: str) -> Optional[WorkflowCard]:
    """Get a single workflow card by ID."""
    template = WORKFLOW_TEMPLATES.get(workflow_id)
    if not template:
        return None
    return _build_workflow_card(workflow_id, template)


def get_all_workflow_cards() -> List[WorkflowCard]:
    """Get all workflow cards."""
    return [
        _build_workflow_card(wf_id, template)
        for wf_id, template in WORKFLOW_TEMPLATES.items()
    ]


def get_quick_wins() -> List[WorkflowCard]:
    """Get all Quick Win workflows."""
    return [
        _build_workflow_card(wf_id, template)
        for wf_id, template in WORKFLOW_TEMPLATES.items()
        if template.get("quick_win", False)
    ]


# =============================================================================
# WORKFLOW RECOMMENDATION ENGINE
# =============================================================================

def recommend_workflows_for_profile(
    branch: str,
    size: str,
    usecases: Optional[List[str]] = None,
    max_results: int = 5,
    include_quick_wins: bool = True,
) -> List[WorkflowRecommendation]:
    """
    Recommend workflows for a company profile.

    Args:
        branch: Branch/industry key
        size: Company size (solo/team/kmu)
        usecases: Optional list of specific use cases
        max_results: Maximum number of recommendations
        include_quick_wins: Whether to prioritize Quick Wins

    Returns:
        List of WorkflowRecommendation sorted by relevance
    """
    recommendations: List[WorkflowRecommendation] = []
    usecases = usecases or []
    usecase_lower = [uc.lower() for uc in usecases]

    for wf_id, template in WORKFLOW_TEMPLATES.items():
        # Calculate relevance score
        score = 0.0
        reasons_de = []
        reasons_en = []

        # Branch match (0.4 weight)
        branch_lower = branch.lower()
        if branch_lower in template.get("suitable_branches", []):
            score += 0.4
            reasons_de.append(f"Passend für {branch}")
            reasons_en.append(f"Suitable for {branch}")

        # Size match (0.3 weight)
        size_lower = size.lower()
        if size_lower in template.get("suitable_sizes", []):
            score += 0.3
            reasons_de.append(f"Geeignet für {size}")
            reasons_en.append(f"Appropriate for {size}")

        # Quick Win bonus (0.2 weight)
        if include_quick_wins and template.get("quick_win", False):
            score += 0.2
            reasons_de.append("Quick Win")
            reasons_en.append("Quick Win")

        # Use case matching (0.1 weight)
        workflow_keywords = [
            template["name"].lower(),
            template["name_en"].lower(),
            template["description"].lower(),
            template["description_en"].lower(),
        ]
        for uc in usecase_lower:
            for kw in workflow_keywords:
                if uc in kw or any(word in uc for word in kw.split()):
                    score += 0.1
                    break

        # Only include if relevance score is significant
        if score >= 0.3:
            workflow_card = _build_workflow_card(wf_id, template)
            recommendations.append(WorkflowRecommendation(
                workflow=workflow_card,
                relevance_score=min(1.0, score),
                reason="; ".join(reasons_de) if reasons_de else "Allgemeine Empfehlung",
                reason_en="; ".join(reasons_en) if reasons_en else "General recommendation",
                priority=1 if score >= 0.8 else (2 if score >= 0.5 else 3),
            ))

    # Sort by relevance score (descending) and priority
    recommendations.sort(key=lambda r: (-r.relevance_score, r.priority))

    return recommendations[:max_results]


def get_workflows_by_category(category: WorkflowCategory) -> List[WorkflowCard]:
    """Get all workflows in a category."""
    return [
        _build_workflow_card(wf_id, template)
        for wf_id, template in WORKFLOW_TEMPLATES.items()
        if template["category"] == category
    ]


# =============================================================================
# HTML OUTPUT GENERATION
# =============================================================================

def generate_workflow_html(
    workflows: List[WorkflowRecommendation],
    language: str = "de",
) -> str:
    """
    Generate HTML for workflow cards.

    Args:
        workflows: List of workflow recommendations
        language: Output language (de/en)

    Returns:
        HTML string for TOOLS_WORKFLOW_HTML
    """
    if not workflows:
        return ""

    is_de = language.lower() == "de"

    # Header
    header = "Empfohlene Workflows" if is_de else "Recommended Workflows"
    html_parts = [
        f'<div class="workflow-recommendations">',
        f'<h3 class="workflow-header">{header}</h3>',
    ]

    for rec in workflows:
        wf = rec.workflow

        # Workflow card
        name = wf.name if is_de else wf.name_en
        desc = wf.description if is_de else wf.description_en
        benefits = wf.expected_benefits if is_de else wf.expected_benefits_en

        # Quick Win badge
        quick_win_badge = ""
        if wf.quick_win:
            badge_text = "Quick Win" if is_de else "Quick Win"
            quick_win_badge = f'<span class="badge badge-quickwin">{badge_text}</span>'

        # Effort badge
        effort_text = {
            EffortLevel.LOW: ("Geringer Aufwand", "Low effort"),
            EffortLevel.MEDIUM: ("Mittlerer Aufwand", "Medium effort"),
            EffortLevel.HIGH: ("Hoher Aufwand", "High effort"),
        }
        effort_label = effort_text[wf.effort_level][0 if is_de else 1]
        effort_class = f"badge-effort-{wf.effort_level.value}"

        # ROI and time to value
        ttv_label = "Wochen bis Nutzen" if is_de else "Weeks to value"

        html_parts.append(f'''
        <div class="workflow-card" data-category="{wf.category.value}">
            <div class="workflow-header">
                <h4>{name}</h4>
                <div class="workflow-badges">
                    {quick_win_badge}
                    <span class="badge {effort_class}">{effort_label}</span>
                    <span class="badge badge-roi">ROI: {wf.roi_estimate_percent}%</span>
                </div>
            </div>
            <p class="workflow-desc">{desc}</p>
        ''')

        # Tools section
        tools_header = "Empfohlene Tools" if is_de else "Recommended Tools"
        html_parts.append(f'<div class="workflow-tools"><strong>{tools_header}:</strong><ul>')
        for tool in wf.tools[:3]:  # Max 3 tools
            role_labels = {
                "primary": ("Primär", "Primary"),
                "alternative": ("Alternative", "Alternative"),
                "budget": ("Budget", "Budget"),
                "enterprise": ("Enterprise", "Enterprise"),
                "assistant": ("KI-Assistent", "AI Assistant"),
                "design": ("Design", "Design"),
                "technical": ("Technisch", "Technical"),
                "access": ("Zugang", "Access"),
                "international": ("International", "International"),
            }
            role_label = role_labels.get(tool.role, (tool.role, tool.role))[0 if is_de else 1]
            cost_text = f"€{tool.monthly_cost_eur:.2f}/Monat" if is_de else f"€{tool.monthly_cost_eur:.2f}/month"
            html_parts.append(f'<li><strong>{tool.name}</strong> ({role_label}) - {cost_text}</li>')
        html_parts.append('</ul></div>')

        # Benefits section
        benefits_header = "Erwarteter Nutzen" if is_de else "Expected Benefits"
        html_parts.append(f'<div class="workflow-benefits"><strong>{benefits_header}:</strong><ul>')
        for benefit in benefits:
            html_parts.append(f'<li>{benefit}</li>')
        html_parts.append('</ul></div>')

        # Setup steps (collapsed by default)
        steps_header = "Setup-Schritte" if is_de else "Setup Steps"
        total_hours = sum(step.effort_hours for step in wf.setup_steps)
        hours_label = "Stunden" if is_de else "hours"

        html_parts.append(f'''
            <details class="workflow-steps">
                <summary>{steps_header} ({total_hours} {hours_label})</summary>
                <ol>
        ''')
        for step in wf.setup_steps:
            html_parts.append(f'<li>{step.title} ({step.effort_hours}h)</li>')
        html_parts.append('</ol></details>')

        # Time to value
        html_parts.append(f'''
            <div class="workflow-meta">
                <span class="ttv">{ttv_label}: {wf.time_to_value_weeks}</span>
            </div>
        </div>
        ''')

    html_parts.append('</div>')

    return "\n".join(html_parts)


def generate_quick_wins_html(branch: str, size: str, language: str = "de") -> str:
    """
    Generate HTML specifically for Quick Wins section.

    Args:
        branch: Branch/industry key
        size: Company size
        language: Output language

    Returns:
        HTML string for quick wins
    """
    recommendations = recommend_workflows_for_profile(
        branch=branch,
        size=size,
        max_results=3,
        include_quick_wins=True,
    )

    # Filter to only Quick Wins
    quick_win_recs = [r for r in recommendations if r.workflow.quick_win]

    if not quick_win_recs:
        # Get general Quick Wins
        quick_wins = get_quick_wins()[:3]
        quick_win_recs = [
            WorkflowRecommendation(
                workflow=qw,
                relevance_score=0.5,
                reason="Allgemeine Quick Win Empfehlung",
                reason_en="General Quick Win recommendation",
                priority=2,
            )
            for qw in quick_wins
        ]

    return generate_workflow_html(quick_win_recs, language)


# =============================================================================
# INTEGRATION FUNCTION
# =============================================================================

def get_workflow_html_sections(
    briefing: Dict,
    language: str = "de",
) -> Dict[str, str]:
    """
    Generate all workflow-related HTML sections.

    Args:
        briefing: Company briefing dictionary
        language: Output language (de/en)

    Returns:
        Dictionary with HTML sections:
        - TOOLS_WORKFLOW_HTML: Main workflow recommendations
        - TOOLS_QUICK_WINS_HTML: Quick wins section
    """
    branch = briefing.get("branche", "beratung")
    size = briefing.get("unternehmensgroesse", "team")
    usecases = briefing.get("usecases", [])

    if isinstance(usecases, str):
        usecases = [u.strip() for u in usecases.split(",") if u.strip()]

    # Map frontend branch to engine key if needed
    try:
        from services.branch_mapping import map_frontend_branch_to_engine
        branch = map_frontend_branch_to_engine(branch)
    except ImportError:
        pass

    # Get workflow recommendations
    recommendations = recommend_workflows_for_profile(
        branch=branch,
        size=size,
        usecases=usecases,
        max_results=5,
        include_quick_wins=True,
    )

    # Generate HTML sections
    workflow_html = generate_workflow_html(recommendations, language)
    quick_wins_html = generate_quick_wins_html(branch, size, language)

    return {
        "TOOLS_WORKFLOW_HTML": workflow_html,
        "TOOLS_QUICK_WINS_HTML": quick_wins_html,
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[B3-D] Workflow Engine loaded - %d workflow templates, %d tool definitions",
    len(WORKFLOW_TEMPLATES),
    len(TOOL_WORKFLOW_DATA),
)
