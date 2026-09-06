# -*- coding: utf-8 -*-
"""
Sprint G29: Risk Engine 2.0 – Consolidated Risk Assessment
============================================================

Ein neues Risk Engine Modul, das AI Act, DSGVO, Vendor/Hosting und
Use-Case-Risiken aus allen vorhandenen Engines zusammenführt, bewertet
und als eigene Report-Section + Datenbasis für Strategy Engine nutzt.

Features:
- AI Act Klassifizierung (high_risk, limited, minimal, unacceptable)
- DSGVO-Risiko-Assessment
- Vendor/Hosting Risk Score
- Use-Case spezifische Risiken
- Risiko-Matrix (Likelihood x Impact)
- Konsolidierter Risk Score (0-100) + Grade (A-F)

Version: 2.0.0 (Sprint G29)
Author: Claude + Wolf
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union, Literal

# v14.35.17: Import text_healing for fragment repair
try:
    from services.text_healing import heal_text_block
    _HEALING_AVAILABLE = True
except ImportError:
    _HEALING_AVAILABLE = False

log = logging.getLogger(__name__)

__all__ = [
    "RiskMatrixEntry",
    "RiskReport",
    "generate_risk_report",
    "risk_report_to_html",
    "extract_risk_from_tools",
    "extract_risk_from_funding",
    "calculate_consolidated_score",
    "RISK_ENGINE_V2_ENABLED",
]


# =============================================================================
# CONFIGURATION
# =============================================================================

RISK_ENGINE_V2_ENABLED = True

# AI Act Risk Classifications
AI_ACT_CLASSES: List[str] = [
    "unacceptable",  # Verbotene Anwendungen
    "high_risk",     # Hochrisiko-Systeme (Anhang III)
    "limited",       # Begrenzte Risiken (Transparenzpflichten)
    "minimal",       # Minimales Risiko
]

# DSGVO Risk Levels
DSGVO_RISK_LEVELS: List[str] = [
    "hoch",     # Sensible Daten, Profiling, automatisierte Entscheidungen
    "mittel",   # Personenbezogene Daten, aber kontrolliert
    "niedrig",  # Keine/minimale personenbezogene Daten
]

# Vendor Risk Categories
VENDOR_CATEGORIES: List[str] = [
    "eu_compliant",      # EU-Anbieter mit DSGVO-Konformität
    "us_with_dpa",       # US-Anbieter mit DPA/AVV
    "us_standard",       # US-Anbieter ohne besondere Schutzmaßnahmen
    "unknown_vendor",    # Unbekannter/Ungeprüfter Anbieter
]

# Risk Matrix Colors
RISK_COLORS: Dict[str, str] = {
    "low": "#22c55e",       # Grün
    "medium": "#f59e0b",    # Gelb/Orange
    "high": "#f97316",      # Orange
    "critical": "#dc2626",  # Rot
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RiskMatrixEntry:
    """
    Einzelner Eintrag in der Risiko-Matrix.

    Likelihood und Impact jeweils 1-5 Skala:
    - 1: Sehr niedrig
    - 2: Niedrig
    - 3: Mittel
    - 4: Hoch
    - 5: Sehr hoch
    """
    id: str
    title: str
    likelihood: int  # 1–5
    impact: int      # 1–5
    color: str       # "low" | "medium" | "high" | "critical"
    description: str

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        self.likelihood = max(1, min(5, self.likelihood))
        self.impact = max(1, min(5, self.impact))

        if self.color not in ("low", "medium", "high", "critical"):
            self.color = _calculate_risk_color(self.likelihood, self.impact)

    @property
    def risk_score(self) -> int:
        """Calculate risk score from likelihood * impact."""
        return self.likelihood * self.impact

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "color": self.color,
            "description": self.description,
            "risk_score": self.risk_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskMatrixEntry":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            likelihood=int(data.get("likelihood", 3)),
            impact=int(data.get("impact", 3)),
            color=data.get("color", "medium"),
            description=data.get("description", ""),
        )


@dataclass
class RiskReport:
    """
    Gesamter Risk Report mit allen Risiko-Dimensionen.

    G29: Konsolidierter Report aus AI Act, DSGVO, Vendor und Use-Case Risiken.
    """
    # AI Act
    ai_act_class: str  # "high_risk", "limited", "minimal", "unacceptable"
    ai_act_reasons: List[str] = field(default_factory=list)
    ai_act_required_controls: List[str] = field(default_factory=list)

    # DSGVO
    dsgvo_risk_level: str = "mittel"  # "hoch", "mittel", "niedrig"
    dsgvo_risk_factors: List[str] = field(default_factory=list)

    # Vendor Risk
    vendor_category: str = "eu_compliant"
    vendor_risk_score: int = 3  # 1-5
    vendor_flags: List[str] = field(default_factory=list)

    # Use-Case Risks
    use_case_risks: List[Dict[str, Any]] = field(default_factory=list)

    # Risk Matrix
    risk_matrix: List[RiskMatrixEntry] = field(default_factory=list)

    # Consolidated
    consolidated_score: float = 50.0  # 0-100
    consolidated_grade: str = "C"  # A-F

    # Summary
    narrative_summary: str = ""

    def __post_init__(self) -> None:
        """Validate and normalize values."""
        # Validate AI Act class
        if self.ai_act_class not in AI_ACT_CLASSES:
            self.ai_act_class = "minimal"

        # Validate DSGVO risk level
        if self.dsgvo_risk_level not in DSGVO_RISK_LEVELS:
            self.dsgvo_risk_level = "mittel"

        # Validate vendor category
        if self.vendor_category not in VENDOR_CATEGORIES:
            self.vendor_category = "unknown_vendor"

        # Clamp scores
        self.vendor_risk_score = max(1, min(5, self.vendor_risk_score))
        self.consolidated_score = max(0.0, min(100.0, self.consolidated_score))

        # Calculate grade if not set
        if not self.consolidated_grade or self.consolidated_grade not in "ABCDF":
            self.consolidated_grade = _score_to_grade(self.consolidated_score)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ai_act_class": self.ai_act_class,
            "ai_act_reasons": self.ai_act_reasons,
            "ai_act_required_controls": self.ai_act_required_controls,
            "dsgvo_risk_level": self.dsgvo_risk_level,
            "dsgvo_risk_factors": self.dsgvo_risk_factors,
            "vendor_category": self.vendor_category,
            "vendor_risk_score": self.vendor_risk_score,
            "vendor_flags": self.vendor_flags,
            "use_case_risks": self.use_case_risks,
            "risk_matrix": [
                entry.to_dict() if isinstance(entry, RiskMatrixEntry) else entry
                for entry in self.risk_matrix
            ],
            "consolidated_score": round(self.consolidated_score, 1),
            "consolidated_grade": self.consolidated_grade,
            "narrative_summary": self.narrative_summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskReport":
        """Create from dictionary."""
        risk_matrix_data = data.get("risk_matrix", [])
        risk_matrix = [
            RiskMatrixEntry.from_dict(entry) if isinstance(entry, dict) else entry
            for entry in risk_matrix_data
        ]

        return cls(
            ai_act_class=data.get("ai_act_class", "minimal"),
            ai_act_reasons=data.get("ai_act_reasons", []),
            ai_act_required_controls=data.get("ai_act_required_controls", []),
            dsgvo_risk_level=data.get("dsgvo_risk_level", "mittel"),
            dsgvo_risk_factors=data.get("dsgvo_risk_factors", []),
            vendor_category=data.get("vendor_category", "eu_compliant"),
            vendor_risk_score=int(data.get("vendor_risk_score", 3)),
            vendor_flags=data.get("vendor_flags", []),
            use_case_risks=data.get("use_case_risks", []),
            risk_matrix=risk_matrix,
            consolidated_score=float(data.get("consolidated_score", 50.0)),
            consolidated_grade=data.get("consolidated_grade", "C"),
            narrative_summary=data.get("narrative_summary", ""),
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _calculate_risk_color(likelihood: int, impact: int) -> str:
    """Calculate risk color from likelihood and impact."""
    score = likelihood * impact

    if score <= 4:
        return "low"
    elif score <= 9:
        return "medium"
    elif score <= 16:
        return "high"
    else:
        return "critical"


def _score_to_grade(score: float) -> str:
    """Convert numeric score (0-100) to letter grade (A-F)."""
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def _grade_to_score_range(grade: str) -> tuple[float, float]:
    """Get score range for a grade."""
    ranges = {
        "A": (85.0, 100.0),
        "B": (70.0, 84.9),
        "C": (55.0, 69.9),
        "D": (40.0, 54.9),
        "F": (0.0, 39.9),
    }
    return ranges.get(grade.upper(), (0.0, 100.0))


def _extract_text(html: str) -> str:
    """Extract plain text from HTML."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_risk_from_tools(
    tools_data: Optional[Any] = None,
    sections: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Extract risk information from Tools Engine 4.0 data.

    Args:
        tools_data: Tools engine output (list of ToolProfile or dicts)
        sections: Report sections dictionary

    Returns:
        Dict with vendor_risk_score, vendor_category, vendor_flags
    """
    result: Dict[str, Any] = {
        "vendor_risk_score": 3,
        "vendor_category": "eu_compliant",
        "vendor_flags": [],
        "compliance_warnings": [],
    }

    if not tools_data:
        return result

    tools_list = tools_data if isinstance(tools_data, list) else []

    max_vendor_risk = 1
    has_eu_hosting = True
    compliance_warnings = []

    for tool in tools_list:
        if isinstance(tool, dict):
            vendor_risk = tool.get("vendor_risk", 3)
            compliance_score = tool.get("compliance_score", 3)
            eu_hosting = tool.get("eu_hosting")
            tool_name = tool.get("name", "Unknown")
        else:
            # Assume ToolProfile object
            vendor_risk = getattr(tool, "vendor_risk", 3)
            compliance_score = getattr(tool, "compliance_score", 3)
            eu_hosting = getattr(tool, "eu_hosting", None)
            tool_name = getattr(tool, "name", "Unknown")

        # Track maximum vendor risk
        if vendor_risk > max_vendor_risk:
            max_vendor_risk = vendor_risk

        # Check EU hosting
        if eu_hosting is False:
            has_eu_hosting = False
            result["vendor_flags"].append(f"{tool_name}: Non-EU Hosting")

        # Check compliance score (4-5 = risk)
        if compliance_score >= 4:
            compliance_warnings.append(f"{tool_name}: Compliance-Score {compliance_score}/5")

    result["vendor_risk_score"] = max_vendor_risk
    result["compliance_warnings"] = compliance_warnings

    # Determine vendor category
    if has_eu_hosting and max_vendor_risk <= 2:
        result["vendor_category"] = "eu_compliant"
    elif max_vendor_risk <= 3:
        result["vendor_category"] = "us_with_dpa"
    elif max_vendor_risk <= 4:
        result["vendor_category"] = "us_standard"
    else:
        result["vendor_category"] = "unknown_vendor"

    return result


def extract_risk_from_funding(
    funding_data: Optional[Any] = None,
    sections: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Extract AI Act relevance from Funding Engine v2 data.

    Args:
        funding_data: Funding engine output
        sections: Report sections dictionary

    Returns:
        Dict with ai_act_relevant programmes
    """
    result: Dict[str, Any] = {
        "ai_act_relevant_programmes": [],
        "ki_high_relevance_count": 0,
    }

    if not funding_data:
        return result

    programmes = []
    if hasattr(funding_data, "programmes"):
        programmes = funding_data.programmes
    elif isinstance(funding_data, dict):
        programmes = funding_data.get("programmes", [])
    elif isinstance(funding_data, list):
        programmes = funding_data

    for prog in programmes:
        if isinstance(prog, dict):
            ai_act = prog.get("ai_act_relevant", False)
            ki_rel = prog.get("ki_relevance", "medium")
            name = prog.get("name", "")
        else:
            ai_act = getattr(prog, "ai_act_relevant", False)
            ki_rel = getattr(prog, "ki_relevance", "medium")
            name = getattr(prog, "name", "")

        if ai_act:
            result["ai_act_relevant_programmes"].append(name)

        if ki_rel == "high":
            result["ki_high_relevance_count"] += 1

    return result


