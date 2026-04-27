"""
Executive Navigation Engine - N4.1 PLATIN+++ Executive Experience Layer.

C-Suite Navigation Map providing:
- Semantic structure mapping for all sections
- Executive Jump Points + Impact Hotspots
- PDF navigation anchors with page-break control
- Decision Flow Guidance per section
- "You Are Here" markers for orientation

Board-Ready. Investment-Ready. C-Level-Perfect.
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TypedDict

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPE DEFINITIONS
# =============================================================================


class SectionCategory(Enum):
    """Primary section categories for executive navigation."""
    EXECUTIVE_SUMMARY = "executive_summary"
    STRATEGIC_ANALYSIS = "strategic_analysis"
    FINANCIAL_IMPACT = "financial_impact"
    OPERATIONAL_READINESS = "operational_readiness"
    RISK_GOVERNANCE = "risk_governance"
    TRANSFORMATION_ROADMAP = "transformation_roadmap"
    APPENDIX = "appendix"


class ImpactLevel(Enum):
    """Impact level classification for hotspots."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DecisionUrgency(Enum):
    """Decision urgency classification."""
    IMMEDIATE = "immediate"  # Within 30 days
    SHORT_TERM = "short_term"  # 30-90 days
    MEDIUM_TERM = "medium_term"  # 90-180 days
    LONG_TERM = "long_term"  # 180+ days


class SectionNode(TypedDict):
    """Type definition for a section node in the navigation hierarchy."""
    id: str
    title: str
    category: str
    subcategory: str
    key_sentence: str
    kpi_links: List[str]
    page_number: int
    is_jump_point: bool
    impact_level: str
    decision_urgency: str


class NavigationAnchor(TypedDict):
    """PDF navigation anchor definition."""
    anchor_id: str
    section_id: str
    page_number: int
    bookmark_title: str
    level: int
    requires_page_break: bool


class DecisionFlowGuidance(TypedDict):
    """Decision flow guidance for a section."""
    section_id: str
    why_matters: str
    decision_options: List[str]
    risks_30_days: str
    risks_90_days: str
    risks_180_days: str


class ExecutiveFlowMap(TypedDict):
    """Complete executive flow map structure."""
    total_sections: int
    categories: Dict[str, int]
    jump_points: List[str]
    impact_hotspots: List[str]
    navigation_score: float


# =============================================================================
# CONFIGURATION
# =============================================================================


NAVIGATION_CONFIG: Dict[str, Any] = {
    "max_hierarchy_depth": 4,
    "min_section_length": 50,
    "key_sentence_max_words": 25,
    "jump_point_threshold": 0.7,
    "impact_hotspot_threshold": 0.8,
    "page_break_before_major_sections": True,
    "bookmark_max_level": 3,
}


# Section category mappings for the 324 sections
SECTION_CATEGORY_RULES: Dict[str, SectionCategory] = {
    r"^G[0-9]+.*zusammenfassung": SectionCategory.EXECUTIVE_SUMMARY,
    r"^G[0-9]+.*strateg": SectionCategory.STRATEGIC_ANALYSIS,
    r"^G[0-9]+.*(roi|kosten|invest|finanz)": SectionCategory.FINANCIAL_IMPACT,
    r"^G[0-9]+.*(prozess|automat|operation)": SectionCategory.OPERATIONAL_READINESS,
    r"^G[0-9]+.*(risik|governance|compliance|ai.act)": SectionCategory.RISK_GOVERNANCE,
    r"^G[0-9]+.*(roadmap|transform|zeit)": SectionCategory.TRANSFORMATION_ROADMAP,
    r"^G[0-9]+.*(anhang|appendix|glossar)": SectionCategory.APPENDIX,
}


# Decision urgency patterns
URGENCY_PATTERNS: Dict[DecisionUrgency, List[str]] = {
    DecisionUrgency.IMMEDIATE: [
        "sofort", "unmittelbar", "kritisch", "dringend", "notwendig",
        "jetzt", "unverzüglich", "akut", "immediate", "critical",
    ],
    DecisionUrgency.SHORT_TERM: [
        "kurzfristig", "bald", "zeitnah", "in kürze", "short-term",
        "nächste wochen", "q1", "first quarter",
    ],
    DecisionUrgency.MEDIUM_TERM: [
        "mittelfristig", "halbjahr", "medium-term", "6 monate",
        "q2", "q3", "second half",
    ],
    DecisionUrgency.LONG_TERM: [
        "langfristig", "strategisch", "nachhaltig", "long-term",
        "jahresplanung", "mehrjährig", "annual",
    ],
}


