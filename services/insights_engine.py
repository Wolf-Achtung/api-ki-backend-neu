# -*- coding: utf-8 -*-
"""
Sprint G17-B: Insight Cards Engine

Generates real-world insight cards for reports based on segment data.
Each report receives 3-5 insight cards showing how they compare to similar businesses.

Version: 1.0.0
"""
from __future__ import annotations

import html
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

INSIGHTS_ENGINE_ENABLED = os.environ.get("INSIGHTS_ENGINE_ENABLED", "1") == "1"
INSIGHTS_TOP_CARDS_PER_REPORT = int(os.environ.get("INSIGHTS_TOP_CARDS_PER_REPORT", "5"))

# G17.1-B: Reliability Filter Configuration
INSIGHTS_REQUIRE_RELIABLE_SEGMENT = os.environ.get("INSIGHTS_REQUIRE_RELIABLE_SEGMENT", "1") == "1"
INSIGHTS_FALLBACK_TO_GENERIC = os.environ.get("INSIGHTS_FALLBACK_TO_GENERIC", "1") == "1"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class InsightCard:
    """Single insight card."""
    title: str
    severity: str  # info, highlight, opportunity, risk
    body_html: str
    category: str = "general"  # position, use_cases, roi, warnings, funding
    priority: int = 0  # Lower = higher priority

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "severity": self.severity,
            "body_html": self.body_html,
            "category": self.category,
        }


@dataclass
class InsightResult:
    """Complete insights result for a report."""
    cards: List[InsightCard] = field(default_factory=list)
    summary_html: str = ""
    cards_html: str = ""
    segment_label: str = ""
    has_sufficient_data: bool = False
    # G17.1-B: Reliability metadata
    is_reliable: bool = False
    is_generic_fallback: bool = False
    segment_stability: str = "unknown"  # strong, medium, weak, unknown
    reliability_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "INSIGHT_CARDS": [card.to_dict() for card in self.cards],
            "summary_html": self.summary_html,
            "cards_html": self.cards_html,
            "segment_label": self.segment_label,
            "has_sufficient_data": self.has_sufficient_data,
            # G17.1-B fields
            "is_reliable": self.is_reliable,
            "is_generic_fallback": self.is_generic_fallback,
            "segment_stability": self.segment_stability,
            "reliability_note": self.reliability_note,
        }


# =============================================================================
# INSIGHT CARD GENERATORS
# =============================================================================

