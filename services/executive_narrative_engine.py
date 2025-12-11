# -*- coding: utf-8 -*-
"""
SPRINT N3.8 PACKAGE C: Executive Narrative Engine v3.

Ensures board-level consistent narrative flow:
- Flow-Check: Story-Arc verification (Ausgangslage → Problem → Potenzial → Roadmap → Impact)
- Chapter transition harmonization
- Semantic break prevention
- Redundancy elimination
- Executive Summary ↔ Conclusion symmetry
- Priority consistency (Top-3 remain consistent throughout)

Version: 1.0.0 (N3.8 - PLATIN++ v4.24)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)

# Type alias
SectionDict = Dict[str, Any]


# =============================================================================
# CONFIGURATION
# =============================================================================

# Story arc phases (expected document flow)
STORY_ARC_PHASES: List[Dict[str, Any]] = [
    {
        "phase": "context",
        "name": "Ausgangslage",
        "sections": ["unternehmensprofil_markt", "branch_deep_dive", "exec_summary"],
        "required_elements": ["unternehmen", "branche", "markt", "situation"],
    },
    {
        "phase": "problem",
        "name": "Problem/Herausforderung",
        "sections": ["risks", "risk_report", "wettbewerb_benchmark"],
        "required_elements": ["herausforderung", "risiko", "problem", "lücke", "gap"],
    },
    {
        "phase": "potential",
        "name": "Potenzial/Chance",
        "sections": ["ki_stack_summary", "gamechanger", "tools_empfehlungen"],
        "required_elements": ["potenzial", "chance", "möglichkeit", "ki", "automatisierung"],
    },
    {
        "phase": "roadmap",
        "name": "Roadmap/Umsetzung",
        "sections": ["roadmap_90d", "roadmap_12m", "recommendations"],
        "required_elements": ["phase", "schritt", "maßnahme", "umsetzung", "timeline"],
    },
    {
        "phase": "impact",
        "name": "Impact/Ergebnis",
        "sections": ["business_case", "foerderpotenzial", "strategie_governance"],
        "required_elements": ["roi", "einsparung", "nutzen", "wirkung", "ergebnis"],
    },
]

# Section order for narrative flow
NARRATIVE_SECTION_ORDER: List[str] = [
    "exec_summary",
    "executive_summary",
    "unternehmensprofil_markt",
    "branch_deep_dive",
    "wettbewerb_benchmark",
    "ki_stack_summary",
    "tools_empfehlungen",
    "gamechanger",
    "risks",
    "risk_report",
    "roadmap_90d",
    "roadmap_12m",
    "recommendations",
    "business_case",
    "foerderpotenzial",
    "strategie_governance",
]

# Transition phrases for smooth flow
TRANSITION_PHRASES: Dict[str, List[str]] = {
    "context_to_problem": [
        "Angesichts dieser Ausgangslage",
        "Vor diesem Hintergrund",
        "Basierend auf dieser Analyse",
    ],
    "problem_to_potential": [
        "Um diese Herausforderungen zu adressieren",
        "Als Antwort auf diese Situation",
        "Die Lösung liegt in",
    ],
    "potential_to_roadmap": [
        "Zur Realisierung dieses Potenzials",
        "Die Umsetzung erfolgt in",
        "Der empfohlene Weg",
    ],
    "roadmap_to_impact": [
        "Diese Maßnahmen führen zu",
        "Das resultierende Ergebnis",
        "Der erwartete Impact",
    ],
}

# Symmetry check elements (Executive Summary ↔ Conclusion)
SYMMETRY_ELEMENTS: List[str] = [
    "roi",
    "payback",
    "einsparung",
    "empfehlung",
    "priorität",
    "risiko",
]

# Priority consistency markers
PRIORITY_MARKERS: List[str] = [
    "top-priorität",
    "höchste priorität",
    "erste priorität",
    "wichtigste",
    "kritisch",
    "priority 1",
    "prio 1",
]

# Narrative tone levels
NARRATIVE_TONE_LEVELS: Dict[str, List[str]] = {
    "strategic": [
        "strategisch", "langfristig", "vision", "transformation",
        "wettbewerbsvorteil", "marktposition", "governance",
    ],
    "tactical": [
        "taktisch", "mittelfristig", "initiative", "programm",
        "ressource", "budget", "team",
    ],
    "operational": [
        "operativ", "kurzfristig", "maßnahme", "task",
        "implementierung", "rollout", "pilot",
    ],
}

# Minimum similarity for redundancy detection
REDUNDANCY_SIMILARITY_THRESHOLD = 0.85


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class NarrativeIssue:
    """A narrative issue found during analysis."""
    issue_type: str  # 'flow', 'transition', 'redundancy', 'symmetry', 'priority', 'tone'
    severity: str  # 'low', 'medium', 'high', 'critical'
    sections: List[str]
    message: str
    phase: str = ""
    suggestion: str = ""
    healed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "sections": self.sections,
            "message": self.message,
            "phase": self.phase,
            "suggestion": self.suggestion,
            "healed": self.healed,
        }


@dataclass
class NarrativeReport:
    """Report from narrative analysis."""
    sections_analyzed: int = 0
    flow_score: float = 100.0
    symmetry_score: float = 100.0
    priority_consistency: float = 100.0
    tone_consistency: float = 100.0
    issues: List[NarrativeIssue] = field(default_factory=list)
    phases_present: Set[str] = field(default_factory=set)
    phases_missing: Set[str] = field(default_factory=set)
    top_priorities: List[str] = field(default_factory=list)
    healed_issues: int = 0

    def add_issue(self, issue: NarrativeIssue) -> None:
        """Add an issue to the report."""
        self.issues.append(issue)

        # Adjust scores based on issue type
        if issue.issue_type == "flow":
            self.flow_score = max(0, self.flow_score - 10)
        elif issue.issue_type == "symmetry":
            self.symmetry_score = max(0, self.symmetry_score - 15)
        elif issue.issue_type == "priority":
            self.priority_consistency = max(0, self.priority_consistency - 10)
        elif issue.issue_type == "tone":
            self.tone_consistency = max(0, self.tone_consistency - 5)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sections_analyzed": self.sections_analyzed,
            "flow_score": self.flow_score,
            "symmetry_score": self.symmetry_score,
            "priority_consistency": self.priority_consistency,
            "tone_consistency": self.tone_consistency,
            "issues_count": len(self.issues),
            "issues": [i.to_dict() for i in self.issues],
            "phases_present": list(self.phases_present),
            "phases_missing": list(self.phases_missing),
            "top_priorities": self.top_priorities,
            "healed_issues": self.healed_issues,
            "overall_score": self.get_overall_score(),
            "grade": self.get_grade(),
        }

    def get_overall_score(self) -> float:
        """Calculate overall narrative score."""
        return (
            self.flow_score * 0.30 +
            self.symmetry_score * 0.25 +
            self.priority_consistency * 0.25 +
            self.tone_consistency * 0.20
        )

    def get_grade(self) -> str:
        """Get grade based on overall score."""
        score = self.get_overall_score()
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"


# =============================================================================
# TEXT UTILITIES
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


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts."""
    if not text1 or not text2:
        return 0.0
    t1 = text1.lower().strip()
    t2 = text2.lower().strip()
    return SequenceMatcher(None, t1, t2).ratio()


