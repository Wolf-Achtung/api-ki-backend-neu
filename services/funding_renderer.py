# -*- coding: utf-8 -*-
"""
Funding Renderer - Unified HTML rendering for funding programmes.

This module provides a central rendering interface for all funding variants
(DE, EN-DE, EU-Core), ensuring consistent HTML structure and styling.

Version: 1.0.0
"""
from __future__ import annotations

import logging
from typing import List, Optional

from services.funding_types import (
    FundingProgramView,
    FundingRenderContext,
    FundingScope,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Main Renderer Functions
# =============================================================================


def render_funding_html(context: FundingRenderContext) -> str:
    """
    Render funding programmes into HTML.

    This is the central rendering function used by all funding variants.
    Produces consistent HTML structure regardless of scope (DE, EN-DE, EU-Core).

    Args:
        context: FundingRenderContext with programmes and metadata

    Returns:
        HTML string for embedding in report, or empty string if no programmes
    """
    if not context.has_programmes:
        return ""

    html_parts: List[str] = []

    # Determine CSS class based on scope
    css_class = _get_css_class(context.scope)
    html_parts.append(f'<div class="funding-programmes{css_class}">')

    # Render each programme
    for prog in context.programmes:
        html_parts.append(_render_programme(prog, context))

    html_parts.append("</div>")

    # Add disclaimer for EU-Core
    if context.show_disclaimer:
        html_parts.append(_render_disclaimer(context.lang))

    return "\n".join(html_parts)


def render_funding_html_simple(
    programmes: List[FundingProgramView],
    scope: FundingScope = "DE",
    lang: str = "de",
    show_disclaimer: bool = False,
) -> str:
    """
    Convenience function for simple rendering without full context.

    Args:
        programmes: List of FundingProgramView objects
        scope: Funding scope ("DE", "DE_EN", "EU_CORE")
        lang: Language code ("de" or "en")
        show_disclaimer: Whether to show EU disclaimer

    Returns:
        HTML string
    """
    context = FundingRenderContext(
        scope=scope,
        programmes=programmes,
        lang=lang,
        show_disclaimer=show_disclaimer,
    )
    return render_funding_html(context)


# =============================================================================
# Internal Rendering Helpers
# =============================================================================


def _get_css_class(scope: FundingScope) -> str:
    """Get additional CSS class based on scope."""
    if scope == "EU_CORE":
        return " eu-core"
    return ""


def _render_programme(prog: FundingProgramView, context: FundingRenderContext) -> str:
    """Render a single funding programme to HTML."""
    parts: List[str] = []

    parts.append('<div class="funding-programme">')
    parts.append(f"  <h4>{_escape_html(prog.name)}</h4>")

    # Summary
    if prog.summary:
        parts.append(f'  <p class="summary">{_escape_html(prog.summary)}</p>')

    # Details list
    parts.append('  <ul class="details">')
    parts.extend(_render_details(prog, context))
    parts.append("  </ul>")

    # Notes (for EU-Core)
    if prog.notes and context.scope == "EU_CORE":
        parts.append(f'  <p class="notes"><em>{_escape_html(prog.notes)}</em></p>')

    # URL link
    if prog.url:
        link_text = _get_link_text(context.lang)
        parts.append(
            f'  <p class="url"><a href="{prog.url}" target="_blank">{link_text}</a></p>'
        )

    parts.append("</div>")

    return "\n".join(parts)


def _render_details(prog: FundingProgramView, context: FundingRenderContext) -> List[str]:
    """Render programme details as list items."""
    items: List[str] = []
    lang = context.lang

    # Labels based on language and scope
    if lang == "en":
        if context.scope == "EU_CORE":
            # EU-Core uses slightly different labels
            if prog.funding_type:
                items.append(f"    <li><strong>Funding type:</strong> {_escape_html(prog.funding_type)}</li>")
            if prog.funding_rate:
                items.append(f"    <li><strong>Typical co-funding rate:</strong> {_escape_html(prog.funding_rate)}</li>")
            if prog.max_amount:
                items.append(f"    <li><strong>Typical amount:</strong> {_escape_html(prog.max_amount)}</li>")
            if prog.target_groups:
                targets_str = ", ".join(prog.target_groups)
                items.append(f"    <li><strong>Target groups:</strong> {_escape_html(targets_str)}</li>")
            if prog.ai_relevance:
                items.append(f"    <li><strong>AI relevance:</strong> {_escape_html(prog.ai_relevance)}</li>")
        else:
            # EN-DE (German programmes in English)
            if prog.funding_type:
                items.append(f"    <li><strong>Type:</strong> {_escape_html(prog.funding_type)}</li>")
            if prog.funding_rate:
                items.append(f"    <li><strong>Funding Rate:</strong> {_escape_html(prog.funding_rate)}</li>")
            if prog.max_amount:
                items.append(f"    <li><strong>Maximum Amount:</strong> {_escape_html(prog.max_amount)}</li>")
            if prog.scope_label:
                items.append(f"    <li><strong>Region:</strong> {_escape_html(prog.scope_label)}</li>")
    else:
        # German labels
        if prog.funding_type:
            items.append(f"    <li><strong>Förderart:</strong> {_escape_html(prog.funding_type)}</li>")
        if prog.funding_rate:
            items.append(f"    <li><strong>Fördersatz:</strong> {_escape_html(prog.funding_rate)}</li>")
        if prog.max_amount:
            items.append(f"    <li><strong>Max. Betrag:</strong> {_escape_html(prog.max_amount)}</li>")
        if prog.scope_label:
            items.append(f"    <li><strong>Region:</strong> {_escape_html(prog.scope_label)}</li>")

    return items


def _render_disclaimer(lang: str) -> str:
    """Render EU funding disclaimer."""
    if lang == "en":
        return (
            '<p class="funding-disclaimer small muted">'
            "Note: EU funding programmes have varying deadlines, eligibility criteria, and call-specific "
            "requirements. The information above provides general guidance. Please consult official "
            "programme documentation and national contact points for current opportunities."
            "</p>"
        )
    else:
        return (
            '<p class="funding-disclaimer small muted">'
            "Hinweis: EU-Förderprogramme haben unterschiedliche Fristen, Zulassungskriterien und "
            "ausschreibungsspezifische Anforderungen. Die obigen Informationen dienen als allgemeine "
            "Orientierung. Bitte konsultieren Sie die offizielle Programmdokumentation und nationale "
            "Kontaktstellen für aktuelle Möglichkeiten."
            "</p>"
        )


def _get_link_text(lang: str) -> str:
    """Get link text for programme URL."""
    if lang == "en":
        return "More information"
    return "Mehr Informationen"


def _escape_html(text: str) -> str:
    """
    Basic HTML escaping for user content.

    Note: This is a simple implementation. For production, consider using
    markupsafe or similar library.
    """
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# =============================================================================
# Conversion Helpers (for backwards compatibility)
# =============================================================================


def programmes_to_views(
    programmes: List[dict],
    lang: str = "de",
    scope_label: Optional[str] = None,
) -> List[FundingProgramView]:
    """
    Convert list of programme dictionaries to FundingProgramView objects.

    This helper maintains backwards compatibility with existing code that
    uses raw dictionaries.

    Args:
        programmes: List of programme dictionaries
        lang: Language code ("de" or "en")
        scope_label: Default scope label for all programmes

    Returns:
        List of FundingProgramView objects
    """
    return [
        FundingProgramView.from_dict(p, lang, scope_label)
        for p in programmes
    ]
