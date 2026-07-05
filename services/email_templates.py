# -*- coding: utf-8 -*-
from __future__ import annotations
"""E‑Mail‑Templates (HTML) für den Report-Versand (UTF‑8, mobil‑tauglich)."""
import logging
import re
from html import escape
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

logger = logging.getLogger(__name__)


# Values that are enum tokens rather than free text get turned into readable
# German for the briefing dossier (e.g. "2000_10000" -> "2.000–10.000",
# "ueber_10" -> "über 10", "keine_angabe" -> "keine Angabe"). Free text (with
# spaces, capitals or punctuation) is returned unchanged.
_ENUM_VALUE_OVERRIDES = {
    "keine_angabe": "keine Angabe",
    "sehr_hoch": "sehr hoch",
    "eher_hoch": "eher hoch",
    "eher_niedrig": "eher niedrig",
    "sehr_niedrig": "sehr niedrig",
    "ja": "Ja",
    "nein": "Nein",
}


# KIS-1245: Klarnamen für Tool-Slugs aus dem Chat-Extraktor —
# "claude, github, netlify, railway" stand roh im Briefing-PDF (Lauf 4).
_TOOL_SLUG_LABELS: Dict[str, str] = {
    "claude": "Claude (Anthropic)",
    "anthropic": "Anthropic",
    "chatgpt": "ChatGPT (OpenAI)",
    "openai": "OpenAI",
    "gemini": "Gemini (Google)",
    "copilot": "GitHub Copilot",
    "github": "GitHub",
    "gitlab": "GitLab",
    "netlify": "Netlify",
    "railway": "Railway",
    "notion": "Notion",
    "perplexity": "Perplexity",
    "midjourney": "Midjourney",
    "canva": "Canva",
    "slack": "Slack",
    "zapier": "Zapier",
    "airtable": "Airtable",
    "hubspot": "HubSpot",
    "salesforce": "Salesforce",
    "datev": "DATEV",
    "sap": "SAP",
}

# KIS-1245: Einheiten für reine Zahlbereichs-Enums je Feld —
# "2.000–10.000" ohne € und "81–100" ohne % im Briefing-PDF (Lauf 4).
_RANGE_UNIT_SUFFIX: Dict[str, str] = {
    "s1_budget": " €",
    "investitionsbudget": " €",
    "prozesse_papierlos": " %",
}


def _prettify_enum_value(val: Any, field: str = "") -> str:
    """Turn an enum-looking token into readable German; leave free text as-is."""
    # KIS-1245: Booleans kamen roh als "True" ins PDF ("Datenschutz: True").
    if isinstance(val, bool):
        return "Ja" if val else "Nein"
    s = str(val).strip()
    # KIS-1248: Bindestrich-Bereichswerte ("51-80") fielen durch das
    # Enum-Gate und blieben ohne Einheit — nur für Felder mit bekannter
    # Einheit anfassen (Datums-/Freitextwerte bleiben unberührt).
    if field in _RANGE_UNIT_SUFFIX:
        _hy = re.fullmatch(r"(\d+)\s*-\s*(\d+)", s)
        if _hy:
            return f"{_hy.group(1)}\u2013{_hy.group(2)}{_RANGE_UNIT_SUFFIX[field]}"
    # Only touch pure enum tokens: lowercase, no spaces, [a-z0-9_] only.
    if not s or s != s.lower() or not re.fullmatch(r"[a-z0-9_]+", s):
        # KIS-1248: Komma-gejointe Listen ohne Leerzeichen lesbar machen
        # ("ChatGPT / OpenAI,Claude / Anthropic" — Lauf 1238).
        _out = str(val)
        if "," in _out and not s.startswith("{"):
            _out = re.sub(r",(?=\S)", ", ", _out)
        return _out
    # KIS-1235: Erst die Fragebogen-Antwortlabels probieren — das Briefing
    # zeigte rohe Codes ("freiberufler", "marktfuehrerschaft", "kunden").
    if field:
        try:
            from services.chat_conversation import _ENUM_DISPLAY
            _display = _ENUM_DISPLAY.get(field) or {}
            # KIS-1245: Einige Maps führen Bindestrich-Keys ("81-100": "81–100 %"),
            # gespeichert wird aber "81_100" — beide Varianten probieren.
            label = _display.get(s) or _display.get(s.replace("_", "-"))
            if label:
                return label
        except Exception:
            pass
    if s in _TOOL_SLUG_LABELS:
        return _TOOL_SLUG_LABELS[s]
    if s in _ENUM_VALUE_OVERRIDES:
        return _ENUM_VALUE_OVERRIDES[s]
    # Numeric range like "2000_10000" -> "2.000–10.000" (+ Einheit je Feld).
    m = re.fullmatch(r"(\d+)_(\d+)", s)
    if m:
        a = f"{int(m.group(1)):,}".replace(",", ".")
        b = f"{int(m.group(2)):,}".replace(",", ".")
        return f"{a}–{b}{_RANGE_UNIT_SUFFIX.get(field, '')}"
    parts = ["über" if p == "ueber" else p for p in s.split("_")]
    out = " ".join(parts)
    # KIS-1245: Alleinstehende Kleinbuchstaben-Tokens ("viele", "gemischt",
    # "keine") als Zellwert groß beginnen; Mehrwort-Enums behalten ihre
    # gewachsene Schreibweise ("sehr hoch", "über 10").
    if "_" not in s and out:
        return out[:1].upper() + out[1:]
    return out