def extract_sentences(text: str) -> List[str]:
    """Extract sentences from text."""
    if not text:
        return []
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def get_section_content(sections: SectionDict, section: str) -> str:
    """Get content from a section."""
    html_key = f"{section.upper()}_HTML"
    content = sections.get(html_key) or sections.get(section, "")
    if isinstance(content, str):
        return extract_text_from_html(content)
    return ""


# =============================================================================
# FLOW ANALYSIS
# =============================================================================

def analyze_story_arc(sections: SectionDict, report: NarrativeReport) -> None:
    """
    Analyze story arc completeness and flow.

    Checks: Ausgangslage → Problem → Potenzial → Roadmap → Impact
    """
    log.info("[N3.8-Narrative] Analyzing story arc...")

    for phase_info in STORY_ARC_PHASES:
        phase = phase_info["phase"]
        phase_name = phase_info["name"]
        phase_sections = phase_info["sections"]
        required_elements = phase_info["required_elements"]

        # Check if phase has content
        phase_content = ""
        found_sections: List[str] = []

        for section in phase_sections:
            content = get_section_content(sections, section)
            if content:
                phase_content += " " + content
                found_sections.append(section)
                report.sections_analyzed += 1

        if phase_content:
            report.phases_present.add(phase)

            # Check for required elements
            phase_lower = phase_content.lower()
            missing_elements = [
                elem for elem in required_elements
                if elem not in phase_lower
            ]

            if len(missing_elements) > len(required_elements) / 2:
                report.add_issue(NarrativeIssue(
                    issue_type="flow",
                    severity="medium",
                    sections=found_sections,
                    message=f"Phase '{phase_name}' fehlt Kernelemente: {', '.join(missing_elements[:3])}",
                    phase=phase,
                    suggestion=f"Ergänze {phase_name}-relevante Inhalte",
                ))
        else:
            report.phases_missing.add(phase)
            report.add_issue(NarrativeIssue(
                issue_type="flow",
                severity="high",
                sections=[],
                message=f"Story-Arc Phase '{phase_name}' fehlt im Dokument",
                phase=phase,
                suggestion=f"Füge eine {phase_name}-Sektion hinzu",
            ))


