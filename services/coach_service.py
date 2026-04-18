# -*- coding: utf-8 -*-
"""
coach_service.py — Post-Report Coach

Lädt Report-Kontext (R1 + optional Strategy), baut eine strukturierte
Zusammenfassung für den Coach-Prompt (Token-schonend), und streamt
Opus-4.6-Antworten per SSE.

KPA (gamechanger_deep_dive) ist in v1 bewusst nicht eingebunden, da sie
on-the-fly erzeugt wird und nicht persistiert ist — Re-Generierung pro
Coach-Call wäre zu teuer.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, AsyncIterator, Optional

import httpx

from core.db import SessionLocal

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template (read once at import)
# ---------------------------------------------------------------------------

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "coach_system.txt"
try:
    _COACH_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")
except Exception as exc:  # pragma: no cover
    log.error("[COACH] Failed to read coach prompt template: %s", exc)
    _COACH_PROMPT_TEMPLATE = ""

# ---------------------------------------------------------------------------
# Thinking-tag filter
# ---------------------------------------------------------------------------

_THINKING_PATTERN = re.compile(
    r"<coach_thinking>.*?</coach_thinking>",
    re.DOTALL | re.IGNORECASE,
)
_OPEN_TAG = "<coach_thinking>"
_CLOSE_TAG = "</coach_thinking>"


def filter_thinking_tags(text: str) -> str:
    """Remove complete <coach_thinking>...</coach_thinking> blocks."""
    return _THINKING_PATTERN.sub("", text)


# ---------------------------------------------------------------------------
# Model + client configuration
# ---------------------------------------------------------------------------

COACH_MODEL = os.getenv("ANTHROPIC_MODEL_COACH") or os.getenv(
    "ANTHROPIC_MODEL_OPUS", "claude-opus-4-6"
).strip()
COACH_MAX_TOKENS = int(os.getenv("COACH_MAX_TOKENS", "2000"))
COACH_TEMPERATURE = float(os.getenv("COACH_TEMPERATURE", "0.4"))
COACH_HISTORY_LIMIT = int(os.getenv("COACH_HISTORY_LIMIT", "12"))

_async_client: Optional[Any] = None


def _get_async_client() -> Optional[Any]:
    """Lazy-init a module-level AsyncAnthropic client with generous read timeout."""
    global _async_client
    if _async_client is not None:
        return _async_client

    try:
        import anthropic
    except ImportError:
        log.error("[COACH] anthropic SDK not installed")
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("[COACH] ANTHROPIC_API_KEY not set")
        return None

    base_timeout = float(os.getenv("ANTHROPIC_TIMEOUT", "120"))
    _async_client = anthropic.AsyncAnthropic(
        api_key=api_key,
        timeout=httpx.Timeout(base_timeout, read=300.0),
    )
    log.info("[COACH] AsyncAnthropic client initialized (model=%s)", COACH_MODEL)
    return _async_client


# ---------------------------------------------------------------------------
# HTML → text helpers
# ---------------------------------------------------------------------------

def _html_to_markdown(html: str) -> str:
    """Convert HTML snippet to compact markdown. Falls back to stripped text."""
    if not html or not html.strip():
        return ""
    try:
        from markdownify import markdownify as _md
        md = _md(html, heading_style="ATX", strip=["style", "script"])
    except Exception as exc:
        log.warning("[COACH] markdownify failed (%s), falling back to bs4 text", exc)
        try:
            from bs4 import BeautifulSoup
            md = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
        except Exception:
            md = re.sub(r"<[^>]+>", " ", html)
    # Collapse excessive whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"[ \t]+", " ", md)
    return md.strip()


def _truncate(text: str, max_chars: int) -> str:
    """Hard char cap with ellipsis to keep token budget predictable."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20].rstrip() + "\n… [gekürzt]"


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

