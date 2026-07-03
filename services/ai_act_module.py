# -*- coding: utf-8 -*-
"""
AI Act Compliance Module - Sprint G7/G8

Size-aware, branch-aware, language-aware AI Act risk assessment and compliance generation.

Version: 1.1.0 (Sprint G8 - Cross-Integration & Harmonization)

This module provides:
- Risk level determination (none/minimal/limited/high-risk)
- Duty matrix HTML generation
- Non-compliance alerts
- Data gaps identification
- Recommended next steps
- Use case risk tagging
- Cross-section injection (G8.1)
- Harmonization engine (G8.2)
- Extended persona guards (G8.3)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

VALID_RISK_LEVELS = {"none", "minimal", "limited", "high-risk"}

# High-risk branches per AI Act Annex III
HIGH_RISK_BRANCHES = {"gesundheit", "medizin", "healthcare", "medical"}
LIMITED_RISK_BRANCHES = {"recht", "legal", "law"}
REGULATED_BRANCHES = {"finanzen", "versicherung", "finance", "insurance", "banking"}

# Use case keywords that indicate high-risk
HIGH_RISK_USECASES_KEYWORDS = {
    "scoring", "kredit", "credit", "entscheidung", "decision",
    "bewertung", "assessment", "rating", "profiling", "biometric",
    "recruitment", "hiring", "personalauswahl", "bewerberauswahl"
}

# Use case keywords that indicate limited risk
# KIS-1234: um Art.-50-relevante Anwendungsfälle erweitert (Chatbots,
# personalisierte KI-Interaktion, KI-generierte Inhalte) — Transparenz-
# pflichten ab 02.08.2026 gelten unabhängig von der Betriebsgröße.
LIMITED_RISK_USECASES_KEYWORDS = {
    "chatbot", "chatbots", "kundenservice", "customer service", "kommunikation",
    "content", "marketing", "empfehlung", "recommendation",
    "personalisierung", "personalization", "generierung", "generation",
    "assistent", "assistant", "avatar",
}

# Solo-forbidden terms (for persona clean checks)
SOLO_FORBIDDEN_TERMS = [
    "team", "teams", "abteilung", "mitarbeiter", "kollegen",
    "fachbereich", "projektteam", "department", "employees", "colleagues"
]

# Team/KMU forbidden terms for Solo reports
TEAM_KMU_TERMS_FOR_SOLO = [
    "abteilungsleiter", "projektleiter", "compliance-officer",
    "department head", "project manager", "governance board"
]


# =============================================================================
# KIS-1235: AI-Act-Fristen-Box (deterministisch, datumsabhängig)
# =============================================================================
# Der 1235-Lauf zeigte: Das Kapitel "AI Act Kompakt" nannte KEINE einzige
# Frist, obwohl Art. 50 (Transparenzpflichten) zum Reportdatum nur 4 Wochen
# entfernt war. Diese Box macht den nächsten Stichtag zum Handlungsanker.

AI_ACT_DEADLINES = [
    ("2025-02-02", "Verbotene Praktiken & KI-Kompetenzpflicht (Art. 4, 5)"),
    ("2025-08-02", "Pflichten für GPAI-Modelle (Kap. V)"),
    ("2026-08-02", "Transparenzpflichten (Art. 50) & Hochrisiko-Pflichten Anhang III"),
    ("2027-08-02", "Hochrisiko-KI in regulierten Produkten (Anhang I)"),
]


def build_ai_act_deadline_box(risk_level: str = "", today: Optional[Any] = None) -> str:
    """Countdown-Box mit dem nächsten AI-Act-Stichtag (HTML)."""
    from datetime import date as _date
    d = today or _date.today()
    upcoming = []
    for iso, label in AI_ACT_DEADLINES:
        y, m, dd = (int(x) for x in iso.split("-"))
        deadline = _date(y, m, dd)
        if deadline >= d:
            upcoming.append((deadline, label))
    if not upcoming:
        return ""
    next_deadline, next_label = upcoming[0]
    days = (next_deadline - d).days
    date_fmt = next_deadline.strftime("%d.%m.%Y")
    urgency = ""
    if days <= 90:
        urgency = f" — <strong>in {days} Tagen</strong>"
    relevance = ""
    if (risk_level or "").strip().lower() in ("limited", "begrenzt") and "Art. 50" in next_label:
        relevance = (
            " Für Ihre Einstufung (begrenztes Risiko) ist genau dieser Stichtag "
            "maßgeblich: KI-Chatbots müssen sich als KI zu erkennen geben, "
            "KI-generierte Inhalte müssen gekennzeichnet sein."
        )
    return (
        '<div class="callout" style="border-left:4px solid #b45309;background:#fffbeb;'
        'padding:12px 16px;margin:12px 0;break-inside:avoid;">'
        f'<strong>Nächster Stichtag: {date_fmt}</strong>{urgency} · {next_label}.'
        f'{relevance}'
        '</div>'
    )


# =============================================================================
# RISK LEVEL DETERMINATION
# =============================================================================

def determine_risk_level(
    branche: str,
    size: str,
    usecases: List[str],
    automatisierung_prozent: int = 0
) -> str:
    """
    Determine AI Act risk level based on branch, size, and use cases.

    Returns: "none" | "minimal" | "limited" | "high-risk"
    """
    branche_lower = branche.lower().strip()
    size_lower = size.lower().strip()
    usecases_text = " ".join(usecases).lower()

    # Rule 1: Finance/Insurance with scoring/decision → high-risk
    if any(b in branche_lower for b in ["finanz", "versicher", "finance", "insurance", "bank"]):
        if any(kw in usecases_text for kw in HIGH_RISK_USECASES_KEYWORDS):
            return "high-risk"
        return "limited"

    # Rule 2: Healthcare/Medical → high-risk
    if any(b in branche_lower for b in ["gesundheit", "medizin", "health", "medical", "pharma"]):
        return "high-risk"

    # Rule 3: Legal → limited
    if any(b in branche_lower for b in ["recht", "legal", "law", "anwalt", "lawyer"]):
        return "limited"

    # Rule 4: HR/Recruitment with automated decisions → high-risk
    if any(b in branche_lower for b in ["hr", "personal", "human resources", "recruiting"]):
        if any(kw in usecases_text for kw in ["auswahl", "selection", "screening", "bewertung"]):
            return "high-risk"
        return "limited"

    # Rule 4b (KIS-1234): Kundeninteraktion / KI-generierte Inhalte → limited.
    # Art. 50 EU AI Act (Transparenzpflichten ab 02.08.2026) greift bei
    # Chatbots, Personalisierung und KI-generierten Inhalten UNABHÄNGIG von
    # der Betriebsgröße. Die Pauschal-Regel "Solo → minimal" stufte einen
    # Anbieter mit Kunden-Chatbots als "minimal" ein (Lauf KIS-1234) — der
    # eigene Strategiebericht widersprach dem korrekt mit "begrenzt".
    if any(kw in usecases_text for kw in LIMITED_RISK_USECASES_KEYWORDS):
        return "limited"

    # Rule 5: Solo with low automation → minimal
    from services.company_size_normalizer import get_segment
    _segment = get_segment(size)
    if _segment == "solo":
        return "minimal"

    # Rule 6: Team with low automation (<30%) → minimal
    if _segment == "team" and automatisierung_prozent < 30:
        return "minimal"

    # Default: limited
    return "limited"


def generate_risk_reasoning(
    risk_level: str,
    branche: str,
    size: str,
    usecases: List[str],
    lang: str = "de"
) -> str:
    """
    Generate 80-120 word reasoning for the risk level determination.
    Size-aware, no persona leaks.
    """
    from services.company_size_normalizer import get_segment
    _seg = get_segment(size)
    is_solo = _seg == "solo"
    is_team = _seg == "team"

    usecases_str = ", ".join(usecases[:3]) if usecases else "allgemeine KI-Nutzung"

    if lang == "en":
        return _generate_risk_reasoning_en(risk_level, branche, size, usecases_str, is_solo, is_team)
    else:
        return _generate_risk_reasoning_de(risk_level, branche, size, usecases_str, is_solo, is_team)


def _generate_risk_reasoning_de(
    risk_level: str,
    branche: str,
    size: str,
    usecases_str: str,
    is_solo: bool,
    is_team: bool
) -> str:
    """German risk reasoning generation."""

    if risk_level == "high-risk":
        if is_solo:
            return f"""Die Einstufung als Hochrisiko-System ergibt sich aus der Branche {branche} und den
geplanten Anwendungsfällen ({usecases_str}). Gemäß EU AI Act Anhang III fallen automatisierte
Entscheidungssysteme in regulierten Branchen unter strenge Anforderungen. Auch bei Ihrer
Unternehmensgröße gelten diese Pflichten vollumfänglich, sobald entsprechende Systeme eingesetzt
werden. Empfohlen wird eine frühzeitige Konformitätsprüfung, Dokumentation der Datengrundlagen
und Definition klarer Human-Oversight-Prozesse. Die Anforderungen umfassen Risikoanalyse,
Qualitätsmanagement und Post-Market-Monitoring."""
        elif is_team:
            return f"""Die Einstufung als Hochrisiko-System ergibt sich aus der Branche {branche} und den
geplanten Anwendungsfällen ({usecases_str}). Gemäß EU AI Act Anhang III fallen automatisierte
Entscheidungssysteme in regulierten Branchen unter strenge Anforderungen. Für Ihr Unternehmen
bedeutet dies die Notwendigkeit einer strukturierten Compliance-Strategie mit klaren
Verantwortlichkeiten. Empfohlen wird die Benennung eines KI-Verantwortlichen, Dokumentation
aller Datenflüsse und Implementierung von Review-Prozessen. Die Anforderungen umfassen
Risikoanalyse, Qualitätsmanagement und Post-Market-Monitoring."""
        else:
            return f"""Die Einstufung als Hochrisiko-System ergibt sich aus der Branche {branche} und den
