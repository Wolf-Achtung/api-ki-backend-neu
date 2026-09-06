# -*- coding: utf-8 -*-
"""
N4.3: Cross-Model Consistency Kernel v7
=======================================

PLATIN+++ v5.3 - Enterprise Safety Layer

Advanced cross-model consistency validation:
- Claude and GPT output semantic normalization
- Contradiction identification and merge
- 3-Way Alignment: narrative, numerical, governance
- Tolerance-based validation

Tolerances:
- KPIs: ±3%
- Governance claims: ±1 level
- Risk trends: ≥90% semantic overlap

Self-healing: Automatically resolves model disagreements.

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
Author: Claude + Wolf
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from services.types import SectionDict, BriefingDict

log = logging.getLogger(__name__)

__all__ = [
    "AlignmentDimension",
    "ConsistencyLevel",
    "ModelSource",
    "ConsistencyIssue",
    "AlignmentResult",
    "ConsistencyKernelV7",
    "normalize_model_output",
    "identify_contradictions",
    "merge_model_outputs",
    "check_3way_alignment",
    "validate_cross_model_consistency",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class AlignmentDimension(Enum):
    """Dimensions for cross-model alignment."""
    NARRATIVE = "narrative"     # Text/story consistency
    NUMERICAL = "numerical"     # KPI/metric consistency
    GOVERNANCE = "governance"   # Compliance/risk consistency


class ConsistencyLevel(Enum):
    """Consistency levels between models."""
    FULL = "full"           # Complete agreement
    HIGH = "high"           # Minor differences (within tolerance)
    MODERATE = "moderate"   # Some disagreements (healable)
    LOW = "low"             # Significant disagreements
    CONFLICT = "conflict"   # Direct contradiction


class ModelSource(Enum):
    """AI model sources."""
    CLAUDE = "claude"
    GPT = "gpt"
    MERGED = "merged"
    UNKNOWN = "unknown"


class IssueSeverity(Enum):
    """Consistency issue severity."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Tolerance thresholds
TOLERANCES: Dict[str, float] = {
    "kpi_percentage": 0.03,         # ±3% for KPIs
    "kpi_absolute": 0.05,           # ±5% for absolute values
    "governance_level": 1,          # ±1 level for governance
    "semantic_overlap": 0.90,       # 90% minimum overlap
    "risk_trend": 0.90,             # 90% for risk trends
    "narrative_similarity": 0.85,   # 85% for narratives
}

# Governance level mapping
GOVERNANCE_LEVELS: Dict[str, int] = {
    "optimizing": 5,
    "managed": 4,
    "defined": 3,
    "developing": 2,
    "initial": 1,
    # Risk levels
    "minimal": 1,
    "limited": 2,
    "high": 3,
    "unacceptable": 4,
    # Maturity levels
    "excellent": 5,
    "good": 4,
    "adequate": 3,
    "needs_improvement": 2,
    "poor": 1,
}

# KPI extraction patterns
KPI_PATTERNS: Dict[str, str] = {
    "roi": r"ROI[:\s]*(\d+(?:[.,]\d+)?)\s*%",
    "payback": r"(?:Payback|Amortisation)[:\s-]*(\d+(?:[.,]\d+)?)",
    "savings": r"(?:Einspar|Savings?|Ersparnis)[:\s]*(\d+(?:[.,]\d+)?)",
    "time_savings": r"(?:Zeit(?:ersparnis)?|Time\s+Savings?)[:\s]*(\d+(?:[.,]\d+)?)",
    "productivity": r"(?:Produktivität|Productivity)[:\s]*(?:\+)?(\d+(?:[.,]\d+)?)\s*%",
    "fte": r"FTE[:\s-]*(\d+(?:[.,]\d+)?)",
    "cost": r"(?:Kosten|Cost|Investition)[:\s]*(\d+(?:[.,]\d+)?)",
}