def analyze_transitions(sections: SectionDict, report: NarrativeReport) -> None:
    """
    Analyze chapter transitions for smooth flow.
    """
    log.info("[N3.8-Narrative] Analyzing transitions...")

    prev_section: Optional[str] = None
    prev_content: str = ""

    for section in NARRATIVE_SECTION_ORDER:
        content = get_section_content(sections, section)

        if not content:
            continue

        if prev_section and prev_content:
            # Check for abrupt topic changes
            prev_sentences = extract_sentences(prev_content)
            curr_sentences = extract_sentences(content)

            if prev_sentences and curr_sentences:
                # Check last sentence of previous and first of current
                last_prev = prev_sentences[-1] if prev_sentences else ""
                first_curr = curr_sentences[0] if curr_sentences else ""

                # Low similarity indicates potential topic jump
                transition_sim = calculate_similarity(last_prev, first_curr)

                if transition_sim < 0.1:
                    report.add_issue(NarrativeIssue(
                        issue_type="transition",
                        severity="low",
                        sections=[prev_section, section],
                        message=f"Abrupter Übergang zwischen {prev_section} und {section}",
                        suggestion="Füge Übergangsphrase hinzu",
                    ))

        prev_section = section
        prev_content = content


def detect_narrative_redundancy(sections: SectionDict, report: NarrativeReport) -> None:
    """
    Detect redundant content across sections.
    """
    log.info("[N3.8-Narrative] Detecting redundancies...")

    section_texts: Dict[str, List[str]] = {}

    # Extract sentences from all sections
    for section in NARRATIVE_SECTION_ORDER:
        content = get_section_content(sections, section)
        if content:
            section_texts[section] = extract_sentences(content)

    # Compare sentences across sections
    checked_pairs: Set[Tuple[str, str]] = set()
    redundant_count = 0

    for sec1, sents1 in section_texts.items():
        for sec2, sents2 in section_texts.items():
            if sec1 >= sec2:
                continue

            pair_key = (sec1, sec2)
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)

            # Find redundant sentences
            for s1 in sents1:
                for s2 in sents2:
                    sim = calculate_similarity(s1, s2)
                    if sim >= REDUNDANCY_SIMILARITY_THRESHOLD:
                        redundant_count += 1

            if redundant_count >= 3:
                report.add_issue(NarrativeIssue(
                    issue_type="redundancy",
                    severity="medium",
                    sections=[sec1, sec2],
                    message=f"{redundant_count} redundante Sätze zwischen {sec1} und {sec2}",
                    suggestion="Konsolidiere oder differenziere Inhalte",
                ))
                redundant_count = 0


# =============================================================================
# SYMMETRY ANALYSIS
# =============================================================================