def _prettify_key_label(key: str) -> str:
    """Turn a raw snake_case answer key into a readable label."""
    return key.replace("_", " ").strip().capitalize()


def generate_feedback_link(email: str, briefing_id: int = None) -> str:
    """Generiert den Feedback-Link mit der E-Mail als URL-Parameter."""
    encoded_email = quote(email)
    url = f"https://make.ki-sicherheit.jetzt/feedback/feedback.html?email={encoded_email}"
    if briefing_id:
        url += f"&briefing_id={briefing_id}"
    return url


def render_coach_cta(briefing_id: int, accent_color: str) -> str:
    """Render the Coach-Gespräch CTA block for user-facing report emails."""
    coach_url = f"https://make.ki-sicherheit.jetzt/coach/{briefing_id}"
    return (
        '<table role="presentation" style="margin: 24px auto; width: 100%; max-width: 600px;">'
        '<tr>'
        '<td style="padding: 20px 16px; background: #f8f9fa; border-radius: 12px; text-align: center;">'
        '<p style="font-size: 16px; color: #1a1a1a; margin: 0 0 8px; font-weight: 600;">'
        'Fragen zu Ihrem Report?'
        '</p>'
        '<p style="font-size: 14px; color: #6b7280; margin: 0 0 18px; line-height: 1.5;">'
        'Sprechen Sie mit Ihrem pers\u00f6nlichen KI-Coach \u2014 er kennt Ihren Report '
        'und begleitet Sie bei den n\u00e4chsten Schritten.'
        '</p>'
        f'<a href="{escape(coach_url)}" '
        f'style="display: inline-block; background: {accent_color}; color: #ffffff; '
        'padding: 13px 28px; border-radius: 8px; text-decoration: none; '
        'font-weight: 600; font-size: 14px; '
        "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\">"
        'Coach-Gespr\u00e4ch starten'
        '</a>'
        '<p style="font-size: 11px; color: #9ca3af; margin: 14px 0 0;">'
        'Kostenlos w\u00e4hrend der Testphase \u00b7 Gespr\u00e4che werden nicht gespeichert'
        '</p>'
        '</td>'
        '</tr>'
        '</table>'
    )


