# -*- coding: utf-8 -*-
from __future__ import annotations
"""E‑Mail‑Templates (HTML) für den Report-Versand (UTF‑8, mobil‑tauglich)."""
from html import escape
from typing import Optional
from urllib.parse import quote


def generate_feedback_link(email: str) -> str:
    """Generiert den Feedback-Link mit der E-Mail als URL-Parameter."""
    encoded_email = quote(email)
    return f"https://make.ki-sicherheit.jetzt/feedback/feedback.html?email={encoded_email}"

def render_report_ready_email(recipient: str, pdf_url: Optional[str], briefing_summary_html: Optional[str] = None, user_email: Optional[str] = None, briefing_id: Optional[int] = None) -> str:
    if recipient == "admin":
        title = "Kopie: KI‑Status‑Report (inkl. Briefing)"
        intro = "dies ist die Admin‑Kopie des automatisch generierten KI‑Status‑Reports."
        cta_hint = "Tipp: Für Audit‑Ready‑Kunden kann optional das EU‑AI‑Act‑Add‑on (Tabellen‑Kit/Compliance‑Kit/Audit‑Ready) ergänzt werden."
    else:
        title = "Ihr KI‑Status‑Report"
        intro = "anbei erhalten Sie Ihren automatisch generierten KI‑Status‑Report."
        cta_hint = "Auf Wunsch erstelle ich eine tabellarische Übersicht mit allen zentralen EU‑AI‑Act‑Terminen (2025–2027)."

    link_html = f'<p>Sie können den Report <a href="{escape(pdf_url)}">hier als PDF abrufen</a>.</p>' if pdf_url else ""

    # Add briefing summary for admin emails
    briefing_section = ""
    if recipient == "admin" and briefing_summary_html:
        briefing_section = f"""
        <hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">
        <h2 style="color:#0b3b8f;font-size:18px;margin:16px 0 8px">📋 Briefing-Details</h2>
        <p class="muted">Nachfolgend die wichtigsten Angaben des Users für Qualitätskontrolle und Nachvollziehbarkeit:</p>
        {briefing_summary_html}
        """

    # CTA to Strategy form (user emails only)
    strategy_cta = ""
    if recipient != "admin" and briefing_id:
        _strategy_url = f"https://api-ki-backend-neu-production.up.railway.app/public/strategy.html?briefing_id={briefing_id}"
        strategy_cta = (
            '<hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">'
            '<p style="font-size:15px;margin:0 0 8px"><strong>N\u00e4chster Schritt:</strong></p>'
            '<p style="margin:0 0 12px">Fordern Sie jetzt Ihren pers\u00f6nlichen <strong>KI\u2011Strategiebericht</strong> an '
            '\u2014 10 Fragen, 3 Minuten, und Sie erhalten einen individuellen Implementierungsfahrplan.</p>'
            f'<p><a href="{escape(_strategy_url)}" style="display:inline-block;background:#0b3b8f;color:#fff;'
            'padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:600">'
            'Strategiebericht anfordern \u2192</a></p>'
            '<p class="muted" style="margin-top:8px">Tipp: In K\u00fcrze erhalten Sie au\u00dferdem Ihre '
            'KI\u2011Potenzial\u2011Analyse mit vertiefter Bewertung Ihres strategischen KI\u2011Potenzials.</p>'
        )

    # Add feedback section for user emails only
    feedback_section = ""
    if recipient != "admin" and user_email:
        feedback_link = generate_feedback_link(user_email)
        feedback_section = f"""
        <hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">
        <p style="font-size:15px;margin:0 0 8px">💬 <strong>Ihr Feedback hilft!</strong></p>
        <p class="muted" style="margin:0 0 12px">Wie hilfreich war der Report? Was können wir verbessern?<br>Dauert nur 2–3 Minuten:</p>
        <p><a href="{escape(feedback_link)}" style="color:#0b3b8f;font-weight:600">→ Feedback geben</a></p>
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
      .card{{background:#fff;border:1px solid #e6edf3;border-radius:12px;padding:18px;box-shadow:0 6px 30px #18324a16}}
      h1{{color:#0b3b8f;font-size:20px;margin:0 0 8px}}
      p{{margin:8px 0;font-size:14px}}
      .muted{{color:#64748b}}
      a.btn{{display:inline-block;background:#0b3b8f;color:#fff;padding:8px 12px;border-radius:8px;text-decoration:none}}
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
        <p class="muted">{escape(cta_hint)}</p>
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
        _strategy_url = f"https://api-ki-backend-neu-production.up.railway.app/public/strategy.html?briefing_id={briefing_id}"
        strategy_cta_html = (
            '<hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">'
            '<p style="font-size:15px;margin:0 0 8px"><strong>Noch mehr Tiefe?</strong></p>'
            '<p style="margin:0 0 12px">Ihr ma\u00dfgeschneiderter <strong>KI\u2011Strategiebericht</strong> '
            '\u2014 10 Fragen, 3 Minuten, und Sie erhalten einen individuellen 90\u2011Tage\u2011Implementierungsplan.</p>'
            f'<p><a href="{escape(_strategy_url)}" style="display:inline-block;background:#0b3b8f;color:#fff;'
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
      .card{{background:#fff;border:1px solid #e6edf3;border-radius:12px;padding:18px;box-shadow:0 6px 30px #18324a16}}
      h1{{color:#0b3b8f;font-size:20px;margin:0 0 8px}}
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
      .card{{background:#fff;border:1px solid #e6edf3;border-radius:12px;padding:18px;box-shadow:0 6px 30px #18324a16}}
      h1{{color:#0b3b8f;font-size:20px;margin:0 0 8px}}
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