geplanten Anwendungsfällen ({usecases_str}). Gemäß EU AI Act Anhang III fallen automatisierte
Entscheidungssysteme in regulierten Branchen unter strenge Anforderungen. Für Ihr Unternehmen
ist eine umfassende Compliance-Struktur mit definierten Rollen und Prozessen erforderlich.
Dies umfasst ein Qualitätsmanagementsystem, dokumentierte Risikoanalysen, klare
Human-Oversight-Konzepte und Post-Market-Monitoring. Die Benennung eines Compliance-Beauftragten
und regelmäßige Audits werden empfohlen."""

    elif risk_level == "limited":
        if is_solo:
            return f"""Die Einstufung als System mit begrenztem Risiko basiert auf der Branche {branche}
und Ihren Anwendungsfällen ({usecases_str}). Der EU AI Act sieht für diese Kategorie primär
Transparenzpflichten vor. Für Sie bedeutet dies: Dokumentation der eingesetzten KI-Systeme,
klare Kennzeichnung KI-generierter Inhalte und nachvollziehbare Qualitätsprüfung. Formale
Zertifizierungen sind nicht erforderlich, aber eine strukturierte Dokumentation Ihrer
KI-Nutzung wird empfohlen. Dies schafft Vertrauen und erleichtert eventuelle spätere
Erweiterungen."""
        elif is_team:
            return f"""Die Einstufung als System mit begrenztem Risiko basiert auf der Branche {branche}
und den Anwendungsfällen ({usecases_str}). Der EU AI Act sieht für diese Kategorie primär
Transparenzpflichten vor. Für Ihr Unternehmen bedeutet dies: gemeinsame Dokumentation der
eingesetzten KI-Systeme, klare Kennzeichnung KI-generierter Inhalte und definierte
Qualitätsprüfprozesse. Die Benennung eines KI-Verantwortlichen und einfache Logging-Mechanismen
werden empfohlen. Dies schafft eine solide Basis für verantwortungsvolle KI-Nutzung."""
        else:
            return f"""Die Einstufung als System mit begrenztem Risiko basiert auf der Branche {branche}
und den Anwendungsfällen ({usecases_str}). Der EU AI Act sieht für diese Kategorie primär
Transparenzpflichten vor. Für Ihr Unternehmen empfiehlt sich eine strukturierte
Dokumentation aller KI-Systeme, klare Prozesse für Kennzeichnung und Qualitätsprüfung
sowie definierte Verantwortlichkeiten. Ein einfaches Governance-Framework mit Logging
und regelmäßigen Reviews schafft die Basis für Compliance und ermöglicht Erweiterung."""

    else:  # minimal or none
        if is_solo:
            return f"""Die Einstufung als minimales Risiko basiert auf der Branche {branche}, Ihrer
Unternehmensgröße und den Anwendungsfällen ({usecases_str}). Der EU AI Act sieht für
diese Kategorie keine spezifischen Pflichten vor. Dennoch empfehlen sich Best Practices:
Dokumentation der genutzten Tools, Prüfung wichtiger Ergebnisse vor Verwendung und
Transparenz gegenüber Kunden. Diese Maßnahmen sind freiwillig, stärken aber das
Vertrauen und bereiten auf eventuelle künftige Anforderungen vor."""
        elif is_team:
            return f"""Die Einstufung als minimales Risiko basiert auf der Branche {branche}, Ihrer
Unternehmensgröße und den Anwendungsfällen ({usecases_str}). Der EU AI Act sieht für
diese Kategorie keine spezifischen Pflichten vor. Dennoch empfehlen sich Best Practices
für Ihr Unternehmen: gemeinsame Dokumentation der genutzten Tools, einfache Qualitätsprüfung
und Transparenz. Die Etablierung grundlegender Richtlinien für die KI-Nutzung ist
sinnvoll und bereitet auf eventuelle Erweiterungen vor."""
        else:
            return f"""Die Einstufung als minimales Risiko basiert auf der Branche {branche} und den
Anwendungsfällen ({usecases_str}). Der EU AI Act sieht für diese Kategorie keine
spezifischen Pflichten vor. Dennoch empfiehlt sich für Ihr Unternehmen die Etablierung
freiwilliger Best Practices: Dokumentation der KI-Systeme, einfache Governance-Richtlinien
und Qualitätsprüfprozesse. Diese Maßnahmen stärken das Vertrauen und schaffen eine
Grundlage für verantwortungsvolle Erweiterung."""


def _generate_risk_reasoning_en(
    risk_level: str,
    branche: str,
    size: str,
    usecases_str: str,
    is_solo: bool,
    is_team: bool
) -> str:
    """English risk reasoning generation."""

    if risk_level == "high-risk":
        if is_solo:
            return f"""The high-risk classification results from the {branche} industry and planned
use cases ({usecases_str}). According to EU AI Act Annex III, automated decision-making
systems in regulated industries fall under strict requirements. These obligations apply
fully regardless of business size when such systems are deployed. Early conformity
assessment, documentation of data foundations, and clear human oversight processes are
recommended. Requirements include risk analysis, quality management, and post-market
monitoring."""
        elif is_team:
            return f"""The high-risk classification results from the {branche} industry and planned
use cases ({usecases_str}). According to EU AI Act Annex III, automated decision-making
systems in regulated industries fall under strict requirements. For your organization,
this means establishing a structured compliance strategy with clear responsibilities.
Designating an AI lead, documenting all data flows, and implementing review processes
is recommended. Requirements include risk analysis, quality management, and post-market
monitoring."""
        else:
            return f"""The high-risk classification results from the {branche} industry and planned
use cases ({usecases_str}). According to EU AI Act Annex III, automated decision-making
systems in regulated industries fall under strict requirements. Your organization requires
a comprehensive compliance structure with defined roles and processes. This includes a
quality management system, documented risk analyses, clear human oversight concepts,
and post-market monitoring. Designating a compliance officer and regular audits are
recommended."""

    elif risk_level == "limited":
        if is_solo:
            return f"""The limited risk classification is based on the {branche} industry and your
use cases ({usecases_str}). The EU AI Act primarily requires transparency obligations
for this category. For you, this means: documenting AI systems in use, clearly labeling
AI-generated content, and maintaining traceable quality checks. Formal certifications
are not required, but structured documentation of your AI usage is recommended. This
builds trust and facilitates potential future expansions."""
        elif is_team:
            return f"""The limited risk classification is based on the {branche} industry and use
cases ({usecases_str}). The EU AI Act primarily requires transparency obligations for
this category. For your organization, this means: shared documentation of AI systems,
clear labeling of AI-generated content, and defined quality review processes. Designating
an AI lead and implementing simple logging mechanisms is recommended. This creates a
solid foundation for responsible AI use."""
        else:
            return f"""The limited risk classification is based on the {branche} industry and use
cases ({usecases_str}). The EU AI Act primarily requires transparency obligations for
this category. Your organization should establish structured documentation of all AI
systems, clear processes for labeling and quality review, and defined responsibilities.
A simple governance framework with logging and regular reviews creates the foundation
for compliance and enables scaling."""

    else:  # minimal or none
        if is_solo:
            return f"""The minimal risk classification is based on the {branche} industry, your
business size, and use cases ({usecases_str}). The EU AI Act does not mandate specific
requirements for this category. However, best practices are recommended: documenting
tools in use, reviewing important outputs before use, and transparency with clients.
These measures are voluntary but build trust and prepare for potential future
requirements."""
        elif is_team:
            return f"""The minimal risk classification is based on the {branche} industry, your
business size, and use cases ({usecases_str}). The EU AI Act does not mandate specific
requirements for this category. However, best practices for your organization are
recommended: shared documentation of tools, simple quality reviews, and transparency.
Establishing basic guidelines for AI usage is sensible and prepares for potential
expansions."""
        else:
            return f"""The minimal risk classification is based on the {branche} industry and use
cases ({usecases_str}). The EU AI Act does not mandate specific requirements for this
category. However, your organization should consider voluntary best practices:
documenting AI systems, simple governance guidelines, and quality review processes.
These measures build trust and create a foundation for responsible scaling."""


# =============================================================================
# DUTY MATRIX GENERATION
# =============================================================================

def generate_duty_matrix_html(
    risk_level: str,
    branche: str,
    size: str,
    lang: str = "de"
) -> str:
    """
    Generate HTML duty matrix table based on risk level.

    - none/minimal: 3-4 rows (best practices)
    - limited: 6-8 rows
    - high-risk: 8-12 rows
    """
    size_lower = size.lower()
    is_solo = "solo" in size_lower or "freiberuf" in size_lower

    if lang == "en":
        return _generate_duty_matrix_en(risk_level, branche, is_solo)
    else:
        return _generate_duty_matrix_de(risk_level, branche, is_solo)


def _generate_duty_matrix_de(risk_level: str, branche: str, is_solo: bool) -> str:
    """German duty matrix."""

    header = """<table class="table table-modern duty-matrix">
  <thead>
    <tr>
      <th>Pflicht / Best Practice</th>
      <th>Beschreibung</th>
      <th>Priorität</th>
    </tr>
  </thead>
  <tbody>"""

    footer = """  </tbody>