# Impact indicators
IMPACT_INDICATORS: Dict[ImpactLevel, List[str]] = {
    ImpactLevel.CRITICAL: [
        "geschäftskritisch", "existenziell", "überlebenswichtig",
        "business-critical", "mission-critical", "showstopper",
    ],
    ImpactLevel.HIGH: [
        "erheblich", "signifikant", "wesentlich", "substantial",
        "major", "significant", "high-impact",
    ],
    ImpactLevel.MEDIUM: [
        "moderat", "mittelmäßig", "durchschnittlich", "moderate",
        "medium", "reasonable",
    ],
    ImpactLevel.LOW: [
        "gering", "minimal", "niedrig", "low", "minor", "marginal",
    ],
}


# Leadership relevance phrases for "Why This Matters"
LEADERSHIP_RELEVANCE: Dict[SectionCategory, str] = {
    SectionCategory.EXECUTIVE_SUMMARY: (
        "Diese Sektion liefert die Entscheidungsgrundlage für das gesamte "
        "KI-Transformationsprogramm und definiert die strategische Ausrichtung."
    ),
    SectionCategory.STRATEGIC_ANALYSIS: (
        "Strategische Positionierung bestimmt langfristige Wettbewerbsfähigkeit "
        "und Marktdifferenzierung durch KI-Kapazitäten."
    ),
    SectionCategory.FINANCIAL_IMPACT: (
        "Finanzielle Kennzahlen legitimieren Investitionsentscheidungen "
        "und schaffen Transparenz für Stakeholder und Aufsichtsgremien."
    ),
    SectionCategory.OPERATIONAL_READINESS: (
        "Operative Reife bestimmt Umsetzungsgeschwindigkeit und Risiko "
        "bei der KI-Integration in Kernprozesse."
    ),
    SectionCategory.RISK_GOVERNANCE: (
        "Risiko- und Governance-Strukturen sind Voraussetzung für regulatorische "
        "Compliance und nachhaltige KI-Nutzung im Unternehmen."
    ),
    SectionCategory.TRANSFORMATION_ROADMAP: (
        "Die Transformations-Roadmap definiert Meilensteine und Entscheidungspunkte "
        "für die systematische KI-Adoption."
    ),
    SectionCategory.APPENDIX: (
        "Detailinformationen für vertiefte Analyse und Due-Diligence-Prozesse."
    ),
}


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Section:
    """Internal representation of a report section."""
    id: str
    title: str
    content: str
    category: SectionCategory
    subcategory: str = ""
    page_number: int = 0
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    kpi_links: List[str] = field(default_factory=list)
    key_sentence: str = ""
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    decision_urgency: DecisionUrgency = DecisionUrgency.MEDIUM_TERM
    is_jump_point: bool = False
    is_impact_hotspot: bool = False


@dataclass
class NavigationGraph:
    """Complete navigation graph for the report."""
    sections: Dict[str, Section] = field(default_factory=dict)
    hierarchy: Dict[str, List[str]] = field(default_factory=dict)
    jump_points: List[str] = field(default_factory=list)
    impact_hotspots: List[str] = field(default_factory=list)
    anchors: List[NavigationAnchor] = field(default_factory=list)
    total_pages: int = 0


# =============================================================================
# SEMANTIC STRUCTURE MAPPER
# =============================================================================


