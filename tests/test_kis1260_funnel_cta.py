# -*- coding: utf-8 -*-
"""KIS-1260: Funnel-CTA fuer den Reaktionsluecken-Check in der r1-User-Mail."""

from services.email_templates import render_report_ready_email


def _mail(recipient="user", lang="de"):
    return render_report_ready_email(
        recipient=recipient, pdf_url="https://x/report.pdf", briefing_id=123, lang=lang,
    )


class TestResilienzCTA:

    def test_de_user_mail_hat_cta(self):
        html = _mail()
        assert "Reaktionslücke ermitteln" in html
        assert "/resilienz.html" in html
        # Wording vermeidet den Begriff Resilienz im sichtbaren Text
        assert "Resilienz-Check" not in html.replace("resilienz.html", "")

    def test_admin_mail_ohne_cta(self):
        assert "Reaktionslücke ermitteln" not in _mail(recipient="admin")

    def test_en_mail_ohne_cta(self):
        assert "Reaktionslücke ermitteln" not in _mail(lang="en")
