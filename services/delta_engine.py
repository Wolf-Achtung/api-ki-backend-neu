# -*- coding: utf-8 -*-
"""
Sprint G11: Delta Engine 1.0

Provides intelligent comparison between report versions:
- Section-level word count delta
- Semantic similarity (optional, requires embeddings)
- Score and KPI changes
- AI Act compliance changes
- Business case evolution

Version: 1.0.0 (Sprint G11)
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from difflib import SequenceMatcher

log = logging.getLogger(__name__)

# =============================================================================
# ENV CONFIGURATION
# =============================================================================

ENABLE_DELTA_ENGINE = os.getenv("ENABLE_DELTA_ENGINE", "1").lower() in ("1", "true", "yes")
DELTA_EMBEDDING_MODEL = os.getenv("DELTA_EMBEDDING_MODEL", "")
SIGNIFICANT_WORD_CHANGE_THRESHOLD = int(os.getenv("DELTA_WORD_THRESHOLD", "50"))
SIGNIFICANT_SCORE_CHANGE_THRESHOLD = float(os.getenv("DELTA_SCORE_THRESHOLD", "5.0"))


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SectionDelta:
    """Delta analysis for a single section."""
    section: str
    change_type: str  # "significant", "minor", "none"
    old_tokens: int = 0
    new_tokens: int = 0
    word_delta: int = 0
    word_delta_percent: float = 0.0
    semantic_similarity: Optional[float] = None
    highlights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScoreDelta:
    """Delta analysis for scores."""
    field: str
    old_value: Any
    new_value: Any
    delta: float = 0.0
    is_improvement: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BCDelta:
    """Delta analysis for business case."""
    field: str
    old_value: Any
    new_value: Any
    delta: float = 0.0
    delta_percent: float = 0.0
    is_favorable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FullDelta:
    """Complete delta between two report versions."""
    from_version: int
    to_version: int
    section_deltas: List[SectionDelta] = field(default_factory=list)
    score_deltas: List[ScoreDelta] = field(default_factory=list)
    bc_deltas: List[BCDelta] = field(default_factory=list)
    ai_act_changes: Dict[str, Any] = field(default_factory=dict)
    label_changes: Dict[str, Any] = field(default_factory=dict)
    overall_change_type: str = "none"  # "major", "moderate", "minor", "none"
    summary_de: str = ""
    summary_en: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "section_deltas": [s.to_dict() for s in self.section_deltas],
            "score_deltas": [s.to_dict() for s in self.score_deltas],
            "bc_deltas": [b.to_dict() for b in self.bc_deltas],
            "ai_act_changes": self.ai_act_changes,
            "label_changes": self.label_changes,
            "overall_change_type": self.overall_change_type,
            "summary_de": self.summary_de,
            "summary_en": self.summary_en,
        }


# =============================================================================
# CORE DELTA COMPUTATION
# =============================================================================

def compute_delta(
    v1: Dict[str, Any],
    v2: Dict[str, Any],
    include_semantic: bool = False
) -> Dict[str, Any]:
    """
    Compute comprehensive delta between two report versions.

    Args:
        v1: First (older) version data
        v2: Second (newer) version data
        include_semantic: Whether to compute semantic similarity (slower)

    Returns:
        Full delta analysis as dictionary
    """
    if not ENABLE_DELTA_ENGINE:
        return {"enabled": False, "message": "Delta engine disabled"}

    delta = FullDelta(
        from_version=v1.get("version", 0),
        to_version=v2.get("version", 0),
    )

    # Compute section deltas
    delta.section_deltas = _compute_section_deltas(
        v1.get("section_stats", {}),
        v2.get("section_stats", {}),
        include_semantic
    )

    # Compute score deltas
    delta.score_deltas = _compute_score_deltas(
        v1.get("scores", {}),
        v2.get("scores", {})
    )

    # Compute business case deltas
    delta.bc_deltas = _compute_bc_deltas(
        v1.get("business_case", {}),
        v2.get("business_case", {})
    )

    # Compute AI Act changes
    delta.ai_act_changes = _compute_ai_act_changes(
        v1.get("ai_act", {}),
        v2.get("ai_act", {})
    )

    # Compute label changes
    delta.label_changes = _compute_label_changes(
        v1.get("labels", {}),
        v2.get("labels", {})
    )

    # Determine overall change type
    delta.overall_change_type = _determine_overall_change_type(delta)

    # Generate summaries
    delta.summary_de = _generate_summary_de(delta)
    delta.summary_en = _generate_summary_en(delta)

    return delta.to_dict()


def _compute_section_deltas(
    old_stats: Dict[str, Any],
    new_stats: Dict[str, Any],
    include_semantic: bool = False
) -> List[SectionDelta]:
    """Compute deltas for each section."""
    deltas = []

    all_sections = set(old_stats.keys()) | set(new_stats.keys())

    for section in all_sections:
        old_data = old_stats.get(section, {})
        new_data = new_stats.get(section, {})

        old_wc = old_data.get("word_count", 0)
        new_wc = new_data.get("word_count", 0)
        word_delta = new_wc - old_wc

        # Calculate percentage change
        if old_wc > 0:
            word_delta_percent = (word_delta / old_wc) * 100
        else:
            word_delta_percent = 100.0 if new_wc > 0 else 0.0

        # Determine change type
        if abs(word_delta) >= SIGNIFICANT_WORD_CHANGE_THRESHOLD * 2:
            change_type = "significant"
        elif abs(word_delta) >= SIGNIFICANT_WORD_CHANGE_THRESHOLD:
            change_type = "minor"
        else:
            change_type = "none"

        delta = SectionDelta(
            section=section,
            change_type=change_type,
            old_tokens=old_wc,
            new_tokens=new_wc,
            word_delta=word_delta,
            word_delta_percent=round(word_delta_percent, 1),
        )

        deltas.append(delta)

    return deltas


def _compute_score_deltas(
    old_scores: Dict[str, Any],
    new_scores: Dict[str, Any]
) -> List[ScoreDelta]:
    """Compute deltas for scores."""
    deltas = []

    score_fields = [
        "GOVERNANCE_SCORE", "SECURITY_SCORE", "BENEFIT_SCORE",
        "READINESS_SCORE", "RISK_SCORE", "OVERALL_SCORE",
    ]

    for field in score_fields:
        old_val = old_scores.get(field)
        new_val = new_scores.get(field)

        if old_val is None and new_val is None:
            continue

        old_num = float(old_val) if old_val is not None else 0.0
        new_num = float(new_val) if new_val is not None else 0.0
        delta_val = new_num - old_num

        if abs(delta_val) >= SIGNIFICANT_SCORE_CHANGE_THRESHOLD:
            deltas.append(ScoreDelta(
                field=field,
                old_value=old_val,
                new_value=new_val,
                delta=round(delta_val, 1),
                is_improvement=delta_val > 0 if field != "RISK_SCORE" else delta_val < 0,
            ))

    return deltas


def _compute_bc_deltas(
    old_bc: Dict[str, Any],
    new_bc: Dict[str, Any]
) -> List[BCDelta]:
    """Compute deltas for business case metrics."""
    deltas = []

    bc_fields = {
        "CAPEX_REALISTISCH_EUR": ("cost", False),  # Lower is better
        "OPEX_REALISTISCH_EUR": ("cost", False),
        "EINSPARUNG_MONAT_EUR": ("benefit", True),  # Higher is better
        "ROI_12M": ("roi", True),
        "PAYBACK_MONTHS": ("payback", False),  # Lower is better
    }

    for field, (category, higher_is_better) in bc_fields.items():
        old_val = old_bc.get(field)
        new_val = new_bc.get(field)

        if old_val is None and new_val is None:
            continue

        old_num = float(old_val) if old_val is not None else 0.0
        new_num = float(new_val) if new_val is not None else 0.0
        delta_val = new_num - old_num

        # Calculate percentage change
        if old_num != 0:
            delta_pct = (delta_val / abs(old_num)) * 100
        else:
            delta_pct = 100.0 if new_num != 0 else 0.0

        # Only include significant changes (>5%)
        if abs(delta_pct) >= 5.0 or abs(delta_val) >= 100:
            is_favorable = delta_val > 0 if higher_is_better else delta_val < 0

            deltas.append(BCDelta(
                field=field,
                old_value=old_val,
                new_value=new_val,
                delta=round(delta_val, 2),
                delta_percent=round(delta_pct, 1),
                is_favorable=is_favorable,
            ))

    return deltas


def _compute_ai_act_changes(
    old_ai_act: Dict[str, Any],
    new_ai_act: Dict[str, Any]
) -> Dict[str, Any]:
    """Compute changes in AI Act compliance."""
    changes = {}

    # Risk level change
    old_risk = old_ai_act.get("AI_ACT_RISK_LEVEL")
    new_risk = new_ai_act.get("AI_ACT_RISK_LEVEL")
    if old_risk != new_risk:
        risk_order = {"none": 0, "minimal": 1, "limited": 2, "high-risk": 3}
        old_order = risk_order.get(old_risk, -1)
        new_order = risk_order.get(new_risk, -1)

        changes["risk_level"] = {
            "old": old_risk,
            "new": new_risk,
            "direction": "increased" if new_order > old_order else "decreased",
            "significant": abs(new_order - old_order) >= 2,
        }

    # Modifier changes
    for mod in ["CAPEX_MODIFIER", "OPEX_MODIFIER"]:
        old_mod = old_ai_act.get(mod, 1.0)
        new_mod = new_ai_act.get(mod, 1.0)
        if old_mod != new_mod:
            changes[mod.lower()] = {
                "old": old_mod,
                "new": new_mod,
                "delta": round(new_mod - old_mod, 2),
            }

    return changes


def _compute_label_changes(
    old_labels: Dict[str, Any],
    new_labels: Dict[str, Any]
) -> Dict[str, Any]:
    """Compute changes in labels."""
    changes = {}

    for key in set(old_labels.keys()) | set(new_labels.keys()):
        old_val = old_labels.get(key)
        new_val = new_labels.get(key)
        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}

    return changes


def _determine_overall_change_type(delta: FullDelta) -> str:
    """Determine the overall significance of changes."""
    significant_sections = sum(1 for s in delta.section_deltas if s.change_type == "significant")
    score_changes = len(delta.score_deltas)
    bc_changes = len(delta.bc_deltas)
    risk_changed = "risk_level" in delta.ai_act_changes

    if risk_changed or significant_sections >= 3 or score_changes >= 3:
        return "major"
    elif significant_sections >= 1 or score_changes >= 1 or bc_changes >= 2:
        return "moderate"
    elif delta.section_deltas or delta.bc_deltas:
        return "minor"
    else:
        return "none"


def _generate_summary_de(delta: FullDelta) -> str:
    """Generate German summary of changes."""
    parts = []

    if delta.ai_act_changes.get("risk_level"):
        rc = delta.ai_act_changes["risk_level"]
        parts.append(f"AI-Act-Risiko: {rc['old']} → {rc['new']}")

    significant = [s for s in delta.section_deltas if s.change_type == "significant"]
    if significant:
        sections = ", ".join(s.section for s in significant[:3])
        parts.append(f"Wesentliche Änderungen in: {sections}")

    score_improvements = [s for s in delta.score_deltas if s.is_improvement]
    if score_improvements:
        parts.append(f"{len(score_improvements)} Score(s) verbessert")

    if delta.bc_deltas:
        favorable = sum(1 for b in delta.bc_deltas if b.is_favorable)
        parts.append(f"Business Case: {favorable}/{len(delta.bc_deltas)} Verbesserungen")

    if not parts:
        return "Keine wesentlichen Änderungen seit der letzten Version."

    return " | ".join(parts)


def _generate_summary_en(delta: FullDelta) -> str:
    """Generate English summary of changes."""
    parts = []

    if delta.ai_act_changes.get("risk_level"):
        rc = delta.ai_act_changes["risk_level"]
        parts.append(f"AI Act risk: {rc['old']} → {rc['new']}")

    significant = [s for s in delta.section_deltas if s.change_type == "significant"]
    if significant:
        sections = ", ".join(s.section for s in significant[:3])
        parts.append(f"Significant changes in: {sections}")

    score_improvements = [s for s in delta.score_deltas if s.is_improvement]
    if score_improvements:
        parts.append(f"{len(score_improvements)} score(s) improved")

    if delta.bc_deltas:
        favorable = sum(1 for b in delta.bc_deltas if b.is_favorable)
        parts.append(f"Business case: {favorable}/{len(delta.bc_deltas)} improvements")

    if not parts:
        return "No significant changes since last version."

    return " | ".join(parts)


# =============================================================================
# SEMANTIC SIMILARITY (OPTIONAL)
# =============================================================================

def compute_semantic_similarity(text1: str, text2: str) -> float:
    """
    Compute semantic similarity between two texts.

    Uses simple sequence matching as fallback when embeddings not available.
    """
    if not text1 or not text2:
        return 0.0

    # Strip HTML tags
    text1_clean = re.sub(r"<[^>]+>", " ", text1).strip()
    text2_clean = re.sub(r"<[^>]+>", " ", text2).strip()

    # Use SequenceMatcher for basic similarity
    return SequenceMatcher(None, text1_clean, text2_clean).ratio()


# =============================================================================
# PDF DELTA BLOCK GENERATOR
# =============================================================================

def generate_delta_html_block(delta: Dict[str, Any], lang: str = "de") -> str:
    """
    Generate HTML block for PDF showing version changes.

    Args:
        delta: Delta dict from compute_delta()
        lang: Language code (de/en)

    Returns:
        HTML string for PDF template
    """
    if not delta or delta.get("overall_change_type") == "none":
        return ""

    summary = delta.get("summary_de" if lang == "de" else "summary_en", "")

    title = "Veränderungen seit Ihrem letzten Report" if lang == "de" else "Changes since your last report"

    html = f"""
    <div class="delta-block" style="margin-top:20px;padding:16px;background:#f8f9fa;border-radius:8px;border-left:4px solid #007bff;">
        <h4 style="margin:0 0 12px 0;color:#007bff;font-size:14px;">{title}</h4>
        <p style="margin:0;font-size:13px;color:#495057;">{summary}</p>
    """

    # Add change type badge
    change_type = delta.get("overall_change_type", "none")
    badge_colors = {
        "major": "#dc3545",
        "moderate": "#ffc107",
        "minor": "#28a745",
        "none": "#6c757d",
    }
    badge_labels_de = {
        "major": "Große Änderungen",
        "moderate": "Moderate Änderungen",
        "minor": "Kleine Änderungen",
        "none": "Keine Änderungen",
    }
    badge_labels_en = {
        "major": "Major changes",
        "moderate": "Moderate changes",
        "minor": "Minor changes",
        "none": "No changes",
    }

    badge_label = badge_labels_de.get(change_type) if lang == "de" else badge_labels_en.get(change_type)
    badge_color = badge_colors.get(change_type, "#6c757d")

    html += f"""
        <div style="margin-top:12px;">
            <span style="display:inline-block;padding:4px 8px;background:{badge_color};color:#fff;border-radius:4px;font-size:11px;">{badge_label}</span>
        </div>
    </div>
    """

    return html


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G11] Delta Engine loaded - enabled=%s", ENABLE_DELTA_ENGINE)