class SemanticStructureMapper:
    """
    Maps semantic structure of all sections.

    Creates hierarchy: Kategorie → Sub-Kategorie → Section → Key Sentence → KPI Link
    """

    def __init__(self) -> None:
        self._section_counter = 0
        self._kpi_pattern = re.compile(
            r"(ROI|EBIT|KPI|Metric|Score|Rate|Index|Faktor|Quote|Anteil|"
            r"Wachstum|Ersparnis|Einsparung|Potential|Potenzial|\d+%|\d+€|\d+\sEUR)",
            re.IGNORECASE,
        )

    def map_sections(
        self,
        report_sections: List[Dict[str, Any]],
    ) -> Dict[str, Section]:
        """
        Map all report sections to semantic structure.

        Args:
            report_sections: List of raw report section dicts

        Returns:
            Dict mapping section IDs to Section objects
        """
        sections: Dict[str, Section] = {}

        for raw_section in report_sections:
            section = self._process_section(raw_section)
            sections[section.id] = section
            self._section_counter += 1

        log.info(
            "[N4.1-Navigation] Mapped %d sections to semantic structure",
            len(sections),
        )

        return sections

    def _process_section(self, raw: Dict[str, Any]) -> Section:
        """Process a single raw section into structured Section."""
        section_id = raw.get("id", f"section_{self._section_counter}")
        title = raw.get("title", raw.get("name", "Untitled"))
        content = raw.get("content", raw.get("text", ""))

        category = self._classify_category(title, content)
        subcategory = self._extract_subcategory(title, category)
        key_sentence = self._extract_key_sentence(content)
        kpi_links = self._extract_kpi_links(content)
        impact_level = self._assess_impact(content)
        urgency = self._assess_urgency(content)

        return Section(
            id=section_id,
            title=title,
            content=content,
            category=category,
            subcategory=subcategory,
            key_sentence=key_sentence,
            kpi_links=kpi_links,
            impact_level=impact_level,
            decision_urgency=urgency,
        )

    def _classify_category(
        self,
        title: str,
        content: str,
    ) -> SectionCategory:
        """Classify section into primary category."""
        combined = f"{title} {content[:500]}".lower()

        for pattern, category in SECTION_CATEGORY_RULES.items():
            if re.search(pattern, combined, re.IGNORECASE):
                return category

        # Default classification based on keywords
        if any(kw in combined for kw in ["zusammenfassung", "summary", "überblick"]):
            return SectionCategory.EXECUTIVE_SUMMARY
        if any(kw in combined for kw in ["strateg", "markt", "wettbewerb"]):
            return SectionCategory.STRATEGIC_ANALYSIS
        if any(kw in combined for kw in ["kosten", "roi", "invest", "finanz"]):
            return SectionCategory.FINANCIAL_IMPACT
        if any(kw in combined for kw in ["prozess", "automat", "tool"]):
            return SectionCategory.OPERATIONAL_READINESS
        if any(kw in combined for kw in ["risik", "compliance", "governance"]):
            return SectionCategory.RISK_GOVERNANCE
        if any(kw in combined for kw in ["roadmap", "plan", "phase"]):
            return SectionCategory.TRANSFORMATION_ROADMAP

        return SectionCategory.APPENDIX

    def _extract_subcategory(
        self,
        title: str,
        category: SectionCategory,
    ) -> str:
        """Extract subcategory from title."""
        # Extract G-number if present
        g_match = re.search(r"(G\d+)", title)
        if g_match:
            return g_match.group(1)

        # Use category-specific subcategorization
        title_lower = title.lower()

        if category == SectionCategory.FINANCIAL_IMPACT:
            if "roi" in title_lower:
                return "ROI Analysis"
            if "kosten" in title_lower or "cost" in title_lower:
                return "Cost Analysis"
            if "invest" in title_lower:
                return "Investment Case"
            return "Financial Metrics"

        if category == SectionCategory.RISK_GOVERNANCE:
            if "ai act" in title_lower or "ai-act" in title_lower:
                return "AI Act Compliance"
            if "dsgvo" in title_lower or "gdpr" in title_lower:
                return "Data Protection"
            if "governance" in title_lower:
                return "AI Governance"
            return "Risk Management"

        return "General"

    def _extract_key_sentence(self, content: str) -> str:
        """Extract the key sentence from content."""
        if not content:
            return ""

        # Split into sentences
        sentences = re.split(r"[.!?]\s+", content)

        if not sentences:
            return ""

        # Prefer sentences with strong indicators
        strong_indicators = [
            "empfehlung", "entscheidend", "kritisch", "wichtig",
            "priorität", "fazit", "ergebnis", "kernaussage",
        ]

        for sentence in sentences[:10]:  # Check first 10 sentences
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in strong_indicators):
                return self._truncate_sentence(sentence)

        # Fall back to first substantive sentence
        for sentence in sentences[:5]:
            if len(sentence.split()) >= 5:
                return self._truncate_sentence(sentence)

        return self._truncate_sentence(sentences[0]) if sentences else ""

    def _truncate_sentence(self, sentence: str) -> str:
        """Truncate sentence to max words."""
        max_words = NAVIGATION_CONFIG["key_sentence_max_words"]
        words = sentence.split()

        if len(words) <= max_words:
            return sentence.strip()

        return " ".join(words[:max_words]) + "..."

    def _extract_kpi_links(self, content: str) -> List[str]:
        """Extract KPI references from content."""
        matches = self._kpi_pattern.findall(content)
        # Deduplicate and limit
        unique_kpis = list(dict.fromkeys(matches))
        return unique_kpis[:5]

    def _assess_impact(self, content: str) -> ImpactLevel:
        """Assess impact level from content."""
        content_lower = content.lower()

        for level, indicators in IMPACT_INDICATORS.items():
            if any(ind in content_lower for ind in indicators):
                return level

        return ImpactLevel.MEDIUM

    def _assess_urgency(self, content: str) -> DecisionUrgency:
        """Assess decision urgency from content."""
        content_lower = content.lower()

        for urgency, patterns in URGENCY_PATTERNS.items():
            if any(pat in content_lower for pat in patterns):
                return urgency

        return DecisionUrgency.MEDIUM_TERM


# =============================================================================
# EXECUTIVE JUMP POINT DETECTOR
# =============================================================================