# R1 section keys → human-readable heading for the coach prompt.
# Order matters — that's the order in which they appear in the summary.
_R1_SECTION_MAP: list[tuple[str, str, int]] = [
    # (key, heading, char-budget for this section)
    ("EXECUTIVE_SUMMARY_HTML", "Executive Summary", 2200),
    ("EXEC_SUMMARY_HTML", "Executive Summary", 2200),  # alias
    ("QUICK_WINS_HTML", "Top-Quick-Wins (Titel + Wirkung)", 1800),
    ("ROADMAP_90D_HTML", "90-Tage-Plan", 1400),
    ("NINETY_DAY_PLAN_HTML", "90-Tage-Plan", 1400),
    ("ROADMAP_HTML", "Roadmap", 1400),
    ("BUSINESS_CASE_HTML", "Business Case (ROI / Break-Even / Szenarien)", 1600),
    ("VENDOR_AUDIT_HTML", "Vendor-Audit (RED/GELB-Tools)", 1200),
    ("VENDOR_DETAIL_HTML", "Vendor-Detail", 1200),
    ("ADVISOR_NOTE_HTML", "Persönliche Einschätzung (Wolf Hohl)", 1500),
    ("FUNDING_HTML", "Förderpotenzial (Top-Programme)", 1000),
    ("GAMECHANGER_HTML", "Gamechanger-Hinweis", 700),
]

# Strategy section keys (from StrategyReport.sections dict — stored as HTML).
_STRATEGY_SECTION_MAP: list[tuple[str, str, int]] = [
    ("exec_summary", "Executive Summary", 2000),
    ("S3", "Top-Handlungsfelder (Impact / Komplexität)", 1800),
    ("s_moat", "Moat-Matrix", 1200),
    ("S5", "Investitionsplan + ROI-Szenarien", 1400),
    ("S7", "Top-Fördermittel", 1000),
]


def _extract_r1_summary(sections: dict[str, Any]) -> str:
    """Build a compact markdown summary from R1 Analysis.meta['sections']."""
    if not sections:
        return ""

    seen_headings: set[str] = set()
    parts: list[str] = []
    for key, heading, budget in _R1_SECTION_MAP:
        if heading in seen_headings:
            continue
        html = sections.get(key)
        if not html or not isinstance(html, str) or not html.strip():
            continue
        md = _html_to_markdown(html)
        if not md:
            continue
        parts.append(f"### {heading}\n\n{_truncate(md, budget)}")
        seen_headings.add(heading)

    return "\n\n".join(parts).strip()


def _extract_strategy_summary(sections: dict[str, Any]) -> str:
    """Build a compact markdown summary from StrategyReport.sections."""
    if not sections:
        return ""

    parts: list[str] = []
    for key, heading, budget in _STRATEGY_SECTION_MAP:
        content = sections.get(key)
        if not content or not isinstance(content, str) or not content.strip():
            continue
        md = _html_to_markdown(content) if "<" in content else content.strip()
        if not md:
            continue
        parts.append(f"### {heading}\n\n{_truncate(md, budget)}")

    return "\n\n".join(parts).strip()


# ---------------------------------------------------------------------------
# Score loader (via ReportHistory)
# ---------------------------------------------------------------------------

_SCORE_KEY_ALIASES: dict[str, list[str]] = {
    "total": ["total", "overall", "gesamt", "gesamtscore", "overall_score"],
    "spielregeln": [
        "spielregeln", "governance", "compliance", "rules",
        "governance_score", "spielregeln_score",
    ],
    "sicherheit": [
        "sicherheit", "security", "safety",
        "security_score", "sicherheit_score",
    ],
    "wertschoepfung": [
        "wertschoepfung", "wertschöpfung", "value", "benefit",
        "value_score", "wertschoepfung_score",
    ],
    "befaehigung": [
        "befaehigung", "befähigung", "enablement", "enabling",
        "enablement_score", "befaehigung_score",
    ],
}


