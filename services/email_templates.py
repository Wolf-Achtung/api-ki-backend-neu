# file: services/email_templates.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
HTML-Mail-Templates für Report-Benachrichtigungen.
Warum: Einheitlicher CTA fürs EU‑AI‑Act-Tabellen‑Kit + optionaler CSV-Hinweis.
API bleibt kompatibel zu send_mail(..., render_report_ready_email(...)).
"""
from html import escape
from typing import Optional
import os

# Warum: Phase/CSV-Hinweis ohne Codeänderungen toggeln
AI_ACT_PHASE_LABEL = os.getenv("AI_ACT_PHASE_LABEL", "2025–2027")
ENABLE_AI_ACT_ATTACH_CSV = (os.getenv("ENABLE_AI_ACT_ATTACH_CSV", "1") == "1")

def _cta_block() -> str:
    """Add-on Bewerbung (Tabellen‑Kit) inkl. optionalem CSV-Hinweis."""
    csv_note = (
        "<p>Hinweis: Die kompakte Terminübersicht liegt dieser Mail als CSV bei.</p>"
        if ENABLE_AI_ACT_ATTACH_CSV else ""
    )
    return (
        "<hr>"
        "<p><strong>Optionale Vertiefung:</strong> Auf Wunsch erstellen wir eine "
        "<em>tabellarische Übersicht</em> aller zentralen Termine, Übergangsfristen und "
        "Praxis‑Checkpoints <strong>für Ihre Zielgruppe</strong> "
        f"(Fokus {escape(AI_ACT_PHASE_LABEL)}). Antworten Sie einfach mit „Tabellen‑Kit“.</p>"
        f"{csv_note}"
    )

def render_report_ready_email(recipient: str, pdf_url: Optional[str]) -> str:
    """
    Warum: Einheitliche, robuste Mail – PDF per Link oder Anhang (vom Aufrufer gesteuert).
    """
    title = "Kopie: KI‑Status‑Report (inkl. Briefing)" if recipient == "admin" else "Ihr KI‑Status‑Report"
    intro = (
        "dies ist die Admin‑Kopie des automatisch generierten KI‑Status‑Reports."
        if recipient == "admin"
        else "anbei erhalten Sie Ihren automatisch generierten KI‑Status‑Report."
    )

    link_html = (
        f'<p>Sie können den Report <a href="{escape(pdf_url)}">hier als PDF abrufen</a>.</p>'
        if pdf_url else "<p>Der Report ist als PDF im Anhang.</p>"
    )

    # Preheader verbessert Zustell- & Öffnungsraten (warum: Mail-Clients zeigen ihn prominent)
    preheader = (
        "Ihr individueller KI‑Status‑Report ist fertig – inkl. Next‑Actions und AI‑Act‑Hinweisen."
    )

    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta http-equiv="x-ua-compatible" content="ie=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta charset="utf-8">
    <title>{escape(title)}</title>
    <style>
      /* Fokus: breite Mail‑Kompatibilität, wenig CSS, keine externen Ressourcen */
      body{{margin:0;padding:0;background:#f6f9ff;color:#0f172a;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;line-height:1.5}}
      .wrap{{max-width:640px;margin:0 auto;padding:24px}}
      .card{{background:#fff;border:1px solid #e6edf3;border-radius:12px;padding:18px;box-shadow:0 6px 30px #18324a16}}
      h1{{color:#0b3b8f;font-size:20px;margin:0 0 8px}}
      p{{margin:8px 0;font-size:14px}}
      .muted{{color:#64748b}}
      a.btn{{display:inline-block;background:#0b3b8f;color:#fff;padding:8px 12px;border-radius:8px;text-decoration:none}}
      .preheader{{display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden}}
      @media (prefers-color-scheme: dark) {{
        body{{background:#0b1220;color:#e2e8f0}}
        .card{{background:#0f172a;border-color:#1f2937;box-shadow:none}}
        h1{{color:#93c5fd}}
        a.btn{{background:#2563eb}}
        .muted{{color:#94a3b8}}
      }}
    </style>
  </head>
  <body>
    <div class="preheader">{escape(preheader)}</div>
    <div class="wrap">
      <div class="card">
        <h1>{escape(title)}</h1>
        <p>Guten Tag,</p>
        <p>{escape(intro)}</p>
        {link_html}
        {_cta_block()}
        <p class="muted">Hinweis: Diese E‑Mail wurde automatisch erzeugt.</p>
      </div>
    </div>
  </body>
</html>"""