def build_report_insights(
    report_sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> InsightResult:
    """
    Build insight cards for a report.

    Args:
        report_sections: Report sections dictionary
        profile: Profile data (optional)

    Returns:
        InsightResult with cards and HTML
    """
    if not INSIGHTS_ENGINE_ENABLED:
        log.debug("Insights engine disabled")
        return InsightResult()

    from services.feedback_analyzer import (
        get_segment_for_report,
        get_segment_comparison,
        is_segment_reliable,
        SegmentStats,
    )

    # Get segment stats
    segment_stats = get_segment_for_report(report_sections, profile)
    comparison = get_segment_comparison(report_sections, profile)

    if not segment_stats or not comparison.get("segment_found"):
        log.debug("No segment data available for insights")
        return InsightResult(
            summary_html="<p>Für Ihr Segment liegen noch nicht genügend Vergleichsdaten vor.</p>",
            has_sufficient_data=False,
            segment_stability="unknown",
        )

    # G17.1-B: Check segment reliability
    segment_is_reliable = is_segment_reliable(segment_stats)
    segment_stability = getattr(segment_stats, "segment_stability", "unknown")

    # If reliability filter is enabled and segment is unreliable, use fallback
    if INSIGHTS_REQUIRE_RELIABLE_SEGMENT and not segment_is_reliable:
        log.info(f"Segment unstable (stability={segment_stability}), using fallback cards")

        if INSIGHTS_FALLBACK_TO_GENERIC:
            # Build generic fallback cards based on size/branch
            return _build_generic_fallback_insights(
                report_sections, profile, segment_stats, segment_stability
            )
        else:
            # Return empty result with reliability note
            return InsightResult(
                summary_html="<p>Die Datenbasis für Ihr Segment ist noch nicht ausreichend für detaillierte Insights.</p>",
                has_sufficient_data=False,
                is_reliable=False,
                segment_stability=segment_stability,
                reliability_note="Segment hat zu wenige Datenpunkte oder zu hohe Varianz",
            )

    # Build cards (reliable segment path)
    cards: List[InsightCard] = []

    # 1. Position card
    position_card = _build_position_card(comparison, segment_stats)
    if position_card:
        cards.append(position_card)

    # 2. Score comparison cards
    score_cards = _build_score_cards(report_sections, segment_stats)
    cards.extend(score_cards)

    # 3. Use case potential card
    use_case_card = _build_use_case_card(report_sections, segment_stats)
    if use_case_card:
        cards.append(use_case_card)

    # 4. ROI comparison card
    roi_card = _build_roi_card(report_sections, segment_stats)
    if roi_card:
        cards.append(roi_card)

    # 5. Risk/warning card
    warning_card = _build_warning_card(report_sections, segment_stats)
    if warning_card:
        cards.append(warning_card)

    # Sort by priority and limit
    cards.sort(key=lambda c: c.priority)
    cards = cards[:INSIGHTS_TOP_CARDS_PER_REPORT]

    # Build HTML outputs
    segment_label = comparison.get("segment_label", "Ihr Segment")
    summary_html = _build_summary_html(cards, segment_label)
    cards_html = _build_cards_html(cards)

    # G17.1-B: Add reliability indicator for medium stability
    reliability_note = ""
    if segment_stability == "medium":
        reliability_note = "Segment-Daten basieren auf begrenzter Stichprobe"
        # Add subtle note to summary
        summary_html = _add_reliability_note_to_summary(summary_html, segment_stability)

    result = InsightResult(
        cards=cards,
        summary_html=summary_html,
        cards_html=cards_html,
        segment_label=segment_label,
        has_sufficient_data=True,
        is_reliable=segment_is_reliable,
        is_generic_fallback=False,
        segment_stability=segment_stability,
        reliability_note=reliability_note,
    )

    log.info(f"Generated {len(cards)} insight cards for segment: {segment_label} (stability={segment_stability})")

    return result


def _build_generic_fallback_insights(
    report_sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]],
    segment_stats: Any,
    segment_stability: str,
) -> InsightResult:
    """
    Build generic fallback insight cards when segment is unreliable.

    G17.1-B: Provides general insights based on size + branch without
    relying on potentially skewed segment statistics.

    Args:
        report_sections: Report sections dictionary
        profile: Profile data
        segment_stats: Segment stats (may be unreliable)
        segment_stability: Current stability level

    Returns:
        InsightResult with generic cards
    """
    cards: List[InsightCard] = []

    # Extract size and branch for generic insights
    size_label = "solo"
    branch = "other"

    if profile:
        size_label = profile.get("size_label", "solo")
        branch = profile.get("branch", "") or "other"

    # 1. General size-based insight card
    size_card = _build_generic_size_card(size_label)
    if size_card:
        cards.append(size_card)

    # 2. General maturity insight (if we can determine from report)
    maturity_card = _build_generic_maturity_card(report_sections)
    if maturity_card:
        cards.append(maturity_card)

    # 3. General AI readiness tip
    ai_readiness_card = _build_generic_ai_readiness_card(report_sections, size_label)
    if ai_readiness_card:
        cards.append(ai_readiness_card)

    # Sort and limit
    cards.sort(key=lambda c: c.priority)
    cards = cards[:INSIGHTS_TOP_CARDS_PER_REPORT]

    # Build HTML outputs
    segment_label = f"{_size_label_de(size_label)} · Allgemein"
    summary_html = _build_generic_summary_html(cards, segment_label)
    cards_html = _build_cards_html(cards)

    return InsightResult(
        cards=cards,
        summary_html=summary_html,
        cards_html=cards_html,
        segment_label=segment_label,
        has_sufficient_data=True,
        is_reliable=False,
        is_generic_fallback=True,
        segment_stability=segment_stability,
        reliability_note="Allgemeine Insights - spezifische Segment-Daten noch nicht ausreichend",
    )


