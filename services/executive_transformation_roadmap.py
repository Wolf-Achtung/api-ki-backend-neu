"""
Executive Transformation Roadmap - N4.1 PLATIN+++ Executive Experience Layer.

Dual-Track Transformation Roadmap providing:
- Track A: Operational Automation Roadmap (based on G36)
- Track B: Organisational Transformation Roadmap (Skills, Governance, Culture, Data, Tools)
- Time horizons for C-Level decisions (30/90/180/365 days)
- Automatic "Decision Checkpoints"
- KPI coupling: each phase contains measurable Executive Outcomes

Board-Ready. Investment-Ready. C-Level-Perfect.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPE DEFINITIONS
# =============================================================================


class RoadmapTrack(Enum):
    """Roadmap track types."""
    OPERATIONAL_AUTOMATION = "operational_automation"
    ORGANISATIONAL_TRANSFORMATION = "organisational_transformation"


class TransformationDomain(Enum):
    """Transformation domains for Track B."""
    SKILLS = "skills"
    GOVERNANCE = "governance"
    CULTURE = "culture"
    DATA_READINESS = "data_readiness"
    TOOL_ADOPTION = "tool_adoption"


class TimeHorizon(Enum):
    """Time horizons for C-Level decisions."""
    IMMEDIATE = "30_days"
    SHORT_TERM = "90_days"
    MEDIUM_TERM = "180_days"
    ANNUAL = "365_days"


class PhaseStatus(Enum):
    """Phase status indicators."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"


class DecisionType(Enum):
    """Types of decision checkpoints."""
    GO_NO_GO = "go_no_go"
    RESOURCE_ALLOCATION = "resource_allocation"
    VENDOR_SELECTION = "vendor_selection"
    STRATEGY_PIVOT = "strategy_pivot"
    SCALING_DECISION = "scaling_decision"


class PhaseKPI(TypedDict):
    """KPI definition for a phase."""
    name: str
    target_value: str
    current_value: str
    unit: str
    trend: str


class DecisionCheckpoint(TypedDict):
    """Decision checkpoint definition."""
    checkpoint_id: str
    decision_type: str
    timeline: str
    description: str
    decision_makers: List[str]
    required_inputs: List[str]
    success_criteria: List[str]


class RoadmapPhase(TypedDict):
    """Single phase in the roadmap."""
    phase_id: str
    name: str
    timeline: str
    duration_days: int
    objectives: List[str]
    deliverables: List[str]
    kpis: List[PhaseKPI]
    decision_checkpoints: List[DecisionCheckpoint]
    dependencies: List[str]
    resources: Dict[str, Any]
    status: str


class TransformationTrack(TypedDict):
    """Complete transformation track."""
    track_type: str
    phases: List[RoadmapPhase]
    total_duration_days: int
    critical_path: List[str]
    risk_factors: List[str]


class ExecutiveRoadmap(TypedDict):
    """Complete executive roadmap."""
    operational_track: TransformationTrack
    organisational_track: TransformationTrack
    integrated_timeline: List[Dict[str, Any]]
    executive_summary: str
    total_investment: str
    expected_roi: str


# =============================================================================
# CONFIGURATION
# =============================================================================


ROADMAP_CONFIG: Dict[str, Any] = {
    "max_phases_per_track": 6,
    "min_phase_duration_days": 30,
    "max_phase_duration_days": 180,
    "checkpoint_frequency_days": 45,
    "kpis_per_phase": 3,
}


