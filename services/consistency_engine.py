# -*- coding: utf-8 -*-
"""
G22: Cross-Section Consistency Engine
======================================

Ein internes Modul, das sicherstellt, dass alle Report-Sections
logisch zueinander passen. Erreicht "McKinsey Digital"-Level Konsistenz.

Prüft 6 Konsistenz-Domänen:
1. Tools-Konsistenz (KI-Stack ↔ Tools Section)
2. Funding-Konsistenz (KI-Stack ↔ Funding Section)
3. KPI-Konsistenz (ROI ↔ Payback ↔ Time Savings)
4. Risk-Level-Konsistenz (KI-Stack ↔ AI Act ↔ Risks)
5. Starter-Kit ↔ Roadmap Alignment
6. Narrative-Kohärenz (keine widersprüchlichen Aussagen)

Version: 1.0.0 (Sprint G22)
Author: Claude + Wolf
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from html import unescape

log = logging.getLogger(__name__)

__all__ = [
    "ConsistencyIssue",
    "ConsistencyReport",
    "ConsistencyEngine",
    "check_consistency",
]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ConsistencyIssue:
    """Einzelnes Konsistenz-Problem zwischen Sections."""

    rule_id: str           # z.B. "TOOLS_001"
    severity: str          # "ERROR", "WARNING", "INFO"
    domain: str            # "tools", "funding", "kpi", "risk", "roadmap", "narrative"
    source_section: str    # z.B. "ki_stack_summary"
    target_section: str    # z.B. "tools_empfehlungen"
    message: str           # Menschenlesbare Beschreibung
    expected: Any = None   # Erwarteter Wert
    actual: Any = None     # Tatsächlicher Wert
    suggestion: str = ""   # Lösungsvorschlag

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "domain": self.domain,
            "source_section": self.source_section,
            "target_section": self.target_section,
            "message": self.message,
            "expected": str(self.expected) if self.expected else None,
            "actual": str(self.actual) if self.actual else None,
            "suggestion": self.suggestion,
        }


@dataclass
class ConsistencyReport:
    """Gesamtergebnis der Konsistenz-Prüfung."""

    status: str = "PASS"          # "PASS", "WARN", "FAIL"
    grade: str = "A"              # "A", "B", "C", "D", "F"
    score: float = 100.0          # 0.0-100.0
    issues: List[ConsistencyIssue] = field(default_factory=list)
    checked_rules: int = 0
    passed_rules: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Breakdown by domain
    domain_scores: Dict[str, float] = field(default_factory=dict)

    def add_issue(self, issue: ConsistencyIssue) -> None:
        """Add an issue and recalculate status."""
        self.issues.append(issue)
        self._recalculate()

    def _recalculate(self) -> None:
        """Recalculate status, grade, and score based on issues."""
        errors = sum(1 for i in self.issues if i.severity == "ERROR")
        warnings = sum(1 for i in self.issues if i.severity == "WARNING")

        # Score calculation: -10 per error, -3 per warning
        self.score = max(0.0, 100.0 - (errors * 10) - (warnings * 3))

        # Grade calculation
        if self.score >= 95:
            self.grade = "A"
        elif self.score >= 85:
            self.grade = "B"
        elif self.score >= 70:
            self.grade = "C"
        elif self.score >= 50:
            self.grade = "D"
        else:
            self.grade = "F"

        # Status calculation
        if errors > 0:
            self.status = "FAIL"
        elif warnings > 0:
            self.status = "WARN"
        else:
            self.status = "PASS"

        self.passed_rules = self.checked_rules - errors - warnings

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status,
            "grade": self.grade,
            "score": round(self.score, 1),
            "issues": [i.to_dict() for i in self.issues],
            "checked_rules": self.checked_rules,
            "passed_rules": self.passed_rules,
            "timestamp": self.timestamp,
            "domain_scores": self.domain_scores,
            "summary": {
                "errors": sum(1 for i in self.issues if i.severity == "ERROR"),
                "warnings": sum(1 for i in self.issues if i.severity == "WARNING"),
                "info": sum(1 for i in self.issues if i.severity == "INFO"),
            }
        }


# =============================================================================
# EXTRACTION HELPERS
# =============================================================================

def _strip_html(html: str) -> str:
    """Remove HTML tags and decode entities."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_tool_names(html: str) -> List[str]:
    """
    Extract tool names from HTML section.

    Looks for patterns like:
    - <td>ToolName</td> in tables
    - <strong>ToolName</strong> in cards
    - .pair-card-name content
    """
    if not html:
        return []

    tools: Set[str] = set()

    # Pattern 1: Table cells with tool names (typically first column)
    table_pattern = r'<td[^>]*>([A-Za-z0-9\s\-\.]+(?:AI|GPT|Bot|Tool|Cloud|Pro|Plus)?)</td>'
    for match in re.finditer(table_pattern, html, re.IGNORECASE):
        name = match.group(1).strip()
        if len(name) > 2 and len(name) < 50:
            tools.add(name)

    # Pattern 2: pair-card-name class (G21 design)
    card_pattern = r'<[^>]*class="[^"]*pair-card-name[^"]*"[^>]*>([^<]+)</[^>]+>'
    for match in re.finditer(card_pattern, html, re.IGNORECASE):
        name = match.group(1).strip()
        if len(name) > 2:
            tools.add(name)

    # Pattern 3: Strong tags in tool context
    strong_pattern = r'<strong[^>]*>([A-Za-z0-9\s\-\.]+(?:AI|GPT|Bot)?)</strong>'
    for match in re.finditer(strong_pattern, html, re.IGNORECASE):
        name = match.group(1).strip()
        # Filter out generic phrases
        if (len(name) > 2 and len(name) < 40 and
            not any(skip in name.lower() for skip in [
                "schritt", "step", "phase", "monat", "woche",
                "hinweis", "note", "wichtig", "tipp"
            ])):
            tools.add(name)

    return list(tools)


def _extract_funding_programs(html: str) -> List[str]:
    """
    Extract funding program names from HTML section.

    Looks for common German funding program patterns.
    """
    if not html:
        return []

    programs: Set[str] = set()

    # Known funding programs
    known_programs = [
        "go-digital", "go digital", "Digital Jetzt", "ZIM",
        "INVEST", "KfW", "ERP", "BAFA", "GRW",
        "Digitalbonus", "Digital-Bonus", "Digitalisierungsprämie",
        "Gründungszuschuss", "EXIST", "High-Tech Gründerfonds",
        "Horizon Europe", "Horizon 2020", "KMU-innovativ",
        "Förderprogramm", "Zuschuss", "Förderung",
    ]

    text = _strip_html(html)

    for prog in known_programs:
        if prog.lower() in text.lower():
            programs.add(prog)

    # Pattern: pair-card-name for funding (G21 design)
    card_pattern = r'<[^>]*class="[^"]*pair-card-name[^"]*"[^>]*>([^<]+)</[^>]+>'
    for match in re.finditer(card_pattern, html, re.IGNORECASE):
        name = match.group(1).strip()
        if len(name) > 3:
            programs.add(name)

    return list(programs)


def _extract_risk_level(html: str) -> Optional[str]:
    """
    Extract AI Act risk level from HTML section.

    Returns: "low", "medium", "high", or None
    """
    if not html:
        return None

    text = html.lower()

    # Check for risk-level CSS classes (G21 design)
    if "risk-high" in text or "high-risk" in text or "hohes risiko" in text:
        return "high"
    if "risk-medium" in text or "medium-risk" in text or "mittleres risiko" in text:
        return "medium"
    if "risk-low" in text or "low-risk" in text or "niedriges risiko" in text:
        return "low"

    # Check for text patterns (expanded to handle more German phrasings)
    risk_patterns = {
        "high": [
            r"risiko[:\s]*hoch",
            r"high[\s\-]?risk",
            r"hohes\s+risiko",
            r"risiko\s+(?:ist\s+)?hoch",
        ],
        "medium": [
            r"risiko[:\s]*mittel",
            r"medium[\s\-]?risk",
            r"mittleres\s+risiko",
            r"risiko\s+(?:ist\s+)?mittel",
        ],
        "low": [
            r"risiko[:\s]*niedrig",
            r"low[\s\-]?risk",
            r"niedriges\s+risiko",
            r"geringes\s+risiko",
            r"risiko\s+(?:ist\s+)?niedrig",
            r"risiko\s+(?:ist\s+)?gering",
        ],
    }

    for level, patterns in risk_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return level

    return None


def _extract_kpis(html: str) -> Dict[str, Optional[float]]:
    """
    Extract KPI values from HTML section.

    Returns dict with keys: roi, payback_months, time_savings_hours, time_savings_eur
    """
    if not html:
        return {}

    kpis: Dict[str, Optional[float]] = {
        "roi": None,
        "payback_months": None,
        "time_savings_hours": None,
        "time_savings_eur": None,
    }

    text = _strip_html(html)

    # ROI patterns: "ROI 150%", "ROI: 150%", "150% ROI", "ROI beträgt 150%"
    roi_patterns = [
        r"ROI[:\s]*(\d+(?:[.,]\d+)?)\s*%",
        r"ROI\s+(?:beträgt|von|ist|liegt\s+bei)\s+(\d+(?:[.,]\d+)?)\s*%",
        r"(\d+(?:[.,]\d+)?)\s*%\s*ROI",
        r"Return on Investment[:\s]*(\d+(?:[.,]\d+)?)\s*%",
        r"(\d+(?:[.,]\d+)?)\s*%\s*(?:Return|ROI)",
    ]
    for pattern in roi_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            kpis["roi"] = float(match.group(1).replace(",", "."))
            break

    # Payback patterns: "Payback 6 Monate", "Amortisation: 6 Monate"
    payback_patterns = [
        r"Payback[:\s]*(\d+(?:[.,]\d+)?)\s*(?:Monate?|months?)",
        r"Amortisation[:\s]*(\d+(?:[.,]\d+)?)\s*(?:Monate?|months?)",
        r"Break[\s\-]?even[:\s]*(\d+(?:[.,]\d+)?)\s*(?:Monate?|months?)",
        r"(\d+(?:[.,]\d+)?)\s*(?:Monate?|months?)\s*(?:Payback|Amortisation)",
    ]
    for pattern in payback_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            kpis["payback_months"] = float(match.group(1).replace(",", "."))
            break

    # Time savings hours: "40 Stunden/Monat", "40 h/Monat"
    time_patterns = [
        r"(\d+(?:[.,]\d+)?)\s*(?:Stunden?|hours?|h)\s*/?\s*(?:Monat|month|mtl)",
        r"Zeitersparnis[:\s]*(\d+(?:[.,]\d+)?)\s*(?:Stunden?|hours?|h)",
    ]
    for pattern in time_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            kpis["time_savings_hours"] = float(match.group(1).replace(",", "."))
            break

    # Time savings EUR: "2.400 €/Monat", "€ 2.400/Monat"
    eur_patterns = [
        r"(\d+(?:[.,]\d+)?)\s*€\s*/?\s*(?:Monat|month|mtl)",
        r"€\s*(\d+(?:[.,]\d+)?)\s*/?\s*(?:Monat|month|mtl)",
        r"Einsparung[:\s]*(\d+(?:[.,]\d+)?)\s*€",
    ]
    for pattern in eur_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val_str = match.group(1).replace(".", "").replace(",", ".")
            kpis["time_savings_eur"] = float(val_str)
            break

    return kpis


