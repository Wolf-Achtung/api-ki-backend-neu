# -*- coding: utf-8 -*-
"""KIS-1284: Login-Code-Mail mit großem Code (HTML-Teil) — zustellungssicher.

Wunsch aus dem Testbetrieb: Der 6-stellige Code soll in der Mail deutlich
größer und sichtbarer erscheinen. Umsetzung deliverability-first:
  - Der Plain-Text-Teil bleibt WORTGLEICH zur bisherigen Mail (multipart/
    alternative) — Text-Preview, Spam-Score und Text-only-Clients unverändert.
  - Der neue HTML-Teil ist minimal: keine Bilder, keine externen Links oder
    Ressourcen, nur Inline-CSS mit System-/Monospace-Schriften; der Code
    steht groß (36px), fett und mit Buchstabenabstand in einer eigenen Box.
  - services/mailer._send_smtp baut mit HTML jetzt ein echtes
    multipart/alternative statt den Textteil zu verwerfen.
"""

import re

from routes.auth import build_login_code_email


class TestLoginCodeEmailBuilder:

    def test_text_part_unchanged_en(self):
        subject, text, _ = build_login_code_email("748828", 10, en=True)
        assert subject == "Your login code"
        assert "Your personal login code is:\n\n748828\n\n" in text
        assert "The code is valid for 10 minutes." in text
        assert "It is not advertising." in text

    def test_text_part_unchanged_de(self):
        subject, text, _ = build_login_code_email("123456", 10, en=False)
        assert subject == "Ihr Anmeldecode"
        assert "Ihr persönlicher Anmeldecode lautet:\n\n123456\n\n" in text
        assert "Der Code ist 10 Minuten gültig." in text
        assert "Es handelt sich nicht um Werbung." in text

    def test_html_shows_code_large_and_bold(self):
        for en in (True, False):
            _, _, html = build_login_code_email("748828", 10, en=en)
            code_box = re.search(r"<div[^>]*>748828</div>", html)
            assert code_box, "Code muss in einer eigenen Box stehen"
            style = code_box.group(0)
            assert "font-size:36px" in style
            assert "font-weight:700" in style
            assert "letter-spacing" in style

    def test_html_is_deliverability_safe(self):
        """Keine Bilder, keine externen Links/Ressourcen, kein Script."""
        for en in (True, False):
            _, _, html = build_login_code_email("748828", 10, en=en)
            lowered = html.lower()
            assert "<img" not in lowered
            assert "http://" not in lowered
            assert "https://" not in lowered
            assert "<script" not in lowered
            assert "<a " not in lowered  # Support-Adresse nur als Text
            assert "@font-face" not in lowered

    def test_html_contains_all_text_information(self):
        """Der HTML-Teil darf inhaltlich nichts weglassen (EN)."""
        _, _, html = build_login_code_email("748828", 10, en=True)
        for fragment in (
            "Your personal login code is:",
            "valid for 10 minutes",
            "you can ignore this e-mail",
            "No code received?",
            "spam or junk folder",
            "support@ki-sicherheit.jetzt",
            "It is not advertising",
        ):
            assert fragment in html, fragment

    def test_request_code_passes_html(self):
        """routes/auth.request_code übergibt den HTML-Teil an den Mailer."""
        with open("routes/auth.py", encoding="utf-8") as fh:
            src = fh.read()
        assert "build_login_code_email(code, mins, _en)" in src
        assert "html=html_template" in src
        assert "html=None" not in src.split("def request_code")[1].split("def login")[0]


class TestSmtpMultipart:

    def test_smtp_builds_multipart_alternative_with_html(self):
        """_send_smtp darf den Textteil nicht mehr verwerfen."""
        import inspect
        from services.mailer import Mailer
        src = inspect.getsource(Mailer._send_smtp)
        assert 'MIMEMultipart("alternative")' in src
        assert 'MIMEText(text, "plain", "utf-8")' in src
        assert 'MIMEText(html, "html", "utf-8")' in src