def _pick_score(scores: dict[str, Any], canonical: str) -> int:
    """Return the best-match integer score for one canonical key."""
    if not scores:
        return 0
    # Direct lookup
    for alias in _SCORE_KEY_ALIASES.get(canonical, [canonical]):
        if alias in scores:
            val = scores[alias]
            try:
                return int(round(float(val)))
            except (TypeError, ValueError):
                continue
    # Case-insensitive fallback
    lower = {k.lower(): v for k, v in scores.items() if isinstance(k, str)}
    for alias in _SCORE_KEY_ALIASES.get(canonical, [canonical]):
        val = lower.get(alias.lower())
        if val is not None:
            try:
                return int(round(float(val)))
            except (TypeError, ValueError):
                continue
    return 0


def _load_latest_scores(db, briefing_id: int) -> dict[str, int]:
    """Find latest ReportHistory row for this briefing and extract canonical scores."""
    from models import Report, ReportHistory
    from sqlalchemy import desc

    row = (
        db.query(ReportHistory)
        .join(Report, Report.id == ReportHistory.report_id)
        .filter(Report.briefing_id == briefing_id)
        .order_by(desc(ReportHistory.version), desc(ReportHistory.id))
        .first()
    )
    if not row or not row.scores_json:
        return {
            "total": 0,
            "spielregeln": 0,
            "sicherheit": 0,
            "wertschoepfung": 0,
            "befaehigung": 0,
        }

    return {
        key: _pick_score(row.scores_json, key)
        for key in ("total", "spielregeln", "sicherheit", "wertschoepfung", "befaehigung")
    }


# ---------------------------------------------------------------------------
# Context loader
# ---------------------------------------------------------------------------

def load_report_context(briefing_id: int) -> dict[str, Any]:
    """
    Synchronously load briefing + latest R1 analysis + strategy report.

    Returns the dict of placeholder values for the Coach system prompt.
    Raises ValueError if the briefing doesn't exist.
    """
    from models import Analysis, Briefing, StrategyReport

    db = SessionLocal()
    try:
        briefing = db.get(Briefing, briefing_id)
        if briefing is None:
            raise ValueError(f"Briefing {briefing_id} not found")

        analysis = (
            db.query(Analysis)
            .filter(Analysis.briefing_id == briefing_id)
            .order_by(Analysis.id.desc())
            .first()
        )

        strategy = (
            db.query(StrategyReport)
            .filter(StrategyReport.briefing_id == briefing_id)
            .order_by(StrategyReport.id.desc())
            .first()
        )

        answers: dict[str, Any] = briefing.answers or {}

        r1_sections = analysis.sections if analysis is not None else {}
        strategy_sections: dict[str, Any] = {}
        if strategy is not None and isinstance(strategy.sections, dict):
            strategy_sections = strategy.sections

        scores = _load_latest_scores(db, briefing_id)
    finally:
        db.close()

    # Compose summaries
    r1_summary = _extract_r1_summary(r1_sections)
    strategy_summary = _extract_strategy_summary(strategy_sections)

    report_types: list[str] = []
    if r1_summary:
        report_types.append("r1")
    if strategy_summary:
        report_types.append("strategy")
    if not report_types:
        report_types = ["r1"]  # fallback label; summaries may be empty

    # Normalise multi-select / list fields
    ki_ziele_raw = answers.get("ki_ziele")
    if isinstance(ki_ziele_raw, list):
        ki_ziele = ", ".join(str(x) for x in ki_ziele_raw if x)
    else:
        ki_ziele = str(ki_ziele_raw or "").strip()

    return {
        "report_types": "+".join(report_types),
        "branche": str(answers.get("branche") or "unbekannt"),
        "size": str(answers.get("unternehmensgroesse") or "unbekannt"),
        "country": str(answers.get("country") or "DE"),
        "bundesland": str(answers.get("bundesland") or ""),
        "budget": str(answers.get("investitionsbudget") or "unklar"),
        "ki_ziele": ki_ziele or "—",
        "hauptleistung": str(answers.get("hauptleistung") or ""),
        "strategische_ziele": str(answers.get("strategische_ziele") or ""),
        "vision_3_jahre": str(answers.get("vision_3_jahre") or ""),
        "gesamtscore": scores["total"],
        "score_spielregeln": scores["spielregeln"],
        "score_sicherheit": scores["sicherheit"],
        "score_wertschoepfung": scores["wertschoepfung"],
        "score_befaehigung": scores["befaehigung"],
        "r1_markdown": r1_summary or "_Keine R1-Zusammenfassung verfügbar._",
        "kpa_markdown": "_Keine KPA-Zusammenfassung in v1 verfügbar._",
        "strategy_markdown": strategy_summary or "_Kein Strategy-Report vorhanden._",
    }


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def build_system_prompt(context: dict[str, Any]) -> str:
    """Fill the coach prompt template with the given context dict."""
    if not _COACH_PROMPT_TEMPLATE:
        raise RuntimeError("Coach prompt template not loaded")
    try:
        return _COACH_PROMPT_TEMPLATE.format(**context)
    except KeyError as exc:
        raise RuntimeError(f"Missing context key for coach prompt: {exc}") from exc