class ExecutiveJumpPointDetector:
    """
    Identifies key executive decision points in the report.

    Jump Points are sections that require C-Level attention or decision.
    """

    JUMP_POINT_INDICATORS: List[str] = [
        "entscheidung", "decision", "empfehlung", "recommendation",
        "handlungsbedarf", "action required", "kritisch", "critical",
        "vorstand", "board", "geschäftsführung", "management",
        "investment", "budget", "freigabe", "approval",
        "risiko", "risk", "compliance", "governance",
    ]

    def __init__(self) -> None:
        self._threshold = NAVIGATION_CONFIG["jump_point_threshold"]

    def identify_jump_points(
        self,
        sections: Dict[str, Section],
    ) -> List[str]:
        """
        Identify executive jump points across all sections.

        Args:
            sections: Dict of section ID to Section

        Returns:
            List of section IDs that are jump points
        """
        jump_points: List[str] = []

        for section_id, section in sections.items():
            score = self._calculate_jump_score(section)

            if score >= self._threshold:
                section.is_jump_point = True
                jump_points.append(section_id)

        log.info(
            "[N4.1-Navigation] Identified %d executive jump points",
            len(jump_points),
        )

        return jump_points

    def _calculate_jump_score(self, section: Section) -> float:
        """Calculate jump point score for a section."""
        score = 0.0
        content_lower = section.content.lower()
        title_lower = section.title.lower()

        # Check indicators in title (higher weight)
        for indicator in self.JUMP_POINT_INDICATORS:
            if indicator in title_lower:
                score += 0.3

        # Check indicators in content
        for indicator in self.JUMP_POINT_INDICATORS:
            if indicator in content_lower:
                score += 0.1

        # Impact level bonus
        if section.impact_level == ImpactLevel.CRITICAL:
            score += 0.3
        elif section.impact_level == ImpactLevel.HIGH:
            score += 0.2

        # Urgency bonus
        if section.decision_urgency == DecisionUrgency.IMMEDIATE:
            score += 0.2
        elif section.decision_urgency == DecisionUrgency.SHORT_TERM:
            score += 0.1

        # Category bonus
        if section.category in [
            SectionCategory.EXECUTIVE_SUMMARY,
            SectionCategory.RISK_GOVERNANCE,
        ]:
            score += 0.15

        return min(score, 1.0)


# =============================================================================
# IMPACT HOTSPOT DETECTOR
# =============================================================================


class ImpactHotspotDetector:
    """
    Identifies impact hotspots - sections with highest business impact.
    """

    FINANCIAL_IMPACT_PATTERNS: List[str] = [
        r"\d+\.?\d*\s*(mio|million|mrd|billion|tsd|thousand)",
        r"\d+\.?\d*\s*%\s*(roi|ebit|ersparnis|saving)",
        r"(€|eur)\s*\d+",
        r"\d+\s*(€|eur)",
    ]

    def __init__(self) -> None:
        self._threshold = NAVIGATION_CONFIG["impact_hotspot_threshold"]
        self._patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.FINANCIAL_IMPACT_PATTERNS
        ]

    def identify_hotspots(
        self,
        sections: Dict[str, Section],
    ) -> List[str]:
        """
        Identify impact hotspots across all sections.

        Args:
            sections: Dict of section ID to Section

        Returns:
            List of section IDs that are impact hotspots
        """
        hotspots: List[str] = []

        for section_id, section in sections.items():
            score = self._calculate_impact_score(section)

            if score >= self._threshold:
                section.is_impact_hotspot = True
                hotspots.append(section_id)

        log.info(
            "[N4.1-Navigation] Identified %d impact hotspots",
            len(hotspots),
        )

        return hotspots

    def _calculate_impact_score(self, section: Section) -> float:
        """Calculate impact score for a section."""
        score = 0.0

        # Check for financial patterns
        for pattern in self._patterns:
            matches = pattern.findall(section.content)
            score += min(len(matches) * 0.1, 0.4)

        # KPI density
        kpi_count = len(section.kpi_links)
        score += min(kpi_count * 0.1, 0.3)

        # Impact level contribution
        if section.impact_level == ImpactLevel.CRITICAL:
            score += 0.4
        elif section.impact_level == ImpactLevel.HIGH:
            score += 0.25
        elif section.impact_level == ImpactLevel.MEDIUM:
            score += 0.1

        # Category contribution
        if section.category == SectionCategory.FINANCIAL_IMPACT:
            score += 0.2
        elif section.category in [
            SectionCategory.STRATEGIC_ANALYSIS,
            SectionCategory.OPERATIONAL_READINESS,
        ]:
            score += 0.1

        return min(score, 1.0)


# =============================================================================
# PDF NAVIGATION ANCHOR GENERATOR
# =============================================================================