</table>"""

    if risk_level in ["none", "minimal"]:
        rows = [
            ("Dokumentation", "Übersicht der genutzten KI-Tools und deren Einsatzzweck", "Empfohlen"),
            ("Qualitätsprüfung", "Stichprobenartige Prüfung wichtiger KI-Ergebnisse", "Empfohlen"),
            ("Transparenz", "Kennzeichnung KI-generierter Inhalte gegenüber Kunden", "Empfohlen"),
        ]
        if not is_solo:
            rows.append(("Richtlinien", "Einfache Regeln für die KI-Nutzung im Unternehmen", "Empfohlen"))
        note = ('<p class="small muted">Für Ihre aktuelle Einstufung bestehen überwiegend '
                'keine spezifischen Pflichten aus dem EU AI Act. Wichtig: Die Transparenzpflichten '
                'zur Kennzeichnung KI-generierter Inhalte (Art. 50 EU AI Act) gelten ab dem '
                '2. August 2026 — prüfen Sie, ob Ihre Anwendungsfälle darunterfallen.</p>')

    elif risk_level == "limited":
        rows = [
            ("Transparenzpflicht", "Klare Kennzeichnung aller KI-generierten Inhalte", "Pflicht"),
            ("Dokumentation", "Vollständige Dokumentation aller KI-Systeme", "Pflicht"),
            ("Human Oversight", "Definierte Prozesse für menschliche Kontrolle", "Empfohlen"),
            ("Logging", "Protokollierung der KI-Nutzung und Entscheidungen", "Empfohlen"),
            ("Datenqualität", "Sicherstellung der Qualität von Trainingsdaten", "Empfohlen"),
            ("Monitoring", "Regelmäßige Überprüfung der KI-Systemleistung", "Empfohlen"),
        ]
        if not is_solo:
            rows.extend([
                ("Verantwortlichkeiten", "Klare Zuweisung von Rollen und Zuständigkeiten", "Empfohlen"),
                ("Schulung", "Grundlegende KI-Kompetenz für alle Beteiligten", "Empfohlen"),
            ])
        note = '<p class="small muted">Transparenzpflichten sind gesetzlich vorgeschrieben, weitere Maßnahmen werden empfohlen.</p>'

    else:  # high-risk
        rows = [
            ("Konformitätserklärung", "EU-Konformitätserklärung gemäß AI Act", "Pflicht"),
            ("Qualitätsmanagementsystem", "Dokumentiertes QMS für KI-Systeme", "Pflicht"),
            ("Risikoanalyse", "Umfassende Risikobewertung und -dokumentation", "Pflicht"),
            ("Human Oversight", "Definierte Prozesse für menschliche Kontrolle und Eingriff", "Pflicht"),
            ("Logging & Audit Trail", "Vollständige Protokollierung aller Entscheidungen", "Pflicht"),
            ("Daten-Governance", "Dokumentierte Prozesse für Datenqualität und -management", "Pflicht"),
            ("Post-Market Monitoring", "Kontinuierliche Überwachung im Betrieb", "Pflicht"),
            ("Incident Reporting", "Definierter Prozess für Vorfallsmeldungen", "Pflicht"),
        ]
        if not is_solo:
            rows.extend([
                ("Compliance-Beauftragter", "Benannte verantwortliche Person für AI Act Compliance", "Pflicht"),
                ("Regelmäßige Audits", "Interne und externe Überprüfungen", "Empfohlen"),
                ("Schulungsprogramm", "Systematische Schulung aller Beteiligten", "Empfohlen"),
                ("Dokumentenmanagement", "Zentrale Verwaltung aller Compliance-Dokumente", "Empfohlen"),
            ])
        note = '<p class="small muted">Alle als Pflicht markierten Maßnahmen sind gesetzlich vorgeschrieben.</p>'

    rows_html = "\n".join([
        f'    <tr><td>{pflicht}</td><td>{beschreibung}</td><td><span class="badge badge-{"danger" if prio == "Pflicht" else "info"}">{prio}</span></td></tr>'
        for pflicht, beschreibung, prio in rows
    ])

    return f"{header}\n{rows_html}\n{footer}\n{note}"


def _generate_duty_matrix_en(risk_level: str, branche: str, is_solo: bool) -> str:
    """English duty matrix."""

    header = """<table class="table table-modern duty-matrix">
  <thead>
    <tr>
      <th>Obligation / Best Practice</th>
      <th>Description</th>
      <th>Priority</th>
    </tr>
  </thead>
  <tbody>"""

    footer = """  </tbody>