def render_report_ready_email(recipient: str, pdf_url: Optional[str], briefing_summary_html: Optional[str] = None, user_email: Optional[str] = None, briefing_id: Optional[int] = None) -> str:
    if recipient == "admin":
        # FIX-KIS-1027.5-B: "(inkl. Briefing)" aus Title entfernt — diese Mail
        # enthaelt KEIN Briefing mehr. Briefing-Daten + PDF kommen separat
        # ueber die [KIS-Admin]-Mail (routes/chat.py:_finalize_strategy_chat).
        title = "Kopie: KI‑Status‑Report"
        intro = "dies ist die Admin‑Kopie des automatisch generierten KI‑Status‑Reports."
        cta_hint = "Tipp: Für Audit‑Ready‑Kunden kann optional das EU‑AI‑Act‑Add‑on (Tabellen‑Kit/Compliance‑Kit/Audit‑Ready) ergänzt werden."
    else:
        title = "Ihr KI‑Status‑Report"
        intro = "anbei erhalten Sie Ihren automatisch generierten KI‑Status‑Report."
        cta_hint = ""

    link_html = f'<p>Sie können den Report <a href="{escape(pdf_url)}">hier als PDF abrufen</a>.</p>' if pdf_url else ""

    # FIX-KIS-1027.5-B: Briefing-Section deaktiviert. Selbst wenn ein Caller
    # versehentlich briefing_summary_html durchreicht, wird sie nicht mehr
    # gerendert — Single-Source-of-Truth fuer Admin-Briefing-Daten ist
    # die [KIS-Admin]-Mail aus dem Chat-Abschluss-Hook.
    briefing_section = ""

    # [COACH-CTA-REMOVED] Sprint B Dramaturgie: Coach-CTA wird nicht mehr in
    # R1/KPA/Strategy Mails gerendert. User soll alle drei Reports in Ruhe
    # lesen, der Coach-CTA kommt jetzt erst in der dedizierten 4. Mail
    # (`_send_coach_reminder_email`) nach Strategy-Mail.
    coach_cta = ""
    if recipient != "admin" and briefing_id:
        logger.info("[COACH-CTA-REMOVED] template=report_ready briefing_id=%d", briefing_id)

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
        {coach_cta}
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

    # KIS-1116: Strategy-Upsell removed from KPA-Email (belongs in R1-Email only)
    strategy_cta_html = ""

    # [COACH-CTA-REMOVED] Sprint B Dramaturgie — siehe render_report_ready_email.
    coach_cta = ""
    if recipient != "admin" and briefing_id:
        logger.info("[COACH-CTA-REMOVED] template=deep_dive briefing_id=%d", briefing_id)

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
        {coach_cta}
        <hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">
        <p class="muted">Wolf Hohl — KI‑Sicherheit.jetzt</p>
        <p class="muted">Hinweis: Diese E‑Mail wurde automatisch erzeugt.</p>
      </div>
    </div>
  </body>
</html>"""


def render_strategy_email(recipient: str = "user", briefing_id: Optional[int] = None) -> str:
    """Render email HTML for KI-Strategiebericht delivery.

    Args:
        recipient: "user" or "admin".
        briefing_id: Briefing ID — required to render the Coach CTA for user emails.
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

    # [COACH-CTA-REMOVED] Sprint B Dramaturgie — siehe render_report_ready_email.
    coach_cta = ""
    if recipient != "admin" and briefing_id is not None:
        logger.info("[COACH-CTA-REMOVED] template=strategy briefing_id=%d", briefing_id)

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
        {coach_cta}
        <hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">
        <p class="muted">Wolf Hohl \u2014 KI\u2011Sicherheit.jetzt</p>
        <p class="muted">Hinweis: Diese E\u2011Mail wurde automatisch erzeugt.</p>
      </div>
    </div>
  </body>
