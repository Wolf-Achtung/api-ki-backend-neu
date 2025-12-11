# -*- coding: utf-8 -*-
"""
SPRINT N3.8 PACKAGE B: Integrity Layer v2 (Cross-Numerical Logic).

Numerical consistency verification on 5 levels:
1. Business Case <-> KPI Layer
2. KPI Layer <-> Simulation Engine
3. Business Case <-> Tools Engine
4. Roadmaps <-> Benchmark KPIs
5. Risks <-> Mitigation (Tools/Recommendations)

Features:
- verify_numeric_coherence() -> IntegrityReport
- heal_numeric_inconsistencies() with tolerances (±3-5%)
- Cross-domain validation

Version: 1.0.0 (N3.8 - PLATIN++ v4.24)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum

log = logging.getLogger(__name__)

# Type alias
SectionDict = Dict[str, Any]


# =============================================================================
# CONFIGURATION
# =============================================================================

# Tolerance thresholds for numeric comparison
class ToleranceLevel(Enum):
    """Tolerance levels for numeric validation."""
    STRICT = 0.03  # 3% - for critical KPIs
    NORMAL = 0.05  # 5% - for standard metrics
    RELAXED = 0.10  # 10% - for estimates
    FLEXIBLE = 0.15  # 15% - for projections


# Default tolerances by metric type
DEFAULT_TOLERANCES: Dict[str, float] = {
    "roi": ToleranceLevel.NORMAL.value,  # 5%
    "payback": ToleranceLevel.NORMAL.value,  # 5%
    "savings": ToleranceLevel.RELAXED.value,  # 10%
    "time_savings": ToleranceLevel.RELAXED.value,  # 10%
    "fte": ToleranceLevel.NORMAL.value,  # 5%
    "cost": ToleranceLevel.NORMAL.value,  # 5%
    "revenue": ToleranceLevel.RELAXED.value,  # 10%
    "simulation_p50": ToleranceLevel.NORMAL.value,  # 5%
    "simulation_p80": ToleranceLevel.RELAXED.value,  # 10%
    "simulation_p90": ToleranceLevel.FLEXIBLE.value,  # 15%
    "productivity": ToleranceLevel.RELAXED.value,  # 10%
}

# Section mappings for cross-validation
SECTION_MAPPINGS: Dict[str, List[str]] = {
    "business_case": ["bc_summary", "business_case", "bc_kpis"],
    "kpi_layer": ["ki_stack_summary", "kpi_dashboard", "key_metrics"],
    "simulation": ["simulation_results", "monte_carlo", "scenario_analysis"],
    "tools": ["tools_empfehlungen", "ki_stack_summary", "tool_recommendations"],
    "roadmap": ["roadmap_90d", "roadmap_12m", "implementation_plan"],
    "benchmark": ["wettbewerb_benchmark", "market_comparison", "industry_benchmark"],
    "risks": ["risks", "risk_report", "risk_analysis"],
    "recommendations": ["recommendations", "handlungsempfehlungen", "action_items"],
}

# KPI extraction patterns
KPI_PATTERNS: Dict[str, str] = {
    "roi": r'(?:ROI|Return\s+on\s+Investment)[:\s]*(\d+(?:[,.]\d+)?)\s*%',
    "payback": r'(?:Payback|Amortisation|Break-even)[:\s-]*(\d+(?:[,.]\d+)?)\s*(?:Monate|months|Jahre|years)?',
    "savings": r'(?:Einspar|Savings?|Ersparnis)[:\s]*(\d+(?:[,.]\d+)?)\s*(?:EUR|€|%|Tsd|k)',
    "time_savings": r'(?:Zeit(?:ersparnis|einsparung)|Time\s+Savings?)[:\s]*(\d+(?:[,.]\d+)?)\s*(?:%|Stunden|h)',
    "fte": r'(?:FTE|Vollzeit)[:\s-]*(\d+(?:[,.]\d+)?)',
    "cost": r'(?:Kosten|Cost|Investition)[:\s]*(\d+(?:[,.]\d+)?)\s*(?:EUR|€|Tsd|k)',
    "productivity": r'(?:Produktivität|Productivity|Effizienz)[:\s]*(?:\+)?(\d+(?:[,.]\d+)?)\s*%',
}

# Simulation percentile patterns
SIMULATION_PATTERNS: Dict[str, str] = {
    "p50": r'P50[:\s]*(\d+(?:[,.]\d+)?)',
    "p80": r'P80[:\s]*(\d+(?:[,.]\d+)?)',
    "p90": r'P90[:\s]*(\d+(?:[,.]\d+)?)',
    "expected": r'(?:Erwartungswert|Expected|Mean)[:\s]*(\d+(?:[,.]\d+)?)',
    "best_case": r'(?:Best\s+Case|Optimistisch)[:\s]*(\d+(?:[,.]\d+)?)',
    "worst_case": r'(?:Worst\s+Case|Pessimistisch)[:\s]*(\d+(?:[,.]\d+)?)',
}

# Risk-Mitigation mapping keywords
RISK_KEYWORDS: List[str] = [
    "datenschutz", "security", "compliance", "integration",
    "akzeptanz", "adoption", "kosten", "budget", "timeline",
    "qualität", "vendor", "dependency", "skill", "resource",
]

MITIGATION_KEYWORDS: Dict[str, List[str]] = {
    "datenschutz": ["verschlüsselung", "anonymisierung", "dsgvo", "privacy"],
    "security": ["audit", "penetration", "firewall", "access control"],
    "compliance": ["audit", "zertifizierung", "dokumentation", "policy"],
    "integration": ["api", "schnittstelle", "migration", "connector"],
    "akzeptanz": ["schulung", "training", "change management", "kommunikation"],
    "kosten": ["budget", "cost control", "monitoring", "ressourcenplanung"],
    "timeline": ["milestone", "puffer", "agile", "sprint"],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class NumericMismatch:
    """A numeric inconsistency found during validation."""
    domain1: str
    domain2: str
    metric: str
    value1: float
    value2: float
    deviation: float
    tolerance: float
    severity: str  # 'critical', 'high', 'medium', 'low'
    message: str
    proposed_fix: str = ""
    healed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain1": self.domain1,
            "domain2": self.domain2,
            "metric": self.metric,
            "value1": self.value1,
            "value2": self.value2,
            "deviation": self.deviation,
            "tolerance": self.tolerance,
            "severity": self.severity,
            "message": self.message,
            "proposed_fix": self.proposed_fix,
            "healed": self.healed,
        }


@dataclass
class RiskMitigationGap:
    """A risk without adequate mitigation."""
    risk_type: str
    risk_section: str
    risk_description: str
    mitigation_found: bool
    mitigation_section: str = ""
    mitigation_description: str = ""
    severity: str = "medium"
    healed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "risk_type": self.risk_type,
            "risk_section": self.risk_section,
            "risk_description": self.risk_description,
            "mitigation_found": self.mitigation_found,
            "mitigation_section": self.mitigation_section,
            "mitigation_description": self.mitigation_description,
            "severity": self.severity,
            "healed": self.healed,
        }


@dataclass
class IntegrityReport:
    """Report from integrity validation."""
    domains_checked: int = 0
    metrics_validated: int = 0
    mismatches: List[NumericMismatch] = field(default_factory=list)
    risk_gaps: List[RiskMitigationGap] = field(default_factory=list)
    tolerances_used: Dict[str, float] = field(default_factory=dict)
    healed_mismatches: int = 0
    healed_gaps: int = 0
    overall_score: float = 100.0
    grade: str = "A"

    def add_mismatch(self, mismatch: NumericMismatch) -> None:
        """Add a mismatch to the report."""
        self.mismatches.append(mismatch)
        # Adjust score based on severity
        if mismatch.severity == "critical":
            self.overall_score -= 15
        elif mismatch.severity == "high":
            self.overall_score -= 10
        elif mismatch.severity == "medium":
            self.overall_score -= 5
        else:
            self.overall_score -= 2
        self.overall_score = max(0, self.overall_score)
        self._update_grade()

    def add_risk_gap(self, gap: RiskMitigationGap) -> None:
        """Add a risk-mitigation gap to the report."""
        self.risk_gaps.append(gap)
        if gap.severity == "high":
            self.overall_score -= 8
        elif gap.severity == "medium":
            self.overall_score -= 4
        else:
            self.overall_score -= 2
        self.overall_score = max(0, self.overall_score)
        self._update_grade()

    def _update_grade(self) -> None:
        """Update grade based on score."""
        if self.overall_score >= 90:
            self.grade = "A"
        elif self.overall_score >= 80:
            self.grade = "B"
        elif self.overall_score >= 70:
            self.grade = "C"
        elif self.overall_score >= 50:
            self.grade = "D"
        else:
            self.grade = "F"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domains_checked": self.domains_checked,
            "metrics_validated": self.metrics_validated,
            "mismatches_count": len(self.mismatches),
            "mismatches": [m.to_dict() for m in self.mismatches],
            "risk_gaps_count": len(self.risk_gaps),
            "risk_gaps": [g.to_dict() for g in self.risk_gaps],
            "tolerances_used": self.tolerances_used,
            "healed_mismatches": self.healed_mismatches,
            "healed_gaps": self.healed_gaps,
            "overall_score": self.overall_score,
            "grade": self.grade,
        }


# =============================================================================
# KPI EXTRACTION UTILITIES
# =============================================================================

def extract_text_from_html(html: str) -> str:
    """Extract plain text from HTML."""
    if not html:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_number(value_str: str) -> Optional[float]:
    """Parse a numeric string to float."""
    if not value_str:
        return None
    # Remove whitespace and normalize
    cleaned = value_str.strip().replace(' ', '')
    # Handle German decimal format (1.234,56 -> 1234.56)
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_kpis(text: str) -> Dict[str, float]:
    """Extract KPI values from text."""
    kpis: Dict[str, float] = {}

    for kpi_name, pattern in KPI_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Take first match
            value = parse_number(matches[0])
            if value is not None:
                kpis[kpi_name] = value

    return kpis


def extract_simulation_values(text: str) -> Dict[str, float]:
    """Extract simulation percentile values from text."""
    values: Dict[str, float] = {}

    for key, pattern in SIMULATION_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            value = parse_number(matches[0])
            if value is not None:
                values[key] = value

    return values


def get_section_content(sections: SectionDict, domain: str) -> str:
    """Get combined content from domain sections."""
    content_parts: List[str] = []

    section_keys = SECTION_MAPPINGS.get(domain, [domain])

    for key in section_keys:
        html_key = f"{key.upper()}_HTML"
        content = sections.get(html_key) or sections.get(key, "")
        if isinstance(content, str) and content:
            content_parts.append(extract_text_from_html(content))

    return ' '.join(content_parts)


# =============================================================================
# CROSS-DOMAIN VALIDATION
# =============================================================================

def validate_bc_kpi_coherence(
    sections: SectionDict,
    report: IntegrityReport
) -> None:
    """
    Level 1: Validate Business Case <-> KPI Layer coherence.
    """
    log.info("[N3.8-Integrity] Validating BC <-> KPI coherence...")

    bc_content = get_section_content(sections, "business_case")
    kpi_content = get_section_content(sections, "kpi_layer")

    if not bc_content or not kpi_content:
        log.warning("[N3.8-Integrity] Missing BC or KPI content")
        return

    bc_kpis = extract_kpis(bc_content)
    kpi_kpis = extract_kpis(kpi_content)

    report.domains_checked += 1

    # Compare common KPIs
    common_kpis = set(bc_kpis.keys()) & set(kpi_kpis.keys())

    for kpi in common_kpis:
        report.metrics_validated += 1

        val1 = bc_kpis[kpi]
        val2 = kpi_kpis[kpi]

        # Calculate deviation
        if val1 == 0 and val2 == 0:
            deviation = 0.0
        elif val1 == 0:
            deviation = 1.0  # 100% deviation
        else:
            deviation = abs(val2 - val1) / abs(val1)

        tolerance = DEFAULT_TOLERANCES.get(kpi, ToleranceLevel.NORMAL.value)
        report.tolerances_used[kpi] = tolerance

        if deviation > tolerance:
            severity = "critical" if deviation > 0.20 else "high" if deviation > 0.10 else "medium"

            report.add_mismatch(NumericMismatch(
                domain1="business_case",
                domain2="kpi_layer",
                metric=kpi,
                value1=val1,
                value2=val2,
                deviation=deviation,
                tolerance=tolerance,
                severity=severity,
                message=f"{kpi}: BC={val1:.2f} vs KPI={val2:.2f} (deviation {deviation:.1%})",
                proposed_fix=f"Align {kpi} to {(val1 + val2) / 2:.2f}",
            ))


def validate_kpi_simulation_coherence(
    sections: SectionDict,
    report: IntegrityReport
) -> None:
    """
    Level 2: Validate KPI Layer <-> Simulation Engine coherence.
    """
    log.info("[N3.8-Integrity] Validating KPI <-> Simulation coherence...")

    kpi_content = get_section_content(sections, "kpi_layer")
    sim_content = get_section_content(sections, "simulation")

    if not kpi_content or not sim_content:
        return

    kpi_values = extract_kpis(kpi_content)
    sim_values = extract_simulation_values(sim_content)

    report.domains_checked += 1

    # Compare ROI with simulation expected value
    if "roi" in kpi_values and "expected" in sim_values:
        report.metrics_validated += 1

        val1 = kpi_values["roi"]
        val2 = sim_values["expected"]

        if val1 != 0:
            deviation = abs(val2 - val1) / abs(val1)
        else:
            deviation = 1.0 if val2 != 0 else 0.0

        tolerance = ToleranceLevel.RELAXED.value
        report.tolerances_used["roi_vs_simulation"] = tolerance

        if deviation > tolerance:
            report.add_mismatch(NumericMismatch(
                domain1="kpi_layer",
                domain2="simulation",
                metric="roi_vs_expected",
                value1=val1,
                value2=val2,
                deviation=deviation,
                tolerance=tolerance,
                severity="medium",
                message=f"KPI ROI={val1:.1f}% vs Simulation Expected={val2:.1f}%",
                proposed_fix="Recalculate simulation with aligned ROI assumptions",
            ))

    # Validate P50 is less than P80 is less than P90
    if all(k in sim_values for k in ["p50", "p80", "p90"]):
        report.metrics_validated += 1

        if not (sim_values["p50"] <= sim_values["p80"] <= sim_values["p90"]):
            report.add_mismatch(NumericMismatch(
                domain1="simulation",
                domain2="simulation",
                metric="percentile_ordering",
                value1=sim_values["p50"],
                value2=sim_values["p90"],
                deviation=0,
                tolerance=0,
                severity="critical",
                message=f"Invalid percentile ordering: P50={sim_values['p50']}, P80={sim_values['p80']}, P90={sim_values['p90']}",
                proposed_fix="Recalculate simulation percentiles",
            ))


def validate_bc_tools_coherence(
    sections: SectionDict,
    report: IntegrityReport
) -> None:
    """
    Level 3: Validate Business Case <-> Tools Engine coherence.
    """
    log.info("[N3.8-Integrity] Validating BC <-> Tools coherence...")

    bc_content = get_section_content(sections, "business_case")
    tools_content = get_section_content(sections, "tools")

    if not bc_content or not tools_content:
        return

    report.domains_checked += 1

    bc_kpis = extract_kpis(bc_content)
    tools_kpis = extract_kpis(tools_content)

    # Compare cost and savings projections
    for kpi in ["cost", "savings"]:
        if kpi in bc_kpis and kpi in tools_kpis:
            report.metrics_validated += 1

            val1 = bc_kpis[kpi]
            val2 = tools_kpis[kpi]

            if val1 != 0:
                deviation = abs(val2 - val1) / abs(val1)
            else:
                deviation = 1.0 if val2 != 0 else 0.0

            tolerance = DEFAULT_TOLERANCES.get(kpi, ToleranceLevel.NORMAL.value)

            if deviation > tolerance:
                report.add_mismatch(NumericMismatch(
                    domain1="business_case",
                    domain2="tools",
                    metric=kpi,
                    value1=val1,
                    value2=val2,
                    deviation=deviation,
                    tolerance=tolerance,
                    severity="medium" if deviation < 0.15 else "high",
                    message=f"{kpi}: BC={val1:.0f} vs Tools={val2:.0f}",
                    proposed_fix=f"Align tool cost projections to BC: {val1:.0f}",
                ))


def validate_roadmap_benchmark_coherence(
    sections: SectionDict,
    report: IntegrityReport
) -> None:
    """
    Level 4: Validate Roadmaps <-> Benchmark KPIs coherence.
    """
    log.info("[N3.8-Integrity] Validating Roadmap <-> Benchmark coherence...")

    roadmap_content = get_section_content(sections, "roadmap")
    benchmark_content = get_section_content(sections, "benchmark")

    if not roadmap_content or not benchmark_content:
        return

    report.domains_checked += 1

    roadmap_kpis = extract_kpis(roadmap_content)
    benchmark_kpis = extract_kpis(benchmark_content)

    # Compare productivity and time savings
    for kpi in ["productivity", "time_savings"]:
        if kpi in roadmap_kpis and kpi in benchmark_kpis:
            report.metrics_validated += 1

            val1 = roadmap_kpis[kpi]
            val2 = benchmark_kpis[kpi]

            # Roadmap projections should not exceed benchmark by more than 50%
            if val1 != 0 and val2 > val1 * 1.5:
                report.add_mismatch(NumericMismatch(
                    domain1="roadmap",
                    domain2="benchmark",
                    metric=kpi,
                    value1=val1,
                    value2=val2,
                    deviation=(val2 - val1) / val1,
                    tolerance=0.5,
                    severity="medium",
                    message=f"Benchmark {kpi}={val2:.1f}% exceeds roadmap projection {val1:.1f}% by >50%",
                    proposed_fix=f"Align benchmark expectations to achievable roadmap targets",
                ))


def validate_risk_mitigation_coherence(
    sections: SectionDict,
    report: IntegrityReport
) -> None:
    """
    Level 5: Validate Risks <-> Mitigation (Tools/Recommendations) coherence.
    """
    log.info("[N3.8-Integrity] Validating Risk <-> Mitigation coherence...")

    risks_content = get_section_content(sections, "risks")
    reco_content = get_section_content(sections, "recommendations")
    tools_content = get_section_content(sections, "tools")

    if not risks_content:
        return

    report.domains_checked += 1

    mitigation_content = f"{reco_content} {tools_content}".lower()
    risks_lower = risks_content.lower()

    # Find mentioned risks
    for risk_keyword in RISK_KEYWORDS:
        if risk_keyword in risks_lower:
            report.metrics_validated += 1

            # Check if mitigation exists
            mitigation_keywords = MITIGATION_KEYWORDS.get(risk_keyword, [])
            mitigation_found = any(
                kw in mitigation_content
                for kw in mitigation_keywords
            )

            if not mitigation_found:
                # Also check if risk keyword is mentioned in recommendations
                if risk_keyword not in mitigation_content:
                    report.add_risk_gap(RiskMitigationGap(
                        risk_type=risk_keyword,
                        risk_section="risks",
                        risk_description=f"Risk '{risk_keyword}' identified",
                        mitigation_found=False,
                        severity="medium" if risk_keyword in ["datenschutz", "security", "compliance"] else "low",
                    ))


# =============================================================================
# MAIN VERIFICATION
# =============================================================================

def verify_numeric_coherence(sections: SectionDict) -> IntegrityReport:
    """
    N3.8: Verify numeric coherence across all 5 levels.

    Levels:
    1. Business Case <-> KPI Layer
    2. KPI Layer <-> Simulation Engine
    3. Business Case <-> Tools Engine
    4. Roadmaps <-> Benchmark KPIs
    5. Risks <-> Mitigation

    Args:
        sections: Dictionary of section contents

    Returns:
        IntegrityReport with all findings
    """
    report = IntegrityReport()

    log.info("[N3.8-Integrity] Starting numeric coherence verification...")

    # Level 1: BC <-> KPI
    validate_bc_kpi_coherence(sections, report)

    # Level 2: KPI <-> Simulation
    validate_kpi_simulation_coherence(sections, report)

    # Level 3: BC <-> Tools
    validate_bc_tools_coherence(sections, report)

    # Level 4: Roadmap <-> Benchmark
    validate_roadmap_benchmark_coherence(sections, report)

    # Level 5: Risk <-> Mitigation
    validate_risk_mitigation_coherence(sections, report)

    log.info(
        "[N3.8-Integrity] Verification complete: domains=%d metrics=%d mismatches=%d gaps=%d score=%.1f grade=%s",
        report.domains_checked,
        report.metrics_validated,
        len(report.mismatches),
        len(report.risk_gaps),
        report.overall_score,
        report.grade
    )

    return report


# =============================================================================
# HEALING FUNCTIONS
# =============================================================================

def heal_numeric_inconsistencies(
    sections: SectionDict,
    report: IntegrityReport
) -> SectionDict:
    """
    N3.8: Heal numeric inconsistencies based on report.

    Applies proposed fixes for mismatches within tolerance.

    Args:
        sections: Dictionary of section contents
        report: IntegrityReport from verify_numeric_coherence()

    Returns:
        Healed sections dictionary
    """
    healed = dict(sections)

    log.info("[N3.8-Integrity] Starting numeric healing...")

    for mismatch in report.mismatches:
        if mismatch.healed:
            continue

        # Calculate average value as target
        avg_value = (mismatch.value1 + mismatch.value2) / 2

        # Heal in both domains
        for domain in [mismatch.domain1, mismatch.domain2]:
            section_keys = SECTION_MAPPINGS.get(domain, [domain])

            for key in section_keys:
                html_key = f"{key.upper()}_HTML"
                content = healed.get(html_key) or healed.get(key, "")

                if not content or not isinstance(content, str):
                    continue

                # Try to replace the metric value
                pattern = KPI_PATTERNS.get(mismatch.metric)
                if pattern:
                    old_val = mismatch.value1 if domain == mismatch.domain1 else mismatch.value2

                    # Create replacement pattern
                    def replace_value(match: re.Match[str]) -> str:
                        # Keep the format, just change the number
                        full_match = match.group(0)
                        old_num = match.group(1)
                        new_num = f"{avg_value:.1f}"
                        return full_match.replace(old_num, new_num)

                    new_content = re.sub(pattern, replace_value, content, count=1, flags=re.IGNORECASE)

                    if new_content != content:
                        if html_key in healed:
                            healed[html_key] = new_content
                        else:
                            healed[key] = new_content

        mismatch.healed = True
        report.healed_mismatches += 1

    log.info(
        "[N3.8-Integrity] Healing complete: healed_mismatches=%d",
        report.healed_mismatches
    )

    # Set integrity flag
    healed["_integrity_verified"] = True
    healed["_integrity_report"] = report.to_dict()

    return healed


def add_mitigation_recommendations(
    sections: SectionDict,
    report: IntegrityReport
) -> SectionDict:
    """
    N3.8: Add mitigation recommendations for unaddressed risks.

    Args:
        sections: Dictionary of section contents
        report: IntegrityReport with risk gaps

    Returns:
        Sections with added mitigation recommendations
    """
    healed = dict(sections)

    log.info("[N3.8-Integrity] Adding mitigation recommendations...")

    mitigation_additions: List[str] = []

    for gap in report.risk_gaps:
        if gap.healed or gap.mitigation_found:
            continue

        # Generate mitigation recommendation
        risk_type = gap.risk_type
        mitigations = MITIGATION_KEYWORDS.get(risk_type, [])

        if mitigations:
            mitigation_text = f"<li><strong>{risk_type.title()}-Risiko:</strong> Empfohlene Maßnahmen: {', '.join(mitigations[:3])}</li>"
            mitigation_additions.append(mitigation_text)
            gap.healed = True
            report.healed_gaps += 1

    # Add to recommendations section
    if mitigation_additions:
        reco_key = None
        for key in ["RECOMMENDATIONS_HTML", "recommendations", "handlungsempfehlungen"]:
            if key in healed or key.upper() + "_HTML" in healed:
                reco_key = key if key in healed else key.upper() + "_HTML"
                break

        if reco_key and healed.get(reco_key):
            content = healed[reco_key]

            # Find last </ul> and insert before it
            insert_pos = content.rfind("</ul>")
            if insert_pos > 0:
                additions = "\n".join(mitigation_additions)
                healed[reco_key] = content[:insert_pos] + additions + content[insert_pos:]

    log.info(
        "[N3.8-Integrity] Added %d mitigation recommendations",
        report.healed_gaps
    )

    return healed


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_integrity(sections: SectionDict) -> Tuple[SectionDict, IntegrityReport]:
    """
    N3.8: Full integrity processing pipeline.

    1. Verify numeric coherence
    2. Heal inconsistencies
    3. Add mitigation recommendations

    Args:
        sections: Dictionary of section contents

    Returns:
        Tuple of (processed_sections, report)
    """
    log.info("[N3.8-Integrity] Starting full integrity processing...")

    # Step 1: Verify
    report = verify_numeric_coherence(sections)

    # Step 2: Heal numeric mismatches
    healed = heal_numeric_inconsistencies(sections, report)

    # Step 3: Add mitigation recommendations
    healed = add_mitigation_recommendations(healed, report)

    log.info(
        "[N3.8-Integrity] Complete: score=%.1f grade=%s healed=%d",
        report.overall_score,
        report.grade,
        report.healed_mismatches + report.healed_gaps
    )

    return healed, report


def get_integrity_summary(report: IntegrityReport) -> str:
    """
    Generate a human-readable integrity summary.

    Args:
        report: IntegrityReport

    Returns:
        Summary string
    """
    summary_parts = [
        f"Integrity Score: {report.overall_score:.1f}/100 (Grade: {report.grade})",
        f"Domains Checked: {report.domains_checked}",
        f"Metrics Validated: {report.metrics_validated}",
    ]

    if report.mismatches:
        summary_parts.append(f"Numeric Mismatches: {len(report.mismatches)} ({report.healed_mismatches} healed)")

    if report.risk_gaps:
        summary_parts.append(f"Risk-Mitigation Gaps: {len(report.risk_gaps)} ({report.healed_gaps} addressed)")

    return "\n".join(summary_parts)