</table>"""

    if risk_level in ["none", "minimal"]:
        rows = [
            ("Documentation", "Overview of AI tools in use and their purpose", "Recommended"),
            ("Quality Review", "Spot-check review of important AI outputs", "Recommended"),
            ("Transparency", "Label AI-generated content for clients", "Recommended"),
        ]
        if not is_solo:
            rows.append(("Guidelines", "Simple rules for AI usage in the organization", "Recommended"))
        note = ('<p class="small muted">For your current classification, most EU AI Act '
                'obligations do not apply. Note: the transparency obligations for labeling '
                'AI-generated content (Art. 50 EU AI Act) apply from 2 August 2026 — check '
                'whether your use cases fall under them.</p>')

    elif risk_level == "limited":
        rows = [
            ("Transparency Obligation", "Clear labeling of all AI-generated content", "Required"),
            ("Documentation", "Complete documentation of all AI systems", "Required"),
            ("Human Oversight", "Defined processes for human control", "Recommended"),
            ("Logging", "Logging of AI usage and decisions", "Recommended"),
            ("Data Quality", "Ensuring quality of training data", "Recommended"),
            ("Monitoring", "Regular review of AI system performance", "Recommended"),
        ]
        if not is_solo:
            rows.extend([
                ("Responsibilities", "Clear assignment of roles and responsibilities", "Recommended"),
                ("Training", "Basic AI competency for all stakeholders", "Recommended"),
            ])
        note = '<p class="small muted">Transparency obligations are legally required, additional measures are recommended.</p>'

    else:  # high-risk
        rows = [
            ("Conformity Declaration", "EU conformity declaration per AI Act", "Required"),
            ("Quality Management System", "Documented QMS for AI systems", "Required"),
            ("Risk Analysis", "Comprehensive risk assessment and documentation", "Required"),
            ("Human Oversight", "Defined processes for human control and intervention", "Required"),
            ("Logging & Audit Trail", "Complete logging of all decisions", "Required"),
            ("Data Governance", "Documented processes for data quality and management", "Required"),
            ("Post-Market Monitoring", "Continuous monitoring in operation", "Required"),
            ("Incident Reporting", "Defined process for incident reports", "Required"),
        ]
        if not is_solo:
            rows.extend([
                ("Compliance Officer", "Designated responsible person for AI Act compliance", "Required"),
                ("Regular Audits", "Internal and external reviews", "Recommended"),
                ("Training Program", "Systematic training for all stakeholders", "Recommended"),
                ("Document Management", "Central management of all compliance documents", "Recommended"),
            ])
        note = '<p class="small muted">All measures marked as Required are legally mandated.</p>'

    rows_html = "\n".join([
        f'    <tr><td>{duty}</td><td>{description}</td><td><span class="badge badge-{"danger" if prio == "Required" else "info"}">{prio}</span></td></tr>'
        for duty, description, prio in rows
    ])

    return f"{header}\n{rows_html}\n{footer}\n{note}"


# =============================================================================
# NON-COMPLIANCE ALERTS
# =============================================================================

def generate_noncompliance_alerts(
    risk_level: str,
    branche: str,
    size: str,
    lang: str = "de"
) -> List[str]:
    """
    Generate 3-8 non-compliance alert bullet points.
    """
    size_lower = size.lower()
    is_solo = "solo" in size_lower or "freiberuf" in size_lower

    if lang == "en":
        return _generate_alerts_en(risk_level, is_solo)
    else:
        return _generate_alerts_de(risk_level, is_solo)


def _generate_alerts_de(risk_level: str, is_solo: bool) -> List[str]:
    """German non-compliance alerts."""

    if risk_level in ["none", "minimal"]:
        alerts = [
            "Keine formale Risikoanalyse vorhanden",
            "Keine Dokumentation der genutzten KI-Modelle",
            "Fehlende Qualitätsprüfung vor Nutzung von KI-Ergebnissen",
        ]
        if not is_solo:
            alerts.append("Keine definierten Verantwortlichkeiten für KI-Nutzung")

    elif risk_level == "limited":
        alerts = [
            "Transparenzpflicht nicht vollständig umgesetzt",
            "Human Oversight unzureichend definiert",
            "Datenqualität nicht dokumentiert",
            "Keine Versionierung von Modellen",
            "Fehlende Logging-Mechanismen für KI-Entscheidungen",
        ]
        if not is_solo:
            alerts.extend([
                "Keine klaren Verantwortlichkeiten für KI-Compliance",
                "Fehlende Schulungsmaßnahmen für KI-Nutzer",
            ])

    else:  # high-risk
        alerts = [
            "Fehlende EU-Konformitätserklärung – gesetzlich zwingend erforderlich",
            "Kein dokumentiertes Qualitätsmanagementsystem vorhanden",
            "Risikoanalyse nicht vollständig oder nicht aktuell",
            "Human Oversight nicht ausreichend implementiert",
            "Post-Market Monitoring nicht eingerichtet",
            "Keine definierte Incident-Meldestruktur",
            "Audit Trail / Logging unvollständig",
        ]
        if not is_solo:
            alerts.extend([
                "Kein Compliance-Beauftragter benannt",
            ])

    return alerts


def _generate_alerts_en(risk_level: str, is_solo: bool) -> List[str]:
    """English non-compliance alerts."""

    if risk_level in ["none", "minimal"]:
        alerts = [
            "No formal risk analysis available",
            "No documentation of AI models in use",
            "Missing quality review before using AI outputs",
        ]
        if not is_solo:
            alerts.append("No defined responsibilities for AI usage")

    elif risk_level == "limited":
        alerts = [
            "Transparency obligation not fully implemented",
            "Human oversight insufficiently defined",
            "Data quality not documented",
            "No model versioning",
            "Missing logging mechanisms for AI decisions",
        ]
        if not is_solo:
            alerts.extend([
                "No clear responsibilities for AI compliance",
                "Missing training measures for AI users",
            ])

    else:  # high-risk
        alerts = [
            "Missing EU conformity declaration – legally required",
            "No documented quality management system",
            "Risk analysis incomplete or outdated",
            "Human oversight not sufficiently implemented",
            "Post-market monitoring not established",
            "No defined incident reporting structure",
            "Audit trail / logging incomplete",
        ]
        if not is_solo:
            alerts.append("No compliance officer designated")

    return alerts


# =============================================================================
# DATA GAPS
# =============================================================================

def generate_data_gaps(
    risk_level: str,
    branche: str,
    size: str,
    lang: str = "de"
) -> List[str]:
    """
    Generate 2-6 data gap bullet points.
    """
    size_lower = size.lower()
    is_solo = "solo" in size_lower or "freiberuf" in size_lower
    is_team = "team" in size_lower or "klein" in size_lower

    if lang == "en":
        return _generate_gaps_en(risk_level, is_solo, is_team)
    else:
        return _generate_gaps_de(risk_level, is_solo, is_team)


def _generate_gaps_de(risk_level: str, is_solo: bool, is_team: bool) -> List[str]:
    """German data gaps."""

    if is_solo:
        gaps = [
            "Keine definierte Datenklassifikation",
            "Unklare Trennung zwischen Test- und Produktivdaten",
        ]
        if risk_level not in ["none", "minimal"]:
            gaps.append("Fehlende Dokumentation der Datenherkunft")

    elif is_team:
        gaps = [
            "Keine dokumentierten Datenqualitätsmetriken",
            "Fehlende Prozessbeschreibung der Datenflüsse",
            "Keine definierten Verantwortlichkeiten für Datenkategorien",
        ]
        if risk_level not in ["none", "minimal"]:
            gaps.extend([
                "Fehlende Versionierung von Trainingsdaten",
                "Keine dokumentierte Datenlöschstrategie",
            ])

    else:  # KMU
        gaps = [
            "Keine dokumentierten Datenqualitätsmetriken",
            "Fehlende Prozessbeschreibung der Datenflüsse zwischen Fachbereichen",
            "Keine definierten Data Owner für sensible Kategorien",
            "Fehlende Datenherkunftsdokumentation (Data Lineage)",
        ]
        if risk_level not in ["none", "minimal"]:
            gaps.extend([
                "Keine systematische Datenvalidierung vor KI-Training",
                "Fehlende Archivierungs- und Löschkonzepte",
            ])

    return gaps


def _generate_gaps_en(risk_level: str, is_solo: bool, is_team: bool) -> List[str]:
    """English data gaps."""

    if is_solo:
        gaps = [
            "No defined data classification",
            "Unclear separation between test and production data",
        ]
        if risk_level not in ["none", "minimal"]:
            gaps.append("Missing documentation of data origin")

    elif is_team:
        gaps = [
            "No documented data quality metrics",
            "Missing process description for data flows",
            "No defined responsibilities for data categories",
        ]
        if risk_level not in ["none", "minimal"]:
            gaps.extend([
                "Missing versioning of training data",
                "No documented data deletion strategy",
            ])

    else:  # SME
        gaps = [
            "No documented data quality metrics",
            "Missing process description for data flows between departments",
            "No defined data owners for sensitive categories",
            "Missing data provenance documentation (data lineage)",
        ]
        if risk_level not in ["none", "minimal"]:
            gaps.extend([
                "No systematic data validation before AI training",
                "Missing archival and deletion concepts",
            ])

    return gaps


# =============================================================================
# RECOMMENDED NEXT STEPS
# =============================================================================

def generate_next_steps_html(
    risk_level: str,
    branche: str,
    size: str,
    lang: str = "de"
) -> str:
    """
    Generate HTML list with 3-5 recommended next steps.
    """
    size_lower = size.lower()
    is_solo = "solo" in size_lower or "freiberuf" in size_lower

    if lang == "en":
        return _generate_next_steps_en(risk_level, is_solo)
    else:
        return _generate_next_steps_de(risk_level, is_solo)


def _generate_next_steps_de(risk_level: str, is_solo: bool) -> str:
    """German next steps."""

    if risk_level in ["none", "minimal"]:
        if is_solo:
            steps = [
                ("Woche 1–2", "KI-Tool-Dokumentation", "Erstellen Sie eine einfache Übersicht der genutzten KI-Tools und deren Einsatzzweck."),
                ("Woche 2–3", "Qualitätsprüfung", "Definieren Sie 3-5 Prüfpunkte für wichtige KI-Ergebnisse."),
                ("Woche 3–4", "Transparenz", "Legen Sie fest, wie KI-generierte Inhalte gegenüber Kunden gekennzeichnet werden."),
            ]
        else:
            steps = [
                ("Woche 1–2", "KI-Inventar erstellen", "Dokumentieren Sie alle genutzten KI-Tools und deren Einsatzbereiche."),
                ("Woche 2–3", "Richtlinien definieren", "Erstellen Sie einfache Regeln für die KI-Nutzung."),
                ("Woche 3–4", "Verantwortlichkeiten klären", "Benennen Sie einen KI-Verantwortlichen."),
                ("Woche 4", "Qualitätsprüfung", "Definieren Sie Prüfprozesse für wichtige KI-Ergebnisse."),
            ]

    elif risk_level == "limited":
        if is_solo:
            steps = [
                ("Woche 1–2", "Dokumentation aufsetzen", "Erstellen Sie eine vollständige Dokumentation Ihrer KI-Systeme."),
                ("Woche 2–3", "Transparenz umsetzen", "Implementieren Sie klare Kennzeichnung für KI-generierte Inhalte."),
                ("Woche 3–4", "Human Oversight definieren", "Legen Sie fest, welche Ergebnisse vor Verwendung geprüft werden."),
                ("Woche 4–5", "Logging einrichten", "Implementieren Sie einfache Protokollierung der KI-Nutzung."),
            ]
        else:
            steps = [
                ("Woche 1–2", "KI-Verantwortlichen benennen", "Definieren Sie klare Verantwortlichkeiten für AI Act Compliance."),
                ("Woche 2–3", "Dokumentation aufsetzen", "Erstellen Sie vollständige Dokumentation aller KI-Systeme."),
                ("Woche 3–4", "Transparenzpflichten umsetzen", "Implementieren Sie Kennzeichnung und Logging."),
                ("Woche 4–6", "Human Oversight etablieren", "Definieren Sie Prüf- und Freigabeprozesse."),
                ("Woche 6–8", "Monitoring einrichten", "Etablieren Sie regelmäßige Reviews der KI-Nutzung."),
            ]

    else:  # high-risk
        if is_solo:
            steps = [
                ("Woche 1–2", "Risikoanalyse durchführen", "Erstellen Sie eine umfassende Risikobewertung Ihrer KI-Nutzung."),
                ("Woche 2–4", "Konformitätspflichten prüfen", "Identifizieren Sie alle relevanten AI Act Anforderungen."),
                ("Woche 4–6", "Human Oversight konzipieren", "Definieren Sie klare Prozesse für menschliche Kontrolle."),
                ("Woche 6–8", "Dokumentation vervollständigen", "Erstellen Sie alle erforderlichen Compliance-Dokumente."),
                ("Woche 8–10", "Externe Beratung einholen", "Konsultieren Sie einen Experten für AI Act Compliance."),
            ]
        else:
            steps = [
                ("Woche 1–2", "Compliance-Beauftragten benennen", "Definieren Sie eine verantwortliche Person für AI Act."),
                ("Woche 2–4", "Risikoanalyse durchführen", "Erstellen Sie umfassende Risikobewertungen für alle KI-Systeme."),
                ("Woche 4–6", "QMS aufsetzen", "Implementieren Sie ein dokumentiertes Qualitätsmanagementsystem."),
                ("Woche 6–8", "Human Oversight etablieren", "Definieren Sie Prozesse für Kontrolle und Eingriff."),
                ("Woche 8–12", "Post-Market Monitoring einrichten", "Etablieren Sie kontinuierliche Überwachung."),
            ]

    html = '<ol class="next-steps-list">\n'
    for zeitraum, titel, beschreibung in steps:
        html += f'  <li><strong>{titel}</strong> ({zeitraum})<br/>{beschreibung}</li>\n'
    html += '</ol>'

    return html


def _generate_next_steps_en(risk_level: str, is_solo: bool) -> str:
    """English next steps."""

    if risk_level in ["none", "minimal"]:
        if is_solo:
            steps = [
                ("Week 1–2", "AI Tool Documentation", "Create a simple overview of AI tools in use and their purpose."),
                ("Week 2–3", "Quality Review", "Define 3-5 checkpoints for important AI outputs."),
                ("Week 3–4", "Transparency", "Establish how AI-generated content is labeled for clients."),
            ]
        else:
            steps = [
                ("Week 1–2", "Create AI Inventory", "Document all AI tools in use and their application areas."),
                ("Week 2–3", "Define Guidelines", "Create simple rules for AI usage."),
                ("Week 3–4", "Clarify Responsibilities", "Designate an AI lead."),
                ("Week 4", "Quality Review", "Define review processes for important AI outputs."),
            ]

    elif risk_level == "limited":
        if is_solo:
            steps = [
                ("Week 1–2", "Set Up Documentation", "Create complete documentation of your AI systems."),
                ("Week 2–3", "Implement Transparency", "Implement clear labeling for AI-generated content."),
                ("Week 3–4", "Define Human Oversight", "Establish which outputs require review before use."),
                ("Week 4–5", "Set Up Logging", "Implement simple logging of AI usage."),
            ]
        else:
            steps = [
                ("Week 1–2", "Designate AI Lead", "Define clear responsibilities for AI Act compliance."),
                ("Week 2–3", "Set Up Documentation", "Create complete documentation of all AI systems."),
                ("Week 3–4", "Implement Transparency", "Implement labeling and logging."),
                ("Week 4–6", "Establish Human Oversight", "Define review and approval processes."),
                ("Week 6–8", "Set Up Monitoring", "Establish regular reviews of AI usage."),
            ]

    else:  # high-risk
        if is_solo:
            steps = [
                ("Week 1–2", "Conduct Risk Analysis", "Create a comprehensive risk assessment of your AI usage."),
                ("Week 2–4", "Review Conformity Requirements", "Identify all relevant AI Act requirements."),
                ("Week 4–6", "Design Human Oversight", "Define clear processes for human control."),
                ("Week 6–8", "Complete Documentation", "Create all required compliance documents."),
                ("Week 8–10", "Seek External Advice", "Consult an AI Act compliance expert."),
            ]
        else:
            steps = [
                ("Week 1–2", "Designate Compliance Officer", "Define a responsible person for AI Act."),
                ("Week 2–4", "Conduct Risk Analysis", "Create comprehensive risk assessments for all AI systems."),
                ("Week 4–6", "Set Up QMS", "Implement a documented quality management system."),
                ("Week 6–8", "Establish Human Oversight", "Define processes for control and intervention."),
                ("Week 8–12", "Set Up Post-Market Monitoring", "Establish continuous monitoring."),
            ]

    html = '<ol class="next-steps-list">\n'
    for timeframe, title, description in steps:
        html += f'  <li><strong>{title}</strong> ({timeframe})<br/>{description}</li>\n'
    html += '</ol>'

    return html


# =============================================================================
# USE CASE RISK TAGGING
# =============================================================================

def generate_usecase_risk_html(
    usecases: List[str],
    branche: str,
    size: str,
    lang: str = "de"
) -> str:
    """
    Generate HTML list of use cases with risk tags.
    """
    if not usecases:
        usecases = _get_default_usecases(branche, lang)

    tagged_usecases = []
    for usecase in usecases:
        risk_tag = _determine_usecase_risk(usecase, branche)
        tagged_usecases.append((usecase, risk_tag))

    if lang == "en":
        return _render_usecase_html_en(tagged_usecases)
    else:
        return _render_usecase_html_de(tagged_usecases)


def _determine_usecase_risk(usecase: str, branche: str) -> str:
    """Determine risk tag for a single use case."""
    usecase_lower = usecase.lower()
    branche_lower = branche.lower()

    # High-risk indicators
    if any(kw in usecase_lower for kw in HIGH_RISK_USECASES_KEYWORDS):
        return "high-risk"

    # Branch-specific high-risk
    if any(b in branche_lower for b in ["gesundheit", "health", "medical"]):
        if any(kw in usecase_lower for kw in ["diagnose", "diagnosis", "behandlung", "treatment"]):
            return "high-risk"

    if any(b in branche_lower for b in ["finanz", "finance", "bank"]):
        if any(kw in usecase_lower for kw in ["kredit", "credit", "risiko", "risk"]):
            return "high-risk"

    # Limited risk indicators
    if any(kw in usecase_lower for kw in LIMITED_RISK_USECASES_KEYWORDS):
        return "limited"

    # Default
    return "minimal"


def _get_default_usecases(branche: str, lang: str) -> List[str]:
    """Get default use cases based on branch."""
    branche_lower = branche.lower()

    if lang == "en":
        if "finanz" in branche_lower or "finance" in branche_lower:
            return ["Document Automation", "Customer Communication", "Report Generation", "Risk Assessment Support"]
        elif "gesund" in branche_lower or "health" in branche_lower:
            return ["Documentation", "Appointment Scheduling", "Patient Communication", "Research Support"]
        elif "recht" in branche_lower or "legal" in branche_lower:
            return ["Contract Analysis", "Legal Research", "Document Generation", "Case Summary"]
        else:
            return ["Content Generation", "Document Automation", "Customer Support", "Data Analysis"]
    else:
        if "finanz" in branche_lower:
            return ["Dokumentenautomatisierung", "Kundenkommunikation", "Berichterstellung", "Risikoanalyse-Unterstützung"]
        elif "gesund" in branche_lower:
            return ["Dokumentation", "Terminplanung", "Patientenkommunikation", "Rechercheunterstützung"]
        elif "recht" in branche_lower:
            return ["Vertragsanalyse", "Rechtsrecherche", "Dokumentenerstellung", "Fallzusammenfassung"]
        else:
            return ["Content-Erstellung", "Dokumentenautomatisierung", "Kundensupport", "Datenanalyse"]


def _render_usecase_html_de(tagged_usecases: List[Tuple[str, str]]) -> str:
    """Render German use case list."""
    risk_labels = {
        "none": "Kein Risiko",
        "minimal": "Minimal",
        "limited": "Begrenzt",
        "high-risk": "Hochrisiko"
    }
    risk_classes = {
        "none": "success",
        "minimal": "success",
        "limited": "warning",
        "high-risk": "danger"
    }

    html = '<ul class="usecase-risk-list">\n'
    for usecase, risk in tagged_usecases:
        label = risk_labels.get(risk, risk)
        css_class = risk_classes.get(risk, "secondary")
        html += f'  <li>{usecase} <span class="badge badge-{css_class}">{label}</span></li>\n'
    html += '</ul>'

    return html


def _render_usecase_html_en(tagged_usecases: List[Tuple[str, str]]) -> str:
    """Render English use case list."""
    risk_labels = {
        "none": "No Risk",
        "minimal": "Minimal",
        "limited": "Limited",
        "high-risk": "High-Risk"
    }
    risk_classes = {
        "none": "success",
        "minimal": "success",
        "limited": "warning",
        "high-risk": "danger"
    }

    html = '<ul class="usecase-risk-list">\n'
    for usecase, risk in tagged_usecases:
        label = risk_labels.get(risk, risk)
        css_class = risk_classes.get(risk, "secondary")
        html += f'  <li>{usecase} <span class="badge badge-{css_class}">{label}</span></li>\n'
    html += '</ul>'

    return html


# =============================================================================
# MAIN BUILD FUNCTION
# =============================================================================

def build_ai_act_sections(
    briefing: Dict[str, Any],
    lang: str = "de"
) -> Dict[str, Any]:
    """
    Build all AI Act sections from briefing data.

    Returns dict with all AI_ACT_* variables.
    """
    # Extract relevant data from briefing
    branche = briefing.get("BRANCHE_LABEL") or briefing.get("branche", "Allgemein")
    size = briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse", "")

    # Extract use cases from various possible fields
    usecases = []
    if briefing.get("ki_einsatzbereiche"):
        if isinstance(briefing["ki_einsatzbereiche"], list):
            usecases = briefing["ki_einsatzbereiche"]
        elif isinstance(briefing["ki_einsatzbereiche"], str):
            usecases = [x.strip() for x in briefing["ki_einsatzbereiche"].split(",")]

    # KIS-1234: "anwendungsfaelle" (Fragebogen-Feld: chatbots, content
    # generation, personalisierung, ...) floss bisher NICHT in die
    # Risikoklassifikation ein — die Einstufung lief dann nur über die
    # Hauptleistung und übersah Art.-50-relevante Anwendungsfälle.
    _af = briefing.get("anwendungsfaelle") or briefing.get("ANWENDUNGSFAELLE_LABELS")
    if _af:
        if isinstance(_af, str):
            _af = [x.strip() for x in _af.split(",") if x.strip()]
        usecases = list(usecases) + [str(x) for x in _af]

    if not usecases and briefing.get("hauptleistung"):
        usecases = [briefing["hauptleistung"]]

    # Get automation percentage if available
    automatisierung = briefing.get("automatisierungsgrad", 0)
    if isinstance(automatisierung, str):
        try:
            automatisierung = int(automatisierung.replace("%", ""))
        except ValueError:
            automatisierung = 0

    # Determine risk level
    risk_level = determine_risk_level(branche, size, usecases, automatisierung)

    # Generate all sections
    risk_reasoning = generate_risk_reasoning(risk_level, branche, size, usecases, lang)
    duty_matrix = generate_duty_matrix_html(risk_level, branche, size, lang)
    alerts = generate_noncompliance_alerts(risk_level, branche, size, lang)
    gaps = generate_data_gaps(risk_level, branche, size, lang)
    next_steps = generate_next_steps_html(risk_level, branche, size, lang)
    usecase_html = generate_usecase_risk_html(usecases, branche, size, lang)

    log.info("🏛️ AI Act sections generated: risk_level=%s, alerts=%d, gaps=%d",
             risk_level, len(alerts), len(gaps))

    return {
        "AI_ACT_RISK_LEVEL": risk_level,
        "AI_ACT_RISK_REASONING": risk_reasoning,
        "AI_ACT_DUTY_MATRIX_HTML": duty_matrix,
        "AI_ACT_NONCOMPLIANCE_ALERTS": alerts,
        "AI_ACT_DATA_GAPS": gaps,
        "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML": next_steps,
        "AI_ACT_RELATED_USECASES_HTML": usecase_html,
    }


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_ai_act_sections(sections: Dict[str, Any]) -> List[str]:
    """
    Validate AI Act sections for completeness and correctness.
    Returns list of error messages (empty if valid).
    """
    errors = []

    # Check risk level
    risk_level = sections.get("AI_ACT_RISK_LEVEL", "")
    if risk_level not in VALID_RISK_LEVELS:
        errors.append(f"Invalid AI_ACT_RISK_LEVEL: '{risk_level}' not in {VALID_RISK_LEVELS}")

    # Check risk reasoning length
    reasoning = sections.get("AI_ACT_RISK_REASONING", "")
    word_count = len(reasoning.split())
    if word_count < 60:
        errors.append(f"AI_ACT_RISK_REASONING too short: {word_count} words (min 60)")

    # Check duty matrix
    matrix = sections.get("AI_ACT_DUTY_MATRIX_HTML", "")
    if "<table" not in matrix or "</table>" not in matrix:
        errors.append("AI_ACT_DUTY_MATRIX_HTML missing table tags")

    # Count table rows
    row_count = matrix.count("<tr>") - 1  # Subtract header row
    if row_count < 3:
        errors.append(f"AI_ACT_DUTY_MATRIX_HTML has only {row_count} rows (min 3)")

    # Check alerts
    alerts = sections.get("AI_ACT_NONCOMPLIANCE_ALERTS", [])
    if len(alerts) < 2:
        errors.append(f"AI_ACT_NONCOMPLIANCE_ALERTS has only {len(alerts)} items (min 2)")

    # Check gaps
    gaps = sections.get("AI_ACT_DATA_GAPS", [])
    if len(gaps) < 2:
        errors.append(f"AI_ACT_DATA_GAPS has only {len(gaps)} items (min 2)")

    # Check next steps
    next_steps = sections.get("AI_ACT_RECOMMENDED_NEXT_STEPS_HTML", "")
    if not next_steps or "<ol" not in next_steps:
        errors.append("AI_ACT_RECOMMENDED_NEXT_STEPS_HTML is empty or malformed")

    # Check use cases
    usecases = sections.get("AI_ACT_RELATED_USECASES_HTML", "")
    if not usecases or "<ul" not in usecases:
        errors.append("AI_ACT_RELATED_USECASES_HTML is empty or malformed")

    return errors


def check_persona_leaks(text: str, size: str) -> List[str]:
    """
    Check for persona leaks in AI Act text.
    Returns list of found forbidden terms.
    """
    size_lower = size.lower()
    text_lower = text.lower()
    leaks = []

    is_solo = "solo" in size_lower or "freiberuf" in size_lower or "1" in size_lower

    if is_solo:
        # Check for team/kmu terms in solo report
        for term in SOLO_FORBIDDEN_TERMS + TEAM_KMU_TERMS_FOR_SOLO:
            if term in text_lower:
                leaks.append(term)
    else:
        # Check for solo-specific terms in team/kmu report
        solo_specific = ["als einzelperson", "allein arbeitend", "solo-selbstständig",
                        "as an individual", "working alone", "freelancer"]
        for term in solo_specific:
            if term in text_lower:
                leaks.append(term)

    return leaks


# =============================================================================
# SPRINT G8.1: CROSS-SECTION INJECTION
# =============================================================================

# G8.3: Extended Persona Hard-Guards
EXTENDED_SOLO_FORBIDDEN = [
    # Team/Organization terms
    "ihr team", "your team", "das team", "the team",
    "mitarbeiter", "employees", "mitarbeitende",
    "abteilung", "abteilungen", "department", "departments",
    "fachbereiche", "fachbereich", "divisions",
    "organisation", "organization",
    "unternehmen mit 11", "company with 11",
    "governance board", "compliance-officer", "compliance officer",
    "projektleiter", "project manager", "abteilungsleiter",
    "teamleiter", "team lead", "team leader",
]

EXTENDED_TEAM_FORBIDDEN = [
    # Solo-specific terms
    "als einzelperson", "as an individual", "as a solo",
    "solo-selbstständig", "solo-selbstständige", "solo-selbstständigen",
    "individuelle kapazität", "individual capacity",
    "ihre persönliche kapazität", "your personal capacity",
    "freiberufler", "freiberuflerin", "freelancer",
    "einzelunternehmer", "einzelunternehmerin", "sole proprietor",
    "allein arbeitend", "working alone",
]

EXTENDED_KMU_FORBIDDEN = [
    # Solo-specific terms (same as Team + some extras)
    "als einzelperson", "as an individual", "as a solo",
    "solo-selbstständig", "solo-selbstständige", "solo-selbstständigen",
    "individuelle kapazität", "individual capacity",
    "ihre persönliche kapazität", "your personal capacity",
    "freiberufler", "freiberuflerin", "freelancer",
    "einzelunternehmer", "einzelunternehmerin", "sole proprietor",
    "allein arbeitend", "working alone",
    # Team-specific mini-structures (optional for large KMU)
    "2–10 personen", "2-10 persons", "kleines team von",
]


def get_ai_act_exec_summary_injection(
    risk_level: str,
    size: str,
    branche: str,
    lang: str = "de"
) -> str:
    """
    G8.1: Generate 1-2 sentence AI Act injection for Executive Summary.
    Size-aware, no tables, no legal jargon.
    """
    size_lower = size.lower()
    is_solo = "solo" in size_lower or "freiberuf" in size_lower
    is_team = "team" in size_lower or "klein" in size_lower

    if lang == "en":
        if risk_level == "high-risk":
            if is_solo:
                return (
                    "EU AI Act classification: High-risk. Your AI applications require "
                    "documented risk management, quality controls, and human oversight. "
                    "Early compliance preparation is essential."
                )
            elif is_team:
                return (
                    "EU AI Act classification: High-risk. Your organization needs structured "
                    "compliance measures including risk documentation, oversight processes, "
                    "and designated responsibilities. Proactive preparation is recommended."
                )
            else:
                return (
                    "EU AI Act classification: High-risk. Your company requires comprehensive "
                    "compliance infrastructure including quality management, risk analysis, "
                    "human oversight, and post-market monitoring. Immediate action recommended."
                )
        elif risk_level == "limited":
            if is_solo:
                return (
                    "EU AI Act classification: Limited risk. Focus on transparency: "
                    "document AI usage and label AI-generated content clearly."
                )
            elif is_team:
                return (
                    "EU AI Act classification: Limited risk. Establish transparency measures, "
                    "basic documentation, and shared guidelines for AI usage."
                )
            else:
                return (
                    "EU AI Act classification: Limited risk. Implement transparency obligations, "
                    "structured documentation, and defined responsibilities for AI governance."
                )
        else:  # minimal/none
            if is_solo:
                return (
                    "EU AI Act classification: Minimal risk. No mandatory requirements apply. "
                    "Voluntary best practices like documentation and quality checks are recommended."
                )
            else:
                return (
                    "EU AI Act classification: Minimal risk. No specific obligations apply. "
                    "Establish basic guidelines and documentation as voluntary best practices."
                )
    else:  # German
        if risk_level == "high-risk":
            if is_solo:
                return (
                    "EU AI Act Einstufung: Hochrisiko. Ihre KI-Anwendungen erfordern "
                    "dokumentiertes Risikomanagement, Qualitätskontrollen und menschliche "
                    "Aufsicht. Frühzeitige Compliance-Vorbereitung ist essenziell."
                )
            elif is_team:
                return (
                    "EU AI Act Einstufung: Hochrisiko. Ihr Unternehmen benötigt strukturierte "
                    "Compliance-Maßnahmen mit Risikodokumentation, Aufsichtsprozessen und "
                    "klaren Verantwortlichkeiten. Proaktive Vorbereitung wird empfohlen."
                )
            else:
                return (
                    "EU AI Act Einstufung: Hochrisiko. Ihr Unternehmen erfordert umfassende "
                    "Compliance-Strukturen mit Qualitätsmanagement, Risikoanalyse, menschlicher "
                    "Aufsicht und Post-Market-Monitoring. Sofortige Maßnahmen empfohlen."
                )
        elif risk_level == "limited":
            if is_solo:
                return (
                    "EU AI Act Einstufung: Begrenztes Risiko. Fokus auf Transparenz: "
                    "KI-Nutzung dokumentieren und KI-generierte Inhalte klar kennzeichnen."
                )
            elif is_team:
                return (
                    "EU AI Act Einstufung: Begrenztes Risiko. Transparenzmaßnahmen etablieren, "
                    "Basisdokumentation führen und gemeinsame Richtlinien für KI-Nutzung definieren."
                )
            else:
                return (
                    "EU AI Act Einstufung: Begrenztes Risiko. Transparenzpflichten umsetzen, "
                    "strukturierte Dokumentation etablieren und Verantwortlichkeiten für "
                    "KI-Governance definieren."
                )
        else:  # minimal/none
            if is_solo:
                return (
                    "EU AI Act Einstufung: Minimales Risiko. Keine Pflichten. "
                    "Freiwillige Best Practices wie Dokumentation und Qualitätsprüfung empfohlen."
                )
            else:
                return (
                    "EU AI Act Einstufung: Minimales Risiko. Keine spezifischen Pflichten. "
                    "Grundlegende Richtlinien und Dokumentation als freiwillige Best Practices."
                )


def get_ai_act_business_case_injection(
    risk_level: str,
    size: str,
    lang: str = "de"
) -> Dict[str, Any]:
    """
    G8.1: Generate Business Case cost adjustments based on risk level.
    Returns dict with CAPEX/OPEX modifiers and text injection.
    """
    size_lower = size.lower()
    is_solo = "solo" in size_lower or "freiberuf" in size_lower

    if risk_level == "high-risk":
        capex_modifier = 1.25  # +25% for compliance infrastructure
        opex_modifier = 1.15   # +15% for ongoing compliance
        if lang == "en":
            text = (
                "Compliance costs: High-risk classification requires additional investment "
                "in documentation, monitoring, and quality management systems."
            )
        else:
            text = (
                "Compliance-Kosten: Hochrisiko-Einstufung erfordert zusätzliche Investitionen "
                "in Dokumentation, Monitoring und Qualitätsmanagementsysteme."
            )
    elif risk_level == "limited":
        capex_modifier = 1.10  # +10% for transparency tools
        opex_modifier = 1.05   # +5% for documentation
        if lang == "en":
            text = (
                "Transparency costs: Limited risk requires investment in documentation "
                "and labeling infrastructure."
            )
        else:
            text = (
                "Transparenz-Kosten: Begrenztes Risiko erfordert Investitionen in "
                "Dokumentations- und Kennzeichnungsinfrastruktur."
            )
    else:  # minimal/none
        capex_modifier = 1.0
        opex_modifier = 1.0
        if lang == "en":
            text = "Minimal compliance overhead – focus on efficiency gains."
        else:
            text = "Minimaler Compliance-Aufwand – Fokus auf Effizienzgewinne."

    return {
        "CAPEX_MODIFIER": capex_modifier,
        "OPEX_MODIFIER": opex_modifier,
        "AI_ACT_BUSINESS_CASE_TEXT": text,
    }


def get_ai_act_roadmap_injection(
    risk_level: str,
    size: str,
    lang: str = "de"
) -> Dict[str, str]:
    """
    G8.1: Generate roadmap milestones based on risk level.
    Returns dict with 90d and 12m roadmap additions.
    """
    size_lower = size.lower()
    is_solo = "solo" in size_lower or "freiberuf" in size_lower

    if lang == "en":
        if risk_level == "high-risk":
            roadmap_90d = (
                "<li><strong>Week 1-4:</strong> Risk analysis & documentation framework</li>"
                "<li><strong>Week 5-8:</strong> Human oversight processes & QMS setup</li>"
                "<li><strong>Week 9-12:</strong> Conformity assessment preparation</li>"
            )
            roadmap_12m = (
                "<li><strong>Q1:</strong> Complete risk documentation & QMS implementation</li>"
                "<li><strong>Q2:</strong> Human oversight training & process rollout</li>"
                "<li><strong>Q3:</strong> Post-market monitoring setup & incident procedures</li>"
                "<li><strong>Q4:</strong> Audit preparation & conformity declaration</li>"
            )
        elif risk_level == "limited":
            roadmap_90d = (
                "<li><strong>Week 1-4:</strong> AI inventory & documentation setup</li>"
                "<li><strong>Week 5-8:</strong> Transparency labeling implementation</li>"
                "<li><strong>Week 9-12:</strong> Monitoring & logging setup</li>"
            )
            roadmap_12m = (
                "<li><strong>Q1:</strong> Complete AI documentation</li>"
                "<li><strong>Q2:</strong> Transparency measures & oversight processes</li>"
                "<li><strong>Q3:</strong> Regular review cycles</li>"
                "<li><strong>Q4:</strong> Compliance assessment & optimization</li>"
            )
        else:  # minimal
            roadmap_90d = (
                "<li><strong>Week 1-4:</strong> AI awareness & basic documentation</li>"
                "<li><strong>Week 5-8:</strong> Quality review guidelines</li>"
                "<li><strong>Week 9-12:</strong> Simple logging implementation</li>"
            )
            roadmap_12m = (
                "<li><strong>Q1-Q2:</strong> Best practices implementation</li>"
                "<li><strong>Q3-Q4:</strong> Review & optimization</li>"
            )
    else:  # German
        if risk_level == "high-risk":
            roadmap_90d = (
                "<li><strong>Woche 1-4:</strong> Risikoanalyse & Dokumentationsrahmen</li>"
                "<li><strong>Woche 5-8:</strong> Human Oversight Prozesse & QMS-Aufbau</li>"
                "<li><strong>Woche 9-12:</strong> Konformitätsbewertung vorbereiten</li>"
            )
            roadmap_12m = (
                "<li><strong>Q1:</strong> Risikodokumentation & QMS-Implementierung</li>"
                "<li><strong>Q2:</strong> Human Oversight Schulung & Prozess-Rollout</li>"
                "<li><strong>Q3:</strong> Post-Market-Monitoring & Incident-Prozesse</li>"
                "<li><strong>Q4:</strong> Audit-Vorbereitung & Konformitätserklärung</li>"
            )
        elif risk_level == "limited":
            roadmap_90d = (
                "<li><strong>Woche 1-4:</strong> KI-Inventar & Dokumentation aufsetzen</li>"
                "<li><strong>Woche 5-8:</strong> Transparenz-Kennzeichnung implementieren</li>"
                "<li><strong>Woche 9-12:</strong> Monitoring & Logging einrichten</li>"
            )
            roadmap_12m = (
                "<li><strong>Q1:</strong> KI-Dokumentation vervollständigen</li>"
                "<li><strong>Q2:</strong> Transparenzmaßnahmen & Aufsichtsprozesse</li>"
                "<li><strong>Q3:</strong> Regelmäßige Review-Zyklen</li>"
                "<li><strong>Q4:</strong> Compliance-Bewertung & Optimierung</li>"
            )
        else:  # minimal
            roadmap_90d = (
                "<li><strong>Woche 1-4:</strong> KI-Awareness & Basis-Dokumentation</li>"
                "<li><strong>Woche 5-8:</strong> Qualitätsprüfungs-Richtlinien</li>"
                "<li><strong>Woche 9-12:</strong> Einfaches Logging implementieren</li>"
            )
            roadmap_12m = (
                "<li><strong>Q1-Q2:</strong> Best Practices implementieren</li>"
                "<li><strong>Q3-Q4:</strong> Review & Optimierung</li>"
            )

    return {
        "AI_ACT_ROADMAP_90D_INJECTION": roadmap_90d,
        "AI_ACT_ROADMAP_12M_INJECTION": roadmap_12m,
    }


def get_ai_act_governance_injection(
    risk_level: str,
    size: str,
    alerts: List[str],
    gaps: List[str],
    lang: str = "de"
) -> str:
    """
    G8.1: Generate governance section injection with duty matrix integration.
    """
    size_lower = size.lower()
    is_solo = "solo" in size_lower or "freiberuf" in size_lower

    # Build action items from alerts (max 3)
    action_items = alerts[:3] if alerts else []

    if lang == "en":
        if risk_level == "high-risk":
            if is_solo:
                intro = "AI Act governance focus: Risk management, documentation, and oversight."
            else:
                intro = "AI Act governance requirements: Structured compliance with defined roles and processes."
            level_text = "High-risk systems require comprehensive governance including QMS, risk documentation, and human oversight."
        elif risk_level == "limited":
            intro = "AI Act governance focus: Transparency and documentation."
            level_text = "Limited risk requires transparency measures and basic documentation."
        else:
            intro = "AI Act governance: Voluntary best practices."
            level_text = "Minimal risk – no mandatory governance requirements."

        if action_items:
            actions_html = "<ul class='governance-actions'>"
            for item in action_items:
                actions_html += f"<li>{item}</li>"
            actions_html += "</ul>"
        else:
            actions_html = ""

        return f"<div class='ai-act-governance'><p><strong>{intro}</strong></p><p>{level_text}</p>{actions_html}</div>"

    else:  # German
        if risk_level == "high-risk":
            if is_solo:
                intro = "AI Act Governance-Fokus: Risikomanagement, Dokumentation und Aufsicht."
            else:
                intro = "AI Act Governance-Anforderungen: Strukturierte Compliance mit definierten Rollen und Prozessen."
            level_text = "Hochrisiko-Systeme erfordern umfassende Governance mit QMS, Risikodokumentation und Human Oversight."
        elif risk_level == "limited":
            intro = "AI Act Governance-Fokus: Transparenz und Dokumentation."
            level_text = "Begrenztes Risiko erfordert Transparenzmaßnahmen und Basisdokumentation."
        else:
            intro = "AI Act Governance: Freiwillige Best Practices."
            level_text = "Minimales Risiko – keine Pflicht-Governance-Anforderungen."

        if action_items:
            actions_html = "<ul class='governance-actions'>"
            for item in action_items:
                actions_html += f"<li>{item}</li>"
            actions_html += "</ul>"
        else:
            actions_html = ""

        return f"<div class='ai-act-governance'><p><strong>{intro}</strong></p><p>{level_text}</p>{actions_html}</div>"


def get_ai_act_risks_injection(
    risk_level: str,
    branche: str,
    size: str,
    lang: str = "de"
) -> str:
    """
    G8.1: Generate risk section injection with branch-specific context.
    """
    branche_lower = branche.lower()
    is_finance = any(b in branche_lower for b in ["finanz", "finance", "bank", "versicher", "insurance"])
    is_hr = any(b in branche_lower for b in ["hr", "personal", "human resources", "recruiting"])

    if lang == "en":
        if risk_level == "high-risk":
            base_risk = "AI Act non-compliance risk: High. Potential penalties up to €35M or 7% of global turnover."
            if is_finance:
                sector_risk = " Additional sector regulations (BAIT/MaRisk) apply to AI systems in financial services."
            elif is_hr:
                sector_risk = " Employment law considerations for automated decision-making in HR processes."
            else:
                sector_risk = ""
        elif risk_level == "limited":
            base_risk = "AI Act non-compliance risk: Moderate. Transparency violations may result in regulatory action."
            sector_risk = ""
        else:
            base_risk = "AI Act risk exposure: Low. Focus on voluntary compliance measures."
            sector_risk = ""

        return f"<p class='ai-act-risk'>{base_risk}{sector_risk}</p>"

    else:  # German
        if risk_level == "high-risk":
            base_risk = "AI Act Non-Compliance-Risiko: Hoch. Mögliche Strafen bis €35 Mio. oder 7% des globalen Umsatzes."
            if is_finance:
                sector_risk = " Zusätzliche Branchenregulierung (BAIT/MaRisk/VAIT) für KI-Systeme im Finanzsektor."
            elif is_hr:
                sector_risk = " Arbeitsrechtliche Aspekte bei automatisierten Entscheidungen in HR-Prozessen."
            else:
                sector_risk = ""
        elif risk_level == "limited":
            base_risk = "AI Act Non-Compliance-Risiko: Moderat. Transparenzverstöße können zu Aufsichtsmaßnahmen führen."
            sector_risk = ""
        else:
            base_risk = "AI Act Risikoexposition: Gering. Fokus auf freiwillige Compliance-Maßnahmen."
            sector_risk = ""

        return f"<p class='ai-act-risk'>{base_risk}{sector_risk}</p>"


def get_ai_act_tools_injection(
    risk_level: str,
    size: str,
    lang: str = "de"
) -> str:
    """
    G8.1: Generate tools recommendation injection based on risk level.
    """
    size_lower = size.lower()
    is_solo = "solo" in size_lower or "freiberuf" in size_lower

    if lang == "en":
        if risk_level == "high-risk":
            tools = [
                "Audit trail & logging tools (e.g., MLflow, Weights & Biases)",
                "Explainability frameworks (e.g., SHAP, LIME)",
                "Model monitoring solutions (e.g., Evidently, Arize)",
                "Documentation platforms (e.g., Notion, Confluence)",
            ]
        elif risk_level == "limited":
            tools = [
                "Version control & documentation (e.g., Git, Notion)",
                "Simple logging solutions",
                "Content labeling tools",
            ]
        else:
            tools = [
                "Basic documentation tools",
                "Simple quality review checklists",
            ]

        intro = "Recommended compliance tools based on your AI Act risk classification:"
    else:
        if risk_level == "high-risk":
            tools = [
                "Audit-Trail & Logging-Tools (z.B. MLflow, Weights & Biases)",
                "Explainability-Frameworks (z.B. SHAP, LIME)",
                "Model-Monitoring-Lösungen (z.B. Evidently, Arize)",
                "Dokumentationsplattformen (z.B. Notion, Confluence)",
            ]
        elif risk_level == "limited":
            tools = [
                "Versionskontrolle & Dokumentation (z.B. Git, Notion)",
                "Einfache Logging-Lösungen",
                "Content-Kennzeichnungs-Tools",
            ]
        else:
            tools = [
                "Basis-Dokumentations-Tools",
                "Einfache Qualitätsprüfungs-Checklisten",
            ]

        intro = "Empfohlene Compliance-Tools basierend auf Ihrer AI Act Risikoeinstufung:"

    tools_html = f"<p class='ai-act-tools-intro'>{intro}</p><ul class='ai-act-tools'>"
    for tool in tools:
        tools_html += f"<li>{tool}</li>"
    tools_html += "</ul>"

    return tools_html


# =============================================================================
# SPRINT G8.2: HARMONIZATION & CONSISTENCY ENGINE
# =============================================================================

def ai_act_harmonize(sections: Dict[str, Any], briefing: Dict[str, Any]) -> Dict[str, Any]:
    """
    G8.2: Harmonize AI Act content across sections for consistency.

    Checks:
    - Executive Summary ↔ Risk Level consistency
    - Roadmap ↔ Duty Matrix alignment
    - Governance ↔ Alerts/Gaps integration
    - Business Case ↔ Risk Level cost adjustment

    Returns:
    - Harmonized sections dict
    - AI_ACT_CONSISTENCY_WARNINGS list (max 3)
    """
    warnings: List[str] = []

    risk_level = sections.get("AI_ACT_RISK_LEVEL", "minimal")
    size = briefing.get("unternehmensgroesse", "")
    branche = briefing.get("branche", "")
    lang = briefing.get("lang", "de")
    alerts = sections.get("AI_ACT_NONCOMPLIANCE_ALERTS", [])
    gaps = sections.get("AI_ACT_DATA_GAPS", [])

    # --- Consistency Check 1: Executive Summary ---
    exec_summary = sections.get("EXECUTIVE_SUMMARY_HTML", "")
    if exec_summary:
        exec_lower = exec_summary.lower()
        if risk_level == "high-risk" and "hochrisiko" not in exec_lower and "high-risk" not in exec_lower:
            warnings.append("Executive Summary erwähnt Hochrisiko-Einstufung nicht")
        elif risk_level == "limited" and "begrenzt" not in exec_lower and "limited" not in exec_lower and "transparenz" not in exec_lower:
            warnings.append("Executive Summary erwähnt Transparenzpflichten nicht")

    # --- Consistency Check 2: Business Case CAPEX/OPEX ---
    if risk_level == "high-risk":
        capex = sections.get("CAPEX_REALISTISCH_EUR", 0)
        if isinstance(capex, (int, float)) and capex > 0:
            # Check if compliance costs are factored in
            bc_html = sections.get("BUSINESS_CASE_HTML", "")
            if bc_html and "compliance" not in bc_html.lower() and "konformität" not in bc_html.lower():
                warnings.append("Business Case enthält keine Compliance-Kosten für Hochrisiko")

    # --- Consistency Check 3: Roadmap coverage ---
    roadmap_90d = sections.get("PILOT_PLAN_HTML", "") or sections.get("ROADMAP_90D_HTML", "")
    if roadmap_90d and risk_level == "high-risk":
        roadmap_lower = roadmap_90d.lower()
        if "qms" not in roadmap_lower and "qualitätsmanagement" not in roadmap_lower and "quality management" not in roadmap_lower:
            warnings.append("90-Tage-Roadmap enthält keine QMS-Planung für Hochrisiko")

    # --- Inject cross-section content ---
    harmonized = dict(sections)

    # Add AI Act injection for Executive Summary (if not already present)
    if "AI_ACT_EXEC_INJECTION" not in harmonized:
        harmonized["AI_ACT_EXEC_INJECTION"] = get_ai_act_exec_summary_injection(
            risk_level, size, branche, lang
        )

    # Add Business Case injection
    bc_injection = get_ai_act_business_case_injection(risk_level, size, lang)
    harmonized.update(bc_injection)

    # Add Roadmap injection
    roadmap_injection = get_ai_act_roadmap_injection(risk_level, size, lang)
    harmonized.update(roadmap_injection)

    # Add Governance injection
    harmonized["AI_ACT_GOVERNANCE_INJECTION"] = get_ai_act_governance_injection(
        risk_level, size, alerts, gaps, lang
    )

    # Add Risks injection
    harmonized["AI_ACT_RISKS_INJECTION"] = get_ai_act_risks_injection(
        risk_level, branche, size, lang
    )

    # Add Tools injection
    harmonized["AI_ACT_TOOLS_INJECTION"] = get_ai_act_tools_injection(
        risk_level, size, lang
    )

    # Store warnings (max 3)
    harmonized["AI_ACT_CONSISTENCY_WARNINGS"] = warnings[:3]

    log.info("🔄 AI Act harmonization complete: %d warnings", len(warnings))

    return harmonized


# =============================================================================
# SPRINT G8.3: EXTENDED PERSONA HARD-GUARDS
# =============================================================================

def apply_ai_act_persona_filter(text: str, size: str) -> str:
    """
    G8.3: Apply persona-specific filtering to AI Act content.
    Removes or replaces size-inappropriate terms.
    """
    if not text or not isinstance(text, str):
        return text

    size_lower = size.lower()

    # Determine size category
    if "solo" in size_lower or "freiberuf" in size_lower or "1" in size_lower:
        size_key = "solo"
        forbidden = EXTENDED_SOLO_FORBIDDEN
        replacements = {
            "ihr team": "Sie",
            "your team": "you",
            "das team": "Sie",
            "the team": "you",
            "mitarbeiter": "Sie",
            "employees": "you",
            "abteilung": "Ihren Arbeitsbereich",
            "department": "your work area",
        }
    elif "team" in size_lower or "klein" in size_lower:
        size_key = "team"
        forbidden = EXTENDED_TEAM_FORBIDDEN
        replacements = {
            "als einzelperson": "als kleines Team",
            "as an individual": "as a small team",
            "solo-selbstständige": "kleine Teams",
            "freelancer": "Ihr Team",
        }
    else:  # KMU
        size_key = "kmu"
        forbidden = EXTENDED_KMU_FORBIDDEN
        replacements = {
            "als einzelperson": "als Unternehmen",
            "as an individual": "as a company",
            "solo-selbstständige": "KMU",
            "freelancer": "Ihr Unternehmen",
        }

    # Apply replacements
    import re
    result = text
    for term, replacement in replacements.items():
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        result = pattern.sub(replacement, result)

    return result


def validate_ai_act_persona_compliance(sections: Dict[str, Any], size: str) -> List[str]:
    """
    G8.3: Validate that AI Act sections contain no persona leaks.
    Returns list of violations found.
    """
    violations = []
    size_lower = size.lower()

    # Determine forbidden terms based on size
    if "solo" in size_lower or "freiberuf" in size_lower:
        forbidden = EXTENDED_SOLO_FORBIDDEN
        size_key = "solo"
    elif "team" in size_lower or "klein" in size_lower:
        forbidden = EXTENDED_TEAM_FORBIDDEN
        size_key = "team"
    else:
        forbidden = EXTENDED_KMU_FORBIDDEN
        size_key = "kmu"

    # AI Act sections to validate
    ai_act_keys = [
        "AI_ACT_RISK_REASONING",
        "AI_ACT_DUTY_MATRIX_HTML",
        "AI_ACT_NONCOMPLIANCE_ALERTS_HTML",
        "AI_ACT_DATA_GAPS_HTML",
        "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML",
        "AI_ACT_RELATED_USECASES_HTML",
        "AI_ACT_EXEC_INJECTION",
        "AI_ACT_GOVERNANCE_INJECTION",
        "AI_ACT_RISKS_INJECTION",
        "AI_ACT_TOOLS_INJECTION",
    ]

    for key in ai_act_keys:
        content = sections.get(key, "")
        if not isinstance(content, str):
            continue

        content_lower = content.lower()
        for term in forbidden:
            if term.lower() in content_lower:
                violations.append(f"[{key}] Persona leak: '{term}' (size={size_key})")

    return violations


# =============================================================================
# SPRINT G8.6: PERFORMANCE OPTIMIZATION (Caching)
# =============================================================================

# Simple cache for duty matrix (per risk_level + size + lang)
_duty_matrix_cache: Dict[str, str] = {}


def get_cached_duty_matrix(risk_level: str, branche: str, size: str, lang: str) -> str:
    """
    G8.6: Get duty matrix with caching for performance.
    """
    cache_key = f"{risk_level}:{size}:{lang}"

    if cache_key not in _duty_matrix_cache:
        _duty_matrix_cache[cache_key] = generate_duty_matrix_html(
            risk_level, branche, size, lang
        )

    return _duty_matrix_cache[cache_key]


def clear_duty_matrix_cache() -> None:
    """Clear the duty matrix cache."""
    global _duty_matrix_cache
    _duty_matrix_cache = {}


def build_ai_act_sections_optimized(
    briefing: Dict[str, Any],
    lang: str = "de"
) -> Dict[str, Any]:
    """
    G8.6: Optimized version of build_ai_act_sections with caching.
    Generates all AI Act sections with performance optimizations.
    """
    # Extract relevant data
    branche = briefing.get("BRANCHE_LABEL") or briefing.get("branche", "Allgemein")
    size = briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse", "")

    # Extract use cases
    usecases = []
    if briefing.get("ki_einsatzbereiche"):
        if isinstance(briefing["ki_einsatzbereiche"], list):
            usecases = briefing["ki_einsatzbereiche"]
        elif isinstance(briefing["ki_einsatzbereiche"], str):
            usecases = [x.strip() for x in briefing["ki_einsatzbereiche"].split(",")]

    # KIS-1234: "anwendungsfaelle" (Fragebogen-Feld: chatbots, content
    # generation, personalisierung, ...) floss bisher NICHT in die
    # Risikoklassifikation ein — die Einstufung lief dann nur über die
    # Hauptleistung und übersah Art.-50-relevante Anwendungsfälle.
    _af = briefing.get("anwendungsfaelle") or briefing.get("ANWENDUNGSFAELLE_LABELS")
    if _af:
        if isinstance(_af, str):
            _af = [x.strip() for x in _af.split(",") if x.strip()]
        usecases = list(usecases) + [str(x) for x in _af]

    if not usecases and briefing.get("hauptleistung"):
        usecases = [briefing["hauptleistung"]]

    # Get automation percentage
    automatisierung = briefing.get("automatisierungsgrad", 0)
    if isinstance(automatisierung, str):
        try:
            automatisierung = int(automatisierung.replace("%", ""))
        except ValueError:
            automatisierung = 0

    # Determine risk level (single pass)
    risk_level = determine_risk_level(branche, size, usecases, automatisierung)

    # Generate all sections in one pass
    sections = {
        "AI_ACT_RISK_LEVEL": risk_level,
        "AI_ACT_RISK_REASONING": generate_risk_reasoning(
            risk_level, branche, size, usecases, lang
        ),
        "AI_ACT_DUTY_MATRIX_HTML": get_cached_duty_matrix(
            risk_level, branche, size, lang
        ),
        "AI_ACT_NONCOMPLIANCE_ALERTS": generate_noncompliance_alerts(
            risk_level, branche, size, lang
        ),
        "AI_ACT_DATA_GAPS": generate_data_gaps(
            risk_level, branche, size, lang
        ),
        "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML": generate_next_steps_html(
            risk_level, branche, size, lang
        ),
        "AI_ACT_RELATED_USECASES_HTML": generate_usecase_risk_html(
            usecases, branche, size, lang
        ),
    }

    # Apply persona filter to text sections
    for key in ["AI_ACT_RISK_REASONING"]:
        value = sections[key]
        if isinstance(value, str):
            sections[key] = apply_ai_act_persona_filter(value, size)

    log.info("🏛️ AI Act sections (optimized): risk_level=%s", risk_level)

    return sections
