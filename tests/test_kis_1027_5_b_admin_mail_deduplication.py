# -*- coding: utf-8 -*-
"""FIX-KIS-1027.5-B: R1-Admin-Mail enthaelt KEINE Briefing-Section mehr.

KIS-1199 zeigte 4 Mails statt 3 fuer Admin:
1. "Neuer KI-Status-Report (inkl. Briefing)" — R1-Admin-Mail mit Inline-Briefing-HTML
2. "[KIS-Admin] Briefing #1082" — neue Admin-Briefing-Mail aus Chat-Hook mit PDF-Anhang
3. "Kopie: KI-Potenzial-Analyse"
4. "Kopie: KI-Strategiebericht"

Sprint-1027.4-Item-3A war als "Verschiebung" gedacht, ist aber faktisch
eine "Addition" geworden — Briefing-Daten wurden doppelt transportiert.

Fix:
- gpt_analyze.py: _build_briefing_summary_html-Call entfernt vor R1-Admin-Mail
- services/email_templates.py:render_report_ready_email:
  - Title "Kopie: KI-Status-Report (inkl. Briefing)" -> "Kopie: KI-Status-Report"
  - briefing_section wird NICHT mehr gerendert, auch wenn ein Caller
    briefing_summary_html durchreicht (defensiver Schutz)

Akzeptanzkriterium: R1-Admin-Mail enthaelt nur Report-Hinweis + Link,
keine Briefing-Felder mehr. [KIS-Admin]-Mail unveraendert.
"""
from __future__ import annotations

from services.email_templates import render_report_ready_email


def test_admin_mail_title_no_longer_says_inkl_briefing():
    """Title-String enthaelt nicht mehr '(inkl. Briefing)'."""
    html = render_report_ready_email(recipient="admin", pdf_url="https://x/x.pdf")
    assert "inkl. Briefing" not in html, (
        "R1-Admin-Mail-Title enthaelt noch '(inkl. Briefing)' — "
        "1027.5-B nicht angewendet."
    )
    assert "KI" in html and "Status" in html and "Report" in html, (
        "R1-Admin-Mail-Title fehlt komplett — Overshoot bei 1027.5-B."
    )


def test_admin_mail_does_not_render_briefing_section_even_if_passed():
    """Defensiv: selbst wenn briefing_summary_html durchgereicht wird,
    rendert die Mail keinen Briefing-Block."""
    fake_briefing_html = (
        "<table><tr><td><strong>UNIQUE_BRIEFING_MARKER_12345</strong></td></tr></table>"
    )
    html = render_report_ready_email(
        recipient="admin",
        pdf_url="https://x/x.pdf",
        briefing_summary_html=fake_briefing_html,
    )
    assert "UNIQUE_BRIEFING_MARKER_12345" not in html, (
        "briefing_summary_html wurde gerendert — 1027.5-B-Defensivschutz greift nicht."
    )
    assert "Briefing-Details" not in html, (
        "Briefing-Details-Header wird noch gerendert."
    )


def test_admin_mail_keeps_pdf_link_and_intro():
    """Sanity: andere Mail-Bestandteile sind unveraendert da."""
    html = render_report_ready_email(recipient="admin", pdf_url="https://example.com/r.pdf")
    assert "https://example.com/r.pdf" in html, "PDF-Link fehlt"
    assert "Admin" in html or "Kopie" in html, "Admin-Hinweis fehlt"


def test_user_mail_unaffected_by_change():
    """User-Mail bleibt von 1027.5-B unberuehrt — kein briefing-summary
    fuer User auch vorher schon."""
    html = render_report_ready_email(
        recipient="user",
        pdf_url="https://example.com/r.pdf",
        briefing_id=1234,
    )
    # User-Title unveraendert
    assert "Ihr KI" in html and "Status" in html and "Report" in html
    # Briefing-Section war fuer User schon vorher abwesend
    assert "Briefing-Details" not in html


def test_gpt_analyze_no_longer_builds_briefing_summary_for_admin_mail():
    """Code-Pfad in gpt_analyze.py: _build_briefing_summary_html wird vor der
    R1-Admin-Mail nicht mehr aufgerufen (briefing_summary_html bleibt None)."""
    import inspect
    import gpt_analyze
    src = inspect.getsource(gpt_analyze)
    # Marker fuer den Fix
    assert "FIX-KIS-1027.5-B" in src, (
        "FIX-KIS-1027.5-B-Marker fehlt in gpt_analyze.py — Fix nicht angewendet."
    )
    # Heuristik: in der R1-Admin-Mail-Sektion (zwischen 'Send to admins'
    # und render_report_ready_email-Call) darf kein aktiver
    # _build_briefing_summary_html-Call mehr stehen.
    import re
    match = re.search(
        r'# Send to admins.*?render_report_ready_email\(\s*recipient="admin"',
        src,
        re.DOTALL,
    )
    assert match, "Admin-Mail-Sektion nicht gefunden"
    block = match.group(0)
    # Keine aktive Zeile (nicht-Kommentar), die _build_briefing_summary_html aufruft.
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert "_build_briefing_summary_html(" not in line, (
            f"Aktiver _build_briefing_summary_html-Call gefunden: {line!r}"
        )