# ---------------------------------------------------------------------------
# Streaming entry-point
# ---------------------------------------------------------------------------

def _trim_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Clean + cap incoming conversation history."""
    cleaned: list[dict[str, Any]] = []
    for msg in history or []:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str) or not content.strip():
            continue
        cleaned.append({"role": role, "content": content})
    if COACH_HISTORY_LIMIT > 0 and len(cleaned) > COACH_HISTORY_LIMIT:
        cleaned = cleaned[-COACH_HISTORY_LIMIT:]
    return cleaned


async def stream_coach_response(
    briefing_id: int,
    user_message: str,
    history: list[dict[str, Any]],
) -> AsyncIterator[str]:
    """
    Yield thinking-filtered text chunks for a coach response.

    The filter buffers output until it can cleanly strip <coach_thinking>
    blocks, so the user never sees internal deliberation.
    """
    client = _get_async_client()
    if client is None:
        yield "Der Coach ist derzeit nicht verfügbar (Konfigurationsfehler)."
        return

    context = load_report_context(briefing_id)
    system_prompt = build_system_prompt(context)

    messages = _trim_history(history)
    messages.append({"role": "user", "content": user_message})

    buffer = ""
    inside_thinking = False

    try:
        async with client.messages.stream(
            model=COACH_MODEL,
            max_tokens=COACH_MAX_TOKENS,
            temperature=COACH_TEMPERATURE,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                buffer += text

                while True:
                    if not inside_thinking:
                        open_idx = buffer.find(_OPEN_TAG)
                        if open_idx == -1:
                            # Safe to flush everything except a trailing partial tag
                            safe_cut = _safe_flush_cut(buffer, _OPEN_TAG)
                            if safe_cut > 0:
                                yield buffer[:safe_cut]
                                buffer = buffer[safe_cut:]
                            break
                        # Flush text before the opening tag
                        if open_idx > 0:
                            yield buffer[:open_idx]
                        buffer = buffer[open_idx + len(_OPEN_TAG):]
                        inside_thinking = True
                    else:
                        close_idx = buffer.find(_CLOSE_TAG)
                        if close_idx == -1:
                            # Drop buffered thinking content, keep a short tail for tag boundary
                            buffer = buffer[-(len(_CLOSE_TAG) - 1):]
                            break
                        buffer = buffer[close_idx + len(_CLOSE_TAG):]
                        inside_thinking = False

        # Final flush after stream end
        if not inside_thinking and buffer:
            yield buffer

    except Exception as exc:
        log.exception("[COACH] Streaming failed: %s", exc)
        yield " [Fehler beim Laden der Coach-Antwort]"


def _safe_flush_cut(buffer: str, open_tag: str) -> int:
    """
    Return the index up to which the buffer can be safely yielded without
    truncating a partial `<coach_thinking>` opener that might span chunks.
    """
    # If buffer is shorter than a full tag, check for partial-prefix match at end.
    tail_len = len(open_tag) - 1
    tail = buffer[-tail_len:] if tail_len > 0 else ""
    for i in range(len(tail), 0, -1):
        if open_tag.startswith(tail[-i:]):
            return len(buffer) - i
    return len(buffer)