def _build_generic_size_card(size_label: str) -> Optional[InsightCard]:
    """Build generic insight card based on company size."""
    size_insights = {
        "solo": {
            "title": "Typische Herausforderungen für Solo-Unternehmer",
            "body": """<p>📊 Als Solo-Unternehmer stehen Sie vor einzigartigen Herausforderungen bei der KI-Einführung:</p>
            <ul style="margin:8px 0;padding-left:20px;">
                <li>Begrenzte Zeit für Experimentieren mit neuen Tools</li>
                <li>Fokus auf schnelle ROI-Realisierung</li>
                <li>Niedrigschwellige, sofort einsetzbare Lösungen bevorzugt</li>
            </ul>
            <p class="insight-detail">Empfehlung: Starten Sie mit einem fokussierten Use Case.</p>""",
        },
        "team": {
            "title": "KI-Potenzial für kleine Teams",
            "body": """<p>📊 Kleine Teams (2-10 Personen) profitieren besonders von:</p>
            <ul style="margin:8px 0;padding-left:20px;">
                <li>Automatisierung wiederkehrender Aufgaben</li>
                <li>Kollaborativen KI-Tools für Wissensaustausch</li>
                <li>Skalierbare Lösungen, die mit dem Team wachsen</li>
            </ul>
            <p class="insight-detail">Empfehlung: Definieren Sie gemeinsame KI-Richtlinien.</p>""",
        },
        "kmu": {
            "title": "KI-Strategie für KMU",
            "body": """<p>📊 Als KMU haben Sie die Ressourcen für strategische KI-Implementierung:</p>
            <ul style="margin:8px 0;padding-left:20px;">
                <li>Abteilungsübergreifende KI-Governance erforderlich</li>
                <li>Integration mit bestehenden Systemen priorisieren</li>
                <li>Mitarbeiter-Enablement als Erfolgsfaktor</li>
            </ul>
            <p class="insight-detail">Empfehlung: Etablieren Sie ein KI-Kompetenzzentrum.</p>""",
        },
    }

    insight = size_insights.get(size_label, size_insights["team"])

    return InsightCard(
        title=insight["title"],
        severity="info",
        body_html=insight["body"],
        category="general",
        priority=1,
    )


def _build_generic_maturity_card(report_sections: Dict[str, Any]) -> Optional[InsightCard]:
    """Build generic maturity insight card."""
    overall_score = 0.0
    try:
        overall_score = float(report_sections.get("REIFEGRAD_GESAMT", 0))
    except (ValueError, TypeError):
        return None

    if overall_score <= 0:
        return None

    if overall_score >= 70:
        title = "Fortgeschrittene KI-Reife"
        body = """<p>✅ Ihr Gesamt-Score deutet auf eine <strong>fortgeschrittene KI-Reife</strong> hin.</p>
        <p class="insight-detail">Fokussieren Sie sich auf Optimierung und Skalierung bestehender KI-Initiativen.</p>"""
        severity = "highlight"
    elif overall_score >= 50:
        title = "Solide KI-Grundlage"
        body = """<p>📊 Sie haben eine <strong>solide Grundlage</strong> für KI-Initiativen geschaffen.</p>
        <p class="insight-detail">Nächste Schritte: Vertiefen Sie Governance und erweitern Sie Use Cases systematisch.</p>"""
        severity = "info"
    else:
        title = "KI-Einstiegsphase"
        body = """<p>📈 Sie befinden sich in der <strong>Einstiegsphase</strong> Ihrer KI-Journey.</p>
        <p class="insight-detail">Empfehlung: Beginnen Sie mit Quick Wins und bauen Sie schrittweise Kompetenz auf.</p>"""
        severity = "opportunity"

    return InsightCard(
        title=title,
        severity=severity,
        body_html=body,
        category="maturity",
        priority=2,
    )