# Phase templates for operational automation (Track A)
OPERATIONAL_PHASE_TEMPLATES: List[Dict[str, Any]] = [
    {
        "name": "Assessment & Quick Wins",
        "duration_days": 45,
        "timeline": "Tag 1-45",
        "objectives": [
            "Prozesslandschaft analysieren",
            "Automatisierungspotenziale identifizieren",
            "Quick-Win-Projekte starten",
        ],
        "deliverables": [
            "Prozess-Mapping",
            "Automatisierungs-Shortlist",
            "Pilotprojekt-Kick-off",
        ],
        "default_kpis": [
            {"name": "Prozesse analysiert", "unit": "Anzahl", "target": "20+"},
            {"name": "Quick Wins identifiziert", "unit": "Anzahl", "target": "5+"},
            {"name": "Pilotprojekte gestartet", "unit": "Anzahl", "target": "2+"},
        ],
    },
    {
        "name": "Pilot & Proof of Concept",
        "duration_days": 60,
        "timeline": "Tag 46-105",
        "objectives": [
            "Pilotprojekte durchführen",
            "ROI validieren",
            "Change-Readiness aufbauen",
        ],
        "deliverables": [
            "Pilot-Ergebnisse",
            "Validierter Business Case",
            "Skalierungsplan",
        ],
        "default_kpis": [
            {"name": "Pilotprojekte abgeschlossen", "unit": "Anzahl", "target": "2"},
            {"name": "Realisierter ROI", "unit": "%", "target": ">50%"},
            {"name": "Mitarbeiterzufriedenheit", "unit": "Score", "target": ">3.5/5"},
        ],
    },
    {
        "name": "Skalierung Phase 1",
        "duration_days": 90,
        "timeline": "Tag 106-195",
        "objectives": [
            "Erfolgreiche Piloten skalieren",
            "Infrastruktur ausbauen",
            "Team-Kapazitäten aufbauen",
        ],
        "deliverables": [
            "Skalierte Automatisierungen",
            "Produktions-Infrastruktur",
            "Geschultes Team",
        ],
        "default_kpis": [
            {"name": "Automatisierte Prozesse", "unit": "Anzahl", "target": "10+"},
            {"name": "FTE-Einsparung", "unit": "FTE", "target": "3+"},
            {"name": "Fehlerreduktion", "unit": "%", "target": ">30%"},
        ],
    },
    {
        "name": "Skalierung Phase 2",
        "duration_days": 90,
        "timeline": "Tag 196-285",
        "objectives": [
            "Unternehmensweite Ausrollung",
            "Center of Excellence etablieren",
            "Governance-Strukturen festigen",
        ],
        "deliverables": [
            "Enterprise Deployment",
            "CoE operativ",
            "Governance Framework",
        ],
        "default_kpis": [
            {"name": "Unternehmensabdeckung", "unit": "%", "target": ">60%"},
            {"name": "Automatisierungsgrad", "unit": "%", "target": ">40%"},
            {"name": "Kostenreduktion", "unit": "%", "target": ">15%"},
        ],
    },
    {
        "name": "Optimierung & Innovation",
        "duration_days": 80,
        "timeline": "Tag 286-365",
        "objectives": [
            "Kontinuierliche Optimierung",
            "Neue Use Cases identifizieren",
            "KI-Maturität steigern",
        ],
        "deliverables": [
            "Optimierungs-Roadmap",
            "Innovation Pipeline",
            "Reifegradsteigerung",
        ],
        "default_kpis": [
            {"name": "Optimierungspotenzial realisiert", "unit": "%", "target": ">80%"},
            {"name": "Neue Use Cases", "unit": "Anzahl", "target": "10+"},
            {"name": "KI-Reifegrad", "unit": "Level", "target": "3+/5"},
        ],
    },
]


