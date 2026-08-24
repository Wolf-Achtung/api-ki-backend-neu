# -*- coding: utf-8 -*-
"""Funnel-CTA fuer den Cyberangriffs-Check.

KIS-1260 setzte den CTA in die Status-Report-Mail. KIS-1262 verschiebt ihn
in die Strategie-Mail: die Status-Mail trug vier Links (PDF, Strategie,
Check, Feedback), und das Projekt folgt der Sprint-B-Dramaturgie — ein
Angebot pro Mail.
"""

from services.email_templates import render_report_ready_email, render_strategy_email


def _status_mail(recipient="user", lang="de"):
    return render_report_ready_email(
        recipient=recipient, pdf_url="https://x/report.pdf", briefing_id=123, lang=lang,
    )


def _strategie_mail(recipient="user", lang="de"):
    return render_strategy_email(recipient=recipient, briefing_id=123, lang=lang)


class TestCyberCTAInStrategieMail:

    def test_de_user_mail_hat_cta(self):
        html = _strategie_mail()
        assert "Reaktionslücke ermitteln" in html
        assert "/resilienz.html" in html
        # Wording vermeidet den Begriff Resilienz im sichtbaren Text
        assert "Resilienz-Check" not in html.replace("resilienz.html", "")
        assert "automatisierten Cyber-Angriff" in html

    def test_admin_mail_ohne_cta(self):
        assert "Reaktionslücke ermitteln" not in _strategie_mail(recipient="admin")

    def test_en_mail_ohne_cta(self):
        assert "Reaktionslücke ermitteln" not in _strategie_mail(lang="en")


class TestStatusMailBleibtSchlank:

    def test_status_mail_ohne_cyber_cta(self):
        # KIS-1262: genau ein Angebot in dieser Mail — der Strategiebericht.
        html = _status_mail()
        assert "Reaktionslücke ermitteln" not in html
        assert "/resilienz.html" not in html

    def test_status_mail_behaelt_strategie_cta(self):
        assert "strategy" in _status_mail().lower()