class PDFNavigationAnchorGenerator:
    """
    Generates PDF navigation anchors with:
    - Precise page-break control
    - Click-through bookmarks
    - "You Are Here" markers
    """

    def __init__(self) -> None:
        self._anchor_counter = 0
        self._page_break_sections = {
            SectionCategory.EXECUTIVE_SUMMARY,
            SectionCategory.STRATEGIC_ANALYSIS,
            SectionCategory.FINANCIAL_IMPACT,
            SectionCategory.RISK_GOVERNANCE,
            SectionCategory.TRANSFORMATION_ROADMAP,
        }

    def generate_anchors(
        self,
        sections: Dict[str, Section],
        estimated_pages: Dict[str, int],
    ) -> List[NavigationAnchor]:
        """
        Generate PDF navigation anchors for all sections.

        Args:
            sections: Dict of section ID to Section
            estimated_pages: Dict of section ID to estimated page number

        Returns:
            List of NavigationAnchor objects
        """
        anchors: List[NavigationAnchor] = []

        for section_id, section in sections.items():
            page_num = estimated_pages.get(section_id, 1)
            section.page_number = page_num

            anchor = self._create_anchor(section, page_num)
            anchors.append(anchor)

        log.info(
            "[N4.1-Navigation] Generated %d PDF navigation anchors",
            len(anchors),
        )

        return anchors

    def _create_anchor(
        self,
        section: Section,
        page_number: int,
    ) -> NavigationAnchor:
        """Create a single navigation anchor."""
        self._anchor_counter += 1

        # Determine bookmark level based on category/subcategory
        level = self._determine_bookmark_level(section)

        # Check if page break is needed
        requires_break = self._requires_page_break(section)

        # Generate unique anchor ID
        anchor_id = self._generate_anchor_id(section)

        return NavigationAnchor(
            anchor_id=anchor_id,
            section_id=section.id,
            page_number=page_number,
            bookmark_title=self._format_bookmark_title(section),
            level=level,
            requires_page_break=requires_break,
        )

    def _determine_bookmark_level(self, section: Section) -> int:
        """Determine bookmark hierarchy level."""
        max_level = int(NAVIGATION_CONFIG["bookmark_max_level"])

        # Category-level sections are level 1
        if section.is_jump_point or section.is_impact_hotspot:
            return 1

        # Based on subcategory
        if section.subcategory and section.subcategory.startswith("G"):
            return 2

        return int(min(3, max_level))

    def _requires_page_break(self, section: Section) -> bool:
        """Check if section requires page break before it."""
        if not NAVIGATION_CONFIG["page_break_before_major_sections"]:
            return False

        # Major sections always get page break
        if section.category in self._page_break_sections:
            if section.is_jump_point:
                return True

        return False

    def _generate_anchor_id(self, section: Section) -> str:
        """Generate unique anchor ID for PDF."""
        # Create deterministic hash from section ID
        hash_input = f"{section.id}_{section.title}"
        hash_val = hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"nav_{hash_val}"

    def _format_bookmark_title(self, section: Section) -> str:
        """Format bookmark title for PDF navigation."""
        # Clean title
        title = section.title.strip()

        # Add marker for jump points
        if section.is_jump_point:
            title = f"★ {title}"
        elif section.is_impact_hotspot:
            title = f"● {title}"

        # Truncate if too long
        if len(title) > 50:
            title = title[:47] + "..."

        return title


# =============================================================================
# DECISION FLOW GUIDANCE GENERATOR
# =============================================================================