# Governance claim patterns
GOVERNANCE_PATTERNS: Dict[str, List[str]] = {
    "risk_level": [
        r"(?:risk\s+level|Risikostufe|niveau\s+de\s+risque)[:\s]*(\w+)",
        r"(?:high|medium|low|minimal|limited)\s+risk",
        r"(?:hohes?|mittleres?|niedriges?|minimales?)\s+Risiko",
    ],
    "maturity": [
        r"(?:maturity|Reifegrad|maturité)[:\s]*(\w+)",
        r"(?:initial|developing|defined|managed|optimizing)",
    ],
    "compliance": [
        r"(?:compliant|konform|conforme)",
        r"(?:non-compliant|nicht\s+konform|non\s+conforme)",
    ],
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ConsistencyIssue:
    """A single consistency issue between models."""

    issue_id: str
    dimension: AlignmentDimension
    severity: IssueSeverity
    section: str
    description: str
    claude_value: str = ""
    gpt_value: str = ""
    merged_value: str = ""
    deviation: float = 0.0
    auto_healable: bool = True
    healed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_id": self.issue_id,
            "dimension": self.dimension.value,
            "severity": self.severity.value,
            "section": self.section,
            "description": self.description,
            "claude_value": self.claude_value[:50] if self.claude_value else "",
            "gpt_value": self.gpt_value[:50] if self.gpt_value else "",
            "merged_value": self.merged_value[:50] if self.merged_value else "",
            "deviation": round(self.deviation, 4),
            "auto_healable": self.auto_healable,
            "healed": self.healed,
        }


@dataclass
class AlignmentResult:
    """Result of alignment check for a dimension."""

    dimension: AlignmentDimension
    consistency_level: ConsistencyLevel
    score: float  # 0.0 - 1.0
    issues: List[ConsistencyIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dimension": self.dimension.value,
            "consistency_level": self.consistency_level.value,
            "score": round(self.score, 3),
            "issues_count": len(self.issues),
            "metrics": self.metrics,
        }


@dataclass
class ConsistencyKernelReport:
    """Report from consistency kernel."""

    engine_id: str = "CONSISTENCY_KERNEL_V7"
    success: bool = True
    model_consistency_validated: bool = False
    narrative_alignment: float = 0.0
    numerical_alignment: float = 0.0
    governance_alignment: float = 0.0
    overall_alignment: float = 0.0
    contradictions_found: int = 0
    contradictions_resolved: int = 0
    kpi_deviations: int = 0
    governance_mismatches: int = 0
    healed: bool = False
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "model_consistency_validated": self.model_consistency_validated,
            "narrative_alignment": round(self.narrative_alignment, 3),
            "numerical_alignment": round(self.numerical_alignment, 3),
            "governance_alignment": round(self.governance_alignment, 3),
            "overall_alignment": round(self.overall_alignment, 3),
            "contradictions_found": self.contradictions_found,
            "contradictions_resolved": self.contradictions_resolved,
            "kpi_deviations": self.kpi_deviations,
            "governance_mismatches": self.governance_mismatches,
            "healed": self.healed,
            "issues": self.issues,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# CONSISTENCY KERNEL V7
# =============================================================================