def _extract_step_count(html: str) -> int:
    """Extract number of steps from Starter-Kit section."""
    if not html:
        return 0

    # Count step-card elements (G21 design)
    # Match class="step-card" exactly (not step-cards or step-card-number)
    # Pattern: step-card followed by space or end of class attribute
    card_count = len(re.findall(r'class="[^"]*\bstep-card\b(?!-)[^"]*"', html, re.IGNORECASE))
    if card_count > 0:
        return card_count

    # Alternative: count step-card-number elements (each step has one number)
    number_count = len(re.findall(r'class="[^"]*step-card-number[^"]*"', html, re.IGNORECASE))
    if number_count > 0:
        return number_count

    # Count numbered steps in text
    step_patterns = [
        r'Schritt\s*(\d+)',
        r'Step\s*(\d+)',
        r'Phase\s*(\d+)',
    ]

    steps: Set[int] = set()
    for pattern in step_patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            steps.add(int(match.group(1)))

    return len(steps)


def _count_words(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    clean = _strip_html(text)
    return len(clean.split())


# =============================================================================
# CONSISTENCY RULES
# =============================================================================

class ConsistencyEngine:
    """
    Cross-Section Consistency Engine.

    Prüft alle Report-Sections auf logische Konsistenz.
    """

    # Tolerance thresholds
    ROI_TOLERANCE_PCT = 15.0          # Allow 15% deviation in ROI values
    PAYBACK_TOLERANCE_MONTHS = 2.0    # Allow 2 months deviation
    TIME_SAVINGS_TOLERANCE_PCT = 20.0 # Allow 20% deviation

    def __init__(
        self,
        sections: Dict[str, str],
        briefing: Dict[str, Any],
        language: str = "de",
    ):
        """
        Initialize Consistency Engine.

        Args:
            sections: Dict of section_key -> HTML content
            briefing: Original briefing/answers dict
            language: Report language ("de" or "en")
        """
        self.sections = sections
        self.briefing = briefing
        self.language = language
        self.report = ConsistencyReport()

    def check_all(self) -> ConsistencyReport:
        """
        Run all consistency checks.

        Returns:
            ConsistencyReport with all findings
        """
        log.info("[G22] Starting cross-section consistency check...")

        # Run all domain checks
        self._check_tools_consistency()
        self._check_funding_consistency()
        self._check_kpi_consistency()
        self._check_risk_level_consistency()
        self._check_roadmap_alignment()
        self._check_narrative_coherence()
        self._check_exec_snapshot_consistency()  # G27
        self._check_risk_engine_consistency()  # G29
        self._check_business_case_consistency()  # G30
        self._check_recommendations_consistency()  # G32

        # Calculate domain scores
        self._calculate_domain_scores()

        log.info(
            "[G22] Consistency check complete: status=%s, grade=%s, score=%.1f",
            self.report.status, self.report.grade, self.report.score
        )

        return self.report

    # -------------------------------------------------------------------------
    # DOMAIN 1: Tools Consistency
    # -------------------------------------------------------------------------

    def _check_tools_consistency(self) -> None:
        """Check tools are consistent between KI-Stack and Tools section."""
        self.report.checked_rules += 3

        ki_stack_html = self.sections.get("KI_STACK_SUMMARY_HTML", "")
        tools_html = self.sections.get("TOOLS_EMPFEHLUNGEN_HTML", "") or self.sections.get("TOOLS_HTML", "")

        if not ki_stack_html or not tools_html:
            log.debug("[G22] Tools consistency: Skipping (missing sections)")
            return

        # Extract tools from both sections
        ki_stack_tools = _extract_tool_names(ki_stack_html)
        full_tools = _extract_tool_names(tools_html)

        # Rule TOOLS_001: KI-Stack tools must appear in full tools section
        if ki_stack_tools:
            missing_tools = [t for t in ki_stack_tools if t not in full_tools and
                           not any(t.lower() in ft.lower() for ft in full_tools)]

            if missing_tools:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="TOOLS_001",
                    severity="WARNING",
                    domain="tools",
                    source_section="ki_stack_summary",
                    target_section="tools_empfehlungen",
                    message=f"KI-Stack enthält Tools, die nicht in der Tools-Section erscheinen",
                    expected=f"Tools aus KI-Stack in Tools-Section vorhanden",
                    actual=f"Fehlend: {', '.join(missing_tools[:3])}",
                    suggestion="Synchronisiere Tool-Empfehlungen zwischen Sections",
                ))

        # Rule TOOLS_002: Check tool count is reasonable
        if len(ki_stack_tools) > 5:
            self.report.add_issue(ConsistencyIssue(
                rule_id="TOOLS_002",
                severity="INFO",
                domain="tools",
                source_section="ki_stack_summary",
                target_section="ki_stack_summary",
                message="KI-Stack enthält mehr als 5 Tools (sollte max. 3 sein)",
                expected="3 Tools",
                actual=f"{len(ki_stack_tools)} Tools",
                suggestion="Reduziere auf Top-3 Tools",
            ))

        # Rule TOOLS_003: Check full tools section has sufficient recommendations
        if len(full_tools) < 3:
            self.report.add_issue(ConsistencyIssue(
                rule_id="TOOLS_003",
                severity="WARNING",
                domain="tools",
                source_section="tools_empfehlungen",
                target_section="tools_empfehlungen",
                message="Tools-Section enthält weniger als 3 Empfehlungen",
                expected="Mindestens 3 Tools",
                actual=f"{len(full_tools)} Tools",
                suggestion="Erweitere Tool-Empfehlungen basierend auf Branche und Use Cases",
            ))

        # G25: Additional Tools Engine v4 rules
        self._check_tools_v4_consistency(ki_stack_html, tools_html)

    def _check_tools_v4_consistency(self, ki_stack_html: str, tools_html: str) -> None:
        """G25: Check Tools Engine v4 consistency rules."""
        self.report.checked_rules += 3

        size = self.briefing.get("unternehmensgroesse", "").lower()
        size_label = "solo" if "solo" in size or "freiberuf" in size else (
            "team" if "team" in size or "klein" in size else "kmu"
        )

        # Rule TOOLS_004: Cost Level must match recommended savings potential
        # Check if high-cost tools (€€€) are recommended when savings are low
        einsparung = self.briefing.get("EINSPARUNG_MONAT_EUR", 0)
        try:
            einsparung = float(einsparung) if einsparung else 0
        except (ValueError, TypeError):
            einsparung = 0

        # Check for expensive tool badges in HTML
        has_expensive_tools = "cost-level-4" in ki_stack_html or "cost-level-5" in ki_stack_html or "€€€" in ki_stack_html

        if has_expensive_tools and einsparung < 500:
            self.report.add_issue(ConsistencyIssue(
                rule_id="TOOLS_004",
                severity="WARNING",
                domain="tools",
                source_section="ki_stack_summary",
                target_section="business_case",
                message="Teure Tools empfohlen bei geringem Einsparpotenzial",
                expected="Kostengünstige Tools bei geringer Ersparnis",
                actual=f"Enterprise-Tools bei {einsparung:.0f}€/Monat Ersparnis",
                suggestion="Wähle kostengünstigere Tool-Alternativen für das Budget",
            ))

        # Rule TOOLS_005: Compliance Score must align with Risk Assessment
        risk_level = self.sections.get("AI_ACT_RISK_LEVEL", "").lower()
        has_compliance_risk = "compliance-4" in ki_stack_html or "compliance-5" in ki_stack_html or "compliance-risk" in ki_stack_html

        if risk_level == "high-risk" and has_compliance_risk:
            self.report.add_issue(ConsistencyIssue(
                rule_id="TOOLS_005",
                severity="ERROR",
                domain="tools",
                source_section="ki_stack_summary",
                target_section="ai_act",
                message="Tools mit Compliance-Risiko bei High-Risk AI Act Klassifikation",
                expected="EU-konforme Tools für High-Risk Anwendungen",
                actual="Tools mit Compliance-Warnung in High-Risk Kontext",
                suggestion="Ersetze riskante Tools durch EU-konforme Alternativen",
            ))

        # Rule TOOLS_006: Fit Level must match size recommendation
        # Check if tools for wrong size are recommended
        wrong_fit_indicators = []

        if size_label == "solo":
            # Solo should not have enterprise/complex tools
            if "complexity-4" in ki_stack_html or "complexity-5" in ki_stack_html:
                wrong_fit_indicators.append("komplexe Enterprise-Tools")
            if "cost-level-5" in ki_stack_html:
                wrong_fit_indicators.append("Enterprise-Preisklasse")

        if wrong_fit_indicators:
            self.report.add_issue(ConsistencyIssue(
                rule_id="TOOLS_006",
                severity="WARNING",
                domain="tools",
                source_section="ki_stack_summary",
                target_section="roadmap",
                message=f"Tool-Empfehlungen passen nicht zur Unternehmensgröße ({size_label})",
                expected=f"Tools mit hohem Fit für {size_label}",
                actual=f"Gefunden: {', '.join(wrong_fit_indicators)}",
                suggestion=f"Wähle Tools mit besserer Eignung für {size_label}-Unternehmen",
            ))

    # -------------------------------------------------------------------------
    # DOMAIN 2: Funding Consistency
    # -------------------------------------------------------------------------

    def _check_funding_consistency(self) -> None:
        """Check funding programs are consistent across sections."""
        self.report.checked_rules += 2

        ki_stack_html = self.sections.get("KI_STACK_SUMMARY_HTML", "")
        funding_html = self.sections.get("FOERDERPOTENZIAL_HTML", "") or self.sections.get("FOERDERPROGRAMME_HTML", "")

        if not ki_stack_html or not funding_html:
            log.debug("[G22] Funding consistency: Skipping (missing sections)")
            return

        ki_stack_programs = _extract_funding_programs(ki_stack_html)
        full_programs = _extract_funding_programs(funding_html)

        # Rule FUNDING_001: KI-Stack funding must appear in funding section
        if ki_stack_programs:
            missing_programs = [p for p in ki_stack_programs if p not in full_programs and
                              not any(p.lower() in fp.lower() for fp in full_programs)]

            if missing_programs:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="FUNDING_001",
                    severity="WARNING",
                    domain="funding",
                    source_section="ki_stack_summary",
                    target_section="foerderpotenzial",
                    message="KI-Stack enthält Förderprogramme, die nicht in der Förder-Section erscheinen",
                    expected="Förderprogramme aus KI-Stack in Förder-Section vorhanden",
                    actual=f"Fehlend: {', '.join(missing_programs[:2])}",
                    suggestion="Synchronisiere Förder-Empfehlungen zwischen Sections",
                ))

        # Rule FUNDING_002: Check company size eligibility
        size = self.briefing.get("unternehmensgroesse", "").lower()
        if size == "solo" and any("kmu" in p.lower() or "mittel" in p.lower() for p in ki_stack_programs):
            self.report.add_issue(ConsistencyIssue(
                rule_id="FUNDING_002",
                severity="WARNING",
                domain="funding",
                source_section="ki_stack_summary",
                target_section="ki_stack_summary",
                message="Förderprogramme für KMU bei Solo-Unternehmen empfohlen",
                expected="Solo-geeignete Förderprogramme",
                actual="KMU-spezifische Programme empfohlen",
                suggestion="Prüfe Förder-Eligibility für Unternehmensgrße",
            ))

        # G26: Additional Funding Engine V2 rules
        self._check_funding_v2_consistency(ki_stack_html, funding_html)

    def _check_funding_v2_consistency(self, ki_stack_html: str, funding_html: str) -> None:
        """G26: Check Funding Engine V2 consistency rules."""
        self.report.checked_rules += 5

        size = self.briefing.get("unternehmensgroesse", "").lower()
        size_label = "solo" if "solo" in size or "freiberuf" in size else (
            "team" if "team" in size or "klein" in size else "kmu"
        )
        region = self.briefing.get("bundesland", "").upper()

        # Get funding matrix HTML if available
        funding_matrix_html = self.sections.get("FUNDING_MATRIX_2025_HTML", "")
        combined_html = funding_html + funding_matrix_html

        # Rule FUNDING_003: Year badges must be present in multi-year matrix
        if funding_matrix_html:
            has_year_badges = any(f"year-{y}" in funding_matrix_html or f"{y}</span>" in funding_matrix_html
                                  for y in [2025, 2026, 2027])

            if not has_year_badges:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="FUNDING_003",
                    severity="WARNING",
                    domain="funding",
                    source_section="funding_matrix_2025",
                    target_section="funding_matrix_2025",
                    message="Fördermatrix enthält keine Jahr-Badges (2025/2026/2027)",
                    expected="Jahr-Badges für Multi-Jahres-Ansicht",
                    actual="Keine Jahr-Badges gefunden",
                    suggestion="Füge Jahr-Badges zur Fördermatrix hinzu (G26)",
                ))

        # Rule FUNDING_004: Level badges must be consistent (EU/Bund/Land)
        if funding_matrix_html:
            has_level_badges = any(level in funding_matrix_html.lower()
                                   for level in ["level-eu", "level-federal", "level-state", "bund", "land"])

            if not has_level_badges and len(funding_matrix_html) > 200:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="FUNDING_004",
                    severity="INFO",
                    domain="funding",
                    source_section="funding_matrix_2025",
                    target_section="funding_matrix_2025",
                    message="Fördermatrix enthält keine Ebenen-Badges (EU/Bund/Land)",
                    expected="Ebenen-Klassifikation für Programme",
                    actual="Keine Ebenen-Badges gefunden",
                    suggestion="Füge Ebenen-Badges zur Fördermatrix hinzu",
                ))

        # Rule FUNDING_005: Regional funding must match Bundesland
        if region and len(region) == 2:
            # Check for regional programmes that don't match
            regional_markers = {
                "BY": ["bayern", "bayerisch", "freistaat"],
                "NW": ["nrw", "nordrhein", "westfalen"],
                "BW": ["baden", "württemberg"],
                "BE": ["berlin"],
                "HE": ["hessen", "hessisch"],
                "SN": ["sachsen", "sächsisch"],
                "NI": ["niedersachsen"],
                "HH": ["hamburg"],
            }

            other_regions = {r: markers for r, markers in regional_markers.items() if r != region}
            funding_lower = combined_html.lower()

            wrong_region_found = []
            for other_region, markers in other_regions.items():
                if any(m in funding_lower for m in markers):
                    # Check it's actually a programme recommendation, not just mention
                    for m in markers:
                        if f"programm" in funding_lower and m in funding_lower:
                            wrong_region_found.append(other_region)
                            break

            if wrong_region_found:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="FUNDING_005",
                    severity="WARNING",
                    domain="funding",
                    source_section="funding_matrix_2025",
                    target_section="foerderpotenzial",
                    message=f"Landesspezifische Programme aus anderen Bundesländern empfohlen",
                    expected=f"Nur Programme für Region {region}",
                    actual=f"Programme aus: {', '.join(wrong_region_found[:2])}",
                    suggestion=f"Filtere Förderprogramme nach Bundesland {region}",
                ))

        # Rule FUNDING_006: Deadline urgency must be highlighted
        if funding_matrix_html:
            # Check for 2025 programmes without urgency indicators
            has_2025_deadline = "2025" in funding_matrix_html
            has_urgency = any(term in funding_matrix_html.lower()
                              for term in ["urgent", "dringend", "auslauf", "bald", "schnell"])

            if has_2025_deadline and not has_urgency:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="FUNDING_006",
                    severity="INFO",
                    domain="funding",
                    source_section="funding_matrix_2025",
                    target_section="funding_matrix_2025",
                    message="2025-Programme ohne Dringlichkeits-Hinweis",
                    expected="Dringlichkeits-Indikator für auslaufende Programme",
                    actual="Keine Dringlichkeits-Hinweise gefunden",
                    suggestion="Füge Dringlichkeits-Badges für 2025-Programme hinzu",
                ))

        # Rule FUNDING_007: Fit scores must align with company size
        if funding_matrix_html:
            # Check for mismatched fit indicators
            mismatched_fit = False

            if size_label == "solo":
                # Solo should not have programmes with low solo fit
                if "fit_solo: 0.2" in funding_matrix_html or "fit_solo: 0.3" in funding_matrix_html:
                    mismatched_fit = True
            elif size_label == "kmu":
                # KMU should not have programmes with low KMU fit
                if "fit_kmu: 0.2" in funding_matrix_html or "fit_kmu: 0.3" in funding_matrix_html:
                    mismatched_fit = True

            # Also check for size badges in HTML
            if size_label == "solo" and any(term in funding_matrix_html.lower()
                                            for term in ["nur kmu", "ab 10 mitarbeiter", "> 10 ma"]):
                mismatched_fit = True

            if mismatched_fit:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="FUNDING_007",
                    severity="WARNING",
                    domain="funding",
                    source_section="funding_matrix_2025",
                    target_section="briefing",
                    message=f"Förderprogramme mit niedrigem Fit für {size_label} empfohlen",
                    expected=f"Programme mit hohem Fit für {size_label}",
                    actual=f"Programme mit niedrigem Size-Fit gefunden",
                    suggestion=f"Priorisiere Programme mit hohem fit_{size_label} Score",
                ))

    # -------------------------------------------------------------------------
    # DOMAIN 3: KPI Consistency
    # -------------------------------------------------------------------------

    def _check_kpi_consistency(self) -> None:
        """Check KPI values are consistent across sections."""
        self.report.checked_rules += 4

        # Extract KPIs from various sections
        ki_stack_kpis = _extract_kpis(self.sections.get("KI_STACK_SUMMARY_HTML", ""))
        bc_kpis = _extract_kpis(self.sections.get("BUSINESS_CASE_HTML", ""))
        exec_kpis = _extract_kpis(self.sections.get("EXECUTIVE_SUMMARY_HTML", ""))

        # Also check briefing-level KPIs
        briefing_roi = self.briefing.get("ROI_12M")
        briefing_payback = self.briefing.get("PAYBACK_MONTHS")

        # Rule KPI_001: ROI consistency
        roi_values = [
            ("ki_stack_summary", ki_stack_kpis.get("roi")),
            ("business_case", bc_kpis.get("roi")),
            ("executive_summary", exec_kpis.get("roi")),
            ("briefing", briefing_roi if isinstance(briefing_roi, (int, float)) else None),
        ]
        roi_values = [(src, val) for src, val in roi_values if val is not None]

        if len(roi_values) >= 2:
            roi_nums = [v for _, v in roi_values]
            roi_max = max(roi_nums)
            roi_min = min(roi_nums)

            if roi_max - roi_min > self.ROI_TOLERANCE_PCT:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="KPI_001",
                    severity="ERROR",
                    domain="kpi",
                    source_section=roi_values[0][0],
                    target_section=roi_values[1][0],
                    message="ROI-Werte weichen stark voneinander ab",
                    expected=f"ROI-Werte innerhalb {self.ROI_TOLERANCE_PCT}% Toleranz",
                    actual=f"Abweichung: {roi_max - roi_min:.1f}% ({roi_min:.1f}% - {roi_max:.1f}%)",
                    suggestion="Stelle sicher, dass ROI konsistent berechnet wird",
                ))

        # Rule KPI_002: Payback consistency
        payback_values = [
            ("ki_stack_summary", ki_stack_kpis.get("payback_months")),
            ("business_case", bc_kpis.get("payback_months")),
            ("briefing", briefing_payback if isinstance(briefing_payback, (int, float)) else None),
        ]
        payback_values = [(src, val) for src, val in payback_values if val is not None]

        if len(payback_values) >= 2:
            pb_nums = [v for _, v in payback_values]
            pb_max = max(pb_nums)
            pb_min = min(pb_nums)

            if pb_max - pb_min > self.PAYBACK_TOLERANCE_MONTHS:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="KPI_002",
                    severity="ERROR",
                    domain="kpi",
                    source_section=payback_values[0][0],
                    target_section=payback_values[1][0],
                    message="Payback-Zeiträume weichen stark voneinander ab",
                    expected=f"Payback innerhalb {self.PAYBACK_TOLERANCE_MONTHS} Monate Toleranz",
                    actual=f"Abweichung: {pb_max - pb_min:.1f} Monate ({pb_min:.1f} - {pb_max:.1f})",
                    suggestion="Stelle sicher, dass Payback konsistent berechnet wird",
                ))

        # Rule KPI_003: ROI-Payback logical consistency
        # High ROI should correlate with short payback
        if ki_stack_kpis.get("roi") and ki_stack_kpis.get("payback_months"):
            roi = ki_stack_kpis["roi"]
            payback = ki_stack_kpis["payback_months"]

            # Very high ROI (>200%) but long payback (>12 months) is suspicious
            if roi > 200 and payback > 12:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="KPI_003",
                    severity="WARNING",
                    domain="kpi",
                    source_section="ki_stack_summary",
                    target_section="ki_stack_summary",
                    message="ROI und Payback sind logisch inkonsistent",
                    expected="Hoher ROI sollte mit kurzem Payback korrelieren",
                    actual=f"ROI: {roi:.1f}%, Payback: {payback:.1f} Monate",
                    suggestion="Überprüfe Business Case Berechnungen",
                ))

        # Rule KPI_004: Time savings plausibility
        time_hours = ki_stack_kpis.get("time_savings_hours")
        if time_hours and time_hours > 160:  # More than full-time equivalent
            self.report.add_issue(ConsistencyIssue(
                rule_id="KPI_004",
                severity="WARNING",
                domain="kpi",
                source_section="ki_stack_summary",
                target_section="ki_stack_summary",
                message="Zeitersparnis erscheint unrealistisch hoch",
                expected="Realistische Zeitersparnis (< 160h/Monat)",
                actual=f"{time_hours:.0f} Stunden/Monat",
                suggestion="Überprüfe Quick-Wins Zeitschätzungen",
            ))

    # -------------------------------------------------------------------------
    # DOMAIN 4: Risk Level Consistency
    # -------------------------------------------------------------------------

    def _check_risk_level_consistency(self) -> None:
        """Check AI Act risk levels are consistent across sections."""
        self.report.checked_rules += 2

        ki_stack_risk = _extract_risk_level(self.sections.get("KI_STACK_SUMMARY_HTML", ""))
        ai_act_risk = _extract_risk_level(self.sections.get("AI_ACT_SUMMARY_HTML", ""))
        risks_risk = _extract_risk_level(self.sections.get("RISKS_HTML", ""))

        # Also check briefing-level risk
        briefing_risk = self.briefing.get("ai_act_risk_level")

        risk_values = [
            ("ki_stack_summary", ki_stack_risk),
            ("ai_act_summary", ai_act_risk),
            ("risks", risks_risk),
            ("briefing", briefing_risk),
        ]
        risk_values = [(src, val) for src, val in risk_values if val is not None]

        # Rule RISK_001: All sections must show same risk level
        if len(risk_values) >= 2:
            unique_risks = set(v for _, v in risk_values)

            if len(unique_risks) > 1:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="RISK_001",
                    severity="ERROR",
                    domain="risk",
                    source_section=risk_values[0][0],
                    target_section=risk_values[1][0],
                    message="AI Act Risiko-Level inkonsistent zwischen Sections",
                    expected="Einheitliches Risiko-Level in allen Sections",
                    actual=f"Verschiedene Levels gefunden: {', '.join(unique_risks)}",
                    suggestion="Synchronisiere Risiko-Einstufung aus determine_risk_level()",
                ))

        # Rule RISK_002: Risk level must match branch profile
        branch = self.briefing.get("branche", "").lower()
        high_risk_branches = ["medizin", "finanzen", "behörden", "versicherung", "healthcare", "finance"]

        if ki_stack_risk and any(b in branch for b in high_risk_branches):
            if ki_stack_risk == "low":
                self.report.add_issue(ConsistencyIssue(
                    rule_id="RISK_002",
                    severity="WARNING",
                    domain="risk",
                    source_section="ki_stack_summary",
                    target_section="ki_stack_summary",
                    message=f"Niedriges Risiko-Level für regulierte Branche '{branch}'",
                    expected="Medium oder High Risk für regulierte Branchen",
                    actual=f"Risiko: {ki_stack_risk}, Branche: {branch}",
                    suggestion="Überprüfe Branche-spezifische Risiko-Faktoren",
                ))

    # -------------------------------------------------------------------------
    # DOMAIN 5: Roadmap Alignment
    # -------------------------------------------------------------------------

    def _check_roadmap_alignment(self) -> None:
        """Check Starter-Kit steps align with Roadmap phases."""
        self.report.checked_rules += 2

        ki_stack_html = self.sections.get("KI_STACK_SUMMARY_HTML", "")
        roadmap_html = self.sections.get("ROADMAP_12M_HTML", "") or self.sections.get("PILOT_PLAN_HTML", "")

        if not ki_stack_html or not roadmap_html:
            log.debug("[G22] Roadmap alignment: Skipping (missing sections)")
            return

        starter_steps = _extract_step_count(ki_stack_html)

        # Rule ROADMAP_001: Starter-Kit should have 3 steps
        if starter_steps > 0 and starter_steps != 3:
            self.report.add_issue(ConsistencyIssue(
                rule_id="ROADMAP_001",
                severity="INFO",
                domain="roadmap",
                source_section="ki_stack_summary",
                target_section="ki_stack_summary",
                message="Starter-Kit hat nicht die erwarteten 3 Schritte",
                expected="3 Schritte (Setup → Workflow → Optimierung)",
                actual=f"{starter_steps} Schritte",
                suggestion="Standardisiere auf 3-Schritt-Format",
            ))

        # Rule ROADMAP_002: Tools mentioned in Starter-Kit should appear in Roadmap
        ki_stack_tools = _extract_tool_names(ki_stack_html)
        roadmap_tools = _extract_tool_names(roadmap_html)

        if ki_stack_tools and roadmap_tools:
            tools_in_roadmap = sum(1 for t in ki_stack_tools
                                   if t in roadmap_tools or
                                   any(t.lower() in rt.lower() for rt in roadmap_tools))

            if tools_in_roadmap < len(ki_stack_tools) * 0.5:  # Less than 50% overlap
                self.report.add_issue(ConsistencyIssue(
                    rule_id="ROADMAP_002",
                    severity="INFO",
                    domain="roadmap",
                    source_section="ki_stack_summary",
                    target_section="roadmap_12m",
                    message="KI-Stack Tools erscheinen nicht vollständig in der Roadmap",
                    expected="Alle empfohlenen Tools in Roadmap-Phasen integriert",
                    actual=f"{tools_in_roadmap}/{len(ki_stack_tools)} Tools in Roadmap erwähnt",
                    suggestion="Integriere Tool-Rollout in Roadmap-Phasen",
                ))

    # -------------------------------------------------------------------------
    # DOMAIN 6: Narrative Coherence
    # -------------------------------------------------------------------------

    def _check_narrative_coherence(self) -> None:
        """Check for contradictory statements across sections."""
        self.report.checked_rules += 3

        size = self.briefing.get("unternehmensgroesse", "").lower()

        # Rule NARR_001: Size-appropriate terminology
        size_terms: Dict[str, Tuple[List[str], List[str]]] = {
            "solo": (
                # Forbidden terms for solo
                ["team", "abteilung", "koordinator", "mitarbeiter", "angestellte"],
                # Expected terms for solo
                ["selbstständig", "einzelunternehm", "freiberuf", "persönlich", "allein"],
            ),
            "team": (
                # Forbidden terms for team (too small or too big)
                ["abteilung", "board", "vorstand", "konzern"],
                # Expected terms for team
                ["team", "kolleg", "gemeinsam", "zusammenarbeit"],
            ),
            "kmu": (
                # Forbidden terms for KMU
                ["konzern", "global", "multinational"],
                # Expected terms for KMU
                ["unternehmen", "abteilung", "management", "mitarbeiter"],
            ),
        }

        if size in size_terms:
            forbidden, expected = size_terms[size]

            # Check all major sections for forbidden terms
            for section_key in ["EXECUTIVE_SUMMARY_HTML", "KI_STACK_SUMMARY_HTML",
                               "ROADMAP_12M_HTML", "RECOMMENDATIONS_HTML"]:
                html = self.sections.get(section_key, "")
                if not html:
                    continue

                text_lower = _strip_html(html).lower()

                found_forbidden = [term for term in forbidden if term in text_lower]
                if found_forbidden:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="NARR_001",
                        severity="WARNING",
                        domain="narrative",
                        source_section=section_key.lower().replace("_html", ""),
                        target_section=section_key.lower().replace("_html", ""),
                        message=f"Unpassende Terminologie für Unternehmensgröße '{size}'",
                        expected=f"Größen-angepasste Sprache für {size}",
                        actual=f"Gefunden: {', '.join(found_forbidden[:3])}",
                        suggestion=f"Ersetze durch {size}-geeignete Begriffe",
                    ))
                    break  # Only report once per section type

        # Rule NARR_002: Positive/negative consistency
        exec_html = self.sections.get("EXECUTIVE_SUMMARY_HTML", "")
        risks_html = self.sections.get("RISKS_HTML", "")

        if exec_html and risks_html:
            exec_text = _strip_html(exec_html).lower()

            # Check for overly optimistic exec summary with severe risks
            optimistic_terms = ["hervorragend", "optimal", "perfekt", "ideal", "excellent", "outstanding"]
            severe_risk_terms = ["kritisch", "gravierend", "existenzbedrohend", "schwerwiegend", "critical"]

            exec_optimistic = any(term in exec_text for term in optimistic_terms)
            risks_text = _strip_html(risks_html).lower()
            risks_severe = any(term in risks_text for term in severe_risk_terms)

            if exec_optimistic and risks_severe:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="NARR_002",
                    severity="WARNING",
                    domain="narrative",
                    source_section="executive_summary",
                    target_section="risks",
                    message="Executive Summary zu optimistisch angesichts kritischer Risiken",
                    expected="Ausgewogene Darstellung von Chancen und Risiken",
                    actual="Sehr positive Exec Summary, aber kritische Risiken identifiziert",
                    suggestion="Passe Tonalität der Exec Summary an Risiko-Profil an",
                ))

        # Rule NARR_003: Branch consistency
        branch = self.briefing.get("branche", "")
        if branch:
            branch_mentioned = False
            for section_key in ["EXECUTIVE_SUMMARY_HTML", "UNTERNEHMENSPROFIL_MARKT_HTML"]:
                html = self.sections.get(section_key, "")
                if html and branch.lower() in _strip_html(html).lower():
                    branch_mentioned = True
                    break

            if not branch_mentioned:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="NARR_003",
                    severity="INFO",
                    domain="narrative",
                    source_section="executive_summary",
                    target_section="unternehmensprofil_markt",
                    message="Branche wird in Schlüssel-Sections nicht explizit erwähnt",
                    expected=f"Branche '{branch}' in Exec Summary oder Profil erwähnt",
                    actual="Branche nicht gefunden",
                    suggestion="Füge Branchen-Kontext in relevante Sections ein",
                ))

    # -------------------------------------------------------------------------
    # DOMAIN 7: Executive Snapshot Consistency (G27)
    # -------------------------------------------------------------------------

    def _check_exec_snapshot_consistency(self) -> None:
        """G27: Check Executive Snapshot consistency with other sections."""
        snapshot_html = self.sections.get("EXEC_SNAPSHOT_HTML", "")

        if not snapshot_html:
            log.debug("[G27] Exec Snapshot consistency: Skipping (no snapshot)")
            return

        self.report.checked_rules += 5

        # Rule SNAPSHOT_001: KPIs must match Business Case
        bc_html = self.sections.get("BUSINESS_CASE_HTML", "")
        if bc_html and snapshot_html:
            # Extract ROI from both
            import re
            snapshot_roi_match = re.search(r'(\d+(?:[.,]\d+)?)\s*%', snapshot_html)
            bc_roi_match = re.search(r'ROI[:\s]*(\d+(?:[.,]\d+)?)\s*%', bc_html, re.IGNORECASE)

            if snapshot_roi_match and bc_roi_match:
                snapshot_roi = float(snapshot_roi_match.group(1).replace(",", "."))
                bc_roi = float(bc_roi_match.group(1).replace(",", "."))

                if abs(snapshot_roi - bc_roi) > 20:  # More than 20% deviation
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="SNAPSHOT_001",
                        severity="ERROR",
                        domain="snapshot",
                        source_section="exec_snapshot",
                        target_section="business_case",
                        message="Snapshot ROI weicht stark vom Business Case ab",
                        expected=f"ROI ~{bc_roi:.0f}% (wie Business Case)",
                        actual=f"Snapshot zeigt {snapshot_roi:.0f}%",
                        suggestion="Synchronisiere KPI-Werte zwischen Snapshot und Business Case",
                    ))

        # Rule SNAPSHOT_002: Tools must match Tools Engine 4.0
        ki_stack_html = self.sections.get("KI_STACK_SUMMARY_HTML", "")
        if ki_stack_html and snapshot_html:
            ki_stack_tools = _extract_tool_names(ki_stack_html)
            snapshot_tools = _extract_tool_names(snapshot_html)

            if ki_stack_tools and snapshot_tools:
                # Check if snapshot tools are subset of ki_stack tools
                mismatched = [t for t in snapshot_tools
                              if not any(t.lower() in kt.lower() or kt.lower() in t.lower()
                                        for kt in ki_stack_tools)]

                if len(mismatched) > len(snapshot_tools) * 0.5:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="SNAPSHOT_002",
                        severity="WARNING",
                        domain="snapshot",
                        source_section="exec_snapshot",
                        target_section="ki_stack_summary",
                        message="Snapshot Tools stimmen nicht mit KI-Stack überein",
                        expected="Tools aus KI-Stack Summary",
                        actual=f"Abweichende Tools: {', '.join(mismatched[:2])}",
                        suggestion="Verwende Tools aus Tools Engine 4.0",
                    ))

        # Rule SNAPSHOT_003: Funding must match Funding Engine 2.0
        funding_html = self.sections.get("FUNDING_MATRIX_2025_HTML", "") or self.sections.get("FOERDERPOTENZIAL_HTML", "")
        if funding_html and snapshot_html:
            funding_progs = _extract_funding_programs(funding_html)
            snapshot_progs = _extract_funding_programs(snapshot_html)

            if snapshot_progs and funding_progs:
                mismatched = [p for p in snapshot_progs
                              if not any(p.lower() in fp.lower() or fp.lower() in p.lower()
                                        for fp in funding_progs)]

                if mismatched:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="SNAPSHOT_003",
                        severity="WARNING",
                        domain="snapshot",
                        source_section="exec_snapshot",
                        target_section="funding_matrix",
                        message="Snapshot Förderprogramme stimmen nicht mit Matrix überein",
                        expected="Programme aus Funding Engine 2.0",
                        actual=f"Unbekannte Programme: {', '.join(mismatched[:2])}",
                        suggestion="Verwende Programme aus Funding Matrix",
                    ))

        # Rule SNAPSHOT_004: Quick Wins must not contain unsuitable tools
        size = self.briefing.get("unternehmensgroesse", "").lower()
        if "solo" in size and snapshot_html:
            enterprise_indicators = ["enterprise", "team-plan", "business-plan", "konzern"]
            snapshot_lower = snapshot_html.lower()

            has_enterprise = any(ind in snapshot_lower for ind in enterprise_indicators)
            if has_enterprise:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="SNAPSHOT_004",
                    severity="WARNING",
                    domain="snapshot",
                    source_section="exec_snapshot",
                    target_section="briefing",
                    message="Snapshot enthält Enterprise-Tools für Solo-Unternehmer",
                    expected="Solo-geeignete Quick Wins",
                    actual="Enterprise-Tools in Snapshot gefunden",
                    suggestion="Wähle Solo-freundliche Alternativen",
                ))

        # Rule SNAPSHOT_005: Risk level must be consistent
        ai_act_risk = self.sections.get("AI_ACT_RISK_LEVEL", "").lower()
        snapshot_lower = snapshot_html.lower()

        if ai_act_risk == "high-risk" and "minimal" in snapshot_lower and "risk" in snapshot_lower:
            self.report.add_issue(ConsistencyIssue(
                rule_id="SNAPSHOT_005",
                severity="ERROR",
                domain="snapshot",
                source_section="exec_snapshot",
                target_section="ai_act",
                message="Snapshot zeigt 'minimal risk' obwohl AI Act High-Risk klassifiziert",
                expected="Konsistente Risiko-Darstellung",
                actual="Widersprüchliche Risiko-Level",
                suggestion="Synchronisiere Risiko-Level mit AI Act Analyse",
            ))

    # -------------------------------------------------------------------------
    # DOMAIN 8: Risk Engine V2 Consistency (G29)
    # -------------------------------------------------------------------------

    def _check_risk_engine_consistency(self) -> None:
        """
        G29: Check Risk Engine V2 consistency with other sections and engines.

        Rules:
        - RISK_001: AI Act class must be consistent with existing risk labels
        - RISK_002: Vendor risk score must not be lower than Tools Engine vendor_risk
        - RISK_003: High compliance score tools must be mentioned as risk
        - RISK_004: High DSGVO risk → Strategy must have mitigation plans
        - RISK_005: High-Risk AI Act → Strategy must reflect required controls
        - RISK_006: Consolidated score must be consistent with Strategy Plan
        """
        risk_engine_html = self.sections.get("RISK_ENGINE_HTML", "")

        if not risk_engine_html:
            log.debug("[G29] Risk Engine consistency: Skipping (no risk engine section)")
            return

        self.report.checked_rules += 6

        # Extract data from Risk Engine HTML
        risk_html_lower = risk_engine_html.lower()

        # Rule RISK_001: AI Act class consistency
        # Check if AI Act class in Risk Engine matches existing labels
        existing_ai_act = _extract_risk_level(self.sections.get("AI_ACT_SUMMARY_HTML", ""))
        ki_stack_risk = _extract_risk_level(self.sections.get("KI_STACK_SUMMARY_HTML", ""))

        # Extract AI Act class from Risk Engine HTML
        risk_engine_ai_act = None
        if "hochrisiko" in risk_html_lower or "high_risk" in risk_html_lower or "high-risk" in risk_html_lower:
            risk_engine_ai_act = "high"
        elif "limited" in risk_html_lower or "begrenzt" in risk_html_lower:
            risk_engine_ai_act = "medium"
        elif "minimal" in risk_html_lower and "risiko" in risk_html_lower:
            risk_engine_ai_act = "low"

        # Compare with existing classifications
        if risk_engine_ai_act and existing_ai_act:
            if risk_engine_ai_act != existing_ai_act:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="RISK_001",
                    severity="ERROR",
                    domain="risk_engine",
                    source_section="risk_engine",
                    target_section="ai_act_summary",
                    message="AI Act Klassifizierung im Risk Report inkonsistent mit AI Act Summary",
                    expected=f"AI Act Level: {existing_ai_act}",
                    actual=f"Risk Engine zeigt: {risk_engine_ai_act}",
                    suggestion="Synchronisiere AI Act Klassifizierung zwischen Sections",
                ))

        # Rule RISK_002: Vendor Risk Score consistency
        # Extract vendor risk from Tools Engine
        tools_html = self.sections.get("KI_STACK_SUMMARY_HTML", "") or self.sections.get("TOOLS_HTML", "")
        tools_vendor_risk = self._extract_tools_vendor_risk(tools_html)

        # Extract vendor risk from Risk Engine
        risk_vendor_score = self._extract_vendor_score_from_risk_engine(risk_engine_html)

        if tools_vendor_risk and risk_vendor_score:
            if risk_vendor_score < tools_vendor_risk:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="RISK_002",
                    severity="ERROR",
                    domain="risk_engine",
                    source_section="risk_engine",
                    target_section="tools_engine",
                    message="Vendor Risk Score im Risk Report niedriger als in Tools Engine",
                    expected=f"Vendor Risk >= {tools_vendor_risk}",
                    actual=f"Risk Engine zeigt: {risk_vendor_score}",
                    suggestion="Vendor Risk Score muss mindestens dem Tools Engine Wert entsprechen",
                ))

        # Rule RISK_003: High compliance tools must be in risk report
        high_compliance_tools = self._extract_high_compliance_tools(tools_html)

        if high_compliance_tools:
            missing_tools = []
            for tool_name in high_compliance_tools:
                if tool_name.lower() not in risk_html_lower:
                    missing_tools.append(tool_name)

            if missing_tools:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="RISK_003",
                    severity="WARNING",
                    domain="risk_engine",
                    source_section="tools_engine",
                    target_section="risk_engine",
                    message="Tools mit hohem Compliance-Score fehlen im Risk Report",
                    expected="Compliance-kritische Tools als Risiko erwähnt",
                    actual=f"Fehlend: {', '.join(missing_tools[:3])}",
                    suggestion="Erwähne Tools mit Compliance-Score >= 4 im Risk Report",
                ))

        # Rule RISK_004: High DSGVO risk → Strategy needs mitigation
        dsgvo_high = "hoch" in risk_html_lower and ("dsgvo" in risk_html_lower or "datenschutz" in risk_html_lower)

        strategy_html = self.sections.get("STRATEGY_PLAN_HTML", "") or self.sections.get("ROADMAP_12M_HTML", "")

        if dsgvo_high and strategy_html:
            strategy_lower = strategy_html.lower()
            has_mitigation = any(term in strategy_lower for term in [
                "datenschutz", "dsgvo", "privacy", "mitigation", "schutzmaßnahme",
                "einwilligung", "consent", "anonymisierung", "pseudonymisierung"
            ])

            if not has_mitigation:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="RISK_004",
                    severity="WARNING",
                    domain="risk_engine",
                    source_section="risk_engine",
                    target_section="strategy_plan",
                    message="Hohes DSGVO-Risiko ohne Mitigation-Plan im Strategy",
                    expected="Datenschutz-Maßnahmen im Strategy Plan",
                    actual="Keine DSGVO-Mitigation-Maßnahmen gefunden",
                    suggestion="Ergänze konkrete Datenschutz-Maßnahmen im Strategy Plan",
                ))

        # Rule RISK_005: High-Risk AI Act → Strategy reflects controls
        ai_act_high = ("high_risk" in risk_html_lower or "hochrisiko" in risk_html_lower or
                       "high-risk" in risk_html_lower)

        if ai_act_high and strategy_html:
            strategy_lower = strategy_html.lower()
            has_controls = any(term in strategy_lower for term in [
                "risikomanagement", "risk management", "dokumentation", "logging",
                "human oversight", "human-in-the-loop", "qualitätssicherung",
                "audit", "kontrolle", "monitoring", "ai act"
            ])

            if not has_controls:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="RISK_005",
                    severity="ERROR",
                    domain="risk_engine",
                    source_section="risk_engine",
                    target_section="strategy_plan",
                    message="High-Risk AI Act ohne erforderliche Controls im Strategy",
                    expected="AI Act Required Controls im Strategy Plan",
                    actual="Keine AI Act Control-Maßnahmen gefunden",
                    suggestion="Integriere AI Act Required Controls in den Strategy Plan",
                ))

        # Rule RISK_006: Consolidated Score consistency with Strategy
        consolidated_score = self._extract_consolidated_score(risk_engine_html)

        if consolidated_score is not None and strategy_html:
            strategy_lower = strategy_html.lower()

            # High risk score (low safety) shouldn't have "low risk" narrative
            if consolidated_score <= 40:  # Grade F or D
                low_risk_claims = any(term in strategy_lower for term in [
                    "niedriges risiko", "low risk", "minimales risiko", "minimal risk",
                    "geringes risiko", "unkritisch", "unbedenklich"
                ])

                if low_risk_claims:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="RISK_006",
                        severity="ERROR",
                        domain="risk_engine",
                        source_section="risk_engine",
                        target_section="strategy_plan",
                        message="Strategy behauptet niedriges Risiko bei hohem Risk Score",
                        expected=f"Risiko-Narrative konsistent mit Score {consolidated_score:.0f}",
                        actual="Strategy suggeriert niedrigeres Risiko als berechnet",
                        suggestion="Passe Risk-Narrative im Strategy Plan an den Score an",
                    ))

            # Low risk score (high safety) shouldn't have "high risk" warnings without context
            elif consolidated_score >= 85:  # Grade A
                high_risk_claims = any(term in strategy_lower for term in [
                    "hohes risiko", "high risk", "kritisch", "critical",
                    "erhebliches risiko", "significant risk"
                ])

                if high_risk_claims and "mitigation" not in strategy_lower and "maßnahme" not in strategy_lower:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="RISK_006",
                        severity="INFO",
                        domain="risk_engine",
                        source_section="risk_engine",
                        target_section="strategy_plan",
                        message="Strategy betont Risiken obwohl Risk Score günstig ist",
                        expected=f"Balanced Risk-Narrative für Score {consolidated_score:.0f}",
                        actual="Strategy überbetont Risiken",
                        suggestion="Balanciere Risiko-Darstellung im Strategy Plan",
                    ))

    def _extract_tools_vendor_risk(self, html: str) -> Optional[int]:
        """Extract maximum vendor risk from Tools Engine HTML."""
        if not html:
            return None

        import re

        # Look for vendor-risk badges or scores
        # Pattern: vendor-4, vendor_risk: 4, vendor risk score 4, etc.
        patterns = [
            r'vendor[\-_](\d)',
            r'vendor[\s_-]*risk[\s:]*(\d)',
            r'vendor[\s_-]*score[\s:]*(\d)',
        ]

        max_risk = None
        for pattern in patterns:
            matches = re.findall(pattern, html.lower())
            for match in matches:
                try:
                    risk = int(match)
                    if 1 <= risk <= 5:
                        if max_risk is None or risk > max_risk:
                            max_risk = risk
                except ValueError:
                    continue

        return max_risk

    def _extract_vendor_score_from_risk_engine(self, html: str) -> Optional[int]:
        """Extract vendor risk score from Risk Engine HTML."""
        if not html:
            return None

        import re

        # Look for vendor risk score patterns
        patterns = [
            r'vendor[\s_-]*risk[\s_-]*score[\s:]*(\d)',
            r'vendor[\s_-]*score[\s:]*(\d)',
            r'>(\d)/5</span>',  # Common badge format
        ]

        for pattern in patterns:
            match = re.search(pattern, html.lower())
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def _extract_high_compliance_tools(self, html: str) -> List[str]:
        """Extract tool names with high compliance scores (>=4)."""
        if not html:
            return []

        import re

        # Look for compliance-4 or compliance-5 badges near tool names
        tools: List[str] = []

        # Pattern 1: compliance badge with nearby tool name
        compliance_pattern = r'compliance-[45]'
        if re.search(compliance_pattern, html.lower()):
            # Extract tool names from same HTML
            tool_names = _extract_tool_names(html)
            # For simplicity, return first few tools as potentially high-compliance
            tools = tool_names[:3]

        return tools

    def _extract_consolidated_score(self, html: str) -> Optional[float]:
        """Extract consolidated score from Risk Engine HTML."""
        if not html:
            return None

        import re

        # Look for score patterns like "Score: 75" or large numbers in score context
        patterns = [
            r'score[\s:]*(\d+(?:\.\d+)?)',
            r'>(\d{2,3})</p>',  # Large numbers in paragraphs
            r'sicherheits[\s-]*score[\s:]*(\d+)',
            r'safety[\s-]*score[\s:]*(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html.lower())
            if match:
                try:
                    score = float(match.group(1))
                    if 0 <= score <= 100:
                        return score
                except ValueError:
                    continue

        return None

    # -------------------------------------------------------------------------
    # DOMAIN 9: Business Case Engine V2 Consistency (G30)
    # -------------------------------------------------------------------------

    def _check_business_case_consistency(self) -> None:
        """
        G30: Check Business Case Engine V2 consistency with other sections.

        Rules:
        - BC_001: Scenario ordering (optimistic >= realistic >= conservative)
        - BC_002: ROI matches existing KPI calculations from briefing/KI-Stack
        - BC_003: Investment aligns with Tools Engine cost estimates
        - BC_004: Savings align with time savings baseline
        - BC_005: Funding effect matches Funding Engine
        """
        bc_html = self.sections.get("BUSINESS_CASE_ENGINE_HTML", "")

        if not bc_html:
            log.debug("[G30] Business Case consistency: Skipping (no business case section)")
            return

        self.report.checked_rules += 5

        bc_html_lower = bc_html.lower()

        # Rule BC_001: Scenario ordering consistency
        # Extract ROI values from scenarios
        scenario_rois = self._extract_scenario_rois(bc_html)

        if scenario_rois:
            opt_roi = scenario_rois.get("optimistic", 0)
            real_roi = scenario_rois.get("realistic", 0)
            cons_roi = scenario_rois.get("conservative", 0)

            # Check ordering: optimistic >= realistic >= conservative
            if opt_roi < real_roi:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="BC_001",
                    severity="ERROR",
                    domain="business_case",
                    source_section="business_case_engine",
                    target_section="business_case_engine",
                    message="Szenario-Reihenfolge inkonsistent: Optimistic ROI < Realistic ROI",
                    expected=f"Optimistic ROI >= Realistic ROI",
                    actual=f"Optimistic: {opt_roi:.1f}%, Realistic: {real_roi:.1f}%",
                    suggestion="Korrigiere Szenario-Werte, sodass optimistic >= realistic >= conservative",
                ))

            if real_roi < cons_roi:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="BC_001",
                    severity="ERROR",
                    domain="business_case",
                    source_section="business_case_engine",
                    target_section="business_case_engine",
                    message="Szenario-Reihenfolge inkonsistent: Realistic ROI < Conservative ROI",
                    expected=f"Realistic ROI >= Conservative ROI",
                    actual=f"Realistic: {real_roi:.1f}%, Conservative: {cons_roi:.1f}%",
                    suggestion="Korrigiere Szenario-Werte, sodass optimistic >= realistic >= conservative",
                ))

        # Rule BC_002: ROI matches existing KPI calculations
        briefing_roi = self.briefing.get("ROI_12M")
        ki_stack_kpis = _extract_kpis(self.sections.get("KI_STACK_SUMMARY_HTML", ""))
        ki_stack_roi = ki_stack_kpis.get("roi")

        bc_realistic_roi = scenario_rois.get("realistic") if scenario_rois else None

        if bc_realistic_roi is not None:
            reference_roi = None
            reference_source = None

            if ki_stack_roi is not None:
                reference_roi = ki_stack_roi
                reference_source = "KI-Stack Summary"
            elif briefing_roi is not None:
                try:
                    reference_roi = float(briefing_roi)
                    reference_source = "Briefing"
                except (ValueError, TypeError):
                    pass

            if reference_roi is not None:
                # Allow 25% tolerance
                roi_diff = abs(bc_realistic_roi - reference_roi)
                tolerance = max(25, abs(reference_roi) * 0.25)

                if roi_diff > tolerance:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="BC_002",
                        severity="WARNING",
                        domain="business_case",
                        source_section="business_case_engine",
                        target_section="ki_stack_summary",
                        message=f"Business Case ROI weicht von {reference_source} ab",
                        expected=f"ROI ~{reference_roi:.1f}% (aus {reference_source})",
                        actual=f"Business Case Realistic ROI: {bc_realistic_roi:.1f}%",
                        suggestion="Überprüfe ROI-Berechnung in Business Case Engine",
                    ))

        # Rule BC_003: Investment aligns with Tools Engine cost estimates
        tools_html = self.sections.get("KI_STACK_SUMMARY_HTML", "") or self.sections.get("TOOLS_HTML", "")
        bc_investment = self._extract_investment_from_bc(bc_html)
        tools_cost_estimate = self._estimate_tools_cost(tools_html)

        if bc_investment is not None and tools_cost_estimate is not None:
            # Investment should be reasonably close to tools cost (within 3x)
            if bc_investment > 0 and tools_cost_estimate > 0:
                ratio = bc_investment / tools_cost_estimate

                if ratio > 5:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="BC_003",
                        severity="WARNING",
                        domain="business_case",
                        source_section="business_case_engine",
                        target_section="tools_engine",
                        message="Business Case Investment deutlich höher als Tools-Kosten",
                        expected=f"Investment nahe Tools-Schätzung (~{tools_cost_estimate:.0f}€)",
                        actual=f"BC Investment: {bc_investment:.0f}€ ({ratio:.1f}x Tools-Kosten)",
                        suggestion="Prüfe, ob alle Investment-Komponenten berechtigt sind",
                    ))
                elif ratio < 0.3:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="BC_003",
                        severity="INFO",
                        domain="business_case",
                        source_section="business_case_engine",
                        target_section="tools_engine",
                        message="Business Case Investment niedriger als Tools-Kosten",
                        expected=f"Investment >= Tools-Schätzung (~{tools_cost_estimate:.0f}€)",
                        actual=f"BC Investment: {bc_investment:.0f}€",
                        suggestion="Prüfe, ob alle Tool-Kosten im Investment berücksichtigt sind",
                    ))

        # Rule BC_004: Savings align with time savings baseline
        briefing_hours = self.briefing.get("EINSPARUNG_STUNDEN_MONAT")
        briefing_savings = self.briefing.get("EINSPARUNG_MONAT_EUR")
        bc_savings = self._extract_monthly_savings_from_bc(bc_html)

        if bc_savings is not None and bc_savings > 0:
            expected_savings = None

            if briefing_savings:
                try:
                    expected_savings = float(briefing_savings)
                except (ValueError, TypeError):
                    pass
            elif briefing_hours:
                try:
                    hours = float(briefing_hours)
                    # Estimate at 50€/hour
                    expected_savings = hours * 50
                except (ValueError, TypeError):
                    pass

            if expected_savings is not None and expected_savings > 0:
                savings_ratio = bc_savings / expected_savings

                if savings_ratio > 3:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="BC_004",
                        severity="WARNING",
                        domain="business_case",
                        source_section="business_case_engine",
                        target_section="briefing",
                        message="Business Case Ersparnis deutlich höher als Baseline",
                        expected=f"Monatl. Ersparnis ~{expected_savings:.0f}€ (aus Briefing)",
                        actual=f"BC Ersparnis: {bc_savings:.0f}€ ({savings_ratio:.1f}x Baseline)",
                        suggestion="Überprüfe Ersparnis-Annahmen im Business Case",
                    ))
                elif savings_ratio < 0.3:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="BC_004",
                        severity="INFO",
                        domain="business_case",
                        source_section="business_case_engine",
                        target_section="briefing",
                        message="Business Case Ersparnis niedriger als Baseline",
                        expected=f"Monatl. Ersparnis ~{expected_savings:.0f}€ (aus Briefing)",
                        actual=f"BC Ersparnis: {bc_savings:.0f}€",
                        suggestion="Prüfe, ob Einspar-Potenzial vollständig erfasst ist",
                    ))

        # Rule BC_005: Funding effect matches Funding Engine
        funding_html = self.sections.get("FUNDING_MATRIX_2025_HTML", "") or self.sections.get("FOERDERPOTENZIAL_HTML", "")
        bc_funding_effect = self._extract_funding_effect_from_bc(bc_html)

        if bc_funding_effect is not None and bc_funding_effect > 0:
            # Check if funding section mentions any programs
            has_funding_programs = bool(_extract_funding_programs(funding_html))

            if not has_funding_programs:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="BC_005",
                    severity="WARNING",
                    domain="business_case",
                    source_section="business_case_engine",
                    target_section="funding_engine",
                    message="Business Case enthält Fördereffekt ohne passende Förderprogramme",
                    expected="Fördereffekt basiert auf identifizierten Programmen",
                    actual=f"Fördereffekt: {bc_funding_effect:.0f}€, keine Programme gefunden",
                    suggestion="Verknüpfe Fördereffekt mit konkreten Programmen aus Funding Engine",
                ))

            # Check if funding effect is unrealistically high
            if bc_investment is not None and bc_funding_effect > bc_investment * 0.8:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="BC_005",
                    severity="WARNING",
                    domain="business_case",
                    source_section="business_case_engine",
                    target_section="funding_engine",
                    message="Fördereffekt unrealistisch hoch (>80% des Investments)",
                    expected="Fördereffekt max. 50-70% des Investments",
                    actual=f"Fördereffekt: {bc_funding_effect:.0f}€ bei {bc_investment:.0f}€ Investment",
                    suggestion="Überprüfe Förder-Berechnungen auf Plausibilität",
                ))

    def _extract_scenario_rois(self, html: str) -> Dict[str, float]:
        """Extract ROI values for each scenario from Business Case HTML."""
        if not html:
            return {}

        rois: Dict[str, float] = {}

        # Pattern: scenario name followed by ROI value
        import re

        # Look for scenario cards/sections with ROI
        scenarios = ["optimistic", "optimistisch", "realistic", "realistisch", "conservative", "konservativ"]

        for scenario in scenarios:
            # Normalize to English
            normalized = scenario
            if scenario == "optimistisch":
                normalized = "optimistic"
            elif scenario == "realistisch":
                normalized = "realistic"
            elif scenario == "konservativ":
                normalized = "conservative"

            # Look for ROI near scenario name
            pattern = rf'{scenario}[^<]*?(\d+(?:[.,]\d+)?)\s*%'
            match = re.search(pattern, html.lower())
            if match:
                try:
                    rois[normalized] = float(match.group(1).replace(",", "."))
                except ValueError:
                    pass

        return rois

    def _extract_investment_from_bc(self, html: str) -> Optional[float]:
        """Extract total investment from Business Case HTML."""
        if not html:
            return None

        import re

        patterns = [
            r'investment[:\s]*(\d+(?:[.,]\d+)?)\s*€',
            r'(\d+(?:[.,]\d+)?)\s*€\s*(?:investment|invest)',
            r'investition[:\s]*(\d+(?:[.,]\d+)?)\s*€',
            r'gesamt[:\s]*(\d+(?:[.,]\d+)?)\s*€',
        ]

        for pattern in patterns:
            match = re.search(pattern, html.lower())
            if match:
                try:
                    value = match.group(1).replace(".", "").replace(",", ".")
                    return float(value)
                except ValueError:
                    continue

        return None

    def _extract_monthly_savings_from_bc(self, html: str) -> Optional[float]:
        """Extract monthly savings from Business Case HTML."""
        if not html:
            return None

        import re

        patterns = [
            r'monatl[^<]*?(\d+(?:[.,]\d+)?)\s*€',
            r'monthly[^<]*?(\d+(?:[.,]\d+)?)\s*€',
            r'ersparnis[^<]*?(\d+(?:[.,]\d+)?)\s*€',
            r'savings[^<]*?(\d+(?:[.,]\d+)?)\s*€',
        ]

        for pattern in patterns:
            match = re.search(pattern, html.lower())
            if match:
                try:
                    value = match.group(1).replace(".", "").replace(",", ".")
                    return float(value)
                except ValueError:
                    continue

        return None

    def _extract_funding_effect_from_bc(self, html: str) -> Optional[float]:
        """Extract funding effect from Business Case HTML."""
        if not html:
            return None

        import re

        patterns = [
            r'förder[^<]*?(\d+(?:[.,]\d+)?)\s*€',
            r'funding[^<]*?(\d+(?:[.,]\d+)?)\s*€',
            r'zuschuss[^<]*?(\d+(?:[.,]\d+)?)\s*€',
        ]

        for pattern in patterns:
            match = re.search(pattern, html.lower())
            if match:
                try:
                    value = match.group(1).replace(".", "").replace(",", ".")
                    return float(value)
                except ValueError:
                    continue

        return None

    def _estimate_tools_cost(self, html: str) -> Optional[float]:
        """Estimate tools cost from Tools Engine HTML."""
        if not html:
            return None

        import re

        # Look for cost indicators
        cost_sum = 0.0
        found_costs = False

        # Pattern: cost-level badges
        cost_level_pattern = r'cost-level-(\d)'
        for match in re.finditer(cost_level_pattern, html.lower()):
            level = int(match.group(1))
            # Estimate: level 1=0, 2=10, 3=50, 4=150, 5=500 €/month
            cost_estimates = {1: 0, 2: 10, 3: 50, 4: 150, 5: 500}
            cost_sum += cost_estimates.get(level, 50) * 12  # Annual
            found_costs = True

        # Add setup costs (2-3 months of operating)
        if found_costs:
            return cost_sum + (cost_sum / 12) * 2.5

        # Pattern: direct EUR amounts
        eur_pattern = r'(\d+(?:[.,]\d+)?)\s*€\s*/?\s*(?:monat|month)'
        for match in re.finditer(eur_pattern, html.lower()):
            try:
                value = match.group(1).replace(".", "").replace(",", ".")
                cost_sum += float(value) * 12
                found_costs = True
            except ValueError:
                continue

        return cost_sum if found_costs else None

    # -------------------------------------------------------------------------
    # DOMAIN 10: Recommendations Engine Consistency (G32)
    # -------------------------------------------------------------------------

    def _check_recommendations_consistency(self) -> None:
        """
        G32: Check Recommendations Engine consistency with other engines.

        Rules:
        - RECO_001: Tools fit validation (fit >= 0.3 for size, no high vendor_risk)
        - RECO_002: Risk relation validation (reduces_risk must reference high/critical risks)
        - RECO_003: Funding consistency (programmes must exist in Funding Engine)
        - RECO_004: Strategy phase consistency (timeline_phase matches Strategy Plan)
        - RECO_005: Size-appropriate count (Solo: max 5, Team: max 8, KMU: max 10)
        """
        reco_html = self.sections.get("RECOMMENDATIONS_ENGINE_HTML", "")

        if not reco_html:
            log.debug("[G32] Recommendations consistency: Skipping (no recommendations section)")
            return

        self.report.checked_rules += 5

        reco_html_lower = reco_html.lower()

        # Get company size
        size = self.briefing.get("unternehmensgroesse", "").lower()
        size_label = "solo" if "solo" in size or "freiberuf" in size else (
            "team" if "team" in size or "klein" in size else "kmu"
        )

        # Rule RECO_001: Tools fit validation
        # related_tools must have fit >= 0.3 for company size, no high vendor_risk
        tools_html = self.sections.get("KI_STACK_SUMMARY_HTML", "") or self.sections.get("TOOLS_HTML", "")

        if tools_html and reco_html:
            # Extract tool names from recommendations
            reco_tools = self._extract_related_tools_from_reco(reco_html)
            tools_engine_tools = _extract_tool_names(tools_html)

            # Check if recommended tools are from Tools Engine
            invalid_tools = []
            for tool in reco_tools:
                if not any(tool.lower() in t.lower() or t.lower() in tool.lower()
                          for t in tools_engine_tools):
                    invalid_tools.append(tool)

            if invalid_tools:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="RECO_001",
                    severity="ERROR",
                    domain="recommendations",
                    source_section="recommendations_engine",
                    target_section="tools_engine",
                    message="Empfehlungen referenzieren Tools nicht aus Tools Engine",
                    expected="Nur Tools aus Tools Engine 4.0 verwenden",
                    actual=f"Unbekannte Tools: {', '.join(invalid_tools[:3])}",
                    suggestion="Verwende nur Tools, die von Tools Engine empfohlen wurden",
                ))

            # Check for tools with high vendor risk (vendor-risk >= 4)
            high_vendor_tools = self._extract_high_vendor_risk_tools(tools_html)
            risky_reco_tools = [t for t in reco_tools
                               if any(t.lower() in hvt.lower() or hvt.lower() in t.lower()
                                     for hvt in high_vendor_tools)]

            if risky_reco_tools:
                # Check if mitigation is mentioned
                has_mitigation = any(term in reco_html_lower for term in [
                    "mitigation", "risiko", "risk", "alternativ", "vorsicht"
                ])

                if not has_mitigation:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="RECO_001",
                        severity="WARNING",
                        domain="recommendations",
                        source_section="recommendations_engine",
                        target_section="tools_engine",
                        message="Empfehlungen enthalten Tools mit hohem Vendor-Risiko ohne Mitigation",
                        expected="Mitigation-Hinweis für riskante Tools",
                        actual=f"Tools mit hohem Vendor-Risk: {', '.join(risky_reco_tools[:2])}",
                        suggestion="Füge Risiko-Hinweise für Tools mit vendor_risk >= 4 hinzu",
                    ))

        # Rule RECO_002: Risk relation validation
        # If risk_relation="reduces_risk", related_risks must contain high/critical risks
        risk_html = self.sections.get("RISK_ENGINE_HTML", "") or self.sections.get("RISKS_HTML", "")

        if risk_html and reco_html:
            # Check for "reduces_risk" markers in recommendations
            has_reduces_risk = "reduces_risk" in reco_html_lower or "reduziert risiko" in reco_html_lower

            if has_reduces_risk:
                # Check if related risks reference actual high/critical risks from Risk Engine
                high_risks = self._extract_high_risks_from_engine(risk_html)
                related_risks = self._extract_related_risks_from_reco(reco_html)

                if related_risks:
                    # Check if any related risk matches a high risk
                    matching_risks = [r for r in related_risks
                                     if any(r.lower() in hr.lower() or hr.lower() in r.lower()
                                           for hr in high_risks)]

                    if not matching_risks and high_risks:
                        self.report.add_issue(ConsistencyIssue(
                            rule_id="RECO_002",
                            severity="WARNING",
                            domain="recommendations",
                            source_section="recommendations_engine",
                            target_section="risk_engine",
                            message="reduces_risk Empfehlungen referenzieren keine kritischen Risiken",
                            expected="Referenz auf high/critical Risiken aus Risk Engine",
                            actual=f"Referenzierte Risiken nicht in High-Risk Liste gefunden",
                            suggestion="Verknüpfe reduces_risk Empfehlungen mit tatsächlich kritischen Risiken",
                        ))
                elif has_reduces_risk:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="RECO_002",
                        severity="ERROR",
                        domain="recommendations",
                        source_section="recommendations_engine",
                        target_section="risk_engine",
                        message="reduces_risk Empfehlung ohne related_risks",
                        expected="Bei risk_relation='reduces_risk' mindestens 1 related_risk",
                        actual="Keine related_risks angegeben",
                        suggestion="Füge related_risks für reduces_risk Empfehlungen hinzu",
                    ))

        # Rule RECO_003: Funding consistency
        # related_funding must exist in Funding Engine
        funding_html = self.sections.get("FUNDING_MATRIX_2025_HTML", "") or self.sections.get("FOERDERPOTENZIAL_HTML", "")

        if funding_html and reco_html:
            reco_funding = self._extract_related_funding_from_reco(reco_html)
            funding_engine_programs = _extract_funding_programs(funding_html)

            if reco_funding:
                invalid_funding = []
                for prog in reco_funding:
                    if not any(prog.lower() in fp.lower() or fp.lower() in prog.lower()
                              for fp in funding_engine_programs):
                        invalid_funding.append(prog)

                if invalid_funding:
                    self.report.add_issue(ConsistencyIssue(
                        rule_id="RECO_003",
                        severity="ERROR",
                        domain="recommendations",
                        source_section="recommendations_engine",
                        target_section="funding_engine",
                        message="Empfehlungen referenzieren unbekannte Förderprogramme",
                        expected="Nur Programme aus Funding Engine V2 verwenden",
                        actual=f"Unbekannte Programme: {', '.join(invalid_funding[:2])}",
                        suggestion="Verwende nur Programme, die in Funding Engine identifiziert wurden",
                    ))

        # Rule RECO_004: Strategy phase consistency
        # timeline_phase must align with Strategy Plan
        strategy_html = self.sections.get("STRATEGY_PLAN_HTML", "") or self.sections.get("ROADMAP_12M_HTML", "")

        if strategy_html and reco_html:
            # Check for phase misalignment
            # Phase 1 recommendations should not reference Phase 3 measures
            phase_1_recos = "phase_1" in reco_html_lower or "phase 1" in reco_html_lower
            phase_3_strategy = "phase_3" in strategy_html.lower() or "phase 3" in strategy_html.lower()

            # Look for urgent measures in phase_3
            urgent_in_phase_3 = False
            if "urgency_level.*high" in reco_html_lower or "urgency.*hoch" in reco_html_lower:
                # Check if urgent items are in phase_3
                import re
                urgent_phase_3 = re.search(r'urgency[^}]*high[^}]*phase_3', reco_html_lower, re.DOTALL)
                if urgent_phase_3:
                    urgent_in_phase_3 = True

            if urgent_in_phase_3:
                self.report.add_issue(ConsistencyIssue(
                    rule_id="RECO_004",
                    severity="WARNING",
                    domain="recommendations",
                    source_section="recommendations_engine",
                    target_section="strategy_plan",
                    message="Dringende Empfehlung (urgency=high) in Phase 3",
                    expected="urgency=high sollte in Phase 1 sein",
                    actual="High-Urgency Empfehlung für Phase 3 gefunden",
                    suggestion="Verschiebe dringende Empfehlungen in frühere Phasen",
                ))

        # Rule RECO_005: Size-appropriate count
        # Solo: max 5, Team: max 8, KMU: max 10
        reco_count = self._count_recommendations(reco_html)
        high_impact_count = self._count_high_impact_recommendations(reco_html)

        size_limits = {
            "solo": (5, 2),   # max 5 total, max 2 high impact
            "team": (8, 4),   # max 8 total, max 4 high impact
            "kmu": (10, 6),   # max 10 total, max 6 high impact
        }

        max_total, max_high = size_limits.get(size_label, (10, 6))

        if reco_count > max_total:
            self.report.add_issue(ConsistencyIssue(
                rule_id="RECO_005",
                severity="ERROR",
                domain="recommendations",
                source_section="recommendations_engine",
                target_section="briefing",
                message=f"Zu viele Empfehlungen für Unternehmensgröße '{size_label}'",
                expected=f"Max. {max_total} Empfehlungen für {size_label}",
                actual=f"{reco_count} Empfehlungen gefunden",
                suggestion=f"Reduziere auf max. {max_total} Empfehlungen",
            ))

        if high_impact_count > max_high:
            self.report.add_issue(ConsistencyIssue(
                rule_id="RECO_005",
                severity="WARNING",
                domain="recommendations",
                source_section="recommendations_engine",
                target_section="briefing",
                message=f"Zu viele High-Impact Empfehlungen für '{size_label}'",
                expected=f"Max. {max_high} High-Impact Empfehlungen für {size_label}",
                actual=f"{high_impact_count} High-Impact Empfehlungen",
                suggestion=f"Reduziere High-Impact Empfehlungen auf max. {max_high}",
            ))

    def _extract_related_tools_from_reco(self, html: str) -> List[str]:
        """Extract related tools from Recommendations Engine HTML."""
        if not html:
            return []

        tools: List[str] = []

        import re

        # Pattern: related_tools: ["Tool A", "Tool B"]
        tools_pattern = r'related_tools["\s:]*\[(.*?)\]'
        matches = re.findall(tools_pattern, html, re.IGNORECASE | re.DOTALL)

        for match in matches:
            # Extract tool names from the list
            tool_names = re.findall(r'"([^"]+)"', match)
            tools.extend(tool_names)

        # Also extract from HTML list items
        li_pattern = r'<li[^>]*>([A-Za-z0-9\s\-\.]+(?:AI|GPT|Bot|Tool|Cloud|Pro|Plus)?)</li>'
        for match in re.finditer(li_pattern, html, re.IGNORECASE):
            name = match.group(1).strip()
            if len(name) > 2 and len(name) < 50:
                tools.append(name)

        return list(set(tools))

    def _extract_high_vendor_risk_tools(self, html: str) -> List[str]:
        """Extract tools with high vendor risk (>=4) from Tools Engine HTML."""
        if not html:
            return []

        tools: List[str] = []

        import re

        # Look for vendor-risk-4 or vendor-risk-5 badges
        pattern = r'vendor[\-_]risk[\-_]?[45]'

        if re.search(pattern, html.lower()):
            # Extract tool names near these badges
            tool_names = _extract_tool_names(html)
            # For simplicity, return all tools from section with high vendor risk indicators
            tools = tool_names[:5]

        return tools

    def _extract_high_risks_from_engine(self, html: str) -> List[str]:
        """Extract high/critical risk titles from Risk Engine HTML."""
        if not html:
            return []

        risks: List[str] = []

        import re

        # Look for high/critical risk indicators
        high_patterns = [
            r'(kritisch|critical|hoch|high)[\s\-]?risk[:\s]*([^<]+)',
            r'risk[:\s]*([^<]+?)[\s]*(?:kritisch|critical|hoch|high)',
            r'<strong>([^<]+)</strong>\s*(?:kritisch|critical|hoch|high)',
        ]

        for pattern in high_patterns:
            matches = re.findall(pattern, html.lower())
            for match in matches:
                if isinstance(match, tuple):
                    risk_name = match[-1].strip()
                else:
                    risk_name = match.strip()
                if len(risk_name) > 3 and len(risk_name) < 100:
                    risks.append(risk_name)

        return list(set(risks))

    def _extract_related_risks_from_reco(self, html: str) -> List[str]:
        """Extract related risks from Recommendations Engine HTML."""
        if not html:
            return []

        risks: List[str] = []

        import re

        # Pattern: related_risks: ["Risk A", "Risk B"]
        risks_pattern = r'related_risks["\s:]*\[(.*?)\]'
        matches = re.findall(risks_pattern, html, re.IGNORECASE | re.DOTALL)

        for match in matches:
            risk_names = re.findall(r'"([^"]+)"', match)
            risks.extend(risk_names)

        return list(set(risks))

    def _extract_related_funding_from_reco(self, html: str) -> List[str]:
        """Extract related funding programmes from Recommendations Engine HTML."""
        if not html:
            return []

        funding: List[str] = []

        import re

        # Pattern: related_funding: ["Programme A", "Programme B"]
        funding_pattern = r'related_funding["\s:]*\[(.*?)\]'
        matches = re.findall(funding_pattern, html, re.IGNORECASE | re.DOTALL)

        for match in matches:
            prog_names = re.findall(r'"([^"]+)"', match)
            funding.extend(prog_names)

        return list(set(funding))

    def _count_recommendations(self, html: str) -> int:
        """Count total recommendations in HTML."""
        if not html:
            return 0

        import re

        # Count recommendation cards or IDs
        patterns = [
            r'"id":\s*"rec\d+"',  # JSON ID pattern
            r'class="[^"]*recommendation-card[^"]*"',  # CSS class pattern
            r'class="[^"]*reco-card[^"]*"',  # Alternative CSS class
            r'<div[^>]*recommendation[^>]*>',  # Generic div pattern
        ]

        max_count = 0
        for pattern in patterns:
            count = len(re.findall(pattern, html, re.IGNORECASE))
            if count > max_count:
                max_count = count

        return max_count

    def _count_high_impact_recommendations(self, html: str) -> int:
        """Count high-impact recommendations in HTML."""
        if not html:
            return 0

        import re

        # Count impact_level: "high" patterns
        patterns = [
            r'"impact_level":\s*"high"',
            r'impact[\-_]?level[:\s]*high',
            r'class="[^"]*impact-high[^"]*"',
        ]

        total_count = 0
        for pattern in patterns:
            count = len(re.findall(pattern, html, re.IGNORECASE))
            total_count += count

        return total_count

    # -------------------------------------------------------------------------
    # SCORING
    # -------------------------------------------------------------------------

    def _calculate_domain_scores(self) -> None:
        """Calculate scores per domain."""
        domains = ["tools", "funding", "kpi", "risk", "roadmap", "narrative", "snapshot", "risk_engine", "business_case", "recommendations"]

        for domain in domains:
            domain_issues = [i for i in self.report.issues if i.domain == domain]
            errors = sum(1 for i in domain_issues if i.severity == "ERROR")
            warnings = sum(1 for i in domain_issues if i.severity == "WARNING")

            # Score: Start at 100, -20 per error, -5 per warning
            score = max(0.0, 100.0 - (errors * 20) - (warnings * 5))
            self.report.domain_scores[domain] = score


# =============================================================================
# PUBLIC API
# =============================================================================

def check_consistency(
    sections: Dict[str, str],
    briefing: Dict[str, Any],
    language: str = "de",
) -> ConsistencyReport:
    """
    Run cross-section consistency check.

    Args:
        sections: Dict of section_key -> HTML content
        briefing: Original briefing/answers dict
        language: Report language ("de" or "en")

    Returns:
        ConsistencyReport with all findings

    Example:
        >>> report = check_consistency(sections, briefing)
        >>> if report.status == "FAIL":
        ...     for issue in report.issues:
        ...         print(f"[{issue.severity}] {issue.message}")
    """
    engine = ConsistencyEngine(sections, briefing, language)
    return engine.check_all()