class DecisionFlowGuidanceGenerator:
    """
    Generates decision flow guidance for each section:
    - Why this matters for leadership
    - Immediate decision options
    - Risks of inaction (30/90/180 days)
    """

    DEFAULT_DECISION_OPTIONS: Dict[SectionCategory, List[str]] = {
        SectionCategory.EXECUTIVE_SUMMARY: [
            "Gesamtstrategie bestätigen und Ressourcen freigeben",
            "Detailanalyse einzelner Bereiche anfordern",
            "Priorisierung der Handlungsfelder festlegen",
        ],
        SectionCategory.STRATEGIC_ANALYSIS: [
            "Strategische Ausrichtung bestätigen",
            "Wettbewerbsanalyse vertiefen",
            "Marktpositionierung neu bewerten",
        ],
        SectionCategory.FINANCIAL_IMPACT: [
            "Investitionsbudget freigeben",
            "ROI-Ziele festlegen und Tracking initiieren",
            "Kostenbasis validieren lassen",
        ],
        SectionCategory.OPERATIONAL_READINESS: [
            "Pilotprojekt genehmigen",
            "Ressourcenallokation bestätigen",
            "Skill-Assessment durchführen lassen",
        ],
        SectionCategory.RISK_GOVERNANCE: [
            "Governance-Framework etablieren",
            "Compliance-Roadmap bestätigen",
            "Risikomitigationsmaßnahmen priorisieren",
        ],
        SectionCategory.TRANSFORMATION_ROADMAP: [
            "Transformationsphase 1 starten",
            "Change-Management-Programm initiieren",
            "Meilensteine und KPIs festlegen",
        ],
        SectionCategory.APPENDIX: [
            "Detailanalyse bei Bedarf anfordern",
            "Vertiefungsmaterial verteilen",
            "Experten-Review einplanen",
        ],
    }

    INACTION_RISKS: Dict[SectionCategory, Dict[str, str]] = {
        SectionCategory.EXECUTIVE_SUMMARY: {
            "30": "Verzögerung strategischer Entscheidungen, Wettbewerbsnachteil bei Early Movers",
            "90": "Verpasste Quick-Win-Opportunitäten, Ressourcenfehlallokation",
            "180": "Signifikanter Wettbewerbsrückstand, potentieller Marktanteilsverlust",
        },
        SectionCategory.STRATEGIC_ANALYSIS: {
            "30": "Unklare strategische Ausrichtung, verzögerte Projektinitiierung",
            "90": "Inkonsistente KI-Initiativen, Budget-Fragmentierung",
            "180": "Strategische Fehlpositionierung, schwer korrigierbare Investitionsentscheidungen",
        },
        SectionCategory.FINANCIAL_IMPACT: {
            "30": "Verzögerte Budgetallokation, verpasste Fördermittel-Deadlines",
            "90": "Opportunitätskosten durch Nicht-Investition, ROI-Verzögerung",
            "180": "Kumulative Effizienzeinbußen, Wettbewerber realisieren Kostenvorteil",
        },
        SectionCategory.OPERATIONAL_READINESS: {
            "30": "Prozessineffizienzen bleiben bestehen, Mitarbeiterfrustration",
            "90": "Technologieschulden akkumulieren, Change-Resistance verfestigt sich",
            "180": "Operative Inflexibilität, signifikanter Nachholbedarf",
        },
        SectionCategory.RISK_GOVERNANCE: {
            "30": "Ungeklärte Compliance-Risiken, potentielle Haftungsfragen",
            "90": "Regulatorische Exposition, AI-Act-Vorbereitungsrückstand",
            "180": "Compliance-Verletzungsrisiko, Reputationsschäden möglich",
        },
        SectionCategory.TRANSFORMATION_ROADMAP: {
            "30": "Planungsunsicherheit, unkoordinierte Einzelinitiativen",
            "90": "Transformationsverzug, erschwerte Erweiterung",
            "180": "Grundlegende Nachplanung erforderlich, erhöhte Transformationskosten",
        },
        SectionCategory.APPENDIX: {
            "30": "Informationsdefizite bei Detailfragen",
            "90": "Fehlende Dokumentation für Audits",
            "180": "Wissenslücken bei Due-Diligence-Prozessen",
        },
    }

    def generate_guidance(
        self,
        sections: Dict[str, Section],
    ) -> Dict[str, DecisionFlowGuidance]:
        """
        Generate decision flow guidance for all sections.

        Args:
            sections: Dict of section ID to Section

        Returns:
            Dict of section ID to DecisionFlowGuidance
        """
        guidance_map: Dict[str, DecisionFlowGuidance] = {}

        for section_id, section in sections.items():
            guidance = self._create_guidance(section)
            guidance_map[section_id] = guidance

        log.info(
            "[N4.1-Navigation] Generated decision flow guidance for %d sections",
            len(guidance_map),
        )

        return guidance_map

    def _create_guidance(self, section: Section) -> DecisionFlowGuidance:
        """Create decision flow guidance for a single section."""
        category = section.category

        # Get relevance statement
        why_matters = LEADERSHIP_RELEVANCE.get(
            category,
            "Diese Sektion enthält relevante Informationen für die Entscheidungsfindung.",
        )

        # Get decision options
        options = self.DEFAULT_DECISION_OPTIONS.get(category, [])

        # Get inaction risks
        risks = self.INACTION_RISKS.get(category, {})

        return DecisionFlowGuidance(
            section_id=section.id,
            why_matters=why_matters,
            decision_options=options,
            risks_30_days=risks.get("30", "Verzögerte Entscheidungsfindung"),
            risks_90_days=risks.get("90", "Akkumulierte Opportunitätskosten"),
            risks_180_days=risks.get("180", "Signifikanter strategischer Nachteil"),
        )


# =============================================================================
# YOU ARE HERE MARKER GENERATOR
# =============================================================================