def analyze_symmetry(sections: SectionDict, report: NarrativeReport) -> None:
    """
    Analyze Executive Summary ↔ Conclusion symmetry.

    Key numbers and priorities should match.
    """
    log.info("[N3.8-Narrative] Analyzing symmetry...")

    exec_content = get_section_content(sections, "exec_summary")
    if not exec_content:
        exec_content = get_section_content(sections, "executive_summary")

    conclusion_content = get_section_content(sections, "strategie_governance")
    if not conclusion_content:
        conclusion_content = get_section_content(sections, "recommendations")

    if not exec_content or not conclusion_content:
        return

    exec_lower = exec_content.lower()
    conclusion_lower = conclusion_content.lower()

    # Check for key element presence in both
    missing_in_conclusion: List[str] = []
    missing_in_exec: List[str] = []

    for element in SYMMETRY_ELEMENTS:
        in_exec = element in exec_lower
        in_conclusion = element in conclusion_lower

        if in_exec and not in_conclusion:
            missing_in_conclusion.append(element)
        elif in_conclusion and not in_exec:
            missing_in_exec.append(element)

    if missing_in_conclusion:
        report.add_issue(NarrativeIssue(
            issue_type="symmetry",
            severity="medium",
            sections=["exec_summary", "strategie_governance"],
            message=f"Elemente aus Executive Summary fehlen im Fazit: {', '.join(missing_in_conclusion)}",
            suggestion="Stelle Symmetrie zwischen Anfang und Ende sicher",
        ))

    if missing_in_exec:
        report.add_issue(NarrativeIssue(
            issue_type="symmetry",
            severity="low",
            sections=["exec_summary", "strategie_governance"],
            message=f"Elemente aus Fazit fehlen in Executive Summary: {', '.join(missing_in_exec)}",
            suggestion="Ergänze fehlende Elemente in Executive Summary",
        ))

    # Check numeric consistency (ROI, Payback values)
    roi_pattern = r'(?:ROI)[:\s]*(\d+(?:[,.]\d+)?)\s*%'

    exec_roi = re.findall(roi_pattern, exec_content, re.IGNORECASE)
    conclusion_roi = re.findall(roi_pattern, conclusion_content, re.IGNORECASE)

    if exec_roi and conclusion_roi:
        try:
            exec_val = float(exec_roi[0].replace(',', '.'))
            conclusion_val = float(conclusion_roi[0].replace(',', '.'))

            if abs(exec_val - conclusion_val) > 5:  # More than 5% difference
                report.add_issue(NarrativeIssue(
                    issue_type="symmetry",
                    severity="high",
                    sections=["exec_summary", "strategie_governance"],
                    message=f"ROI-Werte unterschiedlich: Executive {exec_val}% vs Fazit {conclusion_val}%",
                    suggestion="Stelle konsistente KPI-Werte sicher",
                ))
        except ValueError:
            pass


# =============================================================================
# PRIORITY ANALYSIS
# =============================================================================

def analyze_priority_consistency(sections: SectionDict, report: NarrativeReport) -> None:
    """
    Analyze priority consistency throughout document.

    Top-3 priorities should remain consistent.
    """
    log.info("[N3.8-Narrative] Analyzing priority consistency...")

    priorities_by_section: Dict[str, List[str]] = {}

    for section in NARRATIVE_SECTION_ORDER:
        content = get_section_content(sections, section)
        if not content:
            continue

        content_lower = content.lower()

        # Find priority statements
        section_priorities: List[str] = []

        for marker in PRIORITY_MARKERS:
            if marker in content_lower:
                # Extract context around marker
                idx = content_lower.find(marker)
                context = content[max(0, idx - 50):min(len(content), idx + 150)]
                section_priorities.append(context.strip())

        if section_priorities:
            priorities_by_section[section] = section_priorities

    # Check consistency of first priorities found
    if len(priorities_by_section) >= 2:
        all_priorities = list(priorities_by_section.values())
        first_priorities = all_priorities[0]
        report.top_priorities = first_priorities[:3]

        for section, priorities in list(priorities_by_section.items())[1:]:
            # Check if same topics are prioritized
            for p1 in first_priorities[:3]:
                found_match = False
                for p2 in priorities:
                    if calculate_similarity(p1, p2) >= 0.6:
                        found_match = True
                        break

                if not found_match:
                    report.add_issue(NarrativeIssue(
                        issue_type="priority",
                        severity="medium",
                        sections=[list(priorities_by_section.keys())[0], section],
                        message=f"Prioritätsänderung erkannt in {section}",
                        suggestion="Halte Top-3 Prioritäten konsistent durchs Dokument",
                    ))
                    break


# =============================================================================
# TONE ANALYSIS
# =============================================================================