def _build_generic_ai_readiness_card(
    report_sections: Dict[str, Any],
    size_label: str,
) -> Optional[InsightCard]:
    """Build generic AI readiness tip card."""
    # Check governance score if available
    gov_score = 0.0
    try:
        gov_score = float(report_sections.get("REIFEGRAD_GOVERNANCE", 0))
    except (ValueError, TypeError):
        pass

    if gov_score > 0 and gov_score < 50:
        return InsightCard(
            title="Governance als Schlüssel zum KI-Erfolg",
            severity="opportunity",
            body_html="""<p>🔐 <strong>KI-Governance</strong> ist ein häufiger Engpass bei der KI-Einführung.</p>
            <p class="insight-detail">Definieren Sie klare Richtlinien für Datenschutz, Qualitätssicherung
            und Verantwortlichkeiten, bevor Sie skalieren.</p>""",
            category="governance",
            priority=3,
        )

    return InsightCard(
        title="Kontinuierliches Lernen",
        severity="info",
        body_html="""<p>📚 <strong>KI-Kompetenz</strong> entwickelt sich kontinuierlich weiter.</p>
        <p class="insight-detail">Planen Sie regelmäßige Reviews Ihrer KI-Strategie ein,
        um mit den technologischen Entwicklungen Schritt zu halten.</p>""",
        category="general",
        priority=4,
    )


def _size_label_de(size_label: str) -> str:
    """Get German label for size."""
    labels = {
        "solo": "Solo-Unternehmer",
        "team": "Kleines Team",
        "kmu": "KMU",
    }
    return labels.get(size_label, size_label)


def _build_generic_summary_html(cards: List[InsightCard], segment_label: str) -> str:
    """Build summary HTML for generic fallback cards."""
    if not cards:
        return "<p>Allgemeine Empfehlungen für Ihre KI-Strategie.</p>"

    return f"""<p>Basierend auf Ihrem Profil (<strong>{segment_label}</strong>) haben wir
    {len(cards)} allgemeine Empfehlungen für Ihre KI-Strategie zusammengestellt.</p>
    <p class="insight-note" style="font-size:11px;color:#6c757d;margin-top:8px;">
    <em>Hinweis: Für detailliertere, segmentspezifische Insights werden mehr Vergleichsdaten benötigt.</em>
    </p>"""


def _add_reliability_note_to_summary(summary_html: str, stability: str) -> str:
    """Add subtle reliability note to summary HTML for medium stability segments."""
    if stability != "medium":
        return summary_html

    note = """<p class="reliability-note" style="font-size:10px;color:#6c757d;margin-top:8px;font-style:italic;">
    * Basierend auf einer begrenzten Stichprobe. Werte können bei mehr Daten präziser werden.
    </p>"""

    return summary_html + note


def _build_position_card(
    comparison: Dict[str, Any],
    segment_stats: Any,
) -> Optional[InsightCard]:
    """Build market position card."""
    position = comparison.get("position", "unknown")
    position_text = comparison.get("position_text", "")
    current_score = comparison.get("current_score", 0)
    avg_score = comparison.get("segment_avg_score", 0)
    segment_label = comparison.get("segment_label", "Ihrem Segment")
    report_count = comparison.get("report_count", 0)

    if position == "unknown" or not position_text:
        return None

    # Determine severity
    if position == "oberes_drittel":
        severity = "highlight"
        emoji = "🏆"
    elif position == "durchschnitt":
        severity = "info"
        emoji = "📊"
    else:
        severity = "opportunity"
        emoji = "📈"

    body = f"""<p>{emoji} Sie liegen mit einem Gesamt-Score von <strong>{current_score:.0f}/100</strong>
    {position_text} Ihres Segments ({html.escape(segment_label)}).</p>
    <p class="insight-detail">Durchschnitt im Segment: {avg_score:.0f}/100
    (basierend auf {report_count} vergleichbaren Unternehmen)</p>"""

    return InsightCard(
        title="Ihre Position im Marktsegment",
        severity=severity,
        body_html=body,
        category="position",
        priority=1,
    )


