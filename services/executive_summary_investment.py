"""
Executive Summary Investment v6 - N4.1 PLATIN+++ Executive Experience Layer.

Investment Memo Format providing:
- The Investment Thesis (3 sentences)
- The Strategic Rationale (Bullet-Logic)
- The Financial Case (KPI-Triangle + ROI Narrative)
- The Operational Case (Automation Potential + Process Bottlenecks)
- The Risk Case (AI Act + DSGVO + Vendor Exposure)
- The 90-Day Mandate (What leadership must do now)

GPT + Claude Dual Mode support.
Board-Ready. Investment-Ready. C-Level-Perfect.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPE DEFINITIONS
# =============================================================================


class SummarySection(Enum):
    """Investment memo sections."""
    INVESTMENT_THESIS = "investment_thesis"
    STRATEGIC_RATIONALE = "strategic_rationale"
    FINANCIAL_CASE = "financial_case"
    OPERATIONAL_CASE = "operational_case"
    RISK_CASE = "risk_case"
    NINETY_DAY_MANDATE = "ninety_day_mandate"


class InvestmentSentiment(Enum):
    """Investment recommendation sentiment."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    CAUTIOUS = "cautious"
    DEFER = "defer"


class ModelPreference(Enum):
    """Model preference for section generation."""
    GPT = "gpt"
    CLAUDE = "claude"
    DUAL = "dual"


class InvestmentThesis(TypedDict):
    """Investment thesis structure."""
    headline: str
    sentences: List[str]
    sentiment: str
    confidence_level: float


class StrategicRationale(TypedDict):
    """Strategic rationale structure."""
    core_argument: str
    supporting_points: List[str]
    market_position: str
    competitive_advantage: str


class FinancialCase(TypedDict):
    """Financial case structure."""
    kpi_triangle: Dict[str, Any]
    roi_narrative: str
    investment_required: str
    payback_period: str
    npv_assessment: str


class OperationalCase(TypedDict):
    """Operational case structure."""
    automation_potential: str
    automation_percentage: float
    process_bottlenecks: List[str]
    quick_wins: List[str]
    resource_requirements: str


class RiskCase(TypedDict):
    """Risk case structure."""
    ai_act_exposure: str
    dsgvo_compliance: str
    vendor_exposure: str
    mitigation_priorities: List[str]
    risk_score: float


class NinetyDayMandate(TypedDict):
    """90-day mandate structure."""
    immediate_actions: List[str]
    decision_deadlines: List[str]
    resource_allocations: List[str]
    success_metrics: List[str]


class ExecutiveSummaryV6(TypedDict):
    """Complete Executive Summary v6 structure."""
    investment_thesis: InvestmentThesis
    strategic_rationale: StrategicRationale
    financial_case: FinancialCase
    operational_case: OperationalCase
    risk_case: RiskCase
    ninety_day_mandate: NinetyDayMandate
    generation_metadata: Dict[str, Any]


# =============================================================================
# CONFIGURATION
# =============================================================================


SUMMARY_CONFIG: Dict[str, Any] = {
    "thesis_sentence_count": 3,
    "max_rationale_points": 5,
    "max_bottlenecks": 4,
    "max_quick_wins": 3,
    "max_mandate_items": 5,
    "confidence_threshold": 0.7,
    "risk_threshold": 0.3,
}


# Section-Model mapping for dual generation
SECTION_MODEL_MAPPING: Dict[SummarySection, ModelPreference] = {
    SummarySection.INVESTMENT_THESIS: ModelPreference.CLAUDE,
    SummarySection.STRATEGIC_RATIONALE: ModelPreference.CLAUDE,
    SummarySection.FINANCIAL_CASE: ModelPreference.GPT,
    SummarySection.OPERATIONAL_CASE: ModelPreference.GPT,
    SummarySection.RISK_CASE: ModelPreference.DUAL,
    SummarySection.NINETY_DAY_MANDATE: ModelPreference.CLAUDE,
}


# Investment sentiment thresholds
SENTIMENT_THRESHOLDS: Dict[InvestmentSentiment, Dict[str, float]] = {
    InvestmentSentiment.STRONG_BUY: {"roi_min": 150, "risk_max": 0.3},
    InvestmentSentiment.BUY: {"roi_min": 100, "risk_max": 0.5},
    InvestmentSentiment.HOLD: {"roi_min": 50, "risk_max": 0.6},
    InvestmentSentiment.CAUTIOUS: {"roi_min": 20, "risk_max": 0.8},
    InvestmentSentiment.DEFER: {"roi_min": 0, "risk_max": 1.0},
}


# =============================================================================
# INVESTMENT THESIS GENERATOR
# =============================================================================