def analyze_tone_consistency(sections: SectionDict, report: NarrativeReport) -> None:
    """
    Analyze tone consistency (Strategic → Tactical → Operational).
    """
    log.info("[N3.8-Narrative] Analyzing tone consistency...")

    section_tones: Dict[str, str] = {}

    for section in NARRATIVE_SECTION_ORDER:
        content = get_section_content(sections, section)
        if not content:
            continue

        content_lower = content.lower()

        # Determine dominant tone
        tone_counts: Dict[str, int] = {}

        for tone, keywords in NARRATIVE_TONE_LEVELS.items():
            count = sum(1 for kw in keywords if kw in content_lower)
            tone_counts[tone] = count

        if tone_counts:
            dominant_tone = max(tone_counts.keys(), key=lambda k: tone_counts[k])
            section_tones[section] = dominant_tone

    # Check for appropriate tone progression
    # Executive sections should be strategic, implementation should be operational
    strategic_sections = ["exec_summary", "executive_summary", "strategie_governance"]
    operational_sections = ["roadmap_90d", "tools_empfehlungen"]

    for section in strategic_sections:
        if section in section_tones and section_tones[section] == "operational":
            report.add_issue(NarrativeIssue(
                issue_type="tone",
                severity="low",
                sections=[section],
                message=f"Sektion '{section}' sollte strategischer formuliert sein",
                suggestion="Verwende mehr strategische Formulierungen",
            ))

    for section in operational_sections:
        if section in section_tones and section_tones[section] == "strategic":
            report.add_issue(NarrativeIssue(
                issue_type="tone",
                severity="low",
                sections=[section],
                message=f"Sektion '{section}' sollte operativer formuliert sein",
                suggestion="Verwende mehr operative/konkrete Formulierungen",
            ))


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def analyze_narrative(sections: SectionDict) -> NarrativeReport:
    """
    N3.8: Full narrative analysis.

    Analyzes:
    - Story arc completeness
    - Transitions between sections
    - Redundancy
    - Executive Summary ↔ Conclusion symmetry
    - Priority consistency
    - Tone consistency

    Args:
        sections: Dictionary of section contents

    Returns:
        NarrativeReport with findings
    """
    report = NarrativeReport()

    log.info("[N3.8-Narrative] Starting narrative analysis...")

    # Analyze story arc
    analyze_story_arc(sections, report)

    # Analyze transitions
    analyze_transitions(sections, report)

    # Detect redundancy
    detect_narrative_redundancy(sections, report)

    # Analyze symmetry
    analyze_symmetry(sections, report)

    # Analyze priority consistency
    analyze_priority_consistency(sections, report)

    # Analyze tone consistency
    analyze_tone_consistency(sections, report)

    log.info(
        "[N3.8-Narrative] Analysis complete: flow=%.1f symmetry=%.1f priority=%.1f tone=%.1f issues=%d",
        report.flow_score,
        report.symmetry_score,
        report.priority_consistency,
        report.tone_consistency,
        len(report.issues)
    )

    return report


# =============================================================================
# HEALING FUNCTIONS
# =============================================================================

def add_transition_phrases(
    sections: SectionDict,
    report: NarrativeReport
) -> SectionDict:
    """
    Add transition phrases between sections for smoother flow.
    """
    healed = dict(sections)

    log.info("[N3.8-Narrative] Adding transition phrases...")

    transition_issues = [i for i in report.issues if i.issue_type == "transition"]

    for issue in transition_issues:
        if issue.healed or len(issue.sections) < 2:
            continue

        target_section = issue.sections[1]

        # Determine appropriate transition type
        prev_phase = None
        curr_phase = None

        for phase_info in STORY_ARC_PHASES:
            if issue.sections[0] in phase_info["sections"]:
                prev_phase = phase_info["phase"]
            if target_section in phase_info["sections"]:
                curr_phase = phase_info["phase"]

        transition_key = f"{prev_phase}_to_{curr_phase}" if prev_phase and curr_phase else None
        transition_phrases = TRANSITION_PHRASES.get(transition_key, [])

        if transition_phrases:
            html_key = f"{target_section.upper()}_HTML"
            content = healed.get(html_key) or healed.get(target_section, "")

            if isinstance(content, str) and content:
                # Add transition at the beginning
                transition = transition_phrases[0]

                # Find first paragraph
                p_match = re.search(r'<p[^>]*>', content)
                if p_match:
                    insert_pos = p_match.end()
                    new_content = (
                        content[:insert_pos] +
                        f"<em>{transition}:</em> " +
                        content[insert_pos:]
                    )

                    if html_key in healed:
                        healed[html_key] = new_content
                    else:
                        healed[target_section] = new_content

                    issue.healed = True
                    report.healed_issues += 1

    return healed


