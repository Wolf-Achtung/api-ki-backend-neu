# -*- coding: utf-8 -*-
"""
services/news_researcher.py — Weekly news research pipeline.

Recherchiert KI-Regulierung, Förderprogramme und Cybersicherheit-News
via Tavily, fasst sie per GPT-4o zusammen und sendet einen HTML-Draft
per E-Mail an Wolf zur redaktionellen Prüfung.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.provider_tavily import search as tavily_search
from services.openai_retry import openai_request_simple
from services.mailer import Mailer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Search queries — one per news category
# ---------------------------------------------------------------------------
NEWS_QUERIES: List[Dict[str, str]] = [
    {
        "query": "EU AI Act 2026 Umsetzung Deutschland Unternehmen",
        "category": "EU AI ACT",
        "tag_color": "#3b82f6",
    },
    {
        "query": "KI Förderung KMU Deutschland 2026 Programm",
        "category": "FÖRDERUNG",
        "tag_color": "#10b981",
    },
    {
        "query": "DSGVO KI Datenschutz Unternehmen Urteil 2026",
        "category": "DATENSCHUTZ",
        "tag_color": "#8b5cf6",
    },
    {
        "query": "NIS2 Cybersicherheit Deutschland Unternehmen Pflicht",
        "category": "NIS2",
        "tag_color": "#ef4444",
    },
    {
        "query": "KI Mittelstand Deutschland Studie Adoption 2026",
        "category": "KI-MARKT",
        "tag_color": "#f59e0b",
    },
]

# Allowed domains for DE-focused results
_INCLUDE_DOMAINS = [
    "heise.de",
    "golem.de",
    "handelsblatt.com",
    "bsi.bund.de",
    "bitkom.org",
    "dihk.de",
    "bmwk.de",
    "kfw.de",
    "europa.eu",
    "eur-lex.europa.eu",
    "bafa.de",
    "bmbf.de",
    "faz.net",
    "sueddeutsche.de",
    "tagesschau.de",
    "netzpolitik.org",
    "t3n.de",
    "computerwoche.de",
    "it-daily.net",
]

# Tag colors for HTML rendering
TAG_COLORS: Dict[str, str] = {
    "EU AI ACT": "#3b82f6",
    "FÖRDERUNG": "#10b981",
    "DATENSCHUTZ": "#8b5cf6",
    "NIS2": "#ef4444",
    "KI-MARKT": "#f59e0b",
    "CYBERSICHERHEIT": "#6366f1",
}

# Prompt file path
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "news_summarizer.md"


# ---------------------------------------------------------------------------
# Step 1: Tavily research
# ---------------------------------------------------------------------------
def research_news() -> List[Dict[str, Any]]:
    """Run all search queries via Tavily and return deduplicated results."""
    all_results: List[Dict[str, Any]] = []

    for q in NEWS_QUERIES:
        try:
            results = tavily_search(
                query=q["query"],
                max_results=5,
                days=30,
            )
            for r in results:
                all_results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:500],
                    "category": q["category"],
                    "tag_color": q["tag_color"],
                })
        except Exception as e:
            logger.warning("[NEWS] Tavily query failed: %s: %s", q["query"], e)
            continue

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique: List[Dict[str, Any]] = []
    for r in all_results:
        if r["url"] and r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            unique.append(r)

    logger.info("[NEWS] %d raw results, %d unique after dedup", len(all_results), len(unique))
    return unique[:15]


# ---------------------------------------------------------------------------
# Step 2: LLM summarization
# ---------------------------------------------------------------------------
def summarize_news(raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarize raw search results into structured news items via GPT-4o."""
    try:
        system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("[NEWS] Prompt file not found: %s", _PROMPT_PATH)
        return []

    results_text = "\n\n".join(
        f"[{r['category']}] {r['title']}\n"
        f"URL: {r['url']}\n"
        f"Inhalt: {r['content']}"
        for r in raw_results
    )

    response_text = openai_request_simple(
        section="news_summarizer",
        prompt=results_text,
        system_prompt=system_prompt,
        model="gpt-4o",
        temperature=0.3,
        max_tokens=2000,
    )

    if not response_text:
        logger.error("[NEWS] LLM summarization returned empty response")
        return []

    try:
        data = json.loads(response_text)
        items: List[Dict[str, Any]] = data.get("news_items", [])
        return items
    except json.JSONDecodeError:
        logger.error("[NEWS] Failed to parse LLM response as JSON")
        return []