def _build_score_cards(
    report_sections: Dict[str, Any],
    segment_stats: Any,
) -> List[InsightCard]:
    """Build score comparison cards for dimensions."""
    cards = []

    # Map section keys to score dimensions
    score_mapping = [
        ("governance", "REIFEGRAD_GOVERNANCE", "Governance", segment_stats.avg_score_governance),
        ("security", "REIFEGRAD_SECURITY", "Sicherheit", segment_stats.avg_score_security),
        ("value", "REIFEGRAD_VALUE", "Wertschöpfung", segment_stats.avg_score_value),
        ("enablement", "REIFEGRAD_ENABLEMENT", "Enablement", segment_stats.avg_score_enablement),
    ]

    for dim_key, section_key, label, avg_score in score_mapping:
        if avg_score <= 0:
            continue

        # Get current score from report
        current_score = 0.0
        if section_key in report_sections:
            try:
                current_score = float(report_sections[section_key])
            except (ValueError, TypeError):
                continue

        if current_score <= 0:
            continue

        # Calculate difference
        diff = current_score - avg_score
        diff_pct = (diff / avg_score) * 100 if avg_score > 0 else 0

        # Only create card if significant difference
        if abs(diff_pct) < 10:
            continue

        if diff_pct > 20:
            severity = "highlight"
            icon = "✅"
            comparison_text = f"{abs(diff_pct):.0f}% über dem Durchschnitt"
        elif diff_pct > 0:
            severity = "info"
            icon = "📊"
            comparison_text = f"{abs(diff_pct):.0f}% über dem Durchschnitt"
        elif diff_pct > -20:
            severity = "opportunity"
            icon = "📈"
            comparison_text = f"{abs(diff_pct):.0f}% unter dem Durchschnitt"
        else:
            severity = "risk"
            icon = "⚠️"
            comparison_text = f"{abs(diff_pct):.0f}% unter dem Durchschnitt"

        body = f"""<p>{icon} Im Bereich <strong>{label}</strong> liegen Sie mit {current_score:.0f}/100
        {comparison_text} Ihres Segments (Ø {avg_score:.0f}/100).</p>"""

        cards.append(InsightCard(
            title=f"{label}: {comparison_text}",
            severity=severity,
            body_html=body,
            category="scores",
            priority=3 if severity in ("highlight", "risk") else 5,
        ))

    return cards


def _build_use_case_card(
    report_sections: Dict[str, Any],
    segment_stats: Any,
) -> Optional[InsightCard]:
    """Build use case potential card."""
    # Try to extract use case count from report
    current_use_cases = 0

    # Check various possible sources for use case count
    if "USE_CASES_COUNT" in report_sections:
        try:
            current_use_cases = int(report_sections["USE_CASES_COUNT"])
        except (ValueError, TypeError):
            pass

    if current_use_cases == 0 and "HAUPTLEISTUNG_HTML" in report_sections:
        # Estimate from hauptleistung content
        hauptleistung = report_sections.get("HAUPTLEISTUNG_HTML", "")
        # Simple heuristic: count bullet points or numbered items
        current_use_cases = hauptleistung.count("<li>") or hauptleistung.count("•") or 1

    # Average use cases in segment (estimated from scores)
    avg_use_cases = 3 if segment_stats.avg_score_value > 60 else 2

    if current_use_cases <= 0:
        return None

    diff = avg_use_cases - current_use_cases

    if diff > 1:
        severity = "opportunity"
        body = f"""<p>📈 Vergleichbare Unternehmen in Ihrem Segment haben im Durchschnitt
        <strong>{avg_use_cases}–{avg_use_cases+1} produktive KI-Use-Cases</strong> etabliert –
        Sie stehen aktuell bei <strong>{current_use_cases}–{current_use_cases+1}</strong>.</p>
        <p class="insight-detail">Hier liegt zusätzlicher Hebel für Ihre KI-Strategie.</p>"""

        return InsightCard(
            title="Potenzial im Bereich KI-Use-Cases",
            severity=severity,
            body_html=body,
            category="use_cases",
            priority=2,
        )
    elif diff < -1:
        severity = "highlight"
        body = f"""<p>🌟 Mit <strong>{current_use_cases}–{current_use_cases+1} produktiven KI-Use-Cases</strong>
        liegen Sie deutlich über dem Segment-Durchschnitt von {avg_use_cases}–{avg_use_cases+1}.</p>
        <p class="insight-detail">Sie gehören zu den KI-Vorreitern in Ihrem Segment.</p>"""

        return InsightCard(
            title="KI-Vorreiter in Ihrem Segment",
            severity=severity,
            body_html=body,
            category="use_cases",
            priority=2,
        )

    return None


