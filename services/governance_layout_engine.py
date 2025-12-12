# -*- coding: utf-8 -*-
"""
N4.3: Governance Layout Engine v1
=================================

PLATIN+++ v5.3 - Enterprise Safety Layer

Advanced layout engine for governance-related document components:
- Policy card templates (multi-language)
- Governance matrix table layout
- Compliance badge positioning
- Page break logic for governance sections
- Risk classification visual cues

Features:
- render_policy_card(card, style, language)
- render_governance_matrix(matrix, format)
- position_compliance_badges(sections, badges)
- calculate_page_breaks(sections, max_height)
- generate_risk_visual_cues(risk_class, style)

Self-healing: Auto-adjusts layout for overflow.

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
Author: Claude + Wolf
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from services.types import SectionDict, BriefingDict
from services.language_strategy_engine import SupportedLanguage

log = logging.getLogger(__name__)

__all__ = [
    "CardStyle",
    "BadgeType",
    "LayoutMode",
    "RiskVisualStyle",
    "PolicyCardLayout",
    "MatrixCell",
    "GovernanceMatrixLayout",
    "ComplianceBadge",
    "PageBreakPoint",
    "RiskVisualCue",
    "GovernanceLayoutReport",
    "GovernanceLayoutEngineV1",
    "render_policy_card",
    "render_governance_matrix",
    "position_compliance_badges",
    "calculate_page_breaks",
    "generate_risk_visual_cues",
    "get_card_template",
    "validate_layout",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class CardStyle(Enum):
    """Policy card styles."""
    EXECUTIVE = "executive"      # Clean, minimal for executives
    DETAILED = "detailed"        # Full details for compliance teams
    COMPACT = "compact"          # Compressed for dashboards
    BOARD = "board"              # Board-ready presentation


class BadgeType(Enum):
    """Compliance badge types."""
    COMPLIANCE = "compliance"    # Compliance status badge
    RISK = "risk"                # Risk level badge
    MATURITY = "maturity"        # Maturity level badge
    FRAMEWORK = "framework"      # Framework badge (ISO, NIST, etc.)
    CERTIFICATION = "certification"  # Certification badge
    WARNING = "warning"          # Warning/alert badge


class LayoutMode(Enum):
    """Layout modes."""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    DOCX = "docx"


class RiskVisualStyle(Enum):
    """Risk visual styles."""
    TRAFFIC_LIGHT = "traffic_light"  # Red/Yellow/Green
    GRADIENT = "gradient"            # Color gradient
    ICON = "icon"                    # Icon-based
    TEXT = "text"                    # Text-only
    BADGE = "badge"                  # Badge style


# Risk level color mapping
RISK_COLORS: Dict[str, Dict[str, str]] = {
    "minimal": {
        "primary": "#28a745",    # Green
        "secondary": "#d4edda",
        "text": "#155724",
        "icon": "check-circle",
    },
    "limited": {
        "primary": "#ffc107",    # Yellow
        "secondary": "#fff3cd",
        "text": "#856404",
        "icon": "info-circle",
    },
    "high": {
        "primary": "#dc3545",    # Red
        "secondary": "#f8d7da",
        "text": "#721c24",
        "icon": "exclamation-triangle",
    },
    "unacceptable": {
        "primary": "#343a40",    # Dark
        "secondary": "#e2e3e5",
        "text": "#1b1e21",
        "icon": "ban",
    },
}

# Maturity level color mapping
MATURITY_COLORS: Dict[str, Dict[str, str]] = {
    "initial": {
        "primary": "#6c757d",
        "secondary": "#e9ecef",
        "score_range": "0-20",
    },
    "developing": {
        "primary": "#17a2b8",
        "secondary": "#d1ecf1",
        "score_range": "21-40",
    },
    "defined": {
        "primary": "#007bff",
        "secondary": "#cce5ff",
        "score_range": "41-60",
    },
    "managed": {
        "primary": "#28a745",
        "secondary": "#d4edda",
        "score_range": "61-80",
    },
    "optimizing": {
        "primary": "#20c997",
        "secondary": "#c3e6cb",
        "score_range": "81-100",
    },
}

# Page break settings
PAGE_BREAK_CONFIG: Dict[str, Any] = {
    "pdf": {
        "max_height_mm": 247,  # A4 minus margins
        "header_height_mm": 15,
        "footer_height_mm": 10,
        "card_height_mm": 45,
        "matrix_row_height_mm": 12,
        "section_gap_mm": 8,
    },
    "html": {
        "max_height_px": 1000,
        "card_height_px": 200,
        "matrix_row_height_px": 50,
    },
}

# Card template dimensions
CARD_DIMENSIONS: Dict[CardStyle, Dict[str, Any]] = {
    CardStyle.EXECUTIVE: {
        "width": "100%",
        "min_height": "80px",
        "padding": "16px 20px",
        "border_radius": "8px",
        "font_size": "14px",
    },
    CardStyle.DETAILED: {
        "width": "100%",
        "min_height": "120px",
        "padding": "20px 24px",
        "border_radius": "8px",
        "font_size": "13px",
    },
    CardStyle.COMPACT: {
        "width": "48%",
        "min_height": "60px",
        "padding": "12px 16px",
        "border_radius": "6px",
        "font_size": "12px",
    },
    CardStyle.BOARD: {
        "width": "100%",
        "min_height": "100px",
        "padding": "24px 28px",
        "border_radius": "12px",
        "font_size": "16px",
    },
}

# Multi-language labels
LAYOUT_LABELS: Dict[SupportedLanguage, Dict[str, str]] = {
    SupportedLanguage.DE: {
        "risk_level": "Risikostufe",
        "maturity": "Reifegrad",
        "compliance": "Compliance",
        "score": "Punktzahl",
        "status": "Status",
        "recommendations": "Empfehlungen",
        "controls": "Kontrollen",
        "gaps": "Lücken",
        "framework": "Framework",
        "compliant": "Konform",
        "partial": "Teilweise",
        "non_compliant": "Nicht konform",
        "high_risk": "Hohes Risiko",
        "limited_risk": "Begrenztes Risiko",
        "minimal_risk": "Minimales Risiko",
        "page": "Seite",
        "of": "von",
    },
    SupportedLanguage.EN: {
        "risk_level": "Risk Level",
        "maturity": "Maturity",
        "compliance": "Compliance",
        "score": "Score",
        "status": "Status",
        "recommendations": "Recommendations",
        "controls": "Controls",
        "gaps": "Gaps",
        "framework": "Framework",
        "compliant": "Compliant",
        "partial": "Partial",
        "non_compliant": "Non-Compliant",
        "high_risk": "High Risk",
        "limited_risk": "Limited Risk",
        "minimal_risk": "Minimal Risk",
        "page": "Page",
        "of": "of",
    },
    SupportedLanguage.FR: {
        "risk_level": "Niveau de risque",
        "maturity": "Maturité",
        "compliance": "Conformité",
        "score": "Score",
        "status": "Statut",
        "recommendations": "Recommandations",
        "controls": "Contrôles",
        "gaps": "Lacunes",
        "framework": "Cadre",
        "compliant": "Conforme",
        "partial": "Partiel",
        "non_compliant": "Non conforme",
        "high_risk": "Risque élevé",
        "limited_risk": "Risque limité",
        "minimal_risk": "Risque minimal",
        "page": "Page",
        "of": "de",
    },
    SupportedLanguage.IT: {
        "risk_level": "Livello di rischio",
        "maturity": "Maturità",
        "compliance": "Conformità",
        "score": "Punteggio",
        "status": "Stato",
        "recommendations": "Raccomandazioni",
        "controls": "Controlli",
        "gaps": "Lacune",
        "framework": "Framework",
        "compliant": "Conforme",
        "partial": "Parziale",
        "non_compliant": "Non conforme",
        "high_risk": "Alto rischio",
        "limited_risk": "Rischio limitato",
        "minimal_risk": "Rischio minimo",
        "page": "Pagina",
        "of": "di",
    },
    SupportedLanguage.ES: {
        "risk_level": "Nivel de riesgo",
        "maturity": "Madurez",
        "compliance": "Cumplimiento",
        "score": "Puntuación",
        "status": "Estado",
        "recommendations": "Recomendaciones",
        "controls": "Controles",
        "gaps": "Brechas",
        "framework": "Marco",
        "compliant": "Conforme",
        "partial": "Parcial",
        "non_compliant": "No conforme",
        "high_risk": "Alto riesgo",
        "limited_risk": "Riesgo limitado",
        "minimal_risk": "Riesgo mínimo",
        "page": "Página",
        "of": "de",
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PolicyCardLayout:
    """Layout configuration for a policy card."""

    card_id: str
    title: str
    style: CardStyle
    language: SupportedLanguage

    # Content
    summary: str = ""
    status: str = "pending"
    score: int = 0
    recommendations: List[str] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)

    # Visual
    primary_color: str = "#007bff"
    secondary_color: str = "#cce5ff"
    text_color: str = "#004085"
    icon: str = ""

    # Layout
    width: str = "100%"
    height: str = "auto"
    position: str = "relative"
    page: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "card_id": self.card_id,
            "title": self.title,
            "style": self.style.value,
            "language": self.language.value,
            "summary": self.summary,
            "status": self.status,
            "score": self.score,
            "recommendations": self.recommendations,
            "controls": self.controls,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "text_color": self.text_color,
            "icon": self.icon,
            "width": self.width,
            "height": self.height,
            "position": self.position,
            "page": self.page,
        }


@dataclass
class MatrixCell:
    """A cell in a governance matrix."""

    row: int
    col: int
    content: str
    cell_type: str = "data"  # header, data, summary
    status: str = ""  # compliant, partial, non_compliant
    score: Optional[int] = None
    color: str = ""
    colspan: int = 1
    rowspan: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "row": self.row,
            "col": self.col,
            "content": self.content,
            "cell_type": self.cell_type,
            "status": self.status,
            "score": self.score,
            "color": self.color,
            "colspan": self.colspan,
            "rowspan": self.rowspan,
        }


@dataclass
class GovernanceMatrixLayout:
    """Layout configuration for governance matrix."""

    matrix_id: str
    title: str
    language: SupportedLanguage
    rows: int = 0
    cols: int = 0
    cells: List[MatrixCell] = field(default_factory=list)
    headers: List[str] = field(default_factory=list)
    row_labels: List[str] = field(default_factory=list)
    total_score: int = 0
    page: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "matrix_id": self.matrix_id,
            "title": self.title,
            "language": self.language.value,
            "rows": self.rows,
            "cols": self.cols,
            "cells": [c.to_dict() for c in self.cells],
            "headers": self.headers,
            "row_labels": self.row_labels,
            "total_score": self.total_score,
            "page": self.page,
        }


@dataclass
class ComplianceBadge:
    """A compliance badge."""

    badge_id: str
    badge_type: BadgeType
    label: str
    value: str
    color: str
    icon: str = ""
    position: str = "top-right"  # top-right, top-left, inline, header
    section: str = ""
    size: str = "medium"  # small, medium, large

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "badge_id": self.badge_id,
            "badge_type": self.badge_type.value,
            "label": self.label,
            "value": self.value,
            "color": self.color,
            "icon": self.icon,
            "position": self.position,
            "section": self.section,
            "size": self.size,
        }


@dataclass
class PageBreakPoint:
    """A page break point in the document."""

    break_id: str
    after_section: str
    page_number: int
    reason: str = ""
    force: bool = False  # Force break even if content fits

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "break_id": self.break_id,
            "after_section": self.after_section,
            "page_number": self.page_number,
            "reason": self.reason,
            "force": self.force,
        }


@dataclass
class RiskVisualCue:
    """A visual cue for risk classification."""

    cue_id: str
    risk_class: str
    style: RiskVisualStyle
    language: SupportedLanguage
    label: str
    color: str
    icon: str
    description: str = ""
    html_class: str = ""
    css_styles: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cue_id": self.cue_id,
            "risk_class": self.risk_class,
            "style": self.style.value,
            "language": self.language.value,
            "label": self.label,
            "color": self.color,
            "icon": self.icon,
            "description": self.description,
            "html_class": self.html_class,
            "css_styles": self.css_styles,
        }


@dataclass
class GovernanceLayoutReport:
    """Report from governance layout engine."""

    engine_id: str = "GOVERNANCE_LAYOUT_V1"
    success: bool = True
    cards_rendered: int = 0
    matrices_rendered: int = 0
    badges_positioned: int = 0
    page_breaks_added: int = 0
    total_pages: int = 1
    overflow_healed: int = 0
    healed: bool = False
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "cards_rendered": self.cards_rendered,
            "matrices_rendered": self.matrices_rendered,
            "badges_positioned": self.badges_positioned,
            "page_breaks_added": self.page_breaks_added,
            "total_pages": self.total_pages,
            "overflow_healed": self.overflow_healed,
            "healed": self.healed,
            "issues": self.issues,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# GOVERNANCE LAYOUT ENGINE V1
# =============================================================================

class GovernanceLayoutEngineV1:
    """
    N4.3: Governance Layout Engine.

    Generates visual layouts for governance components:
    - Policy cards with multi-language support
    - Governance matrix tables
    - Compliance badges
    - Page break logic
    - Risk classification visuals

    Self-healing: Auto-adjusts for content overflow.
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        target_language: str = "de",
        layout_mode: str = "pdf",
        card_style: str = "executive",
    ) -> None:
        """
        Initialize Governance Layout Engine v1.

        Args:
            sections: Section dictionary
            briefing: Briefing data
            target_language: Target language code
            layout_mode: Layout mode (pdf, html, markdown, docx)
            card_style: Card style (executive, detailed, compact, board)
        """
        self.sections = sections
        self.briefing = briefing

        # Parse target language
        try:
            self._language = SupportedLanguage(target_language.lower())
        except ValueError:
            self._language = SupportedLanguage.DE

        # Parse layout mode
        try:
            self._layout_mode = LayoutMode(layout_mode.lower())
        except ValueError:
            self._layout_mode = LayoutMode.PDF

        # Parse card style
        try:
            self._card_style = CardStyle(card_style.lower())
        except ValueError:
            self._card_style = CardStyle.EXECUTIVE

        self._report = GovernanceLayoutReport()
        self._cards: List[PolicyCardLayout] = []
        self._matrices: List[GovernanceMatrixLayout] = []
        self._badges: List[ComplianceBadge] = []
        self._page_breaks: List[PageBreakPoint] = []
        self._risk_cues: List[RiskVisualCue] = []
        self._current_page = 1
        self._current_height = 0.0

        log.info(
            "[N4.3-Layout] Engine initialized: lang=%s, mode=%s, style=%s",
            self._language.value, self._layout_mode.value, self._card_style.value
        )

    def process(self) -> Tuple[SectionDict, GovernanceLayoutReport]:
        """
        Process sections through governance layout engine.

        Returns:
            Tuple of (processed_sections, report)
        """
        log.info("[N4.3-Layout] Processing started")

        # Step 1: Extract governance data from sections
        governance_data = self._extract_governance_data()

        # Step 2: Generate policy cards
        self._cards = self._generate_policy_cards(governance_data)
        self._report.cards_rendered = len(self._cards)

        # Step 3: Generate governance matrix
        self._matrices = self._generate_governance_matrices(governance_data)
        self._report.matrices_rendered = len(self._matrices)

        # Step 4: Generate compliance badges
        self._badges = self._generate_compliance_badges(governance_data)
        self._report.badges_positioned = len(self._badges)

        # Step 5: Generate risk visual cues
        self._risk_cues = self._generate_risk_cues(governance_data)

        # Step 6: Calculate page breaks
        self._page_breaks = self._calculate_page_breaks()
        self._report.page_breaks_added = len(self._page_breaks)
        self._report.total_pages = self._current_page

        # Step 7: Detect and heal overflow
        overflow_count = self._detect_and_heal_overflow()
        self._report.overflow_healed = overflow_count
        self._report.healed = overflow_count > 0

        # Step 8: Validate layout
        self._report.success = self._validate_layout()

        # Apply to sections
        result_sections = self._apply_layout_to_sections()

        log.info(
            "[N4.3-Layout] Complete: cards=%d, matrices=%d, pages=%d",
            self._report.cards_rendered,
            self._report.matrices_rendered,
            self._report.total_pages
        )

        return result_sections, self._report

    def _extract_governance_data(self) -> Dict[str, Any]:
        """Extract governance data from sections."""
        data: Dict[str, Any] = {
            "risk_class": "minimal",
            "maturity_level": "initial",
            "compliance_score": 0,
            "policy_cards": [],
            "governance_matrix": {},
            "controls": [],
            "gaps": [],
        }

        # Extract from sections metadata
        if "_governance_score" in self.sections:
            score_data = self.sections["_governance_score"]
            if isinstance(score_data, dict):
                data["compliance_score"] = score_data.get("overall_score", 0)
                data["maturity_level"] = score_data.get("maturity_level", "initial")
                data["gaps"] = score_data.get("gaps", [])

        if "_governance_matrix" in self.sections:
            matrix_data = self.sections["_governance_matrix"]
            if isinstance(matrix_data, dict):
                data["risk_class"] = matrix_data.get("risk_class", "minimal")
                data["governance_matrix"] = matrix_data

        if "_policy_cards" in self.sections:
            cards = self.sections["_policy_cards"]
            if isinstance(cards, list):
                data["policy_cards"] = cards

        # Extract from briefing
        data["risk_class"] = self.briefing.get("risk_class", data["risk_class"])

        return data

    def _generate_policy_cards(
        self,
        governance_data: Dict[str, Any],
    ) -> List[PolicyCardLayout]:
        """Generate policy card layouts."""
        cards: List[PolicyCardLayout] = []
        labels = LAYOUT_LABELS.get(self._language, LAYOUT_LABELS[SupportedLanguage.EN])

        # Get existing policy cards
        existing_cards = governance_data.get("policy_cards", [])

        for card_data in existing_cards:
            # Determine colors based on status
            status = card_data.get("status", "pending")
            if status == "compliant":
                colors = MATURITY_COLORS["optimizing"]
            elif status == "partial":
                colors = MATURITY_COLORS["developing"]
            else:
                colors = {"primary": "#dc3545", "secondary": "#f8d7da"}

            # Get card dimensions
            dimensions = CARD_DIMENSIONS.get(
                self._card_style,
                CARD_DIMENSIONS[CardStyle.EXECUTIVE]
            )

            card = PolicyCardLayout(
                card_id=card_data.get("card_id", f"CARD_{len(cards)+1:03d}"),
                title=card_data.get("title", ""),
                style=self._card_style,
                language=self._language,
                summary=card_data.get("summary", ""),
                status=status,
                score=card_data.get("score", 0),
                recommendations=card_data.get("recommendations", [])[:3],
                primary_color=colors.get("primary", "#007bff"),
                secondary_color=colors.get("secondary", "#cce5ff"),
                width=dimensions["width"],
                page=self._current_page,
            )

            cards.append(card)

        # If no cards exist, create default cards
        if not cards:
            cards = self._create_default_cards(governance_data, labels)

        return cards

    def _create_default_cards(
        self,
        governance_data: Dict[str, Any],
        labels: Dict[str, str],
    ) -> List[PolicyCardLayout]:
        """Create default policy cards."""
        cards: List[PolicyCardLayout] = []

        # Risk Classification Card
        risk_class = governance_data.get("risk_class", "minimal")
        risk_colors = RISK_COLORS.get(risk_class, RISK_COLORS["minimal"])

        risk_labels = {
            "high": labels["high_risk"],
            "limited": labels["limited_risk"],
            "minimal": labels["minimal_risk"],
        }

        cards.append(PolicyCardLayout(
            card_id="CARD_RISK",
            title=labels["risk_level"],
            style=self._card_style,
            language=self._language,
            summary=risk_labels.get(risk_class, labels["minimal_risk"]),
            status="compliant" if risk_class == "minimal" else "partial",
            score=100 - ({"high": 70, "limited": 40, "minimal": 20}.get(risk_class, 20)),
            primary_color=risk_colors["primary"],
            secondary_color=risk_colors["secondary"],
            text_color=risk_colors["text"],
            icon=risk_colors["icon"],
        ))

        # Maturity Card
        maturity = governance_data.get("maturity_level", "initial")
        maturity_colors = MATURITY_COLORS.get(maturity, MATURITY_COLORS["initial"])

        cards.append(PolicyCardLayout(
            card_id="CARD_MATURITY",
            title=labels["maturity"],
            style=self._card_style,
            language=self._language,
            summary=maturity.title(),
            status="compliant" if maturity in ("managed", "optimizing") else "partial",
            score=int(maturity_colors.get("score_range", "0-20").split("-")[1]),
            primary_color=maturity_colors["primary"],
            secondary_color=maturity_colors["secondary"],
        ))

        # Compliance Score Card
        score = governance_data.get("compliance_score", 0)

        if score >= 80:
            score_colors = MATURITY_COLORS["optimizing"]
            score_status = "compliant"
        elif score >= 60:
            score_colors = MATURITY_COLORS["managed"]
            score_status = "partial"
        else:
            score_colors = MATURITY_COLORS["initial"]
            score_status = "non_compliant"

        cards.append(PolicyCardLayout(
            card_id="CARD_COMPLIANCE",
            title=labels["compliance"],
            style=self._card_style,
            language=self._language,
            summary=f"{labels['score']}: {score}/100",
            status=score_status,
            score=score,
            primary_color=score_colors["primary"],
            secondary_color=score_colors["secondary"],
        ))

        return cards

    def _generate_governance_matrices(
        self,
        governance_data: Dict[str, Any],
    ) -> List[GovernanceMatrixLayout]:
        """Generate governance matrix layouts."""
        matrices: List[GovernanceMatrixLayout] = []
        labels = LAYOUT_LABELS.get(self._language, LAYOUT_LABELS[SupportedLanguage.EN])

        # Get matrix data
        matrix_data = governance_data.get("governance_matrix", {})

        if not matrix_data:
            return matrices

        # ISO 42001 Compliance Matrix
        iso_mapping = matrix_data.get("iso42001_mapping", {})

        if iso_mapping:
            iso_matrix = GovernanceMatrixLayout(
                matrix_id="MATRIX_ISO42001",
                title="ISO 42001 Compliance Matrix",
                language=self._language,
                headers=["Domain", labels["status"], labels["score"]],
                page=self._current_page,
            )

            row = 0
            for domain, domain_data in iso_mapping.items():
                if not isinstance(domain_data, dict):
                    continue

                compliance_level = domain_data.get("compliance_level", "non_compliant")
                status_label = labels.get(compliance_level, compliance_level)

                # Calculate domain score
                controls = domain_data.get("controls", [])
                implemented = sum(
                    1 for c in controls
                    if isinstance(c, dict) and c.get("status") == "partially_implemented"
                )
                domain_score = int((implemented / len(controls) * 100)) if controls else 0

                # Determine color
                if compliance_level == "compliant":
                    color = MATURITY_COLORS["optimizing"]["primary"]
                elif compliance_level == "partial":
                    color = MATURITY_COLORS["developing"]["primary"]
                else:
                    color = RISK_COLORS["high"]["primary"]

                # Add cells
                iso_matrix.cells.extend([
                    MatrixCell(row=row, col=0, content=domain.title(), cell_type="data"),
                    MatrixCell(row=row, col=1, content=status_label, status=compliance_level, color=color),
                    MatrixCell(row=row, col=2, content=f"{domain_score}%", score=domain_score),
                ])

                iso_matrix.row_labels.append(domain)
                row += 1

            iso_matrix.rows = row
            iso_matrix.cols = 3
            matrices.append(iso_matrix)

        # NIST AI RMF Matrix
        nist_mapping = matrix_data.get("nist_rmf_mapping", {})

        if nist_mapping:
            nist_matrix = GovernanceMatrixLayout(
                matrix_id="MATRIX_NIST_RMF",
                title="NIST AI RMF Status",
                language=self._language,
                headers=["Function", labels["maturity"], labels["status"]],
                page=self._current_page,
            )

            row = 0
            for function, function_data in nist_mapping.items():
                if not isinstance(function_data, dict):
                    continue

                maturity = function_data.get("maturity", "initial")
                maturity_colors = MATURITY_COLORS.get(maturity, MATURITY_COLORS["initial"])

                nist_matrix.cells.extend([
                    MatrixCell(row=row, col=0, content=function.upper(), cell_type="data"),
                    MatrixCell(row=row, col=1, content=maturity.title(), color=maturity_colors["primary"]),
                    MatrixCell(row=row, col=2, content=maturity_colors.get("score_range", "0-20")),
                ])

                row += 1

            nist_matrix.rows = row
            nist_matrix.cols = 3
            matrices.append(nist_matrix)

        return matrices

    def _generate_compliance_badges(
        self,
        governance_data: Dict[str, Any],
    ) -> List[ComplianceBadge]:
        """Generate compliance badges."""
        badges: List[ComplianceBadge] = []
        labels = LAYOUT_LABELS.get(self._language, LAYOUT_LABELS[SupportedLanguage.EN])

        # Risk Badge
        risk_class = governance_data.get("risk_class", "minimal")
        risk_colors = RISK_COLORS.get(risk_class, RISK_COLORS["minimal"])
        risk_labels = {
            "high": labels["high_risk"],
            "limited": labels["limited_risk"],
            "minimal": labels["minimal_risk"],
        }

        badges.append(ComplianceBadge(
            badge_id="BADGE_RISK",
            badge_type=BadgeType.RISK,
            label=labels["risk_level"],
            value=risk_labels.get(risk_class, labels["minimal_risk"]),
            color=risk_colors["primary"],
            icon=risk_colors["icon"],
            position="header",
            section="governance",
        ))

        # Compliance Score Badge
        score = governance_data.get("compliance_score", 0)

        if score >= 80:
            badge_color = MATURITY_COLORS["optimizing"]["primary"]
        elif score >= 60:
            badge_color = MATURITY_COLORS["managed"]["primary"]
        elif score >= 40:
            badge_color = MATURITY_COLORS["defined"]["primary"]
        else:
            badge_color = MATURITY_COLORS["initial"]["primary"]

        badges.append(ComplianceBadge(
            badge_id="BADGE_SCORE",
            badge_type=BadgeType.COMPLIANCE,
            label=labels["compliance"],
            value=f"{score}/100",
            color=badge_color,
            icon="chart-bar",
            position="top-right",
            section="executive_summary",
        ))

        # Framework Badges
        frameworks = ["EU AI Act", "ISO 42001", "NIST AI RMF"]
        for i, framework in enumerate(frameworks):
            badges.append(ComplianceBadge(
                badge_id=f"BADGE_FW_{i+1}",
                badge_type=BadgeType.FRAMEWORK,
                label=labels["framework"],
                value=framework,
                color="#007bff",
                icon="check-circle",
                position="inline",
                section="governance",
                size="small",
            ))

        # Warning Badge (if high risk)
        if risk_class == "high":
            badges.append(ComplianceBadge(
                badge_id="BADGE_WARNING",
                badge_type=BadgeType.WARNING,
                label="",
                value=labels["high_risk"],
                color=RISK_COLORS["high"]["primary"],
                icon="exclamation-triangle",
                position="header",
                section="risks",
                size="large",
            ))

        return badges

    def _generate_risk_cues(
        self,
        governance_data: Dict[str, Any],
    ) -> List[RiskVisualCue]:
        """Generate risk visual cues."""
        cues: List[RiskVisualCue] = []
        labels = LAYOUT_LABELS.get(self._language, LAYOUT_LABELS[SupportedLanguage.EN])

        risk_class = governance_data.get("risk_class", "minimal")
        risk_colors = RISK_COLORS.get(risk_class, RISK_COLORS["minimal"])

        risk_labels = {
            "high": labels["high_risk"],
            "limited": labels["limited_risk"],
            "minimal": labels["minimal_risk"],
            "unacceptable": "Unacceptable",
        }

        risk_descriptions = {
            "high": {
                SupportedLanguage.DE: "Strikte Anforderungen gemäß EU AI Act",
                SupportedLanguage.EN: "Strict requirements per EU AI Act",
            },
            "limited": {
                SupportedLanguage.DE: "Transparenzpflichten erforderlich",
                SupportedLanguage.EN: "Transparency obligations required",
            },
            "minimal": {
                SupportedLanguage.DE: "Keine verbindlichen Anforderungen",
                SupportedLanguage.EN: "No mandatory requirements",
            },
        }

        desc = risk_descriptions.get(risk_class, {})
        description = desc.get(self._language, desc.get(SupportedLanguage.EN, ""))

        # Traffic light style cue
        cues.append(RiskVisualCue(
            cue_id="CUE_TRAFFIC_LIGHT",
            risk_class=risk_class,
            style=RiskVisualStyle.TRAFFIC_LIGHT,
            language=self._language,
            label=risk_labels.get(risk_class, risk_class),
            color=risk_colors["primary"],
            icon=risk_colors["icon"],
            description=description,
            html_class=f"risk-{risk_class}",
            css_styles={
                "background-color": risk_colors["secondary"],
                "border-color": risk_colors["primary"],
                "color": risk_colors["text"],
            },
        ))

        # Badge style cue
        cues.append(RiskVisualCue(
            cue_id="CUE_BADGE",
            risk_class=risk_class,
            style=RiskVisualStyle.BADGE,
            language=self._language,
            label=risk_labels.get(risk_class, risk_class),
            color=risk_colors["primary"],
            icon=risk_colors["icon"],
            css_styles={
                "display": "inline-block",
                "padding": "4px 12px",
                "border-radius": "16px",
                "background-color": risk_colors["primary"],
                "color": "#ffffff",
                "font-weight": "bold",
            },
        ))

        return cues

    def _calculate_page_breaks(self) -> List[PageBreakPoint]:
        """Calculate page break points."""
        breaks: List[PageBreakPoint] = []

        config = PAGE_BREAK_CONFIG.get(
            self._layout_mode.value,
            PAGE_BREAK_CONFIG["pdf"]
        )

        if self._layout_mode == LayoutMode.PDF:
            max_height = config["max_height_mm"]
            current_height = config["header_height_mm"]

            # Track content height
            content_items = []

            # Add cards
            for card in self._cards:
                content_items.append({
                    "id": card.card_id,
                    "type": "card",
                    "height": config["card_height_mm"],
                })

            # Add matrices
            for matrix in self._matrices:
                matrix_height = (
                    config["matrix_row_height_mm"] * (matrix.rows + 1) +
                    config["section_gap_mm"]
                )
                content_items.append({
                    "id": matrix.matrix_id,
                    "type": "matrix",
                    "height": matrix_height,
                })

            # Calculate breaks
            for item in content_items:
                if current_height + item["height"] > max_height:
                    # Need page break
                    self._current_page += 1
                    breaks.append(PageBreakPoint(
                        break_id=f"BREAK_{len(breaks)+1:03d}",
                        after_section=item["id"],
                        page_number=self._current_page,
                        reason="Content overflow",
                    ))
                    current_height = config["header_height_mm"] + item["height"]
                else:
                    current_height += item["height"]

            # Update item pages
            page = 1
            current_height = config["header_height_mm"]

            for item in content_items:
                if current_height + item["height"] > max_height:
                    page += 1
                    current_height = config["header_height_mm"]

                # Update card/matrix page
                for card in self._cards:
                    if card.card_id == item["id"]:
                        card.page = page
                for matrix in self._matrices:
                    if matrix.matrix_id == item["id"]:
                        matrix.page = page

                current_height += item["height"]

        return breaks

    def _detect_and_heal_overflow(self) -> int:
        """Detect and heal content overflow."""
        healed_count = 0

        # Check card content overflow
        for card in self._cards:
            if len(card.summary) > 200:
                # Truncate summary
                card.summary = card.summary[:197] + "..."
                healed_count += 1
                self._report.warnings.append(
                    f"Card {card.card_id} summary truncated"
                )

            if len(card.recommendations) > 3:
                # Limit recommendations
                card.recommendations = card.recommendations[:3]
                healed_count += 1
                self._report.warnings.append(
                    f"Card {card.card_id} recommendations limited"
                )

        # Check matrix overflow
        for matrix in self._matrices:
            if matrix.rows > 10:
                # Matrix too large, need to paginate
                self._report.warnings.append(
                    f"Matrix {matrix.matrix_id} may need pagination"
                )

        return healed_count

    def _validate_layout(self) -> bool:
        """Validate layout configuration."""
        validations = {
            "has_cards": len(self._cards) > 0 or len(self._matrices) > 0,
            "valid_pages": self._current_page >= 1,
            "no_critical_issues": len([i for i in self._report.issues if "critical" in i.lower()]) == 0,
        }

        return all(validations.values())

    def _apply_layout_to_sections(self) -> SectionDict:
        """Apply layout data to sections."""
        result_sections = dict(self.sections)

        # Add policy card layouts
        result_sections["_policy_card_layouts"] = [
            card.to_dict() for card in self._cards
        ]

        # Add matrix layouts
        result_sections["_governance_matrix_layouts"] = [
            matrix.to_dict() for matrix in self._matrices
        ]

        # Add badges
        result_sections["_compliance_badges"] = [
            badge.to_dict() for badge in self._badges
        ]

        # Add page breaks
        result_sections["_page_breaks"] = [
            pb.to_dict() for pb in self._page_breaks
        ]

        # Add risk visual cues
        result_sections["_risk_visual_cues"] = [
            cue.to_dict() for cue in self._risk_cues
        ]

        # Add layout metadata
        result_sections["_layout_validated"] = self._report.success
        result_sections["_layout_report"] = self._report.to_dict()
        result_sections["_layout_healed"] = self._report.healed
        result_sections["_total_pages"] = self._report.total_pages

        return result_sections

    def get_cards(self) -> List[PolicyCardLayout]:
        """Get policy card layouts."""
        return self._cards

    def get_matrices(self) -> List[GovernanceMatrixLayout]:
        """Get governance matrix layouts."""
        return self._matrices

    def get_badges(self) -> List[ComplianceBadge]:
        """Get compliance badges."""
        return self._badges

    def get_risk_cues(self) -> List[RiskVisualCue]:
        """Get risk visual cues."""
        return self._risk_cues


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def render_policy_card(
    card: Dict[str, Any],
    style: str = "executive",
    language: str = "de",
    layout_mode: str = "html",
) -> str:
    """
    Render a policy card to HTML/Markdown.

    Args:
        card: Policy card data
        style: Card style
        language: Language code
        layout_mode: Output format

    Returns:
        Rendered card string
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    labels = LAYOUT_LABELS.get(lang, LAYOUT_LABELS[SupportedLanguage.EN])

    if layout_mode == "html":
        return _render_card_html(card, style, labels)
    else:
        return _render_card_markdown(card, labels)


def _render_card_html(
    card: Dict[str, Any],
    style: str,
    labels: Dict[str, str],
) -> str:
    """Render card as HTML."""
    status = card.get("status", "pending")
    score = card.get("score", 0)

    status_class = {
        "compliant": "success",
        "partial": "warning",
        "non_compliant": "danger",
    }.get(status, "secondary")

    html = f"""
    <div class="policy-card card-{style}" style="
        background-color: {card.get('secondary_color', '#f8f9fa')};
        border-left: 4px solid {card.get('primary_color', '#007bff')};
        padding: 16px 20px;
        margin-bottom: 16px;
        border-radius: 8px;
    ">
        <div class="card-header">
            <h4 style="color: {card.get('primary_color', '#007bff')}; margin: 0;">
                {card.get('title', '')}
            </h4>
            <span class="badge badge-{status_class}">{labels.get(status, status)}</span>
        </div>
        <div class="card-body">
            <p>{card.get('summary', '')}</p>
            <div class="score">
                <strong>{labels['score']}:</strong> {score}/100
            </div>
        </div>
    </div>
    """
    return html.strip()


def _render_card_markdown(card: Dict[str, Any], labels: Dict[str, str]) -> str:
    """Render card as Markdown."""
    status = card.get("status", "pending")
    score = card.get("score", 0)

    md = f"""