</html>"""


def render_coach_reminder_email(briefing_id: int) -> str:
    """4. Mail im Delivery-Vertrag: Coach-Reminder nach Strategy-Mail.

    Sprint B Coach-CTA-Dramaturgie: User erhält nach Versand aller drei
    Reports (R1, KPA, Strategy) eine separate Mail mit prominentem
    Coach-CTA. Ziel: fundierte Coach-Gespräche statt oberflächlicher
    Klicks unmittelbar nach R1. Die drei Report-Mails enthalten daher
    KEINEN Coach-CTA mehr (siehe [COACH-CTA-REMOVED] Marker oben).
    """
    title = "Ihr KI-Coach steht bereit"
    cta = render_coach_cta(briefing_id, "#2B6CB0")
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
      ul{{padding-left:22px;margin:8px 0;font-size:14px}}
      li{{margin:4px 0}}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>{escape(title)}</h1>
        <p>Guten Tag,</p>
        <p>Sie haben jetzt alle drei Reports erhalten — den
        <strong>KI‑Status‑Report</strong>, die
        <strong>KI‑Potenzial‑Analyse</strong> und den
        <strong>KI‑Strategiebericht</strong>.</p>
        <p>Nehmen Sie sich Zeit, die Reports in Ruhe durchzuarbeiten.
        Die Inhalte ergänzen sich — zusammen ergeben sie ein vollständiges
        Bild Ihrer KI‑Ausgangslage und Ihres Implementierungspfads.</p>
        <p>Sobald Fragen auftauchen, steht Ihnen Ihr persönlicher
        <strong>KI‑Coach</strong> unter folgendem Link für konkrete,
        individuelle und sichere Antworten zur Verfügung:</p>
        {cta}
        <p style="margin-top:16px">Der Coach kennt Ihre Reports und unterstützt Sie typischerweise bei:</p>
        <ul>
          <li>Konkreten Umsetzungsfragen aus den Quick Wins und der 90‑Tage‑Roadmap</li>
          <li>Risikodiskussion und Stop‑Signal‑Setzung</li>
          <li>Tool‑Auswahl und Anbietervergleich</li>
          <li>Förderstrategie und Programm‑Eignung</li>
        </ul>
        <hr style="border:none;border-top:1px solid #e6edf3;margin:24px 0">
        <p class="muted">Wolf Hohl — KI‑Sicherheit.jetzt</p>
        <p class="muted">Hinweis: Diese E‑Mail wurde automatisch erzeugt.</p>
      </div>
    </div>
  </body>
</html>"""


# =============================================================================
# APPETIZER (Schnell-Check) EMAIL
# =============================================================================

_ZEITAUFWAND_LABELS = {
    "unter_25": "unter 25 %",
    "25_50": "25–50 %",
    "ueber_50": "über 50 %",
}

_KI_ERFAHRUNG_LABELS = {
    "keine": "Keine",
    "erste_versuche": "Erste Versuche",
    "regelmaessig": "Regelmäßig",
}

_MITARBEITER_LABELS = {
    "1": "Solo (1)",
    "2-10": "Team (2–10)",
    "11-100": "KMU (11–100)",
}