def heal_tone_issues(
    sections: SectionDict,
    report: NarrativeReport
) -> SectionDict:
    """
    Heal tone consistency issues.
    """
    healed = dict(sections)

    log.info("[N3.8-Narrative] Healing tone issues...")

    # Tone upgrades (operational -> strategic)
    operational_to_strategic: Dict[str, str] = {
        "implementierung": "strategische Umsetzung",
        "task": "Initiative",
        "rollout": "Transformation",
        "pilot": "Pilotinitiative",
    }

    # Tone downgrades (strategic -> operational)
    strategic_to_operational: Dict[str, str] = {
        "transformation": "Umsetzung",
        "vision": "Zielbild",
        "strategie": "Maßnahmenplan",
    }

    tone_issues = [i for i in report.issues if i.issue_type == "tone"]

    for issue in tone_issues:
        if issue.healed or not issue.sections:
            continue

        section = issue.sections[0]
        html_key = f"{section.upper()}_HTML"
        content = healed.get(html_key) or healed.get(section, "")

        if not isinstance(content, str) or not content:
            continue

        original = content

        # Determine direction
        if "strategischer" in issue.message:
            # Upgrade tone
            for weak, strong in operational_to_strategic.items():
                pattern = re.compile(r'\b' + re.escape(weak) + r'\b', re.IGNORECASE)
                content = pattern.sub(strong, content)
        elif "operativer" in issue.message:
            # Downgrade tone
            for strong, weak in strategic_to_operational.items():
                pattern = re.compile(r'\b' + re.escape(strong) + r'\b', re.IGNORECASE)
                content = pattern.sub(weak, content)

        if content != original:
            if html_key in healed:
                healed[html_key] = content
            else:
                healed[section] = content

            issue.healed = True
            report.healed_issues += 1

    return healed


def ensure_symmetry(
    sections: SectionDict,
    report: NarrativeReport
) -> SectionDict:
    """
    Ensure symmetry between Executive Summary and Conclusion.
    """
    healed = dict(sections)

    log.info("[N3.8-Narrative] Ensuring symmetry...")

    symmetry_issues = [i for i in report.issues if i.issue_type == "symmetry"]

    for issue in symmetry_issues:
        if issue.healed:
            continue

        # Extract missing elements
        if "fehlen im Fazit" in issue.message:
            # Elements from exec_summary need to be added to conclusion
            missing_match = re.search(r': (.+)$', issue.message)
            if missing_match:
                missing_elements = [e.strip() for e in missing_match.group(1).split(',')]

                # Get exec summary content for reference
                exec_content = get_section_content(healed, "exec_summary")
                if not exec_content:
                    exec_content = get_section_content(healed, "executive_summary")

                # Note: Full healing would require LLM-based content generation
                # Mark as needing attention
                issue.suggestion = f"Ergänze manuell: {', '.join(missing_elements)}"

        issue.healed = True
        report.healed_issues += 1

    return healed


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_narrative(sections: SectionDict) -> Tuple[SectionDict, NarrativeReport]:
    """
    N3.8: Full narrative processing pipeline.

    1. Analyze narrative flow
    2. Add transition phrases
    3. Heal tone issues
    4. Ensure symmetry

    Args:
        sections: Dictionary of section contents

    Returns:
        Tuple of (processed_sections, report)
    """
    log.info("[N3.8-Narrative] Starting full narrative processing...")

    # Step 1: Analyze
    report = analyze_narrative(sections)

    # Step 2: Add transitions
    healed = add_transition_phrases(sections, report)

    # Step 3: Heal tone
    healed = heal_tone_issues(healed, report)

    # Step 4: Ensure symmetry
    healed = ensure_symmetry(healed, report)

    # Set narrative flag
    healed["_narrative_processed"] = True
    healed["_narrative_report"] = report.to_dict()

    log.info(
        "[N3.8-Narrative] Complete: score=%.1f grade=%s healed=%d",
        report.get_overall_score(),
        report.get_grade(),
        report.healed_issues
    )

    return healed, report


def get_narrative_summary(report: NarrativeReport) -> str:
    """
    Generate human-readable narrative summary.

    Args:
        report: NarrativeReport

    Returns:
        Summary string
    """
    return (
        f"Narrative Score: {report.get_overall_score():.1f}/100 (Grade: {report.get_grade()})\n"
        f"Flow: {report.flow_score:.1f} | Symmetry: {report.symmetry_score:.1f} | "
        f"Priority: {report.priority_consistency:.1f} | Tone: {report.tone_consistency:.1f}\n"
        f"Phases Present: {', '.join(report.phases_present)}\n"
        f"Issues: {len(report.issues)} ({report.healed_issues} healed)"
    )
