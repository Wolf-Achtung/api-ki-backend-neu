"""
DEBUG-503D: Debug artifact collection for admin email attachments.

When DEBUG_RENDER=1, this module builds 4 debug artifacts:
1. debug_503d_quick_wins_block.html - Final rendered Quick Wins DETAIL section
2. debug_503d_risk_matrix_block.html - Final rendered Risk Matrix table with CSS
3. debug_503d_payback_mentions.txt - Canonical PAYBACK_MONTHS + all occurrences in HTML
4. debug_503d_quick_wins_keys.json - Lengths + marker presence for QW keys

These artifacts attach to admin emails for forensic debugging of PDF rendering issues.

IMPORTANT: The raw bytes are passed directly to the email function - they are NEVER
stored in meta/sections that get persisted to the database (Postgres JSONB can't serialize bytes).
Only JSON-safe metadata (filenames, sizes, sha256) is stored in meta["debug_503d_summary"].
"""
import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# Max size for HTML snippets (200KB each)
MAX_SNIPPET_SIZE = 200 * 1024

# Debug anchors that should be in the templates
QUICK_WINS_START = "<!-- DEBUG-ANCHOR: QUICK_WINS_DETAIL_START -->"
QUICK_WINS_END = "<!-- DEBUG-ANCHOR: QUICK_WINS_DETAIL_END -->"
RISK_MATRIX_START = "<!-- DEBUG-ANCHOR: RISK_MATRIX_START -->"
RISK_MATRIX_END = "<!-- DEBUG-ANCHOR: RISK_MATRIX_END -->"


def is_debug_render_enabled() -> bool:
    """Check if DEBUG_RENDER=1 is set."""
    return os.getenv("DEBUG_RENDER", "").strip() == "1"


def _extract_between_anchors(html: str, start_anchor: str, end_anchor: str, max_size: int = MAX_SNIPPET_SIZE) -> str:
    """
    Extract HTML content between two anchor comments.

    Args:
        html: Full HTML string
        start_anchor: Start comment marker
        end_anchor: End comment marker
        max_size: Maximum size of extracted content

    Returns:
        Extracted HTML snippet or empty string if anchors not found
    """
    start_idx = html.find(start_anchor)
    if start_idx == -1:
        return ""

    # Start after the anchor
    content_start = start_idx + len(start_anchor)

    end_idx = html.find(end_anchor, content_start)
    if end_idx == -1:
        # If no end anchor, take reasonable chunk
        end_idx = min(content_start + max_size, len(html))

    content = html[content_start:end_idx].strip()

    # Enforce max size
    if len(content) > max_size:
        content = content[:max_size] + "\n<!-- TRUNCATED -->"

    return content


def _build_quick_wins_snippet(final_html: str) -> str:
    """
    Extract the Quick Wins DETAIL section from final HTML.

    Looks for DEBUG-ANCHOR markers, falls back to section class matching.

    Returns:
        HTML snippet for Quick Wins block
    """
    # Try anchor-based extraction first
    content = _extract_between_anchors(final_html, QUICK_WINS_START, QUICK_WINS_END)

    if content:
        return f"<!-- DEBUG-503D: Quick Wins section extracted via anchors -->\n{content}"

    # Fallback: Find section with Quick Wins heading
    # Look for the section containing "Quick Wins" h2
    qw_pattern = r'(<section[^>]*>.*?<h2>Quick Wins</h2>.*?</section>)'
    match = re.search(qw_pattern, final_html, re.DOTALL | re.IGNORECASE)

    if match:
        content = match.group(1)
        if len(content) > MAX_SNIPPET_SIZE:
            content = content[:MAX_SNIPPET_SIZE] + "\n<!-- TRUNCATED -->"
        return f"<!-- DEBUG-503D: Quick Wins section extracted via pattern matching -->\n{content}"

    return "<!-- DEBUG-503D: Quick Wins section NOT FOUND in final HTML -->"


def _get_risk_matrix_css() -> str:
    """
    Return the CSS rules relevant to Risk Matrix rendering.

    These rules are critical for proper PDF rendering and are included
    inline in the debug snippet.
    """
    return """
<style>
/* Risk Matrix CSS - FIX-503B */
.risk-matrix-section {
    page-break-inside: avoid;
    margin: 20px 0;
}
.risk-matrix-section table {
    table-layout: auto;
    width: 100%;
    border-collapse: collapse;
    font-size: 10pt;
}
.risk-matrix-section td,
.risk-matrix-section th {
    padding: 8px;
    border-bottom: 1px solid #e2e8f0;
    overflow-wrap: anywhere;
    word-break: break-word;
    hyphens: auto;
    white-space: normal;
    overflow: visible;
}
.table-modern {
    table-layout: auto;
    width: 100%;
    border-collapse: collapse;
}
</style>
"""