def _build_roi_card(
    report_sections: Dict[str, Any],
    segment_stats: Any,
) -> Optional[InsightCard]:
    """Build ROI comparison card."""
    avg_roi = segment_stats.avg_roi_percent
    avg_payback = segment_stats.avg_payback_months

    if avg_roi <= 0 and avg_payback <= 0:
        return None

    # Get current ROI from report if available
    current_roi = 0.0
    if "BC_ROI_PERCENT" in report_sections:
        try:
            current_roi = float(report_sections["BC_ROI_PERCENT"])
        except (ValueError, TypeError):
            pass

    if avg_roi > 0:
        roi_text = f"{avg_roi:.0f}%"
        if current_roi > 0:
            if current_roi > avg_roi * 1.1:
                severity = "highlight"
                comparison = f"Ihr erwarteter ROI von {current_roi:.0f}% liegt über dem Segment-Durchschnitt."
            elif current_roi < avg_roi * 0.9:
                severity = "opportunity"
                comparison = f"Ihr erwarteter ROI von {current_roi:.0f}% liegt unter dem Segment-Durchschnitt."
            else:
                severity = "info"
                comparison = f"Ihr erwarteter ROI von {current_roi:.0f}% entspricht dem Segment-Durchschnitt."
        else:
            severity = "info"
            comparison = ""

        payback_text = ""
        if avg_payback > 0:
            payback_text = f" bei einer durchschnittlichen Amortisationszeit von {avg_payback:.0f} Monaten"

        body = f"""<p>💰 In Ihrem Segment erreichen vergleichbare Unternehmen eine
        <strong>ROI-Spanne von {int(avg_roi*0.8)}–{int(avg_roi*1.2)}%</strong> im ersten Jahr{payback_text}.</p>
        <p class="insight-detail">{comparison}</p>"""

        return InsightCard(
            title="ROI-Benchmark Ihres Segments",
            severity=severity,
            body_html=body,
            category="roi",
            priority=2,
        )

    return None


def _build_warning_card(
    report_sections: Dict[str, Any],
    segment_stats: Any,
) -> Optional[InsightCard]:
    """Build warning/risk comparison card."""
    top_warnings = segment_stats.top_warning_types

    if not top_warnings:
        return None

    # Get most common warning in segment
    most_common = top_warnings[0] if top_warnings else ("unknown", 0)
    warning_type, count = most_common

    if count < 3:
        return None

    # Map warning types to human-readable descriptions
    warning_descriptions = {
        "min-word": "unzureichende Detailtiefe in Abschnitten",
        "redundancy": "Redundanzen zwischen Abschnitten",
        "persona-leak": "inkonsistente Persona-Formulierungen",
        "placeholder": "fehlende Daten in Platzhaltern",
        "fallback": "eingeschränkte Research-Abdeckung",
    }

    description = warning_descriptions.get(warning_type, warning_type)

    body = f"""<p>📋 Die häufigste Herausforderung in Ihrem Segment ist
    <strong>{description}</strong>.</p>
    <p class="insight-detail">Achten Sie besonders auf vollständige und konsistente Angaben,
    um optimale Ergebnisse zu erzielen.</p>"""

    return InsightCard(
        title="Typische Herausforderungen im Segment",
        severity="info",
        body_html=body,
        category="warnings",
        priority=4,
    )