class InvestmentThesisGenerator:
    """
    Generates the Investment Thesis section.

    Produces exactly 3 sentences that capture:
    1. The opportunity
    2. The competitive imperative
    3. The recommended action
    """

    THESIS_TEMPLATES: Dict[InvestmentSentiment, List[str]] = {
        InvestmentSentiment.STRONG_BUY: [
            "{company} steht vor einer transformativen Chance, durch KI-Adoption "
            "einen nachhaltigen Wettbewerbsvorteil von {advantage}% zu realisieren.",
            "Der Markt bewegt sich schnell – Wettbewerber investieren bereits "
            "{competitor_investment} in vergleichbare Initiativen, was sofortiges "
            "Handeln zur strategischen Notwendigkeit macht.",
            "Wir empfehlen eine sofortige Investitionsfreigabe von {investment} "
            "mit erwarteter Amortisation innerhalb von {payback} Monaten.",
        ],
        InvestmentSentiment.BUY: [
            "{company} kann durch gezielte KI-Integration erhebliche "
            "Effizienzgewinne von {efficiency}% in Kernprozessen erzielen.",
            "Die Wettbewerbslandschaft erfordert eine proaktive Positionierung, "
            "um den technologischen Anschluss nicht zu verlieren.",
            "Wir empfehlen eine strukturierte Investition von {investment} "
            "mit klarem Fokus auf {focus_area}.",
        ],
        InvestmentSentiment.HOLD: [
            "{company} verfügt über moderate KI-Potenziale, die eine sorgfältige "
            "Evaluation und selektive Investitionen rechtfertigen.",
            "Der Marktdruck ist präsent, aber nicht kritisch – ein "
            "risikobewusster Ansatz ist angemessen.",
            "Wir empfehlen eine Pilotphase mit begrenztem Investment von "
            "{investment} vor weiteren Commitments.",
        ],
        InvestmentSentiment.CAUTIOUS: [
            "{company} sollte KI-Investitionen mit Vorsicht angehen, "
            "da signifikante Hürden die Realisierung des vollen Potenzials erschweren.",
            "Strukturelle Voraussetzungen wie {prerequisites} müssen zunächst "
            "adressiert werden, bevor größere Investitionen sinnvoll sind.",
            "Wir empfehlen einen explorativen Ansatz mit minimaler Exposition "
            "von maximal {investment}.",
        ],
        InvestmentSentiment.DEFER: [
            "{company} ist aktuell nicht bereit für signifikante KI-Investitionen – "
            "grundlegende Voraussetzungen fehlen.",
            "Investitionen in diesem Stadium würden hohe Risiken bei "
            "ungewisser Rendite bedeuten.",
            "Wir empfehlen, zunächst {prerequisites} zu adressieren und "
            "die KI-Strategie in {timeframe} Monaten neu zu bewerten.",
        ],
    }

    def __init__(self) -> None:
        self._sentiment: InvestmentSentiment = InvestmentSentiment.HOLD

    def generate(
        self,
        analysis_data: Dict[str, Any],
        kpi_data: Dict[str, Any],
    ) -> InvestmentThesis:
        """
        Generate investment thesis.

        Args:
            analysis_data: Full analysis context
            kpi_data: KPI metrics

        Returns:
            InvestmentThesis structure
        """
        # Determine sentiment
        self._sentiment = self._assess_sentiment(kpi_data)

        # Generate sentences
        sentences = self._generate_sentences(analysis_data, kpi_data)

        # Create headline
        headline = self._create_headline(analysis_data)

        # Calculate confidence
        confidence = self._calculate_confidence(kpi_data)

        return InvestmentThesis(
            headline=headline,
            sentences=sentences,
            sentiment=self._sentiment.value,
            confidence_level=confidence,
        )

    def _assess_sentiment(self, kpi_data: Dict[str, Any]) -> InvestmentSentiment:
        """Assess investment sentiment from KPIs."""
        roi = kpi_data.get("roi_percentage", 0)
        risk_score = kpi_data.get("risk_score", 0.5)

        for sentiment, thresholds in SENTIMENT_THRESHOLDS.items():
            if roi >= thresholds["roi_min"] and risk_score <= thresholds["risk_max"]:
                return sentiment

        return InvestmentSentiment.DEFER

    def _generate_sentences(
        self,
        analysis_data: Dict[str, Any],
        kpi_data: Dict[str, Any],
    ) -> List[str]:
        """Generate the three thesis sentences."""
        templates = self.THESIS_TEMPLATES.get(
            self._sentiment,
            self.THESIS_TEMPLATES[InvestmentSentiment.HOLD],
        )

        company = analysis_data.get("company_name", "Das Unternehmen")
        investment = self._format_investment(kpi_data.get("investment_required", 0))
        payback = kpi_data.get("payback_months", 24)
        advantage = kpi_data.get("competitive_advantage_pct", 20)
        efficiency = kpi_data.get("efficiency_gain_pct", 30)
        focus_area = analysis_data.get("primary_focus", "Prozessautomatisierung")
        prerequisites = analysis_data.get(
            "prerequisites", "Dateninfrastruktur und Governance",
        )
        competitor_investment = self._format_investment(
            kpi_data.get("competitor_benchmark", 500000),
        )
        timeframe = kpi_data.get("reassessment_months", 12)

        sentences = []
        for template in templates:
            sentence = template.format(
                company=company,
                investment=investment,
                payback=payback,
                advantage=advantage,
                efficiency=efficiency,
                focus_area=focus_area,
                prerequisites=prerequisites,
                competitor_investment=competitor_investment,
                timeframe=timeframe,
            )
            sentences.append(sentence)

        return sentences[:SUMMARY_CONFIG["thesis_sentence_count"]]

    def _create_headline(self, analysis_data: Dict[str, Any]) -> str:
        """Create thesis headline."""
        company = analysis_data.get("company_name", "Unternehmen")

        headlines = {
            InvestmentSentiment.STRONG_BUY: f"{company}: Sofortige Investition empfohlen",
            InvestmentSentiment.BUY: f"{company}: Strukturierte Investition empfohlen",
            InvestmentSentiment.HOLD: f"{company}: Selektive Investition empfohlen",
            InvestmentSentiment.CAUTIOUS: f"{company}: Explorativer Ansatz empfohlen",
            InvestmentSentiment.DEFER: f"{company}: Investition derzeit nicht empfohlen",
        }

        return headlines.get(self._sentiment, f"{company}: KI-Readiness Assessment")

    def _format_investment(self, amount: float) -> str:
        """Format investment amount."""
        if amount >= 1_000_000:
            return f"{amount / 1_000_000:.1f} Mio EUR"
        if amount >= 1000:
            return f"{amount / 1000:.0f} Tsd EUR"
        return f"{amount:.0f} EUR"

    def _calculate_confidence(self, kpi_data: Dict[str, Any]) -> float:
        """Calculate confidence level."""
        # Based on data completeness and consistency
        data_completeness = kpi_data.get("data_completeness", 0.7)
        model_confidence = kpi_data.get("model_confidence", 0.8)

        return (data_completeness * 0.4 + model_confidence * 0.6)