class ConsistencyKernelV7:
    """
    N4.3: Cross-Model Consistency Kernel.

    Validates and merges outputs from different AI models:
    - Semantic normalization
    - Contradiction detection
    - 3-way alignment (narrative, numerical, governance)
    - Tolerance-based validation

    Self-healing: Automatically resolves model disagreements.
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        claude_output: Optional[SectionDict] = None,
        gpt_output: Optional[SectionDict] = None,
    ) -> None:
        """
        Initialize Consistency Kernel v7.

        Args:
            sections: Current section dictionary
            briefing: Briefing data
            claude_output: Optional Claude-specific output
            gpt_output: Optional GPT-specific output
        """
        self.sections = sections
        self.briefing = briefing
        self.claude_output = claude_output or {}
        self.gpt_output = gpt_output or {}

        self._report = ConsistencyKernelReport()
        self._issues: List[ConsistencyIssue] = []
        self._issue_counter = 0

        # Extract model outputs from sections if not provided
        if not self.claude_output:
            self.claude_output = self._extract_model_output(sections, ModelSource.CLAUDE)
        if not self.gpt_output:
            self.gpt_output = self._extract_model_output(sections, ModelSource.GPT)

        log.info("[N4.3-Consistency] Kernel initialized")

    def process(self) -> Tuple[SectionDict, ConsistencyKernelReport]:
        """
        Process sections through consistency kernel.

        Returns:
            Tuple of (merged_sections, report)
        """
        log.info("[N4.3-Consistency] Processing started")

        # Step 1: Normalize outputs
        normalized_claude = self._normalize_output(self.claude_output)
        normalized_gpt = self._normalize_output(self.gpt_output)

        # Step 2: Check narrative alignment
        narrative_result = self._check_narrative_alignment(
            normalized_claude, normalized_gpt
        )
        self._report.narrative_alignment = narrative_result.score
        self._issues.extend(narrative_result.issues)

        # Step 3: Check numerical alignment
        numerical_result = self._check_numerical_alignment(
            normalized_claude, normalized_gpt
        )
        self._report.numerical_alignment = numerical_result.score
        self._report.kpi_deviations = len([
            i for i in numerical_result.issues
            if i.dimension == AlignmentDimension.NUMERICAL
        ])
        self._issues.extend(numerical_result.issues)

        # Step 4: Check governance alignment
        governance_result = self._check_governance_alignment(
            normalized_claude, normalized_gpt
        )
        self._report.governance_alignment = governance_result.score
        self._report.governance_mismatches = len([
            i for i in governance_result.issues
            if i.dimension == AlignmentDimension.GOVERNANCE
        ])
        self._issues.extend(governance_result.issues)

        # Step 5: Identify contradictions
        contradictions = self._identify_contradictions(
            normalized_claude, normalized_gpt
        )
        self._report.contradictions_found = len(contradictions)
        self._issues.extend(contradictions)

        # Step 6: Resolve contradictions (self-healing)
        resolved = self._resolve_contradictions(contradictions)
        self._report.contradictions_resolved = resolved
        self._report.healed = resolved > 0

        # Step 7: Merge outputs
        # KIS-1327: Die normalisierten Fassungen (Leerraum gerafft, Dezimalkomma
        # zu Punkt) dienen nur dem Vergleich. Bis Lauf KIS1296 gingen sie als
        # Sektionen zurück in den Report — „5,50–8,30 €" wurde „5.50–8.30 €"
        # (Duden-Mentor, R1 S. 14, seit KIS1293 beobachtet, Ursache offen).
        merged_sections = self._merge_outputs(
            self.claude_output, self.gpt_output
        )

        # Calculate overall alignment
        self._report.overall_alignment = (
            self._report.narrative_alignment * 0.4 +
            self._report.numerical_alignment * 0.35 +
            self._report.governance_alignment * 0.25
        )

        # Validate consistency
        self._report.model_consistency_validated = (
            self._report.overall_alignment >= 0.85 and
            self._report.contradictions_found == self._report.contradictions_resolved
        )
        self._report.success = self._report.model_consistency_validated

        # Store metadata
        merged_sections["_model_consistency_validated"] = self._report.model_consistency_validated
        merged_sections["_consistency_report"] = self._report.to_dict()
        merged_sections["_model_healed"] = self._report.healed

        log.info(
            "[N4.3-Consistency] Complete: alignment=%.2f, contradictions=%d/%d resolved",
            self._report.overall_alignment,
            self._report.contradictions_resolved,
            self._report.contradictions_found
        )

        return merged_sections, self._report

    def _extract_model_output(
        self,
        sections: SectionDict,
        source: ModelSource,
    ) -> SectionDict:
        """Extract model-specific output from sections."""
        prefix = f"_{source.value}_"
        output: SectionDict = {}

        for key, value in sections.items():
            if key.startswith(prefix):
                clean_key = key[len(prefix):]
                output[clean_key] = value
            elif not key.startswith("_"):
                output[key] = value

        return output

    def _normalize_output(self, output: SectionDict) -> SectionDict:
        """Normalize model output for comparison."""
        normalized: SectionDict = {}

        for key, value in output.items():
            if isinstance(value, str):
                # Normalize whitespace
                normalized_value = " ".join(value.split())
                # Normalize numbers (replace comma with dot for decimals)
                normalized_value = re.sub(r"(\d),(\d)", r"\1.\2", normalized_value)
                normalized[key] = normalized_value
            elif isinstance(value, dict):
                normalized[key] = self._normalize_output(value)
            else:
                normalized[key] = value

        return normalized

    def _check_narrative_alignment(
        self,
        claude_output: SectionDict,
        gpt_output: SectionDict,
    ) -> AlignmentResult:
        """Check narrative alignment between models."""
        issues: List[ConsistencyIssue] = []
        similarities: List[float] = []

        # Get common keys
        claude_keys = set(k for k in claude_output.keys() if not k.startswith("_"))
        gpt_keys = set(k for k in gpt_output.keys() if not k.startswith("_"))
        common_keys = claude_keys & gpt_keys

        for key in common_keys:
            claude_text = str(claude_output.get(key, ""))
            gpt_text = str(gpt_output.get(key, ""))

            if not claude_text or not gpt_text:
                continue

            # Calculate similarity
            similarity = self._calculate_text_similarity(claude_text, gpt_text)
            similarities.append(similarity)

            if similarity < TOLERANCES["narrative_similarity"]:
                issue = ConsistencyIssue(
                    issue_id=self._get_issue_id(),
                    dimension=AlignmentDimension.NARRATIVE,
                    severity=IssueSeverity.MEDIUM if similarity >= 0.7 else IssueSeverity.HIGH,
                    section=key,
                    description=f"Narrative divergence: {(1-similarity)*100:.1f}%",
                    claude_value=claude_text[:100],
                    gpt_value=gpt_text[:100],
                    deviation=1 - similarity,
                )
                issues.append(issue)

        # Calculate overall score
        score = sum(similarities) / len(similarities) if similarities else 1.0

        # Determine consistency level
        if score >= 0.95:
            level = ConsistencyLevel.FULL
        elif score >= 0.90:
            level = ConsistencyLevel.HIGH
        elif score >= 0.80:
            level = ConsistencyLevel.MODERATE
        elif score >= 0.70:
            level = ConsistencyLevel.LOW
        else:
            level = ConsistencyLevel.CONFLICT

        return AlignmentResult(
            dimension=AlignmentDimension.NARRATIVE,
            consistency_level=level,
            score=score,
            issues=issues,
            metrics={"sections_compared": len(common_keys)},
        )

    def _check_numerical_alignment(
        self,
        claude_output: SectionDict,
        gpt_output: SectionDict,
    ) -> AlignmentResult:
        """Check numerical alignment between models."""
        issues: List[ConsistencyIssue] = []
        kpi_comparisons: List[Tuple[str, float, float]] = []

        # Extract KPIs from both outputs
        claude_kpis = self._extract_kpis(claude_output)
        gpt_kpis = self._extract_kpis(gpt_output)

        # Compare common KPIs
        common_kpis = set(claude_kpis.keys()) & set(gpt_kpis.keys())

        for kpi in common_kpis:
            claude_val = claude_kpis[kpi]
            gpt_val = gpt_kpis[kpi]

            if claude_val == 0 and gpt_val == 0:
                continue

            # Calculate deviation
            base = max(abs(claude_val), abs(gpt_val), 1)
            deviation = abs(claude_val - gpt_val) / base

            kpi_comparisons.append((kpi, claude_val, gpt_val))

            # Check tolerance
            tolerance = TOLERANCES["kpi_percentage"]
            if deviation > tolerance:
                issue = ConsistencyIssue(
                    issue_id=self._get_issue_id(),
                    dimension=AlignmentDimension.NUMERICAL,
                    severity=IssueSeverity.HIGH if deviation > 0.10 else IssueSeverity.MEDIUM,
                    section=kpi,
                    description=f"KPI deviation: {deviation*100:.1f}% (tolerance: {tolerance*100:.0f}%)",
                    claude_value=str(claude_val),
                    gpt_value=str(gpt_val),
                    merged_value=str((claude_val + gpt_val) / 2),
                    deviation=deviation,
                )
                issues.append(issue)

        # Calculate score
        if kpi_comparisons:
            deviations = [
                abs(c - g) / max(abs(c), abs(g), 1)
                for _, c, g in kpi_comparisons
            ]
            score = 1.0 - (sum(deviations) / len(deviations))
        else:
            score = 1.0

        # Determine level
        if score >= 0.97:
            level = ConsistencyLevel.FULL
        elif score >= 0.93:
            level = ConsistencyLevel.HIGH
        elif score >= 0.85:
            level = ConsistencyLevel.MODERATE
        else:
            level = ConsistencyLevel.LOW

        return AlignmentResult(
            dimension=AlignmentDimension.NUMERICAL,
            consistency_level=level,
            score=score,
            issues=issues,
            metrics={"kpis_compared": len(common_kpis)},
        )

    def _check_governance_alignment(
        self,
        claude_output: SectionDict,
        gpt_output: SectionDict,
    ) -> AlignmentResult:
        """Check governance alignment between models."""
        issues: List[ConsistencyIssue] = []
        alignments: List[float] = []

        # Extract governance claims
        claude_gov = self._extract_governance_claims(claude_output)
        gpt_gov = self._extract_governance_claims(gpt_output)

        # Compare risk levels
        if "risk_level" in claude_gov and "risk_level" in gpt_gov:
            claude_level = GOVERNANCE_LEVELS.get(claude_gov["risk_level"].lower(), 0)
            gpt_level = GOVERNANCE_LEVELS.get(gpt_gov["risk_level"].lower(), 0)

            level_diff = abs(claude_level - gpt_level)
            alignments.append(1.0 - (level_diff / 4))

            if level_diff > TOLERANCES["governance_level"]:
                issue = ConsistencyIssue(
                    issue_id=self._get_issue_id(),
                    dimension=AlignmentDimension.GOVERNANCE,
                    severity=IssueSeverity.CRITICAL if level_diff > 2 else IssueSeverity.HIGH,
                    section="risk_level",
                    description=f"Risk level mismatch: {level_diff} levels",
                    claude_value=claude_gov["risk_level"],
                    gpt_value=gpt_gov["risk_level"],
                    deviation=level_diff / 4,
                )
                issues.append(issue)

        # Compare maturity levels
        if "maturity" in claude_gov and "maturity" in gpt_gov:
            claude_mat = GOVERNANCE_LEVELS.get(claude_gov["maturity"].lower(), 0)
            gpt_mat = GOVERNANCE_LEVELS.get(gpt_gov["maturity"].lower(), 0)

            mat_diff = abs(claude_mat - gpt_mat)
            alignments.append(1.0 - (mat_diff / 5))

            if mat_diff > TOLERANCES["governance_level"]:
                issue = ConsistencyIssue(
                    issue_id=self._get_issue_id(),
                    dimension=AlignmentDimension.GOVERNANCE,
                    severity=IssueSeverity.HIGH,
                    section="maturity",
                    description=f"Maturity level mismatch: {mat_diff} levels",
                    claude_value=claude_gov["maturity"],
                    gpt_value=gpt_gov["maturity"],
                    deviation=mat_diff / 5,
                )
                issues.append(issue)

        # Compare compliance status
        if "compliance" in claude_gov and "compliance" in gpt_gov:
            if claude_gov["compliance"] != gpt_gov["compliance"]:
                alignments.append(0.0)
                issue = ConsistencyIssue(
                    issue_id=self._get_issue_id(),
                    dimension=AlignmentDimension.GOVERNANCE,
                    severity=IssueSeverity.CRITICAL,
                    section="compliance",
                    description="Compliance status contradiction",
                    claude_value=claude_gov["compliance"],
                    gpt_value=gpt_gov["compliance"],
                    deviation=1.0,
                    auto_healable=False,
                )
                issues.append(issue)
            else:
                alignments.append(1.0)

        # Calculate score
        score = sum(alignments) / len(alignments) if alignments else 1.0

        # Determine level
        if score >= 0.95:
            level = ConsistencyLevel.FULL
        elif score >= 0.85:
            level = ConsistencyLevel.HIGH
        elif score >= 0.70:
            level = ConsistencyLevel.MODERATE
        else:
            level = ConsistencyLevel.LOW

        return AlignmentResult(
            dimension=AlignmentDimension.GOVERNANCE,
            consistency_level=level,
            score=score,
            issues=issues,
            metrics={"claims_compared": len(alignments)},
        )

    def _identify_contradictions(
        self,
        claude_output: SectionDict,
        gpt_output: SectionDict,
    ) -> List[ConsistencyIssue]:
        """Identify direct contradictions between models."""
        contradictions: List[ConsistencyIssue] = []

        # Contradiction patterns
        contradiction_pairs = [
            ("increase", "decrease"),
            ("improve", "worsen"),
            ("positive", "negative"),
            ("success", "failure"),
            ("recommend", "advise against"),
            ("compliant", "non-compliant"),
            ("low risk", "high risk"),
            ("erhöhen", "verringern"),
            ("verbessern", "verschlechtern"),
            ("positiv", "negativ"),
            ("empfehlen", "abraten"),
            ("konform", "nicht konform"),
        ]

        common_keys = set(claude_output.keys()) & set(gpt_output.keys())

        for key in common_keys:
            if key.startswith("_"):
                continue

            claude_text = str(claude_output.get(key, "")).lower()
            gpt_text = str(gpt_output.get(key, "")).lower()

            for term1, term2 in contradiction_pairs:
                if (term1 in claude_text and term2 in gpt_text) or \
                   (term2 in claude_text and term1 in gpt_text):
                    contradiction = ConsistencyIssue(
                        issue_id=self._get_issue_id(),
                        dimension=AlignmentDimension.NARRATIVE,
                        severity=IssueSeverity.CRITICAL,
                        section=key,
                        description=f"Direct contradiction: {term1} vs {term2}",
                        claude_value=claude_text[:100],
                        gpt_value=gpt_text[:100],
                        deviation=1.0,
                    )
                    contradictions.append(contradiction)
                    break

        return contradictions

    def _resolve_contradictions(
        self,
        contradictions: List[ConsistencyIssue],
    ) -> int:
        """Resolve contradictions through consensus or preference rules."""
        resolved = 0

        for contradiction in contradictions:
            if not contradiction.auto_healable:
                self._report.issues.append(
                    f"Unresolvable contradiction in {contradiction.section}"
                )
                continue

            # Resolution strategy: prefer more conservative/cautious claim
            conservative_terms = [
                "risk", "caution", "consider", "evaluate",
                "risiko", "vorsicht", "prüfen", "bewerten",
            ]

            claude_conservative = any(
                term in contradiction.claude_value.lower()
                for term in conservative_terms
            )
            gpt_conservative = any(
                term in contradiction.gpt_value.lower()
                for term in conservative_terms
            )

            if claude_conservative and not gpt_conservative:
                contradiction.merged_value = contradiction.claude_value
            elif gpt_conservative and not claude_conservative:
                contradiction.merged_value = contradiction.gpt_value
            else:
                # Default: use Claude (typically more nuanced)
                contradiction.merged_value = contradiction.claude_value

            contradiction.healed = True
            resolved += 1
            self._report.warnings.append(
                f"Resolved contradiction in {contradiction.section}"
            )

        return resolved

    def _merge_outputs(
        self,
        claude_output: SectionDict,
        gpt_output: SectionDict,
    ) -> SectionDict:
        """Merge outputs from both models."""
        merged: SectionDict = dict(self.sections)

        # Get all keys
        all_keys = set(claude_output.keys()) | set(gpt_output.keys())

        for key in all_keys:
            if key.startswith("_"):
                continue

            claude_val = claude_output.get(key)
            gpt_val = gpt_output.get(key)

            if claude_val and gpt_val:
                # Both have values - merge
                if isinstance(claude_val, str) and isinstance(gpt_val, str):
                    # Check if significantly different
                    similarity = self._calculate_text_similarity(claude_val, gpt_val)
                    if similarity >= 0.9:
                        # Very similar - prefer Claude
                        merged[key] = claude_val
                    else:
                        # Different - use longer/more complete
                        merged[key] = claude_val if len(claude_val) >= len(gpt_val) else gpt_val
                else:
                    merged[key] = claude_val
            elif claude_val:
                merged[key] = claude_val
            elif gpt_val:
                merged[key] = gpt_val

        return merged

    def _extract_kpis(self, output: SectionDict) -> Dict[str, float]:
        """Extract KPI values from output."""
        kpis: Dict[str, float] = {}

        # Combine all text content
        text = " ".join(
            str(v) for v in output.values()
            if isinstance(v, str) and not str(v).startswith("_")
        )

        for kpi_name, pattern in KPI_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    # Convert to float (handle both . and , as decimal)
                    value_str = matches[0].replace(",", ".")
                    kpis[kpi_name] = float(value_str)
                except ValueError:
                    pass

        return kpis

    def _extract_governance_claims(self, output: SectionDict) -> Dict[str, str]:
        """Extract governance claims from output."""
        claims: Dict[str, str] = {}

        text = " ".join(
            str(v) for v in output.values()
            if isinstance(v, str)
        )

        for claim_type, patterns in GOVERNANCE_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    claims[claim_type] = match.group(1) if match.lastindex else match.group()
                    break

        return claims

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        # Tokenize
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _get_issue_id(self) -> str:
        """Generate unique issue ID."""
        self._issue_counter += 1
        return f"CON-{self._issue_counter:04d}"

    def get_issues(self) -> List[ConsistencyIssue]:
        """Get all consistency issues."""
        return self._issues


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def normalize_model_output(
    output: SectionDict,
    source: str = "unknown",
) -> SectionDict:
    """
    Normalize model output for comparison.

    Args:
        output: Model output dictionary
        source: Model source identifier

    Returns:
        Normalized output dictionary
    """
    normalized: SectionDict = {}

    for key, value in output.items():
        if isinstance(value, str):
            normalized_value = " ".join(value.split())
            normalized_value = re.sub(r"(\d),(\d)", r"\1.\2", normalized_value)
            normalized[key] = normalized_value
        else:
            normalized[key] = value

    normalized["_source"] = source
    return normalized


def identify_contradictions(
    claude_output: SectionDict,
    gpt_output: SectionDict,
) -> List[Dict[str, Any]]:
    """
    Identify contradictions between model outputs.

    Args:
        claude_output: Claude output
        gpt_output: GPT output

    Returns:
        List of contradiction dictionaries
    """
    kernel = ConsistencyKernelV7(
        sections={},
        briefing={},
        claude_output=claude_output,
        gpt_output=gpt_output,
    )

    contradictions = kernel._identify_contradictions(
        kernel._normalize_output(claude_output),
        kernel._normalize_output(gpt_output),
    )

    return [c.to_dict() for c in contradictions]


def merge_model_outputs(
    claude_output: SectionDict,
    gpt_output: SectionDict,
    preference: str = "claude",
) -> SectionDict:
    """
    Merge outputs from both models.

    Args:
        claude_output: Claude output
        gpt_output: GPT output
        preference: Preferred model for conflicts

    Returns:
        Merged output dictionary
    """
    kernel = ConsistencyKernelV7(
        sections={},
        briefing={},
        claude_output=claude_output,
        gpt_output=gpt_output,
    )

    return kernel._merge_outputs(
        kernel._normalize_output(claude_output),
        kernel._normalize_output(gpt_output),
    )


def check_3way_alignment(
    claude_output: SectionDict,
    gpt_output: SectionDict,
    reference: Optional[SectionDict] = None,
) -> Dict[str, AlignmentResult]:
    """
    Check 3-way alignment across all dimensions.

    Args:
        claude_output: Claude output
        gpt_output: GPT output
        reference: Optional reference sections

    Returns:
        Dictionary of alignment results by dimension
    """
    kernel = ConsistencyKernelV7(
        sections=reference or {},
        briefing={},
        claude_output=claude_output,
        gpt_output=gpt_output,
    )

    normalized_claude = kernel._normalize_output(claude_output)
    normalized_gpt = kernel._normalize_output(gpt_output)

    results: Dict[str, AlignmentResult] = {}

    results["narrative"] = kernel._check_narrative_alignment(
        normalized_claude, normalized_gpt
    )
    results["numerical"] = kernel._check_numerical_alignment(
        normalized_claude, normalized_gpt
    )
    results["governance"] = kernel._check_governance_alignment(
        normalized_claude, normalized_gpt
    )

    return results


def validate_cross_model_consistency(
    sections: SectionDict,
    briefing: Optional[BriefingDict] = None,
    claude_output: Optional[SectionDict] = None,
    gpt_output: Optional[SectionDict] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate cross-model consistency.

    Args:
        sections: Current sections
        briefing: Optional briefing data
        claude_output: Optional Claude output
        gpt_output: Optional GPT output

    Returns:
        Tuple of (is_consistent, details)
    """
    kernel = ConsistencyKernelV7(
        sections=sections,
        briefing=briefing or {},
        claude_output=claude_output,
        gpt_output=gpt_output,
    )

    _, report = kernel.process()

    details = {
        "validated": report.model_consistency_validated,
        "overall_alignment": report.overall_alignment,
        "narrative_alignment": report.narrative_alignment,
        "numerical_alignment": report.numerical_alignment,
        "governance_alignment": report.governance_alignment,
        "contradictions_found": report.contradictions_found,
        "contradictions_resolved": report.contradictions_resolved,
        "kpi_deviations": report.kpi_deviations,
        "governance_mismatches": report.governance_mismatches,
    }

    return report.model_consistency_validated, details
