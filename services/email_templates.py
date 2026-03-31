# -*- coding: utf-8 -*-
from __future__ import annotations
"""E‑Mail‑Templates (HTML) für den Report-Versand (UTF‑8, mobil‑tauglich)."""
from html import escape
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote


def generate_feedback_link(email: str, briefing_id: int = None) -> str:
    """Generiert den Feedback-Link mit der E-Mail als URL-Parameter."""
    encoded_email = quote(email)
    url = f"https://make.ki-sicherheit.jetzt/feedback/feedback.html?email={encoded_email}"
    if briefing_id:
        url += f"&briefing_id={briefing_id}"
    return url

def render_report_ready_email(recipient: str, pdf_url: Optional[str], briefing_summary_html: Optional[str] = None, user_email: Optional[str] = None, briefing_id: Optional[int] = None) -> str:
    if recipient == "admin":
        title = "Kopie: KI‑Status‑Report (inkl. Briefing)"
        intro = "dies ist die Admin‑Kopie des automatisch generierten KI‑Status‑Reports."
        cta_hint = "Tipp: Für Audit‑Ready‑Kunden kann optional das EU‑AI‑Act‑Add‑on (Tabellen‑Kit/Compliance‑Kit/Audit‑Ready) ergänzt werden."
    else:
        title = "Ihr KI‑Status‑Report"
        intro = "anbei erhalten Sie Ihren automatisch generierten KI‑Status‑Report."
        cta_hint = ""

    link_html = f'<p>Sie können den Report <a href="{escape(pdf_url)}">hier als PDF abrufen</a>.</p>' if pdf_url else ""

    # Add briefing summary for admin emails
    briefing_section = ""
    if recipient == "admin" and briefing_summary_html:
        briefing_section = f"""
        <hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">
        <h2 style="color:#2B6CB0;font-size:18px;margin:16px 0 8px">📋 Briefing-Details</h2>
        <p class="muted">Nachfolgend die wichtigsten Angaben des Users für Qualitätskontrolle und Nachvollziehbarkeit:</p>
        {briefing_summary_html}
        """

    # CTA to Strategy form (user emails only)
    strategy_cta = ""
    if recipient != "admin" and briefing_id:
        _strategy_url = f"https://make.ki-sicherheit.jetzt/strategy.html?briefing_id={briefing_id}"
        strategy_cta = (
            '<hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">'
            '<p style="font-size:15px;margin:0 0 8px"><strong>N\u00e4chster Schritt:</strong></p>'
            '<p style="margin:0 0 12px">Fordern Sie jetzt Ihren pers\u00f6nlichen <strong>KI\u2011Strategiebericht</strong> an '
            '\u2014 10 Fragen, 3 Minuten, und Sie erhalten einen individuellen Implementierungsfahrplan.</p>'
            f'<p><a href="{escape(_strategy_url)}" style="display:inline-block;background:#2B6CB0;color:#fff;'
            'padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600">'
            'Strategiebericht anfordern \u2192</a></p>'
            '<p class="muted" style="margin-top:8px">Tipp: In K\u00fcrze erhalten Sie au\u00dferdem Ihre '
            'KI\u2011Potenzial\u2011Analyse mit vertiefter Bewertung Ihres strategischen KI\u2011Potenzials.</p>'
        )

    # Add feedback section for user emails only
    feedback_section = ""
    if recipient != "admin" and user_email:
        feedback_link = generate_feedback_link(user_email, briefing_id=briefing_id)
        feedback_section = f"""
        <hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">
        <p style="font-size:15px;margin:0 0 8px">💬 <strong>Ihr Feedback hilft!</strong></p>
        <p class="muted" style="margin:0 0 12px">Wie hilfreich war der Report? Was können wir verbessern?<br>Dauert nur 2–3 Minuten:</p>
        <p><a href="{escape(feedback_link)}" style="color:#2B6CB0;font-weight:600">→ Feedback geben</a></p>
        """

    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <style>
      body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0f172a;line-height:1.5;margin:0;padding:0;background:#f6f9ff}}
      .wrap{{max-width:640px;margin:0 auto;padding:24px}}
      .card{{background:#fff;border:1px solid #e6edf3;border-radius:12px;padding:18px;box-shadow:0 6px 30px #18324a16;border-top:4px solid #2B6CB0}}
      h1{{color:#2B6CB0;font-size:20px;margin:0 0 8px}}
      p{{margin:8px 0;font-size:14px}}
      .muted{{color:#64748b}}
      a.btn{{display:inline-block;background:#2B6CB0;color:#fff;padding:8px 12px;border-radius:8px;text-decoration:none}}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>{escape(title)}</h1>
        <p>Guten Tag,</p>
        <p>{escape(intro)}</p>
        {link_html}
        {briefing_section}
        {'<p class="muted">' + escape(cta_hint) + '</p>' if cta_hint else ''}
        {strategy_cta}
        {feedback_section}
        <p class="muted">Hinweis: Diese E‑Mail wurde automatisch erzeugt.</p>
      </div>
    </div>
  </body>
</html>"""


def render_deep_dive_email(recipient: str = "user", briefing_id: Optional[int] = None) -> str:
    """Render email HTML for KI-Potenzial-Analyse delivery.

    Args:
        recipient: "user" or "admin".
    """
    if recipient == "admin":
        title = "Kopie: KI-Potenzial-Analyse"
        intro = "dies ist die Admin‑Kopie der KI-Potenzial-Analyse."
    else:
        title = "Ihre KI-Potenzial-Analyse"
        intro = "Ihre KI-Potenzial-Analyse ist fertig."

    body_text = (
        "Im Anhang finden Sie die vertiefende Analyse Ihres strategischen KI‑Bruchpunkts "
        "mit 90‑Tage‑Implementierungsplan, Business Case, Risikobewertung und konkreten n\u00e4chsten Schritten."
    )
    cta = "Bei Fragen stehen wir Ihnen gerne zur Verf\u00fcgung."

    # CTA to Strategy form (user emails only)
    strategy_cta_html = ""
    if recipient != "admin" and briefing_id:
        _strategy_url = f"https://make.ki-sicherheit.jetzt/strategy.html?briefing_id={briefing_id}"
        strategy_cta_html = (
            '<hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">'
            '<p style="font-size:15px;margin:0 0 8px"><strong>Noch mehr Tiefe?</strong></p>'
            '<p style="margin:0 0 12px">Ihr ma\u00dfgeschneiderter <strong>KI\u2011Strategiebericht</strong> '
            '\u2014 10 Fragen, 3 Minuten, und Sie erhalten einen individuellen 90\u2011Tage\u2011Implementierungsplan.</p>'
            f'<p><a href="{escape(_strategy_url)}" style="display:inline-block;background:#0D7377;color:#fff;'
            'padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600">'
            'Strategiebericht anfordern \u2192</a></p>'
        )

    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <style>
      body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0f172a;line-height:1.5;margin:0;padding:0;background:#f6f9ff}}
      .wrap{{max-width:640px;margin:0 auto;padding:24px}}
      .card{{background:#fff;border:1px solid #e6edf3;border-radius:12px;padding:18px;box-shadow:0 6px 30px #18324a16;border-top:4px solid #0D7377}}
      h1{{color:#0D7377;font-size:20px;margin:0 0 8px}}
      p{{margin:8px 0;font-size:14px}}
      .muted{{color:#64748b}}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>{escape(title)}</h1>
        <p>Guten Tag,</p>
        <p>{escape(intro)}</p>
        <p>{escape(body_text)}</p>
        <p>{escape(cta)}</p>
        {strategy_cta_html}
        <hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">
        <p class="muted">Wolf Hohl — KI‑Sicherheit.jetzt</p>
        <p class="muted">Hinweis: Diese E‑Mail wurde automatisch erzeugt.</p>
      </div>
    </div>
  </body>
</html>"""


def render_strategy_email(recipient: str = "user") -> str:
    """Render email HTML for KI-Strategiebericht delivery.

    Args:
        recipient: "user" or "admin".
    """
    if recipient == "admin":
        title = "Kopie: KI-Strategiebericht"
        intro = "dies ist die Admin\u2011Kopie des KI-Strategieberichts."
    else:
        title = "Ihr KI-Strategiebericht"
        intro = "Ihr pers\u00f6nlicher KI-Strategiebericht liegt vor."

    body_text = (
        "Basierend auf Ihrem KI-Readiness Assessment und Ihren strategischen "
        "Zusatzangaben haben wir einen ma\u00dfgeschneiderten Strategiefahrplan "
        "f\u00fcr Ihr Unternehmen erstellt \u2014 mit priorisierten Handlungsempfehlungen, "
        "90-Tage-Implementierungsplan, ROI-Prognosen und passenden F\u00f6rderprogrammen."
    )
    cta = "Ihr KI-Strategiebericht ist als PDF angeh\u00e4ngt. Bei Fragen stehen wir Ihnen gerne zur Verf\u00fcgung."

    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <style>
      body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0f172a;line-height:1.5;margin:0;padding:0;background:#f6f9ff}}
      .wrap{{max-width:640px;margin:0 auto;padding:24px}}
      .card{{background:#fff;border:1px solid #e6edf3;border-radius:12px;padding:18px;box-shadow:0 6px 30px #18324a16;border-top:4px solid #0F1D35}}
      h1{{color:#0F1D35;font-size:20px;margin:0 0 8px}}
      p{{margin:8px 0;font-size:14px}}
      .muted{{color:#64748b}}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>{escape(title)}</h1>
        <p>Guten Tag,</p>
        <p>{escape(intro)}</p>
        <p>{escape(body_text)}</p>
        <p>{escape(cta)}</p>
        <hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">
        <p class="muted">Wolf Hohl \u2014 KI\u2011Sicherheit.jetzt</p>
        <p class="muted">Hinweis: Diese E\u2011Mail wurde automatisch erzeugt.</p>
      </div>
    </div>
  </body>
</html>"""


# =============================================================================
# ADMIN BRIEFING EMAIL (Fragebogen-Daten bei Strategy-Generierung)
# =============================================================================

# German labels for R1 questionnaire fields
_R1_LABELS: Dict[str, str] = {
    "branche": "Branche",
    "unternehmensgroesse": "Unternehmensgröße",
    "bundesland": "Bundesland",
    "selbststaendig": "Selbstständig",
    "hauptleistung": "Hauptleistung",
    "jahresumsatz": "Jahresumsatz",
    "zielgruppen": "Zielgruppen",
    "it_infrastruktur": "IT-Infrastruktur",
    "interne_ki_kompetenzen": "Interne KI-Kompetenzen",
    "datenquellen": "Datenquellen",
    "digitalisierungsgrad": "Digitalisierungsgrad",
    "prozesse_papierlos": "Prozesse papierlos",
    "automatisierungsgrad": "Automatisierungsgrad",
    "ki_einsatz": "KI-Einsatz",
    "ki_kompetenz": "KI-Kompetenz",
    "ki_ziele": "KI-Ziele",
    "ki_guardrails": "KI-Guardrails",
    "ki_projekte": "KI-Projekte",
    "anwendungsfaelle": "Anwendungsfälle",
    "zeitersparnis_prioritaet": "Zeitersparnis-Priorität",
    "pilot_bereich": "Pilot-Bereich",
    "geschaeftsmodell_evolution": "Geschäftsmodell-Evolution",
    "vision_3_jahre": "Vision (3 Jahre)",
    "vision_prioritaet": "Vision-Priorität",
    "strategische_ziele": "Strategische Ziele",
    "massnahmen_komplexitaet": "Maßnahmen-Komplexität",
    "roadmap_vorhanden": "Roadmap vorhanden",
    "governance_richtlinien": "Governance-Richtlinien",
    "change_management": "Change Management",
    "zeitbudget": "Zeitbudget",
    "vorhandene_tools": "Vorhandene Tools",
    "regulierte_branche": "Regulierte Branche",
    "trainings_interessen": "Trainings-Interessen",
    "datenschutzbeauftragter": "Datenschutzbeauftragter",
    "technische_massnahmen": "Technische Maßnahmen",
    "folgenabschaetzung": "Folgenabschätzung",
    "meldewege": "Meldewege",
    "loeschregeln": "Löschregeln",
    "ai_act_kenntnis": "AI-Act-Kenntnis",
    "ki_hemmnisse": "KI-Hemmnisse",
    "bisherige_foerdermittel": "Bisherige Fördermittel",
    "interesse_foerderung": "Interesse an Förderung",
    "erfahrung_beratung": "Erfahrung mit Beratung",
    "investitionsbudget": "Investitionsbudget",
    "marktposition": "Marktposition",
    "benchmark_wettbewerb": "Benchmark Wettbewerb",
    "innovationsprozess": "Innovationsprozess",
    "risikofreude": "Risikofreude",
    "datenschutz": "Datenschutz (Zustimmung)",
    "country": "Land",
}

# German labels for Strategy questionnaire fields (S1–S10)
_STRATEGY_LABELS: Dict[str, str] = {
    "s1_budget": "Budget (12 Monate)",
    "s2_zeitrahmen": "Zeitrahmen",
    "s3_prioritaeten": "Prioritäten (max. 3)",
    "s4_engpass": "Größter Engpass",
    "s5_vision": "Vision",
    "s5_software": "Genutzte Software/Tools",
    "s6_foerderinteresse": "Förderinteresse",
    "s7_entscheidung": "Entscheidungsprozess",
    "s8_erfahrung": "KI-Erfahrung",
    "s9_ansatz": "Infrastruktur-Ansatz",
    "s10_datenschutz": "Datenschutz-Priorität",
}

# Conditional R1 fields – only shown if present in the record
_CONDITIONAL_R1_KEYS = {"selbststaendig", "bundesland"}


def _format_value(val: Any) -> str:
    """Format a field value for display in the admin email."""
    if val is None or val == "" or val == []:
        return '<span style="color:#94a3b8">\u2014</span>'
    if isinstance(val, list):
        return ", ".join(str(v) for v in val) if val else '<span style="color:#94a3b8">\u2014</span>'
    if isinstance(val, bool):
        return "Ja" if val else "Nein"
    return escape(str(val))


def _render_table(title: str, rows: List[Tuple[str, str]], color: str = "#2B6CB0") -> str:
    """Render a 2-column HTML table (Label | Wert) with alternating rows."""
    header = (
        f'<h2 style="color:{color};font-size:16px;margin:24px 0 8px">{escape(title)}</h2>'
        '<table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:16px">'
        '<tr style="background:#f1f5f9">'
        '<th style="text-align:left;padding:6px 10px;border:1px solid #e2e8f0;width:35%">Feld</th>'
        '<th style="text-align:left;padding:6px 10px;border:1px solid #e2e8f0">Wert</th>'
        '</tr>'
    )
    body = ""
    for idx, (label, value) in enumerate(rows):
        bg = ' style="background:#f8fafc"' if idx % 2 == 0 else ""
        body += (
            f"<tr{bg}>"
            f'<td style="padding:6px 10px;border:1px solid #e2e8f0;font-weight:600">{escape(label)}</td>'
            f'<td style="padding:6px 10px;border:1px solid #e2e8f0">{value}</td>'
            "</tr>"
        )
    return header + body + "</table>"


def render_admin_briefing_email(
    briefing_id: int,
    meta: Dict[str, Any],
    r1_answers: Dict[str, Any],
    strategy_answers: Dict[str, Any],
) -> str:
    """Render admin email with all questionnaire data for a strategy generation.

    Args:
        briefing_id: The briefing ID.
        meta: Dict with keys: segment, branche, region, score, timestamp.
        r1_answers: The R1 questionnaire answers dict.
        strategy_answers: The strategy questions dict (S1–S10/S11).
    """
    # --- Meta block ---
    segment = escape(str(meta.get("segment", "\u2014")))
    branche = escape(str(meta.get("branche", "\u2014")))
    region = escape(str(meta.get("region", "\u2014")))
    score = escape(str(meta.get("score", "\u2014")))
    timestamp = escape(str(meta.get("timestamp", "\u2014")))
    kis_number = escape(str(meta.get("kis_number", "")))

    kis_line = f'<p style="margin:4px 0"><strong>KIS-Nummer:</strong> {kis_number}</p>' if kis_number else ""

    meta_html = (
        '<div style="background:#f0f4ff;border-radius:8px;padding:12px 16px;margin-bottom:16px">'
        f'<p style="margin:4px 0"><strong>Briefing-ID:</strong> #{briefing_id}</p>'
        f'{kis_line}'
        f'<p style="margin:4px 0"><strong>Segment:</strong> {segment}</p>'
        f'<p style="margin:4px 0"><strong>Branche:</strong> {branche}</p>'
        f'<p style="margin:4px 0"><strong>Region:</strong> {region}</p>'
        f'<p style="margin:4px 0"><strong>Score:</strong> {score}</p>'
        f'<p style="margin:4px 0"><strong>Generiert am:</strong> {timestamp}</p>'
        "</div>"
    )

    # --- R1 table ---
    r1_rows: List[Tuple[str, str]] = []
    for key, val in r1_answers.items():
        if key in _CONDITIONAL_R1_KEYS and key not in r1_answers:
            continue  # conditional field not present
        label = _R1_LABELS.get(key, key)
        r1_rows.append((label, _format_value(val)))

    r1_table = _render_table("Fragebogen 1 \u2014 KI-Readiness", r1_rows, color="#2B6CB0")

    # --- Strategy table ---
    strategy_keys = [
        "s1_budget", "s2_zeitrahmen", "s3_prioritaeten", "s4_engpass",
        "s5_vision", "s5_software", "s6_foerderinteresse", "s7_entscheidung",
        "s8_erfahrung", "s9_ansatz", "s10_datenschutz",
    ]
    strategy_rows: List[Tuple[str, str]] = []
    for key in strategy_keys:
        val = strategy_answers.get(key)
        # Skip keys that don't exist at all in the data (e.g. s5_vision if not present)
        if key not in strategy_answers:
            continue
        label = _STRATEGY_LABELS.get(key, key)
        strategy_rows.append((label, _format_value(val)))
    # Also include any extra keys not in the predefined list
    for key, val in strategy_answers.items():
        if key not in strategy_keys and key not in ("id", "briefing_id", "created_at"):
            label = _STRATEGY_LABELS.get(key, key)
            strategy_rows.append((label, _format_value(val)))

    strategy_table = _render_table("Fragebogen 2 \u2014 Strategiefragen", strategy_rows, color="#0D7377")

    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>[KIS-Admin] Briefing #{briefing_id}</title>
    <style>
      body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0f172a;line-height:1.5;margin:0;padding:0;background:#f6f9ff}}
      .wrap{{max-width:720px;margin:0 auto;padding:24px}}
      .card{{background:#fff;border:1px solid #e6edf3;border-radius:12px;padding:18px;box-shadow:0 6px 30px #18324a16;border-top:4px solid #0F1D35}}
      h1{{color:#0F1D35;font-size:18px;margin:0 0 12px}}
      p{{margin:6px 0;font-size:13px}}
      .muted{{color:#64748b;font-size:12px}}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>[KIS-Admin] Briefing #{briefing_id} \u2014 Fragebogen-Daten</h1>
        {meta_html}
        {r1_table}
        {strategy_table}
        <hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">
        <p class="muted">Automatisch generiert bei Strategy-Generierung.</p>
      </div>
    </div>
  </body>
</html>"""


def render_briefing_pdf_html(
    display_id: str,
    datum: str,
    answers: Dict[str, Any],
    scores: Dict[str, Any],
    sections: Dict[str, Any],
) -> str:
    """Render a compact briefing summary as a self-contained HTML page for PDF conversion.

    This produces a clean, print-ready document that can be archived as a customer dossier.
    Rendered to PDF via Puppeteer and attached to the admin email.
    """
    from datetime import date as _date

    _dash = "\u2014"  # em dash
    _nbsp = "\u00a0"  # non-breaking space
    _eur = "\u20ac"   # euro sign

    def _e(val: Any) -> str:
        return escape(str(val)) if val and str(val).strip() and str(val) != _dash else _dash

    def _fmt_eur(val: Any) -> str:
        try:
            v = float(val)
            return f"{int(v):,}".replace(",", ".")
        except (ValueError, TypeError):
            return str(val) if val else _dash

    # --- Extract data ---
    branche = answers.get("branche", "") or ""
    segment = answers.get("unternehmensgroesse", "") or ""
    bundesland = answers.get("bundesland", "") or ""
    country = answers.get("country", "DE") or "DE"
    firmenname = answers.get("unternehmen_name", "") or ""

    score_overall = int(scores.get("overall", 0) or 0)
    gov = int(scores.get("governance", 0) or 0)
    sec = int(scores.get("security", 0) or 0)
    val = int(scores.get("value", 0) or 0)
    ena = int(scores.get("enablement", 0) or 0)

    if score_overall >= 80:
        score_label = "Exzellent"
    elif score_overall >= 65:
        score_label = "Gut"
    elif score_overall >= 50:
        score_label = "Solide"
    elif score_overall >= 35:
        score_label = "Ausbauf\u00e4hig"
    else:
        score_label = "Kritisch"

    hours = sections.get("CANON_HOURS_MONTH") or sections.get("qw_hours_total") or sections.get("monatsersparnis_stunden") or _dash
    rate = sections.get("CANON_RATE_EUR") or sections.get("stundensatz_eur") or _dash
    capex = sections.get("CANON_CAPEX_EUR") or sections.get("CAPEX_REALISTISCH_EUR") or _dash
    opex = sections.get("CANON_OPEX_MONTH_EUR") or sections.get("OPEX_REALISTISCH_EUR") or _dash
    roi = sections.get("ROI_12M") or sections.get("ROI_12M_CAPPED") or _dash
    payback = sections.get("PAYBACK_MONTHS") or _dash

    try:
        brutto_jahr = float(hours) * float(rate) * 12
        brutto_jahr_str = _fmt_eur(brutto_jahr)
    except (ValueError, TypeError):
        brutto_jahr_str = _dash

    pipeline_grade = sections.get("PIPELINE_GRADE", _dash)
    consistency_grade = sections.get("CONSISTENCY_GRADE", _dash)

    # Free text (truncated)
    hauptleistung = escape(str(answers.get("hauptleistung", ""))[:200])
    ziele = escape(str(answers.get("strategische_ziele", ""))[:300])

    today_str = _date.today().strftime("%d.%m.%Y")

    return (
        "<!doctype html>\n"
        '<html lang="de">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>Kunden-Briefing {_e(display_id)}</title>\n"
        "<style>\n"
        "  @page { size: A4; margin: 20mm 15mm; }\n"
        "  body { font-family: -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; color: #0f172a; line-height: 1.5; margin: 0; padding: 20px; font-size: 13px; }\n"
        "  h1 { font-size: 18px; color: #1e293b; margin: 0 0 4px; }\n"
        "  h2 { font-size: 14px; color: #2B6CB0; margin: 20px 0 8px; border-bottom: 2px solid #2B6CB0; padding-bottom: 4px; }\n"
        "  .meta { font-size: 12px; color: #64748b; margin: 0 0 16px; }\n"
        "  table { width: 100%; border-collapse: collapse; margin-bottom: 12px; }\n"
        "  td { padding: 5px 8px; font-size: 13px; border-bottom: 1px solid #e2e8f0; }\n"
        "  td:first-child { color: #64748b; width: 40%; }\n"
        "  td:last-child { font-weight: 600; }\n"
        "  .score-box { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 12px 16px; text-align: center; margin-bottom: 16px; }\n"
        "  .score-big { font-size: 32px; font-weight: 700; color: #0369a1; }\n"
        "  .score-label { font-size: 13px; color: #0369a1; }\n"
        "  .dims { display: flex; justify-content: space-around; margin-top: 8px; font-size: 12px; color: #475569; }\n"
        "  .footer { margin-top: 24px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; }\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "\n"
        f"<h1>KUNDEN-BRIEFING {_dash} {_e(display_id)}</h1>\n"
        f'<p class="meta">{_e(datum)} &middot; Erstellt: {today_str} &middot; ki-sicherheit.jetzt</p>\n'
        "\n"
        "<h2>Unternehmen</h2>\n"
        "<table>\n"
        f"  <tr><td>Firma</td><td>{_e(firmenname)}</td></tr>\n"
        f"  <tr><td>Branche</td><td>{_e(branche)}</td></tr>\n"
        f"  <tr><td>Segment</td><td>{_e(segment)}</td></tr>\n"
        f"  <tr><td>Region</td><td>{_e(bundesland)}, {_e(country)}</td></tr>\n"
        "</table>\n"
        "\n"
        "<h2>Scores</h2>\n"
        '<div class="score-box">\n'
        f'  <span class="score-big">{score_overall}</span><span style="font-size:14px;color:#64748b">/100</span>\n'
        f'  <div class="score-label">{score_label}</div>\n'
        '  <div class="dims">\n'
        f"    <span>Governance {gov}</span>\n"
        f"    <span>Sicherheit {sec}</span>\n"
        f"    <span>Wertsch\u00f6pfung {val}</span>\n"
        f"    <span>Bef\u00e4higung {ena}</span>\n"
        "  </div>\n"
        "</div>\n"
        "\n"
        "<h2>Financials (Canonical)</h2>\n"
        "<table>\n"
        f"  <tr><td>Zeitersparnis</td><td>{_e(hours)}h/Monat</td></tr>\n"
        f"  <tr><td>Stundensatz</td><td>{_e(rate)}{_nbsp}{_eur}</td></tr>\n"
        f"  <tr><td>CAPEX</td><td>{_fmt_eur(capex)}{_nbsp}{_eur}</td></tr>\n"
        f"  <tr><td>OPEX</td><td>{_fmt_eur(opex)}{_nbsp}{_eur}/Monat</td></tr>\n"
        f"  <tr><td>Brutto-Jahresersparnis</td><td>{brutto_jahr_str}{_nbsp}{_eur}</td></tr>\n"
        f"  <tr><td>ROI (12M)</td><td>{_e(roi)}%</td></tr>\n"
        f"  <tr><td>Payback</td><td>{_e(payback)} Monate</td></tr>\n"
        "</table>\n"
        "\n"
        "<h2>Qualit\u00e4t</h2>\n"
        "<table>\n"
        f"  <tr><td>Pipeline Grade</td><td>{_e(pipeline_grade)}</td></tr>\n"
        f"  <tr><td>Consistency Grade</td><td>{_e(consistency_grade)}</td></tr>\n"
        "</table>\n"
        "\n"
        "<h2>Profil</h2>\n"
        "<table>\n"
        f"  <tr><td>Hauptleistung</td><td>{hauptleistung or _dash}</td></tr>\n"
        f"  <tr><td>Strategische Ziele</td><td>{ziele or _dash}</td></tr>\n"
        "</table>\n"
        "\n"
        '<div class="footer">\n'
        "  Dieses Briefing wurde automatisch generiert. Alle Werte basieren auf den Fragebogen-Eingaben und dem kanonischen Business Case.\n"
        "</div>\n"
        "\n"
        "</body>\n"
        "</html>"
    )