# ---------------------------------------------------------------------------
# Step 3: HTML snippet generation
# ---------------------------------------------------------------------------
def generate_html_snippets(news_items: List[Dict[str, Any]]) -> str:
    """Generate copy-paste-ready HTML blocks matching the Aktuell page design."""
    snippets: List[str] = []

    for item in news_items:
        color = TAG_COLORS.get(item.get("category", ""), "#6b7280")
        title = _escape_html(item.get("title", ""))
        summary = _escape_html(item.get("summary", ""))
        date = _escape_html(item.get("date", ""))
        category = _escape_html(item.get("category", ""))
        source_url = _escape_html(item.get("source_url", ""))
        cta_text = _escape_html(item.get("cta_text", "Mehr →"))

        snippet = (
            f'<!-- NEWS: {date} — {category} -->\n'
            f'<div style="margin-bottom: 2rem;">\n'
            f'  <time style="color: #6b7280; font-size: 0.85rem;">{date}</time>\n'
            f'  <span style="display: inline-block; background: {color}; color: white;\n'
            f'    font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; margin-left: 8px;\n'
            f'    font-weight: 600; letter-spacing: 0.05em;">{category}</span>\n'
            f'  <h3 style="margin: 0.5rem 0 0.25rem; font-size: 1.05rem;">\n'
            f'    {title}\n'
            f'  </h3>\n'
            f'  <p style="color: #4a5568; margin: 0 0 0.5rem; font-size: 0.95rem;">\n'
            f'    {summary}\n'
            f'  </p>\n'
            f'  <a href="{source_url}" target="_blank" rel="noopener"\n'
            f'    style="color: #2b6cb0; text-decoration: none; font-weight: 500;">\n'
            f'    {cta_text}\n'
            f'  </a>\n'
            f'</div>'
        )
        snippets.append(snippet)

    today = datetime.now().strftime("%d.%m.%Y")
    header = (
        f'<!--\n'
        f'  ═══════════════════════════════════════════════\n'
        f'  NEWS-DRAFT vom {today}\n'
        f'  Recherchiert via Tavily · Zusammengefasst via GPT-4o\n'
        f'\n'
        f'  BITTE PRÜFEN:\n'
        f'  ✓ Sind die Fakten korrekt?\n'
        f'  ✓ Sind die Links erreichbar?\n'
        f'  ✓ Ist etwas dabei, das nicht auf die Seite passt?\n'
        f'\n'
        f'  Geprüfte Karten in aktuell/index.html einfügen\n'
        f'  (im Bereich <div class="news-list"> nach dem letzten Eintrag)\n'
        f'  ═══════════════════════════════════════════════\n'
        f'-->\n'
    )
    return header + "\n\n".join(snippets)