def render_appetizer_result_email(
    recipient: str,
    request_data: dict,
    result: dict,
) -> str:
    """Render email HTML for KI-Schnell-Check result.

    Args:
        recipient: "user" or "admin".
        request_data: Dict with all AppetizerRequest fields.
        result: The full appetizer result dict (score, hebel, monetarisierung, etc.).
    """
    score = result.get("score", {})
    score_wert = score.get("wert", 0)
    einordnung = score.get("einordnung", "")
    einordnung_text = score.get("einordnung_text", "")

    if recipient == "admin":
        return _render_appetizer_admin_email(request_data, result)

    # --- USER EMAIL ---
    hebel = result.get("hebel", [])
    hebel_html = ""
    for h in hebel:
        hebel_html += (
            f'<tr><td style="padding:6px 8px;border-bottom:1px solid #e6edf3">'
            f'<strong>{escape(h.get("titel", ""))}</strong><br>'
            f'<span style="color:#64748b;font-size:13px">{escape(h.get("beschreibung", ""))}</span></td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #e6edf3;white-space:nowrap;text-align:right;vertical-align:top">'
            f'<strong>{h.get("zeitersparnis_pro_woche_stunden", 0)} h/Wo</strong></td></tr>'
        )

    monet = result.get("monetarisierung", [])
    monet_html = ""
    for m in monet:
        monet_html += (
            f'<tr><td style="padding:6px 8px;border-bottom:1px solid #e6edf3">'
            f'<strong>{escape(m.get("titel", ""))}</strong></td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #e6edf3;white-space:nowrap;text-align:right">'
            f'{m.get("umsatzpotenzial_monat_eur", 0):,}\u202f\u20ac/Mon</td></tr>'.replace(",", ".")
        )

    positionierung = escape(result.get("positionierung", ""))
    cta = result.get("cta", {})
    cta_headline = escape(cta.get("headline", "Vollständigen Report anfordern"))

    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Ihr KI\u2011Schnell\u2011Check Ergebnis</title>
    <style>
      body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0f172a;line-height:1.5;margin:0;padding:0;background:#f6f9ff}}
      .wrap{{max-width:640px;margin:0 auto;padding:24px}}
      .card{{background:#fff;border:1px solid #e6edf3;border-radius:12px;padding:18px;box-shadow:0 6px 30px #18324a16;border-top:4px solid #2B6CB0}}
      h1{{color:#2B6CB0;font-size:20px;margin:0 0 8px}}
      h2{{color:#2B6CB0;font-size:16px;margin:16px 0 6px}}
      p{{margin:8px 0;font-size:14px}}
      .muted{{color:#64748b}}
      .score-box{{background:#f0f7ff;border:1px solid #b8d4f0;border-radius:8px;padding:12px 16px;text-align:center;margin:12px 0}}
      .score-val{{font-size:32px;font-weight:700;color:#2B6CB0}}
      table{{width:100%;border-collapse:collapse;font-size:14px}}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>Ihr KI\u2011Schnell\u2011Check Ergebnis</h1>
        <p>Guten Tag,</p>
        <p>vielen Dank f\u00fcr Ihren KI\u2011Schnell\u2011Check. Hier ist Ihr Ergebnis:</p>

        <div class="score-box">
          <div class="score-val">{score_wert}/100</div>
          <div style="font-weight:600">{escape(einordnung)}</div>
          <div class="muted" style="font-size:13px">{escape(einordnung_text)}</div>
        </div>

        <h2>Top\u20113 KI\u2011Hebel</h2>
        <table>{hebel_html}</table>

        <h2>Monetarisierungs\u2011Potenzial</h2>
        <table>{monet_html}</table>

        <p style="margin-top:14px"><em>{positionierung}</em></p>

        <hr style="border:none;border-top:1px solid #e6edf3;margin:20px 0">
        <p style="text-align:center">
          <a href="https://make.ki-sicherheit.jetzt" style="display:inline-block;background:#2B6CB0;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600">
            {cta_headline} \u2192
          </a>
        </p>
        <p class="muted" style="text-align:center;font-size:13px">{escape(cta.get("subline", ""))}</p>

        <hr style="border:none;border-top:1px solid #e6edf3;margin:20px 0">
        <p class="muted">Wolf Hohl \u2014 KI\u2011Sicherheit.jetzt</p>
        <p class="muted">Hinweis: Diese E\u2011Mail wurde automatisch erzeugt.</p>
      </div>
    </div>
  </body>
</html>"""


def _render_appetizer_admin_email(request_data: dict, result: dict) -> str:
    """Internal: admin lead-notification for Schnell-Check."""
    score = result.get("score", {})
    rows = [
        ("Firma", request_data.get("firma", "")),
        ("Branche", request_data.get("branche", "")),
        ("Mitarbeiter", _MITARBEITER_LABELS.get(request_data.get("mitarbeiter", ""), request_data.get("mitarbeiter", ""))),
        ("Hauptleistung", request_data.get("hauptleistung", "")),
        ("Zeitaufwand repetitiv", _ZEITAUFWAND_LABELS.get(request_data.get("zeitaufwand_repetitiv", ""), request_data.get("zeitaufwand_repetitiv", ""))),
        ("KI-Erfahrung", _KI_ERFAHRUNG_LABELS.get(request_data.get("ki_erfahrung", ""), request_data.get("ki_erfahrung", ""))),
        ("Größte Herausforderung", request_data.get("groesste_herausforderung", "")),
        ("Email", request_data.get("email", "")),
        ("Newsletter Opt-in", "Ja" if request_data.get("newsletter_optin") else "Nein"),
        ("Score", f'{score.get("wert", 0)}/100 — {score.get("einordnung", "")}'),
    ]
    rows_html = ""
    for label, value in rows:
        rows_html += (
            f'<tr><td style="padding:6px 8px;border-bottom:1px solid #e6edf3;font-weight:600;white-space:nowrap;vertical-align:top">'
            f'{escape(label)}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #e6edf3">{escape(str(value))}</td></tr>'
        )

    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Schnell-Check Lead</title>
    <style>
      body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0f172a;line-height:1.5;margin:0;padding:0;background:#f6f9ff}}
      .wrap{{max-width:640px;margin:0 auto;padding:24px}}
      .card{{background:#fff;border:1px solid #e6edf3;border-radius:12px;padding:18px;box-shadow:0 6px 30px #18324a16;border-top:4px solid #2B6CB0}}
      h1{{color:#2B6CB0;font-size:18px;margin:0 0 12px}}
      p{{margin:8px 0;font-size:14px}}
      .muted{{color:#64748b}}
      table{{width:100%;border-collapse:collapse;font-size:14px}}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>Schnell-Check Lead</h1>
        <table>{rows_html}</table>
        <p class="muted" style="margin-top:12px">Hinweis: Diese E\u2011Mail wurde automatisch erzeugt.</p>
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
    "projekte_pro_monat": "Aufträge/Projekte pro Monat",
    "durchschnittshonorar": "Durchschnittshonorar/Projekt",
    "top_zeitfresser": "Top-Zeitfresser",
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
    # KIS-1237: S-Moat-Felder — standen im Briefing-PDF (Lauf 1119) als
    # rohe Feldnamen ("wettbewerber_anzahl") in der Fragebogen-2-Tabelle.
    "wettbewerber_anzahl": "Wettbewerber (Anzahl)",
    "kundenbindung_typ": "Kundenbindung",
    "datenreife": "Datenreife",
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
    s = str(val)
    # KIS-1237: String-Booleans ("True") und fehlende Leerzeichen nach
    # Kommas ("ChatGPT / OpenAI,Claude / Anthropic") lesbar machen \u2014
    # beides stand so im Briefing-PDF von Lauf 1119.
    if s.strip().lower() in ("true", "false"):
        return "Ja" if s.strip().lower() == "true" else "Nein"
    s = re.sub(r",(?=\S)", ", ", s)
    return escape(s)


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
    # FIX-KIS-1027.5-C: Underscore-prefixed keys sind interne Pipeline-Metadaten
    # (z.B. "_chat_unsurveyed_blocks") und gehoeren nicht in die Admin-Briefing-
    # Tabelle. Sonst erscheint "A, B, C, D" als Debug-Falle.
    r1_rows: List[Tuple[str, str]] = []
    for key, val in r1_answers.items():
        if key in _CONDITIONAL_R1_KEYS and key not in r1_answers:
            continue  # conditional field not present
        if key.startswith("_"):
            continue
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


def _render_pdf_questionnaire_tables(
    answers: Dict[str, Any],
    strategy_answers: Optional[Dict[str, Any]],
    dash: str,
) -> str:
    """Render full R1 + Strategy questionnaire data as print-friendly HTML tables for the PDF."""
    html_parts: List[str] = []

    # --- R1 Questionnaire ---
    r1_rows: List[str] = []
    # Keys already shown in the summary section above — skip to avoid duplication
    _skip_r1 = {"branche", "unternehmensgroesse", "bundesland", "country",
                 "unternehmen_name", "hauptleistung", "strategische_ziele"}
    for key, label in _R1_LABELS.items():
        if key in _skip_r1:
            continue
        val = answers.get(key)
        if val is None or val == "" or val == []:
            continue
        display = (escape(", ".join(_prettify_enum_value(v, key) for v in val)) if isinstance(val, list)
                   else escape(_prettify_enum_value(val, key)))
        r1_rows.append(f"  <tr><td>{escape(label)}</td><td>{display}</td></tr>")

    # Also include any answer keys not in _R1_LABELS (catch-all)
    # FIX-KIS-1027.5-C: Underscore-prefixed keys ("_chat_*", "_meta_*", etc.)
    # sind interne Pipeline-Metadaten und gehoeren nicht ins Briefing-PDF.
    # Vorher tauchte z.B. "_chat_unsurveyed_blocks: A, B, C, D" als
    # Debug-Falle auf (Wolf-Briefing 1027.5-C).
    for key, val in answers.items():
        if key in _skip_r1 or key in _R1_LABELS:
            continue
        if val is None or val == "" or val == []:
            continue
        if key in ("id", "briefing_id", "created_at", "updated_at", "email", "user_id"):
            continue
        if key.startswith("_"):
            continue
        display = (escape(", ".join(_prettify_enum_value(v, key) for v in val)) if isinstance(val, list)
                   else escape(_prettify_enum_value(val, key)))
        r1_rows.append(f"  <tr><td>{escape(_prettify_key_label(key))}</td><td>{display}</td></tr>")

    if r1_rows:
        html_parts.append('<h2 style="page-break-before:always">Fragebogen 1 \u2014 KI-Readiness</h2>\n')
        html_parts.append("<table>\n")
        html_parts.extend(r + "\n" for r in r1_rows)
        html_parts.append("</table>\n\n")

    # --- Strategy Questionnaire ---
    if strategy_answers:
        s_rows: List[str] = []
        strategy_keys = [
            "s1_budget", "s2_zeitrahmen", "s3_prioritaeten", "s4_engpass",
            "s5_vision", "s5_software", "s6_foerderinteresse", "s7_entscheidung",
            "s8_erfahrung", "s9_ansatz", "s10_datenschutz",
        ]
        seen: set = set()
        for key in strategy_keys:
            val = strategy_answers.get(key)
            seen.add(key)
            if val is None or val == "" or val == []:
                continue
            label = _STRATEGY_LABELS.get(key, key)
            # KIS-1248: field durchreichen — sonst bekommt s1_budget kein €
            display = (escape(", ".join(_prettify_enum_value(v, key) for v in val)) if isinstance(val, list)
                   else escape(_prettify_enum_value(val, key)))
            s_rows.append(f"  <tr><td>{escape(label)}</td><td>{display}</td></tr>")
        # Catch-all for extra strategy keys
        for key, val in strategy_answers.items():
            if key in seen or key in ("id", "briefing_id", "created_at"):
                continue
            if val is None or val == "" or val == []:
                continue
            label = _STRATEGY_LABELS.get(key, key)
            display = (escape(", ".join(_prettify_enum_value(v, key) for v in val)) if isinstance(val, list)
                   else escape(_prettify_enum_value(val, key)))
            s_rows.append(f"  <tr><td>{escape(label)}</td><td>{display}</td></tr>")

        if s_rows:
            html_parts.append("<h2>Fragebogen 2 \u2014 Strategiefragen</h2>\n")
            html_parts.append("<table>\n")
            html_parts.extend(r + "\n" for r in s_rows)
            html_parts.append("</table>\n\n")

    return "".join(html_parts)


def render_briefing_pdf_html(
    display_id: str,
    datum: str,
    answers: Dict[str, Any],
    scores: Dict[str, Any],
    sections: Dict[str, Any],
    strategy_answers: Optional[Dict[str, Any]] = None,
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
    # Resolve enum codes (branche/size/region) to readable labels via the central
    # normalizer. Done on a local copy so the raw `answers` still flow into the
    # questionnaire dump below (avoids duplicate *_LABEL rows there).
    try:
        from services.answers_normalizer import normalize_answers
        _norm = normalize_answers(answers)
    except Exception:  # pragma: no cover - defensive: never break the briefing
        _norm = answers
    branche = _norm.get("BRANCHE_LABEL") or answers.get("branche", "") or ""
    segment = _norm.get("UNTERNEHMENSGROESSE_LABEL") or answers.get("unternehmensgroesse", "") or ""
    bundesland = _norm.get("BUNDESLAND_LABEL") or answers.get("bundesland", "") or ""
    country = answers.get("country", "DE") or "DE"
    firmenname = answers.get("unternehmen_name", "") or ""

    score_overall = int(scores.get("overall", 0) or 0)
    gov = int(scores.get("governance", 0) or 0)
    sec = int(scores.get("security", 0) or 0)
    val = int(scores.get("value", 0) or 0)
    ena = int(scores.get("enablement", 0) or 0)

    # KIS-1126 / C1 FIX: Use central deterministic score label
    from services.extra_sections import get_score_label
    score_label = get_score_label(score_overall, lang="de").capitalize()

    def _de_num(v: Any) -> Any:
        """KIS-1237: '50.0' → '50', '22.5' → '22,5' (deutsches Format —
        das Briefing-PDF zeigte '50.0h/Monat' und '22.5%')."""
        try:
            f = float(v)
        except (ValueError, TypeError):
            return v
        if f == int(f):
            return str(int(f))
        return f"{f:g}".replace(".", ",")

    _hours_raw = sections.get("CANON_HOURS_MONTH") or sections.get("qw_hours_total") or sections.get("monatsersparnis_stunden") or _dash
    hours = _de_num(_hours_raw)
    rate = sections.get("CANON_RATE_EUR") or sections.get("stundensatz_eur") or _dash
    capex = sections.get("CANON_CAPEX_EUR") or sections.get("CAPEX_REALISTISCH_EUR") or _dash
    opex = sections.get("CANON_OPEX_MONTH_EUR") or sections.get("OPEX_REALISTISCH_EUR") or _dash
    roi = _de_num(sections.get("ROI_12M") or sections.get("ROI_12M_CAPPED") or _dash)
    payback = sections.get("PAYBACK_MONTHS") or _dash

    try:
        brutto_jahr = float(_hours_raw) * float(rate) * 12
        brutto_jahr_str = _fmt_eur(brutto_jahr)
    except (ValueError, TypeError):
        brutto_jahr_str = _dash

    pipeline_grade = sections.get("PIPELINE_GRADE", _dash)
    consistency_grade = sections.get("CONSISTENCY_GRADE", _dash)

    # Free text (truncated)
    # KIS-1235: harte [:200]-Kappung schnitt mitten im Wort ("KI-API-basie")
    _hl_raw = str(answers.get("hauptleistung", ""))
    if len(_hl_raw) > 300:
        _hl_raw = _hl_raw[:300].rsplit(" ", 1)[0].rstrip(" ,;.") + " …"
    hauptleistung = escape(_hl_raw)
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
        # KIS-1245: Zeilen nicht mitten durchbrechen, Überschrift klebt an
        # ihrer Tabelle (eine Briefing-Seite trug nur ein einzelnes Feld).
        "  tr { page-break-inside: avoid; }\n"
        "  h2 { page-break-after: avoid; }\n"
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
        # KIS-1245: Firma wird aus Sicherheitsgründen nie erhoben — die leere
        # „Firma —"-Zeile entfällt; falls Alt-Daten einen Namen tragen, bleibt er.
        + (f"  <tr><td>Firma</td><td>{_e(firmenname)}</td></tr>\n" if str(firmenname).strip() else "")
        + f"  <tr><td>Branche</td><td>{_e(branche)}</td></tr>\n"
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
        "<h2>Kennzahlen (kanonisch)</h2>\n"
        "<table>\n"
        f"  <tr><td>Zeitersparnis</td><td>{_e(hours)}{_nbsp}h/Monat</td></tr>\n"
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
        f"  <tr><td>Pipeline-Qualität</td><td>{_e(pipeline_grade)}</td></tr>\n"
        f"  <tr><td>Konsistenz-Bewertung</td><td>{_e(consistency_grade)}</td></tr>\n"
        "</table>\n"
        "\n"
        "<h2>Profil</h2>\n"
        "<table>\n"
        f"  <tr><td>Hauptleistung</td><td>{hauptleistung or _dash}</td></tr>\n"
        f"  <tr><td>Strategische Ziele</td><td>{ziele or _dash}</td></tr>\n"
        "</table>\n"
        "\n"
        + _render_pdf_questionnaire_tables(answers, strategy_answers, _dash)
        + '<div class="footer">\n'
        "  Dieses Briefing wurde automatisch generiert. Alle Werte basieren auf den Fragebogen-Eingaben und dem kanonischen Business Case.\n"
        "</div>\n"
        "\n"
        "</body>\n"
        "</html>"
    )