class YouAreHereMarkerGenerator:
    """
    Generates "You Are Here" markers for each major section.

    Provides contextual orientation showing:
    - Current position in report
    - Related sections
    - Navigation path
    """

    def generate_markers(
        self,
        sections: Dict[str, Section],
        hierarchy: Dict[str, List[str]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate "You Are Here" markers for navigation.

        Args:
            sections: Dict of section ID to Section
            hierarchy: Category to section IDs mapping

        Returns:
            Dict of section ID to marker information
        """
        markers: Dict[str, Dict[str, Any]] = {}

        # Group sections by category
        category_sections: Dict[SectionCategory, List[Section]] = {}
        for section in sections.values():
            if section.category not in category_sections:
                category_sections[section.category] = []
            category_sections[section.category].append(section)

        for section_id, section in sections.items():
            marker = self._create_marker(section, category_sections)
            markers[section_id] = marker

        return markers

    def _create_marker(
        self,
        section: Section,
        category_sections: Dict[SectionCategory, List[Section]],
    ) -> Dict[str, Any]:
        """Create a single "You Are Here" marker."""
        category_list = category_sections.get(section.category, [])
        section_index = -1

        for i, s in enumerate(category_list):
            if s.id == section.id:
                section_index = i
                break

        # Find previous and next sections
        prev_section: Optional[str] = None
        next_section: Optional[str] = None

        if section_index > 0:
            prev_section = category_list[section_index - 1].id
        if section_index < len(category_list) - 1:
            next_section = category_list[section_index + 1].id

        return {
            "section_id": section.id,
            "category": section.category.value,
            "position_in_category": section_index + 1,
            "total_in_category": len(category_list),
            "previous_section": prev_section,
            "next_section": next_section,
            "is_jump_point": section.is_jump_point,
            "is_hotspot": section.is_impact_hotspot,
            "breadcrumb": f"{section.category.value} > {section.subcategory} > {section.title}",
        }


# =============================================================================
# MAIN ENGINE CLASS
# =============================================================================


class ExecutiveNavigationEngine:
    """
    Main engine for executive navigation.

    Orchestrates:
    - Semantic structure mapping
    - Jump point detection
    - Impact hotspot identification
    - PDF anchor generation
    - Decision flow guidance
    - You Are Here markers
    """

    def __init__(self) -> None:
        self._structure_mapper = SemanticStructureMapper()
        self._jump_detector = ExecutiveJumpPointDetector()
        self._hotspot_detector = ImpactHotspotDetector()
        self._anchor_generator = PDFNavigationAnchorGenerator()
        self._guidance_generator = DecisionFlowGuidanceGenerator()
        self._marker_generator = YouAreHereMarkerGenerator()

        self._navigation_graph: Optional[NavigationGraph] = None

    def build_navigation(
        self,
        report_sections: List[Dict[str, Any]],
        estimated_pages: Optional[Dict[str, int]] = None,
    ) -> NavigationGraph:
        """
        Build complete executive navigation graph.

        Args:
            report_sections: List of raw report section dicts
            estimated_pages: Optional dict of section ID to page number

        Returns:
            Complete NavigationGraph
        """
        log.info("[N4.1-Navigation] Building executive navigation graph...")

        # Map semantic structure
        sections = self._structure_mapper.map_sections(report_sections)

        # Identify jump points
        jump_points = self._jump_detector.identify_jump_points(sections)

        # Identify impact hotspots
        hotspots = self._hotspot_detector.identify_hotspots(sections)

        # Generate page estimates if not provided
        if estimated_pages is None:
            estimated_pages = self._estimate_pages(sections)

        # Generate PDF anchors
        anchors = self._anchor_generator.generate_anchors(
            sections, estimated_pages,
        )

        # Build hierarchy
        hierarchy = self._build_hierarchy(sections)

        # Create navigation graph
        self._navigation_graph = NavigationGraph(
            sections=sections,
            hierarchy=hierarchy,
            jump_points=jump_points,
            impact_hotspots=hotspots,
            anchors=anchors,
            total_pages=max(estimated_pages.values()) if estimated_pages else 0,
        )

        log.info(
            "[N4.1-Navigation] Navigation graph complete: %d sections, "
            "%d jump points, %d hotspots",
            len(sections),
            len(jump_points),
            len(hotspots),
        )

        return self._navigation_graph

    def get_decision_guidance(
        self,
        section_id: Optional[str] = None,
    ) -> Dict[str, DecisionFlowGuidance]:
        """
        Get decision flow guidance.

        Args:
            section_id: Optional specific section ID

        Returns:
            Dict of section ID to guidance
        """
        if self._navigation_graph is None:
            return {}

        guidance = self._guidance_generator.generate_guidance(
            self._navigation_graph.sections,
        )

        if section_id:
            return {section_id: guidance[section_id]} if section_id in guidance else {}

        return guidance

    def get_you_are_here(
        self,
        section_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get "You Are Here" marker for a section.

        Args:
            section_id: Section ID to get marker for

        Returns:
            Marker dict or None
        """
        if self._navigation_graph is None:
            return None

        markers = self._marker_generator.generate_markers(
            self._navigation_graph.sections,
            self._navigation_graph.hierarchy,
        )

        return markers.get(section_id)

    def get_executive_flow_map(self) -> ExecutiveFlowMap:
        """
        Get the executive flow map summary.

        Returns:
            ExecutiveFlowMap with navigation statistics
        """
        if self._navigation_graph is None:
            return ExecutiveFlowMap(
                total_sections=0,
                categories={},
                jump_points=[],
                impact_hotspots=[],
                navigation_score=0.0,
            )

        # Count sections per category
        categories: Dict[str, int] = {}
        for section in self._navigation_graph.sections.values():
            cat = section.category.value
            categories[cat] = categories.get(cat, 0) + 1

        # Calculate navigation score
        nav_score = self._calculate_navigation_score()

        return ExecutiveFlowMap(
            total_sections=len(self._navigation_graph.sections),
            categories=categories,
            jump_points=self._navigation_graph.jump_points,
            impact_hotspots=self._navigation_graph.impact_hotspots,
            navigation_score=nav_score,
        )

    def get_bookmark_map(self) -> List[Dict[str, Any]]:
        """
        Get bookmark map for PDF generation.

        Returns:
            List of bookmark entries for PDF
        """
        if self._navigation_graph is None:
            return []

        bookmarks: List[Dict[str, Any]] = []

        for anchor in self._navigation_graph.anchors:
            bookmarks.append({
                "id": anchor["anchor_id"],
                "title": anchor["bookmark_title"],
                "page": anchor["page_number"],
                "level": anchor["level"],
                "page_break": anchor["requires_page_break"],
            })

        # Sort by page number
        bookmarks.sort(key=lambda x: (x["page"], x["level"]))

        return bookmarks

    def _estimate_pages(
        self,
        sections: Dict[str, Section],
    ) -> Dict[str, int]:
        """Estimate page numbers for sections."""
        estimates: Dict[str, int] = {}
        current_page = 1

        # Approximate characters per page
        chars_per_page = 3000

        for section_id, section in sections.items():
            estimates[section_id] = current_page

            # Estimate pages for this section
            content_length = len(section.content)
            section_pages = max(1, content_length // chars_per_page)
            current_page += section_pages

        return estimates

    def _build_hierarchy(
        self,
        sections: Dict[str, Section],
    ) -> Dict[str, List[str]]:
        """Build category hierarchy mapping."""
        hierarchy: Dict[str, List[str]] = {}

        for section_id, section in sections.items():
            cat = section.category.value
            if cat not in hierarchy:
                hierarchy[cat] = []
            hierarchy[cat].append(section_id)

        return hierarchy

    def _calculate_navigation_score(self) -> float:
        """Calculate overall navigation quality score."""
        if self._navigation_graph is None:
            return 0.0

        total = len(self._navigation_graph.sections)
        if total == 0:
            return 0.0

        # Factors for score
        jump_ratio = len(self._navigation_graph.jump_points) / total
        hotspot_ratio = len(self._navigation_graph.impact_hotspots) / total
        anchor_coverage = len(self._navigation_graph.anchors) / total

        # Optimal ratios
        optimal_jump = 0.15  # ~15% should be jump points
        optimal_hotspot = 0.10  # ~10% should be hotspots

        # Score calculation
        jump_score = 1.0 - abs(jump_ratio - optimal_jump) * 3
        hotspot_score = 1.0 - abs(hotspot_ratio - optimal_hotspot) * 3
        coverage_score = min(anchor_coverage, 1.0)

        # Weight and combine
        score = (
            jump_score * 0.3 +
            hotspot_score * 0.3 +
            coverage_score * 0.4
        )

        return max(0.0, min(1.0, score))


# =============================================================================
# SINGLETON & CONVENIENCE FUNCTIONS
# =============================================================================


_engine_instance: Optional[ExecutiveNavigationEngine] = None


def get_navigation_engine() -> ExecutiveNavigationEngine:
    """Get or create the singleton navigation engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ExecutiveNavigationEngine()
    return _engine_instance


def build_executive_navigation(
    report_sections: List[Dict[str, Any]],
    estimated_pages: Optional[Dict[str, int]] = None,
) -> NavigationGraph:
    """
    Build executive navigation for a report.

    Convenience function for external use.

    Args:
        report_sections: List of report section dicts
        estimated_pages: Optional page number estimates

    Returns:
        Complete NavigationGraph
    """
    engine = get_navigation_engine()
    return engine.build_navigation(report_sections, estimated_pages)


def get_bookmark_map() -> List[Dict[str, Any]]:
    """
    Get PDF bookmark map.

    Convenience function for external use.

    Returns:
        List of bookmark entries
    """
    engine = get_navigation_engine()
    return engine.get_bookmark_map()


def get_executive_flow_map() -> ExecutiveFlowMap:
    """
    Get executive flow map summary.

    Convenience function for external use.

    Returns:
        ExecutiveFlowMap with statistics
    """
    engine = get_navigation_engine()
    return engine.get_executive_flow_map()


def get_section_guidance(section_id: str) -> Optional[DecisionFlowGuidance]:
    """
    Get decision guidance for a specific section.

    Convenience function for external use.

    Args:
        section_id: Section to get guidance for

    Returns:
        DecisionFlowGuidance or None
    """
    engine = get_navigation_engine()
    guidance = engine.get_decision_guidance(section_id)
    return guidance.get(section_id)


def get_you_are_here_marker(section_id: str) -> Optional[Dict[str, Any]]:
    """
    Get "You Are Here" marker for a section.

    Convenience function for external use.

    Args:
        section_id: Section to get marker for

    Returns:
        Marker dict or None
    """
    engine = get_navigation_engine()
    return engine.get_you_are_here(section_id)
