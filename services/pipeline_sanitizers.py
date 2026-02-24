#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX-528: Pipeline Sanitizers - Post-Processing Functions

This module provides post-processing functions for the report generation pipeline.
These functions should be applied:
1. After LLM output
2. After html_repair fallback
3. After OpenAI 502 recovery

Functions:
- decode_html_entities(): Convert HTML entities to actual characters
- ensure_complete_sentences(): Ensure text ends with complete sentences
- validate_entity_free(): Validation gate for entity-free output

Usage:
    from services.pipeline_sanitizers import (
        decode_html_entities,
        ensure_complete_sentences,
        apply_post_llm_sanitization,
    )

    # After LLM output
    content = apply_post_llm_sanitization(content, section_name="exec_summary")

    # After html_repair
    content = decode_html_entities(content)
    content = ensure_complete_sentences(content)

Version: 1.0.0 (FIX-528)
"""
from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

ENTITY_PATTERN = re.compile(r'&(?:#[0-9]+|#x[0-9a-fA-F]+|[a-zA-Z]+);')  # Matches &amp; &#123; &#xAB; etc.



# =============================================================================
# FIX-J2: Explicit mojibake replacement map for common patterns
# =============================================================================
_MOJIBAKE_REPLACEMENTS = {}

def _build_mojibake_map():
    """Build mojibake map safely using byte sequences."""
    pairs = [
        # bullet
        (b"\xe2\x80\xa2", "\u2022"),
        # German umlauts lowercase
        (b"\xc3\xa4", "\u00e4"), (b"\xc3\xb6", "\u00f6"), (b"\xc3\xbc", "\u00fc"),
        # German umlauts uppercase
        (b"\xc3\x84", "\u00c4"), (b"\xc3\x96", "\u00d6"), (b"\xc3\x9c", "\u00dc"),
        # Eszett
        (b"\xc3\x9f", "\u00df"),
        # dashes
        (b"\xe2\x80\x93", "\u2013"), (b"\xe2\x80\x94", "\u2014"),
        # quotes
        (b"\xe2\x80\x98", "\u2018"), (b"\xe2\x80\x99", "\u2019"),
        (b"\xe2\x80\x9c", "\u201c"), (b"\xe2\x80\x9d", "\u201d"),
        # ellipsis
        (b"\xe2\x80\xa6", "\u2026"),
        # French accents
        (b"\xc3\xa9", "\u00e9"), (b"\xc3\xa8", "\u00e8"), (b"\xc3\xaa", "\u00ea"),
        (b"\xc3\xa0", "\u00e0"), (b"\xc3\xa2", "\u00e2"),
        (b"\xc3\xae", "\u00ee"), (b"\xc3\xaf", "\u00ef"),
        (b"\xc3\xb4", "\u00f4"),
        (b"\xc3\xb9", "\u00f9"), (b"\xc3\xbb", "\u00fb"),
        (b"\xc3\xa7", "\u00e7"),
    ]
    m = {}
    for bseq, replacement in pairs:
        try:
            mojibake_str = bseq.decode("latin-1")
            m[mojibake_str] = replacement
        except Exception:
            pass
    return m

_MOJIBAKE_REPLACEMENTS = _build_mojibake_map()
_MOJIBAKE_PATTERN = re.compile("|".join(re.escape(k) for k in _MOJIBAKE_REPLACEMENTS.keys())) if _MOJIBAKE_REPLACEMENTS else None


def _apply_mojibake_fixes(text: str) -> str:
    """Apply explicit mojibake replacements."""
    if not _MOJIBAKE_PATTERN or not text:
        return text
    return _MOJIBAKE_PATTERN.sub(lambda m: _MOJIBAKE_REPLACEMENTS[m.group()], text)




def fix_double_encoded_utf8(text: str) -> str:
    """FIX-D3: Repariert doppelt-encodiertes UTF-8.
    Erkennt und repariert Muster wo UTF-8 Bytes als Latin-1 interpretiert wurden.
    Beispiel: \xc3\xa4 (UTF-8 fuer ae) wird als Latin-1 zu \u00c3\u00a4 = two chars.
    """
    if not text or not isinstance(text, str):
        return text
    # Schnellcheck: Enthaelt der Text das typische \xc3 Prefix?
    # \xc3 = Latin-1 char 195 = first byte of 2-byte UTF-8 for chars U+00C0..U+00FF
    CHECK_CHAR = chr(195)  # \xc3 als Latin-1
    if CHECK_CHAR not in text:
        # Kein \xc3 -> auch kein double-encoded UTF-8
        return text
    try:
        repaired = text.encode("latin-1").decode("utf-8")
        if len(repaired) < len(text):
            log.info(
                "[FIX-D3][UTF8-REPAIR] Repaired double-encoded UTF-8 (%d -> %d chars)",
                len(text), len(repaired)
            )
            return repaired
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    # Fallback: Zeichenweise bekannte Paare ersetzen
    # Latin-1 Interpretation von UTF-8 Bytes fuer deutsche Umlaute
    PAIRS = [
        (chr(195) + chr(164), chr(228)),   # ae
        (chr(195) + chr(182), chr(246)),   # oe
        (chr(195) + chr(188), chr(252)),   # ue
        (chr(195) + chr(132), chr(196)),   # Ae
        (chr(195) + chr(150), chr(214)),   # Oe
        (chr(195) + chr(156), chr(220)),   # Ue
        (chr(195) + chr(159), chr(223)),   # ss (eszett)
        (chr(195) + chr(169), chr(233)),   # e-acute
        (chr(195) + chr(168), chr(232)),   # e-grave
        (chr(195) + chr(167), chr(231)),   # c-cedilla
        (chr(226) + chr(128) + chr(147), chr(8211)),  # en-dash
        (chr(226) + chr(128) + chr(148), chr(8212)),  # em-dash
        (chr(226) + chr(128) + chr(162), chr(8226)),  # bullet
        (chr(226) + chr(128) + chr(152), chr(8216)),  # left single quote
        (chr(226) + chr(128) + chr(153), chr(8217)),  # right single quote
        (chr(226) + chr(128) + chr(156), chr(8220)),  # left double quote
        (chr(226) + chr(128) + chr(157), chr(8221)),  # right double quote
    ]
    result = text
    count = 0
    for bad, good in PAIRS:
        if bad in result:
            result = result.replace(bad, good)
            count += 1
    if count > 0:
        log.info("[FIX-D3][UTF8-FALLBACK] Replaced %d double-encoded patterns", count)
    
    # FIX-J2: Apply explicit mojibake replacements
    result = _apply_mojibake_fixes(result)
    return result


def decode_html_entities(text: str, preserve_html_structure: bool = True) -> str:
    """
    FIX-528: Decode HTML entities to actual characters.

    Converts entities like &uuml; to ü, &amp; to &, &bdquo; to „, etc.
    This should be applied after LLM output and after html_repair.

    Args:
        text: Text with potential HTML entities
        preserve_html_structure: If True, preserves valid HTML tags

    Returns:
        Text with entities converted to actual characters

    Example:
        >>> decode_html_entities("F&uuml;r Ihre &bdquo;Daten&ldquo;")
        'Für Ihre „Daten"'
    """
    if not text or not isinstance(text, str):
        return text or ""

    # Track if we had entities
    original = text
    result = text

    # Step 1: Fix double-escaped entities first (e.g., &amp;uuml; -> &uuml; -> ü)
    # This can happen when content is escaped multiple times
    max_iterations = 3
    for _ in range(max_iterations):
        if '&amp;' not in result:
            break
        # Convert &amp;entity; to &entity;
        result = re.sub(r'&amp;([a-zA-Z]{2,8});', r'&\1;', result)

    # Step 2: Use Python's html.unescape for comprehensive entity handling
    result = html.unescape(result)

    # Step 3: Handle numeric entities that might have been missed
    result = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), result)
    result = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), result)

    # Log if entities were decoded
    if result != original:
        entity_count = len(ENTITY_PATTERN.findall(original)) - len(ENTITY_PATTERN.findall(result))
        if entity_count > 0:
            log.info("[FIX-528][ENTITY-DECODE] Decoded %d HTML entities", entity_count)

    return result


def validate_entity_free(text: str) -> Tuple[bool, List[str]]:
    """
    FIX-528: Validate that no visible HTML entities remain.

    Gate check for final output. Entities like &[a-z]{2,6}; should not appear
    in rendered text (except in URLs with query strings).

    Args:
        text: Text to validate

    Returns:
        Tuple of (passed, list_of_found_entities)
    """
    if not text:
        return True, []

    found_entities = []

    # Find all entity-like patterns
    for match in ENTITY_PATTERN.finditer(text):
        entity = match.group(0)

        # Check context - skip if in URL (href/src attribute)
        start = max(0, match.start() - 50)
        context = text[start:match.end() + 10]

        # Allow &amp; in URLs
        if ('href=' in context or 'src=' in context or 'url(' in context):
            if entity == '&amp;':
                continue

        found_entities.append(entity)

    passed = len(found_entities) == 0

    if not passed:
        unique = list(set(found_entities))[:10]
        log.warning("[FIX-528][ENTITY-GATE] Found %d entities: %s", len(found_entities), unique)

    return passed, list(set(found_entities))


# =============================================================================
# FIX-528: SENTENCE COMPLETION
# =============================================================================

# Sentence-ending punctuation
SENTENCE_ENDS = {'.', '!', '?'}

# Words that indicate incomplete sentences (German)
INCOMPLETE_END_WORDS = {
    # Articles
    'der', 'die', 'das', 'den', 'dem', 'des',
    'ein', 'eine', 'einer', 'eines', 'einem', 'einen',
    # Prepositions
    'mit', 'bei', 'für', 'auf', 'von', 'zu', 'zur', 'zum',
    'in', 'im', 'ins', 'an', 'am', 'ans', 'aus', 'nach',
    'durch', 'über', 'unter', 'ohne', 'gegen', 'zwischen',
    # Conjunctions
    'und', 'oder', 'aber', 'sowie', 'dass', 'weil', 'wenn',
    'ob', 'falls', 'damit', 'sodass', 'indem', 'wobei',
    # Pronouns
    'sie', 'ihnen', 'ihr', 'ihre', 'ihren', 'sich',
    'dies', 'diese', 'dieser', 'dieses',
    # Adverbs
    'auch', 'nur', 'noch', 'so', 'als', 'bereits', 'ca',
}


def ensure_complete_sentences(text: str, min_words: int = 5) -> str:
    """
    FIX-528: Ensure text ends with complete sentences.

    This function is critical after OpenAI 502 fallback or html_repair,
    where content might be truncated mid-sentence.

    Strategy:
    1. Check if text ends with sentence-ending punctuation
    2. If not, check if last word indicates incomplete sentence
    3. If incomplete, trim to last complete sentence boundary
    4. If still incomplete, add ellipsis or period

    Args:
        text: Text to process
        min_words: Minimum words to keep (prevents over-trimming)

    Returns:
        Text ending with complete sentence

    Example:
        >>> ensure_complete_sentences("Dies ist ein Test für die")
        'Dies ist ein Test.'
        >>> ensure_complete_sentences("Dies ist ein Test.")
        'Dies ist ein Test.'
    """
    if not text or not isinstance(text, str):
        return text or ""

    text = text.strip()
    if not text:
        return ""

    # Check if already ends with sentence punctuation
    if text[-1] in SENTENCE_ENDS:
        return text

    # Get words for analysis
    words = text.split()
    if len(words) < min_words:
        # Too short - just add period
        return text + "."

    last_word = words[-1].lower().rstrip('.,;:!?')

    # Check if last word indicates incomplete sentence
    is_incomplete = last_word in INCOMPLETE_END_WORDS

    if is_incomplete:
        # Find last sentence boundary
        last_period = text.rfind('.')
        last_excl = text.rfind('!')
        last_quest = text.rfind('?')

        # Find the latest sentence end
        best_end = max(last_period, last_excl, last_quest)

        if best_end > len(text) // 3:  # Only trim if boundary is in latter 2/3
            trimmed = text[:best_end + 1].strip()
            if len(trimmed.split()) >= min_words:
                log.info(
                    "[FIX-528][SENTENCE-COMPLETE] Trimmed incomplete ending: '%s' -> '%s'",
                    text[-30:], trimmed[-30:]
                )
                return trimmed

        # No good boundary - try comma cut
        last_comma = text.rfind(',')
        if last_comma > len(text) // 2:
            trimmed = text[:last_comma].strip() + "."
            if len(trimmed.split()) >= min_words:
                log.info(
                    "[FIX-528][SENTENCE-COMPLETE] Comma-cut: '%s' -> '%s'",
                    text[-30:], trimmed[-30:]
                )
                return trimmed

    # Fallback: add period
    return text.rstrip('.,;:') + "."


def ensure_complete_sentences_html(html_content: str) -> str:
    """
    FIX-528: Apply sentence completion to HTML content.

    Processes text nodes in HTML (paragraphs, list items) to ensure
    complete sentences.

    Args:
        html_content: HTML content to process

    Returns:
        HTML with complete sentences
    """
    if not html_content:
        return html_content

    def process_text_node(match: re.Match[str]) -> str:
        open_tag: str = match.group(1)
        inner: str = match.group(2)
        close_tag: str = match.group(3)

        # Skip if contains nested HTML
        if '<' in inner and '>' in inner:
            return str(match.group(0))

        processed = ensure_complete_sentences(inner)
        return f"{open_tag}{processed}{close_tag}"

    result = html_content

    # Process paragraphs
    result = re.sub(
        r'(<p[^>]*>)([^<]{10,})(</p>)',
        process_text_node,
        result,
        flags=re.IGNORECASE
    )

    # Process list items
    result = re.sub(
        r'(<li[^>]*>)([^<]{10,})(</li>)',
        process_text_node,
        result,
        flags=re.IGNORECASE
    )

    return result


# =============================================================================
# FIX-528: COMBINED SANITIZATION PIPELINE
# =============================================================================

@dataclass
class SanitizationResult:
    """Result of sanitization pipeline."""
    content: str
    entities_decoded: int
    sentences_fixed: int
    warnings: List[str]


def apply_post_llm_sanitization(
    content: str,
    section_name: str = "",
    decode_entities: bool = True,
    complete_sentences: bool = True,
    is_html: bool = True,
) -> SanitizationResult:
    """
    FIX-528: Apply full post-LLM sanitization pipeline.

    This should be called after:
    1. Normal LLM output
    2. html_repair fallback
    3. OpenAI 502 recovery

    Pipeline:
    1. Decode HTML entities
    2. Ensure complete sentences
    3. Validate output

    Args:
        content: Content to sanitize
        section_name: Section name for logging
        decode_entities: Whether to decode HTML entities
        complete_sentences: Whether to ensure complete sentences
        is_html: Whether content is HTML (affects sentence processing)

    Returns:
        SanitizationResult with processed content and stats
    """
    if not content:
        return SanitizationResult(
            content="",
            entities_decoded=0,
            sentences_fixed=0,
            warnings=[],
        )

    result = content
    entities_decoded = 0
    sentences_fixed = 0
    warnings: List[str] = []

    # Step 1: Decode HTML entities
    if decode_entities:
        before_entity_count = len(ENTITY_PATTERN.findall(result))
        result = decode_html_entities(result)
        after_entity_count = len(ENTITY_PATTERN.findall(result))
        entities_decoded = before_entity_count - after_entity_count

    # Step 2: Ensure complete sentences
    if complete_sentences:
        original = result
        if is_html:
            result = ensure_complete_sentences_html(result)
        else:
            result = ensure_complete_sentences(result)

        if result != original:
            sentences_fixed = 1

    # Step 3: Validate
    entity_passed, entity_violations = validate_entity_free(result)
    if not entity_passed:
        warnings.append(f"Remaining entities: {entity_violations[:5]}")

    # Logging
    if entities_decoded > 0 or sentences_fixed > 0:
        log.info(
            "[FIX-528][SANITIZE] section=%s entities=%d sentences=%d warnings=%d",
            section_name or "unknown",
            entities_decoded,
            sentences_fixed,
            len(warnings)
        )

    return SanitizationResult(
        content=result,
        entities_decoded=entities_decoded,
        sentences_fixed=sentences_fixed,
        warnings=warnings,
    )


def apply_post_fallback_sanitization(
    content: str,
    section_name: str = "",
    retry_count: int = 0,
    fallback_used: bool = False,
) -> str:
    """
    FIX-528: Specialized sanitization for fallback/recovery scenarios.

    Called after html_repair or OpenAI 502 recovery.

    Args:
        content: Content to sanitize
        section_name: Section name for logging
        retry_count: Number of retries before success/fallback
        fallback_used: Whether fallback was triggered

    Returns:
        Sanitized content
    """
    if not content:
        return ""

    log.info(
        "[FIX-528][POST-FALLBACK] section=%s retry_count=%d fallback=%s",
        section_name, retry_count, fallback_used
    )

    # Apply full sanitization pipeline
    result = apply_post_llm_sanitization(
        content,
        section_name=section_name,
        decode_entities=True,
        complete_sentences=True,
        is_html=True,
    )

    return result.content


# =============================================================================
# FIX-528: SECTION-LEVEL SANITIZATION
# =============================================================================

def sanitize_all_sections(
    sections: Dict[str, Any],
    fallback_triggered: bool = False,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """
    FIX-528: Apply sanitization to all HTML sections.

    Args:
        sections: Dict of section_key -> content
        fallback_triggered: Whether fallback was used (applies stricter checks)

    Returns:
        Tuple of (sanitized_sections, stats)
    """
    sanitized = dict(sections)
    stats = {
        'entities_decoded': 0,
        'sentences_fixed': 0,
        'sections_processed': 0,
    }

    for key, value in sections.items():
        if not isinstance(value, str):
            continue

        # FIX-E2: UTF-8 Repair auf ALLE String-Values (Mojibake auch in LABEL Keys)
        repaired = fix_double_encoded_utf8(value)
        if repaired != value:
            value = repaired
            sanitized[key] = value
            log.info("[FIX-E2] UTF-8 repaired non-HTML key: %s", key)

        # Only process HTML sections for further sanitization
        if not (key.endswith('_HTML') or key.endswith('_html')):
            continue

        if len(value) < 50:
            continue

        result = apply_post_llm_sanitization(
            value,
            section_name=key,
            decode_entities=True,
            complete_sentences=fallback_triggered,  # Only fix sentences if fallback
            is_html=True,
        )

        # FIX-C1: Strip context block leaks
        cleaned, c1_rem = strip_context_block_leaks(result.content, key)
        if c1_rem > 0:
            stats['context_blocks_stripped'] = stats.get('context_blocks_stripped', 0) + c1_rem

        # FIX-I1/I7: Strip variable name leaks and grammar fixes
        cleaned, i1_rem = strip_variable_name_leaks(cleaned, key)
        if i1_rem > 0:
            stats['variable_leaks_stripped'] = stats.get('variable_leaks_stripped', 0) + i1_rem

        # FIX-I4: Strip redundant content blocks
        cleaned, i4_rem = strip_redundant_blocks(cleaned, key)
        if i4_rem > 0:
            stats['redundant_blocks_stripped'] = stats.get('redundant_blocks_stripped', 0) + i4_rem

        sanitized[key] = cleaned
        stats['entities_decoded'] += result.entities_decoded
        stats['sentences_fixed'] += result.sentences_fixed
        stats['sections_processed'] += 1

    if stats['entities_decoded'] > 0 or stats['sentences_fixed'] > 0:
        log.info(
            "[FIX-528][SECTION-SANITIZE] processed=%d entities=%d sentences=%d",
            stats['sections_processed'],
            stats['entities_decoded'],
            stats['sentences_fixed']
        )

    return sanitized, stats


# =============================================================================
# FIX-I1: STRIP VARIABLE NAME LEAKS FROM LLM OUTPUT
# =============================================================================
_VARIABLE_NAME_LEAK_PATTERNS = [
    re.compile(r'<h4[^>]*>\s*quick_wins\s*</h4>', re.IGNORECASE),
    re.compile(r'<h3[^>]*>\s*quick_wins\s*</h3>', re.IGNORECASE),
    re.compile(r'<p[^>]*>\s*quick_wins\s*</p>', re.IGNORECASE),
    re.compile(r'<strong>\s*quick_wins\s*</strong>', re.IGNORECASE),
    re.compile(r'<h4[^>]*>\s*(?:risks_html|RISKS_HTML|executive_summary|roadmap_12m)\s*</h4>', re.IGNORECASE),
    re.compile(r'<h3[^>]*>\s*(?:risks_html|RISKS_HTML|executive_summary|roadmap_12m)\s*</h3>', re.IGNORECASE),
]

_GRAMMAR_FIX_PATTERNS = [
    (re.compile(r'Kleines\s+Kapazit[äa]t', re.IGNORECASE), 'Kleines Team'),
    (re.compile(r'Kleine\s+Kapazit[äa]t', re.IGNORECASE), 'Kleine Kapazität'),
]


def strip_variable_name_leaks(html_content: str, section_name: str = "") -> tuple:
    """FIX-I1: Remove variable name leaks from LLM output."""
    if not html_content or len(html_content) < 50:
        return html_content, 0
    result = html_content
    removals = 0
    for pattern in _VARIABLE_NAME_LEAK_PATTERNS:
        matches = pattern.findall(result)
        if matches:
            removals += len(matches)
            result = pattern.sub('', result)
    for pattern, replacement in _GRAMMAR_FIX_PATTERNS:
        matches = pattern.findall(result)
        if matches:
            removals += len(matches)
            result = pattern.sub(replacement, result)
    if removals > 0:
        result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)
        log.info("[FIX-I1] Stripped %d variable name leaks from section=%s", removals, section_name)
    return result, removals


# =============================================================================
# FIX-I4: STRIP REDUNDANT CONTENT BLOCKS
# =============================================================================
def strip_redundant_blocks(html: str, section_name: str = "") -> tuple:
    """FIX-I4: Detect and remove duplicate content blocks in HTML."""
    if not html or len(html) < 500:
        return html, 0
    # FIX-J5: Extended to detect <ul>, <ol>, and large <div> block repetitions
    block_pattern = re.compile(r'(<(?:ul|ol)[^>]*>.*?</(?:ul|ol)>|<div[^>]*>(?:(?!<div).)*?</div>)', re.DOTALL | re.IGNORECASE)
    ul_blocks = block_pattern.findall(html)
    if not ul_blocks:
        return html, 0
    from collections import Counter
    normalized_blocks = [re.sub(r'\s+', ' ', b.strip()) for b in ul_blocks]
    block_counts = Counter(normalized_blocks)
    result = html
    removals = 0
    for block_norm, count in block_counts.items():
        if count <= 1 or len(block_norm) < 100:
            continue
        for original_block in ul_blocks:
            if re.sub(r'\s+', ' ', original_block.strip()) == block_norm:
                first_pos = result.find(original_block)
                if first_pos >= 0:
                    after_first = first_pos + len(original_block)
                    rest = result[after_first:]
                    removed_in_rest = rest.count(original_block)
                    if removed_in_rest > 0:
                        rest = rest.replace(original_block, '', removed_in_rest)
                        result = result[:after_first] + rest
                        removals += removed_in_rest
                break
    if removals > 0:
        log.info("[FIX-I4] Stripped %d redundant blocks from section=%s", removals, section_name)
    return result, removals





# =============================================================================
# FIX-C1: STRIP CONTEXT BLOCK LABELS FROM LLM OUTPUT
# =============================================================================

_CONTEXT_BLOCK_RE = re.compile(
    r'<div[^>]*class="context-block[^"]*"[^>]*>.*?</div>',
    re.DOTALL | re.IGNORECASE,
)

_CONTEXT_LABEL_PATTERNS = [
    # L2: Catch raw strategic context bullets leaked into output
    r'<(?:p|li|div)[^>]*>\s*(?:Kundenakquise\s+via\s+Netzwerk|Erstgespr\xe4che\s+und\s+Bedarfsanalyse)[^<]{0,200}</(?:p|li|div)>',
    r'<(?:ul|ol)[^>]*>\s*(?:<li[^>]*>\s*(?:Kundenakquise|Erstgespr|Projektbasiert|Wissensmanagement)[^<]{0,200}</li>\s*){2,}</(?:ul|ol)>',
    r'<p[^>]*>\s*<strong>\s*(?:Typische (?:Tools im Einsatz|Workflows)|'
    r'H\xe4ufigste Pain Points|Charakteristika|Fokus-Priorit\xe4ten|'
    r'In Ihrer aktuellen Gr\xf6\xdfe nicht sinnvoll|'
    r'Branchen-Context|Gr\xf6\xdfen-Context|Mitarbeiter|'
    r'Budget (?:CAPEX|OPEX) max|'
    r'Kernleistung \(Hauptleistung\)|'
    r'Typical (?:Tools in Use|Workflows)|Common Pain Points|'
    r'Characteristics|Focus Priorities|'
    r'Not recommended for your current size|'
    r'Industry Context|Size Context|Core Service \(Main Offering\)'
    r')\s*:?\s*</strong>\s*</p>',
    r'<p[^>]*>\s*(?:Typische Tools im Einsatz|Charakteristika|'
    r'Fokus-Priorit\xe4ten|In Ihrer aktuellen Gr\xf6\xdfe nicht sinnvoll)\s*:?\s*</p>',
    r'<ul[^>]*>\s*<li>\s*\((?:Keine Angaben|No data available)\)\s*</li>\s*</ul>',
]

_CONTEXT_LABEL_RES = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _CONTEXT_LABEL_PATTERNS]

_CONTEXT_SECTION_RE = re.compile(
    r'<(?:div|section)[^>]*(?:context-block|branch-context|size-context)[^>]*>'
    r'.*?</(?:div|section)>',
    re.DOTALL | re.IGNORECASE,
)

_CONTEXT_HR_RE = re.compile(
    r'<hr[^>]*style="[^"]*border[^"]*#cbd5e1[^"]*"[^>]*/?>',
    re.IGNORECASE,
)


def strip_context_block_leaks(html: str, section_name: str = "") -> tuple:
    """FIX-C1: Remove context block labels leaked from prompts into LLM output."""
    if not html or len(html) < 100:
        return html, 0
    removals = 0
    result = html
    for _ in _CONTEXT_BLOCK_RE.finditer(result): removals += 1
    result = _CONTEXT_BLOCK_RE.sub("", result)
    for _ in _CONTEXT_SECTION_RE.finditer(result): removals += 1
    result = _CONTEXT_SECTION_RE.sub("", result)
    for pr in _CONTEXT_LABEL_RES:
        for _ in pr.finditer(result): removals += 1
        result = pr.sub("", result)
    result = _CONTEXT_HR_RE.sub("", result)
    result = re.sub(r'<(?:div|section)[^>]*>\s*</(?:div|section)>', "", result)
    result = re.sub(r'\n\s*\n\s*\n', "\n\n", result)

    # -- O7: Tool/Communication context-block sanitizer --
    _tool_phrases = [
        re.compile(r'[•·\-]\s*Microsoft Office\s*/\s*Google Workspace[^\n<]*[.\n]?\s*', re.I),
        re.compile(r'[•·\-]\s*Excel\s*/\s*Google Sheets[^\n<]*[.\n]?\s*', re.I),
        re.compile(r'[•·\-]\s*Email als Haupt-Kommunikationskanal[^\n<]*[.\n]?\s*', re.I),
        re.compile(r'[•·\-]\s*Zoom\s*/\s*Microsoft Teams[^\n<]*[.\n]?\s*', re.I),
        re.compile(r'Erweiterung nur mit mehr Zeit:\s*Kapazit.tsgrenze[^\n<]*[.\n]?\s*', re.I),
        # Also in <li> tags
        re.compile(r'<li[^>]*>[^<]*Microsoft Office\s*/\s*Google Workspace[^<]*</li>\s*', re.I),
        re.compile(r'<li[^>]*>[^<]*Excel\s*/\s*Google Sheets[^<]*</li>\s*', re.I),
        re.compile(r'<li[^>]*>[^<]*Email als Haupt-Kommunikationskanal[^<]*</li>\s*', re.I),
        re.compile(r'<li[^>]*>[^<]*Zoom\s*/\s*Microsoft Teams[^<]*</li>\s*', re.I),
    ]
    for _tp_re in _tool_phrases:
        _tp_hits = _tp_re.findall(result)
        if _tp_hits:
            result = _tp_re.sub('', result)
            removals += len(_tp_hits)

    # -- O2c: Kl→KI fix (common OCR/input error: lowercase L instead of uppercase I) --
    _kl_re = re.compile(r'\bKl-(?=Readiness|Sicherheit|Manager|Strategie|Einsatz|Tool|System|Projekt|Kompetenz|Verantwort)')
    _kl_hits = _kl_re.findall(result)
    if _kl_hits:
        result = _kl_re.sub('KI-', result)
        removals += len(_kl_hits)

    # -- N9: KI-KI deduplication (LLM artifact) --
    _kiki_re = re.compile(r'KI-KI-', re.IGNORECASE)
    _kiki_hits = _kiki_re.findall(result)
    if _kiki_hits:
        result = _kiki_re.sub('KI-', result)
        removals += len(_kiki_hits)

    # -- N2: Pain-Point phrase blacklist (zeitersparnis_prioritaet leaks) --
    _pain_phrases = [
        re.compile(r'[•·\-]\s*Angebotserstellung\s*\(individuell[^)]*\)[.,;]?\s*', re.I),
        re.compile(r'[•·\-]\s*Akquise frisst produktive Zeit[^\n<]*[.\n]?\s*', re.I),
        re.compile(r'[•·\-]\s*Angebote schreiben dauert zu lang[^\n<]*[.\n]?\s*', re.I),
        re.compile(r'[•·\-]\s*Standardisierung schwierig[^\n<]*[.\n]?\s*', re.I),
        re.compile(r'[•·\-]\s*Projektdurchf.hrung:\s*Workshops[^\n<]*[.\n]?\s*', re.I),
        re.compile(r'[•·\-]\s*Jede[rs]?\s+Kunde\s+will\s+individuelle[^\n<]*[.\n]?\s*', re.I),
        re.compile(r'30.40%\s+f.r\s+Marketing\s+statt\s+Delivery[^\n<]*[.\n]?\s*', re.I),
        # Also catch without bullet prefix (in <li> or <p> tags)
        re.compile(r'<li[^>]*>[^<]*Angebotserstellung\s*\(individuell[^<]*</li>\s*', re.I),
        re.compile(r'<li[^>]*>[^<]*Akquise frisst produktive Zeit[^<]*</li>\s*', re.I),
        re.compile(r'<li[^>]*>[^<]*Angebote schreiben dauert zu lang[^<]*</li>\s*', re.I),
        re.compile(r'<li[^>]*>[^<]*Standardisierung schwierig[^<]*</li>\s*', re.I),
        re.compile(r'<li[^>]*>[^<]*Projektdurchf.hrung:\s*Workshops[^<]*</li>\s*', re.I),
    ]
    for _pp_re in _pain_phrases:
        _pp_hits = _pp_re.findall(result)
        if _pp_hits:
            result = _pp_re.sub('', result)
            removals += len(_pp_hits)
    # Clean up empty containers after removal
    result = re.sub(r'<ul[^>]*>\s*</ul>', '', result)
    result = re.sub(r'<ol[^>]*>\s*</ol>', '', result)
    result = re.sub(r'<p[^>]*>\s*</p>', '', result)

    # -- M2: Catch-all for Context-Block 1 (Beratung/Kundenakquise) --
    _ctx1_re = re.compile(
        r'Beratung und Unterstützung f.r Unternehm[^.]{0,500}?'
        r'(?:einf.hren wollen|Tavily|etc\)|ihren Unternehmen)',
        re.DOTALL | re.IGNORECASE
    )
    _ctx1_hits = _ctx1_re.findall(result)
    if _ctx1_hits:
        result = _ctx1_re.sub("", result)
        removals += len(_ctx1_hits)
        log.info("[FIX-M2] Stripped %d context-1 blocks from section=%s", len(_ctx1_hits), section_name)

    # -- M3: Catch-all for Context-Block 2 (Pain-Points / Angebotserstellung) --
    _ctx2_re = re.compile(
        r'Angebotserstellung\s*\(individuell[^)]{0,500}?'
        r'(?:Kleines Team|Gr.{1,2}en-Context)',
        re.DOTALL | re.IGNORECASE
    )
    _ctx2_hits = _ctx2_re.findall(result)
    if _ctx2_hits:
        result = _ctx2_re.sub("", result)
        removals += len(_ctx2_hits)
        log.info("[FIX-M3] Stripped %d pain-points context blocks from section=%s", len(_ctx2_hits), section_name)

    # M3b: Standalone size-context marker
    _size_re = re.compile(r'Gr.{1,2}en-Context\s*:\s*[^<\n]{0,100}', re.IGNORECASE)
    _size_hits = _size_re.findall(result)
    if _size_hits:
        result = _size_re.sub("", result)
        removals += len(_size_hits)

    # M2+M3: Cleanup empty elements after stripping
    result = re.sub(r'<p[^>]*>\s*</p>', '', result)
    result = re.sub(r'<div[^>]*>\s*</div>', '', result)
    result = re.sub(r'<li[^>]*>\s*</li>', '', result)

    if removals > 0:
        log.info("[FIX-C1][CONTEXT-STRIP] section=%s removed=%d", section_name, removals)
    return result, removals


# L3: Strip internal sprint codes (G33, G35, G36, G30, G37, B2.2 etc.) from rendered HTML
_SPRINT_CODE_RE = re.compile(
    r'(?<![A-Za-z0-9])'          # Not preceded by alphanumeric
    r'(?:G[0-9]{2}|B[0-9]\.[0-9])'  # G33, G35, G30, B2.2 etc.
    r'(?:\s*[:–—-]\s*)?'         # Optional separator
    r'(?![0-9])',                 # Not followed by digit (avoid matching G20 in "G2048" etc.)
    re.IGNORECASE,
)

def strip_sprint_codes(html: str, section_name: str = "") -> str:
    """L3: Remove internal sprint/engine codes like G33, G35, B2.2 from rendered HTML."""
    if not html:
        return html
    result = _SPRINT_CODE_RE.sub("", html)
    # Clean up leftover empty elements
    result = re.sub(r'<(?:span|strong|b)[^>]*>\s*</(?:span|strong|b)>', "", result)
    if result != html:
        log.info("[L3][SPRINT-CODE-STRIP] section=%s codes removed", section_name)
    return result


# =============================================================================
# INITIALIZATION
# =============================================================================

log.info(
    "[FIX-528] pipeline_sanitizers loaded: decode_html_entities, "
    "ensure_complete_sentences, apply_post_llm_sanitization, sanitize_all_sections"
)


# =============================================================================
# FIX-B734b: Strip dangerous multi-column grid layouts from LLM output
# WeasyPrint breaks grid-template-columns with 3+ columns at narrow margins
# =============================================================================

_MULTI_COLUMN_SECTIONS = {
    'ai_policy_mini', 'AI_POLICY_MINI_HTML',
    'templates_start', 'TEMPLATES_START_HTML',
    'monetarisierung', 'MONETARISIERUNG_HTML',
    'ki_skillplan', 'KI_SKILLPLAN_HTML',
    'kickoff_vorlage', 'KICKOFF_VORLAGE_HTML',
    'glossar', 'GLOSSAR_HTML',
    # FIX-B734e: Added missing sections that produce 3+ column grids
    'starter_kit', 'STARTER_KIT_HTML',
    'STARTER_KIT_COMPACT_HTML',
    'SOFORT_START_HTML', 'sofort_start',
    'CHALLENGE_30_TAGE_HTML', 'challenge_30_tage',
    'branch_deep_dive', 'BRANCH_DEEP_DIVE_HTML',
    'BRANCH_PROFILE_HTML', 'branch_profile',
    'TOOLS_HTML', 'tools_empfehlungen', 'TOOLS_EMPFEHLUNGEN_HTML',
    'RISK_ENGINE_HTML', 'RISK_ENGINE_V3_HTML',
    'VENDOR_AUDIT_HTML',
    'roi_tracking', 'ROI_TRACKING_HTML',
    'AUTOMATION_ROADMAP_HTML',
    'BENCHMARKS_HTML', 'BENCHMARKS_SECTION_HTML',
}


def sanitize_grid_layouts(html_content: str, section_name: str = "") -> str:
    """FIX-B734b: Replace multi-column grid with single-column block layout.

    Only applies to sections known to break in WeasyPrint PDF rendering.
    Converts grid-template-columns with 3+ columns to single column.
    """
    if not html_content or not isinstance(html_content, str):
        return html_content

    if section_name and section_name not in _MULTI_COLUMN_SECTIONS:
        return html_content

    original_len = len(html_content)
    result = html_content
    fixes = 0

    # Fix 1: grid-template-columns mit 3+ Spalten -> 1fr
    _pat_3col = re.compile(
        r'grid-template-columns\s*:\s*(?:repeat\s*\(\s*[3-9]\s*,|(?:[\w.]+\s+){2,})',
        re.IGNORECASE,
    )
    if _pat_3col.search(result):
        result = re.sub(
            r'(grid-template-columns\s*:\s*)(?:repeat\s*\([^)]+\)|[^;"]+)',
            r'\g<1>1fr',
            result,
        )
        fixes += 1

    # Fix 2: column-count > 1 -> 1
    _pat_colcount = re.compile(r'column-count\s*:\s*[2-9]', re.IGNORECASE)
    if _pat_colcount.search(result):
        result = _pat_colcount.sub('column-count: 1', result)
        fixes += 1

    # Fix 3: columns: N -> columns: 1
    _pat_columns = re.compile(r'(?<![a-z-])columns\s*:\s*[2-9]', re.IGNORECASE)
    if _pat_columns.search(result):
        result = _pat_columns.sub('columns: 1', result)
        fixes += 1

    if fixes > 0:
        log.info(
            "[FIX-B734b] Sanitized %d grid/column layouts in %s (%d->%d chars)",
            fixes, section_name or "unknown", original_len, len(result),
        )

    return result