### {card.get('title', '')}

**{labels['status']}:** {labels.get(status, status)}
**{labels['score']}:** {score}/100

{card.get('summary', '')}
"""
    return md.strip()


def render_governance_matrix(
    matrix: Dict[str, Any],
    format: str = "html",
    language: str = "de",
) -> str:
    """
    Render governance matrix to HTML/Markdown.

    Args:
        matrix: Matrix data
        format: Output format
        language: Language code

    Returns:
        Rendered matrix string
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    labels = LAYOUT_LABELS.get(lang, LAYOUT_LABELS[SupportedLanguage.EN])

    if format == "html":
        return _render_matrix_html(matrix, labels)
    else:
        return _render_matrix_markdown(matrix, labels)


def _render_matrix_html(matrix: Dict[str, Any], labels: Dict[str, str]) -> str:
    """Render matrix as HTML table."""
    headers = matrix.get("headers", [])
    cells = matrix.get("cells", [])
    rows = matrix.get("rows", 0)

    html = f"""
    <table class="governance-matrix" style="width: 100%; border-collapse: collapse;">
        <caption style="font-weight: bold; margin-bottom: 8px;">
            {matrix.get('title', '')}
        </caption>
        <thead>
            <tr>
    """

    for header in headers:
        html += f'<th style="border: 1px solid #dee2e6; padding: 8px; background: #f8f9fa;">{header}</th>'

    html += "</tr></thead><tbody>"

    # Group cells by row
    for row_idx in range(rows):
        html += "<tr>"
        row_cells = [c for c in cells if c.get("row") == row_idx]
        row_cells.sort(key=lambda x: x.get("col", 0))

        for cell in row_cells:
            color = cell.get("color", "")
            style = f'border: 1px solid #dee2e6; padding: 8px;'
            if color:
                style += f' background-color: {color}; color: white;'

            html += f'<td style="{style}">{cell.get("content", "")}</td>'

        html += "</tr>"

    html += "</tbody></table>"
    return html


