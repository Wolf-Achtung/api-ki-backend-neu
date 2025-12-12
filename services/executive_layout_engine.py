"""
Executive Layout Engine - N4.1 PLATIN+++ Executive Experience Layer.

PDF Experience Upgrade v3 providing:
- Precise page-break optimization for sections, tables, KPIs, roadmap blocks
- Executive White Space Management
- Unified card layouts (Tools, Funding, KPIs, Risks)
- Optimized font scale for C-Suite readability

Board-Ready. Investment-Ready. C-Level-Perfect.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TypedDict

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPE DEFINITIONS
# =============================================================================


class ElementType(Enum):
    """Types of layout elements."""
    SECTION_HEAD = "section_head"
    SUBSECTION_HEAD = "subsection_head"
    TABLE = "table"
    KPI_VISUAL = "kpi_visual"
    ROADMAP_BLOCK = "roadmap_block"
    CARD = "card"
    PARAGRAPH = "paragraph"
    BULLET_LIST = "bullet_list"
    CHART = "chart"
    EXECUTIVE_SUMMARY = "executive_summary"


class CardType(Enum):
    """Types of card layouts."""
    TOOL_CARD = "tool_card"
    FUNDING_CARD = "funding_card"
    KPI_CARD = "kpi_card"
    RISK_CARD = "risk_card"
    ACTION_CARD = "action_card"


class PageBreakRule(Enum):
    """Page break rules."""
    ALWAYS_BEFORE = "always_before"
    NEVER_BREAK = "never_break"
    PREFER_BEFORE = "prefer_before"
    ALLOW_BREAK = "allow_break"
    KEEP_WITH_NEXT = "keep_with_next"


class LayoutElement(TypedDict):
    """Single layout element."""
    id: str
    element_type: str
    content: Any
    height_estimate: float
    page_break_rule: str
    margin_before: float
    margin_after: float


class PageLayout(TypedDict):
    """Single page layout."""
    page_number: int
    elements: List[str]
    fill_percentage: float
    white_space_score: float


class LayoutResult(TypedDict):
    """Complete layout result."""
    total_pages: int
    pages: List[PageLayout]
    elements: Dict[str, LayoutElement]
    layout_score: float
    white_space_score: float


class CardLayout(TypedDict):
    """Card layout specification."""
    card_type: str
    title: str
    content_blocks: List[Dict[str, Any]]
    accent_color: str
    icon: str


# =============================================================================
# CONFIGURATION
# =============================================================================


LAYOUT_CONFIG: Dict[str, Any] = {
    # Page dimensions (A4 in points, 72 dpi)
    "page_width": 595,
    "page_height": 842,
    "margin_top": 72,
    "margin_bottom": 72,
    "margin_left": 56,
    "margin_right": 56,
    # Content area
    "content_width": 483,  # page_width - margin_left - margin_right
    "content_height": 698,  # page_height - margin_top - margin_bottom
    # Element spacing
    "section_head_margin_before": 36,
    "section_head_margin_after": 18,
    "subsection_margin_before": 24,
    "subsection_margin_after": 12,
    "paragraph_spacing": 12,
    "table_margin": 18,
    "card_margin": 16,
    # White space targets
    "min_white_space_ratio": 0.15,
    "max_white_space_ratio": 0.35,
    "optimal_fill_percentage": 0.80,
    # Orphan/Widow control
    "min_orphan_lines": 3,
    "min_widow_lines": 3,
}


# Font scaling for C-Suite readability
FONT_SCALE: Dict[str, Dict[str, Any]] = {
    "headline": {
        "base_size": 18,
        "scale_factor": 1.06,  # +6%
        "effective_size": 19.08,
        "line_height": 1.3,
        "weight": "bold",
    },
    "subhead": {
        "base_size": 14,
        "scale_factor": 1.04,  # +4%
        "effective_size": 14.56,
        "line_height": 1.35,
        "weight": "semibold",
    },
    "body": {
        "base_size": 11,
        "scale_factor": 0.97,  # -3%
        "effective_size": 10.67,
        "line_height": 1.5,
        "weight": "normal",
    },
    "caption": {
        "base_size": 9,
        "scale_factor": 1.0,
        "effective_size": 9,
        "line_height": 1.4,
        "weight": "normal",
    },
    "kpi_large": {
        "base_size": 32,
        "scale_factor": 1.0,
        "effective_size": 32,
        "line_height": 1.2,
        "weight": "bold",
    },
}


# Page break rules by element type
PAGE_BREAK_RULES: Dict[ElementType, PageBreakRule] = {
    ElementType.SECTION_HEAD: PageBreakRule.ALWAYS_BEFORE,
    ElementType.SUBSECTION_HEAD: PageBreakRule.PREFER_BEFORE,
    ElementType.TABLE: PageBreakRule.NEVER_BREAK,
    ElementType.KPI_VISUAL: PageBreakRule.NEVER_BREAK,
    ElementType.ROADMAP_BLOCK: PageBreakRule.PREFER_BEFORE,
    ElementType.CARD: PageBreakRule.NEVER_BREAK,
    ElementType.PARAGRAPH: PageBreakRule.ALLOW_BREAK,
    ElementType.BULLET_LIST: PageBreakRule.KEEP_WITH_NEXT,
    ElementType.CHART: PageBreakRule.NEVER_BREAK,
    ElementType.EXECUTIVE_SUMMARY: PageBreakRule.ALWAYS_BEFORE,
}


# Card style specifications
CARD_STYLES: Dict[CardType, Dict[str, Any]] = {
    CardType.TOOL_CARD: {
        "accent_color": "#2563EB",
        "icon": "tool",
        "min_height": 120,
        "padding": 16,
    },
    CardType.FUNDING_CARD: {
        "accent_color": "#059669",
        "icon": "currency",
        "min_height": 100,
        "padding": 16,
    },
    CardType.KPI_CARD: {
        "accent_color": "#7C3AED",
        "icon": "chart",
        "min_height": 80,
        "padding": 12,
    },
    CardType.RISK_CARD: {
        "accent_color": "#DC2626",
        "icon": "warning",
        "min_height": 100,
        "padding": 16,
    },
    CardType.ACTION_CARD: {
        "accent_color": "#F59E0B",
        "icon": "action",
        "min_height": 90,
        "padding": 14,
    },
}


# =============================================================================
# HEIGHT ESTIMATOR
# =============================================================================


class HeightEstimator:
    """
    Estimates height of layout elements.

    Uses font metrics and content analysis for accurate estimation.
    """

    def __init__(self) -> None:
        self._chars_per_line = 85  # Average for body text

    def estimate(
        self,
        element_type: ElementType,
        content: Any,
    ) -> float:
        """
        Estimate element height in points.

        Args:
            element_type: Type of element
            content: Element content

        Returns:
            Estimated height in points
        """
        if element_type == ElementType.SECTION_HEAD:
            return self._estimate_heading(content, "headline")

        if element_type == ElementType.SUBSECTION_HEAD:
            return self._estimate_heading(content, "subhead")

        if element_type == ElementType.TABLE:
            return self._estimate_table(content)

        if element_type == ElementType.KPI_VISUAL:
            return self._estimate_kpi_visual(content)

        if element_type == ElementType.ROADMAP_BLOCK:
            return self._estimate_roadmap(content)

        if element_type == ElementType.CARD:
            return self._estimate_card(content)

        if element_type == ElementType.PARAGRAPH:
            return self._estimate_paragraph(content)

        if element_type == ElementType.BULLET_LIST:
            return self._estimate_bullet_list(content)

        if element_type == ElementType.CHART:
            return self._estimate_chart(content)

        if element_type == ElementType.EXECUTIVE_SUMMARY:
            return self._estimate_executive_summary(content)

        return 100  # Default fallback

    def _estimate_heading(self, content: str, style: str) -> float:
        """Estimate heading height."""
        font = FONT_SCALE[style]
        line_height = font["effective_size"] * font["line_height"]

        # Count lines needed
        lines = len(content) / 50 + 1  # Assume shorter line length for headings

        return line_height * lines

    def _estimate_paragraph(self, content: str) -> float:
        """Estimate paragraph height."""
        font = FONT_SCALE["body"]
        line_height = font["effective_size"] * font["line_height"]

        # Estimate lines
        lines = len(content) / self._chars_per_line + 1

        return line_height * lines + LAYOUT_CONFIG["paragraph_spacing"]

    def _estimate_table(self, content: Dict[str, Any]) -> float:
        """Estimate table height."""
        rows = content.get("rows", 5)
        header_height = 30
        row_height = 24

        return header_height + (rows * row_height) + LAYOUT_CONFIG["table_margin"] * 2

    def _estimate_kpi_visual(self, content: Dict[str, Any]) -> float:
        """Estimate KPI visual height."""
        kpi_count = content.get("count", 3)

        # KPIs arranged in row of 3
        rows = (kpi_count + 2) // 3
        kpi_height = 100  # Per row

        return rows * kpi_height

    def _estimate_roadmap(self, content: Dict[str, Any]) -> float:
        """Estimate roadmap block height."""
        phases = content.get("phases", 4)
        phase_height = 80

        return phases * phase_height + 40  # Header

    def _estimate_card(self, content: Dict[str, Any]) -> float:
        """Estimate card height."""
        card_type = CardType(content.get("type", "kpi_card"))
        style = CARD_STYLES.get(card_type, CARD_STYLES[CardType.KPI_CARD])

        content_lines = content.get("content_lines", 3)
        line_height = 20

        return max(
            style["min_height"],
            style["padding"] * 2 + 30 + content_lines * line_height,
        )

    def _estimate_bullet_list(self, content: List[str]) -> float:
        """Estimate bullet list height."""
        items = len(content) if isinstance(content, list) else 5
        item_height = 24

        return items * item_height

    def _estimate_chart(self, content: Dict[str, Any]) -> float:
        """Estimate chart height."""
        return content.get("height", 200)

    def _estimate_executive_summary(self, content: Dict[str, Any]) -> float:
        """Estimate executive summary height."""
        # Full page minimum
        return LAYOUT_CONFIG["content_height"] * 0.9


# =============================================================================
# PAGE BREAK OPTIMIZER
# =============================================================================


class PageBreakOptimizer:
    """
    Optimizes page breaks for visual flow.

    Ensures:
    - Section heads don't orphan at page bottom
    - Tables don't split across pages
    - KPI visuals stay together
    - Roadmap blocks maintain integrity
    """

    def __init__(self) -> None:
        self._content_height = LAYOUT_CONFIG["content_height"]

    def optimize_breaks(
        self,
        elements: List[LayoutElement],
    ) -> List[PageLayout]:
        """
        Optimize page breaks for element sequence.

        Args:
            elements: List of layout elements

        Returns:
            List of PageLayout with optimized breaks
        """
        pages: List[PageLayout] = []
        current_page: List[str] = []
        current_height = 0.0
        page_number = 1

        for element in elements:
            element_height = element["height_estimate"]
            rule = PageBreakRule(element["page_break_rule"])
            margin_before = element["margin_before"]
            margin_after = element["margin_after"]
            total_height = margin_before + element_height + margin_after

            # Check if page break needed
            needs_break = self._needs_page_break(
                rule,
                current_height,
                total_height,
            )

            if needs_break and current_page:
                # Finalize current page
                fill_pct = current_height / self._content_height
                pages.append(PageLayout(
                    page_number=page_number,
                    elements=current_page,
                    fill_percentage=fill_pct,
                    white_space_score=self._calculate_white_space_score(fill_pct),
                ))
                page_number += 1
                current_page = []
                current_height = 0.0

            # Add element to current page
            current_page.append(element["id"])
            current_height += total_height

        # Finalize last page
        if current_page:
            fill_pct = current_height / self._content_height
            pages.append(PageLayout(
                page_number=page_number,
                elements=current_page,
                fill_percentage=fill_pct,
                white_space_score=self._calculate_white_space_score(fill_pct),
            ))

        return pages

    def _needs_page_break(
        self,
        rule: PageBreakRule,
        current_height: float,
        element_height: float,
    ) -> bool:
        """Determine if page break is needed."""
        remaining = self._content_height - current_height

        if rule == PageBreakRule.ALWAYS_BEFORE:
            return current_height > 0

        if rule == PageBreakRule.NEVER_BREAK:
            # Break if element won't fit
            return remaining < element_height

        if rule == PageBreakRule.PREFER_BEFORE:
            # Break if less than 30% page remaining
            return remaining < self._content_height * 0.3

        if rule == PageBreakRule.KEEP_WITH_NEXT:
            # Break if less than 20% remaining (need room for next element)
            return remaining < self._content_height * 0.2

        # ALLOW_BREAK - only break if element won't fit
        return remaining < element_height

    def _calculate_white_space_score(self, fill_percentage: float) -> float:
        """Calculate white space quality score."""
        white_space = 1.0 - fill_percentage
        min_ws = LAYOUT_CONFIG["min_white_space_ratio"]
        max_ws = LAYOUT_CONFIG["max_white_space_ratio"]

        if min_ws <= white_space <= max_ws:
            return 1.0

        if white_space < min_ws:
            return white_space / min_ws

        return max(0, 1.0 - (white_space - max_ws))


# =============================================================================
# WHITE SPACE MANAGER
# =============================================================================


class WhiteSpaceManager:
    """
    Manages executive white space for visual clarity.

    Ensures consistent, professional spacing throughout the document.
    """

    def __init__(self) -> None:
        self._min_ratio = LAYOUT_CONFIG["min_white_space_ratio"]
        self._max_ratio = LAYOUT_CONFIG["max_white_space_ratio"]

    def adjust_spacing(
        self,
        elements: List[LayoutElement],
        target_fill: float = 0.80,
    ) -> List[LayoutElement]:
        """
        Adjust element spacing for optimal white space.

        Args:
            elements: List of layout elements
            target_fill: Target page fill percentage

        Returns:
            Elements with adjusted margins
        """
        total_content_height = sum(e["height_estimate"] for e in elements)
        total_margin_height = sum(
            e["margin_before"] + e["margin_after"]
            for e in elements
        )

        current_total = total_content_height + total_margin_height
        target_total = LAYOUT_CONFIG["content_height"] * target_fill

        if current_total == 0:
            return elements

        # Calculate adjustment factor
        adjustment = target_total / current_total

        # Apply adjustment to margins
        adjusted: List[LayoutElement] = []
        for element in elements:
            adjusted_element = LayoutElement(
                id=element["id"],
                element_type=element["element_type"],
                content=element["content"],
                height_estimate=element["height_estimate"],
                page_break_rule=element["page_break_rule"],
                margin_before=element["margin_before"] * adjustment,
                margin_after=element["margin_after"] * adjustment,
            )
            adjusted.append(adjusted_element)

        return adjusted

    def calculate_overall_score(
        self,
        pages: List[PageLayout],
    ) -> float:
        """Calculate overall white space quality score."""
        if not pages:
            return 0.0

        return sum(p["white_space_score"] for p in pages) / len(pages)


# =============================================================================
# CARD LAYOUT BUILDER
# =============================================================================


class CardLayoutBuilder:
    """
    Builds unified card layouts for consistent visual presentation.

    Supports: Tools, Funding, KPIs, Risks, Actions
    """

    def build_tool_card(
        self,
        tool_name: str,
        description: str,
        category: str,
        score: Optional[float] = None,
    ) -> CardLayout:
        """Build a tool card."""
        style = CARD_STYLES[CardType.TOOL_CARD]
        content_blocks = [
            {"type": "title", "content": tool_name},
            {"type": "category", "content": category},
            {"type": "description", "content": description},
        ]
        if score is not None:
            content_blocks.append({"type": "score", "content": f"{score:.0f}/100"})

        return CardLayout(
            card_type=CardType.TOOL_CARD.value,
            title=tool_name,
            content_blocks=content_blocks,
            accent_color=style["accent_color"],
            icon=style["icon"],
        )

    def build_funding_card(
        self,
        program_name: str,
        amount: str,
        deadline: str,
        eligibility: str,
    ) -> CardLayout:
        """Build a funding card."""
        style = CARD_STYLES[CardType.FUNDING_CARD]
        return CardLayout(
            card_type=CardType.FUNDING_CARD.value,
            title=program_name,
            content_blocks=[
                {"type": "amount", "content": amount},
                {"type": "deadline", "content": deadline},
                {"type": "eligibility", "content": eligibility},
            ],
            accent_color=style["accent_color"],
            icon=style["icon"],
        )

    def build_kpi_card(
        self,
        kpi_name: str,
        value: str,
        trend: str,
        benchmark: Optional[str] = None,
    ) -> CardLayout:
        """Build a KPI card."""
        style = CARD_STYLES[CardType.KPI_CARD]
        content_blocks = [
            {"type": "value", "content": value},
            {"type": "trend", "content": trend},
        ]
        if benchmark:
            content_blocks.append({"type": "benchmark", "content": benchmark})

        return CardLayout(
            card_type=CardType.KPI_CARD.value,
            title=kpi_name,
            content_blocks=content_blocks,
            accent_color=style["accent_color"],
            icon=style["icon"],
        )

    def build_risk_card(
        self,
        risk_name: str,
        severity: str,
        probability: str,
        mitigation: str,
    ) -> CardLayout:
        """Build a risk card."""
        style = CARD_STYLES[CardType.RISK_CARD]
        return CardLayout(
            card_type=CardType.RISK_CARD.value,
            title=risk_name,
            content_blocks=[
                {"type": "severity", "content": severity},
                {"type": "probability", "content": probability},
                {"type": "mitigation", "content": mitigation},
            ],
            accent_color=style["accent_color"],
            icon=style["icon"],
        )

    def build_action_card(
        self,
        action_name: str,
        priority: str,
        timeline: str,
        owner: str,
    ) -> CardLayout:
        """Build an action card."""
        style = CARD_STYLES[CardType.ACTION_CARD]
        return CardLayout(
            card_type=CardType.ACTION_CARD.value,
            title=action_name,
            content_blocks=[
                {"type": "priority", "content": priority},
                {"type": "timeline", "content": timeline},
                {"type": "owner", "content": owner},
            ],
            accent_color=style["accent_color"],
            icon=style["icon"],
        )


# =============================================================================
# MAIN ENGINE CLASS
# =============================================================================


class ExecutiveLayoutEngine:
    """
    Main engine for executive layout optimization.

    Orchestrates:
    - Page break optimization
    - White space management
    - Card layout generation
    - Font scaling
    """

    def __init__(self) -> None:
        self._height_estimator = HeightEstimator()
        self._page_optimizer = PageBreakOptimizer()
        self._white_space_manager = WhiteSpaceManager()
        self._card_builder = CardLayoutBuilder()
        self._element_counter = 0

    def process_layout(
        self,
        content_elements: List[Dict[str, Any]],
    ) -> LayoutResult:
        """
        Process content elements into optimized layout.

        Args:
            content_elements: Raw content elements

        Returns:
            LayoutResult with optimized page layout
        """
        log.info(
            "[N4.1-Layout] Processing %d content elements...",
            len(content_elements),
        )

        # Convert to layout elements
        layout_elements = self._convert_elements(content_elements)

        # Build element map
        element_map = {e["id"]: e for e in layout_elements}

        # Optimize page breaks
        pages = self._page_optimizer.optimize_breaks(layout_elements)

        # Calculate scores
        layout_score = self._calculate_layout_score(pages)
        white_space_score = self._white_space_manager.calculate_overall_score(pages)

        log.info(
            "[N4.1-Layout] Layout complete: %d pages, layout score %.2f, "
            "white space score %.2f",
            len(pages),
            layout_score,
            white_space_score,
        )

        return LayoutResult(
            total_pages=len(pages),
            pages=pages,
            elements=element_map,
            layout_score=layout_score,
            white_space_score=white_space_score,
        )

    def create_element(
        self,
        element_type: ElementType,
        content: Any,
    ) -> LayoutElement:
        """
        Create a layout element.

        Args:
            element_type: Type of element
            content: Element content

        Returns:
            LayoutElement structure
        """
        self._element_counter += 1
        element_id = f"elem_{self._element_counter:04d}"

        height = self._height_estimator.estimate(element_type, content)
        rule = PAGE_BREAK_RULES.get(element_type, PageBreakRule.ALLOW_BREAK)

        margins = self._get_margins(element_type)

        return LayoutElement(
            id=element_id,
            element_type=element_type.value,
            content=content,
            height_estimate=height,
            page_break_rule=rule.value,
            margin_before=margins[0],
            margin_after=margins[1],
        )

    def create_card(
        self,
        card_type: CardType,
        **kwargs: Any,
    ) -> CardLayout:
        """
        Create a card layout.

        Args:
            card_type: Type of card
            **kwargs: Card-specific parameters

        Returns:
            CardLayout structure
        """
        if card_type == CardType.TOOL_CARD:
            return self._card_builder.build_tool_card(
                kwargs.get("tool_name", ""),
                kwargs.get("description", ""),
                kwargs.get("category", ""),
                kwargs.get("score"),
            )

        if card_type == CardType.FUNDING_CARD:
            return self._card_builder.build_funding_card(
                kwargs.get("program_name", ""),
                kwargs.get("amount", ""),
                kwargs.get("deadline", ""),
                kwargs.get("eligibility", ""),
            )

        if card_type == CardType.KPI_CARD:
            return self._card_builder.build_kpi_card(
                kwargs.get("kpi_name", ""),
                kwargs.get("value", ""),
                kwargs.get("trend", ""),
                kwargs.get("benchmark"),
            )

        if card_type == CardType.RISK_CARD:
            return self._card_builder.build_risk_card(
                kwargs.get("risk_name", ""),
                kwargs.get("severity", ""),
                kwargs.get("probability", ""),
                kwargs.get("mitigation", ""),
            )

        if card_type == CardType.ACTION_CARD:
            return self._card_builder.build_action_card(
                kwargs.get("action_name", ""),
                kwargs.get("priority", ""),
                kwargs.get("timeline", ""),
                kwargs.get("owner", ""),
            )

        raise ValueError(f"Unknown card type: {card_type}")

    def get_font_spec(self, style: str) -> Dict[str, Any]:
        """Get font specification for a style."""
        return FONT_SCALE.get(style, FONT_SCALE["body"]).copy()

    def _convert_elements(
        self,
        content_elements: List[Dict[str, Any]],
    ) -> List[LayoutElement]:
        """Convert raw elements to layout elements."""
        layout_elements: List[LayoutElement] = []

        for raw in content_elements:
            element_type = self._determine_element_type(raw)
            content = raw.get("content", raw)

            element = self.create_element(element_type, content)
            layout_elements.append(element)

        return layout_elements

    def _determine_element_type(self, raw: Dict[str, Any]) -> ElementType:
        """Determine element type from raw content."""
        type_str = raw.get("type", "paragraph")

        type_mapping = {
            "section_head": ElementType.SECTION_HEAD,
            "heading": ElementType.SECTION_HEAD,
            "h1": ElementType.SECTION_HEAD,
            "subsection": ElementType.SUBSECTION_HEAD,
            "h2": ElementType.SUBSECTION_HEAD,
            "h3": ElementType.SUBSECTION_HEAD,
            "table": ElementType.TABLE,
            "kpi": ElementType.KPI_VISUAL,
            "kpi_visual": ElementType.KPI_VISUAL,
            "roadmap": ElementType.ROADMAP_BLOCK,
            "card": ElementType.CARD,
            "paragraph": ElementType.PARAGRAPH,
            "text": ElementType.PARAGRAPH,
            "list": ElementType.BULLET_LIST,
            "bullet_list": ElementType.BULLET_LIST,
            "chart": ElementType.CHART,
            "executive_summary": ElementType.EXECUTIVE_SUMMARY,
        }

        return type_mapping.get(type_str, ElementType.PARAGRAPH)

    def _get_margins(self, element_type: ElementType) -> Tuple[float, float]:
        """Get margins for element type."""
        if element_type == ElementType.SECTION_HEAD:
            return (
                LAYOUT_CONFIG["section_head_margin_before"],
                LAYOUT_CONFIG["section_head_margin_after"],
            )

        if element_type == ElementType.SUBSECTION_HEAD:
            return (
                LAYOUT_CONFIG["subsection_margin_before"],
                LAYOUT_CONFIG["subsection_margin_after"],
            )

        if element_type in [ElementType.TABLE, ElementType.CHART]:
            return (
                LAYOUT_CONFIG["table_margin"],
                LAYOUT_CONFIG["table_margin"],
            )

        if element_type == ElementType.CARD:
            return (
                LAYOUT_CONFIG["card_margin"],
                LAYOUT_CONFIG["card_margin"],
            )

        return (
            LAYOUT_CONFIG["paragraph_spacing"] / 2,
            LAYOUT_CONFIG["paragraph_spacing"] / 2,
        )

    def _calculate_layout_score(self, pages: List[PageLayout]) -> float:
        """Calculate overall layout quality score."""
        if not pages:
            return 0.0

        # Check fill consistency
        fill_percentages = [p["fill_percentage"] for p in pages]
        avg_fill = sum(fill_percentages) / len(fill_percentages)
        fill_variance = sum(
            (f - avg_fill) ** 2 for f in fill_percentages
        ) / len(fill_percentages)

        # Fill quality (closer to optimal is better)
        optimal_fill = LAYOUT_CONFIG["optimal_fill_percentage"]
        fill_score = 1.0 - abs(avg_fill - optimal_fill)

        # Consistency score (lower variance is better)
        consistency_score = 1.0 - min(fill_variance, 1.0)

        # White space quality
        ws_score = self._white_space_manager.calculate_overall_score(pages)

        return (fill_score * 0.4 + consistency_score * 0.3 + ws_score * 0.3)


# =============================================================================
# SINGLETON & CONVENIENCE FUNCTIONS
# =============================================================================


_engine_instance: Optional[ExecutiveLayoutEngine] = None


def get_layout_engine() -> ExecutiveLayoutEngine:
    """Get or create the singleton layout engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ExecutiveLayoutEngine()
    return _engine_instance


def process_layout(
    content_elements: List[Dict[str, Any]],
) -> LayoutResult:
    """
    Process content elements into optimized layout.

    Convenience function for external use.

    Args:
        content_elements: Raw content elements

    Returns:
        LayoutResult with optimized layout
    """
    engine = get_layout_engine()
    return engine.process_layout(content_elements)


def create_card(
    card_type: CardType,
    **kwargs: Any,
) -> CardLayout:
    """
    Create a card layout.

    Convenience function for external use.

    Args:
        card_type: Type of card
        **kwargs: Card parameters

    Returns:
        CardLayout structure
    """
    engine = get_layout_engine()
    return engine.create_card(card_type, **kwargs)


def get_font_spec(style: str) -> Dict[str, Any]:
    """
    Get font specification.

    Convenience function for external use.

    Args:
        style: Font style name

    Returns:
        Font specification dict
    """
    engine = get_layout_engine()
    return engine.get_font_spec(style)