# Phase templates for organisational transformation (Track B)
ORGANISATIONAL_PHASE_TEMPLATES: Dict[TransformationDomain, Dict[str, Any]] = {
    TransformationDomain.SKILLS: {
        "name": "Skills & Talent Development",
        "objectives": [
            "Skill-Gap-Analyse durchführen",
            "Schulungsprogramm entwickeln",
            "KI-Champions ausbilden",
        ],
        "deliverables": [
            "Skill-Matrix",
            "Trainingskatalog",
            "Champion-Netzwerk",
        ],
        "kpis": [
            {"name": "Mitarbeiter geschult", "unit": "%", "target": ">60%"},
            {"name": "KI-Champions", "unit": "Anzahl", "target": "10+"},
            {"name": "Skill-Score-Verbesserung", "unit": "%", "target": "+20%"},
        ],
    },
    TransformationDomain.GOVERNANCE: {
        "name": "AI Governance & Compliance",
        "objectives": [
            "AI Governance Framework etablieren",
            "Compliance-Strukturen aufbauen",
            "Risikomanagement implementieren",
        ],
        "deliverables": [
            "Governance Framework",
            "Compliance-Checklisten",
            "Risiko-Register",
        ],
        "kpis": [
            {"name": "Governance-Reife", "unit": "Level", "target": "3+/5"},
            {"name": "Compliance-Score", "unit": "%", "target": ">85%"},
            {"name": "Risiken mitigiert", "unit": "%", "target": ">90%"},
        ],
    },
    TransformationDomain.CULTURE: {
        "name": "Culture & Change Management",
        "objectives": [
            "Change-Kommunikation starten",
            "Akzeptanz fördern",
            "Innovationskultur stärken",
        ],
        "deliverables": [
            "Kommunikationsplan",
            "Change-Monitoring",
            "Kultur-Initiativen",
        ],
        "kpis": [
            {"name": "Mitarbeiterakzeptanz", "unit": "%", "target": ">70%"},
            {"name": "Change-Readiness-Index", "unit": "Score", "target": ">3.5/5"},
            {"name": "Innovation-Score", "unit": "Index", "target": ">60"},
        ],
    },
    TransformationDomain.DATA_READINESS: {
        "name": "Data Readiness & Quality",
        "objectives": [
            "Datenqualität verbessern",
            "Dateninfrastruktur modernisieren",
            "Data Governance etablieren",
        ],
        "deliverables": [
            "Data Quality Report",
            "Infrastruktur-Upgrade",
            "Data Governance Policy",
        ],
        "kpis": [
            {"name": "Datenqualität-Score", "unit": "%", "target": ">85%"},
            {"name": "Daten-Verfügbarkeit", "unit": "%", "target": ">95%"},
            {"name": "Data Governance Maturity", "unit": "Level", "target": "3+/5"},
        ],
    },
    TransformationDomain.TOOL_ADOPTION: {
        "name": "Tool Adoption & Integration",
        "objectives": [
            "Tool-Landschaft evaluieren",
            "Ausgewählte Tools implementieren",
            "Integration sicherstellen",
        ],
        "deliverables": [
            "Tool-Evaluierung",
            "Implementierung",
            "Integrations-Layer",
        ],
        "kpis": [
            {"name": "Tool-Adoption-Rate", "unit": "%", "target": ">75%"},
            {"name": "Integration-Score", "unit": "%", "target": ">80%"},
            {"name": "User Satisfaction", "unit": "Score", "target": ">4/5"},
        ],
    },
}


# Decision checkpoint templates
DECISION_CHECKPOINT_TEMPLATES: Dict[TimeHorizon, Dict[str, Any]] = {
    TimeHorizon.IMMEDIATE: {
        "type": DecisionType.GO_NO_GO,
        "description": "Go/No-Go-Entscheidung für Pilotprojekte",
        "decision_makers": ["Projektleitung", "Bereichsleitung"],
        "required_inputs": [
            "Pilotplan",
            "Ressourcenplanung",
            "Risikoanalyse",
        ],
        "success_criteria": [
            "Business Case validiert",
            "Ressourcen gesichert",
            "Stakeholder-Buy-in",
        ],
    },
    TimeHorizon.SHORT_TERM: {
        "type": DecisionType.RESOURCE_ALLOCATION,
        "description": "Ressourcen-Allokation für Skalierungsphase",
        "decision_makers": ["Geschäftsführung", "CFO"],
        "required_inputs": [
            "Pilot-Ergebnisse",
            "Skalierungsplan",
            "Budget-Anforderung",
        ],
        "success_criteria": [
            "Pilot-Erfolg nachgewiesen",
            "ROI bestätigt",
            "Skalierungsplan genehmigt",
        ],
    },
    TimeHorizon.MEDIUM_TERM: {
        "type": DecisionType.SCALING_DECISION,
        "description": "Skalierungs-Entscheidung für Enterprise Rollout",
        "decision_makers": ["Vorstand", "Steering Committee"],
        "required_inputs": [
            "Phase-1-Ergebnisse",
            "Enterprise-Roadmap",
            "Change-Readiness-Report",
        ],
        "success_criteria": [
            "Phase-1-KPIs erreicht",
            "Organisation bereit",
            "Budget freigegeben",
        ],
    },
    TimeHorizon.ANNUAL: {
        "type": DecisionType.STRATEGY_PIVOT,
        "description": "Strategische Neubewertung und Ausrichtung",
        "decision_makers": ["Aufsichtsrat", "Vorstand"],
        "required_inputs": [
            "Jahresreview",
            "Marktentwicklung",
            "Technologie-Trends",
        ],
        "success_criteria": [
            "Jahresziele erreicht",
            "Wettbewerbsposition gestärkt",
            "Investitions-Rendite positiv",
        ],
    },
}