# =============================================================================
# HTML GENERATORS
# =============================================================================

def _build_summary_html(cards: List[InsightCard], segment_label: str) -> str:
    """Build summary HTML from cards."""
    if not cards:
        return "<p>Für Ihr Segment liegen noch nicht genügend Vergleichsdaten vor.</p>"

    # Find position card
    position_card = next((c for c in cards if c.category == "position"), None)
    opportunity_cards = [c for c in cards if c.severity == "opportunity"]
    highlight_cards = [c for c in cards if c.severity == "highlight"]

    paragraphs = []

    # Opening statement
    paragraphs.append(
        f"<p>Basierend auf dem Vergleich mit <strong>{segment_label}</strong> "
        f"haben wir {len(cards)} relevante Erkenntnisse für Ihr Unternehmen identifiziert.</p>"
    )

    # Position summary
    if position_card:
        paragraphs.append(position_card.body_html)

    # Opportunities summary
    if opportunity_cards:
        opp_count = len(opportunity_cards)
        paragraphs.append(
            f"<p>Wir haben <strong>{opp_count} Verbesserungspotenzial{'e' if opp_count > 1 else ''}</strong> "
            f"identifiziert, in denen Sie Ihr Segment übertreffen können.</p>"
        )

    # Highlights summary
    if highlight_cards:
        highlight_count = len(highlight_cards)
        paragraphs.append(
            f"<p>In <strong>{highlight_count} Bereich{'en' if highlight_count > 1 else ''}</strong> "
            f"liegen Sie bereits über dem Durchschnitt Ihres Segments.</p>"
        )

    return "\n".join(paragraphs)


def _build_cards_html(cards: List[InsightCard]) -> str:
    """Build cards HTML block."""
    if not cards:
        return ""

    html_parts = ['<div class="insight-cards">']

    for card in cards:
        severity_class = f"insight-card--{card.severity}"
        html_parts.append(f'''
        <div class="insight-card {severity_class}">
            <h4 class="insight-card__title">{html.escape(card.title)}</h4>
            <div class="insight-card__body">
                {card.body_html}
            </div>
        </div>
        ''')

    html_parts.append('</div>')

    return "\n".join(html_parts)


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def inject_insights_into_sections(
    sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Inject insight sections into report sections.

    Args:
        sections: Report sections dictionary
        profile: Profile data (optional)

    Returns:
        Updated sections with INSIGHTS_SUMMARY_HTML and INSIGHT_CARDS_HTML
    """
    if not INSIGHTS_ENGINE_ENABLED:
        return sections

    try:
        insights = build_report_insights(sections, profile)

        sections["INSIGHTS_SUMMARY_HTML"] = insights.summary_html
        sections["INSIGHT_CARDS_HTML"] = insights.cards_html

        if insights.has_sufficient_data:
            log.info(f"✅ Injected {len(insights.cards)} insight cards into report")
        else:
            log.debug("No sufficient segment data for insights")

    except Exception as e:
        log.error(f"Failed to build insights: {e}")
        sections["INSIGHTS_SUMMARY_HTML"] = ""
        sections["INSIGHT_CARDS_HTML"] = ""

    return sections


def get_insight_cards_json(
    report_sections: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Get insight cards as JSON for API responses.

    Args:
        report_sections: Report sections dictionary
        profile: Profile data (optional)

    Returns:
        List of card dictionaries
    """
    insights = build_report_insights(report_sections, profile)
    return [card.to_dict() for card in insights.cards]