# =============================================================================
# STRATEGIC RATIONALE GENERATOR
# =============================================================================


class StrategicRationaleGenerator:
    """
    Generates the Strategic Rationale section.

    Uses bullet-logic structure for clarity.
    """

    def generate(
        self,
        analysis_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> StrategicRationale:
        """
        Generate strategic rationale.

        Args:
            analysis_data: Full analysis context
            market_data: Market positioning data

        Returns:
            StrategicRationale structure
        """
        core_argument = self._formulate_core_argument(analysis_data)
        supporting_points = self._generate_supporting_points(analysis_data, market_data)
        market_position = self._assess_market_position(market_data)
        competitive_advantage = self._identify_competitive_advantage(analysis_data)

        return StrategicRationale(
            core_argument=core_argument,
            supporting_points=supporting_points,
            market_position=market_position,
            competitive_advantage=competitive_advantage,
        )

    def _formulate_core_argument(self, analysis_data: Dict[str, Any]) -> str:
        """Formulate the core strategic argument."""
        industry = analysis_data.get("industry", "der Branche")
        readiness_score = analysis_data.get("readiness_score", 50)

        if readiness_score >= 70:
            return (
                f"Mit einem KI-Readiness-Score von {readiness_score}/100 ist das "
                f"Unternehmen gut positioniert, um KI als strategischen Differentiator "
                f"in {industry} zu nutzen und First-Mover-Vorteile zu realisieren."
            )
        if readiness_score >= 50:
            return (
                f"Der KI-Readiness-Score von {readiness_score}/100 zeigt solide "
                f"Grundlagen mit klarem Verbesserungspotenzial – gezielte Investitionen "
                f"können die Wettbewerbsposition in {industry} signifikant stärken."
            )
        return (
            f"Der KI-Readiness-Score von {readiness_score}/100 signalisiert "
            f"Nachholbedarf – strukturierte Grundlagenarbeit ist erforderlich, um "
            f"in {industry} wettbewerbsfähig zu bleiben."
        )

    def _generate_supporting_points(
        self,
        analysis_data: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> List[str]:
        """Generate supporting bullet points."""
        points: List[str] = []

        # Market opportunity
        market_size = market_data.get("addressable_market", "signifikant")
        points.append(f"Adressierbares Marktpotenzial: {market_size}")

        # Efficiency gains
        efficiency = analysis_data.get("efficiency_potential", 30)
        points.append(f"Effizienzsteigerungspotenzial: {efficiency}% in Kernprozessen")

        # Competitive pressure
        competitor_adoption = market_data.get("competitor_ai_adoption", "steigend")
        points.append(f"Wettbewerbsdruck: KI-Adoption bei Wettbewerbern {competitor_adoption}")

        # Regulatory alignment
        regulatory_fit = analysis_data.get("regulatory_alignment", "mittel")
        points.append(f"Regulatorische Passung: {regulatory_fit}")

        # Talent availability
        talent_situation = analysis_data.get("talent_availability", "herausfordernd")
        points.append(f"Talentsituation: {talent_situation}")

        return points[:SUMMARY_CONFIG["max_rationale_points"]]

    def _assess_market_position(self, market_data: Dict[str, Any]) -> str:
        """Assess current market position."""
        position_score = market_data.get("market_position_score", 50)

        if position_score >= 70:
            return "Marktführer mit starker Innovationsposition"
        if position_score >= 50:
            return "Etablierter Anbieter mit Differenzierungspotenzial"
        if position_score >= 30:
            return "Challenger mit Aufholbedarf"
        return "Nachzügler mit strategischem Handlungsbedarf"

    def _identify_competitive_advantage(self, analysis_data: Dict[str, Any]) -> str:
        """Identify primary competitive advantage."""
        advantages = analysis_data.get("competitive_advantages", [])

        if advantages:
            return f"Primärer Vorteil: {advantages[0]}"

        return "Differenzierungspotenzial durch KI-gestützte Prozessexzellenz"


# =============================================================================
# FINANCIAL CASE GENERATOR
# =============================================================================


class FinancialCaseGenerator:
    """
    Generates the Financial Case section.

    Includes KPI-Triangle and ROI Narrative.
    """

    def generate(
        self,
        kpi_data: Dict[str, Any],
        simulation_data: Dict[str, Any],
    ) -> FinancialCase:
        """
        Generate financial case.

        Args:
            kpi_data: Financial KPIs
            simulation_data: Simulation results (Monte Carlo, scenarios)

        Returns:
            FinancialCase structure
        """
        kpi_triangle = self._build_kpi_triangle(kpi_data)
        roi_narrative = self._compose_roi_narrative(kpi_data, simulation_data)
        investment_required = self._format_investment_required(kpi_data)
        payback_period = self._calculate_payback_narrative(kpi_data)
        npv_assessment = self._assess_npv(simulation_data)

        return FinancialCase(
            kpi_triangle=kpi_triangle,
            roi_narrative=roi_narrative,
            investment_required=investment_required,
            payback_period=payback_period,
            npv_assessment=npv_assessment,
        )

    def _build_kpi_triangle(self, kpi_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the KPI triangle (ROI, Payback, Risk-Adjusted Return)."""
        return {
            "roi": {
                "value": kpi_data.get("roi_percentage", 0),
                "label": "ROI (%)",
                "benchmark": 100,
                "status": self._get_status(kpi_data.get("roi_percentage", 0), 100),
            },
            "payback": {
                "value": kpi_data.get("payback_months", 0),
                "label": "Payback (Monate)",
                "benchmark": 24,
                "status": self._get_status(24, kpi_data.get("payback_months", 36)),
            },
            "risk_adjusted_return": {
                "value": kpi_data.get("risk_adjusted_return", 0),
                "label": "Risikoadjustierte Rendite (%)",
                "benchmark": 80,
                "status": self._get_status(
                    kpi_data.get("risk_adjusted_return", 0), 80,
                ),
            },
        }

    def _get_status(self, value: float, benchmark: float) -> str:
        """Get status indicator based on value vs benchmark."""
        ratio = value / benchmark if benchmark > 0 else 0
        if ratio >= 1.2:
            return "excellent"
        if ratio >= 1.0:
            return "good"
        if ratio >= 0.7:
            return "moderate"
        return "needs_improvement"

    def _compose_roi_narrative(
        self,
        kpi_data: Dict[str, Any],
        simulation_data: Dict[str, Any],
    ) -> str:
        """Compose the ROI narrative."""
        roi = kpi_data.get("roi_percentage", 0)
        investment = kpi_data.get("investment_required", 0)
        expected_return = kpi_data.get("expected_return", 0)
        confidence = simulation_data.get("confidence_interval", "80-120%")

        investment_str = self._format_currency(investment)
        return_str = self._format_currency(expected_return)

        return (
            f"Bei einer Gesamtinvestition von {investment_str} prognostizieren wir "
            f"einen ROI von {roi:.0f}% über 3 Jahre. Der erwartete Gesamtnutzen "
            f"beträgt {return_str} (Konfidenzintervall: {confidence}). "
            f"Die Investition amortisiert sich damit deutlich innerhalb des "
            f"strategischen Planungshorizonts."
        )

    def _format_investment_required(self, kpi_data: Dict[str, Any]) -> str:
        """Format investment required statement."""
        capex = kpi_data.get("capex", 0)
        opex_annual = kpi_data.get("opex_annual", 0)
        total_3y = capex + (opex_annual * 3)

        return (
            f"CAPEX: {self._format_currency(capex)} | "
            f"OPEX p.a.: {self._format_currency(opex_annual)} | "
            f"Total (3J): {self._format_currency(total_3y)}"
        )

    def _calculate_payback_narrative(self, kpi_data: Dict[str, Any]) -> str:
        """Calculate payback period narrative."""
        months = kpi_data.get("payback_months", 24)

        if months <= 12:
            assessment = "hervorragend – innerhalb eines Geschäftsjahres"
        elif months <= 18:
            assessment = "sehr gut – deutlich unter 2 Jahren"
        elif months <= 24:
            assessment = "gut – innerhalb von 2 Jahren"
        elif months <= 36:
            assessment = "akzeptabel – mittelfristiger Horizont"
        else:
            assessment = "langfristig – erfordert strategische Geduld"

        return f"{months} Monate – {assessment}"

    def _assess_npv(self, simulation_data: Dict[str, Any]) -> str:
        """Assess NPV from simulation data."""
        npv = simulation_data.get("npv", 0)
        discount_rate = simulation_data.get("discount_rate", 10)

        npv_str = self._format_currency(npv)
        return f"NPV bei {discount_rate}% Diskontierung: {npv_str}"

    def _format_currency(self, amount: float) -> str:
        """Format currency amount."""
        if amount >= 1_000_000:
            return f"{amount / 1_000_000:.2f} Mio EUR"
        if amount >= 1000:
            return f"{amount / 1000:.0f} Tsd EUR"
        return f"{amount:.0f} EUR"


# =============================================================================
# OPERATIONAL CASE GENERATOR
# =============================================================================


class OperationalCaseGenerator:
    """
    Generates the Operational Case section.

    Covers automation potential and process bottlenecks.
    """

    def generate(
        self,
        process_data: Dict[str, Any],
        automation_analysis: Dict[str, Any],
    ) -> OperationalCase:
        """
        Generate operational case.

        Args:
            process_data: Process analysis data
            automation_analysis: Automation potential analysis

        Returns:
            OperationalCase structure
        """
        automation_potential = self._describe_automation_potential(automation_analysis)
        automation_pct = automation_analysis.get("automation_percentage", 40)
        bottlenecks = self._identify_bottlenecks(process_data)
        quick_wins = self._identify_quick_wins(automation_analysis)
        resources = self._describe_resource_requirements(automation_analysis)

        return OperationalCase(
            automation_potential=automation_potential,
            automation_percentage=automation_pct,
            process_bottlenecks=bottlenecks,
            quick_wins=quick_wins,
            resource_requirements=resources,
        )

    def _describe_automation_potential(
        self,
        automation_analysis: Dict[str, Any],
    ) -> str:
        """Describe the automation potential."""
        pct = automation_analysis.get("automation_percentage", 40)
        primary_areas = automation_analysis.get("primary_areas", ["Kernprozesse"])

        areas_str = ", ".join(primary_areas[:3])

        if pct >= 60:
            return (
                f"Hohes Automatisierungspotenzial von {pct}% identifiziert – "
                f"primäre Bereiche: {areas_str}. Signifikante Effizienzgewinne "
                f"sind kurzfristig realisierbar."
            )
        if pct >= 40:
            return (
                f"Solides Automatisierungspotenzial von {pct}% – "
                f"Fokus auf {areas_str}. Strukturierte Umsetzung empfohlen."
            )
        return (
            f"Moderates Automatisierungspotenzial von {pct}% – "
            f"selektive Ansätze in {areas_str} sinnvoll."
        )

    def _identify_bottlenecks(self, process_data: Dict[str, Any]) -> List[str]:
        """Identify process bottlenecks."""
        bottlenecks = process_data.get("bottlenecks", [])

        if not bottlenecks:
            bottlenecks = [
                "Manuelle Datenverarbeitung in Kernprozessen",
                "Fragmentierte Systemlandschaft",
                "Fehlende Prozessstandardisierung",
                "Qualitätssicherung ohne KI-Unterstützung",
            ]

        return bottlenecks[:SUMMARY_CONFIG["max_bottlenecks"]]

    def _identify_quick_wins(self, automation_analysis: Dict[str, Any]) -> List[str]:
        """Identify quick win opportunities."""
        quick_wins = automation_analysis.get("quick_wins", [])

        if not quick_wins:
            quick_wins = [
                "Dokumentenverarbeitung automatisieren",
                "Reporting-Prozesse mit KI beschleunigen",
                "Kundenanfragen durch Chatbot entlasten",
            ]

        return quick_wins[:SUMMARY_CONFIG["max_quick_wins"]]

    def _describe_resource_requirements(
        self,
        automation_analysis: Dict[str, Any],
    ) -> str:
        """Describe resource requirements."""
        fte = automation_analysis.get("fte_required", 5)
        duration = automation_analysis.get("implementation_months", 12)
        skills = automation_analysis.get("skill_gaps", ["Data Science", "ML Ops"])

        skills_str = ", ".join(skills[:3])

        return (
            f"Ressourcenbedarf: {fte} FTE über {duration} Monate. "
            f"Kritische Skills: {skills_str}."
        )


# =============================================================================
# RISK CASE GENERATOR
# =============================================================================


class RiskCaseGenerator:
    """
    Generates the Risk Case section.

    Covers AI Act, DSGVO, and Vendor Exposure.
    """

    def generate(
        self,
        risk_data: Dict[str, Any],
        governance_data: Dict[str, Any],
    ) -> RiskCase:
        """
        Generate risk case.

        Args:
            risk_data: Risk assessment data
            governance_data: Governance analysis

        Returns:
            RiskCase structure
        """
        ai_act = self._assess_ai_act_exposure(governance_data)
        dsgvo = self._assess_dsgvo_compliance(governance_data)
        vendor = self._assess_vendor_exposure(risk_data)
        priorities = self._identify_mitigation_priorities(risk_data, governance_data)
        risk_score = self._calculate_risk_score(risk_data, governance_data)

        return RiskCase(
            ai_act_exposure=ai_act,
            dsgvo_compliance=dsgvo,
            vendor_exposure=vendor,
            mitigation_priorities=priorities,
            risk_score=risk_score,
        )

    def _assess_ai_act_exposure(self, governance_data: Dict[str, Any]) -> str:
        """Assess AI Act exposure."""
        risk_level = governance_data.get("ai_act_risk_level", "limited")
        compliance_status = governance_data.get("ai_act_compliance", 60)

        level_mapping = {
            "unacceptable": "Kritisch – sofortige Maßnahmen erforderlich",
            "high": "Hoch – strukturierte Compliance-Roadmap notwendig",
            "limited": "Moderat – definierte Transparenzanforderungen",
            "minimal": "Gering – Basisanforderungen erfüllen",
        }

        level_str = level_mapping.get(risk_level, level_mapping["limited"])

        return (
            f"AI Act Risikoklasse: {risk_level.upper()} | {level_str} | "
            f"Aktuelle Compliance: {compliance_status}%"
        )

    def _assess_dsgvo_compliance(self, governance_data: Dict[str, Any]) -> str:
        """Assess DSGVO compliance status."""
        compliance_score = governance_data.get("dsgvo_compliance", 70)
        gaps = governance_data.get("dsgvo_gaps", [])

        if compliance_score >= 90:
            status = "Vollständig compliant"
        elif compliance_score >= 70:
            status = "Überwiegend compliant, Nachbesserungen erforderlich"
        elif compliance_score >= 50:
            status = "Teilweise compliant, strukturierte Maßnahmen notwendig"
        else:
            status = "Signifikante Lücken, dringende Maßnahmen erforderlich"

        gaps_str = ", ".join(gaps[:2]) if gaps else "keine kritischen Lücken"

        return f"{status} ({compliance_score}%) | Fokus: {gaps_str}"

    def _assess_vendor_exposure(self, risk_data: Dict[str, Any]) -> str:
        """Assess vendor exposure."""
        vendor_dependency = risk_data.get("vendor_dependency", "moderat")
        key_vendors = risk_data.get("key_vendors", ["OpenAI", "Microsoft"])
        lock_in_risk = risk_data.get("lock_in_risk", "mittel")

        vendors_str = ", ".join(key_vendors[:3])

        return (
            f"Vendor-Abhängigkeit: {vendor_dependency} | "
            f"Schlüsselanbieter: {vendors_str} | Lock-in-Risiko: {lock_in_risk}"
        )

    def _identify_mitigation_priorities(
        self,
        risk_data: Dict[str, Any],
        governance_data: Dict[str, Any],
    ) -> List[str]:
        """Identify risk mitigation priorities."""
        priorities: List[str] = []

        # AI Act compliance
        if governance_data.get("ai_act_compliance", 100) < 80:
            priorities.append("AI Act Compliance-Roadmap implementieren")

        # DSGVO gaps
        if governance_data.get("dsgvo_compliance", 100) < 90:
            priorities.append("DSGVO-Lücken schließen")

        # Vendor diversification
        if risk_data.get("vendor_dependency", "") in ["hoch", "kritisch"]:
            priorities.append("Vendor-Diversifikation vorantreiben")

        # Data governance
        if governance_data.get("data_governance_maturity", 100) < 60:
            priorities.append("Data Governance Framework etablieren")

        # Model governance
        priorities.append("KI-Governance-Strukturen aufbauen")

        return priorities[:5]

    def _calculate_risk_score(
        self,
        risk_data: Dict[str, Any],
        governance_data: Dict[str, Any],
    ) -> float:
        """Calculate overall risk score (0-1, lower is better)."""
        ai_act_comp = governance_data.get("ai_act_compliance", 50) / 100
        dsgvo_comp = governance_data.get("dsgvo_compliance", 70) / 100
        vendor_risk = {"gering": 0.2, "moderat": 0.4, "hoch": 0.7, "kritisch": 0.9}.get(
            risk_data.get("vendor_dependency", "moderat"), 0.4,
        )

        # Invert compliance scores (higher compliance = lower risk)
        risk_from_compliance = ((1 - ai_act_comp) * 0.4 + (1 - dsgvo_comp) * 0.3)
        risk_from_vendor = vendor_risk * 0.3

        return round(risk_from_compliance + risk_from_vendor, 2)


# =============================================================================
# 90-DAY MANDATE GENERATOR
# =============================================================================


class NinetyDayMandateGenerator:
    """
    Generates the 90-Day Mandate section.

    Defines what leadership must do now.
    """

    def generate(
        self,
        analysis_data: Dict[str, Any],
        priority_data: Dict[str, Any],
    ) -> NinetyDayMandate:
        """
        Generate 90-day mandate.

        Args:
            analysis_data: Full analysis context
            priority_data: Priority assessments

        Returns:
            NinetyDayMandate structure
        """
        actions = self._define_immediate_actions(analysis_data, priority_data)
        deadlines = self._set_decision_deadlines(priority_data)
        allocations = self._define_resource_allocations(analysis_data)
        metrics = self._define_success_metrics(priority_data)

        return NinetyDayMandate(
            immediate_actions=actions,
            decision_deadlines=deadlines,
            resource_allocations=allocations,
            success_metrics=metrics,
        )

    def _define_immediate_actions(
        self,
        analysis_data: Dict[str, Any],
        priority_data: Dict[str, Any],
    ) -> List[str]:
        """Define immediate actions for leadership."""
        actions: List[str] = []

        # Strategic decision
        actions.append(
            "KI-Strategie-Freigabe: Investitionsentscheidung im Vorstand herbeiführen"
        )

        # Governance setup
        if analysis_data.get("governance_maturity", 100) < 60:
            actions.append(
                "KI-Governance: Verantwortlichkeiten und Entscheidungsgremium etablieren"
            )

        # Quick wins
        quick_wins = priority_data.get("quick_wins", [])
        if quick_wins:
            actions.append(f"Quick Win initiieren: {quick_wins[0]}")

        # Talent
        actions.append(
            "Talent Assessment: Skill-Gaps identifizieren und Schulungsplan erstellen"
        )

        # Vendor
        actions.append(
            "Vendor Evaluation: Shortlist für KI-Partner finalisieren"
        )

        return actions[:SUMMARY_CONFIG["max_mandate_items"]]

    def _set_decision_deadlines(
        self,
        priority_data: Dict[str, Any],
    ) -> List[str]:
        """Set decision deadlines."""
        return [
            "Tag 15: Kick-off Meeting mit Stakeholdern",
            "Tag 30: Investitionsvorlage für Vorstand",
            "Tag 45: Vendor-Shortlist finalisiert",
            "Tag 60: Pilotprojekt-Start",
            "Tag 90: Erste Ergebnisse und Go/No-Go für Phase 2",
        ][:SUMMARY_CONFIG["max_mandate_items"]]

    def _define_resource_allocations(
        self,
        analysis_data: Dict[str, Any],
    ) -> List[str]:
        """Define resource allocations."""
        return [
            "Projektleitung: 1 FTE (Senior Manager)",
            "Fachexperten: 2-3 FTE (teilzeit)",
            "IT/Data: 2 FTE",
            "Externes Budget: gemäß Investitionsvorlage",
            "Management Attention: wöchentliches Steering Committee",
        ][:SUMMARY_CONFIG["max_mandate_items"]]

    def _define_success_metrics(
        self,
        priority_data: Dict[str, Any],
    ) -> List[str]:
        """Define success metrics for 90-day period."""
        return [
            "Investitionsentscheidung getroffen (Go/No-Go)",
            "Governance-Struktur etabliert und kommuniziert",
            "Mindestens 1 Quick Win in Umsetzung",
            "Skill-Gap-Analyse abgeschlossen",
            "Vendor-Verträge verhandlungsreif",
        ][:SUMMARY_CONFIG["max_mandate_items"]]


# =============================================================================
# MAIN ENGINE CLASS
# =============================================================================


class ExecutiveSummaryInvestmentEngine:
    """
    Main engine for Executive Summary v6 (Investment Memo Format).

    Orchestrates all section generators with GPT+Claude dual mode support.
    """

    def __init__(self) -> None:
        self._thesis_generator = InvestmentThesisGenerator()
        self._rationale_generator = StrategicRationaleGenerator()
        self._financial_generator = FinancialCaseGenerator()
        self._operational_generator = OperationalCaseGenerator()
        self._risk_generator = RiskCaseGenerator()
        self._mandate_generator = NinetyDayMandateGenerator()

    def generate_executive_summary(
        self,
        full_analysis: Dict[str, Any],
    ) -> ExecutiveSummaryV6:
        """
        Generate complete Executive Summary v6.

        Args:
            full_analysis: Complete analysis data from all engines

        Returns:
            ExecutiveSummaryV6 structure
        """
        log.info("[N4.1-ExecSummary] Generating Executive Summary v6...")

        # Extract relevant data subsets
        analysis_data = full_analysis.get("analysis", {})
        kpi_data = full_analysis.get("kpis", {})
        market_data = full_analysis.get("market", {})
        simulation_data = full_analysis.get("simulation", {})
        process_data = full_analysis.get("processes", {})
        automation_data = full_analysis.get("automation", {})
        risk_data = full_analysis.get("risks", {})
        governance_data = full_analysis.get("governance", {})
        priority_data = full_analysis.get("priorities", {})

        # Generate all sections
        thesis = self._thesis_generator.generate(analysis_data, kpi_data)
        rationale = self._rationale_generator.generate(analysis_data, market_data)
        financial = self._financial_generator.generate(kpi_data, simulation_data)
        operational = self._operational_generator.generate(process_data, automation_data)
        risk = self._risk_generator.generate(risk_data, governance_data)
        mandate = self._mandate_generator.generate(analysis_data, priority_data)

        # Metadata
        metadata = {
            "version": "v6",
            "format": "investment_memo",
            "sections_generated": 6,
            "model_preferences": {
                s.value: SECTION_MODEL_MAPPING[s].value
                for s in SummarySection
            },
        }

        log.info("[N4.1-ExecSummary] Executive Summary v6 generation complete")

        return ExecutiveSummaryV6(
            investment_thesis=thesis,
            strategic_rationale=rationale,
            financial_case=financial,
            operational_case=operational,
            risk_case=risk,
            ninety_day_mandate=mandate,
            generation_metadata=metadata,
        )

    def get_section(
        self,
        section: SummarySection,
        full_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a specific section only.

        Args:
            section: Section to generate
            full_analysis: Full analysis data

        Returns:
            Section content as dict
        """
        summary = self.generate_executive_summary(full_analysis)

        section_map = {
            SummarySection.INVESTMENT_THESIS: summary["investment_thesis"],
            SummarySection.STRATEGIC_RATIONALE: summary["strategic_rationale"],
            SummarySection.FINANCIAL_CASE: summary["financial_case"],
            SummarySection.OPERATIONAL_CASE: summary["operational_case"],
            SummarySection.RISK_CASE: summary["risk_case"],
            SummarySection.NINETY_DAY_MANDATE: summary["ninety_day_mandate"],
        }

        return dict(section_map.get(section, {}))

    def get_investment_thesis_text(
        self,
        full_analysis: Dict[str, Any],
    ) -> str:
        """
        Get investment thesis as formatted text.

        Args:
            full_analysis: Full analysis data

        Returns:
            Formatted thesis text
        """
        summary = self.generate_executive_summary(full_analysis)
        thesis = summary["investment_thesis"]

        lines = [thesis["headline"], ""]
        lines.extend(thesis["sentences"])
        lines.append("")
        lines.append(
            f"Empfehlung: {thesis['sentiment'].upper()} "
            f"(Konfidenz: {thesis['confidence_level']:.0%})"
        )

        return "\n".join(lines)


# =============================================================================
# SINGLETON & CONVENIENCE FUNCTIONS
# =============================================================================


_engine_instance: Optional[ExecutiveSummaryInvestmentEngine] = None


def get_executive_summary_engine() -> ExecutiveSummaryInvestmentEngine:
    """Get or create the singleton engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ExecutiveSummaryInvestmentEngine()
    return _engine_instance


def generate_executive_summary_v6(
    full_analysis: Dict[str, Any],
) -> ExecutiveSummaryV6:
    """
    Generate Executive Summary v6 (Investment Memo Format).

    Convenience function for external use.

    Args:
        full_analysis: Complete analysis data

    Returns:
        ExecutiveSummaryV6 structure
    """
    engine = get_executive_summary_engine()
    return engine.generate_executive_summary(full_analysis)


def get_investment_thesis(
    full_analysis: Dict[str, Any],
) -> InvestmentThesis:
    """
    Get investment thesis section.

    Convenience function for external use.

    Args:
        full_analysis: Complete analysis data

    Returns:
        InvestmentThesis structure
    """
    engine = get_executive_summary_engine()
    summary = engine.generate_executive_summary(full_analysis)
    return summary["investment_thesis"]


def get_ninety_day_mandate(
    full_analysis: Dict[str, Any],
) -> NinetyDayMandate:
    """
    Get 90-day mandate section.

    Convenience function for external use.

    Args:
        full_analysis: Complete analysis data

    Returns:
        NinetyDayMandate structure
    """
    engine = get_executive_summary_engine()
    summary = engine.generate_executive_summary(full_analysis)
    return summary["ninety_day_mandate"]