# =============================================================================
# OPERATIONAL ROADMAP BUILDER
# =============================================================================


class OperationalRoadmapBuilder:
    """
    Builds Track A: Operational Automation Roadmap.

    Based on G36 process analysis and automation assessment.
    """

    def __init__(self) -> None:
        self._phase_counter = 0

    def build_track(
        self,
        automation_data: Dict[str, Any],
        start_date: Optional[datetime] = None,
    ) -> TransformationTrack:
        """
        Build operational automation track.

        Args:
            automation_data: Automation analysis data
            start_date: Optional start date

        Returns:
            TransformationTrack for operational automation
        """
        if start_date is None:
            start_date = datetime.now()

        phases = self._build_phases(automation_data, start_date)
        critical_path = self._identify_critical_path(phases)
        risk_factors = self._identify_risk_factors(automation_data)
        total_duration = sum(p["duration_days"] for p in phases)

        return TransformationTrack(
            track_type=RoadmapTrack.OPERATIONAL_AUTOMATION.value,
            phases=phases,
            total_duration_days=total_duration,
            critical_path=critical_path,
            risk_factors=risk_factors,
        )

    def _build_phases(
        self,
        automation_data: Dict[str, Any],
        start_date: datetime,
    ) -> List[RoadmapPhase]:
        """Build phases from templates and data."""
        phases: List[RoadmapPhase] = []
        current_date = start_date

        automation_potential = automation_data.get("automation_percentage", 40)

        for template in OPERATIONAL_PHASE_TEMPLATES:
            # Adjust duration based on automation potential
            duration = self._adjust_duration(
                template["duration_days"],
                automation_potential,
            )

            phase = self._create_phase(
                template,
                current_date,
                duration,
                automation_data,
            )
            phases.append(phase)

            current_date += timedelta(days=duration)

        return phases

    def _adjust_duration(
        self,
        base_duration: int,
        automation_potential: float,
    ) -> int:
        """Adjust phase duration based on automation potential."""
        # Higher potential = slightly faster execution
        factor = 1.0 - (automation_potential / 200)  # Max 20% reduction
        adjusted = int(base_duration * factor)

        return max(
            ROADMAP_CONFIG["min_phase_duration_days"],
            min(adjusted, ROADMAP_CONFIG["max_phase_duration_days"]),
        )

    def _create_phase(
        self,
        template: Dict[str, Any],
        start_date: datetime,
        duration: int,
        automation_data: Dict[str, Any],
    ) -> RoadmapPhase:
        """Create a single phase from template."""
        self._phase_counter += 1
        phase_id = f"OP_{self._phase_counter:02d}"

        end_date = start_date + timedelta(days=duration)
        timeline = f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"

        # Build KPIs
        kpis = self._build_kpis(template.get("default_kpis", []))

        # Build decision checkpoints
        checkpoints = self._build_checkpoints(phase_id, start_date, duration)

        return RoadmapPhase(
            phase_id=phase_id,
            name=template["name"],
            timeline=timeline,
            duration_days=duration,
            objectives=template["objectives"],
            deliverables=template["deliverables"],
            kpis=kpis,
            decision_checkpoints=checkpoints,
            dependencies=[],
            resources=self._estimate_resources(template, automation_data),
            status=PhaseStatus.NOT_STARTED.value,
        )

    def _build_kpis(
        self,
        kpi_templates: List[Dict[str, Any]],
    ) -> List[PhaseKPI]:
        """Build KPI structures from templates."""
        return [
            PhaseKPI(
                name=kpi.get("name", "KPI"),
                target_value=kpi.get("target", "N/A"),
                current_value="0",
                unit=kpi.get("unit", ""),
                trend="neutral",
            )
            for kpi in kpi_templates[:ROADMAP_CONFIG["kpis_per_phase"]]
        ]

    def _build_checkpoints(
        self,
        phase_id: str,
        start_date: datetime,
        duration: int,
    ) -> List[DecisionCheckpoint]:
        """Build decision checkpoints for phase."""
        checkpoints: List[DecisionCheckpoint] = []

        # Checkpoint at phase midpoint and end
        midpoint = start_date + timedelta(days=duration // 2)
        endpoint = start_date + timedelta(days=duration)

        checkpoints.append(DecisionCheckpoint(
            checkpoint_id=f"{phase_id}_MID",
            decision_type=DecisionType.GO_NO_GO.value,
            timeline=midpoint.strftime("%d.%m.%Y"),
            description="Mid-Phase Review und Kurskorrektur",
            decision_makers=["Projektleitung"],
            required_inputs=["Fortschrittsbericht", "Risiko-Update"],
            success_criteria=["Meilensteine im Plan", "Budget im Rahmen"],
        ))

        checkpoints.append(DecisionCheckpoint(
            checkpoint_id=f"{phase_id}_END",
            decision_type=DecisionType.SCALING_DECISION.value,
            timeline=endpoint.strftime("%d.%m.%Y"),
            description="Phase-Abschluss und Übergang",
            decision_makers=["Projektleitung", "Steering Committee"],
            required_inputs=["Phase-Report", "KPI-Auswertung"],
            success_criteria=["KPIs erreicht", "Deliverables abgenommen"],
        ))

        return checkpoints

    def _estimate_resources(
        self,
        template: Dict[str, Any],
        automation_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Estimate resources for phase."""
        base_fte = automation_data.get("fte_required", 5)

        return {
            "fte_internal": base_fte * 0.6,
            "fte_external": base_fte * 0.4,
            "budget_range": "50-150 Tsd EUR",
            "tools": ["Automation Platform", "Analytics Tool"],
        }

    def _identify_critical_path(
        self,
        phases: List[RoadmapPhase],
    ) -> List[str]:
        """Identify critical path phases."""
        # For sequential phases, all are critical
        return [p["phase_id"] for p in phases]

    def _identify_risk_factors(
        self,
        automation_data: Dict[str, Any],
    ) -> List[str]:
        """Identify risk factors for operational track."""
        risks = [
            "Change Resistance bei Mitarbeitern",
            "Technische Integrationskomplexität",
            "Ressourcenverfügbarkeit",
        ]

        if automation_data.get("data_quality", 100) < 70:
            risks.append("Unzureichende Datenqualität")

        if automation_data.get("skill_gaps", []):
            risks.append("Skill-Gaps im Team")

        return risks


# =============================================================================
# ORGANISATIONAL ROADMAP BUILDER
# =============================================================================


class OrganisationalRoadmapBuilder:
    """
    Builds Track B: Organisational Transformation Roadmap.

    Covers Skills, Governance, Culture, Data Readiness, Tool Adoption.
    """

    def __init__(self) -> None:
        self._phase_counter = 0

    def build_track(
        self,
        org_data: Dict[str, Any],
        start_date: Optional[datetime] = None,
    ) -> TransformationTrack:
        """
        Build organisational transformation track.

        Args:
            org_data: Organisational assessment data
            start_date: Optional start date

        Returns:
            TransformationTrack for organisational transformation
        """
        if start_date is None:
            start_date = datetime.now()

        phases = self._build_phases(org_data, start_date)
        critical_path = self._identify_critical_path(phases, org_data)
        risk_factors = self._identify_risk_factors(org_data)
        total_duration = max(
            sum(p["duration_days"] for p in phases[:3]),
            365,
        )  # Parallel execution possible

        return TransformationTrack(
            track_type=RoadmapTrack.ORGANISATIONAL_TRANSFORMATION.value,
            phases=phases,
            total_duration_days=total_duration,
            critical_path=critical_path,
            risk_factors=risk_factors,
        )

    def _build_phases(
        self,
        org_data: Dict[str, Any],
        start_date: datetime,
    ) -> List[RoadmapPhase]:
        """Build phases for each transformation domain."""
        phases: List[RoadmapPhase] = []

        for domain in TransformationDomain:
            template = ORGANISATIONAL_PHASE_TEMPLATES.get(domain)
            if template is None:
                continue

            # Calculate domain-specific duration
            duration = self._calculate_domain_duration(domain, org_data)

            phase = self._create_domain_phase(
                domain,
                template,
                start_date,
                duration,
                org_data,
            )
            phases.append(phase)

        return phases

    def _calculate_domain_duration(
        self,
        domain: TransformationDomain,
        org_data: Dict[str, Any],
    ) -> int:
        """Calculate duration based on current maturity."""
        maturity_key = f"{domain.value}_maturity"
        maturity = org_data.get(maturity_key, 50)

        # Lower maturity = longer duration
        base_duration = 120
        adjustment = (100 - maturity) / 100 * 60  # Up to 60 days extra

        return int(base_duration + adjustment)

    def _create_domain_phase(
        self,
        domain: TransformationDomain,
        template: Dict[str, Any],
        start_date: datetime,
        duration: int,
        org_data: Dict[str, Any],
    ) -> RoadmapPhase:
        """Create phase for a transformation domain."""
        self._phase_counter += 1
        phase_id = f"ORG_{domain.value[:3].upper()}_{self._phase_counter:02d}"

        end_date = start_date + timedelta(days=duration)
        timeline = f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"

        # Build KPIs
        kpis = [
            PhaseKPI(
                name=kpi["name"],
                target_value=kpi["target"],
                current_value="0",
                unit=kpi["unit"],
                trend="neutral",
            )
            for kpi in template.get("kpis", [])
        ]

        # Build checkpoints
        checkpoints = self._build_domain_checkpoints(
            phase_id, domain, start_date, duration,
        )

        return RoadmapPhase(
            phase_id=phase_id,
            name=template["name"],
            timeline=timeline,
            duration_days=duration,
            objectives=template["objectives"],
            deliverables=template["deliverables"],
            kpis=kpis,
            decision_checkpoints=checkpoints,
            dependencies=self._get_domain_dependencies(domain),
            resources=self._estimate_domain_resources(domain, org_data),
            status=PhaseStatus.NOT_STARTED.value,
        )

    def _build_domain_checkpoints(
        self,
        phase_id: str,
        domain: TransformationDomain,
        start_date: datetime,
        duration: int,
    ) -> List[DecisionCheckpoint]:
        """Build checkpoints for domain phase."""
        checkpoints: List[DecisionCheckpoint] = []

        # Quarterly checkpoint
        q1_date = start_date + timedelta(days=min(90, duration))

        checkpoints.append(DecisionCheckpoint(
            checkpoint_id=f"{phase_id}_Q1",
            decision_type=DecisionType.RESOURCE_ALLOCATION.value,
            timeline=q1_date.strftime("%d.%m.%Y"),
            description=f"{domain.value} Quarterly Review",
            decision_makers=["HR/IT Leitung", "Projektleitung"],
            required_inputs=["Fortschrittsbericht", "Ressourcenbedarf"],
            success_criteria=["Meilensteine erreicht", "Budget im Plan"],
        ))

        return checkpoints

    def _get_domain_dependencies(
        self,
        domain: TransformationDomain,
    ) -> List[str]:
        """Get dependencies for a domain."""
        dependencies: Dict[TransformationDomain, List[str]] = {
            TransformationDomain.SKILLS: [],
            TransformationDomain.GOVERNANCE: [],
            TransformationDomain.CULTURE: ["ORG_SKI"],
            TransformationDomain.DATA_READINESS: ["ORG_GOV"],
            TransformationDomain.TOOL_ADOPTION: ["ORG_DAT", "ORG_SKI"],
        }

        return dependencies.get(domain, [])

    def _estimate_domain_resources(
        self,
        domain: TransformationDomain,
        org_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Estimate resources for domain."""
        resource_templates: Dict[TransformationDomain, Dict[str, Any]] = {
            TransformationDomain.SKILLS: {
                "fte_internal": 1.5,
                "fte_external": 1.0,
                "budget_range": "80-120 Tsd EUR",
                "tools": ["LMS", "Assessment Platform"],
            },
            TransformationDomain.GOVERNANCE: {
                "fte_internal": 1.0,
                "fte_external": 0.5,
                "budget_range": "40-80 Tsd EUR",
                "tools": ["GRC Platform", "Policy Management"],
            },
            TransformationDomain.CULTURE: {
                "fte_internal": 2.0,
                "fte_external": 0.5,
                "budget_range": "60-100 Tsd EUR",
                "tools": ["Survey Tool", "Collaboration Platform"],
            },
            TransformationDomain.DATA_READINESS: {
                "fte_internal": 2.0,
                "fte_external": 2.0,
                "budget_range": "150-250 Tsd EUR",
                "tools": ["Data Quality Tool", "Master Data Management"],
            },
            TransformationDomain.TOOL_ADOPTION: {
                "fte_internal": 1.5,
                "fte_external": 1.5,
                "budget_range": "100-200 Tsd EUR",
                "tools": ["AI Platform", "Integration Layer"],
            },
        }

        return resource_templates.get(domain, {
            "fte_internal": 1.0,
            "fte_external": 0.5,
            "budget_range": "50-100 Tsd EUR",
            "tools": [],
        })

    def _identify_critical_path(
        self,
        phases: List[RoadmapPhase],
        org_data: Dict[str, Any],
    ) -> List[str]:
        """Identify critical path in organisational track."""
        # Governance and Data are typically critical
        critical_domains = ["GOV", "DAT"]
        return [
            p["phase_id"] for p in phases
            if any(d in p["phase_id"] for d in critical_domains)
        ]

    def _identify_risk_factors(
        self,
        org_data: Dict[str, Any],
    ) -> List[str]:
        """Identify risk factors for organisational track."""
        risks = [
            "Widerstand gegen Veränderung",
            "Mangelnde Management-Attention",
            "Konkurrierende Prioritäten",
        ]

        if org_data.get("culture_maturity", 100) < 50:
            risks.append("Schwache Innovationskultur")

        if org_data.get("data_readiness", 100) < 60:
            risks.append("Unzureichende Datenreife")

        return risks


# =============================================================================
# MAIN ENGINE CLASS
# =============================================================================


class ExecutiveTransformationRoadmapEngine:
    """
    Main engine for Executive Transformation Roadmap.

    Orchestrates:
    - Track A: Operational Automation
    - Track B: Organisational Transformation
    - Integrated timeline with decision checkpoints
    """

    def __init__(self) -> None:
        self._operational_builder = OperationalRoadmapBuilder()
        self._organisational_builder = OrganisationalRoadmapBuilder()

    def build_roadmap(
        self,
        analysis_data: Dict[str, Any],
        start_date: Optional[datetime] = None,
    ) -> ExecutiveRoadmap:
        """
        Build complete executive transformation roadmap.

        Args:
            analysis_data: Full analysis data
            start_date: Optional start date

        Returns:
            ExecutiveRoadmap with both tracks
        """
        log.info("[N4.1-Roadmap] Building executive transformation roadmap...")

        if start_date is None:
            start_date = datetime.now()

        # Build both tracks
        automation_data = analysis_data.get("automation", {})
        org_data = analysis_data.get("organization", {})

        operational_track = self._operational_builder.build_track(
            automation_data, start_date,
        )
        organisational_track = self._organisational_builder.build_track(
            org_data, start_date,
        )

        # Create integrated timeline
        integrated_timeline = self._create_integrated_timeline(
            operational_track,
            organisational_track,
        )

        # Generate summary
        summary = self._generate_executive_summary(
            operational_track,
            organisational_track,
            analysis_data,
        )

        # Calculate total investment and ROI
        total_investment = self._calculate_total_investment(
            operational_track,
            organisational_track,
        )
        expected_roi = analysis_data.get("kpis", {}).get("roi_percentage", 100)

        log.info(
            "[N4.1-Roadmap] Roadmap complete: %d operational phases, "
            "%d organisational phases",
            len(operational_track["phases"]),
            len(organisational_track["phases"]),
        )

        return ExecutiveRoadmap(
            operational_track=operational_track,
            organisational_track=organisational_track,
            integrated_timeline=integrated_timeline,
            executive_summary=summary,
            total_investment=total_investment,
            expected_roi=f"{expected_roi}%",
        )

    def get_decision_checkpoints(
        self,
        roadmap: ExecutiveRoadmap,
        horizon: Optional[TimeHorizon] = None,
    ) -> List[DecisionCheckpoint]:
        """
        Get decision checkpoints from roadmap.

        Args:
            roadmap: Executive roadmap
            horizon: Optional filter by time horizon

        Returns:
            List of decision checkpoints
        """
        checkpoints: List[DecisionCheckpoint] = []

        # Collect from operational track
        for phase in roadmap["operational_track"]["phases"]:
            checkpoints.extend(phase["decision_checkpoints"])

        # Collect from organisational track
        for phase in roadmap["organisational_track"]["phases"]:
            checkpoints.extend(phase["decision_checkpoints"])

        # Sort by timeline
        checkpoints.sort(key=lambda x: x["timeline"])

        return checkpoints

    def _create_integrated_timeline(
        self,
        op_track: TransformationTrack,
        org_track: TransformationTrack,
    ) -> List[Dict[str, Any]]:
        """Create integrated timeline view."""
        timeline: List[Dict[str, Any]] = []

        # Add milestones from both tracks
        for horizon in TimeHorizon:
            days = int(horizon.value.replace("_days", ""))

            timeline.append({
                "day": days,
                "label": f"Tag {days}",
                "horizon": horizon.value,
                "checkpoint": DECISION_CHECKPOINT_TEMPLATES[horizon],
                "operational_phase": self._get_phase_at_day(op_track, days),
                "organisational_phases": self._get_org_phases_at_day(org_track, days),
            })

        return timeline

    def _get_phase_at_day(
        self,
        track: TransformationTrack,
        day: int,
    ) -> Optional[str]:
        """Get operational phase active at given day."""
        cumulative = 0
        for phase in track["phases"]:
            cumulative += phase["duration_days"]
            if cumulative >= day:
                return phase["name"]
        return None

    def _get_org_phases_at_day(
        self,
        track: TransformationTrack,
        day: int,
    ) -> List[str]:
        """Get organisational phases active at given day."""
        # Assumes parallel execution
        active = []
        for phase in track["phases"]:
            if phase["duration_days"] >= day:
                active.append(phase["name"])
        return active

    def _generate_executive_summary(
        self,
        op_track: TransformationTrack,
        org_track: TransformationTrack,
        analysis_data: Dict[str, Any],
    ) -> str:
        """Generate executive summary for roadmap."""
        company = analysis_data.get("company_name", "das Unternehmen")
        op_duration = op_track["total_duration_days"]
        org_duration = org_track["total_duration_days"]

        return (
            f"Die KI-Transformation für {company} umfasst zwei parallel laufende "
            f"Transformations-Tracks: Der operative Track fokussiert auf "
            f"Prozessautomatisierung über {op_duration} Tage in "
            f"{len(op_track['phases'])} Phasen. Der organisationale Track "
            f"adressiert Skills, Governance, Kultur, Daten und Tools über "
            f"{org_duration} Tage in {len(org_track['phases'])} parallelen "
            f"Workstreams. Entscheidungspunkte sind für Tag 30, 90, 180 und 365 "
            f"definiert."
        )

    def _calculate_total_investment(
        self,
        op_track: TransformationTrack,
        org_track: TransformationTrack,
    ) -> str:
        """Calculate total investment estimate."""
        # Simplified calculation based on resource estimates
        # In reality, this would parse budget ranges and sum up
        op_phases = len(op_track["phases"])
        org_phases = len(org_track["phases"])

        # Average estimate per phase
        avg_op_budget = 100_000  # EUR
        avg_org_budget = 100_000  # EUR

        total = (op_phases * avg_op_budget) + (org_phases * avg_org_budget)

        if total >= 1_000_000:
            return f"{total / 1_000_000:.1f} Mio EUR"
        return f"{total / 1000:.0f} Tsd EUR"


# =============================================================================
# SINGLETON & CONVENIENCE FUNCTIONS
# =============================================================================


_engine_instance: Optional[ExecutiveTransformationRoadmapEngine] = None


def get_roadmap_engine() -> ExecutiveTransformationRoadmapEngine:
    """Get or create the singleton roadmap engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ExecutiveTransformationRoadmapEngine()
    return _engine_instance


def build_transformation_roadmap(
    analysis_data: Dict[str, Any],
    start_date: Optional[datetime] = None,
) -> ExecutiveRoadmap:
    """
    Build executive transformation roadmap.

    Convenience function for external use.

    Args:
        analysis_data: Full analysis data
        start_date: Optional start date

    Returns:
        ExecutiveRoadmap with both tracks
    """
    engine = get_roadmap_engine()
    return engine.build_roadmap(analysis_data, start_date)


def get_decision_checkpoints_by_horizon(
    roadmap: ExecutiveRoadmap,
    horizon: TimeHorizon,
) -> List[DecisionCheckpoint]:
    """
    Get decision checkpoints for a specific time horizon.

    Convenience function for external use.

    Args:
        roadmap: Executive roadmap
        horizon: Time horizon filter

    Returns:
        List of relevant checkpoints
    """
    engine = get_roadmap_engine()
    return engine.get_decision_checkpoints(roadmap, horizon)
