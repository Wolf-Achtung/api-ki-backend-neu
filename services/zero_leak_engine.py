# -*- coding: utf-8 -*-
"""
SPRINT N3.6 PACKAGE E: Zero-Leak Layer v3.

Comprehensive GPT leak detection and removal:
- 200+ leak phrases with fuzzy matching
- Full-sentence replacement
- Guarantee: PDF never fails due to leaks

Version: 1.2.2 (N3.6 + CRITICAL vs BENIGN + systemprompt false-positive fix)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Pattern, Tuple

log = logging.getLogger(__name__)


# =============================================================================
# CRITICAL LEAK PATTERNS - Real security risks (FAIL-CLOSED)
# =============================================================================
# These indicate actual prompt/policy/secret leakage. If detected → suppress section.

# String-based CRITICAL patterns (exact substring match, case-insensitive)
CRITICAL_LEAK_PATTERNS: List[str] = [
    # System/developer prompt references
    "system prompt",
    # NOTE: "systemprompt" moved to BENIGN (v1.2.2) - German word appears in explanatory text
    "developer prompt",
    "developer message",
    "system message",
    "system instruction",
    "hidden instruction",
    "internal instruction",
    "my instructions",
    "my prompt",
    "I was instructed",
    "I have been instructed",
    "according to my instructions",
    "based on my instructions",
    # Policy/tooling references
    "OpenAI policy",
    "Anthropic policy",
    "usage policy",
    "content policy",
    "I can't reveal",
    "I cannot reveal",
    "I'm not allowed to",
    "I am not allowed to",
    "I must not",
    "I cannot disclose",
    "I can't disclose",
    # NOTE: "prompt injection" moved to ALLOWED_SECURITY_TERMS (FIX-529) - legitimate security term
    # "prompt injection",
    "jailbreak",
    # NOTE: "chain-of-thought" moved to BENIGN (v1.2.1) - appears in legitimate strategy text
    "function call",
    "tool call",
    "tool use",
    # Secrets/credentials (string patterns)
    "API key",
    "api_key",
    "Bearer ",
    "Authorization:",
    # NOTE: "sk-" removed (v1.2.1) - replaced with regex pattern below
    "OPENAI_API",
    "secret key",
    "access token",
    "password:",
    "credential",
    # Meta-responses about restrictions
    "as an AI model I",
    "as an AI, I",
    "as a large language model",
    "my programming prevents",
    "my guidelines",
    "violates my",
    "against my programming",
    "I'm programmed to",
    "I am programmed to",
]

# Regex-based CRITICAL patterns for complex detection (compiled for performance)
# Each tuple: (compiled_pattern, label_for_logging)
CRITICAL_LEAK_REGEX: List[Tuple[Pattern, str]] = [
    # OpenAI API key pattern: sk- followed by 16+ alphanumeric chars
    (re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"), "OpenAI_API_Key"),
    # Anthropic API key pattern: sk-ant- followed by alphanumeric
    (re.compile(r"\bsk-ant-[A-Za-z0-9]{16,}\b"), "Anthropic_API_Key"),
    # Generic secret patterns with key-like structure
    (re.compile(r"\b[A-Za-z0-9_]*(SECRET|KEY|TOKEN)[A-Za-z0-9_]*\s*[=:]\s*['\"][A-Za-z0-9+/=]{20,}['\"]", re.IGNORECASE), "Exposed_Secret"),
]

# =============================================================================
# FIX-529: ALLOWED SECURITY TERMS - Legitimate in risk/security context
# =============================================================================
# These terms are legitimate security terminology that should NOT trigger
# blacklist detection when appearing in risk analysis, AI Act compliance,
# or security awareness sections.
#
# Context: These terms describe real security risks that users need to know about.
# Blocking them would prevent accurate security communication.

ALLOWED_SECURITY_TERMS: List[str] = [
    # Security attack vectors (legitimate to discuss in risk context)
    "prompt injection",
    "Prompt-Injection",
    "Prompt Injection",
    "injection attack",
    "Injection-Angriff",
    # Data security terms
    "data exfiltration",
    "Datenexfiltration",
    # AI security terms
    "adversarial attack",
    "model poisoning",
    # Access control terms
    "privilege escalation",
    "unauthorized access",
    # FIX-618: Credential management terms (legitimate in risk/security context)
    "credential",
    "Credential-Management",
    "Credential Theft",
    "Credential Stuffing",
]

# Sections where security terms are explicitly allowed
SECURITY_CONTEXT_SECTIONS: List[str] = [
    "RISKS_HTML",
    "risks",                  # FIX-618: shadow key also scanned by precommit_zero_leak
    "RISKS_LIGHT_HTML",
    "RISK_ENGINE_HTML",
    "RISK_ENGINE_V3_HTML",
    "AI_ACT_HTML",
    "SECURITY_HTML",
    "DATA_SECURITY_HTML",
    "COMPLIANCE_HTML",
    # FIX-620: TOOLS_EMPFEHLUNGEN legitimately discusses Credential-Management,
    # Identity & Access Management, etc. - not actual credential leaks
    "TOOLS_EMPFEHLUNGEN_HTML",
    "tools_empfehlungen",
]

# =============================================================================
# BENIGN CHATBOT PHRASES - Safe to remove (CLEAN-AND-KEEP)
# =============================================================================
# These are just chatbot meta-phrases (help offers, context requests).
# Removing them is safe; no need to suppress the entire section.

BENIGN_CHATBOT_PHRASES: List[str] = [
    # v1.2.1: Chain-of-thought moved from CRITICAL (appears in legitimate strategy text)
    "chain-of-thought",
    "chain of thought",
    # v1.2.2: systemprompt moved from CRITICAL (German "Systemprompt" in explanatory text)
    "systemprompt",
    "Systemprompt",
    # German assistant phrases
    "wie kann ich dir helfen",
    "wie kann ich Ihnen helfen",
    "wie kann ich ihnen helfen",
    "ich helfe Ihnen gern",
    "ich helfe ihnen gern",
    "gern helfe ich Ihnen",
    "gerne helfe ich Ihnen",
    "gerne helfe ich ihnen",
    "als KI kann ich",
    "als KI-Assistent",
    "als KI-Modell",
    "ich bin ein KI-Modell",
    "ich bin ein KI-Assistent",
    "als künstliche Intelligenz",
    "ich bin eine künstliche Intelligenz",
    # FINAL GO FIX: Meta-commentary phrases (LLM safety responses)
    "ich sehe keine konkrete frage",
    "ich sehe keine konkrete aufgabe",
    "ich sehe keine frage",
    "ich sehe keine aufgabe",
    "keine konkrete frage",
    "keine konkrete aufgabe",
    "bitte beschreibe kurz dein anliegen",
    "bitte beschreiben sie kurz ihr anliegen",
    "ich benötige weitere informationen",
    "ohne weitere angaben kann ich",
    "mir fehlen die nötigen informationen",
    # FINAL GO FIX v2: Additional meta-commentary and help-prompt phrases
    "du hast noch keine frage",
    "du hast noch keine aufgabe",
    "sie haben noch keine frage",
    "sie haben noch keine aufgabe",
    "beschreibe dein anliegen",
    "beschreiben sie ihr anliegen",
    "schreib mir, wobei ich dir helfen",
    "schreiben sie mir, wobei ich ihnen helfen",
    "dann antworte ich",
    "dann werde ich antworten",
    "wobei ich dir helfen soll",
    "wobei ich ihnen helfen soll",
    # FIX-517C: Chat/questionnaire artifact phrases
    "wobei kann ich dir helfen",
    "wobei kann ich Ihnen helfen",
    "wobei kann ich ihnen helfen",
    "bitte nenne kurz",
    "bitte nennen sie kurz",
    # English assistant phrases
    "how can I help you",
    "how may I assist you",
    "I'm happy to help",
    "as an AI",
    "as an AI assistant",
    "as a language model",
    "I am an AI",
    "I'm an AI",
    # English meta-commentary
    "I don't see a specific question",
    "I don't see a question",
    "please describe your request",
    "I need more information",
    "you haven't asked a question",
    "you have not asked a question",
    "describe what you need help with",
    "tell me what you need",
    # FINAL GO FIX v3: Fragment patterns (remnants after partial cleanup)
    "oder aufgabe in deiner nachricht",
    "oder frage in deiner nachricht",
    "aufgabe in deiner nachricht",
    "frage in deiner nachricht",
    "in deiner nachricht",
    "in ihrer nachricht",
    "or task in your message",
    "or question in your message",
    "in your message",
    # WP3: Additional assistant leak phrases for robust detection
    "ich kann dir helfen",
    "ich kann Ihnen helfen",
    "ich kann ihnen helfen",
    "als KI",
    "Gerne erstelle ich",
    "Gerne zeige ich",
    "Gerne erläutere ich",
    "Natürlich kann ich",
    "Selbstverständlich kann ich",
    "Hier sind einige",
    "Hier finden Sie",
    "Of course,",
    "Of course!",
    "Sure,",
    "Sure!",
    "Here is",
    "Here are",
    "Let me help",
    "I'd be happy to",
    "I would be happy to",
    "Certainly,",
    "Certainly!",
]

# Executive sections that require hard blacklist enforcement
EXECUTIVE_SECTIONS: List[str] = [
    "EXECUTIVE_SUMMARY_HTML",
    "EXECUTIVE_DECISION_HTML",
    "ROADMAP_90D_DECISION_HTML",
    "GAMECHANGER_DECISION_HTML",
    "KI_STACK_SUMMARY_HTML",
    "BRANCH_DEEP_DIVE_HTML",  # FINAL GO: Add to prevent assistant text
]

# =============================================================================
# --- FIX-52x: strip prompt-echo chat phrases at the very beginning only ---
def _strip_prompt_echo_prefix(text: str, phrases: List[str]) -> tuple:
    """
    Remove prompt-echo phrases that appear only in the first ~400 chars / 6 lines.
    These are artifacts where the LLM echoes parts of the prompt at the start.
    Returns (cleaned_text, count_of_removed_lines).
    """
    if not text:
        return text, 0
    head = text[:400]  # only inspect prefix to avoid hiding real content issues
    removed = 0
    for ph in phrases:
        if ph.lower() in head.lower():
            # remove the whole line containing the phrase within the prefix
            lines = text.splitlines()
            new_lines = []
            for i, ln in enumerate(lines):
                if i <= 6 and ph.lower() in ln.lower():
                    removed += 1
                    continue
                new_lines.append(ln)
            text = "\n".join(new_lines)
    return text, removed


# =============================================================================
# FIX-526 P3: DETERMINISTIC PRESCRUB PHRASES
# =============================================================================
# These phrases are deterministically scrubbed BEFORE the critical scan.
# They are template/prompt leaks that should be cleaned without triggering FAIL-CLOSED.
# This prevents unnecessary regeneration cycles for recoverable template artifacts.
DETERMINISTIC_PRESCRUB_PHRASES: List[str] = [
    # Template prompt echoes
    "bitte beschreibe kurz",
    "bitte beschreiben sie kurz",
    "Bitte beschreibe kurz",
    "Bitte beschreiben Sie kurz",
    "bitte beschreib kurz",
    # Context requests that slip through
    "beschreibe kurz dein anliegen",
    "beschreiben sie kurz ihr anliegen",
    # Template markers
    "Beispiel-Workflow",
    "Beispiel-Ablauf",
    "Platzhalter",
    "Template-Text",
    # FIX-629: Help-offer phrases REMOVED from prescrub → now HARD-BLOCK
    # in EXECUTIVE_SECTIONS via EXECUTIVE_CRITICAL_PHRASES.
    # Reverses FIX-620: prescrub silently removed these, masking broken
    # chat-style responses (GPT-5.2 "wie kann ich dir helfen" in decision
    # sections). Now triggers FAIL-CLOSED + regeneration for executive sections,
    # while BENIGN_CHATBOT_PHRASES still handles them in non-executive sections.
    # Chat introduction artifacts
    "Hier ist",
    "Natürlich,",
    "Natürlich!",
    "Selbstverständlich,",
    "Selbstverständlich!",
    "Gerne!",
    "Gerne,",
    # WP3: Additional assistant leak phrases (DE/EN)
    "ich kann dir helfen",
    "ich kann Ihnen helfen",
    "als KI",
    "Hier sind",
    "Hier finden Sie",
    "Gerne erstelle ich",
    "Gerne zeige ich",
    "Gerne erläutere ich",
    "Natürlich kann ich",
    "Selbstverständlich kann ich",
    "Of course,",
    "Of course!",
    "Sure,",
    "Sure!",
    "Here is",
    "Here are",
    "Let me help",
    "I'd be happy to",
    "I would be happy to",
    "Certainly,",
    "Certainly!",
    # FIX-R5-2: Prompt-Leak patterns (Ziel/Branche/Daten/KPI prompt fragments)
    "Ihr Ziel (z. B.",
    "Ihr Ziel (z.B.",
    "Kontext/Branche",
    "Welche Daten/Quellen",
    "Erfolgskriterien (KPIs)",
    "Erfolgskriterien (KPI)",
    "nenne auch Ihre größten",
    # FIX-R5-3: Duzen/Siezen-Mix — grammatically broken prompt leak
    "Wenn Sie magst",
    "wenn Sie magst",
]


# Fix-Batch A3: EXECUTIVE_CRITICAL_PHRASES
# =============================================================================
# These phrases are CRITICAL (fail-closed) ONLY when found in EXECUTIVE_SECTIONS.
# They are chat/assistant artifacts that should NEVER appear in executive summaries.
# In other sections, they remain BENIGN (clean-and-keep).
# FIX-526: "bitte beschreibe kurz" moved to DETERMINISTIC_PRESCRUB_PHRASES (scrub before fail-closed)
EXECUTIVE_CRITICAL_PHRASES: List[str] = [
    # KI-Assistenz Identifikation
    "ich bin ein KI-Assistent",
    "ich bin ein KI-Modell",
    "als KI-Assistent",
    "als KI-Modell",
    "als künstliche Intelligenz",
    # Hilfsangebote
    "gerne erkläre ich",
    "gerne helfe ich",
    "gern helfe ich",
    "wie kann ich dir helfen",
    "wie kann ich Ihnen helfen",
    "wie kann ich ihnen helfen",
    "wobei kann ich helfen",
    "wobei ich dir helfen",
    "wobei ich Ihnen helfen",
    # Meta-Kommentare (FIX-526: "bitte beschreibe kurz" moved to prescrub)
    "ich sehe keine konkrete frage",
    "ich sehe keine konkrete aufgabe",
    "ich sehe keine frage",
    "ich sehe keine aufgabe",
    "keine konkrete frage",
    "keine konkrete aufgabe",
    # English variants
    "I am an AI assistant",
    "I'm an AI assistant",
    "as an AI assistant",
    "how can I help you",
    "how may I assist you",
    "I don't see a specific question",
    "I don't see a question",
]

# Dual-key aliases: If we clean EXECUTIVE_SUMMARY_HTML, also clean executive_summary
DUAL_KEY_ALIASES: Dict[str, str] = {
    "EXECUTIVE_SUMMARY_HTML": "executive_summary",
    "EXECUTIVE_DECISION_HTML": "executive_decision",
    "ROADMAP_90D_DECISION_HTML": "roadmap_90d_decision",
    "GAMECHANGER_DECISION_HTML": "gamechanger_decision",
    "KI_STACK_SUMMARY_HTML": "ki_stack_summary",
    "BRANCH_DEEP_DIVE_HTML": "branch_deep_dive",
    "ROADMAP_SPRINT_HTML": "roadmap_sprint",
    "QUICK_WINS_HTML": "quick_wins",
    "BUSINESSCASE_HTML": "businesscase",
    "GAMECHANGER_HTML": "gamechanger",
    "RISIKEN_CHANCEN_HTML": "risiken_chancen",
    "PROZESSCHECK_HTML": "prozesscheck",
    "DATENSTRATEGIE_HTML": "datenstrategie",
    "MITARBEITER_ENABLEMENT_HTML": "mitarbeiter_enablement",
    "RESPONSIBLE_AI_HTML": "responsible_ai",
}


@dataclass
class BlacklistResult:
    """Result of blacklist application with CRITICAL vs BENIGN classification."""
    cleaned_text: str
    critical_hits: List[str] = field(default_factory=list)
    benign_hits: List[str] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return len(self.critical_hits) > 0

    @property
    def has_benign(self) -> bool:
        return len(self.benign_hits) > 0

    @property
    def all_removed(self) -> List[str]:
        return self.critical_hits + self.benign_hits


def apply_hard_blacklist(text: str, section_name: str = "") -> Tuple[str, List[str]]:
    """
    Apply hard blacklist to remove forbidden assistant phrases.

    LEGACY wrapper - returns (cleaned_text, all_removed_phrases).
    For new code, use apply_blacklist_classified() instead.
    """
    result = apply_blacklist_classified(text, section_name)
    return result.cleaned_text, result.all_removed


def apply_blacklist_classified(text: str, section_name: str = "") -> BlacklistResult:
    """
    Apply blacklist with CRITICAL vs BENIGN classification.

    v1.2.0: Separates critical leaks (suppress section) from benign chatbot
    phrases (safe to remove and keep content).
    v1.2.1: Added regex-based CRITICAL patterns for API keys; improved logging.
    v1.2.2: systemprompt moved to BENIGN; added debug logging for root cause.

    Args:
        text: Input text/HTML
        section_name: Section name for logging context

    Returns:
        BlacklistResult with cleaned_text, critical_hits, benign_hits
    """
    if not text:
        return BlacklistResult(cleaned_text=text)

    # v1.2.2: Debug logging for DATA_READINESS to identify root cause of systemprompt hits
    if section_name and "DATA_READINESS" in section_name.upper():
        # Check for systemprompt variants (case-insensitive)
        text_lower = text.lower()
        if "systemprompt" in text_lower:
            # Find position and extract context window (120 chars, sanitized)
            pos = text_lower.find("systemprompt")
            start = max(0, pos - 40)
            end = min(len(text), pos + 80)
            context = text[start:end]
            # Sanitize: remove angle brackets and quotes to avoid log injection
            context = context.replace("<", "[").replace(">", "]").replace('"', "'").replace("\n", " ")
            log.info(
                "[zero-leak-debug] section=%s contains_systemprompt=True context=\"...%s...\"",
                section_name,
                context[:120]
            )

    critical_hits: List[str] = []
    benign_hits: List[str] = []
    prescrub_count: int = 0
    cleaned = text

    # FIX-526 P3: Deterministic prescrub - remove template phrases BEFORE critical scan
    # This prevents FAIL-CLOSED for recoverable template artifacts
    for phrase in DETERMINISTIC_PRESCRUB_PHRASES:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        matches = pattern.findall(cleaned)
        if matches:
            cleaned = pattern.sub("", cleaned)
            prescrub_count += len(matches)
            log.debug(
                '[zero-leak-prescrub] phrase="%s" hits=%d section=%s (no fail-closed)',
                phrase[:30],
                len(matches),
                section_name or "unknown"
            )

    if prescrub_count > 0:
        # Clean up double spaces from removals
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        log.info(
            "[FIX-526][PRESCRUB] Removed %d template phrases from %s (no fail-closed triggered)",
            prescrub_count,
            section_name or "unknown"
        )

    # FIX-618: Determine if this section is a security context section
    # In security context sections, allowed security terms should not trigger FAIL-CLOSED
    _is_security_context = section_name in SECURITY_CONTEXT_SECTIONS

    # Check CRITICAL string patterns first
    for phrase in CRITICAL_LEAK_PATTERNS:
        # FIX-618: Skip allowed security terms in security-context sections
        # e.g. "credential" is legitimate in RISKS_HTML when discussing Credential Management
        if _is_security_context and any(
            phrase.lower() in allowed_term.lower() or allowed_term.lower() in phrase.lower()
            for allowed_term in ALLOWED_SECURITY_TERMS
        ):
            continue
        # FIX-618: Context-sensitive "credential" check - only flag if it looks like
        # actual credential leakage (e.g. "credential: xxx", "credential=")
        # not when used as a security term (e.g. "Credential-Management", "Credential Theft")
        if phrase.lower() == "credential" and _is_security_context:
            continue

        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        matches = pattern.findall(cleaned)

        if matches:
            # Log with pattern label for auditability
            log.warning(
                '[leak_blacklist] CRITICAL pattern="%s" hits=%d section=%s',
                phrase[:30],  # Truncate long patterns
                len(matches),
                section_name or "unknown"
            )
            critical_hits.extend(matches)
            cleaned = pattern.sub("", cleaned)

    # Check CRITICAL regex patterns (for API keys, secrets)
    for regex_pattern, label in CRITICAL_LEAK_REGEX:
        matches = regex_pattern.findall(cleaned)

        if matches:
            log.warning(
                '[leak_blacklist] CRITICAL regex=%s hits=%d section=%s',
                label,
                len(matches),
                section_name or "unknown"
            )
            # Store label instead of actual match (avoid logging secrets)
            critical_hits.extend([f"[{label}]"] * len(matches))
            cleaned = regex_pattern.sub("", cleaned)

    # Fix-Batch A3: Check EXECUTIVE_CRITICAL_PHRASES for executive sections
    # These are CRITICAL only in EXECUTIVE_SECTIONS (causes fail-closed)
    is_executive_section = section_name in EXECUTIVE_SECTIONS
    if is_executive_section:
        # --- FIX-52x: strip prompt-echo prefix lines before critical scan ---
        cleaned, stripped = _strip_prompt_echo_prefix(cleaned, EXECUTIVE_CRITICAL_PHRASES)
        if stripped > 0:
            log.info(f"[FIX-52x][ZERO-LEAK] stripped_prompt_echo_lines={stripped} section={section_name} (prefix_only=True)")

        # FIX-618: Build set of prescrub phrases (lowercase) to skip double-detection
        _prescrub_set = {p.lower() for p in DETERMINISTIC_PRESCRUB_PHRASES}

        for phrase in EXECUTIVE_CRITICAL_PHRASES:
            # FIX-618: Skip phrases already handled by prescrub to prevent
            # race condition where prescrub removes the phrase but executive
            # critical scan still detects remnants or case variants
            if phrase.lower() in _prescrub_set:
                continue

            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            matches = pattern.findall(cleaned)

            if matches:
                log.warning(
                    '[leak_blacklist] EXECUTIVE_CRITICAL phrase="%s" hits=%d section=%s → FAIL-CLOSED',
                    phrase[:40],
                    len(matches),
                    section_name
                )
                critical_hits.extend(matches)
                cleaned = pattern.sub("", cleaned)

    # Check BENIGN chatbot phrases
    for phrase in BENIGN_CHATBOT_PHRASES:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        matches = pattern.findall(cleaned)

        if matches:
            for match in matches:
                log.debug(
                    '[leak_blacklist] benign phrase removed: "%s" (section=%s)',
                    match,
                    section_name or "unknown"
                )
                benign_hits.append(match)
            cleaned = pattern.sub("", cleaned)

    # Cleanup artifacts (double spaces, empty tags)
    if critical_hits or benign_hits:
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        cleaned = re.sub(r'<p>\s*</p>', '', cleaned)
        cleaned = re.sub(r'<li>\s*</li>', '', cleaned)
        cleaned = re.sub(r'\.\s*\.', '.', cleaned)
        # FIX: Remove empty angle brackets <> that remain after phrase removal
        cleaned = re.sub(r'<\s*>', '', cleaned)

    return BlacklistResult(
        cleaned_text=cleaned.strip(),
        critical_hits=critical_hits,
        benign_hits=benign_hits,
    )


def process_executive_sections_blacklist(
    sections: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
    """
    Apply hard blacklist specifically to executive sections.

    Args:
        sections: Section dictionary

    Returns:
        Tuple of (cleaned_sections, removed_phrases_by_section)
    """
    cleaned = dict(sections)
    removed_by_section: Dict[str, List[str]] = {}

    for section_name in EXECUTIVE_SECTIONS:
        content = sections.get(section_name)
        if not content or not isinstance(content, str):
            continue

        cleaned_content, removed = apply_hard_blacklist(content, section_name)

        if removed:
            cleaned[section_name] = cleaned_content
            removed_by_section[section_name] = removed
            log.info(
                "[leak_blacklist] Executive section %s: %d phrases removed",
                section_name, len(removed)
            )

    return cleaned, removed_by_section


# =============================================================================
# LEAK PHRASES DATABASE (200+)
# =============================================================================

# Category 1: Direct AI/Assistant references (40 phrases)
AI_REFERENCE_LEAKS: List[str] = [
    "ich bin ein KI",
    "als KI-Assistent",
    "als KI-Modell",
    "als künstliche Intelligenz",
    "als Sprachmodell",
    "ich bin ein Sprachmodell",
    "ich bin ChatGPT",
    "ich bin Claude",
    "ich bin GPT",
    "als AI assistant",
    "as an AI",
    "I'm an AI",
    "I am an AI",
    "as a language model",
    "ich wurde trainiert",
    "mein Training",
    "meine Trainingsdaten",
    "Stand meines Wissens",
    "my knowledge cutoff",
    "mein Wissensstand",
    "ich habe keinen Zugriff",
    "I don't have access",
    "ich kann keine Echtzeit",
    "ich kann nicht auf das Internet",
    "ich habe keine Möglichkeit",
    "es liegt außerhalb meiner Fähigkeiten",
    "das übersteigt meine Kapazitäten",
    "ich bin nicht in der Lage",
    "I cannot",
    "I'm not able to",
    "ich verfüge nicht über",
    "mir fehlt die Fähigkeit",
    "das ist mir nicht möglich",
    "leider kann ich nicht",
    "bedauerlicherweise ist es mir nicht möglich",
    "ich muss darauf hinweisen dass ich",
    "als KI muss ich",
    "meine Einschränkungen",
    "aufgrund meiner Beschränkungen",
    "innerhalb meiner Grenzen",
]

# Category 2: Support/Help offers (30 phrases)
SUPPORT_LEAKS: List[str] = [
    "wie kann ich helfen",
    "wie kann ich Ihnen helfen",
    "kann ich Ihnen behilflich sein",
    "wobei kann ich helfen",
    "gerne helfe ich",
    "ich helfe Ihnen gerne",
    "bei Fragen stehe ich",
    "für Rückfragen stehe ich",
    "wenden Sie sich bitte an",
    "kontaktieren Sie bitte",
    "erreichen Sie uns unter",
    "unser Support-Team",
    "unser Kundenservice",
    "unsere Hotline",
    "rufen Sie uns an",
    "schreiben Sie uns",
    "senden Sie eine E-Mail",
    "füllen Sie das Formular aus",
    "besuchen Sie unsere Website",
    "weitere Informationen finden Sie",
    "mehr dazu erfahren Sie",
    "für weitere Details",
    "bei Interesse",
    "sollten Sie Fragen haben",
    "falls Sie Unterstützung benötigen",
    "zögern Sie nicht",
    "melden Sie sich gerne",
    "sprechen Sie uns an",
    "nehmen Sie Kontakt auf",
    "wir freuen uns auf Ihre Anfrage",
]

# Category 3: Conversational fillers (40 phrases)
FILLER_LEAKS: List[str] = [
    "natürlich",
    "selbstverständlich",
    "absolut",
    "definitiv",
    "auf jeden Fall",
    "zweifellos",
    "ohne Zweifel",
    "ganz klar",
    "das ist richtig",
    "Sie haben Recht",
    "das stimmt",
    "genau",
    "exakt",
    "präzise",
    "in der Tat",
    "tatsächlich ist es so",
    "ehrlich gesagt",
    "um ehrlich zu sein",
    "ich muss zugeben",
    "ich würde sagen",
    "ich denke",
    "meiner Meinung nach",
    "meines Erachtens",
    "aus meiner Sicht",
    "persönlich finde ich",
    "ich glaube",
    "ich vermute",
    "möglicherweise",
    "eventuell",
    "unter Umständen",
    "es könnte sein",
    "es ist denkbar",
    "interessanterweise",
    "überraschenderweise",
    "bemerkenswerterweise",
    "erstaunlicherweise",
    "bezeichnenderweise",
    "wichtig zu wissen ist",
    "es sei darauf hingewiesen",
    "nicht zu vergessen",
]

# Category 4: Introduction fluff (30 phrases)
INTRO_LEAKS: List[str] = [
    "in diesem Abschnitt",
    "nachfolgend wird",
    "im Folgenden",
    "wie bereits erwähnt",
    "wie oben beschrieben",
    "wie eingangs erläutert",
    "zunächst einmal",
    "erst einmal",
    "zu Beginn",
    "einleitend",
    "vorab",
    "zuallererst",
    "an erster Stelle",
    "bevor wir beginnen",
    "lassen Sie uns",
    "lassen Sie mich",
    "erlauben Sie mir",
    "gestatten Sie",
    "ich möchte",
    "ich werde",
    "ich würde gerne",
    "in diesem Zusammenhang",
    "in diesem Kontext",
    "diesbezüglich",
    "hinsichtlich",
    "bezüglich",
    "was das betrifft",
    "was das angeht",
    "wenn es um",
    "wenn wir über",
]

# Category 5: Conclusion fluff (30 phrases)
CONCLUSION_LEAKS: List[str] = [
    "zusammenfassend",
    "abschließend",
    "zum Schluss",
    "zum Abschluss",
    "insgesamt",
    "alles in allem",
    "im Großen und Ganzen",
    "unter dem Strich",
    "summa summarum",
    "resümierend",
    "fazit",
    "schlussendlich",
    "letztendlich",
    "letzten Endes",
    "im Endeffekt",
    "im Ergebnis",
    "als Fazit",
    "zusammenfassend lässt sich sagen",
    "abschließend sei erwähnt",
    "abschließend ist festzuhalten",
    "es bleibt festzuhalten",
    "es lässt sich festhalten",
    "es zeigt sich",
    "es wird deutlich",
    "klar wird",
    "deutlich wird",
    "offensichtlich",
    "ersichtlich",
    "erkennbar",
    "last but not least",
]

# Category 6: Generic/vague phrases (30 phrases)
VAGUE_LEAKS: List[str] = [
    "Dinge",
    "Sachen",
    "irgendwie",
    "irgendwas",
    "irgendwann",
    "irgendwo",
    "gewissermaßen",
    "sozusagen",
    "quasi",
    "praktisch",
    "im Prinzip",
    "im Grunde",
    "grundsätzlich",
    "generell",
    "allgemein",
    "prinzipiell",
    "theoretisch",
    "normalerweise",
    "üblicherweise",
    "in der Regel",
    "typischerweise",
    "gewöhnlich",
    "für gewöhnlich",
    "mehr oder weniger",
    "bis zu einem gewissen Grad",
    "in gewisser Weise",
    "auf gewisse Weise",
    "ein bisschen",
    "ein wenig",
    "etwas",
]

# Combine all leaks
ALL_LEAK_PHRASES: List[str] = (
    AI_REFERENCE_LEAKS +
    SUPPORT_LEAKS +
    FILLER_LEAKS +
    INTRO_LEAKS +
    CONCLUSION_LEAKS +
    VAGUE_LEAKS
)


# =============================================================================
# FUZZY MATCHING PATTERNS
# =============================================================================

# Regex patterns for fuzzy matching
FUZZY_LEAK_PATTERNS: List[Tuple[str, str]] = [
    # AI references
    (r'(ich\s+bin\s+(?:ein|eine)\s+(?:KI|AI|künstliche))', ""),
    (r'(als\s+(?:KI|AI|Sprach)\s*(?:modell|assistent)?)', ""),
    (r'(kann.*?ich.*?helfen)', ""),
    (r'(wenden.*?(?:sich|Sie).*?an)', ""),
    (r'(support.*?team)', ""),
    (r'(bei\s+fragen.*?kontakt)', ""),
    (r'(mein(?:e|es)?\s+(?:Training|Wissen|Daten))', ""),

    # Conversational
    (r'(ich\s+(?:denke|glaube|vermute|meine))', "Die Analyse zeigt"),
    (r'(meiner\s+Meinung\s+nach)', "Basierend auf der Evaluation"),
    (r'(aus\s+meiner\s+Sicht)', "Aus fachlicher Perspektive"),

    # Filler cleanup
    (r'(natürlich\s*,?\s*)', ""),
    (r'(selbstverständlich\s*,?\s*)', ""),
    (r'(absolut\s*,?\s*)', ""),

    # Intro/conclusion
    (r'(zusammenfassend\s+(?:lässt\s+sich\s+)?(?:sagen|festhalten)?)', "Im Ergebnis"),
    (r'(abschließend\s+(?:sei|ist|lässt)?)', "Resultierend"),
    (r'(in\s+diesem\s+(?:Abschnitt|Zusammenhang))', ""),
]


# =============================================================================
# CONSULTING-STYLE REPLACEMENTS
# =============================================================================

# Replacement sentences for removed content
CONSULTING_REPLACEMENTS: Dict[str, str] = {
    "intro": "Die nachfolgende Analyse basiert auf systematischer Evaluation der relevanten Faktoren.",
    "conclusion": "Die strategische Handlungsempfehlung ergibt sich aus der Gesamtbewertung.",
    "support": "",  # Just remove support phrases
    "ai_reference": "",  # Just remove AI references
    "filler": "",  # Just remove fillers
    "vague": "",  # Just remove vague phrases
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class LeakDetectionResult:
    """Result of leak detection."""
    phrase: str
    category: str
    position: int
    sentence: str
    replaced: bool = False
    replacement: str = ""


@dataclass
class ZeroLeakReport:
    """Report of zero-leak processing."""
    total_leaks_found: int = 0
    leaks_removed: int = 0
    sentences_removed: int = 0
    sentences_replaced: int = 0
    categories: Dict[str, int] = field(default_factory=dict)
    details: List[LeakDetectionResult] = field(default_factory=list)

    def add_leak(self, result: LeakDetectionResult) -> None:
        """Add a leak detection result."""
        self.total_leaks_found += 1
        self.details.append(result)

        category = result.category
        self.categories[category] = self.categories.get(category, 0) + 1

        if result.replaced:
            if result.replacement:
                self.sentences_replaced += 1
            else:
                self.sentences_removed += 1
            self.leaks_removed += 1


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def detect_leaks(text: str) -> List[LeakDetectionResult]:
    """
    N3.6: Detect all leak phrases in text.

    Args:
        text: Input text

    Returns:
        List of leak detection results
    """
    if not text:
        return []

    results: List[LeakDetectionResult] = []
    text_lower = text.lower()

    # Check exact phrases
    for phrase in ALL_LEAK_PHRASES:
        phrase_lower = phrase.lower()
        if phrase_lower in text_lower:
            # Find position and extract sentence
            pos = text_lower.find(phrase_lower)
            sentence = _extract_sentence(text, pos)

            # Determine category
            category = _categorize_leak(phrase)

            results.append(LeakDetectionResult(
                phrase=phrase,
                category=category,
                position=pos,
                sentence=sentence,
            ))

    # Check fuzzy patterns
    for pattern, replacement in FUZZY_LEAK_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Skip if already detected
            if any(r.position == match.start() for r in results):
                continue

            results.append(LeakDetectionResult(
                phrase=match.group(0),
                category="fuzzy",
                position=match.start(),
                sentence=_extract_sentence(text, match.start()),
            ))

    return results


def _extract_sentence(text: str, position: int) -> str:
    """Extract the sentence containing a position."""
    # Find sentence boundaries
    start = position
    while start > 0 and text[start - 1] not in '.!?\n':
        start -= 1

    end = position
    while end < len(text) and text[end] not in '.!?\n':
        end += 1

    return text[start:end + 1].strip()


def _categorize_leak(phrase: str) -> str:
    """Categorize a leak phrase."""
    phrase_lower = phrase.lower()

    if phrase in AI_REFERENCE_LEAKS or any(w in phrase_lower for w in ["ki", "ai", "training", "modell"]):
        return "ai_reference"
    if phrase in SUPPORT_LEAKS or any(w in phrase_lower for w in ["helfen", "kontakt", "support"]):
        return "support"
    if phrase in INTRO_LEAKS or any(w in phrase_lower for w in ["zunächst", "einleitend", "folgend"]):
        return "intro"
    if phrase in CONCLUSION_LEAKS or any(w in phrase_lower for w in ["zusammenfassend", "abschließend", "fazit"]):
        return "conclusion"
    if phrase in VAGUE_LEAKS:
        return "vague"
    return "filler"


def remove_leaks(text: str, aggressive: bool = False) -> Tuple[str, ZeroLeakReport]:
    """
    N3.6: Remove all detected leaks from text.

    Args:
        text: Input text
        aggressive: If True, removes entire sentences; if False, just phrases

    Returns:
        Tuple of (cleaned_text, report)
    """
    if not text:
        return text, ZeroLeakReport()

    report = ZeroLeakReport()
    cleaned = text

    # Detect all leaks
    leaks = detect_leaks(text)

    # Sort by position (reverse) to avoid position shifts
    leaks.sort(key=lambda x: x.position, reverse=True)

    for leak in leaks:
        report.add_leak(leak)

        if aggressive:
            # Remove entire sentence
            cleaned = cleaned.replace(leak.sentence, "")
            leak.replaced = True
            leak.replacement = ""
        else:
            # Just remove the phrase
            pattern = re.compile(re.escape(leak.phrase), re.IGNORECASE)
            cleaned = pattern.sub("", cleaned)
            leak.replaced = True

    # Apply fuzzy pattern replacements
    for fuzzy_pattern, replacement in FUZZY_LEAK_PATTERNS:
        cleaned = re.sub(fuzzy_pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Cleanup artifacts
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = re.sub(r'\.\s*\.', '.', cleaned)
    cleaned = re.sub(r',\s*,', ',', cleaned)
    cleaned = re.sub(r'<p>\s*</p>', '', cleaned)
    cleaned = re.sub(r'<li>\s*</li>', '', cleaned)
    # FIX: Remove empty angle brackets <> that remain after phrase removal
    cleaned = re.sub(r'<\s*>', '', cleaned)
    # FIX B: Remove standalone "?" placeholders (not in natural text like "Warum jetzt?")
    # Pattern: "?" alone in a tag, or "?" at start of line, or "??" sequences
    cleaned = re.sub(r'>\s*\?\s*<', '><', cleaned)  # "?" alone between tags
    cleaned = re.sub(r'^\s*\?\s*$', '', cleaned, flags=re.MULTILINE)  # "?" alone on line
    cleaned = re.sub(r'\?\?+', '—', cleaned)  # Multiple "?" become em-dash

    report.leaks_removed = len(leaks)

    if report.leaks_removed > 0:
        log.info(
            "[N3.6-ZeroLeak] Removed %d leaks (%d AI, %d support, %d filler)",
            report.leaks_removed,
            report.categories.get("ai_reference", 0),
            report.categories.get("support", 0),
            report.categories.get("filler", 0) + report.categories.get("fuzzy", 0)
        )

    return cleaned.strip(), report


def guarantee_leak_free(html: str) -> str:
    """
    N3.6 GUARANTEE: Ensure HTML is completely leak-free.

    This function guarantees that PDF generation will never fail
    due to leak content. If leaks cannot be properly replaced,
    they are simply removed.

    Args:
        html: Input HTML

    Returns:
        Leak-free HTML (guaranteed)
    """
    if not html:
        return html

    # First pass: Standard removal
    cleaned, report = remove_leaks(html, aggressive=False)

    # Second pass: Check for remaining leaks
    remaining_leaks = detect_leaks(cleaned)

    if remaining_leaks:
        log.warning(
            "[N3.6-ZeroLeak] %d leaks remaining after first pass, applying aggressive removal",
            len(remaining_leaks)
        )
        # Aggressive removal
        cleaned, _ = remove_leaks(cleaned, aggressive=True)

    # Final check
    final_leaks = detect_leaks(cleaned)
    if final_leaks:
        # Nuclear option: regex remove anything suspicious
        for leak in final_leaks:
            pattern = re.compile(re.escape(leak.phrase), re.IGNORECASE)
            cleaned = pattern.sub("", cleaned)

        log.warning(
            "[N3.6-ZeroLeak] Applied nuclear removal for %d stubborn leaks",
            len(final_leaks)
        )

    return cleaned


def process_sections_zero_leak(
    sections: Dict[str, Any],
) -> Tuple[Dict[str, Any], ZeroLeakReport]:
    """
    N3.6: Process all sections for zero-leak compliance.

    Now includes hard blacklist pre-processing for executive sections.

    Args:
        sections: Section dictionary

    Returns:
        Tuple of (cleaned_sections, aggregated_report)
    """
    # Step 1: Apply hard blacklist to executive sections FIRST
    cleaned, blacklist_removed = process_executive_sections_blacklist(sections)
    total_report = ZeroLeakReport()

    # Track blacklist removals in report
    for section_name, phrases in blacklist_removed.items():
        total_report.categories["hard_blacklist"] = (
            total_report.categories.get("hard_blacklist", 0) + len(phrases)
        )
        total_report.leaks_removed += len(phrases)
        total_report.total_leaks_found += len(phrases)

    # Step 2: Apply regular leak removal to all sections
    for section_id, content in cleaned.items():
        # Skip metadata
        if section_id.startswith("_"):
            continue

        # Skip non-string content
        if not isinstance(content, str):
            continue

        cleaned_content, report = remove_leaks(content)
        cleaned[section_id] = cleaned_content

        # Aggregate report
        total_report.total_leaks_found += report.total_leaks_found
        total_report.leaks_removed += report.leaks_removed
        total_report.sentences_removed += report.sentences_removed
        total_report.sentences_replaced += report.sentences_replaced

        for cat, count in report.categories.items():
            total_report.categories[cat] = total_report.categories.get(cat, 0) + count

    if total_report.leaks_removed > 0:
        log.info(
            "[N3.6-ZeroLeak] Sections processed: %d leaks removed total (hard_blacklist=%d)",
            total_report.leaks_removed,
            total_report.categories.get("hard_blacklist", 0)
        )

    return cleaned, total_report


def precommit_zero_leak_all_sections(
    sections: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Pre-commit zero-leak guard for ALL sections.

    This function runs IMMEDIATELY after section generation, BEFORE
    ReportValidator and N2-Healing. It applies the blacklist to
    ALL sections with dual-key hygiene.

    v1.2.0: CRITICAL vs BENIGN classification:
    - CRITICAL hits (prompt/policy/secrets) → FAIL-CLOSED (suppress section)
    - BENIGN hits only (chatbot phrases) → CLEAN-AND-KEEP (remove phrases, keep content)

    Fix-Batch C1: Now returns list of FAIL-CLOSED sections for regeneration.

    Features:
    - Runs on ALL section keys, not just EXECUTIVE_SECTIONS
    - Dual-key hygiene: cleans both *_HTML and lowercase aliases
    - FAIL-CLOSED only for CRITICAL leaks in EXECUTIVE_SECTIONS
    - CLEAN-AND-KEEP for benign-only hits (preserves important sections)
    - Logs: [zero-leak] FAIL-CLOSED / CLEAN-AND-KEEP

    Args:
        sections: Section dictionary from _generate_content_sections()

    Returns:
        Tuple of (cleaned_sections, fail_closed_section_keys)
    """
    cleaned = dict(sections)
    cleaned_count = 0
    total_critical = 0
    total_benign = 0
    fail_closed_sections: List[str] = []  # Fix-Batch C1: Track FAIL-CLOSED sections

    # Process all string sections
    for section_key, content in list(sections.items()):
        # Skip metadata and non-string content
        if section_key.startswith("_"):
            continue
        if not isinstance(content, str):
            continue
        if not content:
            continue

        # Apply blacklist with classification
        result = apply_blacklist_classified(content, section_key)

        # Decision logic for executive sections
        if section_key in EXECUTIVE_SECTIONS:
            if result.has_critical:
                # FAIL-CLOSED: Critical leak detected → suppress entire section
                log.warning(
                    "[zero-leak] FAIL-CLOSED critical_hits=%d section=%s (phrases: %s)",
                    len(result.critical_hits),
                    section_key,
                    ", ".join(result.critical_hits[:3]),  # Log first 3 for brevity
                )
                cleaned[section_key] = ""
                # Also suppress the alias
                alias_key = DUAL_KEY_ALIASES.get(section_key)
                if alias_key and alias_key in cleaned:
                    cleaned[alias_key] = ""
                cleaned_count += 1
                total_critical += len(result.critical_hits)
                # Fix-Batch C1: Track this section for regeneration
                fail_closed_sections.append(section_key)
                continue

            elif result.has_benign:
                # CLEAN-AND-KEEP: Only benign chatbot phrases → remove them, keep content
                log.info(
                    "[zero-leak] CLEAN-AND-KEEP benign_hits=%d section=%s",
                    len(result.benign_hits),
                    section_key,
                )
                cleaned[section_key] = result.cleaned_text
                cleaned_count += 1
                total_benign += len(result.benign_hits)

                # Also clean the alias
                alias_key = DUAL_KEY_ALIASES.get(section_key)
                if alias_key and alias_key in cleaned:
                    alias_content = cleaned.get(alias_key)
                    if isinstance(alias_content, str) and alias_content:
                        alias_result = apply_blacklist_classified(alias_content, alias_key)
                        if alias_result.has_benign and not alias_result.has_critical:
                            cleaned[alias_key] = alias_result.cleaned_text
                continue

        # Non-executive sections: always clean and keep (no suppression)
        if result.has_critical or result.has_benign:
            cleaned[section_key] = result.cleaned_text
            cleaned_count += 1
            total_critical += len(result.critical_hits)
            total_benign += len(result.benign_hits)

            # Dual-key hygiene: also clean the alias if exists
            alias_key = DUAL_KEY_ALIASES.get(section_key)
            if alias_key and alias_key in cleaned:
                alias_content = cleaned.get(alias_key)
                if isinstance(alias_content, str) and alias_content:
                    alias_result = apply_blacklist_classified(alias_content, alias_key)
                    if alias_result.all_removed:
                        cleaned[alias_key] = alias_result.cleaned_text
                        log.debug(
                            "[leak_blacklist] Also cleaned alias %s (%d phrases)",
                            alias_key, len(alias_result.all_removed)
                        )

    # Also check reverse: lowercase keys that have uppercase aliases
    reverse_aliases = {v: k for k, v in DUAL_KEY_ALIASES.items()}
    for section_key, content in list(sections.items()):
        if section_key.startswith("_"):
            continue
        if not isinstance(content, str) or not content:
            continue
        if section_key in DUAL_KEY_ALIASES:
            continue  # Already processed above

        # Check if this lowercase key has an uppercase alias
        uppercase_key = reverse_aliases.get(section_key)
        if uppercase_key:
            # Already handled via dual-key hygiene above
            continue

        # Apply blacklist to remaining sections (non-executive, always keep)
        result = apply_blacklist_classified(content, section_key)
        if result.all_removed:
            cleaned[section_key] = result.cleaned_text
            cleaned_count += 1
            total_critical += len(result.critical_hits)
            total_benign += len(result.benign_hits)

    if cleaned_count > 0:
        log.info(
            "[precommit_zero_leak] cleaned=%d sections, critical=%d, benign=%d, fail_closed=%d",
            cleaned_count, total_critical, total_benign, len(fail_closed_sections)
        )

    # Fix-Batch C1: Return both cleaned sections and list of FAIL-CLOSED sections
    return cleaned, fail_closed_sections