def _build_risk_matrix_snippet(final_html: str) -> str:
    """
    Extract the Risk Matrix table from final HTML with relevant CSS.

    Looks for DEBUG-ANCHOR markers, falls back to class matching.

    Returns:
        HTML snippet for Risk Matrix with inline CSS
    """
    # Try anchor-based extraction first
    content = _extract_between_anchors(final_html, RISK_MATRIX_START, RISK_MATRIX_END)

    if content:
        return f"<!-- DEBUG-503D: Risk Matrix extracted via anchors -->\n{_get_risk_matrix_css()}\n{content}"

    # Fallback: Find risk-matrix-section div
    rm_pattern = r'(<div[^>]*class="[^"]*risk-matrix-section[^"]*"[^>]*>.*?</div>)'
    match = re.search(rm_pattern, final_html, re.DOTALL | re.IGNORECASE)

    if match:
        content = match.group(1)
        if len(content) > MAX_SNIPPET_SIZE:
            content = content[:MAX_SNIPPET_SIZE] + "\n<!-- TRUNCATED -->"
        return f"<!-- DEBUG-503D: Risk Matrix extracted via class matching -->\n{_get_risk_matrix_css()}\n{content}"

    # Second fallback: Find table with Risiko-Matrix heading
    rm_pattern2 = r'(<div[^>]*>.*?Risiko-Matrix.*?<table.*?</table>.*?</div>)'
    match2 = re.search(rm_pattern2, final_html, re.DOTALL | re.IGNORECASE)

    if match2:
        content = match2.group(1)
        if len(content) > MAX_SNIPPET_SIZE:
            content = content[:MAX_SNIPPET_SIZE] + "\n<!-- TRUNCATED -->"
        return f"<!-- DEBUG-503D: Risk Matrix extracted via pattern matching -->\n{_get_risk_matrix_css()}\n{content}"

    return f"<!-- DEBUG-503D: Risk Matrix NOT FOUND in final HTML -->\n{_get_risk_matrix_css()}"


def _format_payback_de(value: Any) -> str:
    """Format PAYBACK_MONTHS value in German locale."""
    if value is None or value == "":
        return "N/A"

    try:
        num = float(value)
        # German formatting: comma as decimal separator
        if num == int(num):
            return f"{int(num)}"
        return f"{num:.1f}".replace(".", ",")
    except (ValueError, TypeError):
        return str(value)