def extract_ai_act_class_from_sections(
    sections: Dict[str, str],
) -> Optional[str]:
    """
    Extract AI Act classification from existing sections.

    Args:
        sections: Report sections dictionary

    Returns:
        AI Act classification string or None
    """
    # Check dedicated AI Act section
    ai_act_html = sections.get("AI_ACT_SUMMARY_HTML", "")
    ai_act_level = sections.get("AI_ACT_RISK_LEVEL", "")

    if ai_act_level:
        level_lower = ai_act_level.lower().replace("-", "_")
        if "high" in level_lower:
            return "high_risk"
        elif "limited" in level_lower:
            return "limited"
        elif "minimal" in level_lower or "low" in level_lower:
            return "minimal"

    # Parse HTML for indicators
    if ai_act_html:
        html_lower = ai_act_html.lower()
        if "hochrisiko" in html_lower or "high-risk" in html_lower or "high_risk" in html_lower:
            return "high_risk"
        elif "begrenzt" in html_lower or "limited" in html_lower:
            return "limited"
        elif "minimal" in html_lower or "gering" in html_lower:
            return "minimal"

    return None


def extract_dsgvo_risk_from_sections(
    sections: Dict[str, str],
    briefing: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Extract DSGVO risk factors from sections and briefing.

    Args:
        sections: Report sections dictionary
        briefing: Briefing/answers dictionary

    Returns:
        Dict with dsgvo_risk_level and dsgvo_risk_factors
    """
    result: Dict[str, Any] = {
        "dsgvo_risk_level": "mittel",
        "dsgvo_risk_factors": [],
    }

    risk_factors = []

    # Check briefing for data types
    if briefing:
        data_types = briefing.get("datentypen", [])
        if isinstance(data_types, str):
            data_types = [data_types]

        sensitive_types = ["gesundheit", "finanzen", "biometrisch", "kinder", "religion"]
        for dtype in data_types:
            dtype_lower = dtype.lower() if dtype else ""
            if any(s in dtype_lower for s in sensitive_types):
                risk_factors.append(f"Sensible Daten: {dtype}")

        # FIX-KIS-1098-P3-3: Check regulierte_branche for vertraulich_nda
        regulierte = briefing.get("regulierte_branche", [])
        if isinstance(regulierte, str):
            regulierte = [regulierte]
        if "vertraulich_nda" in regulierte:
            risk_factors.append("Vertrauliche Kundendaten / NDA-Material")

        # Check for automated decisions
        if briefing.get("automatisierte_entscheidungen") or briefing.get("automated_decisions"):
            risk_factors.append("Automatisierte Entscheidungsfindung")

        # Check for profiling
        if briefing.get("profiling") or "profiling" in str(briefing.get("ki_ziele", "")).lower():
            risk_factors.append("Profiling-Aktivitäten")

    # KIS-1320: Der Fragebogen entscheidet, nicht der Modelltext. Lauf
    # KIS1288 gab Note B, Lauf KIS1289 mit identischen Antworten Note C —
    # der Unterschied war das Wort „personenbezogen" in der generierten
    # Risiko-Sektion. Jetzt zählen Datenquellen und Datenschutz-Organisation
    # aus den Antworten; der Textpfad bleibt nur als Rückfall ohne Antworten.
    _fb_keys = ("datenquellen", "folgenabschaetzung", "meldewege", "loeschregeln",
                "datenschutzbeauftragter", "technische_massnahmen")
    _fb_vorhanden = bool(briefing) and any(briefing.get(k) not in (None, "", []) for k in _fb_keys)
    if _fb_vorhanden:
        _quellen = briefing.get("datenquellen") or []
        if isinstance(_quellen, str):
            _quellen = [_quellen]
        _personen = ("kundendaten", "personaldaten", "nutzungsdaten", "crm", "mitarbeiter", "patienten", "mandanten")
        if any(any(p in str(q).lower() for p in _personen) for q in _quellen):
            risk_factors.append("Personenbezogene Daten im Datenbestand (Kunden-, Nutzungs- oder Personaldaten)")
        # KIS-1323: Der Faktor nennt die tatsächlichen Lücken. Lauf KIS1292
        # (Verlag, Löschregeln „Ja, dokumentiert") las im PDF trotzdem
        # „(Folgenabschätzung, Meldewege, Löschregeln)" — ein fester Text.
        _luecken_labels = {
            "folgenabschaetzung": "Folgenabschätzung",
            "meldewege": "Meldewege",
            "loeschregeln": "Löschregeln",
            "datenschutzbeauftragter": "Datenschutzbeauftragter",
            "technische_massnahmen": "technische Maßnahmen",
        }
        _luecken: list = []
        for _k, _label in _luecken_labels.items():
            _v = str(briefing.get(_k) or "").strip().lower()
            if not _v:
                continue
            if _v.startswith("nein") or _v in ("keine", "unbekannt"):
                _luecken.append(f"{_label} fehlt")
            elif _v in ("teilweise", "geplant", "in_planung"):
                _luecken.append(f"{_label} nur teilweise")
        if len(_luecken) >= 2:
            risk_factors.append(f"Datenschutz-Organisation lückenhaft ({', '.join(_luecken)})")
    else:
        # Rückfall: Sektionstext, wenn der Fragebogen keine Datenschutz-Angaben trägt.
        risks_html = sections.get("RISKS_HTML", "")
        if risks_html:
            risks_lower = risks_html.lower()
            if "personenbezogen" in risks_lower:
                if "personenbezogene Daten" not in risk_factors:
                    risk_factors.append("Verarbeitung personenbezogener Daten")
            if "betroffenenrecht" in risks_lower or "auskunft" in risks_lower:
                risk_factors.append("Betroffenenrechte relevant")

    result["dsgvo_risk_factors"] = risk_factors

    # Determine risk level
    if len(risk_factors) >= 3:
        result["dsgvo_risk_level"] = "hoch"
    elif len(risk_factors) >= 1:
        result["dsgvo_risk_level"] = "mittel"
    else:
        result["dsgvo_risk_level"] = "niedrig"

    return result


# =============================================================================
# SCORE CALCULATION
# =============================================================================

def calculate_consolidated_score(
    ai_act_class: str,
    dsgvo_risk_level: str,
    vendor_risk_score: int,
    risk_matrix: List[RiskMatrixEntry],
) -> tuple[float, str]:
    """
    Calculate consolidated risk score and grade.

    Lower score = higher risk (inverse scale for user-friendliness).
    Score represents "safety level" where 100 = safest.

    Args:
        ai_act_class: AI Act classification
        dsgvo_risk_level: DSGVO risk level
        vendor_risk_score: Vendor risk (1-5)
        risk_matrix: List of risk matrix entries

    Returns:
        Tuple of (score 0-100, grade A-F)
    """
    # Base score starts at 100
    score = 100.0

    # AI Act deductions (biggest impact)
    ai_act_deductions = {
        "unacceptable": 50,
        "high_risk": 30,
        "limited": 15,
        "minimal": 0,
    }
    score -= ai_act_deductions.get(ai_act_class, 15)

    # DSGVO deductions
    dsgvo_deductions = {
        "hoch": 20,
        "mittel": 10,
        "niedrig": 0,
    }
    score -= dsgvo_deductions.get(dsgvo_risk_level, 10)

    # Vendor risk deductions (1-5 → 0-20)
    vendor_deduction = (vendor_risk_score - 1) * 5
    score -= vendor_deduction

    # Risk matrix average impact
    if risk_matrix:
        avg_risk_score = sum(
            entry.risk_score if isinstance(entry, RiskMatrixEntry) else entry.get("risk_score", 9)
            for entry in risk_matrix
        ) / len(risk_matrix)
        # Avg risk 1-25 → deduction 0-10
        matrix_deduction = min(10, avg_risk_score / 2.5)
        score -= matrix_deduction

    # Clamp score
    score = max(0.0, min(100.0, score))

    # Calculate grade
    grade = _score_to_grade(score)

    return score, grade


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_risk_report(
    context: Optional[Any] = None,
    sections: Optional[Dict[str, str]] = None,
    tools_data: Optional[Any] = None,
    funding_data: Optional[Any] = None,
    briefing: Optional[Dict[str, Any]] = None,
    llm_response: Optional[Dict[str, Any]] = None,
) -> RiskReport:
    """
    Generate a comprehensive RiskReport.

    This function:
    1. Extracts risk data from Tools Engine 4.0
    2. Extracts risk data from Funding Engine v2
    3. Extracts AI Act and DSGVO info from sections
    4. If LLM response provided, maps it to RiskReport structure
    5. Calculates consolidated score and grade
    6. Performs plausibility checks

    Args:
        context: ReportContext object (optional)
        sections: Dict of section_key -> HTML content
        tools_data: Tools Engine 4.0 output
        funding_data: Funding Engine v2 output
        briefing: Original briefing/answers dict
        llm_response: Parsed JSON from LLM (if available)

    Returns:
        RiskReport with all dimensions evaluated
    """
    log.info("[G29] Generating Risk Report...")

    sections = sections or {}
    briefing = briefing or {}

    # Initialize with defaults
    ai_act_class = "minimal"
    ai_act_reasons: List[str] = []
    ai_act_required_controls: List[str] = []
    dsgvo_risk_level = "mittel"
    dsgvo_risk_factors: List[str] = []
    vendor_category = "eu_compliant"
    vendor_risk_score = 3
    vendor_flags: List[str] = []
    use_case_risks: List[Dict[str, Any]] = []
    risk_matrix: List[RiskMatrixEntry] = []
    narrative_summary = ""

    # If LLM response provided, use it as primary source
    if llm_response:
        ai_act_class = llm_response.get("ai_act_class", ai_act_class)
        ai_act_reasons = llm_response.get("ai_act_reasons", ai_act_reasons)
        ai_act_required_controls = llm_response.get("ai_act_required_controls", ai_act_required_controls)
        dsgvo_risk_level = llm_response.get("dsgvo_risk_level", dsgvo_risk_level)
        dsgvo_risk_factors = llm_response.get("dsgvo_risk_factors", dsgvo_risk_factors)
        vendor_category = llm_response.get("vendor_category", vendor_category)
        vendor_risk_score = int(llm_response.get("vendor_risk_score", vendor_risk_score))
        vendor_flags = llm_response.get("vendor_flags", vendor_flags)
        use_case_risks = llm_response.get("use_case_risks", use_case_risks)
        narrative_summary = llm_response.get("narrative_summary", narrative_summary)

        # Parse risk matrix from LLM
        raw_matrix = llm_response.get("risk_matrix", [])
        for entry in raw_matrix:
            if isinstance(entry, dict):
                risk_matrix.append(RiskMatrixEntry.from_dict(entry))

    # Extract and merge from engines (fills gaps if LLM didn't provide)
    tools_risk = extract_risk_from_tools(tools_data, sections)

    # Only use tools data if LLM didn't provide vendor info
    if not llm_response or not llm_response.get("vendor_risk_score"):
        vendor_risk_score = max(vendor_risk_score, tools_risk["vendor_risk_score"])
        vendor_category = tools_risk["vendor_category"]
        vendor_flags.extend(tools_risk["vendor_flags"])

    # Extract AI Act class from sections if not from LLM
    if not llm_response or ai_act_class == "minimal":
        extracted_class = extract_ai_act_class_from_sections(sections)
        if extracted_class:
            ai_act_class = extracted_class

    # Extract DSGVO factors
    if not llm_response or not dsgvo_risk_factors:
        dsgvo_result = extract_dsgvo_risk_from_sections(sections, briefing)
        if not dsgvo_risk_factors:
            dsgvo_risk_factors = dsgvo_result["dsgvo_risk_factors"]
        if not llm_response:
            dsgvo_risk_level = dsgvo_result["dsgvo_risk_level"]

    # Generate default risk matrix if none provided
    if not risk_matrix:
        risk_matrix = _generate_default_risk_matrix(
            ai_act_class, dsgvo_risk_level, vendor_risk_score, briefing
        )

    # Calculate consolidated score
    consolidated_score, consolidated_grade = calculate_consolidated_score(
        ai_act_class,
        dsgvo_risk_level,
        vendor_risk_score,
        risk_matrix,
    )

    # Plausibility checks and corrections
    # 1. Vendor risk from tools must not exceed report vendor risk
    if tools_risk["vendor_risk_score"] > vendor_risk_score:
        vendor_risk_score = tools_risk["vendor_risk_score"]
        log.warning("[G29] Adjusted vendor_risk_score to match Tools Engine: %d", vendor_risk_score)

    # 2. High compliance score tools must be flagged
    for warning in tools_risk.get("compliance_warnings", []):
        if warning not in vendor_flags:
            vendor_flags.append(warning)

    # Recalculate score after adjustments
    consolidated_score, consolidated_grade = calculate_consolidated_score(
        ai_act_class,
        dsgvo_risk_level,
        vendor_risk_score,
        risk_matrix,
    )

    # Generate narrative if not provided
    if not narrative_summary:
        narrative_summary = _generate_narrative_summary(
            ai_act_class, dsgvo_risk_level, vendor_risk_score,
            consolidated_score, consolidated_grade, briefing
        )

    report = RiskReport(
        ai_act_class=ai_act_class,
        ai_act_reasons=ai_act_reasons,
        ai_act_required_controls=ai_act_required_controls,
        dsgvo_risk_level=dsgvo_risk_level,
        dsgvo_risk_factors=dsgvo_risk_factors,
        vendor_category=vendor_category,
        vendor_risk_score=vendor_risk_score,
        vendor_flags=vendor_flags,
        use_case_risks=use_case_risks,
        risk_matrix=risk_matrix,
        consolidated_score=consolidated_score,
        consolidated_grade=consolidated_grade,
        narrative_summary=narrative_summary,
    )

    log.info(
        "[G29] Risk Report generated: ai_act=%s, dsgvo=%s, vendor=%d, score=%.1f (%s)",
        ai_act_class, dsgvo_risk_level, vendor_risk_score, consolidated_score, consolidated_grade
    )

    return report


def _generate_default_risk_matrix(
    ai_act_class: str,
    dsgvo_risk_level: str,
    vendor_risk_score: int,
    briefing: Optional[Dict[str, Any]] = None,
) -> List[RiskMatrixEntry]:
    """Generate default risk matrix based on available data."""
    matrix: List[RiskMatrixEntry] = []

    # Risk 1: AI Act Compliance Risk
    ai_act_impact = {"unacceptable": 5, "high_risk": 4, "limited": 3, "minimal": 2}.get(ai_act_class, 3)
    matrix.append(RiskMatrixEntry(
        id="R1_AI_ACT",
        title="AI Act Compliance",
        likelihood=3,
        impact=ai_act_impact,
        color=_calculate_risk_color(3, ai_act_impact),
        description="Regulatorisches Risiko durch EU AI Act Anforderungen",
    ))

    # Risk 2: DSGVO Risk
    dsgvo_impact = {"hoch": 5, "mittel": 3, "niedrig": 2}.get(dsgvo_risk_level, 3)
    matrix.append(RiskMatrixEntry(
        id="R2_DSGVO",
        title="Datenschutz (DSGVO)",
        likelihood=3 if dsgvo_risk_level != "niedrig" else 2,
        impact=dsgvo_impact,
        color=_calculate_risk_color(3, dsgvo_impact),
        description="Datenschutzrisiken bei Verarbeitung personenbezogener Daten",
    ))

    # Risk 3: Vendor/Hosting Risk
    vendor_likelihood = min(5, vendor_risk_score + 1)
    matrix.append(RiskMatrixEntry(
        id="R3_VENDOR",
        title="Vendor & Hosting",
        likelihood=vendor_likelihood,
        impact=vendor_risk_score,
        color=_calculate_risk_color(vendor_likelihood, vendor_risk_score),
        description="Abhängigkeits- und Compliance-Risiken durch externe Anbieter",
    ))

    # Risk 4: Implementation Risk (based on size)
    size = (briefing or {}).get("unternehmensgroesse", "team")
    impl_likelihood = 3 if "solo" in str(size).lower() else 2
    matrix.append(RiskMatrixEntry(
        id="R4_IMPLEMENTATION",
        title="Implementierungsrisiko",
        likelihood=impl_likelihood,
        impact=3,
        color=_calculate_risk_color(impl_likelihood, 3),
        description="Risiko bei der technischen Umsetzung und Integration",
    ))

    # Risk 5: Change Management Risk
    matrix.append(RiskMatrixEntry(
        id="R5_CHANGE",
        title="Change Management",
        likelihood=3,
        impact=2,
        color=_calculate_risk_color(3, 2),
        description="Organisatorische Risiken bei der KI-Einführung",
    ))

    return matrix


def _generate_narrative_summary(
    ai_act_class: str,
    dsgvo_risk_level: str,
    vendor_risk_score: int,
    score: float,
    grade: str,
    briefing: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a narrative summary of the risk assessment."""
    size = (briefing or {}).get("unternehmensgroesse", "Unternehmen")
    branch = (briefing or {}).get("branche", "")

    # Grade-based intro
    grade_intros = {
        "A": "Das Risikoprofil ist sehr günstig.",
        "B": "Das Risikoprofil ist gut beherrschbar.",
        "C": "Das Risikoprofil erfordert gezielte Maßnahmen.",
        "D": "Das Risikoprofil zeigt erhöhten Handlungsbedarf.",
        "F": "Das Risikoprofil erfordert dringende Maßnahmen.",
    }

    intro = grade_intros.get(grade, "Das Risikoprofil wurde bewertet.")

    # AI Act specific
    ai_act_texts = {
        "high_risk": "Die geplanten KI-Anwendungen fallen unter die High-Risk Kategorie des AI Act und erfordern umfangreiche Dokumentation und Kontrollen.",
        "limited": "Für die KI-Anwendungen gelten Transparenzpflichten nach dem AI Act.",
        "minimal": "Die KI-Anwendungen unterliegen minimalen regulatorischen Anforderungen.",
        "unacceptable": "ACHTUNG: Einige geplante Anwendungen könnten unter verbotene Praktiken fallen.",
    }

    ai_act_text = ai_act_texts.get(ai_act_class, "")

    # DSGVO specific
    dsgvo_texts = {
        "hoch": "Im Bereich Datenschutz bestehen erhöhte Anforderungen.",
        "mittel": "Standard-Datenschutzmaßnahmen sind erforderlich.",
        "niedrig": "Die Datenschutzanforderungen sind überschaubar.",
    }

    dsgvo_text = dsgvo_texts.get(dsgvo_risk_level, "")

    # Combine
    parts = [intro]
    if ai_act_text:
        parts.append(ai_act_text)
    if dsgvo_text:
        parts.append(dsgvo_text)

    return " ".join(parts)


# =============================================================================
# HTML RENDERING
# =============================================================================

# KIS-1272-R4-T3a: Echte EN-Varianten der deterministischen Narrativ-Satzbausteine
# aus _generate_narrative_summary. Run 4 zeigte Denglisch in der Summary-Box
# ("Das Risk profile ist gut beherrschbar…"), weil die deutschen Sätze
# ungeübersetzt in den EN-Report liefen. Nur im EN-Renderpfad angewendet.
_NARRATIVE_SENTENCES_EN: Dict[str, str] = {
    "Das Risikoprofil ist sehr günstig.": "The risk profile is very favorable.",
    # KIS-1273 (Aufgabe 4): "well manageable" war holpriges Englisch.
    "Das Risikoprofil ist gut beherrschbar.": "The risk profile is manageable.",
    "Das Risikoprofil erfordert gezielte Maßnahmen.": "The risk profile requires targeted measures.",
    "Das Risikoprofil zeigt erhöhten Handlungsbedarf.": "The risk profile shows an elevated need for action.",
    "Das Risikoprofil erfordert dringende Maßnahmen.": "The risk profile requires urgent measures.",
    "Das Risikoprofil wurde bewertet.": "The risk profile has been assessed.",
    "Die geplanten KI-Anwendungen fallen unter die High-Risk Kategorie des AI Act und erfordern umfangreiche Dokumentation und Kontrollen.":
        "The planned AI applications fall under the high-risk category of the AI Act and require extensive documentation and controls.",
    "Für die KI-Anwendungen gelten Transparenzpflichten nach dem AI Act.":
        "Transparency obligations under the AI Act apply to the AI applications.",
    "Die KI-Anwendungen unterliegen minimalen regulatorischen Anforderungen.":
        "The AI applications are subject to minimal regulatory requirements.",
    "ACHTUNG: Einige geplante Anwendungen könnten unter verbotene Praktiken fallen.":
        "WARNING: Some planned applications could fall under prohibited practices.",
    "Im Bereich Datenschutz bestehen erhöhte Anforderungen.":
        "Data protection requirements are elevated.",
    "Standard-Datenschutzmaßnahmen sind erforderlich.":
        "Standard data protection measures are required.",
    "Die Datenschutzanforderungen sind überschaubar.":
        "The data protection requirements are manageable.",
}

# KIS-1272-R4-T3b: EN-Zeilenlabels für die Default-Risk-Matrix
# (_generate_default_risk_matrix erzeugt deutsche Titel; Run 4 zeigte
# "Implementierungsrisiko" auf S.17 des EN-Reports).
_MATRIX_TITLES_EN: Dict[str, str] = {
    "AI Act Compliance": "AI Act Compliance",
    "Datenschutz (DSGVO)": "Data protection (GDPR)",
    "Vendor & Hosting": "Vendor & Hosting",
    "Implementierungsrisiko": "Implementation risk",
    "Change Management": "Change Management",
}


def _translate_narrative_summary_en(narrative: str) -> str:
    """KIS-1272-R4-T3a: Deterministische DE-Narrativ-Sätze nach EN mappen."""
    result = narrative or ""
    for de_sentence, en_sentence in _NARRATIVE_SENTENCES_EN.items():
        if de_sentence in result:
            result = result.replace(de_sentence, en_sentence)
    return result


def risk_report_to_html(
    report: RiskReport,
    lang: str = "de",
) -> str:
    """
    Generate HTML section for the Risk Report.

    Uses only allowed tags: <div>, <p>, <ul>, <li>, <strong>, <span>, <table>, <tr>, <td>

    Args:
        report: RiskReport object
        lang: Language code ("de" or "en")

    Returns:
        HTML string for PDF template
    """
    # Labels
    if lang == "en":
        labels = {
            "ai_act_title": "AI Act Classification",
            "ai_act_class_label": "Risk Category",
            "reasons_label": "Classification Reasons",
            "controls_label": "Required Controls",
            "dsgvo_title": "GDPR Risk Assessment",
            "dsgvo_level_label": "Risk Level",
            "dsgvo_factors_label": "Risk Factors",
            "vendor_title": "Vendor & Hosting Risk",
            "vendor_score_label": "Vendor Risk Score",
            "vendor_flags_label": "Flags",
            "matrix_title": "Risk Matrix",
            "consolidated_title": "Consolidated Assessment",
            "score_label": "Safety Score",
            "grade_label": "Grade",
            "summary_title": "Summary",
            "high_risk": "High Risk",
            "limited": "Limited Risk",
            "minimal": "Minimal Risk",
            "unacceptable": "Unacceptable",
            # KIS-1272-R4-T3b: Kopfzelle der Risk-Matrix
            "matrix_risk_col": "Risk",
        }
    else:
        labels = {
            "ai_act_title": "AI Act Klassifizierung",
            "ai_act_class_label": "Risikokategorie",
            "reasons_label": "Klassifizierungsgründe",
            "controls_label": "Erforderliche Kontrollen",
            "dsgvo_title": "DSGVO Risiko-Assessment",
            "dsgvo_level_label": "Risikostufe",
            "dsgvo_factors_label": "Risikofaktoren",
            "vendor_title": "Vendor & Hosting Risiko",
            "vendor_score_label": "Vendor Risk Score",
            "vendor_flags_label": "Hinweise",
            "matrix_title": "Risiko-Matrix",
            "consolidated_title": "Gesamtbewertung",
            "score_label": "Sicherheits-Score",
            "grade_label": "Note",
            "summary_title": "Zusammenfassung",
            "high_risk": "Hochrisiko",
            "limited": "Begrenzt",
            "minimal": "Minimal",
            "unacceptable": "Unzulässig",
            # KIS-1272-R4-T3b: Kopfzelle der Risk-Matrix (DE unverändert)
            "matrix_risk_col": "Risiko",
        }

    # AI Act class display
    ai_act_display = {
        "high_risk": labels["high_risk"],
        "limited": labels["limited"],
        "minimal": labels["minimal"],
        "unacceptable": labels["unacceptable"],
    }.get(report.ai_act_class, report.ai_act_class)

    ai_act_color = {
        "high_risk": "#f97316",
        "limited": "#f59e0b",
        "minimal": "#22c55e",
        "unacceptable": "#dc2626",
    }.get(report.ai_act_class, "#6b7280")

    # DSGVO level display
    # KIS-1270: Rohwert ist deutsch ("niedrig") — bei lang=en Low/Medium/High
    # rendern statt "Niedrig"-Badge im EN-Report. DE bleibt byte-identisch.
    if lang == "en":
        dsgvo_display = {
            "niedrig": "Low", "mittel": "Medium", "hoch": "High",
        }.get(str(report.dsgvo_risk_level or "").strip().lower(),
              report.dsgvo_risk_level.capitalize())
    else:
        dsgvo_display = report.dsgvo_risk_level.capitalize()
    dsgvo_color = {
        "hoch": "#dc2626",
        "mittel": "#f59e0b",
        "niedrig": "#22c55e",
    }.get(report.dsgvo_risk_level, "#6b7280")

    # Grade color
    grade_color = {
        "A": "#22c55e",
        "B": "#84cc16",
        "C": "#f59e0b",
        "D": "#f97316",
        "F": "#dc2626",
    }.get(report.consolidated_grade, "#6b7280")

    # === v14.35.17: Engine-Level Text Healing ===
    # Heal all text fields BEFORE HTML rendering to remove fragments
    if _HEALING_AVAILABLE:
        # Heal list items
        report.ai_act_reasons = [heal_text_block(r, domain="risk") for r in report.ai_act_reasons]
        report.ai_act_required_controls = [heal_text_block(c, domain="risk") for c in report.ai_act_required_controls]
        report.dsgvo_risk_factors = [heal_text_block(f, domain="risk") for f in report.dsgvo_risk_factors]
        report.vendor_flags = [heal_text_block(f, domain="risk") for f in report.vendor_flags]
        # Heal narrative summary
        if report.narrative_summary:
            report.narrative_summary = heal_text_block(report.narrative_summary, domain="risk")
        log.debug("[G29] Text healing applied to RiskReport fields")
    # === END v14.35.17 ===

    html_parts = [f'''
    <div class="risk-engine-v2" style="font-size:11pt;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
            <span style="font-size:20px;">⚠️</span>
            <span style="font-size:11px;padding:2px 8px;background:#3b82f6;color:#fff;border-radius:4px;font-weight:600;">G29</span>
        </div>
    ''']

    # AI Act Block
    html_parts.append(f'''
        <div class="risk-block ai-act-block" style="margin-bottom:20px;padding:16px;background:#fef3c7;border-radius:8px;border-left:4px solid {ai_act_color};">
            <p style="margin:0 0 8px 0;font-weight:600;color:#1e293b;">{labels["ai_act_title"]}</p>
            <p style="margin:0 0 8px 0;">
                <strong>{labels["ai_act_class_label"]}:</strong>
                <span class="risk-badge" style="display:inline-block;padding:2px 10px;background:{ai_act_color};color:#fff;border-radius:4px;font-weight:600;margin-left:8px;">{ai_act_display}</span>
            </p>
    ''')

    if report.ai_act_reasons:
        html_parts.append(f'<p style="margin:8px 0 4px 0;font-weight:500;">{labels["reasons_label"]}:</p><ul style="margin:0;padding-left:20px;">')
        for reason in report.ai_act_reasons[:4]:
            html_parts.append(f'<li style="margin:2px 0;">{reason}</li>')
        html_parts.append('</ul>')

    if report.ai_act_required_controls:
        html_parts.append(f'<p style="margin:8px 0 4px 0;font-weight:500;">{labels["controls_label"]}:</p><ul style="margin:0;padding-left:20px;">')
        for control in report.ai_act_required_controls[:4]:
            html_parts.append(f'<li style="margin:2px 0;">{control}</li>')
        html_parts.append('</ul>')

    html_parts.append('</div>')

    # DSGVO Block
    html_parts.append(f'''
        <div class="risk-block dsgvo-block" style="margin-bottom:20px;padding:16px;background:#e0f2fe;border-radius:8px;border-left:4px solid {dsgvo_color};">
            <p style="margin:0 0 8px 0;font-weight:600;color:#1e293b;">{labels["dsgvo_title"]}</p>
            <p style="margin:0 0 8px 0;">
                <strong>{labels["dsgvo_level_label"]}:</strong>
                <span class="dsgvo-badge" style="display:inline-block;padding:2px 10px;background:{dsgvo_color};color:#fff;border-radius:4px;font-weight:600;margin-left:8px;">{dsgvo_display}</span>
            </p>
    ''')

    if report.dsgvo_risk_factors:
        html_parts.append(f'<p style="margin:8px 0 4px 0;font-weight:500;">{labels["dsgvo_factors_label"]}:</p><ul style="margin:0;padding-left:20px;">')
        for factor in report.dsgvo_risk_factors[:4]:
            html_parts.append(f'<li style="margin:2px 0;">{factor}</li>')
        html_parts.append('</ul>')

    html_parts.append('</div>')

    # Vendor Risk Block
    vendor_score_pct = report.vendor_risk_score * 20
    html_parts.append(f'''
        <div class="risk-block vendor-block" style="margin-bottom:20px;padding:16px;background:#f1f5f9;border-radius:8px;">
            <p style="margin:0 0 8px 0;font-weight:600;color:#1e293b;">{labels["vendor_title"]}</p>
            <p style="margin:0 0 8px 0;">
                <strong>{labels["vendor_score_label"]}:</strong>
                <span style="margin-left:8px;">{report.vendor_risk_score}/5</span>
                <span style="display:inline-block;width:60px;height:8px;background:#e2e8f0;border-radius:4px;margin-left:8px;vertical-align:middle;">
                    <span style="display:block;width:{vendor_score_pct}%;height:100%;background:{RISK_COLORS.get("medium") if report.vendor_risk_score <= 3 else RISK_COLORS.get("high")};border-radius:4px;"></span>
                </span>
            </p>
    ''')

    if report.vendor_flags:
        html_parts.append(f'<p style="margin:8px 0 4px 0;font-weight:500;">{labels["vendor_flags_label"]}:</p><ul style="margin:0;padding-left:20px;">')
        for flag in report.vendor_flags[:4]:
            html_parts.append(f'<li style="margin:2px 0;color:#64748b;font-size:10pt;">{flag}</li>')
        html_parts.append('</ul>')

    html_parts.append('</div>')

    # Risk Matrix
    # L1: Added colgroup for column width control, class for CSS targeting
    # FIX-503B: Changed to table-layout:auto for better text wrapping in WeasyPrint
    # FIX-506 TASK 4: Enhanced WeasyPrint-proof CSS to prevent table overflow/clipping
    if report.risk_matrix:
        html_parts.append('<!-- DEBUG-ANCHOR: RISK_MATRIX_START -->')
        html_parts.append(f'''
        <div class="risk-block matrix-block risk-matrix-section" style="margin-bottom:20px;max-width:100%;overflow:visible;">
            <p style="margin:0 0 12px 0;font-weight:600;color:#1e293b;">{labels["matrix_title"]}</p>
            <table class="table-modern risk-matrix-table" style="width:100%;max-width:100%;border-collapse:collapse;font-size:10pt;table-layout:fixed;">
                <colgroup>
                    <col style="width:45%;">
                    <col style="width:15%;">
                    <col style="width:15%;">
                    <col style="width:25%;">
                </colgroup>
                <tr style="background:#f8fafc;">
                    <td style="padding:8px;font-weight:600;border-bottom:1px solid #e2e8f0;white-space:normal;overflow-wrap:break-word;word-break:break-word;">{labels["matrix_risk_col"]}</td>
                    <td style="padding:8px;text-align:center;font-weight:600;border-bottom:1px solid #e2e8f0;white-space:nowrap;">L</td>
                    <td style="padding:8px;text-align:center;font-weight:600;border-bottom:1px solid #e2e8f0;white-space:nowrap;">I</td>
                    <td style="padding:8px;text-align:center;font-weight:600;border-bottom:1px solid #e2e8f0;white-space:nowrap;">Score</td>
                </tr>
        ''')

        for entry in report.risk_matrix[:6]:
            if isinstance(entry, RiskMatrixEntry):
                color = RISK_COLORS.get(entry.color, "#6b7280")
                # KIS-1272-R4-T3b: Deutsche Default-Matrix-Titel im EN-Report
                # auf EN mappen (DE-Pfad unverändert).
                _entry_title = entry.title
                if lang == "en":
                    _entry_title = _MATRIX_TITLES_EN.get(_entry_title, _entry_title)
                # L1: Added overflow-wrap, word-break to prevent text truncation
                # FIX-503B: Added white-space:normal and overflow:visible for WeasyPrint
                # FIX-506 TASK 4: Enhanced CSS for WeasyPrint table cell wrapping
                html_parts.append(f'''
                <tr>
                    <td style="padding:8px;border-bottom:1px solid #f1f5f9;word-wrap:break-word;overflow-wrap:break-word;word-break:break-word;hyphens:auto;white-space:normal;max-width:0;">
                        <span style="display:inline-block;width:8px;height:8px;background:{color};border-radius:50%;margin-right:6px;flex-shrink:0;vertical-align:middle;"></span>
                        <span style="word-wrap:break-word;overflow-wrap:break-word;">{_entry_title}</span>
                    </td>
                    <td style="padding:8px;text-align:center;border-bottom:1px solid #f1f5f9;">{entry.likelihood}</td>
                    <td style="padding:8px;text-align:center;border-bottom:1px solid #f1f5f9;">{entry.impact}</td>
                    <td style="padding:8px;text-align:center;border-bottom:1px solid #f1f5f9;font-weight:600;color:{color};">{entry.risk_score}</td>
                </tr>
                ''')

        html_parts.append('</table></div>')
        html_parts.append('<!-- DEBUG-ANCHOR: RISK_MATRIX_END -->')

    # Consolidated Score Block
    # KIS-1270 (Audit Lauf 3, Punkt 16): Score-Kachel nur rendern, wenn ein
    # belastbarer Wert existiert — sonst stand im PDF eine leere Zahl neben
    # der Note. Normalfall (Score > 0) bleibt byte-identisch.
    try:
        _cons_score_ok = float(report.consolidated_score) > 0
    except (TypeError, ValueError):
        _cons_score_ok = False
    if _cons_score_ok:
        _cons_score_cell = f'''
                <div>
                    <p style="margin:0;font-size:28pt;font-weight:700;">{report.consolidated_score:.0f}</p>
                    <p style="margin:4px 0 0 0;font-size:10pt;opacity:0.9;">{labels["score_label"]}</p>
                </div>'''
    else:
        _cons_score_cell = ''
        log.warning("[G29] consolidated_score fehlt/0 — Score-Kachel wird weggelassen (nur Grade)")
    html_parts.append(f'''
        <div class="risk-block consolidated-block" style="margin-bottom:20px;padding:20px;background:linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);border-radius:10px;color:#fff;">
            <p style="margin:0 0 12px 0;font-weight:600;font-size:13pt;">{labels["consolidated_title"]}</p>
            <div style="display:flex;justify-content:space-around;text-align:center;">{_cons_score_cell}
                <div>
                    <p style="margin:0;font-size:28pt;font-weight:700;color:{grade_color};background:#fff;width:50px;height:50px;border-radius:50%;line-height:50px;display:inline-block;">{report.consolidated_grade}</p>
                    <p style="margin:4px 0 0 0;font-size:10pt;opacity:0.9;">{labels["grade_label"]}</p>
                </div>
            </div>
        </div>
    ''')

    # Narrative Summary
    if report.narrative_summary:
        # KIS-1272-R4-T3a: Im EN-Report die deterministischen deutschen
        # Narrativ-Sätze auf ihre EN-Varianten mappen (DE byte-identisch).
        _narrative = report.narrative_summary
        if lang == "en":
            _narrative = _translate_narrative_summary_en(_narrative)
        html_parts.append(f'''
        <div class="risk-block summary-block" style="padding:16px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;">
            <p style="margin:0 0 8px 0;font-weight:600;color:#1e293b;">{labels["summary_title"]}</p>
            <p style="margin:0;color:#475569;line-height:1.6;">{_narrative}</p>
        </div>
        ''')

    html_parts.append('</div>')

    return '\n'.join(html_parts)


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info("[G29] Risk Engine 2.0 loaded")