def _render_matrix_markdown(matrix: Dict[str, Any], labels: Dict[str, str]) -> str:
    """Render matrix as Markdown table."""
    headers = matrix.get("headers", [])
    cells = matrix.get("cells", [])
    rows = matrix.get("rows", 0)

    md = f"### {matrix.get('title', '')}\n\n"
    md += "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for row_idx in range(rows):
        row_cells = [c for c in cells if c.get("row") == row_idx]
        row_cells.sort(key=lambda x: x.get("col", 0))
        row_content = [c.get("content", "") for c in row_cells]
        md += "| " + " | ".join(row_content) + " |\n"

    return md


def position_compliance_badges(
    sections: SectionDict,
    badges: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Position compliance badges in sections.

    Args:
        sections: Section dictionary
        badges: List of badge configurations

    Returns:
        Dictionary mapping sections to badges
    """
    positioned: Dict[str, List[Dict[str, Any]]] = {}

    for badge in badges:
        section = badge.get("section", "")
        if section:
            if section not in positioned:
                positioned[section] = []
            positioned[section].append(badge)

    return positioned


def calculate_page_breaks(
    sections: SectionDict,
    max_height: float,
    layout_mode: str = "pdf",
) -> List[Dict[str, Any]]:
    """
    Calculate page break points.

    Args:
        sections: Section dictionary
        max_height: Maximum page height
        layout_mode: Layout mode

    Returns:
        List of page break configurations
    """
    engine = GovernanceLayoutEngineV1(
        sections=sections,
        briefing={},
        layout_mode=layout_mode,
    )

    engine._calculate_page_breaks()
    return [pb.to_dict() for pb in engine._page_breaks]


def generate_risk_visual_cues(
    risk_class: str,
    style: str = "traffic_light",
    language: str = "de",
) -> Dict[str, Any]:
    """
    Generate risk visual cues.

    Args:
        risk_class: Risk classification
        style: Visual style
        language: Language code

    Returns:
        Visual cue configuration
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    try:
        visual_style = RiskVisualStyle(style.lower())
    except ValueError:
        visual_style = RiskVisualStyle.TRAFFIC_LIGHT

    labels = LAYOUT_LABELS.get(lang, LAYOUT_LABELS[SupportedLanguage.EN])
    colors = RISK_COLORS.get(risk_class.lower(), RISK_COLORS["minimal"])

    risk_labels = {
        "high": labels["high_risk"],
        "limited": labels["limited_risk"],
        "minimal": labels["minimal_risk"],
    }

    return {
        "risk_class": risk_class,
        "style": visual_style.value,
        "label": risk_labels.get(risk_class.lower(), risk_class),
        "color": colors["primary"],
        "secondary_color": colors["secondary"],
        "text_color": colors["text"],
        "icon": colors["icon"],
    }


def get_card_template(
    style: str = "executive",
    language: str = "de",
) -> Dict[str, Any]:
    """
    Get policy card template.

    Args:
        style: Card style
        language: Language code

    Returns:
        Card template configuration
    """
    try:
        card_style = CardStyle(style.lower())
    except ValueError:
        card_style = CardStyle.EXECUTIVE

    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    dimensions = CARD_DIMENSIONS.get(card_style, CARD_DIMENSIONS[CardStyle.EXECUTIVE])
    labels = LAYOUT_LABELS.get(lang, LAYOUT_LABELS[SupportedLanguage.EN])

    return {
        "style": card_style.value,
        "language": lang.value,
        "dimensions": dimensions,
        "labels": labels,
    }


def validate_layout(
    sections: SectionDict,
    layout_mode: str = "pdf",
) -> Tuple[bool, List[str]]:
    """
    Validate layout configuration.

    Args:
        sections: Section dictionary
        layout_mode: Layout mode

    Returns:
        Tuple of (is_valid, validation_messages)
    """
    messages: List[str] = []
    is_valid = True

    # Check for layout data
    if "_policy_card_layouts" not in sections:
        messages.append("No policy card layouts found")

    if "_governance_matrix_layouts" not in sections:
        messages.append("No governance matrix layouts found")

    # Check for excessive pages
    total_pages = sections.get("_total_pages", 1)
    if total_pages > 20:
        messages.append(f"Warning: Document has {total_pages} pages")
        is_valid = False

    return is_valid, messages