def _build_payback_mentions(final_html: str, canonical_kpis: Optional[Dict[str, Any]] = None) -> str:
    """
    Build payback mentions report.

    First line: canonical PAYBACK_MONTHS value (formatted de).
    Then: every occurrence of Payback/Amortisation with +/-80 chars context.

    Args:
        final_html: Final rendered HTML
        canonical_kpis: Dict with PAYBACK_MONTHS value

    Returns:
        Text report of payback mentions
    """
    lines = []

    # First line: canonical value
    payback_val = None
    if canonical_kpis:
        payback_val = canonical_kpis.get("PAYBACK_MONTHS")

    lines.append(f"CANONICAL PAYBACK_MONTHS: {_format_payback_de(payback_val)}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("PAYBACK/AMORTISATION MENTIONS IN FINAL HTML:")
    lines.append("=" * 60)
    lines.append("")

    # Pattern for payback/amortisation mentions
    pattern = re.compile(r'\b(payback|amortisation|amortisierung)\b', re.IGNORECASE)

    # Calculate line numbers
    html_lines = final_html.split('\n')
    char_offset = 0
    line_offsets = []  # (start_char, end_char, line_num)

    for line_num, line in enumerate(html_lines, 1):
        line_offsets.append((char_offset, char_offset + len(line), line_num))
        char_offset += len(line) + 1  # +1 for newline

    def get_line_number(pos: int) -> int:
        """Get line number for character position."""
        for start, end, line_num in line_offsets:
            if start <= pos < end + 1:  # +1 to include newline
                return line_num
        return -1

    # Find all matches
    matches_found = 0
    for match in pattern.finditer(final_html):
        matches_found += 1
        pos = match.start()
        line_num = get_line_number(pos)

        # Extract context: +/- 80 chars
        ctx_start = max(0, pos - 80)
        ctx_end = min(len(final_html), pos + len(match.group()) + 80)
        context = final_html[ctx_start:ctx_end]

        # Clean up context for readability
        context = context.replace('\n', ' ').replace('\r', ' ')
        context = re.sub(r'\s+', ' ', context)

        # Mark the match position
        match_start_in_ctx = pos - ctx_start
        match_end_in_ctx = match_start_in_ctx + len(match.group())

        # Build context string with markers
        marked_context = (
            context[:match_start_in_ctx] +
            ">>>" + context[match_start_in_ctx:match_end_in_ctx] + "<<<" +
            context[match_end_in_ctx:]
        )

        lines.append(f"[Line {line_num:5d}] ...{marked_context}...")
        lines.append("")

    lines.append("=" * 60)
    lines.append(f"TOTAL MATCHES: {matches_found}")

    return "\n".join(lines)


def _build_quick_wins_keys_json(sections: Dict[str, Any]) -> str:
    """
    Build JSON with lengths + marker presence for Quick Wins keys.

    Args:
        sections: Dict with QUICK_WINS_HTML, QUICK_WINS_HTML_LEFT, QUICK_WINS_HTML_RIGHT, quick_wins

    Returns:
        JSON string with debug info
    """
    keys_to_check = ["QUICK_WINS_HTML", "QUICK_WINS_HTML_LEFT", "QUICK_WINS_HTML_RIGHT", "quick_wins"]

    result: Dict[str, Any] = {}

    for key in keys_to_check:
        value = sections.get(key, "")
        if value is None:
            value = ""
        value_str = str(value)

        result[key] = {
            "len": len(value_str),
            "has_quick_win_class": 'class="quick-win' in value_str,
            "has_rendered_marker": 'data-qw-json-rendered="true"' in value_str,
        }

    # Determine template_mode
    right_len = len(str(sections.get("QUICK_WINS_HTML_RIGHT", "") or ""))
    left_len = len(str(sections.get("QUICK_WINS_HTML_LEFT", "") or ""))
    full_len = len(str(sections.get("QUICK_WINS_HTML", "") or ""))

    if right_len > 0:
        template_mode = "LEFT_RIGHT"
    elif left_len > 0:
        template_mode = "LEFT_ONLY"
    elif full_len > 0:
        template_mode = "FULL"
    else:
        template_mode = "NONE"

    result["template_mode"] = template_mode

    # Add timestamp for reference
    from datetime import datetime
    result["captured_at"] = datetime.utcnow().isoformat() + "Z"

    # FIX-510 CHANGE 3: Add runtime LLM config for audit trail
    result["runtime_llm_config"] = _get_runtime_llm_config()

    return json.dumps(result, indent=2, ensure_ascii=False)


def _get_runtime_llm_config() -> Dict[str, Any]:
    """
    FIX-510 CHANGE 3: Get runtime LLM configuration for debug/audit.

    Returns dict with model/endpoint info so we can verify what was actually used.
    """
    import os

    config = {
        # OpenAI config
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "openai_base_url": os.getenv("OPENAI_BASE_URL", "default"),
        "openai_timeout_connect": os.getenv("OPENAI_TIMEOUT_CONNECT", "30"),
        "openai_timeout_read": os.getenv("OPENAI_TIMEOUT_READ", "120"),

        # Perplexity config
        "perplexity_model": os.getenv("PERPLEXITY_MODEL", "sonar-medium-online"),
        "perplexity_base_url": os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"),
        "perplexity_endpoint": os.getenv("PERPLEXITY_ENDPOINT", "/chat/completions"),

        # Runtime flags
        "release_strict_mode": os.getenv("RELEASE_STRICT_MODE", "0"),
        "debug_render": os.getenv("DEBUG_RENDER", "0"),
    }

    # Log the config (FIX-510 requirement)
    log.info(
        "[FIX-510][CONFIG] Perplexity endpoint=%s model=%s | OpenAI model=%s | STRICT=%s",
        config["perplexity_base_url"] + config["perplexity_endpoint"],
        config["perplexity_model"],
        config["openai_model"],
        config["release_strict_mode"]
    )

    return config


def build_debug_503d_attachments(
    final_html: str,
    sections: Dict[str, Any],
    canonical_kpis: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Build DEBUG-503D artifacts for admin email attachments.

    This function should be called right before PDF render, after all post-processing,
    when FINAL HTML is ready. This ensures attachments reflect exactly what the PDF
    renderer uses.

    Args:
        final_html: The final rendered HTML (after all post-processing)
        sections: Dict with section data including QUICK_WINS_HTML variants
        canonical_kpis: Dict with canonical KPI values (PAYBACK_MONTHS, etc.)

    Returns:
        List of attachment dicts: [{filename, content (bytes), mimetype}, ...]
    """
    if not is_debug_render_enabled():
        return []

    attachments = []
    total_bytes = 0

    try:
        # 1. Quick Wins block HTML
        qw_html = _build_quick_wins_snippet(final_html)
        qw_bytes = qw_html.encode("utf-8")
        attachments.append({
            "filename": "debug_503d_quick_wins_block.html",
            "content": qw_bytes,
            "mimetype": "text/html"
        })
        total_bytes += len(qw_bytes)

        # 2. Risk Matrix block HTML
        rm_html = _build_risk_matrix_snippet(final_html)
        rm_bytes = rm_html.encode("utf-8")
        attachments.append({
            "filename": "debug_503d_risk_matrix_block.html",
            "content": rm_bytes,
            "mimetype": "text/html"
        })
        total_bytes += len(rm_bytes)

        # 3. Payback mentions txt
        payback_txt = _build_payback_mentions(final_html, canonical_kpis)
        payback_bytes = payback_txt.encode("utf-8")
        attachments.append({
            "filename": "debug_503d_payback_mentions.txt",
            "content": payback_bytes,
            "mimetype": "text/plain"
        })
        total_bytes += len(payback_bytes)

        # 4. Quick Wins keys JSON
        qw_keys_json = _build_quick_wins_keys_json(sections)
        qw_keys_bytes = qw_keys_json.encode("utf-8")
        attachments.append({
            "filename": "debug_503d_quick_wins_keys.json",
            "content": qw_keys_bytes,
            "mimetype": "application/json"
        })
        total_bytes += len(qw_keys_bytes)

        # Log the collection (must appear in Railway logs)
        log.info(
            "[DEBUG-503D][MAIL] attaching 4 artifacts: "
            "quick_wins_block.html, risk_matrix_block.html, payback_mentions.txt, quick_wins_keys.json "
            "(total_bytes=%d)",
            total_bytes
        )

    except Exception as e:
        log.error("[DEBUG-503D] Failed to build debug attachments: %s", str(e))
        return []

    return attachments


def build_debug_503d_summary(attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a JSON-serializable summary of debug attachments for database storage.

    This function extracts metadata from debug attachments (which contain bytes)
    and returns a JSON-safe dict that can be stored in Postgres JSONB fields.

    IMPORTANT: The raw bytes must NEVER be stored in the database.
    Only this summary is stored in meta["debug_503d_summary"].

    Args:
        attachments: List of attachment dicts from build_debug_503d_attachments()
                     Each has: {filename, content (bytes), mimetype}

    Returns:
        JSON-serializable dict with metadata:
        {
            "artifact_count": 4,
            "artifacts": [
                {"filename": "...", "size_bytes": 1234, "sha256": "abc123...", "mimetype": "..."},
                ...
            ],
            "total_bytes": 5678,
            "captured_at": "2024-01-15T12:00:00Z"
        }
    """
    if not attachments:
        return {}

    from datetime import datetime

    artifacts_meta = []
    total_bytes = 0

    for att in attachments:
        content = att.get("content", b"")
        if isinstance(content, bytes):
            size = len(content)
            sha256 = hashlib.sha256(content).hexdigest()
            # Optional short preview for text files (first 200 chars)
            preview = None
            if att.get("mimetype", "").startswith("text/") or att.get("filename", "").endswith((".txt", ".json", ".html")):
                try:
                    text = content.decode("utf-8", errors="replace")
                    preview = text[:200] + ("..." if len(text) > 200 else "")
                except Exception:
                    preview = None
        else:
            # Already a string (shouldn't happen, but handle gracefully)
            size = len(str(content))
            sha256 = hashlib.sha256(str(content).encode("utf-8")).hexdigest()
            preview = str(content)[:200] + ("..." if len(str(content)) > 200 else "")

        artifact_info: Dict[str, Any] = {
            "filename": att.get("filename", "unknown"),
            "size_bytes": size,
            "sha256": sha256,
            "mimetype": att.get("mimetype", "application/octet-stream"),
        }
        if preview:
            artifact_info["preview"] = preview

        artifacts_meta.append(artifact_info)
        total_bytes += size

    result: Dict[str, Any] = {
        "artifact_count": len(artifacts_meta),
        "artifacts": artifacts_meta,
        "total_bytes": total_bytes,
        "captured_at": datetime.utcnow().isoformat() + "Z",
    }

    log.info(
        "[DEBUG-503D] Built JSON-safe summary: %d artifacts, %d total bytes",
        len(artifacts_meta), total_bytes
    )

    return result
