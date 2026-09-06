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
# Regionale Programme kommen aus funding_recommender (bundesland-gefiltert).
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
    # KIS-1311: ZIM (pausiert bis 15.01.2027) und ein erfundenes Programm
    # „AI Act Compliance Support" standen hier als KMU-Ausweichliste. Sie
    # greift nur, wenn das Förderkapitel fehlt — dann aber mit echten Programmen.
    "kmu": [
        {
            "program_id": "unternehmensberater_foerderung",
            "name": "Förderung unternehmerischen Know-hows",
            "provider": "BAFA",
            "max_amount": "1.750 €",
            "fit_reason": "Beratungsförderung für KMU (bundesweit)",
            "application_complexity": "low",
        },
        {
            "program_id": "kfw_digitalisierung",
            "name": "KfW-Förderkredite Digitalisierung & Innovation",
            "provider": "KfW",
            "max_amount": "variabel",
            "fit_reason": "Zinsvergünstigte Finanzierung für Digitalisierungsvorhaben",
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
            # KIS-1311: ZIM steht bis 15.01.2027 auf „paused" — der feste
            # Schritt nannte es trotzdem in jedem KMU-Report (KIS1280, S. 15).
            # Das Programm kommt aus dem Förderkapitel, nicht aus der Vorlage.
            "step": 6,
            "title": "Förderantrag vorbereiten",
            "description": "Programm aus dem Förderkapitel wählen und das Vorhaben als Projektbeschreibung strukturieren",
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

# KIS-1313: Sparten-Kits innerhalb der Medienbranche. Das Medien-Kit ist
# auf Bewegtbild und Ton geschnitten; ein Fachverlag (Lauf KIS1282) bekam
# Transkription, Frame.io und Media-Asset-Management. Eine Liste je Sparte
# für alle Größen — die Werkzeugnamen stehen in data/tools_seed.json.
TOOL_TEMPLATES_MEDIA_SPARTE: Dict[str, List[Dict[str, Any]]] = {
    "verlag_publishing": [
        {
            "name": "Vorlektorat-KI (z. B. DeepL Write Pro, LanguageTool)",
            "category": "Lektorat",
            "purpose": "Erste Korrekturschleife mit Freigabe durch das Lektorat, KI-Entwurf gekennzeichnet",
            "priority": 1,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
        {
            "name": "Metadaten & Verschlagwortung (z. B. Aleph Alpha PhariaAI)",
            "category": "Metadaten / Archiv",
            "purpose": "Schlagworte, Kurzbeschreibungen je Titel und Erschließung des Archivs",
            "priority": 1,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "Redaktionssystem-Anbindung (z. B. WoodWing, InDesign-Plugins)",
            "category": "Redaktionssystem",
            "purpose": "KI-Entwürfe ohne Medienbruch in Satz, Portal und Newsletter",
            "priority": 1,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "Rechte-Register (z. B. SharePoint, Notion)",
            "category": "Governance / Rechte",
            "purpose": "Autorenrechte, KI-Kennzeichnung und Freigabestatus je Titel",
            "priority": 2,
            "estimated_setup_days": 3,
            "funding_eligible": False,
        },
        {
            "name": "Workflow-Automation (z. B. Make, n8n)",
            "category": "Workflow-Automation",
            "purpose": "Manuskripteingang, Kurzfassungen und Freigaben automatisieren",
            "priority": 2,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
    ],
    "musik_audio": [
        {
            "name": "Audio-Restauration (z. B. iZotope RX, lokal)",
            "category": "Audio / Postproduktion",
            "purpose": "Rauschen, Klicks und Raumanteile entfernen, bevor gemischt wird",
            "priority": 1,
            "estimated_setup_days": 1,
            "funding_eligible": True,
        },
        {
            "name": "Mastering & Podcast-Aufbereitung (z. B. Auphonic)",
            "category": "Audio / Mastering",
            "purpose": "Lautheit, Pegel und Kapitelmarken automatisiert, EU-Anbieter",
            "priority": 1,
            "estimated_setup_days": 1,
            "funding_eligible": True,
        },
        {
            "name": "Transkription & Untertitel (z. B. Amberscript)",
            "category": "Transkription / Untertitelung",
            "purpose": "Sprachaufnahmen durchsuchbar machen, Untertitel-Entwürfe",
            "priority": 1,
            "estimated_setup_days": 1,
            "funding_eligible": True,
        },
        {
            "name": "Rechte-Register (z. B. SharePoint, Notion)",
            "category": "Governance / Rechte",
            "purpose": "Einwilligungen für Stimmen, Lizenzen und Kennzeichnungsstatus je Produktion",
            "priority": 2,
            "estimated_setup_days": 3,
            "funding_eligible": False,
        },
        {
            "name": "Workflow-Automation (z. B. Make, n8n)",
            "category": "Workflow-Automation",
            "purpose": "Materialeingang, Metadaten und Freigaben automatisieren",
            "priority": 2,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
    ],
}

# KIS-1246 (Medien-Vertikale): Branchen-spezifische Kits statt generischer
# Büro-Tools — im Lauf 1129 empfahl das Team-Kit einer Filmproduktion
# "CRM-System" und "Projekt-Management" statt Produktions-Tools.
TOOL_TEMPLATES_MEDIA: Dict[str, List[Dict[str, Any]]] = {
    "solo": [
        {
            "name": "Transkription & Untertitel (z. B. Amberscript, Descript)",
            "category": "Transkription / Untertitelung",
            "purpose": "Rohmaterial durchsuchbar machen, Untertitel-Entwürfe",
            "priority": 1,
            "estimated_setup_days": 1,
            "funding_eligible": True,
        },
        {
            "name": "Schnitt-KI im Bestand (Premiere Textschnitt, DaVinci Neural Engine)",
            "category": "Postproduktion",
            "purpose": "Textbasierter Rohschnitt, Rauschminderung, Reframing",
            "priority": 1,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
        {
            "name": "Belegte Recherche (z. B. Perplexity, nach AVV-Prüfung)",
            "category": "Recherche",
            "purpose": "Stoff- und Archivrecherche mit prüfbaren Quellen",
            "priority": 2,
            "estimated_setup_days": 1,
            "funding_eligible": False,
        },
        {
            "name": "Rechte- & Projektablage (z. B. Notion, Airtable)",
            "category": "Wissensmanagement / Rechte",
            "purpose": "Rechtekette, Einwilligungen und Lizenzen pro Asset dokumentieren",
            "priority": 2,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
    ],
    "team": [
        {
            "name": "Transkription & Untertitelung (z. B. Amberscript, Simon Says)",
            "category": "Transkription / Untertitelung",
            "purpose": "Automatische Transkripte, Untertitel und Sprachfassungen für alle Projekte",
            "priority": 1,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
        {
            "name": "Review & Versionierung (z. B. Frame.io)",
            "category": "Kollaboration / Freigabe",
            "purpose": "Sichtung, Freigabe und Versionierung im Team bündeln",
            "priority": 1,
            "estimated_setup_days": 1,
            "funding_eligible": True,
        },
        {
            "name": "Schnitt-KI im Bestand (Premiere Textschnitt, DaVinci Neural Engine)",
            "category": "Postproduktion",
            "purpose": "Textbasierter Rohschnitt und KI-Funktionen in vorhandenen Tools aktivieren",
            "priority": 1,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
        {
            "name": "Footage-Archiv & Metadaten (z. B. iconik, CatDV oder Notion-Datenbank)",
            "category": "Medienverwaltung",
            "purpose": "Durchsuchbares Archiv mit Rechtekette als zweite Erlösquelle",
            "priority": 2,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "Bild-/Moodboard-KI (z. B. Adobe Firefly, gekennzeichnet)",
            "category": "Kreation / Pitch",
            "purpose": "Moodboards und Pitch-Visuals — nur mit Kennzeichnung",
            "priority": 2,
            "estimated_setup_days": 1,
            "funding_eligible": False,
        },
    ],
    "kmu": [
        {
            "name": "Media-Asset-Management (z. B. iconik, axle.ai)",
            "category": "Medienverwaltung",
            "purpose": "Zentrales, durchsuchbares Archiv mit Metadaten und Rechtekette",
            "priority": 1,
            "estimated_setup_days": 7,
            "funding_eligible": True,
        },
        {
            "name": "Transkriptions-Pipeline (z. B. Amberscript API)",
            "category": "Transkription / Untertitelung",
            "purpose": "Automatische Verschlagwortung und Untertitel ab Materialeingang",
            "priority": 1,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "Rechte-Register (z. B. SharePoint, Notion)",
            "category": "Governance / Rechte",
            "purpose": "Einwilligungen, Lizenzen und Kennzeichnungsstatus pro Asset",
            "priority": 1,
            "estimated_setup_days": 3,
            "funding_eligible": True,
        },
        {
            "name": "Workflow-Automation (z. B. Make, n8n)",
            "category": "Workflow-Automation",
            "purpose": "Material-Eingang, Metadaten und Freigaben automatisieren",
            "priority": 2,
            "estimated_setup_days": 5,
            "funding_eligible": True,
        },
        {
            "name": "Review & Versionierung (z. B. Frame.io)",
            "category": "Kollaboration / Freigabe",
            "purpose": "Sender-/Kundenfreigaben mit dokumentiertem Prüfschritt",
            "priority": 2,
            "estimated_setup_days": 2,
            "funding_eligible": True,
        },
    ],
}

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
# KIS-1251 (Punkt 5): EN-Fassung der Starter-Kit-Texte
# =============================================================================
# Übersetzungs-Maps (Schlüssel = exakter DE-String aus den Templates oben).
# Unbekannte Strings bleiben unverändert (fail-open). DE-Pfad unverändert.

KIT_DESCRIPTIONS_EN: Dict[str, str] = {
    "solo": (
        "A compact entry point for solo entrepreneurs: with this starter kit "
        "you automate first tasks, use AI for text work and secure matching "
        "funding – all with manageable effort."
    ),
    "team": (
        "A team AI stack for effective collaboration: this kit enables shared "
        "AI usage, automated workflows and structured communication – plus "
        "access to attractive funding programmes."
    ),
    "kmu": (
        "A growth kit for SMEs: a structured package for companies with "
        "11-100 employees – focused on data quality, process automation and "
        "step-by-step AI integration, including matching funding programmes."
    ),
}

KIT_DESCRIPTIONS_EXPERT_EN: Dict[str, str] = {
    "solo": (
        "An operations kit for AI professionals: monitoring, prompt "
        "versioning and evaluation for your existing LLM pipelines. Focus on "
        "quality, cost and compliance – not on basics."
    ),
    "team": (
        "A team operations kit: central API management, team-wide monitoring "
        "and a governance framework for productive LLM usage. "
        "Integration: 1-2 weeks."
    ),
    "kmu": (
        "Enterprise LLM operations: scalable infrastructure with monitoring, "
        "governance and automated quality gates for company-wide AI usage. "
        "Integration: 2-4 weeks."
    ),
}

_KIT_TEXT_EN: Dict[str, str] = {
    # --- Tool names (generic DE names) ---
    "KI-Assistent": "AI assistant",
    "Workflow-Automation": "Workflow automation",
    "Formular-Tool": "Form tool",
    "Wissens-Datenbank": "Knowledge base",
    "Team-KI-Plattform": "Team AI platform",
    "Kollaborations-Tool": "Collaboration tool",
    "Projekt-/Aufgaben-Management": "Project/task management",
    "CRM-System": "CRM system",
    "KI-Assistenz-Plattform (KMU)": "AI assistance platform (SME)",
    "Datenqualitäts-Tool": "Data quality tool",
    "Workflow-Automatisierung": "Workflow automation",
    "BI/Reporting-System": "BI/reporting system",
    "KI-Governance-Checkliste": "AI governance checklist",
    "LLM-API-Zugang (Anthropic/OpenAI)": "LLM API access (Anthropic/OpenAI)",
    "LLM-Monitoring (Langfuse)": "LLM monitoring (Langfuse)",
    "Prompt-Versionierung (Git/Langfuse)": "Prompt versioning (Git/Langfuse)",
    "Evaluierungs-Framework (Promptfoo)": "Evaluation framework (Promptfoo)",
    "LLM-Gateway (LiteLLM/Portkey)": "LLM gateway (LiteLLM/Portkey)",
    "LLM-Observability (Langfuse/Helicone)": "LLM observability (Langfuse/Helicone)",
    "KI-Governance-Framework": "AI governance framework",
    "CI/CD für Prompts": "CI/CD for prompts",
    "LLM-Operations-Plattform": "LLM operations platform",
    "Monitoring & Evaluierung": "Monitoring & evaluation",
    "KI-Governance & Compliance": "AI governance & compliance",
    "Evaluierungs-Pipeline": "Evaluation pipeline",
    "Cost-Management & Budgetierung": "Cost management & budgeting",
    # --- Media kit tool names ---
    "Transkription & Untertitel (z. B. Amberscript, Descript)":
        "Transcription & subtitles (e.g. Amberscript, Descript)",
    "Schnitt-KI im Bestand (Premiere Textschnitt, DaVinci Neural Engine)":
        "AI in your editing suite (Premiere text-based editing, DaVinci Neural Engine)",
    "Belegte Recherche (z. B. Perplexity, nach AVV-Prüfung)":
        "Cited research (e.g. Perplexity, after DPA review)",
    "Rechte- & Projektablage (z. B. Notion, Airtable)":
        "Rights & project repository (e.g. Notion, Airtable)",
    "Transkription & Untertitelung (z. B. Amberscript, Simon Says)":
        "Transcription & subtitling (e.g. Amberscript, Simon Says)",
    "Review & Versionierung (z. B. Frame.io)":
        "Review & versioning (e.g. Frame.io)",
    "Footage-Archiv & Metadaten (z. B. iconik, CatDV oder Notion-Datenbank)":
        "Footage archive & metadata (e.g. iconik, CatDV or a Notion database)",
    "Bild-/Moodboard-KI (z. B. Adobe Firefly, gekennzeichnet)":
        "Image/moodboard AI (e.g. Adobe Firefly, labeled)",
    "Media-Asset-Management (z. B. iconik, axle.ai)":
        "Media asset management (e.g. iconik, axle.ai)",
    "Transkriptions-Pipeline (z. B. Amberscript API)":
        "Transcription pipeline (e.g. Amberscript API)",
    "Rechte-Register (z. B. SharePoint, Notion)":
        "Rights register (e.g. SharePoint, Notion)",
    "Workflow-Automation (z. B. Make, n8n)":
        "Workflow automation (e.g. Make, n8n)",
    # --- Categories ---
    "KI-API": "AI API",
    "Fragebogen / Intake": "Questionnaire / intake",
    "Wissensmanagement / Docs": "Knowledge management / docs",
    "Team-Kommunikation": "Team communication",
    "CRM / Sales": "CRM / sales",
    "Data Quality": "Data quality",
    "Automation": "Automation",
    "Monitoring / Observability": "Monitoring / observability",
    "Governance": "Governance",
    "DevOps": "DevOps",
    "Qualitätssicherung": "Quality assurance",
    "FinOps": "FinOps",
    "Transkription / Untertitelung": "Transcription / subtitling",
    "Postproduktion": "Post-production",
    "Recherche": "Research",
    "Wissensmanagement / Rechte": "Knowledge management / rights",
    "Kollaboration / Freigabe": "Collaboration / approval",
    "Medienverwaltung": "Media management",
    "Kreation / Pitch": "Creation / pitch",
    "Governance / Rechte": "Governance / rights",
    # --- Tool purposes ---
    "Alltägliche Textarbeit, Entwürfe, Recherche": "Everyday text work, drafts, research",
    "Automatisierung wiederkehrender Aufgaben": "Automation of recurring tasks",
    "Strukturierte Datenerfassung von Kunden": "Structured data capture from clients",
    "Zentrale Ablage für Templates und Wissen": "Central repository for templates and knowledge",
    "Gemeinsame KI-Nutzung im Team": "Shared AI usage in the team",
    "Interne Kommunikation und Abstimmung": "Internal communication and coordination",
    "Aufgabenverteilung und Fortschrittsverfolgung": "Task distribution and progress tracking",
    "Prozessautomatisierung für Teamabläufe": "Process automation for team workflows",
    "Kundenverwaltung und Vertrieb": "Client management and sales",
    "Unternehmensweite KI-Integration für 11-100 Mitarbeiter": "Company-wide AI integration for 11-100 employees",
    "Sicherung der Datenqualität für KI": "Safeguarding data quality for AI",
    "Automatisierung wiederkehrender Geschäftsprozesse": "Automation of recurring business processes",
    "Monitoring und Analytics": "Monitoring and analytics",
    "AI Act Compliance und interne Richtlinien": "AI Act compliance and internal policies",
    "Direkte API-Integration für eigene Pipelines": "Direct API integration for your own pipelines",
    "Prompt-Tracking, Cost-Monitoring, Evaluierung": "Prompt tracking, cost monitoring, evaluation",
    "Versionskontrolle und A/B-Testing für Prompts": "Version control and A/B testing for prompts",
    "Automatisierte Qualitätsprüfung von LLM-Outputs": "Automated quality checks of LLM outputs",
    "Zentrales API-Management, Multi-Provider-Routing": "Central API management, multi-provider routing",
    "Team-weites Monitoring, Cost-Tracking, Evaluierung": "Team-wide monitoring, cost tracking, evaluation",
    "AI Act Compliance, Richtlinien, Dokumentation": "AI Act compliance, policies, documentation",
    "Automatisierte Tests und Deployment für Prompt-Änderungen": "Automated tests and deployment for prompt changes",
    "Enterprise-weites LLM-Management mit Governance": "Enterprise-wide LLM management with governance",
    "Produktionsreife Observability für alle LLM-Aufrufe": "Production-grade observability for all LLM calls",
    "AI Act Compliance, Risikomanagement, Audit-Trail": "AI Act compliance, risk management, audit trail",
    "Automatisierte Quality Gates und Regression Testing": "Automated quality gates and regression testing",
    "Budget-Alerts, Cost-per-Output-Tracking, Optimierung": "Budget alerts, cost-per-output tracking, optimisation",
    "Rohmaterial durchsuchbar machen, Untertitel-Entwürfe": "Make raw footage searchable, subtitle drafts",
    "Textbasierter Rohschnitt, Rauschminderung, Reframing": "Text-based rough cut, noise reduction, reframing",
    "Stoff- und Archivrecherche mit prüfbaren Quellen": "Story and archive research with verifiable sources",
    "Rechtekette, Einwilligungen und Lizenzen pro Asset dokumentieren": "Document the chain of rights, consents and licences per asset",
    "Automatische Transkripte, Untertitel und Sprachfassungen für alle Projekte": "Automatic transcripts, subtitles and language versions for all projects",
    "Sichtung, Freigabe und Versionierung im Team bündeln": "Bundle review, approval and versioning in the team",
    "Textbasierter Rohschnitt und KI-Funktionen in vorhandenen Tools aktivieren": "Activate text-based rough cut and AI features in existing tools",
    "Durchsuchbares Archiv mit Rechtekette als zweite Erlösquelle": "Searchable archive with chain of rights as a second revenue stream",
    "Moodboards und Pitch-Visuals — nur mit Kennzeichnung": "Moodboards and pitch visuals — only with labeling",
    "Zentrales, durchsuchbares Archiv mit Metadaten und Rechtekette": "Central, searchable archive with metadata and chain of rights",
    "Automatische Verschlagwortung und Untertitel ab Materialeingang": "Automatic tagging and subtitles from material ingest",
    "Einwilligungen, Lizenzen und Kennzeichnungsstatus pro Asset": "Consents, licences and labeling status per asset",
    "Material-Eingang, Metadaten und Freigaben automatisieren": "Automate material ingest, metadata and approvals",
    "Sender-/Kundenfreigaben mit dokumentiertem Prüfschritt": "Broadcaster/client approvals with a documented review step",
    # --- Funding names / fit reasons ---
    "Förderung unternehmerischen Know-hows": "Förderung unternehmerischen Know-hows (BAFA consulting grant)",
    "Beratungsförderung für Gründer und Selbstständige (bundesweit)": "Consulting grant for founders and the self-employed (nationwide)",
    "EU-Innovationsförderung für Solo-Selbstständige": "EU innovation funding for solo self-employed",
    "Beratungsförderung für kleine Teams (bundesweit)": "Consulting grant for small teams (nationwide)",
    "KfW-Digitalisierungskredit": "KfW digitalisation loan",
    "Günstige Finanzierung für Digitalisierungsvorhaben": "Low-cost financing for digitalisation projects",
    "Für größere KI-Innovationsprojekte": "For larger AI innovation projects",
    "Beratungsförderung für AI Act Compliance": "Consulting grant for AI Act compliance",
    # --- Checklist titles/descriptions ---
    "KI-Assistent einrichten": "Set up an AI assistant",
    "Registrierung und erste Testläufe mit einem KI-Assistenten": "Registration and first test runs with an AI assistant",
    "Erste Automatisierung erstellen": "Create a first automation",
    "Einen wiederkehrenden Prozess automatisieren (z.B. E-Mail → Task)": "Automate one recurring process (e.g. email → task)",
    "Persönliche KI-Richtlinie festlegen": "Define a personal AI policy",
    "Dokumentieren, welche Daten in KI eingegeben werden dürfen": "Document which data may be entered into AI",
    "Förderprogramm prüfen": "Check funding programmes",
    "Passende Förderung identifizieren und Antragsinformationen sammeln": "Identify matching funding and collect application information",
    "Erste Quick Wins dokumentieren": "Document first quick wins",
    "Zeitersparnis und Qualitätsverbesserungen nach 2 Wochen notieren": "Note time savings and quality improvements after 2 weeks",
    "Team-Workspace einrichten": "Set up a team workspace",
    "Gemeinsamen Workspace und Kommunikationskanal aufsetzen": "Set up a shared workspace and communication channel",
    "KI-Zugang für Team bereitstellen": "Provide AI access for the team",
    "Team-Accounts für KI-Plattform anlegen und Berechtigungen vergeben": "Create team accounts for the AI platform and assign permissions",
    "Team-Guidelines definieren": "Define team guidelines",
    "Gemeinsame Regeln für KI-Nutzung im Team festlegen": "Agree shared rules for AI usage in the team",
    "Erste Team-Automatisierung": "First team automation",
    "Einen Team-übergreifenden Workflow automatisieren": "Automate one cross-team workflow",
    "Förderantrag vorbereiten": "Prepare a funding application",
    "Unterlagen für go-digital oder regionale Programme zusammenstellen": "Compile documents for go-digital or regional programmes",
    "Kurzes Team-Training": "Short team training",
    "30-minütiges Onboarding für alle Team-Mitglieder": "A 30-minute onboarding for all team members",
    "KI-Strategie skizzieren": "Sketch an AI strategy",
    "Grobe KI-Roadmap mit Prioritäten für die nächsten 12 Monate": "Rough AI roadmap with priorities for the next 12 months",
    "Datenlandschaft analysieren": "Analyse the data landscape",
    "Bestandsaufnahme vorhandener Datenquellen und -qualität": "Inventory of existing data sources and their quality",
    "Pilotprojekt definieren": "Define a pilot project",
    "Konkretes KI-Pilotprojekt mit messbaren Zielen festlegen": "Define a concrete AI pilot project with measurable goals",
    "Governance-Framework etablieren": "Establish a governance framework",
    "KI-Richtlinien, Rollen und Verantwortlichkeiten dokumentieren": "Document AI policies, roles and responsibilities",
    "AI Act Compliance prüfen": "Check AI Act compliance",
    "Risikoeinstufung und Compliance-Anforderungen klären": "Clarify risk classification and compliance requirements",
    "Förderantrag vorbereiten": "Prepare a funding application",
    "Programm aus dem Förderkapitel wählen und das Vorhaben als Projektbeschreibung strukturieren": "Pick a programme from the funding chapter and structure the project description",
    "Schulungskonzept erstellen": "Create a training concept",
    "Rollenspezifische Trainings für Fachbereiche planen": "Plan role-specific trainings for departments",
    # --- Investment ranges ---
    "500–2.000 €/Jahr": "€500–2,000/year",
    "2.000–10.000 €/Jahr": "€2,000–10,000/year",
    "10.000–50.000 €/Jahr": "€10,000–50,000/year",
    "unter 2.000 €/Jahr": "under €2,000/year",
    "über 50.000 €/Jahr": "over €50,000/year",
    "variabel": "variable",
}


def _kit_en(text: str) -> str:
    """EN-Lookup mit Fail-open auf den Originalstring."""
    return _KIT_TEXT_EN.get(text, text)


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

    # KIS-1251 (Punkt 5): EN-Labels bei lang=en (DE unverändert)
    _is_en = (lang or "").strip().lower().startswith("en")
    if _is_en:
        maturity_label = "Beginner" if maturity <= 2 else "Advanced" if maturity <= 3 else "Experienced"
        if expertise_level == "expert":
            maturity_label = "AI expert"
        elif expertise_level == "intermediate":
            maturity_label = "AI practitioner"
    else:
        maturity_label = "Einsteiger" if maturity <= 2 else "Fortgeschritten" if maturity <= 3 else "Erfahren"
        # KIS-1132: Override maturity label with expertise label if available
        if expertise_level == "expert":
            maturity_label = "KI-Experte"
        elif expertise_level == "intermediate":
            maturity_label = "KI-Anwender"

    # KIS-1272-R4-T5: Im EN-Pfad (a) Branchenlabel englisch ("Medien" → "Media")
    # und (b) den internen Slug "TEAM/Medien/…" lesbar lokalisieren
    # ("Team · Media · AI practitioner"). DE bleibt byte-identisch.
    if _is_en:
        _branch_display = _BRANCH_SHORT_EN.get(branch_group.strip().lower(), branch_group)
        _size_display_en = {"solo": "Solo", "team": "Team", "kmu": "SME"}.get(size_label, size_label.capitalize())
        segment_label = f"{_size_display_en} · {_branch_display} · {maturity_label}"
    else:
        _branch_display = branch_group
        segment_label = f"{size_label.upper()}/{branch_group}/{maturity_label}"

    kit_id = f"{size_label}_{branch_group.lower()[:4]}_{maturity}"
    kit_name = _generate_kit_name(size_label, _branch_display, lang, expertise_level=expertise_level)

    # KIS-1132: Get templates based on expertise level
    # KIS-1246: Medien-Branche bekommt produktionsnahe Tools statt
    # generischer Büro-Kits (CRM/Projekt-Management).
    _is_media_branch = any(
        k in branch_group.lower() for k in ("medien", "kreativ", "entertainment", "film")
    )
    # KIS-1313: Die Sparte entscheidet innerhalb der Medienbranche — ein
    # Verlag bekam das Video-Kit (Transkription, Frame.io, MAM), Lauf KIS1282.
    try:
        from services.medien_sparte import slug as _sparte_slug
        _sparte = _sparte_slug(ctx.get("medien_sparte") or ctx.get("MEDIEN_SPARTE_LABEL"))
    except Exception:
        _sparte = ""
    if expertise_level == "expert":
        tool_templates = TOOL_TEMPLATES_EXPERT.get(size_label, TOOL_TEMPLATES_EXPERT["solo"])
    elif _is_media_branch and _sparte in TOOL_TEMPLATES_MEDIA_SPARTE:
        tool_templates = TOOL_TEMPLATES_MEDIA_SPARTE[_sparte]
    elif _is_media_branch:
        tool_templates = TOOL_TEMPLATES_MEDIA.get(size_label, TOOL_TEMPLATES_MEDIA["team"])
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

    # KIS-1251 (Punkt 5): EN-Fassung der Template-Texte (Name/Kategorie/
    # Zweck der Tools, Förder-Begründungen, Checklisten). Fail-open:
    # unbekannte Strings bleiben unverändert.
    if _is_en:
        for t_obj in tools:
            t_obj.name = _kit_en(t_obj.name)
            t_obj.category = _kit_en(t_obj.category)
            t_obj.purpose = _kit_en(t_obj.purpose)
        for f_obj in funding:
            f_obj.fit_reason = _kit_en(f_obj.fit_reason)
        for c_obj in checklist:
            c_obj.title = _kit_en(c_obj.title)
            c_obj.description = _kit_en(c_obj.description)

    # Calculate estimates
    total_setup_days = sum(t.estimated_setup_days for t in tools)
    total_checklist_hours = sum(c.estimated_hours for c in checklist)
    estimated_total_days = total_setup_days + int(total_checklist_hours / 8)

    # Estimate investment
    # KIS-1323: Das genannte Budget schlägt die Größenschätzung. Lauf KIS1292
    # (Verlag, Fragebogen 2 „über 50.000 €") las im Starter-Kit weiter
    # „10.000–50.000 €/Jahr" — die KMU-Voreinstellung, zufällig gleich dem
    # überholten Band aus Fragebogen 1.
    estimated_investment = _budget_investment(ctx) or _estimate_investment(size_label)
    if _is_en:
        estimated_investment = _kit_en(estimated_investment)

    # Calculate potential funding
    potential_funding = _calculate_potential_funding(funding)
    if _is_en and potential_funding.startswith("bis zu "):
        # "bis zu 6.500 €" → "up to €6,500"
        _amount = potential_funding[len("bis zu "):].replace(" €", "").replace(".", ",")
        potential_funding = f"up to €{_amount}"

    # Quick win count
    quick_win_count = min(3, len([t for t in tools if t.priority == 1]))

    if _is_en:
        _descriptions = KIT_DESCRIPTIONS_EXPERT_EN if expertise_level == "expert" else KIT_DESCRIPTIONS_EN
    else:
        _descriptions = KIT_DESCRIPTIONS_EXPERT if expertise_level == "expert" else KIT_DESCRIPTIONS

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
        description=_descriptions.get(size_label, ""),
    )


# KIS-1272-R4-T5: Kurze EN-Branchenlabels für Kit-Name/Untertitel
# (Schlüssel = normalisierte Branchen-Enums bzw. deutsche Kurzlabels).
_BRANCH_SHORT_EN = {
    "medien": "Media",
    "medien & kreativwirtschaft": "Media & Creative Industries",
    "beratung": "Consulting",
    "beratung & dienstleistungen": "Consulting & Services",
    "marketing": "Marketing",
    "marketing & werbung": "Marketing & Advertising",
    "it_software": "IT & Software",
    "it & software": "IT & Software",
    "finanzen": "Finance",
    "finanzen & versicherungen": "Finance & Insurance",
    "handel": "Retail",
    "handel & e-commerce": "Retail & E-Commerce",
    "bildung": "Education",
    "verwaltung": "Public administration",
    "gesundheit": "Healthcare",
    "gesundheit & pflege": "Healthcare & Care",
    "bau": "Construction",
    "bauwesen & architektur": "Construction & Architecture",
    "industrie": "Industry",
    "industrie & produktion": "Industry & Manufacturing",
    "logistik": "Logistics",
    "transport & logistik": "Transport & Logistics",
    "gastronomie": "Hospitality",
    "gastronomie & tourismus": "Hospitality & Tourism",
    "allgemein": "General",
}


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
    # KIS-1251: EN-Kit-Namen bei lang=en
    _is_en = (lang or "").strip().lower().startswith("en")
    # KIS-1132: Expertise-aware kit names
    if expertise_level == "expert":
        size_names = {
            "solo": "AI Operations" if _is_en else "KI-Operations",
            "team": "Team-LLM-Ops",
            "kmu": "SME-LLM-Ops" if _is_en else "Enterprise-LLM-Ops",
        }
    else:
        size_names = {
            "solo": "Solo-Starter",
            "team": "Team-Boost",
            "kmu": "SME-Growth" if _is_en else "KMU-Enterprise",
        }
    base_name = size_names.get(size_label, "Starter")
    if _is_en:
        return f"{base_name} kit for {branch}"
    return f"{base_name} Kit für {branch}"


_BUDGET_BAND_TEXT = {
    "unter_2000": "unter 2.000 €/Jahr",
    "2000_10000": "2.000–10.000 €/Jahr",
    "10000_50000": "10.000–50.000 €/Jahr",
    "ueber_50000": "über 50.000 €/Jahr",
}


def _budget_investment(ctx: Dict[str, Any]) -> str:
    """KIS-1323: Budget aus den Antworten — Fragebogen 2 (``s1_budget``) vor
    Fragebogen 1 (``investitionsbudget``), dieselbe Regel wie im Business Case
    und im Werkzeug-Filter. Leer, wenn kein Band vorliegt."""
    _sa = ctx.get("_strategy_answers") if isinstance(ctx.get("_strategy_answers"), dict) else {}
    band = (str((_sa or {}).get("s1_budget") or "") or str(ctx.get("investitionsbudget") or "")).strip().lower()
    return _BUDGET_BAND_TEXT.get(band, "")


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
    _is_en = (lang or "").strip().lower().startswith("en")
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

    # KIS-1251 (Punkt 5): EN-Scaffolding-Strings
    _t_setup_unit = "day(s)" if _is_en else "Tag(e)"
    _t_complexity = "Complexity" if _is_en else "Komplexität"
    _t_step = "Step" if _is_en else "Schritt"
    _t_days = "days" if _is_en else "Tage"
    _t_impl_time = "Estimated implementation time" if _is_en else "Geschätzte Einführungszeit"
    _t_tools_in_kit = "Tools in the kit" if _is_en else "Tools im Kit"
    _t_funding_count = "Funding programmes" if _is_en else "Förderprogramme"
    _t_funding_potential = "Funding potential" if _is_en else "Förderpotenzial"
    _t_est_investment = "Estimated investment" if _is_en else "Geschätzte Investition"

    # Tools section
    tools_html = ""
    for t in kit.tools:
        _badge_2 = "RECOMMENDED" if _is_en else "EMPFOHLEN"
        priority_badge = {
            1: '<span style="color:#22c55e;font-size:9px;font-weight:600;">ESSENTIAL</span>',
            2: f'<span style="color:#f59e0b;font-size:9px;font-weight:600;">{_badge_2}</span>',
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
                Setup: ~{t.estimated_setup_days} {_t_setup_unit} | {t.category}
            </div>
        </div>
        """

    # Funding section
    funding_html = ""
    for f in kit.funding:
        complexity_color = {"low": "#22c55e", "medium": "#f59e0b", "high": "#ef4444"}.get(
            f.application_complexity, "#6b7280"
        )
        # KIS-1254: Wert eingedeutscht rendern — der englische Rohwert stand
        # in einem eigenen <span>, sodass die Badge-Lokalisierung ihn über
        # die Tag-Grenze nicht fand (Platin-QA english_badge, Lauf 1123).
        # KIS-1251: EN-Reports behalten die englischen Werte.
        if _is_en:
            complexity_label = f.application_complexity
        else:
            complexity_label = {"low": "niedrig", "medium": "mittel", "high": "hoch"}.get(
                f.application_complexity, f.application_complexity
            )
        funding_html += f"""
        <div style="padding:10px;background:#f0f7ff;border-radius:6px;margin-bottom:8px;border-left:3px solid #3b82f6;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <strong style="font-size:12px;color:#1f2937;">{f.name}</strong>
                <span style="font-size:11px;font-weight:600;color:#3b82f6;">{f.max_amount}</span>
            </div>
            <p style="margin:4px 0 0 0;font-size:11px;color:#495057;">{f.fit_reason}</p>
            <div style="margin-top:4px;font-size:10px;color:#9ca3af;">
                {f.provider} | {_t_complexity}: <span style="color:{complexity_color};">{complexity_label}</span>
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
                <strong style="font-size:11px;color:#1f2937;">{_t_step} {c.step}: {c.title}</strong>
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
                <div style="font-size:20px;font-weight:700;color:#059669;">{kit.estimated_total_days} {_t_days}</div>
                <div style="font-size:10px;color:#6b7280;">{_t_impl_time}</div>
            </div>
        </div>

        {f'<p style="margin:0 0 16px 0;font-size:12px;color:#374151;line-height:1.5;">{kit.description}</p>' if kit.description else ''}

        <!-- KIS-1235: align-items:start — sonst streckt sich die kürzere
             Förder-Spalte auf Zeilenhöhe und läuft bei Seitenumbruch als
             große LEERE weiße Box auf der Folgeseite weiter (Lauf 1235,
             Status S. 14/15). break-inside:avoid hält die kompakte
             Förder-Spalte zusammen. -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;align-items:start;">
            <!-- Tools Column -->
            <div style="background:#fff;padding:16px;border-radius:12px;">
                <h4 style="margin:0 0 12px 0;font-size:13px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:8px;">
                    🛠️ {tools_label}
                </h4>
                {tools_html}
            </div>

            <!-- Funding Column -->
            <div style="background:#fff;padding:16px;border-radius:12px;break-inside:avoid;page-break-inside:avoid;">
                <h4 style="margin:0 0 12px 0;font-size:13px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:8px;">
                    💰 {funding_label}
                </h4>
                {funding_html}
                {f'<div style="margin-top:12px;padding:8px;background:#dcfce7;border-radius:6px;text-align:center;"><strong style="color:#166534;font-size:12px;">{_t_funding_potential}: {kit.potential_funding}</strong></div>' if kit.potential_funding else ''}
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
                <div style="font-size:10px;color:#6b7280;">{_t_tools_in_kit}</div>
            </div>
            <div style="background:#fff;padding:12px;border-radius:8px;text-align:center;">
                <div style="font-size:20px;font-weight:700;color:#3b82f6;">{len(kit.funding)}</div>
                <div style="font-size:10px;color:#6b7280;">{_t_funding_count}</div>
            </div>
            <div style="background:#fff;padding:12px;border-radius:8px;text-align:center;">
                <div style="font-size:20px;font-weight:700;color:#f59e0b;">{kit.quick_win_count}</div>
                <div style="font-size:10px;color:#6b7280;">Quick Wins</div>
            </div>
        </div>

        <p style="margin:16px 0 0 0;font-size:10px;color:#9ca3af;text-align:center;">
            {_t_est_investment}: {kit.estimated_investment} | {summary_label}: {kit.segment_label}
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
    _is_en = (lang or "").strip().lower().startswith("en")

    tools_list = ", ".join(t.name for t in kit.tools[:3])

    # FIX-KIS-1188-ITEM5: When kit.funding is reduced to the cross-reference
    # placeholder (program_id "crossref_foerderprogramme"), the bare name
    # "→ siehe Kapitel Fördermittel" appears kontextlos in the compact block.
    # FIX-KIS-1192-ITEM-E: Crossref wandert in eigenen Absatz UNTERHALB der
    # Starter-Kit-Tabelle, damit er nicht als Tool-Listeneintrag missgelesen
    # wird (R1 S.11).
    _is_crossref_only = (
        bool(kit.funding)
        and all(
            getattr(f, "program_id", "").startswith("crossref_")
            for f in kit.funding
        )
    )
    crossref_block_html = ""
    if _is_crossref_only:
        funding_line_html = ""
        if _is_en:
            funding_count_html = (
                f"{len(kit.tools)} tools | ~{kit.estimated_total_days} days to implement"
            )
            crossref_block_html = (
                '<p style="margin:8px 0 16px 0;font-size:11px;color:#475569;'
                'font-style:italic;line-height:1.5;">'
                '<strong>Funding:</strong> '
                'You will find detailed funding programmes '
                'in the main chapter "Funding &amp; Financing".'
                '</p>'
            )
        else:
            funding_count_html = (
                f"{len(kit.tools)} Tools | ~{kit.estimated_total_days} Tage Einführung"
            )
            crossref_block_html = (
                '<p style="margin:8px 0 16px 0;font-size:11px;color:#475569;'
                'font-style:italic;line-height:1.5;">'
                '<strong>Förderung:</strong> '
                'Detaillierte Förderprogramme '
                'finden Sie im Hauptkapitel „Fördermittel &amp; Finanzierung".'
                '</p>'
            )
    else:
        funding_list = ", ".join(f.name for f in kit.funding[:2])
        if _is_en:
            funding_line_html = f"<strong>Funding:</strong> {funding_list}"
            funding_count_html = (
                f"{len(kit.tools)} tools | {len(kit.funding)} funding programmes | "
                f"~{kit.estimated_total_days} days"
            )
        else:
            funding_line_html = f"<strong>Förderung:</strong> {funding_list}"
            funding_count_html = (
                f"{len(kit.tools)} Tools | {len(kit.funding)} Förderprogramme | "
                f"~{kit.estimated_total_days} Tage"
            )

    return f"""
    <div class="starter-kit-compact" style="margin:16px 0;padding:16px;background:#ecfdf5;border-radius:8px;border:1px solid #a7f3d0;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <strong style="font-size:13px;color:#065f46;">🚀 {title}: {kit.kit_name}</strong>
                <p style="margin:4px 0 0 0;font-size:11px;color:#6b7280;">
                    {funding_count_html}
                </p>
            </div>
            {f'<div style="font-size:12px;font-weight:600;color:#059669;">{kit.potential_funding}</div>' if kit.potential_funding else ''}
        </div>
        <div style="margin-top:8px;font-size:10px;color:#495057;">
            <strong>Tools:</strong> {tools_list}{f'<br>{funding_line_html}' if funding_line_html else ''}
        </div>
    </div>
    {crossref_block_html}
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
            # KIS-1251 (Punkt 5): EN-Crossref bei lang=en
            if (lang or "").strip().lower().startswith("en"):
                kit.funding = [
                    StarterKitFunding(
                        program_id="crossref_foerderprogramme",
                        name="\u2192 see the Funding chapter",
                        provider="",
                        max_amount="",
                        fit_reason="You will find detailed funding programmes in the main chapter Funding & Financing.",
                        application_complexity="low",
                    ),
                ]
            else:
                kit.funding = [
                    StarterKitFunding(
                        program_id="crossref_foerderprogramme",
                        name="\u2192 siehe Kapitel F\u00f6rdermittel",
                        provider="",
                        max_amount="",
                        fit_reason="Detaillierte F\u00f6rderprogramme finden Sie im Hauptkapitel F\u00f6rdermittel & Finanzierung.",
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
