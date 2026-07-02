# -*- coding: utf-8 -*-
"""
FIX-505: HTML Contract Validation Module

This module validates the final HTML output against a strict contract
before PDF generation, ensuring quality and preventing broken reports.

Contract Rules:
1. No code fences (```) in final HTML
2. QuickWins must have render markers (class="quick-win" or data-qw-json-rendered)
3. No empty required sections
4. Basic HTML sanity (has headings, no obviously unclosed tags)

Features:
- Single validation function: html_contract_validate()
- Repair attempt support (deterministic + LLM)
- STRICT_MODE fail-closed behavior
- Debug attachments for Admin emails

Usage:
    from services.html_contract import html_contract_validate, ContractViolation

    result = html_contract_validate(html, sections, strict_mode=True)
    if not result.passed:
        # Handle violations
        ...

Version: 1.0.0 (FIX-505)
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# STRICT_MODE: Fail hard on contract violations
RELEASE_STRICT_MODE = os.getenv("RELEASE_STRICT_MODE", "0") in ("1", "true", "True")

# Maximum repair attempts before giving up
MAX_REPAIR_ATTEMPTS = int(os.getenv("HTML_CONTRACT_MAX_REPAIRS", "1"))

# Escalate the truncated-sentence check from warning to critical (blocks output
# in STRICT_MODE). Default: warning only, to avoid false positives blocking
# legitimate reports until the heuristic is tuned against the live corpus.
TRUNCATION_CRITICAL = os.getenv("HTML_CONTRACT_TRUNCATION_CRITICAL", "0") in ("1", "true", "True")

# Required sections that must not be empty
REQUIRED_SECTIONS: Set[str] = {
    "executive_summary",
    "zusammenfassung",
    "recommendations",
    "empfehlungen",
    "quick_wins",
    "schnellgewinne",
}

# Optional sections (can be empty)
OPTIONAL_SECTIONS: Set[str] = {
    "foerderprogramme",
    "funding_programs",
    "ai_policy_mini",
}


# =============================================================================
# DATA CLASSES
# =============================================================================

class ViolationType(Enum):
    """Types of contract violations."""
    CODE_FENCE = "code_fence"
    RAW_JSON = "raw_json"
    EMPTY_SECTION = "empty_section"
    MISSING_HEADING = "missing_heading"
    UNCLOSED_TAG = "unclosed_tag"
    QUICKWINS_NO_MARKER = "quickwins_no_marker"
    QUICKWINS_EMPTY = "quick_wins_empty"  # FIX-513: Non-Empty Guard
    CHAT_ARTIFACT = "chat_artifact"  # FIX-517C: Questionnaire/chat leaks
    TRUNCATED_SENTENCE = "truncated_sentence"  # Section ends mid-sentence


@dataclass
class Violation:
    """A single contract violation."""
    type: ViolationType
    message: str
    section: Optional[str] = None
    line: Optional[int] = None
    context: Optional[str] = None  # Snippet of problematic HTML
    critical: bool = True  # Critical violations block output

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "message": self.message,
            "section": self.section,
            "line": self.line,
            "context": self.context[:200] if self.context else None,
            "critical": self.critical,
        }


@dataclass
class ContractResult:
    """Result of contract validation."""
    passed: bool
    violations: List[Violation] = field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0
    repair_attempted: bool = False
    repair_successful: bool = False
    repair_llm_used: bool = False  # FIX-QW-PROMPT-STABILIZE: track LLM repair usage
    deterministic_repairs: int = 0  # FIX-QW-PROMPT-STABILIZE: count deterministic fixes
    html_bytes: int = 0
    sections_checked: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "repair_attempted": self.repair_attempted,
            "repair_successful": self.repair_successful,
            "repair_llm_used": self.repair_llm_used,
            "deterministic_repairs": self.deterministic_repairs,
            "html_bytes": self.html_bytes,
            "sections_checked": self.sections_checked,
        }


class ContractViolationError(RuntimeError):
    """FIX-505: Raised in STRICT_MODE when contract validation fails."""

    def __init__(
        self,
        message: str,
        result: ContractResult,
        debug_attachments: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.result = result
        self.debug_attachments = debug_attachments or {}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

# Pre-compiled patterns for performance
_CODE_FENCE_PATTERN = re.compile(r'```+[a-zA-Z]*|```+', re.MULTILINE)
_ORHTML_PATTERN = re.compile(r'orhtml|```html', re.IGNORECASE)
_RAW_JSON_PATTERN = re.compile(r'\{[\s]*"[^"]+"\s*:\s*(?:\[|{|")', re.MULTILINE)
# FIX-513: Word-boundary check for quick-win class (not exact string)
_QUICKWIN_MARKER_PATTERN = re.compile(
    r'data-qw-json-rendered=["\']true["\']',
    re.IGNORECASE
)
# FIX-513: Word-boundary regex for class containing "quick-win"
_QUICKWIN_CLASS_PATTERN = re.compile(
    r'class=["\'][^"\']*\bquick-win\b[^"\']*["\']',
    re.IGNORECASE
)
# FIX-513: Debug anchors for QuickWins block extraction
_QUICKWIN_DEBUG_START = '<!-- DEBUG-503D: QUICK_WINS_START -->'
_QUICKWIN_DEBUG_END = '<!-- DEBUG-503D: QUICK_WINS_END -->'
# FIX-513: Minimum block length for non-empty guard
_QUICKWIN_MIN_BLOCK_LEN = 300
_HEADING_PATTERN = re.compile(r'<h[1-6][^>]*>.*?</h[1-6]>', re.IGNORECASE | re.DOTALL)
_SECTION_PATTERN = re.compile(
    r'<section[^>]*(?:id|data-section)=["\']([^"\']+)["\'][^>]*>(.*?)</section>',
    re.IGNORECASE | re.DOTALL
)


def _check_code_fences(html: str) -> List[Violation]:
    """Check for code fence markers in HTML."""
    violations = []

    # Check for ``` markers
    for match in _CODE_FENCE_PATTERN.finditer(html):
        # Find line number
        line_num = html[:match.start()].count('\n') + 1
        context = html[max(0, match.start() - 50):match.end() + 50]

        violations.append(Violation(
            type=ViolationType.CODE_FENCE,
            message=f"Code fence found at line {line_num}: '{match.group()}'",
            line=line_num,
            context=context,
            critical=True,
        ))

    # Check for "orhtml" or "```html"
    for match in _ORHTML_PATTERN.finditer(html):
        line_num = html[:match.start()].count('\n') + 1
        context = html[max(0, match.start() - 50):match.end() + 50]

        violations.append(Violation(
            type=ViolationType.CODE_FENCE,
            message=f"Code fence variant found at line {line_num}: '{match.group()}'",
            line=line_num,
            context=context,
            critical=True,
        ))

    return violations


def _check_quickwins_markers(html: str) -> List[Violation]:
    """
    FIX-513: Check that QuickWins section has proper render markers.

    Acceptance conditions (any ONE is sufficient to pass):
    - data-qw-json-rendered="true" marker present
    - class attribute contains word-boundary match for "quick-win"

    Also checks Non-Empty Guard (P3):
    - At least 1 quick-win item (word-boundary class match)
    - Block length >= _QUICKWIN_MIN_BLOCK_LEN (300 chars)
    """
    violations = []

    # FIX-513: Extract QuickWins block using debug anchors if available
    qw_block = html
    if _QUICKWIN_DEBUG_START in html and _QUICKWIN_DEBUG_END in html:
        start_idx = html.find(_QUICKWIN_DEBUG_START)
        end_idx = html.find(_QUICKWIN_DEBUG_END)
        if start_idx < end_idx:
            qw_block = html[start_idx:end_idx + len(_QUICKWIN_DEBUG_END)]

    # FIX-513: Check for marker OR word-boundary class match
    has_marker = bool(_QUICKWIN_MARKER_PATTERN.search(qw_block))
    has_quick_win_wordclass = bool(_QUICKWIN_CLASS_PATTERN.search(qw_block))

    # Count quick-win items (word-boundary class matches)
    count_quick_win = len(_QUICKWIN_CLASS_PATTERN.findall(qw_block))
    block_len = len(qw_block)

    log.info(
        "[FIX-513][HTML-CONTRACT] quick_wins_check block_len=%d has_marker=%s "
        "has_quick_win_wordclass=%s count_quick_win=%d",
        block_len, has_marker, has_quick_win_wordclass, count_quick_win
    )

    # FIX-513 P1: If marker or word-boundary class is present, QuickWins is rendered
    if has_marker or has_quick_win_wordclass:
        # FIX-517C: Non-Empty Guard - must have at least 2 items and sufficient length
        if count_quick_win < 2:
            violations.append(Violation(
                type=ViolationType.QUICKWINS_EMPTY,
                message=f"QuickWins has marker/class but insufficient items (count={count_quick_win}, min=2)",
                section="quick_wins_empty",
                context=qw_block[:200],
                critical=True,
            ))
        elif block_len < _QUICKWIN_MIN_BLOCK_LEN:
            violations.append(Violation(
                type=ViolationType.QUICKWINS_EMPTY,
                message=f"QuickWins block too short ({block_len} < {_QUICKWIN_MIN_BLOCK_LEN})",
                section="quick_wins_empty",
                context=qw_block[:200],
                critical=True,
            ))
        return violations  # Pass - QuickWins is rendered

    # -------------------------------------------------------------------------
    # FIX-513B: Content-based heuristic for direct HTML renders (no markers).
    # Sonnet sometimes returns valid QW HTML without class="quick-win" or
    # data-qw-json-rendered markers.  When the qw_block is the FULL assembled
    # HTML (debug anchors missing → block_len > 50 000), we first try to
    # extract the QW region via secondary patterns, then validate the extract.
    # -------------------------------------------------------------------------

    _QW_CONTENT_HEADING = re.compile(
        r'<h[3-5][^>]*>\s*(?:(?!</).){5,80}\s*</h[3-5]>',
        re.IGNORECASE | re.DOTALL,
    )
    _QW_CONTENT_PROBLEM = re.compile(
        r'<(?:p|li|span|div)[^>]*>\s*<strong>\s*(?:Problem|Herausforderung|Ausgangslage)\s*'
        r'(?::|</strong>)',
        re.IGNORECASE,
    )
    _QW_CONTENT_SOLUTION = re.compile(
        r'<(?:p|li|span|div)[^>]*>\s*<strong>\s*(?:L[öo]sung|Ma[ßs]nahme|Quick\s*Win|Umsetzung)\s*'
        r'(?::|</strong>)',
        re.IGNORECASE,
    )

    # --- secondary extraction: try to find QW region by id/data-section ------
    _QW_REGION_PATTERNS = [
        re.compile(
            r'(<(?:section|div|article)[^>]*(?:id|data-section)=["\']'
            r'(?:quick[_-]?wins|schnellgewinne|sofort[_-]?massnahmen)["\'][^>]*>)'
            r'(.*?)</(?:section|div|article)>',
            re.IGNORECASE | re.DOTALL,
        ),
        # Template comment markers (some templates wrap QW with HTML comments)
        re.compile(
            r'(<!--\s*QW[_-]?START\s*-->)(.*?)(<!--\s*QW[_-]?END\s*-->)',
            re.IGNORECASE | re.DOTALL,
        ),
    ]

    extracted_qw = None
    for rp in _QW_REGION_PATTERNS:
        m = rp.search(html)
        if m:
            extracted_qw = m.group(0)
            break

    # Use extracted region (or fall through to full-page heuristic below)
    check_block = extracted_qw or qw_block
    is_full_page = (extracted_qw is None and block_len > 50_000)

    # Count QW-indicative structures in the check block
    n_headings = len(_QW_CONTENT_HEADING.findall(check_block))
    n_problems = len(_QW_CONTENT_PROBLEM.findall(check_block))
    n_solutions = len(_QW_CONTENT_SOLUTION.findall(check_block))

    if is_full_page:
        # Full-page mode: require the SPECIFIC Problem/Lösung pattern (not just headings)
        # This prevents false positives from other sections' headings.
        content_pass = (n_problems >= 2 and n_solutions >= 2)
    else:
        # Extracted block: headings + paragraphs sufficient
        content_pass = (n_headings >= 2 and len(check_block) >= _QUICKWIN_MIN_BLOCK_LEN)

    if content_pass:
        log.info(
            "[FIX-513B][HTML-CONTRACT] quick_wins CONTENT-HEURISTIC PASS: "
            "headings=%d problems=%d solutions=%d block_len=%d extracted=%s "
            "(no marker/class, but valid HTML content detected)",
            n_headings, n_problems, n_solutions,
            len(check_block), extracted_qw is not None,
        )
        return violations  # Pass - QuickWins has valid rendered HTML content

    log.info(
        "[FIX-513B][HTML-CONTRACT] quick_wins CONTENT-HEURISTIC FAIL: "
        "headings=%d problems=%d solutions=%d block_len=%d extracted=%s",
        n_headings, n_problems, n_solutions,
        len(check_block), extracted_qw is not None,
    )

    # Fallback: Check via section patterns (old behavior for non-premium renders)
    quickwins_patterns = [
        re.compile(r'(<section[^>]*(?:id|data-section)=["\']quick[_-]?wins["\'][^>]*>)(.*?)</section>', re.IGNORECASE | re.DOTALL),
        re.compile(r'(<section[^>]*(?:id|data-section)=["\']schnellgewinne["\'][^>]*>)(.*?)</section>', re.IGNORECASE | re.DOTALL),
        re.compile(r'(<div[^>]*class=["\'][^"\']*quick[_-]?wins[^"\']*["\'][^>]*>)(.*?)</div>', re.IGNORECASE | re.DOTALL),
    ]

    for pattern in quickwins_patterns:
        for match in pattern.finditer(html):
            opening_tag = match.group(1)
            content = match.group(2)
            full_section = opening_tag + content

            # Check if content has JSON-like structure without markers
            if _RAW_JSON_PATTERN.search(content):
                # Has JSON - must have marker
                if not _QUICKWIN_MARKER_PATTERN.search(full_section) and not _QUICKWIN_CLASS_PATTERN.search(full_section):
                    violations.append(Violation(
                        type=ViolationType.QUICKWINS_NO_MARKER,
                        message="QuickWins section contains JSON-like content without render marker",
                        section="quick_wins",
                        context=content[:200],
                        critical=True,
                    ))
            elif '<li' not in content.lower() and '<p' not in content.lower():
                # No list items or paragraphs - might be empty or broken
                violations.append(Violation(
                    type=ViolationType.QUICKWINS_EMPTY,
                    message="QuickWins section appears to have no rendered content",
                    section="quick_wins_empty",
                    context=content[:200],
                    critical=True,
                ))

    return violations


def _check_empty_sections(html: str, sections: Optional[List[str]] = None) -> List[Violation]:
    """Check for empty required sections."""
    violations = []

    # Find all sections in HTML
    for match in _SECTION_PATTERN.finditer(html):
        section_id = match.group(1)
        content = match.group(2)

        # Normalize section ID
        section_normalized = section_id.lower().replace("-", "_").replace(" ", "_")

        # Skip optional sections
        if section_normalized in OPTIONAL_SECTIONS:
            continue

        # Check if required
        is_required = section_normalized in REQUIRED_SECTIONS
        if sections:
            is_required = is_required or section_normalized in [s.lower() for s in sections]

        if is_required:
            # Check if content is essentially empty
            # Remove whitespace, comments, and empty tags
            stripped = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
            stripped = re.sub(r'<[^>]*>\s*</[^>]*>', '', stripped)
            stripped = stripped.strip()

            if len(stripped) < 50:  # Less than 50 chars of actual content
                violations.append(Violation(
                    type=ViolationType.EMPTY_SECTION,
                    message=f"Required section '{section_id}' appears empty ({len(stripped)} chars)",
                    section=section_id,
                    context=content[:200],
                    critical=True,
                ))

    return violations


_TAG_STRIP_PATTERN = re.compile(r'<[^>]+>')
_ENTITY_PATTERN = re.compile(r'&[a-zA-Z#0-9]+;')
_SENTENCE_TAIL_SPLIT = re.compile(r'[.!?…]\s')
# Characters that legitimately end a section's visible text (no truncation).
_SENTENCE_ENDERS = set('.!?…:;)]}»"\'”’*%€$0123456789')


def _visible_text(html_fragment: str) -> str:
    """Return the collapsed, tag-free visible text of an HTML fragment."""
    txt = re.sub(r'<!--.*?-->', '', html_fragment, flags=re.DOTALL)
    txt = re.sub(r'<(script|style)\b.*?</\1>', ' ', txt, flags=re.DOTALL | re.IGNORECASE)
    txt = _TAG_STRIP_PATTERN.sub(' ', txt)
    txt = _ENTITY_PATTERN.sub(' ', txt)
    return re.sub(r'\s+', ' ', txt).strip()


def _looks_truncated(text: str) -> bool:
    """
    Heuristic: does the visible text end mid-sentence? Conservative to avoid
    false positives on headings, labels or list markers.
    """
    if not text:
        return False
    if text[-1] in _SENTENCE_ENDERS:
        return False
    # The trailing fragment after the last sentence break.
    tail = _SENTENCE_TAIL_SPLIT.split(text)[-1].strip()
    # Short tails are labels/headings, not truncated sentences.
    if len(tail) < 25:
        return False
    # A single word without spaces is a label, not a sentence.
    if ' ' not in tail:
        return False
    return True


def _check_truncated_sentences(html: str, sections: Optional[List[str]] = None) -> List[Violation]:
    """
    Detect sections whose visible text ends mid-sentence (e.g. an LLM/render
    truncation like '...nach dem Schema Input' with no closing punctuation).
    Warning by default; critical when HTML_CONTRACT_TRUNCATION_CRITICAL=1.
    """
    violations: List[Violation] = []
    for match in _SECTION_PATTERN.finditer(html):
        section_id = match.group(1)
        content = match.group(2)
        text = _visible_text(content)
        # Very short sections are covered by the empty-section check.
        if len(text) < 40:
            continue
        if _looks_truncated(text):
            violations.append(Violation(
                type=ViolationType.TRUNCATED_SENTENCE,
                message=(
                    f"Section '{section_id}' appears to end mid-sentence: "
                    f"'...{text[-60:]}'"
                ),
                section=section_id,
                context=content[-200:],
                critical=TRUNCATION_CRITICAL,
            ))
    return violations


def _check_html_sanity(html: str) -> List[Violation]:
    """Basic HTML sanity checks."""
    violations = []

    # Check for at least one heading
    headings = _HEADING_PATTERN.findall(html)
    if len(headings) < 1:
        violations.append(Violation(
            type=ViolationType.MISSING_HEADING,
            message="No headings (h1-h6) found in HTML",
            critical=False,  # Warning, not critical
        ))

    # Check for obviously unclosed tags (simple heuristic)
    # Count opening and closing tags for common elements
    tag_pairs = [
        ('section', r'<section\b', r'</section>'),
        ('div', r'<div\b', r'</div>'),
        ('table', r'<table\b', r'</table>'),
        ('ul', r'<ul\b', r'</ul>'),
        ('ol', r'<ol\b', r'</ol>'),
    ]

    for tag_name, open_pattern, close_pattern in tag_pairs:
        open_count = len(re.findall(open_pattern, html, re.IGNORECASE))
        close_count = len(re.findall(close_pattern, html, re.IGNORECASE))

        if open_count != close_count:
            violations.append(Violation(
                type=ViolationType.UNCLOSED_TAG,
                message=f"Tag mismatch for <{tag_name}>: {open_count} open, {close_count} close",
                critical=False,  # Warning, not critical
            ))

    return violations


def _check_raw_json_artifacts(html: str) -> List[Violation]:
    """Check for raw JSON artifacts in rendered sections."""
    violations = []

    # Patterns that indicate unrendered JSON data
    json_indicators = [
        (r'"title"\s*:\s*"[^"]+"\s*,\s*"description"', "Raw JSON object with title/description"),
        (r'"quick_wins"\s*:\s*\[', "Raw quick_wins JSON array"),
        (r'"recommendations"\s*:\s*\[', "Raw recommendations JSON array"),
        (r'"kpi_name"\s*:', "Raw KPI JSON field"),
        (r'"roi_percent"\s*:', "Raw ROI JSON field"),
    ]

    for pattern, description in json_indicators:
        matches = list(re.finditer(pattern, html, re.IGNORECASE))
        for match in matches[:3]:  # Limit to first 3 matches
            line_num = html[:match.start()].count('\n') + 1
            context = html[max(0, match.start() - 30):match.end() + 70]

            violations.append(Violation(
                type=ViolationType.RAW_JSON,
                message=f"{description} at line {line_num}",
                line=line_num,
                context=context,
                critical=True,
            ))

    return violations


# FIX-517C: Chat/questionnaire artifact patterns (forbidden in final output)
_CHAT_ARTIFACT_PATTERNS = [
    re.compile(r'Wobei kann ich (dir|Ihnen) helfen', re.IGNORECASE),
    re.compile(r'Bitte nenne[n]? kurz', re.IGNORECASE),
]


def _check_chat_artifacts(html: str) -> List[Violation]:
    """FIX-517C: Check for chat/questionnaire artifacts that leaked into output."""
    violations = []

    for pattern in _CHAT_ARTIFACT_PATTERNS:
        for match in pattern.finditer(html):
            line_num = html[:match.start()].count('\n') + 1
            context = html[max(0, match.start() - 30):match.end() + 70]
            violations.append(Violation(
                type=ViolationType.CHAT_ARTIFACT,
                message=f"Chat artifact at line {line_num}: '{match.group()}'",
                line=line_num,
                context=context,
                critical=True,
            ))

    return violations


# =============================================================================
# REPAIR FUNCTIONS
# =============================================================================

def _attempt_deterministic_repair(html: str, violations: List[Violation]) -> Tuple[str, int]:
    """
    Attempt deterministic repairs for known issues.

    Returns:
        Tuple of (repaired_html, fixes_applied)
    """
    fixes_applied = 0
    result = html

    for violation in violations:
        if violation.type == ViolationType.CODE_FENCE:
            # Remove code fences
            result, count = re.subn(_CODE_FENCE_PATTERN, '', result)
            if count > 0:
                fixes_applied += count
                log.info(
                    "[FIX-505][HTML-CONTRACT] Deterministic repair: removed %d code fences",
                    count
                )
        elif violation.type == ViolationType.CHAT_ARTIFACT:
            # FIX-517C: Remove chat artifact lines deterministically
            for pattern in _CHAT_ARTIFACT_PATTERNS:
                # Remove the entire line containing the artifact
                result, count = re.subn(
                    r'[^\n]*' + pattern.pattern + r'[^\n]*\n?',
                    '',
                    result,
                    flags=re.IGNORECASE
                )
                if count > 0:
                    fixes_applied += count
                    log.info(
                        "[FIX-517C][HTML-CONTRACT] Deterministic repair: removed %d chat artifacts",
                        count
                    )

    return result, fixes_applied


def _attempt_llm_repair(
    html: str,
    violations: List[Violation],
    section: str = "html_repair",
) -> Optional[str]:
    """
    Attempt LLM-based repair for complex issues.

    This uses the openai_retry module if available.

    Returns:
        Repaired HTML or None if repair failed
    """
    try:
        from services.openai_retry import openai_request_simple
    except ImportError:
        log.warning("[FIX-505][HTML-CONTRACT] openai_retry module not available for LLM repair")
        return None

    # Build repair prompt
    violation_desc = "\n".join([
        f"- {v.type.value}: {v.message}"
        for v in violations[:5]  # Limit to 5 violations
    ])

    # FIX-512 CHANGE 2: Hardened prompt with explicit NO markdown/code fences instruction
    prompt = f"""Fix the following HTML issues:

{violation_desc}

HTML to repair (first 5000 chars):
{html[:5000]}

CRITICAL RULES:
- Return ONLY raw HTML. No ``` fences. No markdown. No explanations.
- Keep the same structure and content, just fix formatting issues.
- Remove any code fences (``` markers).
- Ensure QuickWins have proper HTML structure.
- Fix any unclosed tags.

OUTPUT: Raw HTML only, starting with < and ending with >. No text before or after."""

    try:
        repaired = openai_request_simple(
            section=section,
            prompt=prompt,
            # FIX-512: Hardened system prompt
            system_prompt="You are an HTML repair assistant. Return ONLY clean HTML. Never use markdown, code fences, or explanations. Output raw HTML only.",
            max_tokens=8000,
        )
        return repaired
    except Exception as e:
        log.error("[FIX-505][HTML-CONTRACT] LLM repair failed: %s", str(e)[:100])
        return None


# =============================================================================
# MAIN VALIDATION FUNCTION
# =============================================================================

def html_contract_validate(
    html: str,
    sections: Optional[List[str]] = None,
    strict_mode: Optional[bool] = None,
    allow_repair: bool = True,
) -> ContractResult:
    """
    FIX-505: Validate HTML against the output contract.

    This is the main entry point for contract validation. It checks:
    1. No code fences
    2. QuickWins have render markers
    3. No empty required sections
    4. Basic HTML sanity

    Args:
        html: HTML content to validate
        sections: Optional list of section names rendered
        strict_mode: Override for RELEASE_STRICT_MODE
        allow_repair: Whether to attempt repairs on failure

    Returns:
        ContractResult with validation outcome

    Raises:
        ContractViolationError: In STRICT_MODE when validation fails after repairs
    """
    is_strict = strict_mode if strict_mode is not None else RELEASE_STRICT_MODE

    result = ContractResult(
        passed=False,
        html_bytes=len(html) if html else 0,
        sections_checked=len(sections) if sections else 0,
    )

    if not html:
        result.violations.append(Violation(
            type=ViolationType.EMPTY_SECTION,
            message="HTML content is empty",
            critical=True,
        ))
        result.critical_count = 1

        if is_strict:
            log.error("[FIX-505][HTML-CONTRACT] FAIL-CLOSED strict=1 reason=empty_html")
            raise ContractViolationError(
                "[FIX-505][HTML-CONTRACT] STRICT_MODE: Empty HTML content",
                result=result,
            )
        return result

    # Run all checks
    all_violations = []
    all_violations.extend(_check_code_fences(html))
    all_violations.extend(_check_quickwins_markers(html))
    all_violations.extend(_check_empty_sections(html, sections))
    all_violations.extend(_check_truncated_sentences(html, sections))
    all_violations.extend(_check_html_sanity(html))
    all_violations.extend(_check_raw_json_artifacts(html))
    all_violations.extend(_check_chat_artifacts(html))  # FIX-517C

    result.violations = all_violations
    result.critical_count = sum(1 for v in all_violations if v.critical)
    result.warning_count = sum(1 for v in all_violations if not v.critical)

    # Log result
    if result.critical_count == 0:
        result.passed = True
        log.info(
            "[HTML-CONTRACT] PASS repair_llm_used=%s deterministic_repairs=%d warnings=%d bytes=%d",
            str(result.repair_llm_used).lower(), result.deterministic_repairs,
            result.warning_count, result.html_bytes
        )
        log.info(
            "[FIX-514][CONTRACT] PASS repair_llm_used=%s deterministic_repairs=%d violations=%d",
            str(result.repair_llm_used).lower(), result.deterministic_repairs,
            result.critical_count
        )
        return result

    # Validation failed - log violations
    violation_keys = list(set(v.section or v.type.value for v in all_violations if v.critical))
    log.warning(
        "[FIX-505][HTML-CONTRACT] FAIL violations=%d critical=%d keys=%s",
        len(all_violations), result.critical_count, violation_keys
    )

    # Attempt repair if allowed
    if allow_repair and result.critical_count > 0:
        log.info("[FIX-505][HTML-CONTRACT] attempting repair via deterministic+html_repair")
        result.repair_attempted = True

        # Phase 1: Deterministic repair
        repaired_html, fixes = _attempt_deterministic_repair(html, all_violations)
        result.deterministic_repairs = fixes

        if fixes > 0:
            # Re-validate after deterministic repair
            recheck = html_contract_validate(
                repaired_html,
                sections=sections,
                strict_mode=False,  # Don't recurse into strict mode
                allow_repair=False,  # Don't recurse repairs
            )

            if recheck.passed or recheck.critical_count < result.critical_count:
                result.passed = recheck.passed
                result.violations = recheck.violations
                result.critical_count = recheck.critical_count
                result.warning_count = recheck.warning_count
                result.repair_successful = recheck.passed
                result.deterministic_repairs = fixes

                if recheck.passed:
                    log.info(
                        "[HTML-CONTRACT] PASS repair_llm_used=false deterministic_repairs=%d",
                        fixes
                    )
                    return result

        # Phase 2: LLM repair (if deterministic didn't fully fix)
        # FIX-513 P2: STRICT mode MUST NOT use LLM repair (deterministic only)
        if result.critical_count > 0 and not is_strict:
            llm_repaired = _attempt_llm_repair(html, all_violations)
            if llm_repaired:
                result.repair_llm_used = True
                # FIX-512 CHANGE 1: Strip code fences AFTER LLM repair, BEFORE re-validation
                llm_repaired_before = llm_repaired
                llm_repaired = strip_code_fences_final(llm_repaired)

                # Count how many code fences were removed
                fence_count_before = len(_CODE_FENCE_PATTERN.findall(llm_repaired_before))
                fence_count_before += len(_ORHTML_PATTERN.findall(llm_repaired_before))
                fence_count_after = len(_CODE_FENCE_PATTERN.findall(llm_repaired))
                fence_count_after += len(_ORHTML_PATTERN.findall(llm_repaired))
                fences_removed = fence_count_before - fence_count_after

                log.info(
                    "[FIX-512][HTML-CONTRACT] stripped_code_fences_after_repair removed=%d",
                    fences_removed
                )

                recheck = html_contract_validate(
                    llm_repaired,
                    sections=sections,
                    strict_mode=False,
                    allow_repair=False,
                )

                if recheck.passed:
                    result.passed = True
                    result.violations = recheck.violations
                    result.critical_count = recheck.critical_count
                    result.warning_count = recheck.warning_count
                    result.repair_successful = True
                    result.repair_llm_used = True
                    log.info(
                        "[HTML-CONTRACT] PASS repair_llm_used=true deterministic_repairs=%d",
                        result.deterministic_repairs
                    )
                    return result

    # FIX-QW-PROMPT-STABILIZE: Fail-closed gate — repair_llm_used MUST be false in STRICT
    if is_strict and result.repair_llm_used:
        debug_attachments = {
            "debug_qw_repair_llm_gate.json": json.dumps(result.to_dict(), indent=2),
        }
        log.error(
            "[FIX-514][CONTRACT] FAIL strict_no_repair_llm violations=%d",
            result.critical_count
        )
        raise ContractViolationError(
            "[HTML-CONTRACT] STRICT_MODE: repair_llm_used=true is not allowed",
            result=result,
            debug_attachments=debug_attachments,
        )

    # Final failure handling
    if is_strict and result.critical_count > 0:
        # Build debug attachments
        debug_attachments = {
            "debug_505_contract_report.json": json.dumps(result.to_dict(), indent=2),
            "debug_505_bad_blocks.html": _extract_bad_blocks(html, all_violations),
        }

        log.error(
            "[FIX-505][HTML-CONTRACT] FAIL-CLOSED strict=1 violations=%d",
            result.critical_count
        )

        raise ContractViolationError(
            f"[FIX-505][HTML-CONTRACT] STRICT_MODE: Contract validation failed with "
            f"{result.critical_count} critical violations",
            result=result,
            debug_attachments=debug_attachments,
        )

    return result


def _extract_bad_blocks(html: str, violations: List[Violation]) -> str:
    """Extract HTML snippets around violations for debugging."""
    blocks = []
    blocks.append("<!-- FIX-505 Debug: Bad Blocks Report -->")

    for i, v in enumerate(violations[:10]):  # Limit to 10
        blocks.append(f"\n<!-- Violation {i+1}: {v.type.value} - {v.message} -->")
        if v.context:
            blocks.append(f"<pre>{v.context}</pre>")
        if v.line:
            # Extract surrounding lines
            lines = html.split('\n')
            start = max(0, v.line - 3)
            end = min(len(lines), v.line + 3)
            context_lines = lines[start:end]
            blocks.append(f"<pre>Lines {start+1}-{end}:\n{chr(10).join(context_lines)}</pre>")

    return '\n'.join(blocks)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def strip_code_fences_final(html: str) -> str:
    """
    Final pass to remove any remaining code fences.

    This is a safety function that can be called as the last step
    before PDF generation.
    """
    result = re.sub(r'```+[a-zA-Z]*', '', html)
    result = re.sub(r'```+', '', result)
    result = re.sub(r'orhtml', '', result, flags=re.IGNORECASE)
    return result


def normalize_typos_and_entities(html: str) -> str:
    """
    FIX-523A: Normalize HTML entities and typographic quotes.

    This function normalizes:
    1. HTML entities: &nbsp; → space, &uuml; → ü, &ouml; → ö, etc.
    2. Typographic quotes: „" → " (straight double quotes)
    3. Typographic single quotes: '' → ' (straight single quotes)

    Args:
        html: Raw HTML string

    Returns:
        Normalized HTML string

    Note:
        Call this BEFORE final validation to ensure clean output.
    """
    if not html:
        return html

    result = html

    # 1. Common HTML entities → Unicode
    entity_map = {
        "&nbsp;": " ",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&apos;": "'",
        # German umlauts
        "&auml;": "ä",
        "&ouml;": "ö",
        "&uuml;": "ü",
        "&Auml;": "Ä",
        "&Ouml;": "Ö",
        "&Uuml;": "Ü",
        "&szlig;": "ß",
        # Common punctuation
        "&ndash;": "–",
        "&mdash;": "—",
        "&hellip;": "…",
        "&euro;": "€",
        "&copy;": "©",
        "&reg;": "®",
        "&trade;": "™",
    }

    for entity, char in entity_map.items():
        result = result.replace(entity, char)

    # 2. Typographic double quotes → straight
    # German opening „ (U+201E) and closing " (U+201C)
    result = result.replace("„", '"')
    result = result.replace(""", '"')
    result = result.replace(""", '"')  # U+201D closing quote

    # 3. Typographic single quotes → straight
    result = result.replace("'", "'")  # U+2018 left single
    result = result.replace("'", "'")  # U+2019 right single
    result = result.replace("‚", "'")  # U+201A single low-9

    # 4. Numeric HTML entities (common ones)
    # &#160; = non-breaking space
    result = re.sub(r'&#160;', ' ', result)
    # &#8211; = en-dash
    result = re.sub(r'&#8211;', '–', result)
    # &#8212; = em-dash
    result = re.sub(r'&#8212;', '—', result)

    log.debug("[FIX-523A][HTML-CONTRACT] normalize_typos_and_entities applied")
    return result


def validate_quick_wins_rendered(html: str) -> bool:
    """
    Check if QuickWins section is properly rendered.

    Returns True if QuickWins appears to be rendered HTML (not raw JSON).
    """
    violations = _check_quickwins_markers(html)
    return len([v for v in violations if v.critical]) == 0


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[FIX-505][HTML-CONTRACT] Module loaded: strict=%d max_repair=%d "
    "required_sections=%d optional_sections=%d",
    int(RELEASE_STRICT_MODE), MAX_REPAIR_ATTEMPTS,
    len(REQUIRED_SECTIONS), len(OPTIONAL_SECTIONS)
)