# ---------------------------------------------------------------------------
# Step 4: Email draft to Wolf
# ---------------------------------------------------------------------------
async def send_news_draft(html_snippets: str, news_items: List[Dict[str, Any]]) -> None:
    """Send the news draft via email for editorial review."""
    recipient = os.getenv("ADMIN_NOTIFY_EMAIL")
    if not recipient:
        logger.error("[NEWS] ADMIN_NOTIFY_EMAIL not set — cannot send draft")
        return

    today = datetime.now().strftime("%d.%m.%Y")

    # Build preview cards
    preview_cards = ""
    for item in news_items:
        color = TAG_COLORS.get(item.get("category", ""), "#6b7280")
        preview_cards += (
            f'<div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #e2e8f0;">\n'
            f'  <span style="display: inline-block; background: {color}; color: white;\n'
            f'    font-size: 0.7rem; padding: 2px 8px; border-radius: 4px;\n'
            f'    font-weight: 600;">{_escape_html(item.get("category", ""))}</span>\n'
            f'  <span style="color: #6b7280; font-size: 0.8rem; margin-left: 8px;">'
            f'{_escape_html(item.get("date", ""))}</span>\n'
            f'  <h3 style="margin: 0.5rem 0 0.25rem; font-size: 1rem;">'
            f'{_escape_html(item.get("title", ""))}</h3>\n'
            f'  <p style="color: #4a5568; margin: 0 0 0.5rem; font-size: 0.9rem;">'
            f'{_escape_html(item.get("summary", ""))}</p>\n'
            f'  <a href="{_escape_html(item.get("source_url", ""))}" style="color: #2b6cb0; '
            f'font-size: 0.85rem;">{_escape_html(item.get("cta_text", "Mehr →"))}</a>\n'
            f'</div>\n'
        )

    escaped_snippets = html_snippets.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    email_html = (
        f'<div style="font-family: Arial, sans-serif; max-width: 640px; margin: 0 auto; '
        f'color: #1a202c;">\n'
        f'  <h2 style="color: #2b6cb0; border-bottom: 2px solid #2b6cb0; padding-bottom: 8px;">'
        f'News-Entwurf für ki-sicherheit.jetzt/aktuell</h2>\n'
        f'  <p style="color: #4a5568;">'
        f'{len(news_items)} relevante Meldungen gefunden ({today}).<br>'
        f'Geprüfte Einträge in <code>aktuell/index.html</code> einfügen.</p>\n'
        f'  <hr style="border: 1px solid #e2e8f0;">\n'
        f'  <h3 style="color: #1a202c;">Vorschau</h3>\n'
        f'{preview_cards}\n'
        f'  <hr style="border: 1px solid #e2e8f0;">\n'
        f'  <h3 style="color: #1a202c;">HTML zum Copy-Paste</h3>\n'
        f'  <div style="background: #f7fafc; padding: 16px; border-radius: 8px;\n'
        f'    font-family: monospace; font-size: 12px; white-space: pre-wrap;\n'
        f'    border: 1px solid #e2e8f0; overflow-x: auto;">'
        f'{escaped_snippets}</div>\n'
        f'</div>'
    )

    mailer = Mailer.from_settings()
    await mailer.send(
        to=recipient,
        subject=f"News-Entwurf ki-sicherheit.jetzt — {today}",
        text=f"{len(news_items)} News-Entwürfe für ki-sicherheit.jetzt/aktuell ({today}). Bitte HTML-Version dieser E-Mail öffnen.",
        html=email_html,
    )
    logger.info("[NEWS] Draft email sent to %s", recipient)


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------
async def run_news_pipeline() -> Dict[str, Any]:
    """Execute the full news research pipeline: search → summarize → email."""
    # Step 1: Research
    raw_results = research_news()
    logger.info("[NEWS] %d raw results from Tavily", len(raw_results))

    if not raw_results:
        return {"status": "no_results", "message": "Keine relevanten News gefunden"}

    # Step 2: Summarize
    news_items = summarize_news(raw_results)
    logger.info("[NEWS] %d news items after LLM summary", len(news_items))

    if not news_items:
        return {"status": "no_items", "message": "LLM-Zusammenfassung hat keine Items ergeben"}

    # Step 3: Generate HTML
    html_snippets = generate_html_snippets(news_items)

    # Step 4: Send email
    await send_news_draft(html_snippets, news_items)

    return {
        "status": "sent",
        "items": len(news_items),
        "date": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _escape_html(text: str) -> str:
    """Minimal HTML escaping for user-generated content."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
